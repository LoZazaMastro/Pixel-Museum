# Integrating the Playhub review queue

Audit: 20 October 2026. This is a merge guide, not approval of every historical
claim. `catalog.json` was not changed by this audit.

## Verified by the actual C++ parser

`tools/catalog-audit.sh content/expansion/playhub-museum-candidates.json` compiles
and executes the real `museum::Catalog` parser. It retained all 318 entries,
1,010 HTTPS source links and 318 day-precision date objects. The input is
1,624,816 bytes; its paragraph bodies total 801,556 UTF-8 bytes. IDs are unique.
All source titles, publisher fields and URLs were compared, as were year,
month, day, precision and region.

The runtime accepts the following candidate fields: `id`, `kind`,
`title`, `subtitle`, `summary`, `era_id`, `layout`, `year`, `date`, `featured`,
`body`, `tags`, `related_ids`, `images`, `videos`, `models`, `sources`,
`event_semantics`, `editorial_credit` and `factual_note`. Each Source additionally
retains optional string `license` and `attribution` fields.
The seven era IDs match the prototype. `organization` and `technology` remain
valid kinds: the parser stores the string without a restrictive enum.

## Preserve these fields during the merge

Append complete JSON objects, rather than reconstructing them from the reduced
C++ Entry structure. The parser ignores these additional provenance fields, but
they remain valuable provenance in the shipped catalogue:

- `source_corpus` and `source_record_id` identify the original local editorial.
- `source_verification` distinguishes inherited source links from live checks.
- `original_editorial_kind` preserves regional-release and hardware labels.
- `editorial_status` describes remaining editorial review.

If the public source panel needs an explicit editorial credit, add a dedicated
field such as `editorial_credit: "Adapted from the Playhub historical collection"`
and display it. Entry already retains that field. Do not substitute this for the actual external source
list. The source corpus provides URLs, not individual article authors; those
authors must not be invented from hostnames. The existing `sources[].publisher`
values are site hostnames, not verified personal bylines.

`event_semantics` is retained in Entry and should be displayed beside the date or
in collection notes before these records are published. There are **293 release,
4 announcement, 10 birth and 11 foundation events**. Treating all 318 as game
release dates would change their meaning. The original kind also distinguishes
regional releases. Every `region` is empty because the source has no structured
region; this means unknown, not worldwide. Prose may explain more specific
regional context and must remain available.

## Merge sequence

1. Retain the main catalogue's metadata and eras. Combine its entries with the
   candidate objects while preserving all original keys.
2. Deduplicate by stable ID first, then review aliases and regional events by
   normalized title. The adapter only removed exact normalized prototype title
   matches; it does not prove that renamed hardware or aliases are distinct.
3. Preserve each date's claimed event. Never replace an announcement with a
   product release or infer a worldwide release from an empty region. Origins
   entries Bertie and OXO deliberately have year-only precision and zero day/month.
4. Keep actual source links. Review calendar-dependent prose and inherited facts
   before assigning published status. Select rights-cleared media separately;
   no image is automatically licensed by its presence in a source article.
5. Keep the complete provenance objects in the bundled JSON even if the frame
   renderer does not display every field. List any new media rights in the
   exhibit and `credits.json`.
6. Run the real-parser audit against the assembled file, then inspect the UI's
   longest titles, source panels, year-only dates and representative announcements.

## Runtime limits to address as the collection grows

The parser accepts at most **5,000 valid records** and rejects a larger update
with an explicit error instead of silently truncating it. Both `load()` and
`parse()` enforce a **16 MiB byte bound**. The real-parser audit exercises 5,000
accepted records, a 5,001-record rejection and a byte-limit rejection, while
preserving the previous valid catalogue after failure. Larger future collections
should use the paged era index described in `docs/research/catalog-scale.md`.
Sorting currently uses year alone; within a year insertion order
is retained. A chronological day sorter must compare precision safely, keeping
unknown month/day distinct from January 1.

The parser retains `precision`, but the present overview header displays only
`year / kind`; dates and their semantics are not otherwise visible there.
Sources & object credits displays each external source title, publisher/domain
and URL. The Source panel's rendering of editorial provenance and the new optional
source licence/attribution strings is the screen owner's responsibility.

ACMI seeds are a separate research queue and must not be fed directly into this
merge: all have `chronology_safe: false`, because collection production dates
are not established public release dates. `official-archives.json` is a source
discovery index, not catalogue exhibit rows.
