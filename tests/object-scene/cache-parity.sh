#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
python3 tests/object-scene/material-fixtures.py
bash tests/object-scene/bake-artwork-cache.sh build/material-fixtures/packed-orm-10497-9987.glb
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/object-scene/cache-parity.cpp src/gfx/gl_program.cpp src/yt/image.cpp host/platform_host.cpp -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -l:libzstd.so.1 -lpthread -o build/cache-parity-test
build/cache-parity-test "$@"
