#!/usr/bin/env python3
"""Trace a glyph mask for an engine `lift` highlight (v3.9).

python3 trace_mask.py IMAGE OUT.png x0 y0 x1 y1 [--cls red,white,yellow,brightred] [--min 200] [--ring]

Box is in fractions of the image (same as the highlight 'box'). The mask is the size of IMAGE:
the letters in the box only (holes filled, specks removed, edges smoothed), so the highlight never
goes beyond the text. --ring adds the thin bright-red outline hugging the letters (for yellow
lettering with a red keyline on a dark red background).
"""
import sys, argparse
import numpy as np, cv2
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('img'); ap.add_argument('out'); ap.add_argument('box', nargs=4, type=float)
ap.add_argument('--cls', default='red,white'); ap.add_argument('--min', type=int, default=200); ap.add_argument('--ring', action='store_true')
a = ap.parse_args()

raw = np.asarray(Image.open(a.img).convert('RGB')).astype(np.int16); H, W = raw.shape[:2]
r, g, b = raw[..., 0], raw[..., 1], raw[..., 2]
CLS = {
    'red': (r > 130) & (g < 125) & (b < 125) & (r - g > 50),
    'brightred': (r > 165) & (r - g > 70) & (b < 120),
    'white': (r > 190) & (g > 190) & (b > 185),
    'yellow': (r > 150) & (g > 125) & (b < 175) & (r - b > 40) & (np.abs(r - g) < 95),
}
x0, y0, x1, y1 = int(a.box[0] * W), int(a.box[1] * H), int(a.box[2] * W), int(a.box[3] * H)
m = np.zeros((H, W), bool)
for c in a.cls.split(','): m |= CLS[c]
sub = m[y0:y1, x0:x1].astype(np.uint8)
sub = cv2.morphologyEx(sub, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(sub); keep = np.zeros_like(sub)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] >= a.min: keep[lab == i] = 1
ff = keep.copy(); cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 1); keep = keep | (1 - ff)
if a.ring: keep = keep | (cv2.dilate(keep, np.ones((7, 7), np.uint8)) & CLS['brightred'][y0:y1, x0:x1].astype(np.uint8))
sm = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.4); keep = (sm > .5).astype(np.float32)
out = np.zeros((H, W), np.float32); out[y0:y1, x0:x1] = cv2.GaussianBlur(keep, (0, 0), .9)
Image.fromarray((out * 255).astype(np.uint8)).save(a.out)
print('saved', a.out)
