# Networks, audiences and the historical record — batch15

Frozen candidate: `content/expansion/editorial-networks-history-15.json`.

Revised SHA-256: `477ad2fd42810d444bd123cda9e5b25826df72385b9f77695f83106a53a1eec9`.

This is original additive prose awaiting independent source and placement review. It contains **8 features, 32 matched cards and 2,747 body words**. Individual cards contain80–92 whitespace-delimited words. None is automatically admitted; no parent narrative, master catalogue, source Playhub file, package or console payload was changed.

## Placement proposals

| Feature | Proposed placement | Scope |
|---|---|---|
| China game networks | CrossFire `wikipedia-33952595` attachment | A specific Korean development/Chinese publishing partnership; Chinese service2008 is distinct from Korean launch2007. |
| Steam library ownership | `steam` attachment |2003 notice;2023 anniversary; current2026 agreement; developer documentation;2024 sharing. Current terms are not attributed to2003. |
| MMO community work | `workbook-05-06-eve-online` attachment |2023 corporation project administration and2024–25 documented volunteer rescue/navigation. |
| App Store change | Held standalone |2008 distribution and2019 Arcade announcement; the March announcement is not presented as a launch. |
| Streamers and play | Held standalone |2014 Twitch Plays Pokémon and clearly later/current GDQ community programmes. No unsupported claim to the first game broadcast. |
| Labour and credit | Held standalone |2023 AEGIS-CWA election and bargaining goals, then the2024 SEGA of America bargaining-unit agreement. |
| Pandemic shared spaces | `animal-crossing` attachment |Getty2020 pattern tool; aquarium staff's2021 retrospective; NVM collecting invitation. Not a population-level mental-health claim. |
| Living-history method | Held standalone |2012 Apple II source recovery and2025 VGHF library; no attachment to the unrelated2008 Prince of Persia game. |

All existing proposed-parent bodies and sources were read and captured in `build/research/editorial-networks-15/parent-snapshots.json`. The receipt records their observed hashes. The EVE parent still includes inherited Playhub wording; this proposal does not silently repair or replace it.

## Evidence and word charging

`build/research/editorial-networks-15/validation-receipt.json` records all **23 distinct primary publications**, their exact locators, SHA-256 and snapshot paths.22 are actual downloaded source responses; the National Videogame Museum announcement is a specific web-reader response, retained as such because directGET returned403. That response's main article is at lines24–30. It is not represented as an independently successful direct download.

Each source is charged the **entire associated paragraph(s), their headings, the complete feature title and summary, and the bibliographic publication title**. The charge is the larger of whitespace splitting and Python Unicode `re.findall(r'\b\w+\b', text)`. Nothing is discounted between multiple citations. The maximum charge is200 words per publication; reported direct quotations are zero. Every feature cites at least two separate primary publications. Bibliographic snapshots and original reference material remain research evidence, not reprinted museum articles.

The first review snapshot (`05f85962…`) is preserved in the research directory. Independent review identified an aggregate cross-batch collision: the IGDA2023 guide already supports batch10's `feature-credits-as-historical-record`. Its two candidate paragraphs were removed, rather than renaming that publication or using a mirror. The replacement uses the genuinely separate10July2023 union-election announcement, including translator Ángel Gómez's stated goals. The2024 contract remains a different primary publication. A direct NLRB request timed out; no independentNLRB snapshot or live verification is claimed here. The earlier guide remains available as unused research evidence.

The same bounded revision corrected possessive/month spacing, identified Roland Gustafsson specifically as a disk programmer, and shortened visible prose/metadata to pass the stricter aggregate counting method. This revision awaits the reviewer's final difference check.

Twitch returned gzip-compressed bodies that the initial lightweight fetcher had not decoded. The evidence pass corrected decoding and read the actual article text before writing. Steam's announcement and anniversary content required reading its embedded publisher data; the saved raw response and extracted text remain available. PDF text for Tencent and IGDA was extracted from the successful original responses using pypdf. The source PDF is authoritative where extracted punctuation is imperfect.

Excluded sources remain recorded: a guessed Monterey annual-report URL returned404; a guessed new Mechner permalink returned404; the direct Steam Offline Mode response exposed only a shell. No prose relies on those failed or empty responses. The Mechner citation uses the verified archive fragment `#2012-04-source`; its separate September2024 repository notice supplies the franchise-rights distinction.

Community statistics remain attributed to participants or publishers. The text does not reproduce individual forum replies, invent testimony, claim private workplace evidence, or imply permission to reproduce archive materials merely because they are accessible. Every card has a concrete media brief; this file admits **no photographs, video or rights clearance**.

Automated checks pass for IDs, exact four-card matching,80–92-word bodies, parent existence, all snapshot hashes, two-plus publications per feature, and conservative source budgets. **Independent editorial signoffs:0.**
