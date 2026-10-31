import json,importlib.util,urllib.parse
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);B=p.RESEARCH/'user-priority';B.mkdir(exist_ok=True);doc=json.loads((R/'content/catalog.json').read_text());games=[e for e in (doc if isinstance(doc,list) else doc['entries']) if e.get('kind')=='game'];m=json.loads((R/'content/expansion/user-soundtrack-priorities.json').read_text());excluded=['battlefield1','kingdomhearts','spiderman','burnout','needforspeedunderground','needforspeedmostwanted','needforspeedcarbon','needforspeedhotpursuit2','fifastreet','thewarriors'];out=[]
for req in m['entries']:
 if any(k in p.norm(req['title']) for k in excluded):continue
 matches=[e for e in games if p.norm(e['title'])==p.norm(req['title']) and e['year']==req['year']];entry=matches[0] if len(matches)==1 else {'id':'priority-music-'+p.norm(req['title'])+'-'+str(req['year']),'title':req['title'],'year':req['year'],'kind':'game','sources':[{'url':req.get('source_page') or 'https://en.wikipedia.org/wiki/'+urllib.parse.quote(req['title'].replace(' ','_'))}]}
 f=B/(entry['id']+'-composer.json')
 if f.exists():out.append(json.loads(f.read_text()));continue
 try:
  names,url,evidence=p.composer(entry);d={'entry':entry,'requested_title':req['title'],'year':req['year'],'catalog_identity_pending':not bool(matches),'composers':names,'composer_source':url,'composer_evidence':evidence,'state':'independent_composer_resolved' if names else 'composer_research_required'};p.write(f,d);out.append(d);print(req['title'],names,url,flush=True)
 except Exception as ex:d={'entry':entry,'state':'research_error','error':str(ex)};p.write(f,d);out.append(d);print('ERROR',req['title'],str(ex),flush=True)
 p.write(B/'priority-original-score-composer-checkpoint.json',{'publication_status':'research_only','entries':out})
