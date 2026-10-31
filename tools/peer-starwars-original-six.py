"""Independent source/identity/native-image checks; no catalogue mutation."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/story-text-profile/priority-original-illustrations'
path=BASE/'six-starwars-original-illustrations-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(path)=='5a8c8b967805073a60405012787c24e735671ef17e712ccd307981a93de17d54'
c=json.loads(path.read_text(encoding='utf8'))
catalog=ROOT/'content/catalog.json'
entries={e['id']:e for e in json.loads(catalog.read_text(encoding='utf8'))['entries']}
sources=[]
for r in c['source_receipts']:
    assert sha(ROOT/r['path'])==r['sha256']
    sources.append(dict(r,actual_json_read=True))
identities={'wikipedia-57645522':('1172380',2019,'Fallen Order'),
            'wikipedia-22112788':('1058020',2004,'Battlefront (Classic, 2004)')}
associations={
 'wikipedia-57645522':[
  'Cal with his blue lightsaber and BD-1 identifies the 2019 protagonist and companion, not the older bearded Survivor appearance.',
  'Cal and BD-1 at an Imperial terminal illustrate companion and character design. Not claimed as a development or recording-session photograph.',
  'Cal faces an electrified-staff Purge Trooper, illustrating original-game combat/visual presentation discussed in reception.'],
 'wikipedia-22112788':[
  'Original classic first-person Kamino battle, blue original HUD and clone equipment identify the 2004 Pandemic game, not the 2015 reboot/2024 compilation.',
  'Geonosis Republic walker and original HUD illustrate conquest battles and vehicles, with no claim of an original launch-platform screenshot.',
  'Gungan shield generators at Naboo illustrate the major film battles discussed in the reception paragraph. No award/sales proof implied.']}
seen=set();pixels=set();media=[];guards=[]
for eid,images in c['entries'].items():
    e=entries[eid];g=c['article_guards'][eid]
    assert e['body']==g['body']
    assert hashlib.sha256(json.dumps(e['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==g['body_sha256']
    assert [i['url'] for i in e['images']]==g['existing_image_urls']
    assert [i['story_paragraph'] for i in images]==list(range(3))
    app,year,term=identities[eid]
    assert e['year']==year
    api=json.loads((BASE/f'steam-{app}.json').read_text(encoding='utf8'))[app]
    assert api['success'] and api['data']['steam_appid']==int(app) and term in api['data']['name']
    urls={im['path_full'] for im in api['data']['screenshots']}
    existing=set();existing_pixels=set()
    for im in e['images']:
        f=ROOT/im['recovery_local_source'];existing.add(sha(f))
        with Image.open(f) as v:
            existing_pixels.add(hashlib.sha256(str(v.size).encode()+v.convert('RGB').tobytes()).hexdigest())
    for im in images:
        f=ROOT/im['recovery_local_source'];h=sha(f)
        assert im['url'] in urls and h==im['verification']['source_sha256'] and h not in seen|existing
        with Image.open(f) as v:
            v.load();dimensions=list(v.size)
            p=hashlib.sha256(str(v.size).encode()+v.convert('RGB').tobytes()).hexdigest()
        assert dimensions==[1920,1080]==im['verification']['native_dimensions']==[im['width'],im['height']]
        assert p not in pixels|existing_pixels
        seen.add(h);pixels.add(p)
        assert im['license']=='Official publisher promotional game imagery; original rights retained.' and not im['license_url']
        media.append({'entry_id':eid,'paragraph':im['story_paragraph'],'path':im['recovery_local_source'],
                      'sha256':h,'native_dimensions':dimensions,'source_url':im['url'],
                      'actual_publisher_gallery_match':True,'full_native_image_viewed':True,
                      'association':associations[eid][im['story_paragraph']],
                      'distinct_from_cover_and_all_new_images':True})
    guards.append({'entry_id':eid,'body_sha256':g['body_sha256'],'source_and_cover_urls_unchanged':True,
                   'existing_cover_full_native_viewed':True})
assert len(media)==len(seen)==len(pixels)==6
out={'status':'PASS','candidate':str(path.relative_to(ROOT)).replace('\\','/'),'candidate_sha256':sha(path),
     'current_master_sha256':sha(catalog),'original_candidate_master_sha256':c['catalog_sha256'],
     'article_guards':guards,'source_receipts':sources,'images':media,
     'rights':'Original publisher promotional material, rights retained. No CC or individual photographer authorship inferred.',
     'limits':['Current official PC publisher galleries, not asserted launch-platform framebuffer captures.',
               'All six sources are native1920x1080; no enlargement or4K master claim.',
               'Source catalogue was not modified; no asset bundling, final Screen image render or console playback test performed.'],
     'master_modified':False}
target=BASE/'independent-six-starwars-original-illustrations-review.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'status':'PASS','images':6}))
