"""worlds.py - immersive genre worlds + 3D card objects for Video 18 (frames for the engine's `prerender` scene).

python3 worlds.py SCENE OUTDIR [t1 t2 ...]   render only those times (board) | without times: every frame
Each scene = a world (procedural backdrop, genre FX) + real card art as 3D objects (thickness, lit edge,
floor reflection, moving studio light). Engine adds captions, chips, logo, transitions.
"""
import sys, os, math, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
A = 'assets/'
FT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'Telegraf-UltraBold.otf')   # resolves from any working directory
gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)


# ------------------------------------------------------------------ helpers
def ease(x): x = min(max(x, 0.), 1.); return x * x * (3 - 2 * x)
def eo3(x): x = min(max(x, 0.), 1.); return 1 - (1 - x) ** 3
def lerp(a, b, x): return a + (b - a) * x
def prog(t, a, b): return min(max((t - a) / (b - a), 0.), 1.) if b > a else float(t >= a)


_IMG = {}
def rgba(name, h=None):
    k = (name, h)
    if k not in _IMG:
        im = Image.open(A + name).convert('RGBA')
        if h: im = im.resize((max(2, round(im.width * h / im.height)), h), Image.LANCZOS)
        _IMG[k] = np.asarray(im).astype(np.float32) / 255
    return _IMG[k]


def bw(x, k=1.25):
    g = x[..., :3] @ np.array([.299, .587, .114], np.float32)
    g = np.clip((g - .5) * k + .52, 0, 1)
    return np.dstack([g, g, g, x[..., 3]])


def over(dst, src, a=None):
    a = src[..., 3:4] if a is None else a
    return dst * (1 - a) + src[..., :3] * a


def screen(dst, rgb, a=1.):
    return 1 - (1 - dst) * (1 - np.clip(rgb * a, 0, 1))


def quad_warp(img, dst):
    h, w = img.shape[:2]
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    return cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_LINEAR)


def corners3d(w, h, cx, cy, yaw, pitch, roll, z=0., F=2400.):
    P = np.array([[-w / 2, -h / 2, z], [w / 2, -h / 2, z], [w / 2, h / 2, z], [-w / 2, h / 2, z]], np.float32)
    cr, sr = math.cos(roll), math.sin(roll)
    P = P @ np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]], np.float32).T
    cy_, sy = math.cos(yaw), math.sin(yaw)
    P = P @ np.array([[cy_, 0, sy], [0, 1, 0], [-sy, 0, cy_]], np.float32).T
    cp, sp = math.cos(pitch), math.sin(pitch)
    P = P @ np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], np.float32).T
    f = F / (F + P[:, 2])
    return np.stack([cx + P[:, 0] * f, cy + P[:, 1] * f], 1)


def card3d(canvas, name, cx, cy, h, yaw=0., pitch=0., roll=0., t=0., sweep=None, thick=10, reflect=None, shadow=.55, alpha=1., img=None, glow=None):
    """Real card art as a physical object: lit edge (thickness), soft shadow, optional floor reflection + light sweep."""
    im = rgba(name, int(h)) if img is None else img
    if len(_IMG) > 160: _IMG.clear()
    hh, ww = im.shape[:2]
    face = im.copy()
    if sweep is not None:   # studio light gliding across the foil
        uu = np.linspace(0, 1, ww)[None, :]; vv = np.linspace(0, 1, hh)[:, None]
        d = (uu * .75 + vv * .55) - sweep
        band = (np.exp(-(d / .06) ** 2) * .55 + np.exp(-(d / .25) ** 2) * .12)[..., None]
        face[..., :3] = screen(face[..., :3], band)
    front = corners3d(ww, hh, cx, cy, yaw, pitch, roll)
    back = corners3d(ww, hh, cx, cy, yaw, pitch, roll, z=thick)
    if reflect is not None:  # mirror below the floor line
        fl = reflect
        ref = quad_warp(face[::-1].copy(), np.stack([front[3], front[2], front[2] + [0, (front[2][1] - front[1][1]) * .9], front[3] + [0, (front[3][1] - front[0][1]) * .9]]) + [0, 6])
        fade = np.clip(1 - (gy - fl) / (h * .55), 0, 1)[..., None] * (gy > fl)[..., None]
        canvas = over(canvas, ref, ref[..., 3:4] * .22 * fade * alpha)
    if shadow:
        sh = quad_warp(np.dstack([np.zeros((hh, ww, 3), np.float32), im[..., 3]]), front + [26, 40])[..., 3]
        sh = cv2.GaussianBlur(sh, (0, 0), 28)[..., None]
        canvas = canvas * (1 - shadow * sh * alpha)
    if glow is not None:
        g = quad_warp(np.dstack([np.ones((hh, ww, 3), np.float32) * np.array(glow, np.float32), im[..., 3]]), front)
        g = cv2.GaussianBlur(g, (0, 0), 40)
        canvas = screen(canvas, g[..., :3] * g[..., 3:4], .9 * alpha)
    edge = quad_warp(np.dstack([np.full((hh, ww, 3), .78, np.float32), im[..., 3]]), back)
    canvas = over(canvas, edge, edge[..., 3:4] * alpha)
    fr = quad_warp(face, front)
    canvas = over(canvas, fr, fr[..., 3:4] * alpha)
    return canvas, front


def text_rgba(text, size, fill=(250, 250, 250), track=0):
    f = ImageFont.truetype(FT, size)
    bb = f.getbbox(text); w, h = bb[2] - bb[0] + 60 + track * len(text), bb[3] - bb[1] + 30
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if track:
        x = 10
        for ch in text: d.text((x, 10 - bb[1]), ch, font=f, fill=fill); x += f.getlength(ch) + track
    else: d.text((10 - bb[0], 10 - bb[1]), text, font=f, fill=fill)
    return np.asarray(im).astype(np.float32) / 255


def put_rgba(canvas, im, cx, cy, a=1., scale=1.):
    if scale != 1: im = cv2.resize(im, None, fx=scale, fy=scale)
    h, w = im.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xs, ys = max(0, x0), max(0, y0); xe, ye = min(W, x0 + w), min(H, y0 + h)
    if xe <= xs or ye <= ys: return canvas
    sub = im[ys - y0:ye - y0, xs - x0:xe - x0]
    canvas[ys:ye, xs:xe] = over(canvas[ys:ye, xs:xe], sub, sub[..., 3:4] * a)
    return canvas


def name_title(canvas, name, kicker, t0, t, y=1220, ink=False):
    a = eo3(prog(t, t0, t0 + .45))
    if a <= 0: return canvas
    fill = (14, 12, 12) if ink else (250, 250, 250)
    sh = text_rgba(name.upper(), 88 if len(name) < 14 else 74, fill=fill); sh2 = sh.copy(); sh2[..., :3] = 1 if ink else 0
    canvas = put_rgba(canvas, cv2.GaussianBlur(sh2, (0, 0), 10), W / 2, y + 30 * (1 - a) + 6, a * (.5 if ink else .8))
    canvas = put_rgba(canvas, sh, W / 2, y + 30 * (1 - a), a)
    k = text_rgba(kicker, 26, fill=fill, track=3)
    canvas = put_rgba(canvas, k, W / 2, y + 86 + 30 * (1 - a), a * .85)
    return canvas


