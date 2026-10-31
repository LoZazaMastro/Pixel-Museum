"""Reuse the already collected original Sega/Gremlin gameplay and controls leaflet."""
from pathlib import Path
import copy,json,hashlib,re
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/deep-scan-existing-prose-period-artifact';base.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']=='wikipedia-24309673')
new=copy.deepcopy(old);assert len(old['body'])==4
new['images'][0]['story_paragraph']=-1;new['explicit_story_media_only']=True
orig=ROOT/'build/research/root-cover-recovery';path=orig/'deep-back.jpg'
url=json.loads((orig/'urls.json').read_text(encoding='utf8'))['deep-back.jpg']
html=(orig/'deep.html').read_text(encoding='utf8');assert url in html
canonical=re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"',html)
source=canonical.group(1)if canonical else 'https://flyers.arcade-museum.com/'
with Image.open(path)as im:size=im.size
new['images'].append(dict(url=url,source_page=source,title='Depth charges, submarines and the radar view',
 caption='Back of the original 1979 Sega/Gremlin Deep Scan leaflet: four arcade-screen views, depth-charge controls and original cabinet formats. This is the original arcade game, not a screenshot of the later Saturn bonus-game version.',
 creator='Sega / Gremlin Industries',credit='Sega / Gremlin Industries / The Arcade Flyer Archive',
 license='Original manufacturer advertisement and imagery rights retained; no open licence asserted.',width=size[0],height=size[1],story_paragraph=2,
 recovery_local_source=path.relative_to(ROOT).as_posix(),verification=dict(sha256=sha(path),native_dimensions=list(size),processing='Complete already-collected original scan, without crop, enlargement or retouch.')))
paths=[orig/'deep.html',orig/'urls.json',path]
d=dict(status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
 source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0,1],[2,3]],
 scope='All four existing paragraphs/headings and correct original arcade longplay retained. Exclusive cover front and distinct original back illustrate two complete chapters. Existing later-port notes remain textual context without mislabelling a Saturn image.',
 quality_limits=['Original published 850-pixel-wide scan retained; no artificial high-resolution claim.',
 'No new historical prose, network requests, film, soundtrack or experience.'])
out=base/'four-existing-deep-scan-paragraphs-two-original-arcade-chapters-candidate.json';out.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
