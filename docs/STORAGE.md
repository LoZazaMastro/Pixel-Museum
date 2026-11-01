# Persistent collection storage

The compact installer stores the collection in `/data/pixelmuseum/collection`,
separately from preferences and trophy state in `/download0/pixelmuseum`.
Native image/video caches and YouTube state use
`/data/pixelmuseum/collection/media-cache`, within the collection reset allowlist.
Host previews retain their original user-data paths.
The twelve published USTAR files remain unchanged. New installations keep those
verified archives and read images directly at indexed offsets; they do not unpack
27,978 individual files or keep a second extracted copy.

`content/collection-archive-index.json` is bundled with the executable. Its offsets,
paths, lengths and inventories were generated from all twelve local release
archives and checked against their pinned SHA256 digests. The index is about
2.58 MB. It is not fetched from an untrusted archive. Each downloaded archive is
flushed and checked on disk against its bundled SHA256 before an atomic rename
and durable checkpoint make it available. The complete collection is exposed only
after every pack and the image registry have passed validation.

The image worker reads only the requested image or preview into its existing
bounded decoder buffer. Quality, original bytes, preview priority, asynchronous
GPU uploads and the memory budgets are unchanged. No per-image extraction,
network request or temporary image write is needed for archived photos. Complete
preloaded editions and older extracted packs remain supported; mixed collections
reuse completed extracted packs rather than downloading them again.

Incoming downloads are explicitly coalesced into 2 MiB writes and forwarded to a
restricted payload writer. It starts automatically through the same local ELF
loader mechanism already used for notifications. The still-open loader connection
becomes its private command channel, following the user-supplied Stremio Plus
download writer. No separate FTP service is required by the installer.

The title retains HTTPS and pinned on-disk SHA verification. The helper alone
performs large file writes. Its embedded session capability allows only listed
pack hashes and lengths in the fixed museum downloads directory, with no client
paths or general filesystem commands. A write acknowledgement counts actual file
bytes; FINISH acknowledges a partial or full prefix only after file/directory
sync and close. Resume uses the actual file length. Missing service support is an
explicit failure, never a silent fallback to the slow title writer. Buffers,
messages, timeouts and the helper lifetime are bounded.

The payload's effective UID differs from its real UID, and its group differs
from the title's group on this console. Shared directories and pack files use
the payload's real UID and GID, with modes 0770 and 0660 respectively. This
keeps the title as owner and the writer in the shared group; assuming group
zero prevents the writer from traversing a title-created directory. Production
namespace authentication and a durable write/readback were verified separately
from the isolated throughput probe.

## Console measurements motivating the change

The previous container-backed writer spent about 96% of later transfers inside
`fwrite`. Moving only the path to ordinary `/data` did not solve the whole flow:
the first 943 MB pack downloaded in 17.562 seconds, but extracting its 1,568 files
took 327.307 seconds. File `fsync` accounted for only 15.250 seconds of that.
Subsequent downloads again fell below 2 MiB/s. The archive installation removed
the small-file extraction pass, but the title writer still degraded on pack 3.
An independent FTP process then wrote 64 MiB at 62.99 MiB/s on the same storage
while the title was slow. The new payload writer separately passed a native
64 MiB test at 66.05 MiB/s, including sync and exact SHA256 readback. These short
probes isolate the process difference; the final sustained installation through
the title's client must still be recorded separately. The installer retains the
archive design and moves bulk writes out of the title process as well.

## Recovery and compatibility

Private staging and final archives share one filesystem for atomic activation.
SHA256 verification, durable checkpoints, pause/retry and actual-byte Range resume
remain mandatory. Legacy imports copy validated data without deleting the old
tree or attempting a cross-filesystem rename. A complete legacy collection can be
read in place. Unrecognized or invalid archive metadata fails closed.

The native worker avoids `statfs` and `statvfs`, whose calls previously stopped
this console. Storage failures, including `ENOSPC` and `EDQUOT`, are reported by
actual writes and flushes. The earlier title-only 16 MiB write probe is skipped
when the native independent writer is used; it would measure the wrong process.

`sce_sys/param.json` reserves `downloadDataSize: 256` MiB for preferences and small
state in `/download0/pixelmuseum`. Collection archives and large caches belong in
`/data/pixelmuseum`, outside that container, so their size is not reserved twice.
The Stremio reference uses zero, but Pixel Museum retains a writable title
container for its preferences. The earlier 64 MiB candidate passed local metadata
checks but failed to launch on the console. The same console previously failed to
launch CD Player with 128 MiB, then successfully recreated its container and
launched with 256 MiB on 23 October 2026. This provides a tested reference for the
256 MiB setting; the updated Museum metadata still needs its own launch check.
Updating metadata alone does not shrink an existing
16 GiB container; reclaiming that reservation is a separate, app-closed operation
which must preserve the installed collection in `/data/pixelmuseum`. The staged
package helper applies the 256 MiB override without changing stable `dist` files or
historical release archives.

The first-run reset helper includes only exact museum roots. `--keep-app` removes
museum data and caches while preserving the application payload. Execution checks
that the title process is closed; no external reset, migration or replacement is
performed while the app is running. Resetting an active download requires a new
explicit user request.
