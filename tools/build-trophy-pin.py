"""Build an enamel-pin GLB from approved frontal artwork and its silhouette.

The outline is a simple closed polygon in the artwork's 0..100 coordinate space.
It describes the metal backing, never disconnected illustration strokes. One
explicit natural aperture may be supplied as a `holes` polygon (for a real ring).
Only Python's standard library is required; artwork remains embedded in the GLB.
"""
import argparse
import json
import math
import struct
import zlib
from functools import lru_cache
from pathlib import Path


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


@lru_cache(maxsize=2)
def reverse_normal_png(size=512):
    """Small deterministic stamped grid, stored as normals, never baked light."""
    rows=bytearray()
    for y in range(size):
        rows.append(0)
        v=(y+.5)/size*64*math.pi
        for x in range(size):
            u=(x+.5)/size*64*math.pi
            # Rounded pressed squares with shallow crossing grooves.
            dx=4*math.sin(u)**3*math.cos(u)*math.sin(v)**4
            dy=4*math.sin(v)**3*math.cos(v)*math.sin(u)**4
            normal=(-dx*.16,-dy*.16,1)
            length=math.sqrt(sum(n*n for n in normal))
            rows.extend(round((n/length*.5+.5)*255) for n in normal)
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,9))+chunk(b'IEND',b'')


def refine_outline(points, mode='smooth'):
    """Round shallow tracing chords, while retaining genuine sharp corners.

    Pixel artwork must explicitly select pixel mode. Smooth mode preserves
    substantial corners. Uniform arc-length filtering deburrs tracing noise;
    it does not retain the 256px tracer's horizontal/vertical microsteps.
    """
    if mode == 'pixel':
        return points
    # A near-circular/elliptical badge is a manufactured curve, not the alpha
    # grid's tiny horizontal/vertical steps. Fit only when every vertex agrees
    # with the same ellipse within 2%; irregular silhouettes never take this path.
    lo = [min(p[j] for p in points) for j in (0,1)]
    hi = [max(p[j] for p in points) for j in (0,1)]
    center = [(a+b)/2 for a,b in zip(lo,hi)]
    radii = [(b-a)/2 for a,b in zip(lo,hi)]
    if min(radii)>0 and max(abs(math.hypot((p[0]-center[0])/radii[0],
            (p[1]-center[1])/radii[1])-1) for p in points)<.02:
        return [(center[0]+radii[0]*math.cos(i*2*math.pi/384),
                 center[1]+radii[1]*math.sin(i*2*math.pi/384)) for i in range(384)]
    lengths=[math.dist(a,b) for a,b in zip(points,points[1:]+points[:1])]
    cumulative=[0.]
    for length in lengths:cumulative.append(cumulative[-1]+length)
    perimeter=cumulative[-1]
    def at(distance):
        distance%=perimeter
        for i,end in enumerate(cumulative[1:]):
            if distance<=end:
                t=(distance-cumulative[i])/lengths[i]
                a,b=points[i],points[(i+1)%len(points)]
                return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
        return points[0]
    count=max(96,min(768,math.ceil(perimeter/.006)))
    step=perimeter/count
    sampled=[at(i*step)for i in range(count)]
    weights=[math.exp(-i*i/(2*1.35**2))for i in range(-4,5)]
    smooth=[tuple(sum(sampled[(n+i)%count][j]*w for i,w in zip(range(-4,5),weights))/sum(weights)for j in (0,1))for n in range(count)]
    # Detect macroscopic corners from 0.04-unit chords, not adjacent pixel edges.
    for i,p in enumerate(points):
        a,b=at(cumulative[i]-.04),at(cumulative[i]+.04)
        u,v=(p[0]-a[0],p[1]-a[1]),(b[0]-p[0],b[1]-p[1])
        denominator=math.hypot(*u)*math.hypot(*v)
        angle=math.acos(max(-1,min(1,(u[0]*v[0]+u[1]*v[1])/denominator)))if denominator else 0
        if angle>math.pi*.42:
            index=round(cumulative[i]/step)%count
            smooth[index]=p
    def simplify(line):
        if len(line)<3:return line
        a,b=line[0],line[-1];dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
        def distance(p):
            t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))if den else 0
            return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
        far=max(range(1,len(line)-1),key=lambda n:distance(line[n]))
        if distance(line[far])<.00065:return [a,b]
        return simplify(line[:far+1])[:-1]+simplify(line[far:])
    opposite=max(range(count),key=lambda n:math.dist(smooth[n],smooth[0]))
    return simplify(smooth[:opposite+1])[:-1]+simplify(smooth[opposite:]+[smooth[0]])[:-1]


