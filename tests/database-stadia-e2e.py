"""Exercise the real database writer, production catalogue reader and native UI.

Payload bytes and production URLs remain unchanged. A bounded test-only curl
adapter directs those exact URLs to a loopback HTTP fixture before publication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pathlib
import queue
import shutil
import subprocess
import threading
import time
from importlib.machinery import SourceFileLoader

fixtures_module = SourceFileLoader('database_fixtures', str(pathlib.Path(__file__).with_name('database-updater-integration.py'))).load_module()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class Protocol:
    def __init__(self, driver, root, data, feed, mapping, log):
        self.stderr = log.open('wb')
        command = [str(driver), str(root), str(data), feed]
        if mapping:
            command.append(str(mapping))
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, text=True, encoding='utf-8', bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW)
        self.queue = queue.Queue()
        threading.Thread(target=lambda: [self.queue.put(line) for line in self.process.stdout], daemon=True).start()

    def call(self, op, **kwargs):
        self.process.stdin.write(json.dumps(dict(op=op, **kwargs)) + '\n')
        self.process.stdin.flush()
        result = json.loads(self.queue.get(timeout=120))
        assert result.get('ok'), result
        assert 'driver_error' not in result, result
        return result

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=30)
        self.stderr.close()
        assert self.process.returncode == 0, self.process.returncode


def clone_data(template, data):
    data.mkdir()
    count = 0
    for source in (template / 'collection').rglob('*'):
        target = data / 'collection' / source.relative_to(template / 'collection')
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix.lower() == '.tar':
                os.link(source, target)
                assert source.stat().st_ino == target.stat().st_ino
                count += 1
            else:
                shutil.copyfile(source, target)
    assert count == 12, count
    preferences = json.loads((template / 'preferences.json').read_bytes())
    preferences.update(language='it', language_chosen=True, theme_chosen=True, onboarding_complete=True, master_volume=0.0)
    (data / 'preferences.json').write_text(json.dumps(preferences, ensure_ascii=False), encoding='utf-8')
    source_trophies = template / 'trophies-v1.dat'
    if source_trophies.is_file():
        shutil.copyfile(source_trophies, data / 'trophies-v1.dat')
    else:
        (data / 'trophies-v1.dat').write_bytes(b'e2e-trophy-preservation-sentinel')


def run(args):
    root, stage, template, output, manifest_path, driver, exe = (pathlib.Path(value).resolve() for value in (args.root, args.stage, args.template, args.output, args.manifest, args.driver, args.exe))
    output.mkdir(parents=True, exist_ok=False)
    data = output / 'data'
    clone_data(template, data)
    report = {'root': str(root), 'data': str(data), 'manifest': str(manifest_path), 'checks': [], 'captures': []}
    protected = [root / 'content/catalog.json', template / 'preferences.json']
    source_catalogue = pathlib.Path(__file__).resolve().parent.parent / 'content/catalog.json'
    if source_catalogue.is_file():
        protected.append(source_catalogue)
    original = {str(path): digest(path) for path in protected}
    pref_digest, trophy_digest = digest(data / 'preferences.json'), digest(data / 'trophies-v1.dat')
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    document = json.loads((stage / 'content/catalog.json').read_bytes())
    expected = next(entry for entry in document['entries'] if entry['id'] == 'google-stadia')
    expected_gta = next(entry for entry in document['entries'] if entry['id'] == 'grand-theft-auto-vi')
    del document

    def passed(label):
        report['checks'].append(label)
        (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print('PASS: ' + label, flush=True)

    server = fixtures_module.Fixtures()
    transport = {}
    for index, row in enumerate(manifest['files']):
        payload = stage / row['path']
        assert payload.resolve().is_relative_to(stage) and payload.is_file() and not payload.is_symlink()
        assert payload.stat().st_size == row['bytes'] and digest(payload) == row['sha256'], row['path']
        assert row['url'].startswith('https://github.com/LoZazaMastro/Pixel-Museum/releases/download/')
        local_path = '/payload/' + str(index)
        server.set(local_path, body=payload.read_bytes())
        transport[row['url']] = server.base + local_path
    server.set('/feed', body=manifest_bytes)
    mapping = output / 'exact-url-loopback-map.json'
    mapping.write_text(json.dumps(transport, indent=2), encoding='utf-8')
    report.update(revision=manifest['revision'], version=manifest['version'], payload_count=len(manifest['files']), payload_bytes=sum(row['bytes'] for row in manifest['files']))
    passed('all staged payload bytes and SHA-256 values match the exact production manifest')
    process = Protocol(driver, root, data, server.base + '/feed', mapping, output / 'downloader-stderr.log')
    try:
        process.call('configure')
        before = process.call('resolved_digest')
        assert before['sha256'] == original[str(root / 'content/catalog.json')]
        assert process.call('catalogue_entry', id='google-stadia')['entry'] is None
        available = process.call('check')
        assert available['state']['phase'] == 'available', available
        process.call('install_async')
        deadline, shown = time.monotonic() + 240, -1
        while True:
            current = process.call('snapshot')['state']
            total = current['total_bytes']
            percentage = int(current['downloaded_bytes'] * 100 / total) if total else 0
            if percentage // 10 != shown:
                shown = percentage // 10
                print('DOWNLOAD: ' + str(percentage) + '%', flush=True)
            if current['phase'] not in ('checking', 'downloading'):
                assert current['phase'] == 'ready', current
                break
            assert time.monotonic() < deadline, current
            time.sleep(.05)
        report['installed_state'] = current
        assert process.call('resolved_digest')['sha256'] == before['sha256']
        assert process.call('catalogue_entry', id='google-stadia')['entry'] is None
        assert digest(data / 'preferences.json') == pref_digest and digest(data / 'trophies-v1.dat') == trophy_digest
        passed('production DatabaseUpdater downloads/verifies all files while the running reader still sees the unchanged baseline')
        passed('database installation preserves preference and trophy bytes')
    finally:
        process.close()
        server.close()

    # The ordinary production feed configuration must accept the committed
    # active pointer. No local URL or hand-written activation map is required.
    reader = Protocol(driver, root, data, 'https://lozazamastro.github.io/Pixel-Museum/database-update.json', None, output / 'reader-stderr.log')
    try:
        activated = reader.call('configure')
        assert activated['state']['current_revision'] == manifest['revision'], activated
        new = reader.call('resolved_digest')
        catalogue_row = next(row for row in manifest['files'] if row['path'] == 'content/catalog.json')
        assert new['sha256'] == catalogue_row['sha256'] and '/database/blobs/' in new['resolved']
        passed('a fresh production-feed process activates the committed snapshot without modifying the bundled catalogue')
        report['languages'] = {}
        for locale in ('en', 'it', 'es', 'fr', 'de'):
            actual = reader.call('catalogue_entry', locale=locale, id='google-stadia')['entry']
            texts = expected
            if locale != 'en':
                document = json.loads((stage / 'content/locales' / (locale + '.json')).read_bytes())
                texts = {**expected, **document['entries']['google-stadia']}
                del document
            assert actual and actual['id'] == 'google-stadia'
            assert (actual['year'], actual['month'], actual['day']) == (2019, 11, 19)
            assert len(actual['body']) == len(actual['story_headings']) == 6
            for field in ('title', 'subtitle', 'summary', 'body', 'story_headings'):
                assert actual[field] == texts[field], (locale, field)
            assert all(any(image['paragraph'] == slot for image in actual['images']) for slot in range(6))
            gta = reader.call('catalogue_entry', locale=locale, id='grand-theft-auto-vi')['entry']
            rooms = gta['soundtrack_rooms']
            assert len(rooms) == 2 and [len(room['tracks']) for room in rooms] == [10, 2]
            ids = [track['id'] for room in rooms for track in room['tracks']]
            assert len(ids) == len(set(ids)) == 12
            assert len({room['title'] for room in rooms}) == 2
            report['languages'][locale] = {'stadia_title': actual['title'], 'stadia_headings': actual['story_headings'], 'body_sha256': hashlib.sha256(json.dumps(actual['body'], ensure_ascii=False).encode()).hexdigest(), 'gta_rooms': rooms}
            passed(locale.upper() + ': production reader loads six exact native Stadia paragraphs/headings with images and GTA rooms 10+2 / twelve unique IDs')
        assert digest(data / 'preferences.json') == pref_digest and digest(data / 'trophies-v1.dat') == trophy_digest
    finally:
        reader.close()

    cases = [('stadia-entry-italian', 'google-stadia', 0, []), ('stadia-card-italian', 'google-stadia', 1, [])]
    for room in (0, 1):
        script = [{'frame': 360, 'pointer': [1800, 500]}]
        script += [{'frame': at, 'wheel': -8} for at in (390, 420, 450, 480, 510, 540)]
        if room == 0:
            script.append({'frame': 570, 'wheel': 1})
        cases.append(('gta-room-' + str(room) + '-italian', 'grand-theft-auto-vi', 1, script))
    for name, entry_id, preview, script in cases:
        script_path, capture = output / (name + '-script.json'), output / (name + '.png')
        script_path.write_text(json.dumps(script), encoding='utf-8')
        command = [str(exe), '--root', str(root), '--data', str(data), '--smoke', '--select', entry_id, '--preview', str(preview), '--frames', '720', '--script', str(script_path), '--screenshot', str(capture)]
        print('CAPTURE: ' + name, flush=True)
        with (output / (name + '-stderr.log')).open('wb') as stderr, (output / (name + '-stdout.log')).open('wb') as stdout:
            result = subprocess.run(command, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW, timeout=180)
        assert result.returncode == 0 and capture.is_file() and capture.stat().st_size > 10000, (name, result.returncode)
        report['captures'].append({'name': name, 'path': str(capture), 'exit_code': result.returncode})
        passed('native Screen relaunch and capture: ' + name)
    assert all(digest(pathlib.Path(path)) == value for path, value in original.items())
    report['immutable_sources'] = original
    passed('staged app/source catalogues and original fixture preferences remain byte-for-byte unchanged')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('root', 'stage', 'template', 'output', 'manifest', 'driver', 'exe'):
        parser.add_argument('--' + argument, required=True)
    run(parser.parse_args())
