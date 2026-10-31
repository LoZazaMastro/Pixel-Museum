# Media collection: batch 04

This additive handoff contains **32 verified remote HD images for 24 previously unillustrated canonical articles**. No master catalogue, assembler, package, source translation, app or FTP payload is changed. The image captions name the actual edition positively; research limitations remain in provenance and explicit holds rather than repeated disclaimer text in the museum.

Payload: [media-collection-batch-04.json](../../content/expansion/media-collection-batch-04.json). SHA-256: `a1ef8c4926ec31a5af8669281e77a0037835b5dc0c3a29d5aedcbfc21350d8c2`.

## Coverage

| Canonical subject | Actual image context |
|---|---|
| Bully | Scholarship Edition PC artwork; linked to the paragraph about the 2008 edition |
| Peggle | Official Peggle Deluxe PC artwork |
| PixelJunk Monsters | Ultimate artwork and gameplay; linked to its 2013 expanded edition |
| Shantae: Risky's Revenge | Director's Cut artwork; linked to the 2014 PC version |
| Retro City Rampage | DX artwork; linked to the later expanded edition |
| Command & Conquer | Original game and Covert Operations PC reissue artwork |
| Tomb Raider | Original 1996 PC application artwork and a gallery image |
| Mass Effect 3 | Original N7 Digital Deluxe Edition artwork and a gallery image |
| Star Wars Battlefront | The original 2015 DICE/EA game |
| Prototype 2 | A genuine later-in-gallery 1,917 x 1,080 image |
| Dragon Quest XI | Original PC Digital Edition of Light, separate from XI S |
| Divinity: Original Sin II | Definitive Edition artwork and a cooperative-play image |
| Super Mario Odyssey | Original Nintendo Switch product artwork |
| Pokemon Legends: Arceus | Nintendo publisher artwork for the exact game |
| Xenoblade Chronicles 3 | Exact Nintendo product artwork |
| The Legend of Zelda: Tears of the Kingdom | Exact Nintendo product artwork |
| Super Smash Bros. Ultimate | Publisher artwork with its full character-rights notice retained |
| Bayonetta 3 | Publisher artwork; Nintendo and Sega copyright notice retained |
| Advance Wars 1+2: Re-Boot Camp | The actual 2023 remake package, not the original GBA display |
| Another Code: Recollection | The actual 2024 collection, not the original DS or Wii editions |
| Donkey Kong Bananza | Two useful game scenes: DK with Pauline, and destructive terrain interaction |
| Super Mario 3D World + Bowser's Fury | The actual 2021 Nintendo Switch package |
| Pokemon Scarlet and Violet | Specifically Scarlet edition artwork, identified in its caption |
| Astro Bot | PS5 key artwork and two actual publisher gallery scenes |

The Bananza demo/award banner is deliberately omitted in favour of its two useful scenes. The original Nintendo gallery resources are fetched without delivery resizing or DPR transforms. Only genuinely large originals pass; the many small gallery screenshots are not enlarged. Nintendo source copyright notices are retained, including Pokemon, Nintendo, Creatures and Game Freak; Nintendo/Sega for Bayonetta 3; Nintendo/Monolith Soft for Xenoblade; and the extended character-owner notice for Smash.

Astro Bot has an additional source-dimension check. Adobe's documented `req=imageprops` returns intrinsic source dimensions, unlike `req=props`, which reports the delivered rendition. The hero source is 2,560 x 956; the two scene sources are 1,920 x 1,080. The delivered JPEGs are at or below those intrinsic dimensions. The scene showing Twin-Frog Gloves is identified by the publisher's own feature description, not an inferred power-up name. All three images depict the 2024 PS5 game, not Astro's Playroom.

## Publication identity holds

The first-paragraph review catches two important source metadata defects. Their images are valid, but must not be attached under the wrong article identity:

- `workbook-05-21-senua-s-saga-hellblade-ii`: its preserved source introduction and English editorial title concern **Never Alone**, Iñupiat collaboration and the World Day for Cultural Diversity. The inherited subject/topic fields say Hellblade II. The original English title is “Never Alone Uses the Video Game as a Meeting Place Between Story and Community.”
- `workbook-08-30-astral-chain`: its introduction describes **Street Fighter's 30 August 1987 arcade release**, Ryu/Ken, special-move inputs and pressure-sensitive controls. The inherited subject/topic fields say Astral Chain. The source English title is “Before the Perfect Combo There Was a Noisy Experiment.”

Both inconsistencies are present in the read-only original Playhub JSON; they are not failed byte copies. Preserve all existing language versions and correct publication identities and date semantics through a separate reviewed metadata override. This media batch does not rewrite the source or invent replacement translations.

Mass Effect 3's game identity is correct, but its preserved source still contains generic template prose. Its real images therefore do not establish editorial readiness. The same distinction applies to all acquisition counts: **zero editorial sign-offs** are claimed.

## Other holds and verification

