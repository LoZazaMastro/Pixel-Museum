"""Prepare genuine offline HarfBuzz runs without replacing source UTF-8 text."""
from pathlib import Path
import ctypes as C
import ctypes.util
import hashlib
import json
import re
import sys
import urllib.request
from font_display_text import ROOT,collect

sys.path.insert(0,str(ROOT/".deps/fonttools"))
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

OUT=ROOT/"build/research/offline-script-shaping"
OUT.mkdir(parents=True,exist_ok=True)
library=ctypes.util.find_library("harfbuzz")
if not library:raise RuntimeError("Offline HarfBuzz is required to bake static script runs; no unshaped fallback is silently admitted")
hb=C.CDLL(library)
class Info(C.Structure):
    _fields_=[("glyph",C.c_uint32),("mask",C.c_uint32),("cluster",C.c_uint32),("var1",C.c_uint32),("var2",C.c_uint32)]
class Position(C.Structure):
    _fields_=[("x_advance",C.c_int32),("y_advance",C.c_int32),("x_offset",C.c_int32),("y_offset",C.c_int32),("var",C.c_uint32)]
def function(name,result,*arguments):
    method=getattr(hb,name);method.restype=result;method.argtypes=list(arguments);return method
blob_create=function("hb_blob_create",C.c_void_p,C.c_char_p,C.c_uint,C.c_int,C.c_void_p,C.c_void_p)
face_create=function("hb_face_create",C.c_void_p,C.c_void_p,C.c_uint)
font_create=function("hb_font_create",C.c_void_p,C.c_void_p)
set_funcs=function("hb_ot_font_set_funcs",None,C.c_void_p)
set_scale=function("hb_font_set_scale",None,C.c_void_p,C.c_int,C.c_int)
buffer_create=function("hb_buffer_create",C.c_void_p)
add_text=function("hb_buffer_add_utf8",None,C.c_void_p,C.c_char_p,C.c_int,C.c_uint,C.c_int)
guess=function("hb_buffer_guess_segment_properties",None,C.c_void_p)
set_direction=function("hb_buffer_set_direction",None,C.c_void_p,C.c_int)
shape=function("hb_shape",None,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint)
infos=function("hb_buffer_get_glyph_infos",C.POINTER(Info),C.c_void_p,C.POINTER(C.c_uint))
positions=function("hb_buffer_get_glyph_positions",C.POINTER(Position),C.c_void_p,C.POINTER(C.c_uint))
for kind in ("blob","face","font","buffer"):
    function("hb_"+kind+"_destroy",None,C.c_void_p)
version=function("hb_version_string",C.c_char_p)().decode()

families={}
for script in ("Arabic","Bengali","Devanagari","Tamil"):
    path=ROOT/"third_party/fonts"/("NotoSans"+script+"-VF.ttf")
    base="https://raw.githubusercontent.com/google/fonts/main/ofl/notosans"+script.lower()+"/"
    for url,destination,cap in [(base+"NotoSans"+script+"%5Bwdth%2Cwght%5D.ttf",path,8<<20),(base+"OFL.txt",path.with_name("NotoSans"+script+"-LICENSE.txt"),32<<10)]:
        if not destination.exists():
            with urllib.request.urlopen(url,timeout=30) as response:data=response.read(cap+1)
            if len(data)>cap:raise ValueError("Script font source exceeds bound")
            pending=destination.with_suffix(destination.suffix+".part");pending.write_bytes(data);pending.replace(destination)
    source=path.read_bytes();font=TTFont(path)
    instantiateVariableFont(font,{axis.axisTag:(400 if axis.axisTag=="wght" else axis.defaultValue) for axis in font["fvar"].axes},inplace=True)
    static=OUT/(script+"-Regular.ttf");font.save(static)
    data=static.read_bytes();blob=blob_create(data,len(data),0,None,None);face=face_create(blob,0);native=font_create(face);set_funcs(native)
    upem=font["head"].unitsPerEm;set_scale(native,upem,upem)
    families[script]={"font":font,"native":native,"face":face,"blob":blob,"upem":upem,"source_sha256":hashlib.sha256(source).hexdigest(),"source":str(path.relative_to(ROOT))}

pattern=r"[\u0590-\u08ff\u0900-\u0dff]+(?:[ \u00a0]+[\u0590-\u08ff\u0900-\u0dff]+)*"
points,records,source_hashes=collect();full={match for record in records for match in re.findall(pattern,record["text"])}
if any(0xF0000<=cp<0xF0200 for cp in points):
    raise RuntimeError("Displayed source text collides with the internal shaped-run glyph range")
