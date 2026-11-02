"""Compile shared update/UI changes with the existing app.ninja PS5 toolchain.

Outputs are isolated: no title packaging, signing, installation or console access.
The optional ELF is a link check against existing objects, not a release artifact.
"""
import concurrent.futures
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
output = root / 'build/ps5-update-compile'
output.mkdir(parents=True, exist_ok=True)
commands = [shlex.split(line.split('=', 1)[1].strip()) for line in (root / 'build/app.ninja').read_text().splitlines() if line.startswith('  command = ')]
compile_commands = {}
for command in commands:
    if '-c' in command:
        compile_commands[command[command.index('-c') + 1]] = command
template = compile_commands[str(root / 'src/museum/screen.cpp')]
sources = [
    'src/museum/database_updater.cpp', 'src/museum/screen_database.cpp',
    'src/core/save_file.cpp', 'src/museum/culture_ambience.cpp',
    'src/platform/remote_cache.cpp', 'src/platform/ps5/http_curl.cpp',
    'src/main.cpp', 'src/museum/playlist.cpp', 'src/museum/experiences.cpp',
    'src/museum/intro.cpp', 'src/museum/history.cpp', 'src/museum/guide.cpp',
    'src/museum/media_scene.cpp', 'src/museum/story.cpp',
    'src/museum/screen_culture_ambience.cpp', 'src/museum/screen_collection.cpp',
    'src/museum/screen.cpp', 'src/museum/screen_desktop.cpp',
    'src/museum/screen_trophies.cpp', 'src/museum/timeline.cpp',
]
environment = dict(os.environ)
sysroot = root / 'build/host-sysroot'
environment['PATH'] = str(sysroot / 'usr/bin') + ':' + str(sysroot / 'usr/lib/llvm-18/bin') + ':' + environment.get('PATH', '')
environment['LD_LIBRARY_PATH'] = str(sysroot / 'usr/lib/x86_64-linux-gnu') + ':' + environment.get('LD_LIBRARY_PATH', '')

# Request's cancellation callback changes its layout. Rebuild every direct
# consumer even when Ninja has already consumed/deleted the .d sidecar.
http_consumers = {
    'src/yt/auth.cpp', 'src/yt/captions.cpp', 'src/yt/decipher.cpp',
    'src/yt/http.cpp', 'src/yt/innertube.cpp', 'src/yt/lounge.cpp',
    'src/yt/service.cpp', 'src/yt/sponsorblock.cpp', 'src/yt/suggest.cpp',
}
ninja = shutil.which('ninja', path=environment['PATH'])
if ninja:
    dependencies = subprocess.run([ninja, '-f', str(root / 'build/app.ninja'), '-t', 'deps'], cwd=root, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if dependencies.returncode == 0:
        target = None
        for line in dependencies.stdout.splitlines():
            if line and not line[0].isspace():
                target = line.split(': #deps', 1)[0]
            elif target and os.path.normpath(line.strip()) == str(root / 'src/yt/http.hpp'):
                prefix = str(root / 'build/obj') + '/'
                if target.startswith(prefix) and target.endswith('.o'):
                    http_consumers.add(target[len(prefix):-2])
sources = list(dict.fromkeys(sources + sorted(http_consumers)))


def compile_one(relative):
    source = str(root / relative)
    command = list(compile_commands.get(source, template))
    destination = output / (relative.replace('/', '_') + '.o')
    command[command.index('-c') + 1] = source
    command[command.index('-o') + 1] = str(destination)
    if '-MF' in command:
        command[command.index('-MF') + 1] = str(destination) + '.d'
    log = destination.with_suffix('.log')
    dependency_file = pathlib.Path(str(destination) + '.d')
    if destination.is_file() and dependency_file.is_file():
        dependencies = shlex.split(dependency_file.read_text().split(':', 1)[1].replace('\\\n', ' '))
        built = destination.stat().st_mtime
        if all(pathlib.Path(path).is_file() and pathlib.Path(path).stat().st_mtime <= built for path in dependencies):
            return relative, destination, 0, log, command
    with log.open('wb') as stream:
        completed = subprocess.run(command, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    return relative, destination, completed.returncode, log, command


results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(compile_one, source) for source in sources]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result)
        source, destination, code, log, command = result
        print(('PASS: ' if code == 0 else 'FAIL: ') + source, flush=True)
        if code:
            print(log.read_text(errors='replace'), flush=True)
report = {'compiled': [{'source': source, 'object': str(destination), 'exit_code': code, 'log': str(log), 'command': command} for source, destination, code, log, command in results]}
(output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
if any(result[2] != 0 for result in results):
    sys.exit(1)

link = next((list(command) for command in commands if command and command[0].endswith('/prospero-lld') and '-o' in command), None)
if link:
    replacements = {str(root / 'build/obj' / (source + '.o')): str(destination) for source, destination, _, _, _ in results}
    link = [replacements.get(argument, argument) for argument in link]
    new_objects = [str(destination) for source, destination, _, _, _ in results if str(root / source) not in compile_commands]
    first_object = next(index for index, argument in enumerate(link) if argument.endswith('.o'))
    link[first_object:first_object] = new_objects
    link[link.index('-o') + 1] = str(output / 'database-update-link-check.elf')
    with (output / 'link.log').open('wb') as stream:
        completed = subprocess.run(link, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    report['link'] = {'exit_code': completed.returncode, 'command': link, 'log': str(output / 'link.log')}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(('PASS: ' if completed.returncode == 0 else 'FAIL: ') + 'isolated PS5 ELF link check', flush=True)
    if completed.returncode:
        print((output / 'link.log').read_text(errors='replace'), flush=True)
        sys.exit(completed.returncode)
print(f'{len(results)} PS5 objects compiled with the exact app.ninja toolchain', flush=True)
