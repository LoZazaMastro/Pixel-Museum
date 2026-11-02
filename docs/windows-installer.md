# Pixel Museum Windows setup

The installer is a native Rust executable with neutral light/dark themes, the museum’s canonical wordmark, and the original Inter variable font at weights 400, 600 and 650. It follows the Windows system theme until the user chooses a manual override. Its frameless title bar provides a theme switch, drag, minimize, maximize/restore, close and resize controls. Flat controls, square checkboxes and the PS5 collection’s 78-square progress display preserve the museum’s visual language. It offers English, Italian, French, German and Spanish; one continuous full licence document and acceptance checkbox; a destination picker; download and verification progress; cancellation; retry; and optional launch after installation. It uses egui/eframe with OpenGL. A user can install into a writable folder without administrator privileges.

The application and collection share the chosen `Pixel Museum` folder. The language chosen in setup affects setup only: it does not create or select the app's `language` or `language_chosen` preferences. On first launch the museum presents its own language selection. Setup does not complete the introduction. It refuses an existing nonempty installation folder, so it cannot silently replace or upgrade a collection; application updates preserve existing preferences.

After successful installation, the final page offers resolution, display mode, VSync, frame limit, five audio levels and cultural audio through the controller speaker. Settings are written only when the user chooses **Finish** or **Launch Pixel Museum**, into that completed installation’s `preferences.json` and `video-settings.json`. Existing appearance, language, onboarding and unrelated keys are preserved. App appearance remains controlled by its own preferences and defaults. Video defaults match the app’s usable-desktop size calculation, windowed mode, VSync and 60 FPS. Audio defaults are 100% master/effects/culture/controller and 48% ambient, with cultural audio on the controller disabled. Closing the window does not launch the app or apply these optional settings.

The initial display-mode choices are **Fullscreen**, **Borderless fullscreen**, **Windowed**, in that order; Windowed remains the default. They save `(fullscreen, borderless)` as `(true, false)`, `(true, true)` or `(false, false)` in `video-settings.json`. Borderless uses the desktop resolution and disables the resolution selector without discarding the selected windowed/exclusive size.

## Build

Install stable Rust **1.95 or newer** for `x86_64-pc-windows-msvc` and Visual Studio C++ Build Tools with a Windows SDK. The build script also discovers Rust in `%USERPROFILE%\.cargo\bin` when it is absent from `PATH`.

```powershell
# Development build: no public Windows release is assumed.
.\tools\build-windows-installer.ps1

# Release build: embed a manifest created from the actual packaged app and verified collection.
.\tools\build-windows-installer.ps1 -ManifestPath .\dist\windows\windows-manifest.json

# Alternative: pin the SHA-256 of a manifest uploaded to a tagged GitHub release.
.\tools\build-windows-installer.ps1 -ManifestUrl 'https://github.com/LoZazaMastro/Pixel-Museum/releases/download/ACTUAL-TAG/windows-manifest.json' -ManifestSha256 'ACTUAL-64-CHARACTER-DIGEST'
```

The last example contains placeholders, not an existing Windows download. A release build must reference actual assets. The script runs the engine tests, validates embedded manifests and builds `dist/windows-installer/Pixel-Museum-Setup.exe` plus its SHA-256 file and licence notices. `-DebugBuild` uses a console-visible debug executable, and `-SkipTests` skips tests already run in the same validation cycle. `Cargo.lock` pins the dependency graph.

`-TargetDirectory` optionally places Cargo’s build cache on another local volume, without changing source files, distribution output, or the user’s chosen installation folder.

The Windows build script links the Visual C runtime statically and restores the caller’s Rust flags afterward. The resulting setup/updater needs Windows system libraries, without a separate VC redistributable bootstrap.

When neither an embedded manifest nor a pinned remote manifest exists, setup can load a neighbouring `windows-manifest.json` or let the user select a local package manifest. It does not claim a Windows release is available.

## Release manifest v1

This is the schema, illustrated with placeholder hashes and sizes that must be replaced by real computed values:

```json
{
  "schema_version": 1,
  "version": "ACTUAL-VERSION",
  "executable": "Pixel Museum.exe",
  "packages": [
    {
      "id": "app",
      "kind": "app",
      "format": "zip",
      "filename": "Pixel-Museum-Windows-x64.zip",
      "url": "https://github.com/LoZazaMastro/Pixel-Museum/releases/download/ACTUAL-TAG/Pixel-Museum-Windows-x64.zip",
      "sha256": "ACTUAL-APP-SHA256",
      "bytes": 1,
      "unpacked_bytes": 1,
      "target": "."
    },
    {
      "id": "images-001",
      "kind": "collection",
      "format": "tar",
      "filename": "images-001.tar",
      "url": "https://github.com/LoZazaMastro/Pixel-Museum/releases/download/v0.1.1/images-001.tar",
      "sha256": "ACTUAL-COLLECTION-PACK-SHA256",
      "bytes": 1,
      "unpacked_bytes": 1,
      "target": "collection/ACTUAL-READY-FOLDER/archives"
    }
  ]
}
```

