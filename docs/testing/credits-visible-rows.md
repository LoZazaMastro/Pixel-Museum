# Complete prose and responsive Credits

Narrative and nested feature cards already render their full source paragraphs. The unused 52-word generated lead has been removed. `bash tools/preview.sh story-reading` now exercises an actual long Screen paragraph: the right stick reaches its final rendered glyph line without pressing R3, changing the card, adding ellipses or mutating the source.

Credits now wrap once per prepared exhibit/language and keep their ordered, full lines. A baseline binary search paints only visible rows plus a font-height guard. Every source, image, model, film and soundtrack credit remains available; theme colors are applied at draw time. Preparing another exhibit or changing language invalidates the layout. Unlimited wrapping also avoids the former default 99-line limit for a single provenance block.

The actual Mario Kart World 348-track article retains 2,810 full credit lines in source order. Host CPU generation previously took 14.765/19.880/16.007 ms at top/middle/bottom, generating 138,657 instances each frame. The new warmed paths measured 0.022/0.026/0.024 ms and 502/644/567 instances. The first full wrapping still costs 9.900 ms once on this host; this is not a PS5 frame-rate measurement or a guarantee of a 120 Hz frame.

The same-renderer scene/navigation suite also passes, including complete source scrolling, card retention, fullscreen photo/film transitions, active media isolation and GL error checks. Receipts and source hashes are in `build/research/story-reading/verification.json`. No FTP transfer was performed.
