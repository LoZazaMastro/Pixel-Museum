"""Native cancellation and sandbox/process bounds; no remote network traffic."""
from pathlib import Path
import os
import subprocess

if os.name != "nt":
    print("SKIP native Windows media boundary checks")
    raise SystemExit(0)

root = Path(__file__).resolve().parents[1]
output = root / "build/windows-youtube-check"
output.mkdir(parents=True, exist_ok=True)
prefix = Path(os.environ.get("PM_MINGW_PREFIX", "C:/msys64/mingw64"))
environment = dict(os.environ)
environment["PATH"] = str(prefix / "bin") + os.pathsep + environment.get("PATH", "")
resource = output / "boundary-resource.o"
subprocess.run([str(prefix / "bin/windres.exe"), "-I", str(root / "src/platform/windows"),
                str(root / "src/platform/windows/pixelmuseum.rc"), str(resource)],
               check=True, env=environment)
yyjson = output / "boundary-yyjson.o"
subprocess.run([str(prefix / "bin/gcc.exe"), "-std=c11", "-O2", "-c",
                str(root / "src/third_party/yyjson/yyjson.c"), "-o", str(yyjson)],
               check=True, env=environment)
results = []
for name, sources, args in [
    ("http-cancellation-windows", [], []),
    ("youtube-resolver-windows", [str(root / "src/yt/log.cpp"), str(yyjson)], [str(root)]),
]:
    binary = output / (name + ".exe")
    command = [str(prefix / "bin/g++.exe"), "-std=c++20", "-O2",
               "-I" + str(root / "src"), "-I" + str(root),
               str(root / ("tests/" + name + ".cpp")),
               str(root / "src/platform/windows/http_windows.cpp"),
               *sources, str(resource), "-o", str(binary), "-lcurl", "-lwinpthread", "-lws2_32"]
    subprocess.run(command, check=True, env=environment)
    run = subprocess.run([str(binary), *args], capture_output=True, text=True,
                         encoding="utf-8", timeout=35, check=True, env=environment)
    results.append(run.stdout)
    print(run.stdout, end="")
(output / "boundary-results.txt").write_text("".join(results), encoding="utf-8")
