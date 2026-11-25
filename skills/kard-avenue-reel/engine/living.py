"""living.py - layered 2.5D living-card renderer (frames for the engine's `prerender` scene).

python3 living.py NAME OUTDIR [--stills]      NAME in CARDS below. Writes OUTDIR/f_0000.png ... (1080x1920, no logo/caption).
Layers back->front: inpainted plate, cut-out layers at their own depth, locked text/frame on top.
Camera: one continuous move (perspective, focus band, optional rack focus), never stops.
"""
import sys, os, math, json
import numpy as np, cv2
from PIL import Image, ImageDraw

W, H, FPS = 1080, 1920, 30
S = 2
L = 'lc/'


def poly_cut(img, pts, art):
    Hh, Ww = img.shape[:2]
    def pm(g):
        m = Image.new('L', (Ww, Hh), 0); ImageDraw.Draw(m).polygon(pts, fill=255); m = np.asarray(m)
        if g > 0: m = cv2.dilate(m, np.ones((g, g), np.uint8))
        if g < 0: m = cv2.erode(m, np.ones((-g, -g), np.uint8))
        return m > 127
    return pm


def plate_from(img, union, art, grow=25, sharp=False):
    hole = (cv2.dilate((union > .3).astype(np.uint8), np.ones((grow, grow), np.uint8)) > 0) & art
    Hh, Ww = img.shape[:2]
    small = cv2.resize(img, (Ww // 2, Hh // 2), interpolation=cv2.INTER_AREA)
    hs = cv2.resize(hole.astype(np.uint8), (Ww // 2, Hh // 2), interpolation=cv2.INTER_NEAREST)
    fill = cv2.resize(cv2.inpaint(small, hs, 9, cv2.INPAINT_TELEA), (Ww, Hh), interpolation=cv2.INTER_CUBIC)
    if sharp: fill = cv2.inpaint(img, hole.astype(np.uint8), 7, cv2.INPAINT_TELEA)
    else: fill = cv2.GaussianBlur(fill, (0, 0), 3)
    out = img.copy(); out[hole] = fill[hole]; return out


# ---------------------------------------------------------------- card definitions
# art: art window (u0,u1,v0,v1) fractions; bands: text rows to lock; extra_lock: rects always locked
CARDS = {
    'palafin': dict(src='lc/palafin.jpg', art=(.046, .956, .031, .852),
                    bands=[(.02, .115), (.525, .63), (.685, .775)], extra_lock=[(0, .2, 0, .115), (.06, .32, .525, .57)],
                    layers=[('L_body.png', .45, .012, 0.0), ('L_fist_pink.png', .80, .020, 1.3), ('L_fist_tl.png', .95, .022, 2.4),
                            ('L_fist_bl.png', .85, .018, 3.6), ('L_fist_br.png', 1.0, .024, 4.7)],
                    plate='L_bg.png'),
    'simisear': dict(src='lc/simisear.jpg', art=(.04, .96, .10, .865),
                     bands=[(.02, .115), (.525, .66), (.66, .82)], extra_lock=[(0, .2, 0, .16), (0, 1, .655, .70)],
                     layers=[('simmask_body.png', 1.0, .018, 0.0)], plate=None, grow=9, sharp=True,
                     rig=dict(poly=[(232, 402), (258, 366), (294, 376), (304, 418), (334, 438), (326, 476), (282, 474), (246, 452)], pivot=(320, 456), fn='wave')),
    'crasher': dict(src='lc/crasher.jpg', art=(.042, .958, .125, .865),
                    bands=[(.02, .12), (.63, .72)], extra_lock=[],
                    layers=[('CR_wake.png', 1.0, .012, 0.0)], plate=None,
                    rig=dict(poly=[(600, 330), (640, 250), (700, 172), (792, 160), (818, 234), (766, 306), (722, 388), (662, 424), (606, 402)], pivot=(640, 412), fn='shake')),
}

SHOTS = {   # camera keys: (t, cx, cy, zoom[screen px per 2x card px], yaw, pitch), dur, rack-in, effect timings
    'palafin': dict(dur=5.4, rack=.8, keys=[(0, .26, .30, 1.30, -.16, .10), (2.7, .55, .40, 1.05, .10, .04), (5.4, .50, .50, .545, .03, 0)],
                    trails=[(2.76, 1.6)]),            # fists push + afterimage trails on "tinjunya"
    'simisear': dict(dur=6.1, rack=.7, keys=[(0, .50, .42, .62, .10, .06), (3.3, .50, .36, .95, -.06, .03), (6.1, .50, .48, .545, -.02, 0)],
                     bounce=[3.6]),                 # little hop on "yay"
    'crasher': dict(dur=1.95, rack=0, sharp=True, keys=[(0, .50, .47, .60, -.07, .03), (2.55, .50, .46, .68, .05, .01)],
                    reveal=(0.05, 1.55, 8)),     # the background hands light up one by one around him              # ghost-hand copies fanning out, one by one
}


def load(name):
    C = CARDS[name]
    card = cv2.cvtColor(cv2.imread(C['src']), cv2.COLOR_BGR2RGB)
    ch, cw = card.shape[:2]; CW, CH = cw * S, ch * S
    up = lambda a: cv2.resize(a, (CW, CH), interpolation=cv2.INTER_CUBIC)
    yy, xx = np.mgrid[0:CH, 0:CW]; u, v = xx / CW, yy / CH
    u0, u1, v0, v1 = C['art']
    art = (u > u0) & (u < u1) & (v > v0) & (v < v1)
    cardS = up(card).astype(np.float32) / 255
    hsv = cv2.cvtColor((cardS * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    lum = cardS @ np.array([.299, .587, .114], np.float32)
    band = np.zeros_like(art)
    for a, b in C['bands']: band |= (v > a) & (v < b)
    txt = band & (lum < .32) & (hsv[..., 1] < 95)
    txt = cv2.dilate(txt.astype(np.uint8), np.ones((13, 13), np.uint8)) > 0
    for a, b, c, d in C['extra_lock']: txt |= (u > a) & (u < b) & (v > c) & (v < d)
    top_a = cv2.GaussianBlur(np.where(art, txt, True).astype(np.float32), (0, 0), 1.6)[..., None]
    txt_soft = cv2.GaussianBlur(cv2.dilate(txt.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32), (0, 0), 2)
    lays, union = [], np.zeros((ch, cw), np.float32)
    for f, d, br, ph in C['layers']:
        rgba = np.asarray(Image.open(L + f).convert('RGBA')).astype(np.float32) / 255
        if f.startswith('simmask'):   # mask-only file -> take colours from the card
            rgba = np.dstack([card.astype(np.float32) / 255, rgba[..., 3]])
        union = np.maximum(union, rgba[..., 3])
        r2 = up(rgba); r2[..., 3] *= (1 - txt_soft)
        ys, xs = np.nonzero(r2[..., 3] > .5)
        lays.append((r2, (xs.mean(), ys.mean()), d, br, ph))
    rig = None
    if C.get('rig') and C.get('use_rig'):
        R = C['rig']; pm = Image.new('L', (cw, ch), 0); ImageDraw.Draw(pm).polygon(R['poly'], fill=255)
        lm = cv2.GaussianBlur(up(np.asarray(pm).astype(np.float32) / 255), (0, 0), 3)
        r2, cc, d, br, ph = lays[0]
        limb = r2.copy(); limb[..., 3] *= lm; body = r2.copy(); body[..., 3] *= (1 - lm)
        lays[0] = (body, cc, d, br, ph)
        rig = dict(limb=limb, pivot=(R['pivot'][0] * S, R['pivot'][1] * S), fn=R['fn'], cc=cc, d=d, br=br, ph=ph)
    if C['plate']: plate = cv2.cvtColor(cv2.imread(L + C['plate']), cv2.COLOR_BGR2RGB)
    else:
        artc = np.zeros((ch, cw), bool); artc[int(v0 * ch):int(v1 * ch), int(u0 * cw):int(u1 * cw)] = True
        plate = cv2.cvtColor(plate_from(cv2.cvtColor(card, cv2.COLOR_RGB2BGR), union, artc, C.get('grow', 25), C.get('sharp', False)), cv2.COLOR_BGR2RGB)
    plate = up(plate).astype(np.float32) / 255
    ts = np.clip(cv2.GaussianBlur(cv2.dilate(txt_soft, np.ones((21, 21), np.uint8)), (0, 0), 4), 0, 1)[..., None]
    plate = plate * (1 - ts) + cardS * ts
    # rounded card alpha (real card shape, transparent scan corners)
    m = Image.new('L', (CW, CH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=int(.047 * CW), fill=255)
    shape = np.asarray(m).astype(np.float32) / 255
    ghost_a = (1 - cv2.dilate(txt_soft, np.ones((25, 25), np.uint8))) * cv2.GaussianBlur(((v < .60) & art).astype(np.float32), (0, 0), 25)
    return dict(rig=rig, card=cardS, plate=plate, lays=lays, top=top_a, art=art, shape=shape, CW=CW, CH=CH, ghost=ghost_a)


def ease(x):
    x = min(max(x, 0), 1); return .35 * x + .65 * x * x * (3 - 2 * x)


def lerp(a, b, x): return a + (b - a) * x


def cam(keys, t):
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t <= t1: x = ease((t - t0) / (t1 - t0)); return [lerp(p, q, x) for p, q in zip(a, b)]
    return list(keys[-1][1:])


def place(rgba, cx, cy, dx, dy, sc, CW, CH):
    M = np.array([[sc, 0, (1 - sc) * cx + dx], [0, sc, (1 - sc) * cy + dy]], np.float32)
    return cv2.warpAffine(rgba, M, (CW, CH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def compose(D, sh, t, yaw, pitch):
    CW, CH = D['CW'], D['CH']; img = D['plate'].copy(); art = D['art'][..., None]
    if False and 'hands' in sh:   # ghost-hand afterimages fanning out from the figure, appearing one by one
        t0, t1 = sh['hands']; n = 7
        for k in range(n):
            a = ease((t - (t0 + k * (t1 - t0) / n)) / .45)
            if a <= 0: continue
            ang = -2.6 + k * (5.2 / (n - 1)); r = 90 * S * a
            g = place(np.dstack([D['plate'], D['ghost']]), CW * .5, CH * .45,
                      math.cos(ang) * r, math.sin(ang) * r * .7, 1 + .05 * a * (k % 3), CW, CH)
            glow = g[..., :3] * np.array([.85, .95, 1.15], np.float32)
            img = 1 - (1 - img) * (1 - glow * g[..., 3:4] * .30 * a * art)
    if 'reveal' in sh:
        t0, t1, n = sh['reveal']
        if 'rv' not in D:
            yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
            dx, dy = xx / CW - .5, (yy / CH - .45) * CH / CW
            D['rv'] = (np.arctan2(dy, dx), np.hypot(dx, dy))
            g = D['plate'] @ np.array([.299, .587, .114], np.float32)
            dim = cv2.GaussianBlur(np.dstack([g] * 3), (0, 0), 5) * .28
            D['dim'] = dim.astype(np.float32)
        ang, rad = D['rv']; rev = np.zeros(ang.shape, np.float32)
        order = [-2.4, -.6, 2.6, -1.6, .5, 1.6, -3.0, 3.1][:n]       # top-left, right, left, top, right-low, low, far left...
        for i, a0 in enumerate(order):
            tk = t0 + i * (t1 - t0) / n
            x = min(max((t - tk) / .32, 0), 1)
            if x <= 0: continue
            da = np.abs(np.angle(np.exp(1j * (ang - a0))))
            sec = np.clip((.62 - da) / .25, 0, 1)                    # soft-edged wedge
            grow = np.clip((x * .75 - rad + .12) / .08, 0, 1)       # wipes outward from the figure like strokes being added
            rev = np.maximum(rev, sec * grow)
        rev = np.where(D['art'], rev, 1)[..., None]
        img = D['dim'] * (1 - rev) + img * rev
    px, py = -yaw * 300, -pitch * 300
    for rgba, (cx, cy), d, br, ph in D['lays']:
        sc = 1 + .006 * d * (t / sh['dur'])
        dy_b = 0
        sh = dict(sh); sh.pop('bounce', None); sh.pop('trails', None)
        for tb in sh.get('bounce', []):
            x = (t - tb) / .55
            if 0 <= x <= 1: dy_b -= math.sin(math.pi * x) * 26 * S * (1 - x * .3)
        L_ = place(rgba, cx, cy, px * d, py * d + dy_b, sc, CW, CH)
        a = L_[..., 3:4] * art
        if 'trails' in sh and d > .7:
            for t0, du in sh['trails']:
                x = (t - t0) / du
                if 0 <= x <= 1:
                    push = math.sin(math.pi * x)
                    L2 = place(rgba, cx, cy, px * d, py * d, sc + .16 * push * d, CW, CH)
                    for j, (g, al) in enumerate([(1.06, .38), (1.14, .22), (1.24, .12)]):
                        Lg = place(rgba, cx, cy, px * d * g, py * d * g, sc + .16 * push * d * g, CW, CH)
                        img = 1 - (1 - img) * (1 - Lg[..., :3] * Lg[..., 3:4] * art * al * push)
                    L_ = L2; a = L_[..., 3:4] * art
        img = img * (1 - a) + L_[..., :3] * a
    R = None
    if R:
        if R['fn'] == 'wave':   # finger wag on "yay"
            env = prog_(t, 2.9, 3.3) * (1 - prog_(t, 4.6, 5.0)); ang = 16 * math.sin((t - 2.9) * 10) * env + 4 * math.sin(t * 2)
        else:                   # raised arm: fist shakes as the hands multiply
            env = prog_(t, .0, .3); ang = (-5 + 4 * math.sin(t * 16)) * env
        Mr = cv2.getRotationMatrix2D(R['pivot'], ang, 1.0)
        limb = cv2.warpAffine(R['limb'], Mr, (CW, CH), flags=cv2.INTER_LINEAR)
        sc = 1 + R['br'] * math.sin(t * 1.1 + R['ph']) + .012 * R['d'] * (t / sh['dur'])
        dy_b = 0
        for tb in sh.get('bounce', []):
            x = (t - tb) / .55
            if 0 <= x <= 1: dy_b -= math.sin(math.pi * x) * 26 * S * (1 - x * .3)
        L_ = place(limb, R['cc'][0], R['cc'][1], px * R['d'], py * R['d'] + dy_b, sc, CW, CH)
        a = L_[..., 3:4] * art; img = img * (1 - a) + L_[..., :3] * a
    img = img * (1 - D['top']) + D['card'] * D['top']
    return img


def prog_(t, a, b): return min(max((t - a) / (b - a), 0.), 1.)


F = 2600.0


def project(cx, cy, zoom, yaw, pitch, CW, CH):
    pts = np.array([[0, 0], [CW, 0], [CW, CH], [0, CH]], np.float32)
    X = pts[:, 0] - cx * CW; Y = pts[:, 1] - cy * CH
    X2 = X * math.cos(yaw); Z2 = -X * math.sin(yaw)
    Y3 = Y * math.cos(pitch) - Z2 * math.sin(pitch); Z3 = Y * math.sin(pitch) + Z2 * math.cos(pitch)
    f = F / (F + Z3)
    return pts, np.stack([W / 2 + X2 * f * zoom, H * .47 + Y3 * f * zoom], 1).astype(np.float32)


gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
VIGN = (1 - .5 * np.clip(np.hypot((gx - W / 2) / (W * .75), (gy - H / 2) / (H * .62)), 0, 1) ** 2.2)[..., None]
r = np.hypot((gx - W / 2) / W, (gy - H * .5) / H)
BG = (np.array([26, 26, 26]) / 255 * np.clip(1 - r * 1.6, 0, 1)[..., None] + np.array([10, 10, 10]) / 255).astype(np.float32)


WORLD = {}
def world_bg(t):
    import worlds as Wd
    k = WORLD.get('name')
    if k == 'simisear': return Wd.bg_fun(t, [(.98, .90, .86), (.96, .78, .76)])
    if k == 'palafin': return Wd.bg_ink(t, None, seed=5)
    if k == 'crasher': return Wd.bg_arena(t)
    return BG


def frame(D, sh, t, rng):
    cx, cy, zoom, yaw, pitch = cam(sh['keys'], t)
    img = compose(D, sh, t, yaw, pitch)
    src, dst = project(cx, cy, zoom, yaw, pitch, D['CW'], D['CH'])
    Mh = cv2.getPerspectiveTransform(src, dst)
    rgb = cv2.warpPerspective(img, Mh, (W, H), flags=cv2.INTER_LINEAR)
    a = cv2.warpPerspective(D['shape'], Mh, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    sh_a = cv2.GaussianBlur(a, (0, 0), 30)[..., None] if a.ndim == 3 else None
    out = world_bg(t) * (1 - .7 * cv2.GaussianBlur(a[..., 0], (0, 0), 35)[..., None]) * (1 - a) + rgb * a
    p = t / sh['dur']
    band = np.clip(np.abs(gy - H * .45) / (H * (0.22 + 0.3 * p)), 0, 1)[..., None] ** 1.5
    rack = max(0.0, 1 - t / sh['rack']) ** 1.6 if sh['rack'] else 0
    k = np.clip(band * .8 * (zoom > .7) * (not sh.get('sharp')) + rack, 0, 1)
    if k.max() > .02: out = out * (1 - k) + cv2.GaussianBlur(out, (0, 0), 9) * k
    out = out * VIGN + rng.normal(0, .01, (H, W, 1)).astype(np.float32)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def wm(im, name):
    if name != 'crasher': return im
    import worlds as Wd
    c = np.asarray(im).astype(np.float32) / 255
    c = Wd.footer(c, "ILLUS. TETSUO HARA · 113/078 SAR", "HIS SECOND POKÉMON CARD")
    return Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8))


if __name__ == '__main__':
    name, od = sys.argv[1], sys.argv[2]; os.makedirs(od, exist_ok=True)
    D = load(name); sh = SHOTS[name]; rng = np.random.default_rng(1); WORLD['name'] = name
    times = [float(x) for x in sys.argv[3:] if not x.startswith('--')]
    if times:
        for t in times: wm(frame(D, sh, t, rng), name).save(f'{od}/f_{int(round(t * FPS)):04d}.jpg', quality=94)
        sys.exit(0)
    if '--stills' in sys.argv:
        ts = [sh['dur'] * x for x in (.1, .35, .6, .95)]
        sheet = Image.new('RGB', (270 * len(ts), 480))
        for i, t in enumerate(ts): sheet.paste(frame(D, sh, t, rng).resize((270, 480)), (270 * i, 0))
        sheet.save(f'{od}/stills.png')
    else:
        n = int(round(sh['dur'] * FPS)) + 18      # +0.6s tail so the shot keeps moving under the next dissolve
        for i in range(n): wm(frame(D, sh, i / FPS, rng), name).save(f'{od}/f_{i:04d}.jpg', quality=94)
        json.dump({'n': n, 'fps': FPS}, open(f'{od}/meta.json', 'w'))
