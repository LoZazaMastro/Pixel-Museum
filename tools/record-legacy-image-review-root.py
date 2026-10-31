"""Record the root editor's visual inspection of eight exact-blob sheets.

This is a subject/edition screen, not a licence or publication signoff. The
contact sheets and originals were opened before these decisions were written.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'build/research/legacy-playhub-media-audit/decoded-inventory.json'
records = json.loads(source.read_text(encoding='utf-8'))['entries']
bad = {
    3: 'Astronomical nebula photograph, not a portrait of Will Wright; original Commons filename and astronomical credit confirm the mismatch.',
    34: 'Surveying instrument, not Zelda artwork or gameplay.',
    35: 'Photograph of a real bridge, not Zelda artwork or gameplay.',
    36: 'D-Link computer network adapter, not Zelda artwork or gameplay.',
    41: 'Different Final Fantasy entry with Cecil/Rydia-era party, not the original Final Fantasy discussed by this record.',
    42: 'Different Final Fantasy world map, not original Final Fantasy; inherited app URL does not authenticate these bytes.',
    43: '3D Final Fantasy party scene with later named characters, not the original Final Fantasy.',
    44: '3D Final Fantasy party scene, not the original Final Fantasy.',
    45: 'Different Final Fantasy dialogue scene, not the original Final Fantasy.',
    46: 'Later Final Fantasy scene; incompatible with the original game identification and inherited app metadata.',
    61: 'Mortal Kombat 2011 box artwork presented for the 1992 game without a later-game comparison.',
    97: 'Super Smash Bros. for Wii U-era character rendering, not the 1999 Nintendo 64 game.',
    115: 'Icelandair passenger aircraft photograph, unrelated to Ico.',
    120: 'Card-based Chain of Memories battle interface, not the original Kingdom Hearts chapter.',
    137: 'PlayStation Vita product photograph, not PlayStation Portable.',
    154: 'Dead Space remake imagery; inherited Steam app1693980 identifies the 2023 remake, not the 2008 game.',
    172: 'Later Street Fighter visual presentation rather than Super Street Fighter IV; current caption and source identity do not justify this association.',
}
holds = {
    21: 'Software cassette packages for ZX Spectrum, incorrectly described as a console photograph. Needs an accurate artefact caption before admission.',
    49: 'Populous edition identity needs direct verification: Olympian-looking interface may be Populous II rather than the first game.',
    50: 'Same exact Populous edition uncertainty as index49; do not use its inherited title as proof.',
    65: 'Nintendo64 Controller Pak accessory, incorrectly captioned as the console. Valid related artefact only after precise caption/owner review.',
    145: 'Wii Mini revision photograph; record currently presents the original Wii launch without identifying this later hardware.',
    174: 'Undead Nightmare scene within Red Dead Redemption PC gallery. Needs expansion/edition-specific context instead of unqualified base-game illustration.',
    190: 'Marvel vs.Capcom3 promotional character artwork, not a gameplay screenshot; precise media-type caption required.',
    193: 'Dark Souls Remastered gallery shows Artorias expansion material. Needs explicit remaster/expansion caption rather than an original2011 capture implication.',
}
notes = {
    2: 'Group photograph, not an isolated Yu Suzuki portrait; preserve all photographer/participant identification.',
    8: 'Capcom Cup event photograph, not company premises or archival founding imagery.',
    30: 'NES product photograph. The composite daily owner explicitly includes NES; do not discard solely because its title also mentions other games.',
    37: 'Atlus office photograph. Subject match does not establish photographer/licence from a Wikipedia company page.',
    51: 'Physical Game Boy/Tetris photograph, not a 3D model or gameplay capture.',
    62: 'Myst gallery appears to show the same game in a later Masterpiece presentation; exact release representation remains a caption task.',
    63: 'Myst gallery appears to show the same game in a later Masterpiece presentation; not an original1993 date/format signoff.',
    66: 'Super Metroid package artwork, not gameplay.',
    74: 'PlayStation DualShock controller accessory photograph, not a console body.',
    77: 'Miyamoto with Mario costume: contextual creator/event photograph, not original1996 Super Mario64 gameplay.',
    96: 'Dreamcast controller/VMU accessories, not a full console-body photograph.',
    109: 'The Sims package artwork.',
    110: 'The Sims gameplay; visually same frame as111. Deduplication is a separate task.',
    111: 'The Sims gameplay; visually same frame as110.',
    121: 'Kingdom Hearts scene in a later high-resolution presentation; no original PS2 capture claim.',
    122: 'Kingdom Hearts scene in a later high-resolution presentation; no original PS2 capture claim.',
    123: 'Kingdom Hearts scene in a later high-resolution presentation; no original PS2 capture claim.',
    128: 'EVE Online Special Edition package, not its original2003 packaging.',
    129: 'Viewtiful Joe PlayStation2 package; do not call it original GameCube packaging.',
    146: 'Dwarf Fortress graphical presentation; does not demonstrate the original ASCII release.',
    192: 'Nintendo3DS photograph with adjacent hardware; image is a physical display, not gameplay.',
    221: 'Dark SoulsII spell-combat frame inspected at full resolution; matches its declared subject without claiming a licence signoff.',
    237: 'Alien:Isolation frame repeated at238; source match is not duplicate-content approval.',
    238: 'Alien:Isolation frame repeated at237.',
}
later = list(range(56,60)) + list(range(70,73)) + list(range(80,89)) + list(range(98,103)) + list(range(104,108)) + list(range(124,128)) + list(range(130,133)) + list(range(138,143)) + list(range(175,177)) + list(range(182,186)) + list(range(194,197))
for index in later:
    notes.setdefault(index, 'Recognisable same-game scene in a modern store gallery; this subject check does not certify original-release capture, platform or date.')
rows = []
for record in records[:240]:
    index = record['index']
    raw = ROOT / 'build/research/legacy-playhub-media-audit/originals' / f'{index:04d}.jpg'
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == record['sha256']
    decision = 'quarantine_unrelated' if index in bad else 'needs_exact_identity_review' if index in holds else 'approve_subject_match'
    note = bad.get(index, holds.get(index, notes.get(index, 'Visually inspected exact-blob thumbnail: recognisable declared game, person or related physical artefact. No independent rights/date approval is implied.')))
    rows.append({'index':index, 'url':record['url'], 'sha256':record['sha256'],
        'decision':decision, 'reason':note, 'owners':[
            {**owner, 'decision':decision, 'reason':note} for owner in record['owners']],
        'rights_signoff':False, 'editorial_signoff':False})
result = {'schema_version':1, 'reviewer':'root visual review',
    'scope':'Indices0–239; sheets00–07; exact original blobs inspected for selected ambiguous frames.',
    'source_inventory_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'review_kind':'Subject and edition identity screening only; full copyright, date, authenticity and original-resolution quality remain separate gates.',
    'entries':rows}
output = ROOT / 'content/editorial/legacy-image-visual-review-00-07.json'
output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
print(output, len(rows), {state:sum(row['decision']==state for row in rows) for state in ['approve_subject_match','quarantine_unrelated','needs_exact_identity_review']})
