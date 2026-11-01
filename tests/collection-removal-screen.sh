#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../tools/host-env.sh"
cd "$root"
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
python3 tests/collection-removal-screen.py
