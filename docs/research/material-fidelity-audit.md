# Material fidelity audit

Checked 20 October 2026 against the actual `src/museum/object_scene.cpp` path and 27 currently selected or newly reviewed source files. Raw material counts and sampler records are in `build/model-material-audit.json`. These are host source/render checks, not a PS5 performance result.

The nine reviewed model rows and their visual limitations are in `model-batch-24-renderer.json`. Successful GL rendering is not a fidelity approval. Geometry simplification already present in an authored low-poly source cannot be repaired with lighting.

## Initial findings before correction

| Previous path | Observable risk | Bounded correction |
| --- | --- | --- |
| Base/emissive maps use RGBA8, followed by `pow(2.2)` in the fragment | Dark logo edges and colours can shift; mip generation/filtering precedes colour decoding | Exact piecewise sRGB conversion immediately; then distinguish colour/data map usages and upload colour maps as SRGB8_ALPHA8 so filtering is linear. Do not gamma-decode normal/MR/AO data. |
| Full base colour diffuse is added even at metallic=1; specular is an arbitrary power lobe | Metals retain diffuse energy and highlights do not follow authored roughness | Generic GGX distribution, correlated Smith visibility and Schlick Fresnel, dielectric F0=.04, metallic F0=base colour; energy-conserving diffuse. Keep one fixed studio lighting setup for every object. |
| `occlusionTexture` is never parsed | Recesses and controller/vent contact detail lose authored ambient shading | Preserve its texture binding, UV selection and strength. Apply AO to indirect contribution only. Shared ORM needs no new image storage; a distinct AO map needs a fifth sampler and complete GL-state save/restore. |
| Authored TANGENT is ignored, cotangent frame is reconstructed from derivatives | Normal-map seams and mirrored/detail shading can diverge from the bake | Preserve tangent.xyz and handedness.w where provided. Transform/reorthogonalize tangent with the baked world transform; handle mirrored transforms. Keep derivative frame only as a documented fallback. Adds 16 bytes/vertex, not more texture storage. |
| Texture sampler parameters are forced repeat/trilinear | Authored nearest-filtered pixel imagery blurs; clamp textures may bleed across edges | Preserve the referenced sampler. Use GL sampler objects per texture binding if one image has multiple sampler uses; include them in material equality and state restoration. |
| Optional transmission, clearcoat and specular extensions are ignored | Transparent/glossy parts may appear materially different even though the file loads | Record used optional extensions in diagnostics. Add supported common extensions generically or surface their omission as a fidelity limitation; do not imply exact material support. |
| Output is gamma-encoded before MSAA/alpha composition into 8-bit targets | Transparency/edge blending occurs in encoded space; bright emission clips | Prefer linear composition and one final sRGB encode, evaluating RGBA16F target cost before changing the memory budget. Keep the interface's straight-alpha contract. |
| Missing source normals are averaged over shared vertices | An intentionally flat unnormalled mesh can become smooth | Generate per-face normals with correct vertex splits when normals are absent. No current audited file relies on vertex colours, but COLOR_0 is also currently ignored. |

## Actual source coverage

Occlusion maps occur in PSP, Game Boy Color, Dreamcast, Famicom, Game Boy, PS2, PS3, PS4, Steam Deck and the previously selected Switch file. Authored tangents occur in 23 of the 27 audited files. No audited primitive currently uses COLOR_0. Two sampler records have non-default-nearest sampler choices, so preserving sampler semantics is relevant to the current collection rather than hypothetical support.

The audit found four transmission, three clearcoat, two specular and five emissive-strength material declarations. Emissive strength is parsed, but the renderer's global required-extension whitelist currently admits only unlit; reconcile that whitelist with actual implemented support rather than silently dropping required features.

## Reference and validation

