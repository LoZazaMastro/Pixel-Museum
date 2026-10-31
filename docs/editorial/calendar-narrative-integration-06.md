# Canonical narrative integration 06

The pure helper `content/expansion/integrate_calendar_narratives_06.py` applies the 39 independently reviewed alternatives plus the six independently approved by the parent reviewer. It does not write files, modify assembly hooks or transfer anything to PS5.

Its frozen declaration is `content/expansion/calendar-canonical-narratives-06.json`, SHA-256 `f0a477b0cacda3ed917d7ace328db6e5eb58f80e6c6aaf241473c48257d21dab`. The declaration binds both review receipts and all three alternative source files. `checked_document(project_root)` verifies those identities. `integrate(entries, locales, document)` validates all 45 original daily/canonical preimages and all eight sets of locale preimages before committing either parsed input.

The assembler should call it **after `integrate_collection_media` and before final readiness**. Four existing media admissions are bound to the old bodies: Horizon Forbidden West and Horizon Zero Dawn in collection batch 03, Mass Effect 3 in batch 04, and The Order: 1886 in batch 05. Admitting those first preserves their original review contract. This helper then archives the complete parent records and removes only their obsolete numeric `story_paragraph` anchors. There are no reference-heading batch collisions in this target set.

Attached `editorial_features` are separate works. They remain intact, including their own body-relative image anchors. Parent dates, years, related IDs, assets, URLs, dimensions, rights, credit, captions and unrelated metadata remain intact. Old parent briefs/cards and stale body-restoration/readiness metadata are archived in the full preimage and cleared; readiness is recomputed by the assembler afterward.

The returned receipt contains `original_records`, `removed_canonical_locale_overlays` and the exact action/credit/binding changes. Persist it as `content/calendar-canonical-narratives-audit-06.json`. The focused tests recognize this path to reconstruct the real pre-migration baseline after a legitimate assembly.

The only daily changes are 45 explicit source-attribution corrections. Their old statements incorrectly said their template had already been replaced even though the displayed original daily prose had been restored. The replacement credit states that the original daily edition is retained and the researched narrative belongs to its linked canonical. Every daily summary, body, heading and locale record stays exact. The 360 obsolete canonical overlays are removed and archived so an untranslated canonical falls back honestly to its new English narrative.

The helper includes the two supplementary Vagrant Story/Pokémon citations from the independent review and the parent's supplemental Hyper Light Drifter composer sources. It merges source metadata, including the corrected Bloodborne authors and primary Kickstarter campaign record, without erasing earlier provenance.

An immediate second pass can pass the returned receipt as `previous_receipt`. It reconstructs the complete original affected records, replays the reviewed transformation, and compares both the complete result and receipt. Altered output or altered receipt is rejected without mutation. This is immediate-operation idempotence, not a prohibition against later legitimate editorial or media enrichment.

## Verification

Six meaningful real-data tests pass in `tests/editorial/test_narratives_06.py`. They cover all 45 actual records and eight language documents, complete archival preservation, corrected credits, source supplements, all media fields except removed numeric anchors, preservation of nested features, last-case failure atomicity, stale translations, changed subjects, duplicate IDs, changed proposals and full immediate replay.

The current dry run reports 45 replacements, 45 source-credit corrections, 110 obsolete parent media anchors detached and 360 canonical locale aliases archived. It creates no destinations and deletes no media. The complete receipt is approximately 3.07 MB before pretty printing.

The Zelda image-identity problem is separate: curation is preparing the quarantine/replacement. This helper neither certifies those images nor repairs them. Its preimage checks intentionally bind narrative fields rather than media lists, so an independently reviewed media quarantine can run before it without weakening narrative identity checks.

No master, actual locale document, assembler hook, payload or console file was written during these tests.
