"""Freeze three public original-game music collections; metadata only, no master mutation."""
from pathlib import Path
import json,re,hashlib,unicodedata,datetime
R=Path(__file__).resolve().parents[1]; P=R/'build/research/soundtrack-broad/modern-three-public-collections'
def load(name):return json.loads((P/name).read_text(encoding='utf8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def sec(s):return sum(int(n)*60**i for i,n in enumerate(reversed(s.split(':'))))
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).replace('version','ver')
def save(name,d):(P/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
master=R/'content/catalog.json';source=load('published-album-tracklists-whitelist.json'); entries={x['id']:x for x in json.loads(master.read_text(encoding='utf8'))['entries']}
tracks_by_game=[];bound_rows=[];held=[]
configs=[('wikipedia-43295977','Tekken 7',2015,'Tpyk_OhgNMk','TEKKEN Project and contributing musicians','https://music.apple.com/us/album/tekken-7-original-soundtrack/1722993388','https://sweeprecord.ocnk.net/product/6'),('workbook-04-14-mortal-kombat-x','Mortal Kombat X',2015,'i8T9rJ34ra0','NetherRealm Studios and contributing composers','https://www.trmk.org/features/interview_mortal_kombat_x_ed_boon_e3_2014/','https://dynamedion.com/news/mortal-kombat-x/'),('wikipedia-45032491','Forza Motorsport 6',2015,'CqzG_0hPq9E','Kaveh Cohen and Michael Nielsen','https://thekoalition.com/2016/the-music-behind-forza-motorsport-6-an-interview-with-the-composers','https://music.apple.com/us/album/forza-motorsport-6-original-soundtrack/1472031057')]
for eid,title,year,vid,artist,credit_source,context_source in configs:
 assert eid in entries and entries[eid]['title']==title and entries[eid]['year']==year
 watch=load(vid+'-actual-watch.json');codec=load('native-'+vid+'.json');assert codec.get('native_compatible_avc_aac') is True
 length=int(watch['lengthSeconds']);desc=watch['shortDescription'];parsed=[]
 if vid=='Tpyk_OhgNMk':
  rows=re.findall(r'^(\d+:\d\d(?::\d\d)?)\s*\u2022\s*(.+)$',desc,re.M);album=source['tekken7-apple.html']+source['tekken7-vol2-apple.html'];assert len(rows)==len(album)==142
  for i,((stamp,label),published) in enumerate(zip(rows,album)):
   assert norm(label)==norm(published['title']),(i,label,published['title'])
   start=sec(stamp);end=sec(rows[i+1][0]) if i+1<len(rows) else length
   parsed.append({'title':published['title'],'source_actual_chapter_title':label,'source_actual_chapter_line':stamp+' \u2022 '+label,'start_seconds':start,'end_seconds':end,'published_title_source':published['source_page'],'published_duration_ms':published['duration_ms'],'recording_album':'Tekken 7 Soundtrack Plus' if i<83 else 'Tekken 7 Original Soundtrack Vol.2','recording_version':'Original same-game score: console, Fated Retribution and Season Pass music (2015, 2017-2021); public archival collection.','credit_scope':'Publisher album artist/project attribution. Individual composition, lyrics and performance roles are not inferred from the project name.','artist_credit_scope':'Album/project-level collective, including contributing composers and performers; not a per-cue co-composition assertion.'})
 else:
  rows=re.findall(r'^\[([\d:]+)\s*-\s*([\d:]+)\]\s*(\d+)\.?\s+(.+)$',desc,re.M);assert len(rows)==(72 if vid=='i8T9rJ34ra0' else 38)
  for a,b,num,label in rows:
   number=int(num)
   if vid=='i8T9rJ34ra0' and (60<=number<=71 or number in [31,32,33,35,36]):
    held.append({'youtube_id':vid,'source_track':number,'title':label,'reason':'Curator medley edit; original in-game arrangement not independently identified.' if number>=60 else 'Very short named effect/failure/success cue; not promoted as a musical recording.'});continue
   if vid=='CqzG_0hPq9E':
    published=source['forza-apple.html'][number-1]; assert norm(label)==norm(published['title']),(label,published['title'])
   else:published={}
   parsed.append({'title':published.get('title',label),'source_actual_chapter_title':label,'source_actual_chapter_line':'['+a+' - '+b+'] '+num+'. '+label,'start_seconds':sec(a),'end_seconds':sec(b),'recording_album':title+' public original-game score collection','recording_version':'Original 2015 game score; public archival collection. Capture hardware not identified.','credit_scope':'Independently documented game-level contributors only; uploader blanket Dan Forden attribution is not accepted as individual cue authorship.' if vid=='i8T9rJ34ra0' else 'Named score composers corroborated by their first-person interview and publisher-delivered album.','published_title_source':published.get('source_page',credit_source)})
 tracks=[];last=-1
 for item in parsed:
  assert 0<=item['start_seconds']<item['end_seconds']<=length and item['start_seconds']>=last
  last=item['end_seconds'];watchurl='https://www.youtube.com/watch?v='+vid
  tr={'youtube_id':vid,'url':watchurl,'title':item.pop('title'),'creator':artist,'uploader':watch['author'],'channel_url':'https://www.youtube.com/channel/'+watch['channelId'],'source_page':watchurl,'publishing_kind':'archival_game_recording','official_uploader_verified':False,'duration_seconds':item['end_seconds']-item['start_seconds'],'source_publication_duration_seconds':length,'composer_source':credit_source,'recording_context_source':context_source,'recording_year':year,'rights':('Bandai Namco Entertainment and the credited music contributors retain their respective rights.' if vid=='Tpyk_OhgNMk' else 'Warner Bros., NetherRealm Studios and the credited music contributors retain their respective rights.' if vid=='i8T9rJ34ra0' else 'The credited composers, Microsoft and applicable recording rights holders retain their respective rights.')+' The public archival upload is not an official publisher delivery.','publication_metadata_receipt':str((P/(vid+'-actual-watch.json')).relative_to(R)).replace('\\','/'),'native_codec_metadata_receipt':str((P/('native-'+vid+'.json')).relative_to(R)).replace('\\','/'),'native_codec_metadata_verified':True,'playback_verified_on_ps5':False,**item}
  if vid=='Tpyk_OhgNMk':tr.pop('recording_year',None) # The combined collection spans several official same-game editions.
  tracks.append(tr);bound_rows.append({'entry_id':eid,'youtube_id':vid,'title':tr['title'],'source_line':tr['source_actual_chapter_line'],'start_seconds':tr['start_seconds'],'end_seconds':tr['end_seconds'],'source_duration':length})
 room={'entry_id':eid,'match_title':title,'match_year':year,'title':'Listen to '+title,'composer':artist,'curator_note':'Listen to the music of '+artist+' from '+title+'.','tracks':tracks,'replace_existing_tracks':True,'full_album_collection':False,'coverage_status':'AVAILABLE_PUBLIC_ORIGINAL_GAME_COLLECTION_NOT_EXHAUSTIVE','album_completeness':{'available_passages':len(tracks),'claim':'Actual public source chapters, with verified positive finite bounds. No assertion of every game file, exact retail masters, all regional versions or complete released albums.'}}
 tracks_by_game.append(room)
result={'schema_version':1,'publication_status':'NEXT_AWAITING_INDEPENDENT_PEER_NOT_ADMITTED','source_catalog_sha256':digest(master),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Three original-game public collections. No media/audio downloaded. Native codec metadata compatibility is separate from physical PS5 playback.','entries':tracks_by_game,'held_source_passages':held}
save('three-modern-original-public-collections-candidate.json',result);save('chapter-bound-reconciliation.json',{'status':'CHECKED_ACTUAL_SOURCE_LINES','rows':bound_rows,'held':held})
print(json.dumps({'candidate_sha256':digest(P/'three-modern-original-public-collections-candidate.json'),'rooms':len(tracks_by_game),'tracks':sum(len(x['tracks']) for x in tracks_by_game),'counts':[(x['match_title'],len(x['tracks'])) for x in tracks_by_game],'held':len(held)}))
