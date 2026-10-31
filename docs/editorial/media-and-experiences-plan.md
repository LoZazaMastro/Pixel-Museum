# Media and playable-study production plan

This is the illustration plan for the full museum, alongside `content/editorial/production-plan.json`. The detailed acquisition queue is `content/editorial/media-backlog.json`. It preserves the original Playhub writing and distinguishes an imported article, a working image, a reviewed chapter and a finished exhibit.

## Current scope

The audited snapshot contains **1,064 distinct runtime articles**: 1,032 normal records and 32 independent calendar features. All 365 published daily editions remain present; 333 same-year linked editions are explicit aliases rather than extra acquisition jobs. The snapshot has 3,798 narrative sections. Of the distinct articles, 421 have any image candidate, 419 have a metadata-qualified HD cover, 16 have documentary video, three have a curated soundtrack and 29 have 3D. A cover does not establish chapter coverage or factual review.

Snapshot: 2026-10-20T21:47:06.719067+00:00. Catalogue SHA-256: `7a9e77806668c88a1d9d0b01e37a47295c20089e5ead31915bbf1f87c1ac1415`. This is the frozen image-integration snapshot, not a claim of final editorial completion. Every distinct article has an entry, source URLs, actual paragraph headings and anchors, existing media mappings, rights state and tasks. There are 87 articles with a strict majority of explicit image mappings; 86 retain that coverage when restricted to metadata-qualified HD candidates. Mapping is not contextual/rights approval. No article is signed off by this plan. The literal-majority target is **2,744 illustrated section slots** across the current articles.

## What completion means

1. Every article needs a recognisable contextual hero: the real person, machine, original edition, event or development object. A franchise logo or unrelated sequel cover is insufficient. Hardware 3D complements a photograph and its real-world provenance.
2. A literal majority means `floor(section_count / 2) + 1`. Set `story_paragraph` after reviewing image and paragraph together. Implicit array order is a rendering fallback, not an editorial mapping. Repeating one cover does not illustrate different claims.
3. A caption states what is visible, including edition/platform, date or uncertainty, creator and source. Label later reconstructions and restorations. Do not imply an image proves a detail it does not show.
4. Prefer original native 1920 px-or-better masters; inspect the actual crop at 4K. A 1600 px metadata gate is only a candidate filter. Smaller archival evidence can be useful at an honest display size; enlargement does not create missing detail.
5. Verify file identity, fresh HTTP/decode health, rights and credits separately. A CDN URL, copyright sentence or museum catalogue listing is not a licence grant. Keep web resources remote and attach only reviewed assets to production.
6. Missing images never hide history. Keep a restrained reading card and source link while the asset is pending.

## Bounded review batches

All 1,064 IDs are assigned to 46 units of at most 24 articles. Each unit ends with contextual hero/chapter mappings, captions, rights notes, decoded-resolution evidence and actual native 4K inspection. A difficult asset moves to an alternate-source lane without blocking the other articles.

| Batch | Scope | Articles | Units |
| --- | --- | ---: | ---: |
| P0 | First Rooms already tested on PS5 |16|1|
| P1 | People, machines and institutional context |81|4|
| P2 | Games before 1990 |238|10|
| P3 | Games 1990–2009 |373|16|
| P4 | Games 2010 onward |356|15|

P0 takes priority over widening the collection. P1 particularly needs human voices, dated portraits and evidence of creative work. Early games need exact platform/region checks. Later games need original-release imagery and production context, rather than remakes or promotional collages. Playhub's existing exact game/app IDs should be reused. Calendar aliases identify the acquisition owner and whether the original bodies match; different chapter meanings require a separate mapping review.

### Installed-trial priority overlay

The 35 entries in `dist/vertical-slice-ready-04/PPSA70421/content/catalog.json` receive an additional priority flag within their existing work units. This does not create another batch or duplicate an article. The exact installed IDs and the trial catalogue hash are retained in the JSON overlay. One is a calendar alias: `daily-10-20` maps to `workbook-10-20-super-mario-bros-wonder`. Both the installed alias and its distinct acquisition owner are identified.

This expands near-term review beyond the original 16 First Rooms to the installed experience and listening articles: Spacewar!, Pong, Breakout, Space Invaders, Pac-Man, Elite, Super Mario Bros., Sonic, Wolfenstein 3D, Super Mario 64, Final Fantasy VII, Dance Dance Revolution, Ico, Lumines, Katamari Damacy, Portal, Minecraft, Fez and the October 20 feature. Inclusion in the installed trial records selection and priority, not independent editorial approval of every article or asset.

