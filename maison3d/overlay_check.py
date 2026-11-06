"""Superpose la maquette (spec.py) sur la photo du plan via une homographie,
pour verifier visuellement que murs / ouvertures / mobilier tombent au bon endroit.

usage: python overlay_check.py <photo_plan.jpg> <sortie.png>
"""
import sys
import numpy as np
from PIL import Image, ImageDraw

import spec

# Points de calage : angles exterieurs releves sur la photo (pixels)
SRC = [(0.0, 0.0), (18.21, 0.0), (18.21, 12.56), (0.0, 8.26)]
DST = [(50, 774), (1076, 750), (1021, 60), (58, 322)]


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.array(A, float))
    return vt[-1].reshape(3, 3) / vt[-1][-1]


H = homography(SRC, DST)


def P(x, y):
    p = H @ np.array([x, y, 1.0])
    return (p[0] / p[2], p[1] / p[2])


def rect(d, x0, x1, y0, y1, color, width=2):
    pts = [P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1), P(x0, y0)]
    d.line(pts, fill=color, width=width)


def main(src, out):
    im = Image.open(src).convert("RGB")
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    S = 2
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    def PS(x, y):
        u, v = P(x, y)
        return (u * S, v * S)

    def R(x0, x1, y0, y1, col, w=2):
        pts = [PS(x0, y0), PS(x1, y0), PS(x1, y1), PS(x0, y1), PS(x0, y0)]
        d.line(pts, fill=col, width=w)

    for name, x0, x1, y0, y1, kind in spec.WALLS:
        R(x0, x1, y0, y1, (255, 0, 0, 230) if kind == "ext" else (0, 90, 255, 230), 2)
    wall = {w[0]: w for w in spec.WALLS}
    for wname, axis, a0, a1, z0, z1, kind, info in spec.OPENINGS:
        _, x0, x1, y0, y1, _ = wall[wname]
        if axis == "x":
            R(a0, a1, y0 - 0.05, y1 + 0.05, (0, 200, 0, 255), 3)
        else:
            R(x0 - 0.05, x1 + 0.05, a0, a1, (0, 200, 0, 255), 3)
    for name, f in spec.FURNITURE.items():
        if isinstance(f, dict):
            if "y0" in f:
                R(f["x0"], f["x1"], f["y0"], f["y1"], (255, 0, 255, 220), 2)
            else:
                R(f["x0"], f["x1"], 0.34, 0.34 + f["depth"], (255, 0, 255, 220), 2)
            continue
        cx, cy, w, dd, rot = f
        R(cx - w / 2, cx + w / 2, cy - dd / 2, cy + dd / 2, (255, 0, 255, 220), 2)
    im = Image.alpha_composite(im.convert("RGBA"), ov)
    im.convert("RGB").save(out)
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
