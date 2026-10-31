#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
mkdir -p build/research
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc -I. \
 tests/catalog-byte-budget.cpp src/museum/catalog.cpp src/museum/localization.cpp src/core/save_file.cpp -o build/catalog-byte-budget-test
build/catalog-byte-budget-test "$@"
