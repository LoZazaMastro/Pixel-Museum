"""Collect exact article and publisher identities before splitting grouped games."""
from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('major',HERE/'major-release-additions.py');major=importlib.util.module_from_spec(spec);spec.loader.exec_module(major)
titles=['Vampire: The Masquerade - Night Road','Vampire: The Masquerade - Out for Blood','Vampire: The Masquerade - Parliament of Knives','9-Nine']
pages=major.api('https://en.wikipedia.org/w/api.php',{'action':'query','titles':'|'.join(titles),'redirects':1,'prop':'extracts|revisions|pageprops','explaintext':1,'exlimit':'max','rvprop':'ids|timestamp|content','rvslots':'main','ppprop':'wikibase_item'},'series-splits')
output={'wikipedia':pages,'steam':{}}
for title in titles:
    result=major.api('https://store.steampowered.com/api/storesearch/',{'term':title,'l':'english','cc':'us'},'steam-search')
    output['steam'][title]=result
for title in ['9-nine-:Episode 1','9-nine-:Episode 2','9-nine-:Episode 3','9-nine-:Episode 4']:
    output['steam'][title]=major.api('https://store.steampowered.com/api/storesearch/',{'term':title,'l':'english','cc':'us'},'steam-search')
path=ROOT/'build/research/major-releases/series-split-research.json';path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for page in pages.get('query',{}).get('pages',[]):print('WIKI',page.get('title'),page.get('pageid'),len(page.get('extract','')))
for title,result in output['steam'].items():print('STEAM',title,[(i.get('id'),i.get('name')) for i in result.get('items',[])[:4]])
