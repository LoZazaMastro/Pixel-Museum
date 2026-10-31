"""Check remote collection-media URLs without storing the media in the package."""
import concurrent.futures,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def check(pair):
    url,ids=pair
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 PixelMuseumCatalogue/1.0","Range":"bytes=0-63"})
        with urllib.request.urlopen(req,timeout=25) as r:
            start=r.read(64)
            return dict(url=url,exhibit_ids=ids,status=r.status,mime=r.headers.get("Content-Type",""),bytes=r.headers.get("Content-Length",""),first_bytes=start[:8].hex(),verified="2026-10-20")
    except Exception as e:return dict(url=url,exhibit_ids=ids,error=str(e),verified="2026-10-20")
if __name__=="__main__":
    d=json.loads((ROOT/"catalog.json").read_text(encoding="utf-8"));urls={}
    for entry in d["entries"]:
        for item in entry["images"]+entry["models"]:urls.setdefault(item["url"],[]).append(entry["id"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:report=list(pool.map(check,urls.items()))
    (ROOT/"media-audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    bad=[r for r in report if "error" in r or not (r.get("mime","").startswith("image/") or r.get("first_bytes","").startswith("676c5446"))]
    for r in bad:print(r)
    print(f"Checked {len(report)} distinct image/model URLs: {len(bad)} unavailable or unexpected responses")
