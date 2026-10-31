#!/usr/bin/env bash
set -euo pipefail
export MUSEUM_PREVIEW_4K=1
bash tools/preview.sh search > build/search-preview-4k.log 2>&1
bash tools/preview.sh playlist > build/playlist-multiroom-preview.log 2>&1
