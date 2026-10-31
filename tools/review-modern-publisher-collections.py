from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/soundtrack-broad/modern-public-albums'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
specs=[('bastion-transistor-pyre84-publisher-candidate.json','5a2c38e89f7bac309646f22688cbf15d1f5cd88482a0de1582f6b366e73f88c3',84),('doom-silksong-hollowknight-celeste131-public-candidate.json','8f38b16b27c84d9009b0c0a4c55fa4dc5861b8b59d0a5ad144a7af6a12197221',131)]
for filename,digest,total in specs:
    path=BASE/filename;assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    data=read(path);checks=[]
    for e in data['entries']:
        for t in e['tracks']:
            pub=read(ROOT/t['publication_metadata_receipt']);pub=pub.get('publication',pub)
            n=read(ROOT/t['native_codec_metadata_receipt'])
            assert pub['title']==t['primary_published_title']
            assert pub.get('channelId') in t['channel_url']
            assert n['id']==t['youtube_id'] and n['native_compatible_avc_aac']
            assert t['rights'] and t['creator'] and not t['playback_verified_on_ps5']
            if 'start_seconds' in t:
                line=t['source_actual_chapter_line'];assert line in pub['shortDescription']
                clock=re.search(r'\d{1,2}:\d{2}(?::\d{2})?',line).group();start=0
                for part in clock.split(':'):start=start*60+int(part)
                assert start==t['start_seconds'] and 0<=start<t['end_seconds']<=float(n['duration'])+1
                assert t['duration_seconds']==t['end_seconds']-start
            else:assert abs(float(n['duration'])-t['duration_seconds'])<1
            if e['match_title']=='Hollow Knight':assert not t['official_uploader_verified'] and t['uploader']=='MindsAblaze2'
            else:assert t['official_uploader_verified']
            checks.append(dict(game=e['match_title'],title=t['title'],creator=t['creator'],roles=t.get('additional_recording_roles',{}),youtube_id=t['youtube_id']))
    assert len(checks)==total
    out=BASE/('root-independent-modern'+str(total)+'-review.json')
    out.write_text(json.dumps(dict(status='PASS',candidate_sha256=digest,tracks=total,checks=checks,
        scope='Actual source-published album chapter lines or individual artist publications, native codec metadata, valid durations and declared original-game versions. Publisher/composer and archival uploader remain distinct; named guests/arrangers not assigned wholesale cue composition.',
        limitations='Available published album inventories, not every possible game stem; no exact-master fingerprint, full listening session or physical PS5 playback claim. No further unavailable/master/order chase.'),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(out.name,total,'PASS')
