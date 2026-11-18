#!/usr/bin/env python3
"""
Kard Avenue Reel engine v3.3 — config-driven. v3 adds the approved Video 05 3D style (macro3d, slam, wall, whip/leak, reflect, glitch, camera, plain captions).

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
  broll, hook_mystery, hero_stamp, product_intro, card_grid, card_lineup, reveal_zoom,
  artist, featured_cards, stat_chart, cta_product, end_card
  v3.3 (Video 12 'Ranked Countdown'): rank, bar_race, leaderboard, coverflow, deal, conveyor.
  v3.3.1 (Video 12 final): logo_stat, deal "logo", rank "enter_at", per-scene "chunk_at"/"chunk_text", global "mystery_art".
  Config: "max_len" overrides the 60s length limit for one video (e.g. 75).
"""
import math, os, sys, json, subprocess, functools, wave, re, shutil, multiprocessing as mp
import numpy as np
from PIL import ImageEnhance, ImageChops
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ======================================================================
# House style (Kard Avenue playbook) — change here, applies to every video
# ======================================================================
W, H, FPS = 1080, 1920, 30
OY = 120                     # content shifted down to balance frame with captions
CAPTION_Y = 1560             # caption block centre
CAPTION_MAXW = 900
SAFE_BOTTOM = 1680           # Instagram UI covers below this
SIDE_MARGIN = 30
LOGO_W, LOGO_ALPHA = 370, 1.
LOGO_POS = ((1080 - 370) // 2, 150)
MIN_LEN, MAX_LEN = 45.0, 60.0
PAPER, INK = (250, 250, 250), (10, 10, 10)   # Kard Avenue brand white #fafafa / black #0a0a0a
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
    if name.startswith('flip:'):   # mirror reflection for a glossy floor
        im = img(name[5:], card).transpose(Image.FLIP_TOP_BOTTOM); a = np.asarray(im.split()[3]).astype(float)
        fade = np.clip(1 - np.linspace(0, 1, im.height) * 2.2, 0, 1)[:, None] * .38; im.putalpha(Image.fromarray((a * fade).astype(np.uint8))); return im
    im = Image.open(apath(name))
    return round_card(im) if card else im.convert('RGBA')

def make_mystery(im):
    a = im.split()[3]; art = np.asarray(im.convert('RGB')).astype(float)
    k_ = CFG.get('mystery_art', .14); dark = np.full_like(art, (20, 20, 20)) * (1 - k_) + art * k_
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

NOW = [0.]

def put(c, name, cx, cy, h, angle=0, alpha=1., shadow=True, sweep=None, crop_frac=None, card=True, role='card', bleed=False):
    """Paste an image centred at (cx, cy+OY) with height h. Records its box for `check`."""
    if alpha <= .01 or h < 4: return
    h = int(round(h / 2) * 2); angle = round(angle * 2) / 2; cy += OY
    fl = CFG.get('float')
    if fl and shadow and not bleed and role == 'card':   # gentle idle float so held cards never look rigid
        ph = (sum(map(ord, name)) % 97) * .37; amp = fl if isinstance(fl, (int, float)) and fl is not True else 9
        cx += amp * .45 * math.sin(NOW[0] * .8 + ph); cy += amp * math.sin(NOW[0] * 1.25 + ph)
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
    if alpha > .5 and role != 'fx': FRAME_BOXES.append((role, x, y, x + s.width, y + s.height, h, bleed))

@functools.lru_cache(None)
def text_img(text, path, size, fill=PAPER, stroke=0):
    f = font(path, size); bb = f.getbbox(text, stroke_width=stroke)
    im = Image.new('RGBA', (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - bb[0], 2 - bb[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(10, 8, 20))
    return im

def put_text(c, text, cx, cy, path=F_XB, size=48, fill=PAPER, stroke=0, alpha=1., scale=1., record=True):
    im = text_img(text, path, size, fill, stroke)
    if scale != 1: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    im = with_alpha(im, alpha); x, y = int(cx - im.width / 2), int(cy + OY - im.height / 2)
    paste_safe(c, im, x, y)
    if record and alpha > .5: FRAME_BOXES.append(('text', x, y, x + im.width, y + im.height, 0, False))

@functools.lru_cache(None)
def chip_img(text, bg=PAPER, fg=INK, size=40):
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
    if a > 0: c.alpha_composite(Image.new('RGBA', (W, H), (10, 10, 10, int(255 * a))))

# ---------------- background / burst / ? ----------------
@functools.lru_cache(None)
def bg_base():
    bw, bh = W + 240, H + 240; yy, xx = np.mgrid[0:bh, 0:bw]
    r = np.clip(np.hypot((xx - bw * .5) / bw, (yy - bh * .38) / bh) * 1.6, 0, 1)
    bc = CFG.get('bg_color')
    if bc: base = np.stack([lerp(bc[0][k], bc[1][k], r) for k in range(3)], -1)   # brand flat background: [centre, edge]
    else: base = np.stack([lerp(42, 10, r), lerp(24, 8, r), lerp(70, 22, r)], -1)
    im = Image.fromarray(base.astype(np.uint8)).convert('RGBA')
    bgc = CFG.get('bg_image')
    if bgc:  # optional event backdrop: image cover-fit, heavily blurred, then darkened toward the navy gradient
        src = img(bgc['img'] if isinstance(bgc, dict) else bgc, card=False).convert('RGBA'); sc = max(bw / src.width, bh / src.height)
        src = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
        src = src.crop(((src.width - bw) // 2, (src.height - bh) // 2, (src.width - bw) // 2 + bw, (src.height - bh) // 2 + bh))
        src = src.filter(ImageFilter.GaussianBlur(bgc.get('blur', 45) if isinstance(bgc, dict) else 45))
        dark = bgc.get('dark', .6) if isinstance(bgc, dict) else .6
        im = Image.blend(src, im, dark)
    bl = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl); rng = np.random.default_rng(3)
    for _ in range(14):
        cx, cy, rr = rng.uniform(0, bw), rng.uniform(0, bh), rng.uniform(60, 220)
        col = [tuple(x) for x in CFG.get('bokeh', [PINK, (90, 160, 255), (180, 120, 255)])][rng.integers(len(CFG.get('bokeh', [0, 0, 0])))]
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
    hh = s.get('h', 1000) + 30 * prog(u, 0, d)
    if s.get('reflect'): put(c, 'flip:' + s['img'], 540, 760 + hh + 6, hh, shadow=False, role='fx')
    put(c, s['img'], 540, 760, hh, sweep=prog(u, d * .5, d * .5 + .8))
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
    cards = s['cards']; NC = s.get('cols', 3); rows = math.ceil(len(cards) / NC); h = s.get('card_h', 360); gap = h * 1.04
    top = 760 - (rows - 1) * gap / 2; keep = s.get('keep'); co = eio(prog(u, d - .4, d)) if keep is not None else 0
    for i, name in enumerate(cards):
        sf = s.get('soft')
        pr = prog(u, .15 + i * sf, .15 + i * sf + .75) if sf else prog(u, .1 + i * .08, .45 + i * .08)
        if pr <= 0: continue
        p = eo3(pr) if sf else eback(pr); col, row = i % NC, i // NC; n_in_row = min(NC, len(cards) - row * NC)
        tx = 540 + (col - (n_in_row - 1) / 2) * s.get('col_gap', 300); ty = top + row * gap
        tx, ty = lerp(tx, 540, co), lerp(ty, 760, co)
        if sf: put(c, name, tx, ty + 140 * (1 - p), h, alpha=p * (1 - co * (i != keep)))   # one by one: soft fade + rise
        else: put(c, name, lerp(540, tx, min(1, p)), lerp(2100, ty, min(1, p)), h, alpha=1 - co * (i != keep))

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
        pa = zm.get('pan', 0)
        if pa: fx += lerp(-pa, pa, eio(prog(u, z0 + .2, d + .45)) * .8 + prog(u, z0 + .2, d + .45) * .2)   # slow left-to-right drift while zoomed
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
@functools.lru_cache(None)
def avatar_square(name, crop=()):
    """Square crop, never stretched. crop = (cx, top, size) as fractions of image width/height/width;
    default: centred square from the top (faces sit high in portrait photos)."""
    im = img(name, card=False); w, h = im.size
    cx, top, size = crop if crop else (.5, 0., min(w, h) / w)
    sz = int(min(size * w, w, h)); x0 = int(min(max(0, cx * w - sz / 2), w - sz)); y0 = int(min(max(0, top * h), h - sz))
    sq = im.crop((x0, y0, x0 + sz, y0 + sz)); bg = Image.new('RGBA', sq.size, (30, 22, 50, 255)); bg.alpha_composite(sq)
    return bg

@functools.lru_cache(maxsize=4)
def cutout_paper(name, crop, ph, seed=7):
    """Photo on a scissor-cut paper: white border with uneven straight snips."""
    im = img(name, card=False)
    if crop: x0, y0, x1, y1 = crop; im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
    pw = round(im.width * ph / im.height); im = im.resize((pw, ph), Image.LANCZOS)
    rng = np.random.default_rng(seed); b = 26; pad = 60; Wp, Hp_ = pw + 2 * (b + pad), ph + 2 * (b + pad)
    def edge(p0, p1, n):
        pts = []
        for k in range(n):
            t = k / n; x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
            pts.append((x + rng.uniform(-9, 9), y + rng.uniform(-9, 9)))
        return pts
    L, T, R, B = pad + 4, pad + 4, Wp - pad - 4, Hp_ - pad - 4
    poly = edge((L, T), (R, T), 5) + edge((R, T), (R, B), 6) + edge((R, B), (L, B), 5) + edge((L, B), (L, T), 6)
    paper = Image.new('RGBA', (Wp, Hp_), (0, 0, 0, 0)); ImageDraw.Draw(paper).polygon(poly, fill=PAPER + (255,))
    sh = Image.new('L', (Wp, Hp_), 0); ImageDraw.Draw(sh).polygon([(x + 10, y + 16) for x, y in poly], fill=170); sh = sh.filter(ImageFilter.GaussianBlur(18))
    out = Image.new('RGBA', (Wp, Hp_), (0, 0, 0, 0)); sl = Image.new('RGBA', (Wp, Hp_), (0, 0, 0, 0)); sl.putalpha(sh); out.alpha_composite(sl)
    out.alpha_composite(paper); out.alpha_composite(im.convert('RGBA'), (pad + b, pad + b)); return out

def artist_cutout(c, u, d, s):
    p = eback(prog(u, .05, .55)); ph = s.get('photo_h', 760)
    if p > 0:
        pc = cutout_paper(s['avatar'], tuple(s.get('photo_crop', ())), ph)
        sc = lerp(.82, 1, p); ang = lerp(-9, s.get('photo_angle', -3), eo3(prog(u, .05, .7))) + .6 * math.sin(u * 1.3)
        im = pc.resize((int(pc.width * sc), int(pc.height * sc)), Image.LANCZOS).rotate(ang, resample=Image.BICUBIC, expand=True)
        cy_ = s.get('photo_y', 640) + OY + 10 * math.sin(u * 1.1); paste_safe(c, with_alpha(im, min(1, p)), int(540 - im.width / 2), int(cy_ - im.height / 2))
        hh = ph * sc / 2 + 40; FRAME_BOXES.append(('card', 540 - hh * .7, cy_ - hh, 540 + hh * .7, cy_ + hh, ph, False))
    a = eo3(prog(u, .45, .85)); ny = s.get('name_y', 1150)
    put_text(c, s['name'], 540, ny, F_BLACK, 104, stroke=6, alpha=a)
    put_text(c, s.get('role', 'ILLUSTRATOR'), 540, ny + 88, F_XB, 40, fill=YELLOW, alpha=a)
    if s.get('handle'): put_text(c, s['handle'], 540, ny + 145, F_B, 36, fill=(220, 220, 220), alpha=a)

def artist(c, u, d, s):
    """avatar, name, role (default ILLUSTRATOR), handle. Avatar alone, centred."""
    if s.get('cutout'): return artist_cutout(c, u, d, s)
    ap = eback(prog(u, .1, .6))
    if ap > 0:
        r = int(230 * ap); cx_, cy_ = 540, 640 + OY
        if r > 4:
            halo = Image.new('RGBA', (r * 2 + 160, r * 2 + 160), (0, 0, 0, 0)); ImageDraw.Draw(halo).ellipse([40, 40, r * 2 + 120, r * 2 + 120], fill=PINK + (120,))
            paste_safe(c, halo.filter(ImageFilter.GaussianBlur(30)), cx_ - r - 80, cy_ - r - 80)
            ring = Image.new('RGBA', (r * 2 + 20, r * 2 + 20), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, r * 2 + 19, r * 2 + 19], fill=YELLOW + (255,))
            paste_safe(c, ring, cx_ - r - 10, cy_ - r - 10)
            av = avatar_square(s['avatar'], tuple(s.get('avatar_crop', ()))).resize((r * 2, r * 2), Image.LANCZOS)
            mk = Image.new('L', (r * 4, r * 4), 0); ImageDraw.Draw(mk).ellipse([0, 0, r * 4 - 1, r * 4 - 1], fill=255)
            av.putalpha(mk.resize((r * 2, r * 2), Image.LANCZOS)); paste_safe(c, av, cx_ - r, cy_ - r)
            FRAME_BOXES.append(('card', cx_ - r, cy_ - r, cx_ + r, cy_ + r, r * 2, False))
        a = min(1, ap)
        put_text(c, s['name'], 540, 1000, F_BLACK, 120, stroke=6, alpha=a)
        put_text(c, s.get('role', 'ILLUSTRATOR'), 540, 1100, F_XB, 44, fill=YELLOW, alpha=a)
        if s.get('handle'): put_text(c, s['handle'], 540, 1165, F_B, 38, fill=(220, 220, 220), alpha=a)

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

# 12 --------------------------------------------------------------- broll
def broll(c, u, d, s):
    """img; pan: {fy, fx0, fx1, h}. One slow, steady left-to-right glide across the card, gentle fade in."""
    pn = s.get('pan', {}); src = img(s['img']); ar = src.width / src.height; h = pn.get('h', 2000)
    nx = CFG['scenes'][CFG['scenes'].index(s) + 1] if s is not CFG['scenes'][-1] else {}
    T = d + nx.get('xfade_in', CFG.get('xfade', .45)); x = prog(u, 0, T); p = x * x * x * (x * (6 * x - 15) + 10) * .7 + x * .3; fx = lerp(pn.get('fx0', .28), pn.get('fx1', .72), p); fy = lerp(pn.get('fy0', pn.get('fy', .42)), pn.get('fy1', pn.get('fy', .42)), p); h = lerp(pn.get('h0', h), pn.get('h1', h), p)  # optional tilt (fy0->fy1) and zoom (h0->h1)
    put(c, s['img'], 540 - (fx - .5) * h * ar, H / 2 - OY - (fy - .5) * h, h, shadow=False, bleed=True)
    yy, xx = np.mgrid[0:H:8, 0:W:8]; r = np.hypot((xx - W / 2) / W, (yy - H / 2) / H)
    v = Image.fromarray((np.clip((r - .3) * 2., 0, 1) * 170).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    vig = Image.new('RGBA', (W, H), (6, 6, 6, 0)); vig.putalpha(v); c.alpha_composite(vig)
    fi = 1 - eo3(prog(u, 0, s.get('fade_in', .5)))
    if fi > 0: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * fi))))
    FRAME_BOXES[:] = [b for b in FRAME_BOXES if b[0] != 'card']

