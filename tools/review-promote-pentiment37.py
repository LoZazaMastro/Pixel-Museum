"""Independent metadata/primary-credit review and guarded NEXT-only promotion."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE='build/research/soundtrack-broad/modern-next-four/'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
path=BASE+'pentiment-thirty-seven-official-album-candidate.json'
expected='7a610b03f199ad72440a0a2478499d1b47db0aea9df5883e76a5e9103993c447'
assert sha(path)==expected
doc=load(path);entry=doc['entries'][0];tracks=entry['tracks']
assert len(tracks)==37 and entry['full_album_collection'] is True
for row in doc['source_receipts']:assert sha(row['path'])==row['sha256']
flat=load(BASE+'pentiment-official-album-flat.json')
assert len(flat['entries'])==37 and flat['title']=='Pentiment (Original Soundtrack)'
seen=set();rows=[]
for n,(t,f) in enumerate(zip(tracks,flat['entries'])):
    w=load(t['publication_metadata_receipt']);native=load(t['native_codec_metadata_receipt'])
    assert t['youtube_id']==native['id']==f['id']
    assert Path(t['publication_metadata_receipt']).stem==t['youtube_id'] and w['status']=='OK'
    assert t['title']==w['title']==native['title']==f['title']
    assert t['duration_seconds']==int(w['lengthSeconds'])==native['duration']
    assert t['creator']==('Lingua Ignota' if n==36 else 'Alkemie')
    assert t['creator'] in w['author'] and w['channelId']==native['channel_id']
    assert t['channel_url'].endswith(w['channelId'])
    description=w['shortDescription']
    for literal in ['Provided to YouTube by Virgin Music Group','2022 Microsoft Studios Music','Released on: 2022-12-24',t['title']+' · '+t['creator']]:assert literal in description
    assert native['native_compatible_avc_aac'] and native['avc_format_count']>0 and native['aac_format_count']>0
    assert t['published_album_track_number']==n+1 and t['playback_verified_on_ps5'] is False
    assert t['youtube_id'] not in seen;seen.add(t['youtube_id'])
    rows.append(dict(ordinal=n+1,title=t['title'],recording_artist=t['creator'],seconds=t['duration_seconds'],video=t['youtube_id']))
primary=(ROOT/(BASE+'pentiment-alkemie-official-album.html')).read_text(encoding='utf8')
for text in ['curated, composed, and arranged','Hildegard','Josquin','The Parting','Tracy Cowart']:assert text in primary
assert 'not an exclusive underlying-composer attribution' in tracks[0]['artist_credit_scope']
owner=next(e for e in load('content/catalog.json')['entries'] if e['id']==entry['entry_id'])
assert owner['title']==entry['match_title']=='Pentiment' and owner['year']==2022
receipt_path=BASE+'independent-thirty-seven-pentiment-album-review.json'
receipt=dict(status='PASS',candidate_path=path,candidate_sha256=expected,tracks=rows,source_receipts_verified=len(doc['source_receipts']),observations=['All37 actual label-delivered titles and recording artists read and compared in order with the actual37-item album; each watch description identifies Virgin Music Group and2022 Microsoft Studios Music.','All37 native receipts contain positive AVC/AAC formats. The27second Parting is a real album cue; Ein Traum is credited to Lingua Ignota.','Alkemie primary page explicitly describes curating, composition and historical arrangements, including named underlying authors. The ensemble is not asserted to be the exclusive underlying composer. Full flag covers this published37track album, not every game sound file.','Metadata/publication provenance review only; no audio fingerprint, decoded listening or physicalPS5 playback claim.'],master_modified=False)
(ROOT/receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
music='content/expansion/soundtrack-multitrack-priority-overrides.json'
oldsha='c319cbc769ca2c29f8283654caca2df06b1a4873ea330b560d9156fa4bcf584a'
assert sha(music)==oldsha
source=load(music);before=copy.deepcopy(source['entries']);assert len(before)==75
assert not any(e['entry_id']==entry['entry_id'] for e in before)
new=copy.deepcopy(entry);new['independent_review_receipt']=receipt_path;source['entries'].append(new)
assert source['entries'][:75]==before
temp=ROOT/(music+'.tmp');temp.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(ROOT/music)
report=dict(status='PASS_SOURCE_ONLY_PROMOTION',source_entries=76,source_sha256=sha(music),previous_source_sha256=oldsha,prior75_exactly_preserved=True,independent_review=receipt_path,independent_review_sha256=sha(receipt_path),master_modified=False,runtime_modified=False)
(ROOT/(BASE+'source76-promotion.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
