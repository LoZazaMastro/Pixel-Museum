# Verified album passages

Soundtrack tracks may supply `start_seconds` and `end_seconds` as paired absolute seconds in the actual YouTube recording. Both must be finite numbers, start at or after zero, end strictly after start, and no later than366days. Partial, malformed or reversed intervals discard that track. Ordinary individual recordings omit both keys. The final cue requires a verified end; do not infer an unlimited tail. Preserve the actual chapter description and duration as research evidence.

`Entry.soundtrack_rooms` contains up to16 independent soundtrack rooms. When nonempty it replaces the legacy `soundtrack` in story cards. Each room accepts up to2048 recordings. Active playback preserves its selected room while cards animate; exit resets ownership, with a separate room index retained only for the closing image.

The Video worker seeks before its first PCM update. A producer-only48k sample allowance truncates decoder blocks at the passage end, then waits for the ring to drain before reporting ended. Next passages sharing the same resolved YouTube recording reuse the decoder by seek. Progress and seek controls are relative to the passage and remain within its verified bounds. Opening, reusing or closing a passage immediately mutes pending old PCM; decoder work remains on the worker.

The museum ambience stays suppressed throughout an active listening room, including loading, paused and completed. Circle releases the player and resumes the museum ambience. An actual muted video continues to use the existing film policy.

`tests/soundtrack/run.sh` exercises the production asynchronous Video bridge with a deterministic fake service/decoder, parser2048/multiroom/malformed fixtures, and the actual packaging projection. It verifies an exact48000-frame boundary across997-frame audio callbacks, initial seek, decoder reuse, pause race, clamped seek, close/cancel/reopen and invalid source ranges. This does not prove network seek latency or physical PS5 playback. `host/playlist_checks.hpp` additionally tests production card construction, no legacy duplicate, room ownership and the closing animation using the real Screen/GL path.
