#!/usr/bin/env python3
"""Verify both distributed compositions after Vorbis encoding."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--ffmpeg', default='ffmpeg')
args = parser.parse_args()
root = Path(__file__).resolve().parent
generation = json.loads((root/'culture-measurements.json').read_text(encoding='utf8'))
report = []
for year in range(1950,2030,10):
    pair = []
    for relative in (f'{year}.ogg',f'culture/{year}.ogg'):
        path=root/'eras'/relative
        decoded=subprocess.check_output([args.ffmpeg,'-v','error','-i',str(path),
            '-f','f32le','-acodec','pcm_f32le','pipe:1'])
        pcm=np.frombuffer(decoded,dtype='<f4').reshape(-1,2)
        assert pcm.shape==(24000*64,2) and np.isfinite(pcm).all(),relative
        assert float(np.max(np.abs(pcm)))<.48,relative
        assert float(np.max(np.abs(pcm[0]-pcm[-1])))<.015,relative
        pair.append(pcm)
    game,culture=pair
    difference=float(np.sqrt(np.mean((game-culture)**2))/np.sqrt(np.mean(game*game)))
    assert difference>.5,(year,difference)
    for mix in (.25,.5,.75):
        assert float(np.max(np.abs(game*(1-mix)+culture*mix)))<.48
    game_hash=hashlib.sha256((root/'eras'/f'{year}.ogg').read_bytes()).hexdigest()
    assert game_hash==generation['existing_game_music_unchanged'][f'{year}.ogg']
    report.append({'year':year,'relative_composition_difference':difference,
        'culture_loop_boundary_step':float(np.max(np.abs(culture[0]-culture[-1]))),
        'culture_peak':float(np.max(np.abs(culture))),
        'gaming_recording_unchanged':True})
(root/'culture-encoded-measurements.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print('PASS: 16 encoded files, exact 64-second stereo duration, distinct compositions, safe crossfade levels, loop boundaries and unchanged gaming recordings.')
