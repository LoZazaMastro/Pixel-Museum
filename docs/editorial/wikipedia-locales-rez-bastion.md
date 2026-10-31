# Rez and Bastion: reference translations

The batch in `content/expansion/wikipedia-locales-rez-bastion.json` contains eight complete translation records: the current English Wikipedia reference entries for Rez and Bastion translated into Italian, Spanish, French and German. It covers titles, subtitles, summaries and every reference-body paragraph. Game titles retain their original names.

| Runtime ID | Reference | Source revision | Paragraphs per locale | Headings per locale |
| --- | --- | --- | --- | --- |
| `wikipedia-101230` | Rez | [1365952586](https://en.wikipedia.org/w/index.php?oldid=1365952586) | 4 | 0 |
| `wikipedia-30602654` | Bastion | [1380386561](https://en.wikipedia.org/w/index.php?oldid=1380386561) | 3 | 0 |

There are 28 translated paragraphs in total. Both source `story_headings` arrays are empty, so the translations keep them empty rather than inventing section titles. No attached original feature was translated: the Mizuguchi feature on Rez and the Korb/Barrett feature on Bastion remain outside this batch. Original Playhub editions are also untouched.

## Text and attribution

The translations follow the current catalogue text directly; they are not imports from Italian, Spanish, French or German Wikipedia articles. Names of people, studios, products, platforms, events and fictional entities are preserved. Dates, version chronology, sales totals, qualified critical judgments and the distinction between original releases and later ports are retained. Thousands separators and ordinary place-name forms follow the target language. The nickname “the Kid” and the named event “Calamity” remain identifiable rather than being replaced with an unverified official localization.

The English Bastion summary currently stops after “Warner Bros.” This boundary is preserved in all four translated summaries. Its complete publisher name, Warner Bros. Interactive Entertainment, remains in the first body paragraph. This batch does not silently repair or extend the source summary.

Each locale record carries its language, exact English-source hash, source revision, contributor-history link and CC BY-SA 4.0 licence. Its active attribution explicitly identifies the text as a translation. The original English attribution is preserved separately as `source_attribution`, so its statement about unmodified English source text is not mistaken for the status of the translation. The translated text remains an adaptation under the same share-alike licence.

## Integration contract and checks

The two top-level `entries` contain `locales.it`, `.es`, `.fr` and `.de`. Each locale record exposes `title`, `subtitle`, `summary`, `body[]` and `story_headings[]`, alongside attribution and provenance. A later assembler should accept the overlay only if the source hashes still match; this file does not modify the master catalogue or any master locale file itself.

Source-body hashes:

- Rez: `f0ce5d32a309e267b3fcfc1e16a29e8a850a737369f6322878f9d1b453dbedfe`
- Bastion: `2999d05b76605cec03953f5ce1a4b6cac45182feb2a212c44ba5c9a6fcb1d755`

Hashes use SHA-256 over UTF-8 JSON with `ensure_ascii=False` and compact comma/colon separators, without a trailing newline. Each entry also has a field hash covering `title`, `subtitle`, `summary`, `body` and `story_headings` in that order, which detects a summary or heading change even if the body stays identical.

Structural checks passed for eight unique ID/locale pairs, exact paragraph and heading counts, nonempty UTF-8 body text, preserved proper names, equivalent numeric tokens after localized thousands formatting, and unchanged revision/contributor/licence URLs. The payload includes per-locale translated-body hashes and an explicit audit. Independent agent source/semantic review is now complete; human native-language and device typography/layout signoff remain pending. The authoring batch's draft status remains historical provenance rather than a signoff claim. See [the integration review](wikipedia-locale-integration-review.md) for the separate source-checked runtime join and actual host-parser regression. No console installation or publication was performed for this review.
