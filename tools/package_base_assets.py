"""Refresh the non-editorial assets even when reusing a signed executable."""
from pathlib import Path
import shutil


def copy_changed(source, target):
    """Keep identical staged files instead of rewriting large static assets."""
    source, target = Path(source), Path(target)
    if target.is_file():
        a, b = source.stat(), target.stat()
        if a.st_size == b.st_size and a.st_mtime_ns == b.st_mtime_ns:
            return str(target)
    return shutil.copy2(source, target)


def stage_base_assets(root: Path, folder: Path):
    root, folder = Path(root), Path(folder)
    (folder / 'assets').mkdir(parents=True, exist_ok=True)
    for source in sorted((root / 'assets').iterdir()):
        # Referenced editorial images and their manifest are staged separately.
        if source.name == 'images':
            continue
        target = folder / 'assets' / source.name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True, copy_function=copy_changed)
        elif source.is_file():
            copy_changed(source, target)
    (folder / 'sce_sys').mkdir(exist_ok=True)
    for name in ('param.json', 'icon0.png', 'pic0.dds', 'pic1.dds', 'snd0.at9'):
        source = root / 'sce_sys' / name
        if source.is_file():
            copy_changed(source, folder / 'sce_sys' / name)
    # The console cannot enumerate /app0. Match build.sh's audio file indices
    # when updating the payload without rebuilding the unchanged native ELF.
    audio = folder / 'assets/audio'
    directories = [audio / 'music']
    if (audio / 'sfx').is_dir():
        directories += [p for p in (audio / 'sfx').iterdir() if p.is_dir()]
    for directory in directories:
        if directory.is_dir():
            names = sorted(p.name for p in directory.iterdir()
                           if p.is_file() and p.name != 'index.txt')
            (directory / 'index.txt').write_bytes(''.join(n + '\n' for n in names).encode('utf8'))
