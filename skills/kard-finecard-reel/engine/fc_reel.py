#!/usr/bin/env python3
"""
Kard Avenue "Fine Card" cut renderer (cinematic style after @thefinecard).
Separate from kard_reel.py. Full-bleed slow-move shots, blur dissolves, one-line captions,
editorial type-on titles, film-strip frame, person card, split screen, fixed end card.

  python3 fc_reel.py fc.json stills OUT.png
  python3 fc_reel.py fc.json render OUT.mp4
  python3 fc_reel.py fc.json page OUTDIR VIDEO.mp4
  python3 fc_reel.py fc.json frame T OUT.png
  python3 fc_reel.py fc.json check            # lint: length, end card, assets, captions, VO file, stock flag
  python3 fc_reel.py fc.json clip OUT.mp4 SPEC # partial render with audio: 6 (scene) / 5-7 / 12.5:20 (seconds)
  python3 fc_reel.py fc.json script OUT.md     # script doc table from the config

Shot types (per scene "shots" list; last shot of a scene takes the remaining time):
  kb     img, plate cover|white|blur, fill, y, from/to [cx,cy,zoom] or keys [[t,cx,cy,zoom],...],
         focus_in (s), title {text with *italic serif*, at, per, size, y}, sfx [[t,name,gain]]
  film   same camera fields, shown inside a film-strip frame (archival look)
  split  top{...} bottom{...} two camera views stacked
  person img (photo), bg (image to blur behind), name_jp, name_en
  end    fixed full-screen end card (23_end_card.png)
Scene fields: beat, dur, vo, caption, visual, no_caption. Global: pills [{text,at,hold,y,size}],
voiceover, stock_confirmed, forbidden_words, logo, assets_dir, sfx_dir.
"""
import os, sys, re, json, math, wave, subprocess, shutil, functools, multiprocessing as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
XF = .45                          # blur-dissolve length (s)
CAP_Y = 1545                      # caption centre (above Instagram UI line ~1680)
def _font(names, dirs, required=True):
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
    for d in (here, *dirs):
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p): return p
    if required: sys.exit(f'Font not found: {names[0]}. Put it in {here}')
    return None
_SYS = ('/usr/share/fonts/opentype/inter', '/usr/share/fonts/truetype/google-fonts', '/usr/share/fonts/opentype/noto',
        '/usr/share/fonts/truetype/noto', '/Library/Fonts', os.path.expanduser('~/Library/Fonts'), 'C:/Windows/Fonts')
F_SANS = _font(['Inter-SemiBold.otf', 'Inter-SemiBold.ttf'], _SYS)
F_SANSB = _font(['Inter-Bold.otf', 'Inter-Bold.ttf'], _SYS)
F_SERIF_I = _font(['Lora-Italic-Variable.ttf', 'Lora-Italic.ttf'], _SYS)
F_CJK = _font(['NotoSansCJKsub-Bold.otf', 'NotoSansCJK-Bold.ttc', 'NotoSansJP-Bold.ttf', 'NotoSansSC-Bold.ttf', 'NotoSansCJKjp-Bold.otf'], _SYS, required=False)   # optional: only for name_jp
END_CARD = '23_end_card.png'
MIN_LEN, MAX_LEN = 45.0, 60.0
RED = (226, 39, 52)
CFG = BASE = None

@functools.lru_cache(None)
def font(p, s, idx=0): return ImageFont.truetype(p, s, index=idx)
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def eio(x): return x * x * (3 - 2 * x)
def eo3(x): return 1 - (1 - x) ** 3
def lerp(a, b, x): return a + (b - a) * x
def ap(n): return os.path.join(BASE, CFG.get('assets_dir', 'assets'), n)

# ---------------- plates (what the camera looks at) ----------------
PW, PH = 1620, 2880
@functools.lru_cache(None)
def studio():
    yy, xx = np.mgrid[0:PH, 0:PW]; r = np.hypot((xx - PW * .5) / PW, (yy - PH * .45) / PH)
    v = np.clip(262 - r * 30, 238, 255)
    return Image.fromarray(np.stack([v, v, v * .985], -1).astype(np.uint8)).convert('RGB')

