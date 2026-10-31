"""One bounded local-only HTTP pass over the real installer worker."""
from pathlib import Path
import hashlib,http.server,io,json,os,subprocess,tarfile,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[1]
BIN=ROOT/'build/collection-installer-driver'
class Handler(http.server.BaseHTTPRequestHandler):
 records=[];payload={};fail_once=set();ignore_range=set();wrong_range=set()
 def log_message(self,*args):pass
 def do_GET(self):
  data=self.payload[self.path];range_header=self.headers.get('Range');begin=int(range_header.split('=')[1].split('-')[0])if range_header else 0
  self.records.append((self.path,range_header));ignore=self.path in self.ignore_range and range_header
  if ignore:begin=0
  self.send_response(206 if range_header and not ignore else 200)
  self.send_header('Content-Length',str(len(data)-begin))
  if range_header and not ignore:self.send_header('Content-Range',f'bytes {begin+(1 if self.path in self.wrong_range else 0)}-{len(data)-1}/{len(data)}')
  self.end_headers();cut=self.path in self.fail_once
  if cut:self.fail_once.remove(self.path)
  try:
   for at in range(begin,len(data),16384):
    self.wfile.write(data[at:at+16384]);self.wfile.flush();time.sleep(.001)
    if cut and at>=131072:self.close_connection=True;return
  except (BrokenPipeError,ConnectionResetError):pass
def tar(files):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w',format=tarfile.USTAR_FORMAT)as archive:
  for name,data in files:
   info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;archive.addfile(info,io.BytesIO(data))
 return b.getvalue()
