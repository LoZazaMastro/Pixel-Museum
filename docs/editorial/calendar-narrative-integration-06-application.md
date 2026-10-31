# Canonical narrative06: integration receipt

Verified on 21 October 2026. This records authoring-data integration and parser checks; it is not a PS5 performance, playback or editorial release signoff.

The assembly hook runs after `integrate_collection_media` validates its original-body-bound acquisition batches and before final publication-readiness evaluation. The legacy visual quarantine follows narrative06. Each original daily edition and source-language sidecar remains archival; researched canonical bodies use English fallback until their own translations are reviewed.

## Preserved evidence

- 45 canonical narratives replaced, with 45 original daily records and 45 original canonical records fully archived.
- 360 old canonical locale overlays archived before removal. Daily translations remain byte-identical to the source editions.
- 110 obsolete parent `story_paragraph` media bindings removed. Associated URLs, captions, rights and other fields remain intact unless the separate reviewed visual quarantine excludes them.
- 45 acquisition jobs moved to the new canonical prose. Their complete previous sections, briefs, source URLs, hero task and existing media snapshots remain in `source_identity_migrations`. Attached authored features and their briefs are separate and unchanged by this migration.
-The source-copy check validates all 365 original editions, 1291 chapters and 365 introductions: 1656 exact English sections plus eight original language editions. It recognises 49 explicit reviewed canonical prose exceptions rather than pretending every canonical is still an exact source duplicate.

## Results

Two fresh assembly runs produced the same catalogue bytes:

`content/catalog.json`: 16139139 bytes, SHA-256 `62fe8367142ce5393329dde86e6b267a368c14d58c74b3466e18995f480d3f87`.

The snapshot contains 1405 raw records and 1093 distinct runtime destinations. It has 44 attached authored features / 176 cards and six standalone authored features / 24 cards; 3814 parent sections become 3990 sections when attached prose is included. 538 destinations have any image URL and 536 have a metadata-qualified HD candidate; 75 have metadata-HD mappings across a majority of their parent sections. These are acquisition/validation counts, not image-rights or editorial signoffs.

Passed checks:

- `tests/editorial/test_narratives_06.py`:seven real-data tests, including full archive/locale/media preservation, rejection of late drift, immediate replay, exact 45-job brief migration, idempotence and atomic failure.
- `content/expansion/check_calendar_identities.py`:five earlier-identity regression tests, reconstructing later narrative06/05/03 preimages in memory.
- `content/expansion/check_playhub_locales.py`:complete exact-source daily and source-locale comparison with the explicit 49 canonical exceptions.
- `content/expansion/check_wikipedia_locale_overlays.py`:six revision, attribution, structure, collision and source-drift tests.
- `tools/catalog-audit.sh content/catalog.json /mnt/f/Playhub/Plugin/Playhub/catalog/on-this-day.json`:the real C++ parser retained 1405 entries, 5209 sources, 350 day-precision dates and 3228379 body bytes. Exact original Playhub text/headings/source URLs, reviewed narrative06 identities, parser limits, chronology and Today adversarial fixtures passed.
- `tools/editorial-plan.py` and `tools/refresh-media-backlog.py`:fresh register/backlog generated, repeated without duplicate migration or lost assignments.

Assembly evidence is in `build/narrative06-assembly.log` and `build/narrative06-assembly-repeat.log`; register/backlog outputs have matching named logs. The independent original narratives and source-review declarations remain separate from these integration checks. No package, publication, console write or runtime-code change was performed in this step.
