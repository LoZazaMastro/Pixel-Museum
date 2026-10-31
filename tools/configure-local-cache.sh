#!/usr/bin/env bash
# Pixel Museum - Optional local reuse of a pre-existing, complete dependency cache.
# Copyright (C) 2026 Andrea Sgarro
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
old=${1:?Pass the absolute path to a complete native homebrew build checkout}
[[ -x "$old/.deps/native/ps5-payload-sdk/bin/prospero-lld" && -d "$old/.deps/pacbrew/v0.40.2/sysroot" ]] || exit 2
mkdir -p "$root/.deps/ps5-opengl" "$root/.deps/pacbrew" "$root/build"
[[ -e "$root/.deps/native" ]] || ln -s "$old/.deps/native" "$root/.deps/native"
[[ -e "$root/.deps/pacbrew/v0.40.2" ]] || ln -s "$old/.deps/pacbrew/v0.40.2" "$root/.deps/pacbrew/v0.40.2"
[[ -e "$root/.deps/pacbrew/ps5-payload-dev-v0.40.2.tar.gz" ]] || ln -s "$old/.deps/pacbrew/ps5-payload-dev-v0.40.2.tar.gz" "$root/.deps/pacbrew/ps5-payload-dev-v0.40.2.tar.gz"
[[ -e "$root/build/host-sysroot" ]] || ln -s "$old/build/host-sysroot" "$root/build/host-sysroot"
prefix=$(readlink -f "$old/.deps/ps5-opengl/current")
printf 'PS5_OPENGL_PREFIX=%s\n' "$prefix" > "$root/.env"
