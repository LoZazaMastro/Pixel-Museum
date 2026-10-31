#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
source tools/host-env.sh
exec > build/sonic-route-redesign-final.log 2>&1
build/momentum-loop-redesign
build/momentum-user-corrections-redesign
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
build/sonic-redesign-preview
printf 'SONIC_ROUTE_REDESIGN_EXIT0\n'
