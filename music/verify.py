#!/usr/bin/env python3
"""Check the distributed Vorbis files after lossy encoding, not just the masters."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--ffmpeg', default='ffmpeg')
args = parser.parse_args()
root = Path(__file__).resolve().parent
report = []
stems = []
for year in range(1950, 2030, 10):
    data = subprocess.check_output([args.ffmpeg, '-hide_banner', '-loglevel', 'error',
        '-i', str(root/'eras'/f'{year}.ogg'), '-f', 'f32le', '-acodec', 'pcm_f32le', 'pipe:1'])
    pcm = np.frombuffer(data, dtype='<f4').reshape(-1, 2)
    assert pcm.shape == (24000*64, 2), (year, pcm.shape)
    assert np.isfinite(pcm).all()
    peak = float(np.max(np.abs(pcm)))
    boundary = float(np.max(np.abs(pcm[0]-pcm[-1])))
    normal = float(np.quantile(np.abs(np.diff(pcm, axis=0)), .99))
    assert peak < .48 and boundary < normal
    report.append({'year': year, 'frames': len(pcm), 'peak':peak,
        'rms':float(np.sqrt(np.mean(pcm*pcm))), 'loop_boundary_step':boundary,
        'adjacent_step_p99':normal})
    stems.append(pcm)
for i in range(7):
    mixed = .5*(stems[i]+stems[i+1])
    assert float(np.max(np.abs(mixed))) < .48
    correlation = float(np.sum(stems[i]*stems[i+1])/np.sqrt(np.sum(stems[i]*stems[i])*np.sum(stems[i+1]*stems[i+1])))
    relative_difference = float(np.sqrt(np.mean((stems[i]-stems[i+1])**2))/np.sqrt(np.mean(stems[i]*stems[i])))
    assert correlation < .94 and relative_difference > .34, (1950+i*10,correlation,relative_difference)
    report[i]['next_era_correlation']=correlation
    report[i]['next_era_relative_difference']=relative_difference
rms = [row['rms'] for row in report]
assert 20*np.log10(max(rms)/min(rms)) < .7
(root/'encoded-measurements.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print('PASS: all eight encoded stems have exactly 1,536,000 stereo frames, finite samples,')
print('headroom, unobtrusive loop boundaries, safe constant-sum blends, matched levels,')
print('and objectively distinct adjacent arrangements (not merely tiny EQ changes).')
