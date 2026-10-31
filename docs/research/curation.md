# Pixel Museum — curation and reference notes

Research date: 20 October 2026. This is the first permanent collection, not a claim to contain the complete history of videogames.

## References collected before the content was written

The collection takes its narrative structure from specific, publicly documented museum approaches. It does not reproduce their writing or visual assets as its own design.

| Reference | Primary page | Useful principle |
| --- | --- | --- |
| Digital Eclipse, The Making of Karateka | https://www.digitaleclipse.com/games/karateka | A timeline opens into documents, prototypes, video and a close study of one creation. The official page includes images of the documentary and a trailer. An object should lead to a story rather than merely a specification sheet. |
| Digital Eclipse, Gold Master Series | https://www.digitaleclipse.com/media/goldmasterseries | Interviews and archival material sit beside the finished game. Attribution and the difference between a recollection and an artifact should stay visible. |
| Gran Turismo 7, Brand Central museums | https://www.gran-turismo.com/au/news/00_1796083.html | Histories live within the identity of each manufacturer. A machine can open a wider cultural timeline instead of ending at its launch date. |
| SMK OPEN | https://collection.smk.dk/ | A restrained object-led collection index; large artwork views and clear work/creator/date information support looking closely. Themes offer another route through the same records. |
| SMK's own collection-design retrospective | https://blog.smk.dk/were-open-thoughts-on-building-a-new-home-for-smks-online-collection | The museum describes a data-driven collection connected through curated themes, audio, YouTube and 3D references. This supports a small native client using attributed online resources. |
| Nasjonalmuseet online collection | https://www.nasjonalmuseet.no/en/collection/ | Quiet typography, generous object presentation and explicit collection metadata. Preserve room around the object; keep factual labels separate from editorial interpretation. |

Visual inspection and native presentation are owned by the app-design pass. These notes record the references and the content implications of the actual collection pages, rather than claiming that a text-only web extraction is a rendered design review.

## Playhub precedent inspected, without changing it

Read-only sources:

- `F:\Playhub\Plugin\Playhub\Source\Playhub\Assets\GamingModeDeckyPlugin\gaming-mode\quick_settings\daily_history.py`
- `history_editorial.json`, `history_days.json`, `history_images.json` in the same directory.

The useful structure is a written month/day catalog, explicit subject associations for images, related themes and an editorial fallback when a day has no verified anniversary. Pixel Museum keeps that distinction. A selected feature must not be presented as something that happened on today's date. Playhub's more aphoristic interludes were not reused: the new copy gives the concrete object, the people involved and the reason it matters in ordinary English.

Some existing Playhub image references are reused with the user's explicit authorization. Only images attached to the exact game are carried over. Their remote URLs are checked again. A screenshot of a different version or sequel is not silently substituted for a historical original.

## Collection scope

The catalogue contains more than one thousand stops from the 1950s onward. Original exhibition stories, adapted Playhub writing and an attributed Wikipedia reference library have separate editorial provenance. It includes laboratories, public arcades, consoles, home computers, portable machines, multiplayer communities, independent games and preservation. People are credited in context: Jerry Lawson, Roberta Williams, Dona Bailey, Carol Shaw, Dani Bunten Berry, Gunpei Yokoi, Masayuki Uemura, Yoko Shimomura and others sit alongside studios and hardware teams. The exact totals are generated in `content/assembly-audit.json`.

Geographic routes include the United States, Japan, Britain, the Soviet Union, Sweden, South Korea, Brazil, Canada and India. Tectoy, Dandara and Raji help prevent a North America/Japan hardware succession from being mistaken for one universal timeline. These are starting routes through a wider history; important regions and communities remain to be added through further research.

Featured exhibits have longer, original multi-paragraph stories. Shorter object labels are intentionally readable from a television. `summary` is an entry invitation, not a replacement for `body`. Wikipedia introductions retain their article revision, contributor-history link and CC BY-SA attribution. No invented quotation or fictional historical testimony is included.

## Date policy

