"""Admit the original publisher's clean Yue illustration after independent visual review."""
from pathlib import Path
import hashlib, json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
local = ROOT / 'build/research/cover-post2015/anmina-chara-01yue.png'
with Image.open(local) as im:
    im.load()
    assert im.size == (1146, 1576)
    assert 'transparency' in im.info or im.mode == 'RGBA'
record = {
    'url': 'https://www.gamecity.ne.jp/anmina/img/chara/chara-01yue.png',
    'source_page': 'https://www.gamecity.ne.jp/anmina/chara01_yue.html',
    'title': 'Angelique Luminarise: Yue, original publisher character illustration',
    'caption': 'Original character artwork of Yue; not the retail package or the full cast.',
    'creator': 'Koei Tecmo / Ruby Party; character design by \u7d17\u4e0e\u30a4\u30c1 (Sayo Ichi)',
    'credit': 'Koei Tecmo / Ruby Party; character design: \u7d17\u4e0e\u30a4\u30c1 (Sayo Ichi)',
    'creator_credit_source': 'https://www.gamecity.ne.jp/anmina/products.html',
    'license': 'Original publisher and artist rights retained. No open licence claimed.',
    'width': 1146, 'height': 1576, 'story_paragraph': -1, 'cover_art': True,
    'recovery_local_source': local.relative_to(ROOT).as_posix(),
    'supersedes_urls': ['https://www.gamecity.ne.jp/anmina/img/og.png'],
    'identity_evidence': {
        'published_title': 'Angelique Luminarise', 'year': 2021,
        'subject': 'Yue, original game character',
        'edition': 'Original 2021 publisher character art; no later game or remake.',
        'artist_credit': 'Official products page explicitly credits character designer \u7d17\u4e0e\u30a4\u30c1.'
    },
    'visual_review': 'Actual native original viewed by author and independent parent reviewer. No platform branding; original integrated Japanese character quotation retained. Not box art or the complete cast. No image elements erased or enlarged.',
    'verification': {'sha256': hashlib.sha256(local.read_bytes()).hexdigest(),
                     'native_dimensions': [1146, 1576], 'no_upscale': True,
                     'reviewed_on': '2026-10-22',
                     'alpha_handling': 'Existing image bundler composites palette transparency onto white through RGBA; never expose hidden RGB.'}
}
path = ROOT / 'content/expansion/museum-preferred-game-covers-editorial-reviewed.json'
doc = json.loads(path.read_text(encoding='utf8'))
doc['entries']['wikipedia-67870471'] = record
path.write_text(json.dumps(doc, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
(ROOT / 'build/research/cover-post2015/angelique-clean-character-art-reviewed.json').write_text(
    json.dumps({'status': 'PASS_SOURCE_AND_INDEPENDENT_VISUAL_REVIEW',
                'entry_id': 'wikipedia-67870471', 'record': record,
                'rejected_alternatives': ['Publisher og.png includes Switch branding.',
                    'Treasure-box print preview has SAMPLE watermark; not admitted.']},
               ensure_ascii=True, indent=2) + '\n', encoding='utf8')
p = ROOT / 'build/research/cover-post2015/progress.json'
progress = json.loads(p.read_text(encoding='utf8'))
progress.update(resolved_source_overrides=57, remaining=0,
                note='57 source-reviewed clean alternatives; current assembled master still56 until next coordinated assembly. Artwork is admitted where original box art has platform branding.')
p.write_text(json.dumps(progress, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
print('57/57 clean-cover source replacements reviewed; final Angelique artwork awaits next assembly.')
