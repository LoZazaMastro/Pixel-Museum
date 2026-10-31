#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
export MUSEUM_PREVIEW_ROOT=build/runtime-preview MUSEUM_PREVIEW_4K=1
export MUSEUM_TEXT_PROFILE_CATALOG=build/runtime-preview/content/catalog.json
export MUSEUM_TEXT_PROFILE_PROBE_ENTRIES=workbook-01-07-game-boy-advance-sp,daily-06-15,dandara,workbook-10-15-disco-elysium,animal-crossing
out=build/research/sixth-source81-font-scoped
bash tools/preview.sh story-text-profile > "$out/actual-profile.log" 2>&1
bash tools/preview.sh unicode-fonts > "$out/unicode-actual-4k.log" 2>&1
export MUSEUM_PLAYLIST_PROBE_ENTRIES=wikipedia-43295977,workbook-04-14-mortal-kombat-x,wikipedia-45032491,wikipedia-75025557,wikipedia-57661331
bash tools/preview.sh playlist > "$out/actual-new-playlists.log" 2>&1
bash tools/preview.sh illustrated-story workbook-01-07-game-boy-advance-sp > "$out/sp-actual-4k.log" 2>&1
bash tools/preview.sh feature dandara feature-latin-american-art-voices > "$out/dandara-feature-actual-4k.log" 2>&1
bash tools/preview.sh feature workbook-10-15-disco-elysium feature-disco-elysium-authorship > "$out/disco-feature-actual-4k.log" 2>&1
bash tools/preview.sh feature animal-crossing feature-pandemic-shared-spaces > "$out/acnh-feature-actual-4k.log" 2>&1
python3 tests/font-display-inventory.py > "$out/inventory-unit.log" 2>&1
bash tests/font-shaped-runs.sh > "$out/shaped-runs.log" 2>&1
printf 'Sixth scoped source81 current UI/font PASS\n'
