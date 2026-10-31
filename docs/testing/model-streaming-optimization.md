# Full-resolution model loading: next physical trial

The renderer changes in this receipt preserve the original model geometry, image resolution, colour handling, sampler settings and material equations. The display and screen orchestration are owned separately. This work changes only `object_scene.cpp/.hpp`, focused renderer tests and this diagnostic note. Caption backend files remain unchanged from their verified handoff.

## What the installed build actually showed

The read-only console capture is `build/performance-review-ready04/session.log`. It belongs to the previous installed build, before one-atlas decoding and immutable texture storage. Around the Game Boy selection, lines 560–580 show CPU direct allocations reaching a 910 MiB peak without CPU-allocation refusals. The largest free physical range then fell to 139 MiB. The graphics driver refused a 156,631,040-byte allocation with `rc=80020023`. This is concrete shared physical-memory pressure, not proof that the Game Boy geometry is too complex.

The same capture later reports approximately 59.94 fps while no model is visible, with draw time around 15.9 ms and swap around 0.68 ms. Those CPU sections can include presentation pacing or waits and cannot be read as isolated GPU work. Earlier model GPU samples and the new request for a 120 Hz display require separate interpretation. This receipt makes no 120 fps claim.

## Changes prepared locally

- One worker already decodes and prepares one original-resolution atlas at a time. The new implementation retains this path and its immutable mip storage; it does not restore the former many-atlas CPU staging or repeated texture-growth path.
- Equivalent OpenGL sampler states now share a single sampler object within a model. The Game Boy's five mesh draws require one distinct sampler rather than 25 separately created equivalent handles. Authored filtering and wrap settings remain distinct when they differ.
- Deferred deletion releases the large texture allocations first. Previously the LIFO queue deleted small sampler handles ahead of the atlases, delaying memory recovery. Deletion remains limited by a four-object / approximately two-millisecond scheduling slice.
- A request remains logically loading through CPU completion, deferred retirement and staged GPU upload. It no longer briefly reports neither loading nor ready at the handoff. Errors, completion and cancellation terminate the loading state explicitly.
- No additional upload or allocation is started after the scheduling slice is already exhausted. Transfers retain the 2 MiB per-call ceiling; their individual chunks adapt between 64 and 512 KiB according to measured CPU submission time. Source pixels and geometry are unchanged.

An individual driver allocation or deletion cannot be interrupted halfway through a GL call. Consequently the two-millisecond value is a scheduling budget, **not a hard execution-time guarantee**. Immutable allocation and deletion are now timed explicitly so the next console capture can distinguish that remaining risk from row copying, worker decoding and actual rendering.

## Actual renderer checks

All figures below come from desktop Mesa **llvmpipe**, which implements GPU storage and drawing in software. They are useful correctness and allocation diagnostics, not PS5 performance estimates.

| Property | Original Game Boy master | Nintendo 3DS master |
| --- | --- | --- |
| Rendered target | 3840 × 2160 | 1766 × 1177, actual hero target |
| Geometry | 16,319 vertices / 18,182 triangles / 5 draws | 4,658 vertices / 4,581 triangles / 7 draws |
| Source maps | Eleven 4096 × 4096 atlases | Three 2048² and nine 512² atlases |
| Encoded model | 128 MiB, rounded | 4 MiB, rounded |
| Peak retained decoded atlas plus mips | 85 MiB | 21 MiB |
| Estimated model GPU storage including mips and geometry | 940.00 MiB | 76.37 MiB |
| Largest staged upload tick | 2,097,152 bytes | 2,097,152 bytes |
| Distinct sampler objects | 1 | 1 |
| Largest measured row transfer in first load | 0.75 ms | 0.79 ms |
| Largest immutable/buffer allocation in first load | 82.01 ms | 20.91 ms |

The Game Boy's repeat/cancel/reload pass also recorded a 107.48 ms software allocation and deletion calls up to 6.77 ms. This is why the scheduling limit must not be described as a guaranteed frame-time ceiling. The 3DS's first upload tick reached 28.23 ms despite its smaller maps. Both models completed real rendering, two poses, GL-state preservation, partial-upload cancellation, latest-request replacement and deferred deletion checks without a GL error or assertion failure. After model retirement, estimated model residency returns to zero while the reusable render target remains accounted for.

The Game Boy source remains byte-identical: SHA-256 `8d60dde415190d24216890b65032db7e8a87d724e63a68f9578ca1c538d2417e`. Its captures are `models/game-boy.glb-0.png` and `models/game-boy.glb-1.png`, both actual 3840 × 2160 renderer output. The first pose was visually inspected for preserved lettering, cartridge artwork and surface detail. The 3DS receipt is `build/object-scene-3ds-performance.log`.

The final neutral suite passed 38 synchronous and 38 streamed pixel/material cases, including authored sampler-state distinctions and sampler reuse. `build/object-material-final.log` is the receipt. The actual 4K coverage-AA test passed both the neutral-alpha and sharp-artwork cases: each retained 1,061,196 exact opaque pixels while antialiasing 8,252 silhouette pixels. That test aborts if a framebuffer blit or multisample allocation is attempted.

## New diagnostic fields and trial focus

`Timings` exposes `last_storage_ms`, `max_storage_ms`, `max_transfer_ms`, `max_delete_ms`, `storage_calls`, `transfer_chunk_bytes`, `estimated_gpu_bytes` and `peak_estimated_gpu_bytes`. `Stats::sampler_objects` reports actual shared sampler handles. The GPU estimate counts image mip chains, geometry and the reusable colour/depth/coverage targets; it excludes driver alignment, unrelated UI assets and temporarily retained resources inside the driver. It is not a physical free-memory query.

The console log now prints allocation time and current estimated model storage for each `3D atlas` line. A `3D slow retirement` line identifies any individual deletion above four milliseconds. A `3D geometry allocation` line identifies an unusually slow geometry-allocation block. Existing stage text distinguishes original-model reading, atlas decoding, atlas upload and readiness. GPU timer queries remain nonblocking and no `glFinish`, readback, compression, texture downsampling or model-specific shader path has been introduced.

For the next PS5 trial, verify the accepted display rate separately, load the unchanged Game Boy master, navigate away during loading and return, then compare allocation/retirement logs and actual GPU times. In particular, confirm that the old 156 MiB growth allocation and 910 MiB CPU peak no longer recur and that failure remains readable if the driver's remaining pool is insufficient. The final native build is coordinated by the parent task. No console executable or payload was modified by this work.
