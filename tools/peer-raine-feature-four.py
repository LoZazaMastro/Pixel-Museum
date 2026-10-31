"""Independently bind the four feature-only Raine images to native/source evidence."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/story-text-profile/priority-original-illustrations/raine-feature'
candidate=BASE/'raine-four-feature-illustrations-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(candidate)=='f9824f2d3dd6f6cfce1554dd3a8bd5aed4dc185eadac12a94bf2787ac22058e5'
c=json.loads(candidate.read_text(encoding='utf8'))
catalog=ROOT/'content/catalog.json'
e=next(e for e in json.loads(catalog.read_text(encoding='utf8'))['entries'] if e['id']=='celeste')
assert len(c['feature_entries'])==1
record=c['feature_entries'][0]
assert record['entry_id']=='celeste' and record['feature_id']=='feature-lena-raine-movement'
f=next(f for f in e['editorial_features'] if f['id']==record['feature_id'])
assert f['body']==record['feature_body'] and f['title']==record['feature_title']
assert hashlib.sha256(json.dumps(f['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==record['feature_body_sha256']
assert [i['url'] for i in f.get('images',[])]==record['existing_feature_image_urls']==[]
assert [i['story_paragraph'] for i in record['images']]==list(range(4))
for r in c['source_receipts']:assert sha(ROOT/r['path'])==r['sha256']
commons=json.loads((BASE/'raine-commons-imageinfo.json').read_text(encoding='utf8'))
info=next(v['imageinfo'][0] for v in commons['query']['pages'].values() if v.get('imageinfo'))
ext=info['extmetadata']
assert ext['LicenseShortName']['value']=='CC BY-SA 4.0'
assert 'Sara Ranlett' in ext['Artist']['value'] and ext['DateTimeOriginal']['value'].startswith('2018-02-10')
assert 'https://creativecommons.org/licenses/by-sa/4.0'==ext['LicenseUrl']['value'].rstrip('/')
steam=json.loads((BASE.parent/'steam-504230.json').read_text(encoding='utf8'))['504230']
assert steam['success'] and steam['data']['steam_appid']==504230 and steam['data']['name']=='Celeste'
gallery={im['path_full'] for im in steam['data']['screenshots']}
interview=(BASE/'minecraft-composer-interview.html').read_text(encoding='utf8')
release=(BASE/'nether-release.html').read_text(encoding='utf8')
assert 'Samuel \u00c5berg' in interview and 'Lena Raine' in interview
assert '2020-04-09T00:00:00Z' in interview and '2020-06-23T14:58:53Z' in release

def pixels(path):
    with Image.open(path) as im:
        im.load()
        return list(im.size),hashlib.sha256(str(im.size).encode()+im.convert('RGB').tobytes()).hexdigest()

existing=[]
for im in c['same_article_distinct_image_check']['checked_existing']:
    p=ROOT/im['path'];dimensions,pixel=pixels(p)
    assert sha(p)==im['sha256'] and pixel==im['decoded_rgb_sha256']
    existing.append({'path':im['path'],'sha256':sha(p),'native_dimensions':dimensions,'RGB_sha256':pixel})
existing_pixels={im['RGB_sha256'] for im in existing}
seen=set();media=[]
associations=[
 'A dated portrait identifies the composer discussing her early Celeste sketches and team feedback; no recording-session claim.',
 'Madeline and Theo in the original gondola/panic scene illustrate emotional intensity and musical pacing. Original in-game dialogue remains part of the publisher frame; no audio-tool screenshot claim.',
 'Actual Mojang interview header identifies the Nether context of transforming the piano sound. Not presented as Celeste imagery or an image of a piano.',
 'Distinct June2020 NetherUpdate release art illustrates the wider landscape/audio identity discussion. Explicitly later than the April interview; not a portrait of SamuelAberg.']
for n,im in enumerate(record['images']):
    p=ROOT/im['recovery_local_source'];dimensions,pixel=pixels(p)
    assert sha(p)==im['verification']['source_sha256']
    assert dimensions==im['verification']['native_dimensions']==[im['width'],im['height']]
    assert pixel not in seen|existing_pixels;seen.add(pixel)
    if n==0:
        assert im['url']==info['url'] and dimensions==[1192,1800]
        assert im['creator']=='Sara Ranlett' and im['license']=='CC BY-SA 4.0'
    elif n==1:
        assert im['url'] in gallery and dimensions==[1920,1080]
        assert not im['license_url']
    else:
        html=interview if n==2 else release
        assert im['url'] in html and dimensions==[1170,500]
        assert im['creator']=='Mojang Studios' and not im['license_url']
    media.append({'paragraph':n,'feature_id':record['feature_id'],'path':im['recovery_local_source'],
                  'sha256':sha(p),'native_dimensions':dimensions,'RGB_sha256':pixel,
                  'full_native_image_viewed':True,'source_url':im['url'],'association':associations[n]})
assert len(seen)==4
out={'status':'PASS','publication_scope':'NEXT_feature_only_not_master_admission',
     'candidate':candidate.relative_to(ROOT).as_posix(),'candidate_sha256':sha(candidate),
     'candidate_master_sha256':c['catalog_sha256'],'current_master_sha256':sha(catalog),
     'entry_id':e['id'],'feature_id':f['id'],'feature_body_sha256':record['feature_body_sha256'],
     'current_feature_body_unchanged':True,'main_Celeste_body_and_images_not_targeted':True,
     'source_receipts':c['source_receipts'],'images':media,'checked_existing':existing,
     'visual_reference_review':'Allfour new images individually viewed; original Celeste cover individually viewed, existinggallery/newscene comparison sheet viewed.',
     'rights_review':'Portrait has actualCommons authorSaraRanlett/date10Feb2018/CCBYSA4 metadata including licence link. Celeste/Minecraft images preserve publisher copyright; no falseCC on gameart.',
     'limits':['TwoMojang headers are genuine native1170x500 publisher originals, notHD4K photographs or enlarged sources.',
               'The gondola scene is intentional original pixelart at the publisher1920x1080 presentation, with its original dialogue intact.',
               'This peer approves only associations inside feature-lena-raine-movement. NoMojang images are assigned to mainCeleste paragraphs.',
               'No master, manifest, bundle, finalScreen render or console transfer was performed.'],
     'master_modified':False}
target=BASE/'independent-four-feature-illustrations-review.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(target.relative_to(ROOT).as_posix(),sha(target))
