"""Freeze the ninth reviewed group; optional Lua correction is admitted separately."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];GROUP='ninth-media7-mega3-source86'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha('content/catalog.json')=='14ec613b84f6a660562dabab79c2de6cb60d26936f393070bad9b20806e997e9'
assert sha('build/runtime-preview/content/catalog.json')=='cad1a476770b7ae47d7c0024a185d03e4639fcab9f1ccd34c4f7b43655addb5d'
recovery='build/research/native-eighth-source85-recoverable/manifest.json'
assert sha(recovery)=='87d83a384154892b546b509829795e9d5c21e300be4e966d6a13b9a975272f63'
for p,r in load(recovery)['files'].items():assert sha('build/research/native-eighth-source85-recoverable/files/'+p)==r['sha256'],p
expected={
 'content/expansion/soundtrack-multitrack-priority-overrides.json':'1508134c195845869dfdbab88c754ed032de17dcde5dd9c5859b89d6adef47b5',
 'content/expansion/museum-story-gap-illustrations-reviewed.json':'39338306cdb8be37e2506c38f51c14659340259d57c4fb4bf98946852831d1de',
 'src/museum/object_scene.cpp':'ef7098bd072920b6df7cb8247d4425e23fa3224c701fd70956774e45d0888ea8'}
for p,h in expected.items():assert sha(p)==h,p
paths=set(load('build/research/eighth-sayonara3-source85-input-freeze.json')['files'])|set(expected)
paths.update([recovery,'build/research/eighth-sayonara3-scoped/verification.json','build/research/eighth-sayonara3-scoped/recovery-independent-verification.json','build/research/playhub-semantic-coverage/wiki-clarity/root-actual193-master-runtime-proof.json','content/assemble_catalog.py','content/expansion/reviewed_clarity_next.py','tools/runtime-catalog.py','tools/bundle-editorial-images.py','tools/package-museum.py','tools/freeze-ninth-media7-mega3-source86.py','tools/prove-ninth-media7-mega3-source86.py','build/research/model-merge-reserve-probe/root-independent-reserve-merge-review.json'])
media=load('content/expansion/museum-story-gap-illustrations-reviewed.json')
for b in media['batches']:
    paths.update(b[k] for k in ('candidate_path','independent_review_receipt') if k in b)
base='build/research/mega-drive-three-concrete-cards/'
paths.update(base+p for p in ('three-concrete-wikipedia-mega-drive-cards-clear-identities-candidate.json','independent-three-concrete-mega-drive-cards-review.json','wikipedia-full-revision.json','two-original-mega-drive-hardware-illustrations-candidate.json','independent-two-original-mega-drive-images-review.json'))
music=load('content/expansion/soundtrack-multitrack-priority-overrides.json');assert len(music['entries'])==86
rp=music['entries'][-1]['independent_review_receipt'];paths.add(rp)
paths.add('build/research/soundtrack-broad/burnout-revenge-licensed-original/forty-original-licensed-songs-candidate.json')
paths.add('build/research/soundtrack-broad/burnout-revenge-licensed-original/source86-next-promotion.json')
paths.update(sys.argv[1:])
paths.add('tools/backup-ninth-source86-recovery.py')
if sys.argv[1:]:
    lua=load('build/research/lua-language-original-cover-correction/one-lua-language-official-transparent-vector-cover-and-quarantine-candidate.json')
    paths.update(r['path'] for r in lua['source_receipts'])
    paths.add(lua['new_cover']['recovery_local_source'])
assert sha('tools/update-museum-ftp.py')=='1a37295eed21e3b9b2a5e1aece238215257c3308e6f613c604edd7dfd28af75e'
paths.update(['tools/update-museum-ftp.py','build/research/deployment-tool-selfcheck/verification.json','build/research/deployment-tool-selfcheck/independent-report-path-fixed-review.json'])
files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p)) for p in sorted(paths)}
freeze=dict(status='APPROVED_INPUT_FREEZE',group=GROUP,expected_entries=1400,source_override_entries=86,new_music_recordings=40,music_inventory=41,music_held=1,reviewed_new_body_replacements=3,total_revised_body_records=196,new_narrative_image_records=7,previous_actual_gaps=353,previous_gap_scope='Seventh full compositor profile; eighth only three illustrated text cards changed.',recovery=recovery,recovery_sha256=sha(recovery),recovery_files_verified=221,files=files,additional_lua_inputs=sys.argv[1:],excluded_next=['Four newer game/maker images','All later discovery candidates'],native_scope='One approved lossless merge-buffer preallocation hunk; sibling owns inventory/font decision and single native compile/scoped QA.',no_ftp=True)
out='build/research/'+GROUP+'-input-freeze.json';assert not (ROOT/out).exists(),'Do not overwrite an existing input freeze.'
(ROOT/out).write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8');print(out,sha(out),len(files))
