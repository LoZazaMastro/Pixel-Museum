"""Add only the missing canonical karaoke vocal; never duplicate the four present."""
from pathlib import Path
import copy,hashlib,json,re
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/soundtrack-broad/yakuza-zero-public-collection'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
parent=P/'yakuza-zero-91-public-passages-vocal-extended-candidate.json'
assert sha(parent)=='856ee702582e146c2a7983d890d1a477094c1e96be52e41bbc044aec2607cac4'
out=copy.deepcopy(load(parent));room=out['entries'][0]
watchpath=ROOT/'build/research/soundtrack-broad/watch/p025z6l57Z0.json'
watch=load(watchpath)
chapters=[]
for line in watch['shortDescription'].splitlines():
 m=re.fullmatch(r'(\d+:\d{2}(?::\d{2})?) - (.+)',line)
 if m:
  n=0
  for part in m[1].split(':'):n=n*60+int(part)
  chapters.append((n,m[2],line))
expected=[('Judgement -Shinpan- (Kiryu, Full Ver.)',12335,12568),
 ('24-hour Cinderella (Majima, Full Ver.)',12921,13176),
 ('\u00d73 SHINE (Yuki, Full Ver.)',13176,13402),
 ('Heartbreak Mermaid (Chika, Full Ver.)',13599,13875)]
present=[]
for title,start,end in expected:
 matches=[t for t in room['tracks'] if (t['source_actual_chapter_title'],t['start_seconds'],t['end_seconds'])==(title,start,end)]
 assert len(matches)==1
 present.append({'title':title,'start_seconds':start,'end_seconds':end,'action':'preserved_existing_record_no_duplicate'})
i=next(i for i,c in enumerate(chapters) if c[1]=='Rouge of Love (Hibiki)')
start,source_title,line=chapters[i];end=chapters[i+1][0]
assert (start,end)==(14087,14224)
assert not any((t['youtube_id'],t['start_seconds'])==('p025z6l57Z0',start) for t in room['tracks'])
primary=ROOT/'build/research/soundtrack-broad/yakuza-zero-public-collection/sega-yakuza5-original-composition-press-reprint.html'
text=primary.read_text(encoding='utf8')
assert all(token in text for token in ['Rouge of Love','青木千紘','堀井亮佑'])
t=copy.deepcopy(room['tracks'][-2])
t.update(title='Rouge of Love (Hibiki, game version)',creator='Chihiro Aoki',composer='Chihiro Aoki',lyricist='Ryosuke Horii',vocalist='Hibiki',
 start_seconds=start,end_seconds=end,duration_seconds=end-start,
 source_actual_chapter_title=source_title,source_actual_chapter_line=line,
 recording_version='Original 2015 game karaoke passage, Hibiki game version.',
 recording_album='Yakuza 0 original 2015 game: regional themes and karaoke',
 composer_source='https://www.4gamer.net/games/139/G013951/20121219002/',
 recording_context_source='https://ryu-ga-gotoku.com/zero/lyric/',
 credit_scope='Underlying Rouge of Love composition and lyrics are credited by the original SEGA manufacturer announcement. The selected Hibiki performance is identified by the actual 2015 game archive chapter; it is not the announcement\'s Kaguya/Shion recording.',
 rights='SEGA and the credited composition, performance and recording contributors retain their respective rights. Public archival upload is not an official publisher delivery.')
credit={
 'subject':'Rouge of Love (Hibiki, Yakuza 0 game version)',
 'source_page':t['composer_source'],'actual_primary_HTML':{'path':primary.relative_to(ROOT).as_posix(),'sha256':sha(primary)},
 'source_kind':'SEGA manufacturer press announcement reproduced verbatim by 4Gamer, 2012-12-19',
 'underlying_song_composer':'Chihiro Aoki','underlying_song_lyricist':'Ryosuke Horii',
 'source_recordings':'Rouge of Love feat.Kaguya / feat.Shion in the earlier Yakuza 5 album',
 'selected_recording':'2015 Yakuza 0 Hibiki game passage, as labeled by the original archive description',
 'scope_limit':'The composition credits do not assert that the selected Hibiki recording is the earlier Kaguya/Shion album master.',
 'archive_watch_receipt':{'path':watchpath.relative_to(ROOT).as_posix(),'sha256':sha(watchpath)},
 'checked_utc':datetime.now(timezone.utc).isoformat()}
creditpath=P/'rouge-of-love-hibiki-underlying-song-credit.json'
creditpath.write_text(json.dumps(credit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
t['credit_verification_receipt']=creditpath.relative_to(ROOT).as_posix()
room['tracks'].append(t)
room['coverage_status']='AVAILABLE_PUBLIC_COLLECTION_88_SIDE_A_B_PASSAGES_PLUS_4_ORIGINAL_GAME_VOCALS'
room['album_completeness']['supplemental_original_game_vocals']=4
out['publication_status']='awaiting_independent_final_Rouge_vocal_peer_NEXT_not_admitted'
out['parent_91_freeze']={'path':parent.relative_to(ROOT).as_posix(),'sha256':sha(parent)}
out['scope']='Original 2015 game archival collection: 88 Side A/B passages plus Bubble, Kiryu Baka Mitai game cut, Kurenai and Hibiki Rouge of Love. Canonical Judgement, Cinderella, SHINE and Mermaid vocals already remain in the original 88.'
out['source_receipts'].append({'path':creditpath.relative_to(ROOT).as_posix(),'sha256':sha(creditpath)})
out['recording_identity_limits'].append('The requested four full karaoke vocals already occur in the original 88. They are preserved without duplicating their exact audio intervals. Rouge of Love adds only the Hibiki version, not alternate takes.')
assert len(room['tracks'])==92 and len({(t['youtube_id'],t['start_seconds'],t['end_seconds']) for t in room['tracks']})==92
assert room['tracks'][:-1]==load(parent)['entries'][0]['tracks']
out['checked_utc']=datetime.now(timezone.utc).isoformat()
target=P/'yakuza-zero-92-public-passages-final-vocals-candidate.json'
target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report={'status':'PASS_MECHANICAL_PRESERVATION_SOURCE_PEER_PENDING',
 'candidate_sha256':sha(target),'parent91_sha256':sha(parent),'old_records_preserved_exactly':91,
 'canonical_full_vocals_already_present':present,'only_new_track':t,
 'unique_passages':92,'no_alternate_take_duplicates_added':True,'no_master_or_SOURCE71_mutation':True,'physical_PS5_playback_verified':False}
receipt=P/'final-five-canonical-vocals-preservation-review.json'
receipt.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(target.relative_to(ROOT),sha(target))
print(receipt.relative_to(ROOT),sha(receipt))
