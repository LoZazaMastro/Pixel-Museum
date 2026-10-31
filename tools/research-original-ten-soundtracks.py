"""Bounded, resumable original-recording recovery; never publishes a batch."""
import importlib.util,json,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
music=module('music','content/expansion/soundtrack-broad-pipeline.py')
video=module('video','tools/discover-museum-videos.py')
targets=json.loads((music.RESEARCH/'checkpoints/original-ten-recovery-targets.json').read_text(encoding='utf8'))['entries']
queries={
 'wikipedia-81114':'Super Mario World Title SNES Game Music Daily Koji Kondo',
 'wikipedia-198005':'F Zero Mute City SNES 1990 original soundtrack',
 'wikipedia-165820':'A Link to the Past Overworld OST SNES original',
 'workbook-11-24-sonic-the-hedgehog-2':'Sonic the Hedgehog 2 Emerald Hill DeoxysPrime OST',
 'wikipedia-153399':'Donkey Kong Country Life in the Mines SNES 1994 OST',
 'wikipedia-165824':'Majoras Mask Clock Town First Day N64 OST original',
 'wikipedia-8484':'Deus Ex UNATCO 2000 Alexander Brandon original soundtrack',
 'lumines':'Lumines PSP 2004 original soundtrack Shake Ya Body',
 'workbook-01-11-resident-evil-4':'Resident Evil 4 2005 Serenity Game Music Daily',
 'wikipedia-20324939':'Demons Souls Maiden Astraea 2009 PS3 Shunsuke Kida original soundtrack',
}
allgames=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']
music.TITLE_YEARS={music.norm(e['title']):{v['year'] for v in allgames if v['kind']=='game' and music.norm(v['title'])==music.norm(e['title'])} for e in allgames if e['kind']=='game'}
out=music.RESEARCH/'independent-original-ten-recovery.json'
previous=json.loads(out.read_text(encoding='utf8')) if out.exists() else {'entries':[]}
done={r['entry_id']:r for r in previous['entries']}
for target in targets:
 e=target['entry'];eid=e['id']
 if done.get(eid,{}).get('track'):continue
 composers,url,evidence=target['composers'],target['source'],target['evidence']
 if eid=='lumines':
  composers=['Takayuki Nakamura','Katsumi Yokota'];url='https://en.wikipedia.org/wiki/Lumines:_Puzzle_Fusion';evidence='Exact2004 original game article names Nakamura as composer and describes Yokota assisting composition; do not infer original2004 credit solely from2018 Remastered album.'
 result={'entry_id':eid,'title':e['title'],'year':e['year'],'independent_composer_credit':{'composers':composers,'composer_source':url,'composer_evidence':evidence},'query':queries[eid],'errors':[]}
 try:
  candidates=video.search(queries[eid])['entries']
  for row in candidates[:10]:
   if len(row['id'])!=11:continue
   if any(x in row['title'].lower() for x in ['cover','remix','extended','metal version','jazz','orchestra','3ds','remastered','remake','3d world']):continue
   try:
    track,reason=music.consider(e,row,composers,url)
    if not track:result['errors'].append({'id':row['id'],'title':row['title'],'reason':reason});continue
    native=video.metadata(row['id'],row)
    result.update(track=track,native_avc_aac_metadata=native.get('native_compatible_avc_aac'),native_metadata_receipt='build/research/video-discovery/video-'+row['id']+'.json')
    print('FOUND',e['title'],track['title'],row['id'],flush=True);break
   except Exception as error:result['errors'].append({'id':row['id'],'title':row['title'],'reason':str(error)})
   time.sleep(.3)
 except Exception as error:result['errors'].append({'stage':'search','reason':str(error)})
 done[eid]=result
 music.write(out,{'publication_status':'independent_research_only','scope':'Exact original-game source context, original public recording metadata and native AVC/AAC metadata; no media downloaded or PS5 playback tested. Final music ingestion is separate.','entries':list(done.values())})
 if not result.get('track'):print('HELD',e['title'],len(result['errors']),flush=True)