def offset_outline(points, distance):
    """Constant-distance miter offset; unlike radial scaling, respects concavities."""
    out = []
    for i, p in enumerate(points):
        a, b = points[i-1], points[(i+1) % len(points)]
        u, v = (p[0]-a[0], p[1]-a[1]), (b[0]-p[0], b[1]-p[1])
        lu, lv = math.hypot(*u), math.hypot(*v)
        nu, nv = (u[1]/lu, -u[0]/lu), (v[1]/lv, -v[0]/lv)
        denominator = max(.25, 1+nu[0]*nv[0]+nu[1]*nv[1])
        out.append((p[0]+distance*(nu[0]+nv[0])/denominator,
                    p[1]+distance*(nu[1]+nv[1])/denominator))
    return out


def triangulate(points):
    indices = list(range(len(points)))
    area = sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(points, points[1:]+points[:1]))
    if area < 0:
        indices.reverse()
    triangles = []
    while len(indices) > 3:
        for i, b in enumerate(indices):
            a, c = indices[i-1], indices[(i+1) % len(indices)]
            if cross(points[a], points[b], points[c]) <= 1e-10:
                continue
            if any(all(v >= -1e-10 for v in (
                    cross(points[a], points[b], points[p]),
                    cross(points[b], points[c], points[p]),
                    cross(points[c], points[a], points[p])))
                   for p in indices if p not in (a, b, c)):
                continue
            triangles.append((a, b, c))
            del indices[i]
            break
        else:
            raise ValueError('Outline must be simple, without holes or repeated edges')
    triangles.append(tuple(indices))
    return triangles


class Model:
    def __init__(self):
        self.data = bytearray()
        self.aspect = (1, 1)
        self.doc = {'asset': {'version': '2.0', 'generator': 'Pixel Museum solid enamel pin'},
                    'buffers': [{}], 'bufferViews': [], 'accessors': [],
                    'materials': [], 'meshes': [], 'nodes': [], 'scenes': [{'nodes': []}], 'scene': 0}

    def view(self, data):
        while len(self.data) % 4:
            self.data.append(0)
        offset = len(self.data)
        self.data.extend(data)
        self.doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(data)})
        return len(self.doc['bufferViews'])-1

    def accessor(self, rows, kind):
        width = {'VEC2': 2, 'VEC3': 3}[kind]
        view = self.view(struct.pack('<'+'f'*len(rows)*width, *(n for row in rows for n in row)))
        self.doc['accessors'].append({'bufferView': view, 'componentType': 5126,
                                     'count': len(rows), 'type': kind,
                                     'min': [min(p[i] for p in rows) for i in range(width)],
                                     'max': [max(p[i] for p in rows) for i in range(width)]})
        return len(self.doc['accessors'])-1

    def mesh(self, name, triangles, material, uv=False, smooth=False):
        positions, normals, coords = [], [], []
        for tri in triangles:
            a, b, c = tri
            u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
            n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
            length = math.sqrt(sum(x*x for x in n))
            if length < 1e-12:
                continue
            for p in tri:
                positions.append(p)
                normals.append([x/length for x in n])
                coords.append([(p[0]/self.aspect[0]+1)/2, (1-p[1]/self.aspect[1])/2])
        if smooth:
            # Weld shading only, never positions/topology. Shared vertex normals
            # eliminate the diagonal seams and hard facets of triangle soup.
            sums = {}
            for index, (p, n) in enumerate(zip(positions, normals)):
                base = index-index%3
                a,b = positions[base+(index%3+1)%3],positions[base+(index%3+2)%3]
                u,v = [a[j]-p[j] for j in range(3)],[b[j]-p[j] for j in range(3)]
                denominator = math.sqrt(sum(x*x for x in u)*sum(x*x for x in v))
                weight = math.acos(max(-1,min(1,sum(u[j]*v[j] for j in range(3))/denominator)))
                key = tuple(round(x, 9) for x in p)
                total = sums.setdefault(key, [0., 0., 0.])
                for j in range(3): total[j] += n[j]*weight
            normals = []
            for p in positions:
                n = sums[tuple(round(x, 9) for x in p)]
                length = math.sqrt(sum(x*x for x in n))
                normals.append([x/length for x in n] if length else [0,0,1])
        attributes = {'POSITION': self.accessor(positions, 'VEC3'),
                      'NORMAL': self.accessor(normals, 'VEC3')}
        if uv:
            attributes['TEXCOORD_0'] = self.accessor(coords, 'VEC2')
        self.doc['meshes'].append({'name': name, 'primitives': [{'attributes': attributes,
                                                              'material': material, 'mode': 4}]})
        self.doc['nodes'].append({'name': name, 'mesh': len(self.doc['meshes'])-1})
        self.doc['scenes'][0]['nodes'].append(len(self.doc['nodes'])-1)

    def save(self, path):
        while len(self.data) % 4:
            self.data.append(0)
        self.doc['buffers'][0]['byteLength'] = len(self.data)
        raw = json.dumps(self.doc, separators=(',', ':')).encode()
        raw += b' '*(-len(raw) % 4)
        payload = struct.pack('<II', len(raw), 0x4E4F534A)+raw
        payload += struct.pack('<II', len(self.data), 0x004E4942)+self.data
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(struct.pack('<III', 0x46546C67, 2, len(payload)+12)+payload)


