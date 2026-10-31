# Heavy console loading: measured lossless changes

The selected PS3, PS4 and Switch2 masters now have optional source-bound Zstandard sidecars containing the exact original RGBA base pixels and existing runtime colour/data mip chains. They add 221.1MiB in total. Source GLBs and embedded texture bytes remain unchanged. The original decode path remains the rollback for an absent, corrupt or version-mismatched sidecar.

The upload scheduler uses measured transfer throughput to raise its per-tick cap from2 to16MiB. A single transfer remains64–512KiB, and CPU walltime stops additional work at the caller's display-frame allowance:18% of the frame, at most2ms (1.5ms at120Hz). Eight real transfer samples are required before growth, growth is limited to2MiB per tick, and a slow previous tick halves the cap. This does not increase the GPU cache or physical-memory budget.

| Model | Earlier host ready | Cache+adaptive host ready | Measured process peakRSS | Post-decode staging |
|---|---:|---:|---:|---:|
|playstation-3|6.16s|2.93s|984.9MiB|85MiB|
|playstation-4|2.79s|1.66s|531.6MiB|21MiB|
|switch-2|4.00s|1.92s|797.3MiB|127MiB|

These are individual host runs with warm filesystem caches and fixture scheduling sleeps. The host software OpenGL renderer stores GPU resources in process RAM, so the RSS values above are real host working-set observations, **not physical PS5 GPU residency**. Source decode falls to zero, but sidecar reads, checksum verification, decompression and transfers remain.

The actual driver-delay fixture injects eight4ms transfers: each delayed frame submits only one chunk and the cap returns to2MiB. The fast path grows above2MiB, and a readback checks every texel of the resulting4K base texture. The full material suite passes64 checks through synchronous, staged and compact-format-fallback paths, including18 complete pixel comparisons. The new sidecars pass47 full-resolution atlas comparisons including all mips and packed sampled channels, with corrupt/version/source rollback.

An unresolved bottleneck is indivisible `glTexStorage2D`: it reached55ms in these host runs. The scheduler can stop subsequent work but cannot interrupt that driver call. The existing conservative GPU backing estimate, admission/retirement gate and large-model photo pressure remain. No arbitrary resolution reduction, larger memory pool, universal neighbour GPU prewarm, instant-loading claim or120FPS claim is introduced. On-console measurements are still required.

## Production Screen framebuffer transitions

`Screen::retain_object()` now tests model-only residency before releasing its framebuffer. A large model that cannot enter the unchanged352MiB neighbour threshold keeps the active target for the next selected console. Cached smaller models still retire their unused targets. Timings expose the actual resident dimensions even after a request resets its load statistics.

The real Screen regression renders at3840?2160 and traverses PS3?PS4?PS3, interrupts a PS4 request with PS3, then caches Nintendo3DS before selecting Pong. Only one3840?1920 object target is created across all model loads. Subsequent renders report zero target-allocation time, and a GL object label proves that normal cache maintenance destroys the small model's target even if its numeric texture name is reused for a photo. All draws/retirement finish with GL0. The first target allocation took roughly50?70ms on the host; this repeated allocation is now avoided, but material upload and driver texture-storage stalls remain. The test uses actual Screen selection/update/draw, not merely isolated ObjectScene swaps.

Receipts: `build/research/model-clean-materials/screen-fbo-transition-verification.json` and the adjacent full log. Re-run with `MUSEUM_PREVIEW_4K=1 bash tools/preview.sh model-transitions`.