def broll_sfx(d, s): return []
def broll_keys(d, s):
    return [(d * .3, 'pan start'), (d * .95, 'pan end')]

def persp_coeffs(dst, src):
    A = []
    for (x, y), (X, Y) in zip(dst, src): A += [[x, y, 1, 0, 0, 0, -X * x, -X * y], [0, 0, 0, x, y, 1, -Y * x, -Y * y]]
    return np.linalg.solve(np.array(A, float), np.array(src, float).reshape(8))

@functools.lru_cache(maxsize=64)
def dof_mask(axis, at, width, q):
    yy, xx = np.mgrid[0:H // 4, 0:W // 4]; v = (yy / (H / 4)) if axis == 'y' else (xx / (W / 4))
    m = np.clip((np.abs(v - at) - width / 2) / .22, 0, 1) ** 1.3
    return Image.fromarray((m * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)

HL_COLOR = (255, 226, 0)
def highlight_src(src, s, u):
    """Editorial highlight on an article screenshot: page upscaled + sharpened + text thickened (bold, crisp);
    noir = drained/darkened page; marker = bright yellow multiplied under the text (text stays solid black), sweeping in sync with the voice."""
    base, bold = article_base(s['img'], bool(s.get('noir')))
    out = base.copy(); Wd, Hd = out.size; hl = s['highlight']
    dim = 0 if s.get('noir') else max((eio(prog(u, h_.get('t0', .4), h_.get('t0', .4) + .5)) for h_ in hl), default=0) * s.get('dim', .45)
    if dim > 0:
        sh = Image.new('RGBA', out.size, (0, 0, 0, int(255 * dim))); m = Image.new('L', out.size, 255); dm = ImageDraw.Draw(m)
        for h_ in hl:
            x0, y0, x1, y1 = h_['box']; dm.rectangle([x0 * Wd - 14, y0 * Hd - 10, x1 * Wd + 14, y1 * Hd + 10], fill=0)
        sh.putalpha(Image.fromarray((np.asarray(m).astype(float) * dim).astype(np.uint8))); out.alpha_composite(sh)
    for h_ in hl:
        t0 = h_.get('t0', .4); pr = eio(prog(u, t0, t0 + h_.get('dur', .7)))
        x0, y0, x1, y1 = h_['box']; bx = (int(x0 * Wd), int(y0 * Hd), int(x1 * Wd), int(y1 * Hd))
        if pr <= 0: continue
        xe = int(bx[0] + (bx[2] - bx[0]) * pr); reg = (bx[0], bx[1], max(bx[0] + 1, xe), bx[3])
        crop = bold.crop(reg).convert('RGB'); col = Image.new('RGB', crop.size, tuple(h_.get('color', HL_COLOR)))
        out.paste(ImageChops.multiply(crop, col).convert('RGBA'), reg[:2])
    return out

@functools.lru_cache(maxsize=8)
def article_base(name, noir):
    """Returns (page, bold): page = sharp, regular-weight text (noir-graded if asked); bold = the same page with a light bold, used only on highlighted lines."""
    im = img(name, False).convert('RGB'); im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im = ImageEnhance.Contrast(im.filter(ImageFilter.UnsharpMask(3, 140, 2))).enhance(1.15)
    sharp = im.point(lambda v: 0 if v < 70 else (255 if v > 225 else v))
    thick = sharp.filter(ImageFilter.MinFilter(3))
    bold = Image.blend(sharp, thick, .55).point(lambda v: 0 if v < 90 else (255 if v > 220 else v)).convert('RGBA')   # light bold, not heavy
    page = sharp.convert('RGBA')
    if noir:
        rgb = ImageEnhance.Brightness(ImageEnhance.Color(sharp).enhance(0)).enhance(.72); page = rgb.convert('RGBA')
    return page, bold

def follow_pos(s, u, h, ar):
    """Camera follows the highlighter: glides along each marked line while it is being marked, then moves to the next line."""
    hv = 540 / (h * ar) * s.get('follow_margin', .78); keys = []
    for h_ in s['highlight']:
        x0, y0, x1, y1 = h_['box']; cy = (y0 + y1) / 2; t0 = h_.get('t0', .4); du = h_.get('dur', .7)
        if x1 - x0 <= 2 * hv: a = b = (x0 + x1) / 2
        else: a, b = x0 + hv, x1 - hv
        keys += [(t0, a, cy), (t0 + du, b, cy)]
    if u <= keys[0][0]: return keys[0][1], keys[0][2]
    for (ta, xa, ya), (tb, xb, yb) in zip(keys, keys[1:]):
        if u <= tb:
            k = eio(prog(u, ta, tb)); return lerp(xa, xb, k), lerp(ya, yb, k)
    return keys[-1][1], keys[-1][2]

def macro3d(c, u, d, s):
    """Macro close-up on a tilted card plane with depth of field. from/to: {fx, fy, h, rot, tx, ty}; focus: {axis, at, width}; dof: blur px."""
    nx = CFG['scenes'][CFG['scenes'].index(s) + 1] if s is not CFG['scenes'][-1] else {}
    T = d + nx.get('xfade_in', CFG.get('xfade', .45)); x = prog(u, 0, T); p = x * x * (3 - 2 * x) * .6 + x * .4
    a, b = s['from'], s['to']; g = lambda k, dv: lerp(a.get(k, dv), b.get(k, a.get(k, dv)), p)
    src = img(s['img'], s.get('card', True))
    if s.get('highlight'): src = highlight_src(src, s, u)
    ar = src.width / src.height; h = g('h', 2600); fx, fy = g('fx', .5), g('fy', .4)
    if s.get('follow') and s.get('highlight'): fx, fy = follow_pos(s, u, h, ar)
    tx, ty = g('tx', 0), g('ty', 0)      # tx > 0: right side recedes; ty > 0: top recedes
    yw, pt, f = math.radians(tx * 40), math.radians(ty * 40), s.get('focal', 2300)   # true 3D rotation of the plane: no stretching
    q = []; m = s.get('plane', 1.)   # plane > 1: the card lies on a bigger surface, so steep fly-over angles never show the plane's edge
    for X, Y in [(-W / 2 * m, -H / 2 * m), (W / 2 * m, -H / 2 * m), (W / 2 * m, H / 2 * m), (-W / 2 * m, H / 2 * m)]:
        X1, Z1 = X * math.cos(yw), X * math.sin(yw); Y2 = Y * math.cos(pt) + Z1 * math.sin(pt); Z2 = Z1 * math.cos(pt) - Y * math.sin(pt)
        q.append((f * X1 / (f + Z2), f * Y2 / (f + Z2)))
    k = 1.
    if s.get('cover', True) and m == 1:   # full-bleed close-ups: scale evenly (both axes) until the tilted plane covers the frame
        k = max(W / 2 / min(abs(x_) for x_, _ in q), H / 2 / min(abs(y_) for _, y_ in q)) * 1.01
    q = [(x_ * k + W / 2, y_ * k + H / 2) for x_, y_ in q]
    e0x, e0y = W / 2 * (1 - m), H / 2 * (1 - m); e1x, e1y = W / 2 * (1 + m), H / 2 * (1 + m)
    Hp = np.append(persp_coeffs(q, [(e0x, e0y), (e1x, e0y), (e1x, e1y), (e0x, e1y)]), 1).reshape(3, 3)      # output -> flat frame
    sc = h / src.height; th = math.radians(g('rot', 0)); C = (540 - (fx - .5) * h * ar, H / 2 - (fy - .5) * h)
    ca, sa = math.cos(th), math.sin(th)                                                        # flat frame -> source pixels (one warp, fast)
    A = np.array([[ca / sc, -sa / sc, 0], [sa / sc, ca / sc, 0], [0, 0, 1.]]) @ np.array([[1, 0, -C[0]], [0, 1, -C[1]], [0, 0, 1.]])
    A = np.array([[1, 0, src.width / 2], [0, 1, src.height / 2], [0, 0, 1.]]) @ A
    M = A @ Hp; M = M / M[2, 2]
    warped = Image.new('RGBA', (W, H), (10, 10, 10, 255)); warped.alpha_composite(src.transform((W, H), Image.PERSPECTIVE, tuple(M.reshape(9)[:8]), Image.BICUBIC))
    dof = s.get('dof', 10)
    if dof:
        fo = s.get('focus', {}); sm = warped.resize((W // 3, H // 3), Image.BILINEAR).filter(ImageFilter.GaussianBlur(dof / 3)).resize((W, H), Image.BILINEAR)
        warped = Image.composite(sm, warped, dof_mask(fo.get('axis', 'y'), round(lerp(fo.get('at', .45), fo.get('at1', fo.get('at', .45)), p), 2), fo.get('width', .3), 0))
    c.paste(warped, (0, 0))
    if s.get('spot'):
        sp = s['spot']; c.alpha_composite(spot_layer(sp.get('w', 1050), sp.get('h', 380), sp.get('dark', .78), round(.5 + .5 * math.sin(u * 7) * sp.get('flicker', .04), 2)))
    FRAME_BOXES[:] = [bx for bx in FRAME_BOXES if bx[0] != 'card']

@functools.lru_cache(maxsize=32)
def spot_layer(w, h, dark, fl):
    """Spotlight on the line being read (frame centre) + heavy vignette closing in from the edges."""
    q = 4; yy, xx = np.mgrid[0:H // q, 0:W // q]; x = (xx * q - W / 2) / (w / 2); y = (yy * q - H / 2) / (h / 2)
    r = np.sqrt(x * x + y * y); m = np.clip((r - .75) / 1.6, 0, 1) ** .9
    e = np.hypot((xx * q - W / 2) / (W / 2), (yy * q - H / 2) / (H / 2)); m = np.clip(m + np.clip(e - .85, 0, 1) * .8, 0, 1)
    a = (m * 255 * (dark + (fl - .5) * .1)).clip(0, 255).astype(np.uint8)
    lay = Image.new('RGBA', (W, H), (4, 3, 2, 0)); lay.putalpha(Image.fromarray(a).resize((W, H), Image.BILINEAR)); return lay

def macro3d_sfx(d, s): return []
def macro3d_keys(d, s): return [(d * .1, 'macro start'), (d * .9, 'macro end')]

def project_layer(lay, tx=0, ty=0, cover=True, f=2300):
    """Tilt a full-frame layer in true 3D (no stretching)."""
    yw, pt = math.radians(tx * 40), math.radians(ty * 40); q = []
    for X, Y in [(-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2), (-W / 2, H / 2)]:
        X1, Z1 = X * math.cos(yw), X * math.sin(yw); Y2 = Y * math.cos(pt) + Z1 * math.sin(pt); Z2 = Z1 * math.cos(pt) - Y * math.sin(pt)
        q.append((f * X1 / (f + Z2), f * Y2 / (f + Z2)))
    k = max(W / 2 / min(abs(x_) for x_, _ in q), H / 2 / min(abs(y_) for _, y_ in q)) * 1.01 if cover else 1.
    q = [(x_ * k + W / 2, y_ * k + H / 2) for x_, y_ in q]
    return lay.transform((W, H), Image.PERSPECTIVE, tuple(persp_coeffs(q, [(0, 0), (W, 0), (W, H), (0, H)])), Image.BICUBIC)

def glitch(c, amt, seed):
    """Short digital glitch: RGB split + a few displaced horizontal bands."""
    r, g, b, a = c.split(); amt = int(amt)
    c = Image.merge('RGBA', (ImageChops.offset(r, -amt, 0), g, ImageChops.offset(b, amt, int(amt * .3)), a))
    rng = np.random.default_rng(seed)
    for _ in range(5):
        y0 = int(rng.uniform(0, H - 60)); hb = int(rng.uniform(14, 70)); dx = int(rng.uniform(-1, 1) * amt * 3)
        band = c.crop((0, y0, W, y0 + hb)); c.paste(ImageChops.offset(band, dx, 0), (0, y0))
    return c

def card_wall(c, u, d, s):
    """Full-screen wall of cards on black: even spacing, slow drift, gentle 3D tilt that changes axis, black fades top/bottom."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cards = s['cards']; th = s.get('tile_h', 330); cols = s.get('cols', 4)
    gx, gy = s.get('gap_x', 262), th * 1.06; dr = s.get('drift', [0, -260]); p = prog(u, 0, d + .5)
    ox, oy = dr[0] * p, dr[1] * p
    for r_ in range(-2, 9):
        for k_ in range(-1, cols + 1):
            idx = (r_ * (cols + 2) + k_) % len(cards); x = 540 + (k_ - (cols - 1) / 2) * gx + ox + (gx / 2 if r_ % 2 else 0); y = 160 + r_ * gy + oy
            if -th < y < H + th and -200 < x < W + 200:
                ap = prog(u, .02 * ((r_ + 2) * 3 + k_ + 1), .02 * ((r_ + 2) * 3 + k_ + 1) + .35)
                put(lay, cards[idx], x, y - OY, th, alpha=ap, shadow=False, role='fx')
    tl = s.get('tilt', {}); tx = lerp(tl.get('tx0', 0), tl.get('tx1', 0), eio(p)); ty = lerp(tl.get('ty0', .12), tl.get('ty1', .05), eio(p))
    c.alpha_composite(project_layer(lay, tx, ty, cover=False, f=1900))
    yy = np.linspace(0, 1, H)[:, None]; fade = np.clip(np.maximum((.22 - yy) / .22, (yy - .7) / .3), 0, 1) ** 1.2
    fl = Image.new('RGBA', (W, H), (10, 10, 10, 0)); fl.putalpha(Image.fromarray((np.repeat(fade, W, 1) * 255).astype(np.uint8))); c.alpha_composite(fl)
    FRAME_BOXES[:] = [bx for bx in FRAME_BOXES if bx[0] != 'card']

def card_wall_sfx(d, s): return []
def card_wall_keys(d, s): return [(d * .3, 'wall'), (d * .9, 'wall end')]

def slam(c, u, d, s):
    """Big word slams in (scale-down + shake), over dimmed grey cards. words: [..], cards: [imgs]."""
    for j, name in enumerate(s.get('cards', [])):
        x = 540 + (j - (len(s['cards']) - 1) / 2) * 300; put(c, name, x, 760 + 20 * math.sin(u * 2 + j), 400, angle=(j - 1) * 4, alpha=.55, role='fx')
    c.alpha_composite(tint_layer(tuple(CFG.get('slam_tint', (150, 10, 25))), .55))
    for j, w_ in enumerate(s['words']):
        t0 = s.get('at', .05) + j * .22; p = prog(u, t0, t0 + .16)
        fs = min(170, int(170 * 940 / max(1, font(F_BLACK, 170).getlength(w_))))
        if p > 0: put_text(c, w_, 540, 700 + j * 190 - (len(s['words']) - 1) * 95, F_BLACK, int(lerp(fs * 1.5, fs, eo3(p))), fill=tuple(CFG.get('slam_color', (255, 70, 80))) if j == len(s['words']) - 1 else PAPER, stroke=10, alpha=p, record=False)

def wall(c, u, d, s):
    """The 'top 300' wall: rows of blacked-out finalist cards scrolling on a tilted plane; counter; rapid ✗ stamps; AI glitch bursts."""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); imgs = s['cards']; th = s.get('tile_h', 250); cols, gap = 5, 205
    scroll = lerp(0, s.get('scroll', 420), prog(u, 0, d)); xs = s.get('x_at', 2.2); xstep = s.get('x_step', .17); xi = s.get('x_tiles', [])
    red = prog(u, xs, xs + 1.2)
    for r_ in range(-1, 12):
        for k_ in range(cols):
            idx = r_ * cols + k_; x = 540 + (k_ - 2) * gap; y = 120 + r_ * 285 - scroll + (60 if k_ % 2 else 0)
            if y < -200 or y > H + 200: continue
            ap = prog(u, .05 + (r_ * cols + k_) * .012, .3 + (r_ * cols + k_) * .012)
            put(lay, 'mystery:' + imgs[idx % len(imgs)], x, y - OY, th, alpha=ap * (1 - .45 * red * (idx not in xi)), shadow=False, role='fx')
    for j, idx in enumerate(xi):
        r_, k_ = divmod(idx, cols); x = 540 + (k_ - 2) * gap; y = 120 + r_ * 285 - scroll + (60 if k_ % 2 else 0)
        put_stamp(lay, 'x', x, y - OY, u, xs + j * xstep, size=.7, angle=-12 + 9 * (j % 3))
    c.alpha_composite(project_layer(lay, 0, s.get('tilt', .2), cover=False, f=1900))
    if red > 0: c.alpha_composite(tint_layer((170, 10, 30), round(red * .45, 2)))
    cv = s.get('counter')
    if cv:
        n = int(cv * eio(prog(u, .15, s.get('count_end', 2.0))))
        put_text(c, 'TOP', 540, 360, F_BLACK, 70, stroke=7, record=False)
        put_text(c, str(n), 540, 500, F_BLACK, 190, fill=(255, 216, 77) if red < .5 else (255, 80, 90), stroke=10, record=False)

def slam_sfx(d, s): return []
def slam_keys(d, s): return [(min(d - .05, .7), 'slam')]
def wall_sfx(d, s): return []
def wall_keys(d, s):
    xs = s.get('x_at', 2.2); g = s.get('glitch', [[d - 1, d - .8]])[0]
    return [(1.0, 'counter'), (xs + .9, 'disqualified'), ((g[0] + g[1]) / 2, 'glitch')]


# ---------------------------------------------------------------- v3.3 "Ranked Countdown" scenes
@functools.lru_cache(None)
def outline_num(text, size, sw=7):
    """Hollow outlined numeral (brand white stroke, transparent inside)."""
    f = font(F_BLACK, size); bb = f.getbbox(text, stroke_width=sw)
    solid = Image.new('L', (bb[2] - bb[0] + 12, bb[3] - bb[1] + 12), 0); inner = solid.copy()
    ImageDraw.Draw(solid).text((6 - bb[0], 6 - bb[1]), text, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    ImageDraw.Draw(inner).text((6 - bb[0], 6 - bb[1]), text, font=f, fill=255)
    a = ImageChops.subtract(solid, inner.filter(ImageFilter.MinFilter(3)))
    im = Image.new('RGBA', solid.size, PAPER + (0,)); im.putalpha(a); return im

def rank(c, u, d, s):
    """Countdown beat. Giant outlined rank numeral behind a card that swings in in true 3D; the counter rolls to the exact count.
    n, img, count, unit (small line under the count), enter: left|right|top|bottom, side: 1|-1 (which side the numeral peeks out),
    swing: [tx0, ty0, tx1, ty1], h, count_at, count_dur."""
    side = s.get('side', 1); hh = s.get('h', 800); ea = s.get('enter_at', 0); p = eo3(prog(u, ea, ea + .75))
    num = outline_num(str(s['n']), s.get('num_size', 900))
    nx = 540 + side * lerp(250, 205, prog(u, 0, d)); na = .34 * prog(u, 0, .4)
    paste_safe(c, with_alpha(num, na), int(nx - num.width / 2), int(640 + OY - num.height / 2))
    ex, ey = {'left': (-950, 0), 'right': (950, 0), 'top': (0, -1350), 'bottom': (0, 1350)}[s.get('enter', 'left')]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if p > 0: put(lay, s['img'], 540 - side * 105 + ex * (1 - p), 660 + ey * (1 - p), hh + 26 * prog(u, 0, d), sweep=prog(u, ea + 1.0, ea + 1.9))
    sw = s.get('swing', [.32 * side, 0, .05 * side, 0]); q = eio(prog(u, ea, ea + min(d - ea, 2.4)))
    c.alpha_composite(project_layer(lay, lerp(sw[0], sw[2], q), lerp(sw[1], sw[3], q), cover=False, f=2000))
    t0 = s.get('count_at', .55); cp = prog(u, t0, t0 + s.get('count_dur', 1.7))
    if cp > 0:
        val = int(round(s['count'] * (1 - (1 - cp) ** 4)))
        put_text(c, f'{val:,}', 540, 1190, F_BLACK, 120, alpha=prog(u, t0, t0 + .25))
        if s.get('unit'): put_text(c, s['unit'], 540, 1278, F_B, 28, fill=(190, 190, 190), alpha=prog(u, t0 + .2, t0 + .6))

def rank_sfx(d, s): return []
def rank_keys(d, s): return [(.45, 'card swinging in'), (min(d - .05, s.get('count_at', .55) + s.get('count_dur', 1.7) + .3), 'count settled')]

def bar_race(c, u, d, s):
    """Bars grow at the same speed, so the bigger one visibly overtakes. bars: [{label, value, win}], img (card above, optional),
    max, start, race_dur, source."""
    bars = s['bars']; mx = s.get('max', max(b['value'] for b in bars) * 1.04); t0 = s.get('start', .45)
    speed = max(b['value'] for b in bars) / s.get('race_dur', 2.0); x0, x1 = 110, 970; bh = 74
    has = bool(s.get('img'))
    if has: put(c, s['img'], 540, s.get('cy', 440) + 14 * math.sin(u * 1.1), s.get('h', 590) + 18 * prog(u, 0, d), alpha=prog(u, 0, .35))
    base = s.get('base', 880 if has else 600); step = 215; dd = ImageDraw.Draw(c)
    for i, b in enumerate(bars):
        a = eo3(prog(u, .1 + i * .12, .5 + i * .12))
        if a <= 0: continue
        y = base + i * step + OY; v = min(b['value'], speed * max(0, u - t0)); wb = (x1 - x0) * v / mx
        col = PAPER if b.get('win') else (125, 125, 125)
        put_text(c, b['label'], x0 + text_img(b['label'], F_BLACK, 46, col).width / 2, y - 50 - OY, F_BLACK, 46, fill=col, alpha=a)
        vt = f'{int(v):,}'; put_text(c, vt, x1 - text_img(vt, F_BLACK, 46, col).width / 2, y - 50 - OY, F_BLACK, 46, fill=col, alpha=a)
        dd.rounded_rectangle([x0, y, x1, y + bh], bh // 2, outline=(70, 70, 70), width=3)
        if wb > bh: dd.rounded_rectangle([x0, y, x0 + wb, y + bh], bh // 2, fill=col)
    if s.get('source'): put_text(c, s['source'], 540, base + len(bars) * step - 60, F_B, 28, fill=(190, 190, 190), alpha=prog(u, .6, 1.))

def bar_race_sfx(d, s): return []
def bar_race_keys(d, s):
    t0 = s.get('start', .45); rd = s.get('race_dur', 2.0)
    return [(t0 + rd * .55, 'mid race'), (min(d - .05, t0 + rd + .3), 'finish')]

def leaderboard(c, u, d, s):
    """Ranking board that the whole video keeps coming back to. rows: [{rank, name, value, lit, hide}], title, bars (default true),
    max0 → max1 (the bar scale animates: a 'zoom out' that shrinks earlier bars), scale_at, scale_dur, step."""
    rows = s['rows']; n = len(rows); rh = s.get('row_h', min(196, 1010 // n)); top = 770 - (n - 1) * rh / 2; st = s.get('step', .1)
    vals = [r.get('value', 0) for r in rows]; m0 = s.get('max0', max(vals) or 1); m1 = s.get('max1', m0)
    sa = s.get('scale_at', .8); mx = lerp(m0, m1, eio(prog(u, sa, sa + s.get('scale_dur', 1.5)))); fs = int(min(60, rh * .36)); x0, x1 = 96, 984
    if s.get('title'): put_text(c, s['title'], 540, top - rh * .5 - 62, F_BLACK, 40, alpha=prog(u, 0, .4))
    for i, r in enumerate(rows):
        at = r.get('at', .12 + i * st); a = eo3(prog(u, at, at + .45))
        if a <= 0: continue
        lit = r.get('lit', True); col = PAPER if lit else (105, 105, 105); hide = r.get('hide'); y = top + i * rh + 34 * (1 - a)
        put_text(c, str(r['rank']), x0 + 34, y - 16, F_BLACK, fs, fill=col, alpha=a)
        nm = '?  ?  ?' if hide else r['name']
        put_text(c, nm, x0 + 96 + text_img(nm, F_BLACK, fs, col).width / 2, y - 16, F_BLACK, fs, fill=col, alpha=a)
        if not hide and r.get('value'):
            vt = f"{r['value']:,}"; put_text(c, vt, x1 - text_img(vt, F_XB, int(fs * .8), col).width / 2, y - 16, F_XB, int(fs * .8), fill=col, alpha=a)
        if s.get('bars', True):
            dd = ImageDraw.Draw(c); by = int(y + OY + fs * .62); bw = (x1 - x0) * r.get('value', 0) / mx * eo3(prog(u, at + .15, at + 1.0))
            dd.rectangle([x0, by, x1, by + 3], fill=(55, 55, 55))
            if bw > 2: dd.rectangle([x0, by - 5, min(W, x0 + bw), by + 8], fill=col)
    if s.get('source'): put_text(c, s['source'], 540, top + (n - .5) * rh + 28, F_B, 28, fill=(190, 190, 190), alpha=prog(u, .5, .9))

def leaderboard_sfx(d, s): return []
def leaderboard_keys(d, s):
    sa = s.get('scale_at', .8)
    return [(min(d - .05, sa), 'board'), (min(d - .05, sa + s.get('scale_dur', 1.5) + .4), 'board settled')]


# ---------------------------------------------------------------- v3.3 extra motions (alternatives to card_wall / crowd)
@functools.lru_cache(maxsize=500)
def yaw_card(name, h, yaw):
    """A card turned about its vertical axis in true perspective (no stretching). yaw in degrees."""
    im = scaled(name, h); w, hh = im.size; f = 1500.; th = math.radians(yaw); pts = []
    for X, Y in [(-w / 2, -hh / 2), (w / 2, -hh / 2), (w / 2, hh / 2), (-w / 2, hh / 2)]:
        x1, z = X * math.cos(th), X * math.sin(th); k = f / (f + z); pts.append((x1 * k, Y * k))
    mnx, mny = min(q[0] for q in pts), min(q[1] for q in pts)
    ow, oh = int(max(q[0] for q in pts) - mnx) + 2, int(max(q[1] for q in pts) - mny) + 2
    q = [(x - mnx, y - mny) for x, y in pts]
    return im.transform((ow, oh), Image.PERSPECTIVE, tuple(persp_coeffs(q, [(0, 0), (w, 0), (w, hh), (0, hh)])), Image.BICUBIC)

def coverflow(c, u, d, s):
    """3D carousel: the centre card faces the camera, neighbours turn away and recede; it advances one card per `step` seconds.
    cards, labels (optional big text over the centre card, one per card), step, h."""
    cards = s['cards']; n = len(cards); st = s.get('step', d / n); hh = s.get('h', 820)
    k = min(n - 1, int(u / st)); pos = k + (eio(prog(u, k * st + st * .55, (k + 1) * st)) if k < n - 1 else 0) - .7 * (1 - eo3(prog(u, 0, .7)))
    fade = prog(u, 0, .35)
    for i in sorted(range(n), key=lambda i: -abs(i - pos)):
        o = i - pos; a = abs(o)
        if a > 2.7: continue
        sg = 1 if o > 0 else -1; x = 540 + sg * (min(a, 1) * 350 + max(a - 1, 0) * 150); yaw = round(-max(-1, min(1, o)) * 58 / 2) * 2
        h = int(lerp(hh, hh * .7, min(a, 1)) / 2) * 2; im = yaw_card(cards[i], h, yaw)
        al = fade * lerp(1, s.get('side_alpha', .62), min(a, 1)) * (1 if a < 1.7 else max(0, 2.7 - a))
        cy = s.get('cy', 740); x0, y0 = int(x - im.width / 2), int(cy + OY - im.height / 2); paste_safe(c, with_alpha(im, al), x0, y0)
        if a < .5:
            FRAME_BOXES.append(('card', x0, y0, x0 + im.width, y0 + im.height, h, False))
            lb = s.get('labels')
            if lb and lb[i]: put_text(c, lb[i], x, cy, F_BLACK, s.get('label_size', 300), alpha=fade * (1 - 2 * a), record=False)

def coverflow_sfx(d, s): return []
def coverflow_keys(d, s):
    st = s.get('step', d / len(s['cards'])); return [(st * .45, 'first card'), (st * 1.8, 'turning'), (d - .1, 'last card')]

def deal(c, u, d, s):
    """Cards are dealt from alternating corners and slap down onto a centre pile, each at its own small angle. cards, step, h, start."""
    cards = s['cards']; st = s.get('step', .5); t0 = s.get('start', .15); hh = s.get('h', 760)
    for i, name in enumerate(cards):
        p = prog(u, t0 + i * st, t0 + i * st + .4)
        if p <= 0: break
        e = eo3(p); af = ((i * 37) % 19 - 9) * 1.4; sx = 900 if i % 2 else -900; sy = -760 if i % 3 else 760
        put(c, name, lerp(540 + sx, 540 + ((i * 53) % 41 - 20), e), lerp(s.get('cy', 740) + sy, s.get('cy', 740) + ((i * 29) % 31 - 15), e), lerp(hh * 1.45, hh, e),
            angle=lerp(af + (22 if i % 2 else -22), af, e), alpha=min(1, p * 3), role='fx')

    lg = s.get('logo')
    if lg: put_plate(c, lg['img'], 540, s.get('cy', 740), lg.get('w', 620), prog(u, lg.get('at', d * .55), lg.get('at', d * .55) + .4))

def deal_sfx(d, s): return []
def deal_keys(d, s):
    st = s.get('step', .5); t0 = s.get('start', .15); return [(t0 + st * 1.25, 'second card landing'), (d - .1, 'pile')]

@functools.lru_cache(maxsize=64)
def ring_img(r, frac64, wd=16):
    S = 2; sz = (r + wd) * 2 * S; im = Image.new('RGBA', (sz, sz), (0, 0, 0, 0)); dd = ImageDraw.Draw(im); b = [wd * S // 2, wd * S // 2, sz - wd * S // 2, sz - wd * S // 2]
    dd.arc(b, 0, 360, fill=(70, 70, 70, 255), width=wd * S)
    if frac64: dd.arc(b, -90, -90 + 360 * frac64 / 64, fill=PAPER + (255,), width=wd * S)
    return im.resize((sz // S, sz // S), Image.LANCZOS)

def conveyor(c, u, d, s):
    """Cards ride a belt across the frame in perspective. Each card that reaches the centre restarts the ring timer and ticks the counter.
    cards, period (seconds per card), h, ring: {secs, unit}, counter: {label}, tilt."""
    cards = s['cards']; n = len(cards); per = s.get('period', 1.1); hh = s.get('h', 640); gap = hh * .84
    cyc = u / per; k = int(cyc); fr = cyc - k; shift = (k + eio(prog(fr, .45, 1.))) * gap    # belt moves in steps: hold, then slide
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); m0 = int(shift // gap)
    for m in range(m0 - 3, m0 + 5):
        x = 540 + m * gap - shift; near = max(0, 1 - abs(x - 540) / gap)
        put(lay, cards[m % n], x, 560, hh * (1 + .07 * near), alpha=prog(u, 0, .35) * lerp(.55, 1, near), shadow=near > .5, role='fx')
    xx = np.clip(np.minimum(np.arange(W), W - 1 - np.arange(W)) / 170., 0, 1)[None, :]   # soft fade at both belt ends
    lay.putalpha(Image.fromarray((np.asarray(lay.split()[3]) * xx).astype(np.uint8)))
    tl = s.get('tilt', [.62, .06]); c.alpha_composite(project_layer(lay, tl[0], tl[1], cover=False, f=1700))
    rg = s.get('ring', {}); secs = rg.get('secs', 18); a = prog(u, .25, .6); r = 96
    ri = with_alpha(ring_img(r, int(prog(fr, 0, .45) * 64)), a); paste_safe(c, ri, 372 - ri.width // 2, 1265 - ri.height // 2)
    put_text(c, str(int(round(secs * prog(fr, 0, .45)))), 372, 1255 - OY, F_BLACK, 62, alpha=a); put_text(c, rg.get('unit', 'SEC'), 372, 1305 - OY, F_B, 22, fill=(190, 190, 190), alpha=a)
    ct = s.get('counter', {})
    put_text(c, f'+{k + (1 if fr >= .45 else 0)}', 700, 1240 - OY, F_BLACK, 120, alpha=a, scale=1 + .12 * (1 - eo3(prog(fr, .45, .7))) * (fr >= .45))
    if ct.get('label'): put_text(c, ct['label'], 700, 1330 - OY, F_B, 26, fill=(190, 190, 190), alpha=a)

def conveyor_sfx(d, s): return []
def conveyor_keys(d, s):
    per = s.get('period', 1.1); return [(per * 1.3, 'timer running'), (per * 2.75, 'belt sliding'), (d - .1, 'counter')]


@functools.lru_cache(maxsize=64)
def plate_img(name, w):
    """A supplied logo on a white rounded plate (keeps the logo's own colours; never redraw or recolour a third-party logo)."""
    lg = Image.open(apath(name)).convert('RGBA'); wb = Image.new('RGBA', lg.size, (255, 255, 255, 255)); wb.alpha_composite(lg); lg = wb.convert('RGB'); lw = int(w * .84); lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    h = lg.height + int(w * .12); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], int(h * .16), fill=(255, 255, 255, 255)); im.paste(lg, ((w - lw) // 2, (h - lg.height) // 2)); return im

def put_plate(c, name, cx, cy, w, p):
    if p <= 0: return
    k = lerp(.55, 1, eback(min(1, p))); im = plate_img(name, int(w / 2) * 2)
    im = im.resize((max(2, int(im.width * k)), max(2, int(im.height * k))), Image.LANCZOS)
    x, y = int(cx - im.width / 2), int(cy + OY - im.height / 2); paste_safe(c, with_alpha(im, min(1, p * 2.5)), x, y)
    if p >= 1: FRAME_BOXES.append(('text', x, y, x + im.width, y + im.height, 0, False))

def logo_stat(c, u, d, s):
    """A supplied logo on a white plate pops in, then stat lines rise in under it. img, w, lines: [big, small, small], at."""
    for j, name in enumerate(s.get('cards', [])[:2]):   # two big cards behind the plate, mirrored, running off the frame edges
        sg = -1 if j == 0 else 1; e = eo3(prog(u, .05 + j * .12, .7 + j * .12))
        put(c, name, 540 + sg * lerp(760, 330, e) + sg * 14 * prog(u, 0, d), s.get('cards_y', 700), s.get('cards_h', 980), angle=-sg * 8, alpha=s.get('cards_alpha', .3) * e, shadow=False, role='fx')
    t0 = s.get('at', .15); put_plate(c, s['img'], 540, s.get('cy', 520) - 12 * prog(u, 0, d), s.get('w', 700), prog(u, t0, t0 + .45))
    spec = [(190, 0), (64, 150), (64, 232)]
    for i, ln in enumerate(s.get('lines', [])[:3]):
        sz, dy = spec[i]; q = eo3(prog(u, t0 + .55 + i * .22, t0 + 1.0 + i * .22))
        if q > 0: put_text(c, ln, 540, s.get('cy', 520) + 330 + dy + 40 * (1 - q), F_BLACK, sz, alpha=q)

def logo_stat_sfx(d, s): return []
def logo_stat_keys(d, s): return [(s.get('at', .15) + .3, 'logo in'), (min(d - .05, s.get('at', .15) + 1.9), 'stat')]

SCENE_TYPES = ['logo_stat', 'coverflow', 'deal', 'conveyor', 'rank', 'bar_race', 'leaderboard', 'card_wall', 'slam', 'wall', 'macro3d', 'broll', 'hook_mystery', 'hero_stamp', 'product_intro', 'card_grid', 'card_lineup', 'reveal_zoom', 'artist',
               'featured_cards', 'stat_chart', 'cta_product', 'end_card']
SCENES = {k: (globals()[k], globals()[k + '_sfx']) for k in SCENE_TYPES}
KEYS = {k: globals()[k + '_keys'] for k in SCENE_TYPES}
NO_LOGO = {'end_card'}
FLOW = {'broll', 'macro3d'}   # keeps moving under the dissolve into the next scene
NO_CAPTION = {'end_card'}   # full-bleed CTA poster: VO plays, caption not burned in

# ---------------- soft sound mode ("sfx_style": "soft") ----------------
def soft_sfx(d, s):
    """Gentle sounds on every card motion. swoosh = airy move, tap = light card tap, drop = water drop (badges/tags)."""
    t = s['type']; ev = []
    if t == 'broll': ev = [(0, 'swoosh', .5)]
    elif t == 'hero_stamp': ev = [(0, 'swoosh', .6), (d * .5, 'swoosh', .35)]          # card arrives, shine sweep
    elif t == 'card_grid': ev = [(.15 + i * s['soft'], 'swoosh', .35) for i in range(len(s['cards']))] if s.get('soft') else [(.1 + i * .08, 'tap', .55) for i in range(len(s['cards']))]
    elif t == 'artist': ev = [(.1, 'drop', 1.)]
    elif t == 'featured_cards':
        per = d / len(s['cards']); ev = [(j * per, 'swoosh', .7) for j in range(len(s['cards']))]
    elif t == 'reveal_zoom':
        ev = [(0, 'swoosh', .5)]
        if s.get('zoom') and s.get('zoom_at', 0) > 0:
            ev += ([(1.0, 'tap', .5, 'hl')] if s['zoom_at'] > 1.3 else []) + [(s['zoom_at'], 'swoosh', .7)] + ([(s['zoom_at'] + .5, 'drop', .8, 'hl')] if s['zoom'].get('tag') else [])
    elif t in ('card_lineup', 'product_intro', 'cta_product'): ev = [(0, 'swoosh', .7)]
    elif t == 'end_card': ev = [(0, 'swoosh', .4)]
    elif t == 'macro3d': ev = [(0, 'swoosh', .45)]
    elif t == 'slam': ev = [(s.get('at', .05) + j * .22, 'impact', .55 if j == len(s['words']) - 1 else .35) for j in range(len(s['words']))]
    elif t == 'wall':
        ev = [(.15, 'typing', .45)] + [(s.get('x_at', 2.2) + j * s.get('x_step', .17), 'stamp', .4) for j in range(len(s.get('x_tiles', [])))]
        ev += [(g0, 'tick', .6) for g0, _ in s.get('glitch', [])]
    elif t == 'logo_stat': ev = [(s.get('at', .15), 'shutter', .45)]
    elif t == 'coverflow': ev = [(i * s.get('step', d / len(s['cards'])) + s.get('step', d / len(s['cards'])) * .55, 'swoosh', .3) for i in range(len(s['cards']) - 1)]
    elif t == 'deal': ev = [(s.get('start', .15) + i * s.get('step', .5) + .3, 'tap', .45) for i in range(len(s['cards'])) if s.get('start', .15) + i * s.get('step', .5) + .3 < d]
    elif t == 'conveyor': ev = [((i + .45) * s.get('period', 1.1), 'shutter', .3) for i in range(int(d / s.get('period', 1.1)))]
    elif t == 'rank': ev = [(s.get('enter_at', 0), 'swoosh', .55), (s.get('count_at', .55) + s.get('count_dur', 1.7), 'shutter', .4)]
    elif t == 'bar_race': ev = [(s.get('start', .45), 'swoosh', .3), (s.get('start', .45) + s.get('race_dur', 2.0), 'coin', .35)]
    elif t == 'leaderboard': ev = [(r.get('at', .12 + i * s.get('step', .1)), 'tap', .3) for i, r in enumerate(s['rows'])]
    bsx = CFG.get('badge_sfx')
    ev += [(b['at'], bsx, .55) for b in s.get('badges', [])] if bsx else [(b['at'], 'drop', .7, 'hl') for b in s.get('badges', [])]
    if CFG.get('cut_sfx') and s is not CFG['scenes'][0]: ev += [(0, CFG['cut_sfx'], .45)]
    return ev

def scene_sfx(s):
    if CFG.get('sfx_style') != 'soft': return SCENES[s['type']][1](s['dur'], s)
    ev = soft_sfx(s['dur'], s)
    if CFG.get('highlight_sfx_once'):   # highlight sounds (circle tap, tag/badge drop) only the first time each kind appears
        seen = set()
        for p in CFG['scenes']:
            if p is s: break
            seen |= {e[1] for e in soft_sfx(p['dur'], p) if len(e) > 3}
        out = []
        for e in sorted(ev):
            if len(e) > 3:
                if e[1] in seen: continue
                seen.add(e[1])
            out.append(e)
        ev = out
    ev = [e[:3] for e in ev] + [tuple(e) for e in s.get('sfx', [])]   # per-scene extra sounds: [[t, name, gain]]
    return ev

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
    if CFG.get('caption_style') == 'plain': return caption_plain(text, CFG.get('caption_size', 50))
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

@functools.lru_cache(None)
def caption_plain(text, size):
    """thefinecard-style caption: plain white, no highlight colours, soft dark shadow instead of a heavy stroke."""
    f = font(F_XB, size); lines = wrap(text, f, CAPTION_MAXW); lh = int(size * 1.22)
    im = Image.new('RGBA', (CAPTION_MAXW + 60, lh * len(lines) + 40), (0, 0, 0, 0)); sh = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(im); ds = ImageDraw.Draw(sh)
    for i, ln in enumerate(lines):
        t = ' '.join(ln); x = (im.width - f.getlength(t)) / 2; y = 20 + i * lh
        ds.text((x, y + 3), t, font=f, fill=200, stroke_width=3); d.text((x, y), t, font=f, fill=PAPER + (255,))
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0)); shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(6)))
    shadow.alpha_composite(im); return shadow

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
    """Returns (text, start_local, size, end_local) currently visible."""
    cap = s.get('caption')
    if not cap: return None
    if CFG.get('caption_mode', 'lines') != 'chunks': return cap, .3 if s is CFG['scenes'][0] else 0, 60, d
    a, b = s.get('vo_window', [.1, d - .15]); parts = chunks(cap, CFG.get('chunk_words', 4))
    if u < a - .05: return None
    if s.get('chunk_at'):                                 # explicit chunk start times (local seconds), e.g. to hold back a reveal
        parts = s.get('chunk_text') or parts; st = s['chunk_at']
        for i, p_ in enumerate(parts):
            end = st[i + 1] if i + 1 < len(parts) else max(b + .25, st[i] + .6)
            if st[i] - .05 <= u < end: return p_, st[i], 72, end
        return None
    L = sum(len(p) for p in parts); t = a
    for i, p in enumerate(parts):
        dt = (b - a) * len(p) / L
        end = t + dt if i < len(parts) - 1 else max(b + .25, t + dt)
        if u < end: return p, t, 72, end
        t += dt
    return None

def draw_caption(c, text, u, t0, size, t1=None, rec=True):
    """Soft caption: fades and rises in; when the next chunk follows, the old one fades out quickly."""
    im = caption_img(text, size); fi = eo3(prog(u, t0, t0 + .28))
    fo = 1 - prog(u, t1 - .14, t1) if t1 is not None else 1
    a = fi * fo
    if a <= .01: return
    im = with_alpha(im, a); x, y = int(W / 2 - im.width / 2), int(CAPTION_Y - im.height / 2 + 18 * (1 - fi))
    paste_safe(c, im, x, y)
    if rec:
        bb = im.getbbox() or (0, 0, 0, 0); FRAME_BOXES.append(('caption', x + bb[0], y + bb[1], x + bb[2], y + bb[3], 0, False))

def scene_layer(i, t, u):
    """Background + scene drawing + badges for scene i at local time u (no caption, no logo)."""
    s = CFG['scenes'][i]; d = s['dur']; NOW[0] = t; c = background(t); fx_layers(c, s, t, u); SCENES[s['type']][0](c, u, d, s)
    if s.get('mono'):   # desaturate (e.g. the "normal" version), optional fade-in time
        m = prog(u, s.get('mono_at', 0), s.get('mono_at', 0) + .4) if s.get('mono_at') else 1
        g = c.convert('L').convert('RGBA'); c = Image.blend(c, g, m * (s['mono'] if isinstance(s['mono'], float) else 1.))
    bs = s.get('badges', [])
    for k, b in enumerate(bs):
        end = bs[k + 1]['at'] if k + 1 < len(bs) else d
        if b['at'] <= u < end + .001:
            out = prog(u, end - .2, end) if k + 1 < len(bs) else 0
            put_chip(c, b['text'], 540, b.get("y", 288 - OY), prog(u, b['at'], b['at'] + .3) * (1 - out), bg=(PAPER if CFG.get('mono_ui') else YELLOW) if b.get('hl') else PAPER, size=b.get('size', 34))
    return c

@functools.lru_cache(None)
def rays_img():
    S = 2600; im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im); c = S / 2; n = 22
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = a0 + 2 * math.pi / n * .42
        d.polygon([(c, c), (c + S * math.cos(a0), c + S * math.sin(a0)), (c + S * math.cos(a1), c + S * math.sin(a1))], fill=255)
    yy, xx = np.mgrid[0:S, 0:S]; r = np.hypot(xx - c, yy - c) / (S / 2)
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(18))).astype(float) * np.clip(1.15 - r, 0, 1)
    return Image.fromarray(a.astype(np.uint8))

