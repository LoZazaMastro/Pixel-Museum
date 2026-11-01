"""Repair only the two explicitly requested, closed homebrew download-area reservations.

The user explicitly accepted losing these two apps' preferences/cache on 2026-10-23.
No application payload, unrelated title, or live system database is replaced.
"""
from pathlib import Path
from ftplib import FTP,error_perm
import argparse,io,json,hashlib,datetime

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/research/storage-size-urgent-2026-10-23'
TITLES={'PPSA98427':256,'PPSA70421':256}
EXPECTED_OLD_BYTES=18763546624
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply',action='store_true')
parser.add_argument('--metadata-only',action='store_true',help='Publish verified metadata before the system registration/reset step.')
args=parser.parse_args()
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'apply':args.apply,
 'authorized_reset':'User explicitly accepts losing all preferences/cache of these two apps.',
 'parameters':[],'download_areas':[],'errors':[]}
sha=lambda data:hashlib.sha256(data).hexdigest()
OUT.mkdir(parents=True,exist_ok=True)

def get(f,path):
 b=io.BytesIO();f.retrbinary('RETR '+path,b.write)
 if b.tell()>65536:raise RuntimeError('Unexpected metadata size: '+path)
 return b.getvalue()

try:
 with FTP()as f:
  f.connect('192.168.1.56',2121,timeout=10);f.login();f.voidcmd('TYPE I')
  sandbox=f.nlst('/mnt/sandbox')
  active=[name for name in sandbox if any(Path(name).name.startswith(title+'_')for title in TITLES)]
  if active:raise RuntimeError('An affected title still has an active sandbox: '+repr(active))
  pending=[]
  for title,quota in TITLES.items():
   for label,path in [('payload','/data/homebrew/'+title+'/sce_sys/param.json'),
      ('registered','/user/app/'+title+'/sce_sys/param.json'),('appmeta','/user/appmeta/'+title+'/param.json')]:
    old_bytes=get(f,path);old=json.loads(old_bytes)
    assert old['titleId']==title
    assert old['downloadDataSize']in(16384,64,quota)
    backup=OUT/(title+'-'+label+'-param-before-storage-fix.json')
    if backup.exists():assert backup.read_bytes()==old_bytes or old['downloadDataSize']==quota
    else:backup.write_bytes(old_bytes)
    new=dict(old);new['downloadDataSize']=quota
    data=(json.dumps(new,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    assert {k:v for k,v in new.items()if k!='downloadDataSize'}=={k:v for k,v in old.items()if k!='downloadDataSize'}
    pending.append((path,data))
    report['parameters'].append({'path':path,'previous_mib':old['downloadDataSize'],'new_mib':quota,'before_sha256':sha(old_bytes),'after_sha256':sha(data),'only_changed_field':'downloadDataSize'})
   download='/user/download/'+title+'/download0.dat'
   size=f.size(download)
   if size!=EXPECTED_OLD_BYTES:raise RuntimeError('Unexpected download image size; refusing reset: '+download+' '+str(size))
   report['download_areas'].append({'path':download,'previous_logical_bytes':size,'reset':False})
  if args.apply:
   for path,data in pending:
    temporary=path+'.storage-reservation-fix'
    f.storbinary('STOR '+temporary,io.BytesIO(data));assert get(f,temporary)==data
    f.sendcmd('SITE CHMOD 0777 '+temporary);f.rename(temporary,path);assert get(f,path)==data
   # Check again immediately before deleting the two specifically authorized files.
   sandbox=f.nlst('/mnt/sandbox')
   assert not any(Path(name).name.startswith(title+'_')for name in sandbox for title in TITLES),'App launched during metadata update; reset refused'
   for item in ([] if args.metadata_only else report['download_areas']):
    path=item['path'];assert path in ['/user/download/'+title+'/download0.dat'for title in TITLES]
    assert f.size(path)==EXPECTED_OLD_BYTES
    f.delete(path)
    try:f.size(path)
    except error_perm as e:
     if not str(e).startswith('550'):raise
     item['reset']=True
    else:raise RuntimeError('Download area still exists after reset: '+path)
  report['status']=('APPLIED_METADATA_ONLY_READBACK_VERIFIED'if args.metadata_only else'APPLIED_METADATA_READBACK_VERIFIED_AWAITING_SYSTEM_RECREATION')if args.apply else'REVIEWED_READY'
except Exception as e:
 report['errors'].append(str(e));report['status']='STOPPED'
finally:
 out=OUT/('two-app-reservation-metadata-only-applied.json'if args.apply and args.metadata_only else'two-app-reservation-reset-applied.json'if args.apply else'two-app-reservation-reset-plan.json')
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps(report))
if report['errors']:raise SystemExit(1)
