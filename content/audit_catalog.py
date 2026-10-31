"""Check catalog structure and report the current availability of its sources."""
import concurrent.futures,datetime,html,json,re,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def check(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 PixelMuseumCatalogueResearch/1.0"})
        with urllib.request.urlopen(req,timeout=25) as response:
            data=response.read(500000); mime=response.headers.get("Content-Type","")
            text=data.decode("utf-8",errors="replace") if "html" in mime else ""
            match=re.search(r"<title[^>]*>(.*?)</title>",text,re.S|re.I)
            title=html.unescape(re.sub(r"\s+"," ",match.group(1))).strip() if match else ""
            youtube=sorted(set(re.findall(r"(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/)([\w-]{11})",text)))
            return dict(url=url,status=response.status,resolved_url=response.url,mime=mime,title=title,youtube_ids=youtube,verified="2026-10-20")
    except Exception as e:return dict(url=url,error=str(e),verified="2026-10-20")
if __name__=="__main__":
    catalog=json.loads((ROOT/"catalog.json").read_text(encoding="utf-8"))
    ids=[x["id"] for x in catalog["entries"]]
    assert len(ids)==len(set(ids)),"Duplicate exhibit IDs"
    for entry in catalog["entries"]:
        assert set(entry["related_ids"]) <= set(ids),(entry["id"],"Unknown related ID")
        assert entry["body"] and entry["sources"]
        d=entry["date"]
        if d["precision"]=="day":datetime.date(entry["year"],d["month"],d["day"])
        if d["precision"]=="year":assert d["month"]==d["day"]==0
    urls=sorted(set(s["url"] for e in catalog["entries"] for s in e["sources"]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check,urls))
    (ROOT/"source-audit.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for result in results:print(result.get("status",result.get("error")),result["url"],result.get("title",""),result.get("youtube_ids",[]))
    print(f"Schema OK: {len(ids)} exhibits, {len(urls)} unique sources")
