#!/usr/bin/env bash
set -euo pipefail
cd '/mnt/f/Playhub/PS5/Pixel Museum'
export MUSEUM_PREVIEW_ROOT=build/runtime-preview MUSEUM_PREVIEW_4K=1
export MUSEUM_TEXT_PROFILE_CATALOG=build/runtime-preview/content/catalog.json
export MUSEUM_TEXT_PROFILE_PROBE_ENTRIES=daily-11-25,workbook-10-22-grand-theft-auto-2,daily-12-12,roberta-williams,workbook-07-28-lua,minecraft
out=build/research/tenth-source86-scoped
bash tools/preview.sh story-text-profile > "$out/actual-profile.log" 2>&1
bash tools/preview.sh unicode-fonts > "$out/unicode-actual-4k.log" 2>&1
bash tools/preview.sh tenth-scoped > "$out/actual-five-prose-four-media.log" 2>&1
