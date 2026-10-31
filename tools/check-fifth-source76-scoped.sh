#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
export MUSEUM_PREVIEW_ROOT=build/runtime-preview
export MUSEUM_PREVIEW_4K=1
export MUSEUM_TEXT_PROFILE_CATALOG=build/runtime-preview/content/catalog.json
export MUSEUM_TEXT_PROFILE_PROBE_ENTRIES=wikipedia-52784993,wikipedia-47748826,wikipedia-52854347,wikipedia-63956111,wikipedia-71748594,super-mario-bros,wii
out=build/research/fifth-source76-font-scoped
bash tools/preview.sh story-text-profile > "$out/actual-profile.log" 2>&1
bash tools/preview.sh unicode-fonts > "$out/unicode-actual-4k.log" 2>&1
export MUSEUM_PLAYLIST_PROBE_ENTRIES=wikipedia-15676843,wikipedia-50574101,daily-04-23
bash tools/preview.sh playlist > "$out/actual-new-playlists.log" 2>&1
for entry in wikipedia-52784993 wikipedia-47748826 wikipedia-52854347 wikipedia-63956111 wikipedia-71748594; do
 bash tools/preview.sh illustrated-story "$entry" > "$out/article-$entry-actual-4k.log" 2>&1
done
python3 tests/font-display-inventory.py > "$out/inventory-unit.log" 2>&1
bash tests/font-shaped-runs.sh > "$out/shaped-runs.log" 2>&1
printf 'Fifth scoped actual composer,5articles,3musicrooms,Unicode4K PASS\n'
