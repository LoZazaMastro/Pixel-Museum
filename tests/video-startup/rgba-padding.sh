#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
mkdir -p build/video-startup
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -I.deps/pacbrew/v0.40.2/sysroot/user/homebrew/include tests/video-startup/rgba-padding.cpp -l:libswscale.so.8 -l:libavutil.so.59 -o build/video-startup/rgba-padding-test
build/video-startup/rgba-padding-test
