#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
python3 tests/image-quality/fixtures.py
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/image-quality/retry.cpp src/platform/remote_cache.cpp src/core/save_file.cpp src/platform/image_quality.cpp src/yt/image.cpp host/platform_host.cpp -L"$sysroot/usr/lib/x86_64-linux-gnu" -l:libGL.so.1 -lpthread -o build/photo-retry-test
build/photo-retry-test
