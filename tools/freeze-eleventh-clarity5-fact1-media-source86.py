"""Final bounded editorial input freeze after independent tenth recovery."""
from pathlib import Path
import hashlib,json,runpy,sys
ROOT=Path(__file__).resolve().parents[1];GROUP='eleventh-clarity5-fact1-media-source86'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha('content/catalog.json')=='7642dadf1c4e9a861965ac29282e594062064c9c771eb54165c0893a99b958d7'
assert sha('build/runtime-preview/content/catalog.json')=='18ae4fb6a38dad88cd3a9a6ba50439e20fbedeec2439d336aab8229e572b72db'
recovery='build/research/native-tenth-source86-recoverable/manifest.json';assert sha(recovery)=='eb93792e9194f1b0bbe143af80b50835d853e7e092112332e3e74241afeec36e'
for p,r in load(recovery)['files'].items():assert sha('build/research/native-tenth-source86-recoverable/files/'+p)==r['sha256'],p
assert sha('content/expansion/soundtrack-multitrack-priority-overrides.json')=='1508134c195845869dfdbab88c754ed032de17dcde5dd9c5859b89d6adef47b5'
assert sha('content/expansion/museum-story-gap-illustrations-reviewed.json')=='b5568b379ab0095ed20957e36d3e82719da2bda594f307055ba022cb6b5e26e2'
paths=set(load('build/research/tenth-clarity5-media4-source86-input-freeze.json')['files'])
paths.update([recovery,'build/research/tenth-source86-scoped/verification.json','build/research/tenth-source86-scoped/recovery-independent-verification.json','tools/freeze-eleventh-clarity5-fact1-media-source86.py','tools/prove-eleventh-clarity5-fact1-media-source86.py','tools/verify-reviewed-clarity206-actual-root.py','build/research/playhub-semantic-coverage/wiki-clarity/root-actual201-master-runtime-proof.json'])
joins=runpy.run_path(str(ROOT/'content/expansion/reviewed_clarity_next.py'))
for c,r in list(joins['PLANS'][-3:])+list(joins['POST_MEDIA_PLANS']):
    paths.update((c,r));doc=load(c)
    paths.update(x['provenance']['source_file'] for x in doc['replacements'] if x.get('provenance',{}).get('source_file'))
paths.update(sys.argv[1:])
paths.add('build/research/eleventh-six-body-staged-isolated-check.json')
if sys.argv[1:]:
    media_plan=load('content/expansion/museum-i-am-alive-bindings-reviewed.json')
    paths.update((media_plan['candidate_path'],media_plan['independent_review_receipt']))
    media=load(media_plan['candidate_path'])
    paths.update(r['path'] for r in media.get('source_receipts',[]))
files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p)) for p in sorted(paths)}
freeze=dict(status='APPROVED_INPUT_FREEZE',group=GROUP,expected_entries=1400,source_override_entries=86,new_music_recordings=0,new_clarity_replacements=5,separate_factual_fixes=1,total_revised_clarity_records=206,previous_actual_gaps=318,recovery=recovery,recovery_sha256=sha(recovery),recovery_files_verified=363,files=files,native_sha256=sha('build/eboot.elf'),native_scope='No new native code or compile; inventory/scoped QA only, sibling owns any necessary external font update.',additional_media_inputs=sys.argv[1:],no_further_source_admissions=True,no_ftp=True,shutdown_authorization=False)
out='build/research/'+GROUP+'-input-freeze.json';assert not (ROOT/out).exists();(ROOT/out).write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8');print(out,sha(out),len(files))
