# Persistent collection storage

`sce_sys/param.json` uses `downloadDataSize` in **MiB**. It reserves the title's
`/download0` area; it is neither a byte count nor the size of the application folder.
Pixel Museum reserves **16384 MiB (16 GiB)**. Build, lint, native-profile and
package checks enforce this value.

The downloadable image collection contains **10,773,044,326 bytes** of original
images, previews and its registry. Installation also needs room for one temporary
USTAR pack of up to **900 MiB**, plus preferences, checkpoints and bounded caches.
The installer deletes each downloaded pack only after its extracted files and
checkpoint are durable. It checks available space on its worker where the
filesystem API is available and reports storage errors explicitly.

The earlier 1024 MiB setting was sufficient for small state and caches but not for
this collection. The tested closed-title container
`/user/download/PPSA70421/download0.dat` occupied 1,212,088,320 bytes with that
setting. Updating metadata alone does not resize an already allocated container;
resetting that title's existing storage is a separate, explicitly authorized step.

Downloaded collections remain inside `/download0/pixelmuseum/collection` in
versioned directories. A private staging tree is exposed to the image cache only
after verification and atomic activation. Complete preloaded editions continue
to read their bundled images from `/app0`; models and the rest of the application
are not moved into the download area. General fallback image caches remain
bounded independently.

`tools/prepare-collection-base.py` overrides the **staged base copy** to
`downloadDataSize: 16384`, even when its source is an older full package. It never
changes the source `dist/PPSA70421` or historical release archives.
