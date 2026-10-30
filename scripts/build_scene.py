# Antler VC — Austin skyline at night from Lady Bird Lake, looping logo drop behind clouds
import bpy, bmesh, math, random
random.seed(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
LOOP = 180
scn.frame_start, scn.frame_end = 1, LOOP
scn.render.fps = 30
scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
scn.render.engine = 'BLENDER_EEVEE'
ee = scn.eevee
for a, v in [("use_raytracing", True), ("taa_render_samples", 48), ("use_shadows", True)]:
    if hasattr(ee, a): setattr(ee, a, v)
scn.view_settings.view_transform = 'Standard'

def fcurves(obj):
    act = obj.animation_data.action
    return list(act.fcurves) if hasattr(act, "fcurves") else [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]

def mat(name, color, emit=None, strength=0.0, metal=0.0, rough=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

# ---------- procedural lit-window facade (tint = object colour RGB, lit fraction = object colour alpha) ----------
def facade_material():
    m = bpy.data.materials.new("Facade"); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.015, 0.02, 0.035, 1)
    b.inputs["Metallic"].default_value = 0.7
    b.inputs["Roughness"].default_value = 0.12
    geo = N.new("ShaderNodeNewGeometry"); oi = N.new("ShaderNodeObjectInfo")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    def op(o, a, bb=None, c=None):
        n = N.new("ShaderNodeMath"); n.operation = o
        for i, v in enumerate((a, bb, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: L.new(v, n.inputs[i])
        return n.outputs[0]
    h = op('DIVIDE', op('ADD', sep.outputs["X"], sep.outputs["Y"]), 0.42)
    v = op('DIVIDE', sep.outputs["Z"], 0.55)
    fh, fv = op('FRACT', h), op('FRACT', v)
    mask = op('MULTIPLY',
              op('MULTIPLY', op('GREATER_THAN', fh, 0.2), op('LESS_THAN', fh, 0.8)),
              op('MULTIPLY', op('GREATER_THAN', fv, 0.28), op('LESS_THAN', fv, 0.8)))
    cell = N.new("ShaderNodeCombineXYZ")
    L.new(op('FLOOR', h), cell.inputs[0]); L.new(op('FLOOR', v), cell.inputs[1])
    L.new(op('MULTIPLY', oi.outputs["Random"], 97.0), cell.inputs[2])
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '3D'
    L.new(cell.outputs[0], wn.inputs["Vector"])
    lit = op('LESS_THAN', wn.outputs["Value"], oi.outputs["Alpha"])
    # per-window brightness jitter + faint glow in unlit windows
    jit = N.new("ShaderNodeSeparateColor"); L.new(wn.outputs["Color"], jit.inputs[0])
    bright = op('ADD', op('MULTIPLY', lit, op('MULTIPLY_ADD', jit.outputs[0], 0.7, 0.5)), 0.04)
    L.new(op('MULTIPLY', op('MULTIPLY', mask, bright), 1.6), b.inputs["Emission Strength"])
    # tint jitter between object tint and a warmer white
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    L.new(jit.outputs[1], mix.inputs["Factor"])
    L.new(oi.outputs["Color"], mix.inputs[6]); mix.inputs[7].default_value = (1.0, 0.85, 0.6, 1)
    mixf = op('MULTIPLY', jit.outputs[1], 0.35); L.new(mixf, mix.inputs["Factor"])
    L.new(mix.outputs[2], b.inputs["Emission Color"])
    return m
facade = facade_material()

WARM, WHITE, COOL, BLUE, GOLD = (1.0, 0.62, 0.28), (1.0, 0.92, 0.8), (0.65, 0.82, 1.0), (0.3, 0.5, 1.0), (1.0, 0.75, 0.35)
crown_white = mat("CrownWhite", (0.9, 0.9, 1), emit=(0.85, 0.9, 1.0), strength=6)
crown_blue  = mat("CrownBlue", (0.2, 0.3, 1), emit=(0.15, 0.35, 1.0), strength=10)
crown_gold  = mat("CrownGold", (1, 0.7, 0.3), emit=(1.0, 0.6, 0.2), strength=6)
crown_cyan  = mat("CrownCyan", (0.6, 0.9, 1), emit=(0.5, 0.85, 1.0), strength=7)

sky = bpy.data.collections.new("Skyline"); scn.collection.children.link(sky)
def put(o, m):
    for c in o.users_collection: c.objects.unlink(o)
    sky.objects.link(o); o.data.materials.append(m); return o

def tower(x, y, w, d, h, tint, lit, z0=0, name="Tower"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z0 + h / 2))
    o = bpy.context.object; o.scale = (w, d, h); bpy.ops.object.transform_apply(scale=True)
    o.name = name; o.color = (*tint, lit); return put(o, facade)

def pyramid(x, y, w, d, h, z0, m, verts=4):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=w * 0.707, depth=h, location=(x, y, z0 + h / 2), rotation=(0, 0, math.pi / 4))
    o = bpy.context.object; o.scale.y = d / w; return put(o, m)

def slab(x, y, w, d, h, z0, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z0 + h / 2))
    o = bpy.context.object; o.scale = (w, d, h); bpy.ops.object.transform_apply(scale=True)
    return put(o, m)

