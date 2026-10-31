"""Read public curated game-music catalogue metadata, without media downloads."""
import concurrent.futures,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/research/soundtrack-broad/curated-catalogs';OUT.mkdir(exist_ok=True)
CHANNELS={'UC4bD7uDwMsPBnUo4CBcYk1g':'Game Music Daily','UC4tDiCTWpnKXadolAqF8g4g':'Good Video Game Music','UCbzxEUpa4_-gK2upd9uwHrw':'VideoGameMusic'}
def index(item):
 cid,name=item;path=OUT/(cid+'.json')
 if path.exists():return name,len(json.loads(path.read_text())['entries']),'cached'
 cmd=[r'C:/Users/Andrea/homebrew/plugins/themedeck/yt-dlp.exe','--flat-playlist','--playlist-end','5000','--dump-single-json','--skip-download','--no-warnings','--socket-timeout','12','--retries','1','https://www.youtube.com/channel/'+cid+'/videos']
 result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=240)
 if result.returncode:raise RuntimeError(name+': '+result.stderr[-500:])
 data=json.loads(result.stdout);rows=[{k:r.get(k) for k in ['id','title','channel','channel_id','duration','description']} for r in data.get('entries',[]) if r]
 out={'publication_status':'research_only','source_page':'https://www.youtube.com/channel/'+cid+'/videos','channel_id':cid,'name':name,'description':data.get('description',''),'scope':'Candidate discovery only. Every actual recording still requires original-game/edition/platform/composer verification and native metadata before editorial admission. No audio/video downloaded.','entries':rows}
 t=path.with_suffix('.json.tmp');t.write_text(json.dumps(out,ensure_ascii=True,indent=2)+'\n');t.replace(path)
 return name,len(rows),'saved'
for row in concurrent.futures.ThreadPoolExecutor(max_workers=2).map(index,CHANNELS.items()):print(row,flush=True)
