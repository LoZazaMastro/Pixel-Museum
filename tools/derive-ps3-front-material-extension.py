#!/usr/bin/env python3
"""Extend existing conventional PS3 shell masks; retain the complete BIN chunk.

No raster repainting, AI, geometry edit, UV edit or source replacement. The
existing source and first display derivation remain independently recoverable.
"""
from pathlib import Path
import hashlib,json,struct
r=Path(__file__).resolve().parents[1]
src=r/'models/playstation-3-clean-surface.glb';b=src.read_bytes()
assert hashlib.sha256(b).hexdigest()=='c74b318cffc6f9e1f6c40fe73b659273836e8b2b90730911b09d187b2886a3bc'
n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);binary=b[20+n:]
before={m['name']:m.get('extras',{}).get('museum_surface_restore') for m in j['materials']}
for m in j['materials']:
 if m['name']=='Main_Body_Plastic':
  # Actual red-mask diagnostic identifies the dusty front flap as the narrow
  # u=.40..48 strip omitted between the two previous shell rectangles.
  m['extras']['museum_surface_restore']['regions'][0][2]=.48
 if m['name']=='SideBack_Plastic':
  s=m['extras']['museum_surface_restore']
  s['regions']=[[0,0,.515,.72],[.515,0,.925,.54]]
  # Retain actual USB labels/apertures on the left atlas border and the
  # authored lower ventilation pattern. Rear-port labels are outside masks.
  s['preserve']=[[0,.065,.032,.255],[.055,.635,.51,.695]]
data=json.dumps(j,separators=(',',':')).encode('utf8');data+=b' '*((-len(data))%4)
out=struct.pack('<III',0x46546c67,2,20+len(data)+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+binary
target=r/'models/playstation-3-clean-front-surface.glb';target.write_bytes(out)
assert out[20+len(data):]==binary
receipt={'source':str(src.relative_to(r)),'source_sha256':hashlib.sha256(b).hexdigest(),'derived':str(target.relative_to(r)),'derived_sha256':hashlib.sha256(out).hexdigest(),'status':'AWAITING_NATIVE_VISUAL_REVIEW','changes':'Only existing UV shell restoration metadata extended. All BIN bytes (geometry, normals, UVs, embedded original artwork) exact. No AI or image retouching. Existing protected wordmarks and logos retained; USB and ventilation areas protected. PS4 untouched.','creator':'Smoggybeard','license':'CC BY-NC-SA 4.0','materials':{m['name']:m.get('extras',{}).get('museum_surface_restore') for m in j['materials'] if m['name'] in ['Main_Body_Plastic','SideBack_Plastic']}}
path=r/'build/research/model-clean-materials/ps3-front-extension-derivation-receipt.json';path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(receipt['derived_sha256'])
