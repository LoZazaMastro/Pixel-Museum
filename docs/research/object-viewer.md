# Console objects and the native renderer

`src/museum/object_scene.hpp` and `.cpp` load licensed GLB assets through the same OpenGL context as the museum UI. The viewer uses the actual authored triangles, textures and scene transforms. It does not replace a console with a generic primitive or turn a photograph into a rotating billboard.

## Thread and drawing contract

- `init()` compiles the geometry and alpha-resolve programs on the GL thread.
- `request(local_asset_path, include_groups = {})` schedules bounded file parsing, material-image decoding, transforms and mesh preparation on a worker. A newer selection supersedes older work and clears the previous object, so another console cannot appear under the new exhibit label.
- `upload_pending()` uploads **one material atlas per call**, releases its CPU pixels immediately and finally uploads geometry. Keep calling it every frame outside the UI draw batch. It returns true only when the object is complete. `loading()` covers parsing and staged upload.
- `render(yaw_radians, width, height, tilt = .13f, source_z_up = false, zoom = 1)` returns a transparent, straight-alpha RGBA texture. Its origin is OpenGL's bottom left; flip V for a top-left UI image primitive. Keep the image quad's aspect ratio equal to the requested target.
- `release()` joins the worker and frees GL resources before context teardown. `ready()` and `error()` distinguish a finished object from an unavailable optional asset.

All instance methods belong to the main GL thread. `load()` is synchronous and intended for small tests, while `validate()` is CPU-only. Runtime file reads use bounded FILE I/O, avoiding unavailable console locale imports. Host builds with C++ exceptions catch worker allocation failures. The native build disables exceptions; image-decode and GL allocation failures return readable errors, while native allocator capacity must be established before heavy loading. Driver allocation errors clear the incomplete object.

An optional group list selects the source author's `node.extras.assembly` before decoding geometry, with inheritance through parent nodes. It was used for detailed CAD fallback assets during research. Filters must be checked visually: the PlayStation CAD asset puts its external disc lid in `Optical`, so selecting only `Body` leaves a hole. `source_z_up` normalizes tabletop CAD geometry before rotation. The final source selection prefers the user's licensed Sketchfab assets; research CAD alternatives are not silent substitutes.

## Materials and anti-aliasing

The static subset follows the [Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html): one embedded binary buffer, indexed triangle meshes, node TRS/affine matrices, unsigned indices, float positions/normals, float or normalized unsigned UVs, and embedded PNG/JPEG images. Four authored UV sets are retained independently for base color, normal, metallic/roughness and emissive maps. This matters for the selected PlayStation/PVM scene: its maps use UV0, UV1, UV2 and UV3. Emissive factors/strength, normal scale, double-sided flags, alpha masks and mirrored winding are respected. Missing normals are averaged indexed vertex normals. Transformed normals use inverse transpose.

Lighting is a restrained studio approximation with a warm key, cool fill, hemispheric ambient and broad neutral reflections. It is not a full environment-map/path-traced renderer. Normal maps use a derivative cotangent frame. There are no cast shadows or screen-space ambient occlusion. Occlusion, transmission and clearcoat maps are not evaluated. Required unsupported extensions produce an error; optional unsupported extensions retain their supported material appearance.

Opaque texels write depth. Blended primitives depth-write opaque texels, then draw translucent texels in primitive back-to-front order. This is not order-independent transparency. A final resolve converts composited RGB to straight alpha for the UI painter.

Object targets support up to **3840 x 2160 pixels** (maximum edge 4096). Targets of at most three million pixels request **4x MSAA**; full 4K requests **2x MSAA** to bound memory. Driver sample limits are respected. Nominal full-4K target storage is about 190 MiB: two RGBA8 textures plus multisampled color and depth. Actual driver allocation/alignment can differ. GL state, including four texture units, framebuffer bindings, viewport, pixel unpack settings, blend/depth/cull configuration and multisample state, is restored afterward.

## Bounded memory and full-resolution masters

Limits: 160 MiB raw GLB, 4 MiB JSON, 64 nesting/node levels, 16,384 source nodes, 32,768 traversed nodes, 8,192 source primitives, four million indexed vertices, sixteen million indices and 384 million decoded texture pixels (1536 MiB RGBA). Equal-material parts are merged after transforms, preserving source triangles and bounding final material groups to 128. CAD drafting points/lines are omitted; a file without triangle surfaces fails. External resources, Draco/meshopt compression, sparse accessors, skins and morphs are unsupported. Simple authored TRS animation tracks can accompany a static object, but are not evaluated: the original rest pose is rendered. Accessors/views are checked against the embedded binary chunk.

Raw bytes and JSON are released before upload. Exact duplicate embedded image bytes share decoded/GPU images. Original images are never silently resized or dropped. The official 4K masters therefore require much more memory than early previews:

The image-table count and aggregate decoded pixel budget are checked before image allocation. Individual images are limited to 16 million pixels. During decode, stb temporarily holds one image in addition to the retained images; that extra image can be up to 64 MiB. The worker is serial, so superseded selections cannot decode two models concurrently. The previous model's GL buffers and textures are deleted when a new request arrives, and each decoded image is freed immediately after its GPU upload. Targets remain allocated for reuse until the viewport changes or the viewer is released. Driver-deferred frees and native unified-memory residency still require measurement on the console.

| Official master | Decoded RGBA, after exact deduplication | GPU textures including mipmaps, approximate |
| --- | ---: | ---: |
| Lokeig Game Boy | 704 MiB | 939 MiB |
| Smoggybeard PlayStation 2 | 496 MiB | 661 MiB |
| dark_igorek PlayStation + Sony PVM | 1456 MiB | 1941 MiB |
| MacDrawz Wii | 1024 MiB | 1365 MiB |

These figures exclude targets, geometry, driver overhead and compressed source bytes during CPU preparation. The console platform's bounded large-allocation arena and separate GPU pool need hardware validation. A host render does not establish console residency, frame rate or display-mode negotiation.

## Sources, rights and verification

Source audits: `docs/research/model-candidates-renderer.json` and `content/model-candidates-curation.json`. The live creator licence takes precedence over an older dataset folder name. Lokeig's exact user-selected Game Boy is **CC BY-NC 4.0**; the selected Smoggybeard PlayStation 2 is **CC BY-NC-SA 4.0**. Preserve attribution, noncommercial and ShareAlike terms. The user subsequently requested all selected 3D model assets inside the app; their licences and credits must accompany the bundled files. Signed official download links expire and are research provenance, not durable public URLs.

Actual GL tests rendered the selected Game Boy, PlayStation/PVM and PlayStation 2 official masters at 3840x2160 with MSAA, original 4K maps, four UV sets where needed, zero GL errors, staged uploads and restored UI state. Captures live beside local validation files. `build/previews/game-boy-4k-model.png` is a separate 4K proof image, not the earlier 768-pixel preview. Tests also cover licensed Spectrum, Dreamcast, Commodore 64 and reviewed alternatives.

`tests/object-scene/run.sh` exercises the real asynchronous loader/render path. `malformed.py` checks truncated buffers, unsupported compression, external resources, accessor overruns, cycles, line-only scenes, sparse accessors and excessive nesting. Host Mesa tests do not replace the final PS5 memory/driver session.
