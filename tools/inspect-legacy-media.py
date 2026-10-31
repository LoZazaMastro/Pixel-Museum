"""Build inspection sheets from exact immutable public Playhub Git blobs.

Original bytes remain unchanged. Small contact-sheet copies are research aids,
never runtime selections or replacements for the original photographs.
"""
from pathlib import Path
import hashlib
import io
import json
import subprocess
import textwrap
from urllib.parse import urlsplit
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'build/research/legacy-playhub-media-audit'
SOURCE = Path('F:/Playhub/Plugin/Playhub')
inventory = json.loads((OUTPUT / 'inventory.json').read_text(encoding='utf-8'))
(OUTPUT / 'originals').mkdir(exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
rows = []
sheet = None
for index, row in enumerate(inventory['entries']):
    parts = urlsplit(row['image']['url']).path.strip('/').split('/')
    assert parts[:2] == ['LoZazaMastro', 'Playhub']
    commit, relative = parts[2], '/'.join(parts[3:])
    # Fresh ls-remote and local origin/main agree on this public revision.
    # Record it explicitly for the 55 inherited mutable-main URLs.
    if commit == 'main':
        commit = '3263731da5bdac468d828ea49270ac50240784d0'
    assert len(commit) == 40 and relative.startswith('assets/on-this-day/v1/')
    raw = subprocess.check_output(['git', '-C', str(SOURCE), 'show', commit + ':' + relative])
    original = OUTPUT / 'originals' / f'{index:04d}.jpg'
    original.write_bytes(raw)
    record = {'index': index, 'url': row['image']['url'], 'git_commit': commit,
              'git_path': relative, 'sha256': hashlib.sha256(raw).hexdigest(),
              'owners': row['owners'], 'declared': row['image'], 'visual_review': 'pending'}
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
        record['decoded_width'], record['decoded_height'] = image.size
        thumbnail = image.convert('RGB')
        thumbnail.thumbnail((308, 172), Image.Resampling.LANCZOS)
    except Exception as error:
        record['decode_error'] = str(error)
        thumbnail = Image.new('RGB', (308, 172), '#8b2525')
    rows.append(record)
    if index % 30 == 0:
        sheet = Image.new('RGB', (1920, 1200), '#e9e7e1')
    x, y = index % 6 * 320, index % 30 // 6 * 240
    sheet.paste(thumbnail, (x + (320 - thumbnail.width) // 2, y + 4 + (172 - thumbnail.height) // 2))
    draw = ImageDraw.Draw(sheet)
    titles = list(dict.fromkeys(owner['title'] for owner in row['owners']))
    label = f'{index:04d} ' + ' / '.join(titles)
    for line, text in enumerate(textwrap.wrap(label, 34)[:3]):
        draw.text((x + 6, y + 179 + line * 18), text, font=font, fill='#171d19')
    if index % 30 == 29 or index == len(inventory['entries']) - 1:
        path = OUTPUT / f'sheet-{index // 30:02d}.jpg'
        sheet.save(path, quality=94)
        print(path.name, flush=True)
(OUTPUT / 'decoded-inventory.json').write_text(json.dumps({'entries': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Exact Git blobs decoded:', len(rows), flush=True)
