"""Reglages de rendu, eclairage (HDRI / ciel), portails, cameras."""
import json
import math
import os

import bpy
from mathutils import Vector

import spec
from lib3d import ASSETS, set_coll, tex_manifest

# Orientation (relevee sur la rose des vents du plan) :
#   le haut du plan (+y, cote terrasse) regarde l'azimut 252 deg (Ouest-Sud-Ouest).
PLAN_UP_AZIMUTH = 252.0


def azimuth_to_plan_angle(az):
    return math.radians(90.0 + (PLAN_UP_AZIMUTH - az))


def render_settings(samples=256, res=(1920, 1280), threshold=0.015, exposure=0.0, look="AgX - Medium High Contrast"):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = threshold
    cy.adaptive_min_samples = 32
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    try:
        cy.denoising_prefilter = "ACCURATE"
        cy.denoising_quality = "HIGH"
    except Exception:
        pass
    cy.max_bounces = 10
    cy.diffuse_bounces = 5
    cy.glossy_bounces = 4
    cy.transmission_bounces = 8
    cy.transparent_max_bounces = 24
    cy.volume_bounces = 0
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.sample_clamp_indirect = 8.0
    cy.blur_glossy = 1.0
    cy.use_light_tree = True
    try:
        cy.texture_limit_render = "2048"
    except Exception:
        pass
    try:
        cy.use_guiding = True
        cy.use_surface_guiding = True
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.threads_mode = "AUTO"
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = look
    sc.view_settings.exposure = exposure
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.unit_settings.system = "METRIC"


def world(sun_az=238.0, sun_el=28.0, strength=1.0):
    """Eclairage : HDRI Poly Haven tourne pour placer son soleil a l'azimut voulu.
    Repli : ciel physique + lampe soleil."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("monde")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(bg.outputs[0], out.inputs[0])
    hd = tex_manifest().get("hdri")
    target = azimuth_to_plan_angle(sun_az)
    if hd and os.path.exists(hd.get("path", "")):
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(hd["path"], check_existing=True)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        u = hd.get("sun_uv", [0.5, 0.5])[0]
        phi = 2 * math.pi * (0.5 - u)          # longitude Blender du soleil dans l'image
        # verifie dans Blender 5.2 : le soleil apparait a l'azimut (phi - theta)
        mp.inputs["Rotation"].default_value = (0, 0, phi - target)
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs[0], env.inputs["Vector"])
        nt.links.new(env.outputs[0], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = strength
        el = hd.get("sun_elevation_deg", sun_el)
        return {"mode": "hdri", "sun_plan_angle": target, "sun_el": el}
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = False
    sky.sun_elevation = math.radians(sun_el)
    sky.sun_rotation = target - math.pi / 2
    nt.links.new(sky.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35 * strength
    ld = bpy.data.lights.new("soleil", "SUN")
    ld.energy = 4.0 * strength
    ld.angle = math.radians(0.6)
    ob = bpy.data.objects.new("soleil", ld)
    sc.collection.objects.link(ob)
    d = Vector((math.cos(target) * math.cos(math.radians(sun_el)),
                math.sin(target) * math.cos(math.radians(sun_el)),
                math.sin(math.radians(sun_el))))
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return {"mode": "sky", "sun_plan_angle": target, "sun_el": sun_el}


def portals():
    """Portails de lumiere sur chaque baie / fenetre (accelere fortement l'eclairage interieur)."""
    from archi import inward
    set_coll("portails")
    wall = {w[0]: w for w in spec.WALLS}
    for i, (wname, ax, a0, a1, z0, z1, typ, info) in enumerate(spec.OPENINGS):
        w = wall[wname]
        if w[5] != "ext" or typ == "porte_entree":
            continue
        face_in, sgn = inward(w)
        ld = bpy.data.lights.new(f"portail{i}", "AREA")
        ld.shape = "RECTANGLE"
        ld.size = a1 - a0
        ld.size_y = z1 - z0
        ld.cycles.is_portal = True
        ob = bpy.data.objects.new(f"portail{i}", ld)
        bpy.context.scene.collection.objects.link(ob)
        a = (a0 + a1) / 2
        zc = (z0 + z1) / 2
        d = face_in - sgn * 0.02
        # une lampe "zone" emet selon son -Z local : on l'oriente vers l'interieur
        if ax == "x":
            ob.location = (a, d, zc)
            ob.rotation_euler = (math.radians(90 if sgn > 0 else -90), 0, 0)
        else:
            ld.size, ld.size_y = z1 - z0, a1 - a0
            ob.location = (d, a, zc)
            ob.rotation_euler = (0, math.radians(-90 if sgn > 0 else 90), 0)


def camera(name, x, y, z, yaw_deg, lens=20.0, shift_y=0.0, shift_x=0.0, pitch_deg=0.0, clip=0.05):
    """yaw_deg : direction de visee dans le plan (0 = +x / droite du plan, 90 = +y / vers la terrasse)."""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.shift_y = shift_y
    cd.shift_x = shift_x
    cd.clip_start = clip
    cd.clip_end = 500
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (x, y, z)
    ob.rotation_euler = (math.radians(90 + pitch_deg), 0, math.radians(yaw_deg - 90))
    return ob