# ---- landmark towers, left to right as seen from Lady Bird Lake ----
tower(-34, 2, 7, 6, 23, COOL, 0.75, name="NorthShore")               # blue glass tower, far left
slab(-34, 2, 7.2, 6.2, 0.6, 23, crown_cyan)
tower(-17, 4, 5.5, 5, 21, GOLD, 0.6, name="TanTowerA")               # tan tower with lit sloped top
bpy.ops.mesh.primitive_cube_add(size=1, location=(-17, 4, 22)); o = bpy.context.object
o.scale = (5.5, 5, 2); o.rotation_euler.y = math.radians(14); put(o, crown_gold)
tower(-12, 9, 5, 5, 18, GOLD, 0.55, name="TanTowerB")
pyramid(-12, 9, 4.6, 4.6, 2.5, 18, crown_gold)
tower(-3, 6, 4.4, 4, 40, WHITE, 0.5, name="Austonian")               # tallest, slim
slab(-3, 6, 4.5, 4.1, 1.2, 38.2, crown_cyan); slab(-3, 6, 3.6, 3.2, 1.2, 40, crown_white)
tower(1.5, 12, 4, 4, 24, WHITE, 0.45, name="Mid1")
tower(6, 8, 4.5, 4.5, 27, BLUE, 0.55, name="BlueTower")              # blue-lit crown
slab(6, 8, 4.6, 4.6, 1.5, 27, crown_blue); slab(6, 8, 3.2, 3.2, 1.0, 28.5, crown_blue)
tower(11, 3, 7, 6, 19, GOLD, 0.65, name="TanWide")                   # wide tan with pyramid roof
pyramid(11, 3, 6.4, 5.4, 3.5, 19, crown_gold)
tower(16, 11, 5, 5, 25, WHITE, 0.35, name="DarkTower")
# Frost Bank Tower: stepped gothic crown
tower(21, 6, 5, 5, 27, WHITE, 0.55, name="FrostTower")
slab(21, 6, 4.2, 4.2, 2, 27, crown_white); slab(21, 6, 3.4, 3.4, 2, 29, crown_white)
pyramid(21, 6, 3.4, 3.4, 6.5, 31, crown_white)
for sx in (-1, 1):
    for sy in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(radius1=0.35, depth=3, location=(21 + sx * 1.9, 6 + sy * 1.9, 30.5)); put(bpy.context.object, crown_white)
tower(33, 4, 10, 7, 30, WARM, 0.7, name="GlassBox")                  # big glass tower on the right
slab(33, 4, 10.2, 7.2, 0.5, 30, crown_white)
tower(29, 12, 5, 5, 22, COOL, 0.5)

