"""Freeze the approved sixth group, excluding all later discovery candidates."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];GROUP='sixth-media11-sp4-source81'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha('content/catalog.json')=='5f25b333317a231768d8003ebae658062a63a3d15443f6164d6724a9b4be7fd7'
assert sha('build/runtime-preview/content/catalog.json')=='dac9d922d972cd8d2a8501ee98d4aff9bbad40620285b977dc6eea3e15ca8f6a'
recovery='build/research/native-fifth-source76-recoverable/manifest.json'
assert sha(recovery)=='68886290e8e202233bea5dcf1585a63f6bc669c557c65a57e81feb8213ae0c8c'
for p,r in load(recovery)['files'].items():assert sha('build/research/native-fifth-source76-recoverable/files/'+p)==r['sha256']
expected={'content/expansion/soundtrack-multitrack-priority-overrides.json':'570c13124161110f53f0cd7d5ef38d9f9e15577ab138377d86e27b80860fb45b','content/expansion/museum-story-gap-illustrations-reviewed.json':'59ce989f9d75b513caf24f94360a62ef56312a433952836f4db2efa6b63fb8b8'}
for p,h in expected.items():assert sha(p)==h
paths=set(load('build/research/fifth-switch5-media5-source76-input-freeze.json')['files'])
paths.update(expected)
paths.update(['content/expansion/reviewed_clarity_next.py','content/expansion/gba_sp_reviewed_narrative_media.py',recovery,'build/research/fifth-source76-font-scoped/verification.json','build/research/fifth-switch5-root-independent-content-review.json'])
for b in load('content/expansion/museum-story-gap-illustrations-reviewed.json')['batches']:
    paths.update(b[k] for k in ['candidate_path','independent_review_receipt'] if k in b)
base='build/research/gba-sp-launch-and-concrete-article/'
paths.update(base+n for n in ['four-wikipedia-cards-launch-without-regional-prose-candidate.json','independent-four-concrete-cards-real-launch-review.json','two-original-sp-accessory-illustrations-readable-candidate.json','independent-two-original-sp-accessory-images-review.json','isolated-admission-check.json'])
music=load('content/expansion/soundtrack-multitrack-priority-overrides.json');assert len(music['entries'])==81
for e in music['entries'][-5:]:
    rp=e['independent_review_receipt'];paths.add(rp);paths.add(load(rp)['candidate_path'])
files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p)) for p in sorted(paths)}
freeze=dict(status='APPROVED_INPUT_FREEZE',group=GROUP,expected_entries=1400,source_override_entries=81,new_music_recordings=307,reviewed_new_body_replacements=4,total_revised_body_records=190,new_narrative_image_records=11,previous_actual_gaps=383,recovery=recovery,recovery_sha256=sha(recovery),recovery_files_verified=137,files=files,excluded_next=['Unreviewed or later Switch music candidates','All media not in SOURCE65 or the explicit SPtwo candidate'],no_ftp=True)
out='build/research/'+GROUP+'-input-freeze.json';(ROOT/out).write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8');print(out,sha(out),len(files))
