#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash tests/object-scene/run.sh downloads-original/nintendo_switch_2.glb --size=3840x2160 --yaw=-0.35 > build/research/model-validation/switch2-renewed-render.log 2>&1
bash tests/object-scene/run.sh downloads-original/wii_u_gamepad_controller__stand.glb --size=3840x2160 --yaw=-0.35 > build/research/model-validation/wiiu-gamepad-renewed-render.log 2>&1
