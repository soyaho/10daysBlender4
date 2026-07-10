# -*- coding: utf-8 -*-
"""
10: 明日館スケールの生徒キャラクター (Mixamo 対応リグ付き)
ヘッドレス bpy スクリプト方式:
    python3 10_生徒キャラクター.py
で以下をすべて行う。
  1. 実寸 (身長約 1.6 m) のローポリ生徒キャラクターを生成
  2. Mixamo 命名規則 (mixamorig:*) の T ポーズアーマチュアを作成し
     自動ウェイトでスキニング
  3. Mixamo アップロード用の FBX をエクスポート
  4. 09 の明日館を読み込み、スケール比較のレンダリングを保存

Mixamo での使い方:
  - 10_生徒キャラクター.fbx を https://www.mixamo.com/ にアップロード
    するとそのままアニメーションを適用できる
  - Mixamo からダウンロードしたアニメーション FBX (Without Skin) は
    ボーン名が一致しているので Blender 上でアクションを流用できる
"""
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BASENAME = "10_生徒キャラクター"
BLEND09 = os.path.join(HERE, "09_自由学園明日館.blend")
TEST = os.environ.get("TEST_RENDER") == "1"  # 低解像度の確認用レンダリング

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
    "skin":   make_material("skin", (0.800, 0.560, 0.420), 0.75),
    "blouse": make_material("blouse", (0.900, 0.880, 0.840), 0.80),
    "skirt":  make_material("skirt", (0.055, 0.075, 0.160), 0.85),
    "hair":   make_material("hair", (0.080, 0.050, 0.030), 0.60),
    "shoe":   make_material("shoe", (0.070, 0.045, 0.028), 0.55),
    "ribbon": make_material("ribbon", (0.420, 0.060, 0.060), 0.70),
    "eye":    make_material("eye", (0.030, 0.025, 0.020), 0.40),
}

# ---------------------------------------------------------------- part helpers
PARTS = []

def _finish(obj, name, mat):
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    except Exception:
        pass
    PARTS.append(obj)
    return obj

def sphere(name, r, loc, mat, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12,
                                         radius=r, location=loc)
    obj = bpy.context.object
    obj.scale = scale
    return _finish(obj, name, mat)

def cyl(name, r, p1, p2, mat, verts=12):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r,
                                        depth=d.length,
                                        location=(p1 + p2) / 2)
    obj = bpy.context.object
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return _finish(obj, name, mat)

def cone(name, r_bottom, r_top, z_bottom, z_top, mat, verts=16):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r_bottom,
                                    radius2=r_top, depth=z_top - z_bottom,
                                    location=(0, 0, (z_top + z_bottom) / 2))
    return _finish(bpy.context.object, name, mat)

