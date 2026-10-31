#!/usr/bin/env bash
set -euo pipefail
bash tools/preview.sh story-audit > build/narrative-cards-audit.log 2>&1
