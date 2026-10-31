from pathlib import Path
import shlex
import subprocess

# Reuse the actual current SDK compiler/sysroot/ABI flags, without a full build.
commands = Path("build/app.ninja").read_text().splitlines()
for filename in ("study_motion.cpp", "study_space.cpp"):
    for line in commands:
        if line.startswith("  command = ") and "/src/museum/object_scene.cpp " in line and " -c " in line:
            args = shlex.split(line.removeprefix("  command = "))
            output, skip = [], False
            for arg in args:
                if skip:
                    skip = False
                    continue
                if arg in ("-o", "-MF"):
                    skip = True
                    continue
                if arg in ("-MD", "-c"):
                    continue
                output.append(arg.replace("/src/museum/object_scene.cpp", "/src/museum/" + filename))
            subprocess.run(output + ["-fsyntax-only", "-Werror"], check=True)
            print("PASS native ABI syntax:", filename)
            break
    else:
        raise SystemExit("No current native compiler command found")
