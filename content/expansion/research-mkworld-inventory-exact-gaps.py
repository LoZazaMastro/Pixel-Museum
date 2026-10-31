"""Discover missing *named* inventory cues, preserving edition/genre tokens.

Exact title/duration matching is research evidence, not publisher-upload or
audio-master equivalence. No record is automatically admitted by this helper.
"""
import concurrent.futures
import importlib.util
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/research/soundtrack-broad/nintendo-full'
spec = importlib.util.spec_from_file_location('reader', ROOT / 'content/expansion/research-botw-cd-individuals.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.cache_dir = OUT / 'mkworld-inventory-exact-gap-individuals'
reader.cache_dir.mkdir(exist_ok=True)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def title_key(text):
    text = re.sub(r'\s*[-\u2014]\s*Mario Kart World (?:Soundtrack|Music).*', '', text)
    text = re.sub(r'\[\s*[a-z]\s*\]', '', text)
    text = text.replace(' Ver.', '').replace('BGM', 'Theme').replace('Mario Kart 8 Deluxe', 'Mario Kart 8')
    text = re.sub(r'^(?:SNES|NES|N64|GBA|GCN|Wii U|Wii|DS|3DS|Tour)\s+', '', text)
    # This normalization does not collapse day/night, phase, original-game
    # parentheticals or instrument/genre variants.
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', text)


inventory = load(OUT / 'mkworld-nintendo-music-secondary-inventory.json')['tracks']
old = load(OUT / 'mkworld253-clean-original-archive-candidate.json')['entries'][0]['tracks']
old_keys = {title_key(track['title']) for track in old}
source = load(OUT / 'mkworld-preston-public-flat-playlist.json')['entries']
selected = []
for expected in inventory:
    if title_key(expected['title']) in old_keys:
        continue
    candidates = [track for track in source if track.get('title') and track.get('duration') and
                  track.get('channel') == 'Mario Kart Music Channel' and
                  title_key(track['title']) == title_key(expected['title']) and
                  abs(track['duration'] - expected['length_seconds']) <= 3]
    if not candidates:
        continue
    candidate = min(candidates, key=lambda track: abs(track['duration'] - expected['length_seconds']))
    selected.append({
        'album_track_number': expected['number'], 'title': expected['title'],
        'expected_seconds': candidate['duration'], 'source': candidate,
        'inventory_expected_duration_seconds': expected['length_seconds'],
        'alias_context': 'Exact original-game/genre/phase title tokens after punctuation, bracket style and trailing Ver. normalization; actual source duration within3s of community NintendoMusic inventory. Publisher-master equivalence remains unasserted.',
    })
reader.pipeline.write(OUT / 'mkworld-inventory-exact-gaps-selected.json', {'tracks': selected})
if __name__ == '__main__':
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(reader.read, selected):
            rows.append(row)
            reader.pipeline.write(OUT / 'mkworld-inventory-exact-gaps-publication-research.json', {
                'publication_status': 'research_only', 'source_kind': 'Public archival individual game-recording metadata, not official publisher uploads.',
                'tracks': rows,
            })
            print(row['album_track_number'], row['source']['id'], row['status'], row.get('error', ''), flush=True)
