"""Tiny Bedrock-geometry toolkit: model builder, texture atlas packer and
software renderer (used to simulate how the entity looks in game).

Coordinates used when authoring are the same as in the exported .geo.json:
  +X = entity's LEFT, +Y = up, -Z = FRONT (the face looks toward -Z).
Rotations are the raw JSON values (degrees).  Internally everything is
converted to Blockbench/three.js space (x negated, rx/ry negated, ZYX order).
"""
import json
import math
import numpy as np
from PIL import Image

FACES = ('north', 'south', 'east', 'west', 'up', 'down')


# ----------------------------------------------------------------- math
def _rot_bb(rx, ry, rz):
    """three.js Euler 'ZYX' matrix (R = Rz @ Ry @ Rx), degrees."""
    x, y, z = (math.radians(a) for a in (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def xform(pivot, rot):
    """4x4 matrix in BB space for a JSON pivot/rotation pair."""
    M = np.eye(4)
    if rot is None or not any(rot):
        return M
    p = np.array([-pivot[0], pivot[1], pivot[2]], float)
    R = _rot_bb(-rot[0], -rot[1], rot[2])
    M[:3, :3] = R
    M[:3, 3] = p - R @ p
    return M


def face_corners(origin, size):
    """TL, TR, BL corners (BB space, unrotated) of every face of a JSON cube.
    TL/TR/BL correspond to uv, uv+(us,0), uv+(0,vs) of a Bedrock per-face uv."""
    ox, oy, oz = origin
    w, h, d = size
    fx, fy, fz = -(ox + w), oy, oz
    tx, ty, tz = -ox, oy + h, oz + d
    return {
        'north': ((tx, ty, fz), (fx, ty, fz), (tx, fy, fz)),
        'south': ((fx, ty, tz), (tx, ty, tz), (fx, fy, tz)),
        'east': ((tx, ty, tz), (tx, ty, fz), (tx, fy, tz)),
        'west': ((fx, ty, fz), (fx, ty, tz), (fx, fy, fz)),
        'up': ((tx, ty, tz), (fx, ty, tz), (tx, ty, fz)),
        'down': ((tx, fy, fz), (fx, fy, fz), (tx, fy, tz)),
    }


def face_dims(size):
    w, h, d = size
    return {'north': (w, h), 'south': (w, h), 'east': (d, h), 'west': (d, h), 'up': (w, d), 'down': (w, d)}


# ----------------------------------------------------------------- model
class Ctx:
    pass


class Cube:
    def __init__(self, origin, size, mat, rot=None, pivot=None, d=4, res=None, faces=None, seed=0, ds=None):
        self.origin = [float(v) for v in origin]
        self.size = [float(v) for v in size]
        self.mat = mat
        self.rot = list(rot) if rot else None
        self.pivot = list(pivot) if pivot is not None else [self.origin[i] + self.size[i] / 2 for i in range(3)]
        self.d = d
        self.ds = ds if ds is not None else d      # texel density of the non-front faces
        self.res = res or {}
        self.faces = faces
        self.seed = seed
        self.uv = {}


class Bone:
    def __init__(self, name, parent=None, pivot=(0, 0, 0), rot=None):
        self.name, self.parent, self.pivot, self.rot = name, parent, list(pivot), (list(rot) if rot else None)
        self.cubes = []

    def cube(self, origin, size, mat, **kw):
        c = Cube(origin, size, mat, **kw)
        self.cubes.append(c)
        return c

    def box(self, x0, y0, z0, x1, y1, z1, mat=None, **kw):
        """cube given by min/max corners"""
        return self.cube((x0, y0, z0), (x1 - x0, y1 - y0, z1 - z0), mat, **kw)


class Model:
    def __init__(self, identifier):
        self.identifier = identifier
        self.bones = []
        self.by_name = {}

    def bone(self, name, parent=None, pivot=(0, 0, 0), rot=None):
        b = Bone(name, parent, pivot, rot)
        self.bones.append(b)
        self.by_name[name] = b
        return b

    def bone_matrix(self, b):
        M = xform(b.pivot, b.rot)
        if b.parent:
            M = self.bone_matrix(self.by_name[b.parent]) @ M
        return M

    # ---- texture baking
    def bake(self, max_w=512, gutter=1):
        rects = []  # (w,h,img,cube,face)
        for b in self.bones:
            MB = self.bone_matrix(b)
            for c in b.cubes:
                dims = face_dims(c.size)
                corners = face_corners(c.origin, c.size)
                MC = xform(c.pivot, c.rot)
                for f in FACES:
                    if c.faces is not None and f not in c.faces:
                        continue
                    fw, fh = dims[f]
                    if fw <= 1e-6 or fh <= 1e-6:
                        continue
                    if f in c.res:
                        W, H = c.res[f]
                    else:
                        dd = c.d if f == 'north' else c.ds
                        W, H = max(1, int(round(fw * dd))), max(1, int(round(fh * dd)))
                    mat = c.mat[f] if isinstance(c.mat, dict) else c.mat
                    if mat is None:
                        continue
                    TL, TR, BL = (np.array(v, float) for v in corners[f])
                    u = (np.arange(W) + .5) / W
                    v = (np.arange(H) + .5) / H
                    U, V = np.meshgrid(u, v)
                    P = TL + U[..., None] * (TR - TL) + V[..., None] * (BL - TL)
                    Pl = P @ MC[:3, :3].T + MC[:3, 3]
                    Pm = Pl @ MB[:3, :3].T + MB[:3, 3]
                    n = np.cross(TR - TL, BL - TL)
                    n = n / np.linalg.norm(n)
                    # outward normal sign fix (TLTR x TLBL may point inward)
                    centre = np.array([-(c.origin[0] + c.size[0] / 2), c.origin[1] + c.size[1] / 2, c.origin[2] + c.size[2] / 2])
                    if np.dot(n, (TL + TR + BL) / 3 - centre) < 0:
                        n = -n
                    n = MC[:3, :3] @ n
                    ctx = Ctx()
                    ctx.face, ctx.w, ctx.h, ctx.fw, ctx.fh = f, W, H, fw, fh
                    ctx.u, ctx.v = U, V
                    ctx.P = Pl * np.array([-1, 1, 1])      # bone-local JSON coords
                    ctx.Pm = Pm * np.array([-1, 1, 1])     # model JSON coords (rest pose)
                    ctx.N = n * np.array([-1, 1, 1])
                    ctx.Nm = (MB[:3, :3] @ n) * np.array([-1, 1, 1])
                    ctx.cube, ctx.seed = c, c.seed
                    img = np.asarray(mat(ctx), float)
                    if img.shape[-1] == 3:
                        img = np.concatenate([img, np.ones(img.shape[:2] + (1,))], -1)
                    assert img.shape == (H, W, 4), (img.shape, (H, W, 4), f)
                    rects.append([W, H, np.clip(img, 0, 1), c, f])
        # shelf packing
        order = sorted(range(len(rects)), key=lambda i: (-rects[i][1], -rects[i][0]))
        for tw in (64, 128, 256, 512, 1024, 2048):
            if tw > max_w:
                break
            x = y = shelf = 0
            pos = {}
            ok = True
            for i in order:
                W, H = rects[i][0] + 2 * gutter, rects[i][1] + 2 * gutter
                if W > tw:
                    ok = False
                    break
                if x + W > tw:
                    x, y, shelf = 0, y + shelf, 0
                pos[i] = (x, y)
                x += W
                shelf = max(shelf, H)
            th = y + shelf
            if ok and th <= tw:
                break
        else:
            raise RuntimeError('atlas too large')
        th_pow = 64
        while th_pow < th:
            th_pow *= 2
        atlas = np.zeros((th_pow, tw, 4))
        for i, (x, y) in pos.items():
            W, H, img, c, f = rects[i]
            pad = np.pad(img, ((gutter, gutter), (gutter, gutter), (0, 0)), mode='edge')
            atlas[y:y + H + 2 * gutter, x:x + W + 2 * gutter] = pad
            c.uv[f] = {'uv': [x + gutter, y + gutter], 'uv_size': [W, H]}
        self.tex_w, self.tex_h = tw, th_pow
        self.atlas = Image.fromarray((atlas * 255 + .5).astype(np.uint8), 'RGBA')
        return self.atlas

    def to_json(self, bounds=(6, 5, 1.5)):
        def r(v):
            return [round(float(a), 4) for a in v]
        bones = []
        for b in self.bones:
            jb = {'name': b.name}
            if b.parent:
                jb['parent'] = b.parent
            jb['pivot'] = r(b.pivot)
            if b.rot and any(b.rot):
                jb['rotation'] = r(b.rot)
            cubes = []
            for c in b.cubes:
                if not c.uv:
                    continue
                jc = {'origin': r(c.origin), 'size': r(c.size)}
                if c.rot and any(c.rot):
                    jc['pivot'] = r(c.pivot)
                    jc['rotation'] = r(c.rot)
                jc['uv'] = c.uv
                cubes.append(jc)
            if cubes:
                jb['cubes'] = cubes
            bones.append(jb)
        return {
            'format_version': '1.12.0',
            'minecraft:geometry': [{
                'description': {
                    'identifier': self.identifier,
                    'texture_width': self.tex_w, 'texture_height': self.tex_h,
                    'visible_bounds_width': bounds[0], 'visible_bounds_height': bounds[1],
                    'visible_bounds_offset': [0, bounds[2], 0]},
                'bones': bones}]}


# ----------------------------------------------------------------- renderer
def load_quads(geo, pose=None):
    """geo: parsed .geo.json  ->  list of (4x3 BB-space corners TL,TR,BR,BL, 4x2 uv, normal)
    pose: optional {bone: (rx,ry,rz)} extra rotations (JSON) for simulation of animations."""
    g = geo['minecraft:geometry'][0]
    bones = {b['name']: b for b in g['bones']}
    cache = {}

    def bm(name):
        if name in cache:
            return cache[name]
        b = bones[name]
        rot = list(b.get('rotation', [0, 0, 0]))
        if pose and name in pose:
            rot = [rot[i] + pose[name][i] for i in range(3)]
        M = xform(b.get('pivot', [0, 0, 0]), rot)
        if b.get('parent'):
            M = bm(b['parent']) @ M
        cache[name] = M
        return M
    quads = []
    for b in g['bones']:
        MB = bm(b['name'])
        for c in b.get('cubes', []):
            M = MB @ xform(c.get('pivot', [0, 0, 0]), c.get('rotation'))
            corners = face_corners(c['origin'], c['size'])
            for f, uv in c['uv'].items():
                TL, TR, BL = (np.array(v, float) for v in corners[f])
                BR = TR + BL - TL
                pts = np.array([TL, TR, BR, BL]) @ M[:3, :3].T + M[:3, 3]
                u0, v0 = uv['uv']
                us, vs = uv['uv_size']
                uvs = np.array([[u0, v0], [u0 + us, v0], [u0 + us, v0 + vs], [u0, v0 + vs]], float)
                n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
                ln = np.linalg.norm(n)
                if ln < 1e-9:
                    continue
                quads.append((pts, uvs, n / ln))
    return quads


def render(geo, tex, yaw=35, pitch=8, dist=110, target=(0, 22, 0), size=(576, 632), fov=30,
           ss=2, bg=(58, 36, 20), pose=None, zoom=1.0, shift=(0, 0), window=None, scale=1, ortho=None, alpha=False, light=True):
    """yaw: camera angle from the entity's front toward its LEFT (deg); pitch: camera elevation."""
    T = np.asarray(tex.convert('RGBA'), float) / 255.
    # window: (x0,y0,x1,y1) in base-size pixels, rendered magnified by `scale`
    if window is None:
        window = (0, 0, size[0], size[1])
    k = ss * scale
    W, H = int((window[2] - window[0]) * k), int((window[3] - window[1]) * k)
    out_size = (int((window[2] - window[0]) * scale), int((window[3] - window[1]) * scale))
    pcx = (size[0] / 2 + shift[0] - window[0]) * k
    pcy = (size[1] / 2 + shift[1] - window[1]) * k
    quads = load_quads(geo, pose)
    ya, pi = math.radians(yaw), math.radians(pitch)
    tgt = np.array([-target[0], target[1], target[2]], float)
    cam = tgt + dist * np.array([-math.sin(ya) * math.cos(pi), math.sin(pi), -math.cos(ya) * math.cos(pi)])
    f = tgt - cam
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0])
    r /= np.linalg.norm(r)
    up = np.cross(r, f)
    foc = (size[1] * k / 2) / math.tan(math.radians(fov) / 2) * zoom
    col = np.zeros((H, W, 3)) + np.array(bg) / 255.
    zb = np.zeros((H, W))
    cov = np.zeros((H, W))
    L = np.array([0.25, 0.9, -0.35])  # BB space light (from above / front)
    L /= np.linalg.norm(L)
    for pts, uvs, n in quads:
        rel = pts - cam
        x, y, z = rel @ r, rel @ up, rel @ f
        if (z < 1).any():
            continue
        if ortho:            # ortho = pixels per model unit
            sx = pcx + ortho * k * x
            sy = pcy - ortho * k * y
            iz = np.ones(4)
            dep = 1.0 / z
        else:
            sx = pcx + foc * x / z
            sy = pcy - foc * y / z
            iz = 1 / z
            dep = iz
        if n @ (pts.mean(0) - cam) > 0:
            n = -n
        shade = min(1.0, 0.66 + 0.26 * max(0.0, n @ L) + 0.10 * n[1] + 0.06 * abs(n[2])) if light else 1.0
        umin, umax = sorted((uvs[0, 0], uvs[2, 0]))
        vmin, vmax = sorted((uvs[0, 1], uvs[2, 1]))
        for a, b, c in ((0, 1, 2), (0, 2, 3)):
            x0, x1 = int(max(0, math.floor(min(sx[a], sx[b], sx[c])))), int(min(W - 1, math.ceil(max(sx[a], sx[b], sx[c]))))
            y0, y1 = int(max(0, math.floor(min(sy[a], sy[b], sy[c])))), int(min(H - 1, math.ceil(max(sy[a], sy[b], sy[c]))))
            if x0 > x1 or y0 > y1:
                continue
            den = (sy[b] - sy[c]) * (sx[a] - sx[c]) + (sx[c] - sx[b]) * (sy[a] - sy[c])
            if abs(den) < 1e-9:
                continue
            PX, PY = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
            wa = ((sy[b] - sy[c]) * (PX - sx[c]) + (sx[c] - sx[b]) * (PY - sy[c])) / den
            wb = ((sy[c] - sy[a]) * (PX - sx[c]) + (sx[a] - sx[c]) * (PY - sy[c])) / den
            wc = 1 - wa - wb
            m = (wa >= -1e-6) & (wb >= -1e-6) & (wc >= -1e-6)
            if not m.any():
                continue
            izp = wa * iz[a] + wb * iz[b] + wc * iz[c]
            dpp = wa * dep[a] + wb * dep[b] + wc * dep[c]
            m &= dpp > zb[y0:y1 + 1, x0:x1 + 1]
            if not m.any():
                continue
            uu = (wa * uvs[a, 0] * iz[a] + wb * uvs[b, 0] * iz[b] + wc * uvs[c, 0] * iz[c]) / izp
            vv = (wa * uvs[a, 1] * iz[a] + wb * uvs[b, 1] * iz[b] + wc * uvs[c, 1] * iz[c]) / izp
            ui = np.clip(np.floor(np.clip(uu, umin, umax - 1e-4)).astype(int), 0, T.shape[1] - 1)
            vi = np.clip(np.floor(np.clip(vv, vmin, vmax - 1e-4)).astype(int), 0, T.shape[0] - 1)
            texel = T[vi, ui]
            m &= texel[..., 3] > 0.5
            if not m.any():
                continue
            sub_c = col[y0:y1 + 1, x0:x1 + 1]
            sub_z = zb[y0:y1 + 1, x0:x1 + 1]
            sub_c[m] = texel[..., :3][m] * shade
            sub_z[m] = dpp[m]
            cov[y0:y1 + 1, x0:x1 + 1][m] = 1
    if alpha:
        img = Image.fromarray((np.clip(np.dstack([col, cov]), 0, 1) * 255 + .5).astype(np.uint8), 'RGBA')
    else:
        img = Image.fromarray((np.clip(col, 0, 1) * 255 + .5).astype(np.uint8))
    if ss > 1:
        img = img.resize(out_size, Image.LANCZOS)
    return img


def load(geo_path, tex_path):
    with open(geo_path) as fh:
        return json.load(fh), Image.open(tex_path)
