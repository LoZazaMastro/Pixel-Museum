#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
for test in studies-reviewed-arcade mario-corrections; do
 clang++-18 -std=c++20 -O1 -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" "tests/$test.cpp" src/museum/experience_audio.cpp build/preview-obj/src_gfx_*.o build/preview-obj/src_ui_glyphs.cpp.o build/preview-obj/host_platform_host.cpp.o -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -lpthread -o "build/$test-quick-fixes"
 "build/$test-quick-fixes"
done
