"""Read-only validation of an isolated real setup run; never targets user data."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def verify(run):
    run = run.resolve()
    project = Path(__file__).resolve().parents[2]
    allowed = (project / "build/windows-installer-test").resolve()
    assert run.is_relative_to(allowed), "Only the approved isolated test tree is accepted"
    manifest_path = run / "windows-manifest-with-notices.json"
    if not manifest_path.exists():
        manifest_path = run / "windows-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    installed = run / "installed/Pixel Museum"
    assert installed.is_dir(), "The installation was not committed"
    collection_raw = (installed / "content/collection-packs.json").read_bytes()
    collection = json.loads(collection_raw)
    collection_sha = digest_bytes(collection_raw)
    ready = installed / "collection" / f"{collection['collection_id']}-{collection_sha[:24]}"
    complete = json.loads((ready / ".complete.json").read_bytes())
    assert complete == {
        "schema_version": 1,
        "manifest_sha256": collection_sha,
        "image_manifest_sha256": collection["image_manifest_sha256"],
        "pack_count": len(collection["packs"]),
    }
    image_manifest = (ready / "assets/images/manifest.json").read_bytes()
    assert digest_bytes(image_manifest) == collection["image_manifest_sha256"]
    archive_index = json.loads((installed / "content/collection-archive-index.json").read_bytes())
    assert archive_index["collection_id"] == collection["collection_id"]
    assert archive_index["image_manifest_sha256"] == collection["image_manifest_sha256"]
    assert len(archive_index["packs"]) == len(collection["packs"]) == 12
    samples, image_count, seen = [], 0, set()
    tar_bytes = 0
    archived_manifest = False
    for number, pack in enumerate(collection["packs"]):
        filename = f"{pack['sha256']}.tar"
        archive = ready / "archives" / filename
        assert archive.is_file() and archive.stat().st_size == pack["bytes"]
        original = run / "payloads" / Path(pack["url"]).name
        assert os.path.samefile(original, archive), "The verified local TAR was not retained intact"
        checkpoint = json.loads((ready / f".pack-{number}.json").read_bytes())
        assert checkpoint == {
            "sha256": pack["sha256"], "storage": "archive",
            "archive": f"archives/{filename}", "bytes": pack["bytes"],
        }
        row = archive_index["packs"][number]
        assert row["id"] == pack["id"] and row["sha256"] == pack["sha256"]
        assert row["bytes"] == pack["bytes"]
        end = 0
        with archive.open("rb") as data:
            for item in row["files"]:
                name, offset, size = item["path"], item["offset"], item["bytes"]
                path = PurePosixPath(name)
                assert name.startswith("assets/images/") and ".." not in path.parts
                assert "\\" not in name and ":" not in name and name not in seen
                assert offset >= 512 and offset % 512 == 0 and offset >= end
                assert size >= 0 and offset + size <= pack["bytes"]
                end = offset + size
                seen.add(name)
                if name == "assets/images/manifest.json":
                    data.seek(offset)
                    assert digest_bytes(data.read(size)) == collection["image_manifest_sha256"]
                    archived_manifest = True
                elif len(samples) < 3 and size > 16 and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    data.seek(offset)
                    head = data.read(min(size, 32))
                    assert head.startswith((b"\x89PNG", b"\xff\xd8", b"RIFF")), name
                    samples.append({"path": name, "bytes": size, "archive": filename})
        image_count += len(row["files"])
        tar_bytes += pack["bytes"]
    assert archived_manifest and samples
    assert image_count == collection.get("file_count", collection["files"])
    prefs = json.loads((installed / "preferences.json").read_bytes())
    app = next(p for p in manifest["packages"] if p["kind"] == "app")
    with zipfile.ZipFile(run / "payloads" / app["filename"]) as source:
        if "preferences.json" in source.namelist():
            assert (installed / "preferences.json").read_bytes() == source.read("preferences.json")
        else:
            assert prefs == {"language": "it", "language_chosen": True}
        if "video-settings.json" not in source.namelist():
            assert not (installed / "video-settings.json").exists()
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    checked_files = 0
    for directory, folders, files in os.walk(installed, followlinks=False):
        for name in folders + files:
            target = Path(directory) / name
            info = target.lstat()
            assert not stat.S_ISLNK(info.st_mode)
            assert not (getattr(info, "st_file_attributes", 0) & reparse), str(target)
            checked_files += 1
    assert not (installed.parent / ".pixel-museum-setup").exists()
    assert not list(installed.parent.glob(".pixel-museum-stage-*"))
    log = (run / "install-with-notices.log").read_text(encoding="utf-16" if (run / "install-with-notices.log").read_bytes().startswith(b"\xff\xfe") else "utf-8-sig")
    assert len([line for line in log.splitlines() if line.startswith("Verify ")]) == 13
    assert not any(line.startswith("Download ") for line in log.splitlines())
    assert any(line.startswith("Finish ") for line in log.splitlines())
    report = {
        "success": True,
        "installed_root": str(installed),
        "manifest": str(manifest_path),
        "app_archive_repaired_only_inside_isolated_test": manifest_path.name.endswith("with-notices.json"),
        "verified_packages": 13,
        "verified_retained_tar_archives": 12,
        "retained_tar_bytes": tar_bytes,
        "ready_root": str(ready),
        "collection_manifest_sha256": collection_sha,
        "indexed_files": image_count,
        "archived_image_manifest_hash_verified": True,
        "real_archive_image_samples": samples,
        "same_file_ids_for_installed_and_local_tar_sources": True,
        "preferences_preserved": prefs,
        "onboarding_not_completed_by_setup": not prefs.get("onboarding_complete", False),
        "filesystem_entries_checked_for_links": checked_files,
        "symlinks_or_reparse_points": 0,
        "download_cache_and_staging_removed_after_success": True,
        "network_downloads": 0,
        "actual_user_destination_accessed": False,
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    report = verify(args.run)
    output = args.run / "full-engine-report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
