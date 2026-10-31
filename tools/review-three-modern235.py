"""Independently parse actual public chapter lines; never substitute next selected cue."""
from pathlib import Path
import hashlib,json,re,html
ROOT=Path(__file__).resolve().parents[1]
BASE='build/research/soundtrack-broad/modern-three-public-collections/'
PATH=BASE+'three-modern-original-public-collections-exact-source-line-candidate.json'
EXPECTED='cdea3386c74d3bc3ee23b997c12eaa02bece1100f37d54fa840e52005ef74b74'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def secs(t):return sum(int(v)*60**i for i,v in enumerate(reversed(t.split(':'))))
assert sha(PATH)==EXPECTED
doc=load(PATH);owners={e['id']:e for e in load('content/catalog.json')['entries']}
original=load(BASE+'three-modern-original-public-collections-edition-year-corrected-candidate.json')
assert sha(BASE+'three-modern-original-public-collections-edition-year-corrected-candidate.json')=='07caf53157fe2cf200df1e3937cd533929102cb1e69fb2729f4466b62bf503d9'
import copy
restored=copy.deepcopy(doc);restored.pop('variant_basis')
next(t for t in restored['entries'][1]['tracks'] if t['title']=='Dead Woods - Round 2')['source_actual_chapter_line']='[17:13 - 18:35] 8. Dead Woods - Round 2'
assert restored==original
rows=[];sources={};rooms=[];whitelist=load(BASE+'published-album-tracklists-whitelist.json')
for receiptname in ['source-fetch-receipts.json','additional-source-fetch-receipts.json']:
    for r in load(BASE+receiptname):
        if r.get('status')=='actual_html':assert sha(BASE+r['key']+'.html')==r['sha256']
for e,count in zip(doc['entries'],[142,55,38]):
    assert len(e['tracks'])==count and e['full_album_collection'] is False
    owner=owners[e['entry_id']];assert owner['title']==e['match_title'] and owner['year']==e['match_year']
    first=e['tracks'][0];watch=load(first['publication_metadata_receipt']);native=load(first['native_codec_metadata_receipt'])
    assert native['id']==first['youtube_id'] and native['native_compatible_avc_aac'] and native['avc_format_count']>0 and native['aac_format_count']>0
    assert watch['channelId']==native['channel_id'] and watch['author']==e['tracks'][0]['uploader']
    total=int(watch['lengthSeconds']);assert total==native['duration']
    description=watch['shortDescription'];lines=description.splitlines()
    tekken=count==142
    starts=[secs(m.group(1)) for line in lines if (m:=re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s+\u2022',line))] if tekken else []
    seen=set()
    for t in e['tracks']:
        line=t['source_actual_chapter_line'];assert line in lines
        if tekken:
            m=re.match(r'^(\d{1,2}:\d{2}:\d{2})\s+\u2022\s+(.*)',line);assert m
            start=secs(m.group(1));end=next((s for s in starts if s>start),total)
            assert t['source_actual_chapter_title']==m.group(2)
        else:
            m=re.match(r'^\[([\d:]+)\s*-\s*([\d:]+)\]\s*\d+\.?\s*(.*)',line);assert m
            start,end=secs(m.group(1)),secs(m.group(2));assert t['source_actual_chapter_title']==m.group(3)
        assert (start,end)==(t['start_seconds'],t['end_seconds']) and 0<=start<end<=total
        assert t['duration_seconds']==end-start and t['source_publication_duration_seconds']==total
        key=(t['youtube_id'],start,end);assert key not in seen;seen.add(key)
        assert t['official_uploader_verified'] is False and t['playback_verified_on_ps5'] is False
        if count==142:
            assert '2015, 2017-2021' in t['recording_version'] and 'recording_year' not in t
            albumrows=[x for a in ['tekken7-apple.html','tekken7-vol2-apple.html'] for x in whitelist.get(a,[])]
            match=[r for r in albumrows if r['title']==t['title'] and r['source_page']==t['published_title_source']]
            assert match and match[0]['duration_ms']==t['published_duration_ms']
        if count==55:assert 'Dan Forden' not in t['creator']
        if count==38:
            albumrows=whitelist['forza-apple.html'];assert any(r['title']==t['title'] and r['source_page']==t['published_title_source'] for r in albumrows)
            assert t['creator']=='Kaveh Cohen and Michael Nielsen'
        rows.append(dict(entry_id=e['entry_id'],title=t['title'],source_line=line,start=start,end=end))
    rooms.append(dict(entry_id=e['entry_id'],count=count,publication=watch['title'],channel=native['channel_id'],duration=total,all_actual_source_bounds_reconstructed=True))
for p in (ROOT/BASE).glob('*'):
    if p.suffix in ('.html','.json') and 'candidate' not in p.name and 'review' not in p.name:sources[p.relative_to(ROOT).as_posix()]=sha(p.relative_to(ROOT))
assert len(rows)==235
receipt=dict(status='PASS',candidate_path=PATH,candidate_sha256=EXPECTED,rooms=rooms,tracks=rows,source_files_sha256=sources,observations=['All235 display titles, credits and edition qualifiers read. All235 ranges independently reconstructed from actual watch-description timestamps; Tekken ends use the next actual source chapter, including any held chapters, rather than the next selected track. MKX/FM6 preserve explicit source range ends; gaps are not claimed to be continuous retail audio.','Tekken142 published titles and label durations match the two actual Apple tracklists. Console/FatedRetribution/SeasonPass2015,2017-2021 context remains explicit on the2015 original game entry; no invented2015-only recording year.','MKX55 excludes short incidental success/failure effects and curator medleys. Uploader-only DanForden blanket attribution is not repeated as per-cue composition; studio/contributors scope remains qualified.','FM638 names match actual published original album and Cohen/Nielsen primary interview credit; source remains public archive rather than official uploader delivery.','All3 actual native receipts have positive AVC/AAC format selections. Partial public-collection flags remain false for completeness; no decoded listening, retail-master fingerprint or physicalPS5 playback claim.'],master_modified=False)
out=BASE+'independent-two-hundred-thirty-five-public-collections-review.json'
(ROOT/out).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(out,sha(out))
