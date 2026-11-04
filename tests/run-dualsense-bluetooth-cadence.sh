#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Wno-error=misleading-indentation -Isrc -I. tests/dualsense-bluetooth-cadence.cpp src/audio/controller_feedback.cpp -o build/dualsense-bluetooth-cadence-test
build/dualsense-bluetooth-cadence-test
