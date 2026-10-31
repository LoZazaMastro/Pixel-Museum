"""Review four real archive publications, preserving three honest component suites."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];BASE='build/research/soundtrack-broad/switch-compilations-tour-next/'
PATH=BASE+'three-switch-compilation-tour-public-music-alternate-id-corrected-candidate.json'
EXPECTED='137da6875537b846b257c88d8909bbce8e572d7236464bd2e518f51dc5092abf'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def secs(s):return sum(int(v)*60**i for i,v in enumerate(reversed(s.split(':'))))
assert sha(PATH)==EXPECTED
d=load(PATH);owners={e['id']:e for e in load('content/catalog.json')['entries']}
for r in load(BASE+'primary-source-fetch-receipts.json'):
    if r['status']=='actual_html':assert sha(BASE+r['key']+'.html')==r['sha256']
sources={};rows=[];rooms=[]
for e,count in zip(d['entries'],[107,3,103]):
    assert len(e['tracks'])==count and e['full_album_collection'] is False
    owner=owners[e['entry_id']];assert owner['title']==e['match_title'] and owner['year']==e['match_year']
    seen=set()
    for t in e['tracks']:
        watchpath=t['publication_metadata_receipt'];nativepath=t['native_codec_metadata_receipt']
        w=load(watchpath);v=load(nativepath);sources[watchpath]=sha(watchpath);sources[nativepath]=sha(nativepath)
        assert v['id']==t['youtube_id'] and int(w['lengthSeconds'])==v['duration']==t['source_publication_duration_seconds']
        assert v['channel_id']==w['channelId'] and t['channel_url'].endswith(v['channel_id']) and t['uploader']==w['author']
        assert v['native_compatible_avc_aac'] and v['avc_format_count']>0 and v['aac_format_count']>0
        # Whitespace at description line ends is not part of an actual cue name.
        line=t['source_actual_chapter_line'];lines=[line.strip() for line in w['shortDescription'].splitlines()]
        assert line.strip() in lines
        if count==3:
            m=re.search(r'([\d:]+)$',line);assert m
            starts=[secs(match.group(1)) for s in lines if (match:=re.search(r'^Super Mario (?:64|Sunshine|Galaxy):\s*([\d:]+)$',s))]
        else:
            m=re.match(r'([\d:]+)',line);assert m
            starts=[secs(match.group(1)) for s in lines if (match:=re.match(r'^([\d:]+)\s+(?:-|:|[A-Za-z])',s))]
        start=secs(m.group(1));end=next((s for s in starts if s>start),int(w['lengthSeconds']))
        assert (t['start_seconds'],t['end_seconds'])==(start,end) and 0<=start<end<=v['duration']
        assert t['duration_seconds']==end-start
        key=(t['youtube_id'],start,end);assert key not in seen;seen.add(key)
        assert t['official_uploader_verified'] is False and t['playback_verified_on_ps5'] is False
        if count==107:
            assert t['component_game'] in ['Super Mario 3D World',"Bowser's Fury"]
            assert t['original_component_release_year']==(2013 if t['component_game']=='Super Mario 3D World' else 2021)
        if count==3:
            assert t['creator'] in ['Koji Kondo','Koji Kondo, Shinobu Tanaka','Mahito Yokota, Koji Kondo']
            assert 'collection' in t['title'] and 'component-score collection' in t['credit_scope']
        if count==103:assert t['individual_cue_authorship_documented'] is False and t['original_component_release_year']==2019
        rows.append(dict(entry_id=e['entry_id'],title=t['title'],source_line=line,start=start,end=end,component=t.get('component_game')))
    rooms.append(dict(entry_id=e['entry_id'],selected_passages=count,source_publications=len({t['youtube_id'] for t in e['tracks']})))
assert len(rows)==213 and len(sources)==8
for n in ['allstars-primary.html','world-fury-primary.html','tour-primary.html','component-composer-source-reuse.json']:sources[BASE+n]=sha(BASE+n)
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,rooms=rooms,tracks=rows,source_files_sha256=sources,observations=['All213 display titles/edition qualifiers read; timestamps independently reconstructed from actual source descriptions and next actual source chapters, not invented subdivisions. Four distinct public source publications have positive nativeAVC/AAC metadata.','World/Fury107 consists of77 original2013score passages plus30BowserFury2021 passages. Original component year and reused compilation context remain explicit; unknown capture hardware is not presented as verifiedSwitch output. Overlapping31chapter alternate archive is excluded.','AllStars has only the three actual long source chapters:Mario64,Sunshine,Galaxy. They remain titled whole component-score collections, with documented component-game composer rosters rather than falsely advertised individual tracks. No missing chapter boundaries invented.','Tour103 retains explicit original mobile-game context and later in-game courses/arrangements; SNES/DS/Wii course names do not claim capture from the original consoles. Nintendo organizational display is qualified and individual cue composers are unresolved.','Partial flags are retained on all3collections. Short named source cues are real bounded passages, not a claim of213distinct compositions, retail-master equivalence, all game files or physicalPS5 playback.'],master_modified=False)
out=BASE+'independent-two-hundred-thirteen-public-collection-review.json';(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))

