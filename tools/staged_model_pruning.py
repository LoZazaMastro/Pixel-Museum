"""Prune unreferenced console meshes from a future staging directory only."""
from pathlib import Path


def prune_unreferenced_models(root, folder, required):
    root, folder = Path(root).resolve(), Path(folder).resolve()
    if folder != root / 'dist/PPSA70421':
        raise ValueError('Model pruning is limited to the exact staged application')
    destination = folder / 'models'
    if not destination.exists():
        return []
    if destination.resolve() != destination or not destination.resolve().is_relative_to(folder):
        raise ValueError('Unsafe staged model directory')
    required = set(required)
    removed = []
    for path in destination.iterdir():
        if not path.is_file() or (path.suffix != '.glb' and not path.name.endswith('.artwork.pmc')):
            continue
        relative = path.relative_to(folder).as_posix()
        if relative in required:
            continue
        if path.resolve().parent != destination:
            raise ValueError('Unsafe staged model file')
        path.unlink()
        removed.append(relative)
    return removed
