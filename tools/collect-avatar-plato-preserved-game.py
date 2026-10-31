"""Collect an actual player's preservation-system capture and its publication context."""
from pathlib import Path
import urllib.request,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/research/avatar-plato-existing-intro-preservation-chapter';base.mkdir(parents=True,exist_ok=True)
rows=[]
for name,url in [('player-capture-publication.html','https://howtomakeanrpg.com/r/l/g/avatar/'),
 ('actual-preserved-game.png','https://howtomakeanrpg.com/img/avatar/basic_gameplay_1.png'),
 ('preservation-community-source.html','https://heavyharmonies.com/Avatar/')]:
 p=base/name
 if not p.exists():
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30)as r:p.write_bytes(r.read())
 rows.append(dict(file=p.relative_to(ROOT).as_posix(),url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(base/'source-downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(size=Image.open(base/'actual-preserved-game.png').size,sources=rows)))
