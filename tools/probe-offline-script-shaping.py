"""Bounded read-only feasibility inventory; does not change runtime text/fonts."""
from pathlib import Path
import ctypes
import ctypes.util
import json
import re
from font_display_text import ROOT,collect

pattern=r"[\u0590-\u08ff\u0900-\u0dff\u0e00-\u0eff\u1780-\u17ff]+(?:[ \u00a0]+[\u0590-\u08ff\u0900-\u0dff\u0e00-\u0eff\u1780-\u17ff]+)*"
_,records,sources=collect()
runs={}
for row in records:
    for text in re.findall(pattern,row["text"]):
        runs.setdefault(text,[]).append({key:row[key] for key in ("file","entry_id","field")})
libraries={name:ctypes.util.find_library(name) for name in ("harfbuzz","freetype","fribidi")}
if libraries["harfbuzz"]:
    hb=ctypes.CDLL(libraries["harfbuzz"]);hb.hb_version_string.restype=ctypes.c_char_p
    libraries["harfbuzz_version"]=hb.hb_version_string().decode()
report={"status":"feasibility_only_not_runtime_shaping_support","libraries":libraries,"distinct_complete_script_runs":len(runs),
        "runs":[{"text":text,"contexts":contexts} for text,contexts in runs.items()],"source_sha256":sources,
        "runtime_limitation":"Font currently maps one codepoint to one baked glyph; real shaping needs complete-run advances/offsets, glyph clusters and safe word-wrap/fit handling. Arabic also needs verified bidi ordering. Adding isolated glyphs is insufficient."}
output=ROOT/"build/research/offline-script-shaping-feasibility.json"
output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
