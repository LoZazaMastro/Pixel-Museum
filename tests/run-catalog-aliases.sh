#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
mkdir -p build/research/catalog-aliases
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc -I. \
 tests/catalog-aliases.cpp src/museum/catalog.cpp src/core/save_file.cpp -o build/catalog-aliases-test
build/catalog-aliases-test
