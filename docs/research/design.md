# Pixel Museum — visual direction

Research reviewed before interface implementation, 20 October 2026.

## References

- [SMK OPEN](https://open.smk.dk/): an isolated collection object with generous negative space, quiet provenance and a small, purposeful navigation. Inspected the live collection landing screen.
- [Nasjonalmuseet collection](https://www.nasjonalmuseet.no/en/collection/): large plain typography, a clear grid, thin rules and an object-led hierarchy. Inspected the live page after dismissing its cookie dialog.
- [The Making of Karateka](https://www.digitaleclipse.com/games/karateka): inspected the official screenshot gallery, including the chapter navigation. Archival material and a readable explanation share the screen; the timeline connects the material rather than becoming a list of release dates.
- [Gran Turismo Brand Central museums](https://www.gran-turismo.com/au/news/00_1796083.html): historical context alongside objects, with the year functioning as a strong visual anchor.

These are references for structure and visual restraint. Their artwork, identities and interface assets are not copied.

## Direction

A digital collection with the calm of a northern European gallery: warm ivory, charcoal ink, generous margins and restrained chapter colours. A small pixel-built M identifies the museum without turning the whole interface into a retro arcade. Large years act as a second spatial layer behind objects. Images retain their proportions; photographs are not silently cropped to look like transparent models.

The timeline gives one exhibit the room to breathe. A lower chronology links nearby exhibits, while shoulder buttons jump between chapters. Opening an exhibit changes the composition according to the material: object plate, portrait, editorial spread or screening room. Clear English explains what changed, who made it happen and why it mattered. Dates distinguish announcements, first releases and regional launches.

The controller focus uses shape and contrast as well as colour. Motion follows the preserved homebrew UI toolkit: interrupted springs, soft content transitions, controller-aware hints, modal blur and a reduced-motion option. Image inspection uses the toolkit's zoom/pan viewer. The original ambient score follows the selected year and ducks beneath video.

## Scope and verification

The catalogue ships original text and provenance as a local fallback. Images, videos and optional object models remain external resources, fetched to a bounded local cache. An unreachable resource must show its real state rather than a simulated video or invented image. No online catalogue endpoint is advertised until one has actually been published.

Desktop captures come from the production OpenGL interface. They verify layout; PS5 video decoding, audio, controller feel and frame pacing require separate hardware verification.
