import json,importlib.util,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];sp=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p);B=p.RESEARCH/'user-priority/dmc';B.mkdir(exist_ok=True)
rooms=[('Devil May Cry',2001,1426650,['Public Enemy','Cathedral','Lock and Load Original']),('Devil May Cry 2',2003,1426670,['Fire Away','Shoot the Works','Wings of Guardian']),('Devil May Cry 3: Dante\'s Awakening',2005,1426680,['Devils Never Cry','Cerberus Battle','Vergil Battle 2']),('Devil May Cry 4',2008,1426690,['Out of Darkness','The Time Has Come','Sworn Through Swords']),('Devil May Cry 5',2019,1050460,['Devil Trigger','Crimson Cloud','Subhuman','Bury the Light','Silver Bullet'])]
for game,year,appid,tracks in rooms:
 folder=B/p.norm(game);folder.mkdir(exist_ok=True);url='https://store.steampowered.com/app/'+str(appid)+'/?l=english';f=folder/'steam-source.html'
 if not f.exists():
  try:
   raw=p.fetch(url);assert 'Capcom' in p.text(raw) or 'CAPCOM' in p.text(raw);f.write_text(raw,encoding='utf-8');p.write(folder/'steam-source.json',{'source_page':url,'local_source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'actual_body_validated':True})
  except Exception as ex:p.write(folder/'steam-source.json',{'source_page':url,'error':str(ex)})
 for i,title in enumerate(tracks,1):
  out=folder/(str(i).zfill(2)+'.json')
  if out.exists():continue
  query=game+' '+title+' Capcom Sound Team Topic';rows=[];errors=[]
  for flat in p.search(query):
   try:
    w=p.watch(flat['id']);lines=[x.strip() for x in w['shortDescription'].splitlines() if x.strip()];provided=bool(lines and lines[0].startswith('Provided to YouTube by '));own=bool(re.search(r'(?i)Capcom|Casey Edwards|Jeff Rona|Cody Matthew Johnson|Ali Edwards',w['author']))
    if not provided and not own:continue
    rows.append({'youtube_id':flat['id'],'actual_title':w['title'],'actual_uploader':w['author'],'duration_seconds':int(w['lengthSeconds']),'metadata_receipt':'build/research/soundtrack-broad/watch/'+flat['id']+'.json','actual_publication_lines':lines,'provided_by_label':provided})
   except Exception as ex:errors.append(str(ex))
  p.write(out,{'game':game,'year':year,'requested_title':title,'primary_game_album_source':url,'publication_status':'research_only_needs_manual_exact_role_review','candidates':rows,'errors':errors});print(game,title,len(rows),flush=True)
