#!/usr/bin/env python3
"""
Kard Avenue Reel engine v2.1 — config-driven.

A new video = one JSON config (script + images + scene types). No code edits.

Usage
  python3 kard_reel.py CONFIG.json check            # lint: length, assets, overlaps, caption rules
  python3 kard_reel.py CONFIG.json stills OUT.png   # contact sheet, key moments of every scene (check-in 2)
  python3 kard_reel.py CONFIG.json render OUT.mp4   # full video (uses all CPU cores)
  python3 kard_reel.py CONFIG.json clip OUT.mp4 SPEC  # partial render for reviewing a fix. SPEC = 6 (scene 6),
                                                      # 5-7 (scenes 5 to 7) or 12.5:20 (seconds). Audio included.
  python3 kard_reel.py CONFIG.json cover OUT.png    # Reels cover frame
  python3 kard_reel.py CONFIG.json script OUT.md    # script doc table (captions = config, always in sync)
  python3 kard_reel.py CONFIG.json page OUTDIR [VIDEO.mp4]  # editor page (index.html + scenes.json + video)
  python3 kard_reel.py CONFIG.json frame T OUT.png  # one frame at T seconds
  python3 kard_reel.py CONFIG.json caption [OUT.txt]  # final Instagram post caption (IG handle filled in)

Config keys used by `check`: "stock_confirmed": true (required when a cta_product scene exists),
"ig_handle": "@yourhandle" (fills @[Kard Avenue IG] in the post caption).
Fonts: Telegraf-UltraBold/Regular.otf (brand font for all video text), Inter-Bold.otf (stills labels) and DejaVuSansMono-Bold.ttf in fonts/ next to this script (bundled in the package).

Requires: Python 3, Pillow, numpy, ffmpeg. Fonts: Inter (Black/ExtraBold/Bold), DejaVu Sans Mono Bold.
SFX wavs come from kard-reel-sfx.py (set "sfx_dir" in the config).

Scene types (see the scene functions' docstrings for fields):
  hook_mystery, hero_stamp, product_intro, card_grid, card_lineup, reveal_zoom,
  artist, featured_cards, stat_chart, cta_product, end_card
"""
import math, os, sys, json, subprocess, functools, wave, re, shutil, multiprocessing as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ======================================================================
# House style (Kard Avenue playbook) — change here, applies to every video
# ======================================================================
W, H, FPS = 1080, 1920, 30
OY = 60                      # content shifted down to balance frame with captions
CAPTION_Y = 1565             # caption block centre
CAPTION_MAXW = 900
SAFE_BOTTOM = 1680           # Instagram UI covers below this
SIDE_MARGIN = 30
LOGO_POS, LOGO_W, LOGO_ALPHA = (60, 120), 300, .85
MIN_LEN, MAX_LEN = 45.0, 60.0
YELLOW, PINK, RED, GREEN = (255, 216, 77), (255, 92, 170), (235, 45, 60), (40, 200, 110)
def _find_font(name, *system_dirs):
    """Bundled fonts/ folder next to this script first, then common system locations."""
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (os.path.join(here, 'fonts'), *system_dirs):
        p = os.path.join(d, name)
        if os.path.exists(p): return p
    sys.exit(f'Font not found: {name}. Put it in {os.path.join(here, "fonts")}')
_INTER = ('/usr/share/fonts/opentype/inter', '/usr/share/fonts/truetype/inter', '/Library/Fonts', os.path.expanduser('~/Library/Fonts'), 'C:/Windows/Fonts')
_DEJAVU = ('/usr/share/fonts/truetype/dejavu', '/Library/Fonts', os.path.expanduser('~/Library/Fonts'), 'C:/Windows/Fonts')
# Brand font: Telegraf (bundled). Inter is kept only for the internal stills-sheet labels (needs ✓/✗ glyphs).
F_BLACK = F_XB = F_B = _find_font('Telegraf-UltraBold.otf')
F_REG = _find_font('Telegraf-Regular.otf')
F_UI = _find_font('Inter-Bold.otf', *_INTER)
F_MONO = _find_font('DejaVuSansMono-Bold.ttf', *_DEJAVU)
IG_PLACEHOLDER = '@[Kard Avenue IG]'

CFG, BASE = None, None
FRAME_BOXES = []             # filled while drawing a frame (used by `check`)

@functools.lru_cache(None)
def font(path, size): return ImageFont.truetype(path, size)

# ---------------- easing ----------------
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def prog(t, t0, t1): return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)
def eo3(x): return 1 - (1 - x) ** 3
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eback(x, s=1.70158):
    x -= 1; return x * x * ((s + 1) * x + s) + 1
def lerp(a, b, x): return a + (b - a) * x

# ---------------- assets ----------------
def apath(name): return name if os.path.isabs(name) else os.path.join(BASE, CFG.get('assets_dir', 'assets'), name)

def round_card(im):
    im = im.convert('RGBA'); w, h = im.size; r = int(w * .045)
    m = Image.new('L', (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], r * 2, fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    im.putalpha(Image.fromarray(np.minimum(np.asarray(im.split()[3]), np.asarray(m))))
    return im

@functools.lru_cache(None)
def img(name, card=True):
    """Load an asset. card=True rounds corners like a TCG card."""
    if name.startswith('mystery:'):
        return make_mystery(img(name[8:]))
    im = Image.open(apath(name))
    return round_card(im) if card else im.convert('RGBA')

def make_mystery(im):
    a = im.split()[3]; art = np.asarray(im.convert('RGB')).astype(float)
    dark = np.full_like(art, (18, 20, 44)) * .86 + art * .14
    m = Image.fromarray(dark.astype(np.uint8)).convert('RGBA'); m.putalpha(a)
    pad = 40; g = Image.new('L', (im.width + pad * 2, im.height + pad * 2), 0); g.paste(a, (pad, pad))
    g = g.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14))
    out = Image.new('RGBA', g.size, (140, 225, 255, 0)); out.putalpha(g.point(lambda v: int(v * .9)))
    out.alpha_composite(m, (pad, pad)); return out

@functools.lru_cache(maxsize=600)
def scaled(name, h, angle=0, card=True):
    im = img(name, card); w = max(1, round(im.width * h / im.height))
    s = im.resize((w, h), Image.LANCZOS)
    return s.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else s

@functools.lru_cache(maxsize=600)
def shadow_of(name, h, angle=0, card=True):
    s = scaled(name, h, angle, card); pad = 60
    a = Image.new('L', (s.width + pad * 2, s.height + pad * 2), 0); a.paste(s.split()[3], (pad, pad))
    a = a.filter(ImageFilter.GaussianBlur(26))
    sh = Image.new('RGBA', a.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: int(v * .65)))
    return sh, pad

def paste_safe(canvas, im, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(canvas.width, x + im.width), min(canvas.height, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    canvas.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def with_alpha(im, a):
    if a >= .999: return im
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a))); return im

