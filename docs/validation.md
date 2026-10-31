# Development validation

This record distinguishes local checks from PS5 observations. No desktop image is evidence of console playback or frame rate.

## Local checks

- The production interface renders through EGL/Mesa at 1920 × 1080 with no OpenGL errors in the captured timeline, exhibit, image viewer, preferences, credits and portrait views.
- Interaction checks cover collection bounds, 600 navigation steps, controller focus loss, opening and leaving an exhibit, changing a preference, and rejecting a malformed catalogue without destroying the working collection.
- The native source set is built with warnings treated as errors. Final package validation is recorded after the build completes.
- The assembled catalogue contains more than one thousand records. Real-parser checks cover the 16 MiB read bound, explicit 5,000-entry refusal, complete paragraphs, source links, date precision and editorial attribution. Source data and unknown dates are preserved.
- Four font faces use the kit's existing glyph fallback mechanism with a small Noto Sans CJK subset. The current title/body audit reports no missing glyphs; Inter remains the interface font.
- A production-screen capture at 3840 × 2160 has passed with no OpenGL errors. Separate GLB tests render the original Game Boy and selected PlayStation models with their authored textures and multisample antialiasing; these are desktop checks.
- Large model allocations use a bounded lazy direct-memory path on PS5. Host kernel-stub checks exercise alignment, realloc, clearing, budget refusal, map failure and release. A successful host check does not prove the console's available physical budget.
- The original score has eight synchronized loops. Actual Vorbis decoding, loop joins, crossfades, mute ramps, missing files and callback block independence were checked. See `music/README.md` for measurements.
- The optional model viewer tests real GLB files, strict buffer bounds and unsupported input errors. Model parsing runs on a worker; GPU uploads and rendering stay on the graphics thread.
- A real request to the verified official Karateka video returned YouTube stream formats and an eligible 720p AVC stream. Resolving a stream does not prove PS5 playback.
- The corresponding Google video byte-range requests returned HTTP 403 in the PC test environment, including four eligible AVC/VP9 variants. Console playback and the optional account connection must be tested before claiming this route works on the user's PS5.

## Console

The first vertical slice was transferred on 20 October 2026 to `/data/homebrew/PPSA70421`. All 183 transferred files were read back and matched their local SHA-256 digests before the title's parameter file was promoted. This was a first install: the title did not previously exist. At the final check, Stremio Plus remained active and the new title had not yet appeared in `/user/app`; closure was requested so ShadowMount could register it. No launch has yet been observed; video decoding, audio output, input feel, network behavior and frame pacing remain to be checked on the PS5.

The trial contains 16 exhibits, 27 remote photographs, five distinct online films and four bundled console models. Its archive is 232,553,254 bytes, SHA-256 `268074c0a1b1a74a01b256dac7bf668b8fc11f970f3b626272843c8ea43660fb`. The complete authoring catalogue remains separate at 1,030 records and 24 selected models.

The new production scene checks render reversible story lifts, photograph expansion from actual card bounds, zoom and return to the same reading position, inline/fullscreen film presentation and input isolation. They passed at 3840 × 2160 with no GL errors. The film test deliberately uses an idle presentation fixture and does not claim YouTube network playback.

The title has its own identity, PPSA70421. It was checked against the installed homebrew folders and the public catalogue during preparation. No existing application was overwritten.


## Experience trial transferred - 20 October 2026

The second trial (`dist/vertical-slice-ready-03`) was installed at17:49:29UTC with Pixel Museum unmounted. The updater backed up previous files, staged and reread changed bytes, checked the title remained closed before each promotion, and activated the executable last. Receipt: `build/console-slice/backups/20261020T174916Z/update-receipt.json`.

Result: `updated_and_byte_verified`;17 payload files changed,167 payload files matched unchanged, and4 registered Home wallpaper copies changed. The installed executable SHA-256 is `a9e48535a4cdf6db1284cae4e65382e04571f47b2f5462673e2624abcdd9b6d1`. All21 experience-to-exhibit links resolve inside the35-exhibit trial. Saved preferences/cache were not replaced. No other title was modified or launched.

