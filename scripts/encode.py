import bpy, os
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
s.render.fps = 30
d = "/home/agent/antler/frames/"
files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
ed = s.sequence_editor_create()
coll = ed.strips if hasattr(ed, "strips") else ed.sequences
st = coll.new_image("frames", d + files[0], 1, 1)
for f in files[1:]: st.elements.append(f)
s.frame_start, s.frame_end = 1, len(files)
im = s.render.image_settings
if hasattr(im, "media_type"): im.media_type = 'VIDEO'
im.file_format = 'FFMPEG'
ff = s.render.ffmpeg
ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.ffmpeg_preset = 'GOOD'
s.render.use_sequencer = True
s.render.filepath = "/home/agent/antler/antler_vc_austin.mp4"
bpy.ops.render.render(animation=True)
