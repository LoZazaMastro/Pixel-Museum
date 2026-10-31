#!/usr/bin/env python3
"""Test checked sidecar packaging without modifying masters or deployment folders."""
from pathlib import Path
import copy
import hashlib
import runpy
import tempfile
helper = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools/model_artwork_cache.py"))
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp) / "source"
    (root / "models").mkdir(parents=True)
    path = root / "models/fixture.artwork.pmc"
    content = b"PMAC0001lossless-cache-fixture"
    path.write_bytes(content)
    model = {"asset_file": "models/fixture.glb", "sha256": "master-sha256", "artwork_cache": {"asset_file": "models/fixture.artwork.pmc", "source_sha256": "master-sha256", "format_version": 1, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}}
    assert helper["checked_artwork_cache"](root, model) == Path("models/fixture.artwork.pmc")
    destination = Path(temp) / "payload"
    helper["copy_artwork_cache"](root, destination, model)
    assert (destination / "models/fixture.artwork.pmc").read_bytes() == content
    v2_content=b'PMAC0002'+content[8:]
    path.write_bytes(v2_content)
    v2=copy.deepcopy(model);v2['artwork_cache'].update(format_version=2,sha256=hashlib.sha256(v2_content).hexdigest())
    assert helper['checked_artwork_cache'](root,v2)==Path('models/fixture.artwork.pmc')
    helper['copy_artwork_cache'](root,destination,v2)
    assert (destination/'models/fixture.artwork.pmc').read_bytes()==v2_content
    path.write_bytes(content)
    for field, value in [("asset_file", "../escape.artwork.pmc"), ("asset_file", "models/another.artwork.pmc"), ("format_version", 2), ("source_sha256", "another-master"), ("bytes", 999), ("sha256", "corrupt")]:
        changed = copy.deepcopy(model)
        changed["artwork_cache"][field] = value
        try:
            helper["checked_artwork_cache"](root, changed)
        except ValueError:
            pass
        else:
            raise AssertionError((field, value))
    path.write_bytes(b"corrupt" + content[7:])
    try:
        helper["checked_artwork_cache"](root, model)
    except ValueError:
        pass
    else:
        raise AssertionError("corrupt sidecar accepted")
print("PASS checked lossless sidecar copy, exact bytes, source/version binding, path guards and corruption rejection")
