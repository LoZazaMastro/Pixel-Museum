#!/usr/bin/env python3
"""Compose Pixel Museum's original, phase-aligned circular ambient score.

Requires Python 3.10+, numpy, and ffmpeg on PATH (or --ffmpeg).
No recordings, sound fonts, or melodies are imported. SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import argparse
import json
import math
import subprocess
import wave
import numpy as np

SR = 24000
SECONDS = 64
N = SR * SECONDS
ROOT = Path(__file__).resolve().parent
# One slow 16-bar phrase, 60 BPM. These rootless extended voicings resolve
# through D minor, F major, B-flat major and A suspended back to D minor.
CHORDS = [(50, 57, 60, 64, 69), (53, 60, 64, 67, 74),
          (46, 53, 57, 60, 65), (45, 52, 55, 62, 64)]
NAMES = ['First Signals', 'Open Circuits', 'Warm Machines', 'Glass Memory',
         'After Hours', 'Quiet Networks', 'Soft Horizons', 'Common Ground']
MOTIF = [(2.5, 76), (6.0, 72), (11.5, 69), (19.0, 74), (23.5, 76),
         (30.0, 79), (35.0, 77), (39.5, 72), (46.0, 69), (51.0, 74), (58.5, 76)]

def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)

def add(out, start, signal, pan=0.0, gain=1.0):
    """Add an event on a circular timeline, retaining its natural release."""
    indices = (int(start * SR) + np.arange(len(signal))) % N
    angle = (pan + 1) * np.pi / 4
    np.add.at(out[:, 0], indices, signal * math.cos(angle) * gain)
    np.add.at(out[:, 1], indices, signal * math.sin(angle) * gain)

def voice(midi, duration, kind, era, seed):
    t = np.arange(int(duration * SR), dtype=np.float64) / SR
    f = hz(midi)
    attack = {'pad': 1.5, 'keys': .018, 'bass': .045, 'bell': .012}[kind]
    release = {'pad': 3.8, 'keys': 1.7, 'bass': .8, 'bell': 2.2}[kind]
    envelope = (1 - np.exp(-t / attack)) * (1 - np.exp(-(duration-t) / release))
    if kind == 'pad':
        signal = (np.sin(2*np.pi*f*t + .09*np.sin(2*np.pi*.12*t))
                  + .25*np.sin(2*np.pi*f*1.0017*t + .6)
                  + .13*np.sin(2*np.pi*f*2*t + .3)) / 1.38
        envelope *= .86 + .14*np.sin(2*np.pi*.07*t + seed)
    elif kind == 'keys':
        # Deliberately different instruments, not eight almost identical EQs.
        depth = [.09, .18, .32, 1.12, .46, .82, .14, .58][era]
        ratio = [2, 1, 2, 2, 1, 3, 2, 2][era]
        mod = depth*np.exp(-t/1.4)*np.sin(2*np.pi*f*ratio*t)
        signal = np.sin(2*np.pi*f*t + mod) + .16*np.sin(2*np.pi*f*3*t)*np.exp(-t/.4)
        if era == 1:
            signal += .34*np.sin(2*np.pi*f*2*t) + .15*np.sin(2*np.pi*f*4*t)
            envelope *= .88+.12*np.sin(2*np.pi*4.1*t)
        elif era == 2:
            signal += .25*np.sin(2*np.pi*f*2*t)*np.exp(-t/1.2)
        elif era == 6:
            envelope *= np.exp(-t/1.5)
        envelope *= np.exp(-t/(2.8 + .1*era))
    elif kind == 'bass':
        signal = np.sin(2*np.pi*f*t) + .12*np.sin(2*np.pi*2*f*t)
        envelope *= np.exp(-t/3.8)
    else:
        signal = (np.sin(2*np.pi*f*t + .45*np.exp(-t/.6)*np.sin(2*np.pi*f*2*t))
                  + .13*np.sin(2*np.pi*f*2.003*t)*np.exp(-t/.7))
        envelope *= np.exp(-t/(1.9 + era*.16))
    return (signal * envelope).astype(np.float32)

def space(signal, era):
    """Circular early reflections and a quiet, progressively wider diffuse tail."""
    out = signal.copy()
    for delay, gain in [(.227, .13), (.381, .10), (.619, .08), (1.031, .055),
                        (1.667, .036), (2.431, .023), (3.719, .014)]:
        reflected = np.roll(signal[:, ::-1], int(delay*SR), axis=0)
        out += reflected * gain
    mid = (out[:, 0]+out[:, 1])*.5
    side = (out[:, 0]-out[:, 1])*(.34+era*.045)
    out[:, 0] = mid+side
    out[:, 1] = mid-side
    # A periodic spectral filter prevents edge state and keeps the score soft.
    spectrum = np.fft.rfft(out, axis=0)
    freq = np.fft.rfftfreq(N, 1/SR)
    lp = 1 / np.sqrt(1+(freq/(3600+era*360))**8)
    hp = (1-np.exp(-(freq/32)**4))
    spectrum *= (lp*hp)[:, None]
    return np.fft.irfft(spectrum, n=N, axis=0).astype(np.float32)

def compose(era):
    rng = np.random.default_rng(8241+era)
    out = np.zeros((N, 2), np.float32)
    for chord_index, chord in enumerate(CHORDS):
        start = chord_index*16
        # Pad enters before the chord and overlaps the following harmony.
        for index, note in enumerate(chord[1:]):
            add(out, start-.8+index*.10, voice(note, 19.0, 'pad', era, index),
                [-.55, .25, -.15, .55][index], .043 + era*.0015)
        add(out, start, voice(chord[0]-12, 11.0, 'bass', era, 0), gain=.14)
        add(out, start+10, voice(chord[0]-12, 5.5, 'bass', era, 0), gain=.077)
        # Deliberately voiced, sparse lounge chords; no machine-gun arpeggio.
        for beat, amp in [(1.0,.070), (7.5,.042), (12.0,.053)]:
            for index, note in enumerate(chord[1:]):
                add(out, start+beat+index*.037, voice(note, 5.5, 'keys', era, index),
                    -.27+index*.18, amp/(1+index*.08))
    for index, (at, note) in enumerate(MOTIF):
        # Same modest melody is heard through different generations of timbre.
        add(out, at, voice(note, 5.5, 'bell', era, index),
            math.sin(index*1.8)*.48, .045 if era < 3 else .053)
    # Timbral history is an allusion, not an imitation of copyrighted hardware audio.
    for beat in range(64):
        if beat % 4 == 0:
            t = np.arange(int(.30*SR))/SR
            kick = np.sin(2*np.pi*(48*t+2.9*(1-np.exp(-t/.035))))*np.exp(-t/.08)
            add(out, beat+.01, kick, gain=.010+era*.0018)
        if era >= 2 and beat % 2 == 1:
            t = np.arange(int(.11*SR))/SR
            noise = rng.standard_normal(len(t))
            brushed = np.convolve(noise, np.ones(9)/9, mode='same')
            add(out, beat+.035, brushed*np.exp(-t/.028)*(1-np.exp(-t/.003)),
                .36 if beat%4 else -.3, .014 + era*.001)
    if era >= 3:
        for at, note in [(5,81),(21,79),(37,77),(53,76)]:
            t = np.arange(int(1.8*SR))/SR
            f = hz(note)
            pulse = (np.sin(2*np.pi*f*t)+.12*np.sin(2*np.pi*f*3*t))
            add(out, at, pulse*np.sin(np.pi*np.minimum(t/.13,1)/2)**2*np.exp(-t/.24),
                -.3 if at%3 else .3, .007 if era < 5 else .003)
    if era >= 5:
        for i, (at,note) in enumerate(MOTIF[::2]):
            add(out, at+.75, voice(note+12, 7.5, 'pad', era, i),
                math.sin(i)*.7, .006+(era-5)*.002)
    # Each era has a clearly audible accompaniment throughout the phrase.
    # Notes follow the same harmony and all events remain on the shared clock.
    for ci, chord in enumerate(CHORDS):
        start = ci*16
        if era == 0:
            # Close, unhurried chamber-electronic counterline.
            for j,(beat,interval) in enumerate([(0,0),(4,7),(8,12),(12,7)]):
                add(out,start+beat,voice(chord[0]+interval,5,'bell',0,j),-.2+j*.12,.062)
        elif era == 1:
            # Rounded drawbar-like sustained chords, with a slow rotary pulse.
            for j,note in enumerate(chord[1:]):
                t=np.arange(int(18*SR))/SR
                organ=(np.sin(2*np.pi*hz(note)*t)+.38*np.sin(2*np.pi*hz(note)*2*t)+.16*np.sin(2*np.pi*hz(note)*3*t))
                env=(1-np.exp(-t/.25))*(1-np.exp(-(18-t)/1.8))*(.8+.2*np.sin(2*np.pi*3.3*t+j))
                add(out,start-.5,organ*env,(-.7+j*.46),.036)
        elif era == 2:
            # Syncopated analog bass and softly brushed backbeats.
            for j,beat in enumerate([0,2.5,4,6.5,8,10.5,12,14.5]):
                add(out,start+beat,voice(chord[0]-12+(12 if j%3==2 else 0),2,'bass',era,j),0,.085)
        elif era == 3:
            # Glassy FM arpeggio: intentional chords, no game tune quotations.
            for j,beat in enumerate([0,.75,2,3.5,4.75,6,8,8.75,10,11.5,12.75,14]):
                add(out,start+beat,voice(chord[1+j%4]+12,2.6,'keys',era,j),math.sin(j)*.55,.052)
        elif era == 4:
            # Loose, low-register mallets with a downtempo kit.
            for j,beat in enumerate([.5,3,6.5,9,11,14.5]):
                add(out,start+beat,voice(chord[1+j%4],3.4,'bell',era,j),(-.5 if j%2 else .5),.095)
        elif era == 5:
            # Sparse digital plucks and a high, diffuse harmonic halo.
            for j,beat in enumerate([0,1.5,4.5,7,8,9.5,12.5,15]):
                add(out,start+beat,voice(chord[1+j%4]+12,4.2,'keys',era,j),math.sin(j*2.3)*.75,.066)
            for j,note in enumerate(chord[2:]):
                add(out,start-1,voice(note+12,20,'pad',era,j),-.8+j*.8,.024)
        elif era == 6:
            # Broad, breathing chords with felt-like key responses.
            for j,note in enumerate(chord[1:]):
                add(out,start-1+j*.18,voice(note+12,20,'pad',era,j),-.85+j*.56,.052)
                add(out,start+4+j*.11,voice(note,5,'keys',era,j),.55-j*.35,.075)
        else:
            # Intimate hybrid: round sub pulse, warm keys and little echoes.
            for j,beat in enumerate([0,3,5.5,8,11,13.5]):
                add(out,start+beat,voice(chord[0]-12,3,'bass',era,j),0,.072)
                add(out,start+beat+.13,voice(chord[1+j%4],3.2,'bell',era,j),-.65 if j%2 else .65,.084)
                add(out,start+beat+.88,voice(chord[1+j%4]+12,3,'keys',era,j),.65 if j%2 else -.65,.027)
    if era in (2,4,7):
        for beat in range(64):
            if beat%4 in (2,):
                t=np.arange(int(.22*SR))/SR
                noise=rng.standard_normal(len(t))
                brush=np.convolve(noise,np.ones(7 if era==2 else 3)/ (7 if era==2 else 3),mode='same')
                add(out,beat+.035,brush*np.exp(-t/.05)*(1-np.exp(-t/.005)),.16,.038 if era==4 else .026)
    return space(out, era)

def encode(ffmpeg, path, signal, title):
    pcm = np.rint(np.clip(signal, -1, 1)*32767).astype('<i2')
    args = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-f', 's16le',
            '-ar', str(SR), '-ac', '2', '-i', 'pipe:0', '-c:a', 'libvorbis',
            '-q:a', '4', '-metadata', 'title='+title, '-metadata', 'artist=Pixel Museum',
            '-metadata', 'LOOPSTART=0', '-metadata', 'LOOPLENGTH='+str(N), str(path)]
    subprocess.run(args, input=pcm.tobytes(), check=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ffmpeg', default='ffmpeg')
    args=parser.parse_args()
    (ROOT/'eras').mkdir(exist_ok=True)
    (ROOT/'previews').mkdir(exist_ok=True)
    # A shared mastering gain preserves the relative era dynamics.
    stems=[compose(i) for i in range(8)]
    # Match listening levels first so changing decade changes the arrangement,
    # rather than merely becoming louder. Shared final gain keeps blend safety.
    for stem in stems:
        stem *= .065 / float(np.sqrt(np.mean(stem*stem)))
    maximum=max(float(np.max(np.abs(s))) for s in stems)
    mastering=.40/maximum
    report={'sample_rate':SR, 'seconds':SECONDS, 'bpm':60, 'key':'D minor / F major',
            'master_gain':mastering, 'eras':[]}
    for i,s in enumerate(stems):
        s*=mastering
        path=ROOT/'eras'/f'{1950+i*10}.ogg'
        encode(args.ffmpeg,path,s,NAMES[i])
        d=np.diff(s,axis=0)
        report['eras'].append({'year':1950+i*10,'title':NAMES[i],
            'peak_dbfs':round(20*math.log10(float(np.abs(s).max())),3),
            'rms_dbfs':round(20*math.log10(float(np.sqrt(np.mean(s*s)))),3),
            'dc':float(np.mean(s)), 'loop_step_peak':float(np.max(np.abs(s[0]-s[-1]))),
            'adjacent_step_p99':float(np.quantile(np.abs(d),.99)), 'bytes':path.stat().st_size})
    # Preview traverses all eras while keeping the shared phrase in sync.
    journey=np.zeros_like(stems[0])
    for i,s in enumerate(stems):
        start,end=i*8*SR,(i+1)*8*SR
        journey[start:end]=s[start:end]
        if i:
            length=int(.2*SR)
            mix=np.arange(1,length+1,dtype=np.float32)/length
            journey[start:start+length]=(stems[i-1][start:start+length]*(1-mix[:,None])+s[start:start+length]*mix[:,None])
    fade=np.minimum(np.arange(N)/(SR*1.5),1)*np.minimum((N-1-np.arange(N))/(SR*2),1)
    journey*=fade[:,None]
    encode(args.ffmpeg,ROOT/'previews'/'Museum - A Walk Through Time.ogg',journey,'A Walk Through Time')
    (ROOT/'measurements.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
