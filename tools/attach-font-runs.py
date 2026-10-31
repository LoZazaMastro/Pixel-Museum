"""Append bounded UTF-8 run identities to the baked fallback without changing text."""
from pathlib import Path
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"assets/fonts/cjk-subset.huifont"
data=bytearray(path.read_bytes())
magic,version=struct.unpack_from("<II",data)
assert magic==0x46505A50 and version==1
glyph_count,kern_count=struct.unpack_from("<II",data,32)
width,height=struct.unpack_from("<HH",data,8)
assert len(data)==40+glyph_count*24+kern_count*12+width*height
glyphs={struct.unpack_from("<I",data,40+n*24)[0] for n in range(glyph_count)}
prepared_path=ROOT/"build/research/offline-script-shaping/script-runs.json"
prepared=json.loads(prepared_path.read_text(encoding="utf-8"))
runs=prepared["runs"];assert len(runs)<=512
trailer=bytearray(struct.pack("<II",0x534E5552,len(runs)))
for run in runs:
    text=run["text"].encode();glyph=run["private_glyph"]
    assert glyph in glyphs and 0xF0000<=glyph<=0xFFFFD and 0<len(text)<=1024
    trailer+=struct.pack("<II",glyph,len(text))+text
assert len(trailer)<=256<<10
struct.pack_into("<I",data,4,2);data+=trailer
temporary=path.with_suffix(".tmp");temporary.write_bytes(data);temporary.replace(path)
manifest_path=ROOT/"assets/fonts/cjk-source.json"
manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["static_complex_runs"]={"complete_source_phrases":prepared["complete_source_phrases"],"word_boundary_runs":len(runs),"harfbuzz_version":prepared["harfbuzz_version"],"font_sources":prepared["font_sources"],"preparation_sha256":hashlib.sha256(prepared_path.read_bytes()).hexdigest(),"original_utf8_preserved":True,"scope":prepared["scope"]}
manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print(f"ATTACHED {len(runs)} originalUTF8 cluster mappings / {len(trailer)} metadata bytes / {width}x{height} existing fallback atlas")
