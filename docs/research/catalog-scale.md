# Scaling the collection without manufacturing history

This audit was made on 20 October 2026. A dated release index, an existing essay
and a finished museum stop are different deliverables. The museum should make
those differences visible in its authoring pipeline, rather than fill a numerical
target with interchangeable summaries.

## What Playhub actually contains

| Local corpus | Records | Records with an English introduction |
|---|---:|---:|
| `history_days.json` | 335 | 335 |
| `history_editorial.json` themes | 52 | 52 |
| `history_imported.json` | 365 | 365 |

There are **686 distinct subjects** across the three files after case,
punctuation and spacing are normalized. This is not 752 distinct finished
exhibits: the files overlap, and the daily features/themes have no explicit year
field suitable for a chronological index.

The imported collection has real existing English narrative, not placeholders:
344–2,423 words per entry, with a median of 454. Its original mix is 313 release
anniversaries, 12 birthdays, 11 foundations and 29 commemorations. Some dates are
outside the museum's 1950–2026 range. A commemoration's associated game year must
not be turned into the release date of that calendar holiday.

The source lists include Nintendo, PlayStation Blog, Capcom, Xbox Wire, Square
Enix, Sega, Konami and other publishers alongside MobyGames, GameFAQs, Gamespot
and Wikipedia. Existing provenance is preserved; it has not been represented as
a new live verification of every linked page.

## First usable expansion

`content/expansion/playhub-museum-candidates.json` contains **318 additional
reviewable records** with an explicit year, a calendar date, existing English
copy, source URLs and an event kind. The adapter excludes 25 in-range
commemorations, six records outside the year range and 16 normalized title
matches already present in the 58-stop prototype.

| Decade | Additional reviewable Playhub candidates |
|---|---:|
| 1950s | 4 |
| 1960s | 5 |
| 1970s | 5 |
| 1980s | 30 |
| 1990s | 74 |
| 2000s | 69 |
| 2010s | 99 |
| 2020s | 32 |

These numbers describe the adapter output against the prototype at the audit
time. They will change if the base catalogue gains more matching titles. Title
matching is deliberately conservative: regional launches, aliases and renamed
hardware still need editorial deduplication. Hardware announcements retain their
announcement semantics instead of silently becoming release dates.

The file is a **review queue**, not an automatic replacement for the published
catalogue. Adapt calendar-dependent wording, select the human conflict or design
decision, verify dates against the best available original sources and assign
rights-cleared media. Existing Playhub chapter bodies are preserved rather than
replaced by generic generated essays.

`origins-additions.json` adds two original, sourced English stops ready for
editorial review: **Bertie the Brain (1950)** and **OXO (1952)**. Their sources
include a linked Rogers Majestic exhibition flyer, Canada's History, the Computer
History Museum and the EDSAC Replica Project's simulator guide. Neither entry
declares a universal winner for “the first video game.” OXO's guide uses “about
1952”; exact-day precision is not invented. Image selection remains outstanding.

## External corpus check

Wikidata is suitable for CC0 research seeds consisting of an entity, title,
release claim and source link. The direct public SPARQL endpoint returned HTTP
429 with an explicit active-outage limit of one request per minute during this
audit. No Wikidata seed is claimed as retrieved. The generator now makes **no
network request by default**; its optional `--wikidata-decade` mode requests only
one decade per invocation. Do not keep retrying an unavailable endpoint.

A Wikipedia annual-release page was inspected as a possible index source. The
1995 page itself carries citation/misrepresentation warnings. It was not promoted
to a verified corpus or used to create exhibition essays. The Computer History
Museum's graphics/games timeline is a stronger curated source for early turning
points, but source selection should follow the story, not a desired row count.

The user has explicitly accepted fewer stops for the earliest decades. There is
no need to pad the 1950s or 1960s with unrelated inventions or birthdays. For later
decades, 100 substantial stops require additional editorial research; the current
audit does not establish that target as complete.

## Actual museum and archive material

`official-archives.json` is a bounded primary-source discovery index, not a
scraped copy of institutional articles. It links the Video Game History
Foundation's actual Computer Gaming World collection record **MAG-CGW**, its
digital counterpart, 1989 Computer Game Developers' Conference recordings and
the official Sega Channel and GamePro press-CD collection portals. The CGW
record describes **284 magazines**, with a November 1981 to April 2008 collection
range that includes its successor publication. A date range for a collection
must not silently become an individual magazine's continuous publication span.
No magazine scans, recording files or press images were copied.

The Computerspielemuseum's official institutional page documents its 1997
opening and the 2011 opening of the present permanent exhibition. Its holdings
figures explicitly refer to **2022**: more than 35,000 original game/application
carriers, 350 console/computer systems and 12,000 magazines. No item-level public
API or general image licence was verified. A separately licensed photograph of
a museum reconstruction must retain that distinction in its caption.

The official **ACMI collection archive** provides a concrete reusable corpus.
One bounded TSV download, documented by ACMI's own API repository, contains
43,445 public work records, including **257 Videogame records**. There are 184
game records with a year in 1950–2026: 4 in the 1970s, 43 in the 1980s, 93 in
the 1990s, 11 in the 2000s, 27 in the 2010s and 6 in the 2020s. The other 73
have missing or out-of-range dates. ACMI's reported physical holdings of 7,000
games must not be confused with those 257 published database records.

`archive-adapters.py` emits `acmi-seeds.json` and a hash/count audit. ACMI
documents its JSON collection metadata as CC0, with TSV as a spreadsheet export;
the adapter copies factual fields, provenance and source links. **Images and
videos have separate rights**. None of the 257 game records has image metadata
in this snapshot, and this adapter selected or downloaded no media.

ACMI's `first_production_date` is not guaranteed to be the first release date:
the SNES Shadowrun record says 1992, for example. Every output seed is marked
`chronology_safe: false` and requires date and story review. A single record's
official JSON was checked successfully; the live API itself returned HTTP 403,
so the documented GitHub archive was used instead. These are additional
research seeds, not 257 finished exhibition stories.

## Authoring and loading at larger scale

Keep three states: research seed, adapted draft and published stop. A published
stop should have a date with stated precision, clear English copy, sources and
media rights. Its central question should concern people, stakes or a turning
point, rather than merely report that a product was released.

For 800–5,000 records, use a lightweight master index with IDs, years, kinds,
chapter IDs, titles and representative media. Store long copy in era/chapter
pages of approximately 50–100 stops. Parse the current page and one neighbor on
a worker, then publish an immutable snapshot to the frame thread. Keep timeline
filtering and year ordering in the index; do not load every image or model when
the catalogue opens. Preserve the offline bundled collection while an optional
remote index updates independently.

The current native loader's numerical record cap may be raised, but doing so is
not a substitute for paging. Music, FFmpeg, GLB staging and image decoding share
the bounded 512 MiB application heap. The remote cache has independent image and
model transfer limits, and the renderer keeps one selected model at a time.

The authoring outputs are intentionally excluded from the PS5 payload, which
ships only the curated `content/catalog.json` and `content/credits.json`.
