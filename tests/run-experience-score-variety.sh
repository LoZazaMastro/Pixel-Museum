#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc \
 tests/experience-score-variety.cpp src/museum/experience_audio.cpp -o build/experience-score-variety-test
build/experience-score-variety-test
clang++-18 -std=c++20 -O2 -Isrc tests/experience-audio.cpp src/museum/experience_audio.cpp -o build/experience-audio-test
build/experience-audio-test
