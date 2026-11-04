# Third-party notices

Pixel Museum incorporates open-source software from several projects. Original copyright notices remain in the source. The application code is distributed under GPL-3.0-or-later; this does not relicense external collection media.

The full [code and runtime acknowledgements](licenses/README.md) identify the adopted ps5-homebrew-ui foundation, native application boilerplate, ytps5-sponsorblock revision, OpenGL stack, FFmpeg, HTTPS libraries, fonts and source dependencies. Their licence texts are preserved under `licenses/` and beside the fonts.

Individual photographs, films and 3D models retain the creators, source pages and licences recorded in [content/credits.json](content/credits.json). These records also ship with the application. The same credits appear in each exhibit's Sources section. Images remain at their publishers; approved licensed 3D models are bundled. YouTube films are streamed rather than bundled.

Optional DualSense state decoding is adapted from **PSSwanStation by Press5elect**, whose local reference traces the controller layout to PSFlyCast. The adapted source retains its copyright notice. PSSwanStation's GPL-3.0-or-later [additional attribution terms](licenses/psswanstation-additional-terms.txt) are preserved with the application. [Controller implementation notes](docs/research/controller-sensors.md) distinguish verified byte-layout tests from physical sensor behaviour that still requires console testing.

The museum's original ambient score and its reproducible composition source are described in [music/README.md](music/README.md).

The restricted collection writer and descriptor-relative syscall normalization adapt the user-supplied Stremio Plus download writer, under GPL-3.0-or-later. Its source licence identifiers are retained; the adapted writer is included under `tools/collection-writer/`.

The Windows player includes [Deno 2.9.8](https://github.com/denoland/deno/releases/tag/v2.9.8), under MIT, and the unchanged official [yt-dlp EJS 0.8.0 solver](https://github.com/yt-dlp/ejs/releases/tag/0.8.0), under Unlicense. EJS bundles the [Meriyah](https://github.com/meriyah/meriyah) parser (ISC) and [Astring](https://github.com/davidbonnet/astring) generator (MIT). Their licence texts accompany the runtime under `tools/windows-media/`; [pinned release and source provenance](tools/windows-media/versions.json) records the exact distributed versions and checksums.
