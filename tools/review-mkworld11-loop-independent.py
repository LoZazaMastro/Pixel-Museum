"""Check complete public game-loop recordings, without inventing album cuts."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad/nintendo-full'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
path=BASE/'mkworld-distinct11-long-loop-versions-candidate.json'
candidate=read(path);entry=candidate['entries'][0];tracks=entry['tracks']
module=read(ROOT/'content/expansion/soundtrack-multitrack-priority-overrides.json')
base=next(e for e in module['entries'] if e['entry_id']==entry['entry_id'])['tracks']
assert len(base)==331 and len(tracks)==11
assert len({t['youtube_id'] for t in base+tracks})==342
assert len({t['title'] for t in base+tracks})==342
assert entry['coverage_status']=='partial' and not entry['full_album_collection']
inventory={t['number']:t for t in read(BASE/'mkworld-nintendo-music-secondary-inventory.json')['tracks']}
normal=lambda s:re.sub('[^a-z0-9]','',s.casefold())
checks=[]
for t in tracks:
    expected=inventory[t['inventory_track_number']]
    assert t['title']==expected['title']
    watch=read(ROOT/t['publication_metadata_receipt']);native=read(ROOT/t['native_codec_metadata_receipt'])
    assert native['id']==t['youtube_id'] and native['native_compatible_avc_aac']
    assert native['avc_format_count']>0 and native['aac_format_count']>0
    assert normal(t['title']) in normal(watch['title']) and 'mariokartworld' in normal(watch['title'])
    assert watch.get('channelId') or (watch.get('provider_name')=='YouTube' and watch.get('author_url'))
    duration=float(native['duration'])
    assert abs(duration-t['duration_seconds'])<.1 and duration>expected['length_seconds']
    assert 'start_seconds' not in t and 'end_seconds' not in t
    assert 'not asserted' in t['recording_version'] and 'without invented cut points' in t['recording_version']
    assert not t['official_uploader_verified'] and not t['playback_verified_on_ps5']
    assert t['creator']=='Nintendo sound team'
    checks.append(dict(title=t['title'],actual_publication_title=watch['title'],youtube_id=t['youtube_id'],
        full_public_recording_seconds=duration,secondary_edited_album_seconds=expected['length_seconds']))
receipt=dict(status='PASS_AS_PUBLIC_GAME_LOOP_VERSIONS',candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    checks=checks,distinct_additions=11,union_recordings=342,coverage_status='partial',
    limitations='Public titles and channels associate the recordings with the game score; descriptions are empty and add no evidence. These are longer archival game-loop versions, not the shorter Nintendo Music edits. No listening, audio fingerprint, edited-master equivalence or console playback certification.')
(BASE/'root-independent-mkworld11-loop-review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('PASS:11 distinct full public game-loop versions;342-recording union remains explicitly partial.')
