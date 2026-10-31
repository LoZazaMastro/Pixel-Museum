"""Remove only exact generic display labels; no prose rewriting."""
GENERIC = frozenset({"From the reference collection"})
def apply(entries):
    changed = []
    subtitles = headings = 0
    for entry in entries:
        hit = False
        if entry.get("subtitle") in GENERIC:
            entry["subtitle"] = ""
            subtitles += 1
            hit = True
        for owner in [entry] + entry.get("editorial_features", []):
            values = owner.get("story_headings", [])
            for i, value in enumerate(values):
                if value in GENERIC:
                    values[i] = ""
                    headings += 1
                    hit = True
        if hit:
            changed.append(entry["id"])
    return {"status": "PASS", "changed_entries": changed, "subtitle_count": subtitles, "heading_count": headings}
