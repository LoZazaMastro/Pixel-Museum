# Code and runtime acknowledgements

Collection images retain their individual creator, archive and licence records
in the catalogue and exhibit Credits. The early De Forest Audion photograph by
Gregory F. Maxwell is distributed under GFDL 1.2; its complete licence text is
included in [GFDL-1.2.txt](GFDL-1.2.txt). This image licence is separate from the
application's source-code licence.

Pixel Museum is licensed under GPL-3.0-or-later. Its interface and native
application foundation incorporate **ps5-homebrew-ui** and
**ps5-native-app-boilerplate**, Copyright 2026 BlackBearReloaded. Their original
copyright and SPDX notices remain in the adopted source files.

YouTube resolving, HTTP support and FFmpeg playback are adapted from
[animatian112/ytps5-sponsorblock](https://github.com/animatian112/ytps5-sponsorblock),
revision `6020a4b23bd7d2fa39d85e70fd5752468952b829`, including the original
ytps5 work by BlackBearReloaded and contributions by the SponsorBlock for PS5
contributors. The museum uses its stream resolver and native decoder, rather
than hosting or redistributing the videos. YouTube may require sign-in or refuse
playback on particular networks. The initial museum player chooses AVC or VP9
at a maximum of 720p and decodes in software.

Other code and build dependencies include:

- Optional DualSense state layout adapted from
  [PSSwanStation by Press5elect](https://github.com/Press5elect/PSSwanStation),
  Copyright 2026 Press5elect, GPL-3.0-or-later with its preserved section 7(b)
  [additional attribution terms](psswanstation-additional-terms.txt). Its local
  controller reference traces the layout to PSFlyCast. No physical motion or
  microphone support is claimed on the strength of host tests alone.
- ps5-opengl, Mesa and OpenGNM; see the SDK notices in `opengl/`.
- The public PS5 payload SDK and LLVM libc++/libc++abi.
- Public direct-memory API declarations and allocation guidance from Mihawk's
  PS5_PayloadSDK platform layer, used for the museum's bounded lazy CPU media
  allocator (`https://github.com/mihawk-99/PS5_PayloadSDK`).
- FFmpeg and its PacBrew dependencies, including x264, libass, HarfBuzz,
  FreeType, Fontconfig, FriBidi, libpng, Expat, libiconv, liblzma and bzip2.
- libcurl, OpenSSL, libpsl, zstd and zlib for verified HTTPS transport.
- stb_image/stb_vorbis, yyjson, nlohmann JSON and QR Code generator; their
  license texts are preserved in `source-dependencies/`.
- Mozilla's CA certificate collection, distributed under MPL-2.0, embedded by
  the upstream YouTube fork.
- Inter, Montserrat and DejaVu Sans Mono; their licenses accompany the baked
  fonts in `assets/fonts/`.
- Noto Sans CJK by its credited font authors, under SIL OFL1.1. An exact Unicode
  subset is baked as a secondary atlas; Latin interface typography stays Inter.
  Its copyright, OFL text and modification/source record accompany that atlas.
- Toolkit glass/paper interface sounds and Inigo Quilez's MIT-licensed signed
  distance functions, as detailed in `homebrew-ui-notices.md`.

`homebrew-ui-notices.md` and `ytps5-notices.md` preserve upstream notices as
historical source documents. Their references to upstream demonstration artwork,
playlists, update systems or title IDs describe those upstream applications, not
Pixel Museum. Pixel Museum has its own artwork, original soundtrack and
independent Media identity PPSA70421. It does not include an updater for any
upstream title.

Individual museum images, models, writing sources and linked videos retain their
own attribution and rights information in the collection catalogue and exhibit
source panels. Original museum music is credited separately in the music
manifest. No game ROM, proprietary console runtime or downloaded YouTube video
is bundled in the application.
