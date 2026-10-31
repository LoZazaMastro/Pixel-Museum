import json,importlib.util,hashlib,re,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p);B=p.RESEARCH/'battlefield1-complete';B.mkdir(exist_ok=True)
albums=[('1407040703','Base game','Battlefield 1 (Original Soundtrack)'),('1419853875','They Shall Not Pass','Battlefield 1: They Shall Not Pass (Original Soundtrack)'),('1410331764','In the Name of the Tsar','Battlefield 1: In the Name of the Tsar (Original Game Soundtrack)'),('1459697920','Turning Tides','Battlefield 1: Turning Tides (Original Soundtrack)'),('1459701682','Apocalypse','Battlefield 1: Apocalypse (Original Soundtrack)')]
rows=[]
for aid,exp,title in albums:
 data=json.loads((B/('apple-'+aid+'.json')).read_text());collection=[x for x in data['results'] if x.get('wrapperType')=='collection'][0]
 for song in data['results']:
  if song.get('wrapperType')!='track':continue
  rows.append({'album_apple_id':aid,'expansion':exp,'album':collection['collectionName'],'album_expected':title,'album_copyright':collection['copyright'],'album_release':collection['releaseDate'],'album_source':'https://music.apple.com/us/album/'+aid,'number':song['trackNumber'],'title':song['trackName'],'duration_seconds':song['trackTimeMillis']/1000,'artist':song['artistName'],'track_apple_id':song['trackId']})
p.write(B/'official-album-inventory.json',{'scope':'Exact official Apple album inventory, complete25+7+16+12+12, metadata-only no media downloads. Album release dates are not the base-game or expansion launch dates.','albums':[{**{'album_apple_id':a,'expansion':e},'count':sum(x['album_apple_id']==a for x in rows),'source_receipt':'apple-'+a+'.json','sha256':hashlib.sha256((B/('apple-'+a+'.json')).read_bytes()).hexdigest()} for a,e,t in albums],'track_count':len(rows),'tracks':rows})
folder=B/'tracks';folder.mkdir(exist_ok=True)
for i,row in enumerate(rows):
 key=row['album_apple_id']+'-'+str(row['number']).zfill(2);out=folder/(key+'.json')
 if out.exists() and __import__('json').loads(out.read_text()).get('candidates'):continue
 queries=[row['title']+' Battlefield 1 '+row['expansion']+' Johan Soderqvist Topic', '"'+row['title']+'" "Johan Soderqvist"', '"'+row['title']+'" "Battlefield 1" Topic']
 candidates=[];errors=[]
 try:
  for q in queries:
   for v in p.search(q):
    vid=v.get('id','')
    if vid in [x.get('youtube_id') for x in candidates]:continue
    if p.norm(v.get('title',''))!=p.norm(row['title']):continue
    try:
     w=p.watch(vid);desc=w['shortDescription'];titlegood=p.norm(w['title'])==p.norm(row['title']);channelgood=w['channelId']=='UCQ2yZBTDSxzo7nfWcismReg';durationgood=abs(float(w['lengthSeconds'])-row['duration_seconds'])<4
     exactalbum=any(p.norm(line)==p.norm(row['album_expected']) or p.norm(line)==p.norm(row['album']) for line in desc.splitlines())
     if titlegood and channelgood and durationgood and exactalbum and 'Provided to YouTube by' in desc and ('Electronic Arts' in desc or 'EA' in desc):
      candidates.append({'youtube_id':vid,'actual_metadata_receipt':str(p.RESEARCH/'watch'/(vid+'.json')).replace(str(R)+'\\','').replace('\\','/'),'actual_title':w['title'],'actual_uploader':w['author'],'actual_description':desc,'duration_seconds':int(w['lengthSeconds']),'channel_id':w['channelId'],'identity_checks':{'exact_title':titlegood,'exact_official_album':exactalbum,'official_topic_channel':channelgood,'album_duration_difference_seconds':round(float(w['lengthSeconds'])-row['duration_seconds'],3)}});break
    except Exception as ex:errors.append(str(ex))
   if candidates:break
  p.write(out,{**row,'state':'matched_official_album_recording' if candidates else 'recording_pending','candidates':candidates,'errors':errors});print(i+1,'/',len(rows),row['expansion'],row['title'],len(candidates),flush=True)
 except Exception as ex:p.write(out,{**row,'state':'search_error','errors':[str(ex)]});print('ERROR',i+1,row['title'],str(ex),flush=True)
 records=[json.loads(x.read_text()) for x in folder.glob('*.json')];p.write(B/'recording-discovery-checkpoint.json',{'publication_status':'research_only','checked':len(records),'matched':sum(x['state']=='matched_official_album_recording' for x in records),'tracks':records})
