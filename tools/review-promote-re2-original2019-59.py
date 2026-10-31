"""Review actual 2019 chapter identities and append a source-only NEXT room."""
from pathlib import Path
import copy,hashlib,json,re,unicodedata
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/soundtrack-broad/modern-following/'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def secs(s):return sum(int(v)*60**i for i,v in enumerate(reversed(s.split(':'))))
def normalized(s):return ''.join(c.lower() for c in unicodedata.normalize('NFKC',s) if c.isalnum())
path=BASE+'resident-evil-two-2019-fifty-nine-visible-label-artists-candidate.json';expected='85defc1c58eca9983d7c297f3d53a5b48b982429b148ddaf7dc0486919f0c145'
assert sha(path)==expected
doc=load(path);e=doc['entries'][0];tracks=e['tracks'];assert len(tracks)==59 and e['full_album_collection'] is False
for s in doc['source_receipts']:assert sha(s['path'])==s['sha256']
label=load(BASE+'re2-2019-label-album.json');assert label['results'][0]['collectionId']==1451575319
labeltracks=[r for r in label['results'] if r.get('wrapperType')=='track'];assert len(labeltracks)==59
w=load(tracks[0]['publication_metadata_receipt']);v=load(tracks[0]['native_codec_metadata_receipt'])
assert v['id']=='MJcCyOD62M8' and v['native_compatible_avc_aac'] and v['avc_format_count']>0 and v['aac_format_count']>0
assert int(w['lengthSeconds'])==v['duration']==10443 and 'Remake' in w['title']
assert w['channelId']==v['channel_id']=='UC4zd43CVepW6h_Fc_HmUVaw'
lines=w['shortDescription'].splitlines();actual=[]
for line in lines:
    m=re.match(r'^(.*?)\s+-\s+([\d:]+)\s*$',line)
    if m:actual.append((m.group(1),secs(m.group(2)),line))
assert len(actual)==59
rows=[]
for n,(t,r,(title,start,line)) in enumerate(zip(tracks,labeltracks,actual)):
    assert t['title']==r['trackName'] and t['label_artist_credit']==r['artistName']
    assert t['published_album_track_number']==r['trackNumber']==n+1
    assert normalized(t['title'])==normalized(title)
    assert t['source_actual_chapter_title']==title and t['source_actual_chapter_line']==line
    end=actual[n+1][1] if n+1<len(actual) else 10443
    assert (t['start_seconds'],t['end_seconds'])==(start,end) and t['duration_seconds']==end-start
    assert t['source_publication_duration_seconds']==10443
    assert t['creator']==('Cody Matthew Johnson feat. Shim' if n==0 else r['artistName'])
    assert t['original_game_year']==t['recording_album_release_year']==2019
    assert t['official_uploader_verified'] is False and t['playback_verified_on_ps5'] is False
    rows.append(dict(ordinal=n+1,title=t['title'],raw_label_artist=t['label_artist_credit'],source_title=title,start=start,end=end))
publisher=(ROOT/(BASE+'re2-capcom-release.html')).read_text(encoding='utf8')
creator=(ROOT/(BASE+'re2-saudade-creator.html')).read_text(encoding='utf8')
assert '59' in publisher and '2019' in publisher and 'Saudade' in publisher
assert 'Cody Matthew Johnson' in creator and 'Shim' in creator and 'Saudade' in creator
owner=next(x for x in load('content/catalog.json')['entries'] if x['id']==e['entry_id'])
assert owner['title']==e['match_title'] and owner['year']==e['match_year']==2019
rp=BASE+'independent-fifty-nine-re2-original2019-passages-review.json'
receipt=dict(status='PASS',candidate_path=path,candidate_sha256=expected,tracks=rows,source_receipts_verified=len(doc['source_receipts']),observations=['All59 titles and order read and matched against the actual Apple digital album1451575319. Every original description line and timestamp was independently parsed; ends derive from the next actual chapter or actual10443second source duration. Punctuation-only title differences normalize identically; raw source titles remain exact.','Capcom primary release confirms59tracks including Saudade in2019. Original2019remake context is explicit throughout; no1998recording association.','Saudade creator display is corroborated by the original Emperia creator page; duplicated raw label string is retained without importing duplicated display. All58 other actual Japanese label artist credits are exposed verbatim in creator display as well as preserved raw; no invented romanization or exclusive composer role. The room-level English collective title remains unchanged.','Public archive channel and native positiveAVC/AAC metadata match.59published titles available does not establish audio-fingerprint identity, retail-master equivalence, every game file or physicalPS5 playback; partial flag is preserved.'],master_modified=False)
(ROOT/rp).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
music='content/expansion/soundtrack-multitrack-priority-overrides.json';oldsha='cffc6f3c8975169a31320715fa1f36acc8de1321394c9f2b895c7b2754027418'
assert sha(music)==oldsha
s=load(music);before=copy.deepcopy(s['entries']);assert len(before)==80 and not any(x['entry_id']==e['entry_id'] for x in before)
e=copy.deepcopy(e);e['independent_review_receipt']=rp;s['entries'].append(e);assert s['entries'][:80]==before
temp=ROOT/(music+'.tmp');temp.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(ROOT/music)
report=dict(status='PASS_NEXT_SOURCE_ONLY_PROMOTION',source_entries=81,source_sha256=sha(music),previous_source_sha256=oldsha,prior80_exactly_preserved=True,added_recordings=59,review=rp,review_sha256=sha(rp),master_modified=False,runtime_modified=False)
(ROOT/(BASE+'source81-promotion.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2))