# ---- filler: mid-rises behind, low-rises along the shore ----
for i in range(70):
    x = random.uniform(-75, 75)
    if abs(x) < 40 and random.random() < 0.5: continue
    tower(x, random.uniform(14, 40), random.uniform(4, 8), random.uniform(4, 7), random.uniform(6, 20),
          random.choice([WARM, WHITE, COOL, GOLD]), random.uniform(0.3, 0.75), name="Filler")
for i in range(45):
    x = -78 + i * 3.6 + random.uniform(-1, 1)
    tower(x, random.uniform(-3, 1), random.uniform(3, 6), random.uniform(3, 5), random.uniform(2.5, 9),
          random.choice([WARM, WARM, GOLD, WHITE]), random.uniform(0.4, 0.85), name="LowRise")

# ---- shoreline: ground, trees, lake ----
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 60, 0)); g = bpy.context.object; g.scale = (400, 140, 1)
g.data.materials.append(mat("Ground", (0.01, 0.012, 0.01), rough=0.9))
treem = mat("Trees", (0.01, 0.025, 0.012), rough=0.9)
trees = bpy.data.collections.new("Trees"); scn.collection.children.link(trees)
for i in range(110):
    x = -90 + i * 1.65 + random.uniform(-0.6, 0.6)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=random.uniform(1.5, 2.8),
                                          location=(x, random.uniform(-10, -6), random.uniform(0.8, 2.2)))
    t = bpy.context.object; t.scale.z = random.uniform(0.6, 0.9); t.data.materials.append(treem)
    for c in t.users_collection: c.objects.unlink(t)
    trees.objects.link(t)

water = bpy.data.materials.new("LadyBirdLake"); water.use_nodes = True
wn_ = water.node_tree.nodes; wl_ = water.node_tree.links
wb = wn_["Principled BSDF"]
wb.inputs["Base Color"].default_value = (0.005, 0.01, 0.02, 1)
wb.inputs["Roughness"].default_value = 0.06
wb.inputs["IOR"].default_value = 1.33
tc = wn_.new("ShaderNodeTexCoord"); mp = wn_.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (0.15, 2.5, 1)      # stretched ripples -> long vertical reflection streaks
nz = wn_.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4; nz.inputs["Detail"].default_value = 6
bump = wn_.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
wl_.new(tc.outputs["Object"], mp.inputs["Vector"]); wl_.new(mp.outputs["Vector"], nz.inputs["Vector"])
wl_.new(nz.outputs["Fac"], bump.inputs["Height"]); wl_.new(bump.outputs["Normal"], wb.inputs["Normal"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -110, -0.3)); lk = bpy.context.object
lk.scale = (400, 200, 1); lk.name = "LadyBirdLake"; lk.data.materials.append(water)

# ---------- Antler VC logo (red tile, white chevron, wordmark) ----------
red = mat("AntlerRed", (0.80, 0.07, 0.07), emit=(0.80, 0.07, 0.07), strength=0.8, rough=0.35)
white = mat("AntlerWhite", (1, 1, 1), emit=(1, 1, 1), strength=2.0, rough=0.3)
logo = bpy.data.objects.new("AntlerVC_Logo", None); scn.collection.objects.link(logo)
logo.empty_display_type = "PLAIN_AXES"
LY = -9   # in front of the towers, behind the cloud bank

bpy.ops.mesh.primitive_cube_add(size=1); tile = bpy.context.object
tile.name = "Tile"; tile.scale = (10, 0.8, 10); bpy.ops.object.transform_apply(scale=True)
bv = tile.modifiers.new("Round", 'BEVEL'); bv.width = 0.6; bv.segments = 6
tile.data.materials.append(red); tile.parent = logo

px = [(92, 45), (108, 45), (160, 155), (134, 155), (100, 82), (71, 155), (51, 155)]   # traced from the logo
me = bpy.data.meshes.new("Chevron"); bm = bmesh.new()
f = bm.faces.new([bm.verts.new(((x - 100) / 24, -0.4, (100 - y) / 24 + 1.0)) for x, y in px])
r = bmesh.ops.extrude_face_region(bm, geom=[f])
for vv in [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]: vv.co.y -= 0.25
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
chev = bpy.data.objects.new("Chevron", me); scn.collection.objects.link(chev)
me.materials.append(white); chev.parent = logo

