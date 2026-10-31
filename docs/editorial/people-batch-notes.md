# People and early experiments: first feature batch

Ten complete English drafts are in `content/expansion/editorial-priority-people.json`. They contain 40 cards and 3,507 body words, with 80–95 words per card. The drafts are ready for independent factual, media and native-layout review; they are not yet assembled into the runtime catalogue.

| Proposed feature | Historical anchor | Existing connection |
| --- | --- | --- |
| A game in front of the crowd | Bertie at the 1950 Canadian National Exhibition | `bertie-the-brain` |
| The computer shows its working | Ferranti's 1951 Nimrod demonstration | `nimrod` |
| A telephone dial becomes a game control | Douglas and EDSAC, circa 1952 | `oxo` |
| Two controls at a laboratory open day | Brookhaven, 18 October 1958 | `tennis-for-two` |
| A game improved by the next pair of hands | Spacewar's collaborative development in 1962 | `spacewar` |
| A game takes shape on the workbench | Brown Box prototype period, 1968 | `brown-box` |
| The ruler of Lagash has to decide | Sumerian Game development and revision, 1964–1966 | New subject; Addis and McKay |
| A cartridge has to survive the living room | Channel F engineering for its 1976 introduction | `channel-f` |
| The console that left room for a computer | APF console work, 1978, and its subsequent expansion | New subject; Ed Smith and APF |
| A river made from rules | Shaw's River Raid design, published in 1982 | `carol-shaw` |

The emphasis is work done by people: laboratory collaborators, a classroom writer and programmer, mechanical and industrial designers, repair skills, testing, revision and preservation. No feature awards a universal “first videogame” or “first woman designer” title. Retrospective testimony is identified as testimony, not silently promoted to a contemporary record.

## Sources and limits

There are 26 source records representing 25 publication groups. Each card names its own citations and useful document pages or sections. The two Ferranti transcription pages count as one original booklet, not two word allowances. The audit conservatively charges each whole card and heading to every cited publication group. This reaches at most 183 words per group. Charging the complete feature title and summary to every publication used in that feature raises the maximum to 200 words. No direct quotations are reproduced. The JSON includes the exact totals and counting rule.

The longer primary documents were read directly, including Kates's and Smith's oral histories, the Canadian museum monograph, the EDSAC simulator guide, Brookhaven's anniversary bulletin and the 1967 classroom project report. The latter identifies Addis and McKay and records the summer 1966 revision; its title page and printed page numbers are cited separately from PDF page numbers. Institutional finding aids establish what survives and the conditions of access. A reference scan available to a researcher is not treated as permission to redistribute it.

Four retrieval qualifications remain visible in the JSON: the Brookhaven history was inspected as indexed primary-page text after a timeout; the Smithsonian Baer spotlight was likewise inspected after a direct 404; the public Ferranti transcripts were readable directly despite the web fetcher's 403; and the unavailable ETHW Bertie flyer was excluded entirely. The first two routes should receive a stable-link check before publication.

Specific factual cautions are retained. The Canadian museum chronology dates Bertie to 1950 while Kates remembered 1951. Nimrod remains year-only because exact opening-day claims differ. Douglas's unverified thesis topic is omitted. Original apparatus, simulators, modern reconstructions and anniversary repairs require distinct captions. No precise construction duration is claimed for Tennis for Two because the institutional accounts differ. Lawson's FCC account is attributed to his recollection without an unsupported industry-wide firstness claim.

## Media and integration

All 40 cards have distinct media briefs. Five also point to existing credited catalogue image candidates: the modern Nimrod reconstruction, the restored PDP-1, Brown Box hardware, Channel F hardware and Shaw with her River Raid award. These remain candidates, with explicit identity and caption cautions. They are not falsely presented as photographs of the original demonstration, a particular repair or the act of programming. The Bertie photograph's documented provenance leads through John Vardalas to a Rogers Majestic publication; the hosting monograph alone does not confer an open image licence.

The only canonical narrative is `body[]`, with matching `story_headings[]`. Cards reference `body_index` and hold citations and media metadata without duplicating prose. Each proposed ID is distinct from the current runtime catalogue; every named related ID and era resolves. An editorial merge must decide whether to attach each feature to an existing exhibit or offer it as a connected destination. Neither route should replace its original Playhub edition.

Structural checks passed for ten unique IDs, four cards per entry, word bounds, citation resolution, HTTPS source URLs without whitespace, source budgets, unique media briefs and existing-ID references. No master catalogue, original Playhub section, assembly script, console file or published release was changed. This batch still needs independent factual approval, image-rights approval and an actual native-layout pass before it becomes a finished museum feature.
