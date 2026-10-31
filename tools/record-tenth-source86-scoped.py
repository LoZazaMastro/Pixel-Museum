"""Bind the tenth scoped UI/font checks to the frozen input. No deployment."""
import datetime, hashlib, json, runpy, shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'build/research/tenth-source86-scoped'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n): return json.loads((R/n).read_text(encoding='utf8'))
def rec(n):
 p=R/n; return dict(path=str(n).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p))
def log(n):
 b=(R/n).read_bytes(); return b.decode('utf16' if b.startswith(b'\xff\xfe') else 'utf8')
master='content/catalog.json'; runtime='build/runtime-preview/content/catalog.json'
assert sha(R/master)=='7642dadf1c4e9a861965ac29282e594062064c9c771eb54165c0893a99b958d7'
assert sha(R/runtime)=='18ae4fb6a38dad88cd3a9a6ba50439e20fbedeec2439d336aab8229e572b72db'
proj=runpy.run_path(str(R/'tools/runtime-catalog.py'))
assert hashlib.sha256(proj['encoded'](proj['project'](load(master),sha(R/master)))).hexdigest()==sha(R/runtime)
a,b=load(master),load(runtime); ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']}
assert len(ai)==len(bi)==1400 and len(a['entry_aliases'])==23 and a['entry_aliases']==b['entry_aliases']
proofname='build/research/tenth-clarity5-media4-source86-final-proof.json';proof=load(proofname)
assert len(proof['body_records'])==201
for row in proof['body_records']:
 for ix in [ai,bi]: assert hashlib.sha256(ix[row['entry_id']]['body'][row['index']].encode()).hexdigest()==row['body_sha256']
for eid in ai:
 for key in ['body','story_headings','models']: assert ai[eid].get(key,[])==bi[eid].get(key,[])
backup=R/'build/research/native-ninth-source86-recoverable';assert sha(backup/'manifest.json')=='738ad9c93b1d6b3353b36279684c85204986beecde5b94bb1673247e58125e19'
for n,ix in [(master,ai),(runtime,bi)]:
 old=json.loads((backup/'files'/n).read_text(encoding='utf8'));oi={e['id']:e for e in old['entries']}
 assert {eid for eid in ix if ix[eid]!=oi[eid]}=={'daily-11-25','daily-12-12','roberta-williams','workbook-07-28-lua','workbook-10-22-grand-theft-auto-2','minecraft'}
 for eid,e in ix.items():
  for key in ['soundtrack','soundtrack_rooms','date','models']: assert e.get(key)==oi[eid].get(key)
audit=load('build/research/font-coverage.json');diff=load(O.relative_to(R)/'inventory-diff.json')
assert diff['new_ordinary']==[20449,22338] and not any(diff[k] for k in ['removed_ordinary','new_runs','removed_runs'])
assert audit['ordinary_glyph_status']=='pass' and len(audit['ordinary_codepoints'])==946
assert not any(audit[k] for k in ['stale_subset_inputs','complex_shaping_unresolved','static_complex_runs_unsupported'])
fonts={}
for p in (R/'assets/fonts').glob('*.huifont'):
 assert sha(p)==sha(R/'build/runtime-preview/assets/fonts'/p.name);fonts[p.relative_to(R).as_posix()]=rec(p.relative_to(R))
native=rec('build/eboot.elf');assert native['sha256']=='71fba8ccff3f25efc1ad610c28b44d459513abc20cc0482ae4c026952a6059f7'
assert sha(R/'src/museum/object_scene.cpp')=='ef7098bd072920b6df7cb8247d4425e23fa3224c701fd70956774e45d0888ea8'
assert 'Native parser equivalence PASS: 1400 entries' in log('build/research/tenth-runtime-equivalence.log')
g=load('build/research/story-text-profile/unillustrated-scenes-current.json')
assert g['catalog']==runtime and g['explicit_catalog_override'] and g['catalog_entries']==1400 and g['count']==318
assert len(g['scoped_composed_narrative_checks'])==16
shutil.copyfile(R/'build/research/story-text-profile/unillustrated-scenes-current.json',O/'actual-profile-frozen.json')
media=[]
for x in proof['new_narrative_image_records']:
 hits=[r for r in g['scoped_composed_narrative_checks'] if x['owner'] in [r['entry_id'],r.get('feature_id')] and x['paragraph'] in r['paragraphs'] and r['image_url']==x['url']]
 assert len(hits)==1,(x,hits)
 media.append(dict(x,actual_card=hits[0]['card'],actual_complete_paragraphs=hits[0]['paragraphs']))
