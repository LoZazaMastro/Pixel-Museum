"""Coherent ninth native/media/music QA. No deployment."""
import json,hashlib,datetime,shutil,runpy
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'build/research/ninth-source86-font-scoped'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(n):
 p=R/n;return {'path':str(n).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
def log(n):
 b=(R/n).read_bytes();return b.decode('utf16' if b.startswith(b'\xff\xfe') else 'utf8')
master='content/catalog.json';runtime='build/runtime-preview/content/catalog.json';proofname='build/research/ninth-media7-mega3-source86-final-proof.json';proof=load(proofname)
assert sha(R/master)=='7f707634e66bb7ebe33018ab8282b1a077b59d6d4a8bfd4215e8776833b0ba97' and sha(R/runtime)=='d2d83337b6fad0c07f6980aa41d1bd3fb4a4a250fd8fc3ee6cb41768cdc13822'
projection=runpy.run_path(str(R/"tools/runtime-catalog.py"));assert hashlib.sha256(projection["encoded"](projection["project"](load(master),sha(R/master)))).hexdigest()==sha(R/runtime)
a,b=load(master),load(runtime);ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']};assert len(ai)==len(bi)==1400 and len(a['entry_aliases'])==23 and a['entry_aliases']==b['entry_aliases']
assert len(proof['body_records'])==196
for item in proof['body_records']:
 for ix in [ai,bi]:assert hashlib.sha256(ix[item['entry_id']]['body'][item['index']].encode()).hexdigest()==item['body_sha256']
for eid,e in ai.items():assert e['body']==bi[eid]['body'] and e.get('story_headings',[])==bi[eid].get('story_headings',[]) and e.get('models',[])==bi[eid].get('models',[])
backup=R/'build/research/native-eighth-source85-recoverable';assert sha(backup/'manifest.json')=='87d83a384154892b546b509829795e9d5c21e300be4e966d6a13b9a975272f63';back=json.loads((backup/'manifest.json').read_text());assert len(back['files'])==221
for name in [master,runtime]:
 old=json.loads((backup/'files'/name).read_text());oldix={e['id']:e for e in old['entries']};newix=ai if name==master else bi;assert {eid for eid in newix if newix[eid]!=oldix[eid]}==set(proof['changed_owners'])
audit=load('build/research/font-coverage.json');diff=load(O.relative_to(R)/'inventory-diff.json');assert not any(diff[k] for k in ['new_ordinary','removed_ordinary','new_runs','removed_runs']);assert audit['ordinary_glyph_status']=='pass' and not audit['stale_subset_inputs'] and not audit['complex_shaping_unresolved'] and not audit['static_complex_runs_unsupported'];assert len(audit['ordinary_codepoints'])==944
fonts={}
for p in (R/'assets/fonts').glob('*.huifont'):
 n=p.relative_to(R).as_posix();assert sha(p)==back['files'][n]['sha256'] and sha(p)==sha(R/'build/runtime-preview/assets/fonts'/p.name);fonts[n]=rec(n)
native=rec('build/eboot.elf');assert native['sha256']=='71fba8ccff3f25efc1ad610c28b44d459513abc20cc0482ae4c026952a6059f7';assert sha(R/'src/museum/object_scene.cpp')=='ef7098bd072920b6df7cb8247d4425e23fa3224c701fd70956774e45d0888ea8';assert 'Native compile/link/conversion complete' in log(O.relative_to(R)/'native-build.log')
assert 'Native parser equivalence PASS: 1400 entries' in log('build/research/ninth-runtime-equivalence.log')
g=load('build/research/story-text-profile/unillustrated-scenes-current.json');assert g['catalog']==runtime and g['explicit_catalog_override'] and g['catalog_entries']==1400 and g['count']==334;assert len(g['scoped_composed_narrative_checks'])==7
shutil.copyfile(R/'build/research/story-text-profile/unillustrated-scenes-current.json',O/'actual-profile-frozen.json');media=[]
for x in proof['new_narrative_image_records']:
 hits=[r for r in g['scoped_composed_narrative_checks'] if r['entry_id']==x['owner'] and x['paragraph'] in r['paragraphs'] and r['image_url']==x['url']];assert len(hits)==1;media.append(dict(x,actual_card=hits[0]['card'],actual_complete_paragraphs=hits[0]['paragraphs']))
eid='burnout-revenge';tracks=bi[eid]['soundtrack']['tracks'];assert len(tracks)==40
for x,y in zip(ai[eid]['soundtrack']['tracks'],tracks):
 for k in ['youtube_id','url','title','creator','source_page','start_seconds','end_seconds']:assert x.get(k)==y.get(k)
mlog=log(O.relative_to(R)/'actual-burnout40-playlist.log')
for n in [1,21,40]:assert f'PASS scoped playlist {eid} {n}/40:' in mlog
u=bi['workbook-07-28-lua'];manifest=load('assets/images/manifest.json');url=u['images'][u['preferred_image']]['url'];assert url=='https://www.lua.org/images/lua-logo-nolabel.ps' and manifest['metadata'][url]['alpha_preserved']
for q in proof['lua_quarantined_image_urls']:
 for ix in [ai,bi]:assert q['url'] not in [i['url'] for i in ix[q['owner']].get('images',[])]
slog=log(O.relative_to(R)/'actual-new-media-mega-lua.log');assert slog.count('PASS ninth current narrative ')==8 and '13actual4K captures GL0' in slog
screens=list((R/'build/previews').glob('ninth-*-4k.png'))+list((R/'build/previews').glob('playlist-scoped-burnout-revenge-*-4k.png'));assert len(screens)==16
rooms=[];games=0
for e in b['entries']:
 effective=e.get('soundtrack_rooms') or ([e['soundtrack']] if e.get('soundtrack',{}).get('tracks') else []);rooms.extend(effective);games+=e.get('kind')=='game' and bool(effective)
rootproof='build/research/playhub-semantic-coverage/wiki-clarity/root-actual196-master-runtime-proof.json';rp=load(rootproof);assert rp['cards']==196
for n in [master,runtime]:assert rp['actual_catalogues'][n]['sha256']==sha(R/n)
report={'status':'PASS_COHERENT_NINTH_NATIVE_LOSSLESS_RAM_OPTIMIZATION_SCOPED_ACTUAL_UI_NOT_CONSOLE','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'catalogues':[rec(master),rec(runtime)],'authoring_proof':rec(proofname),'root_independent_196proof':rec(rootproof),'root_proof_producer':rec('tools/verify-reviewed-clarity196-actual-root.py'),'all196body_hashes_exact':True,'only_seven_owner_records_changed':proof['changed_owners'],'native':native,'native_source':rec('src/museum/object_scene.cpp'),'memory_change_review':rec('build/research/model-merge-reserve-probe/root-independent-reserve-merge-review.json'),'memory_change_measured_receipt':rec('build/research/model-merge-reserve-probe/verification.json'),'native_compile_performed_once':True,'font_rebake_performed':False,'font_binary_reused':fonts,'ordinary_codepoints':944,'static_complex_phrases':9,'font_inventory_diff':rec(O.relative_to(R)/'inventory-diff.json'),'font_revalidation':rec(O.relative_to(R)/'font-revalidation.log'),'new_media7_actual':media,'new_music_room':{'entry_id':eid,'public_recordings':40,'inventory':41,'held':1,'all_runtime_identity_credit_source_bounds_exact':True,'all40_title_creator_glyphs_pass':True,'first_middle_final4K_GL0':True,'physical_playback_verified':False},'effective_native_music_counts':{'rooms':len(rooms),'unique_game_entries':games,'tracks':sum(len(r['tracks']) for r in rooms),'rule':'soundtrack_rooms replaces legacy soundtrack; do not count retainedDS2 legacy16 again.'},'lua_cover':{'url':url,'local_png':rec(manifest['images'][url]),'alpha_preserved':True,'wrong_anime_display_removed':True,'both_theme_gallery4K_checked':True},'actual_profile':rec('build/research/ninth-source86-font-scoped/actual-profile-frozen.json'),'actual_narrative_gaps':334,'main_body_gaps':sum(x['feature']<0 for x in g['entries']),'feature_gaps':sum(x['feature']>=0 for x in g['entries']),'scoped_scene_count':7,'scoped_source_paragraphs':sum(len(x['paragraphs']) for x in g['scoped_composed_narrative_checks']),'scoped_capture_log':rec(O.relative_to(R)/'actual-new-media-mega-lua.log'),'scoped_capture_fixture':rec('host/ninth_scoped_checks.hpp'),'screenshots':[rec(p.relative_to(R)) for p in screens],'eighth_recovery_manifest':rec('build/research/native-eighth-source85-recoverable/manifest.json'),'limits':['No physical PS5 FPS120/instantloading/haptic/playback claim.','Lossless merge optimization demonstrated RAM/worker prep benefit only; total model start time did not improve in measured fullGLpair.','334 actual unillustrated narrative scenes remain.','No signing/staging/package/FTP: final fastpath is held for next coherent group10.','Unchanged font binary944points/9phrases reused without bake.']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'receipt_sha256':sha(O/'verification.json'),'native_sha256':native['sha256'],'effective_rooms':len(rooms),'unique_games':games,'effective_tracks':sum(len(r['tracks']) for r in rooms),'gaps':g['count'],'screenshots':len(screens)}))
