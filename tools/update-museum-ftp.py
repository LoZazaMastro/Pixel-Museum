#!/usr/bin/env python3
"""Update the installed museum using verified temporary files; preserve user data."""
from pathlib import Path, PurePosixPath
from ftplib import FTP, error_perm, error_temp
import argparse
import hashlib
import json
import time
import uuid

REMOTE_ROOT = "/data/homebrew/PPSA70421"
PROTECTED = {"userdata", "savedata", "settings", "session.log", "settings.json", "state.json"}
COMPLETED_REPORTS = {"PASS_ALL_PAYLOAD_SHA256_VERIFIED", "PASS_DELTA_SHA256_VERIFIED_BASELINE_REUSED"}
PARTIAL_REPORTS = {"LOCAL_PAYLOAD_PLAN_ONLY", "UPDATING", "FAILED_DO_NOT_SHUT_DOWN"}
VERIFIED_STATES = {"uploaded_verified", "unchanged_verified", "unchanged_previous_verified_baseline_reused", "unchanged_verified_resume_reused"}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def remote_path(relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or not p.parts or any(x in {".", ".."} for x in p.parts):
        raise ValueError("Unsafe payload path")
    if any(x in relative for x in ("\r", "\n", "\\")) or p.parts[0] in PROTECTED:
        raise ValueError("User data is not deployment payload")
    return REMOTE_ROOT + "/" + p.as_posix()


def verified_baseline(report_path):
    """Validate a complete receipt and its provenance without contacting FTP.

    A failed/interrupted receipt may prove individual resumed files, but can
    never itself become a baseline. Reused rows must resolve all the way to a
    direct uploaded/remote-SHA verification through hash-pinned receipts.
    """
    cache, visiting = {}, set()

    def sha(value):
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdefABCDEF" for c in value):
            raise ValueError("Invalid receipt SHA-256")
        return value.lower()

    def rows(value, verified=False):
        if not isinstance(value, list):
            raise ValueError("Receipt files/verified must be arrays")
        result = {}
        for row in value:
            if not isinstance(row, dict) or not isinstance(row.get("relative"), str):
                raise ValueError("Invalid receipt file row")
            relative = row["relative"]
            remote_path(relative)
            if relative != PurePosixPath(relative).as_posix() or relative in result:
                raise ValueError("Duplicate or noncanonical receipt path: " + relative)
            size = row.get("bytes")
            if type(size) is not int or size < 0:
                raise ValueError("Invalid receipt byte count: " + relative)
            item = {"relative": relative, "bytes": size, "sha256": sha(row.get("sha256"))}
            if verified:
                if row.get("status") not in VERIFIED_STATES:
                    raise ValueError("Unknown verified-row status: " + relative)
                item["status"] = row["status"]
            result[relative] = item
        return result

    def same(left, right):
        return left is not None and right is not None and left["bytes"] == right["bytes"] and left["sha256"] == right["sha256"]

    def read(path, require_completed, expected_sha=None):
        path = path.resolve(strict=True)
        if path in visiting:
            raise ValueError("Cyclic deployment receipt provenance")
        if path in cache:
            result = cache[path]
            if expected_sha is not None and result["receipt_sha256"] != expected_sha:
                raise ValueError("Altered provenance receipt")
            if require_completed and result["status"] not in COMPLETED_REPORTS:
                raise ValueError("An incomplete/failed receipt cannot be a baseline")
            return result
        visiting.add(path)
        try:
            raw = path.read_bytes()
            receipt_sha = hashlib.sha256(raw).hexdigest()
            if expected_sha is not None and receipt_sha != expected_sha:
                raise ValueError("Altered provenance receipt")
            previous = json.loads(raw)
            if not isinstance(previous, dict) or previous.get("remote_root") != REMOTE_ROOT:
                raise ValueError("Receipt belongs to another installation")
            status = previous.get("status")
            if status not in COMPLETED_REPORTS | PARTIAL_REPORTS or require_completed and status not in COMPLETED_REPORTS:
                raise ValueError("Baseline must be a completed verified deployment")
            files = rows(previous.get("files"))
            verified = rows(previous.get("verified", []), verified=True)
            if status in COMPLETED_REPORTS and files.keys() != verified.keys():
                raise ValueError("Completed receipt has incomplete verified-file coverage")
            if any(not same(row, files.get(relative)) for relative, row in verified.items()):
                raise ValueError("Verified row does not match the declared payload SHA/bytes")
            if type(previous.get("payload_bytes")) is not int or previous["payload_bytes"] != sum(row["bytes"] for row in files.values()):
                raise ValueError("Receipt payload byte total is inconsistent")
            for relative, field in (("content/catalog.json", "runtime_sha256"), ("eboot.bin", "eboot_sha256")):
                if relative not in files or sha(previous.get(field)) != files[relative]["sha256"]:
                    raise ValueError("Receipt payload anchor mismatch: " + relative)

            def reference(name, required=False):
                reference_path, expected = previous.get(name + "_report"), previous.get(name + "_report_sha256")
                if reference_path is None and expected is None and not required:
                    return None
                if not isinstance(reference_path, str) or not reference_path:
                    raise ValueError("Missing " + name + " provenance path")
                expected = sha(expected)
                linked = Path(reference_path)
                if not linked.is_absolute():
                    linked = path.parent / linked
                linked = linked.resolve(strict=True)
                return read(linked, name == "baseline", expected)

            baseline = reference("baseline", status == "PASS_DELTA_SHA256_VERIFIED_BASELINE_REUSED")
            resume = reference("resume")
            for relative, row in verified.items():
                state = row["status"]
                origin = baseline if state == "unchanged_previous_verified_baseline_reused" else resume if state == "unchanged_verified_resume_reused" else None
                if state in {"unchanged_previous_verified_baseline_reused", "unchanged_verified_resume_reused"} and (origin is None or not same(row, origin["verified"].get(relative))):
                    raise ValueError("Unproven reused verification: " + relative)
            if status in COMPLETED_REPORTS and "transfer_completed_bytes" in previous:
                total, completed = previous.get("transfer_total_bytes"), previous["transfer_completed_bytes"]
                if type(total) is not int or type(completed) is not int or total < 0 or completed != total:
                    raise ValueError("Completed receipt has incomplete transfer counters")
            result = {"status": status, "files": files, "verified": verified, "receipt_sha256": receipt_sha}
            cache[path] = result
            return result
        finally:
            visiting.remove(path)

    return read(Path(report_path), True)["verified"]


def missing(error):
    text = str(error).lower()
    return text.startswith("550") and any(x in text for x in ("no such", "not found", "does not exist"))


def remote_digest(ftp, path):
    h, count = hashlib.sha256(), 0
    def consume(block):
        nonlocal count
        count += len(block)
        h.update(block)
    ftp.retrbinary("RETR " + path, consume, blocksize=256 * 1024)
    return h.hexdigest(), count


def ensure_directory(ftp, path, known):
    if path in known:
        return
    if path != REMOTE_ROOT:
        ensure_directory(ftp, str(PurePosixPath(path).parent), known)
    try:
        ftp.mkd(path)
    except error_perm:
        previous = ftp.pwd()
        try:
            ftp.cwd(path)
        finally:
            ftp.cwd(previous)
    known.add(path)


def publish(ftp, local, relative, expected_sha, expected_size, known):
    destination = remote_path(relative)
    try:
        size = ftp.size(destination)
    except error_perm as error:
        if not missing(error):
            raise
        size = None
    if size == expected_size:
        sha, received = remote_digest(ftp, destination)
        if sha == expected_sha and received == expected_size:
            return "unchanged_verified"
    directory = str(PurePosixPath(destination).parent)
    ensure_directory(ftp, directory, known)
    temporary = directory + "/." + PurePosixPath(destination).name + ".museum-" + uuid.uuid4().hex + ".tmp"
    with local.open("rb") as stream:
        ftp.storbinary("STOR " + temporary, stream, blocksize=256 * 1024)
    sha, received = remote_digest(ftp, temporary)
    if sha != expected_sha or received != expected_size:
        raise RuntimeError("Uploaded temporary file failed SHA-256 verification: " + relative)
    # Never delete the installed file to make room. A failed rename leaves it intact.
    for attempt in range(12):
        try:
            ftp.rename(temporary, destination)
            break
        except error_temp as error:
            if not str(error).startswith("450") or attempt == 11:
                raise
            # The PS5 FTP server can complete RNTO asynchronously after 450.
            time.sleep(1)
            try:
                sha, received = remote_digest(ftp, destination)
                if sha == expected_sha and received == expected_size:
                    return "uploaded_verified"
            except (error_perm, error_temp):
                pass
    if ftp.size(destination) != expected_size:
        raise RuntimeError("Promoted file size differs: " + relative)
    return "uploaded_verified"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--runtime-sha256", required=True)
    parser.add_argument("--eboot-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--host", default="192.168.1.56")
    parser.add_argument("--port", type=int, default=2121)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--reuse-plan", type=Path, help="Reuse a frozen local manifest after a transient FTP failure")
    parser.add_argument("--baseline-report", type=Path, help="Reuse an earlier successful deployment manifest for unchanged immutable payload files")
    parser.add_argument("--deploy", action="store_true", help="Perform the update; otherwise only inspect local payload")
    parser.add_argument("--app-closed", action="store_true", help="The operator has established that Pixel Museum is closed")
    args = parser.parse_args()
    if args.deploy and not args.app_closed:
        parser.error("Close Pixel Museum before updating its files")
    folder = args.folder.resolve(strict=True)
    if args.report.resolve().is_relative_to(folder):
        parser.error("The report must be outside the payload folder")
    param = json.loads((folder / "sce_sys/param.json").read_text("utf8"))
    if param.get("titleId") != "PPSA70421":
        raise SystemExit("Unexpected app title")
    for relative, expected in [("content/catalog.json", args.runtime_sha256), ("eboot.bin", args.eboot_sha256)]:
        if digest(folder / relative) != expected:
            raise SystemExit("Staged payload differs from the verified build: " + relative)
    if args.reuse_plan:
        plan=json.loads(args.reuse_plan.read_text(encoding="utf8"))
        if plan.get("runtime_sha256") != args.runtime_sha256 or plan.get("eboot_sha256") != args.eboot_sha256 or plan.get("remote_root") != REMOTE_ROOT:
            raise SystemExit("Frozen plan is for a different staged payload")
        files=plan["files"]
        for row in files:
            remote_path(row["relative"])
            path=folder/row["relative"]
            if path.is_symlink() or not path.resolve().is_relative_to(folder) or path.stat().st_size != row["bytes"]:
                raise SystemExit("Staged file changed since the frozen plan: "+row["relative"])
    else:
        files = []
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(folder):
                raise SystemExit("Payload contains an external link")
            relative = path.relative_to(folder).as_posix()
            remote_path(relative)
            files.append({"relative": relative, "bytes": path.stat().st_size, "sha256": digest(path)})
    last = {"models/index.json": 1, "assets/images/manifest.json": 2,
              "content/credits.json": 3, "content/catalog.json": 4, "content/human-history.json": 4,
            "eboot.bin": 5, "sce_sys/param.json": 6}
    files.sort(key=lambda x: (last.get(x["relative"], 0), x["relative"]))
    report = {"status": "LOCAL_PAYLOAD_PLAN_ONLY", "remote_root": REMOTE_ROOT,
              "files": files, "payload_bytes": sum(x["bytes"] for x in files),
              "runtime_sha256": args.runtime_sha256, "eboot_sha256": args.eboot_sha256,
              "preserves_user_data": True, "deletes_installed_files": False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
    save()
    print("Local payload inspected:", len(files), "files,", report["payload_bytes"], "bytes", flush=True)
    if not args.deploy:
        return
    baseline = {}
    if args.baseline_report:
        try:
            baseline = verified_baseline(args.baseline_report)
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise SystemExit("Invalid deployment baseline: " + str(error)) from error
        report["baseline_report"] = str(args.baseline_report.resolve())
        report["baseline_report_sha256"] = digest(args.baseline_report)
    resumed = {}
    if args.reuse_plan:
        resumed = {row["relative"]: row for row in plan.get("verified", []) if row.get("status") in VERIFIED_STATES}
        report["resume_report"] = str(args.reuse_plan.resolve())
        report["resume_report_sha256"] = digest(args.reuse_plan)
    transfer_total = sum(row["bytes"] for row in files
                         if baseline.get(row["relative"], {}).get("sha256") != row["sha256"]
                         or baseline.get(row["relative"], {}).get("bytes") != row["bytes"])
    transfer_done = sum(row["bytes"] for row in files
                        if resumed.get(row["relative"], {}).get("sha256") == row["sha256"]
                        and resumed.get(row["relative"], {}).get("bytes") == row["bytes"]
                        and (baseline.get(row["relative"], {}).get("sha256") != row["sha256"]
                             or baseline.get(row["relative"], {}).get("bytes") != row["bytes"]))
    next_progress = ((transfer_done * 100 // transfer_total) // 10 + 1) * 10 if transfer_total else 100
    if resumed:
        print("TRANSFER_RESUMED", transfer_done * 100 // transfer_total if transfer_total else 100, flush=True)
    report["transfer_total_bytes"] = transfer_total
    verified, started, notified = [], time.monotonic(), time.monotonic()
    last_saved = started
    report["status"] = "UPDATING"
    try:
        with FTP() as ftp:
            ftp.connect(args.host, args.port, timeout=args.timeout)
            ftp.login("anonymous", "anonymous")
            ftp.voidcmd("TYPE I")
            ftp.cwd(REMOTE_ROOT)
            known = {REMOTE_ROOT}
            for row in files:
                old = baseline.get(row["relative"], {})
                prior = resumed.get(row["relative"], {})
                if prior.get("sha256") == row["sha256"] and prior.get("bytes") == row["bytes"]:
                    status = "unchanged_verified_resume_reused"
                elif old.get("sha256") == row["sha256"] and old.get("bytes") == row["bytes"]:
                    status = "unchanged_previous_verified_baseline_reused"
                else:
                    status = publish(ftp, folder / row["relative"], row["relative"], row["sha256"], row["bytes"], known)
                    transfer_done += row["bytes"]
                    report["transfer_completed_bytes"] = transfer_done
                    while next_progress < 100 and transfer_done * 100 >= transfer_total * next_progress:
                        print("TRANSFER_PROGRESS", next_progress, flush=True)
                        next_progress += 10
                verified.append({**row, "status": status})
                if time.monotonic() - last_saved >= 20 or last.get(row["relative"], 0):
                    report["verified"] = verified
                    save()
                    last_saved = time.monotonic()
                if time.monotonic() - notified >= 20:
                    print("Verified payload files:", len(verified), "elapsed seconds:", round(time.monotonic() - started), flush=True)
                    notified = time.monotonic()
            report.update(status="PASS_DELTA_SHA256_VERIFIED_BASELINE_REUSED" if baseline else "PASS_ALL_PAYLOAD_SHA256_VERIFIED", verified=verified,
                          elapsed_seconds=round(time.monotonic() - started, 2))
            save()
            print(report["status"], len(verified), flush=True)
            print("TRANSFER_PROGRESS 100", flush=True)
    except Exception as error:
        report.update(status="FAILED_DO_NOT_SHUT_DOWN", verified=verified, error=str(error))
        save()
        raise


if __name__ == "__main__":
    main()
