"""Pair eight existing paragraphs with unique creator, game and archive material."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/carol-shaw-existing-prose-primary-illustrations'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries'] if e['id']=='carol-shaw')
new=copy.deepcopy(old)
feature=new['editorial_features'][0]
assert len(new['body'])==len(feature['body'])==4
new['explicit_story_media_only']=True
new['images'][0]['story_paragraph']=-1
feature['explicit_story_media_only']=True
# The former feature photograph is the cover itself; retain the cover exclusively.
assert feature['images'][0]['original_url']==new['images'][0]['original_url']
feature['images']=[]
downloads=json.loads((BASE/'primary-pages.json').read_text(encoding='utf8'))
by_name={Path(d['file']).name:d for d in downloads}
def media(name,url,source,title,caption,creator,credit,paragraph,**proof):
    path=BASE/name
    width,height=Image.open(path).size
    return dict(url=url,source_page=source,title=title,caption=caption,
                creator=creator,credit=credit,
                license='Original creator, publisher or museum rights retained; no open licence asserted.',
                width=width,height=height,story_paragraph=paragraph,
                recovery_local_source=path.relative_to(ROOT).as_posix(),
                verification=dict(sha256=sha(path),native_dimensions=[width,height],
                    processing='Original published pixels retained without crop, retouch or enlargement, unless a full vector PDF page render is explicitly described.',**proof))
interview=by_name['shaw-interview.html']['url']
strong=by_name['strong-collection.html']['url']
manual=by_name['river-raid-vcs-1982-manual.pdf']['url']
aid=by_name['strong-finding-aid.pdf']['url']
new['images'] += [
    media('river-raid-2600-original.png',by_name['river-raid-2600-original.png']['url'],interview,
          'The Atari 2600 river, aircraft and fuel',
          'The Atari 2600 game image published with Carol Shaw\'s 2011 interview. This illustrates the playable route and fuel system, not a visual diagram of the terrain-generation algorithm.',
          'Activision / image published by Benj Edwards',
          'Activision / Vintage Computing and Gaming, Carol Shaw interview',1),
    media('strong-shaw-artifacts-original.jpg',by_name['strong-shaw-artifacts-original.jpg']['url'],strong,
          'Carol Shaw\'s surviving development materials',
          'The Strong\'s photograph of Shaw\'s donated materials includes a River Raid source-code printout, a Polo design sheet, Atari-era game boxes and Activision publicity. These are preserved artifacts, not a development-session reconstruction.',
          'The Strong National Museum of Play',
          'Courtesy of The Strong, Rochester, New York',3),
]
feature['images'] = [
    media('strong-carol-shaw-original.jpg',by_name['strong-carol-shaw-original.jpg']['url'],strong,
          'Carol Shaw at work',
          'Carol Shaw at her desk in the historical photograph published by The Strong. The source does not identify the screen as River Raid or establish an exact shooting date.',
          'Historical photograph published by The Strong; photographer not identified',
          'Courtesy of The Strong, Rochester, New York',0),
    media('polo-design-note-original.jpg',by_name['polo-design-note-original.jpg']['url'],interview,
          'Shaw\'s hand-drawn Polo design notes',
          'A complete design sheet for Atari Polo dated 18 December 1978, showing mallet contact zones and ball directions. It illustrates Shaw\'s earlier paper-based design practice, not a River Raid terrain sketch.',
          'Carol Shaw', 'Carol Shaw / Vintage Computing and Gaming',1),
    media('vcs-original-manual-page3.jpg',manual+'#page=3&embedded=Im1.jpg',manual,
          'The original River Raid rules and targets',
          'The complete 1982 Atari 2600 manual page explaining fuel, scoring and the river display, including bridges and fuel depots. This is the original VCS documentation, not the later Atari computer port.',
          'Activision', 'Activision, River Raid Atari VCS manual, 1982',2,
          source_pdf_sha256=sha(BASE/'river-raid-vcs-1982-manual.pdf'),pdf_page=3,
          embedded_image='Im1.jpg',exact_embedded_original=True),
    media('strong-finding-aid-complete-page3.png',aid+'#page=3',aid,
          'Preserving the Carol Shaw papers',
          'The Strong\'s January 2022 finding aid, complete page 3, records the source-code printouts and the arrangement of Shaw\'s donated papers. It is a modern archival document, not an original River Raid code listing.',
          'Brian Sutton-Smith Library and Archives of Play at The Strong',
          'The Strong / Carol Shaw Papers finding aid, January 2022',3,
          source_pdf_sha256=sha(BASE/'strong-finding-aid.pdf'),pdf_page=3,
          vector_page_render_scale=3,complete_page=True),
]
assert new['body']==old['body']
assert feature['body']==old['editorial_features'][0]['body']
assert feature['story_headings']==old['editorial_features'][0]['story_headings']
files=[ROOT/d['file']for d in downloads]
files += [BASE/'vcs-original-manual-page3.jpg',BASE/'strong-finding-aid-complete-page3.png']
out=BASE/'eight-existing-shaw-paragraphs-six-unique-contextual-illustrations-candidate.json'
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
         rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
         source_files={p.relative_to(ROOT).as_posix():sha(p) for p in files},
         expected_main_paragraph_groups=[[0],[1,2],[3]],
         expected_feature_paragraph_groups=[[0],[1],[2],[3]],
         scope='All eight existing paragraphs retained verbatim. Six unique contextual illustrations; main film at paragraph zero and exclusive award cover preserved.',
         quality_limits=['The Polo design sheet is the original native 600 by 821 publication image, not a 4K reconstruction.',
                         'The gameplay image retains its original published 912 by 597 pixels; pixel graphics are not HD photography.',
                         'The Strong artifact photograph is 2560 by 1629 and the work photograph 2560 by 2139.',
                         'The tiny River Raid box scan and separate 600-pixel portrait were inspected but not admitted.',
                         'The full finding-aid page is a genuine modern archival document, not a decorative game image.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
