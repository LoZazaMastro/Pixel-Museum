"""Independent bounded peer of frozen original-Wii-U music publications."""
from pathlib import Path
import hashlib,json,re
from html import unescape
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'build/research/soundtrack-broad/splatoon-original-2015'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
candidate=P/'forty-eight-original-wiiu-publications-candidate.json'
assert sha(candidate)=='488bad179fe00a3432fea03c585c3483226b67b6123915532d7a833492f7e393'
d=load(candidate);room=d['entries'][0];tracks=room['tracks']
assert len(tracks)==48 and len({t['youtube_id'] for t in tracks})==48
assert room['entry_id']=='wikipedia-52874820' and room['match_year']==2015
assert room['composer']=='Toru Minegishi and Shiho Fujii' and not room['full_album_collection']
for r in d['source_receipts']:assert sha(ROOT/r['path'])==r['sha256']
playlist=load(P/'playlist-original-flat.json')
source_by_id={r['id']:r for r in playlist['entries']}
assert len(source_by_id)==68
native=load(P/'native-publication-research.json')
native_by_id={r['youtube_id']:r for r in native['records']}
rows=[]
# Every title was independently read against original game's named music:
# 0..10 multiplayer/news;11..20 player setup/plaza/shop/lobby;
#21..39 campaign/shops/boss phases;40..47 finale/theme/startup/credits.
for i,t in enumerate(tracks):
 assert t['youtube_id'] in source_by_id
 rpath=ROOT/t['publication_metadata_receipt'];r=load(rpath)
 assert r['id']==t['youtube_id']
 assert r['title']==t['source_actual_publication_title']==source_by_id[t['youtube_id']]['title']
 assert r['channel_id']=='UC8fmuIzkgFQ5DBXMEGA0PQQ' and r['channel']=='Everyday OST'
 assert r['duration']==t['duration_seconds'] and 0<r['duration']<=300
 assert r['native_compatible_avc_aac'] and r['avc_format_count']>0 and r['aac_format_count']>0
 assert r['resolver_client']=='TVHTML5' and 'AVC' in r['native_selection']
 assert native_by_id[t['youtube_id']]['metadata']==r
 assert not t['playback_verified_on_ps5'] and not t['official_uploader_verified']
 assert t['creator']=='Nintendo sound team' and t['game_composer_credits']==['Toru Minegishi','Shiho Fujii']
 assert t['recording_version']=='Original Wii U game archival music publication.'
 assert not any(k in t for k in ['independently_matched_composers','individual_composer','cue_composer'])
 assert 'Game-level' in t['artist_credit_scope']
 assert not r['description'] and 'empty' in t['verification_method']
 assert not re.search(r'\b(live|extended|remix|splatoon [23])\b',r['title'],re.I)
 assert not any(key in r for key in ['formats','cookies','stream_url','url'])
 rows.append({'index':i,'youtube_id':r['id'],'actual_title':r['title'],'display_title':t['title'],
  'duration_seconds':r['duration'],'channel_id':r['channel_id'],'actual_description_empty':True,
  'native_AVC_AAC_metadata':'PASS_not_console_playback','metadata_receipt':t['publication_metadata_receipt'],
  'metadata_sha256':sha(rpath),'semantic_status':'PASS_original_WiiU_collection_context_game_level_credits'})
publisher=(P/'publisher-splatune.html').read_text(encoding='utf8')
plain=unescape(re.sub('<[^>]+>',' ',publisher))
assert all(s in plain for s in ['Wii U','2015','Splattack!','37','10','14','61','4541993024681'])
history=(P/'nintendo-history.html').read_text(encoding='utf8')
assert 'https://www.nintendo.com/jp/character/splatoon/en/history/' in history and '2015' in history and 'Wii U' in history
expected={t['youtube_id'] for t in tracks}|{r['youtube_id'] for r in d['collection_limits']['excluded_publications']}|{r['youtube_id'] for r in d['collection_limits']['unavailable_held']}
unaccounted=[{'youtube_id':vid,'title':r['title'],'reason':'Explicit LIVE publication; excluded from original game collection.'} for vid,r in source_by_id.items() if vid not in expected]
assert not unaccounted and len(d['collection_limits']['excluded_publications'])==19
held=d['collection_limits']['unavailable_held']
assert len(held)==1 and held[0]['youtube_id']=='o_AxB4vJFcs'
report={
 'status':'PASS_ALL48_RECORDING_IDENTITIES_AND_NATIVE_METADATA_CORRECTIONS_APPLIED',
 'candidate':{'path':candidate.relative_to(ROOT).as_posix(),'sha256':sha(candidate)},
 'independent_review_scope':'All48actual title/channel/duration/native receipts and all53source hashes; complete publication descriptions are explicitly empty, not fabricated or treated as evidence.',
 'tracks':rows,'recordings_pass':48,'held_new_recordings':[],
 'game_identity':'Original Nintendo Splatoon, Wii U,2015. Distinct original-game campaign/shop/boss-phase variants allowed; no second/third game or live performance admitted.',
 'publisher_primary':{'path':(P/'publisher-splatune.html').relative_to(ROOT).as_posix(),'sha256':sha(P/'publisher-splatune.html'),
   'subject':'KADOKAWA official Splatune product JAN4541993024681, released2015-10-21',
   'inventory':{'music':37,'jingles':10,'sound_effects':14,'total':61},'correspondence':'48game-phase/shop public recordings are not asserted to be the same61retailmasters.'},
 'Nintendo_primary':{'path':(P/'nintendo-history.html').relative_to(ROOT).as_posix(),'sha256':sha(P/'nintendo-history.html'),
   'url':'https://www.nintendo.com/jp/character/splatoon/en/history/','subject':'Original2015WiiU game chronology'},
 'composer_verification':{'url':'https://en.wikipedia.org/wiki/Splatoon_(video_game)',
   'retrieval_kind':'web_tool_actual_page_read_this_peer','actual_infobox':'Composers Toru Minegishi; Shiho Fujii; platform WiiU, original release2015.',
   'scope':'Game-level score attribution only; Nintendo sound team per recording does not assert joint individual cue authorship.'},
 'required_corrections':[],
 'corrections_verified':['All19excluded publications are now persisted, including the last5LIVE rows. All68source entries are accounted for.',
 'All48recording_version fields now state only Original Wii U game archival music publication.'],
 'source_playlist_entries':68,'expected_final_accounting':{'selected':48,'excluded':19,'unavailable':1},
 'limits':['Native AVC/AAC format metadata is not physical PS5 playback or audio-fingerprint validation.',
 'All48optional descriptions are empty. Title/uploader/duration/playlist and publisher-original-game context establish archival selection without inventing publication descriptions.',
 'Different shop/boss/area arrangements can share durations; no byte-identical or exactretail-master claim is made.',
 'No exact album completeness, recording quality level or wholly individual cue-composer allocation is asserted.'],
 'checked_utc':datetime.now(timezone.utc).isoformat(),'master_or_catalog_changed':False}
out=P/'independent-forty-eight-original-wiiu-review.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(out.relative_to(ROOT),sha(out))
