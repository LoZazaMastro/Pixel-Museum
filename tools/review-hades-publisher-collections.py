from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/soundtrack-broad/modern-public-albums'
path=base/'hades-two-publisher-albums82-candidate.json'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
digest=hashlib.sha256(path.read_bytes()).hexdigest()
assert digest=='f4c01f8a1c9af66584b9e4ad9607949fe8f5387c312c777bd9c4ff2c22289626'
d=read(path);rows=[]
assert [len(e['tracks'])for e in d['entries']]==[30,52]
for e in d['entries']:
    last=0
    for t in e['tracks']:
        pub=read(ROOT/t['publication_metadata_receipt'])['publication']
        n=read(ROOT/t['native_codec_metadata_receipt'])
        assert pub['author']=='Supergiant Games' and pub['channelId'] in t['channel_url']
        assert pub['title']==t['primary_published_title']
        assert n['native_compatible_avc_aac'] and n['id']==t['youtube_id']
        line=t['source_actual_chapter_line'];assert line in pub['shortDescription']
        clock=re.search(r'\d{2}:\d{2}(?::\d{2})?',line).group();start=0
        for part in clock.split(':'):start=start*60+int(part)
        assert start==t['start_seconds']==last
        assert 0<=start<t['end_seconds']<=float(n['duration'])+1
        assert t['end_seconds']-start==t['duration_seconds']
        assert t['creator']=='Darren Korb' and 'Music and Lyrics by Darren Korb' in pub['shortDescription']
        assert t['rights'] and not t['playback_verified_on_ps5']
        if e['match_year']==2020 and 'orchestral_arrangement' in t['additional_recording_roles']:
            assert t['title'].startswith(('On the Coast','In the Blood'))
        last=t['end_seconds'];rows.append({'game':e['match_title'],'title':t['title'],'start':start,'end':last})
    assert abs(last-float(n['duration']))<1
receipt=dict(status='PASS',candidate_sha256=digest,selectable_passages=82,checks=rows,
    scope='Two original Supergiant Games full album publications; actual 30/52 chapter lines, native codec metadata, continuous valid intervals and primary publisher credit roles. No additional missing-master/order hunt.',
    limitations='No audio fingerprint, full listening or physical PS5 playback claim. Album inventories do not imply every unreleased stem.')
(base/'root-independent-hades82-review.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS: Hades30 + HadesII52 actual publisher chapters.')
