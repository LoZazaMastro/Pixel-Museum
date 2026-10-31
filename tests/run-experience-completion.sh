#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
MUSEUM_PREVIEW_4K=1 MUSEUM_PREVIEW_ROOT=dist/PPSA70421 build/pixelmuseum-preview experience-completion
