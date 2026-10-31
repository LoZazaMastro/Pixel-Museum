"""Independent whole-flyer and unchanged-prose review."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/shoot-away-existing-prose-period-machines'
path=base/'seven-existing-shoot-away-paragraphs-three-period-machine-chapters-candidate.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=json.loads(path.read_text(encoding='utf8'));row,=doc['rows'];old=row['old_entry'];new=row['new_entry']
current=next(e for e in json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))['entries']if e['id']==row['entry_id'])
assert current==old and new['body']==old['body'] and len(old['body'])==7
assert new.get('story_headings')==old.get('story_headings')
assert doc['expected_main_paragraph_groups']==[[0,1],[2,3,4,5],[6]]
assert new['images'][0].get('story_paragraph',-1)==-1
assert {k:v for k,v in old['images'][0].items()if k!='story_paragraph'}=={k:v for k,v in new['images'][0].items()if k!='story_paragraph'}
assert new['videos']==old['videos'] and new['images'][1]==old['images'][1]
for name,digest in doc['source_files'].items():assert sha(ROOT/name)==digest,name
allhashes=[sha(ROOT/i['recovery_local_source'])for i in new['images']]
assert len(allhashes)==len(set(allhashes))
for item,filename,year in zip(new['images'][2:],['shoot-away-1984-flyer-source.html','clay-champ-1979-flyer-source.html'],['1984','1979']):
    html=(base/filename).read_text(encoding='utf8')
    assert item['url'].split('/')[-1]in html and year in html
    with Image.open(ROOT/item['recovery_local_source'])as image:
        image.load();assert image.size==(850,1101)==(item['width'],item['height'])
out=base/'root-independent-seven-existing-paragraphs-two-period-flyers-peer-review.json'
report=dict(status='PASS_INDEPENDENT_PERIOD_MACHINE_AND_PROSE_REVIEW',candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
    seven_existing_paragraphs_and_headings_unchanged=True,source_hashes_and_published_urls_checked=True,exclusive_cover=True,
    full_visual_review=['Namco Shoot Away flyer: separated large projection screen and two-shotgun scoring stand, Namco America address. Explicitly a 1984 advertisement for the earlier machine format.',
        'Allied Clay Champ flyer: compact enclosed two-gun North American cabinet, correctly distinguished from the 1978 Japanese single-player format.'],
    limits=['Original 850 by 1101 scans retained without enlargement or invented open licence.',
        'No launch-day photograph claim; existing modern film remains unchanged.',
        'Native composition and scroll checks are recorded separately.'])
out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
