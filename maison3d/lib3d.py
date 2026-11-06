"""Petites briques Blender (bpy) : maillages, materiaux PBR, collections."""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ASSETS = os.environ.get("MAISON_ASSETS", "")
_TEX = None


def tex_manifest():
    global _TEX
    if _TEX is None:
        p = os.path.join(ASSETS, "textures.json")
        _TEX = json.load(open(p)) if ASSETS and os.path.exists(p) else {}
    return _TEX


# ------------------------------------------------------------------ collections
def coll(name, parent=None):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


CUR = {"coll": None}


def set_coll(name):
    CUR["coll"] = coll(name)
    return CUR["coll"]


def link(ob, c=None):
    (c or CUR["coll"] or bpy.context.scene.collection).objects.link(ob)
    return ob


# ------------------------------------------------------------------ maillages
def mesh_obj(name, verts, faces, mat=None, c=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        mats = mat if isinstance(mat, (list, tuple)) else [mat]
        for m in mats:
            me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return link(ob, c)


def box(name, x0, x1, y0, y1, z0, z1, mat=None, bevel=0.0, seg=3, c=None, smooth=False):
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    if z0 > z1:
        z0, z1 = z1, z0
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, mat, c, smooth)
    if bevel > 0:
        add_bevel(ob, bevel, seg)
    return ob


def add_bevel(ob, width, seg=3, harden=True):
    m = ob.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = seg
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(40)
    m.harden_normals = harden
    if harden:
        for p in ob.data.polygons:
            p.use_smooth = True
    return m


def add_subsurf(ob, levels=2):
    m = ob.modifiers.new("subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    for p in ob.data.polygons:
        p.use_smooth = True
    return m


def cylinder(name, cx, cy, z0, z1, r, mat=None, seg=32, c=None, axis="Z", bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r, depth=(z1 - z0))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    if axis == "Z":
        ob.location = (cx, cy, (z0 + z1) / 2)
    elif axis == "X":
        ob.rotation_euler = (0, math.pi / 2, 0)
        ob.location = ((z0 + z1) / 2, cx, cy)
    elif axis == "Y":
        ob.rotation_euler = (math.pi / 2, 0, 0)
        ob.location = (cx, (z0 + z1) / 2, cy)
    if mat:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    link(ob, c)
    if bevel:
        add_bevel(ob, bevel, 2)
    return ob


def lathe(name, profile, cx, cy, z, mat=None, seg=48, c=None):
    """profil [(r, z)] tourne autour de Z."""
    verts, faces = [], []
    n = len(profile)
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for r, zz in profile:
            verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z + zz))
    for i in range(seg):
        j = (i + 1) % seg
        for k in range(n - 1):
            faces.append((i * n + k, j * n + k, j * n + k + 1, i * n + k + 1))
    ob = mesh_obj(name, verts, faces, mat, c, smooth=True)
    return ob


