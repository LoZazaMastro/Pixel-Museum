#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc -I. tests/font-shaped-runs.cpp src/gfx/font.cpp -o build/font-shaped-runs-test
build/font-shaped-runs-test
