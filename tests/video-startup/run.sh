set -euo pipefail
source tools/host-env.sh
mkdir -p build/video-startup
clang-18 -O2 -Isrc -c src/third_party/yyjson/yyjson.c -o build/video-startup/yyjson.o
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -Isrc tests/video-startup/test.cpp src/yt/innertube.cpp src/yt/types.cpp build/video-startup/yyjson.o -Wl,--gc-sections -lpthread -o build/video-startup/test
build/video-startup/test
clang++-18 -std=c++20 -Wall -Wextra -Wpedantic -Werror -fno-exceptions -fno-rtti -Isrc -fsyntax-only src/yt/service.cpp
