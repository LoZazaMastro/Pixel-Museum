#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -ffunction-sections -fdata-sections -Isrc -I. tests/museum-search.cpp src/museum/catalog.cpp -Wl,--gc-sections -o build/museum-search-test
build/museum-search-test