@functools.lru_cache(None)
def tint_layer(rgb, strength):
    yy, xx = np.mgrid[0:H:8, 0:W:8]; r = np.clip(1.25 - np.hypot((xx - W / 2) / W, (yy - H * .4) / H) * 1.6, 0, 1)
    a = Image.fromarray((r * 255 * strength).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    lay = Image.new('RGBA', (W, H), tuple(rgb) + (0,)); lay.putalpha(a); return lay

@functools.lru_cache(maxsize=32)
def crowd_strip(names, h, k, blur):
    """One vertical column of cards for the moving crowd background (cached)."""
    sp = int(h * 1.08); n = max(len(names), int(H * 2 / sp) + 2); n -= n % len(names) if n > len(names) else 0
    n = max(n, int(H / sp) + 2); col = Image.new('RGBA', (int(h * .75) + 20, n * sp), (0, 0, 0, 0))
    for j in range(n):
        nm = names[(j * 3 + k * 5) % len(names)]; im = scaled(nm, h, 0, True)
        col.alpha_composite(im, ((col.width - im.width) // 2, j * sp + (sp - h) // 2))
    return col.filter(ImageFilter.GaussianBlur(blur)) if blur else col

def crowd(c, s, t):
    """Moving crowd of cards behind the scene: columns drift up/down in opposite directions, dimmed and soft."""
    cr = s.get('crowd')
    if not cr: return
    names = tuple(cr['cards']); h = cr.get('h', 300); cols = cr.get('cols', 5); sp = W / (cols - 1)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for k in range(cols + 1):
        st = crowd_strip(names, h, k, cr.get('blur', 2)); dy = (t * cr.get('speed', 45) * (1 if k % 2 else -1) * (1 + .15 * (k % 3))) % st.height
        x = int(-sp / 2 + k * sp - st.width / 2 + 20 * math.sin(t * .4 + k))
        y = -dy
        while y < H: paste_safe(lay, st, x, int(y)); y += st.height
    lay = project_layer(lay, cr.get('tx', 0), cr.get('ty', .12), cover=True) if cr.get('tilt', True) else lay
    c.alpha_composite(with_alpha(lay, cr.get('alpha', .3)))
    vg = cr.get('vignette', .55)
    if vg: c.alpha_composite(tint_layer((10, 10, 10), vg))

def fx_layers(c, s, t, u):
    """Upbeat extras behind the scene: per-scene colour tint, slow rotating light rays, drifting confetti."""
    crowd(c, s, t)
    tn = s.get('tint')
    if tn: c.alpha_composite(tint_layer(tuple(tn[:3]), tn[3] if len(tn) > 3 else .45))
    ry = CFG.get('rays')
    if ry:
        R = rays_img().rotate(t * ry.get('speed', 5), resample=Image.BILINEAR); S = R.width
        cy = s.get('rays_y', 700); crop = R.crop((S // 2 - W // 2, S // 2 - int(cy), S // 2 + W // 2, S // 2 - int(cy) + H))
        lay = Image.new('RGBA', (W, H), tuple(ry.get('color', (255, 255, 255))) + (0,)); lay.putalpha(crop.point(lambda v: int(v * ry.get('alpha', .14)))); c.alpha_composite(lay)
    cf = CFG.get('confetti')
    if cf:
        d = ImageDraw.Draw(c); rng = np.random.default_rng(21); cols = [tuple(x) for x in cf.get('colors', [[255, 216, 77], [255, 255, 255], [255, 92, 170], [90, 200, 255]])]
        for k in range(cf.get('n', 26)):
            x0, y0, sp, sz, ph, ci = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(40, 110), rng.uniform(7, 17), rng.uniform(0, 6.3), rng.integers(len(cols))
            y = (y0 - t * sp) % (H + 80) - 40; x = x0 + 26 * math.sin(t * 1.3 + ph); w_ = sz * (.35 + .65 * abs(math.cos(t * 2.2 + ph)))
            al = int(255 * cf.get('alpha', .55))
            if k % 3: d.rounded_rectangle([x - w_ / 2, y - sz / 2, x + w_ / 2, y + sz / 2], 3, fill=cols[ci] + (al,))
            else: d.ellipse([x - sz * .4, y - sz * .4, x + sz * .4, y + sz * .4], fill=cols[ci] + (al,))

@functools.lru_cache(None)
def leak_layer(k):
    a = k / 20; yy, xx = np.mgrid[0:H:8, 0:W:8]; r = np.hypot((xx - W * .75) / W, (yy - H * .3) / H)
    al = Image.fromarray((np.clip(1.1 - r * 1.3, 0, 1) * 235 * a).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    lay = Image.new('RGBA', (W, H), tuple(CFG.get('leak_color', (255, 150, 40))) + (0,)); lay.putalpha(al); return lay

@functools.lru_cache(maxsize=8)
def flare_glow(rgb):
    yy, xx = np.mgrid[0:H // 4, 0:W // 4].astype(float); r = np.hypot(xx - W / 8, yy - H / 8) / (W / 4)
    g = Image.fromarray((np.clip(1 - r, 0, 1) ** 2.2 * 255).astype(np.uint8)).resize((W // 2 * 2, W // 2 * 2), Image.BILINEAR)
    lay = Image.new('RGBA', g.size, tuple(rgb) + (0,)); lay.putalpha(g); return lay

def flare(c, f, u):
    """Warm anamorphic lens flare drifting across the frame (pairs with a fire whoosh). f: {t0, t1, color, y, strength}."""
    t0, t1 = f.get('t0', 0), f.get('t1', 1.6); x = prog(u, t0, t1)
    if x <= 0 or x >= 1: return c
    env = math.sin(math.pi * x) ** 1.2 * f.get('strength', .9); col = tuple(f.get('color', (255, 140, 40)))
    cx = lerp(-150, W + 150, eio(x)); cy = f.get('y', 620) + 60 * math.sin(x * 3)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = flare_glow(col); g = with_alpha(g, env); paste_safe(lay, g, int(cx - g.width / 2), int(cy - g.height / 2))
    core = flare_glow((255, 240, 215)).resize((520, 520)); paste_safe(lay, with_alpha(core, min(1, env * 1.2)), int(cx - 260), int(cy - 260))
    st = Image.new('L', (W, 40), 0); ImageDraw.Draw(st).rectangle([0, 12, W, 28], fill=int(min(255, 255 * env))); st = st.filter(ImageFilter.GaussianBlur(8))
    sl = Image.new('RGBA', (W, 40), col + (0,)); sl.putalpha(st); paste_safe(lay, sl, 0, int(cy - 20))
    for k, (o, r_) in enumerate([(.35, 70), (.6, 40), (.85, 110)]):   # ghost orbs along the flare axis
        gx = lerp(cx, W - cx, o); gy = lerp(cy, H - cy, o * .5); orb = flare_glow(col).resize((r_ * 2, r_ * 2)); paste_safe(lay, with_alpha(orb, env * .5), int(gx - r_), int(gy - r_))
    from PIL import ImageChops as IC
    rgb = IC.screen(c.convert('RGB'), Image.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 255)), lay).convert('RGB'))
    return rgb.convert('RGBA')

def camera(c, s, u, t):
    """Whole-frame camera: punch-in settle at each cut, gentle handheld drift, light colour grade."""
    cm = CFG.get('camera')
    if not cm: return c
    pz = cm.get('punch', .05) * (1 - eo3(prog(u, 0, cm.get('punch_t', .55)))) * s.get('punch', 1)
    br = cm.get('breathe', .012) * (.5 + .5 * math.sin(t * 1.1)); sc = cm.get('base', 1.03) + pz + br
    dx = cm.get('drift', 7) * math.sin(t * .9) + cm.get('drift', 7) * .5 * math.sin(t * 2.3); dy = cm.get('drift', 7) * .7 * math.cos(t * .75)
    shk = s.get('shake', 0) * (1 - prog(u, s.get('shake_at', 0), s.get('shake_at', 0) + .6)) * (u >= s.get('shake_at', 0))
    for g0, g1 in s.get('glitch', []):
        if g0 <= u < g1: shk = max(shk, .5)
    dx += shk * 26 * math.sin(u * 83); dy += shk * 18 * math.cos(u * 71); sc += shk * .03
    cw, ch = W / sc, H / sc; x0, y0 = (W - cw) / 2 + dx, (H - ch) / 2 + dy
    c = c.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR)
    for k_, (g0, g1) in enumerate(s.get('glitch', [])):
        if g0 <= u < g1: c = glitch(c, 14 + 10 * math.sin(u * 40), int(u * 30) + k_)
    g = cm.get('grade')
    if g:
        rgb = c.convert('RGB'); rgb = ImageEnhance.Color(rgb).enhance(g.get('sat', 1.12)); rgb = ImageEnhance.Contrast(rgb).enhance(g.get('contrast', 1.05)); c = rgb.convert('RGBA')
    return c

def caption_panel(c, text, size, alpha):
    im = caption_img(text, size); bb = im.getbbox() or (0, 0, im.width, im.height)
    bw_, bh_ = bb[2] - bb[0] + 70, bb[3] - bb[1] + 50
    pan = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pan).rounded_rectangle([W / 2 - bw_ / 2, CAPTION_Y - bh_ / 2, W / 2 + bw_ / 2, CAPTION_Y + bh_ / 2], 28, fill=(10, 10, 10, int(215 * alpha)))
    c.alpha_composite(pan)

def frame(t):
    FRAME_BOXES.clear(); tl = timeline()
    for i, (t0, t1, s) in enumerate(tl):
        if t0 <= t < t1: break
    else: i = len(tl) - 1; t0, t1, s = tl[i]
    u, d = t - t0, s['dur']; XF = s.get('xfade_in', CFG.get('xfade', .45))
    c = scene_layer(i, t, u)
    mix = 1.
    if i > 0 and u < XF and XF > 0:                     # dissolve from the previous scene's last frame
        pd = tl[i - 1][2]['dur']; pu = pd + u if tl[i - 1][2]['type'] in FLOW else pd - .001
        mix = eio(u / XF); keep = list(FRAME_BOXES); prev = scene_layer(i - 1, t, pu); FRAME_BOXES[:] = keep
        tr = s.get('trans')
        if tr == 'whip':   # whip pan: the new shot slides in from the right as one continuous move, heavy motion blur mid-way
            off = int(W * mix); fr = Image.new('RGBA', (W, H)); fr.paste(prev, (-off, 0)); fr.paste(c, (W - off, 0)); c = fr; bl = math.sin(math.pi * mix)
            if bl > .05: c = Image.blend(c, c.resize((max(8, int(W / (1 + 45 * bl))), H), Image.BILINEAR).resize((W, H), Image.BILINEAR), min(1, bl * 1.3))
        elif tr == 'glitch':   # digital glitch cut: RGB split + band tears, hard switch mid-way
            c = prev if mix < .5 else c; c = glitch(c, 10 + 46 * math.sin(math.pi * mix), int(u * 60))
        elif tr == 'zoom':     # punch-zoom: old shot rushes toward camera and fades, new one settles from slightly large
            z1 = 1 + .35 * mix; z2 = 1.18 - .18 * mix
            def zs(im, z):
                cw, ch = W / z, H / z; return im.transform((W, H), Image.EXTENT, ((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2), Image.BILINEAR)
            c = Image.blend(zs(prev, z1), zs(c, z2), mix); bl = math.sin(math.pi * mix)
            if bl > .1: c = Image.blend(c, c.resize((W // 6, H // 6), Image.BILINEAR).resize((W, H), Image.BILINEAR), bl * .5)
        else: c = Image.blend(prev, c, mix)
        if tr == 'leak':   # warm light-leak flare across the cut
            c.alpha_composite(leak_layer(int(math.sin(math.pi * mix) * 20)))
    c = camera(c, s, u, t)
    if s.get('flare'): c = flare(c, s['flare'], u)
    if s.get('continue_caption'):
        prev = CFG['scenes'][i - 1]; cp = caption_for(prev, prev['dur'] - .01 + u, prev['dur'] + d)
        cp = (cp[0], -9, cp[2], d) if cp else None
    else: cp = caption_for(s, u, d)
    if cp and s['type'] not in NO_CAPTION:
        a = eo3(prog(u, cp[1], cp[1] + .28)) * (1 - prog(u, cp[3] - .14, cp[3]))
        if s.get('caption_bg'): caption_panel(c, cp[0], cp[2], a)
        draw_caption(c, cp[0], u, cp[1], cp[2], cp[3])
    nxt_end = i + 1 < len(tl) and tl[i + 1][2]['type'] in NO_LOGO
    if s['type'] not in NO_LOGO:
        logo(c)
    elif mix < 1:                                        # fade the logo out as the end card dissolves in
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); logo(lay); c.alpha_composite(with_alpha(lay, 1 - mix))
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
        for lt, name, g in scene_sfx(s):
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
        if len(lines) > 1 and len(lines[-1]) == 1 and len(lines[-2]) > 1: lines[-1].insert(0, lines[-2].pop())   # no orphan word
        for i, ln in enumerate(lines): put_text(c, ' '.join(ln), 540, 1560 - OY + i * 110 - (len(lines) - 1) * 55, F_BLACK, 96, fill=(PAPER if CFG.get('mono_ui') else YELLOW), stroke=8)
    logo(c); c.convert('RGB').save(out); print('cover', out)

def cmd_check():
    errs, warns = [], []
    L = total_len()
    mxl = CFG.get('max_len', MAX_LEN)
    if not (MIN_LEN <= L <= mxl): errs.append(f'Length {L:.1f}s is outside {MIN_LEN:.0f}-{mxl:.0f}s')
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
    names = {re.sub(r'^(mystery|flip):', '', n) for n in names}
    if CFG.get('cover', {}).get('img'): names.add(CFG['cover']['img'])
    for n in sorted(names):
        if not os.path.exists(apath(n)): errs.append(f'Missing asset: {n}'); continue
        h = Image.open(apath(n)).height
        if h < 700 and 'avatar' not in n and 'logo' not in n: warns.append(f'Low-res asset ({h}px tall, want >=700): {n}')
    hero = CFG['scenes'][0].get('hero')
    if hero and os.path.exists(apath(hero)) and Image.open(apath(hero)).height < 1000: warns.append(f'Hero card under 1000px tall: {hero}')
    if CFG.get('voiceover') and not os.path.exists(apath(CFG['voiceover'])): errs.append(f'Voiceover file not found: {CFG["voiceover"]}')
    sfx_dir = os.path.join(BASE, CFG.get('sfx_dir', 'sfx'))
    need = sorted({n for _, _, s in timeline() for _, n, _ in scene_sfx(s)})
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

DESC = {'logo_stat': 'Supplied logo on a white plate pops in, stat lines rise in under it',
        'coverflow': '3D carousel: centre card faces camera, neighbours turn away; advances card by card', 'deal': 'Cards dealt from the corners slap down onto a centre pile', 'conveyor': 'Cards ride a belt in perspective; ring timer restarts and counter ticks per card',
        'rank': 'Giant outlined rank numeral behind a card swinging in in 3D; counter rolls to the exact count', 'bar_race': 'Bars race at the same speed; the bigger one overtakes', 'leaderboard': 'Ranking board: rows rise in, bars grow, scale zooms out',
        'hook_mystery': 'Starburst; known versions pop in with ✗; blacked-out mystery card + ?; flash reveal',
        'hero_stamp': 'Hero card push-in + stamp', 'product_intro': 'Box + pack fly in, date types out',
        'card_grid': 'Grid of cards flies in', 'card_lineup': 'Cards fanned side by side with labels',
        'reveal_zoom': 'Wipe to card, circle + arrow, zoom into detail + tag', 'artist': 'Artist avatar centred, name, role, handle',
        'featured_cards': 'Each card full-size one by one, then fan', 'stat_chart': 'Bar chart + counter, then full-screen highlight',
        'slam': 'Big words slam in over dimmed cards, red tint, shake', 'wall': 'Wall of 300 blacked-out finalists on a tilted plane, counter, ✗ stamps, AI glitch', 'macro3d': '3D macro close-up: tilted card plane, depth of field, camera drift', 'cta_product': 'Product slides in + stamp', 'broll': 'Slow left-to-right pan across the card', 'card_wall': 'Full-screen wall of cards on black, slow drift, 3D tilt, black fades top/bottom', 'end_card': 'Full-bleed FOLLOW US! call-to-action poster (store badges)'}

def scene_rows():
    rows = []
    for i, (t0, t1, s) in enumerate(timeline()):
        rows.append({'t': round(t0, 2), 'e': round(t1, 2), 'title': s.get('beat', s['type']), 'vo': s.get('vo', ''), 'cap': s.get('caption', ''),
                     'vis': s.get('visual', DESC[s['type']]), 'sfx': ', '.join(sorted({n for _, n, _ in scene_sfx(s)}))})
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
    if CFG.get('mono_ui'):
        global YELLOW, PINK, RED, GREEN
        YELLOW = PINK = RED = GREEN = PAPER

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
