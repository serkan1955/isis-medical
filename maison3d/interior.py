"""Amenagement interieur : cuisine, sejour, chambres, salle d'eau, entree, terrasse.
Mobilier place d'apres le plan (spec.FURNITURE) ; modeles Poly Haven si disponibles,
sinon modelisation procedurale."""
import json
import math
import os
import random

import bpy
from mathutils import Vector

import spec
from lib3d import (ASSETS, add_bevel, add_subsurf, box, cylinder, emission, image_material, instance,
                   lathe, lib_collection, link, mesh_obj, pbr, principled, set_coll, uv_plane)

H = spec.CEILING
R = random.Random(7)
MODELS = {}


def load_models():
    p = os.path.join(ASSETS, "models.json")
    if ASSETS and os.path.exists(p):
        data = json.load(open(p))
        items = data if isinstance(data, list) else data.get("models", [])
        for e in items:
            if os.path.exists(e.get("blend", "")):
                MODELS[e["id"]] = e


FRONT_ANGLE = {"+X": 0, "+Y": 90, "-X": 180, "-Y": 270}


def place(mid, x, y, face_deg=270, z=0.0, height=None, scale=None, name=None, variant=None, coll_names=None,
          rot_extra=0.0):
    """Pose un modele (instance) : face_deg = direction vers laquelle l'objet doit regarder (angle plan).
    variant : sous-chaine du nom des objets a garder (ex. '_b_' pour une variante)."""
    e = MODELS.get(mid)
    if not e:
        return None
    key = mid + (("@" + variant) if variant else "") + (("#" + ",".join(coll_names)) if coll_names else "")
    keep = (lambda n: variant in n) if variant else None
    lib, dims = lib_collection(e, key, coll_names=coll_names, keep=keep)
    f = FRONT_ANGLE.get(e.get("front", "-Y"), 270)
    rot = math.radians(face_deg - f + rot_extra)
    s = scale or 1.0
    if height:
        s = height / max(dims.z, 1e-6)
    return instance(lib, name or mid, (x, y, z), rot_z=rot, scale=s)


# ------------------------------------------------------------------ materiaux interieurs
def mats():
    m = {}
    m["sofa"] = pbr("tissu_canape", "fabric_sofa", tile=(0.45, 0.45), tint=(0.86, 0.82, 0.76), sheen=0.6,
                    rough_add=0.1, normal=0.8, fallback=(0.72, 0.68, 0.62), fallback_rough=0.9)
    m["linen"] = pbr("lin_blanc", "fabric_linen", tile=(0.35, 0.35), tint=(1.0, 0.99, 0.96), sheen=0.5,
                     normal=0.8, val=1.15, sat=0.3, fallback=(0.88, 0.86, 0.82), fallback_rough=0.9)
    m["linen_sage"] = pbr("lin_sauge", "fabric_linen", tile=(0.35, 0.35), tint=(0.62, 0.68, 0.58), sheen=0.5,
                          normal=0.8, sat=0.4, fallback=(0.55, 0.60, 0.50), fallback_rough=0.9)
    m["linen_terra"] = pbr("lin_terracotta", "fabric_linen", tile=(0.35, 0.35), tint=(0.78, 0.48, 0.36), sheen=0.5,
                           normal=0.8, sat=0.6, fallback=(0.66, 0.38, 0.26), fallback_rough=0.9)
    m["linen_sand"] = pbr("lin_sable", "fabric_linen", tile=(0.35, 0.35), tint=(0.86, 0.78, 0.66), sheen=0.5,
                          normal=0.8, sat=0.5, fallback=(0.78, 0.70, 0.58), fallback_rough=0.9)
    m["rug"] = pbr("tapis", "rug", tile=(0.8, 0.8), tint=(0.95, 0.92, 0.86), normal=1.0, sat=0.5,
                   fallback=(0.80, 0.76, 0.70), fallback_rough=1.0)
    m["oak"] = pbr("chene_meuble", "wood_furniture", tile=(1.2, 1.2), rough_mul=0.8, coat=0.1, normal=0.4,
                   fallback=(0.66, 0.52, 0.38), fallback_rough=0.45)
    m["quartz"] = pbr("quartz", "worktop_stone", tile=(1.6, 1.6), coat=0.25, rough_mul=0.6, normal=0.2,
                      fallback=(0.90, 0.89, 0.86), fallback_rough=0.25)
    m["sage"] = principled("facade_sauge", (0.33, 0.38, 0.33), 0.42, **{"Coat Weight": 0.05})
    m["white_matt"] = principled("blanc_mat", (0.86, 0.86, 0.84), 0.5)
    m["black"] = principled("metal_noir", (0.02, 0.02, 0.022), 0.4, 0.8)
    m["black_glass"] = principled("verre_noir", (0.005, 0.005, 0.006), 0.04, **{"Coat Weight": 1.0})
    m["steel"] = principled("inox", (0.65, 0.65, 0.64), 0.22, 1.0)
    m["brass"] = principled("laiton", (0.78, 0.60, 0.34), 0.3, 1.0)
    m["ceramic"] = principled("ceramique", (0.92, 0.92, 0.90), 0.08, **{"Coat Weight": 0.6})
    m["mirror"] = principled("miroir", (0.95, 0.95, 0.95), 0.0, 1.0)
    m["led"] = emission("led_chaud", (1.0, 0.82, 0.6), 6.0)
    m["shade"] = principled("abat_jour_lin", (0.92, 0.88, 0.80), 0.9, **{"Subsurface Weight": 0.3})
    m["screen"] = principled("ecran_tv", (0.004, 0.004, 0.005), 0.05, **{"Coat Weight": 1.0})
    m["rope"] = principled("corde_ext", (0.55, 0.50, 0.44), 0.9)
    m["teak"] = m["oak"]
    return m


# ------------------------------------------------------------------ utilitaires mobilier
def cushion(name, x0, x1, y0, y1, z0, z1, mat, r=0.04, subd=True):
    ob = box(name, x0, x1, y0, y1, z0, z1, mat, bevel=r, seg=4)
    if subd:
        m = ob.modifiers.new("lissage", "SMOOTH")
        m.iterations = 2
        m.factor = 0.4
    return ob


def plant_fallback(name, x, y, h=1.4, pot_r=0.22, M=None):
    cylinder(name + "_pot", x, y, 0, 0.42, pot_r, M["white_matt"], bevel=0.01)


def pillow(name, x, y, z, w=0.48, h=0.48, t=0.16, rot=0.0, mat=None, tilt=15):
    """Coussin deco : boite subdivisee, gonflee."""
    ob = box(name, -w / 2, w / 2, -t / 2, t / 2, -h / 2, h / 2, mat)
    add_subsurf(ob, 3)
    cs = ob.modifiers.new("gonfle", "CAST")
    cs.factor = 0.12
    cs.cast_type = "SPHERE"
    ob.location = (x, y, z)
    ob.rotation_euler = (math.radians(tilt), 0, rot)
    return ob


