#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
source tools/host-env.sh
if [[ ! -f build/current-console-selectors || tests/object-scene/current-console-selectors.cpp -nt build/current-console-selectors || src/museum/object_scene.cpp -nt build/current-console-selectors || src/yt/image.cpp -nt build/current-console-selectors ]]; then
 clang++-18 -std=c++20 -O1 -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/object-scene/current-console-selectors.cpp src/museum/object_scene.cpp src/gfx/gl_program.cpp src/yt/image.cpp host/platform_host.cpp -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -l:libzstd.so.1 -lpthread -o build/current-console-selectors
fi
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
build/current-console-selectors "$@"
