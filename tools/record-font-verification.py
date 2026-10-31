"""Record the tested static font snapshot; never claims physical-console QA."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import re
import argparse
from font_display_text import ROOT, collect

arguments = argparse.ArgumentParser()
arguments.add_argument('--log-prefix', default='')
options = arguments.parse_args()
output = ROOT / "build/research/offline-script-shaping/verification.json"
audit = json.loads((ROOT / "build/research/font-coverage.json").read_text())
prepared = json.loads((output.parent / "script-runs.json").read_text())
_, _, actual_sources = collect()
assert audit["input_source_sha256"] == actual_sources
assert audit["ordinary_glyph_status"] == "pass" and not audit["stale_subset_inputs"]
assert not audit["complex_shaping_unresolved"] and not audit["static_complex_runs_unsupported"]
assert prepared["source_sha256"] == actual_sources
logs = {
    "native": "native-build.log",
    "runtime_units": "runtime-unit.log",
    "actual_gl": "runtime-actual-gl-final.log",
    "source_prose_regression": "narrative-regression.log",
}
if options.log_prefix:
    logs = {'native': options.log_prefix + '-native-build.log',
            'runtime_units': options.log_prefix + '-shaped-runs.log',
            'actual_gl': options.log_prefix + '-actual-gl.log',
            'source_prose_regression': options.log_prefix + '-narrative-regression.log'}
for name in ("runtime_units", "actual_gl", "source_prose_regression"):
    assert "PASS" in (output.parent / logs[name]).read_text()
native_log = (output.parent / logs["native"]).read_text()
assert "FAILED:" not in native_log and "error:" not in native_log
paths = [ROOT / "build/eboot.elf", ROOT / "assets/fonts/cjk-source.json"]
paths += sorted((ROOT / "assets/fonts").glob("*.huifont"))
paths += [ROOT / p for p in (
    "src/gfx/font.cpp", "src/gfx/font.hpp", "src/gfx/font_format.hpp",
    "src/museum/screen.cpp", "src/museum/object_scene.cpp", "tools/font-baker/bake_font.cpp",
    "tools/font_display_text.py", "tools/prepare-cjk.py", "tools/prepare-script-runs.py",
    "tools/attach-font-runs.py", "tools/audit-font-coverage.py", "tools/bake-fonts.sh",
    "tests/font-shaped-runs.cpp", "host/unicode_font_checks.hpp",
)]
paths += [ROOT / "build/previews" / p for p in (
    "unicode-fonts-dark-4k.png", "unicode-fonts-light-4k.png",
    "unicode-atlas-extended-dark-4k.png", "unicode-atlas-extended-light-4k.png",
    "script-runs-runtime-dark-4k.png", "script-runs-runtime-light-4k.png",
    "unicode-iraq-original-story-4k.png",
)]
files = {str(p.relative_to(ROOT)).replace("\\", "/"): {
    "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()
} for p in paths}
for path in sorted((ROOT / "assets/fonts").glob("*.huifont")):
    runtime_font = ROOT / "build/runtime-preview/assets/fonts" / path.name
    assert runtime_font.is_file() and hashlib.sha256(runtime_font.read_bytes()).hexdigest() == files[path.relative_to(ROOT).as_posix()]["sha256"], "Actual Screen preview font differs from recorded source asset"
catalogues = {name: {
    "bytes": (ROOT / name).stat().st_size,
    "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
} for name in ("content/catalog.json", "build/runtime-preview/content/catalog.json")}
fallback = (ROOT / "assets/fonts/cjk-subset.huifont").read_bytes()
import struct
atlas_width, atlas_height = struct.unpack_from("<HH", fallback, 8)
actual_log = (output.parent / logs["actual_gl"]).read_text()
assert f"PASS rectangular font atlas {atlas_width}x{atlas_height}" in actual_log
host_texture_limit = int(re.search(r"hostGL maximum(\d+)", actual_log).group(1))
receipt = {
    "status": "host_and_native_compile_pass",
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "actual_source_sha256": actual_sources,
    "coherent_catalogues": catalogues,
    "fallback_atlas": {"width": atlas_width, "height": atlas_height,
        "r8_texel_bytes": atlas_width * atlas_height, "bake_maximum_height": 4096,
        "queried_host_GL_MAX_TEXTURE_SIZE": host_texture_limit, "physical_ps5_texture_limit_measured": False,
        "font_file_read_limit_bytes": 10 << 20, "scope": "Font-only bounded allowance; global save/JSON and model memory caps unchanged."},
    "ordinary_display_codepoints": len(audit["ordinary_codepoints"]),
    "visible_ordinary_codepoints": len(audit["visible_ordinary_codepoints"]),
    "current_complete_script_phrases": len(audit["static_complex_runs_required"]),
    "genuine_harfbuzz_word_boundary_runs": len(prepared["runs"]),
    "harfbuzz_version": prepared["harfbuzz_version"],
    "original_utf8_preserved": True,
    "general_dynamic_complex_script_or_bidi_support": False,
    "native_harfbuzz_dependency_added": False,
    "additional_font_texture_slots": 0,
    "v2_font_requires_v2_capable_executable": True,
    "physical_ps5_rendering_verified": False,
    "console_transfer_performed": False,
    "logs": logs,
    "files": files,
    "limits": "Exact packaged static script phrases and their contiguous whole-word subphrases. New unsupported phrases/scripts fail the bake audit; this is not a general dynamic Unicode layout engine.",
}
output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Recorded", output.relative_to(ROOT), files["build/eboot.elf"])
