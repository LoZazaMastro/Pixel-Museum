"""Bind seventh current catalogues, fonts and aptic native build to scoped actual UI."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,struct
R=Path(__file__).resolve().parents[1];O=R/'build/research/seventh-source85-font-scoped'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(n):
 p=R/n;return {'path':str(n).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
def log(n):
 b=(R/n).read_bytes();return b.decode('utf16' if b.startswith(b'\xff\xfe') else 'utf8')
master='content/catalog.json';runtime='build/runtime-preview/content/catalog.json'
assert sha(R/master)=='a54d83ad2d9b49dd16cee5160bc23b2215ee80d96a25372d0192c1ad27106d83'
assert sha(R/runtime)=='889799b37c1eea2c79f67cef7390d24a82d3aabf8150d405ea0900d747ed121a'
a,b=load(master),load(runtime);ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']}
assert len(ai)==len(bi)==1400 and a['entry_aliases']==b['entry_aliases'] and len(a['entry_aliases'])==23
proofpath='build/research/seventh-media5-source85-final-proof.json';proof=load(proofpath);assert len(proof['body_records'])==190
for item in proof['body_records']:
 for idx in [ai,bi]:assert hashlib.sha256(idx[item['entry_id']]['body'][item['index']].encode()).hexdigest()==item['body_sha256']
for eid,e in ai.items():
 assert e['body']==bi[eid]['body'] and e.get('story_headings',[])==bi[eid].get('story_headings',[])
 assert [(f['id'],f['body'],f.get('story_headings',[])) for f in e.get('editorial_features',[])]==[(f['id'],f['body'],f.get('story_headings',[])) for f in bi[eid].get('editorial_features',[])]
 assert e.get('models',[])==bi[eid].get('models',[])
assert sum(len(e.get('models',[])) for e in a['entries'])==30
backup=R/'build/research/native-sixth-source81-recoverable';assert sha(backup/'manifest.json')=='1ee4481281cdc6e1943ab3ed549745e6037eb6cb62bbd5f73fb82dfb0a205558'
back=json.loads((backup/'manifest.json').read_text(encoding='utf8'));assert len(back['files'])==163
for path,item in back['files'].items():assert sha(backup/'files'/path)==item['sha256']
audit=load('build/research/font-coverage.json');runs=load('build/research/offline-script-shaping/script-runs.json');diff=load(O.relative_to(R)/'inventory-diff.json')
assert audit['ordinary_glyph_status']=='pass' and not audit['stale_subset_inputs'] and not audit['complex_shaping_unresolved'] and not audit['static_complex_runs_unsupported']
assert len(audit['ordinary_codepoints'])==944 and len(audit['static_complex_runs_required'])==9 and len(runs['runs'])==26
assert diff['new_ordinary']==[0x2b50] and not diff['removed_ordinary'] and not diff['new_runs']
fonts={p.relative_to(R).as_posix():{k:v for k,v in rec(p.relative_to(R)).items() if k!='path'} for p in (R/'assets/fonts').glob('*.huifont')};assert len(fonts)==6
for path,v in fonts.items():assert sha(R/'build/runtime-preview/assets/fonts'/Path(path).name)==v['sha256']
native=rec('build/eboot.elf');assert native['sha256']=='a249abfce6ad645970c59ac8931543f937f60f0bc7eaed5c0d13d54692e16bfa'
assert 'Native compile/link/conversion complete; existing payload untouched.' in log(O.relative_to(R)/'native-build.log')
assert 'Native parser equivalence PASS: 1400 entries' in log('build/research/equivalence-seventh-media5-source85.log')
for name in ['unicode-actual-4k.log','actual-profile.log','actual-new-playlists.log']:assert 'PASS' in log(O.relative_to(R)/name)
g=load('build/research/story-text-profile/unillustrated-scenes-current.json');assert g['catalog']==runtime and g['catalog_entries']==1400 and g['explicit_catalog_override']
assert g['count']==353 and len(g['scoped_composed_narrative_checks'])==7
shutil.copyfile(R/'build/research/story-text-profile/unillustrated-scenes-current.json',O/'actual-profile-frozen.json');media=[]
for item in proof['new_narrative_image_records']:
 hits=[x for x in g['scoped_composed_narrative_checks'] if item['owner'] in [x['entry_id'],x['feature_id']] and item['paragraph'] in x['paragraphs'] and item['url']==x['image_url']];assert len(hits)==1,item
 media.append(dict(item,actual_card=hits[0]['card'],actual_paragraphs=hits[0]['paragraphs']))
assert len(media)==5
music=[];mlog=log(O.relative_to(R)/'actual-new-playlists.log');screens=[]
for item in proof['new_music_rooms']:
 eid=item['entry_id'];x=ai[eid]['soundtrack']['tracks'];y=bi[eid]['soundtrack']['tracks'];assert len(x)==len(y)==item['recordings']
 for u,v in zip(x,y):
  for key in ['youtube_id','url','title','creator','source_page','start_seconds','end_seconds']:assert u.get(key)==v.get(key),(eid,key)
 count=len(y)
 for index in [0,count//2,count-1]:assert 'PASS scoped playlist '+eid+' '+str(index+1)+'/'+str(count)+':' in mlog
 music.append({'entry_id':eid,'recordings':count,'every_runtime_identity_credit_source_bound_matches':True,'all_title_creator_glyphs_checked':True,'first_middle_final4K_GL0':True,'physical_playback_verified':False});screens+=list((R/'build/previews').glob('playlist-scoped-'+eid+'-*-4k.png'))
assert sum(x['recordings'] for x in music)==295
for name,eid in [('atari','workbook-06-27-atari'),('advance-wars','wikipedia-68026802')]:
 text=log(O.relative_to(R)/(name+'-actual-4k.log'));assert 'GL=0x0' in text
 screens+=list((R/'build/previews').glob('story-'+eid+'-*-4k.png'))
assert log(O.relative_to(R)/'wii-feature-actual-4k.log').count('3840x2160 GL=0x0')==4
screens+=list((R/'build/previews').glob('feature-wii-*-4k.png'))
rooms=[room for e in b['entries'] for room in ([e['soundtrack']] if e.get('soundtrack') else [])+e.get('soundtrack_rooms',[])];games=sum(e.get('kind')=='game' and bool(e.get('soundtrack',{}).get('tracks') or any(x.get('tracks') for x in e.get('soundtrack_rooms',[]))) for e in b['entries'])
atlas=(R/'assets/fonts/cjk-subset.huifont').read_bytes();dims=struct.unpack_from('<HH',atlas,8);assert dims==(2048,2196)
aptic=load('build/research/controller-feedback-coverage/photo-analog-and-focus-stop-verification.json')
for row in aptic['source_files']:assert sha(R/row['path'])==row['sha256'],row['path']
report={'status':'PASS_SEVENTH_COHERENT_FONTS_NATIVE_SCOPED_ACTUAL_UI_APTIC_HOST_NOT_CONSOLE','recorded_utc':datetime.now(timezone.utc).isoformat(),'catalogues':[rec(master),rec(runtime)],'authoring_proof':rec(proofpath),'sixth_backup_manifest':rec('build/research/native-sixth-source81-recoverable/manifest.json'),'all163backupfiles_sha_reverified':True,'native':native,'fonts':fonts,'new_glyphs':diff['new_ordinary'],'ordinary_codepoints':944,'visible_ordinary_codepoints':len(audit['visible_ordinary_codepoints']),'static_complex_phrases':9,'shaped_word_runs':26,'fallback_dimensions':dims,'fallback_R8_bytes':dims[0]*dims[1],'native_equivalence':rec('build/research/equivalence-seventh-media5-source85.log'),'all190_reviewed_bodies_sha_exact':True,'new_media5_actual':media,'new_music':music,'all_music_rooms':len(rooms),'unique_game_entries_with_music':games,'all_music_tracks':sum(len(room.get('tracks',[])) for room in rooms),'actual_profile':rec('build/research/seventh-source85-font-scoped/actual-profile-frozen.json'),'actual_narrative_gaps':g['count'],'main_body_gaps':sum(x['feature']<0 for x in g['entries']),'feature_gaps':sum(x['feature']>=0 for x in g['entries']),'scoped_scenes':len(g['scoped_composed_narrative_checks']),'scoped_source_paragraphs':sum(len(x['paragraphs']) for x in g['scoped_composed_narrative_checks']),'screenshots':[rec(p.relative_to(R)) for p in screens],'aptic_host_receipt':rec('build/research/controller-feedback-coverage/photo-analog-and-focus-stop-verification.json'),'scope_limits':['No physical PS5 playback/performance/FPS/haptic validation.','No FTP or deployment.','353 actual unillustrated narrative scenes remain.','Source85 contains qualified public partial collections; room count is distinct from unique game count.','26 genuine shaped runs reused unchanged; full shaped-run regression was not repeated.']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
globalpath=R/'build/research/offline-script-shaping/verification.json';old=json.loads(globalpath.read_text(encoding='utf8'));shutil.copyfile(globalpath,O/'inherited-sixth-font-verification.json');fresh=dict(old);fresh.update(status='fresh1glyph_scoped_seventh_current_ui_and_native_PASS',recorded_utc=report['recorded_utc'],actual_source_sha256=audit['input_source_sha256'],coherent_catalogues={p:{k:v for k,v in rec(p).items() if k!='path'} for p in [master,runtime]},ordinary_display_codepoints=944,visible_ordinary_codepoints=len(audit['visible_ordinary_codepoints']),files=fonts,scoped_verification='build/research/seventh-source85-font-scoped/verification.json',checks_rerun_this_group=['freshstar1glyphbake','944ordinary4facesboth4Kthemes','7actualscopedscenescompleteparagraphscroll','newmedia5actualmapping4K','4newrooms295titlescredits+firstmiddlefinal4K','actualphoto30/60/120Hzfeedback','actualScreenfocus21','pad-driverandcontroller-output','nativecompilelink'],physical_ps5_tested=False);globalpath.write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'receipt_sha256':sha(O/'verification.json'),'native':native['sha256'],'rooms':len(rooms),'unique_games':games,'tracks':sum(len(room.get('tracks',[])) for room in rooms),'gaps':g['count'],'screenshots':len(screens)}))
