import concurrent.futures,importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];spec=importlib.util.spec_from_file_location('p',root/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
d=json.loads((root/'content/catalog.json').read_text());a=d if isinstance(d,list) else d['entries'];by={e['id']:e for e in a}
for e in a:
 if e.get('kind')=='game':p.TITLE_YEARS.setdefault(p.norm(e['title']),set()).add(e['year'])
work=[]
for f in (p.RESEARCH/'games').glob('*.json'):
 r=json.loads(f.read_text())
 if r['state']=='composer_research_required' and r['year']>=1980 and r['entry_id'] in by:work.append((f,r,by[r['entry_id']]))
def repair(item):
 f,r,e=item;names,url,evidence=p.composer(e);names=p.clean_composer_names(names,e['title'])
 if names:r.update(composers=names,composer_source=url,composer_evidence=evidence,state='recording_research_required',source_identity_researched=p.STAMP)
 else:r.update(composers=[],composer_source=url,composer_evidence=evidence)
 p.write(f,r);return e['id'],e['title'],bool(names),names
print('EXACT GAME COMPOSER SOURCE REPAIR',len(work),'subjects',flush=True)
for row in concurrent.futures.ThreadPoolExecutor(max_workers=4).map(repair,work):print(row,flush=True)
print('CHECKPOINT',p.assemble(),flush=True)
