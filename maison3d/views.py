"""Points de vue (hauteur d'oeil 1.55 m, perspective 2 points : verticales droites)."""
import math

import bpy

import scene

EYE = 1.55

# nom : (x, y, z, direction de visee en deg dans le plan, focale mm, decalage vertical, options)
VIEWS = {
    "plan_dessus":   dict(ortho=True),
    "maquette_3d":   dict(iso=True),
}

VIEWS.update({
    # Sejour : depuis l'entree vers la salle a manger et les baies
    "01_sejour_vers_terrasse": dict(cam=(13.35, 3.75, EYE, 128, 16, -0.06), exposure=0.9),
    # Sejour : depuis l'angle des baies (cote canape) vers la cuisine
    "02_sejour_vers_cuisine":  dict(cam=(13.62, 7.05, EYE, 202, 16, -0.06), exposure=1.0),
    # Cuisine : depuis la salle a manger vers l'ilot et la fenetre
    "03_cuisine":              dict(cam=(5.10, 5.30, EYE, -60, 18, -0.06), exposure=2.2),
    # Salle a manger : depuis la cuisine vers la table et les baies
    "04_salle_a_manger":       dict(cam=(8.75, 3.70, EYE, 128, 17, -0.06), exposure=1.0),
    # Chambre parentale 14.82
    "05_chambre_parentale":    dict(cam=(3.92, 4.52, EYE, 140, 16, -0.05), exposure=1.0),
    # Chambre 10.62 (aile)
    "06_chambre_10m62":        dict(cam=(15.32, 6.45, EYE, 45, 15, -0.05), exposure=2.2),
    # Salle d'eau
    "07_salle_d_eau":          dict(cam=(17.05, 5.28, EYE, 243, 14, -0.04), exposure=2.0),
    # Entree
    "08_entree":               dict(cam=(12.95, 1.45, EYE, 95, 16, -0.05), exposure=1.8),
})

HIDE_FOR_TOP = ["toiture", "plafond"]


def make_cameras():
    cams = {}
    for name, o in VIEWS.items():
        if o.get("ortho"):
            cd = bpy.data.cameras.new(name)
            cd.type = "ORTHO"
            cd.ortho_scale = 21.0
            ob = bpy.data.objects.new(name, cd)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = (9.1, 6.0, 30)
            ob.rotation_euler = (0, 0, 0)
            cams[name] = (ob, {"hide": HIDE_FOR_TOP, "res": (1800, 1300), "exposure": -0.3, "top": True})
        elif o.get("iso"):
            cd = bpy.data.cameras.new(name)
            cd.lens = 42
            cd.clip_end = 500
            ob = bpy.data.objects.new(name, cd)
            bpy.context.scene.collection.objects.link(ob)
            from mathutils import Vector
            ob.location = (-7.5, 27.0, 19.0)
            d = Vector((9.6, 5.6, -1.0)) - ob.location
            ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
            cams[name] = (ob, {"hide": HIDE_FOR_TOP, "res": (1920, 1280), "exposure": -0.3, "top": True})
        else:
            x, y, z, yaw, lens, sy = o["cam"]
            ob = scene.camera(name, x, y, z, yaw, lens=lens, shift_y=sy)
            cams[name] = (ob, {"exposure": o.get("exposure", 0.6)})
    return cams


def _set_hidden(names, hidden):
    for n in names:
        if n in bpy.data.collections:
            c = bpy.data.collections[n]
            c.hide_render = hidden
        elif n in bpy.data.objects:
            bpy.data.objects[n].hide_render = hidden


def prepare(name, opts):
    if opts.get("hide"):
        _set_hidden(opts["hide"], True)


def restore(name, opts):
    if opts.get("hide"):
        _set_hidden(opts["hide"], False)
