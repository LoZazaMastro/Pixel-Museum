"""Windows setup-owned archive mount, no-download failures and removal guards.

Only freshly created fixtures below build/windows-collection-check are removed.
No existing application collection, user settings or external network is used.
"""
from pathlib import Path
import hashlib
import http.server
import io
import json
import os
import subprocess
import tarfile
import threading
import uuid

if os.name != "nt":
    print("SKIP native Windows collection fixture")
    raise SystemExit(0)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build/windows-collection-check"
OUTPUT.mkdir(parents=True, exist_ok=True)
FIXTURES = OUTPUT / ("f-" + uuid.uuid4().hex[:8])
assert not FIXTURES.exists()
FIXTURES.mkdir()
# Every recursive deletion issued by the tested worker is scoped to this new
# absolute workspace directory. Retain fixtures and the report for inspection.
assert FIXTURES.resolve().is_relative_to((ROOT / "build").resolve())
PREFIX = Path(os.environ.get("PM_MINGW_PREFIX", "C:/msys64/mingw64"))
environment = dict(os.environ)
environment["PATH"] = str(PREFIX / "bin") + os.pathsep + environment.get("PATH", "")
BINARY = OUTPUT / "collection-installer-windows.exe"
subprocess.run([
    str(PREFIX / "bin/g++.exe"), "-std=c++20", "-O2", "-DMUSEUM_WINDOWS=1",
    "-DNOMINMAX", "-DWIN32_LEAN_AND_MEAN", "-DJSON_NOEXCEPTION=1",
    "-Wno-deprecated-declarations", "-include", str(ROOT / "src/platform/windows/compat.hpp"),
    "-I" + str(ROOT / "src"), "-I" + str(ROOT),
    str(ROOT / "tests/collection-installer-windows.cpp"),
    str(ROOT / "src/museum/collection_installer.cpp"),
    "-o", str(BINARY), "-lcurl", "-lwinpthread", "-lws2_32",
], check=True, env=environment)


class Handler(http.server.BaseHTTPRequestHandler):
    payload = {}
    requests = []

    def log_message(self, *_):
        pass

    def do_GET(self):
        data = self.payload[self.path]
        header = self.headers.get("Range")
        start = int(header.split("=")[1].split("-")[0]) if header else 0
        self.requests.append((self.path, header))
        self.send_response(206 if header else 200)
        self.send_header("Content-Length", str(len(data) - start))
        if header:
            self.send_header("Content-Range", f"bytes {start}-{len(data)-1}/{len(data)}")
        self.end_headers()
        self.wfile.write(data[start:])


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
results = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text(path, value="keep"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def fixture(name):
    folder = FIXTURES / name
    bundle = folder / "install"
    registry = b'{"images":{}}'
    # Includes CRLF and Ctrl-Z to detect accidental CRT text-mode I/O.
    picture = bytes(range(256)) * 4097 + b"\r\n\x1a\r\n"
    buffer = io.BytesIO()
    files = [("assets/images/manifest.json", registry), ("assets/images/native.bin", picture)]
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for path, data in files:
            info = tarfile.TarInfo(path)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    payload = buffer.getvalue()
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        records = [{"path": item.name, "offset": item.offset_data, "bytes": item.size} for item in archive.getmembers()]
    url = "/" + name + ".tar"
    Handler.payload[url] = payload
    pack = {"id": "native", "url": f"http://127.0.0.1:{server.server_port}{url}",
            "sha256": sha(payload), "bytes": len(payload), "format": "tar",
            "file_count": len(files), "expanded_bytes": sum(len(data) for _, data in files)}
    manifest = {"schema_version": 1, "collection_id": "windows-fixture", "image_manifest_sha256": sha(registry),
                "expanded_bytes": pack["expanded_bytes"], "file_count": len(files), "packs": [pack]}
    index = {"schema_version": 1, "collection_id": "windows-fixture", "image_manifest_sha256": sha(registry),
             "packs": [{key: pack[key] for key in ("id", "sha256", "bytes")} | {"files": records}]}
    manifest_path = bundle / "content/collection-packs.json"
    text(manifest_path, json.dumps(manifest))
    text(bundle / "content/collection-archive-index.json", json.dumps(index))
    registry_path = bundle / "assets/images/manifest.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_bytes(registry)
    text(bundle / "settings.json", '{"keep":"user settings"}')
    text(folder / "outside/keep.bin", "outside sentinel")
    return {"folder": folder, "bundle": bundle, "manifest": manifest_path, "payload": payload, "registry": registry, "pack": pack}


def setup_resources(fixture):
    """Publish the exact verified receipts/layout produced by Windows Setup."""
    manifest_sha = sha(fixture["manifest"].read_bytes())
    ready = fixture["bundle"] / "collection" / ("windows-fixture-" + manifest_sha[:24])
    archive = ready / "archives" / (fixture["pack"]["sha256"] + ".tar")
    archive.parent.mkdir(parents=True)
    archive.write_bytes(fixture["payload"])
    (ready / "assets/images").mkdir(parents=True)
    (ready / "assets/images/manifest.json").write_bytes(fixture["registry"])
    text(ready / ".complete.json", json.dumps({"schema_version": 1, "manifest_sha256": manifest_sha,
         "image_manifest_sha256": sha(fixture["registry"]), "pack_count": 1}))
    text(ready / ".pack-0.json", json.dumps({"sha256": fixture["pack"]["sha256"], "storage": "archive",
         "archive": "archives/" + archive.name, "bytes": len(fixture["payload"])}))
    return ready, archive


def invoke(case, fixture, command="install", data=None, bundle=None):
    data = data or fixture["bundle"]
    assert data.absolute().is_relative_to(FIXTURES.absolute())
    process = subprocess.run([str(BINARY), fixture["manifest"].as_posix(), data.as_posix(),
                              (bundle or fixture["bundle"]).as_posix(), command],
                             capture_output=True, text=True, timeout=20, env=environment)
    assert process.returncode == 0, (case, process.stdout, process.stderr)
    value = json.loads(process.stdout.strip().splitlines()[-1])
    results.append({"case": case, "result": value})
    print(case, value)
    assert (fixture["bundle"] / "settings.json").read_text() == '{"keep":"user settings"}'
    assert (fixture["folder"] / "outside/keep.bin").read_text() == "outside sentinel"
    assert (fixture["bundle"] / "assets/images/manifest.json").read_bytes() == fixture["registry"]
    return value


def junction(link, target):
    assert link.absolute().is_relative_to(FIXTURES.absolute()) and not link.exists()
    assert target.resolve().is_relative_to(FIXTURES.resolve())
    link.parent.mkdir(parents=True, exist_ok=True)
    quote = lambda path: "'" + str(path).replace("'", "''") + "'"
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"New-Item -ItemType Junction -Path {quote(link)} -Target {quote(target)} | Out-Null"],
                   check=True, capture_output=True, text=True)


