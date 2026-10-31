"""Read the original 2004 press-disc ISO without mounting or running its software."""
from pathlib import Path
import json, hashlib, struct

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'build/research/getaway-black-monday-illustrated'
ISO=BASE/'original-2004-press-assets.iso'
SECTOR=2048
rows=[]
with ISO.open('rb') as disc:
    disc.seek(16*SECTOR)
    descriptor=disc.read(SECTOR)
    assert descriptor[1:6]==b'CD001'
    root=descriptor[156:190]
    visited=set()
    def walk(lba,size,prefix=''):
        assert (lba,size) not in visited
        visited.add((lba,size))
        disc.seek(lba*SECTOR);data=disc.read(size);offset=0
        while offset<len(data):
            length=data[offset]
            if not length:
                offset=((offset//SECTOR)+1)*SECTOR
                continue
            record=data[offset:offset+length];offset+=length
            name=record[33:33+record[32]]
            if name in (b'\0',b'\1'):continue
            name=name.decode('ascii').split(';')[0].rstrip('.')
            assert name not in ('.','..') and '/' not in name and '\\' not in name
            path=prefix+name
            extent=struct.unpack_from('<I',record,2)[0]
            count=struct.unpack_from('<I',record,10)[0]
            if record[25]&2:walk(extent,count,path+'/')
            else:rows.append(dict(path=path,lba=extent,bytes=count))
    walk(struct.unpack_from('<I',root,2)[0],struct.unpack_from('<I',root,10)[0])
    # Only inspect/extract editorial images and text, never executables or demos.
    for row in rows:
        if Path(row['path']).suffix.lower() not in ('.jpg','.jpeg','.png','.bmp','.tif','.tiff','.txt','.pdf','.doc','.rtf'):
            continue
        target=(BASE/'press-assets'/row['path']).resolve()
        assert target.is_relative_to((BASE/'press-assets').resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        disc.seek(row['lba']*SECTOR);data=disc.read(row['bytes']);assert len(data)==row['bytes']
        target.write_bytes(data)
        row['local_file']=target.relative_to(ROOT).as_posix()
        row['sha256']=hashlib.sha256(data).hexdigest()
(BASE/'press-disc-file-inventory.json').write_text(json.dumps({'iso_sha256':hashlib.sha256(ISO.read_bytes()).hexdigest(),'files':rows},indent=2),encoding='utf8')
print(json.dumps(rows,indent=2))
