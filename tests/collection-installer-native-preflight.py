"""Compile the real native preflight branch without any volume-stat API."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
source = (root / 'src/museum/collection_installer.cpp').read_text()
function = source[source.index('bool available_bytes('):source.index('struct SmallRead')]
out = root / 'build/collection-installer-tests'
out.mkdir(exist_ok=True)
test = out / 'native-preflight-no-syscalls.cpp'
test.write_text('''#include <cassert>
#include <cerrno>
#include <cstdint>
#include <string>
// Set only after system includes; exercise the console branch on the host.
#define __FreeBSD__ 1
#define statfs(...) FORBIDDEN_UNVERIFIED_NATIVE_STATFS
#define statvfs(...) FORBIDDEN_UNVERIFIED_NATIVE_STATVFS
''' + function + '''
int main() {
    std::uint64_t bytes=123;
    errno=0;
    assert(!available_bytes("/download0/pixelmuseum/collection",bytes));
    assert(errno==ENOSYS && bytes==123);
}
''')
binary = out / 'native-preflight-no-syscalls'
subprocess.run(['clang++-18', '-std=c++17', str(test), '-o', str(binary)], check=True)
subprocess.run([str(binary)], check=True)
assert 'code==ENOSPC||code==EDQUOT' in source
print('PASS native preflight: no statfs/statvfs dependency, ENOSYS, unchanged byte count; ENOSPC/EDQUOT handling retained')
