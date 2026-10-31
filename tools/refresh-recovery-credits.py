"""Refresh attribution for the owners touched by the 30 October recovery patches."""
from pathlib import Path
import copy
import json
from datetime import date

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    temporary = path.with_suffix('.credits.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)

def collect_ids(value, out):
    if isinstance(value, dict):
        for key in ('entry_id', 'id'):
            if isinstance(value.get(key), str):
                out.add(value[key])
        for child in value.values():
            collect_ids(child, out)
    elif isinstance(value, list):
        for child in value:
            collect_ids(child, out)

def main():
    affected = set()
    patterns = ('*patch*.json', '*expansions*.json', '*-prose.json', '*append-only.json', 'TEXT-*.json', 'annual-game-awards-focused.json',
                'foundations-new-entries.json', 'hardware-two-release-dates.json')
    patch_files = set()
    for folder in (ROOT / 'build/research').glob('*20261030'):
        for pattern in patterns:
            patch_files.update(folder.rglob(pattern))
    for path in patch_files:
        collect_ids(read(path), affected)
    documents = [('catalog', read(ROOT / 'content/catalog.json')),
                 ('human-history', read(ROOT / 'content/human-history.json'))]
    owners = {(collection, e['id']): e for collection, doc in documents for e in doc['entries']
              if e['id'] in affected}
    credits_path = ROOT / 'content/credits.json'
    credits = read(credits_path)
    original = copy.deepcopy(credits)
    credits['media'] = [row for row in credits['media'] if not
                        (row.get('media_kind') == 'image' and
                         (row.get('collection'), row.get('exhibit_id')) in owners)]
    source_rows = {(r.get('collection'), r.get('exhibit_id')): r for r in credits['sources']}
    soundtrack_rows = {(r.get('collection'), r.get('exhibit_id'), r.get('room_index', 0)): r
                       for r in credits['soundtracks']}
    for (collection, eid), entry in owners.items():
        features = entry.get('editorial_features', [])
        photos = list(entry.get('images', []))
        for feature in features:
            photos.extend(feature.get('images', []))
        for photo in photos:
            credits['media'].append({'exhibit_id': eid, 'collection': collection, 'media_kind': 'image',
                **{k: photo.get(k, '') for k in
                   ('url', 'title', 'width', 'height', 'credit', 'source_page', 'license', 'license_url')}})
        row = source_rows.get((collection, eid))
        if row is None:
            row = {'exhibit_id': eid, 'collection': collection, 'attribution': {}}
            credits['sources'].append(row)
        row['editorial_credit'] = entry.get('editorial_credit', row.get('editorial_credit', ''))
        references = list(row.get('references', []))
        known = {r.get('url', '') if isinstance(r, dict) else str(r) for r in references}
        for ref in entry.get('sources', []):
            url = ref.get('url', '') if isinstance(ref, dict) else str(ref)
            if url and url not in known:
                references.append(copy.deepcopy(ref))
                known.add(url)
        row['references'] = references
        if entry.get('soundtrack'):
            key = (collection, eid, 0)
            soundtrack_rows[key] = {'exhibit_id': eid, 'collection': collection, 'room_index': 0,
                                    **copy.deepcopy(entry['soundtrack'])}
    credits['soundtracks'] = list(soundtrack_rows.values())
    # The selective archive cues remain separate from the game's soundtrack rooms.
    credits['cultural_audio'] = copy.deepcopy(read(ROOT / 'content/culture-memories.json')['cues'])
    credits['updated'] = date.today().isoformat()
    folder = ROOT / 'build/research/app-media-audio-handoff-20261030'
    folder.mkdir(parents=True, exist_ok=True)
    before = folder / 'credits-before-refresh.json'
    if not before.exists():
        write(before, original)
    write(credits_path, credits)
    write(folder / 'credits-refresh-receipt.json', {'owners_refreshed': len(owners),
          'patch_files': [p.relative_to(ROOT).as_posix() for p in sorted(patch_files)],
          'image_credits': len(credits['media']), 'soundtrack_rooms': len(credits['soundtracks']),
          'cultural_audio_cues': len(credits['cultural_audio'])})
    print(json.dumps({'owners_refreshed': len(owners), 'cultural_audio_cues': len(credits['cultural_audio'])}))

if __name__ == '__main__':
    main()
