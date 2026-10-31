"""Bind fresh fonts and scoped fourth-group QA without claiming a console run."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json,shutil,struct
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/fourth-source73-font-scoped'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1<<20):h.update(b)
 return h.hexdigest()
def rec(path):
 p=Path(path)
 if not p.is_absolute():p=ROOT/p
 return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
master='content/catalog.json';runtime='build/runtime-preview/content/catalog.json'
assert sha(ROOT/master)=='609124314973d6aa78f89125f5d4e99c4acdcc30fa700c9c0126573e882cfc91'
assert sha(ROOT/runtime)=='95cc1374444743e49fd9726a3f16e7b44f8447c4702ac07a3b5afc16568a2ca0'
a,b=load(master),load(runtime);ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']}
assert len(ai)==len(bi)==1395 and a['entry_aliases']==b['entry_aliases'] and len(a['entry_aliases'])==23
assert sum(len(e.get('models',[])) for e in a['entries'])==30
proofpath='build/research/gba-steamdeck-vr-eve-skyrim-final5-source73-final-proof.json';proof=load(proofpath)
assert len(proof['body_records'])==186
for r in proof['body_records']:
 for index in (ai,bi):assert hashlib.sha256(index[r['entry_id']]['body'][r['index']].encode('utf8')).hexdigest()==r['body_sha256']
for id,e in ai.items():
 assert e.get('body',[])==bi[id].get('body',[]) and e.get('story_headings',[])==bi[id].get('story_headings',[])
 assert [(f['id'],f['body'],f['story_headings']) for f in e.get('editorial_features',[])]==[(f['id'],f['body'],f['story_headings']) for f in bi[id].get('editorial_features',[])]
recovery=ROOT/'build/research/native-sano3-media15-recoverable'
assert sha(recovery/'manifest.json')=='a138ea5c99b1687aefbedb1907b9aa1b13e3fc6f100e3ae8e1896041b983abbc'
backup=json.loads((recovery/'manifest.json').read_text(encoding='utf8'))
for path,r in backup['files'].items():assert sha(recovery/'files'/path)==r['sha256']
assert len(backup['files'])==75
audit=load('build/research/font-coverage.json');runs=load('build/research/offline-script-shaping/script-runs.json')
assert audit['ordinary_glyph_status']=='pass' and not audit['stale_subset_inputs']
assert not audit['complex_shaping_unresolved'] and not audit['static_complex_runs_unsupported']
assert len(audit['ordinary_codepoints'])==923 and len(audit['static_complex_runs_required'])==9 and len(runs['runs'])==26
fontfiles={p.relative_to(ROOT).as_posix():{k:v for k,v in rec(p).items() if k!='path'} for p in (ROOT/'assets/fonts').glob('*.huifont')}
assert len(fontfiles)==6
for path,v in fontfiles.items():assert sha(ROOT/'build/runtime-preview/assets/fonts'/Path(path).name)==v['sha256']
native=rec('build/eboot.elf');assert native['sha256']=='71aa22952d2f2155c53e90023040270f9bac87e89ca19ec9b37a4639f67046af'
assert 'Native compile/link/conversion complete; existing payload untouched.' in (OUT/'native-build.log').read_text(encoding='utf8')
for name in ['shaped-runs.log','inventory-unit.log','unicode-actual-4k.log','actual-profile.log','actual-new-playlists.log']:
 assert 'PASS' in (OUT/name).read_text(encoding='utf8')
profilepath=ROOT/'build/research/story-text-profile/unillustrated-scenes-current.json';g=json.loads(profilepath.read_text(encoding='utf8'))
assert g['catalog']==runtime and g['catalog_entries']==1395 and g['explicit_catalog_override'] and g['count']==389
assert len(g['scoped_composed_narrative_checks'])==29
shutil.copyfile(profilepath,OUT/'actual-profile-frozen.json')
mapping=[];missing=[]
for r in proof['added_image_records']:
 hits=[x for x in g['scoped_composed_narrative_checks'] if r['owner'] in [x['entry_id'],x['feature_id']] and r['url']==x['image_url'] and r['paragraph'] in x['paragraphs']]
 row=dict(r,actual_narrative_cards=[{'entry_id':x['entry_id'],'card':x['card'],'paragraphs':x['paragraphs']} for x in hits])
 (mapping if hits else missing).append(row)
assert len(mapping)==22 and len(missing)==1 and missing[0]['owner']=='workbook-03-21-game-boy-advance' and missing[0]['paragraph']==0
gba=bi['workbook-03-21-game-boy-advance'];assert not gba.get('models')
assert any(v['youtube_id']=='eaIGRNQC1T4' for v in gba.get('videos',[]))
gbalog=(OUT/'gba-actual-4k.log').read_text(encoding='utf8')
assert '5 paragraphs, 4 narrative photographs, 7 cards' in gbalog
assert sum(f'story-workbook-03-21-game-boy-advance-{i}-4k.png 3840x2160 GL=0x0' in gbalog for i in range(7))==7
music=[]
for id,candidate,count in [('workbook-03-12-yakuza-0','build/research/soundtrack-broad/yakuza-zero-public-collection/yakuza-zero-92-public-passages-final-vocals-candidate.json',92),('wikipedia-52874820','build/research/soundtrack-broad/splatoon-original-2015/forty-eight-original-wiiu-publications-candidate.json',48)]:
 source=load(candidate)['entries'][0]['tracks'];actual=bi[id]['soundtrack']['tracks']
 assert len(source)==len(actual)==count
 for x,y in zip(source,actual):
  for k in ['youtube_id','title','creator','source_page','start_seconds','end_seconds']:assert x.get(k)==y.get(k)
 log=(OUT/'actual-new-playlists.log').read_text(encoding='utf8')
 assert all(f'PASS scoped playlist {id} {i+1}/{count}:' in log for i in [0,count//2,count-1])
 music.append({'entry_id':id,'tracks':count,'all_parsed_identity_and_bounds_preserved':True,'source':rec(candidate),'first_middle_final_4K_GL0':True,'physical_playback_verified':False})
main=sum(r['feature']<0 for r in g['entries']);feature=g['count']-main
rooms=[r for e in b['entries'] for r in ([e['soundtrack']] if e.get('soundtrack') else [])+e.get('soundtrack_rooms',[])]
game_count=sum(e.get('kind')=='game' and bool(e.get('soundtrack',{}).get('tracks') or any(r.get('tracks') for r in e.get('soundtrack_rooms',[]))) for e in b['entries'])
atlas=(ROOT/'assets/fonts/cjk-subset.huifont').read_bytes();width,height=struct.unpack_from('<HH',atlas,8)
assert (width,height)==(2048,2137)
screens=list((ROOT/'build/previews').glob('playlist-scoped-*-4k.png'))
screens += [ROOT/f'build/previews/story-workbook-03-21-game-boy-advance-{i}-4k.png' for i in range(7)]
screens += [ROOT/'build/previews'/name for name in ['unicode-fonts-dark-4k.png','unicode-fonts-light-4k.png','unicode-atlas-extended-dark-4k.png','unicode-atlas-extended-light-4k.png','script-runs-runtime-dark-4k.png','script-runs-runtime-light-4k.png','unicode-iraq-original-story-4k.png']]
globalpath=ROOT/'build/research/offline-script-shaping/verification.json'
old=load(globalpath)
shutil.copyfile(globalpath,OUT/'inherited-full-font-verification.json')
fresh=copy.deepcopy(old)
fresh.update(status='fresh_font_bake_host_GL_and_native_compile_SCOPED_PASS',recorded_utc=datetime.now(timezone.utc).isoformat(),
 actual_source_sha256=audit['input_source_sha256'],coherent_catalogues={p:{k:v for k,v in rec(p).items() if k!='path'} for p in [master,runtime]},
 ordinary_display_codepoints=923,visible_ordinary_codepoints=len(audit['visible_ordinary_codepoints']),current_complete_script_phrases=9,genuine_harfbuzz_word_boundary_runs=26,
 logs={p.name:p.relative_to(ROOT).as_posix() for p in OUT.glob('*.log')},
 inherited_full_regression_receipt=rec(OUT/'inherited-full-font-verification.json'),
 checks_rerun_this_group=['fresh font bake/source fingerprint audit','104shapedrun/face cases','display inventory unit','923actualordinary glyph geometries/fourfaces/both4Kthemes and lower-edge pixel checks','29actual composed narrative cards/source/order/scroll','92and48track first/middle/final listening room4K','GBAphoto-only7card4K','native compile/link no-op compatibleexistingELF'],
 unchanged_checks_not_repeated=['MK348fullCredits','alias/display lifecycle','unchanged model pixel regression'])
fresh['fallback_atlas']=dict(old['fallback_atlas'],width=width,height=height,r8_texel_bytes=width*height)
for path in list(fresh['files']):
 if (ROOT/path).is_file():fresh['files'][path]={k:v for k,v in rec(path).items() if k!='path'}
fresh['files'].update(fontfiles)
globalpath.write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report={
 'status':'PASS_FROZEN_FOURTH_SOURCE73_FRESH_FONTS_SCOPED_NATIVE_QA','master':rec(master),'runtime':rec(runtime),
 'entries':1395,'aliases':23,'models':30,'actual_body_records_verified':186,'source_music_records':73,
 'coherent_editorial_proof':rec(proofpath),'root_actual186_proof':rec('build/research/playhub-semantic-coverage/wiki-clarity/root-actual186-master-runtime-proof.json'),
 'font_verification':rec(globalpath),'font_assets':fontfiles,'new_ordinary_codepoints':46,'ordinary_codepoints':923,'visible_ordinary_codepoints':len(audit['visible_ordinary_codepoints']),
 'static_complex_phrases':9,'whole_word_runs':26,'fallback_atlas':{'width':width,'height':height,'R8_bytes':width*height,'host_GL_MAX_TEXTURE_SIZE':16384,'physical_PS5_limit_measured':False},
 'native':native,'native_check_ran':True,'native_ELF_bytes_unchanged':True,'new_fonts_are_external_assets':True,
 'actual_profile':dict(rec(OUT/'actual-profile-frozen.json'),gaps=389,main_body=main,features=feature,scoped_narrative_cards=29),
 'new_image_mapping':{'narrative_records_matched':22,'total_new_or_upgraded_records':23,'matches':mapping,'gallery_only':missing,
  'qualification':'GBAparagraph0remains the reviewed historical film with its poster. The new Nintendo components manual is a separate image-only gallery card5, visibly checked. No renderer change or forced duplicate illustration.'},
 'GBA':{'photo_only':True,'models_attached':0,'source_paragraphs':5,'narrative_photos':4,'historical_film':1,'total_cards':7,'all4K_GL0':True},
 'new_music':music,'music_counts':{'rooms':len(rooms),'distinct_games':game_count,'tracks':sum(len(r.get('tracks',[])) for r in rooms)},
 'screenshots':[rec(p) for p in screens],'visual_review':['Unicode lower atlas dark4K','Yakuza final92/92actual4K','Splatoon final48/48actual4K','GBA4player source diagram card2','GBAcomponents manual gallery card5'],
 'host_harness_fixes':['Scoped room static captures settle the previous-entry dissolve before asserting the new visual, preventing staleCeleste snapshots.','Illustrated story source coverage counts film paragraphs with their real posters, while keeping narrative-photo counts distinct.'],
 'logs':{p.name:rec(p) for p in OUT.glob('*.log')},'previous_recovery':dict(rec(recovery/'manifest.json'),verified_original_files=75),
 'inherited_full_tests_not_redundantly_rerun':rec(OUT/'inherited-full-font-verification.json'),
 'product_CPP_changed':False,'physical_PS5_test_or_transfer':False,
 'limits':['Fresh native check is compile/link compatibility only; no new physical PS5 playback/frame-rate/OOM claim.','Game and room counts differ: separate rooms are not extra games.','Scope passes140new musical records metadata/bounds/UI; public sources can still change independently.','General dynamic complex-script shaping/bidi is not claimed beyond the9packaged static phrases and26whole-word runs.']}
target=OUT/'verification.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(target.relative_to(ROOT),sha(target));print('profile',main,feature,'music',len(rooms),game_count)
