# Calendar revision review, 21 October 2026

All 53 alternatives in `calendar-template-revisions-soundtrack.json`, `calendar-template-revisions-curation.json` and `calendar-template-revisions-native.json` have been read in full, including their headings, summaries, paragraph citations and original-body hashes. The machine-readable decision for every entry is in `content/editorial/calendar-revisions-source-review-06.json`.

This pass approves 39 ordinary canonical candidates for editorial integration. Two require the supplementary source records specified in the receipt: the precise combat pause in Vagrant Story, and first-generation trade evolution in Pokémon. The other 37 have no remaining editorial blocker from this review. Seven alternatives are excluded because reviewed identity corrections already take precedence. The March 7 four-game comparison remains a distinct placement decision, with no single linked canonical. The six native-authored alternatives were checked structurally but were **not self-approved**; the parent reviewer is handling their independent source review.

No catalogue, locale, original daily edition, assembly hook or console payload was modified by this pass. Replacing a template is not a new destination.

## Sources checked beyond a successful URL

The original Final Fantasy VIII PlayStation manual is a 47-page raster scan, not the two-page modern controls sheet. Its Junction, Draw and Triple Triad pages were downloaded, rendered and read: PDF pages 25–28 and 37–38, corresponding to printed pages 24–27 and 36–37. This closes the earlier mechanics-evidence gap.

The original Nintendo Zelda manual was also rendered and read. Save and battery information appears on PDF/printed pages 14–15, while the raft and bombs appear on pages 22 and 24. Nintendo's creator interview supplies the separate 1986 Disk System context. These physical editions must remain distinct in the text.

For The Order: 1886, the complete Ready at Dawn game page and Neubelt/Pettineo SIGGRAPH paper were retrieved. The paper's period-clothing samples, fabric response and layered material examples were inspected, including PDF pages 6–8 and 16. They support discussion of surface response rather than an invented technical performance claim.

Full direct publisher pages for God of War, Pillars of Eternity, The Order and Kingdom Hearts are preserved under `build/research/template-review06`. Web-tool errors were not treated as substantive evidence. The original Xbox OverRun announcement was readable using the official cached query variant ending `?ver=3.7.1`; it confirms the alternating five-player COG/Locust teams.

Scribd's generated descriptions are excluded from the evidence. Where the host reproduces a manual, the review uses the original manual's text and copyright identity. The Pokémon Blue Trainer guide is a later English first-generation manual: it supports the shared trading mechanic, not the Japanese release date. The Vagrant Story combat-pause supplement is explicitly a firsthand critical observation, not a developer-authored claim.

All page ordinals above are one-based. Local PDF SHA-256 hashes and the actual downloaded byte sizes are recorded in the receipt.

## Authorized source corrections

The full curation revision file was preserved before editing at `build/research/template-review06/calendar-template-revisions-curation.before-source-review06.json`. Its pre-correction SHA-256 is `9f996964d7b3759f79e11ddbaf14965a96ab89077db3bfe6d3add93653bb8a01`. The corrected file is `615647588eb705c3488fef3d03c1dfaa322905cf6d294181b27a2bda9fe71d08`.

Bloodborne's launch article is by Masaaki Yamagiwa, carrying Hidetaka Miyazaki's message. Its survival guidance is by Sid Shuman with named PlayStation/SCEA contributors. Both now carry those actual credits rather than treating the articles as generically authored by FromSoftware. Their narrative text is unchanged.

Pillars of Eternity retains “September 2012.” The original Kickstarter record explicitly gives the funding period as 14 September to 16 October 2012. That primary citation was added to paragraph 0 and the source list. The campaign's Kickstarter-only total must remain separate from the combined Kickstarter/PayPal total in Obsidian's gold announcement. Its narrative text is unchanged.

The complete before/after metadata is retained in `build/research/template-review06/source-corrections.json` and embedded in the review receipt.

## Publication budgets and integration

The budget check includes the complete exhibit title, complete summary, every heading and every paragraph, using the maximum of whitespace counting and Unicode lexical counting. For each ordinary candidate the *entire* resulting text is charged conservatively to each publication, so the same-publication aggregation cannot exceed that bound merely because it has multiple URLs. All ordinary alternatives are below 200 words by this deliberately conservative method. The combined four-game entry has a 252-word aggregate and needs explicit per-publication/card allocation before any distinct-feature admission.

Integration must target only the exact canonical IDs in approved receipt rows. First validate the current subject, year and template preimage. Keep the original daily editions, their calendar semantics and all eight source-language editions exact. Archive obsolete canonical locale aliases instead of allowing their old template body to replace the researched English narrative when a reader selects another language. Until a new translation is reviewed, the honest fallback is the new English text.

Source metadata should be merged, not substituted in a way that erases provenance. Preserve regional/version caveats: Ultimate's manual is supplementary evidence for shared Marvel vs. Capcom 3 mechanics; later Switch style-switching is not original Devil May Cry 3 behavior; and current publisher pages do not make later additions launch features.

No automatic hook is part of this handoff. The parent decides when to integrate the approved candidates and independently reviews the six native-authored narratives.
