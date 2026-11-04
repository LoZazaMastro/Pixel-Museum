"""Local HTTP integration checks for the production database updater and save overlay.

Build the small driver with the production database_updater.cpp/save_file.cpp.
No publisher URLs or installed game data are touched; all writes stay in fixtures.
"""
from __future__ import annotations
import argparse
import collections
import contextlib
import copy
import hashlib
import http.server
import json
import pathlib
import queue
import socket
import subprocess
import tempfile
import threading
import time


def catalogue(title, **extra):
    return json.dumps({"schema_version": 1, "entries": [{"id": "fixture", "title": title, "year": 1989}], **extra}, separators=(",", ":")).encode("utf-8")


class Fixtures:
    def __init__(self):
        self.routes = {}
        self.hits = collections.Counter()
        self.parallel_active = 0
        self.parallel_peak = 0
        self.lock = threading.Lock()
        owner = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                with owner.lock:
                    owner.hits[self.path] += 1
                    route = dict(owner.routes.get(self.path, {"status": 404, "body": b"missing"}))
                body = route.get("body", b"")
                if isinstance(body, dict):
                    body = json.dumps(body, ensure_ascii=False).encode("utf-8")
                delay = route.get("delay", 0)
                if delay:
                    with owner.lock:
                        owner.parallel_active += 1
                        owner.parallel_peak = max(owner.parallel_peak, owner.parallel_active)
                    try:
                        time.sleep(delay)
                    finally:
                        with owner.lock:
                            owner.parallel_active -= 1
                self.send_response(route.get("status", 200))
                self.send_header("Content-Length", str(route.get("length", len(body))))
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    if route.get("slow"):
                        for at in range(0, len(body), 1024):
                            self.wfile.write(body[at:at + 1024])
                            self.wfile.flush()
                            time.sleep(0.02)
                    else:
                        self.wfile.write(body)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
                self.close_connection = True

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def set(self, path, **route):
        with self.lock:
            self.routes[path] = route

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class Driver:
    def __init__(self, executable, directory, server):
        self.root = directory / "application"
        self.data = directory / "data"
        (self.root / "content").mkdir(parents=True)
        self.data.mkdir()
        self.bundled = catalogue("bundled").decode("utf-8")
        (self.root / "content/catalog.json").write_text(self.bundled, encoding="utf-8")
        (self.root / "content/catalog.json.bak").write_text("sibling", encoding="utf-8")
        (self.root / "content/database-version.json").write_text('{"revision":1}', encoding="utf-8")
        (self.data / "preferences.json").write_text('{"language":"it"}', encoding="utf-8")
        (self.data / "trophies-v1.dat").write_bytes(b"trophy-sentinel")
        self.process = subprocess.Popen([str(executable), str(self.root), str(self.data), server.base + "/feed"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)
        self.lines = queue.Queue()
        threading.Thread(target=lambda: [self.lines.put(line) for line in self.process.stdout], daemon=True).start()
        assert self.call("configure")["ok"]

    def call(self, op, **kwargs):
        self.process.stdin.write(json.dumps({"op": op, **kwargs}) + "\n")
        self.process.stdin.flush()
        try:
            line = self.lines.get(timeout=16)
        except queue.Empty:
            self.process.kill()
            raise AssertionError(f"driver hung during {op}")
        result = json.loads(line)
        assert "driver_error" not in result, result
        return result

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            self.process.wait(timeout=15)
        assert self.process.returncode == 0, self.process.stderr.read()


def manifest(server, payload, revision=2, path="content/catalog.json", url="/payload"):
    return {"schema_version": 1, "database_id": "pixel-museum", "minimum_reader": 1, "revision": revision, "version": f"test-{revision}", "notes": {"en": "A new story.", "it": "Una nuova storia."}, "files": [{"path": path, "url": server.base + url, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}]}


def assert_phase(result, expected):
    assert result["ok"], result
    assert result["state"]["phase"] == expected, result


def run(executable, output):
    server = Fixtures()
    passed = 0

    @contextlib.contextmanager
    def driver_case(name):
        directory = output / name
        directory.mkdir()
        driver = Driver(executable, directory, server)
        try:
            yield driver
        finally:
            driver.close()

    def success(name):
        nonlocal passed
        passed += 1
        print("PASS: " + name, flush=True)

    try:
        new = catalogue("updated")
        good = manifest(server, new)
        server.set("/payload", body=new)
        server.set("/feed", body={**good, "revision": 1, "files": []})
        with driver_case("current") as driver:
            assert_phase(driver.call("check"), "current")
            assert driver.call("read")["content"] == driver.bundled
        success("current manifest keeps the bundled database")

        with driver_case("fresh-setup-bundled-snapshot") as driver:
            (driver.root / "content/catalog.json").write_bytes(new)
            server.set("/feed", body=good)
            hits=server.hits["/payload"]
            assert_phase(driver.call("check"), "available")
            result=driver.call("install")
            assert_phase(result, "ready")
            assert result["state"]["total_bytes"] == result["state"]["downloaded_bytes"] == 0
            assert server.hits["/payload"] == hits
            driver.call("configure")
            assert driver.call("read")["content"] == new.decode()
            assert_phase(driver.call("check"), "current")
        success("a fresh installation mounts its verified bundled snapshot without downloading it again or offering the same update")

        server.set("/feed", body=good)
        with driver_case("activate-reuse-offline") as driver:
            available = driver.call("check")
            assert_phase(available, "available")
            assert available["state"]["notes"]["it"] == "Una nuova storia."
            assert_phase(driver.call("install"), "ready")
            assert driver.call("read")["content"] == driver.bundled
            assert (driver.data / "preferences.json").read_text() == '{"language":"it"}'
            assert (driver.data / "trophies-v1.dat").read_bytes() == b"trophy-sentinel"
            driver.call("configure")
            assert driver.call("read")["content"] == new.decode()
            assert driver.call("read", path="content/catalog.json.bak")["content"] == "sibling"
            success("a verified update activates only on the next configure and preserves preferences, trophies and sibling reads")
            hits = server.hits["/payload"]
            server.set("/feed", body=manifest(server, new, revision=3))
            assert_phase(driver.call("check"), "available")
            reused = driver.call("install")
            assert_phase(reused, "ready")
            assert reused["state"]["total_bytes"] == reused["state"]["downloaded_bytes"] == 0
            assert server.hits["/payload"] == hits
            driver.call("configure")
            assert driver.call("snapshot")["state"]["current_revision"] == 3
            success("an already verified content blob is reused without another HTTP download")
            pointer = (driver.data / "database/active.json").read_bytes()
            changed = catalogue("wrong!!")
            bad = manifest(server, changed, revision=4, url="/bad-hash")
            bad["files"][0]["sha256"] = "0" * 64
            server.set("/feed", body=bad)
            server.set("/bad-hash", body=changed)
            assert_phase(driver.call("check"), "available")
            assert_phase(driver.call("install"), "failed")
            assert (driver.data / "database/active.json").read_bytes() == pointer
            driver.call("configure")
            assert driver.call("read")["content"] == new.decode()
            success("a failed content hash leaves the prior active pointer and readable snapshot unchanged")
            server.set("/feed", status=503, body=b"offline")
            assert_phase(driver.call("check"), "failed")
            assert driver.call("read")["content"] == new.decode()
            assert (driver.data / "database/active.json").read_bytes() == pointer
            success("offline checking retains the previously activated content")
            blob = driver.data / "database/blobs" / hashlib.sha256(new).hexdigest()
            blob.write_bytes(catalogue("tamper!"))
            assert blob.stat().st_size == len(new)
            driver.call("configure")
            assert driver.call("read")["content"] == driver.bundled
            success("same-size corruption is rejected before any saved overlay is mounted")

        with driver_case("cumulative") as driver:
            server.set("/feed", body=good)
            assert_phase(driver.call("check"), "available")
            assert_phase(driver.call("install"), "ready")
            driver.call("configure")
            prior_hits = server.hits["/payload"]
            artwork = b"fixture bytes for an image"
            server.set("/new-art", body=artwork)
            merged = manifest(server, artwork, revision=8, path="assets/image-supplements/a.png", url="/new-art")
            merged["files"].append(good["files"][0])
            merged["files"].append(dict(merged["files"][0], path="assets/image-supplements/b.png"))
            server.set("/feed", body=merged)
            assert_phase(driver.call("check"), "available")
            assert driver.call("install_async")["ok"]
            limit = time.monotonic() + 10
            while (state := driver.call("snapshot")["state"])["phase"] == "downloading":
                assert state["total_bytes"] in (0, len(artwork)) and state["downloaded_bytes"] <= len(artwork)
                assert time.monotonic() < limit
                time.sleep(.01)
            assert state["phase"] == "ready" and state["revision"] == 8, state
            assert state["total_bytes"] == state["downloaded_bytes"] == len(artwork), state
            assert server.hits["/payload"] == prior_hits and server.hits["/new-art"] == 1
            driver.call("configure")
            assert driver.call("snapshot")["state"]["current_revision"] == 8
            assert driver.call("read", path="assets/image-supplements/a.png")["content"] == artwork.decode()
            assert driver.call("read", path="assets/image-supplements/b.png")["content"] == artwork.decode()
        success("a skipped revision uses one cumulative download total with cached and aliased blobs counted correctly")

        batch = {**good, "files": []}
        for index in range(12):
            payload = f"asset {index}".encode()
            url = f"/parallel-{index}"
            path = f"assets/image-supplements/parallel-{index}.png"
            batch["files"].extend(manifest(server, payload, path=path, url=url)["files"])
            server.set(url, body=payload, delay=.15)
        server.set("/feed", body=batch)
        with driver_case("parallel") as driver:
            assert_phase(driver.call("check"), "available")
            assert driver.call("install_async")["ok"]
            total = sum(row["bytes"] for row in batch["files"])
            downloaded = 0
            limit = time.monotonic() + 10
            while (state := driver.call("snapshot")["state"])["phase"] == "downloading":
                assert state["total_bytes"] in (0, total)
                assert downloaded <= state["downloaded_bytes"] <= total
                downloaded = state["downloaded_bytes"]
                assert time.monotonic() < limit
                time.sleep(.01)
            assert state["phase"] == "ready" and state["downloaded_bytes"] == total, state
            assert 1 < server.parallel_peak <= 4, server.parallel_peak
            driver.call("configure")
            for index in range(12):
                assert driver.call("read", path=batch["files"][index]["path"])["content"] == f"asset {index}"
        success("bounded parallel transfers report one monotonic byte count and mount all verified files")

        bad_batch = copy.deepcopy(batch)
        bad_batch["files"][0]["sha256"] = "0" * 64
        server.set("/feed", body=bad_batch)
        with driver_case("parallel-failure") as driver:
            assert_phase(driver.call("check"), "available")
            assert_phase(driver.call("install"), "failed")
            assert not (driver.data / "database/active.json").exists()
            assert not list((driver.data / "database/blobs").glob("*.part"))
            assert driver.call("read")["content"] == driver.bundled
            server.set("/feed", body=batch)
            assert_phase(driver.call("check"), "available")
            assert_phase(driver.call("install"), "ready")
        success("a parallel verification failure leaves the old database active and allows a clean retry")

        malformed = []
        for path in ("../escaped.json", "content/../escaped.json", "Pixel Museum.exe", "assets/image-supplements/code.exe", "/content/catalog.json", "C:/content/catalog.json", "content\\catalog.json"):
            row = copy.deepcopy(good);row["files"][0]["path"] = path;malformed.append(("path " + path, row))
        for url in ("file:///tmp/update.json", "http://evil.invalid/file", "https://github.com/other/project/file", "javascript:alert(1)"):
            row = copy.deepcopy(good);row["files"][0]["url"] = url;malformed.append(("URL " + url, row))
        for key, value in (("schema_version", True), ("revision", "2"), ("version", []), ("files", {}), ("notes", []), ("minimum_reader", "1")):
            row = copy.deepcopy(good);row[key] = value;malformed.append(("type " + key, row))
        for key, value in (("path", 2), ("url", []), ("sha256", {}), ("bytes", "18"), ("bytes", -1)):
            row = copy.deepcopy(good);row["files"][0][key] = value;malformed.append(("file type " + key, row))
        with driver_case("malformed") as driver:
            for name, row in malformed:
                server.set("/feed", body=row)
                assert_phase(driver.call("check"), "failed")
                assert driver.call("read")["content"] == driver.bundled, name
            assert not (driver.data / "database/active.json").exists()
        success(f"{len(malformed)} traversal, executable, unsafe URL and malformed-type feeds fail without aborting")

        invalid_content = [
            ("json-type", "content/catalog.json", b"[]"),
            ("empty-catalogue", "content/catalog.json", b"{}"),
            ("empty-entries", "content/catalog.json", b'{"entries":[]}'),
            ("bad-locale", "content/locales/it.json", b'{"locale":"en","entries":{}}'),
            ("bad-ui-locale", "content/ui-locales/it.json", b'{"locale":"en","strings":{}}'),
        ]
        for name, path, invalid in invalid_content:
            for cached in (False, True):
                server.set("/feed", body=manifest(server, invalid, path=path))
                server.set("/payload", body=invalid)
                with driver_case(name + ("-cached" if cached else "-fresh")) as driver:
                    if cached:
                        blobs = driver.data / "database/blobs";blobs.mkdir(parents=True)
                        (blobs / hashlib.sha256(invalid).hexdigest()).write_bytes(invalid)
                    assert_phase(driver.call("check"), "available")
                    assert_phase(driver.call("install"), "failed")
                    assert not (driver.data / "database/active.json").exists()
                    assert driver.call("read")["content"] == driver.bundled
                success("a " + ("reused" if cached else "fresh") + " " + name + " blob is rejected without activating content")

        large = catalogue("updated", padding="x" * 131072)
        server.set("/feed", body=manifest(server, large, url="/interrupted"))
        server.set("/interrupted", body=large[:4096], length=len(large))
        with driver_case("interrupted") as driver:
            assert_phase(driver.call("check"), "available")
            assert_phase(driver.call("install"), "failed")
            assert not (driver.data / "database/active.json").exists()
            assert not list((driver.data / "database/blobs").glob("*.part"))
        success("an interrupted transfer never commits an active snapshot and removes its partial file")

        server.set("/feed", body=manifest(server, large, url="/slow"))
        server.set("/slow", body=large, slow=True)
        with driver_case("cancelled") as driver:
            assert_phase(driver.call("check"), "available")
            assert driver.call("install_async")["ok"]
            deadline = time.monotonic() + 5
            while driver.call("snapshot")["state"]["downloaded_bytes"] == 0:
                assert time.monotonic() < deadline
                time.sleep(0.01)
            driver.call("shutdown")
            assert not (driver.data / "database/active.json").exists()
            assert driver.call("read")["content"] == driver.bundled
        success("cooperative shutdown interrupts an update without committing or changing current reads")
    finally:
        server.close()
    print(f"{passed} database integration checks passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("driver", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=False)
        run(args.driver.resolve(), args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="pixelmuseum-database-") as temp:
            run(args.driver.resolve(), pathlib.Path(temp))
