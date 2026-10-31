"""Back up the seventh verified data, matching external fonts and haptic-fix ELF."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];GROUP='seventh-media5-source85'
OUT=ROOT/'build/research/native-seventh-source85-recoverable'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
assert len(sys.argv)==2,'Pass the final seventh scoped verification JSON path.'
receipt=ROOT/sys.argv[1];qa=load(receipt);assert qa['status'].startswith('PASS')
for r in qa['catalogues']:assert sha(ROOT/r['path'])==r['sha256']
assert qa['catalogues'][0]['sha256']=='a54d83ad2d9b49dd16cee5160bc23b2215ee80d96a25372d0192c1ad27106d83'
assert qa['catalogues'][1]['sha256']=='889799b37c1eea2c79f67cef7390d24a82d3aabf8150d405ea0900d747ed121a'
for p,r in qa['fonts'].items():assert sha(ROOT/p)==r['sha256']
assert sha(ROOT/qa['native']['path'])==qa['native']['sha256']
proof=ROOT/('build/research/'+GROUP+'-final-proof.json');assert sha(proof)=='b696593957977dfaddd5764a36d65e997feb0bdb4012dd29ae7bb1bcb357f881'
rootproof=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/root-actual190-seventh-master-runtime-proof.json'
assert load(rootproof)['status']=='PASS'
status=dict(status='PASS_VERIFIED_SEVENTH_NOT_COMPLETE',catalogues=qa['catalogues'],scoped_qa_path=receipt.relative_to(ROOT).as_posix(),scoped_qa_sha256=sha(receipt),editorial_proof_sha256=sha(proof),root_actual190_proof_path=rootproof.relative_to(ROOT).as_posix(),root_actual190_proof_sha256=sha(rootproof),native=qa['native'],actual_unillustrated_narrative_scenes=qa['actual_narrative_gaps'],actual_gap_breakdown=dict(main=qa['main_body_gaps'],feature=qa['feature_gaps']),incomplete_editorial_collection=True,no_ftp_performed=True)
statuspath=ROOT/('build/research/'+GROUP+'-final-status.json')
if statuspath.exists():assert load(statuspath)==status
else:statuspath.write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
if (OUT/'manifest.json').exists():
    for name,row in load(OUT/'manifest.json')['files'].items():assert sha(OUT/'files'/name)==row['sha256']
    print('Already archived',sha(OUT/'manifest.json'));raise SystemExit
previous=ROOT/'build/research/native-sixth-source81-recoverable/manifest.json'
freeze=load(ROOT/('build/research/'+GROUP+'-input-freeze.json'))
names=set(load(previous)['files'])|set(freeze['files'])
names.update(p.relative_to(ROOT).as_posix() for p in receipt.parent.glob('*.json'))
names.update([proof.relative_to(ROOT).as_posix(),rootproof.relative_to(ROOT).as_posix(),statuspath.relative_to(ROOT).as_posix(),'build/research/'+GROUP+'-input-freeze.json','build/research/'+GROUP+'-integrity.json','build/research/controller-feedback-coverage/photo-analog-and-focus-stop-verification.json'])
for r in load(ROOT/'build/research/controller-feedback-coverage/photo-analog-and-focus-stop-verification.json')['source_files']:
    assert sha(ROOT/r['path'])==r['sha256'];names.add(r['path'])
records={}
for name in sorted(names):
    source=ROOT/name;target=OUT/'files'/name
    if name in freeze['files']:assert sha(source)==freeze['files'][name]['sha256'],name
    target.parent.mkdir(parents=True,exist_ok=True);assert OUT.resolve() in target.resolve().parents
    shutil.copy2(source,target);records[name]=dict(bytes=target.stat().st_size,sha256=sha(target));assert records[name]['sha256']==sha(source)
manifest=dict(status='PASS_RECOVERABLE_VERIFIED_SEVENTH_PAYLOAD',restore='Restore catalogue/runtime, credits, selectors, model index, external fonts and ELF together from files/. Large immutable original images/models remain at recorded paths. Exact SOURCE85/frozen joins and haptic-fix sources are retained; this is not a full checkout.',verified_master_sha256=qa['catalogues'][0]['sha256'],verified_runtime_sha256=qa['catalogues'][1]['sha256'],native_sha256=qa['native']['sha256'],scoped_verification_sha256=sha(receipt),root_actual190_proof_sha256=sha(rootproof),files=records)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
for name,row in records.items():assert sha(OUT/'files'/name)==row['sha256']
print((OUT/'manifest.json').relative_to(ROOT),sha(OUT/'manifest.json'),len(records))
