"""Read exact publisher-supplied Spider-Man album inventories and role tables."""
import hashlib,html,json,pathlib,re,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/soundtrack-broad/spider-complete';OUT.mkdir(exist_ok=True)
albums=[
 {'entry_id':'workbook-09-07-marvels-spider-man','title':"Marvel's Spider-Man",'year':2018,'url':'https://www.qobuz.com/us-en/album/marvels-spider-man-john-paesano/ec7acrjo9udgb','expected':27},
 {'entry_id':'wikipedia-64248753','title':"Marvel's Spider-Man: Miles Morales",'year':2020,'url':'https://www.qobuz.com/au-en/album/marvels-spider-man-miles-morales-john-paesano/c3mpi3335y7ab'},
 {'entry_id':'wikipedia-68687157','title':"Marvel's Spider-Man 2",'year':2023,'url':'https://www.qobuz.com/us-en/album/marvels-spider-man-2-john-paesano/by0k8544c5uwc','expected':21},
]
for album in albums:
 dest=OUT/(str(album['year'])+'-label.html')
 if not dest.exists():
  raw=urllib.request.urlopen(urllib.request.Request(album['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read().decode('utf-8')
  assert 'John Paesano' in raw and 'Marvel Music' in raw
  raw=re.sub(r'\sdata-source="[^"]*"',' data-source="[preview transport URL omitted]"',raw);dest.write_text(raw,encoding='utf-8')
 raw=dest.read_text(encoding='utf-8');tracks=[]
 for block in raw.split('<div class="player__item">')[1:]:
  m=re.search(r'data-track-v2="(.*?)"',block,re.S)
  if not m:continue
  row=json.loads(html.unescape(m.group(1)));dur=re.search(r'track__item--duration">(.*?)<',block)
  row.update(album_number=len(tracks)+1,duration=dur.group(1),credits=[html.unescape(x) for x in re.findall(r'<p class="track__info">(.*?)</p>',block,re.S)])
  tracks.append(row)
 if album.get('expected'):assert len(tracks)==album['expected'],(album['title'],len(tracks))
 album.update(expected_tracks=len(tracks),tracks=tracks,primary_source_receipt={'url':album['url'],'local_file':dest.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'actual_body_retrieved':True,'preview_transport_urls_removed':True})
 print(album['title'],len(tracks),flush=True)
 for track in tracks:print(track['album_number'],track['item_name'],track['credits'][0]if track['credits']else'NO CUE CREDIT SUPPLIED',flush=True)
(OUT/'original-three-albums-inventory.json').write_text(json.dumps({'albums':albums},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
