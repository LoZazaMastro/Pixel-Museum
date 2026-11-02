# Windows media runtime: attribution and source provenance

The Windows application redistributes **Deno 2.9.8** and the two unchanged **yt-dlp EJS 0.8.0** solver scripts. No standalone yt-dlp executable is included in the application or required at runtime. Pixel Museum obtains public player metadata through its existing native HTTP client, invokes the official EJS solver directly for unsupported player transforms, and streams the selected URLs through native FFmpeg.

## Deno 2.9.8

Copyright 2018–2026 the Deno authors. Deno itself is licensed under **MIT**; its embedded third-party components retain their own licences.

- Official release: https://github.com/denoland/deno/releases/tag/v2.9.8
- Distributed Windows x64 binary: https://github.com/denoland/deno/releases/download/v2.9.8/deno-x86_64-pc-windows-msvc.zip
- Exact source archive: https://github.com/denoland/deno/archive/refs/tags/v2.9.8.tar.gz
- Upstream licence: https://github.com/denoland/deno/blob/v2.9.8/LICENSE.md
- Preserved licence: [deno-2.9.8/LICENSE.md](deno-2.9.8/LICENSE.md).

The executable identifies its embedded engines as **V8 15.0.245.2-rusty** and **TypeScript 6.0.3**. The pinned Deno source lockfile selects the Rust V8 binding **150.4.0**. Corresponding sources and retained notices include:

- Rust V8 binding source archive: https://github.com/denoland/rusty_v8/archive/refs/tags/v150.4.0.tar.gz
- Pinned V8 engine source: https://github.com/denoland/v8/archive/ac1e23989121713ca642f6650b34deff7b686896.tar.gz
- V8 BSD licence, fdlibm/Strongtalk notices and pinned third-party/submodule licences (including ICU, Abseil and LLVM components): files beginning `V8-` under `deno-2.9.8/licenses/`.
- TypeScript source archive: https://github.com/microsoft/TypeScript/archive/refs/tags/v6.0.3.tar.gz
- TypeScript Apache-2.0 licence and additional notices: `deno-2.9.8/licenses/TypeScript-LICENSE.txt` and `TypeScript-ThirdPartyNoticeText.txt`.
- Upstream [Node.js declaration licence](deno-2.9.8/licenses/cli-tsc-dts-node-LICENSE), [Undici licence](deno-2.9.8/licenses/cli-tsc-dts-node-undici-LICENSE) and [WebGPU licence](deno-2.9.8/licenses/ext-webgpu-LICENSE.md).

[Deno dependency licence texts](deno-2.9.8/licenses/THIRD-PARTY-LICENSES.txt) preserve the licence-named files from **all 1,048 registry source packages in Deno's exact upstream Cargo.lock**. This intentionally includes development and other-platform dependencies; it does not claim every listed package is compiled into the Windows executable. Each source archive was verified against its Cargo.lock checksum. Where an upstream crate supplies no separate licence file, the collection records its declared licence, authors and exact source archive URL. Workspace packages are covered by the Deno source archive and their upstream terms.

The exact [Cargo.lock](deno-2.9.8/licenses/Cargo.lock), [dependency source/checksum index](deno-2.9.8/licenses/dependency-provenance.json) and [embedded-component source index](deno-2.9.8/licenses/embedded-provenance.json) accompany those texts.

## yt-dlp EJS 0.8.0

The official yt-dlp project supplies the External JavaScript solver, licensed under **Unlicense**. The scripts incorporate the **Meriyah parser (ISC)** and **Astring generator (MIT)**. Pixel Museum preserves the upstream scripts byte for byte.

- Official release: https://github.com/yt-dlp/ejs/releases/tag/0.8.0
- Exact source archive: https://github.com/yt-dlp/ejs/archive/refs/tags/0.8.0.tar.gz
- Distributed scripts: https://github.com/yt-dlp/ejs/releases/download/0.8.0/yt.solver.core.min.js and https://github.com/yt-dlp/ejs/releases/download/0.8.0/yt.solver.lib.min.js
- Upstream licence: https://github.com/yt-dlp/ejs/blob/0.8.0/LICENSE
- Preserved licences: [Unlicense](ejs-0.8.0/LICENSE), [Meriyah ISC](ejs-0.8.0/licenses/meriyah-ISC.txt) and [Astring MIT](ejs-0.8.0/licenses/astring-MIT.txt).

## Distribution checksums and runtime behaviour

[versions.json](versions.json) lists only the redistributed runtime components, with exact release/download/source URLs and SHA-256 checksums. A standalone yt-dlp executable used during development is excluded from both the application package and this runtime inventory.

The application never downloads or updates these helpers. Setup installs them with the application. Deno runs hidden, without script network/filesystem/environment/process/FFI permissions, remote/npm imports or configuration. Runtime update checks are disabled. The native application bounds execution time, process memory and captured output and terminates the child on cancellation. Collection resource installation remains the responsibility of Pixel Museum Setup.