def box(name, dims, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.scale = dims
    return _finish(obj, name, mat)

# ---------------------------------------------------------------- build body
# 正面は -Y。身長約 1.63 m の T ポーズ。
sphere("head", 0.16, (0, 0, 1.47), MAT["skin"])
sphere("hair", 0.175, (0, 0.025, 1.50), MAT["hair"], scale=(1, 1, 0.95))
box("bangs", (0.30, 0.06, 0.10), (0, -0.115, 1.575), MAT["hair"])
sphere("eye_L", 0.021, (0.058, -0.148, 1.50), MAT["eye"])
sphere("eye_R", 0.021, (-0.058, -0.148, 1.50), MAT["eye"])
cyl("neck", 0.05, (0, 0, 1.28), (0, 0, 1.42), MAT["skin"])

torso = cyl("torso", 0.15, (0, 0, 0.88), (0, 0, 1.30), MAT["blouse"], verts=14)
torso.scale = (1, 0.78, 1)
bpy.ops.object.transform_apply(scale=True)
box("collar", (0.20, 0.16, 0.05), (0, 0.03, 1.275), MAT["skirt"])
box("ribbon", (0.09, 0.035, 0.05), (0, -0.125, 1.22), MAT["ribbon"])

cone("skirt", 0.25, 0.165, 0.52, 0.90, MAT["skirt"])

for sx, tag in ((1, "L"), (-1, "R")):
    # 腕 (T ポーズ, +X が左)
    cyl(f"upperarm_{tag}", 0.048, (sx * 0.15, 0, 1.24), (sx * 0.40, 0, 1.24),
        MAT["blouse"])
    cyl(f"forearm_{tag}", 0.040, (sx * 0.40, 0, 1.24), (sx * 0.62, 0, 1.24),
        MAT["skin"])
    sphere(f"hand_{tag}", 0.055, (sx * 0.66, 0, 1.24), MAT["skin"],
           scale=(1.3, 0.7, 0.9))
    # 脚
    cyl(f"upperleg_{tag}", 0.062, (sx * 0.08, 0, 0.86), (sx * 0.08, 0, 0.48),
        MAT["skin"])
    cyl(f"lowerleg_{tag}", 0.050, (sx * 0.08, 0, 0.48), (sx * 0.08, 0, 0.10),
        MAT["skin"])
    box(f"shoe_{tag}", (0.11, 0.22, 0.10), (sx * 0.08, -0.03, 0.05),
        MAT["shoe"])

# 1 つのメッシュに統合
for o in PARTS:
    o.select_set(True)
bpy.context.view_layer.objects.active = PARTS[0]
bpy.ops.object.join()
body = bpy.context.object
body.name = "student"

# ---------------------------------------------------------------- armature
# Mixamo 命名規則 / 階層。(名前, 親, head, tail)
B = "mixamorig:"
BONES = [
    (B + "Hips", None, (0, 0, 0.86), (0, 0, 0.96)),
    (B + "Spine", B + "Hips", (0, 0, 0.96), (0, 0, 1.08)),
    (B + "Spine1", B + "Spine", (0, 0, 1.08), (0, 0, 1.20)),
    (B + "Spine2", B + "Spine1", (0, 0, 1.20), (0, 0, 1.30)),
    (B + "Neck", B + "Spine2", (0, 0, 1.30), (0, 0, 1.40)),
    (B + "Head", B + "Neck", (0, 0, 1.40), (0, 0, 1.63)),
    (B + "HeadTop_End", B + "Head", (0, 0, 1.63), (0, 0, 1.70)),
]
for sx, side in ((1, "Left"), (-1, "Right")):
    BONES += [
        (B + side + "Shoulder", B + "Spine2",
         (sx * 0.05, 0, 1.27), (sx * 0.15, 0, 1.24)),
        (B + side + "Arm", B + side + "Shoulder",
         (sx * 0.15, 0, 1.24), (sx * 0.40, 0, 1.24)),
        (B + side + "ForeArm", B + side + "Arm",
         (sx * 0.40, 0, 1.24), (sx * 0.62, 0, 1.24)),
        (B + side + "Hand", B + side + "ForeArm",
         (sx * 0.62, 0, 1.24), (sx * 0.73, 0, 1.24)),
        (B + side + "UpLeg", B + "Hips",
         (sx * 0.08, 0, 0.86), (sx * 0.08, 0, 0.48)),
        (B + side + "Leg", B + side + "UpLeg",
         (sx * 0.08, 0, 0.48), (sx * 0.08, 0, 0.10)),
        (B + side + "Foot", B + side + "Leg",
         (sx * 0.08, 0, 0.10), (sx * 0.08, -0.10, 0.03)),
        (B + side + "ToeBase", B + side + "Foot",
         (sx * 0.08, -0.10, 0.03), (sx * 0.08, -0.17, 0.03)),
        (B + side + "Toe_End", B + side + "ToeBase",
         (sx * 0.08, -0.17, 0.03), (sx * 0.08, -0.22, 0.03)),
    ]

arm_data = bpy.data.armatures.new("Armature")
arm_obj = bpy.data.objects.new("Armature", arm_data)
bpy.context.collection.objects.link(arm_obj)
bpy.ops.object.select_all(action="DESELECT")
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode="EDIT")
for name, parent, head, tail in BONES:
    eb = arm_data.edit_bones.new(name)
    eb.head, eb.tail = head, tail
    if parent:
        eb.parent = arm_data.edit_bones[parent]
