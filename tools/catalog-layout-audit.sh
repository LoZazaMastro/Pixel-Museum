#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
clang++-18 -std=c++20 -O2 -fno-exceptions -fno-rtti -Isrc tools/catalog-layout-audit.cpp \
 src/museum/catalog.cpp src/museum/localization.cpp src/core/save_file.cpp src/gfx/font.cpp -o build/catalog-layout-audit
python3 tools/prepare-runtime-preview.py
build/catalog-layout-audit
