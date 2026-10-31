#!/usr/bin/env bash
# Pixel Museum - Test actual image transport and worker decoding without GL.
# Copyright (C) 2026 Andrea Sgarro
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
mkdir -p build/host-include
[[ -d build/host-include/curl ]] || cp -r .deps/pacbrew/v0.40.2/sysroot/user/homebrew/include/curl build/host-include/
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -ffunction-sections -fdata-sections \
 -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -Ibuild/host-include -I"$sysroot/usr/include" \
 tools/media-smoke.cpp src/platform/remote_cache.cpp src/yt/image.cpp host/http_host.cpp host/platform_host.cpp \
 -Wl,--gc-sections -l:libcurl.so.4 -lpthread -lm -o build/media-smoke
build/media-smoke "$@"
