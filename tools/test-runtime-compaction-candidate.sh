#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source tools/host-env.sh
base=build/research/runtime-compaction-source73
for variant in original candidate original candidate original candidate; do
    printf '%s: ' "$variant"
    build/runtime-catalog-load-benchmark "$base/$variant-runtime.json"
done > "$base/native-load-benchmark.log" 2>&1
for variant in original candidate; do
    MUSEUM_TEXT_PROFILE_CATALOG="$base/$variant-runtime.json" \
    MUSEUM_COMPOSITION_SNAPSHOT="$base/$variant-composition.json" \
    MUSEUM_PROFILE_OUTPUT="$base/$variant-gap-profile.json" \
    MUSEUM_PREVIEW_ROOT=build/runtime-preview MUSEUM_PREVIEW_4K=1 \
    bash tools/preview.sh story-text-profile > "$base/$variant-actual-composition.log" 2>&1
done
