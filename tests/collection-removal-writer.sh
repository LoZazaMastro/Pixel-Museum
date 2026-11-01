#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../tools/host-env.sh"
cd "$root"
report=build/research/collection-removal-crashfix
mkdir -p "$report"
clang-18 -std=gnu11 -O1 -g -Wall -Wextra -Werror -DPMCW_HOST_TEST -Isrc \
  tools/collection-writer/collection_writer.c -o "$report/helper-host"
clang++-18 -std=c++20 -O1 -g -Wall -Wextra -Werror -DMUSEUM_COLLECTION_WRITER_TEST -Isrc -I. \
  tests/collection-removal-writer.cpp src/platform/collection_writer.cpp -lpthread -o "$report/writer-tests"
"$report/writer-tests" "$report/helper-host" 2>&1 | tee "$report/writer-tests.log"
