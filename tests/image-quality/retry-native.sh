#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
PS5_PAYLOAD_SDK="$PWD/.deps/native/ps5-payload-sdk" PS5_CLANG=clang-18 USE_CCACHE=0 \
  sh tooling/prospero-clang18 -std=c++20 -O2 -Wall -Wextra -Werror \
  -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections \
  -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I.deps/ps5-opengl/current/include \
  -c src/platform/remote_cache.cpp -o build/photo-retry-native.o