slog=log(O.relative_to(R)/'actual-five-prose-four-media.log');assert '28actual4K captures GL0' in slog
screens=sorted((R/'build/previews').glob('tenth-*-4k.png'));assert len(screens)==28
rootproof='build/research/playhub-semantic-coverage/wiki-clarity/root-actual201-master-runtime-proof.json';rp=load(rootproof);assert rp['cards']==201
for n in [master,runtime]:assert rp['actual_catalogues'][n]['sha256']==sha(R/n)
rooms=[];games=0
for e in b['entries']:
 effective=e.get('soundtrack_rooms') or ([e['soundtrack']] if e.get('soundtrack',{}).get('tracks') else [])
 rooms.extend(effective);games+=e.get('kind')=='game' and bool(effective)
report=dict(status='PASS_COHERENT_TENTH_SCOPED_ACTUAL_UI_FONTS_NOT_CONSOLE',timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),catalogues=[rec(master),rec(runtime)],authoring_proof=rec(proofname),root_independent_201proof=rec(rootproof),root_proof_producer=rec('tools/verify-reviewed-clarity201-actual-root.py'),all201body_hashes_exact=True,only_changed_owners=proof['changed_owners'],music_dates_models_unchanged=True,native=native,native_compile_performed=False,native_source=rec('src/museum/object_scene.cpp'),font_rebake_performed=True,font_reason='Two genuinely new CJK glyphs: U+4FE1 and U+5742.',fonts=fonts,ordinary_codepoints=946,static_complex_phrases=9,static_shaped_runs=26,general_dynamic_shaping_supported=False,fallback_atlas=dict(width=2048,height=2190,r8_texture_bytes=4485120),font_inventory_diff=rec(O.relative_to(R)/'inventory-diff.json'),font_coverage=rec('build/research/font-coverage.json'),font_bake_log=rec(O.relative_to(R)/'font-bake.log'),actual_unicode4K_log=rec(O.relative_to(R)/'unicode-actual-4k.log'),new_media4_actual=media,actual_profile=rec(O.relative_to(R)/'actual-profile-frozen.json'),actual_narrative_gaps=318,main_body_gaps=sum(x['feature']<0 for x in g['entries']),feature_gaps=sum(x['feature']>=0 for x in g['entries']),scoped_scene_count=16,actual_scope='Five changed paragraphs through actual right-stick scroll endpoints, plus four new media pairings; 28 frames across both themes, GL0.',effective_native_music_counts=dict(rooms=len(rooms),unique_game_entries=games,tracks=sum(len(r['tracks']) for r in rooms)),scoped_capture_log=rec(O.relative_to(R)/'actual-five-prose-four-media.log'),scoped_capture_fixture=rec('host/tenth_scoped_checks.hpp'),scoped_test_runner=rec('tools/check-tenth-source86-scoped.sh'),host_bindings=[rec('host/behavior.hpp'),rec('host/preview.cpp')],screenshots=[rec(p.relative_to(R)) for p in screens],contacts=[rec(O.relative_to(R)/f'{t}-contact.jpg') for t in ['light','dark']],ninth_recovery_manifest=rec('build/research/native-ninth-source86-recoverable/manifest.json'),limits=['No physical PS5 FPS120, instant loading, haptic or playback claim.','318 actual narrative scenes remain without images.','Native ELF reused; external font data refreshed.','No signing, staging, packaging or FTP performed.'])
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt_sha256=sha(O/'verification.json'),gaps=318,main=report['main_body_gaps'],features=report['feature_gaps'],screenshots=len(screens),music=report['effective_native_music_counts'])))
