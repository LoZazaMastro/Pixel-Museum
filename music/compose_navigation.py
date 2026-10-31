#!/usr/bin/env python3
"""Regenerate and stage Pixel Museum's original interface bank."""
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    runpy.run_path(str(ROOT/'music/compose_interface.py'),run_name='__main__')
    runpy.run_path(str(ROOT/'music/stage_interface.py'),run_name='__main__')