# All contiguous word subphrases keep independently wrapped lines correctly
# shaped; source strings and original ASCII spaces remain untouched.
tokens=set(full)
for phrase in full:
    words=phrase.split(" ")
    for start in range(len(words)):
        for end in range(start+1,len(words)+1):tokens.add(" ".join(words[start:end]))
if len(tokens)>512:raise RuntimeError("Static shaped-run inventory exceeds the bounded native trailer")
target=TTFont(ROOT/"third_party/fonts/NotoSansCJKjp-Regular.ttf")
target_upem=target["head"].unitsPerEm;order=list(target.getGlyphOrder());rows=[]
for n,text in enumerate(sorted(tokens,key=lambda value:(-len(value.encode()),value))):
    cp=ord(text[0])
    if 0x600<=cp<=0x8ff:script="Arabic"
    elif 0x900<=cp<=0x97f:script="Devanagari"
    elif 0x980<=cp<=0x9ff:script="Bengali"
    elif 0xb80<=cp<=0xbff:script="Tamil"
    else:raise RuntimeError(f"Static shaping font not configured for U+{cp:04X}; keep this new script held for a genuine font/layout implementation")
    source=families[script];encoded=text.encode();buffer=buffer_create();add_text(buffer,encoded,len(encoded),0,len(encoded));guess(buffer);set_direction(buffer,5 if script=="Arabic" else 4);shape(source["native"],buffer,None,0)
    count=C.c_uint();glyphs=infos(buffer,C.byref(count));places=positions(buffer,C.byref(count));assert 0<count.value<=128
    pen=TTGlyphPen(None);glyph_set=source["font"].getGlyphSet();source_order=source["font"].getGlyphOrder();x=y=0;detail=[];scale=target_upem/source["upem"]
    for i in range(count.value):
        item,position=glyphs[i],places[i];assert item.glyph and item.cluster<len(encoded)
        name=source_order[item.glyph];drawing=DecomposingRecordingPen(glyph_set);glyph_set[name].draw(drawing)
        drawing.replay(TransformPen(pen,(scale,0,0,scale,(x+position.x_offset)*scale,(y+position.y_offset)*scale)))
        detail.append({"glyph_id":item.glyph,"glyph_name":name,"source_byte_cluster":item.cluster,"x_advance":position.x_advance,"y_advance":position.y_advance,"x_offset":position.x_offset,"y_offset":position.y_offset})
        x+=position.x_advance;y+=position.y_advance
    private=0xF0000+n;name="museum.shaped."+str(n);glyph=pen.glyph();target["glyf"][name]=glyph;order.append(name);target.setGlyphOrder(list(order));glyph.recalcBounds(target["glyf"]);advance=round(x*scale);assert advance>0
    target["hmtx"].metrics[name]=(advance,glyph.xMin)
    for table in target["cmap"].tables:
        if table.isUnicode() and table.format in (12,13):table.cmap[private]=name
    rows.append({"text":text,"script":script,"direction":"rtl" if script=="Arabic" else "ltr","private_glyph":private,"original_full_phrase":text in full,"advance_font_units":advance,"source_units_per_em":source["upem"],"shaped_glyphs":detail})
    hb.hb_buffer_destroy(buffer)
target.save(OUT/"shaped-fallback.ttf")
(OUT/"codepoints.txt").write_text("".join(chr(cp) for cp in sorted(points|{row['private_glyph'] for row in rows})),encoding="utf-8")
report={"status":"offline_static_runs_prepared_for_bake","harfbuzz_version":version,"complete_source_phrases":len(full),"word_boundary_runs":len(rows),"target_units_per_em":target_upem,"source_sha256":source_hashes,"font_sources":{key:{name:value[name] for name in ("source","source_sha256")} for key,value in families.items()},"runs":rows,
        "original_utf8_preserved":True,"scope":"Exact packaged static phrases and their word-boundary subphrases, not a general dynamic complex-script/bidi engine.","proof":"Contextual forms and ligatures come from actual HarfBuzz output; positioned original outline components are baked as complete clusters, not isolated letters or question-mark aliases."}
(OUT/"script-runs.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
for source in families.values():
    hb.hb_font_destroy(source["native"]);hb.hb_face_destroy(source["face"]);hb.hb_blob_destroy(source["blob"])
print(f"PREPARED {len(full)} exact source phrases / {len(rows)} word-boundary runs shaped byHarfBuzz{version}; UTF8 originals unchanged")
