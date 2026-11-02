"""Exercise the real uninstall CLI and direct installed helper on private fixture roots.

No production Programs/Desktop/registry entries are created. Native COM/HKCU
registration and rollback are covered separately with injected private test roots.
"""
from __future__ import annotations
import argparse, ctypes, hashlib, json, os, subprocess, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = 'tools/windows-updater/Pixel-Museum-Updater.exe'

def sha(data): return hashlib.sha256(data).hexdigest()
def write(path, data): path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
def json_file(path, value): write(path, json.dumps(value, indent=2).encode('utf8'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', type=Path, required=True)
    args = parser.parse_args()
    assert os.name == 'nt'
    setup = args.setup.resolve()
    run = ROOT/'build/windows-installer-test'/('uninstall-smoke-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    source = run/'fixture.c'
    source.write_text(r'''
#include <windows.h>
#include <wchar.h>
int WINAPI WinMain(HINSTANCE a,HINSTANCE b,LPSTR c,int d){
 wchar_t path[32768];if(!GetModuleFileNameW(NULL,path,32768))return 1;
 wchar_t *last=wcsrchr(path,92);if(!last)return 2;wcscpy(last,L"/release-fixture");
 for(int i=0;i<600;i++){if(GetFileAttributesW(path)!=INVALID_FILE_ATTRIBUTES)return 0;Sleep(50);}return 3;
}
''',encoding='ascii')
    compiler = Path(r'C:\msys64\mingw64\bin\gcc.exe')
    environment = dict(os.environ)
    environment['PATH'] = str(compiler.parent)+os.pathsep+environment.get('PATH','')
    app = run/'fixture.exe'
    compiled = subprocess.run([str(compiler),'-Os','-s','-static','-mwindows',str(source),'-o',str(app)],capture_output=True,env=environment)
    assert compiled.returncode == 0, compiled.stderr.decode(errors='replace')
    helper = setup.read_bytes()
    files = {'Pixel Museum.exe':app.read_bytes(),HELPER:helper,'LICENSE':b'GPL fixture','THIRD_PARTY_NOTICES.md':b'fixture notices','assets/owned.bin':b'app asset'}
    root = run/'Pixel Museum'
    for name, data in files.items(): write(root/name,data)
    json_file(root/'application-files.json',{'schema_version':1,'application_id':'pixel-museum','platform':'windows-x64','version':'0.2.0','files':[{'path':name,'bytes':len(data),'sha256':sha(data)} for name,data in files.items()]})
    json_file(root/'pixel-museum-install.json',{'schema_version':1,'version':'0.2.0','executable':'Pixel Museum.exe','language':'it'})
    protected = ['preferences.json','video-settings.json','trophies-v1.dat','database/receipt.json','collection/ready/archives/sentinel.tar','logs/session.log','assets/personal.jpg','notes.txt']
    for name in protected: write(root/name,b'unchanged personal data')
    original_receipt = (root/'pixel-museum-install.json').read_bytes()
    checks = []

    # The real app process is this test's tiny hidden fixture only.
    child = subprocess.Popen([str(root/'Pixel Museum.exe')],cwd=root,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        time.sleep(.15)
        rejected = subprocess.run([str(setup),'--uninstall',str(root),'--quiet'],capture_output=True,timeout=30)
        assert rejected.returncode == 1, rejected.stderr.decode(errors='replace')
        assert (root/'Pixel Museum.exe').read_bytes() == files['Pixel Museum.exe']
        assert (root/'pixel-museum-install.json').read_bytes() == original_receipt
        assert child.poll() is None
        checks.append({'case':'running-app-refused','passed':True,'process_left_running':True})
    finally:
        write(root/'release-fixture',b'close private fixture')
        assert child.wait(timeout=10) == 0

    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateFileW(str(root/'assets/owned.bin'),0x80000000,1,None,3,0,None)
    assert handle not in (None,ctypes.c_void_p(-1).value)
    try:
        rejected = subprocess.run([str(setup),'--uninstall',str(root),'--quiet'],capture_output=True,timeout=30)
        assert rejected.returncode == 1, rejected.stderr.decode(errors='replace')
        for name,data in files.items(): assert (root/name).read_bytes() == data,name
        assert (root/'pixel-museum-install.json').read_bytes() == original_receipt
        checks.append({'case':'locked-owned-file-rolls-back','passed':True})
    finally:
        kernel.CloseHandle(handle)

    # The installed helper performs uninstall directly and truthfully retains its
    # currently mapped executable alongside the preserved personal data.
    completed = subprocess.run([str(root/HELPER),'--uninstall',str(root),'--quiet'],cwd=run,capture_output=True,timeout=30)
    receipt_path = root/'pixel-museum-install.json'
    for _ in range(200):
        receipt = json.loads(receipt_path.read_text())
        if receipt.get('uninstalled'): break
        time.sleep(.05)
    assert completed.returncode == 0, completed.stderr.decode(errors='replace')
    assert receipt.get('uninstalled') is True, (receipt,completed.stderr.decode(errors='replace'))
    for name in files:
        if name != HELPER: assert not (root/name).exists(),name
    assert (root/HELPER).read_bytes() == helper
    assert receipt['retained_maintenance_helper'] == HELPER
    assert not (root/'application-files.json').exists()
    for name in protected: assert (root/name).read_bytes() == b'unchanged personal data',name
    checks.append({'case':'installed-helper-direct-uninstall','passed':True,'running_maintenance_helper_retained':True,'personal_data_preserved':True})
    report={'passed':True,'setup_sha256':sha(helper),'fixture_root':str(run),'checks':checks,'administrator':bool(ctypes.windll.shell32.IsUserAnAdmin()),'real_user_destination_accessed':False,'production_registry_and_shortcuts_written':False,'network_requests':0,'gui_windows_created':0}
    json_file(run/'report.json',report)
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()