@functools.lru_cache(None)
def src(name, maxh=3000):
    im = Image.open(ap(name)); im.load()
    if im.height > maxh: im = im.resize((round(im.width * maxh / im.height), maxh), Image.LANCZOS)
    return im

@functools.lru_cache(None)
def plate(name, kind, fill, y):
    """kind: 'cover' (image itself), 'white' (studio sweep), 'blur' (blurred copy of itself behind)."""
    im = src(name)
    if kind == 'cover': return im.convert('RGB')
    if kind == 'white': base = studio().copy()
    else:
        b = im.convert('RGB'); s = max(PW / b.width, PH / b.height)
        b = b.resize((round(b.width * s), round(b.height * s)), Image.LANCZOS)
        b = b.crop(((b.width - PW) // 2, (b.height - PH) // 2, (b.width - PW) // 2 + PW, (b.height - PH) // 2 + PH))
        base = ImageChops.multiply(b.filter(ImageFilter.GaussianBlur(40)), Image.new('RGB', b.size, (150, 150, 150)))
    s = min(PH * fill / im.height, PW * .92 / im.width); o = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, yy = (PW - o.width) // 2, round(PH * y - o.height / 2)
    if o.mode == 'RGBA':
        if kind == 'white':                                   # soft contact shadow
            sh = Image.new('L', (PW, PH), 0); ImageDraw.Draw(sh).ellipse([x + o.width * .12, yy + o.height - 30, x + o.width * .88, yy + o.height + 40], fill=120)
            base.paste((90, 90, 90), (0, 0), sh.filter(ImageFilter.GaussianBlur(28)))
        base.paste(o, (x, yy), o)
    else:
        m = Image.new('L', o.size, 255)
        if kind == 'white':                                   # feather photo edges into the sweep
            f = max(8, int(min(o.size) * .12)); d = ImageDraw.Draw(m)
            for i in range(f): d.rectangle([i, i, o.width - 1 - i, o.height - 1 - i], outline=int(255 * i / f))
        base.paste(o.convert('RGB'), (x, yy), m)
    return base

def crop_box(pl, cx, cy, z, aspect=W / H, clampit=True):
    pw, ph = pl.size
    if pw / ph > aspect: ch0 = ph; cw0 = ch0 * aspect
    else: cw0 = pw; ch0 = cw0 / aspect
    cw, ch = cw0 / z, ch0 / z; x0, y0 = cx * pw - cw / 2, cy * ph - ch / 2
    if clampit: x0 = clamp(x0, 0, pw - cw); y0 = clamp(y0, 0, ph - ch)
    return (x0, y0, x0 + cw, y0 + ch)

def cam(sh, u):
    k = sh.get('keys') or [[0] + sh.get('from', [.5, .5, 1]), [sh['d']] + sh.get('to', sh.get('from', [.5, .5, 1.08]))]
    if u <= k[0][0]: return k[0][1:]
    for a, b in zip(k, k[1:]):
        if u <= b[0]:
            p = eio(prog(u, a[0], b[0])); return [lerp(a[i], b[i], p) for i in (1, 2, 3)]
    return k[-1][1:]

def view(name, kind, fill, y, cx, cy, z, size=(W, H)):
    pl = plate(name, kind, fill, y); box = crop_box(pl, cx, cy, z, size[0] / size[1])
    return pl.transform(size, Image.EXTENT, box, Image.BICUBIC)

# ---------------- overlays ----------------
@functools.lru_cache(None)
def logo_img(dark):
    lg = Image.open(ap(CFG['logo'])).convert('RGBA'); lg = lg.resize((210, round(lg.height * 210 / lg.width)), Image.LANCZOS)
    if dark: lg = Image.merge('RGBA', (*[Image.new('L', lg.size, 20)] * 3, lg.split()[3]))
    return lg

def lum(im, box): return np.asarray(im.crop(box).convert('L')).mean()

def shadowed(text_im, strength=150, blur=10):
    a = text_im.split()[3]; pad = blur * 3
    out = Image.new('RGBA', (text_im.width + pad * 2, text_im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('L', out.size, 0); sh.paste(a, (pad, pad + 3)); sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: min(255, v * strength // 100))
    out.paste((0, 0, 0), (0, 0), sh); out.alpha_composite(text_im, (pad, pad)); return out, pad

@functools.lru_cache(None)
def cap_img(text, dark):
    size = 50
    while True:
        f = font(F_SANS, size)
        if f.getlength(text) <= 940 or size <= 36: break
        size -= 2
    bb = f.getbbox(text); im = Image.new('RGBA', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 16), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 8 - bb[1]), text, font=f, fill=(22, 22, 22) if dark else (255, 255, 255))
    return (im, 0) if dark else shadowed(im, 170, 9)

def chunks(text, maxw=4):
    words = text.split(); out, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= maxw or (len(cur) >= 2 and w_[-1] in ',.!?—:…'): out.append(' '.join(cur)); cur = []
    if cur:
        if out and len(cur) == 1: out[-1] += ' ' + cur[0]
        else: out.append(' '.join(cur))
    return out

def caption_at(sc, u):
    cap = sc.get('caption')
    if not cap or sc.get('no_caption'): return None
    a, b = .1, sc['dur'] - .1; parts = chunks(cap); L = sum(len(p) for p in parts); t = a
    for p in parts:
        dt = (b - a) * len(p) / L
        if u < t + dt: return p, t
        t += dt
    return parts[-1], t

def title_layout(spec):
    """'*word*' segments -> italic serif. Returns list of (word, font, x, y) laid out top-left."""
    size = spec.get('size', 74); fs, fi = font(F_SANS, size), font(F_SERIF_I, int(size * 1.08))
    x0, y = spec.get('x', 70), spec.get('y', 300); maxw = spec.get('w', 900); x = x0; out = []; ital = False
    for tok in spec['text'].split(' '):
        w_ = tok; it_start = w_.startswith('*'); it_end = w_.endswith('*') and len(w_) > 1
        if it_start: ital = True
        w_ = w_.strip('*'); f = fi if ital else fs
        ww = f.getlength(w_)
        if x > x0 and x + ww > x0 + maxw: x = x0; y += int(size * 1.18)
        out.append((w_, f, x, y)); x += ww + fs.getlength(' ')
        if it_end or (it_start and tok.endswith('*') and len(tok) > 2): ital = False
    if spec.get('align') == 'center':                         # centre each line horizontally
        rows = {}
        for w_, f, x, y in out: rows.setdefault(y, []).append((w_, f, x))
        out2 = []
        for y, r in rows.items():
            right = r[-1][2] + r[-1][1].getlength(r[-1][0]); shift = (W - (right - r[0][2])) / 2 - r[0][2]
            out2 += [(w_, f, x + shift, y) for w_, f, x in r]
        out = out2
    return out

def draw_title(c, spec, u):
    lay = title_layout(spec); t0 = spec.get('at', .3); per = spec.get('per', .14); col = tuple(spec.get('color', [18, 18, 18]))
    for i, (w_, f, x, y) in enumerate(lay):
        p = prog(u, t0 + i * per, t0 + i * per + .22)
        if p <= 0: break
        lay_ = Image.new('RGBA', c.size, (0, 0, 0, 0)); ImageDraw.Draw(lay_).text((x, y + 14 * (1 - eo3(p))), w_, font=f, fill=col + (int(255 * p),))
        c.alpha_composite(lay_)

@functools.lru_cache(None)
def pill(text, size=30):
    f = font(F_SANSB, size); tw = f.getlength(text); im = Image.new('RGBA', (int(tw + size * 1.4), int(size * 1.8)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], 10, fill=RED + (255,))
    d.text((im.width / 2, im.height / 2), text, font=f, fill='white', anchor='mm'); return im

def put_pill(c, text, cx, cy, p, size=30):
    if p <= 0: return
    im = pill(text, size); s = lerp(.6, 1, eo3(min(1, p * 1.4)))
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if p < 1: im.putalpha(im.split()[3].point(lambda v: int(v * min(1, p * 2))))
    c.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

@functools.lru_cache(None)
def grain(i):
    g = np.random.default_rng(5 + i).normal(128, 40, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
    lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(Image.fromarray(g).resize((W, H), Image.NEAREST).point(lambda v: int(abs(v - 128) * .18)))
    return lay

@functools.lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx - W / 2) / W, (yy - H / 2) / H)
    a = (np.clip((r - .42) * 1.6, 0, 1) ** 1.5 * 120).astype(np.uint8); v = Image.new('RGBA', (W, H), (0, 0, 0, 0)); v.putalpha(Image.fromarray(a)); return v

# ---------------- shot renderers (return RGB frame without global overlays) ----------------
def shot_kb(sh, u):
    cx, cy, z = cam(sh, u); im = view(sh['img'], sh.get('plate', 'cover'), sh.get('fill', .7), sh.get('y', .5), cx, cy, z)
    fb = sh.get('focus_in')
    if fb: r = 16 * (1 - eo3(prog(u, 0, fb)));  im = im.filter(ImageFilter.GaussianBlur(r)) if r > .4 else im
    return im

@functools.lru_cache(None)
def film_frame():
    fr = Image.new('RGBA', (W, H), (12, 12, 12, 255)); d = ImageDraw.Draw(fr)
    d.rounded_rectangle([70, 300, W - 70, 1420], 26, fill=(0, 0, 0, 0))
    for y in range(250, 1480, 74):
        d.rounded_rectangle([18, y, 50, y + 42], 7, fill=(225, 225, 220, 255)); d.rounded_rectangle([W - 50, y, W - 18, y + 42], 7, fill=(225, 225, 220, 255))
    return fr

def shot_film(sh, u):
    cx, cy, z = cam(sh, u); inner = view(sh['img'], sh.get('plate', 'cover'), sh.get('fill', .7), sh.get('y', .5), cx, cy, z, (W - 140, 1120))
    inner = inner.filter(ImageFilter.GaussianBlur(.8)); arr = np.asarray(inner).astype(float)
    arr = arr * (.9 + .05 * math.sin(u * 23)) + np.array([14, 6, -10]); inner = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    c = Image.new('RGB', (W, H), (12, 12, 12)); c.paste(inner, (70, 300)); c = c.convert('RGBA'); c.alpha_composite(film_frame())
    return c.convert('RGB')

def shot_split(sh, u):
    c = Image.new('RGB', (W, H), (10, 10, 10)); hh = (H - 10) // 2
    for i, part in enumerate((sh['top'], sh['bottom'])):
        p = dict(part); p['d'] = sh['d']; cx, cy, z = cam(p, u)
        c.paste(view(p['img'], p.get('plate', 'cover'), p.get('fill', .7), p.get('y', .5), cx, cy, z, (W, hh)), (0, i * (hh + 10)))
    return c

def shot_person(sh, u):
    z = lerp(1.0, 1.06, prog(u, 0, sh['d'])); bg = view(sh['bg'], 'cover', .7, .5, .5, .4, z).filter(ImageFilter.GaussianBlur(22))
    bg = ImageChops.multiply(bg, Image.new('RGB', bg.size, (165, 165, 165))).convert('RGBA')
    ph = src(sh['img']).convert('RGB'); s = 700 / ph.width * lerp(1.0, 1.03, prog(u, 0, sh['d'])); ph = ph.resize((round(ph.width * s), round(ph.height * s)), Image.LANCZOS)
    x, y = (W - ph.width) // 2, 1010 - ph.height // 2; sd = Image.new('L', (W, H), 0); ImageDraw.Draw(sd).rounded_rectangle([x + 10, y + 26, x + ph.width + 10, y + ph.height + 26], 24, fill=150)
    bg.paste((0, 0, 0), (0, 0), sd.filter(ImageFilter.GaussianBlur(30)))
    m = Image.new('L', ph.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, ph.width - 1, ph.height - 1], 22, fill=255); bg.paste(ph, (x, y), m)
    p = eo3(prog(u, .15, .6)); d = ImageDraw.Draw(bg)
    if F_CJK and sh.get('name_jp'):
        d.text((W / 2, 420 + 20 * (1 - p)), sh['name_jp'], font=font(F_CJK, 96), fill=(255, 255, 255, int(255 * p)), anchor='mm')
        d.text((W / 2, 530 + 20 * (1 - p)), sh['name_en'], font=font(F_SANS, 54), fill=(240, 240, 240, int(255 * p)), anchor='mm')
    else:                                                      # no CJK font: romaji name only, larger
        d.text((W / 2, 470 + 20 * (1 - p)), sh['name_en'], font=font(F_SANSB, 84), fill=(255, 255, 255, int(255 * p)), anchor='mm')
    return bg.convert('RGB')

def shot_end(sh, u):
    im = src(sh.get('img', END_CARD)).convert('RGB'); p = eo3(prog(u, 0, .5)); sc = lerp(1.06, 1, p) * (1 + .02 * prog(u, .5, sh['d']))
    w_, h_ = round(W * sc), round(H * sc); im = im.resize((w_, h_), Image.LANCZOS).crop(((w_ - W) // 2, (h_ - H) // 2, (w_ - W) // 2 + W, (h_ - H) // 2 + H))
    return Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), im, p)

SHOT = {'kb': shot_kb, 'film': shot_film, 'split': shot_split, 'person': shot_person, 'end': shot_end}

# ---------------- timeline ----------------
@functools.lru_cache(None)
def shots():
    out = []; t = 0
    for si, sc in enumerate(CFG['scenes']):
        rem = sc['dur']; lst = sc['shots']
        for j, sh in enumerate(lst):
            sh = dict(sh); d = sh.get('d') if j < len(lst) - 1 else rem; d = d or rem / (len(lst) - j)
            sh['d'] = d; sh['t0'] = t; sh['scene'] = si; out.append(sh); t += d; rem -= d
    return out

def total(): return sum(s['dur'] for s in CFG['scenes'])
def scene_at(t):
    a = 0
    for sc in CFG['scenes']:
        if t < a + sc['dur']: return sc, t - a
        a += sc['dur']
    return CFG['scenes'][-1], t - (a - CFG['scenes'][-1]['dur'])

def raw(sh, t): return SHOT[sh.get('type', 'kb')](sh, clamp(t - sh['t0'], 0, sh['d'] + XF))

@functools.lru_cache(maxsize=64)
def shot_theme(i):
    """dark text/logo when the shot is bright behind them"""
    sh = shots()[i]; f = raw(sh, sh['t0'] + .01)
    return lum(f, (0, 1450, W, 1640)) > 165, lum(f, (40, 70, 300, 200)) > 165

def frame(t):
    S = shots(); i = max(k for k, s in enumerate(S) if s['t0'] <= t + 1e-6); sh = S[i]
    c = raw(sh, t)
    if i + 1 < len(S) and t > S[i + 1]['t0'] - XF / 2 and S[i + 1].get('type') != 'end' and sh.get('type') != 'end':
        pass
    # blur dissolve around each boundary (centered on the cut)
    for j in (i, i + 1):
        if 0 < j < len(S):
            b = S[j]['t0']
            if abs(t - b) < XF / 2:
                p = (t - (b - XF / 2)) / XF; A = raw(S[j - 1], t); B = raw(S[j], t); r = 14 * math.sin(math.pi * p)
                if S[j].get('type') == 'end': A = Image.blend(A, Image.new('RGB', A.size), p); c = A if p < .5 else B
                else:
                    if r > .5: A, B = A.filter(ImageFilter.GaussianBlur(r)), B.filter(ImageFilter.GaussianBlur(r))
                    c = Image.blend(A, B, eio(p))
                break
    c = c.convert('RGBA')
    if sh.get('type') == 'end': return c.convert('RGB')
    sc, u = scene_at(t); dark_cap, dark_logo = shot_theme(i)
    if sh.get('title'): draw_title(c, sh['title'], t - sh['t0'])
    c.alpha_composite(vignette()) if not dark_cap else None
    c.alpha_composite(grain(int(t * FPS) % 6))
    if not sh.get('no_logo'): c.alpha_composite(logo_img(dark_logo), (56, 96))
    for pl in CFG.get('pills', []):
        p = prog(t, pl['at'], pl['at'] + .35) * (1 - prog(t, pl['at'] + pl.get('hold', 1.6), pl['at'] + pl.get('hold', 1.6) + .3))
        put_pill(c, pl['text'], W / 2, pl.get('y', 1440), p, pl.get('size', 30))
    cp = caption_at(sc, u)
    if cp:
        im, pad = cap_img(cp[0], dark_cap); a = eo3(prog(u, cp[1], cp[1] + .12))
        if a < 1: im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a)))
        c.alpha_composite(im, (int(W / 2 - im.width / 2), int(CAP_Y - im.height / 2 + 6 * (1 - a))))
    return c.convert('RGB')

