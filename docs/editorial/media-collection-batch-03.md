# Media collection: batch 03

This additive batch prepares **44 genuine HD image records for 28 distinct subjects**: 26 existing canonical articles without images and two reviewed feature subjects. It changes no master catalogue, assembler, package, installed app or FTP payload. The frozen Umurangi follow-up file remains untouched.

The coverage check uses catalogue SHA-256 `257d0b0f95f2a3c8c319b09387b5645eb72644ea7fd98675a100e8cf2b53e0cf` (1,403 authoring records). Every one of the 26 canonical targets has no images in that snapshot. The two feature IDs refer to their separate reviewed authoring blocks; they are not invented catalogue identities. This is an acquisition result, not a claim that 28 articles now have editorial sign-off or that most of their cards are illustrated.

The additive payload is [media-collection-batch-03.json](../../content/expansion/media-collection-batch-03.json), SHA-256 `cb2bff8ede0f4b7ce71a3c98bfa40aab8be96c377673b5935adbeab359a83389`.

## Priority features

- **Music that moves with Mario:** Vincent Diamante's author-hosted Flickr page exposes the actual 2,304 x 3,072 original, its CC BY-SA 2.0 licence and the photographer's identity. A fresh download, full decode and individual visual inspection succeeded. The caption identifies Kondo on the right with Diamante at E3 on 11 May 2006. This later photograph is not presented as a 1985 recording session. It accompanies paragraph 0 as a clearly dated portrait context. Attribution and applicable share-alike requirements remain attached. No Commons request was made.
- **The artist between a drawing and a display:** an actual 1,920 x 1,080 battle image from Square Enix's original 2021 PC Pixel Remaster application 1173770 accompanies paragraph 3. The publisher's own application description explicitly credits Kazuko Shibuya with the updated character pixel designs. The caption identifies a later redraw, not the 1987 Famicom display, a concept illustration, or the preserved paper printout. The intentional pixel graphics are not artificially sharpened. This is a contextual image of the work, not a portrait of the artist.
- **The ruler of Lagash has to decide:** held. The Strong's finding aid documents surviving printouts, slides and access conditions. It does not establish unrestricted reproduction permission or supply a qualified remote HD image. A third-party report funded by a federal grant is not automatically treated as a public-domain federal work. No generic terminal photograph or invented portrait fills the gap.

## New canonical coverage

| Article | Edition represented by the media |
|---|---|
| Fallout | Original Fallout PC application, not a 3D sequel |
| The Elder Scrolls III: Morrowind | Game of the Year PC edition, including the original game |
| Jade Empire | 2007 Special Edition PC port of the 2005 game |
| Call of Duty 4: Modern Warfare | Original 2007 application, not Remastered or the 2019 reboot |
| Mass Effect | Original 2008 PC version, not Legendary Edition |
| Grand Theft Auto IV | Complete Edition application; identified as such |
| Brutal Legend | 2013 PC port of the 2009 console game |
| Bayonetta | 2017 PC port of the original game |
| Mass Effect 2 | Publisher-labelled 2010 Edition |
| Dandara | Expanded Trials of Fear Edition; later edition stated explicitly |
| Back 4 Blood | Original PC application |
| Horizon Zero Dawn | Complete Edition PC port, not Remastered |
| Horizon Forbidden West | Complete Edition PC artwork; ambiguous expansion screenshot excluded |
| Call of Duty: Advanced Warfare | Gold Edition of the original game |
| Divinity: Original Sin | Publisher-labelled Classic release, not Enhanced Edition |
| N++ | Same game, expanded retail spelling NPLUSPLUS |
| Kentucky Route Zero | PC Edition, not the console TV Edition |
| Sekiro: Shadows Die Twice | Game of the Year Edition, with bonus content distinguished |
| Grand Theft Auto V | Legacy PC application, distinct from Enhanced |
| FIFA 23 | In-game World Cup trophy image, not a photograph or retail box cover |
| Bandle Tale | Full retail title: A League of Legends Story |
| Alien: Rogue Incursion | Original VR application, not the non-VR Evolved Edition |
| Anno 117 | Full retail title: Pax Romana |
| Shovel Knight | Shovel of Hope, the original campaign; not Dig, Pocket Dungeon or DX |
| Tomb Raider II | Explicitly identified 1997 original PC application |
| Tomb Raider III | Explicitly identified 1998 original PC application |

For GTA V, one additional gallery image visibly concerns GTA Online's later Money Fronts material. Its caption names that later context, and it maps only to paragraph 1, which actually discusses GTA Online. It is not presented as a 2013 campaign image. Dandara's surface-to-surface movement, Kentucky Route Zero's delivery setting and Sekiro's traversal images have similarly bounded paragraph associations. Other supplementary screenshots remain gallery records unless a concrete paragraph association is established. Library artwork accompanies the introduction with its edition stated in the caption.

## Verification and exclusions

Official Steam application title, developer, publisher, description and visible image were reviewed together. Every admitted URL was downloaded from the actual publisher/author host and fully decoded. The payload retains exact dimensions, SHA-256, verification time, source page/API, publisher release metadata and edition notes. Every image has a native long edge of at least 1,600 px. No generated image, resizing, sharpening or enlargement was used. Contact sheets were research aids only; they are not shipped illustrations.

The bounded search also leaves five explicit holds:

1. **Commander Keen: Invasion of the Vorticons:** application 9180 bundles Vorticons and Goodbye Galaxy. Its current HD library picture is not securely identified as a Vorticons illustration. A collection-wide image does not silently become the cover for a specific episode story.
2. **Unreal Tournament:** metadata correctly identifies application 13240, but the sole HD library illustration's subject is not securely identified as the 1999 game. Application identity alone is insufficient; the picture is not admitted.
3. **Prince of Persia (2008):** no native HD success in the bounded original gallery probe.
4. **Prototype 2:** no native HD success in the bounded original gallery probe.
5. **Mabel Addis:** qualified documentary imagery and its reproduction basis remain unresolved, as described above.

Two additional image-level exclusions do not block their articles: Horizon Forbidden West's first Complete Edition screenshot may represent expansion content, so only the properly labelled edition artwork is admitted; FIFA 23's current library picture is omitted in favour of a clearly contextual official in-game gallery image.

## Rights and integration

The Kondo photograph retains its real CC BY-SA 2.0 terms. The game images retain publisher copyright and exact source credits. They are official publisher media prepared for historical editorial illustration, not assets relabelled as Creative Commons. Public availability is not described as blanket redistribution clearance; the payload retains explicit `rights_basis` and `rights_review` fields. Individual illustration artists are not invented when the publisher does not identify them.

The feature rows carry both `feature_id` and `entry_id`. They must be attached to the reviewed feature blocks by the feature integration hook; a parent article cover must not be substituted automatically. The other 26 rows can use the normal additive image hook. All five `holds` stay outside publication. There are **zero editorial sign-offs** in this acquisition payload.

Research evidence and decoded originals are local to `build/research/publishing/batch03/`, including `probes.json`, original application metadata, three contact sheets, the Kondo author page and original, and the Pixel Remaster gallery proofs. Published image records continue to reference remote originals.
