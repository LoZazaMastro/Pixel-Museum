#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
MUSEUM_PREVIEW_4K=1 bash tools/preview.sh illustrated-story workbook-06-10-yu-suzuki > build/research/yu-suzuki-complete-story/actual-screen-4k.log 2>&1
