#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -Isrc \
 tools/export-experiences.cpp src/museum/study_catalog.cpp -o build/export-experiences
build/export-experiences
