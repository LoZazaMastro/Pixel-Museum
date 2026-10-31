#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
MUSEUM_COMPILE_ONLY=1 make --jobserver-style=pipe app >build/native-check.log 2>&1
