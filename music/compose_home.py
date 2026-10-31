"""A quiet, seamless Home-screen arrangement using Pixel Museum's own voices.

No sampled recordings, external music or game melodies are used.
"""
from pathlib import Path
import json
import wave
import numpy as np
import compose as museum


def main():
    museum.SR = 48000
    museum.N = museum.SR * 64
    out = np.zeros((museum.N, 2), np.float32)
    for ci, chord in enumerate(museum.CHORDS):
        start = ci * 16
        for j, note in enumerate(chord[1:]):
            museum.add(out, start - .8 + j * .12,
                       museum.voice(note, 19, 'pad', 6, j),
                       [-.55, .25, -.15, .55][j], .045)
        # Just two rounded key gestures in each slow harmonic phrase.
        for beat, gain in [(3, .023), (11, .015)]:
            for j, note in enumerate(chord[1:]):
                museum.add(out, start + beat + j * .055,
                           museum.voice(note, 5, 'keys', 6, j),
                           -.27 + j * .18, gain)
    out = museum.space(out, 6)
    gain = min(.04 / float(np.sqrt(np.mean(out * out))),
               .18 / float(np.max(np.abs(out))))
    out *= gain
    destination = Path(__file__).resolve().parent / 'home'
    destination.mkdir(exist_ok=True)
    with wave.open(str(destination / 'Pixel Museum - A Quiet Arrival.wav'), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(museum.SR)
        wav.writeframes(np.rint(out * 32767).astype('<i2').tobytes())
    (destination / 'measurements.json').write_text(json.dumps({
        'title': 'A Quiet Arrival', 'duration_seconds': 64,
        'sample_rate': museum.SR, 'loop': True,
        'rms_dbfs': round(float(20 * np.log10(np.sqrt(np.mean(out * out)))), 3),
        'peak_dbfs': round(float(20 * np.log10(np.max(np.abs(out)))), 3),
        'loop_step_peak': float(np.max(np.abs(out[0] - out[-1]))),
        'source': 'Original synthesis; Pixel Museum pad and felt-key voices',
        'external_recordings': False,
    }, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
