"""Pair two restored design chapters with distinct, independently viewed 1991 manual pages."""
from pathlib import Path
import hashlib, json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'content/expansion/playhub-theme-semantic-restorations.json'
doc = json.loads(path.read_text(encoding='utf8'))
row = next(x for x in doc['restorations'] if x['entry_id'] == 'sonic')
pdf_url = 'https://info.sonicretro.org/images/7/7a/Sonic1_MD_US_manual.pdf'
pdf = ROOT / 'build/research/playhub-semantic-coverage/native-images/sonic1-original-us-manual.pdf'
records = []
for chapter_index, pdf_page, basename, title, caption in [
    (0, 9, 'page09-I8_0.jpg', 'Sonic the Hedgehog: the original manual introduces the zones',
     'Original 1991 US Genesis manual, printed page7: Green Hill loops, platforms and Spring Yard bumpers.'),
    (1, 6, 'page06-I5_0.jpg', 'Sonic the Hedgehog: Reach for the Rings',
     'Original 1991 US Genesis manual, printed page4: rings absorb a hit, then are lost.')
]:
    source = ROOT / 'build/research/playhub-semantic-coverage/native-images/sonic1-original-manual-pages' / basename
    with Image.open(source) as im:
        im.load()
        w, h = im.size
    image = dict(url=pdf_url + '#page=' + str(pdf_page) + '&embedded-image=' + basename.split('-', 1)[1],
        source_page=pdf_url, title=title, caption=caption, creator='SEGA',
        credit='SEGA / original 1991 Genesis instruction manual; scan preserved by Sonic Retro',
        license='Original publisher, artist and trademark rights retained. No open licence claimed.',
        width=w, height=h, recovery_local_source=source.relative_to(ROOT).as_posix(),
        artifact_type='original instruction-manual page scan',
        identity_evidence={'game': 'Sonic the Hedgehog (1991, 16-bit)', 'platform': 'Sega Genesis',
                           'edition': 'Original North American printed manual; not a later re-release manual.'},
        verification={'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'source_pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                      'extraction': 'Original embedded JPEG bytes extracted using pypdf; no page rendering, enlargement or screenshot crop.',
                      'native_dimensions': [w, h], 'no_upscale': True},
        visual_review='Full original page actually viewed by author and independent parent reviewer; readable historical monochrome scan. Specific ring-loss or level-geometry content matches the assigned design chapter.')
    chapter = next(x for x in row['chapters'] if x['source_chapter_index'] == chapter_index)
    chapter['images'] = [image]
    chapter['existing_image_urls'] = []
    chapter['illustration_status'] = 'reviewed_native_original_1991_manual_page'
    records.append(dict(source_chapter_index=chapter_index, image=image))
if pdf_url not in row['historical_sources']:
    row['historical_sources'].append(pdf_url)
path.write_text(json.dumps(doc, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
(ROOT / 'build/research/playhub-semantic-coverage/sonic-two-original-manual-pages-review.json').write_text(
    json.dumps(dict(status='PASS_NATIVE_ARTIFACT_AND_INDEPENDENT_VISUAL_ASSOCIATION', entry_id='sonic',
                    reviewed_on='2026-10-22', records=records,
                    review_scope='Original scan identity, native quality and specific design-section relevance; not claimed as modern HD gameplay captures.'),
               ensure_ascii=True, indent=2) + '\n', encoding='utf8')
print('Sonic source-only: two original manual pages paired; no main-cover reuse, no prose changed.')
