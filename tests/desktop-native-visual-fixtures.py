"""Capture final native desktop UI using copied prefs and existing real TAR fixtures."""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True, type=pathlib.Path)
parser.add_argument('--exe', type=pathlib.Path)
parser.add_argument('--template', required=True, type=pathlib.Path)
parser.add_argument('--output', required=True, type=pathlib.Path)
parser.add_argument('--case', action='append', choices=['options-italian-light', 'database-italian-light', 'options-italian-dark', 'video-borderless-italian-dark', 'youtube-signin-italian-dark', 'support-italian-dark', 'application-update-italian-dark'])
args = parser.parse_args()
root, template, output = args.root.resolve(), args.template.resolve(), args.output.resolve()
executable = args.exe.resolve() if args.exe else root / 'Pixel Museum.exe'
output.mkdir(parents=True, exist_ok=False)
original_preferences = (template / 'preferences.json').read_bytes()
original_sha = hashlib.sha256(original_preferences).hexdigest()
cases = [('options-italian-light', False, False), ('database-italian-light', False, True), ('options-italian-dark', True, False)]
if args.case:
    cases += [('video-borderless-italian-dark', True, False), ('youtube-signin-italian-dark', True, False), ('support-italian-dark', True, False), ('application-update-italian-dark', True, False)]
    cases = [case for case in cases if case[0] in args.case]
report = {'source_preferences_sha256': original_sha, 'cases': []}

for name, dark, database in cases:
    data = output / (name + '-data')
    data.mkdir()
    tar_count = 0
    metadata_bytes = 0
    for source in (template / 'collection').rglob('*'):
        destination = data / 'collection' / source.relative_to(template / 'collection')
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix.lower() == '.tar':
                os.link(source, destination)
                assert os.stat(source).st_ino == os.stat(destination).st_ino
                tar_count += 1
            else:
                shutil.copyfile(source, destination)
                metadata_bytes += source.stat().st_size
    assert tar_count == 12, tar_count
    preferences = json.loads(original_preferences)
    preferences.update(language='it', language_chosen=True, theme_chosen=True, onboarding_complete=True, dark_theme=dark, master_volume=0.0)
    (data / 'preferences.json').write_text(json.dumps(preferences), encoding='utf-8')
    if (template / 'trophies-v1.dat').exists():
        shutil.copyfile(template / 'trophies-v1.dat', data / 'trophies-v1.dat')
    script = [{'frame': 360, 'pointer': [1750, 230]}]
    if database:
        script = [{'frame': 420, 'click': [1500, 600]}, {'frame': 450, 'pointer': [1180, 735]}]
    frames = 660
    if name.startswith('video-borderless'):
        script = [{'frame': 360, 'click': [1500, 240]}, {'frame': 390, 'click': [1800, 396]}, {'frame': 420, 'click': [1800, 396]}, {'frame': 450, 'pointer': [1845, 410]}]
    if name.startswith('youtube-signin'):
        # Request a device prompt once; never activate the browser or log in.
        script = [{'frame': 360, 'click': [1500, 480]}, {'frame': 390, 'action': 'confirm'}, {'frame': 450, 'pointer': [1820, 925]}]
        frames = 1500
    if name.startswith('support-'):
        script = [{'frame': 360, 'click': [1500, 780]}, {'frame': 450, 'pointer': [1420, 785]}]
    if name.startswith('application-update-'):
        script = [{'frame': 360, 'click': [1500, 600]}, {'frame': 450, 'pointer': [1180, 735]}]
    script_path = output / (name + '-script.json')
    script_path.write_text(json.dumps(script), encoding='utf-8')
    screenshot = output / (name + '.png')
    command = [str(executable), '--root', str(root), '--data', str(data), '--smoke', '--preview', '4', '--select', 'game-boy', '--frames', str(frames), '--script', str(script_path), '--screenshot', str(screenshot)]
    started = time.monotonic()
    print('START: ' + name, flush=True)
    with (output / (name + '-stderr.log')).open('wb') as stderr, (output / (name + '-stdout.log')).open('wb') as stdout:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=150, creationflags=subprocess.CREATE_NO_WINDOW)
    elapsed = round(time.monotonic() - started, 2)
    assert result.returncode == 0, (name, result.returncode, (data / 'session-windows.log').read_text(errors='replace')[-4000:])
    assert screenshot.is_file() and screenshot.stat().st_size > 10000
    assert hashlib.sha256((template / 'preferences.json').read_bytes()).hexdigest() == original_sha
    report['cases'].append({'name': name, 'dark': dark, 'screenshot': str(screenshot), 'data': str(data), 'tar_hardlinks': tar_count, 'metadata_copied_bytes': metadata_bytes, 'exit_code': result.returncode, 'elapsed_seconds': elapsed})
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: ' + name + ' / ' + str(elapsed) + 's / ' + str(screenshot), flush=True)

report['final_source_preferences_sha256'] = hashlib.sha256((template / 'preferences.json').read_bytes()).hexdigest()
assert report['final_source_preferences_sha256'] == original_sha
(output / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('PASS: original fixture preferences unchanged', flush=True)
