"""Preserve the verified sixth payload and exact frozen source inputs together."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1];GROUP='sixth-media11-sp4-source81'
OUT=ROOT/'build/research/native-sixth-source81-recoverable'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
receipt=ROOT/'build/research/sixth-source81-font-scoped/verification.json';qa=load(receipt)
assert sha(receipt)=='a85dfa16b54c49eab23494674601b72fdbe666229a2d31267897f6f152a3467c'
for r in qa['catalogues']:assert sha(ROOT/r['path'])==r['sha256']
for p,r in qa['fonts'].items():assert sha(ROOT/p)==r['sha256']
assert sha(ROOT/qa['native']['path'])==qa['native']['sha256']
proof=ROOT/('build/research/'+GROUP+'-final-proof.json')
assert sha(proof)=='c71290db35fc5fcd9adbd9f3cdb5491e63c019fae177940a52bfa73382a6a97d'
rootproof=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/root-actual190-master-runtime-proof.json'
status=dict(status='PASS_VERIFIED_SIXTH_NOT_COMPLETE',catalogues=qa['catalogues'],scoped_qa_path=receipt.relative_to(ROOT).as_posix(),scoped_qa_sha256=sha(receipt),editorial_proof_sha256=sha(proof),root_actual190_proof_path=rootproof.relative_to(ROOT).as_posix(),root_actual190_proof_sha256=sha(rootproof),actual_unillustrated_narrative_scenes=363,actual_gap_breakdown=dict(main=207,feature=156),incomplete_editorial_collection=True,no_ftp_performed=True)
statuspath=ROOT/('build/research/'+GROUP+'-final-status.json')
if statuspath.exists():assert load(statuspath)==status
else:statuspath.write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
if (OUT/'manifest.json').exists():
    for name,row in load(OUT/'manifest.json')['files'].items():assert sha(OUT/'files'/name)==row['sha256']
    print('Already archived',sha(OUT/'manifest.json'));raise SystemExit
previous=ROOT/'build/research/native-fifth-source76-recoverable/manifest.json'
freeze=load(ROOT/('build/research/'+GROUP+'-input-freeze.json'))
names=set(load(previous)['files'])|set(freeze['files'])
names.update(p.relative_to(ROOT).as_posix() for p in receipt.parent.glob('*.json'))
names.update([proof.relative_to(ROOT).as_posix(),rootproof.relative_to(ROOT).as_posix(),statuspath.relative_to(ROOT).as_posix(),'build/research/'+GROUP+'-input-freeze.json','build/research/'+GROUP+'-integrity.json'])
records={}
for name in sorted(names):
    source=ROOT/name;target=OUT/'files'/name
    if name in freeze['files']:assert sha(source)==freeze['files'][name]['sha256'],name
    target.parent.mkdir(parents=True,exist_ok=True)
    assert OUT.resolve() in target.resolve().parents
    shutil.copy2(source,target)
    records[name]=dict(bytes=target.stat().st_size,sha256=sha(target))
    assert records[name]['sha256']==sha(source)
manifest=dict(status='PASS_RECOVERABLE_VERIFIED_SIXTH_PAYLOAD',restore='Restore catalogue/runtime, credits, selectors, model index, external fonts and ELF together from files/. Large immutable original images/models remain at recorded paths. Exact SOURCE81 and its frozen join inputs are retained. Not a full checkout.',verified_master_sha256=qa['catalogues'][0]['sha256'],verified_runtime_sha256=qa['catalogues'][1]['sha256'],scoped_verification_sha256=sha(receipt),root_actual190_proof_sha256=sha(rootproof),files=records)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
for name,row in records.items():assert sha(OUT/'files'/name)==row['sha256']
print((OUT/'manifest.json').relative_to(ROOT),sha(OUT/'manifest.json'),len(records))
