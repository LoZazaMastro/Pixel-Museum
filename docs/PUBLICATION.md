# Website and release publication

The website source is in `website/`. Its published copy is in `docs/`, served by GitHub Pages from the `main` branch.

- Website: https://lozazamastro.github.io/Pixel-Museum/
- Source repository: https://github.com/LoZazaMastro/Pixel-Museum
- Download: https://github.com/LoZazaMastro/Pixel-Museum/releases/latest

Keep the website and its published copy synchronized when making changes. The current English screenshots are captured from the application renderer in both themes; their local production records are retained in the development workspace. The approved silent teaser is unchanged.

## Installation

Download all six archive parts from the release into the same folder. Open `.001` with 7-Zip and extract it. Copy the entire `PPSA70421` folder to `/data/homebrew/` on the PS5 via FTP, refresh the homebrew launcher, and open Pixel Museum. The extracted app uses approximately 11.49 GB.

The first public release is `v1.0.0`. Its binary and content are the same verified build delivered to the console. Release assets include SHA-256 checksums and installation instructions. GitHub's source archives contain developer source, not an installable app.

## Updating

Prepare and verify the next complete app folder, increment its content version, update sources and screenshots if needed, and use a new immutable release tag and new asset names. Upload all assets to a draft release before publishing it. The Download link follows the latest published release automatically.

Never commit `.env`, authentication tokens, cookies, personal settings, local dependency installations or build caches. Existing GPL source notices and individual third-party media licenses remain applicable.

The social image is `assets/social-preview.png`, with the museum mark and horizontal wordmark on white. It is configured in website metadata; GitHub's separate repository social-preview setting uses the same PNG.
