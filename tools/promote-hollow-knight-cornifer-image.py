"""Pair the cartography chapter with a verified original-game Cornifer capture."""
from pathlib import Path
import hashlib, json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'content/expansion/playhub-theme-semantic-restorations.json'
doc = json.loads(path.read_text(encoding='utf8'))
row = next(x for x in doc['restorations'] if x['theme_id'] == 'hollow')
local = ROOT / 'build/research/playhub-semantic-coverage/native-images/hollow-original/cornifer-fungal-wastes-original1920.png'
with Image.open(local) as im:
    im.load()
    assert im.size == (1920, 1080)
image = dict(
    url='https://cdn.wikimg.net/en/hkwiki/images/c/cd/Screenshot_HK_Cornifer_05.png',
    source_page='https://hollowknight.wiki/w/File:Screenshot_HK_Cornifer_05.png',
    title='Hollow Knight: Cornifer charts the Fungal Wastes',
    caption='Cornifer with his map and quill in the original game; capture uploaded by Sumwan in2019.',
    creator='Team Cherry',
    credit='Team Cherry / Hollow Knight; screenshot preserved by Sumwan, Hollow Knight Wiki (2019)',
    license='Original game art and publisher rights retained. Screenshot archive does not grant an open licence to the game imagery.',
    width=1920, height=1080, recovery_local_source=local.relative_to(ROOT).as_posix(),
    identity_evidence=dict(game='Hollow Knight', edition='Original game, not Silksong or an unofficial modification',
                           depicted_subject='Cornifer in the Fungal Wastes',
                           source_file_revision='https://hollowknight.wiki/mw/index.php?title=File:Screenshot_HK_Cornifer_05.png&oldid=79444'),
    verification=dict(sha256=hashlib.sha256(local.read_bytes()).hexdigest(), native_dimensions=[1920,1080], no_upscale=True),
    visual_review='Full native capture actually viewed by author and independent parent reviewer. The original cartographer, quill and map match the exact cartography chapter; not a charm menu, Shade Gate, unrelated boss or fan illustration.')
chapter = next(x for x in row['chapters'] if x['source_chapter_index'] == 0)
chapter['images'] = [image]
chapter['existing_image_urls'] = []
chapter['illustration_status'] = 'reviewed_native_original_game_cartography_capture'
path.write_text(json.dumps(doc, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
(local.parent / 'cornifer-independent-artifact-association-review.json').write_text(json.dumps(dict(
    status='PASS_NATIVE_CAPTURE_AND_INDEPENDENT_VISUAL_ASSOCIATION', reviewed_on='2026-10-22',
    entry_id=row['entry_id'], source_chapter_index=0, image=image,
    shade_chapter_still_pending=True, prose_unchanged=True), ensure_ascii=True, indent=2) + '\n', encoding='utf8')
print('Cornifer source-only chapter illustrated; Shade remains pending.')
