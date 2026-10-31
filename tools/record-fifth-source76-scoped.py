"""Record coherent fifth-group fonts, scoped actual UI and native compatibility."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,shutil,struct,runpy
R=Path(__file__).resolve().parents[1]; O=R/'build/research/fifth-source76-font-scoped'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(path):
 p=R/path;return {'path':str(path).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(path):return json.loads((R/path).read_text(encoding='utf8'))
master='content/catalog.json';runtime='build/runtime-preview/content/catalog.json'
assert sha(R/master)=='5f25b333317a231768d8003ebae658062a63a3d15443f6164d6724a9b4be7fd7'
assert sha(R/runtime)=='dac9d922d972cd8d2a8501ee98d4aff9bbad40620285b977dc6eea3e15ca8f6a'
a,b=load(master),load(runtime);ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']};assert len(ai)==len(bi)==1400 and a['entry_aliases']==b['entry_aliases'] and len(a['entry_aliases'])==23
proofpath='build/research/fifth-switch5-media5-source76-final-proof.json';proof=load(proofpath)
for eid,e in ai.items():
 assert e['body']==bi[eid]['body'] and e.get('story_headings',[])==bi[eid].get('story_headings',[])
 assert [(f['id'],f['body'],f.get('story_headings',[])) for f in e.get('editorial_features',[])]==[(f['id'],f['body'],f.get('story_headings',[])) for f in bi[eid].get('editorial_features',[])]
 assert e.get('models',[])==bi[eid].get('models',[])
assert sum(len(e.get('models',[])) for e in a['entries'])==30
backup=R/'build/research/native-fourth-source73-recoverable';assert sha(backup/'manifest.json')=='d4953323e9fe749ff4674af60c1d44193044666f0c4b8a190309a3dd7cc5f1f3'
back=json.loads((backup/'manifest.json').read_text(encoding='utf8'));assert len(back['files'])==84
for path,item in back['files'].items():assert sha(backup/'files'/path)==item['sha256']
audit=load('build/research/font-coverage.json');runs=load('build/research/offline-script-shaping/script-runs.json');diff=load('build/research/fifth-source76-font-scoped/inventory-diff.json')
assert audit['ordinary_glyph_status']=='pass' and not audit['stale_subset_inputs'] and not audit['complex_shaping_unresolved'] and not audit['static_complex_runs_unsupported']
assert len(audit['ordinary_codepoints'])==927 and len(audit['static_complex_runs_required'])==9 and len(runs['runs'])==26
assert diff['new_ordinary']==[8544,8545,8547,8548] and not diff['new_runs']
fonts={p.relative_to(R).as_posix():{k:v for k,v in rec(p.relative_to(R)).items() if k!='path'} for p in (R/'assets/fonts').glob('*.huifont')}
assert len(fonts)==6
for path,v in fonts.items():assert sha(R/'build/runtime-preview/assets/fonts'/Path(path).name)==v['sha256']
native=rec('build/eboot.elf');assert native['sha256']=='71aa22952d2f2155c53e90023040270f9bac87e89ca19ec9b37a4639f67046af'
assert 'Native compile/link/conversion complete; existing payload untouched.' in (O/'native-build.log').read_text(encoding='utf8')
assert 'Native parser equivalence PASS: 1400 entries' in (R/'build/research/equivalence-fifth-switch5-media5-source76.log').read_text(encoding='utf16')
for name in ['shaped-runs.log','inventory-unit.log','unicode-actual-4k.log','actual-profile.log','actual-new-playlists.log']:assert 'PASS' in (O/name).read_text(encoding='utf8'),name
profilepath='build/research/story-text-profile/unillustrated-scenes-current.json';g=load(profilepath);assert g['catalog']==runtime and g['catalog_entries']==1400 and g['explicit_catalog_override'] and g['count']==383
assert len(g['scoped_composed_narrative_checks'])==39
shutil.copyfile(R/profilepath,O/'actual-profile-frozen.json')
media=[]
for item in proof['new_existing_story_images']:
 hits=[x for x in g['scoped_composed_narrative_checks'] if item['entry_id'] in [x['entry_id'],x['feature_id']] and item['paragraph'] in x['paragraphs'] and item['url']==x['image_url']]
 assert len(hits)==1,item
 media.append(dict(item,actual_card=hits[0]['card']))
article_records=[];screens=[]
for item in proof['new_articles']:
 eid=item['entry_id'];cards=[x for x in g['scoped_composed_narrative_checks'] if x['entry_id']==eid and x['feature']<0];assert len(cards)==5 and all(c['image_index']>=0 for c in cards)
 assert [p for c in cards for p in c['paragraphs']]==list(range(5))
 log=(O/('article-'+eid+'-actual-4k.log')).read_text(encoding='utf8');actual=[line for line in log.splitlines() if 'story-'+eid+'-' in line and '3840x2160 GL=0x0' in line];assert len(actual)>=7,(eid,actual)
 article_records.append({'entry_id':eid,'body_paragraphs':5,'actual_narrative_cards':cards,'screenshots_GL0':len(actual),'source_order_full_layout_and_endpoint':True})
 screens+=list((R/'build/previews').glob('story-'+eid+'-*-4k.png'))
music=[];musiclog=(O/'actual-new-playlists.log').read_text(encoding='utf8')
for item in proof['new_music_rooms']:
 eid=item['entry_id'];x=ai[eid]['soundtrack']['tracks'];y=bi[eid]['soundtrack']['tracks'];assert len(x)==len(y)==item['recordings']
 for u,v in zip(x,y):
  for key in ['youtube_id','url','title','creator','source_page','start_seconds','end_seconds']:assert u.get(key)==v.get(key),(eid,key)
 count=len(y)
 for index in [0,count//2,count-1]:assert 'PASS scoped playlist '+eid+' '+str(index+1)+'/'+str(count)+':' in musiclog
 music.append({'entry_id':eid,'recordings':count,'every_runtime_identity_credit_source_bound_matches':True,'all_title_creator_glyphs_checked':True,'first_middle_final4K_GL0':True,'physical_playback_verified':False})
 screens+=list((R/'build/previews').glob('playlist-scoped-'+eid+'-*-4k.png'))
rooms=[room for e in b['entries'] for room in ([e['soundtrack']] if e.get('soundtrack') else [])+e.get('soundtrack_rooms',[])];games=sum(e.get('kind')=='game' and bool(e.get('soundtrack',{}).get('tracks') or any(x.get('tracks') for x in e.get('soundtrack_rooms',[]))) for e in b['entries'])
proj=runpy.run_path(str(R/'tools/runtime-catalog.py'));project=proj['project'];original=project.__globals__['compact_ignored_metadata'];project.__globals__['compact_ignored_metadata']=lambda x:x
before=proj['encoded'](project(a,sha(R/master)));project.__globals__['compact_ignored_metadata']=original
atlas=(R/'assets/fonts/cjk-subset.huifont').read_bytes();dimensions=struct.unpack_from('<HH',atlas,8)
assert dimensions==(2048,2164)
globalpath=R/'build/research/offline-script-shaping/verification.json';old=load(globalpath);shutil.copyfile(globalpath,O/'inherited-full-font-verification.json');fresh=dict(old)
fresh.update(status='fresh_four_required_glyph_bake_scoped_current_ui_and_native_compatibility_PASS',recorded_utc=datetime.now(timezone.utc).isoformat(),actual_source_sha256=audit['input_source_sha256'],coherent_catalogues={p:{k:v for k,v in rec(p).items() if k!='path'} for p in [master,runtime]},ordinary_display_codepoints=927,visible_ordinary_codepoints=len(audit['visible_ordinary_codepoints']),current_complete_script_phrases=9,genuine_harfbuzz_word_boundary_runs=26,files=fonts,scoped_verification='build/research/fifth-source76-font-scoped/verification.json',checks_rerun_this_group=['fresh4RomanNumeralbake','current927ordinary4facesboth4Kthemes','26shapedrun104facecases','39actualscopedcompleteprose/sourceorder/scrollendpoint','5newillustratedarticlesactual4K','3newroomsalltitle/creatorglyphs+first/middle/final4K','nativecompilelinkno-op'],inherited_regressions_not_rerun='Earlier full product-regression receipt is preserved separately; unchanged MK348, aliases/display/study/media tests were not rerun this group.',physical_ps5_tested=False)
globalpath.write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report={'status':'PASS_FIFTH_COHERENT_FONTS_NATIVE_COMPATIBILITY_SCOPED_ACTUAL_UI_NOT_CONSOLE','recorded_utc':datetime.now(timezone.utc).isoformat(),'catalogues':[rec(master),rec(runtime)],'authoring_proof':rec(proofpath),'backup_manifest':rec('build/research/native-fourth-source73-recoverable/manifest.json'),'all84backupfiles_sha_reverified':True,'native':native,'fonts':fonts,'font_new_points':diff['new_ordinary'],'ordinary_codepoints':927,'complex_phrases':9,'shaped_word_runs':26,'fallback_dimensions':dimensions,'fallback_R8_bytes':dimensions[0]*dimensions[1],'host_gl_max_texture_size':16384,'physical_ps5_font_limit_measured':False,'native_equivalence':rec('build/research/equivalence-fifth-switch5-media5-source76.log'),'runtime_uncompacted_projection_bytes':len(before),'runtime_packaged_bytes':(R/runtime).stat().st_size,'ignored_metadata_bytes_saved':len(before)-(R/runtime).stat().st_size,'new_articles':article_records,'new_media5_actual':media,'new_music':music,'all_music_rooms':len(rooms),'unique_game_entries_with_music':games,'all_music_tracks':sum(len(room.get('tracks',[])) for room in rooms),'actual_profile':rec('build/research/fifth-source76-font-scoped/actual-profile-frozen.json'),'actual_narrative_gaps':383,'main_body_gaps':sum(x['feature']<0 for x in g['entries']),'feature_gaps':sum(x['feature']>=0 for x in g['entries']),'screenshots':[rec(p.relative_to(R)) for p in screens],'scope_limits':['No physical PS5 playback/performance/FPS validation.','No new FTP or deployment.','383 genuine unillustrated narrative scenes remain; this is a coherent checkpoint, not a completed-app claim.','Separate235-track Tekken7/MKX/FM6 research remains outside this source76 package.']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'receipt_sha256':sha(O/'verification.json'),'rooms':len(rooms),'unique_games':games,'tracks':sum(len(room.get('tracks',[])) for room in rooms),'gap':383,'saved_json_bytes':report['ignored_metadata_bytes_saved'],'screenshots':len(screens)}))
