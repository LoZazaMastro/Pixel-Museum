"""Independent review of the original Mortal Kombat artifact used in Boon's career."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/ed-boon-existing-prose-original-arcade-artifact'
path=base/'five-existing-ed-boon-paragraphs-two-distinct-career-chapters-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(path.read_text(encoding='utf8'));row,=doc['rows'];old=row['old_entry'];new=row['new_entry']
current=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']==row['entry_id'])
assert current==old and old['body']==new['body'] and len(old['body'])==5
assert old.get('story_headings')==new.get('story_headings')
assert {k:v for k,v in old['images'][0].items()if k!='story_paragraph'}=={k:v for k,v in new['images'][0].items()if k!='story_paragraph'}
assert new['images'][0]['story_paragraph']==-1 and new['images'][0]['portrait']
assert new['images'][1]==old['images'][1]
assert [v['youtube_id']for v in new['videos']]==[v['youtube_id']for v in old['videos']]
assert doc['expected_main_paragraph_groups']==[[0,1,2,3],[4]]
for name,digest in doc['source_files'].items():assert sha(ROOT/name)==digest,name
item=new['images'][2];p=ROOT/item['recovery_local_source']
assert item['story_paragraph']==4 and sha(p)==item['verification']['sha256']
with Image.open(p)as image:image.load();assert image.size==(1280,1656)==(item['width'],item['height'])
out=base/'root-independent-five-existing-paragraphs-original-mk-flyer-peer-review.json'
report=dict(status='PASS_INDEPENDENT_ORIGINAL_GAME_ARTIFACT_AND_PROSE_REVIEW',candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
    current_owner_unchanged=True,five_existing_paragraphs_and_headings_unchanged=True,portrait_cover_exclusive=True,all_source_hashes_checked=True,
    full_visual_review='Complete original Midway Mortal Kombat arcade sales flyer, with the original cabinet, digitized martial-artist cast, Midway/WMS footer and USA1992 Olympic sponsorship mark. Not a reboot or later sequel.',
    limits=['Publisher advertisement is not a development-team photograph.',
        'Existing career interview remains with introductory biography; no unrelated pinball illustration introduced.',
        'Actual native two-scene/scroll validation recorded separately by timeline agent.'])
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
