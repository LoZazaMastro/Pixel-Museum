#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Isrc music/test_music.cpp src/museum/music.cpp src/third_party/stb/vorbis.c -o build/timeline-music-test
build/timeline-music-test music/eras
