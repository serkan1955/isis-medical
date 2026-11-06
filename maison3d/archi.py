"""Architecture : sols, murs avec ouvertures, plafond, menuiseries, portes, toiture, terrasse, jardin."""
import math

import bpy

import spec
from lib3d import (add_bevel, box, cylinder, glass, link, mesh_obj, pbr, principled, set_coll)

H = spec.CEILING
EXT_TOP = 2.72            # haut des murs exterieurs (dessus de dalle plafond)
WALL_BOTTOM = -0.30


# ------------------------------------------------------------------ outils geometriques
def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def wall_axis(w):
    _, x0, x1, y0, y1, _ = w
    return "x" if (x1 - x0) >= (y1 - y0) else "y"


def inward(w):
    """Pour un mur exterieur : (coordonnee de la face interieure, signe vers l'interieur)."""
    name, x0, x1, y0, y1, kind = w
    ax = wall_axis(w)
    if ax == "x":
        xm = (x0 + x1) / 2
        if point_in_poly(xm, y1 + 0.3, spec.FOOTPRINT):
            return y1, +1
        return y0, -1
    ym = (y0 + y1) / 2
    if point_in_poly(x1 + 0.3, ym, spec.FOOTPRINT):
        return x1, +1
    return x0, -1


# ------------------------------------------------------------------ materiaux d'archi
def materials():
    M = {}
    M["paint"] = pbr("peinture_blanche", "wall_paint", tile=(2.0, 2.0), tint=(0.93, 0.92, 0.90),
                     rough_add=0.35, rough_mul=0.4, normal=0.15, fallback=(0.86, 0.85, 0.82),
                     fallback_rough=0.85)
    M["ceiling"] = M["paint"]
    M["render"] = pbr("enduit_ext", "render_exterior", tile=(2.0, 2.0), tint=(0.93, 0.91, 0.87),
                      normal=0.6, fallback=(0.86, 0.84, 0.80), fallback_rough=0.9)
    M["oak"] = pbr("parquet_chene", "floor_oak", tile=(1.7, 1.7), rot=90, rough_mul=0.9,
                   normal=0.5, coat=0.15, val=1.12, fallback=(0.62, 0.48, 0.34), fallback_rough=0.45)
    M["tile"] = pbr("carrelage_sol", "tile_floor_bath", tile=(1.2, 1.2), normal=0.6,
                    fallback=(0.72, 0.71, 0.68), fallback_rough=0.4)
    M["tile_wall"] = pbr("faience_douche", "tile_wall_bath", tile=(0.6, 0.6), normal=0.6, coat=0.3,
                         fallback=(0.86, 0.84, 0.80), fallback_rough=0.2)
    M["deck"] = pbr("terrasse", "terrace_deck", tile=(2.0, 2.0), normal=0.8,
                    fallback=(0.55, 0.50, 0.45), fallback_rough=0.7)
    M["grass"] = pbr("pelouse", "grass", tile=(2.5, 2.5), normal=1.0, sat=1.05, val=0.78,
                     fallback=(0.20, 0.33, 0.12), fallback_rough=0.9)
    M["roof"] = pbr("tuiles", "roof_tiles", tile=(2.0, 2.0), normal=1.0,
                    fallback=(0.35, 0.33, 0.32), fallback_rough=0.7)
    M["alu"] = principled("alu_anthracite", (0.075, 0.08, 0.085), 0.38, 0.6)
    M["white_lacquer"] = principled("laque_blanche", (0.88, 0.88, 0.86), 0.32)
    M["skirting"] = principled("plinthe", (0.86, 0.86, 0.84), 0.4)
    M["steel"] = principled("inox_brosse", (0.62, 0.62, 0.62), 0.28, 1.0)
    M["glass"] = glass("verre")
    M["frosted"] = glass("verre_depoli", frosted=True)
    M["stone_sill"] = principled("appui_pierre", (0.70, 0.68, 0.64), 0.6)
    M["soffit"] = principled("sous_face", (0.85, 0.85, 0.83), 0.8)
    M["fascia"] = principled("bandeau", (0.12, 0.12, 0.13), 0.5)
    M["gutter"] = principled("gouttiere", (0.15, 0.15, 0.16), 0.35, 0.8)
    return M


