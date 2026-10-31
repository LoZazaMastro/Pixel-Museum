"""Build a reviewed-source candidate; never mutate the assembled catalog."""
from pathlib import Path
import json, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/getaway-black-monday-illustrated'
OUT = BASE / 'selected-native'
OUT.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf8'))
entry = next(e for e in catalog['entries'] if e['id'] == 'wikipedia-1531116')
inventory = json.loads((BASE / 'press-native-image-inventory.json').read_text(encoding='utf8'))
archive = 'https://archive.org/details/the-getaway-bm-press-disc'
disk = 'https://hiddenpalace.org/Assets/The_Getaway%3A_Black_Monday/Press_Disk'

# Retain the useful Wikipedia overview and mechanics; replace five consecutive
# plot summaries with concrete production/design topics from the primary kit.
body = entry['body'][:2] + [
    "Black Monday builds its action around a recognisable London. The publisher's original press material names Regent Street, Trafalgar Square and Piccadilly Circus, alongside routes beneath the city and along the Thames. Its map shows how streets, bridges and neighbourhoods connect. The city is both a setting for the crime story and a place the player crosses on foot or in a vehicle.",
    "The performances begin with actors rather than finished digital characters. The original press disc includes photographs of performers wearing motion-capture equipment, with tracking markers and head-mounted microphones visible. Its production notes describe magnetic and optical capture and facial animation. These photographs show part of that process; the equipment and people remain visible before their movements become a scene in the game.",
    "Cars and motorcycles share the streets with the characters. The sequel adds motorcycles and revises vehicle dynamics and damage, while its missions combine driving with action on foot. A production photograph shows two performers seated in a simple capture rig. It is a useful contrast with the finished street scenes: a few physical supports give the actors a position to work from before the surrounding vehicle and city appear on screen.",
    "The music combines an original orchestral score with urban remixes. The contemporary press sheet names Ninja Tune artists Amon Tobin, Diplo, Blockhead and Lotek. The press disc also includes photographs from an orchestral recording session: musicians, stands, microphones and a mixing desk. Together these materials show two sides of the game's sound, the recorded ensemble and the electronic contributions, without confusing the musicians with the fictional characters.",
    "The crime story is told through different characters over a 48-hour period. Mitch is a police officer returning to duty; Eddie is a boxer caught up in a bank robbery; Sam is a thief whose missions emphasise avoiding confrontation. Choices lead to different routes and endings. Beyond the main story, the press material also describes free roaming, street racing, taxi driving and a tourist mode, giving players other ways to revisit the city."
]
headings = ['A London crime story', 'Three approaches to action', 'Building the city',
            'Capturing the performances', 'Driving through London',
            'Orchestra and Ninja Tune', 'Three lives, different routes']
plans = [
    (None, 3, 'Original English PAL cover', 'Original English-language PlayStation 2 cover artwork supplied on the 2004 press disc.', True),
    (0, 39, 'Action among London traffic', 'A pre-release promotional game image supplied on the original Black Monday press disc.', False),
    (1, 47, 'Sam climbing above another character', 'Sam climbs above another character in an original Black Monday promotional game image.', False),
    (2, 7, 'The Black Monday London map', 'The London street map supplied with the original Black Monday press materials.', False),
    (3, 9, 'Performers in the capture studio', 'Motion-capture equipment and performers in a production photograph from the Black Monday press disc. Individual performers are not identified here.', False),
    (4, 11, 'A vehicle scene in the capture rig', 'Two performers seated in a capture rig, from the original production-photo collection. This is a studio photograph, not a rendered car interior.', False),
    (5, 28, 'An orchestral recording session', 'Musicians and recording equipment in the orchestral-session folder of the original Black Monday press disc. No unverified conductor or studio identification is supplied.', False),
    (6, 0, 'Eddie in the snooker room', 'Original promotional character render of Eddie, supplied in the press disc character-art folder. Artwork rather than a gameplay capture.', False),
]
images = []
for paragraph, index, title, caption, cover in plans:
    r = inventory[index]
    source = ROOT / r['local_file']
    assert sha(source) == r['sha256']
    image = Image.open(source)
    assert image.size == (r['width'], r['height'])
    if source.suffix.lower() in ('.bmp', '.tif', '.tiff'):
        target = OUT / (str(index) + '-' + source.stem.lower() + '.png')
        image.save(target)  # lossless native pixel conversion; no resizing/crop
        assert Image.open(target).tobytes() == image.tobytes()
    else:
        target = source
    item = dict(url=archive + '#press-file=' + r['path'], source_page=disk,
                title=title, caption=caption, width=r['width'], height=r['height'],
                creator='Sony Computer Entertainment Europe / London Studio / Team Soho',
                credit='Sony Computer Entertainment Europe / London Studio / Team Soho; original 2004 press materials',
                license='Original publisher, photographic, artwork and trademark rights retained. Archival press materials; no open licence claimed.',
                recovery_local_source=str(target.relative_to(ROOT)).replace('\\', '/'),
                cover_art=cover,
                verification=dict(sha256=sha(target), original_file_sha256=r['sha256'],
                                  original_iso_path=r['path'], native_dimensions=[r['width'], r['height']],
                                  no_upscaling=True, no_crop=True, visually_reviewed=True))
    if paragraph is not None:
        item['story_paragraph'] = paragraph
    images.append(item)
documents = []
for name in ['G2KEYFEA', 'THE_GETA']:
    original = BASE / 'press-assets' / (name + '.DOC')
    extract = BASE / (name + '-extracted.txt')
    documents.append(dict(original=str(original.relative_to(ROOT)).replace('\\', '/'),
                          sha256=sha(original), extracted_text=str(extract.relative_to(ROOT)).replace('\\', '/'),
                          extracted_text_sha256=sha(extract),
                          extraction='Word97 OLE WordDocument / Table CLX piece table, preserving compressed cp1252 and UTF16 pieces; no execution.'))
candidate = dict(schema_version=1, publication_status='independent_review_pending',
    entry_id=entry['id'], source_catalog_sha256=sha(ROOT/'content/catalog.json'),
    old_body_sha256=hashlib.sha256(json.dumps(entry['body'], ensure_ascii=False).encode()).hexdigest(),
    original_record=entry, body=body, story_headings=headings, images=images,
    replace_images=True, preferred_image=0,
    text_scope='Original Wikipedia introduction and mechanics retained verbatim. Five new short original descriptions paraphrase contemporary primary press notes and describe visible primary production photographs. Original plot paragraphs and Japanese packaging remain archived in original_record.',
    rights_scope='Wikipedia text keeps its existing CC BY-SA source and revision. New primary-source paraphrases are not claimed as verbatim Wikipedia. Publisher press images and documents are not claimed as openly licensed.',
    source_documents=documents,
    source_iso=dict(file=str((BASE/'original-2004-press-assets.iso').relative_to(ROOT)).replace('\\', '/'),sha256=sha(BASE/'original-2004-press-assets.iso')),
    additional_sources=[dict(title='The Getaway: Black Monday original 2004 press disc',url=archive,publisher='Sony Computer Entertainment Europe / London Studio / Team Soho; archived by Hidden Palace'),
                        dict(title='Original press disc preservation record',url=disk,publisher='Hidden Palace')],
    excluded_scope='No announced Getaway movie presented as released, no modern remake or first-game asset substitution, no invented actor identities, no claim that promotional screenshots are native PS2 frame-buffer captures or new 4K images.')
path = BASE / 'seven-illustrated-production-cards-candidate.json'
path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(path.relative_to(ROOT), sha(path))
