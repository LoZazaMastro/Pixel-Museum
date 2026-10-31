# Localisation gap audit 02

Snapshot catalog `cbdc1b4ded0d636af2d2e80850a959303be3271bcff9ecc43bef3fbc85882bc8`; not a current-master guarantee after concurrent integration.

The 1096 distinct destinations include 16 English Wikipedia references with reviewed direct translations into Italian, Spanish, French and German (64 pairs).

| Language | Original override | Runtime override | English fallback |
| --- | ---: | ---: | ---: |
| it | 304 | 320 | 776 |
| es | 304 | 320 | 776 |
| fr | 304 | 320 | 776 |
| de | 304 | 320 | 776 |
| pt | 304 | 304 | 792 |
| ru | 304 | 304 | 792 |
| uk | 304 | 304 | 792 |

The 80 nested features remain English. Parent translation is not feature translation. Runtime input and output hashes both match the current overlay audit; no identical-English translated body was found in a non-English override.

A realistic next step is four short illustrated references with complete existing headings:

- `wikipedia-1055604` ? Gun Fight: 3 paragraphs, 164 English words; precise revision/body hash recorded.
- `wikipedia-595917` ? Space Harrier: 3 paragraphs, 247 English words; precise revision/body hash recorded.
- `wikipedia-1159581` ? Ultima IV: Quest of the Avatar: 3 paragraphs, 156 English words; precise revision/body hash recorded.
- `wikipedia-15448272` ? World of Goo: 3 paragraphs, 170 English words; precise revision/body hash recorded.

These are candidates only: no translations written or reserved. Template revisions, identity02/03/05 and systems/authors06 parent lanes are excluded. Preserve all original Playhub source locales; use the separate reference-overlay workflow with subsequent independent review.
