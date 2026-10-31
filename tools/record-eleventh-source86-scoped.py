"""Bind the eleventh scoped UI/font checks to the frozen input. No deployment."""
import datetime, hashlib, json, runpy, shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'build/research/eleventh-source86-scoped'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n): return json.loads((R/n).read_text(encoding='utf8'))
def rec(n):
 p=R/n; return dict(path=str(n).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p))
def log(n):
 b=(R/n).read_bytes(); return b.decode('utf16' if b.startswith(b'\xff\xfe') else 'utf8')
master='content/catalog.json'; runtime='build/runtime-preview/content/catalog.json'
assert sha(R/master)=='50e3d1f91119a6aa7dd62032ef8f7c7f7a42a053d67a7b05ea3e9b51bdca70ba'
assert sha(R/runtime)=='a7c071c8d89d02863fdf7798da991674995ab1f419642a3a1c28e55eeb045e9a'
proj=runpy.run_path(str(R/'tools/runtime-catalog.py'))
assert hashlib.sha256(proj['encoded'](proj['project'](load(master),sha(R/master)))).hexdigest()==sha(R/runtime)
a,b=load(master),load(runtime); ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']}
assert len(ai)==len(bi)==1400 and len(a['entry_aliases'])==23 and a['entry_aliases']==b['entry_aliases']
proofname='build/research/eleventh-clarity5-fact1-media-source86-final-proof.json';proof=load(proofname)
assert len(proof['body_records'])==206
for row in proof['body_records']+proof['separate_factual_fix_records']:
 for ix in [ai,bi]: assert hashlib.sha256(ix[row['entry_id']]['body'][row['index']].encode()).hexdigest()==row['body_sha256']
for eid in ai:
 for key in ['body','story_headings','models']: assert ai[eid].get(key,[])==bi[eid].get(key,[])
backup=R/'build/research/native-tenth-source86-recoverable';assert sha(backup/'manifest.json')=='eb93792e9194f1b0bbe143af80b50835d853e7e092112332e3e74241afeec36e'
for n,ix in [(master,ai),(runtime,bi)]:
 old=json.loads((backup/'files'/n).read_text(encoding='utf8'));oi={e['id']:e for e in old['entries']}
 assert {eid for eid in ix if ix[eid]!=oi[eid]}==set(proof['changed_owners'])
 for eid,e in ix.items():
  for key in ['soundtrack','soundtrack_rooms','date','models']: assert e.get(key)==oi[eid].get(key)
audit=load('build/research/font-coverage.json');diff=load(O.relative_to(R)/'font-inventory-revalidation.json')
assert diff['status'].startswith('PASS') and diff['font_assets']
assert audit['ordinary_glyph_status']=='pass' and len(audit['ordinary_codepoints'])==946
assert not any(audit[k] for k in ['stale_subset_inputs','complex_shaping_unresolved','static_complex_runs_unsupported'])
fonts={}
for p in (R/'assets/fonts').glob('*.huifont'):
 assert sha(p)==sha(R/'build/runtime-preview/assets/fonts'/p.name);fonts[p.relative_to(R).as_posix()]=rec(p.relative_to(R))
native=rec('build/eboot.elf');assert native['sha256']=='71fba8ccff3f25efc1ad610c28b44d459513abc20cc0482ae4c026952a6059f7'
assert sha(R/'src/museum/object_scene.cpp')=='ef7098bd072920b6df7cb8247d4425e23fa3224c701fd70956774e45d0888ea8'
assert 'Native parser equivalence PASS: 1400 entries' in log('build/research/eleventh-runtime-equivalence.log')
g=load('build/research/story-text-profile/unillustrated-scenes-current.json')
assert g['catalog']==runtime and g['explicit_catalog_override'] and g['catalog_entries']==1400
assert g['scoped_composed_narrative_checks']
shutil.copyfile(R/'build/research/story-text-profile/unillustrated-scenes-current.json',O/'actual-profile-frozen.json')
media=[]
for n in range(3):
 image=next(i for i in bi['i-am-alive']['images'] if i.get('story_paragraph')==n)
 hits=[r for r in g['scoped_composed_narrative_checks'] if r['entry_id']=='i-am-alive' and n in r['paragraphs']]
 assert len(hits)==1,(n,hits)
 if n:assert hits[0]['image_url']==image['url']
 else:assert hits[0]['image_url']=='https://i.ytimg.com/vi/n-0Md_QVqSs/maxresdefault.jpg'
 media.append(dict(owner='i-am-alive',paragraph=n,explicit_source_image=image['url'],actual_image=hits[0]['image_url'],actual_card=hits[0]['card'],actual_complete_paragraphs=hits[0]['paragraphs'],note='Existing contextual gameplay film takes p0; explicit p0 photograph remains in gallery.' if n==0 else 'Explicit paragraph image displayed.'))
