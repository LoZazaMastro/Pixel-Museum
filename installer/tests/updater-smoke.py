"""Exercise the shipping offline helper against native x64 fixture apps only."""
from __future__ import annotations
import argparse,ctypes,hashlib,json,os,subprocess,time,uuid,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def write(path:Path,data:bytes):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
def json_file(path:Path,value):write(path,json.dumps(value,ensure_ascii=False,indent=2).encode('utf8'))
def inventory(files:dict[str,bytes],version:str):return {'schema_version':1,'application_id':'pixel-museum','platform':'windows-x64','version':version,'files':[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in sorted(files.items())]}

def main():
 p=argparse.ArgumentParser();p.add_argument('--setup',type=Path,required=True);args=p.parse_args();assert os.name=='nt'
 run=ROOT/'build/windows-installer-test'/('updater-smoke-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]);run.mkdir(parents=True)
 source=run/'fixture.c';source.write_text(r'''
#include <windows.h>
#include <wchar.h>
#ifndef MARKER
#define MARKER 1
#endif
int WINAPI WinMain(HINSTANCE a,HINSTANCE b,LPSTR c,int d){
 wchar_t path[32768];if(!GetModuleFileNameW(NULL,path,32768))return 1;
 wchar_t *last=wcsrchr(path,L'\\');if(!last)return 2;
 wcscpy(last,L"\\application-updates\\relaunch-proof.txt");
 HANDLE out=CreateFileW(path,GENERIC_WRITE,FILE_SHARE_READ,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
 if(out==INVALID_HANDLE_VALUE)return 3;char marker='0'+MARKER;DWORD written=0;
 WriteFile(out,&marker,1,&written,NULL);CloseHandle(out);return MARKER==3?9:(written==1?0:4);
}
''',encoding='ascii')
 compiler=Path(r'C:\msys64\mingw64\bin\gcc.exe')
 compiler_environment=dict(os.environ);compiler_environment['PATH']=str(compiler.parent)+os.pathsep+compiler_environment.get('PATH','')
 native=[]
 for marker in [1,2,3]:
  exe=run/f'fixture-{marker}.exe';built=subprocess.run([str(compiler),'-Os','-s','-static','-mwindows',f'-DMARKER={marker}',str(source),'-o',str(exe)],capture_output=True,env=compiler_environment);assert built.returncode==0,built.stderr.decode(errors='replace');native.append(exe.read_bytes())
 helper=args.setup.resolve().read_bytes();protected=['preferences.json','video-settings.json','trophies.json','logs/session.log','database/current/catalog.json','collection/ready/archives/pack.tar','shortcut.lnk','assets/user-owned.bin']
 reports=[]
 for scenario in ['success','bad-sha','locked-file','unowned-collision','crashing-new-app']:
  root=run/scenario/'Pixel Museum';root.mkdir(parents=True)
  old={
   'Pixel Museum.exe':native[0],'LICENSE':b'GPL fixture','THIRD_PARTY_NOTICES.md':b'Fixture notices',
   'content/collection-packs.json':b'unchanged pack manifest','content/collection-archive-index.json':b'unchanged index',
   'assets/images/manifest.json':b'unchanged image registry','assets/replaced.bin':b'old asset','obsolete.dll':b'old owned DLL',
   'tools/windows-updater/Pixel-Museum-Updater.exe':helper+b'old version overlay',
  }
  for name,data in old.items():write(root/name,data)
  json_file(root/'application-files.json',inventory(old,'0.1.0'))
  receipt={'schema_version':1,'version':'0.1.0','executable':'Pixel Museum.exe','language':'it'};json_file(root/'pixel-museum-install.json',receipt);original_receipt=(root/'pixel-museum-install.json').read_bytes()
  for name in protected:write(root/name,b'unchanged user data')
  new=dict(old);new.pop('obsolete.dll');new['Pixel Museum.exe']=native[1];new['tools/windows-updater/Pixel-Museum-Updater.exe']=helper;new['assets/replaced.bin']=b'new asset';new['added.dll']=b'new library';new['preferences.json']=b'must never replace preferences'
  if scenario=='crashing-new-app':new['Pixel Museum.exe']=native[2]
  zip_path=run/scenario/'app.zip'
  with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
   for name,data in new.items():z.writestr(name,data)
   z.writestr('application-files.json',json.dumps(inventory(new,'0.2.0')).encode())
  payload=zip_path.read_bytes();digest=sha(payload);archive=root/'application-updates/payloads'/f'{digest}.zip';write(archive,payload)
  with zipfile.ZipFile(archive) as z:expanded=sum(i.file_size for i in z.infolist())
  runner=root/'application-updates/runner/updater-4294967295-1.exe';write(runner,helper)
  descriptor={'schema_version':1,'application_id':'pixel-museum','platform':'windows-x64','version':'0.2.0','application_root':str(root),'archive':str(archive),'archive_sha256':digest,'archive_bytes':len(payload),'unpacked_bytes':expanded,'parent_pid':4294967295,'parent_creation_time':1,'language':'it','result_path':str(root/'application-updates/result.json'),'restart':True}
  request=root/'application-updates/request.json';json_file(request,descriptor)
  handle=None
  if scenario=='bad-sha':payload=bytearray(payload);payload[100]^=1;archive.write_bytes(payload)
  if scenario=='unowned-collision':write(root/'added.dll',b'user collision')
  if scenario=='locked-file':
   kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p];kernel.CreateFileW.restype=ctypes.c_void_p;kernel.CloseHandle.argtypes=[ctypes.c_void_p]
   handle=kernel.CreateFileW(str(root/'assets/replaced.bin'),0x80000000,1,None,3,0,None);assert handle not in (None,ctypes.c_void_p(-1).value)
  try:completed=subprocess.run([str(runner),'--apply-update',str(request)],capture_output=True,timeout=30)
  finally:
   if handle is not None:kernel.CloseHandle(handle)
  result=json.loads((root/'application-updates/result.json').read_text(encoding='utf8'))
  marker=root/'application-updates/relaunch-proof.txt'
  for _ in range(60):
   if marker.exists():break
   time.sleep(.05)
  assert marker.exists(),(scenario,completed.returncode,completed.stderr.decode(errors='replace'),result)
  assert marker.read_bytes()==(b'2' if scenario=='success' else b'1'),scenario
  assert result['success']==(scenario=='success'),result
  assert result['rolled_back']==(scenario in ['locked-file','crashing-new-app']),result
  assert completed.returncode==(0 if scenario=='success' else 1),result
  assert (root/'Pixel Museum.exe').read_bytes()==native[1 if scenario=='success' else 0]
  assert (root/'tools/windows-updater/Pixel-Museum-Updater.exe').read_bytes()==(helper if scenario=='success' else helper+b'old version overlay')
  for name in protected:assert (root/name).read_bytes()==b'unchanged user data',(scenario,name)
  assert (root/'pixel-museum-install.json').read_bytes()==original_receipt
  assert (root/'obsolete.dll').exists()==(scenario!='success')
  reports.append({'scenario':scenario,'exit_code':completed.returncode,'success':result['success'],'rolled_back':result['rolled_back'],'relaunch_marker':marker.read_text(),'user_data_preserved':True,'helper_replaced_from_temporary_runner':scenario=='success','result':str(root/'application-updates/result.json')})
 report={'passed':True,'setup_sha256':sha(helper),'test_root':str(run),'scenarios':reports,'real_user_destination_accessed':False,'network_requests':0,'gui_windows_created':0};json_file(run/'report.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
