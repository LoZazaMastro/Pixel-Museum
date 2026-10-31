# Active local photo priority

Cold packaged selections now upload their real local preview first. The full original master is decoded asynchronously, with the preview retained until every master row reaches a private texture. A missing or corrupt optional preview falls back to the installed original. Source identity, original dimensions and the existing4096-edge/16M-pixel retention policy are unchanged.

A newly active request can displace a lower-priority queued image even if sixteen old jobs filled the queue after the last visible-list reorder. Completed background textures remain resident under the existing budget. An incomplete lower-priority upload may be cancelled instead of pinning64MiB of staging in front of the newly focused image. This is temporary priority deferral: neighbour preview warmup resumes after the primary finishes, while the separate memory/LRU deferral still prevents re-decode thrashing.

The actual EGL/worker suite verifies queue ordering, cancellation of an old private4K upload, uninterrupted preview-to-master promotion, all4096?RGBA pixels, corrupt-preview fallback, neighbour resumption and the existing cache/model-pressure regressions. Transfers stay at2MiB and one texture job per frame; GPU/pending budgets are not raised.

The final host run displayed the synthetic packaged preview after14.17ms with zero further old4K chunks. A real local Nintendo JPEG1804?1295 read/decoded in47.96ms and needed five bounded upload ticks, showing its complete master after115.62ms with16ms tick spacing. These are host observations, not PS5 promises. An already running decoder or indivisible driver allocation cannot be interrupted.

Run `MUSEUM_PHOTO_PROBE=assets/images/28df6e8ce9d9618659a62d06.jpg bash tests/image-quality/run.sh`. The optional real-photo probe can be omitted on checkouts without that packaged asset. Receipts and full log: `build/research/model-clean-materials/active-photo-cache-verification.json` and `active-photo-cache-regression.log`.
