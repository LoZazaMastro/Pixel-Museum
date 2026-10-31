"""Freeze only five reviewed bodies and four images after recoverable ninth QA."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='tenth-clarity5-media4-source86'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha('content/catalog.json')=='7f707634e66bb7ebe33018ab8282b1a077b59d6d4a8bfd4215e8776833b0ba97'
assert sha('build/runtime-preview/content/catalog.json')=='d2d83337b6fad0c07f6980aa41d1bd3fb4a4a250fd8fc3ee6cb41768cdc13822'
recovery='build/research/native-ninth-source86-recoverable/manifest.json';assert sha(recovery)=='738ad9c93b1d6b3353b36279684c85204986beecde5b94bb1673247e58125e19'
for p,r in load(recovery)['files'].items():assert sha('build/research/native-ninth-source86-recoverable/files/'+p)==r['sha256'],p
assert sha('content/expansion/soundtrack-multitrack-priority-overrides.json')=='1508134c195845869dfdbab88c754ed032de17dcde5dd9c5859b89d6adef47b5'
assert sha('content/expansion/museum-story-gap-illustrations-reviewed.json')=='b5568b379ab0095ed20957e36d3e82719da2bda594f307055ba022cb6b5e26e2'
paths=set(load('build/research/ninth-media7-mega3-source86-input-freeze.json')['files'])
paths.update([recovery,'build/research/ninth-source86-font-scoped/verification.json','build/research/ninth-source86-font-scoped/recovery-independent-verification.json','tools/freeze-tenth-clarity5-media4-source86.py','tools/prove-tenth-clarity5-media4-source86.py','tools/verify-reviewed-clarity201-actual-root.py','build/research/tenth-five-clarity-isolated-check.json','build/research/story-gap-media81-next-isolated-admission-check.json','build/research/playhub-semantic-coverage/wiki-clarity/root-actual196-master-runtime-proof.json'])
plans=__import__('runpy').run_path(str(ROOT/'content/expansion/reviewed_clarity_next.py'))['PLANS'][-2:]
for c,r in plans:
    for p in (c,r):paths.add(p if p.startswith('build/') else 'build/research/playhub-semantic-coverage/wiki-clarity/'+p)
    candidate=load(c if c.startswith('build/') else 'build/research/playhub-semantic-coverage/wiki-clarity/'+c)
    paths.update(x['provenance']['source_file'] for x in candidate['replacements'])
batch=load('content/expansion/museum-story-gap-illustrations-reviewed.json')['batches'][-1]
paths.update(batch[k] for k in ('candidate_path','independent_review_receipt'))
candidate=load(batch['candidate_path']);paths.update(r['path'] for r in candidate['source_receipts'])
for images in candidate['entries'].values():paths.update(i['recovery_local_source'] for i in images)
for f in candidate['feature_entries']:paths.update(i['recovery_local_source'] for i in f['images'])
files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p)) for p in sorted(paths)}
freeze=dict(status='APPROVED_INPUT_FREEZE',group=GROUP,expected_entries=1400,source_override_entries=86,new_music_recordings=0,new_body_replacements=5,total_revised_body_records=201,new_narrative_image_records=4,previous_actual_gaps=334,recovery=recovery,recovery_sha256=sha(recovery),recovery_files_verified=292,files=files,native_sha256=sha('build/eboot.elf'),native_scope='No new native source changes; inventory and scoped QA only. Sibling decides whether new glyphs need external font bake.',excluded_next=['Atlus Persona1 future11','BG3 date1 future11','All later candidates'],no_ftp=True)
out='build/research/'+GROUP+'-input-freeze.json';assert not (ROOT/out).exists();(ROOT/out).write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8');print(out,sha(out),len(files))
