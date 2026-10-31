"""Replace archive-access housekeeping with a sourced historical conclusion."""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/chronological-mabel-addis-1964'
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries'] if e['id']=='feature-mabel-addis-classroom')
new=copy.deepcopy(old)
assert len(old['body'])==4 and 'permission to redistribute' in old['body'][3]
new['body'][3]=(
    'In 2023, the Game Developers Choice Awards selected Addis for its posthumous Pioneer Award. '
    'The organizers highlighted the narrated decisions and the slides accompanied by synchronized sound in The Sumerian Game. '
    'Addis drew on her training in ancient history at Barnard College while working as a grade-school teacher. '
    'Her classroom project brings together subject knowledge, writing and computer simulation around the choices of a pupil.')
if len(new.get('story_headings',[]))==4:
    new['story_headings'][3]='Recognition beyond the classroom'
for source in new['sources']:
    if source.get('id')=='sumer_aid':
        source['story_paragraphs']=[2]
new['sources'].append(dict(
    title='Legendary game designers John Romero and Mabel Addis honored at GDCA 2023',
    url='https://gdconf.com/article/legendary-game-designers-john-romero-and-mabel-addis-honored-at-gdca-2023/',
    publisher='Game Developers Conference / Game Developers Choice Awards',
    source_type='Primary award organizer announcement',story_paragraphs=[3],
    locator='Mabel Addis Pioneer Award selection; narrated decisions and slides with synchronized audio; Barnard ancient-history degree and grade-school teaching.',
    rights='Bibliographic reference; replacement paragraph is an original English paraphrase, not a quotation.'))
assert new['body'][:3]==old['body'][:3] and new['images']==old['images']
source=BASE/'gdc-primary-addis-pioneer.html'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=BASE/'one-readable-primary-sourced-recognition-paragraph-candidate.json'
document=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={source.relative_to(ROOT).as_posix():sha(source)},
    scope='Replace only fourth paragraph about archival access/redistribution with primary-sourced2023recognition and teaching context. Firstthree paragraphs, images and every other article unchanged.',
    reason='Permissions and research-access housekeeping belong in source records, not the public historical narrative.',
    quality_limits=['Primary source announces selection for the2023award; no claim about a photographed award ceremony.',
        'The existing diagram remains an illustration of the game design; it is not described as an award photograph.'])
out.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
