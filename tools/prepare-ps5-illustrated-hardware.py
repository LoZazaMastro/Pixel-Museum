"""Consolidate repeated PS5 introductions and illustrate each distinct subject."""
from pathlib import Path
import copy, hashlib, json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/ps5-illustrated-hardware'
old = next(e for e in json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf8'))['entries'] if e['id'] == 'playstation-5')
sony = {r['name']: r for r in json.loads((BASE / 'native-sony-image-inventory.json').read_text(encoding='utf8'))}
blog = json.loads((BASE / 'source-image-inventory.json').read_text(encoding='utf8'))
astro = next(e for e in json.loads((ROOT / 'build/research/publishing/batch05/sony-probes.json').read_text(encoding='utf8')) if e['entry_id'] == 'wikipedia-64255520')['images'][2]
history = 'https://www.playstation.com/en-us/playstation-history/2020-ps5-ps-vr2/'
teardown = 'https://blog.playstation.com/2020/10/07/ps5-teardown-an-inside-look-at-our-most-transformative-console-yet/'
film_url = 'https://www.youtube.com/watch?v=CaAY-jAjm0w'

def picture(path, url, source_page, title, caption, paragraph, **extra):
    p = Path(path)
    p = p if p.is_absolute() else ROOT / p
    with Image.open(p) as im:
        im.load()
        w, h = im.size
    return dict(url=url, source_page=source_page, title=title, caption=caption,
                creator='Sony Interactive Entertainment / PlayStation',
                credit='Sony Interactive Entertainment',
                license='Copyright Sony Interactive Entertainment and respective creators; no open licence claimed.',
                license_url='', recovery_local_source=p.relative_to(ROOT).as_posix(),
                width=w, height=h, story_paragraph=paragraph, cover_art=False,
                verification=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(), no_upscale=True), **extra)

images = [copy.deepcopy(old['images'][old.get('preferred_image', 0)])]
images[0].update(cover_art=True, story_paragraph=-1)
images[0]['original_source_dimensions'] = [images[0].get('width'), images[0].get('height')]
images[0].update(width=1280, height=2318)
images.append(picture(sony['overview']['file'], sony['overview']['url'], history,
                      'The original PlayStation 5 and DualSense',
                      'Sony retrospective artwork showing the original disc-drive console and controller.', 0))
images.append(picture(BASE / 'launch-console.png', film_url + '&t=20', teardown,
                      'Yasuhiro Ootori demonstrates the original PS5',
                      'Sony hardware engineer Yasuhiro Ootori with the original console in the October 2020 teardown, before its November launch.', 1,
                      source_video_timestamp_seconds=20))
images.append(picture(BASE / 'ssd-333.jpg', film_url + '&t=333', teardown,
                      'The custom SSD controller',
                      'A close-up from Sony\'s original teardown labels the custom SSD controller and shows the surrounding storage chips; this is not the system-memory image.', 2,
                      source_video_timestamp_seconds=333))
images.append(picture(sony['controller']['file'], sony['controller']['url'],
                      'https://www.playstation.com/en-us/accessories/dualsense-wireless-controller/',
                      'DualSense wireless controller', 'The original white DualSense, shown in Sony\'s product photography.', 3))
images.append(picture(sony['audio']['file'], sony['audio']['url'],
                      'https://www.playstation.com/en-us/accessories/pulse-3d-wireless-headset/',
                      'PULSE 3D wireless headset',
                      'The original white PULSE 3D headset, a launch-era accessory for listening to PS5\'s spatial audio.', 4))
editions = next(x for x in blog if x.get('file', '').endswith('faq-00-PlayStation-FAQ-featured-image-Cropped.jpg'))
images.append(picture(editions['file'], editions['url'],
                      'https://blog.playstation.com/2020/11/09/ps5-the-ultimate-faq/',
                      'Two original launch editions',
                      'The original disc-drive and Digital Edition consoles, without later slim or Pro models.', 5))
images.append(picture(sony['compatibility']['file'], sony['compatibility']['url'], history,
                      'PS4 games in the PS5 library',
                      'Sony\'s retrospective screenshot shows the PS4 collection in the PS5 game-library interface.', 6))
images.append(picture(astro['local_research_path'], astro['url'],
                      'https://www.playstation.com/en-us/games/astros-playroom/',
                      'Astro\'s Playroom: platforming on PS5',
                      'A gameplay scene from the original preinstalled 2020 game. Original publisher capture label retained.', 7))

indices = [0, 2, 4, 5, 6, 7, 8, 9]
body = [old['body'][i] for i in indices]
# Remove a museum-status aside from the launch paragraph; keep its actual facts.
body[1] = body[1].split('Here they sit')[0].rstrip()
headings = ['PlayStation 5: storage, touch and sound', 'The November 2020 launch',
            'Storage that changes loading', 'DualSense: touch and resistance',
            'Tempest 3D AudioTech', 'Disc drive and Digital Edition',
            'Bringing the PS4 library forward', 'Astro\'s Playroom teaches through play']
source = dict(schema_version=1, publication_status='awaiting_independent_review', entry_id='playstation-5',
              body=body, story_headings=headings, summary=old['summary'], images=images,
              preferred_image=0, videos=copy.deepcopy(old.get('videos', [])), sources=copy.deepcopy(old['sources']) +
              [dict(title='PS5 teardown: original 2020 console and storage controller', url=teardown, publisher='Sony Interactive Entertainment'),
               dict(title='PULSE 3D: original headset', url='https://www.playstation.com/en-us/accessories/pulse-3d-wireless-headset/', publisher='Sony Interactive Entertainment'),
               dict(title='Astro\'s Playroom: original game screenshots', url='https://www.playstation.com/en-us/games/astros-playroom/', publisher='Sony Interactive Entertainment')],
              explicit_story_media_only=True, editorial_credit='', factual_note='',
              provenance=dict(previous_draft={k: copy.deepcopy(old.get(k)) for k in ['body', 'story_headings', 'images', 'sources']},
                              source_paragraph_indices=indices,
                              consolidation='Two overlapping introductory/edition paragraphs removed. Eight distinct subjects retained with their full existing historical explanations; only the launch museum-status aside removed.',
                              image_review='Root viewed all final stills. Frame318 describes GDDR6 and is excluded; actual SSD controller is frame333. Original white accessories only, no later Elite/Edge or console revisions. No main-block hero reused in story.',
                              native_source_properties='build/research/ps5-illustrated-hardware/native-sony-image-inventory.json'))
assert len(body) == 8
assert sorted(i['story_paragraph'] for i in images if i['story_paragraph'] >= 0) == list(range(8))
out = BASE / 'candidate.json'
out.write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(out.relative_to(ROOT), hashlib.sha256(out.read_bytes()).hexdigest())
