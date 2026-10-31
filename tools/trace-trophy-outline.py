"""Extract a closed manufacturing outline from PNG alpha, without editing artwork."""
import argparse
import json
from pathlib import Path
from PIL import Image


def simplify(points, tolerance):
    if len(points) < 3:
        return points
    a, b = points[0], points[-1]
    dx, dy = b[0]-a[0], b[1]-a[1]
    denominator = dx*dx+dy*dy
    def distance(p):
        t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/denominator)) if denominator else 0
        return (p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2
    farthest = max(range(1, len(points)-1), key=lambda i: distance(points[i]))
    if distance(points[farthest]) <= tolerance*tolerance:
        return [a, b]
    return simplify(points[:farthest+1], tolerance)[:-1]+simplify(points[farthest:], tolerance)


def trace(source, destination):
    image = Image.open(source)
    if image.mode != 'RGBA':
        raise ValueError('Artwork must have a genuine alpha channel')
    size = 256
    alpha = image.getchannel('A').resize((size, size), Image.Resampling.LANCZOS)
    mask = {(x, y) for y in range(size) for x in range(size) if alpha.getpixel((x, y)) >= 128}
    if len(mask) < 100 or len(mask) == size*size:
        raise ValueError('Artwork must be isolated on a transparent exterior')
    edges = {}
    for x, y in mask:
        for neighbour, a, b in (
            ((x, y-1), (x, y), (x+1, y)),
            ((x+1, y), (x+1, y), (x+1, y+1)),
            ((x, y+1), (x+1, y+1), (x, y+1)),
            ((x-1, y), (x, y+1), (x, y))):
            if neighbour not in mask:
                edges.setdefault(a, []).append(b)
    loops = []
    while edges:
        start = next(iter(edges))
        path, point = [start], start
        while True:
            following = edges[point].pop()
            if not edges[point]:
                del edges[point]
            path.append(following)
            point = following
            if point == start:
                break
            if point not in edges:
                raise ValueError('Alpha boundary is not closed')
        area = sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(path, path[1:]))/2
        loops.append((area, path))
    area, boundary = max(loops, key=lambda v: v[0])
    holes = [a for a, _ in loops if a < -3]
    if holes:
        raise ValueError(f'Pin has {len(holes)} internal alpha holes; repair the artwork first')
    # Split the closed loop at its farthest point before RDP, retaining its shape.
    opposite = max(range(len(boundary)-1), key=lambda i: (
        boundary[i][0]-boundary[0][0])**2+(boundary[i][1]-boundary[0][1])**2)
    contour = simplify(boundary[:opposite+1], .65)[:-1]+simplify(boundary[opposite:], .65)[:-1]
    result = [[round(x/size*100, 5), round(y/size*100, 5)] for x, y in contour]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result)+'\n', encoding='utf-8')
    return {'source': str(source), 'outline': str(destination), 'vertices': len(result),
            'solid_outline': True, 'artwork_modified': False, 'main_area_pixels': area}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(trace(args.source, args.destination)))
