#!/usr/bin/env python3
"""Bind the existing lossless PS3 artwork payload to a metadata-only variant."""
from pathlib import Path
import struct,json,hashlib,copy
r=Path(__file__).resolve().parents[1]
old=r/'models/playstation-3-clean-surface.glb';new=r/'models/playstation-3-clean-front-surface.glb'
def glb(p):
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];return b,json.loads(b[20:20+n]),b[20+n:]
a,aj,ab=glb(old);b,bj,bb=glb(new);assert ab==bb
def without_restore(j):
 j=copy.deepcopy(j)
 for m in j['materials']:
  if m['name'] in ['Main_Body_Plastic','SideBack_Plastic']:m.get('extras',{}).pop('museum_surface_restore',None)
 return j
assert without_restore(aj)==without_restore(bj),'Only selected material restoration extras may differ'
src=r/'models/playstation-3-clean-surface.artwork.pmc';cache=src.read_bytes();assert cache[:8]==b'PMAC0001'
n,h=struct.unpack_from('<IQ',cache,8);header=cache[20:20+n];payload=cache[20+n:]
def fnv(data):
 v=1469598103934665603
 for c in data:v=((v^c)*1099511628211)&0xffffffffffffffff
 return v
assert fnv(header)==h
j=json.loads(header);assert j['source_bytes']==len(a) and j['source_sha256']==hashlib.sha256(a).hexdigest()
j['source_bytes']=len(b);j['source_sha256']=hashlib.sha256(b).hexdigest()
text=json.dumps(j,separators=(',',':'),sort_keys=True).encode();out=cache[:8]+struct.pack('<IQ',len(text),fnv(text))+text+payload
dst=r/'models/playstation-3-clean-front-surface.artwork.pmc';dst.write_bytes(out);assert out[20+len(text):]==payload
receipt={'status':'PASS_HEADER_ONLY_CLONE_PENDING_NATIVE_CACHE_HITS','source_cache':str(src.relative_to(r)),'source_cache_sha256':hashlib.sha256(cache).hexdigest(),'source_glb_sha256':hashlib.sha256(a).hexdigest(),'new_glb_sha256':hashlib.sha256(b).hexdigest(),'new_cache':str(dst.relative_to(r)),'new_cache_sha256':hashlib.sha256(out).hexdigest(),'version':1,'payload_sha256':hashlib.sha256(payload).hexdigest(),'payload_bytes':len(payload),'new_bytes':len(out),'assertions':['Entire GLB BIN byte-identical','GLB JSON identical except two permitted material surface-restore extras','Old PMAC header FNV and source bytes/SHA validated','Only source_bytes/source_sha256 changed in PMAC JSON','All atlas records and compressed pixel/mip payloads exact','New header FNV recomputed, payload-relative offsets unchanged']}
p=r/'build/research/model-clean-materials/ps3-front-extension-identical-artwork-cache-clone.json';p.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(receipt['new_cache_sha256'])
