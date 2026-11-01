"""Archive-backed worker: pinned indexes, mixed checkpoints and crash recovery."""
from pathlib import Path
import hashlib,http.server,io,json,os,subprocess,tarfile,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[1];BIN=Path(os.environ.get('PM_INSTALLER_DRIVER',ROOT/'build/collection-installer-driver'))
class HTTP(http.server.BaseHTTPRequestHandler):
    payload={};requests=[];fail=set()
    def log_message(self,*args):pass
    def do_GET(self):
        data=self.payload[self.path];header=self.headers.get('Range');offset=int(header.split('=')[1].split('-')[0])if header else 0;self.requests.append((self.path,header));cut=self.path in self.fail
        if cut:self.fail.remove(self.path)
        self.send_response(206 if header else 200);self.send_header('Content-Length',str(len(data)-offset))
        if header:self.send_header('Content-Range',f'bytes {offset}-{len(data)-1}/{len(data)}')
        self.end_headers()
        try:
            for at in range(offset,len(data),16384):
                self.wfile.write(data[at:at+16384]);self.wfile.flush();time.sleep(.001)
                if cut and at>=131072:self.close_connection=True;return
        except(BrokenPipeError,ConnectionResetError):pass
def sha(data):return hashlib.sha256(data).hexdigest()
def tar(files):
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w',format=tarfile.USTAR_FORMAT)as archive:
        for name,data in files:
            info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
    data=out.getvalue()
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:')as archive:records=[{'path':x.name,'offset':x.offset_data,'bytes':x.size}for x in archive.getmembers()]
    return data,records
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),HTTP);threading.Thread(target=server.serve_forever,daemon=True).start();results=[]
with tempfile.TemporaryDirectory(prefix='pm-archive-')as temp:
    temp=Path(temp);registry=b'{"images":{}}';a=os.urandom(1<<20);b=os.urandom((3<<20)+123)
    def fixture(name):
        folder=temp/name;bundle=folder/'bundle';content=bundle/'content';content.mkdir(parents=True);(bundle/'assets/images').mkdir(parents=True);(bundle/'assets/images/manifest.json').write_bytes(registry)
        rows=[];indexed=[]
        for n,files in enumerate([[('assets/images/manifest.json',registry),('assets/images/a.jpg',a)],[('assets/images/b.jpg',b)]]):
            data,records=tar(files);url=f'/{name}-{n}.tar';HTTP.payload[url]=data;row={'id':f'pack-{n}','url':f'http://127.0.0.1:{server.server_port}{url}','sha256':sha(data),'bytes':len(data),'format':'tar','file_count':len(records),'expanded_bytes':sum(x['bytes']for x in records)};rows.append(row);indexed.append({k:row[k]for k in('id','sha256','bytes')}|{'files':records})
        manifest={'schema_version':1,'collection_id':'fixture','image_manifest_sha256':sha(registry),'file_count':3,'expanded_bytes':len(registry)+len(a)+len(b),'packs':rows};index={'schema_version':1,'collection_id':'fixture','image_manifest_sha256':sha(registry),'packs':indexed}
        path=content/'collection-packs.json';path.write_text(json.dumps(manifest));indexpath=content/'collection-archive-index.json';indexpath.write_text(json.dumps(index));return folder,bundle,path,indexpath,manifest,index
    def run(name,fixture,mode='normal',service_mode=None):
        folder,bundle,path,_,_,_=fixture;env=dict(os.environ)
        if service_mode:env['PM_SERVICE_TEST_MODE']=service_mode
        p=subprocess.run([str(BIN),str(path),str(folder/'data'),mode,'',str(bundle)],env=env,capture_output=True,text=True,timeout=25);assert p.returncode==0,(name,p.stdout,p.stderr);value=json.loads(p.stdout)if p.stdout.strip()else{};results.append({'case':name,'result':value});return value
    def verify(f,value,mixed=False):
        ready=Path(value['root']);folder,bundle,path,indexpath,manifest,index=f;assert(ready/'assets/images/manifest.json').read_bytes()==registry
        for n,record in enumerate(index['packs']):
            marker=json.loads((ready/f'.pack-{n}.json').read_text())
            if mixed and n==0:assert'storage'not in marker and(ready/'assets/images/a.jpg').read_bytes()==a;continue
            assert marker['storage']=='archive';archive=ready/marker['archive'];assert sha(archive.read_bytes())==manifest['packs'][n]['sha256']
            with archive.open('rb')as stream:
                for file in record['files']:
                    stream.seek(file['offset']);actual=stream.read(file['bytes']);expected=registry if file['path'].endswith('manifest.json')else(a if file['path'].endswith('a.jpg')else b);assert actual==expected
        assert not(ready/'assets/images/b.jpg').exists();return ready
    f=fixture('full');v=run('archive-only-install',f);ready=verify(f,v);before=len(HTTP.requests);again=run('archive-ready-offline',f);assert again['root']==str(ready)and len(HTTP.requests)==before
    f=fixture('resume');HTTP.fail.add('/resume-0.tar');v=run('archive-network-retry',f,'retry');verify(f,v);assert any(path=='/resume-0.tar'and header for path,header in HTTP.requests)
    f=fixture('pause');v=run('archive-pause-tail-flush',f,'pause');verify(f,v);assert v['paused']and v['retried']and any(path=='/pause-0.tar'and header for path,header in HTTP.requests)
    f=fixture('mixed');f[3].unlink();run('legacy-first-pack-process-loss',f,'crash-second');f[3].write_text(json.dumps(f[5]));before=sum(path=='/mixed-0.tar'for path,_ in HTTP.requests);v=run('mixed-physical-first-archive-second',f);verify(f,v,True);assert sum(path=='/mixed-0.tar'for path,_ in HTTP.requests)==before
    f=fixture('checkpoint');run('archive-checkpoint-enospc',f,'archive-checkpoint-full');stage=next((f[0]/'data/collection').glob('.stage-*'));assert list((stage/'archives').glob('*.tar'))and not(stage/'.pack-0.json').exists();before=sum(path=='/checkpoint-0.tar'for path,_ in HTTP.requests);v=run('promoted-archive-recovery-no-redownload',f);verify(f,v);assert sum(path=='/checkpoint-0.tar'for path,_ in HTTP.requests)==before
    for name,mutate in [('bad-path',lambda j:j['packs'][0]['files'][0].update(path='../escape')),('bad-offset',lambda j:j['packs'][0]['files'][0].update(offset=2**63)),('bad-count',lambda j:j['packs'][0]['files'].pop()),('bad-duplicate',lambda j:j['packs'][1]['files'][0].update(path='assets/images/a.jpg'))]:
        f=fixture(name);mutate(f[5]);f[3].write_text(json.dumps(f[5]));before=len(HTTP.requests);v=run(name,f,'fail');assert not v['ready']and len(HTTP.requests)==before and not list((f[0]/'data/collection').glob('fixture-*'))
    f=fixture('bad-sha');f[4]['packs'][0]['sha256']='0'*64;f[5]['packs'][0]['sha256']='0'*64;f[2].write_text(json.dumps(f[4]));f[3].write_text(json.dumps(f[5]));v=run('archive-ondisk-sha-rejection',f,'fail');assert not v['ready']and not list((f[0]/'data/collection').glob('fixture-*'))
    f=fixture('bad-registry');(f[1]/'assets/images/manifest.json').write_bytes(b'wrong');v=run('bundled-registry-sha-rejection',f,'fail');assert not v['ready']and not list((f[0]/'data/collection').glob('fixture-*'))
    if os.environ.get('PM_WRITER_BACKEND_TEST'):
        def events(f):return [json.loads(line)for line in(f[0]/'data/writer-events.jsonl').read_text().splitlines()]
        f=fixture('service-missing');before=len(HTTP.requests);v=run('missing-service-no-fallback',f,'fail','unavailable');assert 'Installation service unavailable'in v['error']and len(HTTP.requests)==before and not list((f[0]/'data/collection/downloads').glob('*.part'))
        f=fixture('service-rewind');downloads=f[0]/'data/collection/downloads';downloads.mkdir(parents=True);(downloads/(f[4]['packs'][0]['sha256']+'.tar.part')).write_bytes(HTTP.payload['/service-rewind-0.tar'][:4096]);v=run('service-open-offset-authoritative',f,service_mode='rewind');verify(f,v);assert [header for path,header in HTTP.requests if path=='/service-rewind-0.tar']==[None]
        f=fixture('service-finish');v=run('service-finish-ack-failure',f,'fail','finish-fail');assert 'Installation service unavailable'in v['error']and not list((f[0]/'data/collection').glob('fixture-*'));before=sum(path=='/service-finish-0.tar'for path,_ in HTTP.requests);v=run('service-finish-full-cache-recovery',f);verify(f,v);assert sum(path=='/service-finish-0.tar'for path,_ in HTTP.requests)==before
        recorded=events(f);assert any(item['event']=='open'and item['bytes']==f[4]['packs'][0]['bytes']for item in recorded)
        for case in('pause','resume'):
            folder=temp/case;recorded=[json.loads(line)for line in(folder/'data/writer-events.jsonl').read_text().splitlines()];assert any(item['event']=='finish'and 0<item['bytes']<len(HTTP.payload['/'+case+'-0.tar'])for item in recorded)
server.shutdown();name='service-backend-report.json'if os.environ.get('PM_WRITER_BACKEND_TEST')else'archive-report.json';out=ROOT/'build/collection-installer-tests'/name;out.write_text(json.dumps({'status':'PASS','cases':results,'external_network':False},indent=2));print('PASS',len(results),'archive/service cases; no image extraction, mixed legacy reuse, raw Range/resume, checkpoint recovery, invalid indexes/SHA/registry rejected')
