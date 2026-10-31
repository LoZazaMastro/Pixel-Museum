"""Keep reviewed88 immutable; add three real original-game vocal passages."""
from pathlib import Path
import copy,hashlib,json,re
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/soundtrack-broad/yakuza-zero-public-collection'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
original=P/'yakuza-zero-88-public-chapters-candidate.json'
assert sha(original)=='1d1080ae01a1cf660af4f1e27305c597d1845fe8ad20086fed2b9869cb3e6021'
out=copy.deepcopy(load(original));room=out['entries'][0]
watchpath=ROOT/'build/research/soundtrack-broad/watch/p025z6l57Z0.json'
watch=load(watchpath)
chapters=[]
for line in watch['shortDescription'].splitlines():
 m=re.fullmatch(r'(\d+:\d{2}(?::\d{2})?) - (.+)',line)
 if m:
  n=0
  for part in m[1].split(':'):n=n*60+int(part)
  chapters.append((n,m[2],line))
assert chapters==sorted(chapters)
acq=load(P/'vocal-primary-source-acquisition.json')
valid={r['url']:r for r in acq['sources'] if r.get('actual_subject_and_credit_body_verified')}
toys_single='https://www.toysfactory.co.jp/sp/artist/shonan/disco/1287'
toys_album='https://www.toysfactory.co.jp/sp/artist/shonan/disco/1335'
sega_press='https://www.4gamer.net/games/139/G013951/20121219002/'
assert all(u in valid for u in (toys_single,toys_album,sega_press))
# Direct public pages from134r returned403/503; these are explicitly structured
# facts read from the web search index of those PRIMARY artist discographies,
# never represented as locally acquired/full-read HTML.
facts={
 'retrieval_kind':'primary_artist_search_index_subject_credit_fields',
 'direct_HTML_status':'HELD_403_503_no_retries_no_challenge_bypass',
 'sources':[
  {'url':'https://www.134r.com/discography/s15.html','subject':'Bubble / original2015single','release':'2015-03-04','lyricist':'Shonan no Kaze','composer':'Shonan no Kaze','arranger':'Shonan no Kaze'},
  {'url':'https://www.134r.com/discography/a09.html','subject':'COME AGAIN / original2015album, ORANGE DISC track8 Kurenai','release':'2015-05-27','lyricist':'Shonan no Kaze','composer':'Shonan no Kaze; Gakuji Matsuda','arranger':'Gakuji Matsuda; Shonan no Kaze'}],
 'independent_actual_HTML_identity':{u:valid[u] for u in (toys_single,toys_album)},
 'Baka_Mitai_underlying_song_roles':{'source':sega_press,'source_kind':'SEGA manufacturer announcement reproduced verbatim by4Gamer, dated2012-12-19','actual_row':'Baka Mitai feat.Saejima&Akiyama','composer':'Mitsuharu Fukuyama','lyricist':'Ryosuke Horii','arranger':'Mitsuharu Fukuyama','scope':'Underlying original composition/lyrics only. This is not evidence that the selectedKiryu game-cut audio is the2012Saejima/Akiyama recording.'},
 'Kiryu_variant_scope':{'source':'https://www.sega.jp/topics/detail/160125_soft_1/','retrieval_kind':'web_tool_actual_primary_page_read','version':'2016KiwamiAishu variant','role_corroboration_only':['Mitsuharu Fukuyama composition','Ryosuke Horii lyrics','Kazuma Kiryu vocalist'],'not_used_as_recording_identity':True},
 'checked_utc':datetime.now(timezone.utc).isoformat()}
factpath=P/'vocal-authorship-and-original-game-context.json'
factpath.write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
supp=[]
specs=[
 ('Bubble','Bubble (Japanese opening, 2015)','Shonan no Kaze','Shonan no Kaze','Shonan no Kaze',toys_single,'https://www.134r.com/discography/s15.html','Japanese 2015 opening song; original game archival passage.'),
 ('Bakamitai (Kiryu)','Baka Mitai (Kiryu, game version)','Mitsuharu Fukuyama','Ryosuke Horii','Kazuma Kiryu',sega_press,sega_press,'Original 2015 game karaoke passage, Kiryu game version; 2-minute game cut.'),
 ('Kurenai','Kurenai (Japanese ending, 2015)','Shonan no Kaze; Gakuji Matsuda','Shonan no Kaze','Shonan no Kaze',toys_album,'https://www.134r.com/discography/a09.html','Japanese 2015 ending song; original game archival passage.')]
