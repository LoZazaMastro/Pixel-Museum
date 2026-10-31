"""Read original Word97 press notes through their CLX text piece tables.

The isolated olefile dependency is retained under research/tool-deps. No Word
application, macros or embedded executable content is invoked.
"""
from pathlib import Path
import struct, sys, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/research/getaway-black-monday-illustrated'
sys.path.insert(0, str(BASE/'tool-deps'))
import olefile

def word_text(path):
    with olefile.OleFileIO(path) as ole:
        doc = ole.openstream('WordDocument').read()
        flags = struct.unpack_from('<H', doc, 10)[0]
        table = ole.openstream('1Table' if flags & 512 else '0Table').read()
        offset = 32
        count = struct.unpack_from('<H', doc, offset)[0]
        offset += 2 + count * 2
        count = struct.unpack_from('<H', doc, offset)[0]
        offset += 2 + count * 4
        pair_count = struct.unpack_from('<H', doc, offset)[0]
        offset += 2
        assert pair_count > 33
        start, size = struct.unpack_from('<II', doc, offset + 33*8)
        clx = table[start:start+size]
        assert len(clx) == size
        pos = 0
        while clx[pos] == 1:
            pos += 3 + struct.unpack_from('<H', clx, pos+1)[0]
        assert clx[pos] == 2
        length = struct.unpack_from('<I', clx, pos+1)[0]
        plc = clx[pos+5:pos+5+length]
        assert len(plc) == length and (length-4) % 12 == 0
        pieces = (length-4)//12
        positions = struct.unpack_from('<'+'I'*(pieces+1), plc)
        result = []
        for i in range(pieces):
            fc = struct.unpack_from('<I', plc, (pieces+1)*4+i*8+2)[0]
            compressed = bool(fc & 0x40000000)
            fc &= 0x3fffffff
            chars = positions[i+1]-positions[i]
            assert chars >= 0
            if compressed:
                fc //= 2
            raw = doc[fc:fc+chars*(1 if compressed else 2)]
            assert len(raw) == chars*(1 if compressed else 2)
            result.append(raw.decode('cp1252' if compressed else 'utf-16le'))
        return ''.join(result).replace('\r', '\n'), pieces

receipt = []
for name in ['G2KEYFEA', 'THE_GETA']:
    path = BASE/'press-assets'/(name+'.DOC')
    text, pieces = word_text(path)
    out = BASE/(name+'-extracted.txt')
    # A changed extraction is visible rather than silently overwriting evidence.
    if out.exists():
        assert out.read_text(encoding='utf8') == text
    else:
        out.write_text(text, encoding='utf8')
    receipt.append(dict(source=str(path.relative_to(ROOT)).replace('\\','/'),
                        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        text=str(out.relative_to(ROOT)).replace('\\','/'),
                        text_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
                        pieces=pieces, characters=len(text)))
(BASE/'word97-piece-table-extraction-receipt.json').write_text(
    json.dumps({'status':'PASS','documents':receipt},indent=2)+'\n',encoding='utf8')
print(json.dumps(receipt,indent=2))
