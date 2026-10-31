#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../../tools/host-env.sh"
cd "$root"
mkdir -p build/controller-sensors
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -Isrc \
 tests/controller-sensors/test.cpp src/core/input.cpp -o build/controller-sensors/check
build/controller-sensors/check
