"""Inspect exact database identities for the final small-game image gaps."""
from pathlib import Path
import json,re,unicodedata,xml.etree.ElementTree as ET,zipfile
ROOT=Path(__file__).resolve().parents[2];FOLDER=ROOT/'build/research/launchbox'
def norm(text):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower())
games={};images={}
with zipfile.ZipFile(FOLDER/'Metadata-range.zip') as archive,archive.open('Metadata.xml') as stream:
    for _,item in ET.iterparse(stream,events=('end',)):
        if item.tag=='Game':
            game={c.tag:c.text or '' for c in item};item.clear();name=norm(game.get('Name',''))
            if any(term in name for term in ('pokemonyellow','americasarmy','fantasywest','honorofkings','magiccatacademy','angeliqueluminar')):
                games[game['DatabaseID']]=game
        elif item.tag=='GameImage':
            image={c.tag:c.text or '' for c in item};item.clear()
            if image.get('DatabaseID') in games:images.setdefault(image['DatabaseID'],[]).append(image)
result={'games':games,'images':images};(FOLDER/'last-commercial-candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([(i,g['Name'],g.get('ReleaseDate'),g.get('Platform'),len(images.get(i,[]))) for i,g in games.items()],ensure_ascii=False,indent=2))
