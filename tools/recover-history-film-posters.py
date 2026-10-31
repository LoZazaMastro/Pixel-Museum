"""Acquire original-film poster scans with explicit archive and design credits.

Each result still requires visual identity review before it becomes an override.
No reissues, recreated fan art, cast portraits or generated artwork are used.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json,re,hashlib,html,io,time,unicodedata,sys
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/research/human-history/film-posters';OUT.mkdir(exist_ok=True)
def key(s):return re.sub('[^a-z0-9]+','',unicodedata.normalize('NFKD',re.sub(r'\s*\([^)]*\)','',s)).encode('ascii','ignore').decode().lower())
def fetch(url):
 with urlopen(Request(url,headers={'User-Agent':'PixelMuseum/0.1 historical image research'}),timeout=15) as r:return r.read(32<<20)
selection=json.loads((ROOT/'content/expansion/human-history-film-selection.json').read_text())
curation=json.loads((ROOT/'content/expansion/human-history-curation.json').read_text())
subjects=selection['keep_subjects']+[e['subject'] for e in curation.get('requested_films',[])]
subjects=list(dict.fromkeys(s for s in subjects if s not in curation.get('excluded_subjects',{})))
sources=[]
for name in ['human-history-seeds-extra.json','human-history-user-additions.json']:
 sources+=json.loads((ROOT/'content/expansion'/name).read_text()).get('entries',[])
sources+=curation.get('requested_films',[])
catalog=json.loads((ROOT/'content/human-history.json').read_text())['entries']
years={key(e['subject']):e['year'] for e in sources};years.update({key(e['provenance']['seed_title']):e['year'] for e in catalog})
special={'Star Wars (film)':'star_wars','The Lord of the Rings: The Fellowship of the Ring':'lord_of_the_rings_the_fellowship_of_the_ring','Harry Potter and the Deathly Hallows \u2013 Part 2':'harry_potter_and_the_deathly_hallows_part_two','2001: A Space Odyssey':'2001_a_space_odyssey','The Wizard of Oz (1939 film)':'wizard_of_oz','Snow White and the Seven Dwarfs (1937 film)':'snow_white_and_the_seven_dwarfs'}
page_overrides={'2001: A Space Odyssey':'1968/two_thousand_and_one_a_space_odyssey.html','Rashomon':'intl/japan/1950/rashomon.html','Parasite (2019 film)':'intl/south_korea/2019/parasite.html','Pulp Fiction':'1994/pulp_fiction_ver3.html','The Exorcist':'1973/exorcist_ver2.html','Seven Samurai':'intl/japan/1954/seven_samurai.html','Ghost in the Shell (1995 film)':'intl/japan/1995/ghost_in_the_shell.html'}
def acquire(subject):
 receipt=OUT/(key(subject)+'.json')
 if receipt.exists():
  prior=json.loads(receipt.read_text())
  if prior.get('status')!='hold' or '--retry-holds' not in sys.argv:return prior
 year=years.get(key(subject));result={'subject':subject,'year':year,'status':'hold'}
 if not year:result['reason']='Original release year is not yet in the sourced candidate registry';return result
 title=re.sub(r'\s*\([^)]*\)','',subject);slug=re.sub('[^a-z0-9]+','_',unicodedata.normalize('NFKD',title).encode('ascii','ignore').decode().lower()).strip('_')
 slugs=list(dict.fromkeys([special.get(subject,slug),re.sub(r'^(?:the|a|an)_','',slug),slug]))
 slugs=[s+'_ver1' for s in slugs]+slugs
 if subject=="Schindler's List":slugs=['schindlers_list_ver1','schindlers_list']+slugs
 attempts=[]
 pages=[f'https://www.impawards.com/{year}/{candidate}.html' for candidate in slugs]
 if subject in page_overrides:pages.insert(0,'https://www.impawards.com/'+page_overrides[subject])
 for page in pages:
  try:
   body=fetch(page);text=body.decode('utf8',errors='replace');heading=html.unescape(re.search(r'<title>(.*?)</title>',text,re.S|re.I).group(1))
   if 'Movie Poster' not in heading:raise ValueError('Source page is not the identified film poster archive')
   basename=re.search(r'<img[^>]+src\s*=\s*[\"\']?(posters/[^\s>\"\']+\.(?:jpg|jpeg|png))',text,re.I)
   if not basename:raise ValueError('Source has no linked poster master')
   base=basename.group(1);ext=base.rsplit('.',1)[1];stem=base.rsplit('.',1)[0]
   sizes=[stem+'_xxlg.'+ext,stem+'_xlg.'+ext,base]
   best=None
   for image in sizes:
    imageurl=page.rsplit('/',1)[0]+'/'+image
    try:
     data=fetch(imageurl)
     with Image.open(io.BytesIO(data)) as im:im.load();w,h=im.size
     if max(w,h)<1200:continue
     path=OUT/(hashlib.sha256(imageurl.encode()).hexdigest()[:20]+'.'+ext);path.write_bytes(data);best=(imageurl,path,w,h,data);break
    except Exception:continue
   if not best:raise ValueError('No sufficiently large native poster scan')
   design=re.findall(r'Poster\s+(?:design|illustration)\s+by\s*<a[^>]+>(.*?)</a>',text,re.I)
   result.update(status='source_acquired_visual_review_required',source_page=page,source_title=heading,url=best[0],recovery_local_source=best[1].relative_to(ROOT).as_posix(),width=best[2],height=best[3],design_credit=[re.sub('<[^>]+>','',html.unescape(s)).strip() for s in design],verification={'sha256':hashlib.sha256(best[4]).hexdigest(),'native_dimensions':[best[2],best[3]]})
   (OUT/(key(subject)+'.html')).write_bytes(body);break
  except Exception as error:attempts.append({'url':page,'error':str(error)})
 result['attempts']=attempts
 receipt.write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf8');return result
rows=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 for future in as_completed([pool.submit(acquire,s) for s in subjects]):
  row=future.result();rows.append(row);print(row['subject'],row['status'],row.get('width'),row.get('height'),flush=True)
(OUT/'acquisition-audit.json').write_text(json.dumps({'schema_version':1,'entries':rows},ensure_ascii=True,indent=2)+'\n',encoding='utf8')
print('Acquired',sum(r['status']!='hold' for r in rows),'of',len(rows),flush=True)