# ------------------------------------------------------------------ materiaux
def _nodes(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return nt, out


def principled(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, **kw):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    nt, out = _nodes(mat)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    for k, v in kw.items():
        b.inputs[k].default_value = v
    nt.links.new(b.outputs[0], out.inputs[0])
    mat.diffuse_color = (*color, 1)
    return mat


def _img(path, noncolor=False):
    im = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def pbr(name, key, tile=(1.0, 1.0), tint=None, rough_add=0.0, rough_mul=1.0, normal=1.0,
        rot=0.0, fallback=(0.8, 0.8, 0.8), fallback_rough=0.5, coords="Object", blend=0.2,
        coat=0.0, sheen=0.0, bump_disp=0.0, sat=1.0, val=1.0):
    """Materiau PBR texture en projection boite (coordonnees objet = monde si l'objet est a l'origine)."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    t = tex_manifest().get(key)
    if not t:
        return principled(name, fallback, fallback_rough)
    maps = t.get("maps", {})
    mat = bpy.data.materials.new(name)
    nt, out = _nodes(mat)
    L = nt.links
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L.new(b.outputs[0], out.inputs[0])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tile[0], 1.0 / tile[1], 1.0 / tile[0])
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot))
    L.new(tc.outputs["UV" if coords == "UV" else "Object"], mp.inputs["Vector"])

    def tex(path, noncolor):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = _img(path, noncolor)
        if coords != "UV":
            n.projection = "BOX"
            n.projection_blend = blend
        L.new(mp.outputs[0], n.inputs["Vector"])
        return n

    if maps.get("color"):
        c = tex(maps["color"], False)
        col = c.outputs["Color"]
        if sat != 1.0 or val != 1.0:
            hsv = nt.nodes.new("ShaderNodeHueSaturation")
            hsv.inputs["Saturation"].default_value = sat
            hsv.inputs["Value"].default_value = val
            L.new(col, hsv.inputs["Color"])
            col = hsv.outputs[0]
        if tint:
            mx = nt.nodes.new("ShaderNodeMix")
            mx.data_type = "RGBA"
            mx.blend_type = "MULTIPLY"
            mx.inputs["Factor"].default_value = 1.0
            L.new(col, mx.inputs[6])
            mx.inputs[7].default_value = (*tint, 1)
            col = mx.outputs[2]
        L.new(col, b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = (*fallback, 1)
    if maps.get("roughness"):
        r = tex(maps["roughness"], True)
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = "MULTIPLY_ADD"
        m.inputs[1].default_value = rough_mul
        m.inputs[2].default_value = rough_add
        m.use_clamp = True
        L.new(r.outputs["Color"], m.inputs[0])
        L.new(m.outputs[0], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = fallback_rough
    nmap = maps.get("normal_gl") or maps.get("normal")
    if nmap and normal > 0:
        nn = tex(nmap, True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        L.new(nn.outputs["Color"], nm.inputs["Color"])
        L.new(nm.outputs[0], b.inputs["Normal"])
    if maps.get("metalness"):
        mm = tex(maps["metalness"], True)
        L.new(mm.outputs["Color"], b.inputs["Metallic"])
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.08
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    mat.diffuse_color = (*fallback, 1)
    return mat


def glass(name="verre", tint=(0.93, 0.96, 0.95), frosted=False):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    nt, out = _nodes(mat)
    L = nt.links
    if frosted:
        tp = nt.nodes.new("ShaderNodeBsdfTransparent")
        tp.inputs["Color"].default_value = (0.92, 0.92, 0.92, 1)
        tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
        tr.inputs["Color"].default_value = (0.95, 0.95, 0.95, 1)
        gl = nt.nodes.new("ShaderNodeBsdfGlossy")
        gl.inputs["Roughness"].default_value = 0.15
        fr = nt.nodes.new("ShaderNodeFresnel")
        fr.inputs["IOR"].default_value = 1.52
        m1 = nt.nodes.new("ShaderNodeMixShader")
        m1.inputs[0].default_value = 0.55
        L.new(tp.outputs[0], m1.inputs[1])
        L.new(tr.outputs[0], m1.inputs[2])
        m2 = nt.nodes.new("ShaderNodeMixShader")
        L.new(fr.outputs[0], m2.inputs[0])
        L.new(m1.outputs[0], m2.inputs[1])
        L.new(gl.outputs[0], m2.inputs[2])
        L.new(m2.outputs[0], out.inputs[0])
        return mat
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    tp.inputs["Color"].default_value = (*tint, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.0
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.52
    # face arriere d'un vitrage epais : pas de reflexion totale (sinon le verre parait noir en vue rasante)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(geo.outputs["Backfacing"], inv.inputs[1])
    fw = nt.nodes.new("ShaderNodeMath")
    fw.operation = "MULTIPLY"
    L.new(fr.outputs[0], fw.inputs[0])
    L.new(inv.outputs[0], fw.inputs[1])
    mx = nt.nodes.new("ShaderNodeMixShader")
    L.new(fw.outputs[0], mx.inputs[0])
    L.new(tp.outputs[0], mx.inputs[1])
    L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0])
    return mat


def emission(name, color=(1, 1, 1), strength=5.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    nt, out = _nodes(mat)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return mat


def image_material(name, path, rough=0.6):
    """Toile / tableau : image plaquee en UV."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    nt, out = _nodes(mat)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = _img(path)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(b.outputs[0], out.inputs[0])
    return mat


def uv_plane(name, p0, ex, ey, mat=None, c=None):
    """Plan rectangulaire avec UV 0-1 : p0 coin, ex/ey vecteurs bords."""
    p0, ex, ey = Vector(p0), Vector(ex), Vector(ey)
    v = [p0, p0 + ex, p0 + ex + ey, p0 + ey]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(x) for x in v], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = co
    ob = bpy.data.objects.new(name, me)
    if mat:
        me.materials.append(mat)
    return link(ob, c)


# ------------------------------------------------------------------ import de modeles (instancies)
_LIB = {}


def lib_collection(entry, key, coll_names=None, keep=None):
    """Charge une fois un modele Poly Haven (.blend) dans une collection bibliotheque
    non liee a la scene ; renvoie (collection, dims). keep(nom_objet) filtre les variantes."""
    if key in _LIB:
        return _LIB[key]
    wanted = coll_names or entry.get("append", {}).get("names") or []
    with bpy.data.libraries.load(entry["blend"], link=False) as (src, dst):
        if wanted:
            dst.collections = [n for n in src.collections if n in wanted]
        else:
            dst.objects = list(src.objects)
    objs = []
    if wanted:
        for col in dst.collections:
            objs += list(col.all_objects)
    else:
        objs = [o for o in dst.objects if o is not None]
    lib = bpy.data.collections.new("LIB_" + key)
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        if ob.type == "MESH" and keep is not None and not keep(ob.name):
            continue
        if ob.name not in lib.objects:
            lib.objects.link(ob)
        if ob.type == "MESH":
            for corner in ob.bound_box:
                w = ob.matrix_world @ Vector(corner)
                mn = Vector(map(min, mn, w))
                mx = Vector(map(max, mx, w))
    lib.instance_offset = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)
    _LIB[key] = (lib, mx - mn)
    return _LIB[key]


def instance(lib, name, location, rot_z=0.0, scale=1.0, c=None):
    ob = bpy.data.objects.new(name, None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = lib
    ob.location = location
    ob.rotation_euler = (0, 0, rot_z)
    ob.scale = (scale, scale, scale)
    return link(ob, c)
