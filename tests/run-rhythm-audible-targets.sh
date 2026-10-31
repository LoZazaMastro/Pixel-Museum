set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc tests/rhythm-audible-targets.cpp src/museum/experience_audio.cpp src/audio/controller_feedback.cpp -o build/rhythm-audible-targets-test
build/rhythm-audible-targets-test
