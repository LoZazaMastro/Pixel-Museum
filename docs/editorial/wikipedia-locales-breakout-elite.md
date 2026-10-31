# Direct reference translations: Breakout and Elite

The authoring batch `content/expansion/wikipedia-locales-breakout-elite.json` contains direct Italian, Spanish, French and German translations of the exact English master title, subtitle, summary, body and existing headings for two reference entries. It contains eight article/language pairs, 32 translated paragraphs and 12 translated headings.

The original authoring pass changed no locale file, master catalogue, assembler, package or console file. Independent agent content review now admits a separate source-checked runtime overlay; human native-language and device typography signoff remain pending. See [the integration review](wikipedia-locale-integration-review.md) for the current join and preservation checks.

| Entry | English revision | Paragraphs per language | Headings per language |
| --- | --- | ---: | ---: |
| `wikipedia-453246` — Breakout | [1380424387](https://en.wikipedia.org/w/index.php?oldid=1380424387) | 3 | 3 |
| `wikipedia-286774` — Elite | [1380286484](https://en.wikipedia.org/w/index.php?oldid=1380286484) | 5 | 0 |

Elite has no headings in the English master, so every translated `story_headings` array remains empty. Breakout's three headings are identified as translations of Pixel Museum editorial headings, separately from the Wikipedia lead text.

## Source identity

The source catalogue snapshot is `257d0b0f95f2a3c8c319b09387b5645eb72644ea7fd98675a100e8cf2b53e0cf`. Each entry retains the exact English title, summary, body and headings, its immutable revision URL and timestamp, contributor-history link, licence link and original attribution.

English body-array SHA-256 values:

- Breakout: `862ba2417be0495d6050434d5bed68b06e53bdf0f894060a12521c3ca0d18d56`.
- Elite: `a99a81a76630c72873225d2e08de47fe544b6df9d7cc152e2fe36e7e1d0d515c`.

These hashes use the UTF-8 compact JSON body array, with `ensure_ascii=false` and comma/colon separators. Exact SHA-256 values for every individual English paragraph, title, summary and heading array are also recorded. Integration must reject a changed source rather than silently applying translations to a different revision or paragraph sequence.

## Translation decisions

Paragraph positions, numeric values and their occurrence counts are preserved. Game, person, company and publication names remain identifiable, including The Dark Wheel, the Frontier titles, Horizons, Odyssey and the quoted label “Game by Frontier”. Rapid-response gameplay in Elite is translated as reflex-based play, not as a reference to the Twitch service. Technical language distinguishes wireframe graphics and hidden-line removal.

The source's historical assertions are translated as supplied. This batch neither adds new history nor silently revises the English article's compressed account of later Elite features, its record claim or its ownership wording. A later factual review should act on the source separately and trigger translation invalidation through the recorded hashes.

No local-language Wikipedia text was substituted. No Playhub edition or newly authored original feature was translated. The scope is exactly the two reference IDs and four requested languages.

## Attribution and review boundary

The translated Wikipedia lead text retains CC BY-SA 4.0, exact source and contributor URLs, and an explicit notice that translation is a change. The original English attribution is kept in the source snapshot; it is not reused as a misleading claim that the translated prose is unchanged English.

Checks pass for the two-ID scope, four-language completeness, matching body and heading counts, nonempty prose, repeated dates/numbers, proper names and exact English-source hashes. The master and all eight original locale-file hashes remain unchanged by this work. Generic subtitles and active translated credits are now included and source-bound. Independent agent semantic review is complete; human fluency and native typography signoff remain pending. Runtime overlay integration uses the separate helper and derived locale directory described in the integration review.
