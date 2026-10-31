#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/study_motion_test.cpp src/museum/study_motion.cpp src/museum/experience_audio.cpp build/preview-obj/src_gfx_*.o build/preview-obj/host_platform_host.cpp.o -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -lpthread -o build/study-motion-test
build/study-motion-test
clang++-18 -std=c++20 -O2 -Isrc tests/experience-audio.cpp src/museum/experience_audio.cpp -o build/experience-audio-test
build/experience-audio-test
