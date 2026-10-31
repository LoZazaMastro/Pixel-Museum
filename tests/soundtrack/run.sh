#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -ffunction-sections -fdata-sections -DGL_GLEXT_PROTOTYPES=1 -Isrc -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/soundtrack/bridge.cpp src/platform/video.cpp -Wl,--gc-sections -lpthread -o build/soundtrack-bridge-test
build/soundtrack-bridge-test
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -ffunction-sections -fdata-sections -Isrc tests/soundtrack/ambient.cpp src/museum/music.cpp -Wl,--gc-sections -o build/soundtrack-ambient-test
build/soundtrack-ambient-test
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -Isrc tests/soundtrack/catalog.cpp src/museum/catalog.cpp src/museum/localization.cpp src/core/save_file.cpp -o build/soundtrack-catalog-test
build/soundtrack-catalog-test
python3 tests/soundtrack/projection.py
