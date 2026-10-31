"""Offline receipt-chain tests; never constructs or contacts an FTP client."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("museum_updater", Path(__file__).resolve().parents[1] / "tools/update-museum-ftp.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class VerifiedBaselineTests(unittest.TestCase):
    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf8")
        return path

    @staticmethod
    def row(name, contents, status=None):
        result = {"relative": name, "bytes": len(contents), "sha256": hashlib.sha256(contents).hexdigest()}
        if status:
            result["status"] = status
        return result

    def receipt(self, files, verified, status):
        return {"status": status, "remote_root": updater.REMOTE_ROOT, "files": copy.deepcopy(files),
                "verified": copy.deepcopy(verified), "payload_bytes": sum(r["bytes"] for r in files),
                "runtime_sha256": files[0]["sha256"], "eboot_sha256": files[1]["sha256"]}

    def link(self, target, kind, name):
        target[kind + "_report"] = name  # Relative provenance paths are supported.
        target[kind + "_report_sha256"] = updater.digest(self.root / name)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        original = [self.row("content/catalog.json", b"catalog"), self.row("eboot.bin", b"old executable"), self.row("assets/a.bin", b"a")]
        self.full = self.receipt(original, [{**r, "status": "uploaded_verified"} for r in original], "PASS_ALL_PAYLOAD_SHA256_VERIFIED")
        self.write("full.json", self.full)
        current = [original[0], self.row("eboot.bin", b"new executable"), original[2], self.row("assets/b.bin", b"b")]
        self.resume = self.receipt(current, [{**current[2], "status": "unchanged_previous_verified_baseline_reused"}, {**current[3], "status": "uploaded_verified"}], "FAILED_DO_NOT_SHUT_DOWN")
        self.link(self.resume, "baseline", "full.json")
        self.write("resume.json", self.resume)
        verified = [{**r, "status": status} for r, status in zip(current, ["unchanged_previous_verified_baseline_reused", "uploaded_verified", "unchanged_verified_resume_reused", "unchanged_verified_resume_reused"])]
        self.delta = self.receipt(current, verified, "PASS_DELTA_SHA256_VERIFIED_BASELINE_REUSED")
        self.link(self.delta, "baseline", "full.json")
        self.link(self.delta, "resume", "resume.json")

    def load(self):
        return updater.verified_baseline(self.write("delta.json", self.delta))

    def rejects(self):
        with self.assertRaises((ValueError, OSError)):
            self.load()

    def test_complete_delta_and_second_delta_reuse_valid_failed_resume(self):
        self.assertEqual(len(self.load()), 4)
        current = self.delta["files"] + [self.row("assets/c.bin", b"c")]
        verified = [{**r, "status": "unchanged_previous_verified_baseline_reused"} for r in current[:-1]] + [{**current[-1], "status": "uploaded_verified"}]
        second = self.receipt(current, verified, "PASS_DELTA_SHA256_VERIFIED_BASELINE_REUSED")
        self.link(second, "baseline", "delta.json")
        self.assertEqual(len(updater.verified_baseline(self.write("second.json", second))), 5)

    def test_failed_resume_is_never_a_baseline(self):
        with self.assertRaises(ValueError):
            updater.verified_baseline(self.root / "resume.json")

    def test_incomplete_completed_report(self):
        self.delta["verified"].pop()
        self.rejects()

    def test_unknown_row_status(self):
        self.delta["verified"][0]["status"] = "trusted_without_evidence"
        self.rejects()

    def test_verified_sha_mismatch(self):
        self.delta["verified"][2]["sha256"] = "a" * 64
        self.rejects()

    def test_verified_size_mismatch(self):
        self.delta["verified"][2]["bytes"] += 1
        self.rejects()

    def test_noninteger_size(self):
        self.delta["files"][2]["bytes"] = True
        self.rejects()

    def test_malformed_sha(self):
        self.delta["files"][2]["sha256"] = "z" * 64
        self.rejects()

    def test_altered_parent_receipt(self):
        self.full["payload_bytes"] += 1
        self.write("full.json", self.full)
        self.rejects()

    def test_hash_pinned_but_semantically_corrupt_parent(self):
        self.full["payload_bytes"] += 1
        self.write("full.json", self.full)
        self.link(self.delta, "baseline", "full.json")
        self.rejects()

    def test_wrong_remote_root(self):
        self.delta["remote_root"] = "/data/homebrew/OTHER"
        self.rejects()

    def test_duplicate_path(self):
        self.delta["files"].append(copy.deepcopy(self.delta["files"][2]))
        self.rejects()

    def test_missing_parent_provenance(self):
        del self.delta["baseline_report"]
        self.rejects()

    def test_missing_resume_provenance(self):
        del self.delta["resume_report"]
        del self.delta["resume_report_sha256"]
        self.rejects()

    def test_reused_row_not_proven_by_resume(self):
        self.resume["verified"].pop()
        self.write("resume.json", self.resume)
        self.link(self.delta, "resume", "resume.json")
        self.rejects()

    def test_forged_reused_hash_matches_files_but_not_ancestor(self):
        self.delta["files"][2]["sha256"] = self.delta["verified"][2]["sha256"] = "c" * 64
        self.rejects()

    def test_incomplete_transfer_counter(self):
        self.delta.update(transfer_total_bytes=200, transfer_completed_bytes=199)
        self.rejects()

    def test_protected_user_data_path(self):
        self.delta["files"][2]["relative"] = "userdata/save.bin"
        self.rejects()


if __name__ == "__main__":
    unittest.main()