# ---------------- audio ----------------
def sfx_events():
    ev = []
    for k, s in enumerate(shots()):
        if k: ev.append((s['t0'] - .2, 'whoosh', .28))
        if s.get('sfx'): ev += [(s['t0'] + a, n, g) for a, n, g in s['sfx']]
        if s.get('title'): ev.append((s['t0'] + s['title'].get('at', .3), 'typing', .35))
    ev += [(p['at'], 'pop', .5) for p in CFG.get('pills', [])]
    return ev

def build_audio(path):
    SR = 48000; L = total(); mix = np.zeros((int(L * SR) + SR, 2)); cache = {}; vo = CFG.get('voiceover')
    for t, n, g in sfx_events():
        if n not in cache:
            with wave.open(os.path.join(BASE, CFG.get('sfx_dir', 'sfx'), n + '.wav')) as w: cache[n] = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768
        i = int(max(0, t) * SR); seg = cache[n][:len(mix) - i]; mix[i:i + len(seg)] += seg * g * (.55 if vo else 1)
    if vo:
        tmp = path + '.vo.wav'; subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', ap(vo), '-ar', str(SR), '-ac', '2', tmp], check=True)
        with wave.open(tmp) as w: v = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768
        n = min(len(v), len(mix)); mix[:n] += v[:n]; os.remove(tmp)
    mix = np.tanh(mix[:int(L * SR)] * 1.1) * .9
    with wave.open(path, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

def _part(a):
    f0, f1, path, cfgp = a; load(cfgp)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for f in range(f0, f1): p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()

def render_range(out, f0, f1, cfgp):
    ensure_sfx()
    n = f1 - f0; k = max(1, min(mp.cpu_count(), math.ceil(n / FPS))); step = math.ceil(n / k); d = out + '.parts'; os.makedirs(d, exist_ok=True)
    parts = [(i, min(f1, i + step), os.path.join(d, f'p{j}.mp4'), cfgp) for j, i in enumerate(range(f0, f1, step))]
    with mp.Pool(len(parts)) as pool: pool.map(_part, parts)
    open(os.path.join(d, 'l.txt'), 'w').writelines(f"file '{os.path.basename(p[2])}'\n" for p in parts); build_audio(os.path.join(d, 'a.wav'))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(d, 'l.txt'), '-ss', f'{f0 / FPS:.3f}', '-t', f'{n / FPS:.3f}',
                    '-i', os.path.join(d, 'a.wav'), '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', out], check=True)
    shutil.rmtree(d)

