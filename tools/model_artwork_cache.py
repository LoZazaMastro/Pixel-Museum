"""Validate/copy optional offline artwork sidecars; source GLBs remain intact."""
from pathlib import Path
import hashlib
import shutil

def checked_artwork_cache(root, model):
    cache = model.get("artwork_cache")
    if not cache:
        return None
    expected = str(Path(model["asset_file"]).with_suffix(".artwork.pmc")).replace("\\", "/")
    asset = cache.get("asset_file", "")
    path = Path(asset)
    if asset != expected or len(path.parts) != 2 or path.parts[0] != "models" or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe model artwork cache path: {asset!r}")
    if cache.get("format_version") not in (1, 2) or cache.get("source_sha256") != model["sha256"]:
        raise ValueError(f"Model artwork cache source/version mismatch: {asset}")
    source = Path(root) / path
    if not source.is_file() or source.stat().st_size != cache["bytes"]:
        raise ValueError(f"Missing/incomplete offline model artwork cache: {asset}")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    if digest.hexdigest() != cache["sha256"]:
        raise ValueError(f"Offline model artwork cache hash mismatch: {asset}")
    with source.open('rb') as stream:
        if stream.read(8) != (b'PMAC0002' if cache['format_version'] == 2 else b'PMAC0001'):
            raise ValueError(f"Offline model artwork cache magic/version mismatch: {asset}")
    return path

def copy_artwork_cache(root, destination, model):
    path = checked_artwork_cache(root, model)
    if path is not None:
        (Path(destination) / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(root) / path, Path(destination) / path)
