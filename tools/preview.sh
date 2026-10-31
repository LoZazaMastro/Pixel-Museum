#!/usr/bin/env bash
# Pixel Museum - Render the actual app UI with software Mesa for inspection.
# Copyright (C) 2026 Andrea Sgarro
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
source tools/ninja-build.sh
ninja_begin "$root/build/preview.ninja"
objects=()
mkdir -p build/host-include
[[ -d build/host-include/curl ]] || cp -r .deps/pacbrew/v0.40.2/sysroot/user/homebrew/include/curl build/host-include/
while IFS= read -r -d '' source; do
 object="build/preview-obj/${source//\//_}.o"
 mkdir -p "$(dirname "$object")"
 ninja_inputs=("$source")
 ninja_edge CXX "$object" clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  -ffunction-sections -fdata-sections -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" \
  -I"$sysroot/usr/include/x86_64-linux-gnu" -Ibuild/host-include -MD -MF "$object.d" -c "$source" -o "$object"
 objects+=("$object")
done < <(find src host -name '*.cpp' ! -path 'src/platform/ps5/*' ! -path 'src/runtime/*' ! -path 'src/third_party/*' ! -name main.cpp -print0)
while IFS= read -r -d '' source; do
 object="build/preview-obj/${source//\//_}.o"
 mkdir -p "$(dirname "$object")"
 ninja_inputs=("$source")
 ninja_edge CC "$object" clang-18 -std=gnu11 -O2 -w -ffunction-sections -fdata-sections \
  -D_GNU_SOURCE -Isrc -I. -I"$sysroot/usr/include" -MD -MF "$object.d" -c "$source" -o "$object"
 objects+=("$object")
done < <(find src/third_party -name '*.c' -print0)
ninja_inputs=("${objects[@]}")
ninja_edge LINK build/pixelmuseum-preview clang++-18 "${objects[@]}" -Wl,--gc-sections \
 -Wl,--wrap=glBlitFramebuffer,--wrap=glReadPixels,--wrap=glGetTexImage,--wrap=glCopyImageSubData \
 -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -l:libzstd.so.1 -l:libcurl.so.4 -lpthread -lm -o build/pixelmuseum-preview
ninja_run > build/preview-build.log 2>&1
if [[ -z "${MUSEUM_PREVIEW_ROOT:-}" ]]; then
 python3 tools/prepare-runtime-preview.py
 export MUSEUM_PREVIEW_ROOT=build/runtime-preview
fi
EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe \
 __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json" \
 LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri" build/pixelmuseum-preview "$@"
