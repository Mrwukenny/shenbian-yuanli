"""模仿参考视频（刀锈科技风）：客厅 + 原理图 + 冷凝器/压缩机剖切。"""

from __future__ import annotations

import math
from typing import Callable

import bpy

from common import (
    add_box,
    add_cylinder,
    add_torus,
    add_uv_sphere,
    assign_material,
    clear_scene,
    configure_render,
    keyframe_dolly,
    keyframe_orbit,
    linear_keys,
    make_material,
    setup_bright_world,
    setup_camera,
    setup_soft_lights,
)


def _mats() -> dict:
    return {
        "wall": make_material("Wall", (0.72, 0.74, 0.76), roughness=0.9),
        "floor": make_material("Floor", (0.55, 0.53, 0.5), roughness=0.8),
        "sofa": make_material("Sofa", (0.42, 0.44, 0.46), roughness=0.75),
        "pillow": make_material("Pillow", (0.92, 0.93, 0.95), roughness=0.6),
        "skin": make_material("Skin", (0.92, 0.78, 0.65), roughness=0.55),
        "shirt": make_material("Shirt", (0.55, 0.62, 0.72), roughness=0.65),
        "ac_white": make_material("ACWhite", (0.96, 0.97, 0.98), roughness=0.25),
        "copper": make_material("Copper", (0.85, 0.48, 0.18), metallic=0.85, roughness=0.18),
        "copper_hot": make_material("CopperHot", (0.95, 0.28, 0.08), metallic=0.7, roughness=0.15, emission=0.35),
        "copper_warm": make_material("CopperWarm", (0.98, 0.62, 0.12), metallic=0.7, roughness=0.15, emission=0.25),
        "copper_cool": make_material("CopperCool", (0.95, 0.78, 0.2), metallic=0.65, roughness=0.15, emission=0.15),
        "metal_grey": make_material("MetalGrey", (0.55, 0.58, 0.62), metallic=0.7, roughness=0.3),
        "compressor_body": make_material("CompBody", (0.08, 0.09, 0.1), roughness=0.4),
        "coil_blue": make_material("CoilBlue", (0.15, 0.55, 0.95), metallic=0.4, emission=0.45),
        "coil_red": make_material("CoilRed", (0.95, 0.2, 0.08), metallic=0.4, emission=0.5),
        "cold_ray": make_material("ColdRay", (0.55, 0.82, 1.0), emission=1.2, alpha=0.35),
        "fan_blade": make_material("FanBlade", (0.75, 0.78, 0.82), metallic=0.5, alpha=0.55),
        "frame": make_material("Frame", (0.62, 0.64, 0.66), metallic=0.6, roughness=0.35),
        "gas_hot": make_material("GasHot", (1.0, 0.35, 0.1), emission=2.5),
        "gas_cold": make_material("GasCold", (0.3, 0.75, 1.0), emission=2.0),
    }


def _living_room(mats: dict) -> dict:
    """参考：灰墙 + 沙发 + 卡通人物。"""
    wall = add_box("Wall", (8, 0.15, 5), (0, 2.5, 1.5), mats["wall"])
    floor = add_box("Floor", (8, 6, 0.15), (0, 0, -0.5), mats["floor"])
    sofa = add_box("Sofa", (2.2, 0.85, 0.55), (0, -0.15, 0.15), mats["sofa"], bevel=0.04)
    add_box("SofaBack", (2.2, 0.15, 0.7), (0, 0.35, 0.45), mats["sofa"], bevel=0.03)
    add_box("PillowL", (0.35, 0.35, 0.12), (-0.55, -0.05, 0.42), mats["pillow"], bevel=0.02)
    add_box("PillowR", (0.35, 0.35, 0.12), (0.55, -0.05, 0.42), mats["pillow"], bevel=0.02)

    # 卡通人物（简化）
    body = add_box("CharBody", (0.45, 0.32, 0.55), (0.15, -0.05, 0.55), mats["shirt"], bevel=0.03)
    head = add_uv_sphere("CharHead", 0.22, (0.15, -0.05, 1.05), mats["skin"])
    add_uv_sphere("EyeL", 0.04, (0.05, -0.18, 1.1), make_material("Eye", (0.1, 0.15, 0.35)))
    add_uv_sphere("EyeR", 0.04, (0.25, -0.18, 1.1), make_material("Eye", (0.1, 0.15, 0.35)))

    return {"wall": wall, "sofa": sofa, "body": body, "head": head}


