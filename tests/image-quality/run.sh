#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
python3 tests/image-quality/fixtures.py
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/image-quality/test.cpp src/platform/image_quality.cpp src/yt/image.cpp -o build/photo-test
build/photo-test "$@"
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/image-quality/cache.cpp src/platform/remote_cache.cpp src/core/save_file.cpp src/platform/image_quality.cpp src/yt/image.cpp host/platform_host.cpp -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -lpthread -Wl,--wrap=glTexSubImage2D -o build/photo-cache-test
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
build/photo-cache-test "$@"
