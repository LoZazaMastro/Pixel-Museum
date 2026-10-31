# Pixel Museum — publication handover

This directory is an unpublished local website. The private repository `https://github.com/LoZazaMastro/Pixel-Museum` has been created with an initial README only. No GitHub Release or GitHub Pages deployment has been created.

## Before publication

1. Finish the app release and confirm the installation instructions against the delivered `PPSA70421` folder.
2. Current English screenshots are already paired in light and dark themes; origins and hashes are in `assets/asset-ledger.json`.
3. The seven preservation logos are integrated; original sources are in `assets/preservation/manifest.json`.
4. Add the finished teaser and its poster only after the final edit and footage credits are ready. Avoid autoplay with sound.
5. Review the intended license for original website artwork and writing. The application's existing GPL and third-party licenses remain applicable to their respective components; do not replace them with a blanket no-reuse notice.

## Local preview

From this folder run `python -m http.server 4173 --bind 127.0.0.1`, then open `http://127.0.0.1:4173/`. Check desktop and mobile widths, keyboard navigation, reduced motion, all screenshots, the source index and outgoing links.

## GitHub Pages — only when you decide to publish

1. Create an empty repository named `Pixel-Museum` under `LoZazaMastro`, or use the one prepared for this project if it already exists. Never upload the whole development workspace: it contains local configuration and research files.
2. Put the contents of this website folder in the repository's `docs/` folder, preserving `assets/` and `.nojekyll`.
3. Open the repository's **Settings → Pages**. Under **Build and deployment**, choose **Deploy from a branch**, select the main branch and `/docs`, and save.
4. Wait for the Pages deployment to complete. Use the exact published URL GitHub reports. The expected project URL is `https://lozazamastro.github.io/Pixel-Museum/`, but it is not confirmed live.
5. Add that confirmed URL to the repository About section and the finished YouTube description. Test it on a phone as well as desktop.

## Release — a separate explicit action

Publishing the website does not publish the app. When you choose to release it, create a GitHub Release with the tested package, version, concise English notes, installation instructions and required notices. Verify the downloaded public asset against the local package checksum. Do not upload credentials, cookies, personal configuration or unreviewed development artifacts.
