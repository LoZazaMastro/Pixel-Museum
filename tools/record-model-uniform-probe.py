"""Capture isolated GL comparisons and the real Screen program lifecycle test."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/research/model-uniform-probe"
rows = []
for model in ("ps5", "gamepad", "ps3"):
    row = {"model": model, "exact_4k_angles": []}
    for variant in ("reference", "guarded"):
        path = OUT / (model + "-" + variant + ".log")
        text = path.read_text()
        match = re.search(r"UNIFORM_PROBE: CPU render submission mean([\d.]+)ms max([\d.]+)ms / vec4calls(\d+) per20frames / original(\d+) drawcalls", text)
        assert match and "Cache/revisit PASS" in text and "32 requests remain cancelled" in text
        row[variant] = {"host_cpu_mean_ms": float(match[1]), "host_cpu_max_ms": float(match[2]),
                        "vec4_uniform_calls_per_frame": int(match[3]) // 20, "draw_calls": int(match[4]),
                        "measurement_scope": "20 warm CPU render submissions in software OpenGL, not physical PS5"}
    for angle in (0, 1):
        a = (OUT / f"{model}-reference-{angle}.png").read_bytes()
        b = (OUT / f"{model}-guarded-{angle}.png").read_bytes()
        assert a == b
        row["exact_4k_angles"].append({"angle": angle, "identical_png_sha256": hashlib.sha256(a).hexdigest()})
    rows.append(row)
screen = (OUT / "actual-screen-programs-transitions.log").read_text()
assert "PASS startup model programs: all3 initialized" in screen
assert "Actual Screen model transitions PASS" in screen and "GL=0x0" in screen
assert "intentional_prepared_program_failure" in screen
files = [ROOT / p for p in (
    "src/museum/object_scene.cpp", "src/museum/object_scene.hpp", "src/museum/screen.cpp", "src/museum/screen.hpp",
    "host/model_transition_checks.hpp", "tests/object-scene/unused-uniform-probe.sh",
    "models/playstation-5.glb", "models/wii-u-gamepad.glb", "models/playstation-3-clean-surface.glb",
)]
result = {"status": "exact_output_and_lifecycle_pass", "isolated_comparisons": rows,
          "real_screen_checks": ["three scene programs initialized before navigation", "real prepared shader compile failure",
                                 "partial-program cleanup and cache-disable fallback", "successful program reinitialization",
                                 "PS3 to PS4 to PS3, including cancelled/re-requested model", "large framebuffer reused",
                                 "restored materials followed by original Nintendo3DS", "small3DS to Pong framebuffer retired", "GL errors clear"],
          "source_textures_geometry_material_values_modified": False,
          "upload_caps_increased": False, "physical_ps5_fps_or_load_latency_verified": False,
          "remaining_limit": "Whole GL storage/deletion calls remain non-preemptible; large originals exceed the neighbour cache and still require worker preparation plus cold GPU allocation.",
          "files": {str(p.relative_to(ROOT)): {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
(OUT / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
print("PASS recorded six exact4K comparisons and actual Screen startup/failure/recovery/transitions")
