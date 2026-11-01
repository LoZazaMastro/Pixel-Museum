#!/usr/bin/env bash
# Build the restricted independent-process writer with the pinned payload SDK.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
sdk="$root/.deps/native/ps5-payload-sdk"
mkdir -p "$root/build/collection-writer"
source "$root/tools/host-env.sh"
PS5_PAYLOAD_SDK="$sdk" sh "$root/tooling/prospero-clang18" -Wall -Wextra -Werror -O2 -I"$root/src" -c "$root/tools/collection-writer/collection_writer.c" -o "$root/build/collection-writer/collection_writer.o"
ld.lld -m elf_x86_64 -pie -T "$sdk/ldscripts/elf_x86_64.x" --eh-frame-hdr -z max-page-size=0x4000 -mllvm -emulated-tls --hash-style=gnu -L "$sdk/target/lib" "$root/build/collection-writer/collection_writer.o" "$sdk/target/lib/crt1.o" -lc -lkernel_web -lSceLibcInternal -lSceNet -o "$root/build/collection-writer/collection_writer.elf"
llvm-strip "$root/build/collection-writer/collection_writer.elf"
python3 - "$root/build/collection-writer/collection_writer.elf" "$root/build/collection_writer.inc" <<'PY'
from pathlib import Path
import sys
import struct
data=Path(sys.argv[1]).read_bytes()
assert data[:6]==b'\x7fELF\x02\x01'
section_offset=struct.unpack_from('<Q',data,40)[0]
section_size,section_count=struct.unpack_from('<HH',data,58)
assert section_offset+section_size*section_count==len(data), 'Loader framing requires ELF section table ending at EOF'
marker=b'PIXEL-MUSEUM-COLLECTION-WRITER-V1'
assert data.count(marker)==1 and data.find(marker)+16384<=len(data)
body='// Generated from tools/collection-writer/collection_writer.c; GPL-3.0-or-later.\nstatic const unsigned char kCollectionWriterElf[]={\n'
body+=',\n'.join(','.join('0x%02x'%x for x in data[i:i+24]) for i in range(0,len(data),24))
body+='\n};\nstatic const std::size_t kCollectionWriterElfSize=sizeof kCollectionWriterElf;\n'
Path(sys.argv[2]).write_text(body,encoding='utf-8')
print('Collection writer ELF:',len(data),'bytes; embedded config:',16384)
PY