# ------------------------------------------------------------------ sols / plafond
def floors(M):
    set_coll("sols")
    # dalle generale (parquet) sur tout l'interieur, y compris sous les portes
    inner = [(0.17, 0.17), (10.82, 0.17), (10.82, 1.12), (13.88, 1.12), (13.88, 0.17), (18.04, 0.17),
             (18.04, 12.39), (13.88, 12.39), (13.88, 8.09), (0.17, 8.09)]
    _prism("sol_parquet", inner, -0.20, 0.0, M["oak"])
    # carrelage dans les pieces d'eau (3 mm au-dessus = seuil)
    wet = {"SDE": (15.12, 17.87, 3.47, 5.42), "WC": (10.72, 11.72, 1.29, 3.27),
           "Cellier": (8.90, 10.65, 0.34, 3.27), "Piece3": (0.34, 2.24, 0.34, 4.02)}
    for k, (x0, x1, y0, y1) in wet.items():
        box("sol_carrelage_" + k, x0, x1, y0, y1, 0.0, 0.004, M["tile"])
    # plafond
    _prism("plafond", inner, H, EXT_TOP - 0.02, M["ceiling"])


def _prism(name, poly, z0, z1, mat):
    n = len(poly)
    verts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return mesh_obj(name, verts, faces, mat)


# ------------------------------------------------------------------ murs
def _assign_wall_faces(ob, w, M):
    """Mur exterieur : faces cote dehors en enduit, cote dedans en peinture."""
    name, x0, x1, y0, y1, kind = w
    me = ob.data
    me.materials.clear()
    me.materials.append(M["paint"])
    me.materials.append(M["render"])
    if kind != "ext":
        return
    face_in, sgn = inward(w)
    ax = wall_axis(w)
    for p in me.polygons:
        c = p.center
        coord = c.y if ax == "x" else c.x
        # profondeur depuis la face interieure (0 = interieur, 0.34 = exterieur)
        depth = (face_in - coord) * sgn
        nrm = p.normal.y if ax == "x" else p.normal.x
        if depth > 0.20 or (depth > 0.17 and abs(nrm) > 0.5 and nrm * sgn < 0):
            p.material_index = 1
        if c.z > H + 0.01 and depth < 0.2:
            p.material_index = 1


def walls(M):
    set_coll("murs")
    ops = {}
    for o in spec.OPENINGS:
        ops.setdefault(o[0], []).append(o)
    pieces = []
    for w in spec.WALLS:
        name, x0, x1, y0, y1, kind = w
        ax = wall_axis(w)
        zb = WALL_BOTTOM if kind == "ext" else -0.20
        zt = EXT_TOP if kind == "ext" else H
        a_start, a_end = (x0, x1) if ax == "x" else (y0, y1)
        cuts = sorted(ops.get(name, []), key=lambda o: o[2])
        segs = []
        cur = a_start
        for (_, oax, a0, a1, z0, z1, typ, info) in cuts:
            segs.append((cur, a0, zb, zt))
            if z0 > 0:
                segs.append((a0, a1, zb, z0))
            segs.append((a0, a1, z1, zt))
            cur = a1
        segs.append((cur, a_end, zb, zt))
        for i, (a0, a1, z0, z1) in enumerate(segs):
            if a1 - a0 < 1e-4 or z1 - z0 < 1e-4:
                continue
            if ax == "x":
                ob = box(f"{name}_{i}", a0, a1, y0, y1, z0, z1)
            else:
                ob = box(f"{name}_{i}", x0, x1, a0, a1, z0, z1)
            _assign_wall_faces(ob, w, M)
            pieces.append((w, ax, a0, a1, z0, z1))
    skirting(M, pieces)


