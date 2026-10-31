# Super Metroid and Symphony of the Night: direct reference translations

The authoring batch `content/expansion/wikipedia-locales-metroid-castlevania.json` translates the exact current English title, generic subtitle, summary, three body paragraphs and three existing editorial headings for each reference into Italian, Spanish, French and German. There are eight article/language pairs, 24 translated paragraphs and 24 translated headings. No attached original feature or Playhub edition is translated.

| Reference ID | English revision | Paragraphs / headings per locale |
| --- | --- | --- |
| `wikipedia-355914` — Super Metroid | [1379193034](https://en.wikipedia.org/w/index.php?oldid=1379193034) | 3 / 3 |
| `wikipedia-756296` — Castlevania: Symphony of the Night | [1380803428](https://en.wikipedia.org/w/index.php?oldid=1380803428) | 3 / 3 |

The observed catalogue snapshot is `959060a6290ec1990226c4ca3ce5a240b7e1a4385fb380501839f10e19208d6e`. Source arrays, per-paragraph hashes, title/subtitle/summary hashes, the combined five-field hash, attribution and exact source lists are retained. Combined hashes use the ordered fields `title,subtitle,summary,body,story_headings` in compact UTF-8 JSON with comma/colon separators and no trailing newline. Catalogue-wide changes do not substitute for checking those exact source fields and revisions.

## Meaning and attribution

Names, sequel titles, studio/platform names and paragraph order are retained. Samus remains the bounty hunter travelling to Zebes; upgrades open inaccessible areas; the eight firing directions and two-year development span stay in their original paragraph. The distinction between good sales and 1.42 million copies **shipped** by late 2003 is explicit in every translation. Decimal punctuation is localized without changing the value. Genre influence remains attributed rather than an independently established invention claim.

Symphony of the Night preserves the five-year fictional interval, Hagihara and Igarashi's different roles, Alucard's return and Richter's disappearance, the return of exploration/role-playing elements, the combined US/Japan figure of more than 700,000 units, and both praise and criticism. Its source says the genre combines “the two games” without naming that pair in the sentence. The translations keep that generic reference; they do not invent a more specific historical assertion. The source's 1997/platform wording is translated as supplied, without adding separate port-release dates.

Each locale has a localized active credit identifying direct translation from Wikipedia contributors under CC BY-SA 4.0, exact revision/article/contributor/licence links, and an explicit change notice. Existing Pixel Museum headings are identified as translated editorial headings. Original English attribution is preserved separately and is never used to claim that translated prose is unchanged English.

## Checks and integration boundary

Checks pass for exact two-ID/four-language scope, three body and heading positions per record, nonempty text, source hashes, proper names and equivalent numeric values per paragraph after localized decimal/thousands normalization. Source assertions and ambiguities are preserved; this is not a historical fact-check signoff. Independent language and native typography reviews are pending.

This batch is authoring-only. The current runtime locale helper still admits only Breakout, Elite, Rez and Bastion. The reviewed-batch manifest and its file hashes must be deliberately extended after independent review before these two new references can be included. No master catalogue, original locale file, runtime/package file, console installation or FTP destination was modified while authoring this batch.
