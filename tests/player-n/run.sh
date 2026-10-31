set -euo pipefail
source tools/host-env.sh
mkdir -p build/player-n
clang-18 -O2 -Isrc -c src/third_party/yyjson/yyjson.c -o build/player-n/yyjson.o
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -Isrc tests/player-n/test.cpp src/yt/innertube.cpp src/yt/decipher.cpp src/yt/types.cpp build/player-n/yyjson.o -Wl,--gc-sections -lpthread -o build/player-n/test
build/player-n/test "${1:-build/research/video403-live/observed-tv-player-cbcfbf2f.js}"
