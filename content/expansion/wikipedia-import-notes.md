# Wikipedia reference collection

The completed main pass supplies 589 additional English reference articles, with 143,501 words in their selected introductions. A separate early-games supplement adds 51 articles and 19,220 words from substantive opening, gameplay and history sections where introductions alone were too short. Together they supply **640 reference articles and 162,721 words**, each with at least 120 words of real source prose. They were deduplicated against the original museum titles and the 318 Playhub candidates before selection. Alias deduplication remains a responsibility of the final catalogue assembler; notably, the distinct games *Dnd* (1975) and *DND* (1977) should not be conflated solely by capitalisation.

The text is reproduced from identified English Wikipedia revisions under CC BY-SA 4.0, rather than presented as new museum writing. Each record retains an immutable revision permalink, timestamp, article identifier, contributor-history link, licence link and a statement of changes. Article, history and licence links also appear directly in `sources` so a client can display them without understanding the additional attribution object. **Keep that attribution visible when merging or displaying these articles.**

Discovery used 56 annual video-game pages from 1970 through 2025, with bounded year-category supplements for the 1970s and 2020s. The earliest release-year category on each included article establishes its year. No exact date or regional release is inferred. These are reference records; a category is not a substitute for verifying a precise anniversary.

| Decade | Main file | Early supplement | Combined |
|---|---:|---:|---:|
| 1970s | 56 | 44 | 100 |
| 1980s | 93 | 7 | 100 |
| 1990s | 110 | 0 | 110 |
| 2000s | 110 | 0 | 110 |
| 2010s | 110 | 0 | 110 |
| 2020s | 110 | 0 | 110 |

The early supplement uses complete prose paragraphs from actual full articles rather than padding short leads. It selects the opening and early substantive sections, removes headings/list fragments, and records that selection in attribution. The selection is substantial but does not claim to contain every game or provide equal coverage of every region and genre.

Nineteen new entries have Wikimedia images with verified free licences and identified creators. Text licensing does not grant image rights. Nonfree game covers and images with missing ownership/licence information remain absent; their absence does not stop the text import. Image source pages, creators and their own licences must travel with the image records.

`build-wikipedia-ready.py`, `enrich-wikipedia-media.py` and `extend-wikipedia-early.py` reproduce the pass using cached API responses and a little over one second between uncached requests. The lead-text importer uses batches of twenty because the TextExtracts API limits introductory extracts per request; the supplement requests full extracts one article at a time. Cached responses are research/build material, not runtime assets. Catalogue-ready files are `wikipedia-ready.json` and `wikipedia-early-ready.json`; `wikipedia-audit.json`, `wikipedia-early-audit.json` and `wikipedia-media-audit.json` record the actual results.

The featured authored stories are kept separately in the original catalogue and `narrative-revisions.json`. This imported reference material is not a claim to have conducted the interviews cited by Wikipedia or to have inspected every original document in those articles' bibliographies.
