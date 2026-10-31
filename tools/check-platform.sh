#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
mkdir -p build/host-include
# curl's public C headers are platform-neutral; the host links its own libcurl.
if [[ ! -d build/host-include/curl ]]; then
 cp -r .deps/pacbrew/v0.40.2/sysroot/user/homebrew/include/curl build/host-include/
fi
for file in src/platform/remote_cache.cpp src/platform/video.cpp; do
 clang++-18 -std=c++20 -fno-exceptions -fno-rtti -Wall -Wextra -Wpedantic -Werror \
 -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -Ibuild/host-include -fsyntax-only "$file"
done
