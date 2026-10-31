"""Acquire real publisher media using explicit Wikidata Steam identifiers.

Wikidata is an identity discovery index, not an image-licensing authority.
Publisher API titles must independently match the article title; ambiguous
remasters/compilations are held for human review, never silently substituted.
Only additive media and research caches are written, never the master catalogue.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, io, json, re, time, unicodedata
import urllib.request, urllib.parse, urllib.error
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'build/research/publishing/wikidata-steam'
OUTPUT = ROOT / 'content/expansion/media-wikidata-steam-additions.json'
AGENT = 'PixelMuseum/0.1 (historical publisher-media research; https://github.com/LoZazaMastro)'

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def norm(s):
    s = unicodedata.normalize('NFKD',s.casefold()).encode('ascii','ignore').decode()
    s = re.sub(r'\s*\((?:video game|\d{4} video game)\)\s*$', '', s)
    return re.sub('[^a-z0-9]', '', s.replace('&','and').replace('™','').replace('®',''))
def get(url, limit=20_000_001):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':AGENT}), timeout=35) as response:
        raw=response.read(limit)
        if len(raw)>=limit: raise ValueError('Response exceeds bounded research size')
        return raw
def api(url, path):
    if path.exists(): return read(path)
    data=json.loads(get(url));write(path,data);time.sleep(1.05);return data

def later_reconstruction(meta, entry):
    years=re.findall(r'\b(?:19|20)\d{2}\b',str(meta.get('release_date',{}).get('date','')))
    published_year=int(years[-1]) if years else 0
    text=re.sub('<[^>]+>',' ',meta.get('short_description','')+' '+meta.get('about_the_game','')).casefold()
    return bool(published_year>entry['year']+2 and re.search(r'\b(?:remake|remastered|remaster|reimagining)\b',text))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=100)
    parser.add_argument('--discover-only', action='store_true');args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True)
    entries=read(ROOT/'content/catalog.json')['entries']
    # Existing verified image records are not new coverage; prioritize the gaps.
    targets=[e for e in entries if not e.get('calendar_only') and not e.get('images')
             and e.get('kind')=='game' and e.get('provenance',{}).get('article_title')]
    titles=sorted({e['provenance']['article_title'] for e in targets})
    identities={}
    for offset in range(0,len(titles),35):
        names=titles[offset:offset+35]
        token=hashlib.sha256('|'.join(names).encode()).hexdigest()[:16]
        url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode({
            'action':'wbgetentities','sites':'enwiki','titles':'|'.join(names),
            'props':'claims|labels|sitelinks','languages':'en','sitefilter':'enwiki','format':'json'})
        try:data=api(url,CACHE/f'identities-{token}.json')
        except urllib.error.HTTPError as error:
            if error.code==429: print('Wikidata rate limited; stopping without retries.',flush=True);return
            raise
        for entity in data.get('entities',{}).values():
            title=entity.get('sitelinks',{}).get('enwiki',{}).get('title')
            apps=[]
            for claim in entity.get('claims',{}).get('P1733',[]):
                value=claim.get('mainsnak',{}).get('datavalue',{}).get('value')
                if isinstance(value,str) and value.isdigit(): apps.append(value)
            if title and apps:identities[title]={'qid':entity['id'],'appids':apps,'article_title':title,
                'source_api':url,'entity_url':'https://www.wikidata.org/wiki/'+entity['id']}
        print('Identity batch',offset//35+1,'Steam-linked subjects',len(identities),flush=True)
    write(CACHE/'identifiers.json',identities)
    if args.discover_only:return
    auditpath=CACHE/'audit.json';audit=read(auditpath) if auditpath.exists() else {}
    output={x['entry_id']:x for x in read(OUTPUT)['entries']} if OUTPUT.exists() else {}
    # Re-evaluate cached discoveries when tightening an edition rule. Retain
    # rejected media in research, but do not leak it into the additive payload.
    heldpath=CACHE/'edition-review-held.json';held=read(heldpath) if heldpath.exists() else {}
    lookup={e['id']:e for e in entries}
    for eid,row in list(output.items()):
        appid=str(row['images'][0]['verification']['appid'])
        path=CACHE/f'app-{appid}.json'
        meta=read(path).get(appid,{}).get('data',{}) if path.exists() else {}
        if later_reconstruction(meta,lookup[eid]):
            held[eid]={'reason':'Later remake/remaster/visual reconstruction requires contextual edition review.',
                'museum_year':lookup[eid]['year'],'published_release_date':meta.get('release_date'),
                'published_title':meta.get('name'),'retained_research_record':row}
            del output[eid]
    write(heldpath,held)
    write(OUTPUT,{'schema_version':1,'policy':'Explicit Wikidata Steam identity plus independent exact publisher title; genuine remotely decoded native HD media. Edition ambiguities held; copyright retained; no invented paragraph associations.','entries':list(output.values())})
    processed=0
    for entry in targets:
        identity=identities.get(entry['provenance']['article_title'])
        if not identity:continue
        for appid in identity['appids']:
            auditkey=entry['id']+':'+appid
            if audit.get(auditkey,{}).get('complete'):continue
            if processed>=args.limit:break
            processed+=1
            try:
                endpoint=f'https://store.steampowered.com/api/appdetails?appids={appid}&l=english'
                meta=api(endpoint,CACHE/f'app-{appid}.json').get(appid,{}).get('data',{})
                if not meta or norm(meta.get('name',''))!=norm(entry['title']):
                    audit[auditkey]={'complete':True,'status':'title_or_edition_review_required',
                        'entry_id':entry['id'],'museum_title':entry['title'],'published_title':meta.get('name'),**identity}
                    write(auditpath,audit);continue
                # A remake can retain the exact same retail title and even be
                # linked from the original game's Wikidata item. Name identity
                # alone must not silently substitute its new visual design.
                if later_reconstruction(meta,entry):
                    audit[auditkey]={'complete':True,'status':'same_title_remake_or_remaster_review_required',
                        'entry_id':entry['id'],'museum_title':entry['title'],'published_title':meta['name'],**identity}
                    write(auditpath,audit);continue
                owner=' / '.join(meta.get('publishers') or meta.get('developers') or [])
                if not owner:raise ValueError('Publisher attribution absent')
                media=[];has_hero=False
                urls=[('artwork',f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_hero_2x.jpg'),
                      ('artwork',f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_hero.jpg')]
                urls += [('screenshot',x['path_full']) for x in meta.get('screenshots',[])[:3]]
                for kind,url in urls:
                    if kind=='artwork' and has_hero:continue
                    try:
                        raw=get(url)
                        with Image.open(io.BytesIO(raw)) as im:im.load();width,height=im.size
                        if max(width,height)<1600:continue
                        item={'url':url,'source_page':f'https://store.steampowered.com/app/{appid}/',
                            'title':meta['name']+(': Steam PC edition library artwork' if kind=='artwork' else ': Steam PC edition screenshot'),
                            'creator':owner,'credit':owner+' / official Steam publisher media',
                            'license':'Publisher copyright; historical editorial illustration. Not an open-licensed asset.',
                            'rights_review':'Publisher copyright retained; editorial-use decision still requires review.',
                            'width':width,'height':height,'native_long_edge':max(width,height),
                            'quality_verified':'Fresh publisher CDN GET and full native image decode; no artificial enlargement.',
                            'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat(),
                                'source_api':endpoint,'appid':int(appid),'published_title':meta['name'],
                                'published_pc_release_date':meta.get('release_date')},
                            'provenance':{'identity_discovery':identity,'edition_note':'Publisher Steam PC edition; not claimed to be original launch-era capture.'}}
                        if kind=='artwork':item['story_paragraph']=0;has_hero=True
                        media.append(item)
                    except urllib.error.HTTPError as error:
                        if error.code==429:raise
                    except Exception as error:
                        print('Image skipped',appid,type(error).__name__,flush=True)
                    time.sleep(.15)
                if media:output[entry['id']]={'entry_id':entry['id'],'images':media}
                audit[auditkey]={'complete':True,'status':'verified' if media else 'no_native_hd_media',
                    'entry_id':entry['id'],'museum_title':entry['title'],'published_title':meta['name'],'images':len(media),**identity}
                write(auditpath,audit);write(OUTPUT,{'schema_version':1,'policy':'Explicit Wikidata Steam identity plus independent exact publisher title; genuine remotely decoded native HD media. Edition ambiguities held; copyright retained; no invented paragraph associations.','entries':list(output.values())})
                print(entry['id'],meta['name'],len(media),flush=True)
            except Exception as error:
                audit[auditkey]={'complete':False,'error':str(error),'entry_id':entry['id'],**identity};write(auditpath,audit)
                if isinstance(error,urllib.error.HTTPError) and error.code==429:print('Rate limited; stopped without retries.',flush=True);return
    print('Additive entries',len(output),'new identities processed',processed,flush=True)

if __name__=='__main__':main()
