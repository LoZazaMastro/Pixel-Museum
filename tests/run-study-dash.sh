#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/study-dash.cpp src/museum/experience_audio.cpp build/preview-obj/src_gfx_*.o build/preview-obj/src_ui_glyphs.cpp.o build/preview-obj/host_platform_host.cpp.o -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -lpthread -o build/study-dash-test
build/study-dash-test
