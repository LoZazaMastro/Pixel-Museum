"""Native display text remains included; hidden research cannot bloat atlases."""
from pathlib import Path
import json
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from font_display_text import collect,script_class

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)
    def write(name,value):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False),encoding="utf-8")
    write("content/catalog.json",{"entries":[{"id":"fixture","title":"任天堂","body":["été"],"factual_note":"𓀀",
        "images":[{"title":"தமிழ்","credit":"By作者","selection_query":"𓀁"}],
        "models":[{"display_caption":"Platinum","include_groups":["node:𓀂"]}],
        "sources":[{"publisher":"Ω","title":"حرب","raw_page":"𓀃"}],
        "soundtrack_rooms":[{"composer":"音楽","tracks":[{"title":"𝒬","creator":"John","raw_description":"𓀄"}]}],
        "editorial_features":[{"id":"feature","body":["テスト"],"verification_notes":"𓀅"}]}]})
    write("content/human-history.json",{"entries":[{"id":"culture","summary":"café"}]})
    write("content/ui-locales/de.json",{"strings":{"Choose":"Wählen","Street":"Straße"},"audit_notes":"𓀆"})
    write("content/museum-locales/it.json",{"entries":{"fixture":{"body":["Đ"]}},"source_snapshot":"𓀇"})
    points,records,hashes=collect(root)
    assert all(ord(c) in points for c in "任天堂éதமிழ்作者Ωحرب音楽𝒬テストäßĐ")
    assert not any(cp in points for cp in range(0x13000,0x13008))
    assert len(hashes)==4 and all(len(value)==64 for value in hashes.values())
    assert script_class(ord("த"))=="complex_script_requires_shaping"
    assert script_class(ord("ح"))=="bidi_or_shaping_requires_review"
    assert script_class(ord("任"))=="ordinary_glyph"
    assert any(row["entry_id"]=="fixture" and row["field"]=="images[0].title" for row in records)
print("PASS Unicode inventory: complete native text/credits/music/features/locales, excluded hidden research, source hashes and honest complex-script classes")
