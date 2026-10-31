"""Freeze only approved NEXT inputs while verifying the fourth recovery copy."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
GROUP='fifth-switch5-media5-source76'
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha('content/catalog.json')=='609124314973d6aa78f89125f5d4e99c4acdcc30fa700c9c0126573e882cfc91'
assert sha('build/runtime-preview/content/catalog.json')=='95cc1374444743e49fd9726a3f16e7b44f8447c4702ac07a3b5afc16568a2ca0'
recovery='build/research/native-fourth-source73-recoverable/manifest.json'
assert sha(recovery)=='d4953323e9fe749ff4674af60c1d44193044666f0c4b8a190309a3dd7cc5f1f3'
for name,row in load(recovery)['files'].items():assert sha('build/research/native-fourth-source73-recoverable/files/'+name)==row['sha256']
expected={
 'content/expansion/museum-switch-game-additions-reviewed.json':'9758d09497812795d54d0f41db515b696e0e3618d9c3969c92045fb336334c5c',
 'content/expansion/museum-story-gap-illustrations-reviewed.json':'74563987cf6c33d80304a82316e3518c068722dbd4a00bfe740dee137cf3534e',
 'content/expansion/soundtrack-multitrack-priority-overrides.json':'26db196e074924347ab6639959b0440cfec108b15887ea7f6bf111ac220697d1',
 'models/index.json':'8b102029e7524b2d2ea712230a946d151e79edd462983bb05a3494b9dc5141a7'}
for p,h in expected.items():assert sha(p)==h,p
paths=set(expected)|{'content/assemble_catalog.py','content/expansion/apply_museum_revision.py','content/expansion/reviewed_switch_game_additions.py','content/expansion/reviewed_story_gap_images.py','tools/runtime-catalog.py','tools/prepare-runtime-preview.py','tools/bundle-editorial-images.py','models/atari-vcs.artwork.pmc','models/licenses/atari-vcs.json',recovery}
for module in ['content/expansion/museum-switch-game-additions-reviewed.json','content/expansion/museum-story-gap-illustrations-reviewed.json']:
    for batch in load(module)['batches']:
        for key in ['candidate_path','independent_review_receipt']:
            if key in batch:paths.add(batch[key])
for p in ['tetris40-resident-evil-seven81-display-corrected-candidate.json','independent-display-corrected-121-review.json','pentiment-thirty-seven-official-album-candidate.json','independent-thirty-seven-pentiment-album-review.json']:paths.add('build/research/soundtrack-broad/modern-next-four/'+p)
files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=sha(p)) for p in sorted(paths)}
freeze=dict(status='APPROVED_INPUT_FREEZE',group=GROUP,expected_entries=1400,expected_new_entries=5,expected_new_narrative_paragraphs=25,expected_new_article_images=35,expected_new_existing_story_images=5,expected_new_music_recordings=158,source_override_entries=76,prior_runtime_bytes=15086769,backup_files_verified=len(load(recovery)['files']),recovery=recovery,recovery_manifest_sha256=sha(recovery),files=files,excluded_next=['Unreviewed new media candidates','Any music other than SOURCE76'],no_ftp=True)
out='build/research/'+GROUP+'-input-freeze.json'
(ROOT/out).write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
print(out,sha(out),len(files))