## Specific First Rooms assignments

- **Tennis for Two:** apparatus, the two controls, then a clearly labelled original interpretive comparison. Distinguish 1958 evidence from later reconstructions.
- **Brown Box:** the exact Smithsonian prototype and documented program cards/control details; a retail Odyssey must not masquerade as the prototype.
- **Channel F:** console/cartridge relationship, controller grip/actions and cartridge interface detail, instead of repeated product glamour shots.
- **Roberta Williams:** original Mystery House room/parser, authorised development artefact or photograph, then a correctly dated later Sierra scene. Do not promote marketing superlatives into historical facts.
- **Carol Shaw:** original River Raid corridor and fuel/route pressure, an original labelled sequence diagram, then authorised archival evidence. A finding aid is not scan-reproduction permission.
- **Karateka:** author-published movement experiment and dated work-in-progress/journal context. Separate original 1984 material from later documentary or remake content. Link sold publications instead of reproducing them wholesale.
- **Tetris:** correct early version, visible row-completion decision and a separately dated handheld pairing where portability is discussed.
- **Game Boy:** DMG-01, screen/battery-format detail, original handheld Tetris context and a Link Cable pairing. Hardware-photo authorship and game-image copyright are separate.
- **Doom:** original gameplay/HUD, an original annotated spatial diagram or authorised development artefact, then specific multiplayer/level-authoring evidence.
- **PlayStation2 / Nintendo3DS / Switch:** licensed exact 3D object plus real control, hinge/screen or media-format photographs. Caption later variants explicitly.
- **Journey:** traveller/landscape scale, observable ribbon/flight/companion behaviour, contrasting light/terrain and the official musical publication.
- **Papers, Please:** the desk and a document/interface showing a real checking decision, not generic dystopian illustration.
- **Celeste:** a readable official hazard/dash route and a separate recovery/retry scene. Our studies do not reconstruct commercial levels.
- **Preserving play:** restored hardware, carriers/tools and a specific archival record, with present-day dates; avoid unrelated server-rack photographs.

The backlog contains exact paragraph indices and original body anchors for these assignments and all other articles. Research briefs do not become public historical claims automatically.

## Sources and access

