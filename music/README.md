# A Walk Through Time

The entrance uses **Before the First Gallery**, a dedicated original bed in
`eras/onboarding/intro.ogg`. It renders only the sustained background pad
voices and harmony from the gaming composition: no lead, keys, arpeggio,
bass pulse or percussion. The language and theme choices retain this bed
until the actual timeline appears. Its shared clock and 200 ms crossfade
match the gaming/culture transition; volume, mute and playback ducking keep
their existing behavior. `compose_onboarding.py` generates this file without
rewriting any gaming or culture recording.

An original, quiet score for Pixel Museum. A short electric-piano phrase,
rounded bass and extended chords pass through eight related arrangements.
Each decade has its own audible instrumentation and rhythm. The arrangements
stay related through the same harmony, without quoting game melodies.

Each era is 64 seconds long, at 60 BPM, in D minor and its relative F major.
All eight arrangements share a musical clock, chord changes and phrase.
The culture timeline plays a second original composition, **The World Around
Us**, using the same instruments and 64-second clock with its own eight-chord
progression, melodic theme, bass movement and accompaniment. Its harmony moves
every eight seconds rather than repeating the gaming track's sixteen-second
chords. Both stay in the related D-minor/F-major palette. Its eight files live
in `eras/culture/`.
Both compositions advance together; switching timelines crossfades in 200 ms
and returning resumes at the shared current position. `compose_culture.py`
generates only the companion files and verifies that gaming recordings remain
unchanged. `tests/run-timeline-music.sh` checks actual decoded playback,
crossfade block invariance, distinct compositions and return without restart.
All eight tracks remain synchronized and silently advance even when their
individual gain is zero. Selecting another decade starts a 200 ms crossfade
on the next audio callback, without restarting or seeking any arrangement.
1989 selects the 1980s arrangement; it does not mostly select the 1990s.
Reflections,
note releases and sustained chords wrap around the loop, so there is no
fade-to-silence at its boundary.

| Era | Movement | Palette |
| --- | --- | --- |
| 1950s | First Signals | Close, warm oscillators, muted keys and a rounded counterline |
| 1960s | Open Circuits | Sustained drawbar-like chords with a gentle rotary pulse |
| 1970s | Warm Machines | Syncopated analog bass, brushed rhythm and electric keys |
| 1980s | Glass Memory | A glassy FM arpeggio over the shared warm harmony |
| 1990s | After Hours | Low mallets, a loose downtempo backbeat and rounded bass |
| 2000s | Quiet Networks | Digital plucks, high harmonic layers and diffuse stereo echoes |
| 2010s | Soft Horizons | Broad breathing pads with intimate, felt-like key responses |
| 2020s | Common Ground | A hybrid sub pulse, warm mallets and small answering echoes |

[Listen to the 64-second journey preview](previews/Museum%20-%20A%20Walk%20Through%20Time.ogg).
The preview changes arrangement every eight seconds with the same 200 ms
crossfade; the app changes in response to the selected decade instead.


## Recording technologies

Arrangement and recording colour are independent. Before 1950 the first,
quieter arrangement supplies the shared score; the playhead never restarts.
The recording profiles change at historical milestones, rather than at every
decade: clean acoustic space before 1877; a narrow mono phonograph from 1877;
a somewhat fuller acoustic gramophone from 1887; electrical mono recording
from 1925; tape/hi-fi mono around 1950; stereo from 1958; and transparent
digital playback from 1982 onward. A move from 1890 to 1910 keeps the same
recording profile. Both profile and arrangement transitions take 200 ms.

These are restrained artistic approximations, not simulations of a particular
machine. Acoustic profiles use continuous band limiting and gentle saturation,
without digital sample hold or few-bit quantization. There is no added surface
noise. The digital profile preserves the decoded 24 kHz source; it cannot add
frequencies absent from that source. Filter histories remain warm and playback
continues through muting and video ducking.

The dates follow the [Library of Congress recording timeline](https://www.loc.gov/programs/national-recording-preservation-plan/tools-and-resources/historical-background/timeline/),
its [history of Berliner's gramophone](https://www.loc.gov/collections/emile-berliner/articles-and-essays/gramophone/),
and its description of [acoustic recording before 1925](https://www.loc.gov/loc/lcib/1106/records.html).
The latter describes a roughly 100-2,500 Hz mechanical recording range; the
chosen filter shapes and saturation amounts remain curatorial choices.

## Rebuilding

Python 3.10+, NumPy and an FFmpeg build with libvorbis are required:

```sh
python compose.py --ffmpeg /path/to/ffmpeg
python verify.py --ffmpeg /path/to/ffmpeg
```

`compose.py` contains the full score, synthesis, arrangement and mastering.
Its deterministic seed controls only percussion texture. The musical notes
and chord voicings are written explicitly. There are no downloaded recordings,
sound fonts, external samples, or borrowed game melodies.

The app needs `eras/*.ogg` and `eras/culture/*.ogg`. The generator, preview, reports and host test
belong in the source distribution rather than the installed music directory.
Files are 24 kHz stereo Vorbis; the native renderer interpolates them to the
48 kHz output clock. Sixteen decoded PCM16 arrangements occupy 98,304,000 bytes.
The original gaming era files occupy 2.20 MiB; culture adds about 1.91 MiB.
Levels are matched before
shared mastering, so an era change changes the arrangement rather than merely
making it louder. `archive-first-score/` preserves the earlier arrangements
for reference and is not needed by the app.

The host checks verify exact fade duration, constant-sum gains during repeated
retargeting, a shared playhead through mute and video ducking, block-size
invariance and seamless loop joins. The encoded-file check also measures
adjacent arrangement differences and level matching. These tests do not
replace a listening check on PS5.

Original soundtrack and synthesis source: Pixel Museum, 2026.
SPDX-License-Identifier: GPL-3.0-or-later. Vorbis decoding uses stb_vorbis;
its existing upstream notice and license remain in the project's third-party
notices. FFmpeg is a build-time encoder and is not bundled with this music.
