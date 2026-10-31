#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
export MUSEUM_PREVIEW_ROOT=build/runtime-preview MUSEUM_PREVIEW_4K=1
export MUSEUM_TEXT_PROFILE_CATALOG=build/runtime-preview/content/catalog.json
export MUSEUM_TEXT_PROFILE_PROBE_ENTRIES=workbook-08-13-gyromite,workbook-04-07-atlus,mega-drive,workbook-06-19-treasure,daily-01-09
out=build/research/ninth-source86-font-scoped
python3 tools/audit-font-coverage.py > "$out/font-revalidation.log" 2>&1
bash tools/preview.sh story-text-profile > "$out/actual-profile.log" 2>&1
export MUSEUM_PLAYLIST_PROBE_ENTRIES=burnout-revenge
bash tools/preview.sh playlist > "$out/actual-burnout40-playlist.log" 2>&1
bash tools/preview.sh ninth-scoped > "$out/actual-new-media-mega-lua.log" 2>&1
