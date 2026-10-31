"""Check the distinct battle/menu supplement without claiming album completion."""
from pathlib import Path
import hashlib,json,re,unicodedata
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad/nintendo-full'
read=lambda path:json.loads(path.read_text(encoding='utf-8'))
path=BASE/'mkworld-distinct21-battle-fanfare-candidate.json'
candidate=read(path);entry=candidate['entries'][0];tracks=entry['tracks']
base_path=BASE/'mkworld253-clean-original-archive-candidate.json'
assert hashlib.sha256(base_path.read_bytes()).hexdigest()==candidate['requires_base_candidate_sha256']
old=read(base_path)['entries'][0]['tracks']
inventory={t['number']:t for t in read(BASE/'mkworld-nintendo-music-secondary-inventory.json')['tracks']}
assert len(tracks)==21 and len(old)==253
assert not entry['full_album_collection'] and entry['coverage_status']=='partial'
assert len({t['youtube_id'] for t in tracks+old})==274
assert len({t['title'] for t in tracks+old})==274
def normal(text):
    text=re.sub(r'\[\s*[a-z]\s*\]','',text)
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',text).casefold())
checks=[]
for t in tracks:
    expected=inventory[t['inventory_track_number']]
    assert normal(t['title'])==normal(expected['title'])
    watch=read(ROOT/t['publication_metadata_receipt'])
    native=read(ROOT/t['native_codec_metadata_receipt'])
    assert native['id']==t['youtube_id'] and native['native_compatible_avc_aac']
    assert native['avc_format_count']>0 and native['aac_format_count']>0
    assert watch.get('channelId') or (watch.get('provider_name')=='YouTube' and watch.get('author_url') and watch.get('author_name'))
    published=watch['title']
    assert normal(t['title']) in normal(published), (t['title'],published)
    assert 'mariokartworld' in normal(published)
    assert not any(word in published.lower() for word in ('cover by','remix','sfx','with sound effects'))
    delta=abs(float(native['duration'])-expected['length_seconds'])
    assert delta<=3 or (t['inventory_track_number']==75 and delta==4)
    assert t['creator']=='Nintendo sound team' and not t['official_uploader_verified'] and not t['playback_verified_on_ps5']
    checks.append(dict(number=t['inventory_track_number'],title=t['title'],actual_publication_title=published,
        duration_difference_seconds=delta,publication_metadata='watch' if watch.get('channelId') else 'public_oembed'))
receipt=dict(status='PASS',candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),checks=checks,
    distinct_supplemental_cues=21,union_cues=274,published_inventory_secondary=348,coverage_status='partial',
    limitations='Public game archive recordings checked against community Nintendo Music transcription. The four-second SMK battle edit difference is disclosed. No authenticated album master, exhaustive game music, audio fingerprint or physical PS5 playback claim.')
(BASE/'root-independent-mkworld21-review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('PASS:21 distinct battle/menu/fanfare cues;274-recording union remains partial.')
