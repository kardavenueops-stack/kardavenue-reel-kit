"""make_masks.py — outline masks + rim lights for the `spotlight` (trace mode) and `spot_groups` scenes (engine v3.8).

Each member in a group artwork gets two full-size RGBA files next to the art:
  <prefix>mask_<key>.png   white, alpha = the member's silhouette (what stays lit)
  <prefix>rim_<key>.png    warm-white glow hugging the silhouette edge (drawn on top when lit)

Usage:
  pip install "rembg[cpu]" --break-system-packages      # first run downloads the isnet-anime model (~170MB)
  python3 make_masks.py ART.png boxes.json [--prefix hs] [--out assets/]
boxes.json = {"ezreal": [x0, y0, x1, y1], ...}  in 0-1 fractions of the art; one loose box per member
(must contain the whole figure, head to feet — anything outside the box is cut; overlap with neighbours is fine).

How it works: each box is cropped (+6% margin), cut out with rembg `isnet-anime` (best for illustrations;
`isnet-general-use` for photos), then cleaned: only the largest blob touching the box centre is kept, so
neighbours that leak into the crop are dropped. Check every mask over the art (--preview) — for figures that
overlap (e.g. one member standing in front of another) tighten that member's box and re-run just that key.
"""
import argparse, json, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def cut(crop, model):
    from rembg import remove, new_session
    global _S
    try: _S
    except NameError: _S = {}
    if model not in _S: _S[model] = new_session(model)
    return np.asarray(remove(crop, session=_S[model]).split()[3]).astype(np.float32) / 255


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('art'); ap.add_argument('boxes')
    ap.add_argument('--prefix', default='hs'); ap.add_argument('--out', default=None)
    ap.add_argument('--model', default='isnet-anime'); ap.add_argument('--only', default=None, help='comma list of keys to (re)make')
    ap.add_argument('--rim', type=int, default=7, help='rim width in px at art resolution')
    ap.add_argument('--preview', action='store_true', help='also write <prefix>_masks_preview.jpg')
    a = ap.parse_args()
    art = Image.open(a.art).convert('RGB'); W, H = art.size
    out = a.out or os.path.dirname(os.path.abspath(a.art)); boxes = json.load(open(a.boxes))
    keys = a.only.split(',') if a.only else list(boxes)
    prev = np.asarray(art).astype(np.float32) * .25
    for k in keys:
        x0, y0, x1, y1 = boxes[k]; m = .06
        X0, Y0 = int(max(0, (x0 - m) * W)), int(max(0, (y0 - m) * H)); X1, Y1 = int(min(W, (x1 + m) * W)), int(min(H, (y1 + m) * H))
        al = cut(art.crop((X0, Y0, X1, Y1)), a.model)
        lab, n = ndimage.label(al > .5)
        if n > 1:   # keep the blob nearest the box centre (drops neighbours leaking into the crop)
            cy, cx = ((y0 + y1) / 2 * H - Y0), ((x0 + x1) / 2 * W - X0)
            com = ndimage.center_of_mass(al > .5, lab, range(1, n + 1)); size = ndimage.sum(al > .5, lab, range(1, n + 1))
            best = max(range(n), key=lambda i: size[i] / (1 + ((com[i][0] - cy) ** 2 + (com[i][1] - cx) ** 2) ** .5 / 200))
            al = al * ndimage.binary_dilation(lab == best + 1, iterations=3)
        full = np.zeros((H, W), np.float32); full[Y0:Y1, X0:X1] = al
        keep = np.zeros((H, W), np.float32); p = .012   # nothing outside the member's own box (+1.2%) survives -> no neighbour leaks
        keep[int(max(0, (y0 - p) * H)):int(min(H, (y1 + p) * H)), int(max(0, (x0 - p) * W)):int(min(W, (x1 + p) * W))] = 1; full *= keep
        mask = Image.new('RGBA', (W, H), (255, 255, 255, 0)); mask.putalpha(Image.fromarray((full * 255).astype(np.uint8)))
        mask.save(f'{out}/{a.prefix}mask_{k}.png')
        b = full > .5; r = a.rim
        band = (ndimage.binary_dilation(b, iterations=r // 2) & ~ndimage.binary_erosion(b, iterations=r)).astype(np.float32)
        band = np.asarray(Image.fromarray((band * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r * .6))).astype(np.float32)
        rim = Image.new('RGBA', (W, H), (255, 240, 215, 0)); rim.putalpha(Image.fromarray(np.clip(band * 1.1, 0, 252).astype(np.uint8)))
        rim.save(f'{out}/{a.prefix}rim_{k}.png')
        prev = np.where(b[..., None], np.asarray(art), prev)
        print(k, 'ok', f'{b.mean() * 100:.1f}% of art')
    if a.preview:
        Image.fromarray(prev.astype(np.uint8)).resize((W // 3, H // 3)).save(f'{out}/{a.prefix}_masks_preview.jpg', quality=85)


if __name__ == '__main__':
    main()