def surface(fn, nu=48, nv=16, reverse=False):
    triangles = []
    for i in range(nu):
        for j in range(nv):
            p = [fn(u/nu*2*math.pi, v/nv*2*math.pi)
                 for u, v in ((i, j), (i+1, j), (i+1, j+1), (i, j+1))]
            triangles.extend(((p[0], p[2], p[1]), (p[0], p[3], p[2])) if reverse else
                             ((p[0], p[1], p[2]), (p[0], p[2], p[3])))
    return triangles


def folded_wing(side):
    """A closed thin stamped spring leaf, rather than an inflated oval."""
    triangles = []
    nu, nv = 12, 20
    def point(u, v, lower):
        y = (v-.5)*.235
        width = .105*math.sqrt(max(0, 1-(y/.122)**2))
        x = side*(.008+u*width)
        z = -.264-.058*math.sin(u*math.pi*.86)-.012*math.cos(y/.122*math.pi/2)
        return (x, y, z+(.009 if lower else 0))
    for lower in (False, True):
        for i in range(nu):
            for j in range(nv):
                a, b, c, d = [point(u/nu, v/nv, lower)
                              for u, v in ((i,j),(i+1,j),(i+1,j+1),(i,j+1))]
                faces = ((a,b,c),(a,c,d))
                triangles.extend(tuple(reversed(t)) for t in faces) if lower == (side>0) else triangles.extend(faces)
    perimeter = [(i/nu,0) for i in range(nu+1)]+[(1,j/nv) for j in range(1,nv+1)]
    perimeter += [(i/nu,1) for i in range(nu-1,-1,-1)]+[(0,j/nv) for j in range(nv-1,0,-1)]
    for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):
        p,q,r,s = point(*a,False),point(*b,False),point(*b,True),point(*a,True)
        faces=((p,q,r),(p,r,s))
        triangles.extend(tuple(reversed(t)) for t in faces) if side>0 else triangles.extend(faces)
    return triangles


