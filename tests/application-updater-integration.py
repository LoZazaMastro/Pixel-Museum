"""Real Windows update downloader against isolated loopback release fixtures.

Never starts the apply helper or contacts a production update feed.
"""
from __future__ import annotations
import argparse, collections, copy, hashlib, http.server, io, json, os
from pathlib import Path
import subprocess, tempfile, threading, time, zipfile


class Server:
    def __init__(self):
        self.routes = {}; self.hits = collections.Counter(); self.ranges = []
        owner = self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self):
                owner.hits[self.path] += 1
                route = dict(owner.routes.get(self.path, {"body": b"missing", "status": 404}))
                body = route.get("body", b"")
                if isinstance(body, dict): body = json.dumps(body).encode()
                status = route.get("status", 200); total = len(body)
                byte_range = self.headers.get("Range")
                if byte_range:
                    owner.ranges.append(byte_range)
                    if not route.get("ignore_range"):
                        at = int(byte_range.removeprefix("bytes=").rstrip("-"))
                        body = body[at:]; status = 206
                self.send_response(status)
                self.send_header("Content-Length", str(route.get("length", len(body))))
                if status == 206: self.send_header("Content-Range", f"bytes {total-len(body)}-{total-1}/{total}")
                self.send_header("Connection", "close"); self.end_headers()
                try:
                    for at in range(0, len(body), route.get("chunk", max(1, len(body)))):
                        self.wfile.write(body[at:at+route.get("chunk", len(body))]); self.wfile.flush()
                        if route.get("delay"): time.sleep(route["delay"])
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass
                self.close_connection = True
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
    def close(self): self.server.shutdown(); self.server.server_close(); self.thread.join()


