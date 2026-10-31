"""Publish the reviewed audio/film-poster batch using exact-field guards."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import runpy
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/app-audio-culture-priority-20261030'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    tmp = path.with_suffix('.recovery.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def main():
    global BASE
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default=str(BASE.relative_to(ROOT)))
    parser.add_argument('--soundtrack-file', default='soundtrack-patches.json')
    parser.add_argument('--cue-file', default='culture-audio-patches.json')
    args = parser.parse_args()
    BASE = ROOT / args.base
    catalog = read(ROOT / 'content/catalog.json')
    history = read(ROOT / 'content/human-history.json')
    cues = read(ROOT / 'content/culture-memories.json')
    by = {e['id']: e for e in catalog['entries']}
    history_by = {e['id']: e for e in history['entries']}
    cue_by = {e['entry_id']: e for e in cues['cues']}
    report = {'soundtracks': [], 'cues': [], 'posters': []}
    track_patches = read(BASE / args.soundtrack_file)['patches'] if (BASE / args.soundtrack_file).exists() else []
    for patch in track_patches:
        owner = by[patch['entry_id']]
        assert patch['field'] == 'soundtrack'
        assert owner.get('soundtrack') in (patch['before'], patch['after']), patch['entry_id']
        owner['soundtrack'] = copy.deepcopy(patch['after'])
        report['soundtracks'].append({'entry_id': owner['id'], 'tracks': len(owner['soundtrack']['tracks'])})
    cue_patches = read(BASE / args.cue_file)['patches'] if (BASE / args.cue_file).exists() else []
    for patch in cue_patches:
        owner = cue_by.get(patch['entry_id'])
        assert owner in (patch['before'], patch['after']), patch['entry_id']
        if owner is None:
            owner = {}
            cues['cues'].append(owner)
            cue_by[patch['entry_id']] = owner
        if 'asset_copy' in patch:
            source = ROOT / patch['asset_copy']['source']
            target = ROOT / patch['asset_copy']['destination']
            assert hashlib.sha256(source.read_bytes()).hexdigest() == patch['after']['local_asset_sha256']
            shutil.copy2(source, target)
        owner.clear()
        owner.update(patch['after'])
        report['cues'].append(owner['entry_id'])
    manifest_path = ROOT / 'assets/images/manifest.json'
    manifest = read(manifest_path)
    helper = runpy.run_path(str(ROOT / 'tools/bundle-editorial-images.py'))
    poster_patches = read(BASE / 'culture-poster-patches.json')['patches'] if (BASE / 'culture-poster-patches.json').exists() else []
    for patch in poster_patches:
        owner = history_by[patch['entry_id']]
        index = patch['image_index']
        assert owner['images'][index] in (patch['before'], patch['after']), patch['entry_id']
        image = copy.deepcopy(patch['after'])
        source = ROOT / image['recovery_local_source']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == image['verification']['sha256']
        with Image.open(source) as original:
            dimensions = original.size
            full, preview, alpha = helper['prepare_rasters'](original)
        name = hashlib.sha256(image['url'].encode()).hexdigest()[:24] + ('.png' if alpha else '.jpg')
        target = ROOT / 'assets/images' / name
        thumb = ROOT / 'assets/images/previews' / name
        helper['save_raster'](full, target)
        helper['save_raster'](preview, thumb, preview=True)
        manifest['images'][image['url']] = target.relative_to(ROOT).as_posix()
        manifest['previews'][image['url']] = thumb.relative_to(ROOT).as_posix()
        manifest['metadata'][image['url']] = {
            'source_width': dimensions[0], 'source_height': dimensions[1],
            'width': full.width, 'height': full.height,
            'preview_width': preview.width, 'preview_height': preview.height,
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'acquisition': image.get('recovery_acquisition', 'same_original_poster_native_high_resolution'),
            'alpha_preserved': alpha, 'alpha_composited': False, 'alpha_policy_version': 1,
            **{k: image.get(k, '') for k in ('title', 'source_page', 'creator', 'credit', 'license', 'license_url')},
        }
        manifest['failures'].pop(image['url'], None)
        owner['images'][index] = image
        report['posters'].append(owner['id'])
    # Keep an exact rollback snapshot, once, before publishing changed fields.
    for filename in ('catalog.json', 'human-history.json', 'culture-memories.json'):
        backup = BASE / (filename + '.before-integration')
        if not backup.exists():
            shutil.copy2(ROOT / 'content' / filename, backup)
    write(manifest_path, manifest)
    write(ROOT / 'content/catalog.json', catalog)
    write(ROOT / 'content/human-history.json', history)
    write(ROOT / 'content/culture-memories.json', cues)
    receipt_name = 'integrated-receipt-' + Path(args.soundtrack_file).stem + '-' + Path(args.cue_file).stem + '.json'
    write(BASE / receipt_name, report)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