- `year` is the timeline anchor, and can describe completion, a regional launch or a later milestone. `date.region` explains which.
- `date.precision` is `day`, `month` or `year`. Unknown month/day fields are zero. Only `day` records should participate in exact Today in Play matches.
- Tennis for Two: 18 October 1958 is a documented public demonstration at Brookhaven.
- Spacewar!: 1962 is used without inventing a single release day for a collaborative project.
- Brown Box: 1968 anchors a development period spanning 1967–1968.
- Pong: 29 November is identified as an announcement date, following the Computer History Museum's wording.
- Space Invaders: 16 June 1978 is Taito's exhibition debut. It is not a universal arcade installation or retail date.
- Adventure: 1979 follows Robinett's chronology. Some retail histories use 1980. The note is retained in the catalog.
- Tetris: 1984 follows the present official chronology; 6 June is not used as a securely documented original release day.
- PlayStation and PlayStation 2: dates are Japanese launches. Later launches are distinguished in the text.
- Sonic: 23 June 1991 is the North American Genesis release, not the Japanese launch.
- Pokémon: the 1996 anchor is Japan's Red/Green, not the later international Red/Blue.
- Minecraft: 2011 marks version 1.0. Public builds appeared in 2009.
- Journey: 13 March 2012 describes the announced general North American PSN release; promotions and regions differ.

## Media and attribution

Images and YouTube films remain remote resources. Licensed 3D models are included in the application, together with their creator credits, source links, original licences and any modification notices. Their rights remain separate from the application source licence. The catalogue holds source URLs for online images and films; image caching is a transport concern, not a new claim of authorship or ownership.

Each image has `url`, `source_page`, `title`, `creator`, `license` and `credit`; open-license images additionally retain the license URL when available. Wikimedia records were resolved through its image-info API. Results were selected by subject: unrelated namesakes, book PDFs, wrong console generations and fan-made cabinets were excluded.

Hardware photographs are predominantly public-domain works by Evan-Amos. Other Commons photographs retain their individual CC BY/CC BY-SA notices. Images of reconstructions and later hardware variants are captioned as such. The Nimrod image is a museum reconstruction, not a claim that the original machine survived. The Atari image shows a later four-switch variant. The second Famicom image shows the later Disk System.

Game screenshots and publisher/museum illustrations are marked copyrighted remote editorial references. A publicly accessible screenshot is not declared CC0 or open-licensed. For those records the credited source and the game rights holders stay attached. The catalog's own license must never be applied to third-party art by implication.

Sixteen YouTube entries were extracted from primary/curatorial pages, then checked using YouTube's oEmbed endpoint. Stored titles and channel names come from that response. All museum-selected videos currently resolve to The Strong Museum, and the other verified channels are Brookhaven Lab, Digital Eclipse, Lucas Pope and Maddy Thorson. A YouTube embed can later become unavailable or restricted; the accompanying text and source links must continue to work.

### Bundled 3D collection

`models/index.json` is the selected runtime inventory. Each record includes the original model page, creator, licence, byte count, SHA-256, reviewed starting pose and acquisition or modification notes. `models/licenses/` contains the matching per-object notices. `models/prepare_models.py` copies approved source files; `tools/model-preflight.py` checks that the selected files and notices match the inventory before packaging.

Models are tested through the actual OpenGL object renderer at 3840 × 2160. Their authored geometry and source texture resolutions are retained. A 4K render does not imply that every author supplied 4K textures, nor does a desktop test prove PS5 memory residency or frame rate. Detailed render statistics and quality notes are in `docs/research/model-candidates-renderer.json`.

Creator-disabled downloads are not extracted from the Sketchfab viewer. Unavailable selections and alternative candidates are recorded separately. Source variants remain visible: the DSi-labelled recreation is incomplete, Saturn uses a later black Model 2 body, and the Series X object is a 2019 pre-release artist reconstruction. Such representations are not manufacturer CAD or proof of the original hardware's internal construction. Research drafts do not ship merely because they pass a renderer test.

## Validation and maintenance

`content/catalog.json` is the runtime catalogue. `assemble_catalog.py` combines the original exhibition copy, editorial revisions, attributed expansions, verified media and the bundled model index. `compile_catalog.py` is the original exhibition authoring source; running it alone does not produce the full collection. `curate_media.py` records deliberate selections and merges `media-supplemental.json`; it is an authoring tool, not an app runtime dependency. `collect_media.py` gathers research candidates and does not itself select a correct historical image.

`audit_catalog.py` checks unique IDs, related IDs and valid precision-aware dates, then records source availability in `source-audit.json`. A page returning 403 to the Python client may still be available in a normal browser; the audit makes that distinction and does not silently mark it verified by that client.

`audit_media.py` checks remote image and model response types without bundling media. Its report is `media-audit.json`. Wikimedia throttled a few original image requests with HTTP 429 during bulk validation; the app should use a small request queue, respect backoff and prefer the existing thumbnail URLs. A transient 429 is not evidence that an image has been deleted. Missing media needs a composed text/object fallback, not a replacement image of the wrong subject.

The browser research found and corrected stale Centre for Computing History and PS2 URLs. The catalog uses source pages directly rather than search result URLs. A current source inventory, media attribution inventory and counts are also generated in `content/credits.json` for application credit presentation.
