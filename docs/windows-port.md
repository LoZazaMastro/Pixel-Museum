# Pixel Museum for Windows

The Windows edition builds the same C++ museum, renderer, catalogues, languages,
workshops and playable experiences as the PS5 edition. SDL3 owns the native
window, keyboard, mouse, gamepads and audio; FFmpeg handles actual streamed media.

## Install and run

Download [Pixel-Museum-Setup.exe](https://github.com/LoZazaMastro/Pixel-Museum/releases/download/windows-v0.2.0/Pixel-Museum-Setup.exe) and open it. Choose the setup language, accept the licence, and choose where to install the museum. Setup downloads the application and the collection to the same folder. Pixel Museum appears in the Windows Start menu and Installed apps. Setup can also create a desktop shortcut.

The museum asks you to choose its language on first launch. An internet connection is required for streamed YouTube videos and soundtracks.

## Controls

| Action | Keyboard / mouse |
| --- | --- |
| Move | Arrow keys or W/A/S/D |
| Right stick in supported experiences | I / J / K / L |
| Timeline forward / back | Wheel down / up over the timeline |
| Select / confirm | Click or Enter |
| Back | Escape or right click |
| Options | Escape on the timeline |
| Search | S on the timeline. Type with the physical or on-screen keyboard, then press Enter for the results list. |
| Guide | Tab |
| Inspect image | Space |
| Read more | V |
| Previous / next decade | Z / C |
| Next filter | F |
| Today | R |
| Scroll long text | Page Up / Page Down |
| Zoom / playback volume | − / +; context-dependent wheel |
| Toggle fullscreen | F11 |

The first Options row opens Video (resolution, Fullscreen, Borderless fullscreen,
Windowed, VSync and frame limit). Borderless fullscreen uses the desktop resolution.
The next row, Audio, adjusts overall volume, sound effects, ambience and cultural timeline audio.
The final row is Exit. **Check for updates** looks for both collection and Windows application updates. A collection update takes effect after restarting the museum. Application updates replace the program files and preserve the collection, settings and trophies. See [Windows application updates](windows-application-updates.md) for the release flow.
PS5 application updates continue through ProsperoStore. The mouse uses the website's
black/white pixel cursor with an interactive glow. Gamepads use their normal buttons; generic pads receive
standard rumble. The native player includes the official Deno/EJS resolver for
current YouTube player scripts; no separate Python or browser sign-in is required.
Optional YouTube account connection offers both a QR code and an Open in browser
button, which opens the verification page in the user's usual browser.
All sound plays through the PC audio output. DualSense uses dedicated PCM haptics
over USB or Bluetooth when available, and conventional rumble otherwise.
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
