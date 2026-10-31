#!/usr/bin/env bash
# Same source/pose/renderer comparison; disable only the exact-uniform path in
# an isolated host reference translation unit. Production files stay unchanged.
set -euo pipefail
cd "$(dirname "$0")/../.."
source tools/host-env.sh
out=build/research/model-memory-audit
mkdir -p "$out"
python3 - <<'PY'
from pathlib import Path
p=Path('src/museum/object_scene.cpp').read_text()
marker='if(job.source.rgba.size()>=4){'
assert p.count(marker)==1
Path('build/research/model-memory-audit/object_scene_reference.cpp').write_text(p.replace(marker,'if(false&&job.source.rgba.size()>=4){'))
PY
clang++-18 -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror -DGL_GLEXT_PROTOTYPES=1 \
 -Isrc -I. -I"$sysroot/usr/include" -I"$sysroot/usr/include/x86_64-linux-gnu" \
 tests/object-scene/test.cpp "$out/object_scene_reference.cpp" src/gfx/gl_program.cpp \
 src/yt/image.cpp host/platform_host.cpp -L"$sysroot/usr/lib/x86_64-linux-gnu" \
 -lEGL -l:libGL.so.1 -l:libzstd.so.1 -lpthread -o "$out/reference-viewer"
export EGL_PLATFORM=surfaceless LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe
export __EGL_VENDOR_LIBRARY_FILENAMES="$sysroot/usr/share/glvnd/egl_vendor.d/50_mesa.json"
export LIBGL_DRIVERS_PATH="$sysroot/usr/lib/x86_64-linux-gnu/dri"
for n in 0 1; do
 cp "models/playstation-5.glb-$n.png" "$out/ps5-uniform-$n.png"
 cp "models/wii-u-gamepad.glb-$n.png" "$out/gamepad-uniform-$n.png"
done
"$out/reference-viewer" models/playstation-5.glb 'node:Sketchfab Model.002_108,node:Sketchfab Model.001_100' --size=3840x2160 --yaw=-.35 --tilt=.2 --zoom=1.3 --adaptive-upload > "$out/ps5-reference-4k.log" 2>&1
"$out/reference-viewer" models/wii-u-gamepad.glb --size=3840x2160 --yaw=-.35 --tilt=.13 --zoom=1.3 --adaptive-upload > "$out/gamepad-reference-4k.log" 2>&1
# PNG writer is deterministic and no source pixels or camera state differ.
for n in 0 1; do
 cmp "$out/ps5-uniform-$n.png" "models/playstation-5.glb-$n.png"
 cmp "$out/gamepad-uniform-$n.png" "models/wii-u-gamepad.glb-$n.png"
done
printf '%s\n' 'PASS PS5 and GamePad: two real3840x2160 angles byte-identical to uncollapsed source renderer; cancel/revisit/state GL0.'
