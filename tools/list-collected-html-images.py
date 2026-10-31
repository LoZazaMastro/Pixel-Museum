"""List published image elements in collected HTML without dumping page prose."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('files',nargs='+',type=Path)
args=parser.parse_args()
class Images(HTMLParser):
    def handle_starttag(self,tag,attrs):
        item=dict(attrs)
        if tag=='img' and item.get('src'):
            rows.append({k:item[k] for k in ['src','alt','width','height','srcset'] if k in item})
for path in args.files:
    rows=[]
    Images().feed(path.read_text(encoding='utf8'))
    print(json.dumps(dict(file=path.as_posix(),images=rows)))
