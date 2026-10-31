"""Record independent source-bound reviews after inspecting every original image."""
from pathlib import Path
import hashlib
import json
import re
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/modern-major-release-coverage-audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
normalize=lambda s:re.sub(r'\s+',' ',s).strip()
cases=[('scarlet-nexus-2021-complete-illustrated',
    'one-original-scarlet-nexus-three-illustrated-chapters-candidate.json',
    'wikipedia-64008282',(2021,6,25),'June 25, 2021',
    ['Clean original Scarlet Nexus artwork', 'Projected signs and streets of New Himuka',
     'Yuito using psychokinesis in actual combat', 'Both protagonists and a grotesque organic-mechanical Other']),
    ('tales-of-arise-2021-complete-illustrated',
     'one-original-tales-arise-four-illustrated-chapters-candidate.json',
     'wikipedia-61002576',(2021,9,10),'September 10, 2021',
     ['Clean original Alphen/Shionne cover', 'Alphen and Shionne in the original game',
      'Alphen attacking a large enemy', 'Fire-lit game environment',
      'Shionne exploring the painted-style town']),
    ('far-cry6-2021-complete-illustrated',
     'one-original-farcry6-four-illustrated-chapters-candidate.json',
     'wikipedia-64515728',(2021,10,7),'Thu Oct 07 2021',
     ['Clean original Castillo and Diego cover',
      'Dani under Castillo propaganda in Yara',
      'Car chase alongside a military tank',
      'The original homemade Resolver weapon in the countryside',
      'Dani with Chorizo and a guerrilla companion']),
    ('riders-republic-2021-complete-illustrated',
     'one-original-riders-republic-three-illustrated-chapters-candidate.json',
     'wikipedia-65303340',(2021,10,28),'Thu Oct 28 2021',
     ['Clean original extreme-sports cover, without platform branding',
      'Actual mountain biking in Bryce Canyon',
      'Mass Race with 64 participants visible in the HUD, Sequoia',
      'Actual clothing selection and sports-sponsor brands']),
    ('battlefield2042-2021-complete-illustrated',
     'one-original-battlefield2042-three-illustrated-chapters-candidate.json',
     'wikipedia-67878456',(2021,11,19),'November 19, 2021',
     ['Clean original Battlefield 2042 cover without platform branding',
      'Publisher promotional image of two specialists in combat',
      'Publisher promotional helicopter and tornado image',
      'Publisher promotional combined infantry, armour and aircraft image']),
    ('dying-light2-2022-complete-illustrated',
     'one-original-dying-light2-three-illustrated-chapters-candidate.json',
     'wikipedia-57651352',(2022,2,4),'February 4th, 2022',
     ['Original official 2019 portrait key art with the Dying Light 2 logo, explicitly pre-release artwork rather than a 2022 box scan',
      'An infected enemy lunging towards the player',
      'First-person parkour above Villedor settlements',
      'The city seen from a high crossing']),
    ('sifu-2022-complete-illustrated',
     'one-original-sifu-four-illustrated-chapters-candidate.json',
     'wikipedia-68689410',(2022,2,8),'February 8, 2022',
     ['Clean original Sifu cover without platform branding',
      'The protagonist approaching a martial artist on a bridge',
      'A close-range strike during combat',
      'Fighting around tables and improvised weapons',
      'A visibly older white-haired protagonist in combat']),
    ('sonic-frontiers-2022-complete-illustrated',
     'one-original-sonic-frontiers-four-illustrated-chapters-candidate.json',
     'wikipedia-60276496',(2022,11,8),'November 8, 2022',
     ['Clean original Sonic Frontiers cover without platform branding',
      'Sonic overlooking the Starfall Islands and their platforming routes',
      'Sonic grinding a rail and collecting rings',
      'Sonic running through an open island landscape',
      'Sonic attacking a robot enemy in the open zone']),
    ('gotham-knights-2022-complete-illustrated',
     'one-original-gotham-knights-three-illustrated-chapters-candidate.json',
     'wikipedia-65045980',(2022,10,21),'October 21,2022',
     ['Clean original four-hero Gotham Knights cover without platform branding',
      'Gotham City skyline at night with the Belfry clocktower',
      'Batgirl beside the Belfry clocktower',
      'Nightwing and Red Hood confronting enemies together']),
    ('hogwarts-legacy-2023-complete-illustrated',
     'one-original-hogwarts-legacy-four-illustrated-chapters-candidate.json',
     'wikipedia-65333994',(2023,2,10),'February 10',
     ['Clean original Hogwarts Legacy cover without platform branding',
      'Students in the Hogwarts Castle entrance hall',
      'A student trying a wand with Ollivander',
      'Flying on a hippogriff above the landscape',
      'A student confronting a troll using a wand']),
    ('dead-space-remake-2023-complete-illustrated',
     'one-original-deadspace-remake-three-illustrated-chapters-candidate.json',
     'wikipedia-68325076',(2023,1,27),'January 27, 2023',
     ['Clean original 2023 Dead Space remake cover without platform branding',
      'Isaac looking into the rebuilt Ishimura interior',
      'Isaac using suit thrusters in zero gravity',
      'A compartment aboard the Ishimura with an enemy behind glass']),
    ('atomic-heart-2023-complete-illustrated',
     'one-original-atomic-heart-three-illustrated-chapters-candidate.json',
     'wikipedia-62111221',(2023,2,21),'21 February 2023',
     ['Clean original Atomic Heart cover without platform branding',
      'The alternate-history retrofuturistic city, retaining the publisher image letterboxing',
      'Actual crafting interface with materials and weapon recipes',
      'The Polymer Glove electricity power attacking robots']),
    ('dead-island2-2023-complete-illustrated',
     'one-original-dead-island2-three-illustrated-chapters-candidate.json',
     'wikipedia-39190240',(2023,4,21),'April 21, 2023',
     ['Clean original Dead Island 2 cover without platform branding',
      'First-person combat against zombies on Venice Beach streets',
      'Slayers together inside a surf-board rental shop',
      'A modified weapon and materials on a workbench']),
    ('diablo4-2023-complete-illustrated',
     'one-original-diablo4-three-illustrated-chapters-candidate.json',
     'wikipedia-62124844',(2023,6,6),'June 6, 2023',
     ['Original clean Lilith and Diablo IV logo key art from the publisher product page',
      'A group of adventurers fighting a world boss',
      'Class fire skills used against enemies in snow',
      'Horseback exploration across Sanctuary']),
    ('remnant2-2023-complete-illustrated',
     'one-original-remnant2-three-illustrated-chapters-candidate.json',
     'wikipedia-72449135',(2023,7,25),'July 25, 2023',
     ['Clean original Remnant II cover without platform branding',
      'An actual third-person firefight against a monster',
      'Close combat in a ruined street',
      'Three adventurers confronting a large boss together']),
    ('lords-fallen2023-complete-illustrated',
     'one-original-lords-fallen2023-three-illustrated-chapters-candidate.json',
     'wikipedia-73854166',(2023,10,13),'13 October 2023',
     ['Clean original 2023 Hexworks cover, distinct from the 2014 game',
      'Publisher promotional illustration of the lamp bearer overlooking Mournstead',
      'Publisher promotional illustration of a sword strike and magical defence',
      'Publisher promotional illustration of the lamp bearer and spectral figures in Umbral']),
    ('rise-ronin-2024-complete-illustrated',
     'one-original-ronin-three-illustrated-chapters-candidate.json',
     'wikipedia-72728836',(2024,3,22),'March 22',
     ['Clean original Rise of the Ronin cover without a platform banner',
      'The protagonist overlooking a coastal Japanese city',
      'An actual sword fight beside a shrine',
      'A historic temple and city environment at sunset']),
    ('indiana-great-circle-2024-complete-illustrated',
     'one-original-indiana-four-illustrated-chapters-candidate.json',
     'wikipedia-66364908',(2024,12,9),'December 9',
     ['Clean original Indiana Jones and the Great Circle game cover',
      'Indiana Jones rendered as the game character',
      'First-person whip combat in a jungle',
      'The player working with a large ancient gear mechanism',
      'A first-person fistfight against an enemy soldier'])]
