set -euo pipefail
source tools/host-env.sh
python3 tests/localization/prepare_runtime.py
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -Isrc tests/localization/test.cpp src/museum/catalog.cpp src/museum/localization.cpp src/core/save_file.cpp -o build/localization-test
build/localization-test build/localization-runtime
