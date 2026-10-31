#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
clang-18 -std=c11 -D_GNU_SOURCE=1 -DMUSEUM_LARGE_HEAP_MIB=32 -Wall -Wextra -Wpedantic -Werror \
 -Isrc tools/large-heap-test.c src/runtime/large_heap.c src/runtime/app_heap.c -lpthread -o build/large-heap-test
build/large-heap-test
