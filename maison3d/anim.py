"""Visite animee : entree -> passage -> piece de vie -> salle a manger / baies.

Les images sont calculees une par une (reprise possible : les images deja presentes
sont sautees), puis assemblees en MP4 avec ffmpeg (voir --encode).

usage :
  MAISON_ASSETS=... python anim.py --out frames/ --res 960x540 --samples 48 [--start 1 --end 200 --step 1]
  python anim.py --encode frames/ --fps 25 --video visite.mp4 [--interp 25]
"""
import argparse
import math
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

p = argparse.ArgumentParser()
p.add_argument("--out", default="frames")
p.add_argument("--res", default="960x540")
p.add_argument("--samples", type=int, default=48)
p.add_argument("--threshold", type=float, default=0.03)
p.add_argument("--start", type=int, default=1)
p.add_argument("--end", type=int, default=0)
p.add_argument("--step", type=int, default=1)
p.add_argument("--encode", default="")
p.add_argument("--fps", type=float, default=12.5)
p.add_argument("--interp", type=int, default=25, help="fps final apres interpolation de mouvement (0 = aucune)")
p.add_argument("--video", default="visite.mp4")
args = p.parse_args()

EYE = 1.55
# Chemin camera (coordonnees du plan) : (image, x, y, direction de visee en deg, exposition)
# Images exprimees a 12.5 i/s (la video finale est interpolee a 25 i/s).
KEYS = [
    (1,   12.77, 1.62, 90.0, 1.7),    # dans l'entree, face au passage (porte d'entree dans le dos)
    (28,  12.76, 2.75, 92.0, 1.55),   # on avance vers le passage 12.24-13.27
    (52,  12.55, 3.75, 112.0, 1.15),  # on debouche dans la piece de vie
    (80,  11.40, 4.12, 140.0, 0.95),  # on longe le canape, le regard tourne vers la salle a manger
    (110, 10.10, 4.22, 152.0, 0.9),   # cote ilot, vue sur la table et les baies
    (130, 9.55, 4.28, 158.0, 0.9),    # arret en douceur
]
TOTAL = KEYS[-1][0]


def smoothstep(t):
    return t * t * (3 - 2 * t)


def catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def sample(frame):
    """Position / visee / exposition lissees (spline Catmull-Rom, depart et arrivee en douceur)."""
    # temps global adouci pour un demarrage et un arret progressifs
    u = (frame - 1) / (TOTAL - 1)
    u = smoothstep(min(max(u, 0.0), 1.0))
    f = 1 + u * (TOTAL - 1)
    ks = KEYS
    for i in range(len(ks) - 1):
        if ks[i][0] <= f <= ks[i + 1][0]:
            break
    t = (f - ks[i][0]) / (ks[i + 1][0] - ks[i][0])
    k0 = ks[max(i - 1, 0)]
    k1, k2 = ks[i], ks[i + 1]
    k3 = ks[min(i + 2, len(ks) - 1)]
    vals = [catmull(k0[j], k1[j], k2[j], k3[j], t) for j in range(1, 5)]
    return vals  # x, y, yaw, exposure


def encode():
    frames = args.encode
    pattern = os.path.join(frames, "f%04d.png")
    vf = []
    if args.interp and args.interp > args.fps:
        vf.append(f"minterpolate=fps={args.interp}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
    vf.append("format=yuv420p")
    cmd = ["ffmpeg", "-y", "-framerate", str(args.fps), "-i", pattern, "-vf", ",".join(vf),
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-movflags", "+faststart", args.video]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


if args.encode:
    encode()
    sys.exit(0)

import bpy  # noqa: E402

import archi  # noqa: E402
import interior  # noqa: E402
import scene  # noqa: E402

t0 = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
res = tuple(int(v) for v in args.res.split("x"))
scene.render_settings(samples=args.samples, res=res, threshold=args.threshold)
sc = bpy.context.scene
sc.cycles.seed = 7                # graine fixe : bruit residuel stable d'une image a l'autre
sc.cycles.use_animated_seed = False
M = archi.materials()
archi.floors(M)
archi.walls(M)
archi.windows(M)
archi.interior_doors(M)
archi.roof(M)
archi.exterior(M)
interior.build(M)
scene.world()
scene.portals()
cam = scene.camera("visite", 12.77, 1.62, EYE, 90, lens=17, shift_y=-0.05)
sc.camera = cam
print(f"[anim] scene prete en {time.time() - t0:.1f}s", flush=True)

os.makedirs(args.out, exist_ok=True)
end = args.end or TOTAL
for fr in range(args.start, end + 1, args.step):
    path = os.path.join(args.out, f"f{fr:04d}.png")
    if os.path.exists(path):
        continue
    x, y, yaw, expo = sample(fr)
    cam.location = (x, y, EYE)
    cam.rotation_euler = (math.radians(90), 0, math.radians(yaw - 90))
    sc.view_settings.exposure = expo
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"[frame] {fr}/{end} {time.time() - t:.0f}s", flush=True)
