#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
python3 tests/object-scene/material-fixtures.py
bash tests/object-scene/bake-artwork-cache.sh build/material-fixtures/packed-*.glb build/material-fixtures/union-*.glb
bash tests/object-scene/materials.sh
