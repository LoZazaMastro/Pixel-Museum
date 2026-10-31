#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
mkdir -p build/research/model-sidecar-v2-probe
python3 tests/object-scene/material-fixtures.py
bash tests/object-scene/bake-artwork-cache.sh --v2 build/material-fixtures/packed-orm-10497-9987.glb
python3 - <<'PY'
from pathlib import Path
import json,subprocess
data=json.loads(Path('build/material-fixtures/manifest.json').read_text())
paths=['build/material-fixtures/'+r['file'] for r in data['cases'] if r.get('expected_error') is None]
subprocess.run(['build/bake-artwork-cache','--v2',*paths],check=True)
PY
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" tests/object-scene/cache-v2-parity.cpp src/gfx/gl_program.cpp src/yt/image.cpp host/platform_host.cpp -L"$sysroot/usr/lib/x86_64-linux-gnu" -lEGL -l:libGL.so.1 -l:libzstd.so.1 -lpthread -o build/cache-v2-parity-test
build/cache-v2-parity-test build/material-fixtures/packed-orm-10497-9987.glb build/material-fixtures/uniform-orm-10497-9987.glb build/material-fixtures/uniform-colour-10497-9987.glb build/material-fixtures/union-orm-ao-10497-9987.glb
bash tests/object-scene/materials.sh
