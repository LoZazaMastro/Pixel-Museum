# Complete prose without hidden glyph work

Narrative cards now keep their exact wrapped body rows after their first draw, including continuation paragraphs, inter-paragraph spacing and distinct subheadings. Draws submit only rows intersecting the existing reading clip plus a 64-pixel font guard. The full source text, fonts, baselines, scroll range, images and card order are retained. Theme colors are applied every frame; preparing an exhibit or changing language invalidates the layout.

`bash tools/preview.sh story-text-profile` loads an immutable copy of the real 1,395-entry runtime catalog. It measures the ten longest distinct composed cards at the top, middle and bottom, and independently checks every cached row against full-source wrapping, including wording, order, font, heading role and baseline. It writes the actual unillustrated narrative-card inventory separately; films, music, Credits, photographs and studies do not inflate that gap count.

On this host, warmed CPU geometry generation fell from approximately 0.75–0.94 ms to 0.02–0.04 ms. Glyph instances fell from 5,330–6,601 to roughly 500–950. All thirty scroll extents remain unchanged to the logged 0.1-pixel precision. The initial full wrapping remains a one-time cost. These measurements cover CPU generation on the host, not physical PS5 frame rate or GPU time.

`bash tools/preview.sh story-reading` additionally renders the actual Screen with GL, uses the right stick to reach the final glyph line of a 200-line paragraph without R3, checks the complete 348-track Credits inventory, and verifies independent image associations for every N64 and DS Lite source paragraph. All pass with no GL error.

Logs and the source-bound receipt are in `build/research/story-text-profile/`. The frozen catalog SHA-256 is `1d782739d6ea1e0f8ca95cd4d011d4c91c2393b66eb2fb9bb8b98dff38465bd4`. No content wording was edited and no files were transferred to the console.