bpy.ops.object.mode_set(mode="OBJECT")
for bone in arm_data.bones:  # 末端マーカーは変形に使わない
    if bone.name.endswith("_End"):
        bone.use_deform = False

# ---------------------------------------------------------------- skinning
# 多シェル構造 (目・前髪などが重なる) はボーンヒート法が失敗するため、
# ボーン軸までの距離をもとにスムーズウェイトを自前で計算する。
def segment_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (a + ab * t - p).length

body.parent = arm_obj
body.modifiers.new("Armature", "ARMATURE").object = arm_obj

deform = [(n, Vector(h), Vector(t)) for n, _, h, t in BONES
          if not n.endswith("_End")]
groups = {n: body.vertex_groups.new(name=n) for n, _, _ in deform}
for v in body.data.vertices:
    dists = sorted(((segment_dist(v.co, h, t), n) for n, h, t in deform))[:3]
    raw = [(max(1e-8, 1.0 / (d + 0.01)) ** 6, n) for d, n in dists]
    wmax = max(w for w, _ in raw)
    raw = [(w, n) for w, n in raw if w > 0.05 * wmax]
    total = sum(w for w, _ in raw)
    for w, n in raw:
        groups[n].add([v.index], w / total, "REPLACE")
print(f"skinned vertices: {len(body.data.vertices)}")

# ---------------------------------------------------------------- FBX export
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.export_scene.fbx(
    filepath=os.path.join(HERE, BASENAME + ".fbx"),
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL",
    add_leaf_bones=False,
    bake_anim=False,
    path_mode="COPY",
    embed_textures=True,
)

# ---------------------------------------------------------------- backdrop
# 09 の明日館を読み込んでスケール比較ショットにする
if os.path.exists(BLEND09):
    with bpy.data.libraries.load(BLEND09) as (data_from, data_to):
        data_to.objects = list(data_from.objects)
    for o in data_to.objects:
        if o and o.type == "MESH":
            bpy.context.collection.objects.link(o)

# キャラクターを前庭の園路の上へ (メッシュはアーマチュアの子)
arm_obj.location = (0.6, -7.5, 0.07)
arm_obj.rotation_euler = (0, 0, math.radians(-15))

# ---------------------------------------------------------------- lighting
sun = bpy.data.lights.new("sun", type="SUN")
sun.energy = 4.2
sun.angle = math.radians(2.0)
sun_obj = bpy.data.objects.new("sun", sun)
sun_obj.rotation_euler = (math.radians(48), 0, math.radians(-35))
bpy.context.collection.objects.link(sun_obj)

world = bpy.data.worlds.new("world")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.45, 0.65, 0.92, 1.0)
bg.inputs["Strength"].default_value = 0.95
scene.world = world

# ---------------------------------------------------------------- camera
cam_data = bpy.data.cameras.new("camera")
cam_data.lens = 40
cam = bpy.data.objects.new("camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = Vector((-1.6, -11.8, 1.55))
direction = Vector((0.4, -6.0, 1.15)) - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

# ---------------------------------------------------------------- render
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16 if TEST else 96
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.resolution_x = 640 if TEST else 1920
scene.render.resolution_y = 360 if TEST else 1080
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"
scene.render.filepath = os.path.join(
    HERE, BASENAME + ("_test.png" if TEST else ".png"))

if not TEST:
    bpy.ops.wm.save_as_mainfile(
        filepath=os.path.join(HERE, BASENAME + ".blend"), relative_remap=True)
bpy.ops.render.render(write_still=True)
print("done:", scene.render.filepath)
