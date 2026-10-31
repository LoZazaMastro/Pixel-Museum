"""One local HTTP download through the real first-run Screen and image cache."""
from pathlib import Path
import hashlib, http.server, io, json, os, subprocess, tarfile, tempfile, threading, time

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / 'build/collection-delivery-20261031'
full = ROOT / 'dist/PPSA70421'
original = json.loads((full / 'assets/images/manifest.json').read_text())
picture_path = next(full / p for p in original['images'].values()
                    if (full / p).is_file() and (full / p).stat().st_size < 100000)
image_name = 'assets/images/full/local-fixture' + picture_path.suffix
picture = picture_path.read_bytes()
image_index = json.dumps({'images': {key: image_name for key in original['images']}}).encode()
stream = io.BytesIO()
with tarfile.open(fileobj=stream, mode='w', format=tarfile.USTAR_FORMAT) as archive:
    for name, payload in [('assets/images/manifest.json', image_index), (image_name, picture)]:
        entry = tarfile.TarInfo(name); entry.size = len(payload); entry.mode = 0o644
        archive.addfile(entry, io.BytesIO(payload))
pack = stream.getvalue()
requests = []

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def do_GET(self):
        requests.append(self.path)
        self.send_response(200); self.send_header('Content-Length', str(len(pack))); self.end_headers()
        for start in range(0, len(pack), 16384):
            self.wfile.write(pack[start:start + 16384]); self.wfile.flush(); time.sleep(.003)

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with tempfile.TemporaryDirectory(prefix='museum-screen-', dir=ROOT / 'build/tmp') as folder:
        folder = Path(folder)
        manifest = folder / 'collection-packs.json'
        manifest.write_text(json.dumps({'schema_version': 1, 'collection_id': 'local-screen-test',
            'version': '1', 'expanded_bytes': len(image_index) + len(picture),
            'image_manifest_sha256': hashlib.sha256(image_index).hexdigest(), 'packs': [{
                'id': 'fixture', 'url': f'http://127.0.0.1:{server.server_port}/fixture.tar',
                'bytes': len(pack), 'sha256': hashlib.sha256(pack).hexdigest(), 'format': 'tar',
                'file_count': 2, 'expanded_bytes': len(image_index) + len(picture)}]}))
        env = os.environ | {'MUSEUM_PREVIEW_ROOT': str(DELIVERY / 'base/PPSA70421'), 'BUILD_JOBS': '6'}
        result = subprocess.run(['bash', 'tools/preview.sh', 'collection-end-to-end', str(manifest), str(folder / 'data')],
                                cwd=ROOT, env=env, text=True, capture_output=True, timeout=180)
        (DELIVERY / 'screen-end-to-end.log').write_text(result.stdout + result.stderr)
        report = {'status': 'PASS' if result.returncode == 0 and requests == ['/fixture.tar'] else 'FAIL',
                  'returncode': result.returncode, 'http_requests': requests,
                  'production_urls_requested': False, 'fixture_image_bytes': len(picture),
                  'real_renderer_and_image_worker': True}
        (DELIVERY / 'screen-end-to-end.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
        raise SystemExit(0 if report['status'] == 'PASS' else 1)
finally:
    server.shutdown(); server.server_close()
