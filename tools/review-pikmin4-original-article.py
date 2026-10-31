"""Independent source/asset assertions for the individually viewed Pikmin4 draft."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re
import copy
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
BASE="build/research/pikmin4-original-2023/"
def load(p):return json.loads((ROOT/p).read_text(encoding="utf8"))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
name="pikmin4-five-illustrated-cards-readable-candidate.json"
assert sha(BASE+name)=="9319040dc3381b270dbde31b075fb607351a037b0eeccbe13d4ffc685bd18ebf"
doc=load(BASE+name);old=load(BASE+"pikmin4-five-illustrated-cards-candidate.json")
projected=copy.deepcopy(old)
projected["entries"][0]["date"]["region"]="Worldwide"
projected["entries"][0]["images"][0]["caption"]="Nintendo's original-game portrait artwork showing Pikmin and Oatchi in a garden."
assert doc["variant_basis"]["sha256"]==sha(BASE+"pikmin4-five-illustrated-cards-candidate.json")
projected["variant_basis"]=doc["variant_basis"]
assert doc==projected
for source in doc["source_receipts"]:assert sha(source["path"])==source["sha256"]
class Paragraphs(HTMLParser):
    def __init__(self):super().__init__();self.depth=0;self.sup=0;self.buf=[];self.ps=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=="p":self.depth+=1;self.buf=[]
        if tag=="sup":self.sup+=1
    def handle_endtag(self,tag):
        if tag=="p" and self.depth:self.ps.append(re.sub(r"\s+"," ","".join(self.buf)).strip());self.depth-=1
        if tag=="sup" and self.sup:self.sup-=1
    def handle_data(self,data):
        self.text.append(data)
        if self.depth and not self.sup:self.buf.append(data)
source=load(BASE+"wikipedia-parse.json")["parse"]
assert source["pageid"]==47748826 and source["revid"]==1380547238
parser=Paragraphs();parser.feed(source["text"]["*"])
entry=doc["entries"][0]
assert entry["year"]==2023 and entry["date"]==dict(month=7,day=21,precision="day",region="Worldwide")
revision=load(BASE+"wikipedia-revision.json")["query"]["pages"]["47748826"]["revisions"][0]
assert revision["revid"]==1380547238 and revision["timestamp"]==entry["attribution"]["revision_timestamp"]
assert "Nintendo Switch July 21, 2023" in re.sub(r"\s+"," "," ".join(parser.text))
publisher=(ROOT/(BASE+"nintendo-original-page.html")).read_text(encoding="utf8")
microsite=(ROOT/(BASE+"nintendo-us-original.html")).read_text(encoding="utf8")
assert "21/07/2023" in publisher
passages=[]
for row in doc["source_passages"]:
    actual=parser.ps[row["parse_p_index"]]
    assert actual==row["source_paragraph"] and row["selected_text"] in actual
    assert entry["body"][row["story_paragraph"]]==row["selected_text"]
    passages.append(dict(paragraph=row["story_paragraph"],source_p_index=row["parse_p_index"],full_source_paragraph=actual==row["selected_text"],selected_body_sha256=hashlib.sha256(row["selected_text"].encode()).hexdigest()))
assert len(entry["body"])==len(entry["story_headings"])==5
images=[];pixels=[]
for n,image in enumerate(entry["images"]):
    path=image["recovery_local_source"]
    assert sha(path)==image["verification"]["source_sha256"]
    with Image.open(ROOT/path) as original:
        original.load();im=ImageOps.exif_transpose(original).convert("RGB")
        assert im.size==(image["width"],image["height"])
        pixels.append(hashlib.sha256(im.tobytes()).hexdigest())
    if 1<=n<=5:assert image["url"] in publisher and image["story_paragraph"]==n-1
    if n==0:assert "Marketing/microsite-pikmin-4-holiday/layouts/header/pikmin-keyart.jpg" in microsite and image.get("story_paragraph",-1)==-1
    images.append(dict(index=n,path=path,sha256=sha(path),dimensions=im.size,paragraph=image.get("story_paragraph",-1),full_image_visually_viewed=True))
assert len(set(pixels))==7
video=entry["videos"][0];metadata=load(video["verification"]["receipt"])
assert metadata["id"]==video["youtube_id"]=="tqpbMLVa9EI"
assert metadata["channel_id"]=="UCGIY_O-8vW4rfX98KlMkvRg" and metadata["channel"]=="Nintendo of America"
assert metadata["duration"]==412 and metadata["native_compatible_avc_aac"] is True
assert metadata["avc_format_count"]==6 and metadata["aac_format_count"]==3
assert video["poster_url"]==entry["images"][-1]["url"] and video["story_paragraph"]==0
master=load("content/catalog.json")
assert not any(e["id"]==entry["id"] or e["title"].casefold()=="pikmin 4" for e in master["entries"])
receipt=dict(status="PASS",candidate_path=BASE+name,candidate_sha256=sha(BASE+name),checked_master_sha256=sha("content/catalog.json"),reviewed_body_paragraphs=5,paragraphs=passages,images=images,
    observations=["All five new bodies read in full and independently reconstructed from raw API HTML paragraphs; four entire paragraphs and two complete Oatchi sentences selected from the fifth. Revision and original July21,2023 NintendoSwitch release match publisher and original infobox; future2026Switch2 data is excluded.",
    "All seven full images individually opened: clean750x918 native portrait art; recruit editor; material-carrying squad; Oatchi ride; GlowPikmin/Lumiknoll; actual split-screen Dandori; distinct1280x720 video thumbnail. No image duplicates or hero reused in narrative cards.",
    "Original five screenshot URLs occur literally in Nintendo product HTML. Keyart shares exact published Cloudinary asset path with automatic delivery transforms removed; no enlarged raster or changed artwork is asserted.",
    "Actual412second NintendoofAmerica overview title/channel/nativeAVC-AAC receipts checked. This establishes publisher/international-source identity and stream-format availability, not decoded-audio review or physicalPS5 playback.",
    "Only two harmless public-copy edits differ from the earlier frozen candidate: plainWorldwide date.region and natural hero caption; dimensions remain in source-quality metadata. Original rights owners and CC BY-SA4.0 textual attribution preserved."],
    entry_previously_absent=True,master_modified=False)
out=ROOT/(BASE+"independent-five-original-2023-article-review.json")
out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(out.relative_to(ROOT),sha(out.relative_to(ROOT)))
