# Pixel Museum — First Rooms

The first console trial uses the production interface with sixteen selected exhibits. The complete authoring catalogue remains in `content/catalog.json`; it is not replaced by the smaller installed collection.

The trial starts with Game Boy. Browse left and right to see the next exhibit immediately. Cross unfolds the story below the same timeline; Circle brings the timeline back down. Up opens object inspection where a model is available, or opens the exhibit photograph otherwise. Down unfolds the story and moves towards its film, when it has one.

While reading, use up/down or the right stick to scroll. Cross opens the photograph or film closest to the centre of the reading area. Triangle expands the source notes. The timeline remains available above the story: left/right changes exhibit and L1/R1 moves between decades.

In a photograph, L2/R2 zoom, the left stick pans and left/right browses pictures when fitted. Circle first leaves zoom, then returns the photograph to its place in the story. In object inspection, the right stick rotates the object, L2/R2 adjusts distance and Cross restores its reviewed pose.

Films open inside their story card. Square expands the frame to fullscreen; Circle returns to the frame, then to the story. Cross pauses or resumes playback. Native playback depends on the console and current YouTube availability; a successful video metadata check is not a playback test.

A short first visit:

1. **Game Boy** — rotate and inspect the object, then read its four illustrated cards.
2. **Carol Shaw and River Raid** — read the personal story, open a portrait and return to the same reading position.
3. **The Making of Karateka** — open the archive film from its card, expand it and return.
4. **Nintendo 3DS** and **Switch** — compare the objects, music and decade colour transitions.
5. **Tennis for Two** or **Jerry Lawson's team** — browse the earlier archive material and films.

The first trial is a development build, version 0.1.0, with title ID PPSA70421. Its ZIP is in `dist/vertical-slice-ready/PPSA70421.zip`. The four models are bundled; the twenty-seven photographs and films remain online with their existing sources and credits.

Local validation covered real production OpenGL draws at 3840 × 2160, reversible story/photo/video presentation, media input isolation, 3D controls, catalogue integrity, native compilation/signing/import checks, package hashes and ZIP permissions. Console playback, audio, output mode and frame pacing are separate observations recorded after launch.


## Second console trial: experiences and listening cards

The audited second trial is staged at `dist/vertical-slice-ready-03`. It contains 35 exhibits, all twenty procedural experiences plus the pixel workshop, their linked historical stories, three official soundtrack playlists, the current calendar discovery, and the four previously selected bundled console models. It deliberately remains a bounded console trial; the full authoring collection stays in `content/catalog.json`.

Touchpad opens the left Guide. Square switches Years / Experiences; Up and Down choose a study, Cross opens its explanation, and Cross again begins it. Circle returns to the same library selection. Triangle in the library opens the related historical exhibit. Stories also include their own experience cards. Every launch repeats the explanation.

Supported introductions offer Triangle to opt into motion controls; the default is off and ordinary controls remain available. The pixel workshop supports touchpad pointing and click-to-shade. Controller sensor decoding and interaction routing have passed local tests, while real controller orientation, haptics and feel require physical PS5 testing. The microphone is not used.

The signed executable passed native compile, link, import conversion and SELF integrity inspection. All 184 packaged files matched ZIP bytes and 0777 modes. Package SHA-256: `f42f1f8b0e6d86b2e9d542ce0c399ecd238cb2fc9d99fa5a07f602fdb96cf828`. Host renders are actual 3840?2160 captures with zero GL errors. Host timing is not presented as PS5 performance, and YouTube identity/provenance checks are not successful native stream-playback tests.