Exactly one app ZIP and at least one collection package are required. `format` defaults to `zip`; only ZIP and retained TAR are accepted. `bytes` is the exact archive length, `sha256` authenticates that archive, and `unpacked_bytes` is the exact sum of file lengths for extracted ZIPs. For retained TARs `unpacked_bytes` equals `bytes`, because TARs remain intact and are read through the app’s verified archive index. Filenames must be plain ZIP/TAR basenames. App ZIP paths are relative to the installation root. Collection ZIP paths are relative to their safe `collection/…` target; retained TARs are stored at `<target>/<sha256>.tar`.

The app ZIP includes the executable, runtime libraries, required app data, `LICENSE`, `THIRD_PARTY_NOTICES.md` and the existing licence notices. For the production archive collection it also supplies the tiny ready records expected by the app:

```text
Pixel Museum/
  Pixel Museum.exe
  content/collection-packs.json
  content/collection-archive-index.json
  collection/<collection_id>-<sha256(raw collection-packs.json)[0:24]>/
    .complete.json
    .pack-0.json … .pack-N.json
    assets/images/manifest.json
    archives/<pack-sha256>.tar
```

`.complete.json` contains `schema_version: 1`, `manifest_sha256` of the raw original collection manifest, its `image_manifest_sha256`, and `pack_count`. Each zero-based `.pack-N.json` contains `sha256`, `storage: "archive"`, `archive: "archives/<sha256>.tar"` and `bytes`. The supplied image manifest is byte-identical to the verified original. The TAR entries are the existing published collection assets, so setup does not expand a second 10 GiB media tree. The packaging script must generate the records from the exact manifest shipped in the app ZIP.

URLs must be HTTPS assets of a tagged `LoZazaMastro/Pixel-Museum` GitHub release. Redirects are limited to GitHub’s HTTPS release asset storage. An externally loaded remote manifest requires a trusted SHA-256 passed with `--manifest-sha256` or embedded at build time; an embedded manifest is part of the setup executable. A local manifest is explicitly supplied local input and still pins every package’s length and SHA-256.

## Offline testing

Place real local payload ZIPs/TARs beside the manifest, or use `--payload-dir`. With an embedded or remote manifest, setup also looks beside its own executable. The installer prefers a matching local filename and verifies it identically to a download. Missing local packages use their manifest URL if present. Omitting `url` makes that package strictly local.

```powershell
$setup = '.\installer\target\debug\pixel-museum-setup.exe'
& $setup --manifest '.\dist\windows\windows-manifest.json' --payload-dir '.\dist\windows' --language it
& $setup --validate-manifest --manifest '.\dist\windows\windows-manifest.json'
& $setup --headless --accept-license --manifest '.\dist\windows\windows-manifest.json' --payload-dir '.\dist\windows' --install-dir 'D:\Museums\Pixel Museum' --language it
```

Headless installation requires both `--accept-license` and an explicit absolute `--install-dir`. It never starts the museum automatically. The same validation, verification, staging and commit code serves the wizard and headless paths. The automated tests create tiny disposable payloads; test installation, rejection of a reused nonempty destination, path traversal rejection, hash mismatch and cancellation.

`installer/tests/cli-smoke.ps1` runs an end-to-end local fixture against the compiled executable, including licence acceptance and verification that the app language remains unselected. It uses `--portable` to avoid writing real Windows integration. `cargo build --features preview` enables an isolated visual QA mode: set `PIXEL_MUSEUM_SETUP_SCREENSHOT` to a PNG output path and optionally `PIXEL_MUSEUM_SETUP_PREVIEW_PAGE` to `licence`, `destination`, `installing`, `finished`, `uninstall` or `uninstalled`, then run setup with `--language`. It captures the actual native framebuffer and exits. Normal builds do not include this mode.

## Windows integration and uninstall

Normal graphical and headless installs create a current-user **Programs → Pixel Museum** shortcut and an Installed Apps / Control Panel entry. An unchecked **Create a desktop shortcut** option adds a desktop link; headless users can pass `--desktop-shortcut`. Native `IShellLinkW` links use the installed executable's icon and the installation folder as their working directory. Setup never overwrites a shortcut belonging to another installation. No administrator rights, login startup task or system-wide registration is needed. Headless `--portable` skips all Windows registration and shortcuts.

