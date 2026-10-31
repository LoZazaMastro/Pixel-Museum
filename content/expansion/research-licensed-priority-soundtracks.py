import json,importlib.util,re,urllib.request,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];sp=importlib.util.spec_from_file_location('p',R/'content/expansion/soundtrack-broad-pipeline.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p);B=p.RESEARCH/'licensed-priority';B.mkdir(exist_ok=True)
sources={'burnout3-publisher-announcement-report':'https://www.gamespot.com/articles/burnout-3-soundtrack-revealed/1100-6105497/','underground2-ea-press-release-reprint':'https://nintendoworldreport.com/pr/10054/snoop-dogg-headlining-nfsu-2-soundtrack'}
for key,url in sources.items():
 f=B/(key+'.html')
 if not f.exists():
  try:
   raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=20).read();assert b'Client Challenge' not in raw and b'Access Denied' not in raw;f.write_bytes(raw)
  except Exception as ex:p.write(B/(key+'-fetch.json'),{'source_page':url,'retrieval_status':'not_retrieved','error':str(ex)})
rosters=[{'game':'Burnout 3: Takedown','year':2004,'source_page':sources['burnout3-publisher-announcement-report'],'source_kind':'contemporary_report_of_EA_publisher_soundtrack_announcement','tracks':[
('Franz Ferdinand','This Fire'),('The F-Ups','Lazy Generation'),('Rise Against','Paper Wings'),('My Chemical Romance',"I'm Not Okay (I Promise)"),('Yellowcard','Breathing'),('Ash','Orpheus'),('Sugarcult','Memory'),('Chronic Future','Time And Time Again'),('Fall Out Boy','Reinventing the Wheel to Run Myself Over'),('The Von Bondies',"C'mon C'mon"),('Ramones','I Wanna Be Sedated'),('Autopilot Off','Make A Sound')]},
{'game':'Need for Speed: Underground 2','year':2004,'source_page':sources['underground2-ea-press-release-reprint'],'source_kind':'EA_press_release_republished_verbatim','tracks':[
('Snoop Dogg, The Doors','Riders On The Storm (Fredwreck Remix)'),('Rise Against','Give It All'),('Queens of the Stone Age','In My Head'),('Spiderbait','Black Betty'),('Skindred','Nobody'),('Xzibit','LAX'),('Terror Squad','Lean Back'),('The Bronx','Notice of Eviction'),('Helmet','Crashing Foreign Cars'),('Killradio','Scavenger'),('Mudvayne','Determined'),('Unwritten Law','The Celebration Song')]}]
p.write(B/'curated-track-requests.json',{'publication_status':'research_only','scope':'Licensed-song requests from actual game soundtrack announcements; firsttracks expressly requested by user. No original-score substitution. Recording-specific source/edition validation still required.','entries':rosters})
for room in rosters:
 folder=B/p.norm(room['game']);folder.mkdir(exist_ok=True)
 for i,(artist,title) in enumerate(room['tracks'],1):
  f=folder/(str(i).zfill(2)+'.json')
  if f.exists():continue
  queries=[artist.replace(', ',' ')+' '+title+' audio Topic'];candidates=[];errors=[]
  for q in queries:
   for row in p.search(q):
    vid=row['id'];candidate_title=row.get('title','');key=p.norm(candidate_title);expected=p.norm(title)
    if not (key==expected or expected in key):continue
    try:
     w=p.watch(vid);d=w['shortDescription'];lines=[x.strip() for x in d.splitlines() if x.strip()];provided=lines[0].startswith('Provided to YouTube by ') if lines else False
     if not provided:continue
     line=lines[1] if len(lines)>1 else '';pn=p.norm(line);artist_names=artist.split(', ')
     if not all(p.norm(a) in pn for a in artist_names):continue
     if any(z in p.norm(w['title']) for z in ['liveat','livefrom','nightcore','slowed','tribute','coverby']):continue
     years=[int(x) for x in re.findall(r'[\u2117\u00a9]\s*(\d{4})',d)];original_year=bool(years and min(years)<=room['year'])
     exacttitle=p.norm(w['title'])==expected
     candidates.append({'youtube_id':vid,'actual_title':w['title'],'actual_uploader':w['author'],'actual_metadata_receipt':'build/research/soundtrack-broad/watch/'+vid+'.json','provided_by':lines[0],'delivered_recording_artist_line':line,'album':lines[2] if len(lines)>2 else '', 'phonogram_years':years,'original_era_phonogram':original_year,'exact_title':exacttitle,'duration_seconds':int(w['lengthSeconds']),'full_role_fields':[x for x in lines if ':' in x and any(k in x.lower() for k in ['composer','lyricist','producer','arranger','vocal','remix'])]})
    except Exception as ex:errors.append(str(ex))
  p.write(f,{'game':room['game'],'year':room['year'],'number':i,'requested_artist':artist,'requested_title':title,'game_association_source':room['source_page'],'source_kind':room['source_kind'],'state':'recording_candidates_pending_manual_review' if candidates else 'recording_pending','candidates':candidates,'errors':errors});print(room['game'],i,artist,title,len(candidates),flush=True)