def clip(out, spec, cfgp):
    if ':' in spec: a, b = spec.split(':'); t0, t1 = float(a or 0), float(b or total())
    else:
        a, _, b = spec.partition('-'); i, j = int(a), int(b or a); st = [0]
        for sc in CFG['scenes']: st.append(st[-1] + sc['dur'])
        t0, t1 = st[i - 1], st[j]
    render_range(out, int(round(t0 * FPS)), int(round(min(t1, total()) * FPS)), cfgp); print('clip', out, f'{t0:.1f}-{t1:.1f}s')

def ensure_sfx():
    """Generate the sound-effect WAVs with make_sfx.py (next to this script) if the sfx folder is missing any."""
    d = os.path.join(BASE, CFG.get('sfx_dir', 'sfx')); need = {e[1] for e in sfx_events()}
    if all(os.path.exists(os.path.join(d, n + '.wav')) for n in need): return
    gen = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'make_sfx.py')
    if os.path.exists(gen):
        os.makedirs(d, exist_ok=True); subprocess.run([sys.executable, gen], cwd=d, check=True, stdout=subprocess.DEVNULL); print('generated sound effects in', d)

def check():
    ensure_sfx(); errs, warns = [], []; L = total(); sc_ = CFG['scenes']
    if not MIN_LEN <= L <= MAX_LEN: errs.append(f'Length {L:.1f}s is outside {MIN_LEN:.0f}-{MAX_LEN:.0f}s')
    if not sc_ or sc_[-1]['shots'][-1].get('type') != 'end': errs.append('The last scene must end on the end card (shot type "end")')
    names = {CFG['logo']}
    for s_ in shots():
        for k in ('img', 'bg'):
            if s_.get(k): names.add(s_[k])
        for k in ('top', 'bottom'):
            if s_.get(k): names.add(s_[k]['img'])
        if s_.get('type') == 'end' and not s_.get('img'): names.add(END_CARD)
    for n in sorted(names):
        if not os.path.exists(ap(n)): errs.append(f'Missing asset: {n}'); continue
        im = Image.open(ap(n))
        if n == END_CARD or n.startswith('23_'):
            if im.height < H: warns.append(f'End card is {im.width}x{im.height}; a {W}x{H} export is sharper')
        elif 'logo' not in n and 'avatar' not in n and im.height < 1200: warns.append(f'{n} is only {im.height}px tall: macro/close-up shots will look soft (want >=2500px for macros)')
    if CFG.get('voiceover') and not os.path.exists(ap(CFG['voiceover'])): errs.append(f'Voiceover file not found: {CFG["voiceover"]}')
    miss = [n for n in {e[1] for e in sfx_events()} if not os.path.exists(os.path.join(BASE, CFG.get('sfx_dir', 'sfx'), n + '.wav'))]
    if miss: errs.append(f'Missing sound effects: {", ".join(sorted(miss))} (run make_sfx.py inside the sfx folder)')
    if any('STOCK' in p['text'].upper() for p in CFG.get('pills', [])) and not CFG.get('stock_confirmed'):
        errs.append('An IN STOCK pill exists but "stock_confirmed" is not true')
    f = font(F_SANS, 36)
    for i, s_ in enumerate(sc_):
        if not s_.get('vo'): warns.append(f'Scene {i + 1} has no voiceover line')
        for w_ in CFG.get('forbidden_words', ['TGA']):
            if re.search(r'\b' + re.escape(w_) + r'\b', s_.get('vo', '') + ' ' + s_.get('caption', '')): errs.append(f'Scene {i + 1} mentions forbidden word "{w_}"')
        if s_.get('caption') and not s_.get('no_caption'):
            for p in chunks(s_['caption']):
                if f.getlength(p) > 940: errs.append(f'Scene {i + 1} caption chunk too long for one line: "{p}"')
        if s_['dur'] > 8: warns.append(f'Scene {i + 1} is {s_["dur"]:.1f}s: split it into more shots (reference cuts every 1.5-3s)')
    if not F_CJK and any(s_.get('type') == 'person' and s_.get('name_jp') for s_ in shots()):
        warns.append('No CJK font found: the artist name shows in romaji only (add NotoSansCJKsub-Bold.otf to engine/fonts)')
    for k, s_ in enumerate(shots()):
        if s_['d'] < .9 and s_.get('type') != 'end': warns.append(f'Shot {k + 1} is only {s_["d"]:.2f}s (dissolves are {XF}s)')
        if s_['d'] > 5.5 and s_.get('type') != 'end': warns.append(f'Shot {k + 1} holds {s_["d"]:.1f}s: add a cut or a second camera key')
    print(f'Length: {L:.1f}s  ({len(sc_)} scenes, {len(shots())} shots)')
    for e in dict.fromkeys(errs): print('ERROR  ', e)
    for w_ in dict.fromkeys(warns): print('WARN   ', w_)
    print('OK — no errors' if not errs else f'{len(errs)} error(s)'); return not errs

