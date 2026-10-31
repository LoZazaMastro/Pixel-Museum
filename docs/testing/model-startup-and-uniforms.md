# Model startup and inactive material uniforms

The lossless artwork sidecars remove repeat PNG decoding, but they cannot make large GPU allocations asynchronous. Existing controlled 4K host results for the admitted PS5 and Wii U GamePad show:

| Cached source, cold GPU | PS5 | GamePad |
|---|---:|---:|
| Source read + parse/identity, worker | 243 ms | 272 ms |
| Checked sidecar read/decompression, worker | 718 ms | 826 ms |
| Residual mip/material preparation, worker | 64 ms | 103 ms |
| GL immutable allocation, main thread sum | 296 ms | 232 ms |
| Largest single texture allocation | 60 ms | 62 ms |
| GL staged row transfers, main thread sum | 81 ms | 56 ms |
| Request to ready, including fixture sleeps | 1982 ms | 1934 ms |
| Conservative model residency | 1031 MiB | 854 MiB |

These are software OpenGL host measurements, not PS5 frame-rate or physical-memory measurements. The existing 512 MiB neighbour-cache admission excludes these large models. Atlas work is on the worker, while GL allocation/transfers and render submission remain on the main/context thread. A 1.5 ms budget can stop before the next GL call but cannot interrupt an already executing `glTexStorage2D`, `glDeleteTextures`, or first render-target allocation. The measured transfer chunk cap and original 4K source pixels remain unchanged.

Two bounded improvements address avoidable work:

* `Screen::initialize_object_programs()` initializes the active scene and both owned prepared scenes during startup. The first neighbour upload therefore does not compile another identical shader in a navigation frame. Programs retain their existing per-scene ownership. A prepared shader failure is logged, all prepared program resources are released, and background GPU caching is disabled while the active scene remains usable. The real Screen regression injects an invalid GLSL prefix only after the active program is initialized, checks failure/cleanup with GL errors clear, then restores the prefix and reinitializes successfully.
* Materials with no restoration region reset `restoreCounts` but skip unused region/detail/ink/colour uploads. Restored materials still upload their actual used values. Counts always reset after a restored material, preventing stale PS3/PS4 restoration state from affecting later originals. No source image, mip, shader equation, geometry or material value changes.

`tests/object-scene/unused-uniform-probe.sh` creates isolated baseline/guarded renderer translation units and checks exact PNG bytes for two actual 3840×2160 angles of PS5, GamePad and the restored PS3. All six pairs match, and existing GL-state, cancellation and cache/revisit checks pass. Twenty warm measured submission frames per model show:

| Host sample | Baseline vec4 calls/frame | Guarded | Baseline CPU mean | Guarded CPU mean |
|---|---:|---:|---:|---:|
| PS5 | 125 | 25 | 25.03 ms | 20.58 ms |
| GamePad | 10 | 2 | 18.30 ms | 16.73 ms |
| Restored PS3 | 30 | 12 | 11.57 ms | 11.84 ms |

This single bounded host comparison proves fewer redundant calls and exact output preservation; the PS3 timing variation also demonstrates why it does not establish a universal frame-rate improvement. Physical PS5 validation remains required. The raw comparisons, counters and hashes are under `build/research/model-uniform-probe/`.

The next substantial latency target is the per-call driver allocation cost, followed by source/sidecar worker preparation. Increasing the byte cap or retaining both huge consoles simultaneously would not remove that allocation cost and risks the previous OOM. The current one-atlas staging bound must be preserved before considering any predictive CPU preparation.

An additional bounded preparation improvement checks exact uniformity before allocating packed material mip copies. The original RGBA base and all existing mips are still checked byte-for-byte and retained for unsupported-format fallback. Only an already proven uniform material view packs one sampled texel instead of a full redundant chain. The PS5 source's constant 4096-square ORM job therefore avoids 44,739,240 CPU bytes (42.67 MiB); its retained original RGBA/mip bytes remain 89,478,484. Prepared vectors for that job fall from approximately 128 MiB to 85.33 MiB. This does not reduce GPU residency or the peak of every other non-uniform atlas job.

`tests/object-scene/uniform-packing-probe.sh` compares isolated source variants before production admission. Five host worker preparation samples averaged 74.575 ms before and 31.667 ms after; these are bounded CPU preparation samples, not total model loading or physical PS5 timing. PS5 and GamePad each retain identical PNG bytes at two actual 3840-by-2160 angles. Production material checks pass all 92 cases in original-RGBA, staged-compact and forced compact-format-failure modes, including 18 cache-backed full-image shader comparisons. Cancellation, immutable-source mutation rejection and cache/revisit checks remain passing. `build/research/uniform-packing-probe/verification.json` records source/sidecar hashes, sample values, output hashes, the matching native compilation and the remaining limits. Deployment requires that matching binary and coherent font/catalogue checkpoint.
