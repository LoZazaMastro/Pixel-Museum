"""Preserve the verified fifth payload before the sixth authoring join."""
from pathlib import Path
import copy,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1];GROUP='fifth-switch5-media5-source76'
OUT=ROOT/'build/research/native-fifth-source76-recoverable'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf8'))
receiptpath=ROOT/'build/research/fifth-source76-font-scoped/verification.json';qa=load(receiptpath)
qa['master']=next(r for r in qa['catalogues'] if r['path']=='content/catalog.json')
qa['runtime']=next(r for r in qa['catalogues'] if r['path']=='build/runtime-preview/content/catalog.json')
for p,r in qa['fonts'].items():assert sha(ROOT/p)==r['sha256']
assert sha(ROOT/qa['native']['path'])==qa['native']['sha256']
for field in ('master','runtime'):
    row=qa[field];assert sha(ROOT/row['path'])==row['sha256']
proof=ROOT/('build/research/'+GROUP+'-final-proof.json');assert sha(proof)=='a2fe21d6ad668fd742bf41899e1715432ff0e6159a4774e4870ac506a71f4ab2'
rootproof=ROOT/'build/research/fifth-switch5-root-independent-content-review.json'
assert sha(rootproof)=='4437ba380d1948d28818ca7e3b443385cef2a92a91a67ac264b9a3e5e1ff4e5e'
status=dict(status='PASS_VERIFIED_FIFTH_NOT_COMPLETE',master=qa['master'],runtime=qa['runtime'],scoped_qa_path=receiptpath.relative_to(ROOT).as_posix(),scoped_qa_sha256=sha(receiptpath),editorial_proof_sha256=sha(proof),root_independent_proof_sha256=sha(rootproof),actual_unillustrated_narrative_scenes=383,actual_gap_breakdown=dict(main=215,feature=168),incomplete_editorial_collection=True,no_ftp_performed=True)
statuspath=ROOT/('build/research/'+GROUP+'-final-status.json')
if not statuspath.exists():statuspath.write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
else:assert load(statuspath)==status
if (OUT/'manifest.json').exists():
    for name,row in load(OUT/'manifest.json')['files'].items():assert sha(OUT/'files'/name)==row['sha256']
    print('Already archived',sha(OUT/'manifest.json'));raise SystemExit(0)
previous=ROOT/'build/research/native-fourth-source73-recoverable'
names=set(load(previous/'manifest.json')['files'])
freeze=load(ROOT/('build/research/'+GROUP+'-input-freeze.json'))
names.update(freeze['files'])
names.update([proof.relative_to(ROOT).as_posix(),statuspath.relative_to(ROOT).as_posix(),rootproof.relative_to(ROOT).as_posix(),'build/research/'+GROUP+'-input-freeze.json','build/research/'+GROUP+'-integrity.json'])
names.update(p.relative_to(ROOT).as_posix() for p in receiptpath.parent.glob('*.json'))
records={};music='content/expansion/soundtrack-multitrack-priority-overrides.json'
for name in sorted(names):
    target=OUT/'files'/name;target.parent.mkdir(parents=True,exist_ok=True)
    assert OUT.resolve() in target.resolve().parents
    if name==music:
        # NEXT81 is outside this payload. Reconstruct the exact frozen76 bytes
        # from its unchanged prefix and require the preassembly hash.
        document=copy.deepcopy(load(ROOT/name));document['entries']=document['entries'][:76]
        data=(json.dumps(document,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode('utf8')
        assert hashlib.sha256(data).hexdigest()==freeze['files'][name]['sha256']
        target.write_bytes(data)
    else:
        source=ROOT/name
        if name in freeze['files']:assert sha(source)==freeze['files'][name]['sha256'],name
        shutil.copy2(source,target)
    records[name]=dict(bytes=target.stat().st_size,sha256=sha(target))
    if name!=music:assert records[name]['sha256']==sha(ROOT/name)
manifest=dict(status='PASS_RECOVERABLE_VERIFIED_FIFTH_PAYLOAD',restore='Restore catalogue/runtime, credits, selectors, models index, matching external fonts and ELF together from files/. Large immutable original images/models remain at their recorded paths. Exact SOURCE76 is preserved; later SOURCE81 is excluded. This is compiled payload recovery with frozen join inputs, not a complete repository checkout.',verified_master_sha256=qa['master']['sha256'],verified_runtime_sha256=qa['runtime']['sha256'],scoped_verification_sha256=sha(receiptpath),root_independent_proof_sha256=sha(rootproof),files=records)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
for name,row in records.items():assert sha(OUT/'files'/name)==row['sha256']
print((OUT/'manifest.json').relative_to(ROOT),sha(OUT/'manifest.json'),len(records))