def script(out):
    fm = lambda x: f'{int(x // 60)}:{x % 60:04.1f}'; t = 0
    L = [f"# {CFG['title']}\n", f'Length {total():.1f}s · 9:16 · Fine Card style · Bahasa VO + EN captions\n',
         '| Time | Beat | Voiceover (Bahasa) | Caption (EN) | Visual |', '|---|---|---|---|---|']
    for sc in CFG['scenes']:
        L.append(f"| {fm(t)}–{fm(t + sc['dur'])} | {sc['beat']} | {sc['vo']} | {sc['caption']} | {sc.get('visual', '')} |"); t += sc['dur']
    if CFG.get('post_caption'): L += ['', '## Post caption', '', CFG['post_caption'].replace('@[Kard Avenue IG]', CFG.get('ig_handle') or '@[Kard Avenue IG]')]
    open(out, 'w').write('\n'.join(L) + '\n'); print('script', out)

def render(out, cfgp):
    render_range(out, 0, int(round(total() * FPS)), cfgp); print('rendered', out, f'{total():.1f}s')

def stills(out):
    S = shots(); cols = 8; tw, th = 225, 400; rows = math.ceil(len(S) / cols)
    sh_ = Image.new('RGB', (cols * tw, rows * (th + 22)), (14, 14, 14)); d = ImageDraw.Draw(sh_)
    for k, s in enumerate(S):
        t = s['t0'] + s['d'] * .7; x, y = (k % cols) * tw, (k // cols) * (th + 22)
        sh_.paste(frame(t).resize((tw, th)), (x, y)); d.text((x + 4, y + th + 3), f"{s['scene'] + 1}.{k + 1} {s.get('type', 'kb')} @{t:.1f}", font=font(F_SANS, 14), fill='white')
    sh_.save(out); print('stills', out, len(S), 'shots')

def page(outdir, video):
    os.makedirs(outdir, exist_ok=True); rows = []; t = 0
    for sc in CFG['scenes']:
        rows.append({'t': round(t, 2), 'e': round(t + sc['dur'], 2), 'title': sc['beat'], 'vo': sc['vo'], 'cap': sc['caption'],
                     'vis': sc.get('visual', ''), 'sfx': 'soft whoosh on cuts' + (', ' + sc['sfx_note'] if sc.get('sfx_note') else '')}); t += sc['dur']
    json.dump({'title': CFG['title'], 'length': round(total(), 1), 'video': 'video.mp4', 'scenes': rows, 'open': CFG.get('open_decisions', [])},
              open(os.path.join(outdir, 'scenes.json'), 'w'), ensure_ascii=False, indent=1)
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'editor_template.html'), os.path.join(outdir, 'index.html'))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '128k', os.path.join(outdir, 'video.mp4')], check=True); print('page', outdir)

def load(p):
    global CFG, BASE
    CFG = json.load(open(p)); BASE = os.path.dirname(os.path.abspath(p)); shots.cache_clear(); shot_theme.cache_clear()

if __name__ == '__main__':
    cfgp, cmd = sys.argv[1], sys.argv[2]; load(cfgp)
    if cmd == 'stills': stills(sys.argv[3])
    elif cmd == 'render': render(sys.argv[3], cfgp)
    elif cmd == 'page': page(sys.argv[3], sys.argv[4])
    elif cmd == 'frame': frame(float(sys.argv[3])).save(sys.argv[4])
    elif cmd == 'check': sys.exit(0 if check() else 1)
    elif cmd == 'clip': clip(sys.argv[3], sys.argv[4], cfgp)
    elif cmd == 'script': script(sys.argv[3])
    else: print(__doc__)
