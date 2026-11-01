#!/usr/bin/env bash
# Standalone no-network, no-production-data collection-removal regression.
set -euo pipefail
source "$(dirname "$0")/../tools/host-env.sh"
cd "$root"
report=build/research/collection-removal-0.1.4
mkdir -p "$report"
clang++-18 -std=c++20 -O1 -Wall -Wextra -Wpedantic -Werror \
  -Wno-missing-field-initializers -Wno-unused-variable -Wno-unused-but-set-variable \
  -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" -Ibuild/host-include \
  tests/collection-removal.cpp src/museum/collection_installer.cpp \
  -Wl,--wrap=unlinkat,--wrap=lstat,--wrap=curl_easy_perform \
  -L"$sysroot/usr/lib/x86_64-linux-gnu" -l:libcurl.so.4 -lpthread -o "$report/backend-test"
"$report/backend-test" | tee "$report/backend.log"
