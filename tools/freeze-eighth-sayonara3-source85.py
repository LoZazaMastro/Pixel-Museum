"""Freeze only the three approved Sayonara text replacements."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='eighth-sayonara3-source85'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha('build/research/native-seventh-source85-recoverable/files/content/catalog.json')=='a54d83ad2d9b49dd16cee5160bc23b2215ee80d96a25372d0192c1ad27106d83'
assert sha('build/research/native-seventh-source85-recoverable/files/build/runtime-preview/content/catalog.json')=='889799b37c1eea2c79f67cef7390d24a82d3aabf8150d405ea0900d747ed121a'
recovery='build/research/native-seventh-source85-recoverable/manifest.json';assert sha(recovery)=='f4eeaee34587b87c54a98b2d473083bf7d16a024571ff68ff79e29e9ef3ac6f0'
for p,r in load(recovery)['files'].items():assert sha('build/research/native-seventh-source85-recoverable/files/'+p)==r['sha256']
paths=set(load('build/research/seventh-media5-source85-input-freeze.json')['files'])
paths.add('content/expansion/integrate_priority_features.py')
base='build/research/playhub-semantic-coverage/wiki-clarity/new-bounded-current-audit/sayonara-three/'
candidate=base+'three-concrete-sayonara-cards-clarity-edited-candidate.json';peer=base+'independent-three-clarity-edited-sayonara-cards-review.json'
assert sha(candidate)=='5972e5bd9d3c1e18b449adb7d3c8a4ef4ff6ac611d4073ccf454c8e37bfb3bee'
assert sha(peer)=='497e4b3237a725ba7cca64f7a10bd5cf024ff171589304bdd2ac7e4fc12a270f'
assert load(peer)['status']=='PASS' and load(peer)['candidate_sha256']==sha(candidate)
paths.update([candidate,peer,base+'wikipedia-full-revision.json',recovery,'content/expansion/reviewed_clarity_next.py','build/research/seventh-source85-font-scoped/verification.json','build/research/seventh-source85-font-scoped/recovery-independent-verification.json','build/research/playhub-semantic-coverage/wiki-clarity/root-actual190-seventh-master-runtime-proof.json'])
assert sha('content/expansion/soundtrack-multitrack-priority-overrides.json')=='9e38d901ecd55361c944d8ff2b7d4734a1997a04a404e8579226ec7ddb515ff3'
assert sha('content/expansion/museum-story-gap-illustrations-reviewed.json')=='854d02bf438c5c9db1f33d01a1315304266abca79ae2a5525fe2145615a21f5b'
files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p)) for p in sorted(paths)}
freeze=dict(status='APPROVED_INPUT_FREEZE',group=GROUP,expected_entries=1400,source_override_entries=85,new_music_recordings=0,new_narrative_image_records=0,new_body_replacements=3,total_revised_body_records=193,previous_actual_gaps=353,recovery=recovery,recovery_sha256=sha(recovery),recovery_files_verified=191,files=files,local_images_manifest_sha256=sha('assets/images/manifest.json'),native_sha256=sha('build/eboot.elf'),no_native_or_font_build_requested=True,no_ftp=True)
out='build/research/'+GROUP+'-input-freeze.json';(ROOT/out).write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8');print(out,sha(out),len(files))
