#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
python3 content/expansion/check_wikipedia_locale_overlays.py
python3 - <<'PY'
from pathlib import Path
import runpy
join = runpy.run_path('content/expansion/integrate_wikipedia_locales.py')
content = Path('content')
documents, _ = join['build'](join['read'](content/'catalog.json'),
    {language:join['read'](content/'locales'/f'{language}.json') for language in join['LANGUAGES']},
    {name:join['read'](content/'expansion'/name) for name in join['BATCH_IDS']})
destination = Path('build/wikipedia-locale-fixture/content/locales')
destination.mkdir(parents=True, exist_ok=True)
for language, document in documents.items():
    (destination/f'{language}.json').write_bytes(join['encoded'](document))
PY
clang++-18 -std=c++20 -O2 -fno-exceptions -fno-rtti -Isrc \
 tests/wikipedia_locale_overlay_test.cpp src/museum/catalog.cpp src/core/save_file.cpp \
 -o build/wikipedia-locale-overlay-test
build/wikipedia-locale-overlay-test content/catalog.json build/wikipedia-locale-fixture
