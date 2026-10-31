import json,hashlib,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];sp=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p);B=p.RESEARCH/'user-priority/classic-extra';B.mkdir(exist_ok=True)
for name,url in [('ape-composer-interview','https://daily.redbullmusicacademy.com/2017/10/soichi-terada-interview/'),('fantavision-original-game','https://en.wikipedia.org/wiki/Fantavision'),('viewtifuljoe-album-transcription','https://www.squareenixmusic.com/albums/v/viewtifuljoe.shtml')]:
 f=B/(name+'.html')
 try:
  body=f.read_text(encoding='utf-8') if f.exists() else p.fetch(url);assert len(body)>5000;f.write_text(body,encoding='utf-8');p.write(B/(name+'-receipt.json'),{'source_page':url,'local_source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'retrieval_type':'actual HTML body, secondary album transcription' if 'transcription' in name else 'actual HTML body'})
 except Exception as ex:p.write(B/(name+'-receipt.json'),{'source_page':url,'error':str(ex)})
for key,query in [('joe1hero','Viewtiful Joe original soundtrack Joe the Hero'),('joe1red','Viewtiful Joe Some Like It Red Hot original soundtrack'),('joe1blue','Viewtiful Joe Blue the True Hero original soundtrack'),('joe2dino','Viewtiful Joe 2 Ten Million Years BC original soundtrack'),('joe2star','Viewtiful Joe 2 Starship Viewties original soundtrack')]:
 f=B/(key+'.json')
 if f.exists():continue
 rows=[]
 for q in p.search(query)[:3]:
  try:rows.append({'youtube_id':q['id'],'actual_publication':p.watch(q['id'])})
  except Exception as ex:rows.append({'youtube_id':q['id'],'error':str(ex)})
 p.write(f,{'query':query,'candidates':rows,'publication_status':'research_only_manual_review_needed'});print(key,len(rows),flush=True)
vid='GWExQ7szPaM'
try:p.write(B/'fantavision-na-second.json',{'youtube_id':vid,'actual_publication':p.watch(vid)})
except Exception as ex:p.write(B/'fantavision-na-second.json',{'youtube_id':vid,'error':str(ex)})