def rounded_gold_path(path, aspect):
    """Closed swept micro-ridge with a rounded top, batched with other gold."""
    if not 2<=len(path['points'])<=2048 or any(len(p)!=2 or any(not math.isfinite(v)or not 0<=v<=100 for v in p)for p in path['points']):
        raise ValueError('Gold path requires 2..2048 finite artwork points')
    points=[((x/50-1)*aspect[0],(1-y/50)*aspect[1])for x,y in path['points']]
    closed=bool(path.get('closed',False))
    if points[0]==points[-1]:points.pop();closed=True
    if len(points)<2:return []
    width=float(path.get('width',.35))/50*min(aspect)
    height=float(path.get('height',.006))
    if not .005<=height<=.008 or not 0<width<=.04:raise ValueError('Gold path height/width outside micro-relief limits')
    profile=[(-math.cos(i*math.pi/8)*width/2,.045+height*math.sin(i*math.pi/8))for i in range(9)]
    profile += [(width/2,.0447),(-width/2,.0447)]
    loops=[]
    for i,p in enumerate(points):
        a=points[i-1]if i or closed else p;b=points[(i+1)%len(points)]if i+1<len(points)or closed else p
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<1e-8:return []
        loops.append([(p[0]+dy/length*s,p[1]-dx/length*s,z)for s,z in profile])
    triangles=[]
    for i in range(len(loops)if closed else len(loops)-1):
        a,b=loops[i],loops[(i+1)%len(loops)]
        for j in range(len(profile)):
            k=(j+1)%len(profile)
            triangles.extend(((a[j],a[k],b[k]),(a[j],b[k],b[j])))
    if not closed:
        for f in triangulate(profile):
            triangles.append(tuple(loops[0][k]for k in f))
            triangles.append(tuple(loops[-1][k]for k in reversed(f)))
    return triangles


def annular_caps(outer, inner):
    """Triangulate a natural aperture using a zero-width visibility bridge."""
    # Select a nonintersecting bridge between actual boundary vertices. The
    # doubled bridge has zero area and is welded by the renderer/topology audit.
    def intersects(a,b,c,d):
        return cross(a,b,c)*cross(a,b,d)<-1e-14 and cross(c,d,a)*cross(c,d,b)<-1e-14
    options=[]
    for oi,a in enumerate(outer):
        for hi,b in enumerate(inner):
            if any(intersects(a,b,c,d)for loop in (outer,inner)for c,d in zip(loop,loop[1:]+loop[:1])):continue
            options.append((math.dist(a,b),oi,hi))
    if not options:raise ValueError('No visible bridge for natural aperture')
    _,oi,hi=min(options)
    clockwise=list(reversed(inner));hi=clockwise.index(inner[hi])
    joined=outer[:oi+1]+clockwise[hi:]+clockwise[:hi+1]+[outer[oi]]+outer[oi+1:]
    indices=list(range(len(joined)));faces=[]
    while len(indices)>3:
        for n in range(len(indices)):
            a,b,c=indices[n-1],indices[n],indices[(n+1)%len(indices)]
            if cross(joined[a],joined[b],joined[c])<=1e-12:continue
            if any(all(v>=-1e-12 for v in (cross(joined[a],joined[b],joined[p]),cross(joined[b],joined[c],joined[p]),cross(joined[c],joined[a],joined[p])))for p in indices if joined[p]not in (joined[a],joined[b],joined[c])):continue
            faces.append((a,b,c));del indices[n];break
        else:raise ValueError('Cannot triangulate aperture without crossing its boundary')
    faces.append(tuple(indices))
    return outer,inner,joined,faces


