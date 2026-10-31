#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
out=build/research/display-refresh
mkdir -p "$out/dynamic" "$out/legacy"
cat > "$out/legacy/ps5_opengl_display.h" <<'HEADER'
#pragma once
#define PS5_OPENGL_NATIVE_WIDTH 1920
#define PS5_OPENGL_NATIVE_HEIGHT 1080
#define PS5_OPENGL_NATIVE_FPS 60
HEADER
cp "$out/legacy/ps5_opengl_display.h" "$out/dynamic/ps5_opengl_display.h"
cat > "$out/dynamic/ps5_opengl_display_modes.h" <<'HEADER'
#pragma once
#include <EGL/egl.h>
#define PS5_OPENGL_DYNAMIC_DISPLAY 1
extern "C" EGLBoolean eglSetDisplayModePS5(EGLDisplay,EGLint,EGLint);
extern "C" EGLBoolean eglSetDisplayRefreshPS5(EGLDisplay,EGLint);
extern "C" EGLBoolean eglGetDisplayModePS5(EGLDisplay,EGLint*,EGLint*,EGLint*);
HEADER
for variant in dynamic legacy; do
 dynamic=0;[[ $variant != dynamic ]] || dynamic=1
 clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 -DEXPECT_DYNAMIC="$dynamic" \
  -Isrc -I"$out/$variant" -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" \
  tests/display-refresh/stub.cpp src/platform/ps5/display_egl.cpp -o "$out/$variant-test"
 "$out/$variant-test"
done
