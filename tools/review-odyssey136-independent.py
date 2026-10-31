"""Independently reconcile selected recordings against the album inventory."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
p = root / 'build/research/soundtrack-broad/nintendo-full'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
candidate_path = p / 'odyssey-complete136-candidate.json'
candidate = read(candidate_path)
tracks = candidate['entries'][0]['tracks']
inventory = [t for medium in read(p / 'odyssey-nintendo-music-inventory.json')['media'] for t in medium['tracks']]
assert len(tracks) == len(inventory) == 136
assert len({t['youtube_id'] for t in tracks}) == 136
checks = []
alternates = {t['id']: t for t in read(p / 'odyssey-five-alternate-publications.json')}
for number, (track, expected) in enumerate(zip(tracks, inventory), 1):
    assert track['album_track_number'] == number
    assert track['title'] == expected['title']
    if track['youtube_id'] in alternates:
        alternate = alternates[track['youtube_id']]
        watch = dict(candidate_id=alternate['id'], publication=alternate['publication'], native_codec_receipt=alternate['native_receipt'])
    else:
        watch = read(p / 'odyssey-individuals' / (track['youtube_id'] + '.json'))
    native = read(root / watch['native_codec_receipt'])
    assert native['id'] == watch['candidate_id'] == track['youtube_id']
    assert native['native_compatible_avc_aac'] and native['avc_format_count'] > 0 and native['aac_format_count'] > 0
    assert watch['publication']['title'] and watch['publication']['channelId']
    delta = abs(float(watch['publication']['lengthSeconds']) - expected['length'] / 1000)
    assert delta <= 3, (number, delta)
    checks.append(dict(number=number, title=track['title'], youtube_id=track['youtube_id'],
        actual_publication_title=watch['publication']['title'], duration_difference_seconds=delta,
        native_receipt=watch['native_codec_receipt']))
receipt = dict(status='PASS', candidate_sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    independently_reconciled_tracks=len(checks), checks=checks,
    limitations='Individual archival game recordings, not a claim of publisher-uploaded CD masters. Actual playback on PS5 remains to be tested.',
    artist_review='Original printed booklet reviewed: Naoto Kubo vocal compositions; Kate Davis / Aimi Mukohara vocals; Rob Tunstall and Nobuyoshi Suzuki English lyrics; Suzuki Japanese lyrics; Yoichi Murata Jump Up arrangement. Other cues retain honest collective Nintendo sound-team credit.')
(p / 'root-independent-odyssey136-review.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print('PASS: 136 titles, order, unique recordings, actual publication metadata, duration and native AVC/AAC receipts.')
