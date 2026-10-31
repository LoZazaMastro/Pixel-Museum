# Exact upload-payload sidecar: bounded research proposal

This is a proposal and an isolated CPU probe. The production renderer and v1
sidecars remain unchanged. The grouped SOURCE71 executable/font/catalogue pair
has already passed separately.

## Current measured constraint

The existing PS5 model cache-hit host run reports source read170.82ms,
parse39.22ms, checked sidecar decode621.86ms, residual packing4.35ms,
GL storage220.85ms, and row transfer67.35ms. The largest indivisible GL storage
call was48.85ms. Request-to-ready1638.67ms includes fixture scheduling sleeps.
These are software-GL host measurements, not physicalPS5 timings.

The next image is currently queued only after the previous image finishes
uploading. This intentionally bounds decoded staging to one image. A second
fully decoded image would add85–128MiB and is not proposed.

## Preserve the formats actually used

ObjectScene currently uses sRGB8_ALPHA8/RGBA8, exactRG8 for two sampled linear
channels, or R8 for one sampled linear channel. It does **not** currently upload
RGB565 or RGBA4444. Introducing either would quantize the existing output and is
outside this lossless proposal.

A v2 view could contain exactly the existing upload byte sequence:

* Colour and normal/three-channel data views retain their existingRGBA8 source
  pixels and precomputed mip bytes.
* ORM-only views retain the exactG/B bytes already packed by production; AO-only
  views retain the exactR bytes. Swizzles, dimensions, mip count and sampler
  parameters remain identical.
* A constant view may store one sampled texel only after offline verification
  that **every originalRGBA byte and every existing mip** is exactly constant.
  This is the same uniform collapse already performed by production.
* Opacity is an offline-derived value over the full original base image,
  validated by checksummed source-bound metadata. It must never be inferred from
  the reduced channel set of an unrelated view.

## Isolated measured candidate

`tests/object-scene/sidecar-v2-probe.cpp` reads the actual v1 frames, packs the
sameG/B values without rounding, compresses using the existing Zstd level1 with
content checksums, and compares every directly decoded packed byte against the
current packed bytes. Five CPU samples are taken per mip. No v2 runtime asset is
written.

Results: `build/research/model-sidecar-v2-probe/results.json`.

| View | Current rawRGBA+mips | Exact packed payload | Decode+pack mean | Direct packed decode mean |
|---|---:|---:|---:|---:|
| GamePad atlas1 |89,478,484B|44,739,242B|135.16ms|50.78ms|
| GamePad atlas4 |89,478,484B|44,739,242B|111.04ms|38.28ms|
| PS5 atlas2, uniform |89,478,484B|44,739,242B before constant collapse|70.14ms|22.08ms|

The two nonuniform GamePad views save157.15ms in this isolated CPU decode/pack
measurement and89,478,484 raw decoded bytes over the complete model. Their
compressed payload falls from26,943,712B to20,320,069B, saving6,623,643B.
The existing whole GamePad sidecar is67,427,829B; the corresponding projected
whole sidecar is approximately60,804,186B plus the revised metadata difference.

For one nonuniform job, the current originalRGBA+mips plus packed vectors total
134,217,726B. A direct packed job needs44,739,242B plus compressed input, rather
than simultaneously retaining the original89,478,484B. Peak staging reduction
would therefore be85.33MiB for that job, **subject to implementation and lifetime
tests**. No second job is needed.

The PS5 constant view has also been independently verified constant across all
RGBA pixels/mips. A two-byte constant payload could avoid its full85.33MiB
decode, but that exact constant-v2 loader has not been implemented or timed.
Other PS5 views remainRGBA8; a broad PS5 load-speed improvement is not implied.

GPU allocation sizes, stored texture precision, upload byte caps and the
non-preemptibleGL storage calls are unchanged by this proposal. This does not
solve every navigation hitch or establish instantaneous loading/120FPS.

## Reader/version/fallback contract before implementation

1. Preserve v1 compatibility and recognize v2 by distinct magic/version. Missing,
   unsupported or malformed v2 data falls back to the immutable originalGLB.
2. Bound header bytes, atlas/view/level counts, original dimensions, expected
   exact raw byte count and every payload offset/length before allocation.
   Require the expected bitmask→format/swizzle mapping, never an arbitraryGLenum
   from JSON. Arithmetic must be checked before multiplication/addition.
3. Preserve sourceGLB SHA256, encoded-image identity, original source dimensions,
   mip-algorithm identity and selected roles/channel union in the header.
   Packaging already verifies the sourceSHA256. A stronger runtime full-source
   binding can additionally hash the already-readGLB on its worker, retaining
   its descriptor identity check and avoiding any main-threadIO. Its cost should
   be measured before admission, not assumed free.
4. A Zstd content checksum verifies all decoded payload bytes. Metadata must be
   checksummed too. A changed source/role/channel mask or corrupt frame must
   reject the cache before committing any view.
5. If compactGL allocation/swizzle is unsupported, retire the failed private
   handle and packed staging safely, then requeue **one originalRGBA job** on
   the worker. Do not keep both full representations or decode the fallback on
   the UI thread. Cancellation serial and source identity must remain current.
6. Native endianness must not reinterpret packed numerical words: payloads are
   ordered8-bit component bytes. Header integer encoding must be explicit.
7. Before production: exact current-vs-v2 RGBA screenshot parity at4K/twoangles,
   every relevant material/filter/wrap/mip case, compact-unsupported fallback,
   corrupt/source-changed/truncated metadata, rapidcancel/re-request, cache
   eviction/revisit and peakCPU/GPU accounting. No payload/master edits should
   enter a coherent build until those checks pass.
