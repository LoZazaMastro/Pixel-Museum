"""Keep a per-cue, read-only reconciliation of the348-name research target.

No fuzzy admission, fabricated splits or zero-equals-silence inference. A title
match does not certify bit-identical Nintendo Music masters.
"""
import collections
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
load = lambda p: json.loads(p.read_text(encoding='utf-8'))


def normalized_title(text):
    text = re.sub(r'\s*[-\u2014]\s*Mario Kart World (?:Soundtrack|Music|OST).*', '', text)
    text = re.sub(r'\[\s*[a-z]\s*\]', '', text)
    text = re.sub(r'^(?:SNES|NES|N64|GBA|GCN|Wii U|Wii|DS|3DS|Tour)\s+', '', text)
    text = text.replace(' Ver.', '').replace('BGM', 'Theme')
    # This is the reference game's name inside a World arrangement title,
    # not an assertion that the recording comes from MK8 instead of World.
    text = text.replace('Mario Kart 8 Deluxe', 'Mario Kart 8')
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower())


sources = []
for name, input_file in [
    ('mkworld-clean-grandprix', 'mkworld-clean-grandprix-archive-publication-research.json'),
    ('mkworld-clean-freeroam', 'mkworld-clean-freeroam-archive-publication-research.json'),
    ('mkworld-inventory-exact-gaps', 'mkworld-inventory-exact-gaps-publication-research.json'),
    ('mkworld-koopasaurus-core', 'mkworld-koopasaurus-core-archive-publication-research.json'),
]:
    path = OUT / input_file
    if not path.exists():
        continue
    fallback_path = OUT / (name + '-public-oembed-fallback-research.json')
    fallbacks = {row['source']['id']: row for row in load(fallback_path)['tracks']} if fallback_path.exists() else {}
    for original in load(path)['tracks']:
        row = fallbacks.get(original['source']['id'], original)
        if row['status'] != 'metadata_candidate' or row['source']['id'] == 'l5XuwkNdcug':
            continue
        publication = row['publication']
        sources.append({
            'youtube_id': row['source']['id'], 'title': publication['title'],
            'duration_seconds': float(publication['lengthSeconds']),
            'uploader': publication['author'],
            'source_research': str(path.relative_to(ROOT)).replace('\\', '/'),
            'native_codec_receipt': row['native_codec_receipt'],
            'publication_metadata_receipt': row.get('publication_metadata_receipt') or 'build/research/soundtrack-broad/watch/' + row['source']['id'] + '.json',
        })
inventory = load(OUT / 'mkworld-nintendo-music-secondary-inventory.json')
rows = []
for expected in inventory['tracks']:
    matches = [source for source in sources if normalized_title(source['title']) == normalized_title(expected['title'])]
    matches.sort(key=lambda source: abs(source['duration_seconds'] - expected['length_seconds']))
    best = matches[0] if matches else None
    if best is None:
        status = 'unresolved_exact_title'
    elif abs(best['duration_seconds'] - expected['length_seconds']) <= 3:
        status = 'exact_named_cue_metadata_and_native_verified'
    else:
        status = 'named_cue_recording_version_or_duration_review'
    rows.append({'inventory': expected, 'status': status, 'best_actual_source': best,
                 'duration_difference_seconds': abs(best['duration_seconds'] - expected['length_seconds']) if best else None,
                 'alternate_actual_sources': matches[1:]})
report = {
    'publication_status': 'research_only_not_production', 'expected_secondary_inventory_count': 348,
    'inventory_source': inventory['source_url'], 'inventory_source_kind': inventory['source_kind'],
    'counts': dict(collections.Counter(row['status'] for row in rows)),
    'scope': 'Named-cue metadata/native/duration reconciliation only. Archival recordings may differ in loops/fades/mastering from the edited Nintendo Music release. Fuzzy/semantic aliases remain unresolved until explicitly reviewed.',
    'all_game_music_complete': False, 'all_audio_independently_listened': False,
    'physical_ps5_playback_verified': False, 'tracks': rows,
}
(OUT / 'mkworld348-named-cue-reconciliation-research.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report['counts']))
for row in rows:
    if row['status'] != 'exact_named_cue_metadata_and_native_verified':
        print(row['inventory']['number'], row['inventory']['title'], row['status'], row['duration_difference_seconds'])
