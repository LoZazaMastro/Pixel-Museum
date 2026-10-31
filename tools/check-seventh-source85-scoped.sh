#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
export MUSEUM_PREVIEW_ROOT=build/runtime-preview MUSEUM_PREVIEW_4K=1
export MUSEUM_TEXT_PROFILE_CATALOG=build/runtime-preview/content/catalog.json
export MUSEUM_TEXT_PROFILE_PROBE_ENTRIES=workbook-06-27-atari,wii,wikipedia-68026802
out=build/research/seventh-source85-font-scoped
bash tools/preview.sh story-text-profile > "$out/actual-profile.log" 2>&1
bash tools/preview.sh unicode-fonts > "$out/unicode-actual-4k.log" 2>&1
export MUSEUM_PLAYLIST_PROBE_ENTRIES=workbook-02-12-super-mario-3d-world-bowser-s-fury,wikipedia-63528316,wikipedia-56464502,wikipedia-54289600
bash tools/preview.sh playlist > "$out/actual-new-playlists.log" 2>&1
bash tools/preview.sh illustrated-story workbook-06-27-atari > "$out/atari-actual-4k.log" 2>&1
bash tools/preview.sh feature wii feature-wii-social-design > "$out/wii-feature-actual-4k.log" 2>&1
bash tools/preview.sh illustrated-story wikipedia-68026802 > "$out/advance-wars-actual-4k.log" 2>&1
printf 'Seventh scoped source85 current UI/font PASS\n'
