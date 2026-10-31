import json,importlib.util,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];sp=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p);B=p.RESEARCH/'licensed-priority';base=json.loads((R/'content/expansion/soundtrack-licensed-primary-research.json').read_text());sources={e['match_title']:e['source_page'] for e in base['entries']}
rooms=[('Need for Speed: Carbon',2006,[('Wolfmother','Joker and the Thief'),('Kyuss','Hurricane'),('Ladytron','Fighting in Built Up Areas'),('Goldfrapp','Ride a White Horse Serge Santiago Remix'),('Ladytron','Sugar Jagz Kooner Remix'),('Gary Numan','Are Friends Electric'),('Vitalic','My Friend Dario'),('The Presets','Steamworks'),('Tiga','Good as Gold'),('Yonderboi','People Always Talk About the Weather Junkie XL Remix'),('Every Move a Picture','Signs of Life'),('Eagles of Death Metal',"Don't Speak I Came to Make a Bang")]),('FIFA Street 2',2006,[('Editors','Munich'),('The Subways','Rock and Roll Queen'),('Art Brut','Formed a Band'),('End of Fashion','O Yeah'),('Boy Kill Boy','Suzie'),('Pendulum','Hold Your Colour Bi Polar Mix'),('Sway','Flo Fashion'),('Curumin','Guerreiro'),('Coldcut Roots Manuva','True Skool'),('Bran Van 3000 Curtis Mayfield','Astounded')])]
for game,year,tracks in rooms:
 folder=B/p.norm(game);folder.mkdir(exist_ok=True)
 for i,(artist,title) in enumerate(tracks,1):
  out=folder/(str(i).zfill(2)+'.json')
  if out.exists():continue
  candidates=[];errors=[];query=artist+' '+title+' audio Topic'
  for row in p.search(query):
   vid=row['id']
   try:
    w=p.watch(vid);lines=[x.strip() for x in w['shortDescription'].splitlines() if x.strip()]
    if not lines or not lines[0].startswith('Provided to YouTube by '):continue
    if re.search(r'(?i)live at|live from|slowed|nightcore|tribute|karaoke',w['title']):continue
    candidates.append({'youtube_id':vid,'actual_title':w['title'],'actual_uploader':w['author'],'metadata_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','publication_lines':lines,'duration_seconds':int(w['lengthSeconds'])})
   except Exception as ex:errors.append(str(ex))
  p.write(out,{'game':game,'year':year,'number':i,'requested_artist':artist,'requested_title':title,'game_association_source':sources[game],'source_kind':'original_Electronic_Arts_investor_press_release_PDF','publication_status':'research_only_needs_manual_recording_review','candidates':candidates,'errors':errors});print(game,i,title,len(candidates),flush=True)
