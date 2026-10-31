#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -Isrc tests/experience-audio.cpp src/museum/experience_audio.cpp -o build/experience-audio-test
build/experience-audio-test
