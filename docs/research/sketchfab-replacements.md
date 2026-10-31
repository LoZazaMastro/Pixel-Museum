# Sketchfab hardware source review

Reviewed 20 October 2026. This is a source and asset audit, not a claim that every candidate has already passed the native renderer. Official Sketchfab model metadata and publisher thumbnails were inspected; actual GLB headers, primitive counts, embedded images and required extensions were checked for downloaded assets.

The machine-readable manifest is `content/model-candidates-sketchfab-curation.json`. It contains exact creator/licence links, official model pages, official Objaverse mirror paths, local research files and SHA-256 values. These files do not change the museum catalogue automatically.

## Exact user selection

[PlayStation 2 by Smoggybeard](https://sketchfab.com/3d-models/playstation-2-8c992e9f5c86496ca7bd7dfe109d3cc2) is downloaded as `build/research/model-validation/sketchfab/ps2-user-smoggybeard.glb`. It is the exact requested model, not the alternative PS2 scene initially shortlisted.

- Official dataset file: <https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-016/8c992e9f5c86496ca7bd7dfe109d3cc2.glb>
- 11,498,596 bytes; seven meshes and 22 embedded images; no required compression extensions.
- Creator: Smoggybeard.
- Licence: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Attribution, noncommercial use and ShareAlike conditions must remain attached to this asset and any adaptations. It must not be labelled simply CC BY.

## Downloaded candidates and honest alternatives

| Hardware | Creator and model | Actual file | Assessment |
|---|---|---|---|
| PlayStation | [Ceki](https://sketchfab.com/3d-models/96bed8283f2940d7bb4b1866ab0637a2) | `ps1-ceki.glb`, 8.68 MB, 283,464 triangles, two images | Detailed original console, real logos and front sockets. CC BY 4.0. Needs native orientation/material check. |
| PlayStation 2 | [Ilgis (Dolgov) Fatykhov](https://sketchfab.com/3d-models/b53f858aa1584229a7f906239fc158a2) | `ps2-dolgov.glb`, 12.90 MB, 53,833 triangles, nine images | Attractive console/accessory scene, but secondary to the user's exact Smoggybeard selection. CC BY 4.0. |
| Atari 2600 | [Zygomir.Fabricati.Diem](https://sketchfab.com/3d-models/9820673636cb4f7c903b3d5d1fd8d8ec) | `atari2600-zygomir.glb`, 2.99 MB, 19,304 triangles, six images | Textured later four-switch variant. Do not misidentify it as the 1977 six-switch model. CC BY 4.0. |
| Famicom | [BirdChen](https://sketchfab.com/3d-models/c18c3608d42e4af59f92d5a14eae6be0) | `famicom-birdchen.glb`, 1.69 MB, 19,990 triangles, one image | Actual photogrammetry test with visibly uneven scan geometry. A fallback, not the preferred quality level. CC BY 4.0. |
| Wii | [libblekibble](https://sketchfab.com/3d-models/258447f719e84a2ca8b245d3d823c9ec) | `wii-libblekibble.glb`, 2.55 MB, 50,792 triangles, no images | Detailed geometric labels and multiple remotes; untextured. Prefer the textured MacDrawz version below. CC BY 4.0. |

Files above are in `build/research/model-validation/sketchfab/`. No proprietary viewer geometry was extracted. Each actual download came from Allen Institute's public Objaverse dataset using its published UID-to-path mapping.

## Preferred textured models needing official account download

These models are currently downloadable according to Sketchfab's public API, with CC BY 4.0 licensing. Their IDs do not appear in the downloaded Objaverse mapping or S3D3C model index. Use Sketchfab's authenticated **Download 3D Model** flow; a viewer page alone is not a downloadable asset URL.

1. [Atari 2600 by dark_igorek](https://sketchfab.com/3d-models/atari-2600-2024d933f6214117a399ad4287ede64d): accurate six-switch Heavy Sixer, 64,380 triangles, 20 reported textures, textured wood grain, controls and peripherals. Stronger visual fit than the mirrored later-variant alternative.
2. [Mercenary's Famicom by Quentin Dejaeghere](https://sketchfab.com/3d-models/mercenarys-famicom-b33939368ad04640919570a9d3bdbeda): 10,948 triangles, five textures, original controller and readable labels. Authored surface detail is substantially cleaner than the photogrammetry test.
3. [Nintendo Wii by MacDrawz](https://sketchfab.com/3d-models/nintendo-wii-7214f7b100874ef3aad664feb0d5c4e4): 76,628 triangles, 25 reported textures, Remote and Nunchuk. Publisher describes 4K textures. A better match for detailed textured presentation than the untextured mirrored alternatives.

Reported Sketchfab texture counts include all authored maps and need not equal the count of images packed into its downloadable GLB conversion.

## Rejections and missing Odyssey

The imgvertex PlayStation candidate was rejected after thumbnail inspection because it visibly substitutes fictional **SONYA / Polistation** labels. Low polygon Atari candidates by Rafenn and Juan Foo are not an upgrade in fidelity; their existence is not grounds to claim the requested detailed model is finished.

S3D3C's primary project is <https://osf.io/w2qu9/>. Its actual public `s3d3c-model-paths.txt` (August 2025, 7,467,140 bytes, 132,297 paths) was downloaded from <https://osf.io/download/egc96/>. Neither proposed Odyssey UID `1442250a6bba4c70af4fc6b9807bcfdf` nor `52a26d742099437dbb27625a86a9b385` appears in it. The index is retained in `build/research/model-validation/s3d3c-model-paths.txt`.

The [S3D3C paper](https://arxiv.org/html/2407.17205v1) describes metadata collected principally by January 2024. A model published in December 2024 cannot be assumed to be in that initial collection. Absence was checked directly against the newer public path index as well; no qualified Odyssey download was found through this route.
