"""Recreate the approved local web captures from their recorded actual renders."""
from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parents[1]
evidence=json.loads((ROOT/'build/research/website-theme-captures-private/evidence.json').read_text(encoding='utf8'))
for row in evidence['captures']:
    with Image.open(row['source']) as image:
        image=image.convert('RGB');image.thumbnail((2400,1350),Image.Resampling.LANCZOS)
        image.save(ROOT/'website/assets'/f"{row['name']}.webp",'WEBP',quality=88,method=6)
print('Four approved English light/dark captures prepared. No app content changed.')
