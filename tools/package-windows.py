"""Package the native Windows build and the existing pinned collection for setup.

Creates a reviewable local setup bundle. No upload or public release is performed.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4<<20),b''):h.update(block)
    return h.hexdigest()

def copy(source:Path,target:Path):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)

def dlls(exe:Path,prefix:Path,destination:Path):
    queue=[exe];seen=set();resolved=[]
    binary=prefix/'bin';objdump=binary/'objdump.exe'
    while queue:
        file=queue.pop()
        for name in re.findall(r'DLL Name:\s*(\S+)',subprocess.check_output([str(objdump),'-p',str(file)],text=True,encoding='utf8',errors='replace')):
            key=name.lower()
            if key in seen:continue
            seen.add(key);source=binary/name
            if source.exists():
                target=destination/name;copy(source,target);resolved.append(name);queue.append(source)
            elif not key.startswith(('api-ms-','ext-ms-')):
                system=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/name
                if not system.exists():raise RuntimeError(f'Missing native dependency {name} required by {file.name}')
    return sorted(resolved)

def prepare(args):
    base=args.runtime.resolve();output=args.output.resolve();app=output/'application'
    if app.exists() and not args.refresh:raise RuntimeError(f'Refusing to overwrite existing staging directory: {app}; use --refresh for an existing local preview')
    app.mkdir(parents=True,exist_ok=True)
    if not args.refresh:
        for folder in ['assets','content','music','licenses','models']:
            if (base/folder).exists():shutil.copytree(base/folder,app/folder)
    # Add the desktop-only labels, retaining the translations from the tested build.
    for source in (ROOT/'content/ui-locales').glob('*.json'):
        target=app/'content/ui-locales'/source.name
        if not target.exists():continue
        current=json.loads(target.read_text(encoding='utf8'));desktop=json.loads(source.read_text(encoding='utf8'))
        for group in ['strings','music_strings']:
            if group in desktop:
                current.setdefault(group,{})
                for key,value in desktop[group].items():
                    current[group][key]=value  # Updated UI translations replace stale bundled values.
        target.write_text(json.dumps(current,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    exe=ROOT/'build/windows-native/Pixel Museum.exe'
    version_file=exe.parent/'application-version.json'
    if not version_file.is_file() or json.loads(version_file.read_text(encoding='utf8')).get('version')!=args.version:
        raise RuntimeError('The package version must match the version compiled by CMake (PIXEL_MUSEUM_APP_VERSION)')
    copy(exe,app/exe.name)
    copy(ROOT/'content/database-version.json',app/'content/database-version.json')
    dependencies=dlls(exe,args.prefix,app)
    license_file=ROOT/'LICENSE'
    if not license_file.exists():license_file=ROOT/'build/publication-20261031/repository/LICENSE'
    copy(license_file,app/'LICENSE')
    copy(ROOT/'THIRD_PARTY_NOTICES.md',app/'THIRD_PARTY_NOTICES.md')
    # Keep the original image manifest and exact raw pack manifest bytes.
    pack_file=app/'content/collection-packs.json';raw=pack_file.read_bytes();manifest=json.loads(raw)
    sha=hashlib.sha256(raw).hexdigest();relative=f"collection/{manifest['collection_id']}-{sha[:24]}";ready=app/relative
    (ready/'assets/images').mkdir(parents=True,exist_ok=True)
    image_manifest=app/'assets/images/manifest.json'
    if digest(image_manifest)!=manifest['image_manifest_sha256']:raise RuntimeError('Bundled image manifest mismatch')
    copy(image_manifest,ready/'assets/images/manifest.json')
    (ready/'.complete.json').write_text(json.dumps({'schema_version':1,'manifest_sha256':sha,'image_manifest_sha256':manifest['image_manifest_sha256'],'pack_count':len(manifest['packs'])}),encoding='utf8')
    for n,pack in enumerate(manifest['packs']):
        (ready/f'.pack-{n}.json').write_text(json.dumps({'sha256':pack['sha256'],'storage':'archive','archive':f"archives/{pack['sha256']}.tar",'bytes':pack['bytes']}),encoding='utf8')
    copy(ROOT/'docs/windows-port.md',app/'Windows guide.md')
    notices=ROOT/'installer/licenses/THIRD-PARTY-NOTICES.txt'
    if notices.exists():copy(notices,app/'licenses/Windows-setup-notices.txt')
    helpers=ROOT/'tools/windows-media'
    for folder in ['deno-2.9.8','ejs-0.8.0']:
        source=helpers/folder
        if not source.is_dir():raise RuntimeError(f'Missing verified Windows media helper: {source}')
        shutil.copytree(source,app/'tools/windows-media'/folder,dirs_exist_ok=True)
    for name in ['versions.json','THIRD-PARTY-NOTICES.md']:
        source=helpers/name
        if source.exists():copy(source,app/'tools/windows-media'/name)
    # Redistribute each native library's supplied licence, not unrelated SDK files.
    for package in ['SDL3','sdl3','glew','ffmpeg','curl','openssl','zstd','zlib','gcc-libs']:
        source=args.prefix/'share/licenses'/package
        if source.exists():shutil.copytree(source,app/'licenses/windows'/package,dirs_exist_ok=True)
    (app/'licenses/windows-native-dependencies.json').write_text(json.dumps({'libraries':dependencies,'prefix':'MSYS2 MinGW-w64','source':'https://packages.msys2.org/'} ,indent=2),encoding='utf8')
    # The apply helper runs from a private temporary copy after the app exits.
    setup=ROOT/'dist/windows-installer/Pixel-Museum-Setup.exe'
    if not setup.is_file():raise RuntimeError('Build the Windows setup/update helper before packaging')
    copy(setup,app/'tools/windows-updater/Pixel-Museum-Updater.exe')
    inventory=app/'application-files.json'
    root_files={'Pixel Museum.exe','LICENSE','THIRD_PARTY_NOTICES.md','Windows guide.md',*dependencies}
    def distributable(file):
        relative_path=file.relative_to(app);parts=relative_path.parts;name=relative_path.as_posix()
        if len(parts)==1:return file.name in root_files or file==inventory
        if parts[0] in {'assets','content','licenses','models','music'}:return True
        if name.startswith('tools/windows-media/') or name=='tools/windows-updater/Pixel-Museum-Updater.exe':return True
        if name.startswith(relative+'/'):
            tail=name[len(relative)+1:]
            return tail=='assets/images/manifest.json' or tail=='.complete.json' or re.fullmatch(r'\.pack-[0-9]+\.json',tail) is not None
        return False
    # Runtime preferences, account tokens, caches, databases, downloaded TARs and
    # logs may exist after a local preview. Never redistribute this mutable state.
    payload_files=[file for file in sorted(app.rglob('*')) if file.is_file() and file!=inventory and distributable(file)]
    if any(file.is_symlink() or not file.resolve().is_relative_to(app.resolve()) for file in payload_files):raise RuntimeError('External/symlink files cannot enter the Windows payload')
    owned=[{'path':file.relative_to(app).as_posix(),'bytes':file.stat().st_size,'sha256':digest(file)} for file in payload_files]
    inventory.write_text(json.dumps({'schema_version':1,'application_id':'pixel-museum','platform':'windows-x64','version':args.version,'files':owned},ensure_ascii=False,indent=2),encoding='utf8')
    archive=output/args.archive_name;expanded=0
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for file in [*payload_files,inventory]:
            if file.is_file():
                expanded+=file.stat().st_size
                z.write(file,file.relative_to(app).as_posix(),compress_type=zipfile.ZIP_STORED if file.suffix.lower() in ['.png','.jpg','.jpeg','.ogg','.zst','.mp4','.bin'] else zipfile.ZIP_DEFLATED)
    packages=[{'id':'app','kind':'app','filename':archive.name,'format':'zip','url':args.app_url,'sha256':digest(archive),'bytes':archive.stat().st_size,'unpacked_bytes':expanded,'target':'.'}]
    for pack in manifest['packs']:
        packages.append({'id':pack['id'],'kind':'collection','filename':pack['id']+'.tar','format':'tar','url':pack['url'],'sha256':pack['sha256'],'bytes':pack['bytes'],'unpacked_bytes':pack['bytes'],'target':relative+'/archives'})
    release={'schema_version':1,'version':args.version,'executable':exe.name,'packages':packages}
    destination=output/'windows-manifest.json';destination.write_text(json.dumps(release,indent=2),encoding='utf8')
    if setup.exists():copy(setup,output/setup.name)
    report={'app_zip':str(archive),'bytes':archive.stat().st_size,'expanded_bytes':expanded,'collection_bytes':sum(p['bytes'] for p in manifest['packs']),'collection_root':relative,'dependency_count':len(dependencies),'manifest':str(destination)}
    (output/'package-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',type=Path,required=True,help='Tested PPSA content root; console executable excluded')
    p.add_argument('--output',type=Path,default=ROOT/'dist/windows-preview')
    p.add_argument('--prefix',type=Path,default=Path(r'C:\msys64\mingw64'))
    p.add_argument('--version',default='0.2.0-preview')
    p.add_argument('--app-url',default=None,help='Set only after this exact ZIP is uploaded and verified; absent uses local ZIP')
    p.add_argument('--refresh',action='store_true',help='Refresh native binary, desktop labels, notices and ZIP in the existing local staging folder')
    p.add_argument('--archive-name',default='Pixel-Museum-Windows-App.zip')
    prepare(p.parse_args())
