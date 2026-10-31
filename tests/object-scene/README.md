# Static object viewer checks

`run.sh` builds the actual C++ renderer against the project's host Mesa environment, loads a GLB through the asynchronous worker/staged-upload path, renders two angles and checks GL errors, visible geometry, state restoration, request replacement and release. It writes transparent PNGs for visual inspection.

```sh
bash tests/object-scene/run.sh path/to/model.glb
bash tests/object-scene/run.sh path/to/model.glb Body,Controls,Optical --z-up --tilt=0.55
bash tests/object-scene/run.sh path/to/official-4K-model.glb --size=3840x2160 --yaw=-0.35
```

Options: `--size=WIDTHxHEIGHT`, `--tilt=RADIANS`, `--yaw=RADIANS`, `--zoom=FACTOR`, `--z-up`. Other arguments are comma-separated authored assembly groups. An empty list keeps the whole scene. `--validate` performs only bounded CPU validation. Keep attribution and the actual model licence with any selected bundled asset; research fixtures and captures in this test folder are ignored.

Malformed-input checks use the same built renderer under the host environment (`source tools/host-env.sh`):

```sh
python3 tests/object-scene/malformed.py tests/object-scene/viewer-test tests/object-scene/GameBoyClassic.glb
```

These tests exercise the same OpenGL path as the app. They do not establish PS5 driver/memory performance. See `docs/research/object-viewer.md` for the API, supported material subset, 4K/MSAA targets and full-resolution master memory figures.
