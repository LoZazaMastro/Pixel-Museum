#!/usr/bin/env bash
# Adjacent Options->Replay regression; reads the existing bundle, never erases it.
set -euo pipefail
source "$(dirname "$0")/../tools/host-env.sh"
cd "$root"
export MUSEUM_PREVIEW_ROOT="$root/dist/PPSA70421"
export MUSEUM_TEST_REPLAY_MANIFEST="$root/build/research/replay-introduction-hotfix-20261101/collection-packs.json"
export MUSEUM_TEST_REPLAY_BUNDLE="$root/build/research/replay-introduction-hotfix-20261101/bundled"
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
build/pixelmuseum-preview collection-existing > build/research/collection-removal-0.1.4/replay.log 2>&1
tail -n 3 build/research/collection-removal-0.1.4/replay.log
