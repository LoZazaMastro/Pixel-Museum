"""Scoped eighth data-only validation: no native compile or font rebake."""
import json,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'build/research/eighth-sayonara3-scoped'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(n):
 p=R/n;return {'path':str(n).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
master='content/catalog.json';runtime='build/runtime-preview/content/catalog.json';proofname='build/research/eighth-sayonara3-source85-final-proof.json'
assert sha(R/master)=='14ec613b84f6a660562dabab79c2de6cb60d26936f393070bad9b20806e997e9' and sha(R/runtime)=='cad1a476770b7ae47d7c0024a185d03e4639fcab9f1ccd34c4f7b43655addb5d'
proof=load(proofname);assert len(proof['body_records'])==193
backup=R/'build/research/native-seventh-source85-recoverable';manifest=json.loads((backup/'manifest.json').read_text());assert sha(backup/'manifest.json')=='f4eeaee34587b87c54a98b2d473083bf7d16a024571ff68ff79e29e9ef3ac6f0'
target='workbook-09-19-sayonara-wild-hearts';changed={}
for name in [master,runtime]:
 new=load(name);old=json.loads((backup/'files'/name).read_text());a={e['id']:e for e in new['entries']};b={e['id']:e for e in old['entries']};assert a.keys()==b.keys() and len(a)==1400
 assert sum(a[e]==b[e] for e in a)==1399
 changes={k for k in a[target].keys()|b[target].keys() if a[target].get(k)!=b[target].get(k)};assert changes<={'body','editorial_credit','provenance','story_headings'}
 assert a[target]['body'][0]==b[target]['body'][0] and len(a[target]['body'])==4
 for item in proof['body_records']:assert hashlib.sha256(a[item['entry_id']]['body'][item['index']].encode()).hexdigest()==item['body_sha256']
 changed[name]=sorted(changes)
fonts={}
for p in (R/'assets/fonts').glob('*.huifont'):
 n=p.relative_to(R).as_posix();assert sha(p)==manifest['files'][n]['sha256'];assert sha(p)==sha(R/'build/runtime-preview/assets/fonts'/p.name);fonts[n]=rec(n)
assert sha(R/'build/eboot.elf')=='a249abfce6ad645970c59ac8931543f937f60f0bc7eaed5c0d13d54692e16bfa'
for n in ['src/museum/screen.cpp','src/ui/components/image_viewer.cpp','src/ui/components/image_viewer.hpp','src/platform/ps5/pad.cpp','src/platform/ps5/pad.hpp','src/main.cpp']:
 assert sha(R/n)==manifest['files'][n]['sha256']
diff=load(O.relative_to(R)/'inventory-diff.json');assert not any(diff[k] for k in ['new_ordinary','removed_ordinary','new_runs','removed_runs'])
audit=load('build/research/font-coverage.json');assert audit['ordinary_glyph_status']=='pass' and not audit['stale_subset_inputs'] and not audit['complex_shaping_unresolved'] and not audit['static_complex_runs_unsupported']
log=(O/'actual-three-both-themes.log').read_text();assert log.count('PASS scoped Sayonara light p')==3 and log.count('PASS scoped Sayonara dark p')==3 and 'PASS scoped Sayonara3 both themes' in log
screens=[]
for theme in ['light','dark']:
 for p in [1,2,3]:
  for end in ['start','end']:screens.append(rec('build/previews/sayonara-eight-'+theme+'-p'+str(p)+'-'+end+'-4k.png'))
report={'status':'PASS_EIGHTH_DATA_ONLY_SCOPED_THREE_CARDS_BOTH_THEMES_NOT_CONSOLE','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'catalogues':[rec(master),rec(runtime)],'proof':rec(proofname),'all193reviewed_body_hashes_exact':True,'all1399other_entries_exact_in_both_catalogues':True,'actual_changed_fields':changed,'only_three_rewritten_source_paragraphs':[1,2,3],'native':rec('build/eboot.elf'),'native_unchanged':True,'native_compile_performed':False,'font_rebake_performed':False,'binary_fonts_unchanged':fonts,'source_font_manifest_hashes_refreshed_only':True,'font_inventory_diff':rec(O.relative_to(R)/'inventory-diff.json'),'ordinary_codepoints':944,'static_complex_phrases':9,'scoped_actual_test':rec(O.relative_to(R)/'actual-three-both-themes.log'),'scoped_test_source':rec('host/sayonara_reading_checks.hpp'),'actual_checks':['All three exact full source paragraphs reach layout, no ellipsis lead.','Right-stick handle/update reaches each final complete line without R3 or changing cards.','Explicit paragraph images1..3 remain distinct and exclude cover.','Three start/end frames in each light/dark theme at3840x2160, GL0.'],'screenshots':screens,'inherited_seventh_receipt':rec('build/research/seventh-source85-font-scoped/verification.json'),'limits':['No product C++ changes, native rebuild or font rebake.','Only three changed cards rendered; unrelated unchanged catalogues/rooms were not rerun.','No physical PS5 performance/playback/haptic validation.','No FTP.']}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(sha(O/'verification.json'))
