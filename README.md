# Antler VC — Austin skyline logo reveal

A 6-second (180 frames @ 30 fps, 1920×1080) Blender animation: the Antler VC logo drops out of the night sky over the Austin skyline, passes behind a cloud bank resting on the tower tops, and descends toward Lady Bird Lake as the camera slowly pushes in until the logo nearly fills the frame.

![Final frame](previews/frame_0180.png)

## Files

| File | What it is |
| --- | --- |
| `antler_vc_austin.mp4` | Rendered animation (H.264, 1080p30) |
| `antler_vc_austin.blend` | Blender scene (Blender 5.2, EEVEE) |
| `scripts/build_scene.py` | Builds the whole scene from scratch |
| `scripts/render_full.py` | Renders the animation to PNG frames |
| `scripts/encode.py` | Encodes the PNG frames to MP4 with Blender's sequencer |
| `previews/` | Stills at frames 1, 60, 120 and 180 |

## Rebuild / re-render

```sh
blender -b -P scripts/build_scene.py                     # writes /tmp/antler_vc_austin.blend
blender -b antler_vc_austin.blend -P scripts/render_full.py
blender -b -P scripts/encode.py
```

`render_full.py` and `encode.py` write to `/home/agent/antler/`; edit the paths at the top of each script to suit your machine.

## Scene notes

- Skyline as seen from Lady Bird Lake: stylised landmark towers (Austonian, Frost Bank Tower, etc.) with a procedural lit-window facade shader, plus filler mid- and low-rises, a tree line and a reflective lake.
- Logo: red rounded tile with the white Λ chevron (traced from the Antler VC mark) and an "ANTLER VC" wordmark.
- Camera: 3/4 view from the lake, dolly + track to the logo, shallow depth of field focused on the logo.
