"""Construit la maison et rend les vues.

usage : MAISON_ASSETS=<dossier assets> python build.py --views sejour1,cuisine --samples 256 --res 1920x1280 --out renders/
        python build.py --views all
        python build.py --views plan   (vue de dessus sans toit, pour controle des cotes)
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import archi  # noqa: E402
import scene  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--views", default="all")
p.add_argument("--samples", type=int, default=256)
p.add_argument("--res", default="1920x1280")
p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders"))
p.add_argument("--no-interior", action="store_true")
p.add_argument("--exposure", type=float, default=None)
p.add_argument("--save-blend", default="")
p.add_argument("--threshold", type=float, default=0.015)
args = p.parse_args()

t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
res = tuple(int(v) for v in args.res.split("x"))
scene.render_settings(samples=args.samples, res=res, threshold=args.threshold)
M = archi.materials()
archi.floors(M)
archi.walls(M)
archi.windows(M)
archi.interior_doors(M)
archi.roof(M)
archi.exterior(M)
if not args.no_interior:
    import interior  # noqa: E402
    interior.build(M)
info = scene.world()
scene.portals()
import views  # noqa: E402
cams = views.make_cameras()
print(f"[build] scene prete en {time.time() - t0:.1f}s ; eclairage {info}")
if args.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=args.save_blend)

os.makedirs(args.out, exist_ok=True)
names = list(cams) if args.views == "all" else args.views.split(",")
for n in names:
    cam, opts = cams[n]
    views.prepare(n, opts)
    sc = bpy.context.scene
    sc.camera = cam
    sc.view_settings.exposure = args.exposure if args.exposure is not None else opts.get("exposure", 0.0)
    if "res" in opts:
        sc.render.resolution_x, sc.render.resolution_y = opts["res"]
    else:
        sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(args.out, f"{n}.png")
    t = time.time()
    bpy.ops.render.render(write_still=True)
    views.restore(n, opts)
    print(f"[render] {n} : {time.time() - t:.0f}s -> {sc.render.filepath}", flush=True)
