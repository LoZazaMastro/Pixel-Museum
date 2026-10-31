set -euo pipefail
source tools/host-env.sh
mkdir -p build/video-startup
clang-18 -O2 -Isrc -c src/third_party/yyjson/yyjson.c -o build/video-startup/yyjson.o
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -fno-exceptions -fno-rtti -ffunction-sections -fdata-sections -Isrc tests/video-startup/service.cpp src/yt/service.cpp src/yt/innertube.cpp src/yt/codec.cpp src/yt/decipher.cpp src/yt/auth.cpp src/yt/watch.cpp src/yt/comments.cpp src/yt/types.cpp src/yt/http.cpp src/core/save_file.cpp build/video-startup/yyjson.o -Wl,--gc-sections -lpthread -o build/video-startup/service-test
build/video-startup/service-test
