"""Save creator interview and museum publication for image identity review."""
from pathlib import Path
import hashlib
import json
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/carol-shaw-existing-prose-primary-illustrations'
BASE.mkdir(parents=True,exist_ok=True)
sources=[('strong-collection.html','https://www.museumofplay.org/blog/preserving-carol-shaws-trailblazing-video-game-career/'),
         ('shaw-interview.html','https://www.vintagecomputing.com/index.php/archives/800/vcg-interview-carol-shaw-female-video-game-pioneer-2'),
         ('strong-finding-aid.pdf','https://www.museumofplay.org/app/uploads/2022/01/Finding-Aid-to-the-Carol-Shaw-papers_013122.pdf'),
         ('river-raid-vcs-1982-manual.pdf','https://www.ataricompendium.com/archives/manuals/vcs/river_raid.pdf'),
         ('strong-shaw-artifacts-original.jpg','https://www.museumofplay.org/app/uploads/2021/08/Carol-Shaw-artifacts-002-1-scaled.jpg'),
         ('strong-carol-shaw-original.jpg','https://www.museumofplay.org/app/uploads/2021/08/CarolShaw-1-scaled.jpg'),
         ('strong-river-raid-original.jpg','https://www.museumofplay.org/app/uploads/2021/08/RiverRaid-002-1-scaled.jpg'),
         ('shaw-river-raid-box-1982.jpg','https://www.vintagecomputing.com/wp-content/images/interviews/shaw/carol_shaw_box_large.jpg'),
         ('polo-design-note-original.jpg','https://www.vintagecomputing.com/wp-content/images/interviews/shaw/polo_note_1_large.jpg'),
         ('river-raid-2600-original.png','https://www.vintagecomputing.com/wp-content/images/interviews/shaw/river_raid_2600_large.png'),
         ('river-raid-box-original.jpg','https://www.vintagecomputing.com/wp-content/images/interviews/shaw/river_raid_box_large.jpg')]
rows=[]
for name,url in sources:
    path=BASE/name
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'PixelMuseumResearch/1.0 (historical source review)'})
        with urllib.request.urlopen(request,timeout=45)as response:
            path.write_bytes(response.read())
    rows.append(dict(file=path.relative_to(ROOT).as_posix(),url=url,bytes=path.stat().st_size,
                     sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(BASE/'primary-pages.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
print(json.dumps(rows))
