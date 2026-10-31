#!/usr/bin/env python3
"""Original sustained entrance bed, extracted from our gaming score's pad voices.

No melody, keys, bells, bass pulse, percussion or arpeggio is rendered.
SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import numpy as np
import compose as score

ROOT = Path(__file__).resolve().parent


def compose():
    out = np.zeros((score.N, 2), np.float32)
    events = []
    for ci, chord in enumerate(score.CHORDS):
        for index, note in enumerate(chord[1:]):
            start = ci * 16 - .8 + index * .10
            score.add(out, start, score.voice(note, 19., 'pad', 0, index),
                      [-.55, .25, -.15, .55][index], .043)
            events.append(dict(start=start, duration=19., kind='pad', midi=note))
    return score.space(out, 0), events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ffmpeg', default='ffmpeg')
    args = parser.parse_args()
    existing = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (ROOT/'eras').rglob('*.ogg') if 'onboarding' not in p.parts}
    audio, events = compose()
    # Quiet, but present: no lowering a complete melodic mix to hide its lead.
    audio *= .045 / float(np.sqrt(np.mean(audio*audio)))
    path = ROOT/'eras/onboarding/intro.ogg'
    path.parent.mkdir(exist_ok=True)
    if args.ffmpeg == 'wsl':
        output = '/mnt/'+path.drive[0].lower()+path.as_posix()[2:]
        command = ['wsl', 'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                   '-f', 's16le', '-ar', str(score.SR), '-ac', '2', '-i', 'pipe:0',
                   '-c:a', 'libvorbis', '-q:a', '4', '-metadata',
                   'title=Before the First Gallery', '-metadata', 'artist=Pixel Museum',
                   '-metadata', 'LOOPSTART=0', '-metadata', 'LOOPLENGTH='+str(score.N), output]
        pcm = np.rint(np.clip(audio, -1, 1)*32767).astype('<i2')
        subprocess.run(command, input=pcm.tobytes(), check=True)
    else:
        score.encode(args.ffmpeg, path, audio, 'Before the First Gallery')
    assert existing == {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (ROOT/'eras').rglob('*.ogg') if 'onboarding' not in p.parts}
    report = dict(title='Before the First Gallery', source='Original Pixel Museum synthesis',
                  generator='compose_onboarding.py', shared_voice_and_space='compose.py',
                  sample_rate=score.SR, seconds=score.SECONDS,
                  chord_midi_notes=score.CHORDS, events=events,
                  excluded_voices=['keys', 'bell', 'bass', 'percussion', 'arpeggio', 'melody'],
                  rms=float(np.sqrt(np.mean(audio*audio))), peak=float(np.abs(audio).max()),
                  loop_step_peak=float(np.abs(audio[0]-audio[-1]).max()),
                  path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  existing_game_and_culture_sha256=existing)
    (ROOT/'onboarding-measurements.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
