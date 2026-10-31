"""Verify exact authoring/runtime image consistency without claiming completeness."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
catalog=read('content/catalog.json');history=read('content/human-history.json');manifest=read('assets/images/manifest.json')
urls=set()
for entry in catalog['entries']+history['entries']:
    for owner in [entry]+entry.get('editorial_features',[]):
        urls.update(i['url']for i in owner.get('images',[])if i.get('url'))
missing=[]
for url in urls:
    for field in ['images','previews']:
        path=manifest.get(field,{}).get(url)
        if not path or not (ROOT/path).is_file():missing.append({'url':url,'field':field})
assert not missing,missing
runtimepath='build/runtime-preview/content/catalog.json';runtime=read(runtimepath)
assert len(catalog['entries'])==len(runtime['entries'])
assert runtime['source_catalog_sha256']==sha('content/catalog.json')
assert len((ROOT/runtimepath).read_bytes())<16<<20
assert len({e['id']for e in catalog['entries']})==len(catalog['entries'])
by_id={e['id']:e for e in catalog['entries']};nintendo=by_id['daily-09-23']
assert len(nintendo['body'])==19 and len(nintendo['images'])==21
assert nintendo['videos'][0]['story_paragraph']==17
recent=read('content/expansion/recent-six-reviewed-additions.json')['entries']
for row in recent:
    assert by_id[row['id']]['body']==row['body']
    assert by_id[row['id']]['preferred_image']==0
    assert by_id[row['id']]['images'][0]['url']==row['images'][0]['url']
assert len(by_id['wikipedia-32307637']['soundtrack']['tracks'])==211
assert len(by_id['wikipedia-79613753']['soundtrack']['tracks'])==107
assert by_id['wikipedia-79613753']['soundtrack']['coverage_status']=='partial'
report={'status':'PASS_ACTUAL_CATALOG_RUNTIME_AND_LOCAL_IMAGE_INTEGRITY','entries':len(catalog['entries']),
 'culture':len(history['entries']),'required_unique_image_urls':len(urls),'manifest_full_images':len(manifest['images']),
 'missing_full_or_preview':0,'runtime_bytes':(ROOT/runtimepath).stat().st_size,'runtime_sha256':sha(runtimepath),
 'catalog_sha256':sha('content/catalog.json'),'reviewed_recent_games':len(recent),'reviewed_recent_developer_films':sum(len(r['videos'])for r in recent),
 'nintendo':{'narrative_paragraphs':19,'image_records':21,'video_id':nintendo['videos'][0]['youtube_id'],'video_after_paragraph':17},
 'botw_verified_cues':211,'bananza_verified_partial_cues':107,'not_a_complete_editorial_claim':True}
destination=ROOT/(sys.argv[1]if len(sys.argv)>1 else 'build/research/editorial-checkpoint-integrity.json')
destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2))
