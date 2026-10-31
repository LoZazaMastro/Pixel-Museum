# Photographic media quality and memory bounds

The remote photo path retains genuine source detail up to a4096-pixel longest edge, without enlarging smaller originals. An incoming3840x2160 photograph remains3840x2160. Larger accepted sources are reduced once on the worker with exact pixel-area integration in linear light and premultiplied alpha; no nearest-neighbour decimation, artificial sharpening or generated enlargement is used. The display texture uses linear sampling. `Asset.source_width/source_height` preserve original decoded dimensions; `width/height` describe retained GPU pixels.

Limits:

| Resource | Bound |
| --- | --- |
| Encoded image | Strictly below12MiB |
| Source dimensions | At most8192 per side and16,777,216 total pixels, checked before decoder allocation |
| Retained dimensions | At most4096 per side, never larger than the source |
| Single RGBA photo | Up to64MiB for4096x4096;3840x2160 uses33,177,600bytes (31.64MiB) |
| Pending decoded photos |64MiB aggregate, worker applies back pressure |
| One decode/reduction job | At most128MiB concurrent application RGBA buffers, plus encoded input and codec working memory |
| Resident photo textures |96MiB and24textures; no mip-chain allocation |
| Persistent encoded cache |384MiB |

`RemoteCache::set_visible(urls)` sets ordered display priority before upload: active gallery photograph first, then other actually visible images. Background uploads cannot evict a higher-priority visible photograph. Under budget pressure an inactive/lower-priority photo is deferred, rather than re-decoded every frame. Once it becomes the primary photo it can replace older textures. Pending uploads choose visible/recent media before older background work. These bounds cannot keep an unlimited gallery resident; missing lower-priority images wait rather than displacing the current photograph. Existing callers without visibility hints retain ordinary recent-use eviction.

Tests exercise actual encoded4K/oversized/small sources, exact detail retention, source metadata, linear-light area averaging, alpha correctness, fractional reduction and input rejection. An offline real-worker/real-GL test pins a64MiB photo while filling the96MiB budget, checks lower-priority eviction, checks deferred requests stay idle, and then changes the active photograph. Native strict no-exception/no-RTTI syntax checks cover both photo preparation and cache implementation. GPU driver allocation overhead and upload timing still require console measurement.