def cutout(name, h, seed=3):
    """Scissor-cut paper cut-out (white border, uneven straight snips)."""
    im = rgba(name, h); hh, ww = im.shape[:2]; rng = np.random.default_rng(seed)
    pad = 26; P = Image.new('L', (ww + pad * 2, hh + pad * 2), 0)
    pts = []
    for side in range(4):
        for k in range(4):
            f = (k + rng.random() * .6) / 4
            x, y = [(f * ww, 0), (ww, f * hh), ((1 - f) * ww, hh), (0, (1 - f) * hh)][side]
            pts.append((x + pad + rng.uniform(-14, 14), y + pad + rng.uniform(-14, 14)))
    ImageDraw.Draw(P).polygon(pts, fill=255)
    m = np.asarray(P).astype(np.float32) / 255
    out = np.zeros((hh + pad * 2, ww + pad * 2, 4), np.float32); out[..., :3] = .98; out[..., 3] = m
    inner = cv2.erode(m, np.ones((19, 19), np.uint8))
    out[pad:pad + hh, pad:pad + ww, :3] = out[pad:pad + hh, pad:pad + ww, :3] * (1 - inner[pad:pad + hh, pad:pad + ww, None]) + im[..., :3] * inner[pad:pad + hh, pad:pad + ww, None]
    return out


def popout(photo, person, crop, h, k=1.3, seed=3, top_fade=0, poff=0, shift=0):
    """Small scissor-cut photo frame with the person scaled up inside it and breaking out over the top edge.
    Returns (tile RGBA float, dy) where dy = how far the frame centre sits below the tile centre."""
    src = Image.open(A + photo).convert('RGB'); per = Image.open(A + person).convert('RGBA')
    x0, y0, x1, y1 = crop; s = h / (y1 - y0); fw = int((x1 - x0) * s)
    inner = np.asarray(src.crop(crop).resize((fw, h), Image.LANCZOS)).astype(np.float32) / 255
    rng = np.random.default_rng(seed); pad = 26
    P = Image.new('L', (fw + pad * 2, h + pad * 2), 0); pts = []
    for side in range(4):
        for q in range(4):
            f = (q + rng.random() * .6) / 4
            x, y = [(f * fw, 0), (fw, f * h), ((1 - f) * fw, h), (0, (1 - f) * h)][side]
            pts.append((x + pad + rng.uniform(-14, 14), y + pad + rng.uniform(-14, 14)))
    ImageDraw.Draw(P).polygon(pts, fill=255)
    pm = np.asarray(P).astype(np.float32) / 255
    ps = s * k
    pal = np.asarray(per.split()[3]); rows = np.where(pal.max(1) > 40)[0]
    ptop = (rows[0] - poff) if len(rows) else y0
    over = max(int(h * (k - 1) * 1.05) + 30, int((y1 - ptop) * ps - pad - h) + 24)   # room for the whole head
    TW, TH = fw + pad * 2, h + pad * 2 + over
    tile = np.zeros((TH, TW, 4), np.float32)
    fy0 = over                                              # frame top inside the tile
    tile[fy0:, :, :3] = .98; tile[fy0:, :, 3] = pm
    ins = cv2.erode(pm, np.ones((19, 19), np.uint8))[pad:pad + h, pad:pad + fw, None]
    reg = tile[fy0 + pad:fy0 + pad + h, pad:pad + fw]
    reg[..., :3] = reg[..., :3] * (1 - ins) + inner * ins
    # person, scaled k x around the frame's bottom centre
    pr = per.resize((max(2, int(per.width * ps)), max(2, int(per.height * ps))), Image.LANCZOS)
    pa = np.asarray(pr).astype(np.float32) / 255
    a = pa[..., 3]; a = np.clip((a - .12) / .45, 0, 1)                # keep fine hair, drop faint halo
    if top_fade:
        ys = np.where(a.max(1) > .5)[0]
        if len(ys): a[ys[0]:ys[0] + top_fade] *= np.linspace(0, 1, top_fade)[:, None]
    cxs = (x0 + x1) / 2 * ps - shift; bys = (y1 + poff) * ps                         # source anchor -> tile frame bottom centre
    ox = int(TW / 2 - cxs); oy = int(fy0 + pad + h - bys)
    lay = np.zeros((TH, TW, 4), np.float32)
    sx0, sy0 = max(0, -ox), max(0, -oy); dx0, dy0 = max(0, ox), max(0, oy)
    w_ = min(pr.width - sx0, TW - dx0); h_ = min(pr.height - sy0, TH - dy0)
    if w_ > 0 and h_ > 0:
        lay[dy0:dy0 + h_, dx0:dx0 + w_, :3] = pa[sy0:sy0 + h_, sx0:sx0 + w_, :3]
        lay[dy0:dy0 + h_, dx0:dx0 + w_, 3] = a[sy0:sy0 + h_, sx0:sx0 + w_]
    allow = np.zeros((TH, TW), np.float32)
    allow[:fy0 + pad + 40, :] = 1                                   # above the frame's top edge: free
    allow[fy0 + pad:fy0 + pad + h, pad + 8:pad + fw - 8] = 1         # inside the photo window
    allow = cv2.GaussianBlur(allow, (0, 0), 1.2)
    la = lay[..., 3] * allow
    # soft contact shadow where the body leaves the frame
    tile[..., :3] = tile[..., :3] * (1 - la[..., None]) + lay[..., :3] * la[..., None]
    tile[..., 3] = np.maximum(tile[..., 3], la)
    return tile, (TH - (h + pad * 2)) / 2


