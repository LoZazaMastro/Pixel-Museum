"""Research public licensed songs; never import score filler or mutate production."""
from pathlib import Path
import hashlib,json,urllib.request,datetime,importlib.util,concurrent.futures
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'build/research/soundtrack-broad/burnout-revenge-licensed-original';BASE.mkdir(exist_ok=True,parents=True)
spec=importlib.util.spec_from_file_location('video',ROOT/'tools/discover-museum-videos.py');video=importlib.util.module_from_spec(spec);spec.loader.exec_module(video)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sources=[('gamespot-track-announcement.html','https://www.gamespot.com/articles/yellowcard-headlines-burnout-revenge-soundtrack/1100-6131734/'),('ea-2007-trax-primary.html','https://www.nintendoworldreport.com/pr/13027/ea-trax-now-on-itunes')]
receipts=[]
for name,url in sources:
    p=BASE/name
    if not p.exists():
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:p.write_bytes(r.read());status=r.status
        except Exception as err:receipts.append(dict(url=url,status='held',error=str(err)));continue
    else:status='cached_actual_html'
    receipts.append(dict(path=p.relative_to(ROOT).as_posix(),url=url,status=status,sha256=sha(p)))
save(BASE/'source-fetch-receipts.json',receipts)
print(json.dumps(receipts,indent=2))
licensed=[
('Andy Hunter','Come On'),('Animal Alpha','Bundy'),('Apocalyptica','Life Burns!'),('Asian Dub Foundation','Flyover'),('Avenged Sevenfold','Beast and the Harlot'),('Billy Talent','Red Flag'),('Bloc Party','Helicopter'),('Bullet For My Valentine','Hand Of Blood'),('The Chemical Brothers','The Big Jump'),('CKY','As The Tables Turn'),('Comeback Kid','Wake The Dead'),('The Dead 60s','Riot Radio'),('Dogs','Tuned to a Different Station'),('The Doors','Break On Through (To The Other Side) BT vs. The Doors Remix'),('Emanuel','The Hey Man!'),('Fall Out Boy','Dance, Dance'),('Finch','Ink'),('Funeral For A Friend','All The Rage'),('Goldfinger','I Want'),('Infusion','Better World (Adam Freeland Mix)'),('Junkie XL','Today'),('LCD Soundsystem','Daft Punk Is Playing At My House (Soulwax Shibuya Mix)'),('Maximo Park','Apply Some Pressure'),('Mindless Self Indulgence','Straight To Video (KMFDM Remix)'),('Morningwood','Nu Rock'),('MxPx','Heard That Sound'),('Nine Black Alps','Shot Down'),('OK Go','Do What You Want'),('Pennywise','Stand Up'),('The Academy Is...','Almost Here'),('The All-American Rejects','Top Of The World'),('The Black Velvets','Fear And Loathing'),('The Bravery','An Honest Mistake (Superdiscount Remix)'),('The Outline','Shotgun'),('The Starting Line','The World'),('Thrice','Lullaby'),('Timo Maas','First Day (General Midi Remix)'),('Tsar','Band-Girls-Money'),('Unwritten Law','F.I.G.H.T.'),('We Are Scientists','The Great Escape'),('Yellowcard','Lights And Sounds')]
assert len(licensed)==41
save(BASE/'licensed-original41-research-inventory.json',dict(status='RESEARCH_ONLY',gamespot_publisher_announcement_url=sources[0][1],original_credit_transcription_url='https://www.mobygames.com/game/19356/burnout-revenge/credits/ps2/',source_access_scope='The contemporary announcement and original credit transcription were read through web-search indexed text. Direct GameSpot and Moby HTTP403 are not represented as acquired HTML. EA2007press release is separately cached actualHTML and corroborates the licensing programme, not every individual song mapping.',songs=[dict(artist=a,title=t) for a,t in licensed],score_filler_included=False,retail_order_claimed=False))
def find(row):
    a,t=row;query=a+' '+t+' official audio'
    try:return dict(artist=a,title=t,query=query,search=video.search(query))
    except Exception as err:return dict(artist=a,title=t,query=query,error=str(err))
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for row in pool.map(find,licensed):rows.append(row);save(BASE/'public-song-search41-research.json',rows);print(len(rows),row['artist'],row['title'],flush=True)
