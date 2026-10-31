"""Render the museum's own geometric identity for the PS5 launcher."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
paper, ink = '#f1efe7', '#202521'
grid = ('10001', '11011', '10101', '10001', '10001')
def mark(draw, x, y, cell, color=ink, accents=None):
    for row, line in enumerate(grid):
        for col, bit in enumerate(line):
            if bit == '1':
                fill = (accents or {}).get((row, col), color)
                draw.rectangle((x+col*cell, y+row*cell, x+(col+1)*cell-1, y+(row+1)*cell-1), fill=fill)

im = Image.new('RGB', (512, 512), ink)
mark(ImageDraw.Draw(im), 136, 136, 48, color=paper)
(root/'sce_sys').mkdir(exist_ok=True)
im.save(root/'sce_sys/icon0.png')
wide = Image.new('RGB', (1920, 1080), paper)
draw = ImageDraw.Draw(wide)
mark(draw, 1200, 300, 96, accents={
    (0, 0): '#7fa48e',
    (1, 3): '#dda83d',
    (2, 2): '#9f96bc',
})
wide.save(root/'assets/brand/launcher.png')
