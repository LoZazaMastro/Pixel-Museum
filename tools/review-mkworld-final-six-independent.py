"""Review the last six public recordings without certifying album masters."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad/nintendo-full'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
path=BASE/'mkworld-final-six-compositions-candidate.json'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='f6b611872a036fafa9080e1dfe8a1c5d909f105cad4f2bf93df496a149ad8dfb'
candidate=read(path);entry=candidate['entries'][0];tracks=entry['tracks']
module_path=ROOT/'content/expansion/soundtrack-multitrack-priority-overrides.json'
assert hashlib.sha256(module_path.read_bytes()).hexdigest()==candidate['requires_base_module_sha256']
base=next(e for e in read(module_path)['entries'] if e['entry_id']==entry['entry_id'])['tracks']
assert len(base)==342 and len(tracks)==6
assert len({t['youtube_id'] for t in base+tracks})==348
assert len({t['title'] for t in base+tracks})==348
assert entry['coverage_status']=='partial' and not entry['full_album_collection']
inventory={t['number']:t for t in read(BASE/'mkworld-nintendo-music-secondary-inventory.json')['tracks']}
expected={236:('eRagOAc9dIw','Enter Bowser Jr'),240:('zCARE6VNNwc','Final Battle with Bowser'),247:('DMQH-JmNOXw','Daisy Circuit Acoustic Ver'),253:('wa8eRlmGF2o','Rainbow Road Mario Kart Wii'),347:('Bwyj34WQo70','Title Theme In the Studio'),348:('q0qClKEGcA4','Crown City Bonus Track')}
normal=lambda s:re.sub('[^a-z0-9]','',s.casefold())
checks=[]
for t in tracks:
    number=t['inventory_track_number'];ident,identity=expected[number]
    inv=inventory[number]
    assert t['youtube_id']==ident and t['title']==inv['title']
    watch=read(ROOT/t['publication_metadata_receipt']);native=read(ROOT/t['native_codec_metadata_receipt'])
    assert native['id']==ident and native['native_compatible_avc_aac']
    assert native['avc_format_count']>0 and native['aac_format_count']>0
    assert normal(identity) in normal(watch['title'])
    assert 'mariokartworld' in normal(watch['title'])
    assert watch.get('channelId') or (watch.get('provider_name')=='YouTube' and watch.get('author_url'))
    if watch.get('channelId'):assert watch['channelId']==t['channel_url'].rsplit('/',1)[-1]
    duration=float(native['duration'])
    assert abs(duration-t['duration_seconds'])<.1
    assert 'start_seconds' not in t and 'end_seconds' not in t
    assert not t['playback_verified_on_ps5']
    if number==347:
        assert duration==100 and inv['length_seconds']==96
        assert t['official_uploader_verified'] and watch['channelId']=='UCGIY_O-8vW4rfX98KlMkvRg'
        assert 'performance of "Title Theme" from the Mario Kart World game' in watch['shortDescription']
        assert 'not asserted' in t['recording_version']
    else:
        assert not t['official_uploader_verified']
        assert abs(duration-inv['length_seconds'])<=3
    checks.append(dict(title=t['title'],publication_title=watch['title'],youtube_id=ident,
        publication_seconds=duration,inventory_seconds=inv['length_seconds'],
        evidence='Public title, uploader identity and compatible codec metadata; no audio fingerprint.'))
html=(BASE/'mkworld-nintendo-music-public-inventory.html').read_text(encoding='utf-8')
assert 'In the Studio' in html and 'Crown City' in html and 'Title Theme' in html
receipt=dict(status='PASS_AS_QUALIFIED_PUBLIC_RECORDINGS',candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    distinct_additions=6,union_recordings=348,checks=checks,coverage_status='partial',
    limitations='The count does not certify all edited-master identities or the semantic aliases of the earlier342 recordings. Four archival cues match named versions and near durations; Crown City matches the named bonus and duration. The official Title Theme studio performance retains its full100seconds rather than inventing a96second cut. No listening or physical PS5 playback certification.')
(BASE/'root-independent-mkworld-final-six-review.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('PASS:6 distinct qualified recordings;348 union remains explicitly partial.')
