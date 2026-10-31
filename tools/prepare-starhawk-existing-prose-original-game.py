"""Separate the existing Starhawk article using an identified original-game image."""
from pathlib import Path
import copy,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/starhawk-existing-prose-original-machines'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']=='wikipedia-1022715')
new=copy.deepcopy(old);assert len(old['body'])==6
new['images'][0]['story_paragraph']=-1;new['explicit_story_media_only']=True
p=base/'museum-original-34529.jpg'
new['images'].append(dict(url='https://www.arcade-museum.com/images-game/34/starhawk-34529.jpg',
 source_page='https://www.arcade-museum.com/Videogame/starhawk',
 title='Vector ships above the trench',
 caption='The original Cinematronics arcade game as illustrated by the Museum of the Game: white vector ships, aiming reticle and trench. The museum rendition is 640 by 480, not a 1979 photograph or a native 4K capture.',
 creator='Cinematronics / Museum of the Game contributor',credit='Cinematronics / Museum of the Game',
 license='Original game and contributed image rights retained; no open licence asserted.',width=640,height=480,story_paragraph=3,
 recovery_local_source=p.relative_to(ROOT).as_posix(),verification=dict(sha256=sha(p),native_dimensions=[640,480],processing='Exact original museum-published JPEG, including its existing KLOV mark. No enlargement, watermark removal or invented high-resolution claim.')))
paths=[base/'museum-source.html',p]
doc=dict(status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
 source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0,1,2],[3,4,5]],
 scope='Keep all six existing paragraphs/headings, exclusive original arcade flyer cover and original arcade longplay. A distinct museum gameplay view creates the second illustrated chapter; no unrelated PS3 game or Vectrex-port capture substituted.',
 quality_limits=['Published native vector-game illustration is 640 by 480, not an HD photograph. All pixels and existing source mark retained.',
 'Small museum cabinet photos were examined and held rather than enlarged into article illustrations.',
 'No new prose, film metadata request, soundtrack or experience added.'])
out=base/'six-existing-starhawk-paragraphs-two-original-game-chapters-candidate.json'
out.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
