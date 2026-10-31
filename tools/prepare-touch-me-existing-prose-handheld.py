"""Use a real, openly licensed photograph for the existing handheld-adaptation paragraph."""
from pathlib import Path
import copy,hashlib,json,urllib.request
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/touch-me-existing-prose-handheld-context';base.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source="https://commons.wikimedia.org/wiki/File:Atari_Touch_Me,_Model_BH-100,_Made_In_Taiwan,_Circa_1978_(Red_LED_Electronic_Handheld_Game)_Atari%27s_Only_Handheld_Game.jpg"
url='https://live.staticflickr.com/7579/15579872399_2a94e61e77_o.jpg'
evidence=base/'commons-public-file-description-web-evidence.json'
evidence.write_text(json.dumps(dict(source_page=source,reader='Public file description read using the web tool before local HTTP rate limiting.',
    original_url=url,author='Joe Haupt',photo_date='2014-11-10',native_dimensions=[2578,2847],
    licence='CC BY-SA 2.0',licence_url='https://creativecommons.org/licenses/by-sa/2.0/',
    flickr_source='https://www.flickr.com/photos/51764518@N02/15579872399/',
    limits='Direct Commons HTTP returned429; no retry. Only the separately hosted openly published Flickr original is requested.'),indent=2)+'\n',encoding='utf8')
for name,address in [('joe-haupt1978-handheld-original-photo2014.jpg',url)]:
    p=base/name
    if not p.exists():
        with urllib.request.urlopen(urllib.request.Request(address,headers={'User-Agent':'Mozilla/5.0'}),timeout=30)as r:data=r.read()
        p.write_bytes(data)
path=base/'joe-haupt1978-handheld-original-photo2014.jpg'
assert Image.open(path).size==(2578,2847)
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']=='wikipedia-5527524')
new=copy.deepcopy(old)
assert len(old['body'])==5 and len(old['images'])==2
new['images'][0]['story_paragraph']=-1;new['images'][1]['story_paragraph']=0;new['explicit_story_media_only']=True
new['images'].append(dict(url=url,source_page=source,title='Touch Me becomes a handheld game',
    caption='Atari Touch Me, model BH-100, circa 1978. Joe Haupt photographed this preserved handheld unit in November 2014; it is the later coloured-button model, not the original 1974 arcade cabinet or Milton Bradley Simon.',
    creator='Joe Haupt',credit='Joe Haupt / CC BY-SA 2.0',license='CC BY-SA 2.0',license_url='https://creativecommons.org/licenses/by-sa/2.0/',
    width=2578,height=2847,story_paragraph=2,recovery_local_source=path.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(path),native_dimensions=[2578,2847],processing='Original published photographer JPEG retained unchanged; no crop, enlargement, retouch or background removal.')))
assert new['body']==old['body']and new.get('story_headings')==old.get('story_headings')
paths=[evidence,path]
doc=dict(status='CANDIDATE_PENDING_FULL_VISUAL_REVIEW_AND_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0,1],[2,3,4]],
    scope='All five existing paragraphs and headings retained. Exclusive arcade flyer cover and different existing back retained; actual later handheld photo separates the Simon and handheld-adaptation chapter.',
    quality_limits=['Modern 2014 photograph of the historic circa1978 object; not a period1974 photograph.',
        'The device is Atari Touch Me, not a substitute Simon photograph.',
        'No extra prose, music, film or experience added.'])
out=base/'five-existing-touch-me-paragraphs-two-distinct-device-chapters-candidate.json'
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
