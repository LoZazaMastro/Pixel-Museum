"""Freeze four viewed physical artifacts; no catalogue/manifest mutation."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/c64-loading-media'
rows=json.loads((OUT/'decoded-artifact-candidates.json').read_text(encoding='utf8'))
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf8'))
entry=next(e for e in catalog['entries'] if e['id']=='commodore-64')
feature=next(f for f in entry['editorial_features'] if f['id']=='feature-loading-screen-culture')
selections=[
    ('c8a88bdd',0,'Leviathan — English Software advertisement','Period advertising for Leviathan on the Commodore 64/128.',
     'English Software (original publisher); scan preserved by LaunchBox Games Database',
     'Original printed advertising shows the visual material surrounding the game whose loading-screen interpretation Docherty discusses. It is captioned as advertising, never falsely as his actual 320x200 loading picture.'),
    ('7835cde9',1,'Enlightenment: Druid II — Firebird box artwork','Firebird packaging for Enlightenment: Druid II on the Commodore 64/128.',
     'Firebird (original publisher); original box artwork credited to Alan Craddock by Lemon64; scan preserved by LaunchBox Games Database',
     'Same original sequel, visibly marked Commodore 64/128. This is printed box artwork, not a claim that Docherty authored the packaging; his exact original loading picture is preserved separately as an optional native-pixel artifact.'),
    ('07dd4a6d',2,'RoboCop — Ocean advertisement','Period Ocean advertising for RoboCop, one of the games illustrated in Hughes’s account of Freeload.',
     'Ocean Software (original advertisement/publisher); original licensed RoboCop artwork and other rights retained by their holders; scan preserved by LaunchBox Games Database',
     'Hughes’s own primary account displays the RoboCop loading picture and credits Stephen Ian Thomson. This high-resolution printed advertisement supplies period game context; it is not packaging, a loading-screen screenshot or a source-code photograph.'),
    ('gryzor-full',3,'Gryzor — The Hit Squad cassette inlay','The Hit Squad budget cassette inlay for Gryzor on the Commodore 64/128.',
     'Ocean Software/The Hit Squad (original packaging); stopXwhispering/RetroVideoGaming (physical collection scan)',
     'Actual budget cassette inlay visibly bears The Hit Squad logo, C64/128 strip and loading instructions. It illustrates the physical budget-release format, without asserting a particular tape master, pulse timing or cue from an image alone.'),
]
images=[]
for needle,paragraph,title,caption,creator,relevance in selections:
    row=next(r for r in rows if needle in r['url'])
    path=ROOT/row['recovery_local_source']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    assert row['source_width']>=800 and row['source_height']>=800
    images.append({key:row[key] for key in ('url','source_page','source_width','source_height','sha256','recovery_local_source')} |
        {'title':title,'caption':caption,'creator':creator,'license':'Copyright retained by original rights holders; archival physical artifact reproduction. No Creative Commons licence is asserted.',
         'story_paragraph':paragraph,'kind':'historical_artifact','preferred_image':False,
         'source_pixels_unchanged':True,'upscaled':False,'visually_reviewed':True,'relevance':relevance})
native=[]
for row in rows:
    if not row['name'].startswith('DOKK original native'):continue
    assert row['source_width']==320 and row['source_height']==200
    native.append({key:row[key] for key in ('url','source_page','source_width','source_height','sha256','recovery_local_source')} |
        {'creator':'Paul Docherty/DOKK','license':'Original image credited to Paul Docherty/DOKK; copyright remains with its original rights holders. Source is the artist’s retrospective gallery hosted by C64.com.',
         'status':'research_only_optional_native_pixel_art','historical_native_pixel_art':True,'upscaled':False,
         'quality_note':'The actual original 320x200 C64 artwork, not an HD scan. Do not claim HD or upscale; requires a deliberate historical-pixel-art presentation if admitted.'})
candidate={'schema_version':1,'publication_status':'awaiting_independent_review_not_admitted',
           'entry_id':'commodore-64','feature_id':feature['id'],'source_catalog_sha256':hashlib.sha256((ROOT/'content/catalog.json').read_bytes()).hexdigest(),
           'source_feature_body_sha256':hashlib.sha256(json.dumps(feature['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
           'images':images,'optional_exact_original_loading_art':native,
           'primary_sources':[{'url':s['url'],'title':s['title']} for s in feature['sources']],
           'additional_identity_sources':['https://www.c64.com/pictures/dokk_gallery/20.php','https://www.c64.com/pictures/dokk_gallery/10.php','https://www.lemon64.com/game/druid-2-enlightenment','https://retro-video-gaming.com/commodore-64-collection/'],
           'review_scope':'Four distinct native-resolution physical artifact scans, all visually inspected, one exact feature paragraph association each. No master, image manifest, runtime catalogue or package was changed. Rights are retained rather than invented as open licences.'}
path=OUT/'four-physical-artifacts-candidate.json'
path.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(path.relative_to(ROOT),hashlib.sha256(path.read_bytes()).hexdigest())
