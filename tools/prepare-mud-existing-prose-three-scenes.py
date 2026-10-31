"""Illustrate existing MUD prose with identified creators and historical hardware."""
from pathlib import Path
import copy
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/mud-existing-prose-primary-illustrations'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
by_id={e['id']:e for e in catalog['entries']}
old=by_id['mud']
new=copy.deepcopy(old)
assert len(old['body'])==2 and len(old['editorial_features'][0]['body'])==4
new['images'][0]['story_paragraph']=-1
new['explicit_story_media_only']=True
reunion=json.loads((BASE/'essex-2022-original-download.json').read_text(encoding='utf8'))
new['images'].append(dict(url=reunion['url'],source_page=reunion['source_page'],
    title='Roy Trubshaw, Nigel Roberts and Richard Bartle reunited at Essex',
    caption='Roy Trubshaw, Nigel Roberts and Richard Bartle at the 2022 Essex honorary-degree celebrations. The university identifies this as a later reunion, not a photograph of the original 1978 development.',
    creator='Photographer not identified in the university publication',
    credit='University of Essex / 2022 MUD pioneers reunion; original photographic rights retained',
    license='University publication photograph; original rights retained. No open licence asserted.',
    width=1000,height=1000,story_paragraph=0,recovery_local_source=reunion['file'],
    verification=dict(sha256=reunion['sha256'],native_dimensions=[1000,1000],no_upscale=True,
        context='Actual university image and named participants, explicitly dated 2022.')))

feature=new['editorial_features'][0]
assert not feature['images']
feature['explicit_story_media_only']=True
hardware=copy.deepcopy(next(i for i in by_id['wikipedia-261798']['editorial_features'][0]['images'] if i.get('story_paragraph')==2))
hardware.update(story_paragraph=0,title='A preserved DEC PDP-10 KI10 mainframe',
    caption='A preserved PDP-10-family computer illustrates the time-sharing hardware context. It is not identified as the original University of Essex computer or a screenshot of MUD.')
hardware['verification']['identity_scope']='Preserved PDP-10 hardware-family photograph; not the original Essex installation.'
feature['images'].append(hardware)
portrait=BASE/'essex-2017-richard-original.jpg'
feature['images'].append(dict(
    url='https://alumni.essex.ac.uk/file/essex-effect-2017.pdf#page=12&embedded=Im0.jpg',
    source_page='https://alumni.essex.ac.uk/file/essex-effect-2017.pdf',
    title='Richard Bartle in the 2017 Essex Effect interview',
    caption='The original portrait published beside Richard Bartle\'s 2017 account of MUD and his collaboration with Roy Trubshaw. This is a later interview photograph, not a 1978 image.',
    creator='Simon Rogers',credit='Simon Rogers / University of Essex, Essex Effect 2017',
    license='Original institutional publication photograph; rights retained. No open licence asserted.',
    width=629,height=1608,story_paragraph=2,
    recovery_local_source=portrait.relative_to(ROOT).as_posix(),
    verification=dict(sha256=sha(portrait),native_dimensions=[629,1608],no_upscale=True,
        source_pdf_sha256=sha(BASE/'essex-effect-2017.pdf'),pdf_page=12,printed_page=12,
        embedded_image='Im0.jpg',processing='Original embedded JPEG extracted byte-for-byte from the cited university PDF; no crop or enlargement.',
        credit_evidence='The same printed page explicitly credits PHOTO: SIMON ROGERS.')))

assert new['body']==old['body'] and new['story_headings']==old['story_headings']
assert feature['body']==old['editorial_features'][0]['body']
assert feature['story_headings']==old['editorial_features'][0]['story_headings']
paths=[BASE/'primary-source-downloads.json',BASE/'essex-effect-2017.pdf',
       BASE/'essex-2022-reunion.html',BASE/'essex-2022-original-download.json',
       ROOT/reunion['file'],portrait,ROOT/hardware['recovery_local_source']]
out=BASE/'six-existing-mud-paragraphs-three-contextual-scenes-candidate.json'
doc=dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
    rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
    source_files={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
    expected_main_paragraph_groups=[[0,1]],expected_feature_paragraph_groups=[[0,1],[2,3]],
    scope='Six existing main and feature paragraphs retained verbatim. Three distinct source-identified contextual illustrations; exclusive 2011 cover retained.',
    quality_limits=['No original 1978 gameplay image or Essex hardware photograph is claimed.',
        'University reunion photograph is 1000 square; portrait is a native 629 by 1608 embedded original, with no artificial enlargement.',
        'PDP-10 image is reused from the licensed local collection with its full native 2560-pixel file.',
        'Paired paragraphs share an image; no photograph-only cards or repeated picture.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