Local validation includes production-screen checks of repeated introductions, source retention, exact touch-and-click target, motion neutral reset on focus loss, playlist UI ownership, carousel/photo/film/object transitions, and4K rendering. The twenty procedural studies passed focused mechanics/reset/input-loss/bounded-work tests. Actual PS5 UI timing, sensor orientation, tactile response and native YouTube stream playback remain pending the user's console trial; local passing tests do not establish these outcomes.


## GPU composition correction and navigation audio

The subsequent physical console trace confirmed sustained approximately1.5-2FPS in the collection view. Repeated3840x2160 software framebuffer blits cost approximately508-524ms per frame, and model MSAA resolves added approximately565-582ms. Those observations supersede any inference of console responsiveness from the earlier host captures.

The revised compositor uses GPU texture draws for settled frames and snapshots. The object renderer uses a full-resolution single-sample scene and GPU silhouette coverage pass. Host abort/counter hooks reject framebuffer blits and CPU readbacks during tested first-page, transition, panel and experience paths. Pixel tests preserve corner orientation/colour, opaque alpha and interrupted dissolves. Object tests preserve exact opaque artwork and original maps/geometry at4K. New startup phase timings distinguish pre-first-frame initialization from continuing frame costs.

The same build adds25original navigation recordings across18cue names, with the score's tuning and no random pitch jitter. Actual SoundBank/Mixer tests report25loaded,0rejected, no dropped events across1200actions and no clipping. These are local checks; the final PS5 frame rate and audible mix remain to be tested on the console.

Audited package: `dist/vertical-slice-ready-04`;211files. Package SHA-256 `ba293c9c68cbac50784e0eb9c10b8f3044c0a66be1eb42a0ba57d5cbe57f49a1`. Signed executable SHA-256 `24a773dfa89d4ed2c9631065e3c7d60099955f9ed41f659e264c03aff8d346c4`, SELF integrity valid.

The corrected build was transferred successfully with Pixel Museum closed. Receipt `build/console-slice/backups/20261020T195019Z/update-receipt.json` records `updated_and_byte_verified`:28changed files and183unchanged files verified. Only Pixel Museum files were activated; the executable was promoted last. Existing preferences, cache and other titles were preserved. Physical performance verification is pending the user's next launch.


## Full source collection and current local corrections

The current local collection restores all365 published Playhub editions:365 introductions and1291chapters,1656 exact source sections. Canonical merges retain333 complete editions;32 remain independent destinations. The exact-copy receipt is `content/playhub-import-receipt.json`, and the check is `content/expansion/check_playhub_locales.py`. Eight existing source language editions are retained. This verifies import fidelity, not factual accuracy or editorial completion. Missing models no longer hide console articles from the runtime chronology.

A complete task register now accounts for every distinct timeline destination and every narrative section. `tools/editorial-plan.py` regenerates it from the current catalogue; media availability, source review and editorial sign-off remain separate gates. The installed35-exhibit trial has not been replaced with this full collection.

The revised loader decodes one original4K atlas at a time and reserves immutable GPU mip storage once per texture. The actual Game Boy passes desktop decoding/upload/render checks with all11 original4096x4096maps and unchanged geometry. This addresses the observed shared-memory pressure; success on the PS5 remains unverified for this revision.

The native display requests3840x2160at120Hz and reports the accepted60/120Hz mode after presentation. Automatic and manual orbit follow the accepted display cadence when the measured object cost fits its budget. This is a request and scheduling change, not a measured120FPS claim.

The local production UI checks pass the new dark language-first onboarding, theme fade and persistence,15 reviewed experience launches and repeated introductions, actual paused study previews, source-card return and the4K compositor regression. Native compilation/linking also passes. Media volume now defaults to60% and is adjustable with the triggers. The audio-only soundtrack path omits video-demux/decoder setup and film rendering; its new native streaming behavior still needs a console test. No new build has been written to the console during this work.
