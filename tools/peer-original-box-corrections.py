"""Independent local-asset and frozen-catalogue audit; never edits authoring data."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/modern-game-cover-visual-qa'
FILES = ['four-classic-original-box-corrections-candidate.json',
         'eight-original-edition-box-corrections-candidate.json']
EXPECTED = ['b4d28682eb2e604ce82629a21b549813f8df23c7913b282ad1cd093dc32f3ee6',
            '28cd3a9d9af0fa9e4927bde6a1e15289dd8c86d3e1fd140095504aea4c221bb9']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
catalog_path = ROOT / 'content/catalog.json'
catalog_sha = sha(catalog_path)
catalog = json.loads(catalog_path.read_text(encoding='utf8'))
entries = {e['id']: e for e in catalog['entries']}
NOTES = {
 'workbook-11-30-excitebike': 'Original North American NES black-box artwork, Nintendo REV-A printing. Correct original game, without asserting the first Japanese 1984 printing. Authored pixel artwork is intentional.',
 'workbook-10-23-super-mario-bros-3': 'Original North American yellow NES Super Mario Bros. 3 box artwork, Raccoon Mario. Regional later packaging is not presented as the first Japanese 1988 printing.',
 'workbook-11-24-sonic-the-hedgehog-2': 'Japanese Mega Drive 16-bit packaging with Sonic and Tails, Sega and Mega Drive Cartridge marks. Not the distinct Game Gear game.',
 'wikipedia-1261600': 'Japanese Mega Drive Gunstar Heroes artwork and title. Replaces the unrelated collective Mega Play advertisement.',
 'wikipedia-2165811': 'Japanese Sega Saturn Grandia package with ESP/Game Arts marks and a visible 1998 award sticker. Later printing is already explicitly qualified, not misrepresented as a first 1997 print.',
 'wikipedia-618559': 'Japanese Dreamcast Grandia II package, Game Arts marks, genuine scanned physical wear. No HD-remaster branding.',
 'katamari-damacy': 'Original Japanese PlayStation 2 NTSC-J Katamari Damacy cover with Namco mark, cow and katamari artwork. No Reroll branding; no first-print claim.',
 'workbook-10-30-grim-fandango': 'Original LucasArts Windows Grim Fandango front artwork, with no Remastered branding. Native 670 by 800 is honestly recorded but limited for a large 4K cover.',
 'wikipedia-7840': 'Original Japanese PlayStation Chrono Cross front, Squaresoft and product number SLPS 02364-5 visible. Not the Radical Dreamers Edition or rejected custom SLUS00000 layout. Native 715 square remains limited for a large 4K cover.',
 'wikipedia-206199': 'Original Japanese Dreamcast Sonic Adventure cover, Sega/Sonic Team marks. No DX/Director\'s Cut branding.',
 'wikipedia-638452': 'Original Age of Empires II: The Age of Kings title and artwork. This source is cover artwork without complete physical-package furniture; do not call it an untrimmed package scan.',
 'wikipedia-8569': 'Original Duke Nukem 3D cover artwork, original logo and 8-player badge. The promotional tagline Total Meltdown alone does not identify the distinct PlayStation edition. No World Tour or Atomic branding.'
}
LIMITED = {'workbook-10-30-grim-fandango', 'wikipedia-7840'}
rows, sources = [], []
for filename, expected in zip(FILES, EXPECTED):
    p = BASE / filename
    if expected:
        assert sha(p) == expected, filename
    expected = sha(p)
    c = json.loads(p.read_text(encoding='utf8'))
    assert c['catalog_sha256'] == catalog_sha
    sources.append({'path': p.relative_to(ROOT).as_posix(), 'sha256': expected})
    for eid, r in c['entries'].items():
        e, im = entries[eid], r['image']
        current = e['images'][e.get('preferred_image', 0)]['url']
        assert current == r['supersedes_preferred_url'], eid
        local = ROOT / im['recovery_local_source']
        digest = sha(local)
        assert digest == im['verification']['sha256'], eid
        with Image.open(local) as decoded:
            decoded.load()
            dimensions = list(decoded.size)
            assert dimensions == [im['width'], im['height']] == im['verification']['native_dimensions']
        assert im['url'].rsplit('/', 1)[1] == local.name
        assert im['cover_art'] is True and im['verification']['no_upscale'] is True
        assert im['license'] and im['source_page'] and im['creator']
        corrections = {}
        if eid == 'wikipedia-638452' and im['title'] != 'Age of Empires II: The Age of Kings original box artwork':
            corrections = {'image.title': 'Age of Empires II: The Age of Kings original box artwork'}
        rows.append({'entry_id': eid, 'entry_title': e['title'], 'status':
                     'PASS_NATIVE_LIMITATION_APPROVED' if eid in LIMITED else
                     'PASS_WITH_REQUIRED_METADATA' if corrections else 'PASS',
                     'image_url': im['url'], 'local_file': im['recovery_local_source'],
                     'sha256': digest, 'native_dimensions': dimensions,
                     'supersedes_preferred_url': current, 'preferred_url_matches_master': True,
                     'native_image_read_in_full': True, 'identity_review': NOTES[eid],
                     'required_metadata': corrections,
                     'raw_database_release_date': im['identity_evidence'].get('ReleaseDate'),
                     'date_policy': 'Keep the current catalogue date; raw database regional dates are not timeline corrections.'})
assert len(rows) == len({r['entry_id'] for r in rows}) == 12
assert len({r['sha256'] for r in rows}) == 12
out = {'schema_version': 1, 'publication_status': 'INDEPENDENT_REVIEW_COMPLETE',
       'source_catalog_sha256': catalog_sha, 'source_catalog_entries': len(entries),
       'candidate_sources': sources, 'entries': rows,
       'ready_pass_ids': [r['entry_id'] for r in rows if r['status'].startswith('PASS') and not r['required_metadata']],
       'metadata_correction_ids': [r['entry_id'] for r in rows if r['required_metadata']],
       'native_quality_limitation_ids': sorted(LIMITED),
       'rights_review': 'Original artwork and publisher copyrights are retained explicitly. No invented open licence or individual artist identity.',
       'scope': 'Independently viewed all 12 full native images. Verified local bytes/dimensions, distinct content and exact replacement URL against frozen SOURCE71. No live origin availability test or new network retrieval.',
       'native_limitation_decision': 'Parent explicitly admitted Grim Fandango and Chrono Cross as original-edition corrections with their actual native-resolution limits. No high-resolution claim; better sources remain desirable.',
       'limits': ['Original regional packaging may be a later printing; catalogue release dates remain unchanged.',
                  'Grim Fandango 670x800 and Chrono Cross 715x715 are identity-correct, but are not high-resolution/4K masters. Preserve those native limits and do not label them HD.',
                  'No pixel upscaling, image edits, catalogue writes or deployment performed.'],
       'master_modified': False}
target = BASE / 'independent-twelve-original-box-corrections-review.json'
target.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'path': target.relative_to(ROOT).as_posix(), 'sha256': sha(target),
                  'pass': len(out['ready_pass_ids']), 'metadata': len(out['metadata_correction_ids']),
                  'limited': len(LIMITED)}))
