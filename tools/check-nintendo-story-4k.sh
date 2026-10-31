#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
MUSEUM_PREVIEW_4K=1 bash tools/preview.sh illustrated-story daily-09-23 > build/research/nintendo-complete-story/actual-screen-4k.log 2>&1
