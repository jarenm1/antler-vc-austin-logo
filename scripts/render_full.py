import bpy
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
s.eevee.taa_render_samples = 32
s.render.image_settings.file_format = 'PNG'
s.render.filepath = "/home/agent/antler/frames/f_"
bpy.ops.render.render(animation=True)
