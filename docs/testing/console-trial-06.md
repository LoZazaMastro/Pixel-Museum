# Pixel Museum: console trial 06

Development trial, 21 October 2026. This is not a release of the complete museum.

The tested package contains 42 exhibits, four bundled 3D models,90 remote image records and56 new narrative cards. Twelve connected features deepen existing stories; two new illustrated features cover Ed Smith/APF and the Riven recording-session context. Other completed drafts remain in the authoring collection while suitable media is acquired. Original Playhub prose and available translations remain intact.

## Changes to try

- Game Boy and Nintendo 3DS: one original 4K atlas is decoded and uploaded at a time; immutable storage, shared sampler states and bounded retirement reduce peak memory/work. Loading stays visible through the CPU/GPU handoff. Right stick rotates; L2/R2 zoom. R3 retries a failed model.
- The renderer requests4K at 120 Hz and records the accepted display mode. Measured120 FPS and physical PS5 allocation behavior are not yet established; unsupported modes retain a synchronized fallback.
- Carol Shaw, Journey, Papers, Please, Monument Valley and the new production stories include additional connected cards with their own source credits.
- Language selection comes before theme selection. First startup begins dark. The museum retains the selected language/appearance; unsupported article translations visibly retain English prose.
- Films default to 60 percent gain; L2/R2 adjust media volume. Soundtrack recordings open audio-only. These native streaming changes still need physical console review.
- Non-English languages request a matching YouTube caption track or an advertised automatic translation. Cues follow playback/seeking and remain when controls hide. Anonymous live metadata works, but the PC caption probe returned 429/empty responses; actual PS5 subtitle playback is unverified.
- Fifteen minimal interactive studies have distinct actual previews and repeated onboarding. Breakout uses its original playable-study preview while archival HD photography remains unresolved.

## Local verification

Native compile/link/conversion; signed SELF integrity; all 224 package files and ZIP digests; actual 4K editorial/caption rendering; 600 navigation actions; onboarding/theme/persistence; 15 study presentation; compositor orientation/alpha and no production CPU readback; 21,084 localization checks; 32 caption backend checks; 76 neutral material checks; original full-resolution Game Boy and3DS state/cancellation/material checks. Final staged-payload smoke and FTPverification are recorded separately.

## First physical checks

Start at Game Boy, wait for the original asset to finish, rotate continuously and leave it visible for 30 seconds. Repeat with Nintendo 3DS. Then open a story and an experience, try a film in a non-English language and a soundtrack with L2/R2 volume. Leave the app open afterward so the session log can establish actual frame pacing, accepted refresh rate and storage/transfer costs.

## Deployment

Installed through the title-scoped FTP updater after confirming Pixel Museum was not mounted. All 224 files were read back and matched by SHA-256; 16 changed files were promoted and 208 unchanged files verified. Backup and receipt: `build/console-slice/backups/20261020T221207Z/update-receipt.json`. User settings and other applications remain outside the update. Actual native performance is awaiting the next user run.