Twenty subjects are held in the payload: two identity mismatches, one unavailable Nintendo collection page, and seventeen bounded Steam probes without a qualifying native HD result. The older Sega and Ubisoft applications often supply only small originals even when the delivery URL requests a larger size. Those failures are recorded without upscaling or substituting a modern sequel. Another attempt on a held subject needs a meaningfully different source or actual new evidence.

Every admitted image has a source page, creator or explicit unidentified-illustrator statement, rights notice, actual decoded dimensions, byte hash and verification time. All 32 byte hashes and decoded dimensions were rechecked locally; all targets are unique and were unillustrated in the recorded catalogue snapshot. Paragraph indices are checked against the real bodies. Supplementary images without a concrete paragraph association remain gallery material.

Research evidence lives in `build/research/publishing/batch04/`: official application metadata, Nintendo pages and JSON-LD gallery metadata, image originals, Adobe intrinsic-property responses and visual contact sheets. Images remain remotely hosted. No Commons request or artificial enlargement is used.

## Next 40 source targets

The next bounded acquisition pass starts with these exact existing IDs, after repeating the title/body identity check. These are a work queue, not claims that media has already been found:

1. `wikipedia-64255520` — Astro's Playroom; official PlayStation game gallery.
2. `workbook-12-07-the-last-guardian` — The Last Guardian; official PlayStation page and launch material.
3. `workbook-04-26-alienation` — Alienation; Housemarque/PlayStation publisher material.
4. `workbook-02-20-the-order-1886` — The Order: 1886; official PlayStation material.
5. `workbook-05-10-uncharted-4-a-thief-s-end` — Uncharted 4; Naughty Dog/PlayStation material with edition labels.
6. `workbook-06-14-the-last-of-us` — The Last of Us; original-versus-remaster identity review first.
7. `wikipedia-52464953` — The Last of Us Part II; later remaster only where the actual article discusses it.
8. `wikipedia-69475062` — Alan Wake 2; Remedy/Epic publisher media.
9. `wikipedia-83404081` — Elden Ring Shadow of the Erdtree; exact expansion application/press gallery.
10. `wikipedia-64249122` — Demon's Souls (2020); the exact PS5 remake, not the PS3 game.
11. `wikipedia-76786178` — Batman: Arkham Shadow; Meta/Camouflaj official media.
12. `wikipedia-61416573` — Genshin Impact; official HoYoverse game media.
13. `wikipedia-57813623` — Fortnite; official Epic media with current mode/update context.
14. `wikipedia-72151918` — Butterfly Soup 2; Brianna Lei's own publication assets.
15. `wikipedia-67445905` — 3 out of 10; Terrible Posture/Epic publisher assets.
16. `wikipedia-60330848` — American Hero; Ziggurat's specific restoration assets.
17. `wikipedia-53596468` — Umamusume: Pretty Derby; original/global edition distinctions.
18. `wikipedia-618559` — Grandia II; remaster media only beside its actual remaster paragraph.
19. `wikipedia-1741368` — Resident Evil Zero; Capcom media labelled by edition.
20. `wikipedia-613343` — Metal Gear Solid 3; Master Collection versus Delta kept distinct.
21. `wikipedia-462914` — The Sims 2; official Legacy Collection context.
22. `wikipedia-1682727` — Oddworld: Stranger's Wrath; Oddworld's edition-specific material.
23. `wikipedia-16401301` — Persona 4; Golden source and paragraph identity review.
24. `wikipedia-52759` — Final Fantasy X; edition-specific Square Enix media.
25. `wikipedia-595618` — Metal Gear Solid 2; exact Master Collection evidence.
26. `workbook-05-19-full-throttle` — Full Throttle; Double Fine's preservation material.
27. `workbook-10-30-grim-fandango` — Grim Fandango; Double Fine's original/remastered comparison material.
28. `wikipedia-1904536` — Cave Story; freeware versus Cave Story+ distinction.
29. `wikipedia-101230` — Rez; original stages versus Infinite's Area X distinguished.
30. `wikipedia-1983945` — Phoenix Wright: Ace Attorney; original/HD compilation identity review.
31. `workbook-09-25-halo-3` — Halo 3; exact Halo Waypoint/Xbox retrospective media.
32. `workbook-11-06-halo-4` — Halo 4; exact official retrospective media.
33. `workbook-11-07-gears-of-war` — Gears of War; original versus later remake media distinguished.
34. `wikipedia-15167275` — Burnout Paradise; labelled original/remaster context.
35. `workbook-12-29-shenmue` — Shenmue; first game versus the combined reissue distinguished.
36. `street-fighter-ii` — Street Fighter II; Capcom's exact original-game material.
37. `wikipedia-18717529` — StarCraft II: Wings of Liberty; Blizzard material.
38. `workbook-03-25-diablo-iii-reaper-of-souls` — Reaper of Souls; exact expansion media.
39. `wikipedia-5077457` — Wii Sports; Nintendo or properly identified museum photography.
40. `wikipedia-12206603` — Wii Fit; Nintendo or properly identified museum photography.

The queue does not authorize a generic image to stand for an unverified edition. Unavailable sources stay held while other subjects proceed.
