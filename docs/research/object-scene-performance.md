# Native object loading and performance instrumentation

The first PS5 slice exposed UI stalls during3D loading and continuous orbit. No PS5 performance claim can be derived from successful host rendering. The app's session log was not retrievable during this audit because its download sandbox had already unmounted; the persistent download0.dat was left untouched.

The former asynchronous CPU loader still submitted a whole4K atlas plus driver-generated mipmaps in one UI call, then uploaded every geometry buffer together. A64MiB image could therefore cause a large upload and mip-generation stall. Cancelling a selection also destroyed potentially gigabytes of prepared CPU pixels on the UI thread. These are explicit blocking points even though source reading/decode already used a worker.

The application request/upload path now:

1. Reads, decodes and preserves original geometry/images on its existing serial worker. Cancellation is checked before image decode and periodically while traversing vertices.
2. Builds mipmaps only for the current atlas on that worker. sRGB colour mips average in linear light; normal/MR/AO data remain linear. A shared colour/data source gets independent mip semantics. Base image bytes and original resolution are retained. Only current-atlas mip storage is added, rather than another full-model mip pyramid.
3. Uploads texture rows in calls of at most512KiB, at most2MiB total per tick. Work stops after a nominal2ms CPU submission budget between calls. Geometry allocation and sub-buffer uploads are similarly staged. A single driver allocation cannot be preempted and can exceed2ms; byte/time limits are not a promise of a hard driver latency bound. At least one bounded chunk progresses even when state-query overhead consumes the nominal time budget.
4. Destroys cancelled/completed CPU Readers and mip buffers on the worker, outside the handoff lock. A new selection supersedes earlier work; partially staged objects are never exposed as ready.

The synchronous `load()` inspection/test path remains explicitly blocking; the application uses `request()` and `upload_pending()`.

`ObjectScene::timings()` is a main-thread diagnostics API. It reports read/decode and current-mip worker time, last/peak upload CPU time, bytes per tick, target allocation, render submission, and resource retirement. Four nonblocking GL_TIME_ELAPSED queries expose last/peak GPU milliseconds plus sample/rejection counts when supported. Results are fetched only after GL_QUERY_RESULT_AVAILABLE; there is no glFinish or query-result wait. A duration longer than the wall interval since submission is rejected, protecting cadence from an observed impossible first llvmpipe result. Unsupported query counters disable timing rather than rendering.

Validation:

-38 neutral material fixtures pass both synchronous and asynchronous loading (76 checks), including minified sRGB checker, all previously supported factors/maps, explicit unsupported-map errors and malformed data.
- Actual PSP1766x1177 and Switch3840x2160 render/state tests pass. Original geometry counts and visible coverage are retained. Cancellation after real partial row uploads successfully hands off to a new selection. Each tick asserts the2MiB submission bound.
- Native strict no-exception/no-RTTI compilation passes. Actual SDK archives define all timer/staging functions.
- Host llvmpipe, indicative only: PSP current-atlas mip preparation148ms on worker; largest upload tick52.5ms including driver allocation, hero target allocation29.9ms, valid GPU render20.27ms. Switch full4K target allocation189.8ms, valid GPU render89.82ms. These measurements are not PS5 frame rates.

The earlier trial used faithful original texture resolution,4x MSAA for hero-sized targets and2x at full4K, three neutral GGX lights and a full-resolution straight-alpha/sRGB resolve. Its MSAA path is superseded by the console-driven correction below. No tiny render target, texture downsampling or shader material shortcut was introduced. Stable target dimensions, retained frames, skipping hidden rendering and measured orbit cadence are Screen responsibilities. Actual PS5 driver timing and memory residency remain necessary before promising sustained responsiveness or a particular frame rate.

## Leaving a hardware exhibit

`ObjectScene::cancel()` increments the request generation, clears queued CPU requests, moves pending Readers/mip buffers to worker retirement, and moves GPU names to a deferred deletion list. It performs no GL deletion on the input path. `upload_pending()` drains at most four GPU handles per tick, stopping between calls after the nominal2ms budget, even when there is no current model. The owner must therefore call it globally after cancellation. The one retained render-target set is a bounded reusable cache; heavy model textures/buffers/samplers are retired. Shutdown drains all remaining handles. A regression test checks immediate non-ready/non-loading state and at most four deletes per tick until retirement completes.


## PS5 software-resolve correction (20 October 2026)

The actual trial log `build/startup-investigation/session-live.log` shows two independent costs: the screen compositor's 3840x2160 software framebuffer blit takes roughly508?524ms per frame, while the3DS object's4x multisample resolve at1766x1177 adds roughly565?582ms whenever rendered. The3DS contains4581triangles in7draws. The log itself reports157.69ms CPU read/decode and at most1.44ms per2MiB staged upload. Loading takes many wall-clock seconds because a2fps interface can make only two staging calls per second; this is not evidence of a blocked decode worker.

ObjectScene now renders into a full requested-size, single-sample sRGB texture with a depth buffer. One GPU triangle samples that texture and writes the returned full-size RGBA texture. No framebuffer blit, multisample renderbuffer or CPU resolve occurs in this component. Original model geometry, material maps, texture dimensions and viewport dimensions are unchanged. At3840x2160 the two colour targets plus nominal32-bit depth require about94.9MiB, compared with about189.8MiB for the former2x-MSAA path; at1766x1177 it is about23.8MiB versus79.3MiB for4xMSAA, excluding driver overhead.

Antialiasing is a silhouette-only post process. A changing coverage alpha determines the local edge normal; two half-pixel bilinear taps smooth that edge in linear premultiplied colour before straight-alpha sRGB output. A fully opaque neighbourhood retains the exact centre sample, so internal logos, lettering and colour-map detail are not globally blurred. This is not geometric multisample coverage, does not reconstruct subpixel geometry, and does not claim to antialias internal opaque material edges. It avoids introducing a speculative multisample-texture backend dependency during an urgent compatibility fix.

Verification:

- Actual native strict syntax passed with no exceptions, RTTI or warnings.
-76 real OpenGL neutral-material checks still pass through both synchronous and worker-staged loading.
- `tests/object-scene/post-aa.sh` interposes `glBlitFramebuffer` and `glRenderbufferStorageMultisample` with aborting hooks: neither is called. It checks actual3840x2160 returned texture dimensions,8252partial-alpha silhouette pixels, and1061196opaque pixels that preserve exact nearest-sampled red/blue artwork; neutral-colour fringe pixels retain their colour without dark halos.
- The actual3DS GLB renders at1766x1177 with the same4658vertices/4581triangles/7draws and59,768,832decoded texture bytes. GL state restoration, cancellation, bounded retirement and2MiB upload-byte limits pass. Host llvmpipe measured9.26ms GPU for the retained second angle; this is a desktop diagnostic, not a PS5 performance result.

A new console trial must verify that both software-blit and msaa-resolve diagnostics disappear and measure the resulting real UI/model cadence. A single driver allocation may still exceed the nominal2ms staging budget; byte chunks remain bounded and original image resolution remains intact.