The per-install HKCU uninstall key records the real display version, icon, location and size. Its `UninstallString` invokes the stable `tools/windows-updater/Pixel-Museum-Updater.exe --uninstall "ABSOLUTE-ROOT"`. The maintenance helper is supplied by the verified r5-or-newer app ZIP, with its own matching `application-files.json` entry and V2 capability marker. Setup verifies its PE header, length and SHA-256 and never copies its own executable over it. Older r4 payloads are rejected before collection installation. Application updates keep that helper inventory consistent and refresh `DisplayVersion` only when this installation already owns the registration; they never create new registration or alter preferences.

Uninstall opens a matching five-language, light/dark confirmation page. It explicitly keeps the collection, database, preferences, trophies, logs and unknown files in the installation folder. There is no recursive personal-data deletion. The helper verifies the install receipt, current executable and application inventory, refuses a running museum without closing it, and rejects linked/reparse paths. It quarantines unchanged inventory-owned app files on the same volume, then removes only owned Windows links and the per-install registry key. Modified app files are retained and reported. File or registration failures restore the original application files, inventory and receipt; incomplete recovery keeps its journal and backups with an actionable path.

Uninstall runs directly from the registered maintenance helper. It never copies or starts a Temp executable, creates cleanup scripts, schedules tasks, or tries to unlink its own running image. When that helper is the current executable, it remains at `tools/windows-updater/Pixel-Museum-Updater.exe` beside the intentionally retained personal data; the confirmation/completion UI discloses this small remainder, and the receipt records `retained_maintenance_helper`. It can be removed manually after closing the uninstaller. The receipt remains with `uninstalled: true`; setup still requires an empty folder for a fresh install.

`cargo test` exercises native shortcut creation, registration/version updates, ownership conflicts, registration failure, install/helper inventory, uninstall rollback and preservation with private folders and `HKCU\Software\PixelMuseum\InstallerTests` keys. It never registers fixture apps in the real Programs/Desktop/Installed Apps locations. `python installer/tests/uninstall-smoke.py --setup ABSOLUTE-SETUP.exe` additionally exercises the real shipping CLI, a running private fixture process, a locked-file rollback and direct execution of the installed helper with truthful retention. Its artifacts stay under `build/windows-installer-test/`.

The integration follows Microsoft's [Shell links](https://learn.microsoft.com/en-us/windows/win32/shell/links), [Uninstall registry key](https://learn.microsoft.com/en-us/windows/win32/msi/uninstall-registry-key), [process enumeration](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-enumprocesses), and [bounded registry-key deletion](https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-regdeletekeyexw) documentation.

## Storage and interrupted installation

Setup checks free space, holds an immutable verified archive handle through ZIP extraction or TAR copying, verifies SHA-256 before using an archive, and stages a complete installation next to the selected destination. It commits by renaming that staging folder on the same volume only after every package has passed. ZIP links, absolute paths, traversal, Windows device names, alternate streams and duplicate file paths are rejected. Existing symlinks and Windows reparse points in destination ancestors are rejected too.

Writable cache handles are validated as ordinary single-link files before any truncation or write. Download checkpoints live in the sibling `.pixel-museum-setup` cache and are addressed by SHA-256. An interrupted HTTP transfer resumes with a validated byte range; if the server returns a full response setup restarts that transfer. A hash mismatch discards its downloaded checkpoint. Cancellation is checked while reading, hashing, copying and extracting; a stalled network read has a 20-second timeout. Closing setup during installation requests cancellation and waits for its worker before exiting. The short final rename is indivisible.

On NTFS, retained TARs from the private resume cache can be hardlinked into staging after comparing the target file identity to the held verified input handle, preserving completed downloads for retries without duplicate storage. Caller-owned local TARs are always copied, so later source edits cannot mutate the installed collection. Filesystems or local source volumes that do not support hard links use a checked copy and need temporary extra space. Cancelled staging folders are removed; downloaded checkpoints remain for a retry. Successful installation removes the cache files used by that release. No system services, registry startup entries or elevated helpers are installed.

The software licence is GPL-3.0-or-later. Collection media and third-party components keep their respective rights and notices; setup imposes no additional EULA restrictions.

