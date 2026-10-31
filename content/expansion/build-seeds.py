#!/usr/bin/env python3
"""Collect provenance-bearing research seeds; never fabricate exhibition prose."""
from pathlib import Path
import collections
import argparse
import datetime
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
PLAYHUB = ROOT.parents[3] / "Plugin/Playhub/Source/GamingModeDeckyPlugin/quick_settings"
TODAY = datetime.date(2026, 10, 20)

def write(name, data):
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def english(value):
    return value.get("en", "") if isinstance(value, dict) else value if isinstance(value, str) else ""

def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

def playhub():
    output=[]
    imported=json.loads((PLAYHUB / "history_imported.json").read_text(encoding="utf-8"))
    for row in imported["entries"]:
        theme=row.get("theme", {}); anniversary=row.get("anniversary", {})
        year=anniversary.get("year"); subject=theme.get("subject") or theme.get("topic", "")
        sources=[s for s in theme.get("sources", []) if isinstance(s,str) and s.startswith("https://")]
        if not isinstance(year,int) or not 1950<=year<=2026 or not subject or not sources:
            continue
        kind=anniversary.get("kind", "unknown")
        output.append({"id":"playhub-"+theme["id"], "title":subject,"year":year,
                       "kind":kind, "source_urls":sources,
                       "provenance":{"corpus":"Playhub history_imported.json", "record":theme["id"],
                                     "calendar_date":anniversary.get("date"), "date_semantics":kind},
                       "english":{"title":english(theme.get("title")),"intro":english(theme.get("intro")),
                                  "chapters":[{"title":english(c.get("title")),"body":english(c.get("body"))} for c in theme.get("chapters", [])]},
                       "status":"existing_editorial_requires_museum_adaptation",
                       "chronology_safe":kind in {"release","foundation","birth","hardware","announcement","event"}})
    write("playhub-seeds.json", {"source":"authorized local Playhub corpus", "entries":output})
    summaries={}
    for name in ("history_days.json","history_editorial.json","history_imported.json"):
        data=json.loads((PLAYHUB/name).read_text(encoding="utf-8"))
        if name=="history_days.json":
            rows=list(data["days"].values())
        elif name=="history_editorial.json":
            rows=list(data["themes"].values()) if isinstance(data["themes"],dict) else data["themes"]
        else: rows=[r["theme"] for r in data["entries"]]
        summaries[name]={"records":len(rows), "unique_subjects":len({r.get("subject") or r.get("topic","") for r in rows}),
                         "english_intros":sum(bool(english(r.get("intro"))) for r in rows),
                         "dated_year_fields":sum(isinstance(r.get("year"),int) for r in rows)}
    return output,summaries

def wikidata(decade):
    end=min(decade+10,2027)
    cutoff=f"{end:04}-01-01T00:00:00Z" if decade<2020 else "2026-10-21T00:00:00Z"
    query=f'''SELECT DISTINCT ?item ?label ?released ?article WHERE {{
      ?item wdt:P31 wd:Q7889; wdt:P577 ?released; rdfs:label ?label.
      FILTER(LANG(?label)="en")
      FILTER(?released >= "{decade:04}-01-01T00:00:00Z"^^xsd:dateTime && ?released < "{cutoff}"^^xsd:dateTime)
      FILTER NOT EXISTS {{ ?item wdt:P577 ?earlier. FILTER(?earlier < ?released) }}
      ?article schema:about ?item; schema:isPartOf <https://en.wikipedia.org/>.
    }} ORDER BY ?released ?label LIMIT 130'''
    cache=ROOT / f"wikidata-{decade}-raw.json"
    if cache.exists():
        data=json.loads(cache.read_text(encoding="utf-8"))
    else:
        url="https://query.wikidata.org/sparql?"+urllib.parse.urlencode({"query":query,"format":"json"})
        request=urllib.request.Request(url,headers={"User-Agent":"PixelMuseumResearch/0.1 (bounded historical data audit)","Accept":"application/sparql-results+json"})
        with urllib.request.urlopen(request, timeout=35) as response:
            raw=response.read(4*1024*1024+1)
        if len(raw)>4*1024*1024: raise ValueError("Wikidata response limit")
        data=json.loads(raw)
        cache.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rows=[]
    seen=set()
    for row in data.get("results",{}).get("bindings",[]):
        qid=row["item"]["value"].rsplit("/",1)[-1]
        if qid in seen: continue
        seen.add(qid)
        released=row["released"]["value"]
        title=row["label"]["value"]
        rows.append({"id":"wikidata-"+qid.lower(),"title":title,"year":int(released[:4]),"kind":"game",
                     "source_urls":["https://www.wikidata.org/wiki/"+qid,row["article"]["value"]],
                     "provenance":{"corpus":"Wikidata","entity":qid,"property":"P577","date_value":released,
                                   "date_semantics":"earliest recorded P577 value; region/precision require review", "data_license":"CC0"},
                     "status":"structured_research_seed_requires_editorial_and_primary_source_review",
                     "english":{},"chronology_safe":False})
    write(f"wikidata-{decade}-seeds.json", {"query":query,"retrieved":str(TODAY),"limit":130,"entries":rows})
    return rows

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--wikidata-decade",type=int,choices=list(range(1950,2030,10)),help="Optional single WDQS request; obey endpoint rate limits between runs")
    args=parser.parse_args()
    ROOT.mkdir(exist_ok=True)
    local,summaries=playhub(); output=list(local); remote={}; failures={}
    print("Playhub dated/source-bearing seeds:",len(local),flush=True)
    for decade in range(1950,2030,10):
        if args.wikidata_decade!=decade and not (ROOT/f"wikidata-{decade}-raw.json").exists():
            continue
        try:
            rows=wikidata(decade); remote[str(decade)]=len(rows); output.extend(rows)
            print(decade,len(rows),flush=True)
        except Exception as exc:
            failures[str(decade)]=str(exc);print(decade,"unavailable",str(exc),flush=True)
    counts=collections.Counter((x["year"]//10)*10 for x in output)
    report={"retrieved":str(TODAY),"playhub_corpus":summaries,"playhub_seed_count":len(local),
            "playhub_chronology_safe":sum(x["chronology_safe"] for x in local),
            "wikidata_retrieved_by_decade":remote,"wikidata_failures":failures,
            "seed_records_before_cross_corpus_deduplication":len(output),
            "raw_counts_by_decade":dict(sorted(counts.items())),
            "warning":"Seed counts are research capacity, not finished museum stops. No generated placeholder essays are included."}
    write("research-seeds.json",{"entries":output})
    write("corpus-audit.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=="__main__": main()
