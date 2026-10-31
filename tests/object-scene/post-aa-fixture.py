from pathlib import Path
import json,struct
root=Path('build/material-fixtures')
raw=(root/'srgb-nearest-filter.glb').read_bytes()
size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);offset=20+size
binary=bytearray(raw[offset+8:])
uv=doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']]
view=doc['bufferViews'][uv['bufferView']]
struct.pack_into('<8f',binary,view.get('byteOffset',0)+uv.get('byteOffset',0),0,0,1,0,1,1,0,1)
(root/'post-aa-sharp-artwork.glb').write_bytes(raw[:offset+8]+binary)