def skirting(M, pieces):
    set_coll("plinthes")
    t, h = 0.012, 0.07
    for w, ax, a0, a1, z0, z1 in pieces:
        name, x0, x1, y0, y1, kind = w
        if z0 > 0.01:     # piece au-dessus d'une ouverture
            continue
        sides = []
        if kind == "ext":
            face, sgn = inward(w)
            sides.append((face, sgn))
        else:
            lo, hi = (y0, y1) if ax == "x" else (x0, x1)
            sides += [(lo, -1), (hi, +1)]
        for face, sgn in sides:
            if ax == "x":
                box(f"plinthe_{name}", a0, a1, face, face + sgn * t, 0.0, h, M["skirting"], bevel=0.002, seg=1)
            else:
                box(f"plinthe_{name}", face, face + sgn * t, a0, a1, 0.0, h, M["skirting"], bevel=0.002, seg=1)


# ------------------------------------------------------------------ menuiseries
def _frame_box(name, ax, a0, a1, d0, d1, z0, z1, mat, bevel=0.003):
    if ax == "x":
        return box(name, a0, a1, d0, d1, z0, z1, mat, bevel=bevel, seg=2)
    return box(name, d0, d1, a0, a1, z0, z1, mat, bevel=bevel, seg=2)


def _rect_frame(prefix, ax, a0, a1, d0, d1, z0, z1, pw, mat, sides=(1, 1, 1, 1)):
    """Cadre rectangulaire (gauche, droite, bas, haut) de profil pw."""
    l, r, b, t = sides
    if l:
        _frame_box(prefix + "_g", ax, a0, a0 + pw, d0, d1, z0, z1, mat)
    if r:
        _frame_box(prefix + "_d", ax, a1 - pw, a1, d0, d1, z0, z1, mat)
    if b:
        _frame_box(prefix + "_b", ax, a0 + pw * l, a1 - pw * r, d0, d1, z0, z0 + pw, mat)
    if t:
        _frame_box(prefix + "_h", ax, a0 + pw * l, a1 - pw * r, d0, d1, z1 - pw, z1, mat)


def _pane(name, ax, a0, a1, d, z0, z1, mat):
    if ax == "x":
        return mesh_obj(name, [(a0, d, z0), (a1, d, z0), (a1, d, z1), (a0, d, z1)], [(0, 1, 2, 3)], mat)
    return mesh_obj(name, [(d, a0, z0), (d, a1, z0), (d, a1, z1), (d, a0, z1)], [(0, 1, 2, 3)], mat)