def sha(data):return hashlib.sha256(data).hexdigest()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}';results=[]
with tempfile.TemporaryDirectory(prefix='pm-collection-')as tmp:
 tmp=Path(tmp);picture=os.urandom(1024*1024);index=b'{"images":{}}'
 good=tar([('assets/images/manifest.json',index),('assets/images/full/example.jpg',picture)])
 def manifest(case,payloads=None,**extra):
  folder=tmp/case;folder.mkdir();packs=[]
  for n,data in enumerate(payloads or[good]):
   url=f'/{case}-{n}.tar';Handler.payload[url]=data;packs.append({'id':f'pack-{n}','url':base+url,'sha256':sha(data),'bytes':len(data),'format':'tar'})
  value={'schema_version':1,'collection_id':'fixture','version':'1','image_manifest_sha256':sha(index),'packs':packs};value.update(extra)
  path=folder/'collection-packs.json';path.write_text(json.dumps(value),encoding='utf8');return folder,path,value
 def run(case,folder,path,mode):
  p=subprocess.run([str(BIN),str(path),str(folder/'data'),mode],capture_output=True,text=True,timeout=25)
  assert p.returncode==0,(case,p.stdout,p.stderr);results.append({'case':case,'result':p.stdout.strip()});return p
 # Interrupted response, Range resume and reset when a server ignores Range.
 for case in ['resume','range-ignored']:
  folder,path,m=manifest(case);Handler.fail_once.add('/'+case+'-0.tar')
  if case=='range-ignored':Handler.ignore_range.add('/'+case+'-0.tar')
  run(case,folder,path,'retry');requests=[r for r in Handler.records if r[0]=='/'+case+'-0.tar'];assert requests[0][1]is None and any(r[1]for r in requests[1:])
  if case=='range-ignored':assert requests[-1][1]is None
  ready=next((folder/'data/collection').glob('fixture-*'));assert(ready/'assets/images/full/example.jpg').read_bytes()==picture
 # Pausing commits the partial prefix, resumes it, and never exposes a stage root.
 folder,path,m=manifest('pause');run('pause',folder,path,'pause');assert any(r[0]=='/pause-0.tar'and r[1]for r in Handler.records)
 folder,path,m=manifest('cancel');run('cancel',folder,path,'cancel');run('cancel-retry',folder,path,'normal')
 # Complete bundled installations never make a network request.
 folder,path,m=manifest('bundled');before=len(Handler.records);run('bundled',folder,path,'bundled');assert len(Handler.records)==before
 # A complete installed version can start again while the network is unavailable.
 before=len(Handler.records);run('ready-restart',tmp/'resume',tmp/'resume/collection-packs.json','normal');assert len(Handler.records)==before
 # Wrong pack/index hashes never activate data. A valid hash does not authorize traversal.
 folder,path,m=manifest('hash-wrong');m['packs'][0]['sha256']='0'*64;path.write_text(json.dumps(m));run('hash-wrong',folder,path,'fail');assert not list((folder/'data/collection').glob('fixture-*'))
 folder,path,m=manifest('index-wrong',image_manifest_sha256='0'*64);run('index-wrong',folder,path,'fail')
 unsafe=tar([('assets/images/manifest.json',index),('../../escape',b'bad')]);folder,path,m=manifest('traversal',[unsafe]);run('traversal',folder,path,'fail');assert not(tmp/'escape').exists()
 # A link entry, even to an in-tree-looking target, is rejected.
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w',format=tarfile.USTAR_FORMAT)as archive:
  entry=tarfile.TarInfo('assets/images/link.jpg');entry.type=tarfile.SYMTYPE;entry.linkname='../../escape';archive.addfile(entry)
 folder,path,m=manifest('link',[b.getvalue()]);run('link',folder,path,'fail')
 # Existing symlink parents and partial output files cannot redirect extraction.
 folder,path,m=manifest('symlink-parent');stage=folder/'data/collection'/('.stage-fixture-'+sha(path.read_bytes())[:24]);stage.mkdir(parents=True);outside=folder/'outside';outside.mkdir();(stage/'assets').symlink_to(outside,target_is_directory=True);run('symlink-parent',folder,path,'fail');assert not list(outside.iterdir())
 folder,path,m=manifest('partial-stage');stage=folder/'data/collection'/('.stage-fixture-'+sha(path.read_bytes())[:24]);(stage/'assets/images/full').mkdir(parents=True);(stage/'assets/images/full/example.jpg').write_bytes(b'partial');(stage/'assets/images/full/example.jpg.install-tmp').write_bytes(b'incomplete');run('partial-stage',folder,path,'normal');ready=next((folder/'data/collection').glob('fixture-*'));assert(ready/'assets/images/full/example.jpg').read_bytes()==picture
 # A real process exits mid-pack2; a new instance retains pack1 and resumes pack2.
 second=tar([('assets/images/full/second.jpg',picture)]);folder,path,m=manifest('power-loss',[good,second]);run('power-loss-crash',folder,path,'crash-second');assert not list((folder/'data/collection').glob('fixture-*'));before=sum(r[0]=='/power-loss-0.tar'for r in Handler.records);run('power-loss-recover',folder,path,'normal');assert sum(r[0]=='/power-loss-0.tar'for r in Handler.records)==before;assert any(r[0]=='/power-loss-1.tar'and r[1]for r in Handler.records)
 # Invalid persisted metadata is treated as incomplete, not parsed with throwing value().
 folder,path,m=manifest('bad-marker');stage=folder/'data/collection'/('.stage-fixture-'+sha(path.read_bytes())[:24]);stage.mkdir(parents=True);(stage/'.pack-0.json').write_text('{"sha256":42}');run('bad-marker',folder,path,'normal')
 folder,path,m=manifest('unsafe-config');m['packs'][0]['url']='file:///etc/passwd';path.write_text(json.dumps(m));run('unsafe-config',folder,path,'invalid')
 # Low space is rejected before HTTP; ENOSPC during extraction is explicit.
 folder,path,m=manifest('space-low',expanded_bytes=len(picture)+len(index));before=len(Handler.records);run('space-low',folder,path,'space-low');assert len(Handler.records)==before
 folder,path,m=manifest('space-write');run('space-write',folder,path,'space-write')
 # Ready markers cannot hide missing/truncated files or a modified small index.
 folder=tmp/'resume';path=folder/'collection-packs.json';ready=next((folder/'data/collection').glob('fixture-*'));(ready/'assets/images/full/example.jpg').write_bytes(b'truncated');before=len(Handler.records);run('ready-truncation-repair',folder,path,'normal');assert len(Handler.records)>before and(ready/'assets/images/full/example.jpg').read_bytes()==picture
 (ready/'assets/images/manifest.json').write_bytes(index.replace(b'images',b'broken'));before=len(Handler.records);run('ready-index-repair',folder,path,'normal');assert len(Handler.records)>before and(ready/'assets/images/manifest.json').read_bytes()==index
server.shutdown();report={'status':'PASS','cases':results,'request_count':len(Handler.records),'external_network':False};out=ROOT/'build/collection-installer-tests';out.mkdir(exist_ok=True);(out/'report.json').write_text(json.dumps(report,indent=2));print('PASS',len(results),'targeted cases; NIST SHA256, HTTP resume/pause/cancel/retry, hashes, USTAR/link safety and process-restart recovery')
