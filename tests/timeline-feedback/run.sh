set -euo pipefail
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -Isrc tests/timeline-feedback/test.cpp src/audio/controller_feedback.cpp -lpthread -o build/timeline-feedback-test
build/timeline-feedback-test
