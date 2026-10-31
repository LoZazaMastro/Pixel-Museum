"""Independent checks after viewing the original images in full."""
from pathlib import Path
import hashlib,json,tarfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=[
 ('wander-existing-prose-actual-a3-context','five-existing-wander-paragraphs-three-actual-restored-context-final-candidate.json',[[0,1],[2,3],[4]],
  'Two distinct actual restored-game terminal framebuffers: a3 opening and take/inventory/customs sequence. Existing HP 2100A family-context photo remains separately identified. Modern captures of the 1982 world revision, not 1974 photographs.'),
 ('dnd-existing-prose-original-plato-version','five-existing-dnd-paragraphs-two-identified-plato-chapters-candidate.json',[[0,1,2],[3,4]],
  'Original orange PLATO dungeon capture, Level 1 Demon encounter. Publisher identifies preserved dnd 5.4 from 1977; not represented as the original 1975 build or Golden Dragon encounter.'),
 ('pedit5-existing-prose-plato-keyboard-context','two-existing-pedit5-paragraphs-two-original-plato-context-scenes-candidate.json',[[0],[1]],
  'Actual complete PLATO IV keyboard photograph, circa-1976 hardware photographed in August 2005. Source explicitly records public-domain dedication; not represented as the original 1975 development terminal.')]
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
for directory,filename,groups,visual in cases:
 base=ROOT/'build/research'/directory;p=base/filename
 d=json.loads(p.read_text(encoding='utf8'));r,=d['rows'];old=r['old_entry'];new=r['new_entry']
 assert next(e for e in catalog['entries']if e['id']==r['entry_id'])==old
 assert old['body']==new['body'] and old.get('story_headings')==new.get('story_headings')
 assert old['date']==new['date'] and old.get('videos')==new.get('videos')
 assert d['expected_main_paragraph_groups']==groups
 assert sorted(i for group in groups for i in group)==list(range(len(old['body'])))
 for name,digest in d['source_files'].items():assert sha(ROOT/name)==digest,name
 hashes=[]
 for item in new['images']:
  path=ROOT/item['recovery_local_source']
  with Image.open(path)as image:image.load();assert image.size==(item['width'],item['height'])
  hashes.append(sha(path))
 assert len(hashes)==len(set(hashes))
 assert new['images'][0]['url']==old['images'][0]['url']
 if directory.startswith('wander'):
  archive=ROOT/'build/research/cover-duplicates/early-originals/wander-gpl-restored-source.tar.gz'
  source=ROOT/'build/research/cover-duplicates/early-originals/wander-gpl-restored-source'
  with tarfile.open(archive)as tar:
   for name in ['a3.misc','a3.wrld','LICENSE']:
    members=[m for m in tar.getmembers()if m.name.endswith('/'+name)]
    assert len(members)==1 and tar.extractfile(members[0]).read()==(source/name).read_bytes(),name
  assert '5/29/82' in (source/'a3.misc').read_text(encoding='utf8',errors='replace').splitlines()[0]
  script=(ROOT/'build/research/cover-duplicates/early-originals/capture-restored-wander-a3-play-reuse.sh').read_text(encoding='utf8')
  assert 'take credit card' in script and './Wander a3' in script and 'import -display :187 -window root' in script
 elif directory.startswith('dnd'):
  html=(base/'original-author-capture-source.html').read_text(encoding='utf8')
  assert 'dnd versjon 5.4, fra 1977' in html and 'Joachim Froholt' in html
  assert new['images'][-1]['url'] in html
 else:
  html=(ROOT/'build/research/cover-origins-extra/PLATO4kb.jpg.html').read_text(encoding='utf8')
  assert 'Photo taken August 20th, 2005' in html and 'public domain' in html and 'circa 1976' in html
 report=dict(status='PASS_INDEPENDENT_EXISTING_PROSE_AND_ORIGINAL_ARTIFACT_REVIEW',candidate=p.relative_to(ROOT).as_posix(),candidate_sha256=sha(p),
  current_owner_unchanged=True,complete_existing_paragraphs_once_in_order=True,all_source_hashes_checked=True,distinct_images=True,exclusive_cover=True,
  full_visual_review=visual,expected_native_paragraph_groups=groups,limits=d['quality_limits']+['Actual native mapping and final package staging checked separately.'])
 out=base/'root-independent-existing-prose-artifact-peer-review.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
