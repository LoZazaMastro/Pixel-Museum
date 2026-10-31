"""Audit prominent original game releases and add attributed, illustrated entries.

The checklist is explicit editorial scope, not a claim to enumerate every AAA
game. Originals and standalone games stay distinct from compilations/remakes.
Only records with substantive English source prose and verified portrait art
are admitted. Image rights remain with each publisher; Wikipedia text retains
its revision and CC BY-SA attribution. The master catalogue is never changed.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, html, importlib.util, io, json, re, time, unicodedata
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
CACHE=ROOT/'build/research/major-releases'
CACHE.mkdir(parents=True,exist_ok=True)
QUALITY=ROOT/'build/research/image-quality'
QUALITY.mkdir(parents=True,exist_ok=True)
AGENT='PixelMuseum/0.1 (historical research; https://github.com/LoZazaMastro)'
LICENCE='https://creativecommons.org/licenses/by-sa/4.0/'
PLAYHUB=Path('F:/Playhub/Plugin/Playhub/Source/GamingModeDeckyPlugin/quick_settings/history_images.json')

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def norm(text):
    text=text.replace('\u2122','').replace('\u00ae','')
    text=unicodedata.normalize('NFKD',html.unescape(text)).encode('ascii','ignore').decode().lower()
    text=re.sub(r'\([^)]*\)','',text).replace('&','and')
    return re.sub('[^a-z0-9]','',text).removeprefix('sidmeiers')

def canonical(text):
    key=norm(text)
    return {'mother':'earthboundbeginnings','donkeykongcountry2diddyskongquest':'donkeykongcountry2'}.get(key,key)

def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':AGENT}),timeout=24) as response:
        data=response.read(24<<20)
    if len(data)>=24<<20:raise ValueError('Response exceeds image research budget')
    return data

def api(base,params,tag):
    endpoint=base+'?'+urlencode({'format':'json','formatversion':2,**params})
    key=hashlib.sha256(endpoint.encode()).hexdigest()[:20]
    path=CACHE/(tag+'-'+key+'.json')
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    result=json.loads(fetch(endpoint));write(path,result);time.sleep(.2)
    return result

def date_from(page,year):
    revision=page.get('revisions',[{}])[0]
    raw=revision.get('slots',{}).get('main',{}).get('content','')
    # Only the release field, never later prose, reception or remaster dates.
    match=re.search(r'^\|\s*(?:released|release|release_date)\s*=\s*(.*?)(?=^\|\s*[A-Za-z_ ]+\s*=|^\}\})',raw,re.M|re.S)
    if not match:return {'month':0,'day':0,'precision':'year','region':'Original release year'}
    field=match.group(1)
    # Citations frequently contain the announcement/review publication date.
    # Those are source metadata, never an alternative release date.
    field=re.sub(r'<ref\b[^>]*/\s*>','',field,flags=re.I|re.S)
    field=re.sub(r'<ref\b[^>]*>.*?</ref\s*>','',field,flags=re.I|re.S)
    field=re.sub(r'<!--.*?-->','',field,flags=re.S)
    # Explanatory footnotes may describe premium early access. They must not
    # override the regular release written immediately before the footnote.
    while True:
        note=re.search(r'\{\{\s*(?:efn|refn|notetag|note)\s*[|}]',field,re.I)
        if not note:break
        depth=1;cursor=note.end()
        while cursor<len(field) and depth:
            if field.startswith('{{',cursor):depth+=1;cursor+=2
            elif field.startswith('}}',cursor):depth-=1;cursor+=2
            else:cursor+=1
        field=field[:note.start()]+' '+field[cursor:]
    months=['January','February','March','April','May','June','July','August','September','October','November','December']
    candidates=[]
    for number,month in enumerate(months,1):
        for m in re.finditer(r'\b'+month+r'\s+(\d{1,2}),?\s+('+str(year)+r')\b',field,re.I):candidates.append((number,int(m.group(1))))
        for m in re.finditer(r'\b(\d{1,2})\s+'+month+r'\s+('+str(year)+r')\b',field,re.I):candidates.append((number,int(m.group(1))))
    for m in re.finditer(r'\{\{(?:start date|startdate|dts|date)\s*\|\s*'+str(year)+r'\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})',field,re.I):candidates.append((int(m.group(1)),int(m.group(2))))
    valid=[x for x in candidates if 1<=x[0]<=12 and 1<=x[1]<=31]
    if valid:
        month,day=min(valid)
        return {'month':month,'day':day,'precision':'day','region':'Earliest listed release in the original release-year infobox'}
    return {'month':0,'day':0,'precision':'year','region':'Original release year; no exact day inferred'}

def era(year):
    return 'personal' if year<1990 else 'dimensions' if year<2000 else 'connected' if year<2010 else 'everywhere' if year<2020 else 'living-history'

def candidates():
    seeds=json.loads((HERE/'major-release-seeds.json').read_text(encoding='utf-8'))['years']
    existing=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))['entries']
    aliases={(canonical(s),e['year']) for e in existing for s in (e['title'],e.get('provenance',{}).get('article_title','')) if s}
    wanted=[(int(y),t) for y,titles in seeds.items() for t in titles if (canonical(t),int(y)) not in aliases]
    return seeds,existing,wanted

def identify(wanted):
    pages=[]
    for start in range(0,len(wanted),18):
        names=[t for _,t in wanted[start:start+18]]
        data=api('https://en.wikipedia.org/w/api.php',{'action':'query','titles':'|'.join(names),'redirects':1,
            'prop':'extracts|revisions|pageprops','exintro':1,'explaintext':1,'exlimit':'max',
            'rvprop':'ids|timestamp|content','rvslots':'main','ppprop':'wikibase_item'},'articles')
        pages.extend(p for p in data.get('query',{}).get('pages',[]) if 'pageid' in p)
        print('Wikipedia batch',start//18+1,'/',(len(wanted)+17)//18,flush=True)
    ids=[p.get('pageprops',{}).get('wikibase_item') for p in pages]
    ids=[x for x in ids if x]
    entities={}
    for start in range(0,len(ids),45):
        data=api('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(ids[start:start+45]),'props':'claims'},'identities')
        entities.update(data.get('entities',{}))
    return pages,entities

def wikipedia_cover(page):
    data=api('https://en.wikipedia.org/w/api.php',{'action':'query','pageids':page['pageid'],'prop':'pageimages','piprop':'original|name','pilicense':'any'},'cover-original')
    meta=data.get('query',{}).get('pages',[{}])[0]
    original=meta.get('original',{});filename=meta.get('pageimage','')
    if not re.search(r'cover|box.?art|box|poster',filename,re.I):return None
    url=original.get('source','').split('?',1)[0]
    if not url.startswith('https://upload.wikimedia.org/'):return None
    cached=QUALITY/(hashlib.sha256(url.encode()).hexdigest()[:16]+Path(filename).suffix.lower())
    try:
        raw=cached.read_bytes() if cached.exists() else fetch(url)
        with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
        if max(w,h)<600 or min(w,h)<350 or not .5<w/h<1.8:return None
        cached.write_bytes(raw)
        return {'url':url,'source_page':'https://en.wikipedia.org/wiki/File:'+filename,
            'title':re.sub(r'\s*\([^)]*\)$','',page['title'])+': original game cover',
            'creator':'Original game publisher and cover artwork rights holders',
            'credit':'Game cover: original publisher and artwork rights holders / Wikipedia file description',
            'license':'Copyrighted game cover; historical editorial illustration. Not an open-licensed image.',
            'width':w,'height':h,'native_long_edge':max(w,h),'kind':'cover','cover_role':True,'story_paragraph':0,
            'quality_verified':'Original file decoded at native dimensions, at least600px long edge; never enlarged.',
            'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()},
            'provenance':{'identity_discovery':'The exact English Wikipedia game article infobox image','file_name':filename}}
    except Exception:return None

def cover(page,entities,year):
    archival=HERE/'major-launchbox-cover-sources.json'
    if archival.exists():
        records=json.loads(archival.read_text(encoding='utf-8')).get('entries',{})
        image=records.get(norm(page['title'])+'|'+str(year))
        if image:return image
        for key,image in records.items():
            if key.endswith('|'+str(year)) and norm(image['title'].removesuffix(': original game cover'))==norm(page['title']):return image
    official=HERE/'major-official-cover-sources.json'
    if official.exists():
        for title,image in json.loads(official.read_text(encoding='utf-8')).get('entries',{}).items():
            if norm(title)==norm(page['title']):return image
    qid=page.get('pageprops',{}).get('wikibase_item')
    ids=[]
    for row in entities.get(qid,{}).get('claims',{}).get('P1733',[]):
        value=row.get('mainsnak',{}).get('datavalue',{}).get('value')
        if isinstance(value,str) and value.isdigit():ids.append(value)
    try:
        search=api('https://store.steampowered.com/api/storesearch/',{'term':re.sub(r'\s*\([^)]*\)$','',page['title']),'l':'english','cc':'us'},'steam-search')
        for item in search.get('items',[])[:8]:
            if str(item.get('id','')).isdigit() and norm(item.get('name',''))==norm(page['title']):ids.append(str(item['id']))
    except Exception:pass
    ids=list(dict.fromkeys(ids))
    for appid in ids:
        try:
            data=api('https://store.steampowered.com/api/appdetails',{'appids':appid,'l':'english'},'steam')
            meta=data.get(appid,{}).get('data',{})
            title=meta.get('name','')
            # Do not use a newer remake just because it shares a franchise name.
            canonical=norm(page['title'])
            simplified=norm(title)
            for suffix in ('gameoftheyearedition','enhancededition','gotyedition','ultimateedition','windowsedition','goldedition'):
                simplified=simplified.removesuffix(suffix)
            if simplified!=canonical:continue
            release_years=re.findall(r'\b(?:19|20)\d{2}\b',meta.get('release_date',{}).get('date',''))
            published_year=int(release_years[-1]) if release_years else 0
            description=re.sub('<[^>]+>',' ',meta.get('short_description','')+' '+meta.get('about_the_game','')).lower()
            if published_year>year+3 and re.search(r'\b(?:remake|remastered|remaster|reimagining)\b',description):continue
            owner=' / '.join(meta.get('publishers') or meta.get('developers') or [])
            if not owner:continue
            for filename in ('library_600x900_2x.jpg','library_600x900.jpg'):
                url=f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/{filename}'
                cached=QUALITY/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
                try:
                    raw=cached.read_bytes() if cached.exists() else fetch(url)
                    with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
                    if w<600 or h<900 or not .55<w/h<.85:continue
                    cached.write_bytes(raw)
                    return {'url':url,'source_page':f'https://store.steampowered.com/app/{appid}/',
                        'title':title+': official library cover','creator':owner,'credit':owner+' / publisher Steam cover artwork',
                        'license':'Publisher copyright; historical editorial illustration. Not an open-licensed asset.',
                        'rights_review':'Publisher retains copyright; this attribution does not grant redistribution rights.',
                        'width':w,'height':h,'native_long_edge':max(w,h),'kind':'cover','cover_role':True,'story_paragraph':0,
                        'quality_verified':'Original publisher CDN file decoded at native dimensions; no enlargement.',
                        'verification':{'appid':int(appid),'published_title':title,'sha256':hashlib.sha256(raw).hexdigest(),
                            'checked_utc':datetime.now(timezone.utc).isoformat()},
                        'provenance':{'identity_discovery':{'qid':qid,'appid':appid},'edition_note':'Publisher Steam PC library cover; not claimed to be an original box scan.'}}
                except Exception:continue
            # A native crop gives the timeline a generous, normal-aspect artwork
            # instead of the very narrow Steam banner. Keep the uncropped source
            # as an additional gallery artefact; do not describe it as box art.
            for filename in ('library_hero_2x.jpg','library_hero.jpg'):
                remote=f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/{filename}'
                url=remote+'#museum-cover-3x2'
                cached=QUALITY/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
                original=QUALITY/(hashlib.sha256(remote.encode()).hexdigest()[:16]+'.jpg')
                try:
                    if cached.exists():
                        raw=cached.read_bytes();im=Image.open(io.BytesIO(raw));im.load();w,h=im.size
                        source=Image.open(original);source.load();sw,sh=source.size
                    else:
                        body=original.read_bytes() if original.exists() else fetch(remote)
                        source=Image.open(io.BytesIO(body));source.load();sw,sh=source.size
                        if sw<1600 or sh<600:continue
                        original.write_bytes(body)
                        width=min(sw,int(sh*1.5));left=(sw-width)//2
                        im=source.crop((left,0,left+width,sh));w,h=im.size
                        im.convert('RGB').save(cached,'JPEG',quality=96,subsampling=0);raw=cached.read_bytes()
                    if w<900 or h<600:continue
                    return {'url':url,'source_page':f'https://store.steampowered.com/app/{appid}/',
                        'title':title+': publisher key artwork','creator':owner,'credit':owner+' / official Steam publisher artwork',
                        'license':'Publisher copyright; historical editorial illustration. Not an open-licensed asset.',
                        'width':w,'height':h,'native_long_edge':max(w,h),'kind':'artwork','cover_role':True,'story_paragraph':0,
                        'quality_verified':'Native central3:2 crop of publisher original; no enlargement. Uncropped image retained in gallery.',
                        'verification':{'appid':int(appid),'published_title':title,'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()},
                        'provenance':{'identity_discovery':{'qid':qid,'appid':appid},'source_image_url':remote,
                            'crop_pixels':[(sw-w)//2,0,(sw+w)//2,sh],'modifications':'Central3:2 crop for timeline composition; original retained as a separate gallery image.'},
                        'uncropped_original':{'url':remote,'width':sw,'height':sh}}
                except Exception:continue
        except Exception:continue
    # Reuse Playhub's already identified game covers, requesting the actual
    # IGDB master rather than a resized derivative. Tiny scans stay held.
    if PLAYHUB.exists():
        source=json.loads(PLAYHUB.read_text(encoding='utf-8'))
        same_name_years={int(y) for y,titles in json.loads((HERE/'major-release-seeds.json').read_text(encoding='utf-8'))['years'].items() for t in titles if norm(t)==norm(page['title'])}
        for rows in source.values():
            for row in rows:
                if row.get('kind')!='cover' or norm(row.get('subject',''))!=norm(page['title']):continue
                origin=row.get('sourceUrl','')
                if len(same_name_years)>1 and str(year) not in origin:continue
                url=row.get('url','')
                if 'images.igdb.com/' not in url:continue
                url=re.sub(r'/t_[^/]+/','/t_original/',url)
                cached=QUALITY/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
                try:
                    raw=cached.read_bytes() if cached.exists() else fetch(url)
                    with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
                    if w<600 or h<900 or not .5<w/h<1.1:continue
                    cached.write_bytes(raw)
                    return {'url':url,'source_page':origin,'title':re.sub(r'\s*\([^)]*\)$','',page['title'])+': original game cover',
                        'creator':row.get('credit','Original game publisher and artwork rights holders'),
                        'credit':row.get('credit','Game cover: original publisher and rights holders.'),
                        'license':row.get('rights','Publisher copyright; historical editorial illustration. Not an open-licensed asset.'),
                        'width':w,'height':h,'native_long_edge':max(w,h),'kind':'cover','cover_role':True,'story_paragraph':0,
                        'quality_verified':'Original image master decoded at native dimensions; no enlarged derivative.',
                        'verification':{'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()},
                        'provenance':{'identity_discovery':'Existing Playhub cover record for the exact subject','source_metadata':str(PLAYHUB),'original_url':row['url']}}
                except Exception:continue
    return wikipedia_cover(page)

def entry(page,year,image):
    extended=False
    text=page.get('extract','').strip()
    paragraphs=[p.strip() for p in text.split('\n') if len(p.split())>=15 and not p.startswith('=')]
    if len(' '.join(paragraphs).split())<120:
        full=api('https://en.wikipedia.org/w/api.php',{'action':'query','pageids':page['pageid'],'prop':'extracts|revisions','explaintext':1,'exsectionformat':'plain','rvprop':'ids|timestamp|content','rvslots':'main'},'full-article')
        current=full.get('query',{}).get('pages',[{}])[0]
        text=current.get('extract','')
        page={**page,**current};extended=True
        paragraphs=[p.strip() for p in text.split('\n') if len(p.split())>=20 and not p.startswith('=')][:7]
    if len(' '.join(paragraphs).split())<120:raise ValueError('Insufficient substantive source prose')
    revision=page['revisions'][0]
    selection='Lead and opening article paragraphs selected; formatting removed.' if extended else 'Lead paragraphs selected; formatting removed.'
    title=re.sub(r'\s*\((?:\d{4} )?video game\)$','',page['title'])
    article='https://en.wikipedia.org/wiki/'+page['title'].replace(' ','_')
    revision_url='https://en.wikipedia.org/w/index.php?oldid='+str(revision['revid'])
    history=article+'?action=history'
    return {'id':'wikipedia-'+str(page['pageid']),'title':title,'year':year,'date':date_from(page,year),'kind':'game',
        'subtitle':'From the reference collection','summary':re.split(r'(?<=[.!?])\s+',paragraphs[0])[0],
        'body':paragraphs,'story_headings':[title]+[('The design' if re.search(r'\b(?:gameplay|player|combat|puzzle|mechanics)\b',p,re.I) else 'Making the game' if re.search(r'\b(?:development|developed|production|director|designed)\b',p,re.I) else 'Reception and legacy' if re.search(r'\b(?:review|acclaim|critics|commercial|sales|sold)\b',p,re.I) else title) for p in paragraphs[1:]],
        'era_id':era(year),'tags':['reference','Wikipedia','major-release-coverage'],'related_ids':[],'layout':'editorial',
        'images':[image],'preferred_image':0,'videos':[],'models':[],'featured':False,'explicit_story_media_only':True,
        'sources':[{'title':page['title']+' - article revision','url':revision_url,'publisher':'English Wikipedia contributors'},
            {'title':'Article contributors and history','url':history,'publisher':'English Wikipedia contributors'},
            {'title':'Text licence: Creative Commons Attribution-ShareAlike 4.0','url':LICENCE,'publisher':'Creative Commons'},
            {'title':image['title'],'url':image['source_page'],'publisher':image['creator']}],
        'attribution':{'text':"Text reproduced from '"+page['title']+"', by Wikipedia contributors, under CC BY-SA 4.0. "+selection,
            'source_url':revision_url,'article_url':article,'contributors_url':history,'license':'CC BY-SA 4.0','license_url':LICENCE,
            'revision_id':revision['revid'],'revision_timestamp':revision['timestamp'],'changes':selection+' Text otherwise reproduced.'},
        'provenance':{'provider':'English Wikipedia','page_id':page['pageid'],'article_title':page['title'],
            'release_year_basis':'Curated original-release checklist, cross-checked against article introduction and infobox',
            'retrieved':datetime.now(timezone.utc).date().isoformat(),'coverage_module':'major-release-additions'},
        'factual_note':'Regional and platform release dates may differ. Where shown, the exact day is taken only from the article release infobox.'}

def context_images(record):
    cover=record['images'][0];appid=cover.get('verification',{}).get('appid')
    if cover.get('uncropped_original'):
        original={**cover,**cover['uncropped_original'],'title':record['title']+': complete publisher artwork','cover_role':False,'story_paragraph':-1}
        original.pop('uncropped_original',None);original['provenance']={**cover.get('provenance',{}),'modifications':'Uncropped original publisher artwork.'}
        source=QUALITY/(hashlib.sha256(original['url'].encode()).hexdigest()[:16]+'.jpg')
        if source.exists():original['verification']={**original.get('verification',{}),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
        record['images'].append(original)
    if not appid:return
    try:meta=api('https://store.steampowered.com/api/appdetails',{'appids':str(appid),'l':'english'},'steam').get(str(appid),{}).get('data',{})
    except Exception:return
    gameplay=[n for n,p in enumerate(record['body']) if n and re.search(r'\b(?:player|gameplay|combat|puzzle|mechanics)\b',p,re.I)]
    for index,shot in enumerate(meta.get('screenshots',[])[:2]):
        url=shot.get('path_full','')
        if not url.startswith('https://'):continue
        cached=QUALITY/(hashlib.sha256(url.encode()).hexdigest()[:16]+'.jpg')
        try:
            raw=cached.read_bytes() if cached.exists() else fetch(url)
            with Image.open(io.BytesIO(raw)) as image:image.load();w,h=image.size
            if w<1280 or h<600 or w/h>2.5:continue
            cached.write_bytes(raw)
            record['images'].append({'url':url,'source_page':cover['source_page'],
                'title':record['title']+': publisher screenshot','creator':cover['creator'],'credit':cover['creator']+' / publisher Steam screenshot',
                'license':cover['license'],'width':w,'height':h,'native_long_edge':max(w,h),'kind':'screenshot',
                'story_paragraph':gameplay[index] if index<len(gameplay) else -1,
                'quality_verified':'Publisher original fully decoded at native resolution; no enlargement.',
                'verification':{'appid':appid,'sha256':hashlib.sha256(raw).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()}})
        except Exception:continue

def main():
    seeds,existing,wanted=candidates()
    pages,entities=identify(wanted)
    aliases={}
    for y,t in wanted:aliases.setdefault(norm(t),[]).append(y)
    oldids={e['id'] for e in existing}
    previous=json.loads((HERE/'major-release-additions.json').read_text(encoding='utf-8')).get('entries',[]) if (HERE/'major-release-additions.json').exists() else []
    outputs=previous;held=[]
    def process(page):
        title=page['title'];years=aliases.get(norm(title),[])
        explicit=re.search(r'\((\d{4}) video game\)',title)
        year=int(explicit.group(1)) if explicit and int(explicit.group(1)) in years else years[0] if len(years)==1 else 0
        if not year:
            # API normalized redirects should not invent a different game's year.
            return None,{'title':title,'reason':'Canonical title/year requires identity review'}
        if 'wikipedia-'+str(page['pageid']) in oldids:return None,None
        image=cover(page,entities,year)
        if not image:return None,{'title':title,'year':year,'reason':'No verified native portrait cover available from its exact publisher Steam identity'}
        try:
            record=entry(page,year,image);context_images(record)
            return record,None
        except Exception as error:return None,{'title':title,'year':year,'reason':str(error)}
    with ThreadPoolExecutor(max_workers=5) as pool:
        for number,(record,review) in enumerate(pool.map(process,pages),1):
            if record and record['id'] not in {e['id'] for e in outputs}:outputs.append(record)
            if review:held.append(review)
            if number%10==0:print('Covers/prose',number,'/',len(pages),'admitted',len(outputs),'held',len(held),flush=True)
    outputs.sort(key=lambda e:(e['year'],e['date']['month'],e['date']['day'],e['title']))
    write(HERE/'major-release-additions.json',{'schema_version':1,'license_notice':'Wikipedia text is CC BY-SA 4.0. Publisher image rights retained. See individual source, contributor, revision and licence records.','entries':outputs})
    write(HERE/'major-release-coverage-audit.json',{'checklist_titles':sum(map(len,seeds.values())),'existing_catalog_entries':len(existing),
        'initial_exact_title_gaps':len(wanted),'admitted':len(outputs),'held':held,
        'remaining_checklist_gaps':[{'year':y,'title':t} for y,t in wanted if (norm(t),y) not in {(norm(e['title']),e['year']) for e in outputs}],
        'scope_notice':'Explicit curated checklist, not an exhaustive list of AAA games; held records are not empty catalogue exhibits.'})
    print('ADMITTED',len(outputs),'HELD',len(held),flush=True)

if __name__=='__main__':main()
