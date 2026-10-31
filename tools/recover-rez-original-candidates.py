"""Select exact original Rez packaging, excluding the later Infinite edition."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'build/research/launchbox'
games={};images=[]
with zipfile.ZipFile(folder/'Metadata-range.zip')as archive,archive.open('Metadata.xml')as stream:
    for _,node in ET.iterparse(stream,events=('end',)):
        if node.tag=='Game':
            row={child.tag:child.text or ''for child in node};node.clear()
            if row.get('Name','').lower()=='rez' and row.get('Platform')in['Sega Dreamcast','Sony Playstation 2','Sony PlayStation 2']:
                games[row['DatabaseID']]=row
        elif node.tag=='GameImage':
            row={child.tag:child.text or ''for child in node};node.clear()
            if row.get('DatabaseID')in games and row.get('Type')in['Box - Front','Box - Back','Advertisement Flyer - Front']:
                images.append(row)
doc={'games':games,'images':images}
(folder/'rez-original-candidates.json').write_text(json.dumps(doc,ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print(json.dumps({'games':len(games),'images':len(images),'fronts':[r for r in images if r['Type']=='Box - Front']},indent=2))