bpy.ops.object.text_add(location=(0, -0.5, -3.4)); txt = bpy.context.object
txt.name = "Wordmark"; txt.data.body = "ANTLER VC"; txt.data.align_x = 'CENTER'
txt.data.size = 1.25; txt.data.space_character = 1.15; txt.data.extrude = 0.08
txt.rotation_euler.x = math.pi / 2; txt.data.materials.append(white); txt.parent = logo

# ---------- the drop: out of the sky, through the cloud bank, down toward the lake ----------
# (behind the clouds while high up, then forward over the trees once it's below them)
END = (0, -30, 11)
for fr, loc in [(1, (0, LY, 82)), (80, (0, LY, 22)), (LOOP, END)]:
    logo.location = loc; logo.keyframe_insert("location", frame=fr)
for fr, ang in [(1, -6), (60, 5), (120, -2), (LOOP, 0)]:
    logo.rotation_euler = (0, math.radians(ang), 0); logo.keyframe_insert("rotation_euler", frame=fr)
for fc in fcurves(logo):
    for k in fc.keyframe_points:
        k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
# ---------- night clouds resting on the tower tops, underlit by the city ----------
cloudm = bpy.data.materials.new("NightCloud"); cloudm.use_nodes = True
cn = cloudm.node_tree.nodes; cl = cloudm.node_tree.links
cb = cn["Principled BSDF"]
cb.inputs["Base Color"].default_value = (0.12, 0.13, 0.18, 1); cb.inputs["Roughness"].default_value = 1.0
cgeo = cn.new("ShaderNodeNewGeometry"); csep = cn.new("ShaderNodeSeparateXYZ")
cl.new(cgeo.outputs["Normal"], csep.inputs[0])
cramp = cn.new("ShaderNodeValToRGB"); cma = cn.new("ShaderNodeMath"); cma.operation = "MULTIPLY_ADD"; cma.inputs[1].default_value = 0.5; cma.inputs[2].default_value = 0.5
cl.new(csep.outputs["Z"], cma.inputs[0]); cl.new(cma.outputs[0], cramp.inputs["Fac"])
cramp.color_ramp.elements[0].position = 0.15; cramp.color_ramp.elements[0].color = (0.55, 0.3, 0.2, 1)   # warm city glow underneath
cramp.color_ramp.elements[1].position = 0.55; cramp.color_ramp.elements[1].color = (0.12, 0.14, 0.22, 1)  # moonlit blue-grey tops
cl.new(cramp.outputs["Color"], cb.inputs["Emission Color"]); cb.inputs["Emission Strength"].default_value = 0.45

