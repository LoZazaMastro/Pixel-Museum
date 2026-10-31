"""Import the five prepared foundation entries together with their real images."""
import copy
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/app-nongame-recovery-20261030'
MEDIA = ROOT / 'build/research/console-media-append-20261030'
LANGS = ('en', 'it', 'fr', 'de', 'es')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    temp = path.with_suffix('.foundation.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def main():
    spec = importlib.util.spec_from_file_location('prose_helpers', ROOT / 'tools/apply-editorial-recovery-patches.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    source = read(BASE / 'foundations-new-entries.json')
    media = read(MEDIA / 'new-organization-heroes-patch.json')
    images = {e['entry_id']: e for e in media['new_entries_media']}
    catalog = read(ROOT / 'content/catalog.json')
    known = {e['id'] for e in catalog['entries']}
    locales = {lang: read(ROOT / f'content/museum-locales/{lang}.json') for lang in LANGS[1:]}
    added = []
    for record in source['new_entries']:
        eid = record['id']
        if eid in known:
            continue
        assert eid in images and images[eid]['images'], (eid, 'missing image')
        row = {k: copy.deepcopy(v) for k, v in record.items() if k != 'main'}
        row.update({
            'era_id': 'three-d' if row['year'] < 2000 else 'connected' if row['year'] < 2010 else 'everywhere',
            'calendar_only': False, 'layout': 'editorial', 'featured': False,
            'tags': ['industry', 'preservation' if eid == 'video-game-history-foundation' else 'press' if eid in ('multiplayer-it-foundation', 'giochi-per-il-mio-computer') else 'events'],
            'related_ids': [], 'videos': [], 'models': [],
            'images': copy.deepcopy(images[eid]['images']), 'preferred_image': images[eid]['preferred_image'],
            'editorial_mode': 'original', 'editorial_credit': 'Pixel Museum / Andrea Sgarro. Original editorial text based on the credited sources.',
        })
        for image in row['images']:
            if eid == 'giochi-per-il-mio-computer':
                image['title'] = 'Giochi per il mio Computer, issue 2, June 1997. Il Mio Castello / RetroEdicola Videoludica.'
        for lang in LANGS:
            text = record['main'][lang]
            target = row if lang == 'en' else locales[lang]['entries'].setdefault(eid, {})
            target.update({'title': text['title'], 'subtitle': text.get('subtitle', ''), 'summary': text['summary'],
                           'body': [c['text'] for c in text['cards']], 'story_headings': [c['heading'] for c in text['cards']]})
        helper.refresh(row, locales, (BASE / 'foundations-new-entries.json').relative_to(ROOT).as_posix())
        catalog['entries'].append(row)
        added.append(eid)
    manifest_path = ROOT / 'assets/images/manifest.json'
    manifest = read(manifest_path)
    for group, values in media['manifest_delta'].items():
        manifest.setdefault(group, {}).update(values)
        if group in ('images', 'previews'):
            for url, relative in values.items():
                target = ROOT / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(MEDIA / 'staged' / relative, target)
                manifest.setdefault('failures', {}).pop(url, None)
    catalog['entries'].sort(key=lambda e: (e['year'], e.get('date', {}).get('month') or 0, e.get('date', {}).get('day') or 0))
    write(manifest_path, manifest)
    write(ROOT / 'content/catalog.json', catalog)
    for lang, doc in locales.items():
        write(ROOT / f'content/museum-locales/{lang}.json', doc)
    write(BASE / 'foundations-integrated.json', {'added': added, 'with_real_media': True})
    print(json.dumps({'new_entries': added}))


if __name__ == '__main__':
    main()