def windows(M):
    set_coll("menuiseries")
    wall = {w[0]: w for w in spec.WALLS}
    for idx, (wname, ax, a0, a1, z0, z1, typ, info) in enumerate(spec.OPENINGS):
        w = wall[wname]
        if w[5] != "ext":
            continue
        face_in, sgn = inward(w)
        # plan du dormant : 0.14 en retrait de la face interieure (pose en applique interieure)
        dmid = face_in - sgn * 0.14
        p = f"men{idx:02d}"
        if typ in ("fenetre", "fenetre_depolie"):
            fw, depth = 0.055, 0.07
            d0, d1 = dmid - depth / 2, dmid + depth / 2
            _rect_frame(p + "_dormant", ax, a0, a1, d0, d1, z0, z1, fw, M["alu"])
            leaves = 2 if (a1 - a0) >= 0.9 else 1
            lw = (a1 - a0 - 2 * fw) / leaves
            gmat = M["frosted"] if typ == "fenetre_depolie" else M["glass"]
            for k in range(leaves):
                la0 = a0 + fw + k * lw
                la1 = la0 + lw
                sw = 0.06
                sd0, sd1 = dmid - 0.03 + sgn * 0.01, dmid + 0.03 + sgn * 0.01
                _rect_frame(f"{p}_ouvrant{k}", ax, la0, la1, sd0, sd1, z0 + fw, z1 - fw, sw, M["alu"])
                _pane(f"{p}_vitre{k}", ax, la0 + sw, la1 - sw, dmid + sgn * 0.01, z0 + fw + sw, z1 - fw - sw, gmat)
            # poignee cote interieur
            hz = (z0 + z1) / 2
            hx = a0 + fw + lw - 0.04 if leaves == 2 else a1 - fw - 0.05
            dd = dmid + sgn * 0.04
            if ax == "x":
                box(p + "_poignee", hx - 0.012, hx + 0.012, dd, dd + sgn * 0.05, hz - 0.08, hz + 0.02, M["alu"], bevel=0.004)
            else:
                box(p + "_poignee", dd, dd + sgn * 0.05, hx - 0.012, hx + 0.012, hz - 0.08, hz + 0.02, M["alu"], bevel=0.004)
            # tablette interieure + appui exterieur
            ti0, ti1 = face_in - sgn * 0.11, face_in + sgn * 0.025
            _frame_box(p + "_tablette", ax, a0 - 0.03, a1 + 0.03, min(ti0, ti1), max(ti0, ti1), z0 - 0.025, z0, M["white_lacquer"], 0.003)
            face_out = face_in - sgn * spec.EXT_T
            to0, to1 = dmid - sgn * 0.035, face_out - sgn * 0.04
            _frame_box(p + "_appui", ax, a0 - 0.03, a1 + 0.03, min(to0, to1), max(to0, to1), z0 - 0.05, z0 - 0.01, M["stone_sill"], 0.004)
        elif typ == "baie":
            fw, depth = 0.05, 0.10
            d0, d1 = dmid - depth / 2, dmid + depth / 2
            _rect_frame(p + "_dormant", ax, a0, a1, d0, d1, 0.0, z1, fw, M["alu"])
            W = a1 - a0 - 2 * fw
            ov = 0.04
            lw = W / 2 + ov / 2
            sw = 0.055
            for k in range(2):
                la0 = a0 + fw + (0 if k == 0 else W - lw)
                la1 = la0 + lw
                off = (-1 if k == 0 else 1) * 0.022
                sd = dmid + off
                _rect_frame(f"{p}_vantail{k}", ax, la0, la1, sd - 0.018, sd + 0.018, fw, z1 - fw, sw, M["alu"])
                _pane(f"{p}_vitre{k}", ax, la0 + sw, la1 - sw, sd, fw + sw, z1 - fw - sw, M["glass"])
                # poignee
                hx = la1 - 0.035 if k == 0 else la0 + 0.035
                dd = dmid + sgn * 0.05
                if ax == "x":
                    box(f"{p}_poignee{k}", hx - 0.01, hx + 0.01, dd, dd + sgn * 0.03, 0.95, 1.20, M["alu"], bevel=0.004)
                else:
                    box(f"{p}_poignee{k}", dd, dd + sgn * 0.03, hx - 0.01, hx + 0.01, 0.95, 1.20, M["alu"], bevel=0.004)
            # seuil alu
            _frame_box(p + "_seuil", ax, a0, a1, min(face_in, dmid) - 0.06, max(face_in, dmid) + 0.06, -0.01, 0.012, M["alu"], 0.002)
        elif typ == "porte_entree":
            fw, depth = 0.06, 0.09
            d0, d1 = dmid - depth / 2, dmid + depth / 2
            _rect_frame(p + "_dormant", ax, a0, a1, d0, d1, 0.0, z1, fw, M["alu"], sides=(1, 1, 0, 1))
            _frame_box(p + "_vantail", ax, a0 + fw, a1 - fw, dmid - 0.03, dmid + 0.03, 0.01, z1 - fw, M["alu"], 0.004)
            # oculus vertical vitre
            g0 = a0 + fw + 0.12
            _pane(p + "_oculus", ax, g0, g0 + 0.12, dmid + sgn * 0.031, 0.35, z1 - fw - 0.25, M["frosted"])
            # barre de tirage
            bx = a1 - fw - 0.10
            for s in (1, -1):
                dd = dmid + s * 0.03
                if ax == "x":
                    box(f"{p}_barre{s}", bx - 0.012, bx + 0.012, dd, dd + s * 0.06, 0.55, 1.75, M["steel"], bevel=0.006)
                else:
                    box(f"{p}_barre{s}", dd, dd + s * 0.06, bx - 0.012, bx + 0.012, 0.55, 1.75, M["steel"], bevel=0.006)


