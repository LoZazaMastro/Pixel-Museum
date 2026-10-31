"""Record official browser downloads; never promote unreviewed assets."""
from pathlib import Path
import hashlib
import json
import struct

root = Path(__file__).resolve().parents[1]
items = [
    ('nintendo_switch_2.glb', '9e93543e1c844fa59c19a99b8cad91af', 'Nintendo Switch 2', 'Nicolas Pinilla', 'nicolaspinilla'),
    ('wii_u_gamepad_controller__stand.glb', '0d6ebdb9b5c7442995108e8cdedf4558', 'Wii U GamePad controller and stand', 'Sean O\u2019Connor (mesh), Jon Blenky (textures)', 'syntheticworlds'),
]
records = []
for filename, uid, title, author, profile in items:
    data = (root / 'downloads-original' / filename).read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    assert magic == b'glTF' and version == 2 and length == len(data)
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(data[20:20 + size])
    assert doc.get('meshes')
    assert all('uri' not in b for b in doc.get('buffers', [])), 'External buffer missing'
    assert all('bufferView' in image for image in doc.get('images', [])), 'External image missing'
    records.append(dict(title=title, file='downloads-original/' + filename,
        source_page='https://sketchfab.com/models/' + uid,
        creator=author, creator_page='https://sketchfab.com/' + profile,
        license='CC BY 4.0', license_url='https://creativecommons.org/licenses/by/4.0/',
        acquisition='Official authenticated Sketchfab download control; highest offered GLB texture profile (4K).',
        bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
        meshes=len(doc['meshes']), materials=len(doc.get('materials', [])),
        embedded_images=len(doc.get('images', [])),
        status='downloaded_valid_glb_awaiting_renderer_and_fidelity_review'))
    log_name = 'switch2-renewed-render.log' if uid.startswith('9e93543') else 'wiiu-gamepad-renewed-render.log'
    log_path = root / 'build/research/model-validation' / log_name
    if log_path.exists():
        log = log_path.read_text(encoding='utf-8')
        if log.count('no GL error, state restored.') == 2 and 'Cache/revisit PASS' in log and '32 requests remain cancelled' in log:
            records[-1]['host_renderer_review'] = dict(status='PASS', resolution='3840x2160',
                captures=2, scope='Host renderer only; PS5 performance not measured.',
                log=log_path.relative_to(root).as_posix(),
                limitations=sorted({line.strip() for line in log.splitlines() if 'fidelity limitation:' in line}))
receipt = dict(date='2026-10-21', downloads_available=True, remaining_daily_quota='not exposed',
    records=records, requested_n64=dict(uid='ca4c866eb4a140e8bcef491e2aa83404',
    creator='dark-minaz', status='No official download control on authenticated model page; not extracted.'))
receipt['other_authenticated_pages_without_download_control'] = {
    'PlayStation Vita': 'b698c80f868d45c48722fa69427fb576',
    'Wii U console': '07bf11be88434b96a5ff5493eb71ab23',
    'Master System': '2ef8bccf2552422fa58f851b7d0fdb21',
    'Magnavox Odyssey': '1442250a6bba4c70af4fc6b9807bcfdf',
    'ColecoVision': '5c6d460c88be458aa5dd6a27b0d415dc',
    'Vectrex': '8f6b060e3ddc40fcbc639552f038468f',
    'Game Boy Advance': 'ba9435d1e90b4eafbefee53ace5549d4',
    'Game Gear': '53419a3c52e945aaa2a833e222a31b21',
    'Neo Geo AES': 'e2b303532785471fbad04af56c205b5f',
    'PC Engine': '13de2546562b4cfb9cf0f6fbe78dd521',
    'Xbox Series S': 'fb5aae627c6b4e14b26d43a25b96a18f',
}
target = root / 'build/research/model-validation/renewed-downloads-20261021.json'
target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=True))
