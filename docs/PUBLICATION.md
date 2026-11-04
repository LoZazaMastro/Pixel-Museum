# Website and release publication

The website source is in `website/`. Its published copy is in `docs/`, served by GitHub Pages from the `main` branch.

- [Website](https://lozazamastro.github.io/Pixel-Museum/)
- [Source repository](https://github.com/LoZazaMastro/Pixel-Museum)
- [Windows setup](https://github.com/LoZazaMastro/Pixel-Museum/releases/download/windows-v0.2.2/Pixel-Museum-Setup.exe)
- [PS5 application ZIP](https://github.com/LoZazaMastro/Pixel-Museum/releases/latest/download/PPSA70421.zip)

Keep the website and its published copy synchronized. Screenshots and the approved teaser are unchanged in this release.

## Installation

On Windows, run the setup and choose an installation folder. Setup installs the application, downloads the image collection and current database, and registers Pixel Museum in the Start menu and Installed apps. It offers an update when it detects an existing installation.

On PS5, extract `PPSA70421.zip` and transfer the `PPSA70421` folder to `/data/homebrew/` via FTP. The application downloads the image collection and current database during the introduction. The v0.1.8 ZIP is 531,786,523 bytes; its extracted application is 741,543,504 bytes. Downloaded resources are stored separately.

GitHub's source archives contain developer source, not an installable application.

## Updating

Use immutable platform tags for application releases. Windows uses `windows-v0.2.2`; PS5 uses `v0.1.8`. Mark the PS5 release as the latest application release so its direct ZIP fallback continues to work.

Upload and verify every asset before publishing its release or activating a feed. `windows-release.json` supplies the website's direct setup link. `application-update.json` supplies the Windows app ZIP URL, SHA-256, compressed size and unpacked size. Its hash describes the app ZIP, not the setup executable or setup manifest.

`database-update.json` remains a separate shared content feed for both platforms. New installations receive its current database during setup on Windows or the introduction on PS5. Existing installations use **Options > Check for updates**. Database updates take effect after restarting the museum. Windows application updates preserve the downloaded collection, database, settings and trophies. PS5 application updates are distributed through ProsperoStore and GitHub Releases.

Never commit authentication tokens, cookies, personal settings, local dependency installations or build caches. Existing source notices and individual third-party media licences remain applicable.

The social image is `assets/social-preview.png`, with the horizontal museum mark and wordmark on white. Website metadata uses it; GitHub's repository social-preview setting is managed separately.