def put(c, name, cx, cy, h, angle=0, alpha=1., shadow=True, sweep=None, crop_frac=None, card=True, role='card', bleed=False):
    """Paste an image centred at (cx, cy+OY) with height h. Records its box for `check`."""
    if alpha <= .01 or h < 4: return
    h = int(round(h / 2) * 2); angle = round(angle * 2) / 2; cy += OY
    s = scaled(name, h, angle, card)
    if sweep is not None and 0 < sweep < 1:
        s = s.copy(); band = Image.new('L', s.size, 0); bd = ImageDraw.Draw(band)
        x = lerp(-s.width * .6, s.width * 1.6, sweep)
        bd.polygon([(x - 90, 0), (x + 30, 0), (x - 90 + s.height * .45, s.height), (x - 210 + s.height * .45, s.height)], fill=150)
        band = band.filter(ImageFilter.GaussianBlur(25))
        band = Image.fromarray(np.minimum(np.asarray(band), np.asarray(s.split()[3])).astype(np.uint8))
        wht = Image.new('RGBA', s.size, (255, 255, 255, 0)); wht.putalpha(band); s.alpha_composite(wht)
    if crop_frac is not None:
        s = s.copy(); a = np.asarray(s.split()[3]).copy(); a[:, int(s.width * crop_frac):] = 0; s.putalpha(Image.fromarray(a))
    s = with_alpha(s, alpha)
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    if shadow:
        sh, pad = shadow_of(name, h, angle, card)
        paste_safe(c, with_alpha(sh, alpha), x - pad + 10, y - pad + 24)
    paste_safe(c, s, x, y)
    if alpha > .5: FRAME_BOXES.append((role, x, y, x + s.width, y + s.height, h, bleed))

@functools.lru_cache(None)
def text_img(text, path, size, fill=(255, 255, 255), stroke=0):
    f = font(path, size); bb = f.getbbox(text, stroke_width=stroke)
    im = Image.new('RGBA', (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - bb[0], 2 - bb[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(10, 8, 20))
    return im

def put_text(c, text, cx, cy, path=F_XB, size=48, fill=(255, 255, 255), stroke=0, alpha=1., scale=1., record=True):
    im = text_img(text, path, size, fill, stroke)
    if scale != 1: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    im = with_alpha(im, alpha); x, y = int(cx - im.width / 2), int(cy + OY - im.height / 2)
    paste_safe(c, im, x, y)
    if record and alpha > .5: FRAME_BOXES.append(('text', x, y, x + im.width, y + im.height, 0, False))

@functools.lru_cache(None)
def chip_img(text, bg=(255, 255, 255), fg=(15, 12, 30), size=40):
    f = font(F_BLACK, size); tw = f.getlength(text)
    im = Image.new('RGBA', (int(tw + size * 1.2), int(size * 1.7)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], im.height // 2, fill=bg)
    d.text((im.width / 2, im.height / 2), text, font=f, fill=fg, anchor='mm'); return im

def put_chip(c, text, cx, cy, p, **kw):
    if p <= 0: return
    im = chip_img(text, **kw); s = lerp(.4, 1, eback(p))
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    x, y = int(cx - im.width / 2), int(cy + OY - im.height / 2); paste_safe(c, im, x, y)
    if p >= 1: FRAME_BOXES.append(('text', x, y, x + im.width, y + im.height, 0, False))

@functools.lru_cache(None)
def stamp_img(kind, text=''):
    if kind in ('x', 'ok'):
        sz = 230; im = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); d = ImageDraw.Draw(im); col = RED if kind == 'x' else GREEN
        d.ellipse([8, 8, sz - 8, sz - 8], outline=col + (255,), width=16, fill=col + (60,))
        if kind == 'x':
            d.line([(70, 70), (sz - 70, sz - 70)], fill=col + (255,), width=26); d.line([(sz - 70, 70), (70, sz - 70)], fill=col + (255,), width=26)
        else:
            d.line([(58, 120), (100, 165), (175, 70)], fill=col + (255,), width=26, joint='curve')
        return im
    f = font(F_BLACK, 74); tw = f.getlength(text)
    im = Image.new('RGBA', (int(tw + 80), 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, im.width - 5, im.height - 5], 18, outline=RED + (255,), width=10, fill=(255, 255, 255, 235))
    d.text((im.width / 2, im.height / 2), text, font=f, fill=RED, anchor='mm'); return im

def put_stamp(c, kind, cx, cy, u, t0, text='', angle=-12, size=1., label=None):
    p = prog(u, t0, t0 + .18)
    if p <= 0: return
    im = stamp_img(kind, text); s = lerp(2., 1., eo3(p)) * size
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS).rotate(angle, expand=True, resample=Image.BICUBIC)
    paste_safe(c, with_alpha(im, p), int(cx - im.width / 2), int(cy + OY - im.height / 2))
    if label: put_text(c, label, cx, cy + 150 * size, F_BLACK, 46, stroke=6, record=False)

def flash(c, u, t0, dur=.3):
    p = prog(u, t0, t0 + dur)
    if 0 < p < 1: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * (1 - p) ** 2))))

def dim(c, a):
    if a > 0: c.alpha_composite(Image.new('RGBA', (W, H), (8, 6, 16, int(255 * a))))

# ---------------- background / burst / ? ----------------
@functools.lru_cache(None)
def bg_base():
    bw, bh = W + 240, H + 240; yy, xx = np.mgrid[0:bh, 0:bw]
    r = np.clip(np.hypot((xx - bw * .5) / bw, (yy - bh * .38) / bh) * 1.6, 0, 1)
    base = np.stack([lerp(42, 10, r), lerp(24, 8, r), lerp(70, 22, r)], -1)
    im = Image.fromarray(base.astype(np.uint8)).convert('RGBA')
    bl = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl); rng = np.random.default_rng(3)
    for _ in range(14):
        cx, cy, rr = rng.uniform(0, bw), rng.uniform(0, bh), rng.uniform(60, 220)
        col = [PINK, (90, 160, 255), (180, 120, 255)][rng.integers(3)]
        bd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col + (int(rng.uniform(25, 60)),))
    im.alpha_composite(bl.filter(ImageFilter.GaussianBlur(70))); return im

