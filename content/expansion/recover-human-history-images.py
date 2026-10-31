"""Acquire identified, attributed history artifacts from their public source files.

These are image overrides only. The history prose remains the English Wikipedia
extract and every downloaded file is decoded at its actual, unscaled resolution.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image
import hashlib, json

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'build/research/human-history'
OUTPUT = ROOT / 'content/expansion/human-history-official-images.json'

SELECTIONS = [
    {
        'subject': 'Macintosh 128K', 'file': 'macintosh-1984-gotfryd.jpg',
        'url': 'https://upload.wikimedia.org/wikipedia/commons/0/05/Macintosh_128k_computer%2C_January_1984%2C_by_Bernard_Gotfryd_-_%28cropped_to_remove_individual%29.jpg',
        'title': 'Macintosh 128K photographed in January 1984 by Bernard Gotfryd',
        'caption': 'The original Macintosh, January1984; a crop from Bernard Gotfryd’s contemporary photograph.',
        'creator': 'Bernard Gotfryd; restoration by Cart; crop by Pittigrilli',
        'license': 'Public domain / no known copyright restrictions (Library of Congress Gotfryd collection)',
        'license_url': 'https://www.loc.gov/rr/print/res/592_gotf.html',
        'source_page': 'https://commons.wikimedia.org/wiki/File:Macintosh_128k_computer,_January_1984,_by_Bernard_Gotfryd_-_(cropped_to_remove_individual).jpg',
        'original_source_page': 'https://hdl.loc.gov/loc.pnp/gtfy.01855',
        'source_review': 'Contemporary January1984 photograph. This existing Commons derivative crops the Macintosh from the original SteveJobs portrait; the2540-class pixel scan is not an enlargement. Actual file2530×2106.'
    },
    {
        'subject': 'Ethernet', 'file': 'ethernet-original-parc.jpg',
        'url': 'https://live.staticflickr.com/3007/2707600310_95b8310aa2_o.jpg',
        'title': 'Original Xerox PARC Ethernet coaxial cable and transceiver, Computer History Museum',
        'caption': 'Original Xerox PARC Ethernet hardware, photographed at the Computer History Museum in 2008.',
        'creator': 'Sascha Pohflepp', 'license': 'CC BY 2.0',
        'license_url': 'https://creativecommons.org/licenses/by/2.0/',
        'source_page': 'https://commons.wikimedia.org/wiki/File:Xerox_PARC_ethernet_cable.jpg',
        'original_source_page': 'https://www.flickr.com/photos/saschapohflepp/2707600310/sizes/o/',
        'source_review': 'Commons file description identifies original PARC Ethernet cable and confirms Flickr CC BY 2.0 review. Native original is 900 by 1200, not an enlarged mirror rendition.'
    },
    {
        'subject': 'Xerox Alto', 'file': 'alto.jpg',
        'url': 'https://history.itlibra.com/_img/images/events/xerox-alto-1973.jpg/1920.webp',
        'title': 'Xerox Alto I, 1973, in the Computer History Museum',
        'caption': 'An original-generation Xerox Alto I, photographed at the Computer History Museum in 2023.',
        'creator': 'The wub', 'license': 'CC BY-SA 4.0',
        'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'source_page': 'https://commons.wikimedia.org/wiki/File:Xerox_Alto_I,_1973,_Computer_History_Museum.jpg',
        'distribution_source_page': 'https://history.itlibra.com/en/events/xerox-alto-1973',
        'source_review': 'The Commons original is 4127 by 3302. This independently distributed, attributed CC BY-SA derivative decodes at 1280 by 1024; no enlargement is performed.'
    },
    {
        'subject': 'Compact disc', 'file': 'cd.jpg',
        'url': 'https://live.staticflickr.com/7528/15424957274_bb4bd06efe_o.jpg',
        'title': 'A prerecorded audio compact disc in its open jewel case',
        'caption': 'A later prerecorded audio CD and jewel case, photographed in 2014; not an original 1982 pressing.',
        'creator': 'Alan Levine (cogdogblog)', 'license': 'CC BY 2.0',
        'license_url': 'https://creativecommons.org/licenses/by/2.0/',
        'source_page': 'https://www.flickr.com/photos/cogdog/15424957274/',
        'licence_review_page': 'https://commons.wikimedia.org/wiki/File:Pre-Recorded_CD_in_open_jewel_case.jpg',
        'source_review': 'Original Flickr master, 5184 by 3456. Wikimedia Commons confirms the public CC BY 2.0 license and original photographer. The photo illustrates the physical audio-CD format, not a claim of 1982 provenance.'
    },
]

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    output = json.loads(OUTPUT.read_text(encoding='utf8')) if OUTPUT.exists() else {'schema_version': 1, 'entries': {}}
    receipts = []
    for selection in SELECTIONS:
        path = CACHE / selection['file']
        try:
            if not path.exists():
                request = Request(selection['url'], headers={'User-Agent': 'PixelMuseum archival image research https://github.com/LoZazaMastro'})
                path.write_bytes(urlopen(request, timeout=35).read())
            with Image.open(path) as image:
                image.load()
                width, height = image.size
            if max(width, height) < 800:
                raise ValueError('Source is below the admitted native-size floor; no enlargement allowed')
            record = {key: value for key, value in selection.items() if key not in ('subject', 'file')}
            record.update(width=width, height=height,
                credit=selection['creator'] + ' / ' + selection['license'],
                recovery_local_source=path.relative_to(ROOT).as_posix(), story_paragraph=0,
                verification={'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'native_dimensions': [width, height]})
            output['entries'][selection['subject']] = record
            receipts.append({'subject': selection['subject'], 'status': 'decoded', 'width': width, 'height': height})
        except Exception as error:
            receipts.append({'subject': selection['subject'], 'status': 'held', 'reason': str(error)})
    OUTPUT.write_text(json.dumps(output, ensure_ascii=True, indent=2) + '\n', encoding='utf8')
    (CACHE / 'identified-artifact-recovery.json').write_text(json.dumps(receipts, indent=2) + '\n', encoding='utf8')
    print(json.dumps(receipts, indent=2))

if __name__ == '__main__':
    main()
