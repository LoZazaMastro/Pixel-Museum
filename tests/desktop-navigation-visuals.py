"""Focused native UI checks/captures, with isolated prefs and real archive hardlinks."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import time

p = argparse.ArgumentParser()
p.add_argument('--exe', required=True, type=pathlib.Path)
p.add_argument('--root', required=True, type=pathlib.Path)
p.add_argument('--template', required=True, type=pathlib.Path)
p.add_argument('--output', required=True, type=pathlib.Path)
p.add_argument('--checks-only', action='store_true')
p.add_argument('--captures-only', action='store_true')
p.add_argument('--case', action='append')
p.add_argument('--language', choices=['en','it','es','fr','de'], default='it')
p.add_argument('--fast', action='store_true')
args = p.parse_args()
root, template, output = args.root.resolve(), args.template.resolve(), args.output.resolve()
exe = args.exe.resolve()
output.mkdir(parents=True, exist_ok=False)
original = (template / 'preferences.json').read_bytes()
original_hash = hashlib.sha256(original).hexdigest()

def fixture(name, dark=False):
    data = output / (name + '-data')
    data.mkdir()
    archives = 0
    for source in (template / 'collection').rglob('*'):
        target = data / 'collection' / source.relative_to(template / 'collection')
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix.lower() == '.tar':
                os.link(source, target)
                assert source.stat().st_ino == target.stat().st_ino
                archives += 1
            else:
                shutil.copyfile(source, target)
    assert archives == 12
    preferences = json.loads(original)
    preferences.update(language=args.language, language_chosen=True, theme_chosen=True,
                       onboarding_complete=True, dark_theme=dark, master_volume=0.0)
    (data / 'preferences.json').write_text(json.dumps(preferences), encoding='utf-8')
    if (template / 'trophies-v1.dat').exists():
        shutil.copyfile(template / 'trophies-v1.dat', data / 'trophies-v1.dat')
    return data

def run_case(name, preview, dark, events, frames=960, checks=False):
    data = fixture(name, dark)
    if args.fast and not checks:
        events = [dict(event, frame=348 if event['frame']==500 else 398 if event['frame']==600 else 400+int((event['frame']-700)*.35)) for event in events]
        frames = 660 if name.startswith('gallery-hidden') else 540
    script = output / (name + '-script.json')
    script.write_text(json.dumps(events), encoding='utf-8')
    image = output / (name + '.png')
    command = [str(exe), '--root', str(root), '--data', str(data), '--smoke',
               '--select', 'game-boy']
    env = os.environ.copy()
    if checks:
        env['MUSEUM_FOCUSED_UI'] = '1'
        command += ['--ui-checks']
    else:
        command += ['--preview', str(preview), '--frames', str(frames),
                    '--script', str(script), '--screenshot', str(image)]
    started = time.monotonic()
    print('START ' + name, flush=True)
    with (output / (name + '.log')).open('wb') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                env=env, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    elapsed = round(time.monotonic() - started, 2)
    assert result.returncode == 0, (name, result.returncode, str(output / (name + '.log')))
    if not checks:
        assert image.stat().st_size > 10000
    assert hashlib.sha256((template / 'preferences.json').read_bytes()).hexdigest() == original_hash
    print('PASS ' + name + ' ' + str(elapsed) + 's', flush=True)
    return dict(name=name, seconds=elapsed, exit_code=result.returncode,
                screenshot=None if checks else str(image), data=str(data), tar_hardlinks=12)

report = {'source_preferences_sha256': original_hash,
          'checks': None if args.captures_only else run_case('focused-checks', 0, False, [], checks=True), 'captures': []}
if not args.checks_only:
    dismiss = [{'frame': 500, 'action': 'back'}, {'frame': 600, 'action': 'back'}]
    cases = [
        ('timeline-light', 0, False, dismiss + [{'frame': 760, 'pointer': [665, 79]}]),
        ('options-dark', 4, True, [{'frame': 760, 'pointer': [1500, 240]}]),
        ('search-dark', 0, True, dismiss + [{'frame': 700, 'search': True}, {'frame': 730, 'text': 'Game'}, {'frame': 800, 'pointer': [1000, 520]}]),
        ('atlas-dark', 0, True, dismiss + [{'frame': 700, 'action': 'touch'}, {'frame': 800, 'pointer': [360, 520]}]),
        ('experiences-dark', 0, True, dismiss + [{'frame': 700, 'action': 'touch'}, {'frame': 750, 'action': 'west'}, {'frame': 800, 'pointer': [1000, 520]}]),
        ('gallery-visible-light', 2, False, [{'frame': 900, 'pointer': [960, 500], 'wheel': 1}]),
        ('gallery-hidden-light', 2, False, [{'frame': 600, 'pointer': [960, 500], 'wheel': 1}]),
        ('combined-updates-dark', 4, True, [{'frame': 700, 'click': [1500, 600]}, {'frame': 820, 'pointer': [1180, 735]}]),
    ]
    if args.case:
        cases = [case for case in cases if case[0] in args.case]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(lambda case: run_case(*case), cases):
            report['captures'].append(result)
            (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
report['final_source_preferences_sha256'] = hashlib.sha256((template / 'preferences.json').read_bytes()).hexdigest()
assert report['final_source_preferences_sha256'] == original_hash
(output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
