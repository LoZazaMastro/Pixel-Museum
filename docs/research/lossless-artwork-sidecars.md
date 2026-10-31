# Lossless artwork sidecars

Only the original Game Boy and selected PlayStation assembly have optional offline sidecars. Run `python tools/prepare-model-artwork-cache.py` to regenerate them through the actual renderer's decoder and mip generator. It checks the unchanged GLB SHA-256, writes complete sidecars atomically, and updates source-bound model records. Other models continue using embedded original artwork.

The read-only runtime accepts a sidecar only when its format, source image fingerprint, original dimensions, material channel union, mip count, offsets and bounds match. The small table has its own integrity checksum; every independent Zstandard frame requires a content checksum verified by the reference decoder. Bad or absent caches fall back to the original PNG. Cached source pixels and every colour/data mip match the original path byte for byte. Channel packing happens afterwards and retains the existing RGBA fallback.

The two files add about 354.54 MiB. One decoded atlas is staged at a time, with no extra retained GPU model. Exact byte comparisons cover 24 canonical original atlases; real GL tests cover cached filtering/wrap/mips, channel unions and forced compact-format failure. Packaging checks source SHA-256, sidecar SHA-256, size, format and safe paths before copying.

Host WSL measurements reduced the checked artwork CPU path from about 3.24 to 1.98 seconds for Game Boy and 2.29 to 1.42 seconds for selected PlayStation. Real disk reads and checksums make this slower than the isolated in-memory zstd benchmark. Original upload payloads remain 896 and 778.67 MiB after channel packing, so 2 MiB display-frame transfers still need at least 448 and 390 ticks. These are not PS5 loading-time, frame-rate or instantaneous-loading claims. Console memory and timing verification remains required.

Sources for checksum/API contracts: https://github.com/facebook/zstd/blob/v1.5.7/lib/zstd.h and https://github.com/facebook/zstd/blob/v1.5.7/doc/zstd_compression_format.md .
