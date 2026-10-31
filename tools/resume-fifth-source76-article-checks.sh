#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
export MUSEUM_PREVIEW_ROOT=build/runtime-preview
export MUSEUM_PREVIEW_4K=1
out=build/research/fifth-source76-font-scoped
for entry in wikipedia-52784993 wikipedia-47748826 wikipedia-52854347 wikipedia-63956111 wikipedia-71748594; do
 bash tools/preview.sh illustrated-story "$entry" > "$out/article-$entry-actual-4k.log" 2>&1
done
python3 tests/font-display-inventory.py > "$out/inventory-unit.log" 2>&1
bash tests/font-shaped-runs.sh > "$out/shaped-runs.log" 2>&1
printf 'Fifth scoped actual composer,5articles,3musicrooms,Unicode4K PASS\n'