# ------------------------------------------------------------------ portes interieures
DOOR_OPEN = {  # angle d'ouverture (deg) et cote charniere ('lo' / 'hi'), sens (+1 / -1 cote du mur)
    "Chambre 14.82": (88, "lo", -1),
    "Chambre -> Piece 3": (0, "lo", -1),
    "Cellier": (0, "lo", +1),
    "WC": (0, "hi", -1),
    "SDE": (80, "hi", +1),
    "Chambre 10.62": (80, "lo", +1),
    "Chambre 11.51": (85, "lo", +1),
    "Chambre 11.69": (85, "hi", -1),
}


def interior_doors(M):
    set_coll("portes")
    wall = {w[0]: w for w in spec.WALLS}
    for idx, (wname, ax, a0, a1, z0, z1, typ, info) in enumerate(spec.OPENINGS):
        w = wall[wname]
        if w[5] != "int" or typ not in ("porte", "passage", "coulissante", "coulissante_ouverte"):
            continue
        name, x0, x1, y0, y1, _ = w
        lo, hi = (y0, y1) if ax == "x" else (x0, x1)
        p = f"porte{idx:02d}"
        # chambranles (huisserie + moulures des 2 cotes)
        cw, ct = 0.06, 0.012
        for side, s in ((lo, -1), (hi, +1)):
            dd0, dd1 = side, side + s * ct
            _frame_box(p + f"_ch{s}_g", ax, a0 - cw, a0, min(dd0, dd1), max(dd0, dd1), 0, z1 + cw, M["white_lacquer"], 0.002)
            _frame_box(p + f"_ch{s}_d", ax, a1, a1 + cw, min(dd0, dd1), max(dd0, dd1), 0, z1 + cw, M["white_lacquer"], 0.002)
            _frame_box(p + f"_ch{s}_h", ax, a0 + 0.0005, a1 - 0.0005, min(dd0, dd1), max(dd0, dd1) - 0.001 * s, z1, z1 + cw, M["white_lacquer"], 0.002)
        # ebrasement (fourrure) dans l'epaisseur
        _frame_box(p + "_fg", ax, a0, a0 + 0.015, lo, hi, 0, z1, M["white_lacquer"], 0.0)
        _frame_box(p + "_fd", ax, a1 - 0.015, a1, lo, hi, 0, z1, M["white_lacquer"], 0.0)
        _frame_box(p + "_fh", ax, a0, a1, lo, hi, z1 - 0.015, z1, M["white_lacquer"], 0.0)
        if typ in ("passage", "coulissante_ouverte"):
            continue
        if typ == "coulissante":   # porte a galandage, representee fermee dans l'epaisseur du mur
            mid = (lo + hi) / 2
            _frame_box(p + "_coul", ax, a0 + 0.015, a1 - 0.015, mid - 0.02, mid + 0.02, 0.008, z1 - 0.015, M["white_lacquer"], 0.002)
            for s_ in (-1, 1):
                cx_ = a1 - 0.08
                _frame_box(p + f"_cuvette{s_}", ax, cx_ - 0.015, cx_ + 0.015, mid + s_ * 0.02, mid + s_ * 0.022, 0.95, 1.10, M["steel"], 0.0)
            continue
        ang, hinge, dirn = DOOR_OPEN.get(info, (0, "lo", 1))
        leaf_w = (a1 - a0) - 0.03
        th = 0.04
        mid = (lo + hi) / 2
        leaf = box(p + "_vantail", 0, leaf_w, -th / 2, th / 2, 0.008, z1 - 0.012, M["white_lacquer"], bevel=0.003)
        # poignee (rosace + bequille) des deux cotes
        hx = leaf_w - 0.065
        for s in (1, -1):
            r = cylinder(p + f"_rosace{s}", hx, s * (th / 2 + 0.004), 0, 0.008, 0.026, M["steel"], seg=24, axis="Y")
            r.location = (hx, s * (th / 2 + 0.004), 1.02)
            r.parent = leaf
            b = box(p + f"_bequille{s}", hx - 0.12, hx + 0.008, s * (th / 2 + 0.008), s * (th / 2 + 0.05), 1.012, 1.028, M["steel"], bevel=0.006)
            b.parent = leaf
        # positionnement : charniere en a0 (lo) ou a1 (hi)
        if hinge == "lo":
            pivot_a, base_rot = a0 + 0.015, 0.0
        else:
            pivot_a, base_rot = a1 - 0.015, math.pi
        s_lo = 1 if ax == "x" else -1
        swing = math.radians(ang) * dirn * (s_lo if hinge == "lo" else -s_lo)
        if ax == "x":
            leaf.location = (pivot_a, mid, 0)
            leaf.rotation_euler = (0, 0, base_rot + swing)
        else:
            leaf.location = (mid, pivot_a, 0)
            leaf.rotation_euler = (0, 0, base_rot + math.pi / 2 + swing)


