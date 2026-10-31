#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
source tools/host-env.sh
clang++-18 -std=c++20 -O1 -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/sonic1-route-refinement.cpp src/museum/experience_audio.cpp build/preview-obj/src_gfx_*.o build/preview-obj/src_ui_glyphs.cpp.o build/preview-obj/host_platform_host.cpp.o -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -lpthread -o build/sonic1-route-refinement
stdbuf -oL build/sonic1-route-refinement > build/research/sonic1-full-route-refinement/real-route.log 2>&1

clang++-18 -std=c++20 -O1 -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/motion-accepted-haptics.cpp src/museum/experience_audio.cpp build/preview-obj/src_gfx_*.o build/preview-obj/src_ui_glyphs.cpp.o build/preview-obj/host_platform_host.cpp.o -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -lpthread -o build/sonic1-accepted-haptics
build/sonic1-accepted-haptics > build/research/sonic1-full-route-refinement/accepted-haptics.log 2>&1
