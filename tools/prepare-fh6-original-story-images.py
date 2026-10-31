"""Pair six distinct publisher originals with their existing narrative topics."""
from pathlib import Path
import json, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/research/fh6-illustrated-story'
rows = json.loads((BASE/'native-selected-images.json').read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
media_page = 'https://forza.net/media'
kyoko_page = 'https://news.xbox.com/ja-jp/2026/06/15/forza-horizon-6-japanese-sensibilities-interview-with-kyoko-yamashita/'
plans = [
    (0, 0, 'Tokyo beyond the hillside', 'Tokyo and the bay seen beyond a grassy hillside in the original 2026 publisher launch gallery.'),
    (1, 1, 'The Horizon Festival at night', 'Festival grounds and racing roads in the original publisher preview collection.'),
    (2, 2, 'A car inside a custom garage', 'A detailed car engine and garage interior in a publisher launch image. It illustrates the vehicle and garage customisation described in the accompanying text.'),
    (4, 3, 'The summer map of Horizon Japan', 'The official map reveal shows the connected road network, mountains and urban areas. This is the game map in its stated summer season, not a geographical map of real Japan.'),
    (5, 5, 'Cultural consultant Kyoko Yamashita', 'Kyoko Yamashita, identified in the publisher interview as the cultural consultant for Forza Horizon 6. This is a portrait, not a claim that the photograph was taken during a research trip.'),
    (6, 4, 'Light and detail on a Tokyo street', 'Original publisher PC-capture image of a Tokyo street. It illustrates the finished rendering; this single image is not a controlled ray-tracing on/off comparison or a claim about PS5 performance.'),
]
images = []
for paragraph, index, title, caption in plans:
    r = next(x for x in rows if x['index'] == index)
    file = ROOT/r['file']
    assert sha(file) == r['sha256']
    pic = Image.open(file)
    pic.load()
    assert pic.size == (r['width'],r['height'])
    images.append(dict(url=r['url'],title=title,caption=caption,story_paragraph=paragraph,
        width=r['width'],height=r['height'],source_page=kyoko_page if index==5 else media_page,
        creator='Xbox Game Studios / Playground Games; original publisher photographic and artwork contributors',
        credit='Xbox Game Studios / Playground Games / original publisher materials',
        license='Original publisher, photographic, artwork and trademark rights retained. No open licence claimed.',
        recovery_local_source=r['file'],
        verification=dict(sha256=r['sha256'],native_dimensions=[r['width'],r['height']],no_upscale=True,no_crop=True,visually_reviewed=True)))
candidate = dict(schema_version=1,publication_status='independent_review_pending',
    entry_id='wikipedia-81179631',images=images,
    story_headings=['Racing across Japan','The festival and its progression','Cars, garages and the Estate',
                    'Playground Games and its collaborators','Building Horizon Japan','Researching Japanese car culture','Lighting and rendering'],
    preserve_body=True,preserve_hero=True,
    source_receipts=[dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p)) for p in [BASE/'official-media-page.html',BASE/'official-media-page-payload.json',BASE/'native-published-urls.json']],
    primary_portrait_evidence=dict(url=kyoko_page,caption='Forza Horizon 6 cultural adviser Kyoko Yamashita',native_photo_url=next(r['url']for r in rows if r['index']==5),available_native_dimensions=[1333,2000]),
    remaining_gap=dict(story_paragraph=3,reason='No photograph of the development collaboration is admitted. The official Xbox developer podcast D5RIjzpGetg is currently login_required in the unsigned native player; its generic promotional thumbnail is not substituted for a studio photograph.'),
    scope='Six precise narrative illustrations, five native game/map publisher originals and a named consultant portrait. No whole-story illustration-completeness claim, no copied hero, no new film admitted, no change to text, dates, models or music.')
path=BASE/'six-original-narrative-images-candidate.json'
path.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(path.relative_to(ROOT),sha(path))