ctex = bpy.data.textures.new("CloudPuff", 'CLOUDS'); ctex.noise_scale = 1.6
clouds = bpy.data.collections.new("Clouds"); scn.collection.children.link(clouds)
def cloud(cx, cy, cz, w, h, n=16, core=True):
    mb = bpy.data.metaballs.new("CloudMB"); mb.resolution = 0.5
    if core:
        e = mb.elements.new(); e.type = 'ELLIPSOID'; e.radius = 2.0
        e.size_x, e.size_y, e.size_z = w / 2, 1.5, h / 2
    for _ in range(n):
        e = mb.elements.new()
        e.co = (random.uniform(-w / 2, w / 2), random.uniform(-1.5, 1.5), random.uniform(-h / 2 + 0.5, h / 2 + 1.5))
        e.radius = random.uniform(2.6, 4.2)
    o = bpy.data.objects.new("Cloud", mb); clouds.objects.link(o); o.location = (cx, cy, cz)
    bpy.context.view_layer.objects.active = o
    for ob in bpy.context.selected_objects: ob.select_set(False)
    o.select_set(True); bpy.ops.object.convert(target='MESH'); o = bpy.context.object
    d = o.modifiers.new("Puff", 'DISPLACE'); d.texture = ctex; d.strength = 1.4; d.mid_level = 0.5
    bpy.ops.object.shade_smooth(); o.data.materials.append(cloudm)
    dx = random.choice([-1, 1]) * random.uniform(0.6, 1.4)
    for fr, off in [(1, 0), (LOOP // 2 + 1, dx), (LOOP + 1, 0)]:
        o.location.x = cx + off; o.keyframe_insert("location", frame=fr)
    for fc in fcurves(o):
        for k in fc.keyframe_points: k.interpolation = 'SINE'; k.easing = 'EASE_IN_OUT'
        fc.modifiers.new('CYCLES')
    return o
cloud(0, -17, 36, 24, 12, 30)                        # main bank that swallows the logo
cloud(1, -19, 42, 14, 3, 12, False)
cloud(-20, -14, 30, 18, 6, 18); cloud(17, -14, 35, 16, 6, 16)
cloud(-42, -10, 25, 20, 5, 16); cloud(42, -10, 26, 20, 5, 16)
cloud(-64, -6, 22, 16, 4, 12, False); cloud(64, -6, 23, 16, 4, 12, False)

# ---------- night sky, moon light, camera at the lake ----------
w = bpy.data.worlds.new("Night"); scn.world = w; w.use_nodes = True
wn = w.node_tree.nodes; wl = w.node_tree.links
bg = wn["Background"]; bg.inputs["Strength"].default_value = 1.0
tcw = wn.new("ShaderNodeTexCoord"); sepw = wn.new("ShaderNodeSeparateXYZ"); ramp = wn.new("ShaderNodeValToRGB")
wl.new(tcw.outputs["Window"], sepw.inputs[0]); wl.new(sepw.outputs["Y"], ramp.inputs["Fac"])
r = ramp.color_ramp
r.elements[0].position = 0.35; r.elements[0].color = (0.025, 0.05, 0.16, 1)
r.elements[1].position = 1.0; r.elements[1].color = (0.004, 0.008, 0.04, 1)
wl.new(ramp.outputs["Color"], bg.inputs["Color"])

moon = bpy.data.lights.new("Moon", 'SUN'); moon.energy = 0.4; moon.color = (0.6, 0.7, 1.0)
mo = bpy.data.objects.new("Moon", moon); scn.collection.objects.link(mo); mo.rotation_euler = (math.radians(55), 0, math.radians(-30))
glow = bpy.data.lights.new("CityGlow", 'AREA'); glow.energy = 0; glow.size = 150; glow.color = (1.0, 0.6, 0.3)
go = bpy.data.objects.new("CityGlow", glow); scn.collection.objects.link(go); go.location = (0, 10, 2)   # area light points down by default -> flip up
go.rotation_euler = (math.pi, 0, 0)

# ---------- camera: new 3/4 angle from out on Lady Bird Lake, slow push-in onto the logo ----------
cam = bpy.data.cameras.new("Cam"); cam.lens = 32
cam.dof.use_dof = True; cam.dof.focus_object = logo; cam.dof.aperture_fstop = 0.2
co = bpy.data.objects.new("Camera", cam); scn.collection.objects.link(co); scn.camera = co
aim = bpy.data.objects.new("CamAim", None); scn.collection.objects.link(aim)
tc_ = co.constraints.new('TRACK_TO'); tc_.target = aim; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
cam_keys = [(1, (-42, -150, 5)), (90, (-22, -95, 8)), (LOOP, (-3, END[1] - 19, END[2] + 0.8))]
aim_keys = [(1, (6, 0, 24)), (90, (2, -15, 22)), (LOOP, (END[0], END[1], END[2] - 0.3))]
for fr, loc in cam_keys:
    co.location = loc; co.keyframe_insert("location", frame=fr)
for fr, loc in aim_keys:
    aim.location = loc; aim.keyframe_insert("location", frame=fr)
for ob in (co, aim):
    for fc in fcurves(ob):
        for k in fc.keyframe_points:
            k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
cam.keyframe_insert  # lens stays fixed; the push-in is a physical dolly

scn.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/antler_vc_austin.blend")
