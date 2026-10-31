"""Check available KHIII publications and primary cue credits, not album perfection."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad/kingdom-hearts-complete'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
path=BASE/'kh3-public136-plus2-vocals-primary-roles-v2-candidate.json'
digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest=='ecc3212bb7b9d31386bf2baea03561a8fb51e9e200198a69d018e156777b5874'
candidate=read(path);entry=candidate['entries'][0];tracks=entry['tracks']
assert len(tracks)==138 and len({t['youtube_id']for t in tracks})==138
assert entry['coverage_status']=='partial' and not entry['full_album_collection']
source=candidate['publisher_primary_html_receipt']
assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256']
primary={(t['disc'],t['disc_track']):t for t in read(BASE/'kh3-publisher-original-per-cue-roles.json')['tracks']}
names={'宇多田ヒカル':'Hikaru Utada','下村 陽子':'Yoko Shimomura','石元 丈晴':'Takeharu Ishimoto',
       '関戸 剛':'Tsuyoshi Sekito','島 翔太朗':'Shotaro Shima','福井 健一郎':'Kenichiro Fukui','鈴木 克崇':'Yoshitaka Suzuki'}
checks=[]
for t in tracks[:136]:
    disc=t['album_disc'];assert 1<=disc<=7
    cue=primary[(disc,t['disc_track_number'])]
    assert cue['published_credit_line']==t['publisher_per_cue_credit_line']
    assert cue['title']==t['publisher_original_title']
    composition=cue['published_roles']['作曲']
    translated=', '.join(names.get(n,n)for n in composition.split('、'))
    assert t['creator']==translated
    if '編曲'in cue['published_roles']:
        assert t['additional_recording_roles']['arrangement_original_publisher_names']==cue['published_roles']['編曲'].split('、')
    native=read(ROOT/t['native_codec_metadata_receipt'])
    raw=read(ROOT/t['publication_metadata_receipt']);watch=raw.get('publication',raw)
    assert native['id']==t['youtube_id'] and native['native_compatible_avc_aac']
    assert native['avc_format_count']>0 and native['aac_format_count']>0
    assert abs(float(native['duration'])-t['duration_seconds'])<.1
    assert watch['title']==t['primary_published_title']
    assert watch.get('channelId') or (watch.get('provider_name')=='YouTube' and watch.get('author_url'))
    assert not t['playback_verified_on_ps5']
    checks.append(dict(title=t['title'],youtube_id=t['youtube_id'],creator=t['creator'],primary_cue=[disc,t['disc_track_number']]))
assert [t['youtube_id']for t in tracks[-2:]]==['GPI-pLBjmf4','vZGgZotzvXs']
assert all(t['creator']and t['rights']for t in tracks)
receipt=dict(status='PASS',candidate_sha256=digest,available_score_recordings=136,english_vocal_supplements=2,
    checks=checks,scope='Available public III/Re Mind music.136 publication/AVC/AAC identities and per-cue first-party composition/arrangement fields checked. No pursuit of unavailable Japanese vocal variants or exact album order.',
    limitations='Public metadata establishes the declared recordings, not audio fingerprints or physical PS5 playback. Partial collection; no claim that every game cue or edition is present.')
(BASE/'root-independent-kh3-available-score-review.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS:136 available score recordings +2 English vocals, primary cue-specific credits retained.')
