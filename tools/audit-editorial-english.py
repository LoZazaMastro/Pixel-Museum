"""Read-only structural audit of the English editorial checkpoint (not a fact-check claim)."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,re,importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('originalgamehelpers',ROOT/'content/expansion/major-release-additions.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
doc=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'));entries=doc['entries'];history=json.loads((ROOT/'content/human-history.json').read_text(encoding='utf8'))['entries']
issues=[];brief=[];language_review=[];exact=defaultdict(list);paragraph_count=0;words=0
placeholder=re.compile(r'^\s*(?:TODO\b|TBD\b|Lorem ipsum\b|content pending\b|placeholder\b|insert (?:text|description)\b)',re.I)
for e in entries:
 containers=[e]+e.get('editorial_features',[])
 for owner in containers:
  paragraphs=owner.get('body',[])
  if not paragraphs or not all(isinstance(p,str) and p.strip() for p in paragraphs):issues.append({'entry_id':e['id'],'owner':owner.get('id',e['id']),'problem':'Empty or malformed narrative body'})
  for n,p in enumerate(paragraphs):
   paragraph_count+=1;words+=len(p.split())
   if placeholder.search(p):issues.append({'entry_id':e['id'],'paragraph':n,'problem':'Placeholder-like opening','excerpt':p[:200]})
   if re.search(r'<(?:script|style)\b|mw-parser-output|\.mw-?[\w]+\s*\{',p):issues.append({'entry_id':e['id'],'paragraph':n,'problem':'HTML/CSS source leakage','excerpt':p[:200]})
   if len(p)>180:exact[p].append(e['id'])
  if owner is e and sum(len(p.split()) for p in paragraphs)<80:brief.append({'entry_id':e['id'],'title':e['title'],'words':sum(len(p.split()) for p in paragraphs),'kind':e['kind']})
 text=' '.join(e.get('body',[]));tokens=re.findall(r"[a-zA-Z']+",text.lower());counts=Counter(tokens)
 italian=sum(counts[w] for w in ['della','delle','degli','nella','nelle','perche','questo','questa','quello','viene','dopo','anche','stato','stata','venne','gioco','giochi'])
 english=sum(counts[w] for w in ['the','and','is','was','with','game','games','that','this','from','which','their'])
 if italian>=6 and italian>english:language_review.append({'entry_id':e['id'],'title':e['title'],'italian_markers':italian,'english_markers':english})
requested=json.loads((ROOT/'content/expansion/user-soundtrack-priorities.json').read_text(encoding='utf8'))['entries'];requested += [{'title':t,'year':y} for y,t in [(2001,'Onimusha: Warlords'),(2002,"Onimusha 2: Samurai's Destiny"),(2004,'Onimusha 3: Demon Siege'),(2006,'Onimusha: Dawn of Dreams'),(1998,'Crash Bandicoot: Warped'),(1998,'Spyro the Dragon'),(1999,"Spyro 2: Ripto's Rage!"),(2000,'Spyro: Year of the Dragon')]]
by_identity={(helper.norm(e['title']),e['year']):e for e in entries if e['kind']=='game'};requests=[]
for row in requested:
 e=by_identity.get((helper.norm(row['title']),row['year']));requests.append({'title':row['title'],'year':row['year'],'status':'present' if e else 'missing','entry_id':e['id'] if e else None})
report={'schema_version':1,'scope':'English source narrative structural integrity and explicit requested-game presence. Does not claim line-by-line stylistic proofreading or independent verification of every historical fact.','catalog_sha256':hashlib.sha256((ROOT/'content/catalog.json').read_bytes()).hexdigest(),'catalog_entries':len(entries),'history_entries':len(history),'counts_by_kind':dict(Counter(e['kind'] for e in entries)),'article_body_paragraphs_including_attached_features':paragraph_count,'english_collection_body_words':words,'structural_issues':issues,'adjacent_duplicate_lead_prefixes':[{'entry_id':e['id'],'paragraph':n} for e in entries for n,p in enumerate(e.get('body',[])[:-1]) if len(p.split())>20 and e['body'][n+1].startswith(p) and len(e['body'][n+1])>len(p)],'summary_integrity_issues':[{'entry_id':e['id'],'summary':e['summary']} for e in entries if e.get('summary','').strip()=='From the reference collection' or (len(e.get('summary','').split())<5 and e.get('summary','').endswith(('Bros.','vs.','S.T.U.N.','F.E.A.R.','Goemon!','Dash!!')))],'brief_exhibits_below80words':brief,'complete_exhibits_below100words_including_features':[{'entry_id':e['id'],'title':e['title'],'words':sum(len(p.split()) for owner in [e]+e.get('editorial_features',[]) for p in owner.get('body',[]))} for e in entries if sum(len(p.split()) for owner in [e]+e.get('editorial_features',[]) for p in owner.get('body',[]))<100],'possible_nonenglish_bodies_requiring_review':language_review,'requested_games':requests,'missing_requested_games':[r for r in requests if r['status']=='missing'],'repeated_paragraph_groups_across_entries':len([v for p,v in exact.items() if len(set(v))>1]),'reviewed_english_depth_module':json.loads((ROOT/'content/expansion/museum-english-editorial-depth.json').read_text(encoding='utf8')).get('publication_status'),'history_source_words':sum(len(p.split()) for e in history for p in e.get('body',[])),'translation_status':'Not generated in this audit. Existing Playhub localizations can be reused after the parent freezes English editorial scope.'}
path=ROOT/'build/research/editorial-english-audit.json';path.write_text(json.dumps(report,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ['requested_games','brief_exhibits_below80words']},ensure_ascii=True,indent=2));print('BRIEF_EXHIBITS',len(brief))
