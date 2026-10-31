# Transparent PNG rendering

Run `python3 tests/image-quality/alpha-fixtures.py`, then `MUSEUM_PREVIEW_4K=1 bash tools/preview.sh alpha-images` in the host environment. The fixture generator uses only the Python standard library.

The actual Screen image helper, packaged RemoteCache worker and native STB decoder upload the complete2960x2360 Nintendo64/64DD PNG as GL_RGBA8. Every uploadedRGBA byte matches the original source, including colors hidden by zero alpha. The real 4K output preserves the exact theme background at5,825 fully transparent samples in each light/dark capture. The image helper adds only its image quad, with zero border/frame geometry.

A separate original synthetic fixture verifies alpha0/64/128/192/255 and image-opacity1/0.5 against numerical compositing, within2eight-bit rounding steps. The shader contract is straightRGBA paired with SRC_ALPHA/ONE_MINUS_SRC_ALPHA and separate alphaONE: the opacity is applied once. Switching all UI/FBO textures to a different premultiplication convention would be incorrect and was unnecessary.

The destructive white-background compositing occurred in the offline JPEG conversion. The image bundler now retains alphaPNG masters and previews; the native decoder/shader already handle them. No production rendering changes or source image alterations were needed for this correction. These captures use the same C++ rendering code on host GL, not a physical PS5 capture. No FTP transfer was performed. Detailed hashes, numeric checks and captures are recorded in `build/research/png-alpha-native-verification.json`.
