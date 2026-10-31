"""Append four independently reviewed partial collections after sixth recovery."""
from pathlib import Path
import hashlib,json,copy
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
backup='build/research/native-sixth-source81-recoverable/manifest.json'
assert sha(backup)=='1ee4481281cdc6e1943ab3ed549745e6037eb6cb62bbd5f73fb82dfb0a205558'
for name,r in load(backup)['files'].items():assert sha('build/research/native-sixth-source81-recoverable/files/'+name)==r['sha256']
music='content/expansion/soundtrack-multitrack-priority-overrides.json'
oldsha='570c13124161110f53f0cd7d5ef38d9f9e15577ab138377d86e27b80860fb45b'
assert sha(music)==oldsha
s=load(music);before=copy.deepcopy(s['entries']);assert len(before)==81
reviews=[('build/research/soundtrack-broad/switch-compilations-tour-next/independent-two-hundred-thirteen-public-collection-review.json','420f10db06c092946f87576c2a1acd2a28b4849d53259eb2d8607b2213cd9494'),('build/research/soundtrack-broad/modern-following/independent-eighty-two-original-mhw-recordings-review.json','f10a771e0261ce40bf2aee25326247eda6915d96dc3f96bd212e26788fb2e758')]
added=[]
for rp,rs in reviews:
    assert sha(rp)==rs
    r=load(rp);assert r['status']=='PASS' and sha(r['candidate_path'])==r['candidate_sha256']
    for e in load(r['candidate_path'])['entries']:
        e=copy.deepcopy(e);assert not any(x['entry_id']==e['entry_id'] for x in s['entries'])
        assert e['full_album_collection'] is False
        e['independent_review_receipt']=rp;s['entries'].append(e)
        added.append(dict(entry_id=e['entry_id'],recordings=len(e['tracks'])))
assert len(s['entries'])==85 and s['entries'][:81]==before and sum(x['recordings'] for x in added)==295
tmp=ROOT/(music+'.tmp');tmp.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8');tmp.replace(ROOT/music)
report=dict(status='PASS_NEXT85_SOURCE_ONLY',previous_source_sha256=oldsha,source_sha256=sha(music),source_entries=85,prior81_exact=True,added=added,added_recordings=295,sixth_backup_sha256=sha(backup),master_sha256=sha('content/catalog.json'),runtime_sha256=sha('build/runtime-preview/content/catalog.json'),master_runtime_modified=False)
out='build/research/soundtrack-broad/source85-next-promotion.json';(ROOT/out).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2))
