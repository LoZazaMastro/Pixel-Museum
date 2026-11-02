# Pixel Museum for Windows

The Windows edition builds the same C++ museum, renderer, catalogues, languages,
workshops and playable experiences as the PS5 edition. SDL3 owns the native
window, keyboard, mouse, gamepads and audio; FFmpeg handles actual streamed media.

## Install and run the local preview

Open **Pixel-Museum-Setup.exe** next to **windows-manifest.json** and
the application ZIP named by that manifest. Choose English, Italian, French, German or Spanish,
accept the software/collection notices, and choose an empty Pixel Museum folder.
Setup verifies the app ZIP and downloads the pinned collection packs from GitHub.
The program and every collection archive remain inside that folder. Launch
**Pixel Museum.exe** after installation. The PC introduction does not download
resources. An Internet connection is required for
streamed YouTube videos and soundtracks.

This is a local development preview. The website's Windows download remains
unavailable until an actual Windows setup release has been uploaded and verified.

## Controls

| Action | Keyboard / mouse |
| --- | --- |
| Move | Arrow keys or W/A/S/D |
| Right stick in experiences / long text | I / J / K / L |
| Timeline forward / back | Wheel down / up |
| Select / confirm | Click or Enter |
| Back | Escape or right click |
| Options | O or F10 |
| Search | F or Ctrl+F; type normally in the search field |
| Guide | Tab |
| Inspect image | Space |
| Read more | V |
| Previous / next exhibit or decade | Q / E |
| Filter | Z / C |
| Today | R |
| Scroll long text | Page Up / Page Down |
| Zoom / playback volume | − / +; context-dependent wheel |
| Toggle fullscreen | F11 |

The first Options row opens Video (resolution, Fullscreen, Borderless fullscreen,
Windowed, VSync and frame limit). Borderless fullscreen uses the desktop resolution.
The final row is Exit. **Update database** checks for reviewed content updates;
verified updates become active on the next launch. Windows also checks for new
application versions and offers **Update application** in Options. It downloads
and verifies an update, closes the app, replaces only owned program files and
restarts it, preserving the collection, settings and trophies. See
[Windows application updates](windows-application-updates.md) for the release flow.
PS5 application updates continue through ProsperoStore. The mouse uses the website's
black/white pixel cursor with an interactive glow. Gamepads use their normal buttons; generic pads receive
standard rumble. The native player includes the official Deno/EJS resolver for
current YouTube player scripts; no separate Python or browser sign-in is required.
Optional YouTube account connection offers both a QR code and an Open in browser
button, which opens the verification page in the user's usual browser.
A supported USB DualSense four-channel endpoint can carry speaker
and PCM haptics; other connections use normal rumble and the PC audio output.
Physical controller validation is still required on the user's actual devices.

## Build

Windows 10 1903+ or Windows 11, x64, with an OpenGL 4.3+ graphics driver is required.
The application manifest enables UTF-8 paths and per-monitor DPI awareness.

Install the native toolchain in the existing MSYS2 MinGW64 environment:

```sh
pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake \
  mingw-w64-x86_64-ninja mingw-w64-x86_64-sdl3 mingw-w64-x86_64-glew \
  mingw-w64-x86_64-ffmpeg mingw-w64-x86_64-curl mingw-w64-x86_64-openssl \
  mingw-w64-x86_64-zstd mingw-w64-x86_64-zlib
```

From PowerShell, run `tools/build-windows.ps1`. The executable is produced at
`build/windows-native/Pixel Museum.exe`. `tools/package-windows.py --runtime PATH`
packages the tested runtime content, recursively includes native DLL dependencies,
and creates the local setup manifest. The current source catalogue is an editing
master; use the packaged, tested runtime catalogue rather than copying that master.
The Rust setup is built using `tools/build-windows-installer.ps1` (see the installer
guide for pinned manifests, offline tests and redistribution notices).

PS5 remains built by the existing Makefile/scripts; Windows sources are excluded.

## Meaningful checks

- `Pixel Museum.exe --root RUNTIME --data ISOLATED_DIRECTORY --ui-checks` exercises
  real Screen input, native UTF-8 search, timeline direction, options and Exit.
- `--smoke --frames 300 --screenshot PATH.png` renders the actual production screen
  on the Windows OpenGL driver without leaving an interactive window open.
- Native media checks cover H.264, VP9, AV1, audio conversion, pause/seek, playback
  speed/pitch and completion over actual HTTP ranges.
- Collection checks cover install, offline reopen, remove/reinstall and rejection
  of junctions that could lead outside the installation's collection directory.

These checks establish implemented software behavior. They do not substitute for
testing every experience and actual generic/DualSense hardware before release.
