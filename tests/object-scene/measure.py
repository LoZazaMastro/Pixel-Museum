#!/usr/bin/env python3
"""Measure one real renderer check; host Mesa GPU storage is included in RSS.

SPDX-License-Identifier: GPL-3.0-or-later
This is not a measurement of the PS5's separate CPU/GPU allocation pools.
"""
import json
import resource
import subprocess
import sys
import time

started = time.monotonic()
result = subprocess.run(["bash", "tests/object-scene/run.sh", *sys.argv[1:]], check=False)
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
print(json.dumps({
    "asset": sys.argv[1], "exit_code": result.returncode,
    "elapsed_seconds": round(time.monotonic() - started, 3),
    "host_peak_rss_kib": usage.ru_maxrss,
    "measurement_scope": "Host llvmpipe process: CPU staging, software GPU storage, targets and repeated request checks. Not PS5 pool residency.",
}, indent=2), flush=True)
raise SystemExit(result.returncode)
