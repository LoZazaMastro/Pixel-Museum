"""Reuse exact-subject Playhub media with its original provenance, never enlarging it.

This importer changes only Pixel Museum's additive media file. Local source files
are read-only; remote bytes must match the pinned Playhub publication hash.
"""
from pathlib import Path
import argparse, collections, hashlib, io, json, re, time, urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
PLAYHUB=Path('F:/Playhub/Plugin/Playhub')
CACHE=ROOT/'build/research/publishing'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def key(s):return re.sub(r'[^a-z0-9]','',s.casefold())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--verify-limit',type=int,default=40);args=ap.parse_args()
    museum=read(ROOT/'content/catalog.json');published=read(PLAYHUB/'catalog/on-this-day.json')
    provenance=read(PLAYHUB/'Source/GamingModeDeckyPlugin/quick_settings/history_images.json')
    original_sections=collections.defaultdict(list)
    for edition in published['editions']['entries']:
        if not edition.get('published'):continue
        theme=edition['theme'];subject=key(theme.get('subject',''))
        original_sections[subject].append((theme.get('intro',{}).get('en',''),theme.get('intro_image_file','')))
        original_sections[subject].extend((chapter.get('body',{}).get('en',''),chapter.get('image_file','')) for chapter in theme.get('chapters',[]))
    originals=collections.defaultdict(list)
    for rows in provenance.values():
        for row in rows:
            if isinstance(row,dict) and row.get('file'):originals[row['file']].append(row)
    auditpath=CACHE/'playhub-image-verification.json';audit=read(auditpath) if auditpath.exists() else {}
    pool=collections.defaultdict(list);exclusions=[];seen=set()
    for rows in published['images'].values():
        for row in rows:
            if not row.get('file') or row['file'] in seen:continue
            seen.add(row['file']);file=PLAYHUB/'assets/on-this-day/v1'/row['file']
            try:
                raw=file.read_bytes()
                with Image.open(io.BytesIO(raw)) as image:w,h=image.size
            except Exception:continue
            if max(w,h)<1600:continue
            matches=[x for x in originals.get(row['file'],[]) if key(x.get('subject',''))==key(row.get('subject',''))]
            original=next((x for x in matches if x.get('sourceUrl') or x.get('url') or x.get('provider')=='User supplied'),None)
            if not original:continue
            # A claimed 960px source paired with a 4912px local raster is not
            # proof of native detail. Keep it out until the original is checked.
            thumb=re.search(r'/(\d+)px-',original.get('url',''))
            if thumb and max(w,h)>int(thumb.group(1))*1.6:
                exclusions.append({'file':row['file'],'reason':'Source thumbnail dimensions conflict with large local raster; possible generated enlargement.'});continue
            digest=hashlib.sha256(raw).hexdigest()
            if row.get('sha256') and row['sha256']!=digest:continue
            url=row.get('url','')
            if not url.startswith('https://'):continue
            pool[key(row.get('subject',''))].append((row,original,w,h,digest))
    # The installed trial is the first priority; other entries retain their
    # exact published subject match. No fuzzy-title or sequel matching.
    trial=ROOT/'dist/vertical-slice-ready-04/PPSA70421/content/catalog.json'
    priority={x['id'] for x in read(trial)['entries']} if trial.exists() else set()
    ordered=sorted(museum['entries'],key=lambda x:(x['id'] not in priority,x.get('calendar_only',False),x['year']))
    checked=0;blocked_hosts=set();entries=[]
    for entry in ordered:
        added=[]
        for row,original,w,h,digest in pool.get(key(entry['title']),[]):
            url=row['url'];host=urllib.parse.urlparse(url).netloc
            verified=audit.get(url,{})
            if not verified.get('verified') and checked<args.verify_limit and host not in blocked_hosts:
                checked+=1
                try:
                    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical-image verification'}),timeout=25) as response:body=response.read(12_000_001);status=response.status
                    with Image.open(io.BytesIO(body)) as im:im.load();actual=im.size
                    verified={'verified':hashlib.sha256(body).hexdigest()==digest and actual==(w,h),'status':status,'width':actual[0],'height':actual[1],'sha256':hashlib.sha256(body).hexdigest(),'checked_utc':datetime.now(timezone.utc).isoformat()}
                except Exception as error:
                    verified={'verified':False,'error':str(error),'checked_utc':datetime.now(timezone.utc).isoformat()}
                    if isinstance(error,urllib.error.HTTPError) and error.code==429:blocked_hosts.add(host)
                audit[url]=verified;write(auditpath,audit);time.sleep(.15)
            if not verified.get('verified'):continue
            rights=original.get('rights') or 'Rights metadata not supplied in the Playhub record; see the original source. No open licence is asserted.'
            source=original.get('sourceUrl') or original.get('url') or 'https://github.com/LoZazaMastro/Playhub/blob/main/catalog/on-this-day.json'
            caption=original.get('caption') or f"{entry['title']}: {row.get('kind','archival image').replace('_',' ')} from the Playhub collection"
            creator=original.get('creator') or original.get('author') or ('Photographer not identified; image supplied by the Playhub project owner' if original.get('provider')=='User supplied' else 'Original image creator not identified in the Playhub record')
            image={'url':url,'original_url':original.get('url',''),'source_page':source,'title':caption,'creator':creator,'license':rights,'credit':f'{creator} / Playhub historical collection / {rights}','width':w,'height':h,'native_long_edge':max(w,h),'quality_verified':'Pinned remote GET and full decode; SHA-256 matches the read-only Playhub asset. No resizing or generated enlargement by Pixel Museum.','verification':verified,'provenance':{'playhub_file':row['file'],'playhub_subject':row.get('subject'),'original_metadata':original}}
            image['rights_review']='Source attribution requires review' if not original.get('rights') or not (original.get('creator') or original.get('author')) else 'Existing source attribution retained; no new licence claim.'
            # Retain an existing editorial association only when the exact
            # paragraph text also survived the museum integration unchanged.
            for text,filename in original_sections.get(key(entry['title']),[]):
                if filename==row['file'] and text and text in entry.get('body',[]):
                    image['story_paragraph']=entry['body'].index(text);break
            if not any(x['url']==url for x in added):added.append(image)
            if len(added)>=6:break
        if added:entries.append({'entry_id':entry['id'],'images':added})
    output={'schema_version':1,'policy':'Exact published subject only. Native raster minimum1600px long edge. Remote bytes and hash verified. Original rights retained; no licence invented.','entries':entries,'audit':{'verified_unique_urls':sum(x.get('verified',False) for x in audit.values()),'entries_with_media':len(entries),'requests_this_run':checked,'excluded_conflicts':exclusions,'pending_subject_pool':len(pool)}}
    write(ROOT/'content/expansion/playhub-illustration-additions.json',output)
    print(json.dumps(output['audit'],ensure_ascii=False))
if __name__=='__main__':main()
