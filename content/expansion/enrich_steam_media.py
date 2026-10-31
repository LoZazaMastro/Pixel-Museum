"""Verify publisher media for exact-title games already identified by Playhub.

URLs are used remotely by the museum. Research caches store response metadata
and hashes, not redistributed publisher texture packs. No fuzzy sequel matching.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,collections,hashlib,io,json,re,time,urllib.request,urllib.error
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'build/research/publishing/steam'
def key(s):return re.sub(r'[^a-z0-9]','',s.casefold())
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fetch(url,limit=12_000_001):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical publisher-media research'}),timeout=20) as response:return response.read(limit)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=50);args=ap.parse_args();CACHE.mkdir(parents=True,exist_ok=True)
    originals=read(Path('F:/Playhub/Plugin/Playhub/Source/GamingModeDeckyPlugin/quick_settings/history_images.json'))
    candidates=collections.defaultdict(set)
    for rows in originals.values():
        for row in rows:
            for field in ('url','sourceUrl'):
                match=re.search(r'(?:/apps/|/app/)(\d+)',row.get(field,''))
                if match and row.get('subject'):candidates[key(row['subject'])].add(int(match.group(1)))
    entries=read(ROOT/'content/catalog.json')['entries'];groups=collections.defaultdict(list)
    for entry in entries:
        if entry.get('kind')=='game':groups[key(entry['title'])].append(entry)
    outputpath=ROOT/'content/expansion/steam-media-additions.json';previous=read(outputpath) if outputpath.exists() else {'entries':[]};output={x['entry_id']:x for x in previous['entries']}
    auditpath=CACHE/'audit.json';audit=read(auditpath) if auditpath.exists() else {};processed=0
    for title,game_entries in groups.items():
        if title not in candidates:continue
        for appid in sorted(candidates[title]):
            token=str(appid)
            if token in audit and audit[token].get('complete'):continue
            if processed>=args.limit:break
            processed+=1
            meta_path=CACHE/f'app-{appid}.json'
            try:
                if not meta_path.exists():meta_path.write_bytes(fetch(f'https://store.steampowered.com/api/appdetails?appids={appid}&l=english'));time.sleep(.6)
                meta=read(meta_path).get(token,{}).get('data',{})
                if not meta or key(meta.get('name',''))!=title:
                    audit[token]={'complete':True,'status':'title_mismatch_or_unavailable','published_title':meta.get('name'),'requested_titles':[x['title'] for x in game_entries]};write(auditpath,audit);continue
                media=[];owner=' / '.join(meta.get('publishers') or meta.get('developers') or [meta['name']+' rights holders'])
                urls=[('artwork',f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_hero_2x.jpg'),('artwork',f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_hero.jpg')]
                urls.extend(('screenshot',x['path_full']) for x in meta.get('screenshots',[])[:4])
                has_hero=False
                for kind,url in urls:
                    if kind=='artwork' and has_hero:continue
                    try:
                        raw=fetch(url)
                        with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
                        if max(w,h)<1600:continue
                        item={'url':url,'source_page':f'https://store.steampowered.com/app/{appid}/','title':meta['name']+(': official library artwork' if kind=='artwork' else ': publisher screenshot'),'creator':owner,'license':'Publisher copyright; historical editorial illustration. Not an open-licensed asset.','credit':owner+' / official Steam publisher media','width':w,'height':h,'native_long_edge':max(w,h),'quality_verified':'Fresh remote GET and full decode of the publisher CDN image; no generated enlargement by Pixel Museum.','verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat(),'appid':appid,'published_title':meta['name'],'source_api':f'https://store.steampowered.com/api/appdetails?appids={appid}&l=english'}}
                        if kind=='artwork':item['story_paragraph']=0;has_hero=True
                        media.append(item)
                    except urllib.error.HTTPError as error:
                        if error.code==429:raise
                    except Exception:pass
                    time.sleep(.1)
                for entry in game_entries:
                    if media:output[entry['id']]={'entry_id':entry['id'],'images':media}
                audit[token]={'complete':True,'status':'verified' if media else 'no_native_hd_media','published_title':meta['name'],'exhibit_ids':[x['id'] for x in game_entries],'hd_images':len(media)}
                write(auditpath,audit);write(outputpath,{'schema_version':1,'policy':'Exact publisher identity; original image decoded at>=1600px long edge. Screenshots have no invented paragraph associations. Publisher rights retained.','entries':list(output.values())})
                print(appid,meta['name'],len(media),flush=True)
            except Exception as error:
                audit[token]={'complete':False,'error':str(error)};write(auditpath,audit)
                if isinstance(error,urllib.error.HTTPError) and error.code==429:print('Rate limited; stopped without retries.',flush=True);return
    print('Verified media entries:',len(output),'requests to new app identities:',processed)
if __name__=='__main__':main()
