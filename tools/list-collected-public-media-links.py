"""List ordinary published image and item links for source review."""
from html.parser import HTMLParser
from pathlib import Path
import json
import sys

class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        item = dict(attrs)
        if tag == 'a' and any(term in item.get('href', '') for term in ('asset/', '.jpg', '.png', '.webp', '/flyer/')):
            rows.append(item)
        if tag == 'meta' and item.get('property') == 'og:image':
            rows.append(item)

for arg in sys.argv[1:]:
    rows = []
    Links().feed(Path(arg).read_text(encoding='utf8'))
    print(json.dumps(dict(file=arg, links=rows)))
