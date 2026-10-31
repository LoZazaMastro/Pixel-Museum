#!/usr/bin/env python3
"""Update only Pixel Museum, with offline backups and RETR hash verification."""
from ftplib import FTP,error_perm
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,time
ROOT=Path(__file__).resolve().parents[1]
TITLE='PPSA70421';REMOTE='/data/homebrew/'+TITLE
parser=argparse.ArgumentParser();parser.add_argument('--slice-dir',required=True);args=parser.parse_args()
parent=(ROOT/args.slice_dir).resolve();assert parent.is_relative_to((ROOT/'dist').resolve())
manifest=json.loads((parent/'payload-manifest.json').read_text());assert manifest['title_id']==TITLE
folder=parent/TITLE
stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime());backup=ROOT/'build/console-slice/backups'/stamp
backup.mkdir(parents=True,exist_ok=False)
report={'title_id':TITLE,'host':'192.168.1.56','port':2121,'archive_sha256':manifest['archive_sha256'],'started_utc':stamp,'changes':[],'verified':[],'status':'preflight'}
receipt=backup/'update-receipt.json'
def save():receipt.write_text(json.dumps(report,indent=2)+'\n')
def hash_file(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def closed(ftp):
 # An uncertain listing must abort, never be treated as an empty sandbox.
 names=[name for name,_ in ftp.mlsd('/mnt/sandbox')]
 assert not any(name.startswith(TITLE+'_') for name in names),'Pixel Museum is mounted/running; no activation permitted'
def inspect(ftp,path,output=None):
 h=hashlib.sha256();count=0
 def consume(block):
  nonlocal count
  h.update(block);count+=len(block)
  if output:output.write(block)
 ftp.retrbinary('RETR '+path,consume,256*1024)
 return count,h.hexdigest()
assert manifest['files'] and len({row['path'] for row in manifest['files']})==len(manifest['files'])
for row in manifest['files']:
 name=PurePosixPath(row['path']);assert not name.is_absolute() and '..' not in name.parts and not any(c in str(name) for c in ':\\\r\n')
 assert (folder/row['path']).resolve().is_relative_to(folder.resolve())
 assert (folder/row['path']).stat().st_size==row['bytes'] and hash_file(folder/row['path'])==row['sha256']
with FTP() as ftp:
 ftp.connect(report['host'],report['port'],timeout=30);ftp.login('anonymous','codex');closed(ftp)
 assert TITLE in [name for name,_ in ftp.mlsd('/data/homebrew')]
 existing={}
 def walk(path,relative=''):
  for name,facts in ftp.mlsd(path):
   if name in ('.','..'):continue
   key=relative+name
   if facts.get('type')=='dir':walk(path+'/'+name,key+'/')
   elif facts.get('type')=='file':existing[key]=facts
 walk(REMOTE)
 # Read every installed payload byte; settings/download0 live elsewhere.
 for n,row in enumerate(manifest['files'],1):
  name=row['path'];remote=REMOTE+'/'+name
  if name in existing:
   local=backup/'previous'/name;local.parent.mkdir(parents=True,exist_ok=True)
   with local.open('wb') as out:count,digest=inspect(ftp,remote,out)
   if count==row['bytes'] and digest==row['sha256']:
    report['verified'].append(row);continue
   previous={'bytes':count,'sha256':digest}
  else:previous=None
  directory=str(PurePosixPath(remote).parent)
  # Only directories named in the audited manifest can be created.
  current=REMOTE
  for part in PurePosixPath(name).parts[:-1]:
   current+='/'+part
   try:ftp.mkd(current)
   except error_perm:
    ftp.cwd(current) # Verify it really exists, rather than hiding a failure.
  temporary=directory+'/.'+PurePosixPath(name).name+'.'+stamp+'.upload'
  with (folder/name).open('rb') as source:ftp.storbinary('STOR '+temporary,source,256*1024)
  count,digest=inspect(ftp,temporary)
  assert (count,digest)==(row['bytes'],row['sha256']),'Staged verification failed: '+name
  report['changes'].append({'path':name,'temporary':temporary,'previous':previous,'bytes':count,'sha256':digest,'promoted':False})
  save()
 # ShadowMount keeps registered Home artwork copies. Update only this
 # title's two wallpaper assets, preserving its registered metadata/settings.
 for registered in ('/user/appmeta/'+TITLE,'/user/app/'+TITLE+'/sce_sys'):
  try:list(ftp.mlsd(registered))
  except error_perm:continue
  for image in ('pic0.dds','pic1.dds'):
   local=folder/'sce_sys'/image;remote=registered+'/'+image
   key='registered-home/'+registered.split('/')[2]+'/'+image
   saved=backup/'previous'/key;saved.parent.mkdir(parents=True,exist_ok=True)
   with saved.open('wb') as out:count,digest=inspect(ftp,remote,out)
   wanted=hash_file(local)
   if count==local.stat().st_size and digest==wanted:continue
   temporary=registered+'/.'+image+'.'+stamp+'.upload'
   with local.open('rb') as source:ftp.storbinary('STOR '+temporary,source,256*1024)
   check_count,check_hash=inspect(ftp,temporary)
   assert (check_count,check_hash)==(local.stat().st_size,wanted)
   report['changes'].append({'path':key,'remote':remote,'temporary':temporary,'previous':{'bytes':count,'sha256':digest},'bytes':check_count,'sha256':check_hash,'promoted':False})
   save()
  # ShadowMount also retains registered parameter copies. Preserve their
  # identity and custom fields while enabling the same audited display flags.
  remote=registered+'/param.json';key='registered-home/'+registered.split('/')[2]+'/param.json'
  saved=backup/'previous'/key;saved.parent.mkdir(parents=True,exist_ok=True)
  with saved.open('wb') as out:count,digest=inspect(ftp,remote,out)
  parameters=json.loads(saved.read_text(encoding='utf-8-sig'))
  assert parameters.get('titleId')==TITLE,'Registered parameter identity mismatch'
  required=json.loads((folder/'sce_sys/param.json').read_text(encoding='utf-8-sig'))['attribute3'] & 0x80040
  assert required==0x80040,'Package is missing the audited display permissions'
  current_flags=int(parameters.get('attribute3',0))
  if current_flags & required != required:
   parameters['attribute3']=current_flags|required
   replacement=backup/'replacement'/key;replacement.parent.mkdir(parents=True,exist_ok=True)
   replacement.write_text(json.dumps(parameters,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
   wanted=hash_file(replacement);temporary=registered+'/.param.json.'+stamp+'.upload'
   with replacement.open('rb') as source:ftp.storbinary('STOR '+temporary,source,256*1024)
   check_count,check_hash=inspect(ftp,temporary)
   assert (check_count,check_hash)==(replacement.stat().st_size,wanted)
   report['changes'].append({'path':key,'remote':remote,'temporary':temporary,'previous':{'bytes':count,'sha256':digest},'bytes':check_count,'sha256':check_hash,'promoted':False})
   save()
 report['status']='staged_and_verified';save();closed(ftp)
 # The executable is activated last. Every promotion gets a fresh closed check.
 ordered=sorted(report['changes'],key=lambda row:(row['path']=='eboot.bin',row['path']))
 try:
  for row in ordered:
   closed(ftp);ftp.rename(row['temporary'],row.get('remote',REMOTE+'/'+row['path']));row['promoted']=True;save()
  for row in report['changes']:
   count,digest=inspect(ftp,row.get('remote',REMOTE+'/'+row['path']));assert (count,digest)==(row['bytes'],row['sha256'])
  report['status']='updated_and_byte_verified';report['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());save()
 except Exception:
  report['status']='activation_failed';save()
  # Do not write a rollback into an app that the user has since opened.
  closed(ftp)
  for row in reversed(ordered):
   if not row['promoted'] or row['previous'] is None:continue
   remote=row.get('remote',REMOTE+'/'+row['path']);temporary=remote+'.rollback'
   with (backup/'previous'/row['path']).open('rb') as source:ftp.storbinary('STOR '+temporary,source,256*1024)
   count,digest=inspect(ftp,temporary);assert (count,digest)==(row['previous']['bytes'],row['previous']['sha256'])
   closed(ftp);ftp.rename(temporary,remote)
  report['residual_new_files']=[row.get('remote',REMOTE+'/'+row['path']) for row in ordered if row['promoted'] and row['previous'] is None]
  report['status']='previous_files_restored_with_new_unreferenced_files' if report['residual_new_files'] else 'previous_changed_files_restored';save();raise
print(json.dumps({'status':report['status'],'changed_files':len(report['changes']),'unchanged_verified_files':len(report['verified']),'receipt':str(receipt)},indent=2))
