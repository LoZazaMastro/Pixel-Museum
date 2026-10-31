"""Read-only, level-bounded check for decoded duplicate PS3 artwork payloads."""
from pathlib import Path
import ctypes
import hashlib
import json
import struct
import time

ROOT=Path(__file__).resolve().parents[1]
cache=ROOT/'models/playstation-3-clean-surface.artwork.pmc'
source=ROOT/'models/playstation-3-clean-surface.glb'
OUT=ROOT/'build/research/ps3-memory-lifetime-audit'
OUT.mkdir(parents=True,exist_ok=True)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(1<<20):h.update(b)
    return h.hexdigest()
z=ctypes.CDLL('libzstd.so.1')
z.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
z.ZSTD_decompress.restype=ctypes.c_size_t
z.ZSTD_isError.argtypes=[ctypes.c_size_t];z.ZSTD_isError.restype=ctypes.c_uint
rows=[];groups={};total=0;largest=0;started=time.perf_counter()
with cache.open('rb') as f:
    prefix=f.read(20);assert prefix[:8]==b'PMAC0001'
    length=struct.unpack_from('<I',prefix,8)[0]
    header=json.loads(f.read(length));payload=20+length
    for atlas in header['atlases']:
        for view in atlas['views']:
            h=hashlib.sha256();raw_total=0;dimensions=[]
            for level in view['levels']:
                size=level['width']*level['height']*4
                f.seek(payload+level['offset']);compressed=f.read(level['compressed_bytes'])
                assert len(compressed)==level['compressed_bytes']
                assert compressed[:4]==b'\x28\xb5\x2f\xfd' and compressed[4]&4
                decoded=ctypes.create_string_buffer(size)
                result=z.ZSTD_decompress(decoded,size,compressed,len(compressed))
                assert not z.ZSTD_isError(result) and result==size
                h.update(struct.pack('<II',level['width'],level['height']))
                h.update(memoryview(decoded).cast('B'))
                dimensions.append([level['width'],level['height']]);raw_total+=size
                largest=max(largest,size)
                del decoded,compressed
            key=(view['role'],atlas['width'],atlas['height'],h.hexdigest())
            groups.setdefault(key,[]).append(atlas['index'])
            total+=raw_total
            rows.append({'atlas':atlas['index'],'role':view['role'],'data_channels':atlas['data_channels'],
                         'dimensions':[atlas['width'],atlas['height']],'levels':len(dimensions),
                         'all_mip_dimensions_and_bytes_sha256':h.hexdigest(),'raw_bytes':raw_total})
duplicates=[{'role':key[0],'dimensions':list(key[1:3]),'payload_sha256':key[3],'atlas_indices':value}
            for key,value in groups.items() if len(value)>1]
out={'status':'READ_ONLY_EXACT_MIP_DUPLICATE_AUDIT_COMPLETE',
     'source':{'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source),'bytes':source.stat().st_size},
     'cache':{'path':cache.relative_to(ROOT).as_posix(),'sha256':sha(cache),'bytes':cache.stat().st_size},
     'view_count':len(rows),'logical_RGBA_mip_bytes':total,'largest_single_level_decode_bytes':largest,
     'decoded_identical_same_role_view_groups':duplicates,'views':rows,
     'elapsed_host_seconds':time.perf_counter()-started,
     'findings':['Every frame content checksum was verified by the reference Zstandard decoder.',
                 'Whole decoded chains were hashed including each mip dimension; encoded PNG differences cannot hide duplicates.',
                 'GPU2x conservative accounting is not a direct physical PS5 residency or CPU working-set measurement.',
                 'No source, sidecar, texture, material, native executable or catalogue was modified.'],
     'implementation_change':False}
p=OUT/'exact-decoded-atlas-duplicates.json'
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'views':len(rows),
                  'duplicates':len(duplicates),'logical_bytes':total,'seconds':out['elapsed_host_seconds']}))
