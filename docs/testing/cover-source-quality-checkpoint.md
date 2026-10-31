# Bounded cover source-quality audit

The production register's 543 metadata-HD cover records, representing 533 distinct URLs, were joined to their owners in the current catalog. Every selected URL still belonged to its recorded exhibit. The register predates unrelated catalog edits, so both file hashes are retained in the receipt rather than claiming identical catalog snapshots.

No new confirmed upscale, padded delivery, dimension contradiction or local byte mismatch was found in the evidence checked. This is **not a certificate that every cover contains native HD detail**. Local research files established the delivered dimensions and bytes for 363 owner/cover associations, representing 353 distinct files. Recorded intrinsic dimensions were available for 44 associations. The remaining origins lack equivalent source-resolution evidence in this bounded pass.

The four selected Adobe Scene7 covers are delivered at or below their recorded intrinsic dimensions: Uncharted4 at1920×1080 from1920×1080; Demon's Souls and Astro's Playroom at2560×1054 from3840×1580; Astro Bot at2400×897 from2560×956. The saved original Astro Bot imageprops response independently agrees. The known592×840 Jak packshot is not selected as a cover. Its rejected1920-wide delivery remains an excluded research artifact.

The only capsule-name signal was American Hero's official restoration poster, `build/research/publishing/batch05/american-hero-publisher-0.jpg`, SHA-256 `5137e7a4e5d95057f43c11d8953455be5ec37bf6eef394824b958019a29f0840`. Actual decoding and visual inspection show a complete1200×1800 poster without the blank padded canvas of the Jak case. Its filename alone is not evidence of a low-resolution thumbnail. The selected Doom and Celeste screenshots were also inspected locally: visibly coarse game textures and deliberate pixel art must not automatically be treated as a defective image upscale. Their original capture-resolution provenance remains a separate question.

No500-file request batch was made: this audit issued **zero HTTP requests**. It changed no catalog, selector, source image or quarantine rule. No unverified replacement is proposed and no new blocking candidate is confirmed. Continue to distinguish delivered dimensions, intrinsic source dimensions and internal image detail when admitting future artwork.

Full owner/URL/local path/hash rows, limits and source-dimension evidence are in `build/checkpoint-cover-quality-audit.json`, SHA-256 `2e63816a91c18657a4116ef7671757ef8cc8aa99b87b588132555e3785bc0322`.
