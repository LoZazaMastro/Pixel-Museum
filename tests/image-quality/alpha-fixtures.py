from pathlib import Path
import json,struct,zlib
root=Path('build/photo-alpha-package/assets/images');root.mkdir(parents=True,exist_ok=True)
def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
row=b''.join(bytes((40,170,230,a) if a else (255,255,255,0))*100 for a in (0,64,128,192,255))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',500,200,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+row)*200))+chunk(b'IEND',b'')
(root/'alpha-composition.png').write_bytes(png)
(root/'manifest.json').write_text(json.dumps({'images':{'https://local.test/alpha-composition':'assets/images/alpha-composition.png'}}))