# ------------------------------------------------------------------ toiture / exterieur
def _hip_roof(name, x0, x1, y0, y1, z, pitch_deg, mat, ridge_axis=None):
    w, d = x1 - x0, y1 - y0
    ax = ridge_axis or ("x" if w >= d else "y")
    t = math.tan(math.radians(pitch_deg))
    if ax == "x":
        hh = d / 2 * t
        r0, r1 = x0 + d / 2, x1 - d / 2
        ym = (y0 + y1) / 2
        v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), (r0, ym, z + hh), (r1, ym, z + hh)]
        f = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4), (3, 2, 1, 0)]
    else:
        hh = w / 2 * t
        r0, r1 = y0 + w / 2, y1 - w / 2
        xm = (x0 + x1) / 2
        v = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), (xm, r0, z + hh), (xm, r1, z + hh)]
        f = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5), (3, 2, 1, 0)]
    ob = mesh_obj(name, v, f, mat)
    sol = ob.modifiers.new("ep", "SOLIDIFY")
    sol.thickness = 0.06
    sol.offset = 1
    return ob


def roof(M):
    set_coll("toiture")
    ov = 0.45
    z = EXT_TOP
    # aile droite (faitage selon y) et corps principal (faitage selon x, croupe a gauche)
    _hip_roof("toit_aile", 13.71 - ov, 18.21 + ov, -ov, 12.56 + ov, z, 22, M["roof"], "y")
    _hip_roof("toit_corps", -ov, 16.0, -ov, 8.26 + ov, z, 22, M["roof"], "x")
    # bandeaux (rives) et sous-faces
    for (x0, x1, y0, y1) in [(-ov, 13.71 - ov, -ov, 8.26 + ov), (13.71 - ov, 18.21 + ov, -ov, 12.56 + ov)]:
        box("sous_face", x0, x1, y0, y1, z - 0.02, z, M["soffit"])
    for (x0, x1, y0, y1) in [(-ov, 13.71 - ov, -ov - 0.02, -ov), (-ov, 13.71 - ov, 8.26 + ov, 8.26 + ov + 0.02),
                             (-ov - 0.02, -ov, -ov, 8.26 + ov),
                             (13.71 - ov, 18.21 + ov, -ov - 0.02, -ov), (13.71 - ov, 18.21 + ov, 12.56 + ov, 12.56 + ov + 0.02),
                             (18.21 + ov, 18.21 + ov + 0.02, -ov, 12.56 + ov), (13.71 - ov - 0.02, 13.71 - ov, 8.26 + ov, 12.56 + ov)]:
        box("rive", x0, x1, y0, y1, z - 0.02, z + 0.16, M["fascia"])


def exterior(M):
    set_coll("exterieur")
    # pelouse
    box("pelouse", -60, 80, -50, 70, -0.40, -0.12, M["grass"])
    # terrasse (dalle 13.09 x 4.20)
    x0, x1, y0, y1 = spec.TERRACE
    box("terrasse", x0, x1, y0, y1, -0.30, -0.03, M["deck"], bevel=0.004, seg=1)
    # parvis du porche
    box("parvis", 11.0, 13.71, -1.2, 0.95, -0.30, -0.04, M["deck"], bevel=0.004, seg=1)
