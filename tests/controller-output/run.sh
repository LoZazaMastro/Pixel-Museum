#!/bin/bash
set -e
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc tests/controller-output/test.cpp src/audio/controller_feedback.cpp src/audio/mixer.cpp src/platform/ps5/controller_audio.cpp -lpthread -o build/controller-output-test
build/controller-output-test
