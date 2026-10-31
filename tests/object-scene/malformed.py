#!/usr/bin/env python3
"""Exercise bounded GLB parsing with the exact native C++ loader."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

tester, source = sys.argv[1:3]
raw = Path(source).read_bytes()
size = struct.unpack_from('<I', raw, 12)[0]
original = json.loads(raw[20:20+size])
binary = raw[20+size+8:]

def packed(document):
    data = json.dumps(document, separators=(',', ':')).encode()
    data += b' ' * (-len(data) % 4)
    return struct.pack('<III', 0x46546c67, 2, 28+len(data)+len(binary)) + struct.pack('<II',len(data),0x4e4f534a) + data + struct.pack('<II',len(binary),0x004e4942) + binary

cases = {'truncated-header': raw[:8], 'truncated-download': raw[:-16]}
doc = copy.deepcopy(original);doc['extensionsRequired']=['KHR_draco_mesh_compression'];cases['compressed-required-extension']=packed(doc)
doc = copy.deepcopy(original);doc['buffers'][0]['uri']='https://example.org/external.bin';cases['external-buffer']=packed(doc)
doc = copy.deepcopy(original);doc['bufferViews'][0]['byteOffset']=2**30;cases['buffer-overrun']=packed(doc)
doc = copy.deepcopy(original);doc['accessors'][0]['count']=2**31;cases['accessor-count-limit']=packed(doc)

doc = copy.deepcopy(original);doc['images']=[copy.deepcopy(doc['images'][0]) for _ in range(65)];cases['image-table-limit']=packed(doc)
doc = copy.deepcopy(original);root=doc['scenes'][doc.get('scene',0)]['nodes'][0];doc['nodes'][root]['children']=[root];cases['node-cycle']=packed(doc)
doc = copy.deepcopy(original);doc['meshes'][0]['primitives'][0]['mode']=1;cases['unsupported-lines']=packed(doc)
doc = copy.deepcopy(original);p=doc['meshes'][0]['primitives'][0]['attributes']['POSITION'];doc['accessors'][p]['sparse']={};cases['sparse-position']=packed(doc)
doc = copy.deepcopy(original);doc['extras']={};cur=doc['extras']
for i in range(70):cur['nested']={};cur=cur['nested']
cases['excessive-json-depth']=packed(doc)

with tempfile.TemporaryDirectory(prefix='pixel-museum-glb-') as temp:
    for name,data in cases.items():
        path=Path(temp)/(name+'.glb');path.write_bytes(data)
        result=subprocess.run([tester,str(path),'--validate'],text=True,capture_output=True,timeout=10)
        assert result.returncode==2,(name,result.returncode,result.stdout,result.stderr)
        print(name+': '+result.stdout.strip())
print(f'PASS: {len(cases)} malformed/unsupported files rejected cleanly.')
