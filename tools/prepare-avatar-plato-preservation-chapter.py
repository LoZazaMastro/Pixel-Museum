"""Complete a genuinely single-paragraph article from the already-collected Wikipedia revision."""
from pathlib import Path
import copy,json,hashlib,re,html
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/avatar-plato-existing-intro-preservation-chapter'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']=='wikipedia-3333468')
assert len(old['body'])==1
wiki=ROOT/'build/research/cover-origins-extra/Avatar_(1979_video_game).html';raw=wiki.read_text(encoding='utf8')
assert '1353544020' in raw and old['attribution']['revision_id']==1353544020
blocks=[]
for block in re.findall(r'<p\b[^>]*>(.*?)</p>',raw,re.S):
 text=html.unescape(re.sub('<[^>]+>','',block));text=re.sub(r'\[\d+\]','',text).strip()
 if text:blocks.append(text)
assert blocks[0]==old['body'][0]
extra=next(t for t in blocks if t.startswith('Classic as well as modified versions of Avatar 84'))
new=copy.deepcopy(old);new['body'].append(extra)
new['story_headings']=['A shared dungeon on PLATO','A world preserved beyond NovaNET']
new['images'][0]['story_paragraph']=-1;new['explicit_story_media_only']=True
path=base/'actual-preserved-dungeon-game.png'
new['images'].append(dict(url='https://howtomakeanrpg.com/img/avatar/basic_gameplay_3.png',
 source_page='https://howtomakeanrpg.com/r/l/g/avatar/',title='Exploring the preserved multiplayer dungeon',
 caption='An actual Avatar session captured by Dan Schuller on the Cyber1 preservation system, lesson 2avatar. The screen shows the small first-person dungeon view, character statistics and keyboard help. This is a later preserved version, not a capture made in 1979.',
 creator='Avatar creators / Dan Schuller (game capture)',credit='Avatar creators / Dan Schuller, How to Make an RPG',
 license='Original game and capture rights retained by their respective authors; no open licence asserted.',
 width=512,height=512,story_paragraph=1,recovery_local_source=path.relative_to(ROOT).as_posix(),
 verification=dict(sha256=sha(path),native_dimensions=[512,512],processing='Original published PLATO-resolution PNG retained without crop, enlargement or invented HD detail.')))
new['attribution']['changes']='Existing complete introductory paragraph preserved; one complete preservation-history paragraph added verbatim from the same Wikipedia revision. Display headings and illustration selection added.'
new['attribution']['text']='Text reproduced from Avatar (1979 video game), Wikipedia contributors, revision 1353544020, under CC BY-SA 4.0. Complete introduction and preservation-history paragraph selected; headings and media selection are editorial.'
new['sources'].append(dict(title='Avatar preservation community and version notes',url='https://heavyharmonies.com/Avatar/',publisher='Dan Harding / Avatar community'))
paths=[wiki,base/'player-capture-publication.html',base/'preservation-community-source.html',path]
doc=dict(status='CANDIDATE_PENDING_INDEPENDENT_PEER',rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
 source_files={p.relative_to(ROOT).as_posix():sha(p)for p in paths},expected_main_paragraph_groups=[[0],[1]],
 scope='The original article genuinely had one complete paragraph. Preserve it exactly and add only one complete paragraph already present in the same collected Wikipedia revision, paired with a distinct original preservation-system game image. Existing exclusive hardware cover and correct film retained.',
 quality_limits=['Capture is native 512x512 PLATO resolution, not an HD photograph, and is explicitly a later Cyber1 session.',
 'The text distinguishes original engines from versions running on Avatar 95 and records the November 2015 NovaNET shutdown.',
 'No new film request, soundtrack, executable or experience bundled.'])
out=base/'original-avatar-intro-and-complete-preservation-paragraph-two-illustrated-chapters-candidate.json'
out.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
