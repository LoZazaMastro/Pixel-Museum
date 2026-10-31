# Optional DualSense input: local evidence and limits

The pinned public payload SDK exports `scePadSetMotionSensorState` in
`.deps/native/ps5-payload-sdk/target/lib/libScePad.so`. Its headers do not supply a
typed controller layout. The existing UI adapter already uses a 120-byte sample,
with connection at `0x4c`, timestamp at `0x50` and connection count at `0x68`.

The local GPL-3.0-or-later PSSwanStation reference is
`F:/Playhub/PS5/CD Player/references/PSSwanStation-ps5-port/ps5/src/ps5/pad_ps5.cpp`.
It documents acceleration at `0x1c`, angular velocity at `0x28`, contact count at
`0x34`, and two eight-byte contact records beginning at `0x3c`. It traces this
layout to PSFlyCast and explicitly says that physical PS5 motion readings were
not established. That limitation still applies here: host byte-layout tests do
not establish controller calibration or real sensor response.

`platform/ps5/pad_state.hpp` names these fields without changing the 120-byte
layout. Static assertions preserve every known offset. Motion requires an
explicit `Pad::set_motion_enabled(true)` request and defaults to off. Failed
requests are not retried every frame; toggling off and on permits another try.
Only finite, plausibly bounded, nonzero accelerometer states become available.
The unit-length `direction` is the accelerometer direction, including dynamic
movement; it is not a separately filtered gravity estimate. No quaternion order,
Euler angle, axis inversion or neutral calibration is guessed.

Touch contacts use the reference's 1920-by-1080 grid, rejecting out-of-range data
instead of turning it into a gesture. Coordinates are normalized to 0–1 with
right/down positive. The frame provides the latest zero, one or two contacts,
not a high-level tap or swipe recognizer. A short contact that begins and ends in
one buffered batch is not retained as a continuing drag.

Both optional fields are unavailable on disconnect, system interception,
invalid data or a frame with no fresh sample. Existing button edges and trigger
behaviour are preserved. Digital navigation from the previous stick state is
also suppressed while the system intercepts input.

## Microphone

The pinned SDK contains `libSceAudioOut.so`, but no AudioIn import stub, typed
capture structures or verified microphone capture API. The local UI/reference
layer supplies output, not a documented input pipeline. No microphone module,
permission flow, capture thread, recording or guessed function signature is
added. Microphone interaction remains unsupported and off. A future local level
meter requires a verified capture API and explicit opt-in before implementation.

## Verification

`tests/controller-sensors/run.sh` exercises actual raw-byte offsets, opt-in
gating, normalized contacts/direction, malformed values, stale samples and
controller/system transitions. A physical PS5 check is still required before
describing motion or touch calibration as hardware-verified.
