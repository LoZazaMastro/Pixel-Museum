"""Peer the thirteen-track digital edition, then append four reviewed NEXT rooms."""
from pathlib import Path
import copy,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BASE='build/research/soundtrack-broad/modern-following/'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
path=BASE+'helldivers2-thirteen-official-album-candidate.json';expected='be6fca0d04871eb2bd636bc7c7acaa03e0fc401699973ff624d5475d5b0f4a30'
assert sha(path)==expected
doc=load(path);e=doc['entries'][0];tracks=e['tracks']
assert len(tracks)==13 and e['full_album_collection'] is True
for s in doc['source_receipts']:assert sha(s['path'])==s['sha256']
label=load(BASE+'helldivers2-label-album.json');album=label['results'][0];rows=[x for x in label['results'] if x.get('wrapperType')=='track']
assert album['collectionId']==1811175755 and len(rows)==13 and album['releaseDate'].startswith('2025-05-02')
playlist=load(BASE+'helldivers2-sony-official-playlist.json')
assert len(playlist['entries'])==16 and playlist['channel_id']=='UCGkX_HCD_T5XOwxi_KR6YoQ'
allowed={x['id'] for x in playlist['entries']};seen=set();report=[]
for n,(t,raw) in enumerate(zip(tracks,rows)):
    assert t['title']==raw['trackName'] and t['creator']==raw['artistName'] and t['published_album_track_number']==raw['trackNumber']==n+1
    assert t['youtube_id'] in allowed and t['youtube_id'] not in seen;seen.add(t['youtube_id'])
    w=load(t['publication_metadata_receipt']);v=load(t['native_codec_metadata_receipt'])
    assert t['youtube_id']==v['id'] and t['title'] in w['title']==v['title']
    assert int(w['lengthSeconds'])==v['duration']==t['duration_seconds']
    assert 'Helldivers 2' in w['shortDescription']
    if n==11:
        assert t['creator']=='Ross Tregenza' and 'Ross Tregenza' in w['title']
        assert 'Music by Wilbert Roget, II' in w['shortDescription']
    else:assert t['creator'] in w['shortDescription']
    assert w['channelId']==v['channel_id'] and t['channel_url'].endswith(w['channelId'])
    if n==6:
        for literal in ['Provided to YouTube by Milan Records','2024 Sony Interactive Entertainment','Released on: 2025-05-02']:assert literal in w['shortDescription']
        assert w['author']=='Wilbert Roget, II - Topic'
    else:assert w['author']=='SonySoundtracksVEVO' and w['channelId']==playlist['channel_id']
    assert v['native_compatible_avc_aac'] and v['avc_format_count']>0 and v['aac_format_count']>0
    assert t['official_uploader_verified'] is True and t['playback_verified_on_ps5'] is False
    assert t['original_game_year']==2024 and t['recording_album_release_year']==2025
    report.append(dict(ordinal=n+1,title=t['title'],recording_artist=t['creator'],video=t['youtube_id'],seconds=t['duration_seconds'],channel=w['channelId']))
primary=(ROOT/(BASE+'helldivers2-milan-primary.html')).read_text(encoding='utf8')
assert 'Wilbert Roget' in primary and 'Ross Tregenza' in primary
assert len(doc['excluded_playlist_items'])==3 and not seen&{t['youtube_id'] for t in doc['excluded_playlist_items']}
receipt_path=BASE+'independent-thirteen-official-helldivers2-review.json'
receipt=dict(status='PASS',candidate_path=path,candidate_sha256=expected,tracks=report,source_receipts_verified=len(doc['source_receipts']),observations=['All13 titles and exact per-track recording artists match the actual Apple digital label album1811175755 released2May2025. ElevenWilbertRogetII and twoRossTregenza deliveries remain correctly assigned.','SonySoundtracksVEVO public playlist16 has exactly these13 music entries plus two trailers and one unavailable item, all three excluded. The IlluminateCult is a legitimate WilbertRogetIITopic Milan/Sony provided-label delivery with explicit2025release, rather than a falsely claimed SonyVEVO upload.','March of the Helldivers has a generic Sony description crediting WilbertRogetII, while the actual video title and exact Apple label credit both identify RossTregenza. Display follows those two explicit track-level credits; the conflicting description is not inherited as an invented co-composer credit.','Actual label primary page corroborates WilbertRogetII and additional music byRossTregenza. All13 native receipts contain positiveAVC/AAC metadata. No downloaded audio, fingerprint or physicalPS5 playback claim.','Full flag covers this explicitly dated13track digital edition, including Illuminate; it does not promise every future live-service update or separateEP.'],master_modified=False)
(ROOT/receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
music='content/expansion/soundtrack-multitrack-priority-overrides.json';oldsha='26db196e074924347ab6639959b0440cfec108b15887ea7f6bf111ac220697d1'
assert sha(music)==oldsha
source=load(music);before=copy.deepcopy(source['entries']);assert len(before)==76
plans=[('build/research/soundtrack-broad/modern-three-public-collections/three-modern-original-public-collections-exact-source-line-candidate.json','cdea3386c74d3bc3ee23b997c12eaa02bece1100f37d54fa840e52005ef74b74','build/research/soundtrack-broad/modern-three-public-collections/independent-two-hundred-thirty-five-public-collections-review.json'),(path,expected,receipt_path)]
for cp,ch,rp in plans:
    assert sha(cp)==ch and load(rp)['status']=='PASS' and load(rp)['candidate_sha256']==ch
    for entry in load(cp)['entries']:
        assert not any(old['entry_id']==entry['entry_id'] for old in source['entries'])
        entry=copy.deepcopy(entry);entry['independent_review_receipt']=rp
        source['entries'].append(entry)
assert len(source['entries'])==80 and source['entries'][:76]==before
temp=ROOT/(music+'.tmp');temp.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(ROOT/music)
out=dict(status='PASS_NEXT_SOURCE_ONLY_PROMOTION',source_entries=80,source_sha256=sha(music),previous_source_sha256=oldsha,prior76_exactly_preserved=True,added_recordings=248,new_rooms=4,master_modified=False,runtime_modified=False,helldivers_review_sha256=sha(receipt_path),modern235_review_sha256=sha(plans[0][2]))
(ROOT/(BASE+'source80-promotion.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
