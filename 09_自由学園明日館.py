# -*- coding: utf-8 -*-
"""
09: 自由学園明日館 (フランク・ロイド・ライト設計, 1921) の簡易モデル
ヘッドレス bpy スクリプト方式:
    python3 09_自由学園明日館.py
で .blend の保存と .png のレンダリングまで行う。

構成:
  - 中央ホール (大きな幾何学格子窓 + 寄棟屋根 + 大谷石の煙突)
  - 左右の低い回廊と教室棟がコの字に芝生の中庭を囲む
  - 大谷石のプランター・階段・園路
"""
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BASENAME = "09_自由学園明日館"
HDRI = os.path.join(HERE, "blue_photo_studio_4k.exr")

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- materials
def make_material(name, color, rough=0.7, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

MAT = {
    "plaster": make_material("plaster", (0.870, 0.835, 0.760), 0.85),
    "wood":    make_material("wood_dark", (0.072, 0.045, 0.028), 0.55),
    "roof":    make_material("roof", (0.300, 0.320, 0.290), 0.80),
    "stone":   make_material("oya_stone", (0.620, 0.600, 0.520), 0.90),
    "glass":   make_material("window_glass", (0.030, 0.045, 0.055), 0.08, 0.85),
    "grass":   make_material("grass", (0.085, 0.210, 0.060), 0.95),
    "path":    make_material("path", (0.560, 0.530, 0.470), 0.95),
    "leaf":    make_material("leaf", (0.070, 0.180, 0.050), 0.90),
    "trunk":   make_material("trunk", (0.130, 0.085, 0.050), 0.85),
}

# ---------------------------------------------------------------- helpers
def add_box(name, dims, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = dims
    obj.data.materials.append(mat)
    return obj


def add_hip_roof(name, width, depth, z0, height, overhang, center_xy, mat):
    """寄棟屋根。width/depth は壁の外寸、overhang で軒の出を付ける。"""
    w = width + 2 * overhang
    d = depth + 2 * overhang
    if w >= d:
        tx, ty = (w - d) / 2 + 0.15, 0.15
    else:
        tx, ty = 0.15, (d - w) / 2 + 0.15
    cx, cy = center_xy
    verts = [
        (cx - w / 2, cy - d / 2, z0), (cx + w / 2, cy - d / 2, z0),
        (cx + w / 2, cy + d / 2, z0), (cx - w / 2, cy + d / 2, z0),
        (cx - tx, cy - ty, z0 + height), (cx + tx, cy - ty, z0 + height),
        (cx + tx, cy + ty, z0 + height), (cx - tx, cy + ty, z0 + height),
    ]
    faces = [
        (3, 2, 1, 0), (4, 5, 6, 7),
        (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def add_window(name, w, h, center, ncols, nrows, facing="Y",
               bar=0.05, frame=0.10, depth=0.10):
    """木製格子入りの窓。facing='Y' は南北向きの壁面、'X' は東西向き。"""
    cx, cy, cz = center

    def bar_box(nm, along_w, along_h, off_along, off_z):
        if facing == "Y":
            dims = (along_w, depth, along_h)
            loc = (cx + off_along, cy, cz + off_z)
        else:
            dims = (depth, along_w, along_h)
            loc = (cx, cy + off_along, cz + off_z)
        return add_box(nm, dims, loc, MAT["wood"])

    # ガラス面
    if facing == "Y":
        add_box(name + "_glass", (w, depth * 0.3, h), (cx, cy, cz), MAT["glass"])
    else:
        add_box(name + "_glass", (depth * 0.3, w, h), (cx, cy, cz), MAT["glass"])
    # 外枠
    bar_box(name + "_fL", frame, h + frame, -(w + frame) / 2, 0)
    bar_box(name + "_fR", frame, h + frame, (w + frame) / 2, 0)
    bar_box(name + "_fT", w + frame * 2, frame, 0, (h + frame) / 2)
    bar_box(name + "_fB", w + frame * 2, frame, 0, -(h + frame) / 2)
    # 縦桟・横桟
    for i in range(1, ncols):
        bar_box(f"{name}_v{i}", bar, h, -w / 2 + w * i / ncols, 0)
    for j in range(1, nrows):
        bar_box(f"{name}_h{j}", w, bar, 0, -h / 2 + h * j / nrows)


def add_tree(name, loc, trunk_h=2.2, canopy_r=1.5):
    add_box(name + "_trunk", (0.22, 0.22, trunk_h),
            (loc[0], loc[1], trunk_h / 2), MAT["trunk"])
    for k, (dx, dy, dz, r) in enumerate([
            (0, 0, 0, 1.0), (0.7, 0.3, -0.35, 0.62), (-0.6, -0.4, -0.3, 0.58)]):
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2, radius=canopy_r * r,
            location=(loc[0] + dx, loc[1] + dy, trunk_h + canopy_r * 0.75 + dz))
        o = bpy.context.object
        o.name = f"{name}_leaf{k}"
        o.data.materials.append(MAT["leaf"])
        bpy.ops.object.shade_smooth()


# ---------------------------------------------------------------- ground
add_box("ground", (90, 90, 0.2), (0, 0, -0.1), MAT["grass"])
add_box("front_path", (3.2, 15, 0.24), (0, -8.4, -0.05), MAT["path"])
add_box("cross_path", (26, 2.4, 0.24), (0, -13.5, -0.05), MAT["path"])

# ---------------------------------------------------------------- central hall
# 壁 (南面 y=0 が正面)
add_box("hall_body", (14, 9, 5.2), (0, 4.5, 2.6), MAT["plaster"])
add_hip_roof("hall_roof", 14, 9, 5.2, 2.3, 1.0, (0, 4.5), MAT["roof"])
add_box("hall_trim", (14.2, 9.2, 0.22), (0, 4.5, 5.1), MAT["wood"])
add_box("hall_band", (14.1, 9.1, 0.14), (0, 4.5, 3.0), MAT["wood"])

# 象徴的な大きな幾何学格子窓 (南面)
add_window("hall_window", 7.2, 3.6, (0, -0.02, 2.9), 12, 6, facing="Y")
for i in (-1, 0, 1):  # 太い縦方立で 4 分割
    add_box(f"hall_mullion{i}", (0.14, 0.16, 3.7),
            (i * 1.8, -0.02, 2.9), MAT["wood"])
# 玄関扉
add_box("hall_door", (1.6, 0.16, 1.0), (0, -0.02, 0.55), MAT["wood"])
# 大窓の左右の小窓
for sx in (-1, 1):
    add_window(f"hall_side_win{sx}", 1.2, 1.4, (sx * 5.4, -0.02, 3.2),
               2, 3, facing="Y")

# 大谷石の煙突
add_box("chimney", (1.7, 1.0, 3.8), (0, 6.5, 6.9), MAT["stone"])
add_box("chimney_cap", (1.9, 1.2, 0.2), (0, 6.5, 8.85), MAT["stone"])

# ---------------------------------------------------------------- terrace
add_box("terrace", (10, 3.6, 0.5), (0, -1.8, 0.25), MAT["stone"])
for k in range(3):
    add_box(f"step{k}", (5.2, 0.5, 0.5 - k * 0.16),
            (0, -3.85 - k * 0.5, (0.5 - k * 0.16) / 2), MAT["stone"])
for sx in (-1, 1):  # 大谷石プランター + 植栽
    add_box(f"planter{sx}", (1.2, 1.2, 0.95), (sx * 4.6, -2.6, 0.475), MAT["stone"])
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=2, radius=0.65, location=(sx * 4.6, -2.6, 1.35))
    o = bpy.context.object
    o.name = f"shrub{sx}"
    o.data.materials.append(MAT["leaf"])
    bpy.ops.object.shade_smooth()

# ---------------------------------------------------------------- wings
for sx in (-1, 1):
    tag = "W" if sx < 0 else "E"
    # 回廊 (ホールと教室棟をつなぐ低い棟)
    add_box(f"corr_{tag}", (4.2, 4.0, 3.0), (sx * 9.1, 3.0, 1.5), MAT["plaster"])
    add_hip_roof(f"corr_roof_{tag}", 4.2, 4.0, 3.0, 1.0, 0.8,
                 (sx * 9.1, 3.0), MAT["roof"])
    add_window(f"corr_win_{tag}", 3.0, 1.3, (sx * 9.1, 0.98, 1.9),
               5, 2, facing="Y")
    # 教室棟 (南へ延び中庭を囲む)
    add_box(f"wing_{tag}", (6, 14, 3.6), (sx * 14.2, -2.0, 1.8), MAT["plaster"])
    add_hip_roof(f"wing_roof_{tag}", 6, 14, 3.6, 1.6, 0.9,
                 (sx * 14.2, -2.0), MAT["roof"])
    add_box(f"wing_trim_{tag}", (6.2, 14.2, 0.2), (sx * 14.2, -2.0, 3.5),
            MAT["wood"])
    # 中庭側の連続窓
    for j in range(3):
        add_window(f"wing_win_{tag}{j}", 2.2, 1.5,
                   (sx * 11.18, -6.2 + j * 4.2, 2.0), 4, 2, facing="X")
    # 南端の妻面窓
    add_window(f"wing_gable_win_{tag}", 2.6, 1.5, (sx * 14.2, -9.02, 2.0),
               4, 2, facing="Y")

# ---------------------------------------------------------------- trees
add_tree("tree_L", (-21.5, -12, 0), trunk_h=2.6, canopy_r=1.9)
add_tree("tree_R", (22.0, -10, 0), trunk_h=2.3, canopy_r=1.7)

# ---------------------------------------------------------------- lighting
sun = bpy.data.lights.new("sun", type="SUN")
sun.energy = 4.0
sun.angle = math.radians(1.5)
sun_obj = bpy.data.objects.new("sun", sun)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(-38))
bpy.context.collection.objects.link(sun_obj)

world = bpy.data.worlds.new("world")
world.use_nodes = True
nt = world.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(HDRI)
bg = nt.nodes["Background"]
bg.inputs["Strength"].default_value = 0.5
nt.links.new(env.outputs["Color"], bg.inputs["Color"])
scene.world = world

# ---------------------------------------------------------------- camera
cam_data = bpy.data.cameras.new("camera")
cam_data.lens = 33
cam = bpy.data.objects.new("camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = Vector((-23.0, -28.0, 11.0))
direction = Vector((0, 1.0, 2.4)) - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# ---------------------------------------------------------------- render setup
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.render.filepath = os.path.join(HERE, BASENAME + ".png")

# ---------------------------------------------------------------- save & render
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, BASENAME + ".blend"),
                            relative_remap=True)
bpy.ops.render.render(write_still=True)
print("done:", scene.render.filepath)
