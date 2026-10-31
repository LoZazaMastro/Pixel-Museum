"""Fetch official OFL font sources and collect only catalogue Unicode glyphs."""
from pathlib import Path
import hashlib,json,struct,urllib.request,sys
from font_display_text import collect
ROOT=Path(__file__).resolve().parents[1]
FONTS=ROOT/"third_party/fonts"
URL="https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/NotoSansCJKjp-VF.ttf"
def fetch(url,path,cap):
    if path.exists():return
    pending=path.with_suffix(path.suffix+".part")
    with urllib.request.urlopen(url,timeout=30) as source,pending.open("wb") as out:
        size=0
        while block:=source.read(1024*1024):
            size+=len(block)
            if size>cap:raise ValueError("Font source exceeds transfer bound")
            out.write(block)
    pending.replace(path)
fetch(URL,FONTS/"NotoSansCJKjp-VF.ttf",64<<20)
fetch("https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE",FONTS/"NotoSansCJK-LICENSE.txt",32<<10)
points,_,source_hashes=collect()
(ROOT/"build/catalog-codepoints.txt").write_text("".join(chr(c) for c in sorted(points)),encoding="utf-8")
data=(FONTS/"NotoSansCJKjp-VF.ttf").read_bytes();tables={}
for i in range(struct.unpack_from(">H",data,4)[0]):
    tag,_,offset,length=struct.unpack_from(">4sIII",data,12+16*i);tables[tag]=(offset,length)
axes=[]
if b"fvar" in tables:
    offset,_=tables[b"fvar"];axis_offset,_,axis_count,axis_size=struct.unpack_from(">HHHH",data,offset+4)
    for i in range(axis_count):
        tag,lo,default,hi=struct.unpack_from(">4siii",data,offset+axis_offset+i*axis_size)
        axes.append({"tag":tag.decode(),"default":default/65536,"min":lo/65536,"max":hi/65536})
print(json.dumps({"source_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"extra_codepoints":len(points),"axes":axes},indent=2))
sys.path.insert(0,str(ROOT/".deps/fonttools"))
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.merge import Merger
from fontTools.ttLib.scaleUpem import scale_upem
font=TTFont(FONTS/"NotoSansCJKjp-VF.ttf")
copyrights=sorted({n.toUnicode() for n in font["name"].names if n.nameID==0})
subsetter=subset.Subsetter();subsetter.populate(unicodes=points|set(range(32,127)));subsetter.subset(font)
instantiateVariableFont(font,{"wght":400},inplace=True)
components=[];additional_sources=[]
# The runtime renderer positions codepoints directly. These two sources add
# genuine monochrome emoji/math outlines, not question marks or Latin aliases.
# They do not purport to add Indic shaping, bidi or emoji sequence composition.
covered=set(font.getBestCmap())|set(TTFont(FONTS/"DejaVuSans.ttf").getBestCmap())
for family,file,url,license_url in [
    ("Noto Sans Math","NotoSansMath-Regular.ttf","https://raw.githubusercontent.com/google/fonts/main/ofl/notosansmath/NotoSansMath-Regular.ttf","https://raw.githubusercontent.com/google/fonts/main/ofl/notosansmath/OFL.txt"),
    ("Noto Emoji","NotoEmoji-VF.ttf","https://raw.githubusercontent.com/google/fonts/main/ofl/notoemoji/NotoEmoji%5Bwght%5D.ttf","https://raw.githubusercontent.com/google/fonts/main/ofl/notoemoji/OFL.txt"),
]:
    fetch(url,FONTS/file,8<<20)
    license_file="NotoSansMath-LICENSE.txt" if family=="Noto Sans Math" else "NotoEmoji-LICENSE.txt"
    fetch(license_url,FONTS/license_file,32<<10)
    extra=TTFont(FONTS/file)
    selected=(points-covered)&set(extra.getBestCmap())
    if not selected:continue
    sub=subset.Subsetter();sub.populate(unicodes=selected);sub.subset(extra)
    if "fvar" in extra:instantiateVariableFont(extra,{"wght":400},inplace=True)
    if extra["head"].unitsPerEm!=font["head"].unitsPerEm:scale_upem(extra,font["head"].unitsPerEm)
    for tag in ("GSUB","GPOS","GDEF","MATH","BASE","vhea","vmtx","VORG"):
        if tag in extra:del extra[tag]
    path=ROOT/"build"/(file+".subset.ttf");extra.save(path);components.append(str(path))
    additional_sources.append({"family":family,"source_url":url,"source_sha256":hashlib.sha256((FONTS/file).read_bytes()).hexdigest(),"licence_file":license_file,"added_codepoints":[f"U+{cp:04X}" for cp in sorted(selected)]})
    covered.update(selected)
if components:
    for tag in ("GSUB","GPOS","GDEF","MATH","BASE","vhea","vmtx","VORG"):
        if tag in font:del font[tag]
    path=ROOT/"build/cjk-core-subset.ttf";font.save(path)
    font=Merger().merge([str(path)]+components)
for name in font["name"].names:
    if name.nameID in (1,4,6,16):name.string=("PixelMuseumCJKFallback-Regular" if name.nameID==6 else "Pixel Museum CJK Fallback").encode(name.getEncoding())
    elif name.nameID in (2,17):name.string="Regular".encode(name.getEncoding())
font.save(FONTS/"NotoSansCJKjp-Regular.ttf")
license_text=(FONTS/"NotoSansCJK-LICENSE.txt").read_text(encoding="utf-8")
if copyrights and not license_text.startswith(copyrights[0]):
    (FONTS/"NotoSansCJK-LICENSE.txt").write_text("\n".join(copyrights)+"\n\n"+license_text,encoding="utf-8")
manifest={"source_url":URL,"source_sha256":hashlib.sha256(data).hexdigest(),"source_family":"Noto Sans CJK JP",
          "derived_family":"Pixel Museum CJK Fallback","weight":400,"glyphs_from_catalogue":len(points),
          "license":"SIL Open Font License 1.1","additional_sources":additional_sources,"display_source_sha256":source_hashes,
          "glyph_request_sha256":hashlib.sha256((ROOT/"build/catalog-codepoints.txt").read_bytes()).hexdigest(),
          "modifications":"Exact native-display Unicode subset, regular400 instance, renamed derived font; baked as a secondary SDF atlas. Latin interface faces remain unchanged. Complex-script shaping is not supplied by this font subset."}
(ROOT/"assets/fonts/cjk-source.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
print("Regular400 exact Unicode subset ready")
