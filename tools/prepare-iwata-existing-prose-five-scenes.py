"""Distribute the existing Iwata prose across pertinent original illustrations."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/iwata-existing-prose-illustrated-chapters'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
by_id={entry['id']:entry for entry in catalog['entries']}
old=by_id['daily-12-06']
new=copy.deepcopy(old)
assert len(old['body'])==7
assert len(old['images'])==3
new['images'][0]['story_paragraph']=-1
new['explicit_story_media_only']=True

def photograph(name, url, source, title, caption, creator, licence, licence_url, paragraph):
    path=BASE/name
    with Image.open(path) as decoded:
        decoded.load()
        width,height=decoded.size
    return dict(url=url,source_page=source,title=title,caption=caption,
        creator=creator,credit=creator+' / '+licence,license=licence,license_url=licence_url,
        width=width,height=height,story_paragraph=paragraph,
        recovery_local_source=path.relative_to(ROOT).as_posix(),
        verification=dict(sha256=sha(path),native_dimensions=[width,height],no_upscale=True,
                          processing='Original published JPEG preserved byte-for-byte; no crop, enlargement or generated content.'))

new['images'].append(photograph('pet-original.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/c/c5/Commodore_2001_Series-IMG_0448b.jpg',
    'https://commons.wikimedia.org/wiki/File:Commodore_2001_Series-IMG_0448b.jpg',
    'Commodore PET 2001 at the Bolo Museum',
    'A Commodore PET 2001 photographed at the Bolo Museum in 2011. This is the model family Iwata used as a student, not his personal computer or a HAL office photograph.',
    'Rama / Musee Bolo','CC BY-SA 2.0 FR','https://creativecommons.org/licenses/by-sa/2.0/fr/',0))

pokemon=copy.deepcopy(next(i for i in by_id['pokemon']['images'] if i.get('story_paragraph')==9))
pokemon.update(story_paragraph=2,
    title='Pokemon Red and Blue in the original English trainer guide',
    caption='The original 1998 English trainer guide shows the translated dialogue and place names in Pokemon Red and Blue. It illustrates the localization discussed here, not Iwata at work.')
new['images'].append(pokemon)

kirby=copy.deepcopy(by_id['wikipedia-772871']['images'][0])
kirby.pop('cover_art',None)
kirby.update(story_paragraph=3,title="Kirby's Adventure: original 1993 packaging",
    caption="Original 1993 Kirby's Adventure packaging, illustrating HAL's Kirby work during Iwata's career. It is not a photograph of the development team or one of the cancelled projects.")
new['images'].append(kirby)

new['images'].append(photograph('gdc-2011-original.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/7/7d/Satoru_Iwata_-_Game_Developers_Conference_2011_-_Day_3_%283%29.jpg',
    'https://commons.wikimedia.org/wiki/File:Satoru_Iwata_-_Game_Developers_Conference_2011_-_Day_3_(3).jpg',
    'Satoru Iwata speaking at GDC in 2011',
    'Iwata at the 2011 Game Developers Conference, speaking about the history and future of video games. This is a conference address, not an Iwata Asks interview session.',
    'Official GDC','CC BY 2.0','https://creativecommons.org/licenses/by/2.0/',5))

assert new['body']==old['body'] and new['story_headings']==old['story_headings']
assert new['editorial_features']==old['editorial_features']
paths=[BASE/'original-photograph-source-files.json',BASE/'pet-source.html',BASE/'gdc-source.html']
paths.extend(ROOT/i['recovery_local_source'] for i in new['images'] if i.get('recovery_local_source'))
for path in paths:
    assert path.exists(),path
out=BASE/'seven-existing-paragraphs-five-illustrated-scenes-candidate.json'
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
    expected_main_paragraph_groups=[[0,1],[2],[3],[4],[5,6]],
    scope='Only main article image bindings changed. All seven existing main paragraphs and four feature paragraphs, headings, cover, dates, film and audio remain intact.',
    quality_limits=['Kirby and Pokemon images depict original published artifacts, not developers at work.',
        'Two paragraphs share the PET illustration and two share the GDC photograph; no duplicated image cards.',
        'Existing feature illustrations remain unchanged. No whole-catalog completion claim.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