The Inter SIL Open Font License is retained in `installer/assets/Inter-LICENSE.txt`. `installer/licenses/THIRD-PARTY-NOTICES.txt` contains dependency and fallback-font notices for the locked Windows build; it is embedded in setup, available through its licence view, and copied beside the executable. Regenerate it after dependency updates with `installer/tools/collect-notices.ps1`; missing registry licence texts are retrieved from the corresponding pinned upstream source commits.

## Offline application-update helper

The same shipping executable is copied into the app payload as `tools/windows-updater/Pixel-Museum-Updater.exe`. The native app downloads a pinned app ZIP, then copies this helper into `application-updates/runner/` and invokes the temporary copy with `--apply-update ABSOLUTE-DESCRIPTOR.json`. Apply mode dispatches before the normal wizard and performs no GUI or network operations. Normal setup invocation is unchanged.

The descriptor uses these fields:

```json
{
  "schema_version": 1,
  "application_id": "pixel-museum",
  "platform": "windows-x64",
  "version": "ACTUAL-STRICT-SEMVER",
  "application_root": "C:\\Users\\USER\\Programs\\Pixel Museum",
  "archive": "C:\\Users\\USER\\Programs\\Pixel Museum\\application-updates\\payloads\\ACTUAL-LOWERCASE-SHA256.zip",
  "archive_sha256": "ACTUAL-LOWERCASE-SHA256",
  "archive_bytes": 1,
  "unpacked_bytes": 1,
  "parent_pid": 1,
  "parent_creation_time": 1,
  "language": "it",
  "result_path": "C:\\Users\\USER\\Programs\\Pixel Museum\\application-updates\\result.json",
  "restart": true
}
```

Hashes, sizes, version and process identity in this example are placeholders. Versions follow SemVer 2.0.0; the parent creation time is its exact Windows FILETIME integer. Compressed archives are bounded to 2 GiB and expanded contents to 4 GiB. The helper requires an ordinary installed root with `pixel-museum-install.json`, a recognized x64 `Pixel Museum.exe`, and its valid `application-files.json`. It checks a live parent’s executable path and creation time, then waits up to 120 seconds for that process to exit. An already-exited parent is accepted only after the installed executable and inventory are verified.

Each app ZIP supplies `application-files.json` with `schema_version: 1`, `application_id: "pixel-museum"`, `platform: "windows-x64"`, a `version`, and `files: [{path, bytes, sha256}]`. It lists every regular ZIP member except itself. The helper independently reads the entire archive SHA-256, validates member CRCs, lengths, hashes, path/type constraints, case aliases and inventory membership, and stages the app before replacing anything. The existing and new `content/collection-packs.json` and `assets/images/manifest.json` must match; resource migrations use their separate delivery path.

Updates preserve `collection/`, `database/`, `application-updates/`, preferences, video settings, trophies, logs, installation receipts and shortcuts. Protected ZIP entries are verified and skipped. Unknown pre-existing files survive; a new payload colliding with one is rejected. Only files declared by the old inventory can become obsolete, and a changed obsolete file is preserved by refusing the update.

The helper stages on the installation volume, journals each backup/replacement, moves the old executable out first and installs the new executable last. A failure rolls back the changed files and relaunches the previous app after complete restoration. A new child exiting nonzero during its first two seconds triggers the same rollback. This early-exit check complements native release/startup QA; it is not a renderer-ready handshake. An incomplete restoration retains its transaction journal and recovery files under `application-updates/transactions/update-*`.

The atomic result receipt contains `schema_version`, `application_id`, `version`, `success`, `rolled_back`, localized `message`, diagnostic `details`, `updated_files` and `removed_files`. A complete restoration reports `success: false, rolled_back: true`. Invalid untrusted paths are rejected without writing to them; operational failures after root/result-path validation receive a failure receipt.

`installer/tests/updater-smoke.py --setup PATH-TO-SETUP` builds tiny native x64 fixture apps and exercises real helper invocation, temporary self-replacement, successful relaunch, bad SHA, file-lock rollback, unowned collisions and immediate app failure. Its fixtures/reports stay under `build/windows-installer-test`. The Rust tests additionally cover all backup/install failure points, real process identity/waiting, links, case aliases, CRC/expansion rejection and preservation of mutable state.

Implementation references: [eframe](https://docs.rs/eframe/0.37.0/eframe/), [reqwest blocking client](https://docs.rs/reqwest/0.13.5/reqwest/blocking/struct.ClientBuilder.html), [ZIP path validation](https://docs.rs/zip/9.2.2/zip/read/struct.ZipFile.html), [native file dialog](https://docs.rs/rfd/0.17.2/rfd/struct.FileDialog.html), [SemVer 2.0.0](https://semver.org/), [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes), [QueryFullProcessImageNameW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew), [WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).
