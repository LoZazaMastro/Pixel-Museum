"""Enrich longer major-game stories with exact publisher Steam screenshots."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,importlib.util,io,json,re
from datetime import datetime,timezone
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('major',HERE/'major-release-additions.py');major=importlib.util.module_from_spec(spec);spec.loader.exec_module(major)
path=HERE/'major-release-additions.json';module=json.loads(path.read_text(encoding='utf-8'))
targets=[e for e in module['entries'] if len(e['body'])>3 and len(e['images'])==1]
def enrich(entry):
    title=entry['title'];canonical=major.norm(title)
    try:found=major.api('https://store.steampowered.com/api/storesearch/',{'term':title,'l':'english','cc':'us'},'steam-search')
    except Exception:return title,0
    for item in found.get('items',[])[:8]:
        appid=str(item.get('id',''))
        if not appid.isdigit():continue
        try:meta=major.api('https://store.steampowered.com/api/appdetails',{'appids':appid,'l':'english'},'steam').get(appid,{}).get('data',{})
        except Exception:continue
        name=major.norm(meta.get('name',''))
        for suffix in ('gameoftheyearedition','enhancededition','gotyedition','ultimateedition','windowsedition','goldedition'):name=name.removesuffix(suffix)
        if name!=canonical:continue
        description=re.sub('<[^>]+>',' ',meta.get('short_description','')+' '+meta.get('about_the_game','')).lower()
        years=re.findall(r'\b(?:19|20)\d{2}\b',meta.get('release_date',{}).get('date',''))
        if years and int(years[-1])>entry['year']+3 and re.search(r'\b(?:remake|remaster|remastered|reimagining)\b',description):continue
        owner=' / '.join(meta.get('publishers') or meta.get('developers') or [])
        if not owner:continue
        count=0
        for shot in meta.get('screenshots',[])[:4]:
            url=shot.get('path_full','');cached=major.QUALITY/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
            try:
                raw=cached.read_bytes() if cached.exists() else major.fetch(url)
                with Image.open(io.BytesIO(raw)) as photo:photo.load();w,h=photo.size
                if w<1280 or h<600:continue
                cached.write_bytes(raw)
                entry['images'].append({'url':url,'source_page':'https://store.steampowered.com/app/'+appid+'/',
                    'title':title+': publisher screenshot','creator':owner,'credit':owner+' / official publisher Steam media',
                    'license':'Original game publisher and artwork rights retained.','width':w,'height':h,'native_long_edge':max(w,h),
                    'kind':'screenshot','story_paragraph':-1,'quality_verified':'Publisher original decoded at native resolution; not enlarged.',
                    'verification':{'appid':int(appid),'published_title':meta['name'],'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()}})
                count+=1
                if count==2:break
            except Exception:continue
        return title,count
    return title,0
with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(enrich,targets))
temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(module,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(path)
out=ROOT/'build/research/major-releases/screenshot-enrichment.json';out.write_text(json.dumps({'entries':results,'images_added':sum(n for _,n in results)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(out.read_text(encoding='utf-8'))