def _wall_indoor_ac(mats: dict, loc=(0, -0.5, 2.35)) -> dict:
    """参考：壁挂白机 + 蓝色冷风气柱。"""
    x, y, z = loc
    shell = add_box("IndoorAC", (1.6, 0.18, 0.42), (x, y, z), mats["ac_white"], bevel=0.015)
    add_box("ACGrille", (1.35, 0.04, 0.12), (x, y - 0.1, z + 0.12), mats["metal_grey"])
    add_box("ACVent", (1.2, 0.03, 0.18), (x, y - 0.11, z - 0.08), mats["ac_white"])
    rays = []
    for i in range(5):
        px = x - 0.55 + i * 0.28
        ray = add_box(f"ColdRay_{i}", (0.12, 0.02, 0.55), (px, y - 0.25, z - 0.55), mats["cold_ray"])
        rays.append(ray)
    return {"shell": shell, "rays": rays}


def _coil_bank(name: str, origin, *, rows: int, mats_list, spacing=0.11) -> bpy.types.Object:
    """参考：水平铜管排，颜色从上到下变凉。"""
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=origin)
    parent = bpy.context.active_object
    parent.name = name
    ox, oy, oz = origin
    for i in range(rows):
        mat = mats_list[min(i, len(mats_list) - 1)]
        tube = add_cylinder(
            f"{name}_tube_{i:02d}",
            0.045,
            1.35,
            (ox, oy, oz + i * spacing),
            mat,
            rot=(0, math.radians(90), 0),
        )
        tube.parent = parent
        # U 形弯头
        bend = add_torus(
            f"{name}_bend_{i:02d}",
            0.05,
            0.018,
            (ox - 0.68, oy, oz + i * spacing + spacing / 2),
            mat,
            rot=(0, 0, math.radians(90)),
        )
        bend.parent = parent
    return parent


def _schematic_loop(mats: dict, y=0.0) -> dict:
    """参考总览图：蒸发器-压缩机-冷凝器 + 铜管连接。"""
    # 蒸发器（左，蓝）
    evap = _coil_bank("Evaporator", (-1.45, y, -0.15), rows=8, mats_list=[mats["copper"]] * 8)
    evap_fan = add_cylinder("EvapFan", 0.22, 0.06, (-1.45, y - 0.35, 0.05), mats["fan_blade"], rot=(math.radians(90), 0, 0))

    # 冷凝器（右，红→黄渐变）
    cond = _coil_bank(
        "Condenser",
        (1.45, y, -0.15),
        rows=10,
        mats_list=[mats["copper_hot"], mats["copper_hot"], mats["copper_warm"], mats["copper_warm"], mats["copper_cool"]] * 3,
    )
    cond_fan = add_cylinder("CondFan", 0.35, 0.05, (1.45, y + 0.45, 0.05), mats["fan_blade"], rot=(math.radians(90), 0, 0))

    # 压缩机（中，剖切感）
    comp_shell = add_cylinder("CompShell", 0.32, 0.75, (0, y, -0.05), mats["compressor_body"])
    comp_inner = add_cylinder("CompInner", 0.18, 0.55, (0, y - 0.05, -0.05), mats["metal_grey"])
    piston = add_cylinder("Piston", 0.12, 0.35, (0, y - 0.12, 0.05), mats["metal_grey"])
    copper_coil = add_torus("CompCoil", 0.14, 0.025, (0, y + 0.08, 0.0), mats["copper"], rot=(math.radians(90), 0, 0))

    # 连接铜管
    pipe_top = add_cylinder("PipeTop", 0.04, 2.6, (0, y, 0.45), mats["copper"], rot=(0, math.radians(90), 0))
    pipe_bot = add_cylinder("PipeBot", 0.035, 2.6, (0, y, -0.55), mats["copper"], rot=(0, math.radians(90), 0))
    pipe_up = add_cylinder("PipeUp", 0.04, 0.55, (1.45, y, 0.45), mats["copper"])
    pipe_down = add_cylinder("PipeDown", 0.035, 0.55, (-1.45, y, -0.55), mats["copper"])

    return {
        "evap": evap,
        "evap_fan": evap_fan,
        "cond": cond,
        "cond_fan": cond_fan,
        "compressor": comp_shell,
        "piston": piston,
        "pipes": [pipe_top, pipe_bot, pipe_up, pipe_down],
    }


