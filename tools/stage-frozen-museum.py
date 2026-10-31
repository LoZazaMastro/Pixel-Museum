"""Local-only guarded final folder staging; never connects to a console."""
import argparse,hashlib,json,shutil,subprocess,datetime,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--qa',required=True);p.add_argument('--recovery-manifest',required=True);p.add_argument('--recovery-verification',required=True);p.add_argument('--output-receipt-dir',required=True);a=p.parse_args()
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf8'))
def rec(path):return dict(path=path.relative_to(R).as_posix(),bytes=path.stat().st_size,sha256=sha(path))
qa=load(R/a.qa);recovery=load(R/a.recovery_manifest);rv=load(R/a.recovery_verification)
assert qa['status'].startswith('PASS') and rv['status'].startswith('PASS')
assert rv['manifest_sha256']==sha(R/a.recovery_manifest)
assert recovery['scoped_verification_sha256']==sha(R/a.qa)
O=R/a.output_receipt_dir;assert O.resolve().is_relative_to((R/'build/research').resolve());O.mkdir(parents=True,exist_ok=True)
assert not (O/'verification.json').exists(),'Refuse to replace an earlier staging receipt'
def inputs_unchanged():
 for item in qa['catalogues']:
  assert sha(R/item['path'])==item['sha256'],item['path']
 assert sha(R/'build/eboot.elf')==qa['native']['sha256']=='71fba8ccff3f25efc1ad610c28b44d459513abc20cc0482ae4c026952a6059f7'
 for name,row in qa['fonts'].items():assert sha(R/name)==row['sha256'],name
inputs_unchanged()
app=R/'dist/PPSA70421';prior=O/'dist-before-final-staging'
assert app.resolve().parent==(R/'dist').resolve() and prior.resolve().is_relative_to(O.resolve())
assert not prior.exists(),'Original distribution backup already exists'
old=[]
if app.exists():
 old=[rec(f) for f in sorted(app.rglob('*')) if f.is_file()]
 app.rename(prior)
 for row in old:assert sha(prior/Path(row['path']).relative_to('dist/PPSA70421'))==row['sha256']
(O/'previous-dist.json').write_text(json.dumps(dict(preserved_directory=prior.relative_to(R).as_posix(),files=old),indent=2)+'\n')
app.mkdir(parents=True);(app/'sce_module').mkdir()
shutil.copytree(R/'sce_sys',app/'sce_sys')
(app/'assets').mkdir()
for src in sorted((R/'assets').iterdir()):
 if src.name=='images':continue
 if src.is_dir():shutil.copytree(src,app/'assets'/src.name)
 else:shutil.copy2(src,app/'assets'/src.name)
audio=app/'assets/audio';dirs=[audio/'music']+sorted((audio/'sfx').glob('*/'))
for folder in dirs:
 if folder.is_dir():(folder/'index.txt').write_text(''.join(n+'\n' for n in sorted(f.name for f in folder.iterdir() if f.is_file() and f.name!='index.txt')),encoding='utf8')
libc=R/'runtime/libc.prx';assert sha(libc)=='e6ff45d16adf687855cc3b33b0c8a4132b6504360b221e0a34c7e99fb3ba0036'
assert struct.unpack('<I',libc.read_bytes()[:4])[0]==0xeef51454
shutil.copy2(libc,app/'sce_module/libc.prx')
commands=[]
def run(args,name):
 commands.append(args)
 with (O/name).open('w',encoding='utf8') as out:subprocess.run(args,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
tool=str(R/'build/host/ps5-native-tool')
run([tool,'self','--sign','--in','build/eboot.elf','--out','dist/PPSA70421/eboot.bin','--magic','0x1D3D154F'],'sign.log')
run([tool,'self','--inspect','--file','dist/PPSA70421/eboot.bin'],'inspect-eboot.log')
run([tool,'self','--inspect','--file','dist/PPSA70421/sce_module/libc.prx'],'inspect-libc.log')
master=qa['catalogues'][0]['sha256'];runtime=qa['catalogues'][1]['sha256']
run(['python3','tools/package-museum.py','--folder-only','--skip-assemble','--expected-catalog-sha256',master,'--expected-runtime-sha256',runtime],'package-folder-only.log')
inputs_unchanged();assert sha(app/'content/catalog.json')==runtime
for src in (R/'assets/fonts').iterdir():
 if src.is_file():assert sha(src)==sha(app/'assets/fonts'/src.name),src.name
for src in (R/'sce_sys').rglob('*'):
 if src.is_file():assert sha(src)==sha(app/'sce_sys'/src.relative_to(R/'sce_sys'))
eboot=rec(app/'eboot.bin');report=O/'local-payload-plan.json'
run(['python3','tools/update-museum-ftp.py','--folder','dist/PPSA70421','--runtime-sha256',runtime,'--eboot-sha256',eboot['sha256'],'--report',str(report)],'local-plan.log')
result=dict(status='PASS_LOCAL_SIGNED_FOLDER_ONLY_STAGING_NO_FTP',timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),qa=rec(R/a.qa),recovery=rec(R/a.recovery_manifest),recovery_independent_verification=rec(R/a.recovery_verification),catalogues=qa['catalogues'],native_elf=qa['native'],signed_eboot=eboot,staged_runtime=rec(app/'content/catalog.json'),staged_param=rec(app/'sce_sys/param.json'),staged_libc=rec(app/'sce_module/libc.prx'),fonts=qa['fonts'],all_fonts_and_sce_sys_byte_verified=True,prior_distribution_preserved=rec(O/'previous-dist.json'),local_payload_plan=rec(report),commands=commands,zip_created=False,assembly_performed=False,network_connection_or_FTP=False,shutdown_performed=False,limits=['No physical console test performed; local checks do not prove 120 FPS or instantaneous 3D loading.'])
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status=result['status'],receipt=rec(O/'verification.json'),signed_eboot=eboot,app_folder=str(app))))
