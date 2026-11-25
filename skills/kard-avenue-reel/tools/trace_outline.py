#!/usr/bin/env python3
"""Trace a whole card character along its black outline -> layer mask for living.py (v3.9).

python3 trace_outline.py CARD.jpg OUT.png x0 y0 x1 y1 [--dark 95]

Box (pixels) loosely around the character. Takes the biggest dark outline in the box, fills
everything it encloses (ears, tail, hands, feet included, no straight cuts), keeps the main blob,
feathers 0.8px. Output: RGBA, alpha = mask (living.py takes colours from the card for 'simmask_*').
Check with an overlay before rendering; works best on inked art with a closed outline.
"""
import argparse
import numpy as np, cv2
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('img'); ap.add_argument('out'); ap.add_argument('box', nargs=4, type=int); ap.add_argument('--dark', type=int, default=95)
a = ap.parse_args()
c = np.asarray(Image.open(a.img).convert('RGB')).astype(np.float32); H, W = c.shape[:2]
lum = c[..., 0] * .299 + c[..., 1] * .587 + c[..., 2] * .114
x0, y0, x1, y1 = a.box
sub = cv2.morphologyEx((lum[y0:y1, x0:x1] < a.dark).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(sub)
ol = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
inv = (1 - ol).astype(np.uint8); cv2.floodFill(inv, np.zeros((inv.shape[0] + 2, inv.shape[1] + 2), np.uint8), (0, 0), 2)
m = np.zeros((H, W), np.uint8); m[y0:y1, x0:x1] = (((inv == 1) | (ol == 1)) * 255).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
m = ((lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])) * 255).astype(np.float32) / 255
rgba = np.zeros((H, W, 4), np.uint8); rgba[..., 3] = (cv2.GaussianBlur(m, (0, 0), .8) * 255).astype(np.uint8)
Image.fromarray(rgba, 'RGBA').save(a.out); print('saved', a.out)
