"""Independent, bounded publication review; no audio fingerprint/order perfection claim."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
results=[]
for rel in ['classic-trilogy-complete/six-public-classic-score-collections-candidate.json','spider-complete/three-public-albums67-candidate.json']:
    path=BASE/rel; data=read(path); rows=[]
    classic=rel.startswith('classic')
    assert len(data['entries'])==(6 if classic else 3)
    for e in data['entries']:
        assert e['match_title'] and e['composer']
        if classic: assert not e['full_album_collection']
        for t in e['tracks']:
            assert t['title'] and t['creator'] and t['rights']
            assert not t.get('playback_verified_on_ps5',False)
            native=read(ROOT/t['native_codec_metadata_receipt'])
            assert native['id']==t['youtube_id'] and native['native_compatible_avc_aac']
            raw=read(ROOT/t.get('publication_metadata_receipt',t.get('verification_receipt')))
            pub=raw.get(t['youtube_id'],raw.get('publication',raw))
            if t.get('primary_published_title'):assert pub['title']==t['primary_published_title']
            else:
                assert t['recording_release_year']==2022 and t['creator']=='Stewart Copeland'
                assert t['independent_semantic_status']=='PASS_EXACT_RECORDING_SOURCE_CONTEXT_AND_NATIVE_CODEC'
                assert (ROOT/t['independent_review_receipt']).is_file()
            if 'start_seconds' in t:
                start,end=t['start_seconds'],t['end_seconds']
                assert 0<=start<end<=float(native['duration'])+1
                assert end-start==t['duration_seconds']
                description=pub['shortDescription']
                assert t['source_actual_chapter_title'] in description
                matches=[]
                for line in description.splitlines():
                    clock=re.search(r'\b\d{1,2}:\d{2}(?::\d{2})?\b',line)
                    if clock:matches.append((clock.group(),line))
                times=[]
                for clock,title in matches:
                    seconds=0
                    for part in clock.split(':'):seconds=seconds*60+int(part)
                    if t['source_actual_chapter_title'] in title:times.append(seconds)
                assert start in times,(t['title'],start,times)
                assert not t.get('official_uploader_verified')
            else:
                assert abs(float(native['duration'])-t['duration_seconds'])<1
            if not classic:
                assert t['official_uploader_verified']
                assert pub.get('channelId') and pub['channelId'] in t['channel_url']
                assert t['recording_year']==e['match_year']
            rows.append({'game':e['match_title'],'title':t['title'],'youtube_id':t['youtube_id']})
    receipt={'status':'PASS','candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'entries':len(data['entries']),'selectable_tracks':len(rows),'checks':rows,'scope':'Actual public publication identity, native AVC/AAC availability, chapter timestamps where used, original-game/version labels and creator rights. Available recordings accepted without pursuing missing masters or exact album ordering.','limitations':'No audio fingerprint, full listening session or physical PS5 playback certification. Classic archives remain partial; Spider albums cover published inventories, not every unreleased game stem.'}
    out=path.parent/'root-independent-public-collections-review.json'
    out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    results.append((str(out.relative_to(ROOT)),len(rows),receipt['candidate_sha256']))
print(json.dumps(results,indent=2))
