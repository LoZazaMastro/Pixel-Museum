"""Acquire exact original games explicitly requested by the curator, resumably."""
from pathlib import Path
import importlib.util,json,re,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import unquote
from urllib.request import Request,urlopen
import hashlib,io
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('franchise_helpers',HERE/'franchise-mainline-additions.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CACHE=ROOT/'build/research/user-requested-games';CACHE.mkdir(parents=True,exist_ok=True);m.CACHE=CACHE
def fast_fetch(url):
 with urlopen(Request(url,headers={'User-Agent':m.helper.AGENT}),timeout=10) as response:return response.read(24<<20)
m.helper.fetch=fast_fetch
ALIAS={
 'Star Wars: Battlefront':'Star Wars: Battlefront (2004 video game)',
 'Star Wars: Battlefront II':'Star Wars: Battlefront II (2005 video game)',
 'Need for Speed: Most Wanted':'Need for Speed: Most Wanted (2005 video game)',
 'From Russia with Love':'From Russia with Love (video game)',
 'Ape Escape':'Ape Escape (video game)',
 'Devil May Cry': 'Devil May Cry (video game)',
 'FIFA Street':'FIFA Street (2005 video game)',
 'The Getaway':'The Getaway (video game)',
 'The Warriors':'The Warriors (video game)',
 'Viewtiful Joe':'Viewtiful Joe (video game)',
 'Marvel\u2019s Spider-Man: Miles Morales':'Spider-Man: Miles Morales',
}
EXTRA=[(2001,'Onimusha: Warlords'),(2002,"Onimusha 2: Samurai's Destiny"),(2004,'Onimusha 3: Demon Siege'),(2006,'Onimusha: Dawn of Dreams'),(1998,'Crash Bandicoot: Warped'),(1998,'Spyro the Dragon'),(1999,"Spyro 2: Ripto's Rage!"),(2000,'Spyro: Year of the Dragon')]
def main():
 registry=json.loads((HERE/'user-soundtrack-priorities.json').read_text(encoding='utf8'))['entries']
 targets=[]
 for r in registry:
  title=r['title'];wiki=unquote(r.get('source_page','').split('/wiki/')[-1]).replace('_',' ') if '/wiki/' in r.get('source_page','') else ALIAS.get(title,title)
  targets.append({'series':'Explicit curator request','year':r['year'],'requested_title':wiki,'display_title':title})
 for y,t in EXTRA:targets.append({'series':'Explicit main chapters and mascot-trilogy request','year':y,'requested_title':t,'display_title':t})
 catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries'];existing={(m.norm(e['title']),e['year']) for e in catalog if e['kind']=='game'}
 prev=json.loads((HERE/'user-requested-game-additions.json').read_text(encoding='utf8')).get('entries',[]) if (HERE/'user-requested-game-additions.json').exists() else []
 existing.update((m.norm(e['title']),e['year']) for e in prev)
 todo=[i for i in targets if (m.norm(i['display_title']),i['year']) not in existing]
 unique={ (i['year'],m.norm(i['requested_title'])):i for i in todo};todo=list(unique.values())
 m.SERIES={'Explicit user requests':[(i['year'],i['requested_title']) for i in todo]}
 records,entities,held=m.identify()
 if any(i['requested_title']=='Auto Modellista' for i in todo):
  cached=CACHE/'auto-modellista-page.json'
  if cached.exists():
   page=json.loads(cached.read_text(encoding='utf8'));date=m.helper.date_from(page,2002)
   if date.get('month')==8 and date.get('day')==22:
    records.append(({'series':'Explicit user request','year':2002,'requested_title':'Auto Modellista'},page));held=[h for h in held if h.get('requested_title')!='Auto Modellista']
 original={(i['year'],i['requested_title']):i for i in todo}
 records=[({**i,**original[(i['year'],i['requested_title'])]},p) for i,p in records]
 candidates=m.archive_candidates(records)
 outputs=list(prev)
 def process(pair):
  i,page=pair
  try:
   recovered=json.loads((HERE/'user-requested-cover-recoveries.json').read_text(encoding='utf8')).get('entries',{}) if (HERE/'user-requested-cover-recoveries.json').exists() else {}
   cover=recovered.get(m.norm(i['display_title'])+'|'+str(i['year']))
   originals=[] if cover else m.archive_images(i,candidates.get(i['requested_title'],[])[:18],3)
   originals=[a for a in originals if max(a['width'],a['height'])>=800]
   cover=cover or next((a for a in originals if a.get('cover_art')),None) or m.helper.cover(page,entities,i['year'])
   if cover and i['year']<=2000 and any(word in cover.get('verification',{}).get('published_title','').lower() for word in ['remastered','reignited','n. sane','trilogy']):cover=None
   if not cover:return None,{**i,'reason':'No identified native original-cover art acquired'}
   if max(cover.get('width',0),cover.get('height',0))<800:return None,{**i,'reason':'Original art is below 800px native quality gate'}
   e=m.helper.entry(page,i['year'],cover);e['title']=i['display_title'];e['provenance']['coverage_module']='user-requested-game-additions';e['provenance']['requested_wikipedia_subject']=i['requested_title']
   e['images'] += [a for a in originals if a['url']!=cover['url']]
   if e['title']=='Need for Speed: Most Wanted' and e['year']==2005 and '1262560' in cover.get('url',''):raise ValueError('Rejected2012Criterioncover for2005BlackBoxgame')
   m.helper.context_images(e)
   e['summary']=re.split(r'(?<=[.!?])\s+',e['body'][0])[0]
   if len(e['summary'])>240:e['summary']=e['summary'].split(',')[0].rstrip('.')+'.'
   return e,None
  except Exception as ex:return None,{**i,'reason':str(ex)}
 with ThreadPoolExecutor(max_workers=4) as pool:
  fs=[pool.submit(process,p) for p in records]
  for n,f in enumerate(as_completed(fs),1):
   e,err=f.result()
   if e:outputs.append(e)
   if err:held.append(err)
   m.atomic(HERE/'user-requested-game-additions.json',{'schema_version':1,'scope_notice':'Exact curator-requested original games; source prose/editions and artwork identities retained.','entries':outputs})
   m.atomic(CACHE/'audit.json',{'requested':targets,'initial_missing':todo,'admitted':len(outputs),'completed':n,'held':held})
   print('USER GAMES',n,'/',len(records),'ADMITTED',len(outputs),'HELD',len(held),flush=True)
 print('FINAL',len(outputs),'HELD',len(held),flush=True)
if __name__=='__main__':main()
