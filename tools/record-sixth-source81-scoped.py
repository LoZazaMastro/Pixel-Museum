"""Bind SOURCE81 fresh fonts/scoped actual UI without a physical-console claim."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,struct
R=Path(__file__).resolve().parents[1];O=R/'build/research/sixth-source81-font-scoped'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def rec(n):
 f=R/n;return {'path':str(n).replace('\\','/'),'bytes':f.stat().st_size,'sha256':sha(f)}
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
def log(n):
 b=(R/n).read_bytes();return b.decode('utf16' if b.startswith(b'\xff\xfe') else 'utf8')
master='content/catalog.json';runtime='build/runtime-preview/content/catalog.json';assert sha(R/master)=='b9d1186dcb05cfc24a16862a3a524d684aae9a6ba804e7a11ebdf4b848d118ba';assert sha(R/runtime)=='e2df21a36acc23ddf6b56e54bd6dcc919bb26103f8b934b256dff4ebfd886e89'
a,b=load(master),load(runtime);ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']};assert len(ai)==len(bi)==1400 and a['entry_aliases']==b['entry_aliases'] and len(a['entry_aliases'])==23
proofpath='build/research/sixth-media11-sp4-source81-final-proof.json';proof=load(proofpath);assert len(proof['body_records'])==190
for item in proof['body_records']:
 for idx in [ai,bi]:assert hashlib.sha256(idx[item['entry_id']]['body'][item['index']].encode()).hexdigest()==item['body_sha256']
for eid,e in ai.items():
 assert e['body']==bi[eid]['body'] and e.get('story_headings',[])==bi[eid].get('story_headings',[])
 assert [(f['id'],f['body'],f.get('story_headings',[])) for f in e.get('editorial_features',[])]==[(f['id'],f['body'],f.get('story_headings',[])) for f in bi[eid].get('editorial_features',[])]
 assert e.get('models',[])==bi[eid].get('models',[])
assert sum(len(e.get('models',[])) for e in a['entries'])==30
sp=bi['workbook-01-07-game-boy-advance-sp'];assert sp['year']==2003 and sp['date']['month']==2 and sp['date']['day']==14
backup=R/'build/research/native-fifth-source76-recoverable';assert sha(backup/'manifest.json')=='68886290e8e202233bea5dcf1585a63f6bc669c557c65a57e81feb8213ae0c8c';back=json.loads((backup/'manifest.json').read_text(encoding='utf8'));assert len(back['files'])==137
for path,item in back['files'].items():assert sha(backup/'files'/path)==item['sha256']
audit=load('build/research/font-coverage.json');runs=load('build/research/offline-script-shaping/script-runs.json');diff=load('build/research/sixth-source81-font-scoped/inventory-diff.json')
assert audit['ordinary_glyph_status']=='pass' and not audit['stale_subset_inputs'] and not audit['complex_shaping_unresolved'] and not audit['static_complex_runs_unsupported'];assert len(audit['ordinary_codepoints'])==943 and len(audit['static_complex_runs_required'])==9 and len(runs['runs'])==26
assert len(diff['new_ordinary'])==16 and not diff['removed_ordinary'] and not diff['new_runs']
fonts={p.relative_to(R).as_posix():{k:v for k,v in rec(p.relative_to(R)).items() if k!='path'} for p in (R/'assets/fonts').glob('*.huifont')};assert len(fonts)==6
for path,v in fonts.items():assert sha(R/'build/runtime-preview/assets/fonts'/Path(path).name)==v['sha256']
native=rec('build/eboot.elf');assert native['sha256']=='71aa22952d2f2155c53e90023040270f9bac87e89ca19ec9b37a4639f67046af';assert 'Native compile/link/conversion complete; existing payload untouched.' in log(O.relative_to(R)/'native-build.log')
assert 'Native parser equivalence PASS: 1400 entries' in log('build/research/equivalence-sixth-media11-sp4-source81.log')
for name in ['shaped-runs.log','inventory-unit.log','unicode-actual-4k.log','actual-profile.log','actual-new-playlists.log']:assert 'PASS' in log(O.relative_to(R)/name)
g=load('build/research/story-text-profile/unillustrated-scenes-current.json');assert g['catalog']==runtime and g['catalog_entries']==1400 and g['explicit_catalog_override'] and g['count']==363;assert len(g['scoped_composed_narrative_checks'])==15 and sum(len(x['paragraphs']) for x in g['scoped_composed_narrative_checks'])==35
shutil.copyfile(R/'build/research/story-text-profile/unillustrated-scenes-current.json',O/'actual-profile-frozen.json');media=[]
for item in proof['new_narrative_image_records']:
 hits=[x for x in g['scoped_composed_narrative_checks'] if item['owner'] in [x['entry_id'],x['feature_id']] and item['paragraph'] in x['paragraphs'] and item['url']==x['image_url']];assert len(hits)==1,item;media.append(dict(item,actual_card=hits[0]['card'],actual_paragraphs=hits[0]['paragraphs']))
assert len(media)==11
music=[];mlog=log(O.relative_to(R)/'actual-new-playlists.log');screens=[]
for item in proof['new_music_rooms']:
 eid=item['entry_id'];x=ai[eid]['soundtrack']['tracks'];y=bi[eid]['soundtrack']['tracks'];assert len(x)==len(y)==item['recordings']
 for u,v in zip(x,y):
  for key in ['youtube_id','url','title','creator','source_page','start_seconds','end_seconds']:assert u.get(key)==v.get(key),(eid,key)
 count=len(y)
 for index in [0,count//2,count-1]:assert 'PASS scoped playlist '+eid+' '+str(index+1)+'/'+str(count)+':' in mlog
 music.append({'entry_id':eid,'recordings':count,'every_runtime_identity_credit_source_bound_matches':True,'all_title_creator_glyphs_checked':True,'first_middle_final4K_GL0':True,'physical_playback_verified':False});screens+=list((R/'build/previews').glob('playlist-scoped-'+eid+'-*-4k.png'))
sptext=log(O.relative_to(R)/'sp-actual-4k.log');assert '4 paragraphs, 2 narrative photographs, 3 cards' in sptext and sptext.count('3840x2160 GL=0x0')==3;screens+=list((R/'build/previews').glob('story-workbook-01-07-game-boy-advance-sp-*-4k.png'))
for eid,name in [('dandara','dandara'),('workbook-10-15-disco-elysium','disco'),('animal-crossing','acnh')]:
 s=log(O.relative_to(R)/(name+'-feature-actual-4k.log'));assert s.count('3840x2160 GL=0x0')==4;screens+=list((R/'build/previews').glob('feature-'+eid+'-*-4k.png'))
rooms=[room for e in b['entries'] for room in ([e['soundtrack']] if e.get('soundtrack') else [])+e.get('soundtrack_rooms',[])];games=sum(e.get('kind')=='game' and bool(e.get('soundtrack',{}).get('tracks') or any(x.get('tracks') for x in e.get('soundtrack_rooms',[]))) for e in b['entries']);atlas=(R/'assets/fonts/cjk-subset.huifont').read_bytes();dims=struct.unpack_from('<HH',atlas,8);assert dims==(2048,2189)
globalpath=R/'build/research/offline-script-shaping/verification.json';old=load(globalpath);shutil.copyfile(globalpath,O/'inherited-full-font-verification.json');fresh=dict(old);fresh.update(status='fresh16CJKglyphs_scoped_current_ui_and_native_compatibility_PASS',recorded_utc=datetime.now(timezone.utc).isoformat(),actual_source_sha256=audit['input_source_sha256'],coherent_catalogues={p:{k:v for k,v in rec(p).items() if k!='path'} for p in [master,runtime]},ordinary_display_codepoints=943,visible_ordinary_codepoints=len(audit['visible_ordinary_codepoints']),current_complete_script_phrases=9,genuine_harfbuzz_word_boundary_runs=26,files=fonts,scoped_verification='build/research/sixth-source81-font-scoped/verification.json',checks_rerun_this_group=['fresh16CJKglyphbake','current943ordinary4facesboth4Kthemes','26shapedrun104facecases','15actualscopedscenes35sourceparagraphs/fullorder/scrollendpoint','SP3actual4Kcards/4sourceparagraphs/correctFeb14date','3feature12captures','5newroomsalltitle/creatorglyphs+first/middle/final4K','nativecompilelinkno-op'],inherited_regressions_not_rerun='Earlier full product-regression receipt preserved separately; unchanged MK348/study/display/media tests were not rerun.',physical_ps5_tested=False);globalpath.write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report={'status':'PASS_SIXTH_COHERENT_FONTS_NATIVE_COMPAT_SCOPED_ACTUAL_UI_NOT_CONSOLE','recorded_utc':datetime.now(timezone.utc).isoformat(),'catalogues':[rec(master),rec(runtime)],'authoring_proof':rec(proofpath),'backup_manifest':rec('build/research/native-fifth-source76-recoverable/manifest.json'),'all137backupfiles_sha_reverified':True,'native':native,'fonts':fonts,'new_glyphs':diff['new_ordinary'],'ordinary_codepoints':943,'visible_ordinary_codepoints':len(audit['visible_ordinary_codepoints']),'static_complex_phrases':9,'shaped_word_runs':26,'fallback_dimensions':dims,'fallback_R8_bytes':dims[0]*dims[1],'native_equivalence':rec('build/research/equivalence-sixth-media11-sp4-source81.log'),'all190_reviewed_bodies_sha_exact':True,'SP_date':sp['date'],'SP_old_id_retained':True,'new_media11_actual':media,'new_music':music,'all_music_rooms':len(rooms),'unique_game_entries_with_music':games,'all_music_tracks':sum(len(room.get('tracks',[])) for room in rooms),'actual_profile':rec('build/research/sixth-source81-font-scoped/actual-profile-frozen.json'),'actual_narrative_gaps':363,'main_body_gaps':sum(x['feature']<0 for x in g['entries']),'feature_gaps':sum(x['feature']>=0 for x in g['entries']),'scoped_scenes':15,'scoped_source_paragraphs':35,'screenshots':[rec(p.relative_to(R)) for p in screens],'scope_limits':['No physical PS5 playback/performance/FPS/haptic validation.','No FTP or deployment.','363 actual unillustrated narrative scenes remain.','Switch213 NEXT and other source research are excluded.','Confirmed photoanalog/compatiblefocusrumble fixes intentionally await this coherentQA receipt.']};(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'receipt_sha256':sha(O/'verification.json'),'rooms':len(rooms),'unique_games':games,'tracks':sum(len(room.get('tracks',[])) for room in rooms),'gaps':363,'screenshots':len(screens)}))
