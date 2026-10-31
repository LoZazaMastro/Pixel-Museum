"""Freeze the seventh approved source group after coherent sixth recovery."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='seventh-media5-source85'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha('content/catalog.json')=='b9d1186dcb05cfc24a16862a3a524d684aae9a6ba804e7a11ebdf4b848d118ba'
assert sha('build/runtime-preview/content/catalog.json')=='e2df21a36acc23ddf6b56e54bd6dcc919bb26103f8b934b256dff4ebfd886e89'
recovery='build/research/native-sixth-source81-recoverable/manifest.json'
assert sha(recovery)=='1ee4481281cdc6e1943ab3ed549745e6037eb6cb62bbd5f73fb82dfb0a205558'
for p,r in load(recovery)['files'].items():assert sha('build/research/native-sixth-source81-recoverable/files/'+p)==r['sha256']
expected={'content/expansion/soundtrack-multitrack-priority-overrides.json':'9e38d901ecd55361c944d8ff2b7d4734a1997a04a404e8579226ec7ddb515ff3','content/expansion/museum-story-gap-illustrations-reviewed.json':'854d02bf438c5c9db1f33d01a1315304266abca79ae2a5525fe2145615a21f5b'}
for p,h in expected.items():assert sha(p)==h
paths=set(load('build/research/sixth-media11-sp4-source81-input-freeze.json')['files'])|set(expected)
paths.update([recovery,'build/research/sixth-source81-font-scoped/verification.json','build/research/playhub-semantic-coverage/wiki-clarity/root-actual190-master-runtime-proof.json','content/assemble_catalog.py','tools/runtime-catalog.py','tools/bundle-editorial-images.py'])
for b in load('content/expansion/museum-story-gap-illustrations-reviewed.json')['batches']:
    paths.update(b[k] for k in ['candidate_path','independent_review_receipt'] if k in b)
music=load('content/expansion/soundtrack-multitrack-priority-overrides.json');assert len(music['entries'])==85
for e in music['entries'][-4:]:
    rp=e['independent_review_receipt'];paths.add(rp);paths.add(load(rp)['candidate_path'])
files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p)) for p in sorted(paths)}
freeze=dict(status='APPROVED_INPUT_FREEZE',group=GROUP,expected_entries=1400,source_override_entries=85,new_music_recordings=295,reviewed_new_body_replacements=0,total_revised_body_records=190,new_narrative_image_records=5,previous_actual_gaps=363,recovery=recovery,recovery_sha256=sha(recovery),recovery_files_verified=163,files=files,excluded_next=['All later discovery candidates','Atari prototype800x600 and catalogue768x1012 held for quality'],native_scope='Sibling owns the two approved scoped haptic code fixes and final font/native QA. No font baking in this authoring process.',no_ftp=True)
out='build/research/'+GROUP+'-input-freeze.json';(ROOT/out).write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8');print(out,sha(out),len(files))
