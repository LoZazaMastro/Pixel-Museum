#!/usr/bin/env bash
# Pixel Museum - Resolve one live YouTube stream using the real native service code.
# Copyright (C) 2026 Andrea Sgarro
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
mkdir -p build/host-include
[[ -d build/host-include/curl ]] || cp -r .deps/pacbrew/v0.40.2/sysroot/user/homebrew/include/curl build/host-include/
clang-18 -O2 -Isrc -c src/third_party/yyjson/yyjson.c -o build/yyjson-smoke.o
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc -I. -Ibuild/host-include \
 tools/video-smoke.cpp host/http_host.cpp src/yt/innertube.cpp src/yt/comments.cpp src/yt/types.cpp src/yt/log.cpp \
 src/yt/codec.cpp src/yt/http.cpp src/yt/decipher.cpp build/yyjson-smoke.o -l:libcurl.so.4 -lpthread -lm -o build/video-smoke
build/video-smoke "$@"
