"""Blender 工具 · 参考「刀锈科技」明亮科普 3D 风。"""

from __future__ import annotations

import math
from typing import Sequence

import bpy
from mathutils import Euler, Vector


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def make_material(
    name: str,
    color: Sequence[float],
    *,
    metallic: float = 0.0,
    roughness: float = 0.45,
    emission: float = 0.0,
    alpha: float = 1.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if alpha < 1.0:
        mat.blend_method = "BLEND"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha
    if emission > 0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (color[0], color[1], color[2], 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def assign_material(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.data and hasattr(obj.data, "materials"):
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)


def add_box(name, size, loc, mat=None, bevel=0.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if mat:
        assign_material(obj, mat)
    return obj


def add_cylinder(name, radius, depth, loc, mat=None, rot=None, verts=32) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, vertices=verts)
    obj = bpy.context.active_object
    obj.name = name
    if rot:
        obj.rotation_euler = Euler(rot, "XYZ")
        bpy.ops.object.transform_apply(rotation=True)
    if mat:
        assign_material(obj, mat)
    return obj


def add_uv_sphere(name, radius, loc, mat=None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=24, ring_count=16)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        assign_material(obj, mat)
    return obj


def add_torus(name, major_r, minor_r, loc, mat=None, rot=None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_radius=major_r, minor_radius=minor_r, location=loc, major_segments=36, minor_segments=12)
    obj = bpy.context.active_object
    obj.name = name
    if rot:
        obj.rotation_euler = Euler(rot, "XYZ")
        bpy.ops.object.transform_apply(rotation=True)
    if mat:
        assign_material(obj, mat)
    return obj


def setup_bright_world() -> None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.82, 0.84, 0.87, 1.0)
    bg.inputs[1].default_value = 1.0


def setup_soft_lights() -> None:
    bpy.ops.object.light_add(type="SUN", location=(3, -4, 8))
    sun = bpy.context.active_object
    sun.data.energy = 2.8
    sun.rotation_euler = Euler((math.radians(55), 0, math.radians(25)), "XYZ")

    bpy.ops.object.light_add(type="AREA", location=(-3, -2, 4))
    fill = bpy.context.active_object
    fill.data.energy = 180
    fill.data.size = 6
    fill.data.color = (0.95, 0.97, 1.0)


def setup_camera(loc, target, lens=32.0) -> bpy.types.Object:
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.data.lens = lens
    direction = Vector(target) - Vector(loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def look_at(obj, target) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def keyframe_dolly(cam, start, end, target, f0, f1) -> None:
    cam.location = start
    look_at(cam, target)
    cam.keyframe_insert("location", frame=f0)
    cam.keyframe_insert("rotation_euler", frame=f0)
    cam.location = end
    look_at(cam, target)
    cam.keyframe_insert("location", frame=f1)
    cam.keyframe_insert("rotation_euler", frame=f1)


def keyframe_orbit(cam, center, radius, z, f0, f1, a0=-50, a1=20) -> None:
    cx, cy, cz = center
    for f, ang in ((f0, a0), (f1, a1)):
        rad = math.radians(ang)
        cam.location = (cx + radius * math.cos(rad), cy + radius * math.sin(rad), z)
        look_at(cam, (cx, cy, cz))
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)


def linear_keys(obj, prop="location") -> None:
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            if fc.data_path == prop:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"


def configure_render(*, width, height, fps, frames, engine, output_path) -> None:
    sc = bpy.context.scene
    sc.render.resolution_x = width
    sc.render.resolution_y = height
    sc.render.fps = fps
    sc.frame_start = 1
    sc.frame_end = frames
    sc.render.filepath = output_path
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.ffmpeg.audio_codec = "NONE"
    sc.render.use_motion_blur = False
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    eevee = getattr(sc, "eevee", None)
    if eevee:
        if hasattr(eevee, "taa_render_samples"):
            eevee.taa_render_samples = 48
        if hasattr(eevee, "use_bloom"):
            eevee.use_bloom = True
