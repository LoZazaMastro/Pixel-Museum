"""Pair original Crash design chapters with distinct developer/manual/disc artifacts."""
from pathlib import Path
from urllib.parse import quote
import hashlib, json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'build/research/playhub-semantic-coverage/native-images/crash-developer'
path = ROOT / 'content/expansion/playhub-theme-semantic-restorations.json'
doc = json.loads(path.read_text(encoding='utf8'))
row = next(x for x in doc['restorations'] if x['theme_id'] == 'crash')
manual = 'https://psxdatacenter.com/manuals/' + quote('Crash Bandicoot [SCUS-94900] (E).cbr')
items = [
    (0, folder / 'crash_bandicoot1.jpg',
     'https://all-things-andy-gavin.com/wp-content/uploads/2011/02/crash_bandicoot1.jpg',
     'https://all-things-andy-gavin.com/2011/02/04/making-crash-bandicoot-part-3/',
     'Crash Bandicoot: looking along the original three-dimensional course',
     'Original-game screenshot published by co-creator Andy Gavin in his 2011 development retrospective.',
     'Naughty Dog / Universal Interactive / Sony Computer Entertainment; published by Andy Gavin',
     'Original game screenshot from developer retrospective; not the 2017 remake.'),
    (1, folder / 'manual-pages/SCUS-94900 pag12.jpg',
     manual + '#file=' + quote('SCUS-94900 pag12.jpg'),
     'https://psxdatacenter.com/manuals.html',
     'Crash Bandicoot: the original instruction manual explains the crates',
     'Original US PlayStation manual, printed page10: arrow, switch, TNT, checkpoint and bonus crates.',
     'Sony Computer Entertainment / Naughty Dog / Universal Interactive; scan preserved by PSX DataCenter (SPECIALT1212)',
     'Original 1996 SCUS-94900 manual-page scan, JPEG extracted without rendering or enlargement.'),
    (2, folder / 'original-artifacts/aa8ec861-a3f0-401f-977f-144c1c742325.png',
     'https://images.launchbox-app.com/aa8ec861-a3f0-401f-977f-144c1c742325.png',
     'https://gamesdb.launchbox-app.com/games/details/1006',
     'Crash Bandicoot: the original PlayStation CD-ROM',
     'The original North American SCUS-94900 disc, carrying the 1996 game and its streamed level data.',
     'Sony Computer Entertainment / Naughty Dog / Universal Interactive; scan catalogued by LaunchBox Games Database',
     'Original 1996 PlayStation SCUS-94900 game disc, not N. Sane Trilogy or a soundtrack disc.')
]
receipts = []
for index, local, url, source, title, caption, credit, identity in items:
    with Image.open(local) as im:
        im.load()
        width, height = im.size
    image = dict(url=url, source_page=source, title=title, caption=caption,
        creator='Sony Computer Entertainment / Naughty Dog / Universal Interactive',
        credit=credit, license='Original game, publisher, illustrator and trademark rights retained. No open licence claimed.',
        width=width, height=height, recovery_local_source=local.relative_to(ROOT).as_posix(),
        identity_evidence=dict(game='Crash Bandicoot', year=1996, platform='Original PlayStation', description=identity),
        verification=dict(sha256=hashlib.sha256(local.read_bytes()).hexdigest(), native_dimensions=[width, height], no_upscale=True),
        visual_review='Actually viewed full native file by author and independent parent reviewer; exact original edition and chapter relevance checked. Main cover is a different artifact.')
    chapter = next(x for x in row['chapters'] if x['source_chapter_index'] == index)
    chapter['images'] = [image]
    chapter['existing_image_urls'] = []
    chapter['illustration_status'] = 'reviewed_native_original_game_development_or_physical_artifact'
    receipts.append(dict(source_chapter_index=index, image=image))
for source in [items[0][3], items[1][3], 'https://www.naughtydog.com/blog/making_crash_bandicoot_by_andy_gavin_and_jason_rubin']:
    if source not in row['historical_sources']:
        row['historical_sources'].append(source)
path.write_text(json.dumps(doc, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
(folder / 'three-original-artifact-review.json').write_text(json.dumps(dict(
    status='PASS_NATIVE_ORIGINAL_ARTIFACT_AND_INDEPENDENT_VISUAL_ASSOCIATION', reviewed_on='2026-10-22',
    records=receipts, prose_unchanged=True,
    limitations=['Developer screenshot is delivered at1024x692; original low-resolution game rendering is apparent and not described as modern4K gameplay.',
                 'Manual and disc are historical scans with the original print texture retained; no restoration or enlargement.']),
    ensure_ascii=True, indent=2) + '\n', encoding='utf8')
print('Crash source-only: three distinct original artifacts paired with three intact chapters.')