def _compressor_cutaway(mats: dict) -> dict:
    """参考：0°C / 80°C 腔室 + 活塞。"""
    frame = add_box("CompFrame", (1.1, 0.55, 1.8), (0, 0, 0.2), mats["frame"], bevel=0.02)
    cold_ch = add_box("ColdChamber", (0.42, 0.38, 0.35), (-0.28, 0, 1.05), mats["coil_blue"], bevel=0.01)
    hot_ch = add_box("HotChamber", (0.42, 0.38, 0.35), (0.28, 0, 1.05), mats["coil_red"], bevel=0.01)
    cylinder = add_cylinder("Cylinder", 0.38, 1.1, (0, 0, 0.05), mats["metal_grey"])
    piston = add_cylinder("Piston", 0.28, 0.45, (0, -0.05, 0.45), mats["metal_grey"])
    rod = add_cylinder("Rod", 0.06, 0.55, (0, -0.05, 0.05), mats["metal_grey"])
    return {"frame": frame, "cold_ch": cold_ch, "hot_ch": hot_ch, "piston": piston, "rod": rod}


def _animate_fan(obj, frames: int) -> None:
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.keyframe_insert("rotation_euler", frame=1)
    obj.rotation_euler = (math.radians(90), 0, math.radians(1440))
    obj.keyframe_insert("rotation_euler", frame=frames)
    linear_keys(obj, "rotation_euler")


