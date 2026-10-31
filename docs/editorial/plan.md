# Pixel Museum editorial production plan

A museum of games, the people who make them and the cultures that grow around them. Each story should leave the visitor with something concrete to notice, hear or understand.

## What this plan covers

Every distinct article currently present in the collection has a record, section inventory, source list and explicit remaining work in `content/editorial/production-plan.json`. The CSV register is a compact companion. A plan covering the collection is not a claim that the collection has passed editorial review.

## Current inventory

| Measure | Count |
| --- | ---: |
| Distinct timeline articles | 1,395 |
| Narrative sections | 5,165 |
| Words in current narrative bodies | 505,948 |
| Articles with any cover URL | 1,395 |
| Articles with metadata-qualified HD covers | 615 |
| Articles with any images mapped to a majority of sections | 337 |
| Articles with metadata-HD images mapped to a majority of sections | 216 |
| Articles needing specific section headings | 492 |
| Sections needing specific headings | 1,475 |
| Imported reference articles | 655 |
| New articles in the history backlog | 140 |
| Attached authored features | 91 |
| Attached sections additional to original bodies | 364 |
| New standalone priority features | 11 |
| Standalone priority sections already in narrative count | 49 |
| Priority feature cards across both placements | 413 |
| All narrative sections including attached features | 5,529 |

These counts describe the files at the recorded catalogue hash. An image URL is not proof of availability, resolution, rights or contextual relevance. Mapped section coverage must still be reviewed by a person.

## Editorial sequence

1. Import every published Playhub edition, introduction, chapter and existing translation. Keep an edition-to-canonical-article map so deduplication never deletes its story. Console articles remain available even when a suitable model is missing.
2. Resolve provenance, duplicate subjects and event dates. Distinguish release, announcement, regional launch, birth date and in-game calendar event. Never turn the day an article was published into a historical launch date.
3. Fill media gaps in the imported collection before treating the wider reference collection as a finished gallery. Every timeline entry needs a relevant cover; most narrative cards need contextual illustrations.
4. Review each article as a sequence of cards. Preserve the full source narrative, with short useful headings, meaningful captions and reading expansion where needed. Add original writing when it explains a person, decision, process or overlooked context better than the reference introduction.
5. Complete the historical gaps recorded in the history backlog. Build cross-links between documented influences and consequences. Review geographical, cultural and disciplinary balance after each batch.
6. Reuse Playhub language editions. Translate the English Wikipedia additions into the selected languages, retaining their revision and licence notices. Report fallback coverage per language; do not label untranslated English as localized.
7. Run the entire collection through source, image, link, layout, controller and performance checks. Then review the resulting stories on the PS5 before release.

## Experience art direction

Interactive studies retain paper and ink, simple abstract geometry and a single contextual accent. Richer mechanics, timing, feedback and sound add depth; literal scenery and game-specific colour schemes do not.

## Article structure

An opening introduces the event and its stakes. Subsequent cards explain a few specific choices, the people involved, contemporary context and what changed afterward. A short reference entry can remain short when it is sufficient; a major turning point needs a fuller, illustrated story. Avoid repeated generic conclusions about legacy, immersion or innovation.

For a game, show a concrete mechanic, artistic or musical choice alongside its historical circumstances. For a console, cover its intended audience, industrial design, technical trade-offs, software and regional life. For a person, explain their work and collaborators rather than reducing a career to a birthday. For a cultural story, include the players, institutions and working conditions that made it possible.

## Approval gates

| Gate | Evidence required |
| --- | --- |
| Identity | The title, version, subject and region match every associated resource. |
| Date | The event meaning and date precision are stated and supported; uncertainty stays visible. |
| Text | Complete, specific narrative; no empty cards, repeated templates or unsupported superlatives. |
| Sources | Claim-level research notes and durable source links; interviews distinguished from later recollections. |
| Cover | Relevant remotely hosted image, verified dimensions and working fetch; no upscaled small source. |
| Card media | A majority of narrative cards illustrated where sources exist, with reviewed bindings and captions. |
| Rights | Creator, source and applicable licence or permission recorded; no blanket assumption that museum access permits reuse. |
| Film and music | Exact title and publisher checked; availability and audio-only soundtrack behavior tested. |
| Models | Faithful, licensed, detailed asset with material and on-device performance validation; absence does not suppress the article. |
| Localization | Correct source edition, intact paragraph structure and explicit English fallback for missing translations. |
| Presentation | Long titles, body expansion, gallery animation and credits readable with the controller. |
| Review | Editorial sign-off recorded separately from script checks and device tests. |

## Language coverage

Every article has English base text. Exact source-locale and English-fallback counts are recorded per language in the production JSON. Attached English features do not inherit a translation from their localized parent. The English sidecar restores source editions; it is not total English coverage. Feature and Wikipedia translations remain separate production tasks.

## Work ownership

The import lane owns source fidelity, canonical mapping and translations. The history lane owns missing subjects, factual framing, dates and narrative briefs. The media lane owns archives, images, films, recordings and contextual card coverage. Integration owns the complete work register, duplicate review, links, presentation checks and the final release gates. Each batch must name concrete article IDs and report evidence, not just a number of added rows.

## Decade inventory

| Decade | Articles | Cover URLs | Metadata HD covers | Sections |
| --- | ---: | ---: | ---: | ---: |
| 1880s | 1 | 1 | 1 | 19 |
| 1920s | 2 | 2 | 1 | 13 |
| 1940s | 1 | 1 | 1 | 4 |
| 1950s | 10 | 10 | 7 | 45 |
| 1960s | 12 | 12 | 7 | 62 |
| 1970s | 116 | 116 | 64 | 460 |
| 1980s | 163 | 163 | 105 | 569 |
| 1990s | 250 | 250 | 131 | 899 |
| 2000s | 320 | 320 | 160 | 1158 |
| 2010s | 314 | 314 | 91 | 1187 |
| 2020s | 206 | 206 | 47 | 749 |

## Working files

- `article-register.csv`: one row for every distinct current timeline article.
- `../../content/editorial/production-plan.json`: complete section-level work register and current catalogue hash.
- `history-coverage-plan.md` and `../../content/editorial/history-backlog.json`: planned research commissions.
- `media-and-experiences-plan.md` and `../../content/editorial/media-backlog.json`: media, archives and interactive-study plan.
- `../../content/editorial-collection-audit.json`: Playhub edition and source-copy evidence.
- `../../content/playhub-localization-audit.json`: available original language coverage.
- `../../content/publication-readiness.json`: automated media and narrative blockers, without hiding imported articles.

Run `python tools/editorial-plan.py` after assembling the catalogue to refresh the register. Do not manually mark a missing image or an unreviewed article complete.
