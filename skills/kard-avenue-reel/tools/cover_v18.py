#!/usr/bin/env python3
"""Video 18 cover (main Reel): card-focused layout (Video 13 style), new background = B/W manga-cover wall."""
import math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
A = 'assets/'
import os
FT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine', 'fonts', 'Telegraf-UltraBold.otf')   # repo font, from any working directory
rng = random.Random(18)


def load(n): return Image.open(A + n).convert('RGBA')


# ---------- background: B/W manga-cover wall tilted in 3D, blurred, dim ----------
covers = [load(n).convert('L') for n in ['m_conan.png', 'm_chiikawa.png', 'm_hokuto.png', 'm_witchhat.png']]
WW, WH = 2600, 3600
wall = Image.new('L', (WW, WH), 8)
tw, th = 520, 760
row = 0
for y in range(-200, WH, th + 40):
    off = (row % 2) * (tw // 2 + 20)
    for x in range(-tw + off, WW, tw + 40):
        cv = covers[rng.randrange(4)].resize((tw, th), Image.LANCZOS)
        cv = Image.eval(cv, lambda v: int(v * rng.uniform(.55, 1.0)))
        wall.paste(cv, (x, y))
    row += 1
wall = np.asarray(wall).astype(np.float32) / 255
src = np.float32([[0, 0], [WW, 0], [WW, WH], [0, WH]])
dst = np.float32([[-420, -260], [W + 420, -260], [W + 1100, H + 200], [-1100, H + 200]])   # tilted back, receding up
M = cv2.getPerspectiveTransform(src, dst)
bg = cv2.warpPerspective(wall, M, (W, H), borderValue=0)
bg = cv2.GaussianBlur(bg, (0, 0), 3.2) * .52
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# halftone dots (manga texture), faint
dots = ((np.sin(xx / 7) * np.sin(yy / 7)) > .55).astype(np.float32) * .035
# soft centre glow in the hero card's colours (Palafin: teal / sea blue)
glow = np.exp(-(((xx - 540) / 520) ** 2 + ((yy - 820) / 600) ** 2))
img = np.dstack([bg] * 3) + dots[..., None]
img += glow[..., None] * np.array([.08, .22, .32], np.float32)
# soft light rays from behind the cards
ang = np.arctan2(yy - 820, xx - 540)
rays = (np.cos(ang * 9) * .5 + .5) ** 6 * np.exp(-((np.hypot(xx - 540, yy - 820)) / 900) ** 2) * .10
img += rays[..., None] * np.array([.7, .9, 1.0], np.float32)
# heavy shadow closing in from the edges
edge = np.clip(np.minimum.reduce([xx, W - xx, yy, H - yy]) / 380, 0, 1) ** 1.3
img *= (.25 + .75 * edge)[..., None]
img *= (1 - .55 * np.clip((yy - 1250) / 670, 0, 1) ** 1.5)[..., None]          # darker under the title
canvas = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')

# bokeh + sparkles
fx = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(fx)
for _ in range(26):
    x, y, r = rng.uniform(0, W), rng.uniform(250, 1250), rng.uniform(10, 34)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(170, 220, 255, int(rng.uniform(18, 45))))
fx = fx.filter(ImageFilter.GaussianBlur(6))
canvas.alpha_composite(fx)
sp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sp)
for _ in range(70):
    x, y = rng.uniform(40, W - 40), rng.uniform(260, 1240); r = rng.uniform(1, 3)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, int(rng.uniform(80, 200))))
canvas.alpha_composite(sp.filter(ImageFilter.GaussianBlur(.6)))


def card(name, h, cx, cy, rot, glow_rgb, glow_a=150):
    c = load(name); c = c.resize((int(c.width * h / c.height), h), Image.LANCZOS)
    pad = 160
    lay = Image.new('RGBA', (c.width + pad * 2, c.height + pad * 2), (0, 0, 0, 0))
    a = c.split()[3]
    # heavy soft shadow
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 215), (pad + 18, pad + 40), a)
    sh = sh.filter(ImageFilter.GaussianBlur(38))
    # glow
    gl = Image.new('RGBA', lay.size, (0, 0, 0, 0)); gl.paste(glow_rgb + (glow_a,), (pad, pad), a)
    gl = gl.filter(ImageFilter.GaussianBlur(44))
    lay.alpha_composite(gl); lay.alpha_composite(sh); lay.alpha_composite(c, (pad, pad))
    lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