def build(front, outline, output, contour_mode='smooth', relief=None, clasp_anchor='auto', stones=None):
    png = front.read_bytes()
    if not png.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Frontal artwork must be PNG')
    width, height = struct.unpack('>II', png[16:24])
    aspect = (width/max(width, height), height/max(width, height))
    points = json.loads(outline.read_text(encoding='utf-8'))
    holes=[]
    if isinstance(points, dict):
        holes=points.get('holes',[])
        contour_mode = points.get('contour_mode', contour_mode)
        clasp_anchor = points.get('clasp_anchor', clasp_anchor)
        points = points['outline']
    if contour_mode not in ('smooth','pixel') or clasp_anchor not in ('auto','center'):
        raise ValueError('Unknown contour or clasp anchor mode')
    if points[0] == points[-1]:
        points = points[:-1]
    if not 3 <= len(points) <= 512 or any(len(p) != 2 or any(
            not math.isfinite(float(v)) or not 0 <= v <= 100 for v in p) for p in points):
        raise ValueError('Outline requires 3..512 finite 0..100 vertices')
    points = [((x/50-1)*aspect[0], (1-y/50)*aspect[1]) for x, y in points]
    if sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(points, points[1:]+points[:1])) < 0:
        points.reverse()
    original_vertices = len(points)
    points = refine_outline(points, contour_mode)
    hole=None
    if holes:
        if len(holes)!=1:raise ValueError('Only one explicit natural aperture is supported')
        raw=holes[0]
        if raw[0]==raw[-1]:raw=raw[:-1]
        if not 3<=len(raw)<=512 or any(len(p)!=2 or any(not math.isfinite(v) or not 0<=v<=100 for v in p)for p in raw):
            raise ValueError('Invalid natural aperture')
        hole=[((x/50-1)*aspect[0],(1-y/50)*aspect[1])for x,y in raw]
        if sum(a[0]*b[1]-b[0]*a[1]for a,b in zip(hole,hole[1:]+hole[:1]))<0:hole.reverse()
        hole=refine_outline(hole,contour_mode)
        points,hole,cap_points,faces=annular_caps(points,hole)
    else:cap_points=points;faces=triangulate(points)
    # Find the widest interior patch. A clutch at the origin can protrude through
    # the notch of a hand, sword or letter-shaped pin when viewed from the front.
    def clearance(x, y):
        inside=False
        for a,b in zip(points,points[1:]+points[:1]):
            if (a[1]>y)!=(b[1]>y)and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        if not inside:return -1
        if hole:
            in_hole=False
            for a,b in zip(hole,hole[1:]+hole[:1]):
                if (a[1]>y)!=(b[1]>y)and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:in_hole=not in_hole
            if in_hole:return -1
        distances = []
        for a, b in list(zip(points, points[1:]+points[:1]))+(list(zip(hole,hole[1:]+hole[:1]))if hole else []):
            dx, dy = b[0]-a[0], b[1]-a[1]
            t = max(0, min(1, ((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
            distances.append(math.hypot(x-a[0]-t*dx, y-a[1]-t*dy))
        return min(distances)
    low=[min(p[j]for p in points)for j in(0,1)];high=[max(p[j]for p in points)for j in(0,1)]
    if clasp_anchor == 'center':
        anchor = tuple((a+b)/2 for a,b in zip(low,high))
    else:
        step=[(b-a)/40 for a,b in zip(low,high)]
        anchor=max(((low[0]+x*step[0],low[1]+y*step[1])for x in range(41)for y in range(41)),key=lambda p:clearance(*p))
        anchor=max(((anchor[0]+x*step[0]/6,anchor[1]+y*step[1]/6)for x in range(-3,4)for y in range(-3,4)),key=lambda p:clearance(*p))
    clasp_scale = 1 if clasp_anchor=='center' else min(1, clearance(*anchor)/.19)
    if clasp_scale < .2:
        raise ValueError('Pin silhouette has no practical area for a clasp')
    def rear(fn):
        def transformed(u, v):
            x, y, z = fn(u, v)
            return (anchor[0]+x*clasp_scale, anchor[1]+y*clasp_scale, z)
        return transformed
    model = Model()
    model.aspect = aspect
    texture = model.view(png)
    reverse_normal=model.view(reverse_normal_png())
    model.doc.update({'images': [{'bufferView': texture, 'mimeType': 'image/png'}],
                      'samplers': [{'magFilter': 9729, 'minFilter': 9987,
                                    'wrapS': 33071, 'wrapT': 33071}],
                      'textures': [{'sampler': 0, 'source': 0}]})
    model.doc['images'].append({'bufferView':reverse_normal,'mimeType':'image/png'})
    model.doc['textures'].append({'sampler':0,'source':1})
    model.doc['materials'] = [
        {'name': 'Polished gold', 'pbrMetallicRoughness': {
            'baseColorFactor': [1, .69, .23, 1], 'metallicFactor': 1, 'roughnessFactor': .23}},
        {'name': 'Coloured enamel', 'pbrMetallicRoughness': {
            'baseColorTexture': {'index': 0}, 'metallicFactor': 0, 'roughnessFactor': .28}},
        {'name': 'Satin gold reverse', 'normalTexture':{'index':1,'scale':.55}, 'pbrMetallicRoughness': {
            'baseColorFactor': [.86, .59, .2, 1], 'metallicFactor': 1, 'roughnessFactor': .45}}]
    # Caps share the exact outer and optional aperture boundaries with the walls.
    cap = lambda p, z: (p[0], p[1], z)
    model.mesh('Solid enamel face', [tuple(cap(cap_points[i], .045) for i in f) for f in faces], 1, True)
    model.mesh('Solid gold reverse', [tuple(cap(cap_points[i], -.045) for i in reversed(f)) for f in faces], 2, True)
    edge = []
    rings = [(0, -.045), (.002, -.044), (.0035, -.041),
             (.004, -.037), (.004, .037), (.0035, .041), (.002, .044), (0, .045)]
    loops = [(offset_outline(points, offset), z) for offset,z in rings]
    for i in range(len(points)):
        j = (i+1) % len(points)
        for (lower,z),(upper,w) in zip(loops,loops[1:]):
            a,b,c,d = lower[i],lower[j],upper[j],upper[i]
            p,q,r,v = (*a,z),(*b,z),(*c,w),(*d,w)
            edge.extend(((p, q, r), (p, r, v)))
    model.mesh('Soft rounded gold edge', edge, 0, smooth=contour_mode!='pixel')
    if hole:
        model.doc['materials'].append({'name':'Polished silver aperture wall','pbrMetallicRoughness':{'baseColorFactor':[.74,.77,.79,1],'metallicFactor':1,'roughnessFactor':.22}})
        wall=[]
        loops=[(offset_outline(hole,-offset),z)for offset,z in rings]
        for i in range(len(hole)):
            j=(i+1)%len(hole)
            for (lower,z),(upper,w)in zip(loops,loops[1:]):
                a,b,c,d=lower[i],lower[j],upper[j],upper[i]
                wall.extend(((( *a,z),(*c,w),(*b,z)),((*a,z),(*d,w),(*c,w))))
        model.mesh('Natural aperture silver inner wall',wall,len(model.doc['materials'])-1,smooth=True)
    relief_count = 0
    all_relief=[]
    if relief:
        spec = json.loads(relief.read_text(encoding='utf-8'))
        for path in spec.get('paths',[]):
            all_relief.extend(rounded_gold_path(path,aspect));relief_count+=1
        for region in spec.get('regions', []):
            # Explicit designer-authored gold regions only; no colour guessing.
            if not 3<=len(region['outline'])<=512 or any(len(p)!=2 or any(
                    not math.isfinite(v) or not 0<=v<=100 for v in p) for p in region['outline']):
                raise ValueError('Gold regions require 3..512 finite artwork coordinates')
            poly = [((x/50-1)*aspect[0], (1-y/50)*aspect[1]) for x,y in region['outline']]
            if poly[0] == poly[-1]: poly.pop()
            if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))<0: poly.reverse()
            poly = refine_outline(poly, region.get('contour_mode', 'smooth'))
            height = float(region.get('height', .010))
            if not .005 <= height <= .012: raise ValueError('Gold relief height must be .005..012 model units')
            inner = offset_outline(poly, -.0015)
            top = .045+height
            geometry = [tuple((*poly[k], .0449) for k in reversed(f)) for f in triangulate(poly)]
            geometry += [tuple((*inner[k], top) for k in f) for f in triangulate(inner)]
            layers = [(poly,.0449),(poly,top-.002),(offset_outline(poly,-.0005),top-.0005),(inner,top)]
            for (lo,z),(hi,w) in zip(layers,layers[1:]):
                for i in range(len(poly)):
                    j=(i+1)%len(poly);a,b,c,d=(*lo[i],z),(*lo[j],z),(*hi[j],w),(*hi[i],w)
                    geometry.extend(((a,b,c),(a,c,d)))
            all_relief.extend(geometry)
            relief_count += 1
        if all_relief:model.mesh('Soft gold inlays',all_relief,0,smooth=True)
    stone_count = 0
    if stones:
        model.doc['extensionsUsed']=['KHR_materials_specular']
        model.doc['materials'].append({'name':'Cut clear crystal','extensions':{
            'KHR_materials_specular':{'specularFactor':1,'specularColorFactor':[4.2,4.2,4.2]}},
            'pbrMetallicRoughness':{'baseColorFactor':[.14,.17,.20,1], 'metallicFactor':0,'roughnessFactor':.07}})
        cut=[];settings=[]
        for stone in json.loads(stones.read_text(encoding='utf-8')).get('stones',[]):
            x,y,r = (float(stone[k]) for k in ('x','y','radius'))
            if not all(math.isfinite(v) for v in (x,y,r)) or not(0<=x<=100 and 0<=y<=100 and .1<=r<=4):
                raise ValueError('Stone sites require finite x/y0..100 and radius .1..4')
            cx,cy=(x/50-1)*aspect[0],(1-y/50)*aspect[1];radius=r/50*min(aspect)
            if clearance(cx,cy)<radius:raise ValueError('Stone must remain inside solid backing')
            # Low crown and embedded pavilion: a genuine faceted stone, not a
            # printed sparkle or a tall jewel perched above the enamel.
            bottom=(cx,cy,.039);table=[];girdle=[]
            for i in range(8):
                angle=i*math.pi/4
                table.append((cx+radius*.46*math.cos(angle),cy+radius*.46*math.sin(angle),.053))
                girdle.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle),.046))
            for i in range(8):
                j=(i+1)%8
                cut.extend((((cx,cy,.053),table[i],table[j]),
                            (table[i],girdle[i],girdle[j]),(table[i],girdle[j],table[j]),
                            (bottom,girdle[j],girdle[i])))
            settings.extend(surface(lambda u,v:(cx+(radius*1.04+.0014*math.cos(v))*math.cos(u),
                           cy+(radius*1.04+.0014*math.cos(v))*math.sin(u),.046+.0014*math.sin(v)),nu=8,nv=4))
            stone_count+=1
        if cut:model.mesh('Inlaid faceted crystals',cut,3)
        if settings:model.mesh('Fine gold crystal settings',settings,0,smooth=True)
    # Physical central post and butterfly clutch, all closed three-dimensional surfaces.
    model.mesh('Pin post', surface(rear(lambda u, v: (
        .024*math.cos(u)*math.sin(v/2), .024*math.sin(u)*math.sin(v/2),
        -.16+.145*math.cos(v/2))), reverse=True), 0, smooth=True)
    model.mesh('Butterfly clutch rim', surface(rear(lambda u, v: (
        (.145+.024*math.cos(v))*math.cos(u),
        (.145+.024*math.cos(v))*math.sin(u), -.255+.024*math.sin(v)))), 0, smooth=True)
    for side in (-1, 1):
        wings = [tuple((anchor[0]+x*clasp_scale,anchor[1]+y*clasp_scale,z)
                       for x,y,z in tri) for tri in folded_wing(side)]
        model.mesh('Stamped butterfly spring leaf '+str(side), wings, 0, smooth=True)
    model.save(output)
    return {'output': str(output), 'bytes': output.stat().st_size,
            'outline_vertices': len(points), 'input_vertices': original_vertices, 'contour_mode':contour_mode,
            'gold_relief_regions':relief_count, 'inlaid_stones':stone_count,
            'clasp_anchor_mode':clasp_anchor,'clasp_anchor':anchor,'solid_front_triangles': len(faces),
            'meshes': len(model.doc['meshes']), 'embedded_png': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('front', 'outline', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--contour-mode', choices=('smooth','pixel'), default='smooth')
    parser.add_argument('--relief', type=Path, help='Explicit gold regions JSON; same 0..100 artwork coordinates')
    parser.add_argument('--clasp-anchor', choices=('auto','center'), default='auto')
    parser.add_argument('--stones',type=Path,help='Explicit inlaid crystal sites JSON in artwork coordinates')
    args = parser.parse_args()
    print(json.dumps(build(args.front, args.outline, args.output, args.contour_mode, args.relief, args.clasp_anchor, args.stones)))
