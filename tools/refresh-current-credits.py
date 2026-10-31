"""Refresh distribution attribution from the live catalogues without reassembling them."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path,
                        default=ROOT/'build/research/final-delivery-20261031')
    args = parser.parse_args()
    target = ROOT/'content/credits.json'
    original = read(target)
    credits = copy.deepcopy(original)
    prior = {(r.get('exhibit_id'), r.get('feature_id')): r
             for r in original.get('sources', [])}
    sources, media, soundtracks = [], [], []
    inputs = {}
    for collection, filename in [('catalog', 'catalog.json'), ('human-history', 'human-history.json')]:
        path = ROOT/'content'/filename
        inputs[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        for entry in read(path)['entries']:
            eid = entry['id']
            for unit in [entry, *(entry.get('editorial_features') or [])]:
                feature = unit is not entry
                identity = {'collection': collection, 'exhibit_id': eid}
                if feature:
                    identity['feature_id'] = unit['id']
                old = prior.get((eid, unit['id'] if feature else None), {})
                references = copy.deepcopy(unit.get('sources') or [])
                known = {r.get('url') if isinstance(r, dict) else str(r) for r in references}
                # Retain immutable licence/revision references from the original attribution.
                for reference in old.get('references') or []:
                    url = reference.get('url') if isinstance(reference, dict) else str(reference)
                    if url and url not in known:
                        references.append(copy.deepcopy(reference)); known.add(url)
                sources.append({**identity,
                    'editorial_credit': unit.get('editorial_credit', old.get('editorial_credit', '')),
                    'attribution': copy.deepcopy(unit.get('attribution', old.get('attribution', {}))),
                    'references': references})
                for kind in ('images', 'videos', 'models'):
                    for item in unit.get(kind) or []:
                        media.append({**identity, 'media_kind': kind[:-1], **copy.deepcopy(item)})
                if not unit.get('calendar_only', False):
                    rooms = unit.get('soundtrack_rooms') or ([unit['soundtrack']] if unit.get('soundtrack') else [])
                    for index, room in enumerate(rooms):
                        soundtracks.append({**identity, 'room_index': index, **copy.deepcopy(room)})
    translations = []
    for locale in ('it', 'fr', 'de', 'es'):
        path = ROOT/'content/museum-locales'/f'{locale}.json'
        inputs[f'museum-locales/{locale}.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
        for eid, row in read(path)['entries'].items():
            translations.append({'exhibit_id': eid, 'locale': locale,
                **{key: copy.deepcopy(row[key]) for key in
                   ('editorial_credit', 'attribution', 'source_body_sha256', 'source_fields_sha256') if key in row}})
    cues_path = ROOT/'content/culture-memories.json'
    inputs['culture-memories.json'] = hashlib.sha256(cues_path.read_bytes()).hexdigest()
    credits.update(sources=sources, media=media, soundtracks=soundtracks,
                   translations=translations, cultural_audio=read(cues_path)['cues'],
                   updated=datetime.now(timezone.utc).date().isoformat())
    folder = args.report_dir.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    backup = folder/'credits.before-refresh.json'
    if not backup.exists():
        backup.write_bytes(target.read_bytes())
    data = (json.dumps(credits, ensure_ascii=False, indent=2)+'\n').encode('utf8')
    temporary = target.with_suffix('.current-credits.tmp')
    temporary.write_bytes(data); temporary.replace(target)
    report = {'inputs': inputs, 'credits_sha256': hashlib.sha256(data).hexdigest(),
              'sources': len(sources), 'media': len(media), 'soundtracks': len(soundtracks),
              'translations': len(translations), 'cultural_audio': len(credits['cultural_audio']),
              'bytes': len(data)}
    (folder/'credits-refresh.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k: v for k, v in report.items() if k != 'inputs'}))

if __name__ == '__main__':
    main()