def tap(name, x, y, z, facing_deg, mat, reach=0.20, height=0.30):
    """Mitigeur col de cygne (courbe avec epaisseur)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.012
    cu.bevel_resolution = 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    pts = [(0, 0, 0), (0, 0, height), (reach, 0, height - 0.06)]
    for bp, co in zip(sp.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    link(ob)
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, math.radians(facing_deg))
    cylinder(name + "_base", x, y, z, z + 0.05, 0.026, mat)
    return ob


def curtain(name, x0, x1, y, z0, z1, mat, folds=7, amp=0.035, axis="x"):
    """Rideau voilage plisse (ondulations sinus), pose selon un axe."""
    n = folds * 8
    verts, faces = [], []
    L = x1 - x0
    for i in range(n + 1):
        t = i / n
        a = x0 + t * L
        off = amp * math.sin(t * folds * 2 * math.pi)
        for z in (z0, z1):
            verts.append((a, y + off, z) if axis == "x" else (y + off, a, z))
    for i in range(n):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    ob = mesh_obj(name, verts, faces, mat, smooth=True)
    so = ob.modifiers.new("ep", "SOLIDIFY")
    so.thickness = 0.003
    return ob


def sheer_mat():
    if "voilage" in bpy.data.materials:
        return bpy.data.materials["voilage"]
    mat = bpy.data.materials.new("voilage")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.93, 0.91, 0.87, 1)
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Sheen Weight"].default_value = 0.6
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.95, 0.93, 0.88, 1)
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    m1 = nt.nodes.new("ShaderNodeMixShader")
    m1.inputs[0].default_value = 0.45
    nt.links.new(b.outputs[0], m1.inputs[1])
    nt.links.new(tr.outputs[0], m1.inputs[2])
    m2 = nt.nodes.new("ShaderNodeMixShader")
    m2.inputs[0].default_value = 0.35
    nt.links.new(m1.outputs[0], m2.inputs[1])
    nt.links.new(tp.outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], out.inputs[0])
    return mat


def bay_curtains(prefix, a0, a1, y_face, inward_sign, M):
    """Voilages tires de part et d'autre d'une baie (sur rail au plafond), facade selon x."""
    mat = sheer_mat()
    y = y_face + inward_sign * 0.12
    w = 0.45
    curtain(prefix + "_g", a0 - 0.25, a0 - 0.25 + w, y, 0.01, H - 0.04, mat, folds=6, amp=0.04)
    curtain(prefix + "_d", a1 + 0.25 - w, a1 + 0.25, y, 0.01, H - 0.04, mat, folds=6, amp=0.04)
    box(prefix + "_rail", a0 - 0.35, a1 + 0.35, y - 0.012, y + 0.012, H - 0.03, H, M["white_lacquer"])


# ------------------------------------------------------------------ art mural (images generees)
def art_images():
    from PIL import Image, ImageDraw, ImageFilter
    out = {}
    d = os.path.join(ASSETS or "/tmp", "art")
    os.makedirs(d, exist_ok=True)
    specs = {
        "art1": ((900, 1200), [(236, 228, 214), (196, 132, 98), (152, 160, 138), (60, 58, 52)]),
        "art2": ((1200, 900), [(240, 236, 228), (214, 190, 156), (122, 134, 118), (176, 112, 84)]),
        "art3": ((800, 1000), [(232, 226, 216), (90, 104, 96), (204, 168, 128), (40, 40, 38)]),
    }
    for k, (size, pal) in specs.items():
        p = os.path.join(d, k + ".png")
        if not os.path.exists(p):
            rr = random.Random(hash(k) & 0xFFFF)
            im = Image.new("RGB", size, pal[0])
            dr = ImageDraw.Draw(im)
            W, Hh = size
            for i in range(5):
                c = pal[1 + i % 3]
                cx, cy = rr.uniform(0.2, 0.8) * W, rr.uniform(0.2, 0.8) * Hh
                r = rr.uniform(0.12, 0.32) * min(W, Hh)
                if i % 2 == 0:
                    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
                else:
                    dr.rectangle([cx - r * 1.2, cy - r * 0.5, cx + r * 0.6, cy + r * 0.8], fill=c)
            im = im.filter(ImageFilter.GaussianBlur(2))
            # grain papier
            noise = Image.effect_noise(size, 18).convert("RGB")
            im = Image.blend(im, noise, 0.04)
            im.save(p)
        out[k] = p
    return out


def frame_art(name, img, cx, cy, zc, w, h, normal_axis, normal_sign, M, frame_mat=None):
    """Tableau encadre accroche a un mur."""
    fm = frame_mat or M["oak"]
    t = 0.03
    fw = 0.025
    am = image_material("toile_" + name, img)
    if normal_axis == "x":
        x_wall = cx
        s = normal_sign
        box(name + "_cadre", x_wall, x_wall + s * t, cy - w / 2, cy + w / 2, zc - h / 2, zc + h / 2, fm, bevel=0.002)
        # passe-partout
        uv_plane(name + "_toile", (x_wall + s * (t + 0.001), cy + s * (w / 2 - fw), zc - h / 2 + fw),
                 (0, -s * (w - 2 * fw), 0), (0, 0, h - 2 * fw), am)
    else:
        y_wall = cy
        s = normal_sign
        box(name + "_cadre", cx - w / 2, cx + w / 2, y_wall, y_wall + s * t, zc - h / 2, zc + h / 2, fm, bevel=0.002)
        uv_plane(name + "_toile", (cx - s * (w / 2 - fw), y_wall + s * (t + 0.001), zc - h / 2 + fw),
                 (s * (w - 2 * fw), 0, 0), (0, 0, h - 2 * fw), am)


# ------------------------------------------------------------------ CUISINE
def kitchen(M, m):
    set_coll("cuisine")
    # ---- linéaire le long de la facade (x 4.28 -> 8.23), profondeur 0.65
    y_wall = 0.34
    y_front = y_wall + 0.60
    kick, top0, top1 = 0.10, 0.88, 0.92
    x0, x1 = 4.28, 8.23
    box("cuis_socle", x0, x1, y_wall, y_front - 0.06, 0, kick, m["black"])
    box("cuis_caissons", x0, x1, y_wall, y_front - 0.02, kick, top0, m["white_matt"])
    units = [(4.28, 4.88, "panel"), (4.88, 5.48, "drawers3"), (5.48, 5.88, "door"), (5.88, 6.78, "door2"),
             (6.78, 7.38, "drawers3"), (7.38, 8.23, "drawers2")]
    g = 0.003
    for i, (a, b, kind) in enumerate(units):
        zt = top0 - 0.035  # gorge (prise de main integree)
        if kind == "drawers3":
            rows = [(kick, kick + 0.30), (kick + 0.30, kick + 0.55), (kick + 0.55, zt)]
        elif kind == "drawers2":
            rows = [(kick, kick + 0.40), (kick + 0.40, zt)]
        else:
            rows = [(kick, zt)]
        cols = [(a, (a + b) / 2), ((a + b) / 2, b)] if kind == "door2" else [(a, b)]
        for (za, zb) in rows:
            for (ca, cb) in cols:
                box(f"cuis_facade{i}", ca + g, cb - g, y_front - 0.02, y_front, za + g, zb - g, m["sage"], bevel=0.0015, seg=2)
        box(f"cuis_gorge{i}", a, b, y_front - 0.045, y_front - 0.02, zt, top0, m["black"])
    # plan de travail quartz avec decoupe evier
    wt = box("cuis_plan", x0, 8.83, y_wall, y_front + 0.04, top0, top1, m["quartz"], bevel=0.002, seg=2)
    sink_x0, sink_x1 = 6.03, 6.63
    cut = box("cut_evier", sink_x0, sink_x1, y_wall + 0.10, y_front - 0.08, top0 - 0.2, top1 + 0.1)
    bo = wt.modifiers.new("evier", "BOOLEAN")
    bo.operation = "DIFFERENCE"
    bo.object = cut
    bo.solver = "EXACT"
    cut.hide_render = True
    cut.hide_viewport = True
    # cuve inox
    ys0, ys1 = y_wall + 0.10, y_front - 0.08
    zb = top0 - 0.20
    box("evier_fond", sink_x0, sink_x1, ys0, ys1, zb - 0.005, zb, m["steel"])
    box("evier_p1", sink_x0 - 0.003, sink_x0, ys0, ys1, zb, top1 - 0.004, m["steel"])
    box("evier_p2", sink_x1, sink_x1 + 0.003, ys0, ys1, zb, top1 - 0.004, m["steel"])
    box("evier_p3", sink_x0, sink_x1, ys0 - 0.003, ys0, zb, top1 - 0.004, m["steel"])
    box("evier_p4", sink_x0, sink_x1, ys1, ys1 + 0.003, zb, top1 - 0.004, m["steel"])
    cylinder("evier_bonde", (sink_x0 + sink_x1) / 2, (ys0 + ys1) / 2, zb, zb + 0.004, 0.035, m["steel"])
    tap("mitigeur", (sink_x0 + sink_x1) / 2, y_wall + 0.05, top1, 90, m["black"], reach=0.22, height=0.32)
    # credence quartz jusqu'a l'allege de la fenetre (1.10)
    box("cuis_credence", x0, 8.23, y_wall, y_wall + 0.015, top1, spec.SILL - 0.025, m["quartz"])
    # colonne four (contre la cloison du cellier)
    cx0, cx1 = 8.23, 8.83
    box("colonne", cx0, cx1, y_wall, y_front - 0.02, 0, 2.20, m["white_matt"])
    box("colonne_socle", cx0, cx1, y_front - 0.06, y_front, 0, kick, m["black"])
    for (za, zb2, mat_) in [(kick, 0.82, m["sage"]), (1.42, 2.20, m["sage"])]:
        box("colonne_facade", cx0 + g, cx1 - g, y_front - 0.02, y_front, za + g, zb2 - g, mat_, bevel=0.0015, seg=2)
    box("four", cx0 + 0.01, cx1 - 0.01, y_front - 0.02, y_front + 0.005, 0.83, 1.41, m["black_glass"], bevel=0.003)
    box("four_poignee", cx0 + 0.08, cx1 - 0.08, y_front + 0.005, y_front + 0.03, 1.34, 1.355, m["steel"], bevel=0.004)
    # etageres ouvertes chene a gauche de la fenetre
    for zz in (1.45, 1.85):
        box("etagere", 4.30, 5.40, y_wall, y_wall + 0.26, zz, zz + 0.035, m["oak"], bevel=0.002)
    # ---- ilot (6.09 -> 8.65 ; 2.17 -> 3.27) ; meubles cote cuisine, debord repas cote sejour
    ix0, ix1, iy0, iy1 = 6.09, 8.65, 2.17, 3.27
    bx0, bx1 = 6.39, 8.61
    box("ilot_socle", bx0, bx1, iy0 + 0.06, iy0 + 0.60, 0, kick, m["black"])
    box("ilot_caissons", bx0, bx1, iy0 + 0.02, iy0 + 0.62, kick, top0, m["white_matt"])
    nunits = 4
    uw = (bx1 - bx0) / nunits
    for i in range(nunits):
        a = bx0 + i * uw
        b = a + uw
        zt = top0 - 0.035
        rows = [(kick, kick + 0.30), (kick + 0.30, kick + 0.55), (kick + 0.55, zt)] if i in (1, 2) else [(kick, zt)]
        for (za, zb2) in rows:
            box(f"ilot_facade{i}", a + g, b - g, iy0, iy0 + 0.02, za + g, zb2 - g, m["sage"], bevel=0.0015, seg=2)
        box(f"ilot_gorge{i}", a, b, iy0 + 0.02, iy0 + 0.045, zt, top0, m["black"])
    # dos de l'ilot en chene (cote assises)
    box("ilot_dos", bx0, bx1, iy0 + 0.62, iy0 + 0.65, 0, top0, m["oak"], bevel=0.002)
    # plan + retombee (joue) cote est en quartz
    box("ilot_plan", ix0, ix1, iy0 - 0.02, iy1, top0, top1, m["quartz"], bevel=0.003, seg=2)
    box("ilot_joue", bx1, ix1, iy0 - 0.02, iy1, 0, top0, m["quartz"], bevel=0.002)
    # plaque induction
    box("induction", 7.10, 7.88, iy0 + 0.06, iy0 + 0.58, top1, top1 + 0.006, m["black_glass"], bevel=0.002)
    # ---- tabourets : 2 cote sejour, 1 en bout
    stools = [(6.58, 3.50, 270), (7.19, 3.50, 270), (5.85, 2.62, 0)]
    for k, (sx, sy, face) in enumerate(stools):
        if not place("bar_chair_round_01", sx, sy, face, scale=0.943, name=f"tabouret{k}"):
            cylinder(f"tabouret{k}_assise", sx, sy, 0.63, 0.68, 0.18, m["oak"], bevel=0.01)
            cylinder(f"tabouret{k}_pied", sx, sy, 0.0, 0.63, 0.02, m["black"])
    # ---- suspensions au-dessus de l'ilot
    for k, px in enumerate((6.75, 7.45, 8.15)):
        pendant(f"susp_ilot{k}", px, 2.72, 1.72, m, r=0.11)
    # ---- deco cuisine
    place("wooden_cutting_board", 5.10, 0.52, 90, z=top1, name="planche")
    place("vintage_electric_kettle", 4.65, 0.55, 300, z=top1, name="bouilloire")
    place("wooden_bowl_01", 7.55, 2.95, 0, z=top1, name="coupe")
    place("food_apple_01", 7.55, 2.95, 0, z=top1 + 0.02, name="pommes")
    place("jug_01", 4.55, 0.47, 0, z=1.48, name="pichet")
    place("ceramic_vase_02", 5.05, 0.46, 0, z=1.885, name="vase_etagere")
    place("wine_bottles_01", 8.05, 0.55, 0, z=top1, name="bouteilles")


def pendant(name, x, y, zb, m, r=0.12, drop_to=H):
    """Suspension : cable + abat-jour metal noir (interieur laiton) + ampoule."""
    cylinder(name + "_cable", x, y, zb + 0.12, drop_to, 0.002, m["black"], seg=8)
    prof = [(0.008, 0.14), (0.03, 0.135), (r * 0.55, 0.11), (r * 0.9, 0.05), (r, 0.0), (r - 0.003, 0.0),
            (r * 0.88, 0.047), (r * 0.53, 0.105), (0.028, 0.13), (0.006, 0.134)]
    lathe(name + "_abat", prof, x, y, zb, m["black"], seg=48)
    cylinder(name + "_patere", x, y, drop_to - 0.012, drop_to, 0.05, m["black"])
    ball = bpy.data.meshes.new(name + "_ampoule")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.03)
    bm.to_mesh(ball)
    bm.free()
    ob = bpy.data.objects.new(name + "_ampoule", ball)
    ob.location = (x, y, zb + 0.06)
    ball.materials.append(emission("ampoule_allumee", (1.0, 0.78, 0.52), 60.0))
    link(ob)


# ------------------------------------------------------------------ SEJOUR / SALLE A MANGER
def living(M, m, art):
    set_coll("sejour")
    # ---- table a manger chene 2.00 x 1.00
    cx, cy, w, d, _ = spec.FURNITURE["table_repas"]
    d = 1.00
    tx0, tx1, ty0, ty1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
    box("table_plateau", tx0, tx1, ty0, ty1, 0.715, 0.755, m["oak"], bevel=0.006, seg=3)
    for lx in (tx0 + 0.12, tx1 - 0.12):
        # pieds en V (trapeze) chene
        box("table_pied", lx - 0.035, lx + 0.035, ty0 + 0.10, ty1 - 0.10, 0.0, 0.715, m["oak"], bevel=0.004)
    box("table_entretoise", tx0 + 0.12, tx1 - 0.12, cy - 0.025, cy + 0.025, 0.62, 0.70, m["oak"], bevel=0.003)
    chairs = [(cx - 0.45, ty0 - 0.22, 90), (cx + 0.45, ty0 - 0.22, 90), (cx - 0.45, ty1 + 0.22, 270),
              (cx + 0.45, ty1 + 0.22, 270), (tx0 - 0.25, cy, 0), (tx1 + 0.25, cy, 180)]
    for k, (x, y, face) in enumerate(chairs):
        place("dining_chair_02", x, y, face, name=f"chaise{k}")
    place("ceramic_vase_01", cx + 0.25, cy + 0.05, 0, z=0.755, name="vase_table")
    place("potted_plant_04", cx - 0.30, cy, 0, z=0.755, name="plante_table")
    # suspension large au-dessus de la table
    for k, px in enumerate((cx - 0.45, cx + 0.45)):
        pendant(f"susp_table{k}", px, cy, 1.62, m, r=0.20)
    # ---- canape d'angle (x 9.85-12.24, y 4.62-7.70)
    sf = spec.FURNITURE["canape_L"]
    X0, X1, Y0, Y1, D = sf["x0"], sf["x1"], sf["y0"], sf["y1"], sf["depth"]
    zseat0, zseat1, zback = 0.20, 0.44, 0.80
    mat = m["sofa"]
    # socles
    box("canape_socle_o", X0, X0 + D, Y0, Y1, 0.05, zseat0, mat, bevel=0.02, seg=3)
    box("canape_socle_s", X0 + D, X1, Y0, Y0 + D, 0.05, zseat0, mat, bevel=0.02, seg=3)
    for (px, py) in [(X0 + 0.06, Y0 + 0.06), (X0 + 0.06, Y1 - 0.06), (X1 - 0.06, Y0 + 0.06), (X0 + D - 0.06, Y1 - 0.06), (X1 - 0.06, Y0 + D - 0.06)]:
        cylinder("canape_pied", px, py, 0.0, 0.05, 0.022, m["black"])
    # dossiers
    cushion("canape_dos_o", X0, X0 + 0.20, Y0, Y1, zseat0, zback - 0.12, mat, r=0.05)
    cushion("canape_dos_s", X0, X1, Y0, Y0 + 0.20, zseat0, zback - 0.12, mat, r=0.05)
    # accoudoirs
    cushion("canape_acc_n", X0, X0 + D, Y1 - 0.20, Y1, zseat0, 0.60, mat, r=0.06)
    cushion("canape_acc_e", X1 - 0.20, X1, Y0, Y0 + D, zseat0, 0.60, mat, r=0.06)
    # coussins d'assise (bras ouest : y de Y0+0.20 a Y1-0.20 ; bras sud : x de X0+D a X1-0.20)
    segs_o = 3
    L = (Y1 - 0.20) - (Y0 + D)
    for i in range(segs_o):
        a = Y0 + D + i * L / segs_o
        cushion(f"canape_assise_o{i}", X0 + 0.20, X0 + D, a + 0.005, a + L / segs_o - 0.005, zseat0, zseat1, mat, r=0.05)
        cushion(f"canape_dossier_o{i}", X0 + 0.16, X0 + 0.38, a + 0.01, a + L / segs_o - 0.01, zseat1 - 0.02, zback, mat, r=0.07)
    cushion("canape_assise_angle", X0 + 0.20, X0 + D, Y0 + 0.20, Y0 + D, zseat0, zseat1, mat, r=0.05)
    L2 = (X1 - 0.20) - (X0 + D)
    for i in range(2):
        a = X0 + D + i * L2 / 2
        cushion(f"canape_assise_s{i}", a + 0.005, a + L2 / 2 - 0.005, Y0 + 0.20, Y0 + D, zseat0, zseat1, mat, r=0.05)
        cushion(f"canape_dossier_s{i}", a + 0.01, a + L2 / 2 - 0.01, Y0 + 0.16, Y0 + 0.38, zseat1 - 0.02, zback, mat, r=0.07)
    cushion("canape_dossier_angle", X0 + 0.16, X0 + 0.38, Y0 + 0.16, Y0 + D, zseat1 - 0.02, zback, mat, r=0.07)
    # coussins deco
    pillow("coussin1", X0 + 0.42, Y1 - 0.55, 0.66, mat=m["linen_terra"], rot=math.radians(90), tilt=12)
    pillow("coussin2", X0 + 0.42, Y1 - 1.05, 0.66, mat=m["linen_sand"], rot=math.radians(90), tilt=14, w=0.42, h=0.42)
    pillow("coussin3", X0 + 0.45, Y0 + 0.45, 0.66, mat=m["linen_sage"], rot=math.radians(45), tilt=12)
    pillow("coussin4", X1 - 0.55, Y0 + 0.42, 0.66, mat=m["linen_terra"], rot=0, tilt=-12, w=0.42, h=0.42)
    # plaid sur l'accoudoir
    cushion("plaid", X0 + 0.25, X0 + 0.80, Y1 - 0.28, Y1 + 0.01, 0.585, 0.615, m["linen_sand"], r=0.012)
    # ---- tapis
    box("tapis_salon", 10.45, 13.05, 5.05, 7.45, 0.0, 0.012, m["rug"], bevel=0.004, seg=1)
    # ---- table basse + fauteuil
    tbx, tby, _, _, _ = spec.FURNITURE["table_basse"]
    if not place("coffee_table_round_01", tbx, tby, 0, scale=0.65, name="table_basse"):
        place("modern_coffee_table_01", tbx, tby, 0, name="table_basse")
    fx, fy, _, _, frot = spec.FURNITURE["fauteuil"]
    place("modern_arm_chair_01", fx, fy, 225, name="fauteuil") or place("mid_century_lounge_chair", fx, fy, 225, name="fauteuil")
    # ---- meuble TV + TV murale (cloison du couloir x = 13.98)
    xw = 13.98
    box("meuble_tv", xw - 0.42, xw, 5.75, 7.45, 0.18, 0.56, m["oak"], bevel=0.004)
    for yy in (5.80, 7.40):
        box("meuble_tv_pied", xw - 0.38, xw - 0.04, yy - 0.02, yy + 0.02, 0, 0.18, m["black"])
    for k in range(3):
        a = 5.77 + k * (1.66 / 3)
        box("meuble_tv_porte", xw - 0.43, xw - 0.42, a + 0.004, a + 1.66 / 3 - 0.004, 0.19, 0.55, m["oak"], bevel=0.001)
    box("tv", xw - 0.04, xw - 0.01, 6.60 - 0.73, 6.60 + 0.73, 1.02, 1.86, m["screen"], bevel=0.004)
    box("tv_cadre", xw - 0.035, xw - 0.012, 6.60 - 0.735, 6.60 + 0.735, 1.015, 1.865, m["black"])
    place("ceramic_vase_03", xw - 0.22, 5.95, 0, z=0.56, name="vase_tv")
    place("decorative_book_set_01", xw - 0.22, 7.10, 180, z=0.56, name="livres_tv", variant="cover0")
    # ---- plantes
    place("potted_plant_01", 13.50, 7.58, 0, name="plante_angle")
    place("potted_plant_01", 4.62, 7.55, 140, name="plante_repas")
    place("potted_plant_02", 9.50, 4.70, 0, name="plante_canape")
    # ---- lampadaire pres du fauteuil (simple, metal noir + abat-jour lin)
    lx, ly = 9.72, 7.62
    cylinder("lampadaire_pied", lx, ly, 0, 0.02, 0.15, m["black"])
    cylinder("lampadaire_tige", lx, ly, 0.02, 1.45, 0.009, m["black"])
    lathe("lampadaire_abat", [(0.20, 0.0), (0.16, 0.30)], lx, ly, 1.35, m["shade"])
    # ---- tableaux
    frame_art("tableau_repas", art["art2"], 4.28, 6.20, 1.55, 1.20, 0.90, "x", +1, M)
    # ---- voilages des baies du sejour
    for (a0, a1) in [(5.28, 8.28), (9.99, 12.99)]:
        bay_curtains(f"voilage_{a0:.0f}", a0, a1, 7.92, -1, M)
    # ---- spots encastres
    for (sx, sy, on) in [(5.0, 1.6, True), (6.5, 1.6, True), (8.0, 1.6, True), (12.7, 2.0, True), (12.7, 2.9, True),
                         (14.55, 4.5, True), (14.55, 6.5, True), (14.55, 8.2, False), (16.0, 4.45, True), (17.0, 4.45, True)]:
        spot(f"spot_{sx}_{sy}", sx, sy, m, on)


def spot(name, x, y, m, on=False):
    cylinder(name, x, y, H - 0.004, H, 0.045, m["white_matt"], seg=24)
    mat = emission("spot_allume", (1.0, 0.86, 0.68), 260.0) if on else principled("spot_reflecteur", (0.7, 0.7, 0.7), 0.2, 1.0)
    cylinder(name + "_in", x, y, H - 0.005, H - 0.004, 0.03, mat, seg=24)


# ------------------------------------------------------------------ CHAMBRES
def bed(prefix, x0, x1, y0, y1, head, m, duvet_mat=None, throw_mat=None, headboard_mat=None):
    """Lit complet. head = 'x0','x1','y0','y1' : cote de la tete de lit (contre le mur)."""
    dm = duvet_mat or m["linen"]
    hb = headboard_mat or m["sofa"]
    along_x = head in ("x0", "x1")
    # tete de lit capitonnee
    if head == "x0":
        cushion(prefix + "_tete", x0, x0 + 0.09, y0 - 0.10, y1 + 0.10, 0.25, 1.15, hb, r=0.03)
        bx0, bx1, by0, by1 = x0 + 0.09, x1, y0, y1
    elif head == "x1":
        cushion(prefix + "_tete", x1 - 0.09, x1, y0 - 0.10, y1 + 0.10, 0.25, 1.15, hb, r=0.03)
        bx0, bx1, by0, by1 = x0, x1 - 0.09, y0, y1
    elif head == "y1":
        cushion(prefix + "_tete", x0 - 0.10, x1 + 0.10, y1 - 0.09, y1, 0.25, 1.15, hb, r=0.03)
        bx0, bx1, by0, by1 = x0, x1, y0, y1 - 0.09
    else:
        cushion(prefix + "_tete", x0 - 0.10, x1 + 0.10, y0, y0 + 0.09, 0.25, 1.15, hb, r=0.03)
        bx0, bx1, by0, by1 = x0, x1, y0 + 0.09, y1
    # sommier tapissier + matelas
    cushion(prefix + "_sommier", bx0 + 0.02, bx1 - 0.02, by0 + 0.02, by1 - 0.02, 0.08, 0.32, hb, r=0.02, subd=False)
    for (px, py) in [(bx0 + 0.08, by0 + 0.08), (bx1 - 0.08, by0 + 0.08), (bx0 + 0.08, by1 - 0.08), (bx1 - 0.08, by1 - 0.08)]:
        cylinder(prefix + "_pied", px, py, 0, 0.08, 0.025, m["oak"])
    cushion(prefix + "_matelas", bx0 + 0.02, bx1 - 0.02, by0 + 0.02, by1 - 0.02, 0.32, 0.54, m["linen"], r=0.05)
    # couette (debord sur les cotes, rabattue cote tete)
    ov = 0.10
    if along_x:
        cx0 = bx0 + 0.55 if head == "x0" else bx0 - 0.04
        cx1 = bx1 + 0.04 if head == "x0" else bx1 - 0.55
        duv = cushion(prefix + "_couette", cx0, cx1, by0 - ov, by1 + ov, 0.36, 0.60, dm, r=0.07)
    else:
        cy0 = by0 - 0.04 if head == "y1" else by0 + 0.55
        cy1 = by1 - 0.55 if head == "y1" else by1 + 0.04
        duv = cushion(prefix + "_couette", bx0 - ov, bx1 + ov, cy0, cy1, 0.36, 0.60, dm, r=0.07)
    d = duv.modifiers.new("plis", "DISPLACE")
    tx = bpy.data.textures.new(prefix + "_plis", "CLOUDS")
    tx.noise_scale = 0.18
    d.texture = tx
    d.strength = 0.018
    sub = duv.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    duv.modifiers.move(len(duv.modifiers) - 1, 0)
    # oreillers
    w = (by1 - by0) if along_x else (bx1 - bx0)
    n = 2
    for i in range(n):
        if along_x:
            yc = by0 + (i + 0.5) * w / n
            xc = bx0 + 0.25 if head == "x0" else bx1 - 0.25
            pillow(f"{prefix}_oreiller{i}", xc, yc, 0.66, w=0.62, h=0.42, t=0.14, rot=math.radians(90), mat=m["linen"],
                   tilt=-62 if head == "x0" else 62)
        else:
            xc = bx0 + (i + 0.5) * w / n
            yc = by1 - 0.25 if head == "y1" else by0 + 0.25
            pillow(f"{prefix}_oreiller{i}", xc, yc, 0.66, w=0.62, h=0.42, t=0.14, rot=0, mat=m["linen"],
                   tilt=62 if head == "y1" else -62)
    # plaid au pied du lit
    tm = throw_mat or m["linen_terra"]
    if along_x:
        fx0, fx1 = (bx1 - 0.55, bx1 + 0.05) if head == "x0" else (bx0 - 0.05, bx0 + 0.55)
        cushion(prefix + "_plaid", fx0, fx1, by0 - ov - 0.02, by1 + ov + 0.02, 0.58, 0.63, tm, r=0.02)
    else:
        fy0, fy1 = (by0 - 0.05, by0 + 0.55) if head == "y1" else (by1 - 0.55, by1 + 0.05)
        cushion(prefix + "_plaid", bx0 - ov - 0.02, bx1 + ov + 0.02, fy0, fy1, 0.58, 0.63, tm, r=0.02)


def nightstand(prefix, x, y, m, lamp=True):
    box(prefix, x - 0.22, x + 0.22, y - 0.20, y + 0.20, 0.0, 0.50, m["oak"], bevel=0.004)
    box(prefix + "_tiroir", x - 0.20, x + 0.20, y - 0.205, y - 0.20, 0.30, 0.47, m["oak"], bevel=0.001)
    if lamp:
        lathe(prefix + "_lampe_pied", [(0.07, 0.0), (0.09, 0.10), (0.07, 0.24), (0.015, 0.30), (0.0, 0.30)], x, y, 0.50, m["ceramic"])
        lathe(prefix + "_lampe_abat", [(0.15, 0.0), (0.12, 0.20)], x, y, 0.78, m["shade"])
        cylinder(prefix + "_lampe_ampoule", x, y, 0.83, 0.90, 0.025, emission("ampoule_allumee", (1.0, 0.78, 0.52), 60.0))


def wardrobe(prefix, x0, x1, y0, y1, face, m):
    """Placard toute hauteur, facades laquees blanches. face : 'x+','x-','y+','y-'."""
    box(prefix, x0, x1, y0, y1, 0.0, H, m["white_matt"])
    along = "y" if face[0] == "x" else "x"
    a0, a1 = (y0, y1) if along == "y" else (x0, x1)
    nd = max(2, round((a1 - a0) / 0.6))
    w = (a1 - a0) / nd
    for i in range(nd):
        b0, b1 = a0 + i * w + 0.002, a0 + (i + 1) * w - 0.002
        if face == "x+":
            box(prefix + "_porte", x1, x1 + 0.02, b0, b1, 0.01, H - 0.01, m["white_matt"], bevel=0.001)
            box(prefix + "_poignee", x1 + 0.02, x1 + 0.035, (b0 + b1) / 2 + (0.27 if i % 2 == 0 else -0.27) - 0.006,
                (b0 + b1) / 2 + (0.27 if i % 2 == 0 else -0.27) + 0.006, 0.85, 1.35, m["black"], bevel=0.003)
        elif face == "y+":
            box(prefix + "_porte", b0, b1, y1, y1 + 0.02, 0.01, H - 0.01, m["white_matt"], bevel=0.001)
            hx = (b0 + b1) / 2 + (0.27 if i % 2 == 0 else -0.27)
            box(prefix + "_poignee", hx - 0.006, hx + 0.006, y1 + 0.02, y1 + 0.035, 0.85, 1.35, m["black"], bevel=0.003)
        elif face == "y-":
            box(prefix + "_porte", b0, b1, y0 - 0.02, y0, 0.01, H - 0.01, m["white_matt"], bevel=0.001)
            hx = (b0 + b1) / 2 + (0.27 if i % 2 == 0 else -0.27)
            box(prefix + "_poignee", hx - 0.006, hx + 0.006, y0 - 0.035, y0 - 0.02, 0.85, 1.35, m["black"], bevel=0.003)


def bedrooms(M, m, art):
    set_coll("chambres")
    # Chambre parentale 14.82 : lit 160 tete contre le mur gauche
    bed("lit1", 0.34, 2.34, 5.20, 6.80, "x0", m, throw_mat=m["linen_terra"])
    nightstand("chevet1a", 0.58, 4.82, m)
    nightstand("chevet1b", 0.58, 7.18, m)
    box("tapis_ch1", 1.0, 3.2, 4.75, 7.25, 0, 0.012, m["rug"], bevel=0.003, seg=1)
    frame_art("tableau_ch1", art["art1"], 0.34, 6.00, 1.62, 0.70, 0.90, "x", +1, M, m["black"])
    bay_curtains("voilage_ch1", 1.56, 3.56, 7.92, -1, M)
    place("potted_plant_02", 3.85, 7.55, 0, name="plante_ch1")
    # Chambre 11.51 (aile, haut) : tete contre le pignon droit
    bed("lit2", 15.87, 17.87, 10.15, 11.75, "x1", m, throw_mat=m["linen_sage"])
    nightstand("chevet2a", 17.62, 9.78, m)
    nightstand("chevet2b", 17.62, 12.0, m, lamp=True)
    x0, x1, y0, y1 = 14.05, 14.60, 10.60, 12.22
    wardrobe("placard_ch2", x0, x1, y0, y1, "x+", m)
    box("tapis_ch2", 15.3, 17.2, 9.75, 12.0, 0, 0.012, m["rug"], bevel=0.003, seg=1)
    # Chambre 10.62 : tete contre la cloison nord (y = 9.35)
    bed("lit3", 15.65, 17.25, 7.35, 9.35, "y1", m, throw_mat=m["linen_terra"])
    nightstand("chevet3a", 15.40, 9.12, m)
    nightstand("chevet3b", 17.50, 9.12, m)
    wardrobe("placard_ch3", 16.27, 17.87, 5.49, 6.09, "y+", m)
    box("tapis_ch3", 15.4, 17.5, 6.65, 8.6, 0, 0.012, m["rug"], bevel=0.003, seg=1)
    frame_art("tableau_ch3", art["art3"], 16.45, 9.35, 1.62, 0.60, 0.75, "y", -1, M, m["oak"])
    curtain("voilage_ch3", 6.70, 7.15, 17.87 - 0.12, 0.01, H - 0.04, sheer_mat(), folds=5, amp=0.035, axis="y")
    # Chambre 11.69 : tete contre la cloison nord (y = 3.40)
    bed("lit4", 15.80, 17.40, 1.40, 3.40, "y1", m, throw_mat=m["linen_sage"])
    nightstand("chevet4a", 15.53, 3.17, m)
    nightstand("chevet4b", 17.65, 3.17, m)
    wardrobe("placard_ch4", 14.05, 14.65, 0.40, 1.90, "x+", m)


# ------------------------------------------------------------------ SALLE D'EAU
def suite(M, m):
    """Suite parentale : salle d'eau (piece 3) et dressing (piece 2), d'apres le plan et le proprietaire."""
    set_coll("suite_parentale")
    tw = M["tile_wall"]
    t = 0.012
    # ---- salle d'eau parentale : x 0.34-2.24, y 0.34-4.02 ; douche dessinee cote facade
    X0, X1, Y0, Y1 = 0.34, 2.24, 0.34, 4.02
    sx0, sx1, sy0, sy1 = 1.34, X1, Y0, 1.25
    box("sdep_faience_e", X1 - t, X1, Y0, sy1 + 0.02, 0.004, 2.20, tw)
    box("sdep_faience_s", sx0 - 0.02, X1, Y0, Y0 + t, 0.004, 1.08, tw)
    box("sdep_receveur", sx0, X1 - t, Y0 + t, sy1, 0.004, 0.03, principled("receveur_resine", (0.82, 0.81, 0.78), 0.55), bevel=0.003)
    box("sdep_caniveau", sx0 + 0.10, X1 - 0.10, Y0 + 0.08, Y0 + 0.12, 0.03, 0.032, m["black"])
    gl = bpy.data.materials.get("verre")
    box("sdep_paroi", sx0, X1 - t, sy1, sy1 + 0.008, 0.03, 2.00, gl)
    box("sdep_paroi_profil", sx0, X1 - t, sy1 - 0.002, sy1 + 0.01, 1.98, 2.00, m["black"])
    box("sdep_paroi_barre", sx0, sx0 + 0.02, sy1, sy1 + 0.008, 0.03, 2.00, m["black"])
    cylinder("sdep_colonne", X1 - 0.04, 0.80, 0.90, 2.15, 0.012, m["black"])
    box("sdep_bras", X1 - 0.30, X1 - 0.03, 0.79, 0.81, 2.14, 2.16, m["black"])
    cylinder("sdep_tete", X1 - 0.30, 0.80, 2.13, 2.15, 0.15, m["black"])
    box("sdep_mitigeur", X1 - 0.05, X1 - t, 0.74, 0.86, 1.05, 1.11, m["black"], bevel=0.008)
    # meuble double vasque contre le mur gauche (x = 0.34)
    vy0, vy1 = 1.75, 3.15
    box("sdep_faience_vasque", X0, X0 + t, vy0 - 0.05, vy1 + 0.05, 0.004, 1.20, tw)
    box("sdep_meuble", X0 + t, X0 + 0.50, vy0, vy1, 0.42, 0.82, m["oak"], bevel=0.003)
    box("sdep_plan", X0 + t, X0 + 0.52, vy0, vy1, 0.82, 0.85, m["quartz"], bevel=0.002)
    for k, vy in enumerate((vy0 + 0.35, vy1 - 0.35)):
        lathe(f"sdep_vasque{k}", [(0.0, 0.0), (0.16, 0.0), (0.20, 0.03), (0.21, 0.13), (0.195, 0.13), (0.185, 0.04), (0.0, 0.02)],
              X0 + 0.29, vy, 0.85, m["ceramic"])
        tap(f"sdep_robinet{k}", X0 + 0.06, vy, 0.85, 0, m["black"], reach=0.13, height=0.26)
    box("sdep_miroir", X0 + t, X0 + t + 0.02, vy0 + 0.05, vy1 - 0.05, 1.05, 1.85, m["mirror"], bevel=0.004)
    box("sdep_miroir_led", X0 + t, X0 + t + 0.01, vy0 + 0.07, vy1 - 0.07, 1.07, 1.83, m["led"])
    for k in range(8):
        box(f"sdep_radiateur{k}", X0 + t, X0 + 0.05, 3.40, 3.90, 0.40 + k * 0.14, 0.42 + k * 0.14, m["black"], bevel=0.008)
    cushion("sdep_serviette", X0 + 0.05, X0 + 0.11, 3.45, 3.85, 1.0, 1.42, m["linen_sand"], r=0.015)
    for (sx, sy) in [(1.30, 2.40), (1.30, 3.50), (1.79, 0.80)]:
        spot(f"spot_sdep_{sx}_{sy}", sx, sy, m, on=True)
    # ---- dressing : x 2.31-4.21, y 0.34-4.02 (sans fenetre)
    D0, D1, E0, E1 = 2.31, 4.21, 0.34, 4.02
    oak = m["oak"]
    # rangements ouverts le long du mur est (cuisine) et du mur sud (facade)
    box("dress_fond_e", D1 - 0.02, D1, E0 + 0.60, E1 - 0.05, 0.0, 2.30, m["white_matt"])
    for k in range(6):
        y = E0 + 0.60 + k * ((E1 - 0.05) - (E0 + 0.60)) / 5
        box(f"dress_montant{k}", D1 - 0.60, D1, y - 0.01, y + 0.01, 0.0, 2.30, oak, bevel=0.002)
    box("dress_dessus_e", D1 - 0.60, D1, E0 + 0.60, E1 - 0.05, 2.28, 2.30, oak)
    cylinder_rail = principled("tringle", (0.05, 0.05, 0.05), 0.35, 0.9)
    box("dress_tringle_e", D1 - 0.32, D1 - 0.30, E0 + 0.62, E1 - 0.07, 1.86, 1.88, cylinder_rail)
    box("dress_tringle_e2", D1 - 0.32, D1 - 0.30, E0 + 0.62, E1 - 0.07, 0.98, 1.00, cylinder_rail)
    colors = [m["linen"], m["linen_sand"], m["linen_terra"], m["linen_sage"], m["sofa"]]
    y = E0 + 0.70
    k = 0
    while y < E1 - 0.12:
        mat = colors[R.randrange(len(colors))]
        h = R.choice([0.95, 0.85, 0.80, 1.05])
        box(f"dress_vetement{k}", D1 - 0.52, D1 - 0.10, y, y + 0.025, 1.87 - h, 1.86, mat, bevel=0.006)
        y += R.uniform(0.045, 0.07)
        k += 1
    box("dress_commode_s", D0 + 0.05, D1 - 0.62, E0, E0 + 0.50, 0.0, 0.85, oak, bevel=0.003)
    for k in range(3):
        box(f"dress_tiroir{k}", D0 + 0.07, D1 - 0.64, E0 + 0.50, E0 + 0.515, 0.08 + k * 0.255, 0.31 + k * 0.255, oak, bevel=0.002)
    for k, zz in enumerate((1.25, 1.65, 2.05)):
        box(f"dress_etagere_s{k}", D0 + 0.05, D1 - 0.62, E0, E0 + 0.40, zz, zz + 0.025, oak, bevel=0.002)
    box("dress_pouf", 2.95, 3.40, 2.20, 2.65, 0.0, 0.42, m["sofa"], bevel=0.05, seg=4)
    box("dress_tapis", 2.55, 3.55, 1.30, 3.60, 0.0, 0.012, m["rug"], bevel=0.003, seg=1)
    box("dress_miroir", D0, D0 + 0.02, 1.20, 1.80, 0.25, 2.05, m["mirror"], bevel=0.004)
    for (sx, sy) in [(3.25, 1.30), (3.25, 3.00)]:
        spot(f"spot_dress_{sx}_{sy}", sx, sy, m, on=True)


def bathroom(M, m):
    set_coll("salle_d_eau")
    X0, X1, Y0, Y1 = 15.12, 17.87, 3.47, 5.42
    tw = M["tile_wall"]
    t = 0.012
    # faience : zone douche (angle sud-ouest) + mur de la vasque
    box("faience_douche_o", X0, X0 + t, Y0, Y0 + 0.92, 0.004, 2.20, tw)
    box("faience_douche_s", X0, X0 + 1.02, Y0, Y0 + t, 0.004, 2.20, tw)
    box("faience_vasque", X0 + 1.02, X1, Y0, Y0 + t, 0.004, 1.20, tw)
    # receveur extra-plat
    box("receveur", X0 + t, X0 + 1.00, Y0 + t, Y0 + 0.90, 0.004, 0.03, principled("receveur_resine", (0.82, 0.81, 0.78), 0.55), bevel=0.003)
    box("caniveau", X0 + 0.12, X0 + 0.88, Y0 + 0.08, Y0 + 0.12, 0.03, 0.032, m["black"])
    # paroi vitree fixe (cote nord de la douche) + profil noir
    gl = bpy.data.materials.get("verre")
    box("paroi", X0 + t, X0 + 0.82, Y0 + 0.90, Y0 + 0.908, 0.03, 2.00, gl)
    box("paroi_profil", X0 + t, X0 + 0.82, Y0 + 0.898, Y0 + 0.91, 1.98, 2.00, m["black"])
    box("paroi_barre", X0 + 0.80, X0 + 0.82, Y0 + 0.90, Y0 + 0.908, 0.03, 2.00, m["black"])
    # colonne de douche noire
    cylinder("douche_colonne", X0 + 0.50, Y0 + 0.04, 0.90, 2.15, 0.012, m["black"])
    cylinder("douche_tete", X0 + 0.50, Y0 + 0.30, 2.13, 2.15, 0.15, m["black"])
    box("douche_bras", X0 + 0.49, X0 + 0.51, Y0 + 0.04, Y0 + 0.30, 2.14, 2.16, m["black"])
    box("douche_mitigeur", X0 + 0.44, X0 + 0.56, Y0 + 0.012, Y0 + 0.06, 1.05, 1.11, m["black"], bevel=0.008)
    # meuble vasque (mur sud, x 16.37 -> 17.87)
    vx0, vx1 = 16.35, 17.85
    box("vasque_meuble", vx0, vx1, Y0 + t, Y0 + 0.48, 0.42, 0.82, m["oak"], bevel=0.003)
    box("vasque_plan", vx0, vx1, Y0 + t, Y0 + 0.50, 0.82, 0.85, m["quartz"], bevel=0.002)
    for k, vx in enumerate((16.72, 17.48)):
        lathe(f"vasque{k}", [(0.0, 0.0), (0.16, 0.0), (0.20, 0.03), (0.21, 0.13), (0.195, 0.13), (0.185, 0.04), (0.0, 0.02)],
              vx, Y0 + 0.27, 0.85, m["ceramic"])
        tap(f"robinet_vasque{k}", vx, Y0 + 0.05, 0.85, 90, m["black"], reach=0.13, height=0.26)
    # miroir retroeclaire
    box("miroir", 16.45, 17.75, Y0 + t, Y0 + t + 0.02, 1.05, 1.85, m["mirror"], bevel=0.004)
    box("miroir_led", 16.47, 17.73, Y0 + t, Y0 + t + 0.01, 1.07, 1.83, m["led"])
    # WC suspendu contre le pignon droit (x = 17.87), y ~ 5.05
    wy = 5.05
    box("wc_bati", X1 - 0.20, X1, Y1 - 0.75, Y1, 0.0, 1.10, M["tile_wall"])
    box("wc_plaque", X1 - 0.205, X1 - 0.20, wy - 0.12, wy + 0.12, 0.92, 1.08, m["black"])
    bowl = box("wc_cuvette", X1 - 0.75, X1 - 0.20, wy - 0.18, wy + 0.18, 0.30, 0.42, m["ceramic"])
    add_subsurf(bowl, 3)
    seat = box("wc_abattant", X1 - 0.76, X1 - 0.21, wy - 0.185, wy + 0.185, 0.42, 0.45, m["ceramic"])
    add_subsurf(seat, 2)
    # seche-serviettes
    for k in range(9):
        box(f"radiateur_barre{k}", 16.25, 16.80, Y1 - 0.07, Y1 - 0.04, 0.35 + k * 0.13, 0.37 + k * 0.13, m["black"], bevel=0.008)
    for xx in (16.25, 16.78):
        box("radiateur_montant", xx, xx + 0.03, Y1 - 0.08, Y1 - 0.03, 0.30, 1.45, m["black"], bevel=0.008)
    cushion("serviette", 16.32, 16.72, Y1 - 0.10, Y1 - 0.015, 0.95, 1.40, m["linen_sand"], r=0.015)
    place("ceramic_vase_04", 17.70, Y0 + 0.30, 0, z=0.85, name="vase_sde")


# ------------------------------------------------------------------ ENTREE / COULOIR / WC
def entry(M, m, art):
    set_coll("entree")
    # banc + patere + miroir rond contre le mur du WC (x = 11.80)
    xw = 11.80
    box("banc", xw, xw + 0.38, 1.70, 2.80, 0.42, 0.46, m["oak"], bevel=0.004)
    for yy in (1.75, 2.75):
        box("banc_pied", xw + 0.02, xw + 0.36, yy - 0.02, yy + 0.02, 0, 0.42, m["oak"])
    box("patere", xw, xw + 0.03, 1.80, 2.70, 1.70, 1.80, m["oak"], bevel=0.003)
    for k in range(4):
        cylinder(f"patere_crochet{k}", xw + 0.03, 1.95 + k * 0.25, 1.73, 1.77, 0.012, m["black"], axis="X")
    place("wicker_basket_02", xw + 0.25, 2.45, 0, name="panier_entree")
    frame_art("tableau_entree", art["art3"], 13.71, 2.30, 1.55, 0.60, 0.80, "x", -1, M, m["black"])
    # WC (piece) : cuvette suspendue
    bowl = box("wc2_cuvette", 10.72 + 0.32, 10.72 + 0.68, 1.29 + 0.20, 1.29 + 0.75, 0.30, 0.42, m["ceramic"])
    add_subsurf(bowl, 3)


# ------------------------------------------------------------------ TERRASSE / JARDIN
def terrace(M, m):
    set_coll("terrasse_mobilier")
    # table de jardin 6 places (position du plan) + chaises pliantes Poly Haven
    tx, ty = 9.90, 10.40
    box("table_ext_plateau", tx - 0.90, tx + 0.90, ty - 0.45, ty + 0.45, 0.70, 0.735, m["teak"], bevel=0.005)
    for (lx, ly) in [(tx - 0.82, ty - 0.37), (tx + 0.82, ty - 0.37), (tx - 0.82, ty + 0.37), (tx + 0.82, ty + 0.37)]:
        box("table_ext_pied", lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, -0.03, 0.70, m["teak"], bevel=0.003)
    for k, (cx, cy, face) in enumerate([(tx - 0.45, ty - 0.70, 90), (tx + 0.45, ty - 0.70, 90), (tx - 0.45, ty + 0.70, 270),
                                         (tx + 0.45, ty + 0.70, 270), (tx - 1.18, ty, 0), (tx + 1.18, ty, 180)]):
        place("outdoor_table_chair_set_01", cx, cy, face, z=-0.03, name=f"chaise_ext{k}", variant="chair_01", rot_extra=165.5)
    # parasol (etoile du plan)
    cylinder("parasol_mat", tx, ty, -0.03, 2.35, 0.022, m["black"])
    lathe("parasol_toile", [(0.0, 0.42), (1.45, 0.0), (1.42, -0.02), (0.0, 0.40)], tx, ty, 2.05,
          principled("toile_parasol", (0.86, 0.82, 0.74), 0.9), seg=8)
    # salon bas (teck + coussins)
    box("canape_ext_base", 2.70, 4.70, 9.00, 9.80, -0.03, 0.30, m["teak"], bevel=0.01)
    cushion("canape_ext_assise", 2.74, 4.66, 9.05, 9.78, 0.30, 0.42, m["linen_sand"], r=0.04)
    cushion("canape_ext_dos", 2.74, 4.66, 9.00, 9.18, 0.30, 0.78, m["linen_sand"], r=0.05)
    box("table_basse_ext", 3.05, 4.35, 10.25, 10.95, -0.03, 0.36, m["teak"], bevel=0.01)
    # massifs + arbustes autour de la terrasse et au fond du jardin
    bushes = [(0.0, 13.2, "_a_"), (3.2, 13.6, "_c_"), (7.0, 13.5, "_e_"), (12.8, 13.4, "_b_"), (-1.3, 10.0, "_f_"),
              (19.4, 13.6, "_g_"), (-1.3, 4.5, "_d_"), (21.0, 6.0, "_a_")]
    for k, (sx, sy, v) in enumerate(bushes):
        place("searsia_lucida", sx, sy, R.uniform(0, 360), z=-0.12, name=f"arbuste{k}", variant=v)
    for k, (tx2, ty2) in enumerate([(-5.0, 19.0), (7.0, 22.0), (17.0, 20.0), (26.0, 15.0), (-8.0, 7.0)]):
        place("tree_small_02", tx2, ty2, R.uniform(0, 360), z=-0.12, name=f"arbre{k}", coll_names=["tree_small_02_LOD1"],
              scale=R.uniform(1.1, 1.5))


def build(M):
    load_models()
    m = mats()
    art = art_images()
    kitchen(M, m)
    living(M, m, art)
    bedrooms(M, m, art)
    bathroom(M, m)
    suite(M, m)
    entry(M, m, art)
    terrace(M, m)
    print(f"[interior] modeles disponibles : {len(MODELS)}")
