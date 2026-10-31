#!/usr/bin/env bash
# Native OS trophy relay, built from the attributed cached Porpoise payload.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
sdk="$root/.deps/native/ps5-payload-sdk"
mkdir -p "$root/build/notify-relay"
# Use the project's Clang18 wrapper and the SDK's exact payload linker recipe.
# Upstream prospero-clang has unquoted SCRIPT_DIR expansions and fails here
# because the actual project/SDK paths contain spaces.
source "$root/tools/host-env.sh"
PS5_PAYLOAD_SDK="$sdk" sh "$root/tooling/prospero-clang18" -Wall -Werror -O2 -c "$root/tools/notify-relay/museum_notify_relay.c" -o "$root/build/notify-relay/museum_notify_relay.o"
ld.lld -m elf_x86_64 -pie -T "$sdk/ldscripts/elf_x86_64.x" --eh-frame-hdr -z max-page-size=0x4000 -mllvm -emulated-tls --hash-style=gnu -L "$sdk/target/lib" "$root/build/notify-relay/museum_notify_relay.o" "$sdk/target/lib/crt1.o" -lSceNotification -lc -lkernel_web -lSceLibcInternal -lSceNet -o "$root/build/notify-relay/museum_notify_relay.elf"
llvm-strip "$root/build/notify-relay/museum_notify_relay.elf"

python3 - "$root/build/notify-relay/museum_notify_relay.elf" "$root/build/trophy_notify_relay.inc" <<'PY'
from pathlib import Path
import sys
raw=Path(sys.argv[1]).read_bytes();marker=b'PORPOISE-NOTIFY-RELAY-JSON-V1';at=raw.find(marker)
assert raw[:4]==b'\x7fELF' and at>=0 and at+16384<=len(raw)
assert raw[at+len(marker):at+16384]==bytes(16384-len(marker))
rows=[', '.join('0x%02x'%x for x in raw[i:i+24])for i in range(0,len(raw),24)]
body='// Generated from tools/notify-relay/museum_notify_relay.c; GPL-3.0-or-later Porpoise/PS5SX2 attribution retained.\nstatic const unsigned char kNotifyRelay[]={\n'+',\n'.join(rows)+'\n};\nstatic const std::size_t kNotifyRelaySize=sizeof kNotifyRelay;\n'
out=Path(sys.argv[2])
if not out.exists()or out.read_text()!=body:out.write_text(body)
print('Native OS relay embedded:',len(raw),'bytes; JSON room16384 verified')
PY
