#!/usr/bin/env bash
# Pixel Museum - Build the independently identified Media application.
# Copyright (C) 2026 Andrea Sgarro
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
source "$(dirname "$0")/host-env.sh"
cd "$root"
make --jobserver-style=pipe app > build/ps5-build.log 2>&1
python3 tools/package-museum.py
