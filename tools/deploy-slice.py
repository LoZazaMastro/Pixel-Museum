#!/usr/bin/env python3
"""Install the first isolated Pixel Museum trial, verifying every remote byte."""
from ftplib import FTP,error_perm
from pathlib import Path,PurePosixPath
import hashlib
import json
import time
from package_native_profile import validate_native_profile

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"dist/vertical-slice-ready"
TITLE="PPSA70421"
REMOTE="/data/homebrew/"+TITLE
manifest=json.loads((PARENT/"payload-manifest.json").read_text())
assert manifest["title_id"]==TITLE and manifest["edition"]=="vertical-slice"
folder=PARENT/TITLE
param=json.loads((folder/"sce_sys/param.json").read_text())
validate_native_profile(param)
for row in manifest["files"]:
    relative=PurePosixPath(row["path"])
    assert not relative.is_absolute() and ".." not in relative.parts and not any(c in str(relative) for c in "\r\n\\")
    path=folder/row["path"]
    check=hashlib.file_digest(path.open("rb"),"sha256").hexdigest()
    assert check==row["sha256"] and path.stat().st_size==row["bytes"],row["path"]

report={"title_id":TITLE,"host":"192.168.1.56","port":2121,"remote":REMOTE,"started_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"archive_sha256":manifest["archive_sha256"],"verified":[]}
with FTP() as ftp:
    ftp.connect(report["host"],report["port"],timeout=30);ftp.login("anonymous","codex");ftp.cwd("/data/homebrew")
    # An absent title cannot be running. Existing installs require a separate,
    # explicitly closed-app update workflow; this first-install tool refuses them.
    assert TITLE not in {name for name,_ in ftp.mlsd()},"Target already exists; first-install tool refuses to replace an app"
    ftp.mkd(REMOTE);directories={REMOTE}
    rows=sorted(manifest["files"],key=lambda row:(2 if row["path"]=="sce_sys/param.json" else 1 if row["path"]=="eboot.bin" else 0,row["path"]))
    for n,row in enumerate(rows,1):
        relative=PurePosixPath(row["path"]);directory=PurePosixPath(REMOTE)
        for part in relative.parts[:-1]:
            directory/=part
            if str(directory) not in directories:ftp.mkd(str(directory));directories.add(str(directory))
        remote=REMOTE+"/"+row["path"];temporary=str(directory/('.'+relative.name+'.upload'))
        with (folder/row["path"]).open("rb") as source:ftp.storbinary("STOR "+temporary,source,256*1024)
        digest=hashlib.sha256();size=[0]
        def consume(block):digest.update(block);size[0]+=len(block)
        ftp.retrbinary("RETR "+temporary,consume,256*1024)
        assert size[0]==row["bytes"] and digest.hexdigest()==row["sha256"],f"Remote verification failed: {row['path']}"
        ftp.rename(temporary,remote)
        report["verified"].append(row)
        (ROOT/"build/slice-ftp-verification.json").write_text(json.dumps(report,indent=2)+"\n")
        print(f"[{n}/{len(rows)}] verified {row['path']}",flush=True)
    report["finished_utc"]=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    report["status"]="installed_and_byte_verified"
    (ROOT/"build/slice-ftp-verification.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"Installed {TITLE}: {len(report['verified'])} verified files; no launch performed")
