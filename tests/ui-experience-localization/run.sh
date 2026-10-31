#!/usr/bin/env bash
set -euo pipefail
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -Isrc tests/ui-experience-localization/test.cpp src/museum/localization.cpp src/museum/catalog.cpp src/museum/study_catalog.cpp src/core/save_file.cpp src/gfx/font.cpp src/gfx/draw_list.cpp src/gfx/triangulate.cpp src/ui/glyphs.cpp src/ui/inline_controls.cpp -o build/ui-experience-localization-test
build/ui-experience-localization-test
