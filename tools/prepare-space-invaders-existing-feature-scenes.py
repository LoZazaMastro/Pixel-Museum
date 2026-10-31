"""Pair four unchanged interview-based paragraphs with identified period media."""
from pathlib import Path
import copy
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/research/space-invaders-existing-prose-context'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
catalog = json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
old = next(e for e in catalog['entries'] if e['id']=='space-invaders')
new = copy.deepcopy(old)
feature = new['editorial_features'][0]
assert feature['id']=='feature-space-invaders-space' and len(feature['body'])==4
assert not feature['images']
feature['explicit_story_media_only'] = True
downloads = json.loads((BASE/'primary-pages.json').read_text(encoding='utf8'))
by_name = {Path(d['file']).name:d for d in downloads}
def media(name, source, title, caption, creator, credit, paragraph):
    p = BASE/name
    width, height = Image.open(p).size
    return dict(url=by_name[name]['url'], source_page=source,
                title=title, caption=caption, creator=creator, credit=credit,
                license='Original maker promotional or archival material; original rights retained. No open licence asserted.',
                width=width,height=height,story_paragraph=paragraph,
                recovery_local_source=p.relative_to(ROOT).as_posix(),
                verification=dict(sha256=sha(p),native_dimensions=[width,height],
                                  processing='Published source image retained byte-for-byte; no crop, enhancement or local enlargement.',
                                  source_identity_reviewed=True))
feature['images'] = [
    media('taito-gameplay-published-large-preview.jpg',
          'https://artsandculture.google.com/asset/space-invaders-ingame-screen-taito/wwEfnzrvs-tYow',
          'The original Space Invaders formation',
          'TAITO identifies this as the colour in-game screen of the original 1978 Space Invaders. The formation illustrates the playing field; this is not a capture of the Nagoya attack itself.',
          'TAITO','TAITO CORPORATION / original Space Invaders, 1978',0),
    media('taito-1978-flyer-original.jpg',
          'https://flyers.arcade-museum.com/videogames/show/980',
          'Space Invaders in its original American sales flyer',
          'The 1978 American Midway sales flyer preserved by the International Arcade Museum, showing the original cabinet and familiar alien figures. It is a promotional artefact, not a photograph of Nishikado or his light-pen development tool.',
          'Midway Manufacturing / TAITO',
          'Midway Manufacturing / TAITO, 1978 / International Arcade Museum',2),
    media('taito-invader-house-published-large-preview.jpg',
          'https://artsandculture.google.com/asset/inside-of-the-so-called-invader-house-5-taito/FAGr_KSCgnsgIA',
          'Playing around the table cabinet in 1979',
          'An Invader House filled with table cabinets, dated 1979 in TAITO\'s own archive. The image illustrates the period\'s social setting; the people and venue are not identified as Yoichi Wada or his particular cafe.',
          'TAITO','TAITO CORPORATION / Invader House, 1979',3),
]
assert new['body']==old['body'] and new['images']==old['images']
assert feature['body']==old['editorial_features'][0]['body']
assert feature['story_headings']==old['editorial_features'][0]['story_headings']
files = [BASE/d['file'].split('/')[-1] for d in downloads]
out = BASE/'four-existing-invaders-feature-paragraphs-three-period-scenes-candidate.json'
doc = dict(schema_version=1,status='CANDIDATE_PENDING_INDEPENDENT_PEER',
           rows=[dict(entry_id=old['id'],old_entry=old,new_entry=new)],
           source_files={p.relative_to(ROOT).as_posix():sha(p) for p in files},
           expected_feature_paragraph_groups=[[0,1],[2],[3]],
           scope='Only illustrate four existing feature paragraphs. Main prose, cover, film, music and experiences remain unchanged.',
           quality_limits=['The maker archive publishes 1200-pixel previews, not 4K originals. The exact observed s1200 URLs are saved in the source HTML.',
                           'The museum flyer is an original 850 by 1096 scan. Its visible Midway American branding is credited explicitly.',
                           'No photograph of the light pen, Nagoya technique, Wada himself or a specific cafe is claimed.',
                           'All three illustrations retain maker rights; no CC or public-domain licence is invented.'])
out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidate=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
