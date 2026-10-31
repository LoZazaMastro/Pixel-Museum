# Native startup and compositor audit

This review uses the actual console log and local production source. It does
not claim that an offscreen host run proves console frame rate.

## Console evidence

`build/startup-investigation/session-live.log` records a clear change in cost:

- The first-visit view initially runs at approximately 59.6–59.95 FPS. Update
  time is usually below a millisecond; drawing is approximately 15.7 ms.
- The collection view repeatedly emits
  `[ps5-gallium] software-blit color=3840x2160->3840x2160 filter=0`.
  Its steady draw mean is approximately 516–518 ms, producing 1.9 FPS.
- Independently, the model emits `msaa4-resolve color=1766x1177`. These model
  updates reach approximately 565 ms and combined frames reach 1,080 ms.
- That same model reports 157.69 ms file/decode time and maximum 1.44 ms staged
  uploads, limited to 2 MiB per tick. Loading appears to take many seconds when
  each tick is already separated by a half-second compositor stall. The log
  does not support treating GLB decoding as the dominant continuing stall.

The old `Screen::draw` performed a full-resolution framebuffer blit every
settled collection frame. The old `snapshot_current` used the same call on
navigation. Those are distinct from the object's MSAA framebuffer resolve.

The linked SDK is
`F:/Playhub/PS5/CD Player/.deps/ps5-opengl/ps5-opengl-sdk-1.0.2/sdk/lib/libPS5OpenGL.a`,
as recorded in `.deps/ps5-opengl/ps5-opengl.ld`. The installed SDK contains
headers, static archives and notices, but no local Gallium backend C source was
found. Accordingly, the precise internal CPU-copy implementation cannot be
cited from a checked-out source file. The backend's own `software-blit` trace,
the matching application call sites and console timings are the evidence for
this fix. No browser research or viewer extraction was used.

## Current transfer paths

- `src/museum/screen.cpp`, `Screen::draw`: the complete scene is rendered into
  a single-sample canvas and sampled by the existing GPU image batch. The
  settled and dissolving views both use this path. The first-visit welcome and
  fully open, opaque experience render directly without preparing an unseen
  collection underneath.
- `src/museum/media_scene.cpp`, `Screen::snapshot_current`: a GPU image draw
  copies `composed_` into a distinct `previous_entry_` target. If another
  navigation step interrupts a dissolve, the previous image is first blended
  into `composed_`, so the next snapshot represents the visible combination.
  There is no source/destination feedback texture in either pass.
- `src/gfx/canvas.cpp:101–110`: `Canvas::resolve` still uses a framebuffer blit
  **only when its draw and resolve targets differ**. All museum UI canvases in
  these paths are explicitly created with one sample, so this resolve is a
  no-op. The class's generic default is four samples; future callers must not
  accidentally omit the explicit single-sample argument.
- `src/gfx/canvas.cpp:112–132`: `save_region` calls `glCopyImageSubData`, after
  `resolve()`. It does not call `glCopyTexImage` or explicitly read pixels to
  CPU memory. There are no museum call sites for `save_region`; it is not the
  present hot path. With no backend source, no assertion is made about every
  possible driver implementation of that copy operation.
- `src/gfx/renderer.cpp`, `capture_glass`: panel blur replays the queued scene
  into a 480×270 single-sample target and performs GPU blur passes. It does not
  read a 4K image to the CPU. Queued draw lists must remain distinct and alive
  until `present`; the separate `experience_layer_` avoids mutating a queued
  Options/Atlas list when an experience is drawn over it.
- Application source contains no `glReadPixels` or `glGetTexImage` call in the
  production screen/render path. Host screenshot and test reads are explicit
  measurement operations and are excluded from transfer counters.

## Orientation, colour and alpha

`kCanvasUv` is `{0,1,1,-1}` in `src/gfx/draw_list.hpp`; framebuffer textures are
bottom-up and this single inversion places them in the UI's top-down space.
`kFullUv` would invert the presented scene. `GlBatch` samples the texture times
a white tint, with straight-alpha blending (`GL_SRC_ALPHA`,
`GL_ONE_MINUS_SRC_ALPHA`) and independently accumulated alpha. The full scene
has an opaque background, so the copy and interrupted snapshot are opaque;
they do not repeatedly multiply partial alpha. The snapshot uses
`1 - smoothstep(fade_)`, preserving the existing dissolve curve.

## Work still serialized before the first frame

These are real startup work, but are not measured individually by the old log:

1. `main.cpp` opens EGL, then calls `Screen::init` before the first render.
2. `Screen::init` builds renderer programs, reads five font files, parses their
   atlases and uploads five GL textures. Font files total about 6.4 MiB here.
   It then parses the installed catalogue and preferences and initialises the
   video service and object programs.
3. `Music::init` reads and decodes all eight 64-second, stereo 24 kHz Ogg stems
   synchronously, producing exactly 49,152,000 PCM bytes. UI sound-bank loading
   also precedes the first frame.
4. The image cache itself starts a worker thread. Disk pruning, remote HTTP,
   image decoding and resizing happen on that worker, not serially inside
   `Screen::init`. Pending photo GL uploads do run on the frame thread in
   `RemoteCache::upload_pending`; they are a separate potential one-frame
   upload cost, not a repeated framebuffer readback.

The old console log includes shader build durations but no elapsed startup
phase timestamps. It cannot identify a measured percentage of first-frame
delay attributable to fonts, music or catalogue parsing. Stage timestamps in
the next console run should establish that before changing startup ownership.

## Regression verification

Run `MUSEUM_PREVIEW_4K=1 bash tools/preview.sh compositor`.

The host build linker-wraps `glBlitFramebuffer`, `glReadPixels`, `glGetTexImage`
and `glCopyImageSubData`. Counters cover production drawing only; deliberate
test pixel measurements turn counting off. The actual 3840×2160 production
Screen test verifies:

- zero framebuffer blits or CPU pixel/texture reads for first-visit welcome,
  first and settled chronology, an entry fade, three rapid navigation changes,
  Options, Year Atlas, partially opened study, study intro and opaque activity;
- output canvas pixels match source canvas colours, orientation and alpha;
- four asymmetric corner colours survive the real snapshot method;
- a second navigation at half-fade snapshots the combined visible image,
  preserving colour and opaque alpha rather than taking only the new layer.

The test does not benchmark PS5 performance. Object resolve is reviewed and
tested separately by the native renderer agent; no production rendering files
were changed by this audit. No FTP writes, application launch or console state
changes were performed.
