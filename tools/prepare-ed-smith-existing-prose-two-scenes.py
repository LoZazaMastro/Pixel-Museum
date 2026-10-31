"""Illustrate Ed Smith's existing prose with his period portrait and APF artifact."""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/ed-smith-existing-prose-primary-images'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old=next(e for e in catalog['entries'] if e['id']=='feature-ed-smith-apf')
new=copy.deepcopy(old)
assert len(old['body'])==4 and len(old['images'])==1
# The person becomes the exclusive cover. The console can now illustrate the prose.
new['images'][0]['story_paragraph']=0
downloads=json.loads((BASE/'observed-original-image-downloads.json').read_text(encoding='utf8'))
for name,paragraph,title,caption,creator,credit in [
    ('ed_smith_marbelite_large.jpg',-1,'Ed Smith at Marbelite, around 1975',
     'Ed Smith photographed at Marbelite around 1975, before his APF work. The published photograph retains its original caption and is not presented as a childhood repair scene.',
     'Photographer not identified; Ed Smith personal photograph published in his interview',
     'Ed Smith personal archive / interview published by Benj Edwards; original photographic rights retained'),
    ('imagination_machine_large.jpg',2,'The APF Imagination Machine in its original advertisement',
     'The original APF advertisement shows the console docked into the keyboard and cassette expansion described here. It is a contemporary product artifact, not a photograph of Ed Smith or his later book.',
     'APF Electronics','APF Electronics; historical advertisement preserved with the Ed Smith interview')]:
    row,=[r for r in downloads if r['file'].endswith('/'+name)]
    new['images'].append(dict(url=row['url'],source_page=row['source_page'],
        title=title,caption=caption,creator=creator,credit=credit,
        license='Original photographic or advertising rights retained. No open licence asserted.',
        width=row['native_dimensions'][0],height=row['native_dimensions'][1],
        story_paragraph=paragraph,portrait=paragraph==-1,
        recovery_local_source=row['file'],verification=dict(sha256=row['sha256'],
            native_dimensions=row['native_dimensions'],no_upscale=True,
            processing='Original published full-size linked image retained byte-for-byte; no regeneration, crop or enlargement.')))
new['preferred_image']=1
new['explicit_story_media_only']=True
assert new['body']==old['body'] and new['story_headings']==old['story_headings']
paths=[BASE/'about.html',BASE/'interview.html',BASE/'observed-primary-image-elements.json',
       BASE/'observed-original-image-downloads.json',BASE/'ed_smith_marbelite_large.jpg',
       BASE/'imagination_machine_large.jpg']
out=BASE/'four-existing-ed-smith-paragraphs-two-illustrated-scenes-candidate.json'
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
    expected_main_paragraph_groups=[[0,1],[2,3]],
    scope='Existing four complete paragraphs and headings unchanged. Person-first period portrait cover, console illustration and original expansion advertisement.',
    quality_limits=['Authentic Marbelite photograph is 852 by 1117 pixels; no 4K claim or artificial enlargement.',
        'Portrait cover is not repeated inside the article.',
        'A later book-cover image and smaller portraits were collected but held for inadequate native dimensions.',
        'Two complete paragraphs share each distinct image; no new prose written.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