The [Khronos glTF 2.0 material specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials) defines colour texture decoding, linear data textures, metallic/roughness channels, tangent handedness and ambient-only occlusion. The [Khronos sample renderer](https://github.com/KhronosGroup/glTF-Sample-Renderer/blob/main/source/Renderer/shaders/pbr.frag) provides a primary implementation reference; any reused code must retain its licence.

For a bounded regression set, use the same unchanged source GLBs at two fixed poses: PSP for dark plastic/labels/normal maps, Game Boy for worn grey plastic and screen, PS2 for reflective dark material, and Intellivision for a textured heritage reconstruction. Include synthetic neutral swatches at metallic 0/1, roughness 0.1/0.5/1, and an unlit sRGB ramp. Compare identity/glyph/UV preservation separately from lighting response. An artist's original studio environment is generally not embedded in GLB, so physically based studio lighting improves material interpretation but is not proof of identical Sketchfab presentation.

## Implemented correction and limits

ObjectScene now uses sRGB texture storage for colour/emission maps and linear RGBA8 for data maps, preserving full source resolution. A source image serving both roles gets separate texture objects only when required; additional base-level duplicate storage is capped at64 MiB and rejected cleanly above that bound. Mipmapped overhead for the duplicate is consequently bounded to approximately85.4 MiB. Decoded CPU pixels remain shared and are released after upload.

Direct light uses generic GGX, height-correlated Smith visibility and Schlick Fresnel with metallic energy conservation. Studio lights are neutral and identical for every model. The indirect environment is still a bounded hemisphere approximation, not the author's original HDR environment or a prefiltered IBL implementation. Separate AO texture/UV/strength affect indirect light only. Authored tangent directions and handedness are retained; only a missing tangent uses the derivative fallback. Missing normals now produce face-normal vertex splits within the existing vertex-count budget.

Each material binding preserves its original sampler. Five touched texture and sampler bindings, the active texture unit and all previous GL state are restored. Alpha/MSAA composition uses sRGB attachments for linear blending, followed by a single exact sRGB conversion into the interface's straight-alpha image. Attachment size stays within the previous 8-bit target budget; HDR intensity beyond display range can still clip. Geometry stride increases from56 to72 bytes to retain authored tangents.

Unsupported optional material extensions are recorded in model diagnostics and exposed through `ObjectScene::material_notes()`. Transmission, clearcoat, specular texture maps and vertex-colour support are not claimed. Scalar specular support is described below. The source images and authored low-poly silhouettes are not modified by these renderer changes.

Validation:18 actual renderer pixel tests cover sRGB filtering, factor decoding, unlit behavior, nearest/repeat/clamp sampling, six metal/roughness combinations, AO strength and independent UV, colour/data dual-role storage, and mirrored tangent frames. Eleven malformed/unsupported GLBs reject cleanly. A128 MiB dual-role fixture rejects at the64 MiB duplicate-storage cap. Actual3840x2160 two-angle proofs of PSP, full-resolution Game Boy, PS1/PVM and PS2 pass with no GL errors and complete texture/sampler state restoration. Native compiler flags pass with-Werror; the SDK's actual archive defines all four sampler functions. Hardware allocation/performance still requires PS5 measurement.


## Scalar specular extension

The generic material path now supports `KHR_materials_specular.specularFactor` and linear-RGB `specularColorFactor`, following the [Khronos extension specification](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_materials_specular). The dielectric F0 is clamped before strength multiplication; grazing reflectance is scaled by the same strength. Diffuse energy uses the maximum dielectric Fresnel component to avoid complementary colour artefacts. Metallic reflection remains independent of these dielectric controls. Material merging includes both factors, and both direct light and the existing indirect approximation use the same values. No new texture allocation or sampler slot is introduced.

Optional `specularTexture` and `specularColorTexture` maps are explicitly named in model diagnostics and remain unsupported; a required extension containing either map rejects with an explicit error. Required scalar-only variants are accepted. Invalid scalar factors, negative/non-numeric colour components, malformed colour vectors and incompatible unlit/specular-glossiness combinations reject. Colour factors above25 saturate the dielectric F0, so values are bounded before float conversion without changing the specified reflectance.

Validation extends the neutral renderer suite from18 to37 cases: strength0/.657178/1, black/tinted/above-one/very-large colour factors, unchanged metallic response, scalar-only required extension, named optional-map limitations, required-map rejection and malformed values. All37 actual GL pixel/rejection checks pass; existing neutral outputs are unchanged. Native no-exception/no-RTTI compilation with-Werror passes. Hanimex's source factor.657178 is now represented; this is not automatic model selection or a claim that unrelated material extensions are supported.
