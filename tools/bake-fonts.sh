#!/usr/bin/env bash
# ps5-homebrew-ui - Rebuild the baked SDF fonts in assets/fonts.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Each line of the table is: source TTF, output name, pixel size, SDF range.
# The baker takes two more arguments, the atlas size and the glyph set: an
# app that shows names it did not write can bake `2048 european` (accented
# Latin, Greek and Cyrillic) instead of the `1024` basic set used here.
# To add a typeface, drop its TTF and licence into third_party/fonts, add a
# line here, run `make fonts`, and load the new .huifont where the others are
# loaded (src/main.cpp and host/snapshot_main.cpp).

set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$root/tools/host-env.sh"
cxx=$(command -v "${HOST_CXX:-clang++}")
mkdir -p "$root/build/host" "$root/assets/fonts"
# Never silently bake a catalogue that changed since the last manual subset.
# This also refreshes the source-hash manifest audited after baking.
python3 "$root/tools/prepare-cjk.py"
python3 "$root/tools/prepare-script-runs.py"
"$cxx" -std=c++20 -O2 -w -I"$root/src" "$root/tools/font-baker/bake_font.cpp" "$root/src/gfx/font.cpp" -o "$root/build/host/bake_font"
extra=()
[[ ! -f "$root/build/catalog-codepoints.txt" ]] || extra+=("$root/build/catalog-codepoints.txt")
while read -r source output size range; do
    [[ -n $source ]] || continue
    "$root/build/host/bake_font" "$root/third_party/fonts/$source" \
        "$root/assets/fonts/$output.huifont" "$size" "$range" 2048 european "${extra[@]}"
done <<'FONTS'
Inter-Regular.ttf inter-regular 56 8
Inter-SemiBold.ttf inter-semibold 56 8
Montserrat-Medium.ttf montserrat-medium 56 8
DejaVuSansMono.ttf dejavu-sans-mono 52 8
DejaVuSans.ttf unicode-fallback 56 8
FONTS
if [[ -f "$root/third_party/fonts/NotoSansCJKjp-Regular.ttf" && ${#extra[@]} -gt 0 ]]; then
    "$root/build/host/bake_font" "$root/build/research/offline-script-shaping/shaped-fallback.ttf" \
        "$root/assets/fonts/cjk-subset.huifont" 56 8 2048 basic "$root/build/research/offline-script-shaping/codepoints.txt" 4096
    python3 "$root/tools/attach-font-runs.py"
fi
cp "$root"/third_party/fonts/*-LICENSE.txt "$root/assets/fonts/"
python3 "$root/tools/audit-font-coverage.py"