**Early hardware and people.** [Smithsonian Open Access](https://www.si.edu/openaccess/faq) offers reusable assets when the specific item carries CC0; begin Baer research with its [prototype collection](https://www.si.edu/spotlight/the-father-of-the-video-game-the-ralph-baer-prototypes-and-electronic-games). [Computer History Museum's policy](https://dev.computerhistory.org/policy) explicitly excludes images from its CC0 metadata API. Use separately licensed photographs or item-level permission. Its [PDP-1 project](https://www.computerhistory.org/pdp-1/spacewar/) supplies primary technical context. [Science Museum Group](https://collection.sciencemuseumgroup.org.uk/about) has collection/image access with per-record terms, including noncommercial image licences.

**Documents and magazines.** [VGHF's library guidance](https://library.gamehistory.org/help) distinguishes public/restricted collections and use conditions; underlying copyright often belongs to donors or publishers. [The Strong](https://www.museumofplay.org/collections/research-access/) separates research access from public reproduction; consult the [collection-materials agreement](https://www.museumofplay.org/app/uploads/2023/05/Use-of-Collections-Materials-Agreement-April2025.pdf). Preserve box/folder/item IDs. These remain useful factual sources even when no freely reusable image is available.

**Museum context.** [Computerspielemuseum Berlin's press downloads](https://www.computerspielemuseum.de/Presse/39-Downloads.htm) offer selected photographs without a blanket open licence on that page. Retain supplied credits and check use terms, or use an independently licensed museum-visit photograph. [V&A's collection API](https://developers.vam.ac.uk/) and [Videogames exhibition](https://www.vam.ac.uk/articles/about-videogames-exhibition) are design-process leads, with separate image/third-party rights. The museum hosting an image does not replace its original designer credit.

**Exact files.** [Commons reuse guidance](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia) requires per-file creator/licence checks. Resolve the original file rather than enlarging a thumbnail. Inspect object identity separately from licence metadata. Brookhaven's [history page](https://www.bnl.gov/about/history/) is the primary Tennis for Two lane; its detailed firstvideo page timed out once during this audit. Recheck it before release and distinguish the laboratory's original material from credited contributor images.

**Original voices.** [Iwata Asks](https://iwataasks.nintendo.com/) and the [Jordan Mechner archive](https://www.jordanmechner.com/en/archive/?lang=en_EN) offer first-person production context. Retain speaker, interviewer, setting and publication. [GDC Vault's free index](https://gdcvault.com/free/) identifies public talks; free viewing does not transfer slide/video copyright or authorise bypassing other restricted talks.

**Modern games.** Follow exact developer/publisher sources and verified Playhub app IDs. [Steamworks asset documentation](https://partner.steamgames.com/doc/store/assets/standard) describes store-media formats, not a general third-party reuse licence. Store screenshots remain publisher-owned editorial material with a recorded use decision. Choose native screenshots that explain the design; capsules and franchise montages are weak chapter evidence.

## Minimal visual language, deeper interaction

The museum stays **minimal and abstract**: paper/ink surfaces, geometric forms and one restrained era accent. Richer gameplay means better rules, feedback, routes and consequences. It does not mean literal game-like landscapes, colourful scenery or copying a game's art style. Keep effects purposeful and low-noise. Library/card/introduction previews show the actual native study, paused before entry.

The 15 published experiences are a reviewed selection, not a quota for every game. Camera, perspective, dash, voxels, portals and light remain withheld research exercises. Controller motion must not be advertised until physically validated; the Movement grouping means game movement, not gyroscope support.

- Paddle/bricks/formation/maze explain anticipation, return angle, target prioritisation and route pressure. Formation includes the passing bonus; the original maze includes continuous movement, pursuit, power duration, fruit and lives.
- Gravity/orbit/wireframe explain packing, heading versus velocity and depth through edges. They are original interpretations, not original game binaries or exact historical simulations.
- Jump/momentum explain readable landings, variable arcs, flags and optional rewards, then slopes, deliberate braking, gaps and upper routes. Preserve the tested mechanics while keeping presentation abstract.
- Rhythm/sequencer/wind/raycast/scale/pixels each explain one musical or visual idea. A weak minigame does not earn a place merely by raising the total.

Official remote listening cards already cover Journey/Austin Wintory, Celeste/Lena Raine and Final Fantasy VII/Nobuo Uematsu. Preserve uploader verification, arrangement/version, artist/publisher links and recording credits in `content/expansion/soundtrack-selections.json`. Recordings remain online with their owners; extracted audio is not bundled. Add another playlist only when its musical function explains the article and an official publication is verified. A composer biography needs an actual interview or credited work, not a fan-upload collage. The original museum ambience/navigation sounds are separate from historical recordings.

## Evidence at the end of each unit

Record source page, original file URL, decoded dimensions, hash where appropriate, rights/credit decision, paragraph mapping and caption. Capture the actual native 4K card and fullscreen crop. Test image navigation/back and offline/error behaviour. Verify official video identity and PS5 playback separately. For studies, test real completion/loss/reset controls on PS5: host renders establish layout and bounds, not physical feel.

Refresh the backlog against the catalogue hash after each import. Report imported articles, verified heroes, reviewed contextual sections and signed-off exhibits as separate measures. Preserve the complete text while finishing the last three.

### Review follow-up

The initial independent review remains recorded in `docs/editorial/independent-review.md` and `content/editorial/plan-review.json`. Its R03 finding concerned proposed history briefs without adequate existing-subject duplicate anchors. The follow-up now records `plan_resolved_production_decision_pending`: the eight missing anchor sets were added, and all 140 commissions retain an explicit editorial decision between expansion and a distinct feature. Those production decisions remain pending. This media refresh records that follow-up without editing the historical review or treating a source link as article approval. R07 identified stale media snapshot counts: the refreshed backlog explicitly records its new hash/time and preserves the earlier snapshot in its history.

`tools/refresh-media-backlog.py` refreshes current evidence after catalogue, production and readiness snapshots agree. It preserves the 1,064 distinct IDs, 333 aliases, authored paragraph briefs, body hashes and original work-unit assignment; changed narrative bodies stop the refresh for review. Run it only after the import lane has finished its current integration. The refresh retained the original task/brief bodies and the previous snapshot hash; it did not alter the master catalogue or historical review files.

Reading-flow migration: three source-controlled reference repairs merge split sentences or remove repeated prose. All earlier paragraph briefs and hashes remain in each affected entry's `reading_flow_migrations`; image anchors follow the reviewed mapping. Original Playhub sections remain unchanged.
