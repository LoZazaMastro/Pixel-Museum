# Persistent storage reservation

`sce_sys/param.json` uses `downloadDataSize` in MiB. It reserves the title's
`/download0` area; it is not the size of the application folder or a byte count.
Pixel Museum reserves **1024 MiB**. Build, lint and package checks enforce it.

The previous value, 16384, requested 16 GiB. On the tested console its
`/user/download/PPSA70421/download0.dat` occupied 18,763,546,624 bytes including
filesystem overhead. Changing the package metadata alone does not shrink an
already allocated console area; console maintenance is a separate operation.

Bundled images and model artwork caches are read from `/app0`. Preferences and
small media state use `/download0/pixelmuseum`. The general fallback cache has
two independently pruned 384 MiB directories and a maximum 160 MiB document;
the 1024 MiB reservation leaves headroom for a temporary write and small state.
This does not promise an unlimited offline download store.

Do not replace this quota with a package-size calculation. Metadata-only fixes
do not require compiling or replacing the executable. Historical snapshots and
published archives retain their original hashes; regenerate a current package
through its normal validation before distributing it.
