set -euo pipefail
source tools/host-env.sh
mkdir -p build/video-startup
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc -I.deps/pacbrew/v0.40.2/sysroot/user/homebrew/include tests/video-startup/range.cpp src/platform/ps5/range_stream.cpp -l:libcurl.so.4 -lpthread -o build/video-startup/range-test
python3 tests/video-startup/range.py
