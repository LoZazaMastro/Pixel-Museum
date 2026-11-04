#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
mkdir -p build/text-field-caret-tests
clang++-18 -std=c++20 -O1 -ffunction-sections -fdata-sections -Isrc \
  tests/text-field-caret.cpp src/ui/components/text_field.cpp \
  src/ui/components/component.cpp src/ui/widgets.cpp src/ui/theme.cpp \
  src/ui/pixel_font.cpp src/gfx/font.cpp src/gfx/draw_list.cpp \
  src/gfx/triangulate.cpp -Wl,--gc-sections \
  -o build/text-field-caret-tests/text-field-caret
build/text-field-caret-tests/text-field-caret "$PWD"