def noise(h, w, scale, seed, oct=3):
    rng = np.random.default_rng(seed); n = 0
    for i in range(oct):
        s = max(2, int(scale / 2 ** i))
        n = n + cv2.resize(rng.random((max(2, h // s), max(2, w // s))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) / (i + 1)
    return (n - n.min()) / (n.max() - n.min() + 1e-6)


def vignette(c, k=.55):
    v = 1 - k * np.clip(np.hypot((gx - W / 2) / (W * .72), (gy - H / 2) / (H * .6)), 0, 1) ** 2.2
    return c * v[..., None]


def grain(c, t, a=.018):
    rng = np.random.default_rng(int(t * 30) + 11)
    return np.clip(c + rng.normal(0, a, (H, W, 1)).astype(np.float32), 0, 1)


# ------------------------------------------------------------------ worlds
_C = {}
def cache(key, fn):
    if key not in _C: _C[key] = fn()
    return _C[key]


def manga_panels():
    """Original screentone panels (dots, hatching, speed lines) for the floating manga space."""
    rng = np.random.default_rng(4); out = []
    for i in range(12):
        w, h = int(rng.uniform(300, 620)), int(rng.uniform(380, 760))
        p = Image.new('L', (w, h), 245); d = ImageDraw.Draw(p)
        kind = i % 4
        if kind == 0:
            s = int(rng.uniform(9, 16))
            for y in range(0, h, s):
                for x in range((y // s % 2) * s // 2, w, s): r = s * rng.uniform(.18, .34); d.ellipse([x - r, y - r, x + r, y + r], fill=30)
        elif kind == 1:
            for k in range(0, w + h, 7): d.line([(k, 0), (k - h, h)], fill=40, width=2)
        elif kind == 2:
            cxp, cyp = w * rng.uniform(.3, .7), h * rng.uniform(.3, .7)
            for k in range(140):
                a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(40, 120)
                d.line([(cxp + math.cos(a) * r0, cyp + math.sin(a) * r0), (cxp + math.cos(a) * 900, cyp + math.sin(a) * 900)], fill=25, width=int(rng.integers(1, 4)))
        else:
            g = np.asarray(p).astype(np.float32); n = noise(h, w, 60, i)
            p = Image.fromarray(np.clip(g * (0.35 + 0.65 * (n > .5)), 0, 255).astype(np.uint8)); d = ImageDraw.Draw(p)
        d.rectangle([0, 0, w - 1, h - 1], outline=0, width=10)
        a = np.asarray(p).astype(np.float32) / 255
        out.append(np.dstack([a, a, a, np.ones_like(a)]))
    return out


def ink_burst(cx, cy, p, seed, r=520, col=(.04, .04, .04)):
    """Ink splash blooming outward (p 0..1)."""
    if p <= 0: return None
    n = cache(('inkn', seed), lambda: noise(H, W, 90, seed, 4))
    d = np.hypot(gx - cx, gy - cy) / r
    m = np.clip((eo3(p) * 1.25 - d - (n - .5) * .55) / .05, 0, 1)
    drops = cache(('drops', seed), lambda: (noise(H, W, 14, seed + 9, 1) > .86).astype(np.float32))
    m = np.maximum(m, drops * np.clip((eo3(p) * 1.6 - d) / .2, 0, 1) * (d > .6))
    return m


def bg_manga(t, dur):
    P = cache('panels', manga_panels)
    c = np.full((H, W, 3), .06, np.float32)
    rng = np.random.default_rng(8)
    for i, pnl in enumerate(P):   # panels fly toward the camera at different depths
        z0 = rng.uniform(.4, 3.0); x0 = rng.uniform(-600, 600); y0 = rng.uniform(-900, 900); rot = rng.uniform(-.5, .5)
        z = (z0 - t * .28) % 3.0 + .35
        sc = 1.0 / z
        cx, cy = W / 2 + x0 * sc, H * .47 + y0 * sc
        hh, ww = pnl.shape[:2]
        q = corners3d(ww * sc, hh * sc, cx, cy, rot * .6, rot * .3, rot * .4)
        L = quad_warp(cv2.resize(pnl, (max(2, int(ww * sc)), max(2, int(hh * sc)))), q)
        dim = np.clip(.5 / z, .08, .55); blur = abs(z - 1.1) * 6
        if blur > 1: L = cv2.GaussianBlur(L, (0, 0), blur)
        c = over(c, L, L[..., 3:4] * dim)
    # radial speed lines
    ang = np.arctan2(gy - H * .46, gx - W / 2); rr = np.hypot(gx - W / 2, gy - H * .46)
    sl = (np.sin(ang * 90 + 7 * np.sin(ang * 13)) > .93).astype(np.float32) * np.clip((rr - 380) / 500, 0, 1)
    c = screen(c, np.dstack([sl] * 3), .18 + .1 * math.sin(t * 9))
    return c


def bg_noir(t):
    """Monochrome detective desk: lamp pool of light, haze, rain on the window behind, papers."""
    def base():
        c = np.full((H, W, 3), .035, np.float32)
        # window with rain (upper part)
        win = (gy < H * .42).astype(np.float32)
        c += win[..., None] * .05 * noise(H, W, 300, 2)[..., None]
        # desk plane with grain
        desk = noise(H, W * 4, 25, 5, 2)[:, ::4] if False else noise(H, W, 30, 5, 2)
        grain_ = cv2.resize(cv2.resize(desk, (W // 40, H)), (W, H))
        dmask = np.clip((gy - H * .40) / 40, 0, 1)
        c = c * (1 - dmask[..., None]) + (np.full((H, W, 3), .07, np.float32) + grain_[..., None] * .05) * dmask[..., None]
        # lamp pool
        pool = np.exp(-(((gx - W * .55) / 520) ** 2 + ((gy - H * .62) / 640) ** 2))
        c = c + pool[..., None] * .26
        return c
    c = cache('noirbase', base).copy()
    # rain streaks on the window, moving down
    rng = np.random.default_rng(1)
    streak = np.zeros((H, W), np.float32)
    for k in range(70):
        x = rng.uniform(0, W); sp = rng.uniform(380, 900); y = (rng.uniform(0, H) + t * sp) % (H * .42); L = rng.uniform(40, 140)
        cv2.line(streak, (int(x), int(y)), (int(x - 6), int(y + L)), rng.uniform(.25, .7), 2)
    streak = cv2.GaussianBlur(streak, (0, 0), 1.4) * (gy < H * .42)
    c = screen(c, np.dstack([streak] * 3), .35)
    # haze in the lamp beam
    hz = cache('haze', lambda: noise(H, W, 220, 7, 3))
    hz = np.roll(hz, int(t * 25), 1)
    beam = np.clip(1 - np.abs((gx - W * .55) - (gy - H * .05) * .18) / 420, 0, 1) * (gy < H * .75)
    c = screen(c, np.dstack([hz * beam * .25] * 3))
    return c


def bg_fun_old(t, cols):
    """Soft pastel world from the card's own colours: big bokeh, doodle sparkles drifting/bouncing."""
    c1, c2 = np.array(cols[0], np.float32), np.array(cols[1], np.float32)
    k = np.clip(gy / H, 0, 1)[..., None]
    c = c1 * (1 - k) + c2 * k
    rng = np.random.default_rng(5)
    for i in range(16):
        x = rng.uniform(0, W); y = (rng.uniform(0, H) - t * rng.uniform(20, 60)) % H; r = rng.uniform(40, 140)
        b = np.exp(-(((gx - x) ** 2 + (gy - y) ** 2) / (r * r)))
        c = screen(c, np.dstack([b * .22] * 3))
    sp = np.zeros((H, W), np.float32)
    for i in range(14):   # 4-point twinkles (generic sparkle shape)
        x = rng.uniform(60, W - 60); y = rng.uniform(80, H - 200) + 18 * math.sin(t * 4 + i); s = rng.uniform(16, 34) * (1 + .25 * math.sin(t * 6 + i * 1.7))
        pts = [(x, y - s), (x + s * .22, y - s * .22), (x + s, y), (x + s * .22, y + s * .22), (x, y + s), (x - s * .22, y + s * .22), (x - s, y), (x - s * .22, y - s * .22)]
        cv2.fillPoly(sp, [np.array(pts, np.int32)], 1.)
    c = c * (1 - sp[..., None] * .85) + np.array([.15, .12, .1], np.float32) * sp[..., None] * .85
    return c


def bg_fun(t, cols=None):
    """Playful but premium: charcoal ground, soft white bokeh drifting, small white twinkles bouncing (no colour)."""
    c = np.dstack([(.10 - .05 * np.clip(gy / H, 0, 1))] * 3).astype(np.float32)
    rng = np.random.default_rng(5)
    for i in range(14):
        x = rng.uniform(0, W); y = (rng.uniform(0, H) - t * rng.uniform(20, 60)) % H; r = rng.uniform(50, 150)
        b = np.exp(-(((gx - x) ** 2 + (gy - y) ** 2) / (r * r)))
        c = screen(c, np.dstack([b * .10] * 3))
    sp = np.zeros((H, W), np.float32)
    for i in range(12):
        x = rng.uniform(60, W - 60); y = rng.uniform(80, H - 200) + 14 * math.sin(t * 3 + i); s = rng.uniform(12, 26) * (1 + .3 * math.sin(t * 5 + i * 1.7))
        pts = [(x, y - s), (x + s * .2, y - s * .2), (x + s, y), (x + s * .2, y + s * .2), (x, y + s), (x - s * .2, y + s * .2), (x - s, y), (x - s * .2, y - s * .2)]
        cv2.fillPoly(sp, [np.array(pts, np.int32)], 1.)
    return screen(c, np.dstack([cv2.GaussianBlur(sp, (0, 0), .8)] * 3), .55)


def brush_strokes(seed, n=5):
    rng = np.random.default_rng(seed); S = []
    for i in range(n):
        y0 = rng.uniform(.1, .9) * H; ang = rng.uniform(-.5, .5); L = rng.uniform(900, 1500); wdt = rng.uniform(60, 160)
        S.append((rng.uniform(-200, 200), y0, ang, L, wdt, rng.uniform(0, .5)))
    return S


def bg_ink(t, col, seed=3):
    """Martial-arts action: black brush strokes revealing, speed lines, dust, coloured rim glow from the art."""
    c = np.full((H, W, 3), .05, np.float32)
    glow = np.exp(-(((gx - W / 2) / 650) ** 2 + ((gy - H * .48) / 900) ** 2))
    c = c + glow[..., None] * .10
    n = cache(('brushn', seed), lambda: noise(H, W, 18, seed, 2))
    for (x0, y0, ang, L, wdt, td) in cache(('strokes', seed), lambda: brush_strokes(seed)):
        p = eo3(prog(t, td, td + .5))
        if p <= 0: continue
        dx, dy = math.cos(ang), math.sin(ang)
        s = ((gx - x0) * dx + (gy - y0) * dy); dist = np.abs(-(gx - x0) * dy + (gy - y0) * dx)
        m = (s > 0) & (s < L * p) & (dist < wdt * (.6 + .5 * n))
        m = m.astype(np.float32) * (1 - .5 * (n > .78))
        c = c * (1 - m[..., None] * .85) + np.array([.92, .92, .9], np.float32) * m[..., None] * .12
    ang = np.arctan2(gy - H * .46, gx - W / 2)
    sl = (np.sin(ang * 70 + t * 3) > .95).astype(np.float32) * np.clip((np.hypot(gx - W / 2, gy - H * .46) - 420) / 400, 0, 1)
    c = screen(c, np.dstack([sl] * 3), .14)
    rng = np.random.default_rng(int(seed))
    dust = np.zeros((H, W), np.float32)
    for k in range(90):
        x = (rng.uniform(0, W) + t * rng.uniform(-80, 80)) % W; y = (rng.uniform(0, H) - t * rng.uniform(30, 120)) % H
        cv2.circle(dust, (int(x), int(y)), int(rng.integers(1, 4)), rng.uniform(.3, .9), -1)
    c = screen(c, np.dstack([cv2.GaussianBlur(dust, (0, 0), 1.2)] * 3), .6)
    return c


def bg_arena(t):
    """Wrestling entrance: sweeping spotlights through haze, camera flashes from the crowd."""
    c = np.full((H, W, 3), .03, np.float32)
    hz = cache('ahaze', lambda: noise(H, W, 180, 12, 3))
    for i, (x0, sp, ph) in enumerate([(.15, .7, 0), (.85, .6, 1.7), (.5, .45, 3.1)]):
        a = math.sin(t * sp + ph) * .45
        dx = gx - x0 * W - (gy + 200) * math.tan(a)
        cone = np.clip(1 - np.abs(dx) / (60 + (gy + 200) * .22), 0, 1) ** 1.5
        c = screen(c, np.dstack([cone * (.18 + .25 * hz)] * 3))
    crowd = (gy > H * .86 + 30 * np.sin(gx / 37) + 20 * np.sin(gx / 13)).astype(np.float32)
    c = c * (1 - crowd[..., None] * .9)
    rng = np.random.default_rng(int(t * 6))
    fl = np.zeros((H, W), np.float32)
    for k in range(5):
        x, y = rng.uniform(0, W), rng.uniform(H * .80, H * .95)
        fl += np.exp(-(((gx - x) ** 2 + (gy - y) ** 2) / (30 ** 2))) * rng.uniform(.4, 1)
    c = screen(c, np.dstack([fl] * 3), .8)
    return c


def magic_circle(t, cx, cy, R, p, col, seed=2):
    """Original ink magic circle drawing itself: rings, ticks, abstract glyph marks (p = draw progress)."""
    m = np.zeros((H, W), np.float32); rng = np.random.default_rng(seed)
    rot = t * .25
    for k, rr in enumerate([R, R * .86, R * .62, R * .4]):
        a1 = int(360 * ease(prog(p, k * .12, k * .12 + .5)))
        if a1 > 0: cv2.ellipse(m, (int(cx), int(cy)), (int(rr), int(rr * .42)), 0, math.degrees(rot) * (1 if k % 2 else -1), math.degrees(rot) * (1 if k % 2 else -1) + a1, 1., 3 if k else 5, cv2.LINE_AA)
    nt = int(48 * ease(prog(p, .3, .9)))
    for k in range(nt):
        a = k / 48 * 2 * math.pi + rot
        p0 = (int(cx + math.cos(a) * R * .86), int(cy + math.sin(a) * R * .86 * .42)); p1 = (int(cx + math.cos(a) * R), int(cy + math.sin(a) * R * .42))
        cv2.line(m, p0, p1, 1., 2, cv2.LINE_AA)
    for k in range(int(10 * ease(prog(p, .5, 1)))):
        a = k / 10 * 2 * math.pi - rot * 1.5; x, y = cx + math.cos(a) * R * .74, cy + math.sin(a) * R * .74 * .42
        s = 18; pts = np.array([(x, y - s), (x + s * .7, y + s * .5), (x - s * .7, y + s * .5)], np.int32)
        cv2.polylines(m, [pts], True, 1., 2, cv2.LINE_AA)
    g = cv2.GaussianBlur(m, (0, 0), 8)
    return np.dstack([m] * 3) * np.array([1, 1, 1], np.float32) + np.dstack([g] * 3) * 1.1


def bg_magic(t, col):
    c = np.full((H, W, 3), .035, np.float32)
    glow = np.exp(-(((gx - W / 2) / 700) ** 2 + ((gy - H * .5) / 900) ** 2))
    c = c + glow[..., None] * .08
    rng = np.random.default_rng(9)
    pt = np.zeros((H, W), np.float32)
    for k in range(120):
        x = (rng.uniform(0, W) + 15 * math.sin(t + k)) % W; y = (rng.uniform(0, H) - t * rng.uniform(20, 70)) % H
        cv2.circle(pt, (int(x), int(y)), int(rng.integers(1, 3)), rng.uniform(.3, 1), -1)
    c = screen(c, np.dstack([cv2.GaussianBlur(pt, (0, 0), 1.5)] * 3) , .7)
    return c


def snow(t, amount=1.):
    rng = np.random.default_rng(21); s = np.zeros((H, W), np.float32)
    for k in range(int(160 * amount)):
        z = rng.uniform(.4, 1.6); x = (rng.uniform(0, W) + 30 * math.sin(t * .8 + k)) % W; y = (rng.uniform(0, H) + t * 90 * z) % H
        cv2.circle(s, (int(x), int(y)), max(1, int(3 * z)), min(1, .5 * z), -1)
    return cv2.GaussianBlur(s, (0, 0), 1.3)


def bg_studio(t):
    """Product videography set: neutral cyclorama, volumetric beam, glossy floor."""
    k = np.clip(gy / H, 0, 1)
    c = np.dstack([.11 - .06 * k] * 3).astype(np.float32)
    floor = np.clip((gy - H * .655) / 6, 0, 1)
    c = c * (1 - floor[..., None] * .35)
    beam = np.clip(1 - np.abs((gx - W * (.25 + .05 * math.sin(t * .6))) - gy * .35) / 300, 0, 1) * (1 - k * .6)
    hz = cache('shaze', lambda: noise(H, W, 260, 4, 3))
    c = screen(c, np.dstack([beam * (.10 + .14 * hz)] * 3))
    spot = np.exp(-(((gx - W / 2) / 560) ** 2 + ((gy - H * .66) / 190) ** 2))
    c = screen(c, np.dstack([spot * .18] * 3))
    return c


# ------------------------------------------------------------------ scenes
def S_hook1(t):
    """Fly through a manga-panel space; the two covers float forward; ink bursts turn them into cards."""
    c = bg_manga(t, 3.8)
    for i, (cov, card, x, tw, yaw) in enumerate([('m_conan.png', 'c_pichu.png', 295, 1.0, .24), ('m_chiikawa.png', 'c_simisear.png', 785, 2.05, -.24)]):
        z = lerp(1.25, .98, ease(t / 3.8)); h = 760 * (1 / z) * (1 + .05 * eo3(prog(t, tw, tw + .4)))
        bob = 12 * math.sin(t * 2.2 + i)
        p = eo3(prog(t, tw, tw + .55))
        if p < 1:
            cv_ = bw(rgba(cov, int(h)))
            c, q = card3d(c, None, x, 880 + bob, h, yaw * (1 - .3 * p), .06, (-.04 if i == 0 else .04), img=cv_, thick=6, alpha=1 - p ** 3)
        m = ink_burst(x, 880 + bob, prog(t, tw - .05, tw + .45), 30 + i, r=420)
        if m is not None: c = c * (1 - m[..., None] * (1 - p) * .95)
        if p > 0:
            sw = lerp(-.3, 1.3, prog(t, tw + .3, tw + 1.5))
            c, q = card3d(c, card, x, 880 + bob, h * .96, yaw * .7, .05, (-.03 if i == 0 else .03), t=t, sweep=sw, alpha=p, thick=10, glow=(.32, .32, .32))
    return grain(vignette(c), t)


def shuchusen(t, cx=540, cy=900, n=150, seed=21):
    """Manga focus lines radiating from a centre (black on the panels), slowly breathing."""
    rng = np.random.default_rng(seed)
    m = np.zeros((H, W), np.float32)
    ang = rng.uniform(0, 2 * np.pi, n); wid = rng.uniform(.004, .016, n); r0 = rng.uniform(360, 560, n)
    A = np.arctan2(gy - cy, gx - cx); R = np.hypot(gx - cx, gy - cy)
    for a0, w0, r in zip(ang, wid, r0):
        d = np.abs(np.angle(np.exp(1j * (A - a0))))
        m = np.maximum(m, np.clip(1 - d / w0, 0, 1) * np.clip((R - r - 40 * math.sin(t * 2 + a0)) / 260, 0, 1))
    return m


def S_trialhook(t, dur=6.0):
    """Trial hook roll call: each cover slams in big at centre on its name, the previous one slides behind to the side;
    on 'semuanya' all three ink into their cards (fan: Pichu left, Simisear right, Palafin front)."""
    c = bg_manga(t, dur)[:, ::-1].copy()                    # mirrored panels
    c = c * .78 + .03                                       # a touch darker than the main hook
    fl = cache('shuchusen', lambda: shuchusen(0))
    c = c * (1 - fl[..., None] * .85)                       # black focus lines pulling to the centre
    T1, T2, T3 = .50, 1.66, 2.58
    C = (540, 900, 820, 0., 0.); L = (165, 925, 740, .26, -.06); R = (915, 925, 740, -.26, .06)
    def slot(i):
        if i == 0: return C if t < T2 else lerp_slot(C, L, eo3(prog(t, T2, T2 + .30)))
        if i == 1: return C if t < T3 else lerp_slot(C, R, eo3(prog(t, T3, T3 + .30)))
        return C
    items = [('m_conan.png', 'c_pichu.png', T1, 3.62), ('m_chiikawa.png', 'c_simisear.png', T2, 3.84), ('m_hokuto.png', 'c_palafin.png', T3, 4.06)]
    shake = sum((1 - prog(t, ts + .10, ts + .42)) * (t >= ts + .08) * 14 * math.sin(t * 75 + ts) for _, _, ts, _ in items)
    push = lerp(1.0, 1.04, ease(t / dur))
    order = [0, 1, 2] if t >= T3 else ([1, 0] if False else [0, 1])
    for i in order:
        cov, card, ts, ti = items[i]
        s = eo3(prog(t, ts - .02, ts + .12))
        if s <= 0: continue
        x, y, h, yaw, roll = slot(i)
        h = h * push * lerp(1.55, 1.0, s); x = 540 + (x - 540) * push + shake; y = y + shake * .5
        p = eo3(prog(t, ti, ti + .5))
        if p < 1:
            c, _ = card3d(c, None, x, y, h, yaw, .05, roll, img=bw(rgba(cov, int(h)), 1.3), thick=6, shadow=.7, alpha=s * (1 - p ** 3))
        m = ink_burst(x, y, prog(t, ti - .05, ti + .45), 70 + i, r=460)
        if m is not None: c = c * (1 - m[..., None] * (1 - p) * .95)
        if p > 0:
            c, _ = card3d(c, card, x, y, h * .97, yaw * .85, .05, roll, sweep=lerp(-.3, 1.3, prog(t, ti + .2, ti + 1.3)), thick=10, shadow=.7, alpha=p, glow=(.30, .30, .30))
        f = (1 - prog(t, ts + .08, ts + .30)) * (t >= ts + .08)
        if f > 0: c = screen(c, np.dstack([np.exp(-(((gx - x) / 420) ** 2 + ((gy - y) / 600) ** 2)) * f * .35] * 3))
    return grain(vignette(c), t)


def lerp_slot(a, b, x): return tuple(lerp(p, q, x) for p, q in zip(a, b))


def S_hook2(t):
    """Ink-action slam: brush strokes rip across, the Hokuto cover slams in, bursts into Palafin; Crasher Wake joins."""
    c = bg_ink(t, (.25, .45, .9), seed=5)
    slam = eo3(prog(t, .05, .32)); shake = (1 - prog(t, .32, .7)) * 14 * math.sin(t * 70)
    tw = 1.45; p = eo3(prog(t, tw, tw + .5)); sl = ease(prog(t, 2.15, 2.75))
    h = lerp(1500, 1000, slam) * lerp(1, .74, sl)
    x = lerp(540, 300, sl) + shake; y = 880 + shake * .5
    if p < 1:
        c, _ = card3d(c, None, x, y, h, lerp(0, .18, sl), .05, 0, img=bw(rgba('m_hokuto.png', int(h)), 1.4), thick=6, alpha=(1 - p ** 3) * slam)
    m = ink_burst(x, y, prog(t, tw - .05, tw + .45), 41, r=520)
    if m is not None: c = c * (1 - m[..., None] * (1 - p) * .95)
    if p > 0:
        c, _ = card3d(c, 'c_palafin.png', x, y, h * .93, lerp(0, .18, sl), .05, 0, sweep=lerp(-.3, 1.3, prog(t, tw + .2, tw + 1.2)), alpha=p, glow=(.32, .32, .32))
    if sl > 0:
        c, _ = card3d(c, 'c_crasher.png', lerp(1400, 790, sl), y, 1000 * .74 * .93, lerp(-.7, -.18, sl), .05, 0, sweep=lerp(-.3, 1.3, prog(t, 2.5, 3.3)), glow=(.32, .32, .32))
    if t < .32:   # impact frame: one hard ink-negative beat on the slam
        c = np.where(t > .26, 1 - c, c)
    return grain(vignette(c), t)


def S_aoyama(t):
    """Noir desk: Conan cover lying under the lamp, camera slowly pushes and rises; name title."""
    c = bg_noir(t)
    push = ease(t / 4.4)
    c, _ = card3d(c, None, 540, 850, lerp(760, 790, push), lerp(-.16, -.06, push), .03, .02, img=rgba('m_conan.png', 1000), thick=8, shadow=.7, sweep=lerp(-.3, 1.2, prog(t, .4, 3.4)))
    a = eo3(prog(t, .55, 1.05))                       # his photo, scissor-cut, lands on the cover's corner
    cut, dy = cache('pop_aoyama', lambda: popout('v_aoyama_photo_src.png', 'x_aoyama_person.png', (70, 300, 560, 760), 330, 1.32, 4, shift=34))
    if a > 0: c, _ = card3d(c, None, 835, lerp(1220, 1125, a) - dy, cut.shape[0], -.10, 0, .07, img=cut, thick=0, shadow=.65, alpha=a)
    c = name_title(c, 'Gosho Aoyama', 'ILLUSTRATOR · DETECTIVE CONAN', .5, t, y=1405)
    return grain(vignette(c, .7), t, .025)


def S_pichu(t):
    """The card itself, product-shot on the noir desk: rises off the desk toward the lens under the lamp."""
    c = bg_noir(t + 4)
    p = ease(t / 1.9)
    c, _ = card3d(c, 'c_pichu.png', 540, lerp(1060, 880, p), lerp(900, 1180, p), lerp(-.25, .08, p), lerp(.75, .06, p), lerp(.15, -.03, p),
                  sweep=lerp(-.2, 1.1, p), thick=12, shadow=.7, glow=(.32, .32, .32))
    return grain(vignette(c, .7), t, .025)


def S_nagano(t):
    c = bg_fun(t, [(.98, .90, .86), (.96, .78, .76)])
    a = eback(prog(t, .05, .5))
    cut = cache('cut_nagano', lambda: cutout('v_nagano.png', 560, 5))
    c = put_rgba(c, cut, W / 2, 820 + 20 * math.sin(t * 5), min(1, a * 2), scale=max(.01, a))
    c = name_title(c, 'nagano', 'ILLUSTRATOR · CHIIKAWA', .35, t, y=1250)
    # name title is white -> give it a soft dark plate on the pastel world
    return grain(vignette(c, .35), t, .012)


def eback(x, s=1.70158): x = min(max(x, 0), 1) - 1; return x * x * ((s + 1) * x + s) + 1


def crop_panel(name, fx, fy, fh, pw, ph):
    """Crop a region (centre fx,fy; height fraction fh) of an asset into a pw x ph panel with rounded corners."""
    im = np.asarray(Image.open(A + name).convert('RGBA')).astype(np.float32) / 255
    Hh, Ww = im.shape[:2]; ch = fh * Hh; cw = ch * pw / ph
    x0, y0 = int(fx * Ww - cw / 2), int(fy * Hh - ch / 2)
    x0 = max(0, min(Ww - int(cw), x0)); y0 = max(0, min(Hh - int(ch), y0))
    p = cv2.resize(im[y0:y0 + int(ch), x0:x0 + int(cw)], (pw, ph), interpolation=cv2.INTER_AREA)
    m = Image.new('L', (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=28, fill=255)
    p[..., 3] = np.asarray(m).astype(np.float32) / 255
    return p


def S_versus(t, dur=2.53):
    """Split screen: two full-height boxes. Left = Chiikawa (cover close-up), right = Simisear VSTAR (card close-up);
    each is a macro with a slow 3D pan side to side, in opposite directions."""
    GAP = 10; HW = (W - GAP) // 2
    out = np.full((H, W, 3), .02, np.float32)
    p = t / dur; sw = math.sin((p - .5) * math.pi)            # -1 -> 1, always moving
    halves = [dict(img='m_chiikawa.png', h=2400, fx=.50, fy=.477, x0=0, dir=1, card=False),
              dict(img='c_simisear.png', h=2300, fx=.46, fy=.326, x0=HW + GAP, dir=-1, card=True)]
    for k, hv in enumerate(halves):
        c = np.full((H, W, 3), .03, np.float32)
        im = rgba(hv['img'], hv['h']); hh, ww = im.shape[:2]
        pan = 110 * sw * hv['dir']
        cx = hv['x0'] + HW / 2 - (hv['fx'] - .5) * ww + pan
        cy = H * .47 - (hv['fy'] - .5) * hh
        c, _ = card3d(c, None, cx, cy, hh, .10 * sw * hv['dir'], .03, 0, img=im, thick=0, shadow=0,
                      sweep=(lerp(-.2, 1.2, p) if hv['card'] else None))
        a = eo3(prog(t, .0 + k * .1, .45 + k * .1))
        xs, xe = hv['x0'], hv['x0'] + HW
        sl = int((1 - a) * HW * hv['dir'] * -1)            # each half slides in from its own side
        seg = c[:, xs:xe]
        if sl: seg = np.roll(seg, sl, 1); seg[:, :max(0, sl)] = .02; seg[:, HW + min(0, sl):] = .02
        out[:, xs:xe] = seg
    out = vignette(out, .5)
    for txt, x, t0 in [('CHIIKAWA', HW / 2, .5), ('SIMISEAR VSTAR', HW + GAP + HW / 2, .6)]:
        a = eo3(prog(t, t0, t0 + .35))
        if a > 0:
            tx = text_rgba(txt, 28, track=4); shd = tx.copy(); shd[..., :3] = 0
            out = put_rgba(out, cv2.GaussianBlur(shd, (0, 0), 9), x, 1424 + 20 * (1 - a), a)
            out = put_rgba(out, tx, x, 1420 + 20 * (1 - a), a)
    return grain(out, t, .014)


def S_hara(t):
    c = bg_ink(t, (.25, .45, .9), seed=8)
    a = eo3(prog(t, .05, .45))
    cut = cache('cut_hara', lambda: cutout('v_hara_photo.png', 820, 8))
    c = put_rgba(c, cut, W / 2 + 10 * math.sin(t * 1.5), 800, a, scale=lerp(1.15, 1.0, a))
    c = name_title(c, 'Tetsuo Hara', 'ILLUSTRATOR · FIST OF THE NORTH STAR', .5, t, y=1300)
    return grain(vignette(c), t)


def focus_blur(c, axis, at, width, amt):
    """Shallow depth of field: sharp band at `at` (0..1 along axis), soft beyond it."""
    if amt <= 0: return c
    sm = cv2.resize(cv2.GaussianBlur(cv2.resize(c, (W // 3, H // 3)), (0, 0), amt / 3), (W, H))
    v = (gy / H) if axis == 'y' else (gx / W)
    m = np.clip((np.abs(v - at) - width / 2) / .18, 0, 1)[..., None] ** 1.2
    return c * (1 - m) + sm * m


def S_flip(t, dur=5.52):
    """27 Nov: macro close-ups gliding over the real JP card back (logo slide, Poke Ball push, low sweep),
    pull back to the whole card, flip to Crasher Wake on its name."""
    c = bg_arena(t)
    fa = 2.9; f = ease(prog(t, fa, fa + .5)); ang = math.pi * f
    spot = np.exp(-(((gx - W / 2) / 420) ** 2 + ((gy - H * .46) / 620) ** 2)) * eo3(prog(t, .2, .9))
    c = screen(c, np.dstack([spot * .35] * 3))
    lift = math.sin(f * math.pi)
    def at_uv(h, u, v, sx, sy):   # card centre so that card point (u, v) sits on screen (sx, sy)
        return sx + (.5 - u) * h * .716, sy + (.5 - v) * h
    if t < 1.40:      # A: extreme close on the top Pokemon logo, sliding left -> right, tilted
        p = ease(t / 1.40); h = 3300
        cx, cy = at_uv(h, lerp(.30, .70, p), .17, 540, 900)
        c, _ = card3d(c, 'c_back.png', cx, cy, h, lerp(-.22, -.12, p), .14, -.05, sweep=lerp(-.2, 1.1, p), thick=0, shadow=0)
        return grain(vignette(focus_blur(c, 'x', lerp(.35, .65, p), .55, 14)), t)
    if t < 2.20:      # B: Poke Ball centre, slow push-in with a slight roll, rack focus in
        p = ease((t - 1.40) / .80); h = lerp(2500, 2950, p)
        cx, cy = at_uv(h, .5, .50, 540, 960)
        c, _ = card3d(c, 'c_back.png', cx, cy, h, .16, -.06, lerp(-.06, .02, p), sweep=lerp(1.2, .2, p), thick=0, shadow=0)
        return grain(vignette(focus_blur(c, 'y', .5, .5, lerp(16, 6, p))), t)
    if t < fa:        # C: low sweep up from the bottom logo, pulling back to the whole card
        p = ease((t - 2.20) / (fa - 2.20)); h = lerp(2300, 940, p)
        sx, sy = lerp(540, 540, p), lerp(1150, 880, p)
        u, v = lerp(.5, .5, p), lerp(.80, .5, p)
        cx, cy = at_uv(h, u, v, sx, sy)
        c, _ = card3d(c, 'c_back.png', cx, cy, h, lerp(-.18, .05, p), lerp(.22, .05, p), 0, thick=int(lerp(0, 10, p)), glow=(.32, .32, .32), shadow=.4 * p)
        return grain(vignette(focus_blur(c, 'y', .5, .6, lerp(10, 0, p))), t)
    yaw = ang if ang < math.pi / 2 else ang - math.pi
    h = 940 * (1 + .06 * lift)
    if ang < math.pi / 2:
        c, _ = card3d(c, 'c_back.png', 540, 880 - 40 * lift, h, yaw + .05, .05, 0, thick=10, glow=(.32, .32, .32))
    else:
        c, _ = card3d(c, 'c_crasher.png', 540, 880 - 40 * lift, h, yaw + .04 * math.sin(t), .05, 0, sweep=lerp(-.3, 1.3, prog(t, fa + .5, fa + 1.6)), thick=10, glow=(.32, .32, .32))
    return grain(vignette(c), t)


def bg_gallery(t):
    """Premium gallery wall: charcoal plaster, one gallery spotlight from above."""
    tex = cache('plaster', lambda: noise(H, W, 40, 31, 3))
    c = np.dstack([.055 + .025 * tex] * 3).astype(np.float32)
    cone = np.clip(1 - np.abs(gx - W / 2) / (180 + gy * .42), 0, 1) ** 1.6 * np.clip(1 - gy / (H * .95), 0, 1)
    pool = np.exp(-(((gx - W / 2) / 520) ** 2 + ((gy - H * .40) / 560) ** 2))
    return screen(c, np.dstack([cone * .16 + pool * .22] * 3))


def framed(name, h, mat=34, edge=8):
    im = rgba(name, h); hh, ww = im.shape[:2]
    out = np.zeros((hh + 2 * (mat + edge), ww + 2 * (mat + edge), 4), np.float32)
    out[..., :3] = .08; out[..., 3] = 1
    out[edge:-edge, edge:-edge, :3] = .95
    out[edge + mat:edge + mat + hh, edge + mat:edge + mat + ww, :3] = im[..., :3]
    return out


def S_shirahama(t):
    c = bg_gallery(t)
    z = lerp(1.0, 1.045, ease(t / 3.3))
    fr = cache('frame_witch', lambda: framed('m_witchhat.png', 760))
    c, _ = card3d(c, None, 540 - 30 * ease(t / 3.3), 700, fr.shape[0] * z * .98, .05 - .04 * ease(t / 3.3), .0, 0, img=cv2.resize(fr, None, fx=z * .98, fy=z * .98), thick=0, shadow=.75)
    a = eo3(prog(t, .35, .85))
    cut, dy = cache('pop_shira', lambda: popout('v_shirahama_photo_src.png', 'x_shirahama_person.png', (0, 110, 391, 470), 330, 1.30, 11))
    if a > 0: c, _ = card3d(c, None, 800, lerp(1220, 1110, a) - dy, cut.shape[0], -.10, 0, .07, img=cut, thick=0, shadow=.6, alpha=a)
    c = name_title(c, 'Kamome Shirahama', 'ILLUSTRATOR · WITCH HAT ATELIER', .5, t, y=1380)
    return grain(vignette(c, .6), t, .016)


def S_glaceon(t, dur=3.78, cues=None):
    c = bg_gallery(t + 4) * .8
    p = ease(t / dur)
    c, _ = card3d(c, 'c_glaceon.png', 540, 790 + 10 * math.sin(t * 1.4), lerp(1040, 960, p), lerp(-.30, .22, p), .06, lerp(-.03, .02, p),
                  sweep=lerp(-.2, 1.2, p), thick=12, glow=(.32, .32, .32), shadow=.55)
    c = screen(c, np.dstack([snow(t, .8)] * 3), .85)
    cues = cues or {'marvel': 2.3, 'starwars': 3.0}
    for key, x, wl in [('marvel', 330, 330), ('starwars', 760, 250)]:
        s = eback(prog(t, cues[key], cues[key] + .35))
        if s <= 0: continue
        lg = cache('logo_' + key, lambda: (lambda im: cv2.resize(im, (wl, int(im.shape[0] * wl / im.shape[1])), interpolation=cv2.INTER_AREA))(rgba('l_' + key + '.png')))
        c = put_rgba(c, lg, x, 1395, min(1, s * 1.5), scale=max(.01, s))
    return grain(vignette(c), t)


def S_payoff(t, at, dur=5.97):
    """Showcase carousel: the four mangaka covers turn on a slow 3D ring; on each name the ring swings that piece to the
    front and its cover inks into the card; after the last name the ring opens into a floating arc that keeps drifting."""
    c = bg_studio(t)
    cards = ['c_pichu.png', 'c_simisear.png', 'c_palafin.png', 'c_glaceon.png']
    covers = ['m_conan.png', 'm_chiikawa.png', 'm_hokuto.png', 'm_witchhat.png']
    # ring angle: slow spin in, then a swing to each card on its name
    keys = [(0, .9), (at[0] - .30, .12)]
    for i in range(4):                                         # swing in just before the name, hold it front, drift a touch
        keys += [(at[i] - .02, -i * math.pi / 2 + .05), (at[i] + .38, -i * math.pi / 2 - .03)]
    def ring(t):
        if t <= keys[0][0]: return keys[0][1]
        for (ta, va), (tb, vb) in zip(keys, keys[1:]):
            if t <= tb: return lerp(va, vb, ease(prog(t, ta, tb)))
        return keys[-1][1] - .08 * (t - keys[-1][0])        # keeps turning, never stops
    base = ring(t)
    opn = ease(prog(t, at[-1] + .45, at[-1] + 1.15))          # ring -> arc
    intro = eo3(prog(t, 0, .9))
    items = []
    for i in range(4):
        th = base + i * math.pi / 2
        z = math.cos(th)                                      # 1 = front
        rx, ry = 540 + 360 * math.sin(th), 900 - 90 * (1 - z) / 2
        rh = lerp(360, 880, ((z + 1) / 2) ** 1.6) * lerp(.85, 1, intro); ryaw = -.75 * math.sin(th)
        ax = [200, 415, 665, 880][i] + 18 * math.sin(t * .7)  # arc: whole group drifts slowly
        ay = [905, 870, 870, 905][i] + 12 * math.sin(t * 1.6 + i * 1.3)
        ah = [470, 530, 530, 470][i]; ayaw = [.30, .10, -.10, -.30][i] + .05 * math.sin(t * 1.1 + i)
        x, y, h, yaw = lerp(rx, ax, opn), lerp(ry, ay, opn), lerp(rh, ah, opn), lerp(ryaw, ayaw, opn)
        depth = lerp(z, [0, .5, .6, .1][i], opn)
        items.append((depth, i, x, y, h, yaw))
    for depth, i, x, y, h, yaw in sorted(items):
        fade = lerp(.45, 1, (depth + 1) / 2)
        p = eo3(prog(t, at[i], at[i] + .45))
        if p < 1:
            cv_ = bw(rgba(covers[i], int(h * .95))).copy(); cv_[..., :3] *= fade
            c, _ = card3d(c, None, x, y, h * .95, yaw, .05, 0, img=cv_, thick=6, shadow=.45, alpha=(1 - p ** 3) * intro)
            m = ink_burst(x, y, prog(t, at[i] - .05, at[i] + .4), 60 + i, r=320)
            if m is not None: c = c * (1 - m[..., None] * (1 - p) * .95)
        if p > 0:
            im = rgba(cards[i], int(h)).copy(); im[..., :3] *= lerp(fade, 1, opn)
            c, _ = card3d(c, None, x, y, h, yaw, .06, 0, img=im, sweep=lerp(-.3, 1.4, prog(t, at[i] + .1, at[i] + 1.0)) if opn < 1 else lerp(-.3, 1.4, prog(t, at[-1] + 1.2, at[-1] + 2.2)),
                          thick=10, shadow=.5, alpha=p, glow=(.22, .22, .22) if depth > .8 else None)
    return grain(vignette(c, .45), t, .012)


# bottom credit line (fills the low empty band like a documentary lower credit); hook1 also keeps the dashed frame
FOOTERS = {'hook1': ('MANGAKA × POKÉMON TCG', 'FOUR ARTISTS · FIVE CARDS', True),
           'trialhook': ('MANGAKA × POKÉMON TCG', 'FOUR ARTISTS · FIVE CARDS', True),
           'aoyama': ('CHAPTER 01 · GOSHO AOYAMA', 'DETECTIVE CONAN · SINCE 1994', False),
           'pichu': ('SPIKY-EARED PICHU · DPt-P 042', 'SHŌNEN SUNDAY PROMO · 2009', False),
           'hara': ('CHAPTER 03 · TETSUO HARA', 'FIST OF THE NORTH STAR · SINCE 1983', False),
           'flip': ("CRASHER WAKE'S PASSION · 113/078 SAR", 'AURA SEEKER · M7 · 27 NOV 2026', False),
           'payoff': ('IN STOCK AT KARD AVENUE', 'PICHU · SIMISEAR · PALAFIN · GLACEON', False)}


def footer(c, l1, l2, frame=False):
    if frame:
        m = np.zeros((H, W), np.float32)
        for x in range(24, W - 24, 36): cv2.line(m, (x, 24), (x + 18, 24), 1., 2); cv2.line(m, (x, H - 24), (x + 18, H - 24), 1., 2)
        for y in range(24, H - 24, 36): cv2.line(m, (24, y), (24, y + 18), 1., 2); cv2.line(m, (W - 24, y), (W - 24, y + 18), 1., 2)
        c = screen(c, np.dstack([m] * 3), .45)
    t1 = text_rgba(l1, 30, track=4); t2 = text_rgba(l2, 21, track=2)
    c = put_rgba(c, t1, W / 2, 1752, .78); c = put_rgba(c, t2, W / 2, 1796, .6)
    return c


def ai_watermark(c, desc):
    """Marks an engine-built stand-in that will be replaced by an AI-generated b-roll plate."""
    m = np.zeros((H, W), np.float32)
    for x in range(24, W - 24, 36): cv2.line(m, (x, 24), (x + 18, 24), 1., 2); cv2.line(m, (x, H - 24), (x + 18, H - 24), 1., 2)
    for y in range(24, H - 24, 36): cv2.line(m, (24, y), (24, y + 18), 1., 2); cv2.line(m, (W - 24, y), (W - 24, y + 18), 1., 2)
    c = screen(c, np.dstack([m] * 3), .45)
    t1 = text_rgba('SPACE FOR AI VIDEO GENERATION', 30, track=4); t2 = text_rgba(desc.upper(), 21, track=2)
    c = put_rgba(c, t1, W / 2, 1752, .78); c = put_rgba(c, t2, W / 2, 1796, .6)
    return c


SCENES = {'trialhook': (S_trialhook, 6.0), 'hook1': (S_hook1, 3.82), 'hook2': (S_hook2, 3.219), 'aoyama': (S_aoyama, 4.428), 'pichu': (S_pichu, 1.91),
          'nagano': (S_nagano, 1.893), 'versus': (S_versus, 2.528), 'hara': (S_hara, 4.435), 'flip': (S_flip, 5.524),
          'shirahama': (S_shirahama, 3.298), 'glaceon': (S_glaceon, 3.783), 'payoff': (None, 5.973)}

if __name__ == '__main__':
    name, od = sys.argv[1], sys.argv[2]; os.makedirs(od, exist_ok=True)
    fn, dur = SCENES[name]
    if name == 'payoff':
        cfg = json.load(open('reel.json')); s = [x for x in cfg['scenes'] if x['beat'] == 'Payoff'][0]
        at = [k['at'] for k in s['cards']]; fn = lambda t: S_payoff(t, at)
    if name == 'glaceon':
        cfg = json.load(open('reel.json')); s = [x for x in cfg['scenes'] if x['beat'] == 'Shirahama'][1]
        fn = lambda t: S_glaceon(t, cues=s['cues'])
    ts = [float(x) for x in sys.argv[3:]] or [i / FPS for i in range(int(round(dur * FPS)) + 18)]
    for t in ts:
        i = int(round(t * FPS))
        fr = fn(t)
        if name in FOOTERS: fr = footer(fr, *FOOTERS[name])
        Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)).save(f'{od}/f_{i:04d}.jpg', quality=93)
