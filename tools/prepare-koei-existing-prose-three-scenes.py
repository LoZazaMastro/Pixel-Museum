"""Add identified founders and original-game images without rewriting Koei prose."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/koei-existing-prose-publisher-context'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries'] if e['id']=='workbook-07-25-koei')
new=copy.deepcopy(old)
assert len(old['body'])==4 and len(old['images'])==1
new['images'][0]['story_paragraph']=-1
new['explicit_story_media_only']=True
downloads=json.loads((BASE/'primary-pages.json').read_text(encoding='utf8'))
by_name={Path(d['file']).name:d for d in downloads if 'file' in d}
def image(name,url,source,title,caption,creator,paragraph):
    path=BASE/name
    width,height=Image.open(path).size
    return dict(url=url,source_page=source,title=title,caption=caption,
                creator=creator,credit='KOEI TECMO / '+title,
                license='Original publisher photograph or game imagery; rights retained. No open licence asserted.',
                width=width,height=height,story_paragraph=paragraph,
                recovery_local_source=path.relative_to(ROOT).as_posix(),
                verification=dict(sha256=sha(path),native_dimensions=[width,height],
                    processing='Original published image bytes retained; no crop or local enlargement.'))
pdf='https://www.koeitecmo.co.jp/e/ir/docs/33833de079919bad7675b6707903b8765d275855.pdf'
new['images'] += [
    image('founders-2019-original.jpg',pdf+'#page=3&embedded=Im0.jpg',pdf,
          'Keiko and Yoichi Erikawa',
          'Koei founders Keiko Erikawa, left, and Yoichi Erikawa, right, in the company\'s 2019 annual report. This is a later corporate portrait, not a photograph of their 1978 founding.',
          'Photographer not identified; published by KOEI TECMO',0),
    image('nobunaga-publisher-shot2.jpg',by_name['nobunaga-publisher-shot2.jpg']['url'],
          'https://store.steampowered.com/app/544990/',
          'Managing territory in the original Nobunaga\'s Ambition',
          'The original Nobunaga\'s Ambition map and resource commands, shown in the publisher\'s Kou Shibusawa Archives reissue. The game originates in 1983; this published reissue image is not claimed as a launch-day capture.',
          'KOEI / KOEI TECMO',2),
    image('three-kingdoms-publisher-shot2.jpg',by_name['three-kingdoms-publisher-shot2.jpg']['url'],
          'https://store.steampowered.com/app/521670/',
          'Leaders and abilities in Romance of the Three Kingdoms',
          'Leader portraits and their abilities in the first Romance of the Three Kingdoms, as published for its Kou Shibusawa Archives reissue. The original game dates to 1985; this is not a later numbered sequel.',
          'KOEI / KOEI TECMO',3),
]
assert new['body']==old['body'] and new['story_headings']==old['story_headings']
files=[BASE/r['file'].split('/')[-1] for r in downloads if 'file' in r]
files.append(BASE/'founders-2019-original.jpg')
out=BASE/'four-existing-koei-paragraphs-three-identified-publisher-scenes-candidate.json'
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
         rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
         source_files={p.relative_to(ROOT).as_posix():sha(p) for p in files},
         expected_main_paragraph_groups=[[0,1],[2],[3]],
         scope='Four existing paragraphs retained verbatim. Exclusive logo cover, later founders portrait, two authentic original-game images.',
         quality_limits=['The founders portrait is the original embedded 1034 by 685 JPEG from PDF page 3, not a 1978 photograph.',
                         'Game screens are authentic native 640 by 400 pixel graphics supplied by the publisher. They are intentionally low-resolution game output, not HD photography or artificially enlarged artwork.',
                         'Tiny 440 by 333 and 279 by 400 historical cover thumbnails were collected for identity comparison only and are not admitted.',
                         'All publisher photographic/game rights retained; no invented CC licence.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
