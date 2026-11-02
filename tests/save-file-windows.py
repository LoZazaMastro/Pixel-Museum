"""Compile the Windows reader check with the real app manifest; retain its fixture."""
from pathlib import Path
import os
import subprocess
import uuid

if os.name != "nt":
    print("SKIP native Windows reader fixture")
    raise SystemExit(0)

root=Path(__file__).resolve().parents[1]
out=root/"build/windows-startup-check"
out.mkdir(parents=True,exist_ok=True)
prefix=Path(os.environ.get("PM_MINGW_PREFIX","C:/msys64/mingw64"))
env=dict(os.environ)
env["PATH"]=str(prefix/"bin")+os.pathsep+env.get("PATH","")
resource=out/"reader-test-resource.o"
subprocess.run([str(prefix/"bin/windres.exe"),"-I",str(root/"src/platform/windows"),
                str(root/"src/platform/windows/pixelmuseum.rc"),str(resource)],check=True,env=env)
binary=out/"save-file-windows.exe"
subprocess.run([str(prefix/"bin/g++.exe"),"-std=c++20","-O2","-DNOMINMAX","-DWIN32_LEAN_AND_MEAN",
                "-Wno-deprecated-declarations","-include",str(root/"src/platform/windows/compat.hpp"),
                "-I"+str(root/"src"),str(root/"tests/save-file-windows.cpp"),
                str(root/"src/core/save_file.cpp"),str(resource),"-o",str(binary)],check=True,env=env)
fixture=out/("reader-"+uuid.uuid4().hex[:8])
result=subprocess.run([str(binary),str(fixture)],capture_output=True,text=True,check=True,env=env)
(out/"reader-test-results.txt").write_text(result.stdout,encoding="utf-8")
print(result.stdout,end="")
