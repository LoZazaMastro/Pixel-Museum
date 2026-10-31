"""Require the complete reviewed pin collection when packaging the trophy build."""
import hashlib
import json
import re
import struct
import math
from collections import Counter, deque
from pathlib import Path


# One explicitly approved natural ring opening. This is not a generic escape
# from the other badges' solid-backing rule: new artwork needs a fresh review.
_RING_FRONT = 'f0bb9ea3cfc51246a68b8a299f7eb60133a65619bb9fd36a20c9895d7ecf2a55'
_RING_MESH = 'd6e3752b87756f24e6e71760484349de84d5dd571b4ff8039837c7ed9b650cb9'
_RING_PROOF = '542b331a5c0cb697334f169dde8ddc9f6301b09f36c6b5a1ee736626d498fac4'
_RING_PROOF_PATH = 'assets/trophies/provenance/secret04-natural-aperture.json'


def _validate_ring_aperture(staged, item):
    if item['badge'] != 'secret_04' or item.get('natural_aperture') is not True or item.get('solid_backing') is not False:
        raise ValueError('Only the reviewed secret_04 may have its natural aperture')
    if (item['front_sha256'], item['mesh_sha256']) != (_RING_FRONT, _RING_MESH):
        raise ValueError('Natural aperture artwork differs from the explicitly reviewed ring')
    binding = item.get('aperture_proof', {})
    if binding != {'path': _RING_PROOF_PATH, 'sha256': _RING_PROOF}:
        raise ValueError('Natural ring requires the exact packaged closure proof')
    proof_bytes = (staged/_RING_PROOF_PATH).read_bytes()
    if hashlib.sha256(proof_bytes).hexdigest() != _RING_PROOF:
        raise ValueError('Natural ring closure proof hash differs')
    proof = json.loads(proof_bytes)
    if proof.get('nonmanifold_edges') != 0 or proof.get('hole_count') != 1 or proof.get('model_sha256') != _RING_MESH:
        raise ValueError('Natural ring has no verified closed aperture body')

    # Independently check actual alpha, rather than accepting a manifest flag.
    from PIL import Image
    alpha = Image.open(staged/item['front']).convert('RGBA').getchannel('A').resize((256, 256), Image.Resampling.NEAREST)
    transparent = {(x, y) for y in range(256) for x in range(256) if alpha.getpixel((x, y)) < 128}
    pending = deque(p for p in transparent if p[0] in (0, 255) or p[1] in (0, 255))
    exterior = set(pending)
    while pending:
        x, y = pending.popleft()
        for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if p in transparent and p not in exterior:
                exterior.add(p); pending.append(p)
    holes = transparent-exterior
    significant = 0
    while holes:
        queue = [holes.pop()]; size = 0
        while queue:
            x,y = queue.pop(); size += 1
            for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if p in holes: holes.remove(p); queue.append(p)
        if size > 16: significant += 1
    if significant != 1:
        raise ValueError('Actual ring PNG must contain exactly one natural aperture')

    raw = (staged/item['mesh']).read_bytes()
    if len(raw) < 28 or raw[:4] != b'glTF' or struct.unpack_from('<II', raw, 4) != (2, len(raw)):
        raise ValueError('Malformed natural-ring GLB')
    count, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4E4F534A or 28+count > len(raw): raise ValueError('Malformed ring JSON chunk')
    doc = json.loads(raw[20:20+count]); binary = raw[28+count:]
    names = ['Solid enamel face', 'Solid gold reverse', 'Soft rounded gold edge', 'Natural aperture silver inner wall']
    if [m['name'] for m in doc['meshes'][:4]] != names: raise ValueError('Ring body surfaces differ')
    edges = Counter()
    for mesh in doc['meshes'][:4]:
        for primitive in mesh['primitives']:
            a = doc['accessors'][primitive['attributes']['POSITION']]
            view = doc['bufferViews'][a['bufferView']]
            if a['componentType'] != 5126 or a['type'] != 'VEC3' or a['count'] % 3 or 'indices' in primitive:
                raise ValueError('Malformed ring body positions')
            offset = view.get('byteOffset',0)+a.get('byteOffset',0)
            points = [tuple(round(x,6) for x in struct.unpack_from('<fff', binary, offset+i*12)) for i in range(a['count'])]
            if not all(math.isfinite(x) for point in points for x in point): raise ValueError('Nonfinite ring geometry')
            for i in range(0,len(points),3):
                a,b,c = points[i:i+3]
                for p,q in ((a,b),(b,c),(c,a)): edges[tuple(sorted((p,q)))] += 1
    if not edges or any(n != 2 for n in edges.values()):
        raise ValueError('Actual ring aperture body is not closed two-manifold')


def validate_trophy_assets(root, staged):
    root, staged = Path(root), Path(staged)
    definitions = root/'src/museum/trophy_definitions.cpp'
    if not definitions.exists():
        return
    expected = set(re.findall(r'd\.badge="([A-Za-z0-9_-]+)"', definitions.read_text(encoding='utf-8')))
    manifest = staged/'assets/trophies/manifest.json'
    if not manifest.is_file():
        raise ValueError('Complete trophy artwork manifest is missing; unfinished pins cannot be packaged')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    entries = data.get('entries', [])
    actual = [item['badge'] for item in entries]
    if data.get('schema_version') != 1 or len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('Pin assets must match every actual trophy definition exactly')
    for item in entries:
        for kind, suffix in (('front', '.png'), ('mesh', '.glb')):
            relative = item[kind]
            path = Path(relative)
            if not relative.startswith('assets/trophies/') or '..' in path.parts or path.is_absolute() or path.suffix != suffix:
                raise ValueError(f'Unsafe {kind} path for {item["badge"]}')
            body = (staged/path).read_bytes()
            if hashlib.sha256(body).hexdigest() != item[kind+'_sha256']:
                raise ValueError(f'Pin {kind} hash mismatch for {item["badge"]}')
        if item.get('reviewed') is not True:
            raise ValueError(f'Unreviewed or non-solid pin: {item["badge"]}')
        if item.get('natural_aperture') is True:
            _validate_ring_aperture(staged, item)
        elif item.get('solid_backing') is not True:
            raise ValueError(f'Unreviewed or non-solid pin: {item["badge"]}')
    return len(entries)
