# Exact constant atlases

The PS5 asset contains one 4096×4096 ORM map whose every RGBA texel is exactly 255. The other admitted PS5 and Wii U GamePad maps have no decoded-identical images or additional fully constant maps. `tools/audit-model-atlas-memory.py` records original pixel hashes, channel extrema and material bindings without modifying any source.

The asynchronous artwork worker now checks exact RGBA equality, including alpha and every existing mip level. Only a proven constant role is uploaded as a 1×1 equivalent. All sampled values stay identical under authored UVs, wrap modes, magnification, minification and mip filtering. A single byte difference refuses the optimization. There is no approximate threshold, texture resampling, normal reconstruction or source/material/shader edit. The original GLB and lossless sidecar pixels remain unchanged. Cancellation checks bound the scan; normal lifetime, format fallback and retirement paths remain in use.

For the selected PS5 model this removes 44,739,240 logical RG8 mip bytes, reducing conservative GPU accounting by approximately 85.3 MiB (1,116 to 1,030 MiB excluding the render target). The remaining maps retain their original dimensions and precision. That accounting intentionally reserves twice the logical storage because earlier physical PS5 traces showed tiled allocation overhead. It is not a fresh measurement of the console driver's allocation. This model still exceeds the adjacent GPU cache budget; the fix does not make a cold load instant.

Verification:

- `tests/object-scene/materials.sh`: 92 original cases in synchronous, staged and simulated compact-format-failure modes. Twenty-seven new cases cover constant colour/ORM/normal/AO unions, alpha, repeat/clamp/mirror, nearest/linear/trilinear filters, off-axis views and real minification/magnification. Their optimized shader output matches the full-resolution original exactly. A one-code-value difference stays uncollapsed.
- `tests/object-scene/uniform-real-parity.sh`: two actual 3840×2160 poses each for PS5 and GamePad, compared byte-for-byte with a reference translation unit that disables only the constant-map path. All four PNGs are identical. Ready-cache swap/revisit, GPU retirement and 32 request cancellations also pass without GL errors.
- `tests/object-scene/cache-parity.sh playstation-5 wii-u-gamepad`: all 13 source RGBA/mip/packed atlases and uniform decisions match the lossless sidecars. Invalid cache versions, source identities, corrupt payloads and truncation still fall back to the original PNG.

Logs and receipts: `build/research/model-memory-audit/`. Host timings remain scheduler-dependent and do not establish physical PS5 latency or frame rate. No console transfer was performed.
