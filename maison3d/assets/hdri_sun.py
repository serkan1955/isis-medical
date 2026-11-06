"""Analyse sun in an equirect HDRI. usage: python -I hdri_sun.py file.hdr [preview.png]"""
import sys, math, json
import numpy as np
import bpy

path = sys.argv[1]
img = bpy.data.images.load(path)
w, h = img.size
px = np.empty(w * h * 4, dtype=np.float32)
img.pixels.foreach_get(px)
arr = px.reshape(h, w, 4)[::-1, :, :3]  # row 0 = top of image
lum = 0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]
mx = float(lum.max())
ys, xs = np.nonzero(lum >= mx * 0.5)
wts = lum[ys, xs]
ang = (xs + 0.5) / w * 2 * math.pi
cx = math.atan2((np.sin(ang) * wts).sum(), (np.cos(ang) * wts).sum()) % (2 * math.pi)
u = cx / (2 * math.pi)
row = (ys * wts).sum() / wts.sum() + 0.5
v = 1.0 - row / h
elev = (v - 0.5) * 180.0
# Blender equirect: direction d -> u = atan2(d.y, -d.x)/(2pi) + 0.5, v = atan2(d.z, hypot(d.x,d.y))/pi + 0.5
phi = (u - 0.5) * 2 * math.pi
el = math.radians(elev)
dx = -math.cos(phi) * math.cos(el)
dy = math.sin(phi) * math.cos(el)
dz = math.sin(el)
# solid-angle weighted energy split: sun region vs rest
theta = (np.arange(h) + 0.5) / h * math.pi  # polar from top
sa = (np.sin(theta) * (math.pi / h) * (2 * math.pi / w))[:, None]
E = lum * sa
sun_mask = lum >= mx * 0.01
# also include a small radius around the centre to capture the sun disc
res = dict(file=path, size=[w, h], sun_uv=[round(u, 5), round(v, 5)], sun_px=[round(cx / (2 * math.pi) * w, 1), round(row, 1)],
           sun_elevation_deg=round(elev, 2),
           sun_dir_world_blender_default_mapping=[round(dx, 4), round(dy, 4), round(dz, 4)],
           sun_azimuth_deg_from_posX_ccw=round(math.degrees(math.atan2(dy, dx)) % 360, 2),
           peak_luminance=round(mx, 1), sun_pixels_above_half_peak=int(len(xs)),
           sun_energy_fraction=round(float(E[sun_mask].sum() / E.sum()), 4),
           mean_luminance=round(float(lum.mean()), 4))
print(json.dumps(res))
if len(sys.argv) > 2:
    from PIL import Image, ImageDraw
    x = arr[::4, ::4] * 0.6
    x = np.clip(x / (1 + x), 0, 1) ** (1 / 2.2)
    im = Image.fromarray((x * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    sx, sy = u * im.width, row / 4
    d.ellipse((sx - 12, sy - 12, sx + 12, sy + 12), outline=(255, 0, 0), width=3)
    im.save(sys.argv[2])