def _animate_piston(piston, rod, frames: int) -> None:
    z0 = piston.location.z
    for f, dz in ((1, 0.0), (frames // 2, 0.18), (frames, 0.0)):
        piston.location.z = z0 + dz
        rod.location.z = z0 - 0.25 + dz * 0.5
        piston.keyframe_insert("location", frame=f)
        rod.keyframe_insert("location", frame=f)


def _animate_refrigerant(mats: dict, frames: int, count=14) -> None:
    path = [
        (0, 0, -0.05),
        (1.45, 0, 0.35),
        (1.45, 0, -0.45),
        (-1.45, 0, -0.45),
        (-1.45, 0, 0.35),
        (0, 0, -0.05),
    ]
    step = max(1, frames // 28)
    for i in range(count):
        mat = mats["gas_hot"] if i % 2 == 0 else mats["gas_cold"]
        ball = add_uv_sphere(f"Ref_{i:02d}", 0.055, path[0], mat)
        phase = i / count
        for f in range(1, frames + 1, step):
            t = ((f - 1) / max(frames - 1, 1) + phase) % 1.0
            seg = t * (len(path) - 1)
            si = min(int(seg), len(path) - 2)
            local = seg - si
            a = path[si]
            b = path[si + 1]
            ball.location = (
                a[0] + (b[0] - a[0]) * local,
                a[1] + (b[1] - a[1]) * local,
                a[2] + (b[2] - a[2]) * local,
            )
            ball.keyframe_insert("location", frame=f)
        linear_keys(ball, "location")


def _animate_cold_rays(rays: list, frames: int) -> None:
    for i, r in enumerate(rays):
        z0 = r.location.z
        for f in (1, frames // 2, frames):
            r.location.z = z0 + 0.08 * math.sin((f / frames) * math.pi + i * 0.5)
            r.keyframe_insert("location", frame=f)


# ---------- 分镜（竖屏构图） ----------


def build_hook(frames: int) -> None:
    clear_scene()
    setup_bright_world()
    setup_soft_lights()
    mats = _mats()
    _living_room(mats)
    ac = _wall_indoor_ac(mats, (0, -0.3, 2.1))
    _animate_cold_rays(ac["rays"], frames)

    # 后半段淡入原理图（下方）
    loop = _schematic_loop(mats, y=-0.8)
    _animate_fan(loop["evap_fan"], frames)
    _animate_fan(loop["cond_fan"], frames)

    cam = setup_camera((0, -5.5, 1.8), (0, -0.2, 1.0), lens=30)
    keyframe_dolly(cam, (0, -5.5, 1.8), (0, -4.2, 1.5), (0, -0.2, 0.9), 1, frames)


def build_cutaway(frames: int) -> None:
    clear_scene()
    setup_bright_world()
    setup_soft_lights()
    mats = _mats()
    add_box("Backdrop", (6, 6, 0.1), (0, 1.5, -0.3), mats["wall"])
    loop = _schematic_loop(mats, y=0.0)
    _animate_fan(loop["evap_fan"], frames)
    _animate_fan(loop["cond_fan"], frames)
    _animate_piston(loop["piston"], loop["compressor"], frames)

    cam = setup_camera((0, -4.8, 1.2), (0, 0, 0.1), lens=28)
    keyframe_orbit(cam, (0, 0, 0.0), 4.6, 1.1, 1, frames, -40, 15)


def build_cycle(frames: int) -> None:
    """参考 frame_120/150：冷凝器渐变管 + 风扇。"""
    clear_scene()
    setup_bright_world()
    setup_soft_lights()
    mats = _mats()
    add_box("Backdrop", (5, 5, 0.1), (0, 1.2, -0.2), mats["wall"])
    cond = _coil_bank(
        "CondenserClose",
        (-0.3, 0, 0.0),
        rows=12,
        mats_list=[
            mats["copper_hot"],
            mats["copper_hot"],
            mats["copper_hot"],
            mats["copper_warm"],
            mats["copper_warm"],
            mats["copper_cool"],
            mats["copper_cool"],
        ],
        spacing=0.1,
    )
    fan = add_cylinder("BigFan", 0.55, 0.06, (0.55, 0.35, 0.15), mats["fan_blade"], rot=(math.radians(90), 0, 0))
    comp = add_cylinder("CompSide", 0.28, 0.7, (1.35, 0, -0.15), mats["compressor_body"])
    add_cylinder("CompPipe", 0.05, 0.45, (1.0, 0, 0.55), mats["copper_hot"])
    _animate_fan(fan, frames)
    _animate_refrigerant(mats, frames, count=10)

    cam = setup_camera((0.2, -3.2, 0.85), (0.1, 0.1, 0.15), lens=32)
    keyframe_dolly(cam, (0.2, -3.2, 0.85), (0.15, -2.5, 0.65), (0.1, 0.1, 0.15), 1, frames)


def build_analogy(frames: int) -> None:
    """参考 frame_90：压缩机剖切 + 冷热腔。"""
    clear_scene()
    setup_bright_world()
    setup_soft_lights()
    mats = _mats()
    cut = _compressor_cutaway(mats)
    _animate_piston(cut["piston"], cut["rod"], frames)
    cam = setup_camera((0, -3.5, 1.0), (0, 0, 0.5), lens=30)
    keyframe_orbit(cam, (0, 0, 0.45), 3.4, 0.95, 1, frames, -35, 25)


def build_outro(frames: int) -> None:
    clear_scene()
    setup_bright_world()
    setup_soft_lights()
    mats = _mats()
    _living_room(mats)
    _wall_indoor_ac(mats, (0, -0.3, 2.0))
    loop = _schematic_loop(mats, y=-0.6)
    _animate_fan(loop["evap_fan"], frames)
    _animate_fan(loop["cond_fan"], frames)
    _animate_refrigerant(mats, frames, count=12)
    cam = setup_camera((0, -6.0, 2.0), (0, 0, 0.6), lens=30)
    keyframe_orbit(cam, (0, 0, 0.5), 5.8, 1.9, 1, frames, -75, -45)


SCENE_BUILDERS: dict[str, Callable[[int], None]] = {
    "hook": build_hook,
    "cutaway": build_cutaway,
    "cycle": build_cycle,
    "analogy": build_analogy,
    "outro": build_outro,
}


def build_scene(scene_name: str, frames: int) -> None:
    fn = SCENE_BUILDERS.get(scene_name)
    if not fn:
        raise KeyError(scene_name)
    fn(frames)
