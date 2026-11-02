"""Bounded C++ downloader -> Rust runner -> replacement PE handoff proof."""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
import zipfile

spec = importlib.util.spec_from_file_location('app_fixtures', Path(__file__).with_name('application-updater-integration.py'))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
EXPECTED_ZIP = 'b328de739a0ea353aac098d38fe4c0cb73d47775cf41585064190842276812d5'
EXPECTED_HELPER = 'c6fa10952020f4f254f6bace8d137c31528b1adedb87527cb5e67e9259a86149'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def process_creation(handle):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    values = [wintypes.FILETIME() for _ in range(4)]
    assert kernel.GetProcessTimes(int(handle), *(ctypes.byref(value) for value in values)), ctypes.get_last_error()
    return values[0].dwHighDateTime << 32 | values[0].dwLowDateTime


def runner_pid(name):
    class Entry(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('usage', wintypes.DWORD), ('pid', wintypes.DWORD), ('heap', ctypes.c_size_t), ('module', wintypes.DWORD), ('threads', wintypes.DWORD), ('parent', wintypes.DWORD), ('priority', wintypes.LONG), ('flags', wintypes.DWORD), ('name', wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    assert snapshot not in (0, ctypes.c_void_p(-1).value)
    try:
        item = Entry(); item.size = ctypes.sizeof(item)
        present = kernel.Process32FirstW(snapshot, ctypes.byref(item))
        while present:
            if item.name.casefold() == name.casefold():
                return int(item.pid)
            present = kernel.Process32NextW(snapshot, ctypes.byref(item))
        return None
    finally:
        kernel.CloseHandle(snapshot)


def run(args):
    project = Path(__file__).resolve().parent.parent
    output, driver, candidate, helper = (value.resolve() for value in (args.output, args.driver, args.candidate, args.helper))
    assert output.parent == project / 'build/windows-installer-test' and output.name.startswith('updater-bridge-')
    assert sha(candidate) == EXPECTED_ZIP and candidate.stat().st_size == 5585078
    assert sha(helper) == EXPECTED_HELPER
    output.mkdir(exist_ok=False)
    root = output / 'Pixel Museum'; root.mkdir()
    report = {'root': str(root), 'checks': [], 'candidate_sha256': EXPECTED_ZIP, 'helper_sha256': EXPECTED_HELPER}

    def passed(message):
        report['checks'].append(message)
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('PASS: ' + message, flush=True)

    with zipfile.ZipFile(candidate) as archive:
        expanded = sum(item.file_size for item in archive.infolist())
        assert expanded == 13212673
        inventory = json.loads(archive.read('application-files.json'))
        expected_exe = hashlib.sha256(archive.read('Pixel Museum.exe')).hexdigest()
        for name in archive.namelist():
            target = root / name
            assert target.resolve().is_relative_to(root) and '\\' not in name and ':' not in name
            if name == 'preferences.json':
                continue  # Intentional protected-data poison remains only in the ZIP.
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    program = root / 'Pixel Museum.exe'
    shutil.copyfile(driver, program)
    shutil.copyfile(helper, root / 'tools/windows-updater/Pixel-Museum-Updater.exe')
    inventory['version'] = '0.1.0'
    inventory['files'] = [row for row in inventory['files'] if row['path'] != 'preferences.json']
    for row in inventory['files']:
        path = root / row['path']
        row.update(bytes=path.stat().st_size, sha256=sha(path))
    (root / 'application-files.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    (root / 'pixel-museum-install.json').write_text(json.dumps({'schema_version': 1, 'version': '0.1.0', 'executable': 'Pixel Museum.exe', 'language': 'it'}), encoding='utf-8')
    (root / '.test-updater-handoff').write_text('pixel-museum-isolated-updater-bridge', encoding='utf-8')
    protected = {
        'preferences.json': b'{"language":"it","keep":"bridge-preferences"}',
        'trophies-v1.dat': b'bridge-trophy-sentinel',
        'database/active.json': b'{"revision":2,"keep":"database-overlay"}',
        'database/blobs/bridge-editorial-blob': b'editorial-snapshot-must-stay',
        'collection/registry.json': b'{"keep":"installed-collection"}',
    }
    for name, body in protected.items():
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
    tar_path = root / 'collection/archives/protected-fixture.tar'; tar_path.parent.mkdir(parents=True)
    with tarfile.open(tar_path, 'w') as archive:
        body = b'original-installed-resource'; entry = tarfile.TarInfo('resource.txt'); entry.size = len(body); archive.addfile(entry, io.BytesIO(body))
    protected['collection/archives/protected-fixture.tar'] = tar_path.read_bytes()
    protected_hashes = {name: sha(root / name) for name in protected}
    old_exe = sha(program)
    passed('isolated old installation owns the actual copied x64 C++ driver and pinned final Rust helper')

    server = fixtures.Server()
    release = {'version': '0.2.0', 'available': True, 'url': server.base + '/app.zip', 'sha256': EXPECTED_ZIP, 'bytes': candidate.stat().st_size, 'unpacked_bytes': expanded, 'notes': {'it': 'Prova di passaggio tra updater e helper.'}}
    server.routes['/feed.json'] = {'body': {'schema_version': 1, 'application_id': 'pixel-museum', 'platforms': {'windows-x64': release}}}
    server.routes['/app.zip'] = {'body': candidate.read_bytes()}
    stderr = (output / 'parent-stderr.log').open('wb')
    parent = subprocess.Popen([str(program), str(root), str(root), server.base + '/feed.json', '--allow-test-handoff'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
    creation = process_creation(parent._handle)

    def call(operation, **fields):
        parent.stdin.write(json.dumps(dict(op=operation, **fields)) + '\n'); parent.stdin.flush()
        line = parent.stdout.readline(); assert line, parent.poll()
        value = json.loads(line); assert value['ok'], value
        return value

    try:
        call('configure', current='0.1.0')
        assert call('check')['state']['phase'] == 'available'
        assert call('install')['state']['phase'] == 'ready'
        assert sha(program) == old_exe and not (root / 'application-updates/relaunch-proof.txt').exists()
        passed('production C++ check and verified download prepare the exact ZIP without replacing or launching the app')
        assert call('handoff', language='it')['ok']
        descriptors = list((root / 'application-updates/runner').glob('update-*.json')); assert len(descriptors) == 1
        job = json.loads(descriptors[0].read_bytes())
        assert job['schema_version'] == 1 and job['application_id'] == 'pixel-museum' and job['platform'] == 'windows-x64'
        assert job['parent_pid'] == parent.pid and job['parent_creation_time'] == creation
        assert Path(job['application_root']).resolve() == root
        assert Path(job['archive']).resolve() == root / 'application-updates/payloads' / (EXPECTED_ZIP + '.zip')
        assert job['archive_sha256'] == EXPECTED_ZIP and job['archive_bytes'] == release['bytes'] and job['unpacked_bytes'] == expanded
        assert job['version'] == '0.2.0' and job['language'] == 'it' and job['restart'] is True
        assert Path(job['result_path']).resolve() == root / 'application-updates/result.json'
        runner = next((root / 'application-updates/runner').glob('updater-*.exe'))
        assert sha(runner) == EXPECTED_HELPER
        deadline = time.monotonic() + 10
        while not runner_pid(runner.name):
            assert time.monotonic() < deadline
            time.sleep(.05)
        report['descriptor'] = job; report['runner_pid'] = runner_pid(runner.name)
        passed('real C++ descriptor carries the exact root, pinned payload, language, actual parent PID and creation time')
        time.sleep(.75)
        assert parent.poll() is None and runner_pid(runner.name)
        assert sha(program) == old_exe and not (root / 'application-updates/result.json').exists()
        assert all(sha(root / name) == value for name, value in protected_hashes.items())
        passed('the real temporary Rust runner waits while the matching parent remains alive')
        parent.stdin.close(); parent.wait(timeout=20); assert parent.returncode == 0
        result_path, marker = root / 'application-updates/result.json', root / 'application-updates/relaunch-proof.txt'
        deadline = time.monotonic() + 30
        while not result_path.exists() or not marker.exists() or marker.read_bytes() != b'2' or runner_pid(runner.name):
            assert time.monotonic() < deadline, result_path.read_text() if result_path.exists() else 'helper did not finish'
            time.sleep(.05)
        result = json.loads(result_path.read_bytes()); assert result['success'] is True and result['rolled_back'] is False, result
        assert sha(program) == expected_exe and sha(program) != old_exe
        installed = json.loads((root / 'application-files.json').read_bytes()); assert installed['version'] == '0.2.0'
        assert all(sha(root / name) == value for name, value in protected_hashes.items())
        assert sha(root / 'tools/windows-updater/Pixel-Museum-Updater.exe') == EXPECTED_HELPER
        report.update(result=result, old_driver_sha256=old_exe, new_mock_sha256=expected_exe, relaunch_marker=marker.read_text(), protected_files=protected_hashes, external_network_requests=0, real_user_destination_accessed=False, ps5_accessed=False)
        passed('parent exit releases the transaction and the replacement mock PE launches with marker 2')
        passed('preferences, trophies, database overlay, registry and TAR remain byte-for-byte intact despite ZIP preference poison')
        passed('production C++ to frozen Rust helper handoff completes without GUI or user-installation access')
    finally:
        if parent.poll() is None:
            parent.stdin.close(); parent.wait(timeout=20)
        stderr.close(); server.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('driver', 'candidate', 'helper', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    run(parser.parse_args())
