"""Independently reconcile all chapter boundaries and label-recorded credits."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
BASE="build/research/soundtrack-broad/modern-next-four/"
NAME="tetris40-resident-evil-seven81-public-collections-candidate.json"
EXPECTED="1c8950c4fb9f5269fa21c13babbbcc5f3c223c4d954fc097015ff95acf52c72a"
def load(p):return json.loads((ROOT/p).read_text(encoding="utf8"))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
assert sha(BASE+NAME)==EXPECTED
doc=load(BASE+NAME)
for source in doc["source_receipts"]:assert sha(source["path"])==source["sha256"]
publisher=(ROOT/(BASE+"tetris-original-2020-official.html")).read_text(encoding="utf8")
assert "https://www.youtube.com/channel/UCtswPJbKycCoSBo_3K2ZReA" in publisher
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,data):self.parts.append(data)
html=Text();html.feed(publisher);publisher_text=re.sub(r"\s+"," "," ".join(html.parts))
assert "digital soundtrack includes 40 songs" in publisher_text
assert "2020.05.28" in publisher_text and "streaming in full on Hydelic" in publisher_text
label=load(BASE+"resident-evil-seven-label-metadata.json")
label_tracks=[row for row in label["results"] if row.get("wrapperType")=="track"]
assert len(label_tracks)==81 and label["results"][0]["collectionId"]==1193905100
steam=load(BASE+"resident-evil-seven-steam-publisher.json")["583810"]
assert steam["success"] and "81 bone-chilling tracks" in steam["data"]["detailed_description"]
master=load("content/catalog.json");owners={e["id"]:e for e in master["entries"]}
rooms=[];all_rows=[]
for entry in doc["entries"]:
    tracks=entry["tracks"];is_re7=len(tracks)==81
    assert len(tracks) in (40,81)
    owner=owners[entry["entry_id"]]
    assert owner["year"]==entry["match_year"] and owner["title"]==entry["match_title"]
    watch=load(tracks[0]["publication_metadata_receipt"])
    native=load(tracks[0]["native_codec_metadata_receipt"])
    assert watch["title"]==native["title"] and watch["channelId"]==native["channel_id"]
    assert native["native_compatible_avc_aac"] is True and native["avc_format_count"]>0 and native["aac_format_count"]>0
    assert int(watch["lengthSeconds"])==native["duration"]==(8932 if is_re7 else 10174)
    if is_re7:assert watch["channelId"]=="UCzrZxFY5MXhBq67zyXI59FQ" and watch["author"]=="GameMusicSound"
    else:assert watch["channelId"]=="UCtswPJbKycCoSBo_3K2ZReA" and watch["author"]=="Hydelic"
    lines=watch["shortDescription"].splitlines();seen=set()
    for n,track in enumerate(tracks):
        line=track["source_actual_chapter_line"]
        assert line in lines
        timestamp=re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)\s*$",line) if is_re7 else re.match(r"(\d{1,2}:\d{2}(?::\d{2})?)\s+",line)
        assert timestamp
        start=sum(int(v)*60**i for i,v in enumerate(reversed(timestamp.group(1).split(":"))))
        end=tracks[n+1]["start_seconds"] if n+1<len(tracks) else int(watch["lengthSeconds"])
        assert track["start_seconds"]==start and track["end_seconds"]==end and start<end
        assert track["duration_seconds"]==end-start and track["source_publication_duration_seconds"]==int(watch["lengthSeconds"])
        key=(track["youtube_id"],start,end);assert key not in seen;seen.add(key)
        assert track["youtube_id"]==native["id"] and track["channel_url"].endswith(native["channel_id"])
        assert track["native_codec_metadata_verified"] is True and track["playback_verified_on_ps5"] is False
        if is_re7:
            expected=label_tracks[n]
            assert track["published_album_track_number"]==expected["trackNumber"]==n+1
            assert track["title"]==expected["trackName"] and track["label_artist_credit"]==track["creator"]==expected["artistName"]
            assert track["official_uploader_verified"] is False
        else:
            assert track["creator"]=="Hydelic" and track["official_uploader_verified"] is True
            assert line[timestamp.end():].strip()==track["source_actual_chapter_title"]==track["title"]
        all_rows.append(dict(entry_id=entry["entry_id"],ordinal=n+1,title=track["title"],creator_as_recorded=track["creator"],start_seconds=start,end_seconds=end,source_actual_chapter_line=line,label_credit_role_not_inferred=is_re7))
    assert entry["full_album_collection"] is (not is_re7)
    rooms.append(dict(entry_id=entry["entry_id"],tracks=len(tracks),actual_publication_title=watch["title"],channel_id=watch["channelId"],duration_seconds=native["duration"],all_bounds_reconstructed=True))
assert len(all_rows)==121
receipt=dict(status="PASS",candidate_path=BASE+NAME,candidate_sha256=EXPECTED,checked_master_sha256=sha("content/catalog.json"),reviewed_recordings=121,rooms=rooms,tracks=all_rows,
    observations=["All121 display titles, artists and source chapter lines read. Each start time independently parsed from actual source description and each end time reconstructed from the next chapter or actual publication duration; no skipped or overlapping passages.",
    "Hydelic official channel identity is literally linked by the game publisher's28May2020 original40-song soundtrack announcement. The40 chapters form that official full original album; Connected2023Volume2 is not substituted.",
    "RE7 Steam publisher confirms81-track original soundtrack. All81 ordinals/display titles/recording artists match actual Apple label collection1193905100; source chapter typo HappyHappyEnding is documented separately from label title HappyHappyBirthday. BeginningHour andVRTutorial are label-listed original2017album cues.",
    "RE7 label spellings MichaelA.Levin and CrisVelaco are reproduced as label-recorded artist metadata; the archive chapters instead spell Levine/Velasco. This receipt does not independently assign composition, performance or arrangement roles, or normalize author identities.",
    "Actual native metadata contains positiveAVC/AAC selections on both publications. This is metadata/identity verification, not audio-fingerprint matching, decoded-listening review, retail-master equivalence or physicalPS5 playback."],
    source_receipts_checked=len(doc["source_receipts"]),master_modified=False)
out=ROOT/(BASE+"independent-one-hundred-twenty-one-collection-review.json")
out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(out.relative_to(ROOT),sha(out.relative_to(ROOT)))
