#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
clang++-18 -std=c++20 -O2 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -Isrc tests/story-video-placement.cpp src/museum/catalog.cpp src/core/save_file.cpp -o build/story-video-placement-test
build/story-video-placement-test
python3 - <<'PY'
import runpy
p=runpy.run_path('tools/runtime-catalog.py')
r=p['project']({'entries':[{'id':'film','videos':[{'youtube_id':'AAAAAAAAAAA','story_paragraph':2,'research_note':'excluded'}]}]})
assert r['entries'][0]['videos'][0]['story_paragraph']==2
assert 'research_note' not in r['entries'][0]['videos'][0]
print('PASS: runtime projection retains editorial video position.')
PY
bash tools/preview.sh scenes karateka > build/story-video-placement-scenes.log 2>&1
