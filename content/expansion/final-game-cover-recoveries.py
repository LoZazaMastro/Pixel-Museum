"""Acquire publisher media or exact original-edition scans for final games."""
from pathlib import Path
from urllib.request import Request,urlopen
from datetime import datetime,timezone
import hashlib,html,io,json,re
from urllib.parse import urljoin
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
CACHE=ROOT/'build/research/image-quality';RESEARCH=ROOT/'build/research/major-releases'
output=HERE/'museum-cover-recoveries-aliases.json';data=json.loads(output.read_text(encoding='utf-8'))
def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical archive'}),timeout=15) as response:return response.read(24<<20)
def save(eid,title,url,page,owner):
    existing=list(CACHE.glob(hashlib.sha256(url.encode()).hexdigest()[:16]+'.*'))
    raw=existing[0].read_bytes() if existing else fetch(url)
    with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
    if max(w,h)<600 or min(w,h)<350:return False
    ext='.png' if raw.startswith(b'\x89PNG') else '.gif' if raw.startswith(b'GIF8') else '.jpg'
    cached=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:16]+ext);cached.write_bytes(raw)
    data['entries'][eid]={'url':url,'source_page':page,'title':title+': original publisher artwork','creator':owner,
        'credit':owner+' / original publication','license':'Original game artwork rights retained by its publisher.',
        'width':w,'height':h,'cover_role':True,'kind':'cover','story_paragraph':0,'native_long_edge':max(w,h),
        'quality_verified':'Original source decoded at native dimensions; not enlarged.',
        'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()}}
    data.get('failures',{}).pop(eid,None);print('COVER',eid,w,h,flush=True);return True
# The 1998 original, not a modern Virtual Console cover or a ROM modification.
archive=json.loads((ROOT/'build/research/launchbox/last-commercial-candidates.json').read_text(encoding='utf-8'))
for picture in archive['images'].get('2359',[]):
    if 'workbook-09-12-pokemon-giallo' in data['entries']:break
    if picture.get('Type')!='Box - Front':continue
    try:
        if save('workbook-09-12-pokemon-giallo','Pokemon Yellow','https://images.launchbox-app.com/'+picture['FileName'],'https://gamesdb.launchbox-app.com/games/details/2359','Nintendo / Game Freak'):break
    except Exception:continue
page='https://doodles.google/doodle/halloween-2016/'
try:
    markup=fetch(page).decode('utf-8');(RESEARCH/'magic-cat-official.html').write_text(markup,encoding='utf-8')
    urls=list(dict.fromkeys(html.unescape(u) for u in re.findall(r'https://[^\s"<>]+',markup) if any(ext in u for ext in ('.jpg','.png','.webp'))))
    (RESEARCH/'magic-cat-image-candidates.json').write_text(json.dumps(urls,indent=2),encoding='utf-8')
    og=re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)',markup)
    if og:urls.insert(0,html.unescape(og.group(1)))
    for url in urls:
        if 'halloween' not in url.lower() and '2016' not in url:continue
        try:
            if save('wikipedia-52144715','Magic Cat Academy',url,page,'Google Doodles'):break
        except Exception:continue
except Exception as error:print('Google publisher source',error)
for eid,title,page,owner in [
    ('wikipedia-67870471','Angelique Luminarise','https://www.gamecity.ne.jp/anmina/','Koei Tecmo / Sayo Ichi'),
    ('wikipedia-54473486','Honor of Kings','https://www.honorofkings.com/','Tencent / TiMi Studio Group'),
    ('wikipedia-11556966','Fantasy Westward Journey','https://xyq.163.com/','NetEase')]:
    try:
        markup=fetch(page).decode('utf-8',errors='replace');(RESEARCH/(eid+'-publisher.html')).write_text(markup,encoding='utf-8')
        urls=[]
        for candidate in re.findall(r'(?:content|src|href)=["\']([^"\']+)["\']|url\(["\']?([^\)"\']+)',markup):
            url=urljoin(page,html.unescape(candidate[0] or candidate[1]))
            if re.search(r'\.(?:jpg|png|webp|jpeg)(?:\?|$)',url,re.I):urls.append(url)
        urls=list(dict.fromkeys(urls));urls.sort(key=lambda u:0 if any(t in u.lower() for t in ['ogp','ogimage','share','mainvisual','keyvisual','key-visual','main-visual','kv.']) else 1)
        (RESEARCH/(eid+'-publisher-image-candidates.json')).write_text(json.dumps(urls,indent=2),encoding='utf-8')
        for url in urls[:6]:
            try:
                if save(eid,title,url,page,owner):break
            except Exception:continue
    except Exception as error:print(title,'publisher source',error,flush=True)
temp=output.with_suffix('.json.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(output)