@functools.lru_cache(None)
def grain(i):
    g = np.random.default_rng(11 + i).integers(0, 255, (H // 2, W // 2), dtype=np.uint8)
    lay = Image.new('RGBA', (W, H), (255, 255, 255, 0)); lay.putalpha(Image.fromarray(g).resize((W, H), Image.NEAREST).point(lambda v: int(v * .06)))
    return lay

def background(t):
    ox, oy = 120 + 60 * math.sin(t * .25), 120 + 70 * math.cos(t * .19)
    return bg_base().crop((int(ox), int(oy), int(ox) + W, int(oy) + H)).copy()

@functools.lru_cache(None)
def burst_img():
    S = 1600; im = Image.new('RGBA', (S, S), (200, 30, 55, 255)); d = ImageDraw.Draw(im); c = S / 2; n = 40
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = a0 + 2 * math.pi / n * .55
        d.polygon([(c, c), (c + S * math.cos(a0), c + S * math.sin(a0)), (c + S * math.cos(a1), c + S * math.sin(a1))],
                  fill=(120, 210, 255, 255) if k % 2 == 0 else (235, 70, 95, 255))
    im = im.filter(ImageFilter.GaussianBlur(3)); yy, xx = np.mgrid[0:S, 0:S]; r = np.hypot(xx - c, yy - c) / (S / 2)
    g = Image.new('RGBA', (S, S), (255, 255, 255, 0)); g.putalpha(Image.fromarray((np.clip(1 - r * 2.2, 0, 1) ** 1.6 * 255).astype(np.uint8)))
    im.alpha_composite(g)
    v = Image.new('RGBA', (S, S), (20, 10, 30, 0)); v.putalpha(Image.fromarray((np.clip((r - .42) * 1.9, 0, 1) * 170).astype(np.uint8)))
    im.alpha_composite(v); return im

def burst(c, t, alpha, cy=760):
    if alpha <= .01: return
    rot = burst_img().rotate(t * 6, resample=Image.BILINEAR); S = rot.width; x0 = S / 2 - 270; y0 = S / 2 - cy / 2
    lay = rot.crop((int(x0), int(y0), int(x0) + W // 2, int(y0) + H // 2)).resize((W, H), Image.BILINEAR)
    c.alpha_composite(with_alpha(lay, alpha))

@functools.lru_cache(None)
def qmark():
    f = font(F_BLACK, 560); bb = f.getbbox('?'); im = Image.new('RGBA', (bb[2] - bb[0] + 120, bb[3] - bb[1] + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); ox, oy = 40 - bb[0], 40 - bb[1]
    for k in range(26, 0, -2): d.text((ox + k, oy + k), '?', font=f, fill=(24, 70, 160), stroke_width=22, stroke_fill=(24, 70, 160))
    d.text((ox, oy), '?', font=f, fill=(255, 205, 30), stroke_width=22, stroke_fill=(50, 110, 210)); d.text((ox, oy), '?', font=f, fill=(255, 216, 60))
    return im

def put_q(c, cx, cy, s, angle=0):
    if s <= .02: return
    im = qmark().resize((max(1, int(qmark().width * s)), max(1, int(qmark().height * s))), Image.LANCZOS)
    if angle: im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    paste_safe(c, im, int(cx - im.width / 2), int(cy + OY - im.height / 2))

def logo(c):
    lg = img(CFG.get('logo', '07_kard_logo.png'), card=False)
    lg = lg.resize((LOGO_W, int(lg.height * LOGO_W / lg.width)), Image.LANCZOS)
    c.alpha_composite(with_alpha(lg, LOGO_ALPHA), LOGO_POS)
    return LOGO_POS[1] + lg.height

def heading_y(cards_top_screen):
    """Midpoint between logo bottom and the top of the cards (screen coords) -> put_text y (minus OY)."""
    logo_bottom = LOGO_POS[1] + int(img(CFG.get('logo', '07_kard_logo.png'), card=False).height * LOGO_W / img(CFG.get('logo', '07_kard_logo.png'), card=False).width)
    return (logo_bottom + cards_top_screen) / 2 - OY

# ======================================================================
# Scene templates. Each: draw(c, u, d, s) with local time u in [0, d).
# sfx(d, s) -> list of (time, name, gain). Times are local seconds.
# keys(d, s) -> list of (local time, label): the moments `stills` shows.
# ======================================================================
def card_h(name, h): im = img(name); return h, h * im.width / im.height

# 1 ---------------------------------------------------------------- hook_mystery
def hook_mystery(c, u, d, s):
    """known: [{img,label}] (2-4 versions you CAN'T get it in), hero: img revealed at the end."""
    n = len(s['known']); R = s.get('reveal_at', d - .9); tm = .2 + .6 * n + .1
    burst(c, u, 1 - prog(u, d - .5, d))
    fall = eio(prog(u, R, R + .6)); xs = {2: [300, 780], 3: [215, 540, 865], 4: [160, 405, 675, 920]}[n]
    hk = {2: 520, 3: 440, 4: 340}[n]
    for i, k in enumerate(s['known']):
        ts = .2 + .6 * i; pr = prog(u, ts, ts + .35)
        if pr <= 0 or fall >= 1: continue
        p = eback(pr); cy = lerp(1950, 540, min(p, 1.06)) + fall * 900; ang = (6, 0, -6, -8)[i] if n == 3 else 0
        put(c, k['img'], xs[i], cy, hk, angle=ang * min(p, 1), alpha=1 - fall)
        if fall < .3: put_stamp(c, 'x', xs[i], cy, u, ts + .35, size=.8, label=k['label'])
    if u < R:
        pr = prog(u, tm, tm + .4)
        if pr > 0:
            put(c, 'mystery:' + s['hero'], 540, lerp(1250, 1015, eo3(pr)), 560 * eback(pr) * 1.11, angle=2.5 * math.sin(u * 5), shadow=False)
            put_q(c, 780, 800, eback(prog(u, tm + .25, tm + .6)) * .36 * (1 + .06 * math.sin(u * 7)), angle=-12 + 6 * math.sin(u * 3))
    else:
        e = eback(prog(u, R, R + .5))
        put(c, s['hero'], 540, lerp(1015, 760, eio(prog(u, R, R + .5))), lerp(560, 1000, e), sweep=prog(u, R + .2, R + 1.))
    flash(c, u, 0, .25); flash(c, u, R, .35)

def hook_mystery_sfx(d, s):
    n = len(s['known']); R = s.get('reveal_at', d - .9); tm = .2 + .6 * n + .1
    ev = [(0, 'whoosh', .7)] + [(.2 + .6 * i, 'flick', .8) for i in range(n)] + [(.55 + .6 * i, 'stamp', 1.) for i in range(n)]
    return ev + [(tm, 'whoosh', .7), (tm + .25, 'pop', 1.), (max(0, R - 2.5), 'riser', .5), (R, 'impact', 1.), (R + .2, 'shimmer', .7)]

def hook_mystery_keys(d, s):
    n = len(s['known']); R = s.get('reveal_at', d - .9)
    return [(.2 + .6 * (n - 1) + .6, 'versions ✗'), (R - .25, 'mystery'), (R + .85, 'reveal')]

# 2 ---------------------------------------------------------------- hero_stamp
def hero_stamp(c, u, d, s):
    """img + stamp {kind: ok|x, label, at}. Card holds big with a slow push-in."""
    put(c, s['img'], 540, 760, 1000 + 30 * prog(u, 0, d), sweep=prog(u, d * .5, d * .5 + .8))
    st = s.get('stamp')
    if st: put_stamp(c, st.get('kind', 'ok'), 860, 330, u, st.get('at', .3), angle=10, label=st.get('label'))

def hero_stamp_sfx(d, s): return [(s.get('stamp', {}).get('at', .3), 'ding', .8), (d * .5, 'shimmer', .5)]
def hero_stamp_keys(d, s): return [(d * .8, 'card + stamp')]

# 3 ---------------------------------------------------------------- product_intro
def product_intro(c, u, d, s):
    """box, pack (optional), date_text (typed), subtitle."""
    pin = eo3(prog(u, 0, .5)); out = eio(prog(u, d - .35, d)); x = lerp(1400, 420 if s.get('pack') else 540, pin)
    put(c, s['box'], x, lerp(640, 560, out), lerp(760, 300, out), angle=lerp(-25, -5, pin) + 3 * math.sin(u * 2), alpha=1 - out, sweep=prog(u, .6, 1.5), card=False)
    if s.get('pack') and prog(u, .35, .75) > 0:
        pp = eback(prog(u, .35, .75))
        put(c, s['pack'], lerp(-300, 830, min(pp, 1.05)), lerp(700, 560, out), lerp(560, 200, out), angle=lerp(-30, 12, pp), alpha=1 - out, card=False)
    dt = s.get('date_text')
    if dt:
        n = int(len(dt) * prog(u, .8, 1.9))
        if n: put_text(c, dt[:n] + ('_' if n < len(dt) and int(u * 6) % 2 else ''), 540, 1120, F_MONO, 110, fill=YELLOW, stroke=6, alpha=1 - out)
    if s.get('subtitle'): put_text(c, s['subtitle'], 540, 1210, F_XB, 34, alpha=(1 - out) * prog(u, 1., 1.4))

def product_intro_sfx(d, s): return [(0, 'whoosh', .9), (.6, 'shimmer', .5)] + ([(.8, 'typing', .7)] if s.get('date_text') else [])
def product_intro_keys(d, s): return [(min(2.2, d - .45), 'box + date')]

# 4 ---------------------------------------------------------------- card_grid
def card_grid(c, u, d, s):
    """cards: up to 9 images, 3 per row, fly in; collapses into `keep` (index) at the end if set."""
    cards = s['cards']; rows = math.ceil(len(cards) / 3); h = s.get('card_h', 360); gap = h * 1.04
    top = 760 - (rows - 1) * gap / 2; keep = s.get('keep'); co = eio(prog(u, d - .4, d)) if keep is not None else 0
    for i, name in enumerate(cards):
        pr = prog(u, .1 + i * .08, .45 + i * .08)
        if pr <= 0: continue
        p = eback(pr); col, row = i % 3, i // 3; n_in_row = min(3, len(cards) - row * 3)
        tx = 540 + (col - (n_in_row - 1) / 2) * 300; ty = top + row * gap
        tx, ty = lerp(tx, 540, co), lerp(ty, 760, co)
        put(c, name, lerp(540, tx, min(1, p)), lerp(2100, ty, min(1, p)), h, alpha=1 - co * (i != keep))

def card_grid_sfx(d, s): return [(.1 + i * .08, 'flick', .7) for i in range(len(s['cards']))] + ([(d - .4, 'whoosh', .6)] if s.get('keep') is not None else [])
def card_grid_keys(d, s):
    k = [(min(d - .5, .6 + len(s['cards']) * .08), 'full grid')]
    return k + ([(d - .05, 'collapse')] if s.get('keep') is not None else [])

# 5 ---------------------------------------------------------------- card_lineup
def card_lineup(c, u, d, s):
    """cards: [{img,label}] 2-3 shown fanned; heading (top); credit (under). riser: build into next scene."""
    cards = s['cards']; n = len(cards); h = s.get('card_h', 520)
    order = [0, 2, 1] if n == 3 else [0, 1]                               # middle card drawn last
    for j in order:
        k = cards[j]; x = {2: [330, 750], 3: [255, 540, 825]}[n][j]; a = {2: [5, -5], 3: [6, 0, -6]}[n][j]
        p = eo3(prog(u, j * .12, .6 + j * .12)); put(c, k['img'], x, lerp(2000, 790, p), h, angle=a)
        lt = .8 + j * (d - 1.6) / max(1, n)
        if k.get('label'): put_chip(c, k['label'], x, 790 + h / 2 + 50, prog(u, lt, lt + .25), size=28)
    if s.get('heading'): put_text(c, s['heading'], 540, heading_y(790 - h / 2 + OY), F_BLACK, 64, stroke=6, alpha=prog(u, .6, 1.))
    if s.get('credit'): put_text(c, s['credit'], 540, 790 + h / 2 + 130, F_B, 36, fill=(220, 220, 235), alpha=prog(u, 1., 1.5))

def card_lineup_sfx(d, s):
    n = len(s['cards']); ev = [(0, 'whoosh', .5)] + [(.8 + j * (d - 1.6) / max(1, n), 'pop', .8) for j in range(n)]
    return ev + ([(max(0, d - 2.5), 'riser', .7)] if s.get('riser') else [])

def card_lineup_keys(d, s): return [(d - .2, 'all labels')]

# 6 ---------------------------------------------------------------- reveal_zoom
def reveal_zoom(c, u, d, s):
    """img; wipe_from: [imgs] (optional lineup to wipe away); zoom: {fx, fy, tag} = spot on the card to zoom into."""
    wp = eio(prog(u, 0, .6)) if s.get('wipe_from') else 1
    if wp < 1:
        for x, a, name in zip([255, 825, 540], [6, -6, 0], s['wipe_from']): put(c, name, x, 790, 520, angle=a, alpha=1 - wp)
    zm = s.get('zoom'); z0 = s.get('zoom_at', max(1.6, d * .4)); z = eio(prog(u, z0, z0 + .55)) if zm else 0
    if z <= 0:
        put(c, s['img'], 540, 760, 1000, crop_frac=wp if wp < 1 else None, sweep=prog(u, .8, 1.7))
        if wp < 1:
            dd = ImageDraw.Draw(c); xw = 540 - 1000 * .7158 / 2 + 1000 * .7158 * wp; dd.rectangle([xw - 4, 260 + OY, xw + 4, 1260 + OY], fill=(255, 255, 255, 230))
        if zm:
            cp = eo3(prog(u, 1.0, 1.4)) * (1 - prog(u, z0 - .05, z0)); fx, fy = zm['fx'], zm['fy']
            if cp > 0:
                dd = ImageDraw.Draw(c); cx_, cy_ = 540 + (fx - .5) * 715.8, 760 + (fy - .5) * 1000 + OY; r = 95 * cp
                dd.ellipse([cx_ - r * 1.6, cy_ - r * .7, cx_ + r * 1.6, cy_ + r * .7], outline=RED, width=12)
                ap = eo3(prog(u, 1.3, 1.7))
                if ap > 0:
                    x0, y0 = cx_ + 460, cy_ + 110; x1, y1 = lerp(x0, cx_ + 180, ap), lerp(y0, cy_ + 25, ap)
                    dd.line([(x0, y0), (x1, y1)], fill=RED, width=18); ang = math.atan2(y1 - y0, x1 - x0)
                    for s_ in (2.6, -2.6): dd.line([(x1, y1), (x1 - 60 * math.cos(ang + s_ * .2), y1 - 60 * math.sin(ang + s_ * .2))], fill=RED, width=18)
    else:
        fx, fy = zm['fx'], zm['fy']; Hz = lerp(1000, zm.get('zoom_h', 3400), z)
        ox, oy = (fx - .5) * Hz * .7158, (fy - .5) * Hz
        px = lerp(540 + (fx - .5) * 715.8, 540, z); py = lerp(760 + (fy - .5) * 1000, 700, z)
        put(c, s['img'], px - ox, py - oy, Hz, shadow=False, bleed=True)
        if zm.get('tag'): put_chip(c, zm['tag'], 540, 1010, prog(u, z0 + .5, z0 + .75), bg=YELLOW, size=40)
    if s.get('wipe_from'): flash(c, u, 0, .2)

def reveal_zoom_sfx(d, s):
    z0 = s.get('zoom_at', max(1.6, d * .4))
    return [(0, 'impact', 1.), (.8, 'shimmer', .6), (1.0, 'pop', .7)] + ([(z0, 'whoosh', .7), (z0 + .5, 'pop', .8)] if s.get('zoom') else [])

def reveal_zoom_keys(d, s):
    if not s.get('zoom'): return [(d * .8, 'card')]
    z0 = s.get('zoom_at', max(1.6, d * .4))
    return [(z0 - .15, 'circle + arrow'), (min(d - .05, z0 + 1.0), 'zoom + tag')]

# 7 ---------------------------------------------------------------- artist
def artist(c, u, d, s):
    """avatar, name, role (default ILLUSTRATOR), handle. Avatar alone, centred."""
    ap = eback(prog(u, .1, .6))
    if ap > 0:
        r = int(230 * ap); cx_, cy_ = 540, 640 + OY
        if r > 4:
            halo = Image.new('RGBA', (r * 2 + 160, r * 2 + 160), (0, 0, 0, 0)); ImageDraw.Draw(halo).ellipse([40, 40, r * 2 + 120, r * 2 + 120], fill=PINK + (120,))
            paste_safe(c, halo.filter(ImageFilter.GaussianBlur(30)), cx_ - r - 80, cy_ - r - 80)
            ring = Image.new('RGBA', (r * 2 + 20, r * 2 + 20), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, r * 2 + 19, r * 2 + 19], fill=YELLOW + (255,))
            paste_safe(c, ring, cx_ - r - 10, cy_ - r - 10)
            av = img(s['avatar'], card=False).resize((r * 2, r * 2), Image.LANCZOS)
            mk = Image.new('L', (r * 4, r * 4), 0); ImageDraw.Draw(mk).ellipse([0, 0, r * 4 - 1, r * 4 - 1], fill=255)
            av.putalpha(mk.resize((r * 2, r * 2), Image.LANCZOS)); paste_safe(c, av, cx_ - r, cy_ - r)
            FRAME_BOXES.append(('card', cx_ - r, cy_ - r, cx_ + r, cy_ + r, r * 2, False))
        a = min(1, ap)
        put_text(c, s['name'], 540, 1000, F_BLACK, 120, stroke=6, alpha=a)
        put_text(c, s.get('role', 'ILLUSTRATOR'), 540, 1100, F_XB, 44, fill=YELLOW, alpha=a)
        if s.get('handle'): put_text(c, s['handle'], 540, 1165, F_B, 38, fill=(220, 220, 235), alpha=a)

def artist_sfx(d, s): return [(0, 'whoosh', .6), (.1, 'pop', .9)]
def artist_keys(d, s): return [(d * .8, 'avatar + name')]

# 8 ---------------------------------------------------------------- featured_cards
def featured_cards(c, u, d, s):
    """cards: [{img,label}] each gets its own full-size moment; then fan of all with heading (optional)."""
    cards = s['cards']; n = len(cards); fan_t = d - .9 if s.get('heading') else d + 1; per = (min(fan_t, d) - 0) / n
    fan = eio(prog(u, fan_t, fan_t + .5))
    if fan <= 0:
        for j, k in enumerate(cards):
            ts, te = j * per, (j + 1) * per; pin = eo3(prog(u, ts, ts + .45)); pout = eio(prog(u, te - .05, te + .35)) if j < n - 1 else 0
            if pin <= 0: continue
            x = lerp(1500, 540, pin) - 1000 * pout
            if x < -600: continue
            put(c, k['img'], x, 760, 980, angle=lerp(10, 0, pin) - 8 * pout, sweep=prog(u, ts + .4, ts + 1.2), bleed=pin < 1 or pout > 0)
            if pout < .2 and k.get('label'): put_chip(c, k['label'], 540, 1310, prog(u, ts + .3, ts + .55), size=34)
    else:
        fx = {2: [330, 750], 3: [295, 785, 540]}[n]; fa = {2: [-6, 6], 3: [-7, 7, 0]}[n]
        for j, k in enumerate(cards):
            sx = 540 if j == n - 1 else (-300 if j == 0 else 1380)
            put(c, k['img'], lerp(sx, fx[j], fan), lerp(760, 780, fan), lerp(980, 600, fan), angle=fa[j] * fan, bleed=fan < 1)
        put_text(c, s['heading'], 540, heading_y(780 - 300 + OY), F_BLACK, 64, stroke=6, alpha=fan)

def featured_cards_sfx(d, s):
    n = len(s['cards']); fan_t = d - .9 if s.get('heading') else d + 1; per = min(fan_t, d) / n
    ev = [x for j in range(n) for x in ((j * per, 'whoosh', .8), (j * per + .4, 'shimmer', .5))]
    return ev + ([(fan_t, 'whoosh', .7), (fan_t + .4, 'pop', .9)] if s.get('heading') else [])

def featured_cards_keys(d, s):
    n = len(s['cards']); fan_t = d - .9 if s.get('heading') else d + 1; per = min(fan_t, d) / n
    k = [(j * per + min(per - .1, .7), f"card {j + 1}") for j in range(n)]
    return k + ([(min(d - .05, fan_t + .6), 'fan + heading')] if s.get('heading') else [])

# 9 ---------------------------------------------------------------- stat_chart
def stat_chart(c, u, d, s):
    """img (side card), title, bars [[label,value]], total {value,label}, source, highlight {at, lines:[l1, BIG, l3, l4]}."""
    put(c, s['img'], 285, 760, 700)
    put_text(c, s.get('title', 'PSA POPULATION'), 780, 380, F_BLACK, 54, stroke=5, alpha=prog(u, 0, .4))
    bars = s['bars']; mx = max(v for _, v in bars); dd = ImageDraw.Draw(c)
    for i, (g, v) in enumerate(bars):
        bp = eo3(prog(u, .3 + i * .12, 1.4 + i * .12)); y = 480 + i * 105 + OY
        dd.text((600, y + 40), str(g), font=font(F_BLACK, 48), fill='white', anchor='rm')
        wb = max(10, 280 * v / mx) * bp; dd.rounded_rectangle([625, y + 12, 625 + wb, y + 68], 12, fill=YELLOW if i == 0 else (150, 140, 190))
        if bp > .8: dd.text((635 + wb + 6, y + 40), f'{v:,}', font=font(F_XB, 34), fill='white', anchor='lm')
    tot = s.get('total')
    if tot:
        put_text(c, f"{int(tot['value'] * eo3(prog(u, .4, 2.4))):,}", 780, 1080, F_BLACK, 130, stroke=7)
        put_text(c, tot.get('label', 'TOTAL GRADED'), 780, 1175, F_XB, 36, fill=(220, 220, 235))
    if s.get('source'): put_text(c, s['source'], 540, 1275, F_B, 26, fill=(200, 200, 215), alpha=prog(u, 1., 1.5))
    hl = s.get('highlight')
    if hl:
        t0 = hl.get('at', d * .55); p = prog(u, t0 - .1, t0 + .5)
        if p > 0:
            FRAME_BOXES.clear()                                   # highlight covers the chart
            dim(c, .91 * eio(p)); L = hl['lines']
            spec = [(560, F_BLACK, 80, (255, 255, 255), 6), (760, F_BLACK, 260, YELLOW, 10), (960, F_BLACK, 96, (255, 255, 255), 7), (1060, F_XB, 56, (255, 255, 255), 5), (1150, F_B, 28, (200, 200, 215), 0)]
            for i, line in enumerate(L[:5]):
                y, f, sz, col, st = spec[i]; q = eo3(prog(u, t0 + [0, .1, .35, .5, .65][i], t0 + [0, .1, .35, .5, .65][i] + .5))
                put_text(c, line, 540, y + lerp(40, 0, q), f, sz, fill=col, stroke=st, alpha=q, scale=lerp(1.12, 1, q) if i == 1 else 1)

def stat_chart_sfx(d, s):
    ev = [(0, 'whoosh', .6)] + [(.4 + i * .1, 'tick', .5) for i in range(20)]
    hl = s.get('highlight'); t0 = hl.get('at', d * .55) if hl else None
    return ev + ([(t0 - .1, 'whoosh', .6), (t0 + .2, 'pop', .7)] if hl else [])

def stat_chart_keys(d, s):
    hl = s.get('highlight')
    if not hl: return [(d * .8, 'chart')]
    t0 = hl.get('at', d * .55)
    return [(t0 - .2, 'full chart'), (min(d - .05, t0 + 1.25), 'highlight')]

# 10 --------------------------------------------------------------- cta_product
def cta_product(c, u, d, s):
    """img (product, no card corners), stamp_text."""
    p = eo3(prog(u, 0, .5))
    put(c, s['img'], lerp(-400, 540, p), 760, 860, angle=lerp(15, -4, p), sweep=prog(u, .6, 1.4), card=False)
    if s.get('stamp_text'): put_stamp(c, 'rect', 560, 1180, u, 1.2, text=s['stamp_text'], angle=-8)

def cta_product_sfx(d, s): return [(0, 'whoosh', .9), (.6, 'shimmer', .5), (1.2, 'stamp', 1.)]
def cta_product_keys(d, s): return [(min(d - .05, 1.8), 'product + stamp')]

# 11 --------------------------------------------------------------- end_card
def end_card(c, u, d, s):
    """img: the Kard Avenue 'FOLLOW US!' call-to-action poster (9:16, own logo + store badges).
    Shown full-bleed; logo overlay and burned-in caption are hidden (the poster carries its own text)."""
    pr = img(s.get('img', '23_follow_us_cta.jpg'), card=False).convert('RGBA')
    p = eo3(prog(u, 0, .5)); sc = lerp(1.06, 1, eo3(prog(u, 0, d)))
    r = max(W / pr.width, H / pr.height) * sc; w_, h_ = int(pr.width * r) + 1, int(pr.height * r) + 1
    im = pr.resize((w_, h_), Image.LANCZOS)
    if p < 1: im.putalpha(Image.new('L', im.size, int(255 * p)))
    paste_safe(c, im, int(W / 2 - w_ / 2), int(H / 2 - h_ / 2))

def end_card_sfx(d, s): return [(0, 'whoosh', .8), (.5, 'shimmer', .5)]
def end_card_keys(d, s): return [(d * .8, 'promo')]

SCENE_TYPES = ['hook_mystery', 'hero_stamp', 'product_intro', 'card_grid', 'card_lineup', 'reveal_zoom', 'artist',
               'featured_cards', 'stat_chart', 'cta_product', 'end_card']
SCENES = {k: (globals()[k], globals()[k + '_sfx']) for k in SCENE_TYPES}
KEYS = {k: globals()[k + '_keys'] for k in SCENE_TYPES}
NO_LOGO = {'end_card'}
NO_CAPTION = {'end_card'}   # full-bleed CTA poster: VO plays, caption not burned in

# ======================================================================
# Timeline, captions, frames
# ======================================================================
def timeline():
    t = 0; out = []
    for s in CFG['scenes']: out.append((t, t + s['dur'], s)); t += s['dur']
    return out

def total_len(): return sum(s['dur'] for s in CFG['scenes'])

def wrap(text, f, maxw):
    lines, cur = [], []
    for w_ in text.split(' '):
        if f.getlength(' '.join(cur + [w_])) > maxw and cur: lines.append(cur); cur = [w_]
        else: cur.append(w_)
    if cur: lines.append(cur)
    return lines

@functools.lru_cache(None)
def caption_img(text, size=60):
    f = font(F_XB, size); lines = wrap(text, f, CAPTION_MAXW); lh = int(size * 1.22)
    im = Image.new('RGBA', (CAPTION_MAXW + 60, lh * len(lines) + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    hl = set(CFG.get('highlight_words', [])) | {'NEW', 'ONLY', 'PSA', 'Kard', 'Avenue'}
    for i, ln in enumerate(lines):
        x = (im.width - f.getlength(' '.join(ln))) / 2; y = 15 + i * lh
        for w_ in ln:
            core = w_.strip('.,!?—:…()"')
            col = YELLOW if (any(ch.isdigit() for ch in core) or core in hl) else (255, 255, 255)
            d.text((x, y), w_, font=f, fill=col, stroke_width=7, stroke_fill=(10, 8, 20)); x += f.getlength(w_ + ' ')
    return im

def chunks(text, maxw=4):
    """Split a caption into 2-4 word chunks, preferring breaks after punctuation."""
    words = text.split(); out, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= maxw or (len(cur) >= 2 and w_[-1] in ',.!?—:…'): out.append(' '.join(cur)); cur = []
    if cur:
        if out and len(cur) == 1: out[-1] += ' ' + cur[0]
        else: out.append(' '.join(cur))
    return out

def caption_for(s, u, d):
    """Returns (text, start_local, size) currently visible."""
    cap = s.get('caption')
    if not cap: return None
    if CFG.get('caption_mode', 'lines') != 'chunks': return cap, .3 if s is CFG['scenes'][0] else 0, 60
    a, b = s.get('vo_window', [.1, d - .15]); parts = chunks(cap); L = sum(len(p) for p in parts); t = a
    for p in parts:
        dt = (b - a) * len(p) / L
        if u < t + dt: return p, t, 72
        t += dt
    return parts[-1], t - dt, 72

def draw_caption(c, text, u, t0, size):
    im = caption_img(text, size); s = lerp(.82, 1, eback(prog(u, t0, t0 + .22)))
    if s < .999: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    x, y = int(W / 2 - im.width / 2), int(CAPTION_Y - im.height / 2); paste_safe(c, im, x, y)
    bb = im.getbbox() or (0, 0, 0, 0); FRAME_BOXES.append(('caption', x + bb[0], y + bb[1], x + bb[2], y + bb[3], 0, False))

def frame(t):
    FRAME_BOXES.clear()
    for t0, t1, s in timeline():
        if t0 <= t < t1: break
    else: t0, t1, s = timeline()[-1]
    u, d = t - t0, s['dur']; c = background(t); fn = SCENES[s['type']][0]
    fn(c, u, d, s)
    if s.get('continue_caption'):                       # keep previous scene's caption on screen, no re-pop
        prev = CFG['scenes'][CFG['scenes'].index(s) - 1]; cp = caption_for(prev, prev['dur'] - .01 + u, prev['dur'] + d)
        cp = (cp[0], -9, cp[2]) if cp else None
    else: cp = caption_for(s, u, d)
    if cp and s['type'] not in NO_CAPTION: draw_caption(c, cp[0], u, cp[1], cp[2])
    if s['type'] not in NO_LOGO: logo(c)
    c.alpha_composite(grain(int(t * FPS) % 4))
    return c.convert('RGB')

# ======================================================================
# Audio
# ======================================================================
def build_audio(path):
    SR = 48000; L = total_len(); mix = np.zeros((int(L * SR) + SR, 2)); cache = {}
    sfx_dir = os.path.join(BASE, CFG.get('sfx_dir', 'sfx')); vo = CFG.get('voiceover')
    duck = .55 if vo else 1.
    for t0, t1, s in timeline():
        for lt, name, g in SCENES[s['type']][1](s['dur'], s):
            if name not in cache:
                with wave.open(os.path.join(sfx_dir, name + '.wav')) as w: cache[name] = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768
            a = cache[name]; i = int((t0 + lt) * SR)
            if 0 <= i < len(mix): seg = a[:len(mix) - i]; mix[i:i + len(seg)] += seg * g * .8 * duck
    if vo:
        tmp = path + '.vo.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', apath(vo), '-ar', str(SR), '-ac', '2', tmp], check=True)
        with wave.open(tmp) as w: v = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2) / 32768
        off = int(CFG.get('voiceover_offset', 0) * SR); n = min(len(v), len(mix) - off); mix[off:off + n] += v[:n]; os.remove(tmp)
    mix = np.tanh(mix[:int(L * SR)] * 1.1) * .9
    with wave.open(path, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ======================================================================
# Commands
# ======================================================================
def _render_part(args):
    a, b, path, cfgp = args; load(cfgp)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    for f in range(a, b): p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()

def render_range(out, f0, f1, cfgp):
    """Render frames [f0, f1) with the matching slice of the audio mix."""
    n = f1 - f0; k = max(1, min(mp.cpu_count(), math.ceil(n / FPS))); step = math.ceil(n / k)
    tmpd = out + '.parts'; os.makedirs(tmpd, exist_ok=True)
    parts = [(i, min(f1, i + step), os.path.join(tmpd, f'p{j}.mp4'), cfgp) for j, i in enumerate(range(f0, f1, step))]
    with mp.Pool(len(parts)) as pool: pool.map(_render_part, parts)
    with open(os.path.join(tmpd, 'list.txt'), 'w') as f: f.writelines(f"file '{os.path.basename(p[2])}'\n" for p in parts)
    wav = os.path.join(tmpd, 'audio.wav'); build_audio(wav)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(tmpd, 'list.txt'),
                    '-ss', f'{f0 / FPS:.3f}', '-t', f'{n / FPS:.3f}', '-i', wav,
                    '-c:v', 'libx264', '-crf', '21', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    shutil.rmtree(tmpd)

def cmd_render(out, cfgp):
    render_range(out, 0, int(total_len() * FPS), cfgp); print('rendered', out, f'{total_len():.1f}s')

def parse_span(spec):
    """'6' -> scene 6, '5-7' -> scenes 5..7 (1-based), '12.5:20' -> seconds. Returns (t0, t1)."""
    tl = timeline()
    if ':' in spec:
        a, b = spec.split(':'); t0, t1 = float(a or 0), float(b or total_len())
    else:
        a, _, b = spec.partition('-'); i, j = int(a), int(b or a)
        if not (1 <= i <= j <= len(tl)): sys.exit(f'Scene range {spec} is outside 1-{len(tl)}')
        t0, t1 = tl[i - 1][0], tl[j - 1][1]
    t0, t1 = max(0., t0), min(total_len(), t1)
    if t1 <= t0: sys.exit(f'Empty range: {spec}')
    return t0, t1

def cmd_clip(out, spec, cfgp):
    t0, t1 = parse_span(spec); render_range(out, int(round(t0 * FPS)), int(round(t1 * FPS)), cfgp)
    print('clip', out, f'{t0:.1f}s-{t1:.1f}s ({t1 - t0:.1f}s)')

def sample_times():
    """Key moments per scene (each scene type defines its own), clamped inside the scene."""
    for i, (t0, t1, s) in enumerate(timeline()):
        d = s['dur']
        for lt, label in KEYS[s['type']](d, s):
            yield i, s, t0 + clamp(lt, 0, d - .04), label

def cmd_stills(out):
    tl = list(sample_times()); cols = min(6, len(tl)); rows = math.ceil(len(tl) / cols); tw, th = 270, 480; lab = 44
    sheet = Image.new('RGB', (cols * tw, rows * (th + lab)), (12, 10, 18)); d = ImageDraw.Draw(sheet)
    for k, (i, s, t, label) in enumerate(tl):
        x, y = (k % cols) * tw, (k // cols) * (th + lab)
        sheet.paste(frame(t).resize((tw, th)), (x, y))
        d.text((x + 6, y + th + 4), f"{i + 1}. {s.get('beat', s['type'])} @{t:.1f}s", font=font(F_UI, 16), fill=(230, 230, 240))
        d.text((x + 6, y + th + 23), label, font=font(F_UI, 15), fill=YELLOW)
    sheet.save(out); print('stills', out, f'{len(tl)} frames')

def cmd_cover(out):
    cv = CFG.get('cover', {}); c = background(3.0); hero = cv.get('img') or CFG['scenes'][0].get('hero')
    put(c, hero, 540, 740, 1080, sweep=.45)
    if cv.get('title'):
        title = ''.join(ch for ch in cv['title'] if ord(ch) < 0x2190).strip()   # fonts have no emoji
        f = font(F_BLACK, 96); lines = wrap(title, f, 900)
        for i, ln in enumerate(lines): put_text(c, ' '.join(ln), 540, 1560 - OY + i * 110 - (len(lines) - 1) * 55, F_BLACK, 96, fill=YELLOW, stroke=8)
    logo(c); c.convert('RGB').save(out); print('cover', out)

def cmd_check():
    errs, warns = [], []
    L = total_len()
    if not (MIN_LEN <= L <= MAX_LEN): errs.append(f'Length {L:.1f}s is outside {MIN_LEN:.0f}-{MAX_LEN:.0f}s')
    # assets
    names = set()
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('img', 'hero', 'box', 'pack', 'avatar') and isinstance(v, str): names.add(v)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, str) and re.search(r'\.(png|jpe?g|webp)$', v, re.I): names.add(v)
                walk(v)
    walk(CFG['scenes']); names.add(CFG.get('logo', '07_kard_logo.png'))
    if CFG.get('cover', {}).get('img'): names.add(CFG['cover']['img'])
    for n in sorted(names):
        if not os.path.exists(apath(n)): errs.append(f'Missing asset: {n}'); continue
        h = Image.open(apath(n)).height
        if h < 700 and 'avatar' not in n and 'logo' not in n: warns.append(f'Low-res asset ({h}px tall, want >=700): {n}')
    hero = CFG['scenes'][0].get('hero')
    if hero and os.path.exists(apath(hero)) and Image.open(apath(hero)).height < 1000: warns.append(f'Hero card under 1000px tall: {hero}')
    if CFG.get('voiceover') and not os.path.exists(apath(CFG['voiceover'])): errs.append(f'Voiceover file not found: {CFG["voiceover"]}')
    sfx_dir = os.path.join(BASE, CFG.get('sfx_dir', 'sfx'))
    need = sorted({n for _, _, s in timeline() for _, n, _ in SCENES[s['type']][1](s['dur'], s)})
    miss = [n for n in need if not os.path.exists(os.path.join(sfx_dir, n + '.wav'))]
    if miss: errs.append(f'Missing sound effects in {sfx_dir}: {", ".join(miss)} (run make_sfx.py inside that folder)')
    # business rules
    if any(s['type'] == 'cta_product' for s in CFG['scenes']) and not CFG.get('stock_confirmed'):
        errs.append('A stock/payoff scene exists but "stock_confirmed" is not true: confirm with the user that the product is in stock, then set it')
    if IG_PLACEHOLDER in CFG.get('post_caption', '') and not CFG.get('ig_handle'):
        warns.append(f'Post caption still has {IG_PLACEHOLDER}: set "ig_handle" in the config (e.g. "@kardavenue")')
    # captions
    f = font(F_XB, 60)
    for i, s in enumerate(CFG['scenes']):
        cap = s.get('caption', '')
        if s.get('continue_caption'): continue
        if not cap: warns.append(f'Scene {i + 1} ({s["type"]}) has no caption'); continue
        if not s.get('vo'): warns.append(f'Scene {i + 1} has no voiceover line')
        lines = wrap(cap, f, CAPTION_MAXW)
        if len(lines) > 3: errs.append(f'Scene {i + 1} caption is {len(lines)} lines (max 3)')
        if len(lines) > 1 and len(lines[-1]) == 1: warns.append(f'Scene {i + 1} caption leaves "{lines[-1][0]}" alone on the last line')
        words = len(re.sub(r'\[[^\]]*\]', '', s.get('vo', '')).split()); span = s['dur']
        for nxt in CFG['scenes'][i + 1:]:
            if not nxt.get('continue_caption'): break
            span += nxt['dur']
        if s.get('vo') and words / span > 3.6: warns.append(f'Scene {i + 1}: {words} VO words in {span:.1f}s is too fast (>3.6 words/s)')
        if s['dur'] > 6.5: warns.append(f'Scene {i + 1} is {s["dur"]}s (keep scenes 2-6s)')
    for w_ in CFG.get('forbidden_words', ['TGA']):
        for i, s in enumerate(CFG['scenes']):
            if re.search(r'\b' + re.escape(w_) + r'\b', s.get('caption', '') + ' ' + s.get('vo', '')): errs.append(f'Scene {i + 1} mentions forbidden word "{w_}"')
    # layout: sample settled frames per scene (needs every image and font to load)
    if any(e.startswith('Missing asset') for e in errs):
        warns.append('Layout checks skipped until the missing assets are added')
    for i, (t0, t1, s) in enumerate(timeline() if not any(e.startswith('Missing asset') for e in errs) else []):
        for fr in (.55, .8, .97):
            frame(t0 + s['dur'] * fr); boxes = list(FRAME_BOXES)
            cap = [b for b in boxes if b[0] == 'caption']; items = [b for b in boxes if b[0] != 'caption']
            for b in items:
                role, x0, y0, x1, y1, h, bleed = b
                if role == 'card' and not bleed:
                    if x0 < SIDE_MARGIN - 8 or x1 > W - SIDE_MARGIN + 8: warns.append(f'Scene {i + 1} @{fr:.0%}: {role} touches the side edge')
                    if 0 < h < 300: warns.append(f'Scene {i + 1} @{fr:.0%}: card only {h}px tall (min 300)')
                if y1 > SAFE_BOTTOM and not bleed: warns.append(f'Scene {i + 1} @{fr:.0%}: {role} goes below the Instagram safe line (y={y1})')
                for cb in cap:
                    if not bleed and x0 < cb[3] and x1 > cb[1] and y0 < cb[4] and y1 > cb[2] - 60:
                        errs.append(f'Scene {i + 1} @{fr:.0%}: {role} is within 60px of / overlapping the caption'); break
    errs = list(dict.fromkeys(errs)); warns = list(dict.fromkeys(warns))
    print(f'Length: {L:.1f}s  ({len(CFG["scenes"])} scenes)')
    for e in errs: print('ERROR  ', e)
    for w_ in warns: print('WARN   ', w_)
    print('OK — no errors' if not errs else f'{len(errs)} error(s)')
    return not errs

DESC = {'hook_mystery': 'Starburst; known versions pop in with ✗; blacked-out mystery card + ?; flash reveal',
        'hero_stamp': 'Hero card push-in + stamp', 'product_intro': 'Box + pack fly in, date types out',
        'card_grid': 'Grid of cards flies in', 'card_lineup': 'Cards fanned side by side with labels',
        'reveal_zoom': 'Wipe to card, circle + arrow, zoom into detail + tag', 'artist': 'Artist avatar centred, name, role, handle',
        'featured_cards': 'Each card full-size one by one, then fan', 'stat_chart': 'Bar chart + counter, then full-screen highlight',
        'cta_product': 'Product slides in + stamp', 'end_card': 'Full-bleed FOLLOW US! call-to-action poster (store badges)'}

def scene_rows():
    rows = []
    for i, (t0, t1, s) in enumerate(timeline()):
        rows.append({'t': round(t0, 2), 'e': round(t1, 2), 'title': s.get('beat', s['type']), 'vo': s.get('vo', ''), 'cap': s.get('caption', ''),
                     'vis': s.get('visual', DESC[s['type']]), 'sfx': ', '.join(sorted({n for _, n, _ in SCENES[s['type']][1](s['dur'], s)}))})
    return rows

def post_caption():
    pc = CFG.get('post_caption', '')
    return pc.replace(IG_PLACEHOLDER, CFG['ig_handle']) if CFG.get('ig_handle') else pc

def cmd_caption(out=None):
    pc = post_caption()
    if out: open(out, 'w').write(pc + '\n'); print('caption', out)
    else: print(pc)

def cmd_script(out):
    fm = lambda x: f'{int(x // 60)}:{x % 60:04.1f}'
    L = [f"# {CFG.get('title', 'Kard Avenue Reel')}\n", f"Length {total_len():.1f}s · 9:16 · Bahasa VO (kamu) + EN captions\n",
         '| Time | Beat | Voiceover (Bahasa) | Caption (EN) | Visual |', '|---|---|---|---|---|']
    for r in scene_rows(): L.append(f"| {fm(r['t'])}–{fm(r['e'])} | {r['title']} | {r['vo']} | {r['cap']} | {r['vis']} |")
    if CFG.get('post_caption'): L += ['', '## Post caption', '', post_caption()]
    open(out, 'w').write('\n'.join(L) + '\n'); print('script', out)

def cmd_page(outdir, video=None):
    os.makedirs(outdir, exist_ok=True)
    data = {'title': CFG.get('title', 'Kard Avenue Reel'), 'length': round(total_len(), 1), 'video': 'video.mp4', 'scenes': scene_rows(),
            'open': CFG.get('open_decisions', [])}
    open(os.path.join(outdir, 'scenes.json'), 'w').write(json.dumps(data, ensure_ascii=False, indent=1))
    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'editor_template.html')
    if os.path.exists(tpl): shutil.copy(tpl, os.path.join(outdir, 'index.html'))
    if video:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-crf', '27', '-preset', 'slow',
                        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '128k', os.path.join(outdir, 'video.mp4')], check=True)
    print('page', outdir)

def load(p):
    global CFG, BASE
    CFG = json.load(open(p)); BASE = os.path.dirname(os.path.abspath(p))

if __name__ == '__main__':
    if len(sys.argv) < 3: print(__doc__); sys.exit(1)
    cfgp, cmd = sys.argv[1], sys.argv[2]; load(cfgp)
    if cmd == 'check': sys.exit(0 if cmd_check() else 1)
    elif cmd == 'stills': cmd_stills(sys.argv[3])
    elif cmd == 'render': cmd_render(sys.argv[3], cfgp)
    elif cmd == 'clip': cmd_clip(sys.argv[3], sys.argv[4], cfgp)
    elif cmd == 'cover': cmd_cover(sys.argv[3])
    elif cmd == 'script': cmd_script(sys.argv[3])
    elif cmd == 'caption': cmd_caption(sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == 'page': cmd_page(sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == 'frame': frame(float(sys.argv[3])).save(sys.argv[4])
    else: print(__doc__)
