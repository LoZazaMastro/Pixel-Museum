"""Different-root recovery using the actual worker and local HTTP only."""
from pathlib import Path
import hashlib,http.server,io,json,os,shutil,subprocess,tarfile,tempfile,threading,time
root=Path(__file__).resolve().parents[1]
binary=root/'build/collection-installer-driver'
class HTTP(http.server.BaseHTTPRequestHandler):
    payload={};requests=[]
    def log_message(self,*args):pass
    def do_GET(self):
        data=self.payload[self.path];header=self.headers.get('Range');offset=int(header.split('=')[1].split('-')[0]) if header else 0
        self.requests.append((self.path,header));self.send_response(206 if header else 200);self.send_header('Content-Length',str(len(data)-offset))
        if header:self.send_header('Content-Range',f'bytes {offset}-{len(data)-1}/{len(data)}')
        self.end_headers()
        try:
            for start in range(offset,len(data),16384):self.wfile.write(data[start:start+16384]);self.wfile.flush();time.sleep(.001)
        except (BrokenPipeError,ConnectionResetError):pass
def sha(data):return hashlib.sha256(data).hexdigest()
def archive(files):
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w',format=tarfile.USTAR_FORMAT) as tar:
        for name,data in files:
            entry=tarfile.TarInfo(name);entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
    return output.getvalue()
def snapshot(folder):return {str(p.relative_to(folder)):('LINK:'+os.readlink(p) if p.is_symlink() else sha(p.read_bytes())) for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),HTTP);threading.Thread(target=server.serve_forever,daemon=True).start();results=[]
with tempfile.TemporaryDirectory(prefix='pm-migration-') as temporary:
    base=Path(temporary);old=base/'legacy';new=base/'preferred';index=b'{"images":{}}';first=os.urandom(2<<20);second=os.urandom(3<<20)
    packs=[archive([('assets/images/manifest.json',index),('assets/images/first.jpg',first)]),archive([('assets/images/second.jpg',second)])]
    rows=[]
    for n,data in enumerate(packs):
        path=f'/pack-{n}.tar';HTTP.payload[path]=data;rows.append({'id':f'pack-{n}','url':f'http://127.0.0.1:{server.server_port}{path}','bytes':len(data),'sha256':sha(data),'format':'tar','file_count':2 if n==0 else 1,'expanded_bytes':len(first)+len(index) if n==0 else len(second)})
    manifest=base/'collection-packs.json';manifest.write_text(json.dumps({'schema_version':1,'collection_id':'fixture','image_manifest_sha256':sha(index),'expanded_bytes':len(first)+len(second)+len(index),'file_count':3,'packs':rows}))
    def run(name,destination,mode='normal',legacy=None):
        command=[str(binary),str(manifest),str(destination),mode]
        if legacy is not None:command.append(str(legacy))
        p=subprocess.run(command,capture_output=True,text=True,timeout=25);assert p.returncode==0,(name,p.stdout,p.stderr);results.append({'case':name,'result':p.stdout.strip()});return json.loads(p.stdout) if p.stdout.strip() else None
    run('legacy-process-loss',old,'crash-second');stage=next((old/'collection').glob('.stage-*'));assert (stage/'.pack-0.json').exists()
    (stage/'assets/images/orphan.install-tmp').write_bytes(b'ignore this unfinished file');before=snapshot(old);first_requests=sum(x[0]=='/pack-0.tar' for x in HTTP.requests)
    migrated=run('migrate-pause-resume',new,'pause-migrate',old);assert migrated['paused'] and migrated['retried'];assert snapshot(old)==before
    assert sum(x[0]=='/pack-0.tar' for x in HTTP.requests)==first_requests;assert any(x[0]=='/pack-1.tar' and x[1] for x in HTTP.requests)
    ready=Path(migrated['root']);assert (ready/'assets/images/first.jpg').read_bytes()==first and (ready/'assets/images/second.jpg').read_bytes()==second
    assert not (ready/'assets/images/orphan.install-tmp').exists();assert not list((new/'collection').glob('.write-probe-*.tmp'))
    receipts=list((new/'collection').glob('.write-probe-*.json'));assert len(receipts)==1 and json.loads(receipts[0].read_text())['bytes']==16<<20
    current=snapshot(new);requests=len(HTTP.requests);reused=run('reuse-legacy-ready',base/'unused-preferred',legacy=new);assert reused['root']==str(ready) and len(HTTP.requests)==requests and snapshot(new)==current;assert not (base/'unused-preferred').exists()
    blocker=base/'not-a-directory';blocker.write_bytes(b'keep');requests=len(HTTP.requests);run('preferred-unwritable-fails-closed',blocker,'fail',old);assert len(HTTP.requests)==requests and snapshot(old)==before
    requests=len(HTTP.requests);run('preferred-enospc-fails-closed',base/'full-preferred','space-write',old);assert len(HTTP.requests)==requests and snapshot(old)==before
    crash_destination=base/'crash-preferred';requests=sum(x[0]=='/pack-0.tar' for x in HTTP.requests);run('migration-process-loss',crash_destination,'crash-migrate',old);assert not list((crash_destination/'collection').glob('fixture-*'));recovered=run('migration-process-loss-recovery',crash_destination,legacy=old);assert sum(x[0]=='/pack-0.tar' for x in HTTP.requests)==requests and snapshot(old)==before;assert (Path(recovered['root'])/'assets/images/first.jpg').read_bytes()==first;assert not list((crash_destination/'collection').rglob('*.migration-tmp'))
    bad=base/'legacy-invalid';shutil.copytree(old,bad);badstage=next((bad/'collection').glob('.stage-*'));(badstage/'.pack-0.json').write_text('{"sha256":"wrong"}');bad_before=snapshot(bad);requests=sum(x[0]=='/pack-0.tar' for x in HTTP.requests);run('invalid-checkpoint-redownloaded',base/'repair-preferred',legacy=bad);assert sum(x[0]=='/pack-0.tar' for x in HTTP.requests)==requests+1 and snapshot(bad)==bad_before
    linked=base/'legacy-linked';shutil.copytree(old,linked);linkedstage=next((linked/'collection').glob('.stage-*'));outside=base/'outside-assets';shutil.move(str(linkedstage/'assets'),str(outside));(linkedstage/'assets').symlink_to(outside,target_is_directory=True);linked_before=snapshot(linked);outside_before=snapshot(outside);requests=len(HTTP.requests);run('legacy-parent-symlink-rejected',base/'safe-preferred','fail',linked);assert len(HTTP.requests)==requests and snapshot(linked)==linked_before and snapshot(outside)==outside_before
server.shutdown();out=root/'build/collection-installer-tests/migration-report.json';out.write_text(json.dumps({'status':'PASS','cases':results,'external_network':False},indent=2));print('PASS',len(results),'migration cases; source unchanged, verified checkpoints reused, partial Range, pause/retry, ready reuse, ENOSPC and link safety')
