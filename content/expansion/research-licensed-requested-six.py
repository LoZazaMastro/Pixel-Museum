import json,re,hashlib,importlib.util,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];sp=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p);B=p.RESEARCH/'licensed-requested-six';B.mkdir(exist_ok=True)
rooms=[{'game':'Need for Speed: Underground','year':2003,'source_page':'https://n-europe.com/news/news-underground-music-list/','source_kind':'contemporary full game credit/tracklist transcription','tracks':[('Lil Jon East Side Boyz Ying Yang Twins','Get Low'),('The Crystal Method','Born Too Slow'),('Rancid','Out of Control'),('Rob Zombie','Two Lane Blacktop'),('Static X','The Only'),('Element Eighty','Broken Promises'),('Story of the Year','And the Hero Will Drown'),('T.I.','24s')]},
{'game':'Need for Speed: Most Wanted','year':2005,'source_page':'https://darkzero.co.uk/ea-announce-nfs-most-wanted-soundtrack/','source_kind':'contemporary report of EA publisher soundtrack announcement','tracks':[('Celldweller Styles of Beyond','Shapeshifter'),('Disturbed','Decadence'),('Avenged Sevenfold','Blinded in Chains'),('Bullet for My Valentine','Hand of Blood'),('Static X','Skinnyman'),('Mastodon','Blood and Thunder'),('The Prodigy','You will Be Under My Wheels'),('Jamiroquai','Feels Just Like It Should Timo Maas Remix')]},
{'game':'Burnout Paradise','year':2008,'source_page':'https://www.mobygames.com/game/32402/burnout-paradise/credits/ps3/','source_kind':'transcription of original2008PS3 licensed game music credits','tracks':[('Guns N Roses','Paradise City'),('Avril Lavigne','Girlfriend'),('Alice in Chains','Would'),('Airbourne','Too Much Too Young Too Fast'),('Seether','Fake It'),('Faith No More','Epic'),('Twisted Sister','I Wanna Rock'),('Adam and the Ants','Stand and Deliver')]},
{'game':'FIFA Street','year':2005,'source_page':'https://www.nintendoworldreport.com/news/10328/ea-reveals-soundtracks-for-upcoming-games','source_kind':'original EApressrelease reprintedverbatim, FIFAStreet sectionONLY notFightNight','tracks':[('Dizzee Rascal','Stand Up Tall'),('Fatboy Slim','Jin Go Lo Ba'),('SL2','On a Ragga Tip'),('Roni Size Stamina MC','On and On'),('Timo Maas','Feedback Welcome'),('Max Sedgley','Happy Fatboy Slim Remix'),('DJ Marky XRS','Rudebwoy'),('Artificial Intelligence','Slam')]},
{'game':'Need for Speed: Hot Pursuit 2','year':2002,'source_page':'https://oldgamesdownload.com/wp-content/uploads/Need_for_Speed_Hot_Pursuit_2_Manual_GameCube_EN.pdf','source_kind':'original publisher GameCube manual music credit pages; also exact2002Windows credittranscript Moby142118','tracks':[('The Buzzhorn','Ordinary'),('Course of Nature','Wall of Shame'),('Bush','The People That We Love'),('Rush','One Little Victory'),('Uncle Kracker','Keep It Coming')]},
{'game':'The Warriors','year':2005,'source_page':'https://www.rockstargames.com/img/manuals/en_us/TheWarriors-PS2-Manual.pdf','source_kind':'original Rockstar publisher PS2manual MusicCredits explicitly licensing filmrecordings','tracks':[('Barry De Vorzon','Theme from The Warriors'),('Barry De Vorzon','Baseball Furies Chase'),('Joe Walsh','In the City The Warriors Soundtrack'),('Arnold McCuller','Nowhere to Run'),('Genya Ravan','Love Is a Fire'),('Desmond Child','Last of an Ancient Breed'),('Amii Stewart','Knock on Wood')]}]
p.write(B/'requested-tracklists.json',{'publication_status':'research_only','entries':rooms})
for e in rooms:
 folder=B/p.norm(e['game']);folder.mkdir(exist_ok=True);u=e['source_page'];suffix='.pdf' if '.pdf' in u else '.html';source=folder/('game-association-source'+suffix)
 if not source.exists():
  try:
   raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read();assert not any(x in raw.lower()[:8000] for x in [b'client challenge',b'just a moment',b'access denied']);source.write_bytes(raw);p.write(folder/'game-source-receipt.json',{'source_page':u,'source_type':e['source_kind'],'local_source':str(source.relative_to(R)),'sha256':hashlib.sha256(raw).hexdigest(),'retrieval_status':'actual_body_saved_semantic_review_pending'})
  except Exception as ex:p.write(folder/'game-source-receipt.json',{'source_page':u,'retrieval_status':'not_fetched','error':str(ex)})
 for i,(artist,title) in enumerate(e['tracks'],1):
  out=folder/(str(i).zfill(2)+'.json')
  if out.exists():continue
  rows=[];errors=[];query=artist+' '+title+' official audio'
  for flat in p.search(query)[:4]:
   try:
    w=p.watch(flat['id']);rows.append({'youtube_id':flat['id'],'actual_publication':w})
   except Exception as ex:errors.append(str(ex))
  p.write(out,{'game':e['game'],'year':e['year'],'number':i,'requested_artist':artist,'requested_title':title,'game_association_source':u,'source_kind':e['source_kind'],'candidates':rows,'errors':errors,'publication_status':'research_only_needs_manual_exact_recording_review'});print(e['game'],i,title,len(rows),flush=True)
