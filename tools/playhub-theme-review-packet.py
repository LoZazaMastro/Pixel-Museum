from pathlib import Path
import json,sys
sys.stdout.reconfigure(encoding="utf8")
root=Path(__file__).resolve().parents[1]
c=json.loads((root/"content/catalog.json").read_text(encoding="utf8"))["entries"];owners={e["id"]:e for e in c};owners.update({f["id"]:f for e in c for f in e.get("editorial_features",[])})
s=json.loads((root/"content/expansion/playhub-theme-sources/history_editorial.json").read_text(encoding="utf8"))["themes"]
a=json.loads((root/"build/research/kojima-playhub-complete/global-theme-audit-current.json").read_text(encoding="utf8"));mapping={r["theme_id"]:r.get("entry_id")for r in a["themes"]}
for t in s[int(sys.argv[1]):int(sys.argv[1])+int(sys.argv[2])]:
 eid=mapping[t["id"]];e=owners.get(eid)
 print("\nTHEME",t["id"],t["topic"],"TARGET",eid)
 print("SOURCE")
 for n,(h,b)in enumerate([(t["title"]["en"],t["intro"]["en"])]+[(x["title"]["en"],x["body"]["en"])for x in t["chapters"]]):print(n,h,":",b)
 if e:
  print("RUNTIME")
  for n,b in enumerate(e["body"]):print(n,(e.get("story_headings",[])+['']*len(e['body']))[n],":",b)
