#!/usr/bin/env python3
"""Bounded official ACMI metadata adapter; no media or full articles copied."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import re
import urllib.request

ROOT=Path(__file__).resolve().parent
ARCHIVE="https://raw.githubusercontent.com/ACMILabs/acmi-api/main/app/tsv/works.tsv"
LICENSE="https://github.com/ACMILabs/acmi-api#licences"

def write(n,d):(ROOT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def download():
    target=ROOT/"acmi-works.tsv"
    if target.exists():return target
    with urllib.request.urlopen(ARCHIVE,timeout=25) as source,target.open("wb") as out:
        total=0
        while block:=source.read(1024*1024):
            total+=len(block)
            if total>96*1024*1024:raise ValueError("ACMI metadata archive exceeds 96 MiB")
            out.write(block)
    return target

def main():
    path=download();csv.field_size_limit(16*1024*1024)
    seeds=[];total=0;types=collections.Counter();dates=collections.Counter();images=0;unknown=0
    with path.open(encoding="utf-8",newline="") as source:
        for row in csv.DictReader(source,delimiter="\t"):
            total+=1;types[row["type"]]+=1
            if row["type"]!="Videogame":continue
            match=re.match(r"(\d{4})-",row["first_production_date"])
            year=int(match[1]) if match else None
            if year is not None and 1950<=year<=2026:dates[year//10*10]+=1
            else:unknown+=1
            if row["images"].strip():images+=1
            record="https://api.acmi.net.au/works/"+row["id"]+"/"
            seeds.append({"id":"acmi-"+row["id"],"title":row["title"],"year":year,"kind":"game",
                          "chronology_safe":False,
                          "creator_credit":row["creator_credit"],
                          "source_urls":[record,"https://github.com/ACMILabs/acmi-api/blob/main/app/json/works/"+row["id"]+".json"],
                          "provenance":{"institution":"ACMI","record_id":row["id"],"data_source":row["source"],
                                        "archive_url":ARCHIVE,"data_license":"CC0","license_url":LICENSE,
                                        "date_semantics":"museum first_production_date; NOT asserted first release date",
                                        "date_raw":row["first_production_date"],"production_date_label":row["production_dates"]},
                          "media":{"images_present_in_metadata":bool(row["images"].strip()),"selected_images":[],
                                   "rights_status":"No image or video reuse permission inferred from CC0 metadata"},
                          "status":"primary_collection_research_seed_requires_date_and_story_review","english":{}})
    audit={"institution":"ACMI","archive_bytes":path.stat().st_size,"archive_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
           "total_public_work_records":total,"types":dict(types),"videogame_records":len(seeds),
           "dated_videogame_records_by_decade":dict(sorted(dates.items())),"unknown_or_outside_dates":unknown,
           "game_records_with_image_metadata":images,"selected_or_downloaded_media":0,
           "metadata_license":"CC0","media_license":"Separate permissions required; not covered by metadata CC0",
           "direct_api_result":"HTTP 403 during audit; documented official GitHub archive used instead",
           "release_date_warning":"Some museum production dates differ from public release dates. Treat them as collection claims, not canonical release chronology."}
    write("acmi-seeds.json",{"entries":seeds});write("acmi-audit.json",audit)
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
