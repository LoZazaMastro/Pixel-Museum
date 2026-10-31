#!/usr/bin/env python3
"""Adapt existing English Playhub essays into reviewable museum records."""
from pathlib import Path
import collections
import datetime
import json
import re
import statistics
import urllib.parse
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
SOURCE=PROJECT.parent.parent / "Plugin/Playhub/Source/GamingModeDeckyPlugin/quick_settings"
def norm(s):return re.sub(r"[^a-z0-9]","",s.casefold())
def en(s):return s.get("en","").strip() if isinstance(s,dict) else ""
def write(n,x):(ROOT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
catalog=json.loads((PROJECT/"content/catalog.json").read_text(encoding="utf-8"))
current={norm(e["title"]) for e in catalog["entries"]}
imported=json.loads((SOURCE/"history_imported.json").read_text(encoding="utf-8"))["entries"]
entries=[]; excluded=collections.Counter(); all_subjects=set(); english_words=[]
for row in imported:
    t=row["theme"]; date=row.get("anniversary",{}); year=date.get("year"); kind=date.get("kind")
    title=t.get("subject") or t.get("topic","")
    intro=en(t.get("intro")); bodies=[en(c.get("body")) for c in t.get("chapters",[])]
    english_words.append(len((intro+" "+" ".join(bodies)).split()))
    if not isinstance(year,int) or not 1950<=year<=2026:excluded["outside_museum_year_range"]+=1;continue
    if kind not in {"release","birth","foundation"}:excluded["commemoration_not_a_dated_release_or_life_event"]+=1;continue
    urls=list(dict.fromkeys([s for s in t.get("sources",[]) if isinstance(s,str) and s.startswith("https://")]+[c["source_url"] for c in t.get("chapters",[]) if isinstance(c.get("source_url"),str) and c["source_url"].startswith("https://")]))
    if not urls or not intro or not any(bodies):excluded["missing_sources_or_English_copy"]+=1;continue
    if norm(title) in current:excluded["already_in_prototype_title_match"]+=1;continue
    if norm(title) in all_subjects:excluded["duplicate_subject_in_imported_corpus"]+=1;continue
    all_subjects.add(norm(title))
    month,day=map(int,date["date"].split("-"));datetime.date(year,month,day)
    era=next(e["id"] for e in catalog["eras"] if e["start_year"]<=year<=e["end_year"])
    original_kind=t.get("kind","")
    hardware=any(s in original_kind for s in ("hardware","console"))
    event_semantics="announcement" if original_kind.startswith("annuncio_") else kind
    entries.append({"id":t["id"],"title":title,"year":year,
                    "date":{"month":month,"day":day,"precision":"day","region":date.get("region","")},
                    "kind":"technology" if hardware else {"birth":"person","foundation":"organization","release":"game"}[kind],
                    "subtitle":en(t.get("title")),"summary":intro,"body":[s for s in bodies if s],
                    "era_id":era,"layout":"portrait" if kind=="birth" else "essay","tags":["Playhub collection",kind],
                    "related_ids":[],"images":[],"videos":[],"models":[],
                    "sources":[{"title":urllib.parse.urlsplit(u).hostname or "Source","url":u,"publisher":urllib.parse.urlsplit(u).hostname or ""} for u in urls],
                    "featured":False,"factual_note":"Imported dated English Playhub editorial. Adapt its calendar wording, review publisher dates and assign rights-cleared media before presenting as a finished museum stop.",
                    "editorial_status":"existing_English_copy_requires_museum_adaptation",
                    "source_corpus":"Playhub history_imported.json","source_record_id":t["id"],
                    "event_semantics":event_semantics,"original_editorial_kind":original_kind,
                    "source_verification":"existing_local_provenance_not_live_reverified"})
union=set();corpus=[]
for name in ["history_days.json","history_editorial.json","history_imported.json"]:
    d=json.loads((SOURCE/name).read_text(encoding="utf-8"));rows=d.get("days",d.get("themes",d.get("entries",[])))
    rows=list(rows.values()) if isinstance(rows,dict) else rows
    themes=[r.get("theme",r) for r in rows]
    subjects={norm(t.get("subject") or t.get("topic","")) for t in themes}
    union.update(subjects)
    corpus.append({"file":name,"records":len(themes),"unique_subjects":len(subjects),"English_intros":sum(bool(en(t.get("intro"))) for t in themes)})
counts=dict(sorted(collections.Counter((e["year"]//10)*10 for e in entries).items()))
report={"corpora":corpus,"unique_subjects_across_all_three_after_normalizing":len(union),
        "imported_English_words":{"min":min(english_words),"median":statistics.median(english_words),"max":max(english_words)},
        "reviewable_new_museum_records":len(entries),"by_decade":counts,"excluded":dict(excluded),
        "ready_for_immediate_publication":False,"reason":"Existing English essays and source links are real; adaptation, source recheck, media selection and narrative curation remain."}
write("playhub-museum-candidates.json",{"schema_version":1,"status":"review_queue_not_published_collection","entries":entries})
write("adaptation-audit.json",report)
print(json.dumps(report,ensure_ascii=False,indent=2))