CY = 800
card('c_simisear.png', 760, 150, CY - 10, 8, (255, 150, 110))       # left, leans out, runs off the edge
card('c_glaceon.png', 760, 930, CY - 10, -8, (150, 210, 255))       # right, mirrored
# hero: Tetsuo Hara holding his Crasher Wake's Passion card (photo cut-out, fades out at the bottom)
hp = load('x_hara_cut.png'); PH = 1230
hp = hp.resize((int(hp.width * PH / hp.height), PH), Image.LANCZOS)
ha = np.asarray(hp.split()[3]).astype(np.float32)
fy = np.linspace(0, 1, PH)[:, None]
ha *= np.clip((1 - fy) / .06, 0, 1)                              # body stays solid; only the photo's bottom edge softens
hp.putalpha(Image.fromarray(ha.astype(np.uint8)))
pad = 120; lay = Image.new('RGBA', (hp.width + pad * 2, PH + pad * 2), (0, 0, 0, 0))
sh = Image.new('RGBA', lay.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 200), (pad + 14, pad + 30), hp.split()[3])
gl = Image.new('RGBA', lay.size, (0, 0, 0, 0)); gl.paste((110, 190, 255, 120), (pad, pad), hp.split()[3])
lay.alpha_composite(gl.filter(ImageFilter.GaussianBlur(40))); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(34))); lay.alpha_composite(hp, (pad, pad))
canvas.alpha_composite(lay, (int(560 - lay.width / 2), 205 - pad))
# soft black fade under everything above the title, so the body melts into the dark
gy_ = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
fade = (np.clip((gy_ * H - 1150) / 330, 0, 1) ** 1.3 * 235).astype(np.uint8)
blk = Image.new('RGBA', (W, H), (0, 0, 0, 0)); blk.putalpha(Image.fromarray(fade)); canvas.alpha_composite(blk)

# ---------- logo + text ----------
lg = load('07_kard_logo.png'); lg = lg.resize((370, int(lg.height * 370 / lg.width)), Image.LANCZOS)
canvas.alpha_composite(lg, ((W - 370) // 2, 150))


def text_line(s, size, y, fill, track=0, shadow=True):
    f = ImageFont.truetype(FT, size)
    ws = [f.getbbox(ch)[2] - f.getbbox(ch)[0] if ch != ' ' else size * .28 for ch in s]
    adv = [f.getlength(ch) for ch in s]
    tot = sum(adv) + track * (len(s) - 1)
    x = (W - tot) / 2
    lay = Image.new('RGBA', (W, size * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for ch, a in zip(s, adv):
        d.text((x, size * .3), ch, font=f, fill=fill); x += a + track
    if shadow:
        sh = Image.new('RGBA', lay.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 200), (0, 6), lay.split()[3])
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, int(y - size * .3)))
    canvas.alpha_composite(lay, (0, int(y - size * .3)))
    return tot


text_line('MANGAKA × POKÉMON TCG', 34, 1300, (255, 214, 0, 255), track=7)
size = 112
while True:
    f = ImageFont.truetype(FT, size)
    if max(f.getlength('KARTU POKÉMON'), f.getlength('KARYA MANGAKA')) <= 960: break
    size -= 2
text_line('KARTU POKÉMON', size, 1362, (250, 250, 250, 255))
text_line('KARYA MANGAKA', size, 1362 + int(size * .9), (250, 250, 250, 255))
print('title size', size)
canvas.convert('RGB').save('cover_v18.png')
# 3:4 grid crop preview (what the profile grid shows)
canvas.convert('RGB').crop((0, 240, 1080, 1680)).save('cover_v18_grid.png')
