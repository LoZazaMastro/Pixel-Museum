# Direct Wikipedia reference translations: batch 06

Four complete illustrated English references translated directly into Italian, Spanish, French and German: 16 article/language pairs, 48 paragraphs and 48 existing editorial headings. English source paragraphs and positions are preserved, with no new historical claims or original feature translations. Independent language review and admission remain pending.

- Batch: `content/expansion/wikipedia-locales-reference-06.json`, SHA-256 `6f6acf10ad367cd846fde2b038a83f5316c5aab5e317cfed00c44d8f48a530d8`.
- Author validation: `content/editorial/wikipedia-locales-reference-06-validation.json`, SHA-256 `57f1c60f15ad6c958066f0f816b47b831cd027c8c364340416c979be33897b4f`.
- Complete authoring source freeze: `build/research/wikipedia-locales-reference-06/source-freeze.json`, SHA-256 `379da89b31f27ba8e8a7cf7e120e1b8edcc0a848e5fd889a62189cde4c3025fa`.
- Catalog snapshot at freeze: `37d81b0abff1f58d7cb796ad155af9cdf40d5147396d9d311a738f11028ce2de`. This is a comparison snapshot; concurrent parent work may change unrelated master content. Each translated English field was compared with the actual current entry before finalisation.

| Reference | Exact English revision | English body SHA-256 |
| --- | --- | --- |
| `wikipedia-1055604` — Gun Fight | [1376644487](https://en.wikipedia.org/w/index.php?oldid=1376644487) | `2122469371a35199c15cc14e8c0b90ed616305f593f00874491db2be952fd231` |
| `wikipedia-595917` — Space Harrier | [1376671325](https://en.wikipedia.org/w/index.php?oldid=1376671325) | `7a4cb48f934fb120516bc51b4229e79fa406d831c7efff24ca51b5713722979a` |
| `wikipedia-1159581` — Ultima IV: Quest of the Avatar | [1379892943](https://en.wikipedia.org/w/index.php?oldid=1379892943) | `38ade48d440869663904e9ef6a9dfc5b4a58980245a600d8dfc26786f3dd1339` |
| `wikipedia-15448272` — World of Goo | [1370760711](https://en.wikipedia.org/w/index.php?oldid=1370760711) | `92625ecb5c4821f9e92a2a4c0e53fb0ea4a96b7e516ef9d5abf1029c44c06dcc` |

## Translation decisions

- **Gun Fight:** Western Gun, Gun Fight, the 1969 electromechanical game and the 1975 Midway adaptation remain distinct. Cabinet sales preserve the value 8,600 with natural local thousands punctuation. Rankings retain their separate years. The source’s last sentence omits a preposition before Atari; each target uses grammatical prose while retaining the platforms and chronology. The universal first-human-combat and first-microprocessor claims are inherited from the exact reference, not independently established by this translation batch.

- **Space Harrier:** The unrealised military concept, released fantasy setting, analog flight stick and moving deluxe cabinet remain different parts of the account. French uses actionneurs linéaires and tangage/roulis, while German identifies the two tilt axes; no wheels, hydraulic specification or new motion claim is added. More than twenty ports, two 1988 sequels, the 2000 spin-off and 2003 remake remain in the same paragraph. Kamiya’s Capcom/PlatinumGames association is inherited; no current employer claim is added.

- **Ultima IV:** The Age of Enlightenment and Age of Darkness names and game titles are preserved. Written sixteen-times map size remains sixteen in each language, rather than an invented new measurement. The 1996 rank is explicitly the list for IBM-PC-compatible systems, not a new claim about every platform. The very short sequel paragraph stays separate.

- **World of Goo:** Nomination at the Independent Games Festival is kept distinct from later awards won. Award names remain recognisable; the twelfth annual ceremony is retained. Physics, economical use of goo balls, platform chronology and the 2 August 2024 sequel collaboration remain unchanged.

## Structural and source checks

The pure overlay join was exercised only in memory with this batch’s allowlist. It accepted all 16 pairs and preserved all preexisting base-locale entries; English, Portuguese, Russian and Ukrainian documents remained unchanged. Negative fixtures rejected altered English paragraphs, headings or source revisions, missing translation licence, wrong paragraph count and a collision with a protected original Playhub locale. No production allowlist or generated locale file was changed.

Per-paragraph decimal-value occurrence counters and proper names were checked against the frozen and current English source. Written numerals and ordinal meanings were additionally read during translation. All target text was read back as UTF-8; no replacement character, unexpected question mark, null or joined year transport corruption remains. These author checks are not independent native-language approval.

Each translation carries the exact English Wikipedia revision URL, contributor history, CC BY-SA 4.0 licence URL and revision timestamp, together with a target-language translation credit and disclosure of translated editorial headings. The headings are Pixel Museum editorial material, not attributed as original Wikipedia headings. Existing image records are inventoried only; no new assets, permissions or quality signoff are claimed.

No catalog, original Playhub source, source-locale file, assembled runtime locale, assembler, runtime code, package or console was modified. Root review and explicit source-checked admission are the next steps.
