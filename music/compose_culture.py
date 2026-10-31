#!/usr/bin/env python3
"""An original companion composition, sharing the museum's instruments/clock.

Writes only eras/culture/. The existing videogame recordings stay untouched.
No external recordings, melodies or soundfonts. GPL-3.0-or-later.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import numpy as np
import compose as score

ROOT = Path(__file__).resolve().parent
# A separate eight-chord journey, not alternate voicings of the gaming beds.
# B-flat maj9 / G minor9 / D minor9 / C add9 / G minor9 / B-flat maj9 /
# F maj9 / C add9. The same D-minor/F-major palette keeps short crossfades soft.
CHORDS = [(46,53,57,60,65),(43,50,53,57,62),(50,57,60,64,69),(48,55,60,62,67),
          (43,50,53,57,62),(46,53,57,60,65),(41,48,52,55,60),(48,55,60,62,67)]
MOTIF = [(0.5,74),(2,77),(4.5,81),(6.5,79),
         (8.5,70),(11,74),(13.5,77),
         (16.5,76),(19,77),(21,81),(23,79),
         (25,74),(27,76),(30,79),
         (32.5,70),(35,74),(37.5,77),
         (40.5,81),(43,77),(45.5,74),
         (48.5,72),(51,76),(53.5,79),
         (56.5,79),(59,76),(61.5,74)]
RHYTHMS = [(2,10),(1.5,8.5,13),(0,3.5,7,11.5),(2,5.5,9,12.5),
           (1.5,6,10.5,14),(0.5,4,8.5,13),(3,11),(0,4.5,9,13.5)]

def compose(era):
    out=np.zeros((score.N,2),np.float32)
    rng=np.random.default_rng(41031+era)
    for ci,chord in enumerate(CHORDS):
        start=ci*8
        # Own harmony, bass movement and phrase lengths; synthesis and space
        # stay identical to the gaming palette, with a common sample clock.
        for j,note in enumerate(reversed(chord[1:])):
            score.add(out,start-.75+j*.17,score.voice(note,10.5,'pad',era,j+4),
                      .52-j*.34,.031+era*.001)
        score.add(out,start+.5,score.voice(chord[0]-12,6,'bass',era,0),gain=.115)
        score.add(out,start+5,score.voice(chord[0]-12,3,'bass',era,1),gain=.06)
        for j,at in enumerate(RHYTHMS[era]):
            # The same rounded keys/mallets as the gaming composition, playing
            # a separate answering figure rather than a filter of that track.
            note=chord[1+(j+ci)%4]+(12 if era in (3,5) else 0)
            kind='bell' if era in (0,4,7) else 'keys'
            score.add(out,start+at*.5,score.voice(note,4.5,kind,era,j),
                      -.45 if j%2 else .45,.047 if era!=6 else .04)
            if era in (1,2,7):
                score.add(out,start+at*.5+.26,score.voice(chord[1+(j+2)%4],3,'keys',era,j+2),
                          .35 if j%2 else -.35,.025)
        if era in (2,4,7):
            for j,at in enumerate((2,6)):
                t=np.arange(int(.2*score.SR))/score.SR
                noise=rng.standard_normal(len(t))
                brush=np.convolve(noise,np.ones(7)/7,mode='same')
                signal=brush*np.exp(-t/.045)*(1-np.exp(-t/.006))
                score.add(out,start+at+.12,signal,.2,.022)
    for j,(at,note) in enumerate(MOTIF):
        score.add(out,at,score.voice(note,5,'bell',era,j),math.sin(j*1.3)*.5,.075)
    return score.space(out,era)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ffmpeg',default='ffmpeg');args=parser.parse_args()
    original={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'eras').glob('*.ogg')}
    output=ROOT/'eras/culture';output.mkdir(exist_ok=True)
    levels=json.loads((ROOT/'measurements.json').read_text(encoding='utf8'))['eras']
    report={'composition':'The World Around Us','sample_rate':score.SR,'seconds':score.SECONDS,
            'bpm':60,'shared_sample_clock':True,'independent_chord_progression':True,
            'chord_duration_seconds':8,'chord_midi_notes':CHORDS,'melody_events':MOTIF,
            'same_voice_and_space_implementations':True,'eras':[]}
    for era in range(8):
        audio=compose(era)
        target=10**(levels[era]['rms_dbfs']/20)
        audio*=target/float(np.sqrt(np.mean(audio*audio)))
        # Keep a safety margin even when a crossfade overlaps correlated pads.
        peak=float(np.max(np.abs(audio)))
        if peak>.40:audio*=.40/peak
        path=output/f'{1950+era*10}.ogg';score.encode(args.ffmpeg,path,audio,'The World Around Us / '+score.NAMES[era])
        report['eras'].append({'year':1950+era*10,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'peak':float(np.max(np.abs(audio))),'rms':float(np.sqrt(np.mean(audio*audio))),
          'loop_step_peak':float(np.max(np.abs(audio[0]-audio[-1]))),'bytes':path.stat().st_size})
    assert original=={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in (ROOT/'eras').glob('*.ogg')}
    report['existing_game_music_unchanged']=original
    (ROOT/'culture-measurements.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
