"""Back up the eighth verified data, matching external fonts and haptic-fix ELF."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];GROUP='eighth-sayonara3-source85'
OUT=ROOT/'build/research/native-eighth-source85-recoverable'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
assert len(sys.argv)==2,'Pass the final eighth scoped verification JSON path.'
receipt=ROOT/sys.argv[1];qa=load(receipt);assert qa['status'].startswith('PASS')
for r in qa['catalogues']:assert sha(ROOT/r['path'])==r['sha256']
assert qa['catalogues'][0]['sha256']=='14ec613b84f6a660562dabab79c2de6cb60d26936f393070bad9b20806e997e9'
assert qa['catalogues'][1]['sha256']=='cad1a476770b7ae47d7c0024a185d03e4639fcab9f1ccd34c4f7b43655addb5d'
for p,r in qa['binary_fonts_unchanged'].items():assert sha(ROOT/p)==r['sha256']
assert sha(ROOT/qa['native']['path'])==qa['native']['sha256']
proof=ROOT/('build/research/'+GROUP+'-final-proof.json');assert sha(proof)=='ced2c3d41a2908228447a50d15811dd9bb174bdf0c9f3b4e51d62aff874adb0f'
rootproof=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/root-actual193-master-runtime-proof.json'
assert load(rootproof)['status']=='PASS'
inherited=qa['inherited_seventh_receipt'];assert sha(ROOT/inherited['path'])==inherited['sha256'];priorqa=load(ROOT/inherited['path'])
status=dict(status='PASS_VERIFIED_EIGHTH_NOT_COMPLETE',catalogues=qa['catalogues'],scoped_qa_path=receipt.relative_to(ROOT).as_posix(),scoped_qa_sha256=sha(receipt),editorial_proof_sha256=sha(proof),root_actual193_proof_path=rootproof.relative_to(ROOT).as_posix(),root_actual193_proof_sha256=sha(rootproof),native=qa['native'],last_full_actual_unillustrated_narrative_scenes=priorqa['actual_narrative_gaps'],last_full_actual_gap_breakdown=dict(main=priorqa['main_body_gaps'],feature=priorqa['feature_gaps']),profile_scope='Seventh full compositor profile retained; eighth validates only the three rewritten, still illustrated cards. All other1399entries exact. No new full-profile run or inferred subtraction.',incomplete_editorial_collection=True,no_ftp_performed=True)
statuspath=ROOT/('build/research/'+GROUP+'-final-status.json')
if statuspath.exists():assert load(statuspath)==status
else:statuspath.write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
if (OUT/'manifest.json').exists():
    for name,row in load(OUT/'manifest.json')['files'].items():assert sha(OUT/'files'/name)==row['sha256']
    print('Already archived',sha(OUT/'manifest.json'));raise SystemExit
previous=ROOT/'build/research/native-seventh-source85-recoverable/manifest.json'
freeze=load(ROOT/('build/research/'+GROUP+'-input-freeze.json'))
names=set(load(previous)['files'])|set(freeze['files'])
names.update(p.relative_to(ROOT).as_posix() for p in receipt.parent.glob('*.json'))
names.update(p.relative_to(ROOT).as_posix() for p in receipt.parent.glob('*.log'))
names.update(r['path'] for r in qa['screenshots'])
names.update(['host/sayonara_reading_checks.hpp','tools/record-eighth-sayonara3-scoped.py','host/behavior.hpp','host/preview.cpp'])
names.update([proof.relative_to(ROOT).as_posix(),rootproof.relative_to(ROOT).as_posix(),statuspath.relative_to(ROOT).as_posix(),'build/research/'+GROUP+'-input-freeze.json','build/research/'+GROUP+'-integrity.json','build/research/controller-feedback-coverage/photo-analog-and-focus-stop-verification.json'])
for r in load(ROOT/'build/research/controller-feedback-coverage/photo-analog-and-focus-stop-verification.json')['source_files']:
    # The two host dispatch files now include the reviewed Sayonara fixture.
    # Their earlier haptic-only bytes remain in recovery7; product C++ must match.
    if r['path'] not in ('host/behavior.hpp','host/preview.cpp'):
        assert sha(ROOT/r['path'])==r['sha256']
    names.add(r['path'])
records={}
for name in sorted(names):
    source=ROOT/name;target=OUT/'files'/name
    if name in freeze['files']:assert sha(source)==freeze['files'][name]['sha256'],name
    target.parent.mkdir(parents=True,exist_ok=True);assert OUT.resolve() in target.resolve().parents
    shutil.copy2(source,target);records[name]=dict(bytes=target.stat().st_size,sha256=sha(target));assert records[name]['sha256']==sha(source)
manifest=dict(status='PASS_RECOVERABLE_VERIFIED_EIGHTH_PAYLOAD',restore='Restore catalogue/runtime, credits, selectors, model index, external fonts and ELF together from files/. Large immutable original images/models remain at recorded paths. Exact SOURCE85/frozen joins and unchanged product haptic-fix sources are retained. Current host dispatch files include scoped Sayonara checks; the earlier haptic-only host versions remain in recovery7. Not a full checkout.',verified_master_sha256=qa['catalogues'][0]['sha256'],verified_runtime_sha256=qa['catalogues'][1]['sha256'],native_sha256=qa['native']['sha256'],scoped_verification_sha256=sha(receipt),root_actual193_proof_sha256=sha(rootproof),files=records)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
for name,row in records.items():assert sha(OUT/'files'/name)==row['sha256']
print((OUT/'manifest.json').relative_to(ROOT),sha(OUT/'manifest.json'),len(records))
