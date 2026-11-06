"""Convertit les rendus PNG en JPEG (galerie / depot).

usage : python finalize.py <dossier_png> <dossier_jpg>
"""
import glob
import os
import sys

from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
for p in sorted(glob.glob(os.path.join(src, "*.png"))):
    im = Image.open(p).convert("RGB")
    out = os.path.join(dst, os.path.splitext(os.path.basename(p))[0] + ".jpg")
    im.save(out, quality=88, optimize=True, progressive=True)
    print(out, os.path.getsize(out) // 1024, "Ko")
