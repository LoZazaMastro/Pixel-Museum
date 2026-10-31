"""Bind an actual Apple II game capture to the existing paragraph about that port."""
from pathlib import Path
import copy,hashlib,json,urllib.request
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/lemonade-existing-prose-original-apple-manual'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
url='https://upload.wikimedia.org/wikipedia/commons/7/71/Lemonade_Stand_1.png'
source='https://commons.wikimedia.org/wiki/File:Lemonade_Stand_1.png'
for name,address in [('commons-applewin-capture-source.html',source),('applewin-original-lemonade-capture.png',url)]:
    p=base/name
    if not p.exists():
        with urllib.request.urlopen(urllib.request.Request(address,headers={'User-Agent':'PixelMuseum/1.0 research contact via GitHub LoZazaMastro'}),timeout=30)as r:data=r.read()
        p.write_bytes(data)
path=base/'applewin-original-lemonade-capture.png'
assert Image.open(path).size==(560,384)
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']=='wikipedia-3989467')
assert len(old['body'])==2 and len(old['images'])==1
new=copy.deepcopy(old);new['images'][0]['story_paragraph']=-1;new['explicit_story_media_only']=True
new['images'].append(dict(url=url,source_page=source,title='Lemonade Stand on the Apple II',
    caption='The later Apple II conversion, captured using AppleWin in 2015. This shows the historic Apple game, not a screenshot of the original 1973 mainframe version.',
    creator='Bultro / Apple Computer / MECC',credit='Bultro / Wikimedia Commons; Apple II game imagery',
    license='PD-ineligible classification recorded on the original Commons file description; underlying game names and marks retain their respective rights.',
    license_url=source,width=560,height=384,story_paragraph=1,recovery_local_source=path.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(path),native_dimensions=[560,384],processing='Original published AppleWin PNG retained without crop, enlargement or retouch. Historic pixel graphics are not described as an HD photograph.')))
assert new['body']==old['body'] and new.get('story_headings')==old.get('story_headings')
paths=[base/'commons-applewin-capture-source.html',path]
out=base/'two-existing-lemonade-paragraphs-two-illustrated-scenes-candidate.json'
doc=dict(status='CANDIDATE_PENDING_FULL_IMAGE_REVIEW_AND_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0],[1]],
    scope='Two original paragraphs and headings unchanged. Current Apple cassette-booklet cover remains exclusive; an actual Apple II capture illustrates the paragraph explicitly discussing that port.',
    quality_limits=['Original 560 by 384 pixel game capture; no fabricated HD detail.',
        'The separately collected Apple manual spread is not admitted: its Lemonade section occupies too little of the page to make a useful illustration.',
        'Existing film identity and metadata unchanged; no new YouTube request.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
