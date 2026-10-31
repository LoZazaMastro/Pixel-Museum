#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
if [[ ! -f tests/object-scene/viewer-test || src/museum/object_scene.cpp -nt tests/object-scene/viewer-test || src/museum/object_scene.hpp -nt tests/object-scene/viewer-test || src/museum/object_artwork_cache.hpp -nt tests/object-scene/viewer-test || src/museum/object_artwork_cache_v2.hpp -nt tests/object-scene/viewer-test || src/museum/object_cache_sha256.hpp -nt tests/object-scene/viewer-test || tests/object-scene/test.cpp -nt tests/object-scene/viewer-test ]]; then
 clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 \
 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" \
 tests/object-scene/test.cpp src/museum/object_scene.cpp src/gfx/gl_program.cpp \
 src/yt/image.cpp host/platform_host.cpp -L"$sysroot/usr/lib/x86_64-linux-gnu" \
 -lEGL -l:libGL.so.1 -l:libzstd.so.1 -lpthread -o tests/object-scene/viewer-test
fi
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
tests/object-scene/viewer-test "$@"
