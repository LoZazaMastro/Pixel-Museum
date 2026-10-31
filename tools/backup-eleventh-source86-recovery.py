"""Recoverable eleventh payload, only after sibling native/font/composer QA."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];GROUP='eleventh-clarity5-fact1-media-source86'
OUT=ROOT/'build/research/native-eleventh-source86-recoverable'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
assert len(sys.argv)==2,'Pass the final eleventh verification receipt path.'
receipt=ROOT/sys.argv[1];qa=load(receipt);assert qa['status'].startswith('PASS')
proofpath=ROOT/('build/research/'+GROUP+'-final-proof.json');proof=load(proofpath)
for r in qa['catalogues']:assert sha(ROOT/r['path'])==r['sha256']
assert qa['catalogues'][0]['sha256']==proof['master_sha256']
assert qa['catalogues'][1]['sha256']==proof['runtime_sha256']
assert sha(ROOT/qa['native']['path'])==qa['native']['sha256']
assert qa['native']['sha256']=='71fba8ccff3f25efc1ad610c28b44d459513abc20cc0482ae4c026952a6059f7','Eleventh uses the already verified ninth binary.'
for p,r in qa.get('fonts',qa.get('binary_fonts_unchanged',{})).items():assert sha(ROOT/p)==r['sha256']
rootproof=ROOT/'build/research/playhub-semantic-coverage/wiki-clarity/root-actual206-master-runtime-proof.json'
assert load(rootproof)['status']=='PASS'
assert qa.get('actual_narrative_gaps') is not None,'Require the current full actual compositor count.'
status=dict(status='PASS_VERIFIED_ELEVENTH_NOT_COMPLETE',catalogues=qa['catalogues'],scoped_qa_path=receipt.relative_to(ROOT).as_posix(),scoped_qa_sha256=sha(receipt),editorial_proof_sha256=sha(proofpath),root_actual206_proof_path=rootproof.relative_to(ROOT).as_posix(),root_actual206_proof_sha256=sha(rootproof),native=qa['native'],actual_unillustrated_narrative_scenes=qa['actual_narrative_gaps'],incomplete_editorial_collection=True,no_ftp_performed=True)
statuspath=ROOT/('build/research/'+GROUP+'-final-status.json')
if statuspath.exists():assert load(statuspath)==status
else:statuspath.write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
if (OUT/'manifest.json').exists():
    for name,row in load(OUT/'manifest.json')['files'].items():assert sha(OUT/'files'/name)==row['sha256']
    print('Already archived',sha(OUT/'manifest.json'));raise SystemExit
previous=ROOT/'build/research/native-tenth-source86-recoverable/manifest.json';freeze=load(ROOT/('build/research/'+GROUP+'-input-freeze.json'))
names=set(load(previous)['files'])|set(freeze['files'])
names.update([receipt.relative_to(ROOT).as_posix(),proofpath.relative_to(ROOT).as_posix(),rootproof.relative_to(ROOT).as_posix(),statuspath.relative_to(ROOT).as_posix(),'build/research/'+GROUP+'-input-freeze.json','build/research/'+GROUP+'-integrity.json','tools/backup-eleventh-source86-recovery.py'])
def refs(value):
    if isinstance(value,str) and not Path(value).is_absolute() and (ROOT/value).is_file():names.add(value.replace('\\','/'))
    elif isinstance(value,dict):
        for key,item in value.items():refs(key);refs(item)
    elif isinstance(value,list):
        for item in value:refs(item)
refs(qa)
names.update(p.relative_to(ROOT).as_posix() for p in receipt.parent.glob('*.json'))
names.update(p.relative_to(ROOT).as_posix() for p in receipt.parent.glob('*.log'))
records={}
for name in sorted(names):
    source=ROOT/name;target=OUT/'files'/name
    if name in freeze['files']:assert sha(source)==freeze['files'][name]['sha256'],name
    target.parent.mkdir(parents=True,exist_ok=True);assert OUT.resolve() in target.resolve().parents
    shutil.copy2(source,target);records[name]=dict(bytes=target.stat().st_size,sha256=sha(target));assert records[name]['sha256']==sha(source)
manifest=dict(status='PASS_RECOVERABLE_VERIFIED_ELEVENTH_PAYLOAD',restore='Restore authoring/runtime, credits, selectors, index, external fonts and matching ELF together from files/. Large immutable original images/models remain at recorded paths. Exact SOURCE86/media81/Vanquish3/Yakuza1/Atlus1/BG3fact1/IAmAlive inputs and unchanged reviewed ObjectScene source are retained. Not a full checkout.',verified_master_sha256=proof['master_sha256'],verified_runtime_sha256=proof['runtime_sha256'],native_sha256=qa['native']['sha256'],scoped_verification_sha256=sha(receipt),root_actual206_proof_sha256=sha(rootproof),files=records)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
for name,row in records.items():assert sha(OUT/'files'/name)==row['sha256']
print((OUT/'manifest.json').relative_to(ROOT),sha(OUT/'manifest.json'),len(records))
