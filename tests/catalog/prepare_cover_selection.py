from pathlib import Path
import copy,json,runpy
root=Path(__file__).resolve().parents[2];runtime=runpy.run_path(str(root/'tools/runtime-catalog.py'));out=root/'build/catalog-cover-selection';out.mkdir(exist_ok=True)
base=dict(id='cover-art',title='Fixture',kind='game',year=2026,body=['First paragraph','Second paragraph'],story_headings=['First','Second'],images=[dict(url='https://example.org/cover.jpg',width=863,height=1413,story_paragraph=0,cover_art=True),dict(url='https://example.org/gameplay.jpg',width=3840,height=2160,story_paragraph=0),dict(url='https://example.org/later.jpg',width=1920,height=1080,story_paragraph=1)])
entries=[]
for eid,flag,value in [('cover-art','cover_art',True),('cover-role','cover_role',True),('kind-cover','kind','cover'),('role-cover','role','cover')]:
 e=copy.deepcopy(base);e['id']=eid;e['images'][0].pop('cover_art');e['images'][0][flag]=value;entries.append(e)
for eid,kind,override in [('explicit-game','game',2),('explicit-cover','game',0),('hardware','hardware',None),('organization','organization',None),('ordinary-game','game',None),('hardware-override','hardware',0)]:
 e=copy.deepcopy(base);e.update(id=eid,kind=kind)
 if override is not None:e['preferred_image']=override
 if eid=='ordinary-game':e['images'][0]['cover_art']=False
 entries.append(e)
source={'entries':entries};projected=runtime['project'](source)
for old,new in zip(entries,projected['entries']):
 assert len(old['images'])==len(new['images'])
 for a,b in zip(old['images'],new['images']):
  for field in ('cover_art','cover_role','kind','role'):
   if field in a:assert b[field]==a[field],(old['id'],field)
for name,doc in [('authoring',source),('runtime',projected)]:(out/(name+'.json')).write_text(json.dumps(doc,ensure_ascii=False),encoding='utf8')
print('PASS projection preserves semantic cover fields, including false flags; authoring/runtime fixtures prepared')
