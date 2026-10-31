#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
clang++-18 -std=c++20 -O2 -fno-exceptions -fno-rtti -Isrc \
 tools/catalog-audit.cpp src/museum/catalog.cpp src/core/save_file.cpp -o build/catalog-audit
build/catalog-audit "$@"