slog=log(O.relative_to(R)/'actual-six-prose-three-mappings.log');assert '30actual4K captures GL0' in slog
screens=sorted((R/'build/previews').glob('eleventh-*-4k.png'));assert len(screens)==30
rootproof='build/research/playhub-semantic-coverage/wiki-clarity/root-actual206-master-runtime-proof.json';rp=load(rootproof);assert rp['cards']==206
for n in [master,runtime]:assert rp['actual_catalogues'][n]['sha256']==sha(R/n)
rooms=[];games=0
for e in b['entries']:
 effective=e.get('soundtrack_rooms') or ([e['soundtrack']] if e.get('soundtrack',{}).get('tracks') else [])
 rooms.extend(effective);games+=e.get('kind')=='game' and bool(effective)
report=dict(status='PASS_COHERENT_ELEVENTH_SCOPED_ACTUAL_UI_FONTS_NOT_CONSOLE',timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),catalogues=[rec(master),rec(runtime)],authoring_proof=rec(proofname),root_independent_206proof=rec(rootproof),root_proof_producer=rec('tools/verify-reviewed-clarity206-actual-root.py'),all206body_hashes_exact=True,only_changed_owners=proof['changed_owners'],music_dates_models_unchanged=True,native=native,native_compile_performed=False,native_source=rec('src/museum/object_scene.cpp'),font_rebake_performed=False,font_reason='Exact glyph request and complex phrases unchanged versus verified tenth fonts; provenance only revalidated.',fonts=fonts,ordinary_codepoints=946,static_complex_phrases=9,static_shaped_runs=26,general_dynamic_shaping_supported=False,fallback_atlas=dict(width=2048,height=2190,r8_texture_bytes=4485120),font_inventory_revalidation=rec(O.relative_to(R)/'font-inventory-revalidation.json'),font_revalidation_script=rec('tools/revalidate-eleventh-font-inventory.py'),font_coverage=rec('build/research/font-coverage.json'),font_revalidation_log=rec(O.relative_to(R)/'font-revalidation.log'),new_media3_actual=media,actual_profile=rec(O.relative_to(R)/'actual-profile-frozen.json'),actual_narrative_gaps=g['count'],main_body_gaps=sum(x['feature']<0 for x in g['entries']),feature_gaps=sum(x['feature']>=0 for x in g['entries']),scoped_scene_count=len(g['scoped_composed_narrative_checks']),actual_scope='Six changed paragraphs through actual right-stick scroll endpoints, plus three semantic media pairings; 30 frames across both themes, GL0.',effective_native_music_counts=dict(rooms=len(rooms),unique_game_entries=games,tracks=sum(len(r['tracks']) for r in rooms)),scoped_capture_log=rec(O.relative_to(R)/'actual-six-prose-three-mappings.log'),scoped_capture_fixture=rec('host/eleventh_scoped_checks.hpp'),host_bindings=[rec('host/behavior.hpp'),rec('host/preview.cpp')],screenshots=[rec(p.relative_to(R)) for p in screens],contacts=[rec(O.relative_to(R)/f'{t}-contact.jpg') for t in ['light','dark']],tenth_recovery_manifest=rec('build/research/native-tenth-source86-recoverable/manifest.json'),limits=['No physical PS5 FPS120, instant loading, haptic or playback claim.',str(g['count'])+' actual narrative scenes remain without images.','Native ELF and all font binaries reused without recompile or rebake.','No signing, staging, packaging or FTP performed.'])
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt_sha256=sha(O/'verification.json'),gaps=g['count'],main=report['main_body_gaps'],features=report['feature_gaps'],screenshots=len(screens),music=report['effective_native_music_counts'])))
