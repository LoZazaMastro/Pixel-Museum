"""Resolve named original licensed song publications without downloading media."""
from pathlib import Path
import hashlib,json,importlib.util,subprocess,concurrent.futures,datetime
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'build/research/soundtrack-broad/burnout-revenge-licensed-original'
spec=importlib.util.spec_from_file_location('video',ROOT/'tools/discover-museum-videos.py');video=importlib.util.module_from_spec(spec);spec.loader.exec_module(video)
load=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
inventory=load(BASE/'licensed-original41-research-inventory.json')['songs']
ids=['0qisdneiTHE','VNCjXzR_w3Y','gF9CIQS9T_8','ytA14Npv_rA','7bDg7n-chhU','DcLVpNJ-M0E','2R6S5CJWlco','o6QDNLsrr5Y','TYlirm4mIAM','a59N2laOirw','l1T3MiVC7oQ','YzMyo9nyqtA','H0h1suV_l4Q','-Y4jNjjQi5c','YBPKr7d9RS0','C6MOKXm8x50','q8e4WbhFu6A','I6CZqVrIP3g','on1Txcamcjs','uKxudXzlJUE','HcYD0HorUtM','cmsRvmY1R6E','-Ue193sAcrE','AMgf9FyR_Os','rHa2PYjlYx8','V9oiVccXNcI','gWQd7Ou5CX8','D9MFpXDqpZI','reTOPtbXZIM','Aseh7GN20GE','N3vh62WvZqI','AI73WHog3tk','RplG-7hCY2Y','el78rnEeRo8','W7l8Bf8s9gI','HXhrl-KIG50','AZcS-gLWaCQ','ia8l4z609rE','KCA55egtZwc','vK20cYuFmbM','7a9wJIhq2J8']
assert len(ids)==len(set(ids))==len(inventory)==41
def resolve(args):
    i,song,vid=args;row=dict(ordinal=i+1,**song,youtube_id=vid)
    wp=ROOT/'build/research/soundtrack-broad/watch'/(vid+'.json')
    try:
        if wp.exists():w=load(wp)
        else:
            cmd=[str(video.YTDLP),'--skip-download','--dump-single-json','--no-warnings','--ignore-no-formats-error','--no-check-formats','--socket-timeout','10','--retries','0','--extractor-retries','0','--extractor-args','youtube:player_skip=webpage,configs;player_client=android','https://www.youtube.com/watch?v='+vid]
            run=subprocess.run(cmd,capture_output=True,encoding='utf8',errors='replace',timeout=35)
            if run.returncode or not run.stdout.strip():raise ValueError(run.stderr[-300:])
            raw=json.loads(run.stdout);w={k:raw.get(v,'') for k,v in [('title','title'),('author','channel'),('channelId','channel_id'),('shortDescription','description')]};w.update(lengthSeconds=str(raw.get('duration') or 0),status='OK',availability=raw.get('availability'),checked=datetime.datetime.now(datetime.timezone.utc).isoformat(),metadata_source='Actual public player via yt-dlp; no media download')
            assert w['title'] and w['channelId'];save(wp,w)
        native=video.metadata(vid,{'title':w['title'],'channel':w['author']})
        assert native['native_compatible_avc_aac'] and native['channel_id']==w['channelId'] and native['duration']==float(w['lengthSeconds'])
        row.update(status='NATIVE_POSITIVE_PENDING_RECORDING_REVIEW',watch_path=wp.relative_to(ROOT).as_posix(),native_path='build/research/video-discovery/video-'+vid+'.json',actual_title=w['title'],actual_uploader=w['author'],duration=native['duration'],description=w['shortDescription'])
    except Exception as err:row.update(status='HELD',reason=str(err))
    return row
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for row in pool.map(resolve,[(i,song,vid) for i,(song,vid) in enumerate(zip(inventory,ids))]):
        rows.append(row);save(BASE/'native41-first-publication-research.json',rows);print(row['ordinal'],row['artist'],row['status'],flush=True)
