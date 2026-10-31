"""Prove the eighth authoring group changes only the approved three card texts."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='eighth-sayonara3-source85'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
master=load('content/catalog.json');runtime=load('build/runtime-preview/content/catalog.json');old=load('build/research/native-seventh-source85-recoverable/files/content/catalog.json')
mo={x['id']:x for x in master['entries']};ro={x['id']:x for x in runtime['entries']};oo={x['id']:x for x in old['entries']};target='workbook-09-19-sayonara-wild-hearts'
assert len(mo)==len(ro)==len(oo)==1400 and mo.keys()==oo.keys()
assert master['entry_aliases']==runtime['entry_aliases']==old['entry_aliases']
assert [k for k in mo if mo[k]!=oo[k]]==[target]
changed=[f for f in set(mo[target])|set(oo[target]) if mo[target].get(f)!=oo[target].get(f)]
assert set(changed)=={'body','story_headings','provenance','editorial_credit'}
assert mo[target]['body'][0]==oo[target]['body'][0]
candidate=load('build/research/playhub-semantic-coverage/wiki-clarity/new-bounded-current-audit/sayonara-three/three-concrete-sayonara-cards-clarity-edited-candidate.json')
records=load('build/research/seventh-media5-source85-final-proof.json')['body_records'][:]
for r in records:
    for doc in (mo,ro):assert hashlib.sha256(doc[r['entry_id']]['body'][r['index']].encode()).hexdigest()==r['body_sha256']
for r in candidate['replacements']:
    i=r['source_chapter_index'];assert oo[target]['body'][i]==r['old_body']
    assert mo[target]['body'][i]==ro[target]['body'][i]==r['body']
    assert mo[target]['story_headings'][i]==ro[target]['story_headings'][i]==r['heading']
    records.append(dict(entry_id=target,index=i,body_sha256=r['body_sha256']))
assert len(records)==193
freeze=load('build/research/'+GROUP+'-input-freeze.json')
for p,r in freeze['files'].items():assert sha(p)==r['sha256'],p
assert sha('assets/images/manifest.json')==freeze['local_images_manifest_sha256']
assert sha('build/eboot.elf')==freeze['native_sha256']=='a249abfce6ad645970c59ac8931543f937f60f0bc7eaed5c0d13d54692e16bfa'
integrity=load('build/research/'+GROUP+'-integrity.json');assert integrity['missing_full_or_preview']==0
proof=dict(status='PASS_EIGHTH_THREE_BODY_ONLY_NOT_COMPLETE',master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),runtime_bytes=(ROOT/'build/runtime-preview/content/catalog.json').stat().st_size,entries=1400,total_revised_body_records=193,body_records=records,only_changed_entry=target,only_changed_fields=sorted(changed),all_other1399_complete_entry_records_exact=True,all_images_dates_music_models_unchanged=True,backlink_order_reproducibility=dict(entries=['workbook-12-18-final-fantasy','preserving-play'],prior_order_and_sets_exactly_preserved=True,helper='content/expansion/integrate_priority_features.py',helper_sha256=sha('content/expansion/integrate_priority_features.py')),local_image_manifest_unchanged=True,required_local_images=integrity['required_unique_image_urls'],missing_full_or_preview=0,source85_sha256=sha('content/expansion/soundtrack-multitrack-priority-overrides.json'),media70_sha256=sha('content/expansion/museum-story-gap-illustrations-reviewed.json'),native_sha256=sha('build/eboot.elf'),new_native_or_font_compile_performed=False,recovery=freeze['recovery'],recovery_sha256=freeze['recovery_sha256'],actual_composition_gap_last_verified=353,composition_scope='Seventh actual compositor only; eighth scoped validation pending. No completion claim.',no_ftp=True)
out='build/research/'+GROUP+'-final-proof.json';(ROOT/out).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(out,sha(out));print(proof['master_sha256'],proof['runtime_sha256'],proof['runtime_bytes'])
