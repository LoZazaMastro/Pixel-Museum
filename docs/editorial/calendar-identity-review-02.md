# Published subject identity corrections and full review queue

Two original published editions attach the wrong game metadata to complete stories about other subjects. The 21 May edition is labelled Hellblade II but every paragraph concerns Never Alone and cultural diversity. The 30 August edition is labelled Astral Chain but every paragraph concerns the original Street Fighter. These are inherited publication mismatches; the repair preserves the complete original narratives, all headings, source records and opaque IDs.

`content/expansion/calendar-identity-corrections-02.json` archives both published editions, both incorrectly associated candidate records and master snapshots, the original Street Fighter reference, and the exact replacement Wikipedia revision extracts. `integrate_calendar_identities.py` validates these identities before the normal calendar enrichment. Its assembler hook runs after the reviewed template revisions. No new identity can enter through that hook without changing its explicit two-case admission.

| Preserved ID | Correct resulting subject and treatment |
| --- | --- |
| `daily-05-21` | Never Alone, year 2014, linked to the new `never-alone` destination. The 21 May calendar slot remains cultural-diversity scheduling. |
| `never-alone` | Complete original four-section Never Alone story; publisher-listed PC release 18 November 2014. No image is inferred from the former Hellblade identity. |
| `workbook-05-21-senua-s-saga-hellblade-ii` | Actual Hellblade II, 2024; opaque ID retained, with two complete exact English Wikipedia paragraphs and explicit CC BY-SA attribution. |
| `daily-08-30` | Street Fighter, year 1987, linked to `wikipedia-2829113`; original 30 August schedule preserved. The exact regional launch day remains unverified in metadata. |
| `wikipedia-2829113` | Original four-section Street Fighter Playhub story; previous three-paragraph reference archived. The old Wikipedia unchanged-text notice does not describe its replacement prose. |
| `workbook-08-30-astral-chain` | Actual Astral Chain, 2019; opaque ID retained, with three complete exact English Wikipedia paragraphs and explicit CC BY-SA attribution. |

The [Never Alone publisher page](https://store.steampowered.com/app/295790/Never_Alone_Kisima_Ingitchuna/) identifies the 2014 PC release, Nuna/Fox, development collaboration and video insights. [UNESCO](https://www.unesco.org/en/days/cultural-diversity-dialogue-development) independently identifies 21 May as the annual cultural-diversity observance. The [Astral Chain developer page](https://www.platinumgames.com/works/astral-chain) identifies its subject and 30 August 2019 launch. [Ninja Theory's launch post](https://news.xbox.com/en-us/2024/05/21/hellblade-2-launch-blog/) supports Hellblade II's 21 May 2024 PC/Xbox launch.

The saved Hellblade reference's first paragraph says ninth-century Iceland, while the current publisher description says tenth century. Its complete first paragraph is therefore omitted; the two selected gameplay/release paragraphs stay verbatim, and the exact first source sentence supplies the summary. The full conflicting extract remains in the review declaration. The selection/change notice and editorial headings are explicit. This correction does not pretend to establish a new resolution of the historical setting.

## Preservation and media migration

The actual Playhub `on-this-day.json` remains unchanged, SHA-256 `49d7f954896f415b062367393d297e851fd43056ae56618d3c8e0bc58d5e9a2c`. The existing locale exporter regenerates museum locale metadata against the corrected canonical mapping. Only two daily titles and two canonical alias destinations change; every source body, heading, summary, subtitle and provenance value stays exact. These approved generated-metadata migrations are separate from the Wikipedia translation overlays, which never rewrite source locale documents.

The explicit media migration archives the previous sections, source URLs and hero brief for restored Hellblade II, Astral Chain and expanded Street Fighter. Original Never Alone briefs move to the one new job; original Street Fighter briefs move from the former Astral job to its actual canonical job. Restored reference paragraphs receive specific new acquisition briefs and exact hashes. All old job IDs and work units remain; one named Never Alone work unit is added. Public source access does not admit an image or establish reproduction permission. No imagery is copied between different subjects.

`python content/expansion/check_calendar_identities.py` passes five regression groups: all 365 exact daily narratives/1,656 sections; 333 canonical aliases plus 32 standalone editions; exact replacement references and distinct date semantics; atomic rejection of stale/unreviewed edits; all eight existing locale prose/headings retained with only approved routing/title changes; and media-job preservation, one addition, archived briefs, unique work units and repeat-safe migration. Temporary trees are used for locale writer tests. Tests leave the actual master and locale files untouched.

`content/editorial/calendar-identity-review-02.json` records the implementation checkpoint. At this handoff the helper and hooks are prepared; this agent has not executed master assembly, media-register refresh, packaging, FTP or a console operation. Final assembled-source and package checks remain the coordinator's next gate.

## Every edition accounted for

`content/editorial/playhub-identity-review-queue.json` enumerates all 365 editions and 1,656 sections, exact English and eight-language reference hashes, original title/year/canonical metadata, current master observations and explicit review states. The two confirmed mismatches lead the queue. The remaining 363 editions are marked unreviewed, rather than accepted by keyword agreement. Twenty-five units contain at most fifteen editions each.

`python tools/build-identity-review-queue.py` refreshes observations while preserving recorded reviews when source prose/headings are unchanged. A source change retains prior evidence and reopens review. Each unit requires reading the full original story, identifying its actual subject/event, checking title/year/date/canonical routing and image identity, and citing specific evidence for corrections. Scheduling, regional launches, reveals and commemorations must remain distinct. No source prose rewrite is authorized by this queue, and no full historical or media signoff is implied by enumerating it.