try:
    good = fixture("archive-lifecycle")
    setup_resources(good)
    value = invoke("quiet mount of resources installed by setup", good)
    assert value["ready"]
    ready = Path(value["root"])
    assert ready.resolve().is_relative_to((good["bundle"] / "collection").resolve())
    archives = list((ready / "archives").glob("*.tar"))
    assert len(archives) == 1 and archives[0].read_bytes() == good["payload"]
    assert not (ready / "assets/images/native.bin").exists()
    before = len(Handler.requests)
    assert invoke("completed archive opens offline", good)["ready"]
    assert len(Handler.requests) == before
    text(good["bundle"] / "collection/downloads/leftover.part", "owned partial")
    assert invoke("remove only owned collection tree", good, "remove")["removed"]
    assert not (good["bundle"] / "collection").exists()
    assert invoke("missing collection removal is idempotent", good, "remove")["removed"]
    setup_resources(good)
    assert invoke("mount after setup reinstalls removed resources", good)["ready"]
    assert len(Handler.requests) == before == 0

    missing = fixture("missing-resources")
    value = invoke("missing archives fail without creating or downloading resources", missing)
    assert value["failed"] and "Setup" in value["error"] and not (missing["bundle"] / "collection").exists()

    truncated = fixture("truncated-archive")
    _, archive = setup_resources(truncated)
    archive.write_bytes(truncated["payload"][:-1])
    value = invoke("truncated archive requests setup repair without HTTP", truncated)
    assert value["failed"] and "Setup" in value["error"]
    assert archive.stat().st_size == len(truncated["payload"])-1

    receipt = fixture("invalid-receipt")
    ready, _ = setup_resources(receipt)
    text(ready / ".complete.json", json.dumps({"schema_version": 1, "manifest_sha256": "0" * 64,
         "image_manifest_sha256": sha(receipt["registry"]), "pack_count": 1}))
    assert invoke("invalid setup receipt fails without HTTP", receipt)["failed"]

    nested = fixture("nested-junction")
    text(nested["bundle"] / "collection/owned.keep")
    junction(nested["bundle"] / "collection/link", nested["folder"] / "outside")
    assert invoke("reject nested reparse before deleting owned files", nested, "remove")["failed"]
    assert (nested["bundle"] / "collection/owned.keep").exists()

    redirected = fixture("root-junction")
    junction(redirected["bundle"] / "collection", redirected["folder"] / "outside")
    assert invoke("reject redirected collection root", redirected, "remove")["failed"]
    assert (redirected["bundle"] / "collection").is_dir()

    ancestor = fixture("ancestor-junction")
    text(ancestor["folder"] / "outside/data/collection/owned.keep")
    junction(ancestor["folder"] / "alias", ancestor["folder"] / "outside")
    assert invoke("reject reparse ancestor of configured collection", ancestor, "remove",
                  data=ancestor["folder"] / "alias/data")["failed"]
    assert (ancestor["folder"] / "outside/data/collection/owned.keep").exists()

    contained = fixture("bundle-containment")
    text(contained["bundle"] / "collection/owned.keep")
    assert invoke("refuse target containing application bundle", contained, "remove",
                  bundle=contained["bundle"] / "collection/app")["failed"]
    assert (contained["bundle"] / "collection/owned.keep").exists()
    assert not Handler.requests, Handler.requests
finally:
    server.shutdown()
report = {"status": "PASS", "cases": results, "request_count": len(Handler.requests),
          "external_network": False, "fixtures": str(FIXTURES)}
(OUTPUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("PASS", len(results), "native Windows collection cases; fixture artifacts retained at", FIXTURES)