class Driver:
    def __init__(self, executable, root, data, source):
        root.mkdir(parents=True, exist_ok=True); data.mkdir(parents=True, exist_ok=True)
        self.root, self.data = root, data
        self.process = subprocess.Popen([str(executable), str(root), str(data), source], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf8")
    def call(self, op, **fields):
        self.process.stdin.write(json.dumps({"op": op, **fields})+"\n"); self.process.stdin.flush()
        line = self.process.stdout.readline()
        assert line, self.process.stderr.read()
        return json.loads(line)
    def close(self):
        self.process.stdin.close(); self.process.wait(timeout=12)
        assert self.process.returncode == 0, self.process.stderr.read()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--driver", type=Path, required=True); parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(); args.directory.mkdir(parents=True, exist_ok=True)
    server = Server(); passed = []
    def good(name): passed.append(name); print("PASS", name, flush=True)
    try:
        # A real ZIP with incompressible bytes keeps interruption/resume observable.
        raw = io.BytesIO()
        with zipfile.ZipFile(raw, "w", zipfile.ZIP_STORED) as z:
            z.writestr("Pixel Museum.exe", b"MZ"+bytes(range(256))*8192)
        payload = raw.getvalue(); sha = hashlib.sha256(payload).hexdigest()
        release = {"version": "0.2.1", "available": True, "url": server.base+"/app.zip", "sha256": sha, "bytes": len(payload), "unpacked_bytes": len(payload)+4096, "notes": {"it": "Aggiornamento di prova"}}
        def feed(row=None): return {"schema_version": 1, "application_id": "pixel-museum", "platforms": {"windows-x64": copy.deepcopy(release if row is None else row)}}
        server.routes["/feed.json"] = {"body": feed()}; server.routes["/app.zip"] = {"body": payload}
        with tempfile.TemporaryDirectory(prefix="app-updater-", dir=args.directory.resolve()) as directory:
            base = Path(directory)
            def create(name, source=None, same=False):
                root = base/name/"app"; data = root if same else base/name/"data"
                d = Driver(args.driver.resolve(), root, data, source or server.base+"/feed.json")
                assert d.call("configure")["ok"]
                return d
            d = create("versions")
            cases = [("0.2.1", "0.2.0", True), ("0.2.0", "0.2.0-preview", True), ("0.2.0-preview.2", "0.2.0-preview.1", True), ("0.2.0-preview.10", "0.2.0-preview.2", True), ("0.2.0-preview", "0.2.0", False), ("0.2.0+new", "0.2.0+old", False), ("0.1.99", "0.2.0", False), ("v1.0.0", "0.9.9", True), ("1.2", "1.0.0", False), ("1.02.3", "1.0.0", False), ("1.2.3-01", "1.2.3-0", False), ("1.2.3-", "1.2.2", False), ("1.2.3-alpha.1", "1.2.3-alpha", True), ("1.2.3-beta", "1.2.3-alpha.9", True)]
            for candidate, current, result in cases: assert d.call("newer", candidate=candidate, current=current)["newer"] == result, (candidate, current)
            d.close(); good("semantic version ordering, prereleases, build metadata and malformed versions")
            d = create("current")
            before = server.hits["/app.zip"]
            for current in ["0.2.1", "0.3.0", "1.0.0"]:
                assert d.call("configure", current=current)["ok"]
                assert d.call("check")["state"]["phase"] == "current"
            row = {"version": "0.2.0-preview", "available": False}; server.routes["/feed.json"] = {"body": feed(row)}
            assert d.call("configure")["ok"] and d.call("check")["state"]["phase"] == "current"
            assert server.hits["/app.zip"] == before; d.close(); good("equal, older and unavailable releases never download or downgrade")
            server.routes["/feed.json"] = {"body": feed()}; d = create("valid")
            (d.root/"Pixel Museum.exe").write_bytes(b"old program"); (d.data/"preferences.json").write_text('{"keep":true}'); (d.data/"trophies.json").write_text('{"trophy":1}')
            assert d.call("check")["state"]["phase"] == "available"
            before = server.hits["/app.zip"]
            assert d.call("install")["state"]["phase"] == "ready"
            target = d.data/"application-updates/payloads"/(sha+".zip")
            assert target.read_bytes() == payload
            assert d.call("install")["state"]["phase"] == "ready" and server.hits["/app.zip"] == before+1
            assert (d.root/"Pixel Museum.exe").read_bytes() == b"old program"
            assert (d.data/"preferences.json").read_text() == '{"keep":true}' and (d.data/"trophies.json").read_text() == '{"trophy":1}'
            assert not d.call("restart")["ok"]  # A separate data fixture is not an installed app.
            d.close(); good("verified payload, cached reuse and zero replacement before safe restart")
            bad_feeds = [{}, {"platforms": []}]
            for key, value in [("version", "9.invalid"), ("available", "yes"), ("bytes", True), ("bytes", 0), ("bytes", 2**31), ("unpacked_bytes", 2**32+1), ("sha256", "x"*64), ("url", "https://github.com/attacker/release.zip"), ("url", "https://github.com/LoZazaMastro/Pixel-Museum.evil/releases/download/x"), ("notes", []), ("notes", {"it": []})]:
                row = copy.deepcopy(release); row[key] = value; bad_feeds.append(feed(row))
            d = create("invalid"); before = server.hits["/app.zip"]
            for item in bad_feeds:
                server.routes["/feed.json"] = {"body": item}
                assert d.call("check")["state"]["phase"] == "failed", item
            assert server.hits["/app.zip"] == before; d.close(); good(f"{len(bad_feeds)} malformed or untrusted manifests rejected before payload access")
            server.routes["/feed.json"] = {"body": feed()}; server.routes["/app.zip"] = {"body": payload[:-1]+b"X"}
            d = create("hash"); d.call("check"); assert d.call("install")["state"]["phase"] == "failed"
            assert not (d.data/"application-updates/payloads"/(sha+".zip")).exists(); d.close(); good("same-size checksum failure never becomes ready")
            server.routes["/app.zip"] = {"body": payload[:32768], "length": len(payload)}
            d = create("resume"); d.call("check"); assert d.call("install")["state"]["phase"] == "failed"
            partial = d.data/"application-updates/payloads"/(sha+".zip.part"); assert partial.stat().st_size == 32768
            server.routes["/app.zip"] = {"body": payload}
            assert d.call("install")["state"]["phase"] == "ready" and server.ranges[-1] == "bytes=32768-"
            d.close(); good("interrupted download resumes with byte ranges and verifies the full digest")
            server.routes["/app.zip"] = {"body": payload[:32768], "length": len(payload)}
            d = create("ignored-range"); d.call("check"); d.call("install")
            server.routes["/app.zip"] = {"body": payload, "ignore_range": True}
            assert d.call("install")["state"]["phase"] == "failed"
            assert not (d.data/"application-updates/payloads"/(sha+".zip")).exists()
            server.routes["/app.zip"] = {"body": payload}; assert d.call("install")["state"]["phase"] == "ready"
            d.close(); good("ignored resume ranges are rejected, then clean retry succeeds")
            server.routes["/app.zip"] = {"body": payload, "chunk": 1024, "delay": .02}
            d = create("cancel"); d.call("check"); assert d.call("install_async")["ok"]; time.sleep(.1)
            start = time.monotonic(); d.call("shutdown"); assert time.monotonic()-start < 2
            assert not (d.data/"application-updates/payloads"/(sha+".zip")).exists()
            d.close(); good("cooperative cancellation leaves only an uncommitted partial payload")
            server.routes["/app.zip"] = {"body": payload}; d = create("cached-corruption"); d.call("check"); d.call("install")
            target = d.data/"application-updates/payloads"/(sha+".zip"); corrupted = bytearray(target.read_bytes()); corrupted[-1] ^= 1; target.write_bytes(corrupted)
            before = server.hits["/app.zip"]; assert d.call("install")["state"]["phase"] == "ready" and server.hits["/app.zip"] == before+1
            d.close(); good("corrupt cached ZIP is re-fetched rather than trusted by size")
            d = create("helper-missing", same=True); (d.root/"Pixel Museum.exe").write_bytes(b"old"); (d.root/"pixel-museum-install.json").write_text('{}')
            d.call("check"); d.call("install"); out = d.call("restart"); assert not out["ok"] and out["state"]["phase"] == "failed"
            assert (d.root/"Pixel Museum.exe").read_bytes() == b"old"; d.close(); good("missing apply helper keeps the old application running and unchanged")
        print(json.dumps({"passed": len(passed), "failed": 0, "checks": passed}, indent=2))
    finally: server.close()


if __name__ == "__main__": main()