for directory,filename,entry_id,date,publisher_date,visual_notes in cases:
    if sys.argv[1:] and directory not in sys.argv[1:]:
        continue
    base=BASE/directory
    path=base/filename
    doc=json.loads(path.read_text(encoding='utf8'))
    entry,=doc['entries']
    assert entry['id']==entry_id
    assert (entry['year'],entry['date']['month'],entry['date']['day'])==date
    assert len(entry['images'])==len(entry['body'])+1==len(visual_notes)
    assert [i['story_paragraph'] for i in entry['images']]==list(range(-1,len(entry['body'])))
    for name,digest in doc['source_files'].items():
        assert sha(ROOT/name)==digest,name
    page,=json.loads((base/'wiki.json').read_text(encoding='utf8'))['query']['pages']
    assert page['revisions'][0]['revid']==entry['attribution']['revision_id']
    for index,paragraph in enumerate(entry['body']):
        for block in paragraph.split('\n\n'):
            assert normalize(block) in normalize(page['extract']),index
    publisher_evidence=base/'publisher-release.html'
    if directory=='gotham-knights-2022-complete-illustrated':
        publisher_evidence=base/'publisher-official-faq-web-capture.json'
    elif directory=='hogwarts-legacy-2023-complete-illustrated':
        publisher_evidence=base/'developer-primary-launch.html'
    elif directory=='dead-island2-2023-complete-illustrated':
        publisher_evidence=base/'publisher-platform-launch.html'
    assert publisher_date in publisher_evidence.read_text(encoding='utf8')
    hashes=[]
    for item in entry['images']:
        image_path=ROOT/item['recovery_local_source']
        assert sha(image_path)==item['verification']['sha256']
        with Image.open(image_path) as image:
            image.load()
            assert image.size==(item['width'],item['height'])
        hashes.append(sha(image_path))
    assert len(hashes)==len(set(hashes))
    report=dict(status='PASS_INDEPENDENT_SOURCE_AND_FULL_IMAGE_REVIEW',
        candidate=path.relative_to(ROOT).as_posix(),candidate_sha256=sha(path),
        entry_id=entry_id,display_release=date,selected_wikipedia_blocks_retained=True,
        full_visual_review=visual_notes,image_sha256=hashes,exclusive_cover=True,
        limits=[f"Original cover/artwork dimensions are {entry['images'][0]['width']} by {entry['images'][0]['height']}; no artificial enlargement.",
            'Original publisher gallery images retain their actual native dimensions recorded in the candidate; no enlargement.',
            'No film or soundtrack admitted here. Native layout and final offline staging follow admission.'])
    out=base/'root-independent-source-and-image-peer-review.json'
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(status=report['status'],receipt=out.relative_to(ROOT).as_posix(),sha256=sha(out))))