for source_title,title,composer,lyricist,vocals,context,credit,version in specs:
 i=next(i for i,c in enumerate(chapters) if c[1]==source_title)
 start,_,line=chapters[i];end=chapters[i+1][0]
 assert (start,end)=={'Bubble':(0,296),'Bakamitai (Kiryu)':(12801,12921),'Kurenai':(14502,14881)}[source_title]
 t=copy.deepcopy(room['tracks'][0])
 for k in ['album_disc','disc_track_number','album_track_number','original_album_tracklist_source','published_album_track_title','published_album_artist_credit','artist_credit_scope']:
  t.pop(k,None)
 t.update(title=title,creator=composer,composer=composer,lyricist=lyricist,vocalist=vocals,
  duration_seconds=end-start,start_seconds=start,end_seconds=end,
  source_actual_chapter_title=source_title,source_actual_chapter_line=line,
  recording_version=version,recording_album='Yakuza 0 original 2015 game: regional themes and karaoke',
  composer_source=credit,recording_context_source=context,
  credit_verification_receipt=factpath.relative_to(ROOT).as_posix(),
  rights='SEGA, Shonan no Kaze, 134RECORDINGS/TOY\'S FACTORY where applicable, and their composition/performance/recording contributors retain their respective rights. Public archival upload is not an official publisher delivery.')
 supp.append(t)
assert len(supp)==3
corrections=[]
for t in room['tracks']:
 if t['title']=='Fatal Confrict':
  corrections.append({'source_chapter':t['source_actual_chapter_line'],'old_display':t['title'],'new_display':'Fatal Conflict','published_album_title':t['published_album_track_title']})
  assert t['published_album_track_title']=='Fatal Conflict'
  t['title']='Fatal Conflict'
room['tracks']+=supp
room['composer']='SEGA Sound Team, Shonan no Kaze and contributing musicians'
room['curator_note']='Listen to the music of SEGA Sound Team, Shonan no Kaze and contributing musicians from Yakuza 0.'
room['coverage_status']='AVAILABLE_PUBLIC_COLLECTION_88_SIDE_A_B_PASSAGES_PLUS_3_ORIGINAL_GAME_VOCALS'
room['album_completeness']['supplemental_original_game_vocals']=3
room['album_completeness']['not_exhaustive']=True
out['publication_status']='awaiting_independent_vocal_supplement_peer_NEXT_not_admitted'
out['scope']='Original2015game archival collection:88publishedSideA/B passages plusBubble,KiryuBakaMitai game cut andKurenai. No2025DirectorsCut or retail-master completeness claim.'
out['parent_88_freeze']={'path':original.relative_to(ROOT).as_posix(),'sha256':sha(original)}
out['display_only_corrections']=corrections
out['source_receipts'] += [dict(r) for r in valid.values()]+[{'path':factpath.relative_to(ROOT).as_posix(),'sha256':sha(factpath)}]
out['recording_identity_limits'][1]='The shared upload contains other regional/bonus material. This candidate adds only three original-game vocal passages to the reviewed88, excluding other bonus/store loops and2025DirectorsCut material.'
out['recording_identity_limits'] += ['Bubble andKurenai are the2015Japanese version themes; their presence does not claim they belong to the Western release.', 'BakaMitai uses the actual120-secondKiryu game passage; not the full commercial song or laterKiwamiAishu arrangement.', 'Artist primary composition fields forBubble/Kurenai were readable through the public search index; direct artistHTML was403/503. Actual labelHTML separately confirms exact2015release/game association.']
assert len(room['tracks'])==91 and len({(t['youtube_id'],t['start_seconds'],t['end_seconds']) for t in room['tracks']})==91
out['checked_utc']=datetime.now(timezone.utc).isoformat()
target=P/'yakuza-zero-91-public-passages-vocal-extended-candidate.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(target.relative_to(ROOT),sha(target))
print('original88 unchanged',sha(original))
