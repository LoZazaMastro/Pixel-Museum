set -euo pipefail
source tools/host-env.sh
clang-18 -O2 -Isrc -c src/third_party/yyjson/yyjson.c -o build/captions-yyjson.o
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -Isrc tests/captions/test.cpp src/yt/captions.cpp src/yt/innertube.cpp src/yt/types.cpp build/captions-yyjson.o -Wl,--gc-sections -lpthread -o build/captions-test
build/captions-test
