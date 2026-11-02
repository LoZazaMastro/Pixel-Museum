# Windows player runtime

The native Windows player uses the unchanged official [yt-dlp EJS 0.8.0 solver](https://github.com/yt-dlp/ejs/releases/tag/0.8.0) with [Deno 2.9.8](https://github.com/denoland/deno/releases/tag/v2.9.8) when the console's small JavaScript interpreter cannot execute a current YouTube player. Media still streams through the application's native HTTP and FFmpeg backends; collection resources are installed by Pixel Museum Setup.

Package these paths underneath the directory containing `Pixel Museum.exe`:

- `tools/windows-media/deno-2.9.8/`, including its licence.
- `tools/windows-media/ejs-0.8.0/`, including its licences.
- This README and `versions.json` with the exact release/source URLs, sizes and SHA-256 checksums.

EJS receives the public player script and the selected stream parameters on private, temporary standard input. Deno runs without network, file, environment, process or FFI permissions, remote/npm imports, configuration or code caching. The process is hidden, has a 20-second wall limit and 1 GiB memory limit, and is terminated with all descendants on cancellation. Output is capped at 256 KiB; solver scripts are checked against pinned hashes before execution. Results and unsupported players are cached for the session.

The upstream solver is Unlicense; its bundled Meriyah parser is ISC and Astring generator is MIT. Deno is MIT. Preserve every included licence in distributed application archives.
