"""Download 2K Poly Haven texture sets into assets/textures/<key>/.
usage: python -I download_ph.py key=id [key=id ...]
Writes assets/textures/_dl_<key>.json with the local map paths.
"""
import sys, os, json, subprocess, hashlib

ASSETS = "/tmp/claude-0/-home-user-isis-medical/29082e2e-5040-5750-9e57-b941bd9f147a/scratchpad/assets"
TEX = os.path.join(ASSETS, "textures")
RES = "2k"
# map role -> (polyhaven key, preferred formats)
ROLES = {
    "color": ("Diffuse", ["jpg", "png"]),
    "roughness": ("Rough", ["jpg", "png"]),
    "normal_gl": ("nor_gl", ["jpg", "png"]),
    "displacement": ("Displacement", ["png", "jpg"]),
    "ao": ("AO", ["jpg", "png"]),
    "metalness": ("Metal", ["jpg", "png"]),
    "mask": ("Mask", ["png", "jpg"]),
}


def curl(url, out=None):
    cmd = ["curl", "-sSL", "--fail", "--retry", "5", "--retry-delay", "3", "--retry-all-errors", "-m", "900", url]
    if out:
        subprocess.run(cmd + ["-o", out], check=True)
        return out
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(key, aid):
    d = os.path.join(TEX, key)
    os.makedirs(d, exist_ok=True)
    files = json.loads(curl(f"https://api.polyhaven.com/files/{aid}"))
    info = json.loads(curl(f"https://api.polyhaven.com/info/{aid}"))
    maps = {}
    for role, (phkey, fmts) in ROLES.items():
        if phkey not in files or RES not in files[phkey]:
            maps[role] = None
            continue
        entry = files[phkey][RES]
        fmt = next((f for f in fmts if f in entry), None)
        if fmt is None:
            maps[role] = None
            continue
        url = entry[fmt]["url"]
        out = os.path.join(d, os.path.basename(url))
        if not (os.path.exists(out) and md5(out) == entry[fmt]["md5"]):
            curl(url, out)
        ok = md5(out) == entry[fmt]["md5"]
        if not ok:
            raise RuntimeError(f"md5 mismatch {out}")
        maps[role] = out
    rec = {"source": "polyhaven", "id": aid, "dir": d, "maps": maps,
           "dimensions_mm": info.get("dimensions"), "authors": info.get("authors"),
           "license": "CC0"}
    with open(os.path.join(TEX, f"_dl_{key}.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(key, aid, {k: (os.path.basename(v) if v else None) for k, v in maps.items()})


for arg in sys.argv[1:]:
    k, a = arg.split("=", 1)
    try:
        fetch(k, a)
    except Exception as e:
        print("FAIL", k, a, e)
