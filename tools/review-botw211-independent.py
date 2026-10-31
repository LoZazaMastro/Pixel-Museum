"""Reconcile the proposed archive with the publisher inventory and raw receipts."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/soundtrack-broad/nintendo-full'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
path = BASE / 'botw211-final209-plus2-base-roster-candidate.json'
candidate = read(path)
tracks = candidate['entries'][0]['tracks']
inventory = [track for medium in read(BASE / 'botw-cd-english-translated-inventory.json')['media'] for track in medium['tracks']]
raw_primary = read(BASE / 'botw-primary-inventory-raw.json')['primary_tracks']
# The publisher page also advertises a separate 15-cue Zelda selection.
# The five-disc Breath of the Wild programme occupies its first 211 rows.
assert len(raw_primary) == 226
primary = raw_primary[:211]
assert len(tracks) == len(inventory) == len(primary) == 211
assert len({(t['youtube_id'], t.get('start_seconds'), t.get('end_seconds')) for t in tracks}) == 211
checks = []
for number, (track, expected, original) in enumerate(zip(tracks, inventory, primary), 1):
    assert track['album_track_number'] == number
    assert track['title'] == expected['title'], number
    assert track['published_original_title'] == original, number
    assert track['creator'] == 'Nintendo sound team'
    assert 'game_score_composers' not in track
    assert not track['official_uploader_verified'] and not track['playback_verified_on_ps5']
    watch = read(ROOT / track['publication_metadata_receipt'])
    native = read(ROOT / track['native_codec_metadata_receipt'])
    assert native['id'] == track['youtube_id']
    assert native['native_compatible_avc_aac'] and native['avc_format_count'] > 0 and native['aac_format_count'] > 0
    assert watch['title']
    if watch.get('channelId'):
        publication_kind = 'watch_metadata'
    else:
        assert number in (146, 193)
        assert watch['provider_name'] == 'YouTube' and watch['author_name'] and watch['author_url'].startswith('https://www.youtube.com/')
        assert watch['native_metadata']['id'] == track['youtube_id']
        publication_kind = 'oembed_and_separate_native_receipt'
    duration = float(native['duration'])
    if 'start_seconds' in track:
        assert number in (158, 200)
        start, end = track['start_seconds'], track['end_seconds']
        assert 0 <= start < end <= duration
        description = watch['shortDescription']
        assert track['archival_published_cue_label'] in description
        assert track['source_next_chapter'] in description
        other = read(ROOT / 'build/research/soundtrack-broad/watch/pR0dZ5fI9Z4.json')
        # A second public recording has a five-second introduction, followed
        # by the same two explicitly named and equally bounded chapters.
        def timestamp(seconds):
            return f'{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}'
        assert timestamp(start + 5) in other['shortDescription']
        assert timestamp(end + 5) in other['shortDescription']
        duration = end - start
    delta = abs(duration - expected['length'] / 1000)
    assert delta <= 3, (number, delta)
    checks.append(dict(number=number, title=track['title'], youtube_id=track['youtube_id'],
        actual_publication_title=watch['title'], duration_difference_seconds=delta,
        chapter_bounded='start_seconds' in track, publication_metadata_kind=publication_kind))
receipt = dict(status='PASS', candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    publisher_inventory_compositions=211, individually_published_recordings=209,
    chapter_bounded_recordings=2, checks=checks,
    limitations='Ordered compositions reconciled against publisher Japanese inventory and secondary translated titles; archive metadata and native codec receipts checked. This is not audio fingerprinting, CD-master certification, or a physical PS5 playback test.')
(BASE / 'root-independent-botw211-review.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print('PASS: 211 ordered compositions, publisher labels, publication and native codec receipts; two explicit chapter bounds.')
