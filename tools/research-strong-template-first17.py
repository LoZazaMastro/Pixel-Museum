"""Cache public Wikipedia article bodies for the assigned source-only copy pass."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import hashlib
import json
import re
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/research/playhub-semantic-coverage/wiki-clarity/strong-first17'
OUT.mkdir(exist_ok=True)
TITLES = ['John Carmack', 'Donkey Kong (video game)', 'Gyromite',
          'Metroid (video game)', 'Starflight', 'Yume Kōjō: Doki Doki Panic',
          'Famicom Wars', 'Super Star Soldier', "Devil's Crush", 'Dr. Mario',
          'Shadow of the Ninja', 'Duke Nukem (video game)',
          'Donkey Kong (1981 video game)', 'Commander Keen', 'Doom (1993 video game)',
          'Quake (video game)']

class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.skip = 0
        self.parts = []
        self.paragraphs = []
    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.active = True
            self.parts = []
        if self.active and tag == 'sup': self.skip += 1
    def handle_endtag(self, tag):
        if tag == 'sup' and self.skip: self.skip -= 1
        if tag == 'p' and self.active:
            value = re.sub(r'\s+', ' ', ''.join(self.parts)).strip()
            if value: self.paragraphs.append(value)
            self.active = False
    def handle_data(self, data):
        if self.active and not self.skip: self.parts.append(data)

sources = {}
for n, title in enumerate(TITLES):
    path = OUT / ('wiki-' + str(n) + '.html')
    url = 'https://en.wikipedia.org/wiki/' + quote(title.replace(' ', '_'), safe='():')
    if not path.exists():
        try:
            with urlopen(Request(url, headers={'User-Agent': 'PixelMuseumEditorial/1.0 (source verification, no media download)'}), timeout=35) as response:
                body = response.read().decode('utf8')
        except HTTPError as error:
            if error.code != 429: raise
            print('RATE_LIMIT stop; no retry', title, flush=True)
            break
        path.write_text(body, encoding='utf8')
        time.sleep(1.1)
    html = path.read_text(encoding='utf8')
    article = re.search(r'"wgArticleId":(\d+)', html)
    revision = re.search(r'"wgRevisionId":(\d+)', html)
    if not article or not revision:
        raise ValueError('Not a valid actual article: ' + title)
    parser = Paragraphs()
    parser.feed(html)
    actual_title = re.search(r'"wgTitle":("(?:[^"\\]|\\.)*")', html)
    sources[title] = {'title': json.loads(actual_title.group(1)) if actual_title else title,
                     'requested_title': title, 'url': url,
                     'page_id': int(article.group(1)), 'revision_id': int(revision.group(1)),
                     'source_file': path.relative_to(ROOT).as_posix(),
                     'source_file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'paragraphs': parser.paragraphs}
    print(title, 'paragraphs', len(parser.paragraphs), 'revision', revision.group(1), flush=True)
(OUT / 'source-pages.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print('Sources', len(sources))
