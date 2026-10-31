import json,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'build/research/twelfth-source86-scoped'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((R/n).read_text(encoding='utf8'))
def rec(n):
 p=R/n;return dict(path=str(n).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p))
proofname='build/research/twelfth-two-bindings-one-release-sentence-final-proof.json';proof=load(proofname)
for row in proof['catalogues']:assert sha(R/row['path'])==row['sha256']
a=load('content/catalog.json');b=load('build/runtime-preview/content/catalog.json');ai={e['id']:e for e in a['entries']};bi={e['id']:e for e in b['entries']}
assert len(ai)==len(bi)==1400 and len(a['entry_aliases'])==23 and a['entry_aliases']==b['entry_aliases']
backup=R/'build/research/native-eleventh-source86-recoverable/files'
for n,ix in [('content/catalog.json',ai),('build/runtime-preview/content/catalog.json',bi)]:
 old={e['id']:e for e in json.loads((backup/n).read_text(encoding='utf8'))['entries']};assert {eid for eid in ix if ix[eid]!=old[eid]}=={'9-nine-episode-2','workbook-10-09-dishonored'}
 for eid in ix:
  for key in ['year','date','models','soundtrack','soundtrack_rooms']:assert ix[eid].get(key)==old[eid].get(key)
 ep=ix['9-nine-episode-2'];assert ep['body']==old[ep['id']]['body'] and ep['images'][1]['story_paragraph']==0 and ep['images'][2]['story_paragraph']==2
 assert not any(i.get('story_paragraph')==1 for i in ep['images'])
 di=ix['workbook-10-09-dishonored'];assert di['body'][1:]==old[di['id']]['body'][1:] and di['body'][0].startswith('Dishonored was released on October 9, 2012.')
for row in proof['body_records']:
 for ix in [ai,bi]:assert hashlib.sha256(ix[row['entry_id']]['body'][row['index']].encode()).hexdigest()==row['body_sha256']
assert len(proof['body_records'])==206
qa11=load('build/research/eleventh-source86-scoped/verification.json');fonts={}
for name,row in qa11['fonts'].items():assert sha(R/name)==row['sha256'];fonts[name]=rec(name)
assert sha(R/'build/eboot.elf')==qa11['native']['sha256']
audit=load('build/research/font-coverage.json');assert audit['ordinary_glyph_status']=='pass' and not audit['stale_subset_inputs'] and not audit['complex_shaping_unresolved'] and len(audit['ordinary_codepoints'])==946
logname='build/research/twelfth-source86-scoped/actual-two-bindings-one-prose.log';log=(R/logname).read_text(encoding='utf8');assert '8actual4K captures GL0' in log and log.count('p1 no direct image binding')==2
screens=sorted((R/'build/previews').glob('twelfth-*-4k.png'));assert len(screens)==8
report=dict(status='PASS_TWELFTH_SCOPED_ACTUAL_COMPOSER_AND_PROSE_NO_NATIVE_BUILD',timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),catalogues=proof['catalogues'],proof=rec(proofname),all206_previous_clarity_body_hashes_exact=True,only_two_entries_changed=True,native=rec('build/eboot.elf'),fonts=fonts,font_rebake_performed=False,native_compile_performed=False,font_inventory_revalidation=rec('build/research/twelfth-source86-scoped/font-inventory-revalidation.json'),font_revalidation_log=rec('build/research/twelfth-source86-scoped/font-revalidation.log'),font_revalidation_script=rec('tools/revalidate-eleventh-font-inventory.py'),episode2_actual=dict(card0=dict(paragraphs=[0,1],image_index=1,direct_image_binding_paragraph=0),card1=dict(paragraphs=[2],image_index=2,direct_image_binding_paragraph=2),paragraph1_own_image_binding=False,limits='p1 continues on the p0 scene; this character still does not demonstrate the shrine/town events. No separate empty card or whole-article illustration claim.'),dishonored=dict(paragraph=0,first_sentence='Dishonored was released on October 9, 2012.',actual_rightstick_final_line_reached_without_R3=True,other7body_paragraphs_unchanged=True),actual_capture_log=rec(logname),actual_capture_fixture=rec('host/twelfth_scoped_checks.hpp'),host_bindings=[rec('host/behavior.hpp'),rec('host/preview.cpp')],screenshots=[rec(p.relative_to(R)) for p in screens],contact=rec('build/research/twelfth-source86-scoped/contact.jpg'),last_full_actual_profile=dict(checkpoint=11,gaps=318,main=178,feature=140,path='build/research/eleventh-source86-scoped/actual-profile-frozen.json'),new_global_profile_run=False,no_staging=True,no_FTP=True,no_shutdown=True,limits=['Eight real4Kframes across boththemes, GL0; scoped actual compositor checks only.','No inference of new global gapcount or complete coverage.','No physical console/instantloading/120FPS claim.'])
p=O/'verification.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(sha(p))
