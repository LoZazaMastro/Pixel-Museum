# Illustrated Wikipedia references: translation batch 05

Six complete English references are translated directly into Italian, Spanish, French and German: 24 article/language pairs, 72 paragraphs and 72 existing editorial headings. The English source has 18 paragraphs and 1,412 whitespace words. These are translation drafts awaiting independent language review and explicit admission, not new articles or finished language signoffs.

The authoring file is `content/expansion/wikipedia-locales-reference-05.json`, SHA-256 `0f8e8b12adc31700d94ed80982f0293af05466606c8a496559fb95093fcfd656`. The validation receipt is `content/editorial/wikipedia-locales-reference-05-validation.json`, SHA-256 `3f94fc2d06e8bc52015132e674dc6205a1e021bf1585e86fff0a663c680ba3a6`.

| Reference ID | Article | English Wikipedia revision | Existing image records |
| --- | --- | --- | ---: |
| wikipedia-18711188 | Fez | 1370716693 | 4 |
| wikipedia-43010284 | Ori and the Blind Forest | 1378417302 | 4 |
| wikipedia-52924170 | What Remains of Edith Finch | 1380916237 | 6 |
| wikipedia-54027590 | Dead Cells | 1380424588 | 6 |
| wikipedia-54280556 | Ori and the Will of the Wisps | 1373008468 | 4 |
| wikipedia-72536576 | The Case of the Golden Idol | 1367915385 | 3 |

The IDs were announced before translation. They avoid the Playhub template restoration/identity lanes and all eight systems/authors batch 06 parents. Each reference has three complete paragraphs and three specific existing headings. No original commissioned feature or Playhub story has been translated here.

## Source and translation boundaries

The announced whole-catalog source snapshot is `991da63d4de21182057fcbe076192659a71b4df66912b20a1997de6bf7762512`. This is a historical snapshot label, not a claim that unrelated concurrent catalog work stopped. Before saving the batch, every translated English title, subtitle, summary, paragraph and heading was compared against both the announced freeze and the current catalog. Exact English text, compact-JSON body and heading hashes, paragraph hashes, source-field hashes, revision timestamp, immutable revision URL, contributor history, source records and CC BY-SA 4.0 licence are retained per entry. Each target language has its own translated attribution and adaptation disclosure. Editorial headings are distinguished from the Wikipedia prose.

The source body hashes are:

| Reference ID | SHA-256 of English body compact JSON |
| --- | --- |
| wikipedia-18711188 | 7e9f74fcd8f56c218e91f70d825fa185f35568f27f5742367544c2f156ccece3 |
| wikipedia-43010284 | ea5eb32dd0f1c7447a1f65db691d8c89bc5bdf33d72f7b23ecffa1f1aad95894 |
| wikipedia-52924170 | 3fc2a5411e56a1821d0d0bc5749eb6b3a9a9de5c3106b9afee88648ebaf21464 |
| wikipedia-54027590 | 6d36478c8bb08d3ce2793dc82821b3b7ae621bbd95e206958c38068e3ad3bdb1 |
| wikipedia-54280556 | 965d26a043c766c9f31e4bd9c313b4c275afd2109cafadb52c32982acb09ab53 |
| wikipedia-72536576 | 92db4e2f6162e78269446d4582bdf8a2824be6caa8c9d725b0cdb946237b669d |

Paragraph order and scope are retained. Names, platforms, editions, dates and numerical occurrences were checked paragraph by paragraph. Roman century notation XVIII/XVIIIe is normalized to 18 only in the numeric comparison, not in the saved source. Written quantities such as five years, seventeen years old, seven years and one million received a semantic translation check. Game titles and cited film titles remain identifiable in their source form. Transport spacing was corrected only in the new translations.

## Inherited English details

- Edith Finch's “Best Game 2017” is translated as the best game **of 2017**, not as a ceremony held in 2017. The coordinating editor checked BAFTA's [official 2018 winners announcement](https://www.bafta.org/media-centre/press-releases/winners-announced-for-the-british-academy-games-awards-in-2018/): the ceremony took place on 12 April 2018 for the games of 2017. No English sentence or hash changed, and the translations add no ceremony date.
- Ori and the Blind Forest calls Definitive Edition an “expansion” and describes the Switch release under the base title. These inherited edition terms were translated as given and flagged for a separate source-bound terminology review. No edition substitution was made.
- Dead Cells says death loses all items and other abilities while also describing permanent upgrades. This inherited generalization was retained rather than silently narrowing its scope. The new translations are not a fresh historical or mechanical audit of that English claim.

The existing image-record counts above establish why these references were chosen; they do not establish resolution, card fit, permissions or image quality. No media was acquired, duplicated, reassigned or approved by this translation batch.

## Validation and handoff

The pure overlay fixture passed 6 source references, 24 language pairs, 72 paragraphs and 72 headings. It preserved every pre-existing base-locale entry and left English, Portuguese, Russian and Ukrainian unchanged. Negative fixtures rejected modified English prose, headings, revision identity, missing translation licence, missing paragraph and a collision with protected Playhub locale content.

The helper admission list was overridden in memory for that fixture only. Neither `generate()` nor the assembler was executed. Catalog, helper and all eight locale files had matching before/after hashes during validation. No production admission list, master, locale, runtime, package, console or FTP operation was changed or performed. Independent language review, root admission and native rendering of this batch remain pending.
