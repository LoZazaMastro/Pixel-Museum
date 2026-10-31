"""Check shipped font coverage against actual catalogue Unicode characters."""
import json
import struct
import unicodedata
from pathlib import Path
import hashlib
from font_display_text import collect,script_class,complex_runs

ROOT = Path(__file__).resolve().parents[1]


def glyphs(path):
    data = path.read_bytes()
    magic, version = struct.unpack_from("<II", data)
    assert magic==0x46505A50 and version in (1,2),path
    count = struct.unpack_from("<I", data, 32)[0]
    assert 40 + count * 24 <= len(data), path
    return {struct.unpack_from("<I", data, 40 + n * 24)[0] for n in range(count)}


def shaped_runs(path):
    data=path.read_bytes()
    if struct.unpack_from("<I",data,4)[0]==1:return set()
    width,height=struct.unpack_from("<HH",data,8)
    count,kerns=struct.unpack_from("<II",data,32)
    at=40+count*24+kerns*12+width*height
    tag,count=struct.unpack_from("<II",data,at);at+=8
    assert tag==0x534E5552 and count<=512
    available=glyphs(path);result=set()
    for _ in range(count):
        glyph,length=struct.unpack_from("<II",data,at);at+=8
        assert glyph in available and 0<length<=1024
        text=data[at:at+length].decode();at+=length
        assert text not in result
        result.add(text)
    assert at==len(data)
    return result


def main():
    fonts = ROOT / "assets/fonts"
    fallback = glyphs(fonts / "unicode-fallback.huifont") | glyphs(fonts / "cjk-subset.huifont")
    # The live native-display inventory is authoritative, never an old build
    # codepoint file. Report stale inputs even if the old subset happens to fit.
    requested,records,source_hashes=collect()
    manifest=json.loads((fonts/"cjk-source.json").read_text(encoding="utf-8"))
    current_request=hashlib.sha256("".join(chr(c) for c in sorted(requested)).encode()).hexdigest()
    stale=manifest.get("display_source_sha256")!=source_hashes or manifest.get("glyph_request_sha256")!=current_request
    # These are the reported failures, checked for every interface face,
    # including Montserrat headings rather than only the body typeface.
    reported={c for c in requested if script_class(c)=="ordinary_glyph"}
    checks = []
    for name in ("inter-regular", "inter-semibold", "montserrat-medium", "dejavu-sans-mono"):
        supported = glyphs(fonts / (name + ".huifont")) | fallback
        missing = sorted(reported - supported)
        checks.append({"face": name, "reported_codepoints": len(reported), "missing": missing})
    supported = glyphs(fonts / "inter-regular.huifont") | fallback
    def describe(c):
        return {"codepoint":f"U+{c:04X}","name":unicodedata.name(chr(c),"UNNAMED"),"class":script_class(c),
                "contexts":[{k:r[k] for k in ("file","entry_id","field","text")} for r in records if chr(c) in r["text"]][:4]}
    other_missing = [describe(c)
                     for c in sorted(requested - supported)]
    required_runs=complex_runs(records);covered_runs=shaped_runs(fonts/"cjk-subset.huifont")
    unsupported_runs=[text for text in required_runs if text not in covered_runs]
    handled_complex={ord(c) for text in required_runs if text in covered_runs for c in text}
    shaping=[describe(c) for c in sorted(requested) if script_class(c)!="ordinary_glyph" and (c not in handled_complex or any(chr(c) in text for text in unsupported_runs))]
    report = {"ordinary_glyph_status":"fail" if any(c["missing"] for c in checks) else "pass", "checks": checks,
              "ordinary_codepoints":sorted(reported),
              "visible_ordinary_codepoints":[c for c in sorted(reported) if unicodedata.category(chr(c)) not in ("Cf","Zs","Zl","Zp") and c!=0x034F and not(0xFE00<=c<=0xFE0F or 0xE0100<=c<=0xE01EF)],
              "other_uncovered_codepoints": other_missing,
              "complex_shaping_unresolved":shaping,"current_display_codepoints":len(requested),
              "static_complex_runs_status":"pass" if not unsupported_runs else "unresolved",
              "static_complex_runs_required":required_runs,"static_complex_runs_unsupported":unsupported_runs,
              "general_dynamic_complex_script_support":False,
              "input_source_sha256":source_hashes,"stale_subset_inputs":stale,
              "scope": "Live native-display fields, including full public Credits and all packaged locale text. Hidden ingestion/research notes are excluded. Glyph presence is not evidence of complex-script shaping."}
    output = ROOT / "build/research/font-coverage.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{'FAIL' if stale else 'CURRENT'}: subset source hashes and glyph request match current display inventory.")
    print(f"{report['ordinary_glyph_status'].upper()}: {len(reported)} ordinary Unicode codepoints across four faces.")
    print(f"Exact packaged static complex runs: {len(required_runs)-len(unsupported_runs)}/{len(required_runs)}; unresolvedcomplex points: {len(shaping)}")
    print(f"Complex codepoints without individual glyphs: {len(other_missing)} (complete shaped-run coverage audited separately; no general dynamic shaping claim)")
    assert not stale,"Run tools/bake-fonts.sh after changing displayed catalogue/locale text"
    assert not any(c["missing"] for c in checks),"Ordinary Unicode glyphs missing; see build/research/font-coverage.json"
    assert not unsupported_runs and not shaping,"Packaged complex-script text requires genuine shaped runs; see build/research/font-coverage.json"


if __name__ == "__main__":
    main()
