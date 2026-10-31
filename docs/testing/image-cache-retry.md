# Image cache: temporary HTTP failures

The image worker now allows three automatic retries after HTTP 429, 500, 502, 503
or 504, after 5, 20 and 60 seconds respectively. This is a capped exponential policy;
the fourth failed response ends automatic attempts. HTTP 501, 505, 511 and unknown
status codes are deliberately excluded, as are transport errors, bad image data,
texture-upload failures and document/model downloads.

Only URLs in `RemoteCache::set_visible()` are eligible for automatic dispatch.
Removing a photo pauses its retry; revisiting it permits a due retry without
resetting its attempt counter. An empty visible list permits no retries. One
worker performs all transfers. Automatic dispatches are separated by at least
one second, and a failing image places its origin on the same cooldown, including
other queued initial image requests. Other origins remain available. Cooldown
metadata is bounded to 64 origins. Manual `retry()` resets the per-image attempt
budget but still honours that origin's cooldown.

The worker waits on a condition variable and wakes for deadlines or actual
visibility changes; unchanged per-frame pin lists do not wake it. No retry timer,
network request or sleep runs on the frame thread. HTTP error bodies never enter
the persistent image cache. Existing 12 MiB encoded-image, 4096 long-edge / 16 M pixel,
64 MiB pending and 96 MiB resident texture limits are unchanged.

The HTTP transport currently returns status/body/error, without response headers.
Consequently this change cannot read or claim to honour `Retry-After`. Supporting
that header needs a separate transport change. The rate-limit classification is
grounded in [RFC 6585 section 4](https://www.rfc-editor.org/rfc/rfc6585#section-4);
the finite delays above are an application policy, not a server guarantee.

## Verification

`bash tests/image-quality/retry.sh` passed against the real worker and an offline
HTTP adapter. Checks include the full 5/20/60 second policy with a logical clock,
three-retry exhaustion, real 5 second 429 recovery, origin-wide cooldown, an
unrelated healthy origin, hidden-photo suspension/re-entry, 404 and decoder-error
exclusion, document exclusion, 10,000 repeated requests without a retry storm and
shutdown interrupting the next 20 second wait in under 500 ms.

`bash tests/image-quality/run.sh` passed the existing image-quality and real EGL
texture-residency regressions: original 4096 square photo retained, 96 MiB pressure,
priority/LRU eviction and no repeated decoding for a deferred background photo.

`bash tests/image-quality/retry-native.sh` compiled the production worker with
the PS5 target, C++20, `-fno-exceptions`, `-fno-rtti` and warnings as errors. It
writes an isolated object and does not link, stage or replace any application.
Logs are `build/photo-retry-test.log`, `build/photo-quality-regression.log` and
`build/photo-retry-native.log`. No console deployment or live PS5 claim is made.
