"""Package the native Windows build and the existing pinned collection for setup.

Creates a reviewable local setup bundle. No upload or public release is performed.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INVENTORY = 'application-files.json'
COLLECTION_MANIFESTS = {'content/collection-packs.json', 'assets/images/manifest.json'}
STORED_MEDIA = {'.png', '.jpg', '.jpeg', '.ogg', '.zst', '.mp4', '.bin'}

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4<<20),b''):h.update(block)
    return h.hexdigest()

def copy(source:Path,target:Path):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)


def semver_order(version):
    identifiers = r'[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*'
    match = re.fullmatch(rf'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-({identifiers}))?(?:\+{identifiers})?', version)
    if not match or len(version) > 100:
        raise ValueError(f'Invalid update version: {version}')
    prerelease = match.group(4).split('.') if match.group(4) else []
    if any(len(part) > 1 and part.isdigit() and part.startswith('0') for part in prerelease):
        raise ValueError(f'Invalid numeric prerelease: {version}')
    return tuple(map(int, match.groups()[:3])), not prerelease, tuple(
        (0, int(part)) if part.isdigit() else (1, part) for part in prerelease)


def read_inventory(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if (data['schema_version'], data['application_id'], data['platform']) != (1, 'pixel-museum', 'windows-x64'):
        raise ValueError(f'Unrecognized Windows inventory: {path}')
    version = data['version']
    semver_order(version)
    rows = {}
    for row in data['files']:
        name = row['path']
        key = name.casefold()
        if (not name or any(part in ('', '.', '..') or part.endswith(('.', ' ')) for part in name.split('/'))
                or any(char in name for char in '\\:<>"|?*') or any(ord(char) < 32 for char in name)
                or key == INVENTORY or key in rows):
            raise ValueError(f'Unsafe or repeated inventory path: {name}')
        if type(row['bytes']) is not int or row['bytes'] < 0 or not re.fullmatch(r'[0-9a-f]{64}', row['sha256']):
            raise ValueError(f'Invalid inventory size or SHA-256: {name}')
        rows[key] = row
    if 'pixel museum.exe' not in rows:
        raise ValueError(f'Inventory is missing Pixel Museum.exe: {path}')
    return version, raw, rows


def write_zip(archive, app, files):
    expanded = 0
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as output:
        for file in files:
            expanded += file.stat().st_size
            compression = zipfile.ZIP_STORED if file.suffix.lower() in STORED_MEDIA else zipfile.ZIP_DEFLATED
            output.write(file, file.relative_to(app).as_posix(), compress_type=compression)
    return expanded


def build_deltas(app, output, release, base_paths):
    if not base_paths:
        return []
    version, raw, target = read_inventory(app / INVENTORY)
    if version != release['version']:
        raise ValueError('The staged inventory and release manifest disagree on version')
    full = next(package for package in release['packages'] if package['kind'] == 'app')
    with zipfile.ZipFile(output / full['filename']) as archive:
        if archive.read(INVENTORY) != raw:
            raise ValueError('The staged inventory must match the full application ZIP byte for byte')
    updates = []
    seen = set()
    for base_path in base_paths:
        previous, base_raw, base = read_inventory(base_path)
        if semver_order(previous) >= semver_order(version):
            raise ValueError(f'An update base must be older than the target: {previous} -> {version}')
        if any(name not in base or target.get(name) != base[name] for name in COLLECTION_MANIFESTS):
            raise ValueError(f'Application updates cannot migrate the installed collection: {previous} -> {version}')
        base_hash = hashlib.sha256(base_raw).hexdigest()
        if base_hash in seen:
            continue
        seen.add(base_hash)
        # Always ship the executable so the helper can move it out first and
        # restore it last, including updates limited to companion files.
        changed = [row for name, row in target.items() if name == 'pixel museum.exe' or base.get(name) != row]
        payload = []
        for row in changed:
            path = app / row['path']
            if (path.is_symlink() or not path.resolve().is_relative_to(app) or not path.is_file()
                    or path.stat().st_size != row['bytes'] or digest(path) != row['sha256']):
                raise ValueError(f"Staged file disagrees with the target inventory: {row['path']}")
            payload.append(path)
        filename = f'Pixel-Museum-Windows-Update-{base_hash[:16]}-to-{version.replace("+", "_")}.zip'
        archive = output / filename
        expanded = write_zip(archive, app, [*payload, app / INVENTORY])
        url = full['url'].rsplit('/', 1)[0] + '/' + filename if full.get('url') else None
        package = {'id': f'app-delta-{base_hash[:16]}', 'kind': 'app', 'filename': filename,
                   'format': 'zip', 'url': url, 'sha256': digest(archive),
                   'bytes': archive.stat().st_size, 'unpacked_bytes': expanded, 'target': '.'}
        updates.append({'from_version': previous, 'base_inventory_sha256': base_hash, 'package': package})
    release['updates'] = updates
    return updates

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
    # The content snapshot and its revision are one unit. Never label a tested
    # newer runtime with an older authoring-tree database version.
    database_version=base/'content/database-version.json'
    if not database_version.is_file():raise RuntimeError('The runtime must identify its bundled database revision')
    copy(database_version,app/'content/database-version.json')
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
    for package in ['SDL3','sdl3','glew','ffmpeg','curl','openssl','zstd','zlib','gcc-libs','opus']:
        source=args.prefix/'share/licenses'/package
        if source.exists():shutil.copytree(source,app/'licenses/windows'/package,dirs_exist_ok=True)
    (app/'licenses/windows-native-dependencies.json').write_text(json.dumps({'libraries':dependencies,'prefix':'MSYS2 MinGW-w64','source':'https://packages.msys2.org/'} ,indent=2),encoding='utf8')
    # The apply helper runs from a private temporary copy after the app exits.
    setup=args.setup.resolve()
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
    archive=output/args.archive_name
    expanded=write_zip(archive,app,[*payload_files,inventory])
    packages=[{'id':'app','kind':'app','filename':archive.name,'format':'zip','url':args.app_url,'sha256':digest(archive),'bytes':archive.stat().st_size,'unpacked_bytes':expanded,'target':'.'}]
    for pack in manifest['packs']:
        packages.append({'id':pack['id'],'kind':'collection','filename':pack['id']+'.tar','format':'tar','url':pack['url'],'sha256':pack['sha256'],'bytes':pack['bytes'],'unpacked_bytes':pack['bytes'],'target':relative+'/archives'})
    release={'schema_version':1,'version':args.version,'executable':exe.name,'packages':packages,'install_current_database':True}
    updates=build_deltas(app,output,release,args.update_from)
    destination=output/'windows-manifest.json';destination.write_text(json.dumps(release,indent=2),encoding='utf8')
    if setup.exists():copy(setup,output/setup.name)
    report={'app_zip':str(archive),'bytes':archive.stat().st_size,'expanded_bytes':expanded,'collection_bytes':sum(p['bytes'] for p in manifest['packs']),'collection_root':relative,'dependency_count':len(dependencies),'manifest':str(destination)}
    if updates:report['updates']=updates
    (output/'package-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',type=Path,help='Tested PPSA content root; console executable excluded')
    p.add_argument('--output',type=Path,default=ROOT/'dist/windows-preview')
    p.add_argument('--prefix',type=Path,default=Path(r'C:\msys64\mingw64'))
    p.add_argument('--version',default='0.2.0-preview')
    p.add_argument('--app-url',default=None,help='Set only after this exact ZIP is uploaded and verified; absent uses local ZIP')
    p.add_argument('--setup', type=Path, default=ROOT/'dist/windows-installer/Pixel-Museum-Setup.exe', help='Verified standalone setup and update helper to include with the Windows preview')
    p.add_argument('--refresh',action='store_true',help='Refresh native binary, desktop labels, notices and ZIP in the existing local staging folder')
    p.add_argument('--archive-name',default='Pixel-Museum-Windows-App.zip')
    p.add_argument('--update-from',type=Path,action='append',default=[],metavar='INVENTORY',
                   help='Write an application delta for this exact previous application-files.json (repeatable)')
    p.add_argument('--delta-only',action='store_true',help='Reuse the full application ZIP and staged application under --output')
    args=p.parse_args()
    if args.delta_only:
        if not args.update_from:p.error('--delta-only requires --update-from')
        output=args.output.resolve()
        destination=output/'windows-manifest.json'
        release=json.loads(destination.read_bytes())
        updates=build_deltas(output/'application',output,release,args.update_from)
        destination.write_text(json.dumps(release,indent=2)+'\n',encoding='utf8')
        print(json.dumps({'manifest':str(destination),'updates':updates},indent=2))
    else:
        if not args.runtime:p.error('--runtime is required unless using --delta-only')
        prepare(args)
