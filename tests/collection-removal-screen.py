"""Run the real Screen removal flow on a tiny, isolated installed collection.

The miniature app has fonts but no bundled image collection. Its only download
URL points to closed loopback port 1; no production asset is read or removed.
Build the host preview first, then run this file from WSL with host-env.sh.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'build/research/collection-removal-0.1.4'
REPORT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='pm-screen-collection-removal-', dir='/tmp') as temporary:
    folder = Path(temporary)
    app, data = folder / 'app', folder / 'data'
    (app / 'assets').mkdir(parents=True)
    (app / 'content').mkdir()
    data.mkdir()
    (app / 'assets/fonts').symlink_to(ROOT / 'dist/PPSA70421/assets/fonts', target_is_directory=True)
    (app / 'content/ui-locales').symlink_to(ROOT / 'content/ui-locales', target_is_directory=True)
    entry = {'id': 'fixture-game', 'title': 'Removal fixture', 'year': 2000,
             'kind': 'game', 'summary': 'An isolated test fixture.',
             'body': ['A real Screen fixture.'], 'story_headings': ['The fixture'],
             'images': [{'url': 'https://fixture.invalid/cover.png', 'title': 'Fixture'}]}
    catalog = json.dumps({'initial_id': entry['id'], 'entries': [entry]})
    (app / 'content/catalog.json').write_text(catalog)
    (app / 'content/human-history.json').write_text(catalog)
    image_path = 'assets/images/full/fixture.png'
    picture = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j8V8AAAAASUVORK5CYII=')
    index = json.dumps({'images': {'https://fixture.invalid/cover.png': image_path}}).encode()
    index_hash = hashlib.sha256(index).hexdigest()
    pack_hash = 'a' * 64
    manifest = json.dumps({'schema_version': 1, 'collection_id': 'screen-removal-fixture',
        'image_manifest_sha256': index_hash, 'packs': [{'id': 'one',
        'url': 'https://127.0.0.1:1/never-requested.tar', 'sha256': pack_hash,
        'bytes': 10240, 'format': 'tar', 'file_count': 2,
        'expanded_bytes': len(index) + len(picture)}]})
    (app / 'content/collection-packs.json').write_text(manifest)
    manifest_hash = hashlib.sha256(manifest.encode()).hexdigest()
    ready = data / 'collection' / ('screen-removal-fixture-' + manifest_hash[:24])
    (ready / 'assets/images/full').mkdir(parents=True)
    (ready / image_path).write_bytes(picture)
    (ready / 'assets/images/manifest.json').write_bytes(index)
    (ready / '.pack-0.json').write_text(json.dumps({'sha256': pack_hash, 'files': [
        {'path': 'assets/images/manifest.json', 'bytes': len(index)},
        {'path': image_path, 'bytes': len(picture)}]}))
    (ready / '.complete.json').write_text(json.dumps({'manifest_sha256': manifest_hash,
                                                     'image_manifest_sha256': index_hash}))
    (data / 'collection/downloads').mkdir()
    (data / 'collection/downloads/unfinished.part').write_bytes(b'partial')
    (data / 'trophy-preservation-sentinel.bin').write_text('trophies-preserved')
    (data / 'preferences.json').write_text(json.dumps({'language': 'en', 'language_chosen': True,
        'theme_chosen': True, 'onboarding_complete': True, 'master_volume': .73,
        'music_volume': .31, 'culture_volume': .62}))
    env = os.environ | {'MUSEUM_PREVIEW_ROOT': str(app), 'MUSEUM_TEST_REMOVAL_DATA': str(data)}
    result = subprocess.run([str(ROOT / 'build/pixelmuseum-preview'), 'collection-removal'],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
    (REPORT / 'screen.log').write_text(result.stdout + result.stderr)
    print(result.stdout + result.stderr)
    report = {'status': 'PASS' if result.returncode == 0 else 'FAIL',
              'exit_code': result.returncode, 'production_data_touched': False,
              'production_urls_requested': False}
    (REPORT / 'screen.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    raise SystemExit(result.returncode)
