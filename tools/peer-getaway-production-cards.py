"""Independent bounded source/image checks; never writes the candidate/catalogue."""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/getaway-black-monday-illustrated'
PATH = BASE / 'seven-illustrated-production-cards-candidate.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
c = json.loads(PATH.read_text(encoding='utf8'))
inventory = json.loads((BASE / 'press-disc-file-inventory.json').read_text(encoding='utf8'))
files = {r['path']: r for r in inventory['files']}
iso = ROOT / c['source_iso']['file']
assert sha(iso) == c['source_iso']['sha256'] == inventory['iso_sha256']
catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf8'))
original = next(e for e in catalog['entries'] if e['id'] == c['entry_id'])
assert sha(ROOT / 'content/catalog.json') == c['source_catalog_sha256']
assert original == c['original_record']
assert hashlib.sha256(json.dumps(original['body'], ensure_ascii=False).encode()).hexdigest() == c['old_body_sha256']
assert c['body'][:2] == original['body'][:2]
assert len(c['body']) == len(c['story_headings']) == 7
assert len(c['images']) == 8
assert [i['story_paragraph'] for i in c['images'] if 'story_paragraph' in i] == list(range(7))
assert c['preferred_image'] == 0 and c['images'][0]['cover_art']
assert 'story_paragraph' not in c['images'][0]
assert len({i['url'] for i in c['images']}) == 8
assert len({i['verification']['sha256'] for i in c['images']}) == 8

def check_iso_file(relative):
    row = files[relative]
    path = ROOT / row['local_file']
    with iso.open('rb') as f:
        f.seek(row['lba'] * 2048)
        data = f.read(row['bytes'])
    assert len(data) == row['bytes']
    assert hashlib.sha256(data).hexdigest() == row['sha256'] == sha(path)
    return path

images = []
for i in c['images']:
    v = i['verification']
    original_path = check_iso_file(v['original_iso_path'])
    path = ROOT / i['recovery_local_source']
    assert sha(path) == v['sha256']
    assert sha(original_path) == v['original_file_sha256']
    with Image.open(path) as a, Image.open(original_path) as b:
        assert a.size == b.size == (i['width'], i['height']) == tuple(v['native_dimensions'])
        assert a.mode == b.mode and a.tobytes() == b.tobytes()
        assert min(a.size) >= 996
    images.append(dict(story_paragraph=i.get('story_paragraph'), path=i['recovery_local_source'], sha256=sha(path), native_dimensions=[i['width'], i['height']], source_pixel_parity=True, visually_reviewed=True))

documents = []
for d in c['source_documents']:
    path = ROOT / d['original']
    assert check_iso_file(path.name) == path
    assert sha(path) == d['sha256']
    extract = ROOT / d['extracted_text']
    assert sha(extract) == d['extracted_text_sha256']
    documents.append(dict(path=d['original'], sha256=sha(path), extracted_text=d['extracted_text'], extracted_text_sha256=sha(extract), read_in_full=True))

corrections = []
sam = c['images'][2]
if 'corridor' in sam['title'].lower():
    corrections.append(dict(field='images[2].title', old=sam['title'], required='Sam climbing above another character', reason='Full native image shows a vertical shaft, not a corridor. Caption and paragraph association are otherwise appropriate.'))

evidence = [
    dict(paragraph=0, status='PASS', basis='Original Wikipedia overview retained verbatim; pre-release traffic promotional image fits the game overview. Not represented as native PS2 framebuffer output.'),
    dict(paragraph=1, status='PASS', basis='Original Wikipedia mechanics retained verbatim; Sam is visibly climbing above another character. Subject-specific title correction noted separately.'),
    dict(paragraph=2, status='PASS', basis='G2KEYFEA names Regent Street, Trafalgar Square, Piccadilly Circus, Underground and River Thames. Selected map visibly shows connected London streets, bridges and districts.'),
    dict(paragraph=3, status='PASS', basis='G2KEYFEA describes real actors, magnetic/optical capture and facial animation. Full photograph visibly shows markers, microphones and performers; no unverified personal names added.'),
    dict(paragraph=4, status='PASS', basis='G2KEYFEA explicitly adds motorcycles, revised vehicle damage/dynamics and mixed action/driving. DRIVE.JPG visibly shows the two seated performers and physical capture supports.'),
    dict(paragraph=5, status='PASS', basis='G2KEYFEA explicitly names original orchestral score and Ninja Tune artists Amon Tobin, Diplo, Blockhead and Lotek. Selected034 is an ensemble session photo; mixing desk is independently visible in the same press collection003. No unverified composer/conductor/studio identification.'),
    dict(paragraph=6, status='PASS', basis='THE_GETA describes48hours, Mitch returning to duty, Eddie/bank job and Sam/thief. G2KEYFEA supports multipath decisions/endings and free-roam/racing/taxi/tourist bonus modes. Eddie character artwork identified as promotional artwork, not gameplay.')
]
out = dict(schema_version=1, publication_status='PASS' if not corrections else 'REQUIRED_METADATA_CORRECTION', candidate_path=str(PATH.relative_to(ROOT)).replace('\\', '/'), candidate_sha256=sha(PATH), source_catalog_sha256=c['source_catalog_sha256'], entry_id=c['entry_id'], retained_original_record_exact=True, retained_wikipedia_paragraphs=[0,1], paragraph_count=7, illustrated_paragraph_count=7, distinct_image_count=8, source_iso_sha256=sha(iso), images=images, source_documents=documents, paragraph_review=evidence, required_corrections=corrections, readability_review='Seven specific short chapters replace five consecutive plot-dump paragraphs while preserving the factual introduction and mechanics. Primary descriptions and visible production artifacts remain clearly distinguished from Wikipedia quotations and game captures.', rights_review='Publisher photographic/artwork rights retained, no invented open licence. Existing Wikipedia revision/CC BY-SA attribution retained; new prose explicitly identified as original primary-source paraphrases.', limits=['Historical press game images have native1280px width, not new4K captures.', 'No physical PS5 loading/performance or final Screen composition claimed by this source peer.', 'The current paragraph1 retains the original Wikipedia grammar unchanged.'], master_modified=False)
target = BASE / 'independent-seven-production-cards-review.json'
target.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps(dict(path=target.relative_to(ROOT).as_posix(), sha256=sha(target), status=out['publication_status'], images=len(images), paragraphs=len(evidence))))
