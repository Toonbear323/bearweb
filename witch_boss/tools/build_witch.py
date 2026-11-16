"""Raven Witch boss (voxel style) - geometry + texture generator for a Bedrock add-on.

The model is authored on the voxel grid of the reference art (../ref/front.png):
one art "voxel" (21.8 px) = one model unit.  Every front-facing texel is taken
straight from the reference picture (orthographic projection), the other faces
are wrapped / tiled from clean parts of the same picture.

Run:  python3 build_witch.py <out_dir>
Authoring space: +X = her LEFT (picture right), +Y = up, -Z = FRONT.
"""
import json
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mclib import Model  # noqa: E402
from paint import C, mix, hashf  # noqa: E402

# ------------------------------------------------------------------ reference grid
PITCH, OX, OY = 21.8, -3.1, -3.1      # art pixels per voxel, origin of cell (0,0)
CX, GY = 28.0, 45.8                   # grid column of X=0, grid row of the ground (Y=0)
_ART = Image.open(os.path.join(HERE, '..', 'ref', 'front.png')).convert('RGB')
_BLUR = {}


def art(d):
    """reference picture pre-filtered for a texel density of d texels / voxel"""
    if d not in _BLUR:
        r = PITCH / d / 2.0
        im = _ART.filter(ImageFilter.BoxBlur(r)) if r > 0.6 else _ART
        _BLUR[d] = np.asarray(im, float) / 255.
    return _BLUR[d]


def sample(col, row, d=4):
    a = art(d)
    ax = np.clip(np.round(OX + np.asarray(col) * PITCH).astype(int), 0, a.shape[1] - 1)
    ay = np.clip(np.round(OY + np.asarray(row) * PITCH).astype(int), 0, a.shape[0] - 1)
    return a[ay, ax]


def dens(ctx):
    return max(1, int(round(ctx.w / ctx.fw)))


def tri(t, w):
    """mirror-repeat t into [0, w]"""
    t = np.mod(t, 2 * w)
    return np.where(t > w, 2 * w - t, t)


def voxel_jitter(ctx, amp=0.07):
    q = np.floor(ctx.Pm + 500.01).astype(np.int64)
    return 1 + (hashf(q[..., 0], q[..., 1], q[..., 2], 7) - .5) * 2 * amp


# ------------------------------------------------------------------ materials
def proj(ctx):
    """orthographic projection of the reference picture (front / back faces)"""
    P = ctx.Pm
    return sample(P[..., 0] + CX, GY - P[..., 1], dens(ctx))


def wrap(side=0.9, top=1.05, bottom=0.72, inset=0.5):
    """front/back: projection.  other faces: the colours of the nearest front edge, smeared
    backwards (keeps every row / column colour of the picture), with a little voxel jitter."""
    def f(ctx):
        c = ctx.cube
        P = ctx.Pm
        X, Y = P[..., 0], P[..., 1]
        x0, x1 = c.origin[0] + inset, c.origin[0] + c.size[0] - inset
        y0, y1 = c.origin[1] + inset, c.origin[1] + c.size[1] - inset
        if x1 < x0:
            x0 = x1 = c.origin[0] + c.size[0] / 2
        if y1 < y0:
            y0 = y1 = c.origin[1] + c.size[1] / 2
        fc = ctx.face
        if fc in ('north', 'south'):
            return proj(ctx)
        if fc in ('east', 'west'):
            Xs = np.full(X.shape, x0 if fc == 'east' else x1)
            return sample(Xs + CX, GY - np.clip(Y, y0, y1), 2) * side * voxel_jitter(ctx)[..., None]
        Ys = np.full(Y.shape, y1 if fc == 'up' else y0)
        return sample(np.clip(X, x0, x1) + CX, GY - Ys, 2) * (top if fc == 'up' else bottom) * voxel_jitter(ctx)[..., None]
    return f


def patch(c0, c1, r0=None, r1=None, north=True, side=0.92, top=1.05, bottom=0.72, row_up=None, row_down=None):
    """front: projection (if north).  other faces: the clean picture columns c0..c1 mirror-tiled
    around the box, rows kept (so bands / gradients line up with the front)."""
    w = c1 - c0

    def f(ctx):
        P = ctx.Pm
        X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
        fc = ctx.face
        if fc == 'north' and north:
            return proj(ctx)
        row = GY - Y
        if r0 is not None:
            row = np.clip(row, r0 + 0.25, r1 - 0.25)
        if fc in ('east', 'west'):
            return sample(c0 + tri(Z + 40.3, w), row, 2) * side
        if fc in ('south', 'north'):
            return sample(c0 + tri(X + 40.3, w), row, 2)
        c = ctx.cube
        if fc == 'up':
            rr = row_up if row_up is not None else (GY - (c.origin[1] + c.size[1]) + 0.5)
            m = top
        else:
            rr = row_down if row_down is not None else (GY - c.origin[1] - 0.5)
            m = bottom
        if r0 is not None:
            rr = min(max(rr, r0 + 0.25), r1 - 0.25)
        return sample(c0 + tri(X + 0.57 * np.floor(Z) + 40.3, w), np.full(X.shape, rr), 2) * m * voxel_jitter(ctx)[..., None]
    return f


def rowpick(cols, r0=None, r1=None, north=True, side=0.92, top=1.05, bottom=0.72, seed=0, row_up=None, streak=True):
    """front: projection.  other faces: voxel cells whose colours are picked at random from the
    clean picture columns `cols`, always from the texel's own row (bands and gradients survive)."""
    cols = np.asarray(cols, float)

    def pick(i, j, k):
        return cols[(hashf(i, j, k, 17 + seed) * len(cols)).astype(int) % len(cols)]

    def f(ctx):
        P = ctx.Pm
        X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
        fc = ctx.face
        if fc == 'north' and north:
            return proj(ctx)
        row = GY - Y
        if r0 is not None:
            row = np.clip(row, r0 + 0.2, r1 - 0.2)
        if fc in ('east', 'west', 'south', 'north'):
            h = Z if fc in ('east', 'west') else X
            i = np.floor(h + 60.001).astype(np.int64)
            j = np.floor(row + 0.001).astype(np.int64)
            c = pick(i, j * 0 if streak else j, 1 if fc in ('east', 'west') else 2)
            return sample(c + (h + 60.001 - i), row, 2) * (side if fc in ('east', 'west') else 1.0)
        c = ctx.cube
        rr = (row_up if row_up is not None else GY - (c.origin[1] + c.size[1]) + 0.5) if fc == 'up' else GY - c.origin[1] - 0.5
        if r0 is not None:
            rr = min(max(rr, r0 + 0.2), r1 - 0.2)
        i = np.floor(X + 60.001).astype(np.int64)
        k = np.floor(Z + 60.001).astype(np.int64)
        cc = pick(i, k, 3)
        return sample(cc + (X + 60.001 - i), np.full(X.shape, rr), 2) * (top if fc == 'up' else bottom) * voxel_jitter(ctx, 0.05)[..., None]
    return f


def flat(col, amp=0.06):
    c = C(col) if isinstance(col, str) else np.asarray(col)

    def f(ctx):
        return np.broadcast_to(c, ctx.u.shape + (3,)) * voxel_jitter(ctx, amp)[..., None]
    return f


def with_alpha(mat, poly=None, key=None):
    """projection + alpha cut-out.  poly: polygon in grid coords;  key: fn(rgb)->bool mask"""
    def f(ctx):
        rgb = mat(ctx)
        a = np.ones(rgb.shape[:2])
        if poly is not None:
            P = ctx.Pm
            col, row = P[..., 0] + CX, GY - P[..., 1]
            c0, r0 = col.min(), row.min()
            s = 8
            im = Image.new('L', (ctx.w * s, ctx.h * s), 0)
            d = dens(ctx)
            c_left = col[0, 0] - 0.5 / d
            r_top = row[0, 0] - 0.5 / d
            ImageDraw.Draw(im).polygon([((c - c_left) * d * s, (r - r_top) * d * s) for c, r in poly], fill=255)
            a = np.asarray(im, float).reshape(ctx.h, s, ctx.w, s).mean((1, 3)) / 255. >= 0.5
        if key is not None:
            a = a * key(rgb)
        return np.dstack([rgb, np.asarray(a, float)])
    return f


def blue_key(rgb):
    return (rgb[..., 2] > 0.36) & (rgb[..., 2] > rgb[..., 0] * 1.6)


def teal_key(rgb):
    return (rgb[..., 1] > rgb[..., 0] + 0.06) & (rgb[..., 1] > 0.28)


# ------------------------------------------------------------------ custom painters
BRIM_C = (0.4, 0.0, 17.0, 16.0)     # centre x, centre z, radius x, radius z


def brim_top(ctx):
    P = ctx.Pm
    X, Z = P[..., 0], P[..., 2]
    r = np.sqrt(((X - BRIM_C[0]) / BRIM_C[2]) ** 2 + ((Z - BRIM_C[1]) / BRIM_C[3]) ** 2)
    purple = sample(18.5 + tri(X + 0.43 * np.floor(Z) + 40, 18.0), 13.85 + 0.8 * hashf(np.floor(X + 99), np.floor(Z + 99), 0, 3), 2)
    gold = sample(11.8 + tri(X + Z + 40, 2.4), np.full(X.shape, 13.45), 2)
    return np.where((r > 0.925)[..., None], gold, purple * voxel_jitter(ctx, 0.05)[..., None])


def brim_under(ctx):
    P = ctx.Pm
    X, Z = P[..., 0], P[..., 2]
    r = np.sqrt(((X - BRIM_C[0]) / BRIM_C[2]) ** 2 + ((Z - BRIM_C[1]) / BRIM_C[3]) ** 2)
    dark = sample(13.0 + tri(X + 0.43 * np.floor(Z) + 40, 5.0), 15.2 + 2.0 * hashf(np.floor(X + 99), np.floor(Z + 99), 0, 5), 2)
    gold = sample(11.8 + tri(X + Z + 40, 2.4), np.full(X.shape, 13.45), 2) * 0.8
    return np.where((r > 0.94)[..., None], gold, dark * 0.9)


def brim_strip(ctx):
    """front/back: projection; outer side faces: keep the gold-on-top / dark-below profile"""
    fc = ctx.face
    if fc in ('north', 'south'):
        return proj(ctx)
    if fc == 'up':
        return brim_top(ctx)
    if fc == 'down':
        return brim_under(ctx)
    c = ctx.cube
    P = ctx.Pm
    xs = c.origin[0] + c.size[0] / 2
    return sample(np.full(P[..., 0].shape, xs) + CX, GY - P[..., 1], 2)


HAIR_COLS = np.array([21, 22, 23, 24, 31, 32, 33, 34], float)
HAIR_RAMP = [(0.0, '#F2F6F8'), (0.2, '#DCEAF0'), (0.4, '#B9DEE8'), (0.58, '#97BEE2'), (0.76, '#7088D4'), (1.0, '#4A52B4')]


def hair_vox(ctx):
    """hair on every non-front face: white near the crown, running through cyan to blue at the
    tips, in vertical strands with a little voxel checker (as in the back view of the sheet)."""
    P = ctx.Pm
    X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
    fc = ctx.face
    row = GY - Y
    if fc in ('east', 'west'):
        h, lat = Z, np.abs(Z) * 0.35
    else:
        h, lat = X, np.abs(X - 0.3)
    if fc in ('up', 'down'):
        i = np.floor(X + 60.001).astype(np.int64)
        j = np.floor(Z + 60.001).astype(np.int64)
        row = np.full(X.shape, 16.5 if fc == 'up' else GY - ctx.cube.origin[1] - 0.5)
        lat = np.zeros(X.shape)
        strand = hashf(i, j, 2, 29)
    else:
        i = np.floor(h + 60.001).astype(np.int64)
        j = np.floor(row + 0.001).astype(np.int64)
        strand = hashf(i, 0, 2, 29)
    cell = hashf(i, j, 9, 31)
    t = 0.04 + np.clip((row - 18.0) / 19.0, 0, 1) ** 1.25 * 0.9 + np.clip(lat / 8.0, 0, 1) * 0.28 + (strand - 0.5) * 0.22 + (cell - 0.5) * 0.12
    t = t + (cell > 0.86) * 0.22            # the odd darker voxel, like the checker of the front
    xs = np.array([q[0] for q in HAIR_RAMP])
    cs = np.array([C(q[1]) for q in HAIR_RAMP])
    t = np.clip(t, 0, 1)
    col = np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], -1)
    if fc in ('east', 'west'):
        col = col * 0.94
    if fc == 'down':
        col = col * 0.78
    return col


hair_back = hair_vox


# ------------------------------------------------------------------ build
def build():
    m = Model('geometry.raven_witch')
    m.bone('root', pivot=(0, 0, 0))

    def G(bone, c0, c1, r0, r1, z0, z1, mat, **kw):
        """box given in grid coordinates (cols c0..c1, rows r0..r1 measured downward)"""
        kw.setdefault('ds', 2)
        return bone.box(c0 - CX, GY - r1, z0, c1 - CX, GY - r0, z1, mat, **kw)

    body = m.bone('body', 'root', pivot=(0, GY - 31, 0))
    head = m.bone('head', 'body', pivot=(0, GY - 25, 0))

    # ================= head / hair =================
    HAIR_L = HAIR_TOP = hair_vox
    # main volume; its front face carries the face itself (projection)
    G(head, 21, 35, 16, 20, -6, 7, {'north': proj, 'south': hair_back, 'east': HAIR_L, 'west': HAIR_L, 'up': HAIR_TOP, 'down': HAIR_L}, d=8)
    G(head, 20, 37, 20, 22, -6, 7, {'north': proj, 'south': hair_back, 'east': HAIR_L, 'west': HAIR_L, 'up': HAIR_L, 'down': HAIR_L}, d=8)
    G(head, 37, 38, 21, 22, -6, 5, HAIR_L)
    # front layer (one voxel proud of the face) with the face window left open
    FR = {'north': proj, 'south': None, 'east': HAIR_L, 'west': HAIR_L, 'up': HAIR_L, 'down': HAIR_L}
    for c0, c1, r0, r1 in ((21, 35, 16, 17), (21, 28, 17, 18), (31, 35, 17, 18), (21, 27, 18, 19), (31, 35, 18, 19),
                           (21, 26, 19, 20), (31, 36, 19, 20), (20, 25, 20, 21), (31, 37, 20, 21), (20, 25, 21, 22), (31, 38, 21, 22)):
        G(head, c0, c1, r0, r1, -7, -6, FR, d=8)
    # side locks falling over the shoulders
    for c0, c1, r0, r1, z0, z1 in ((21, 25, 22, 24, -7, 7), (20, 24, 24, 25, -7, 6), (22.5, 24, 25, 26.5, -7, -5),
                                   (31, 36, 22, 24, -7, 7), (32, 36, 24, 25, -7, 6), (31.6, 33.2, 24, 26.5, -7, -5)):
        G(head, c0, c1, r0, r1, z0, z1, {'north': proj, 'south': hair_back, 'east': HAIR_L, 'west': HAIR_L, 'up': HAIR_L, 'down': HAIR_L})
    # long cascade down the back
    for c0, c1, r0, r1 in ((20.5, 36.5, 22, 26), (22, 35, 26, 29), (23.5, 33.5, 29, 32), (25.2, 31.8, 32, 34.2), (26.8, 30.2, 34.2, 36), (27.8, 29.2, 36, 37.2)):
        G(head, c0, c1, r0, r1, 4.0, 7.6, hair_back)

    # mask collar
    COL = patch(25.2, 26.4, 21, 25.5)
    G(head, 25, 31, 21, 25.5, -6.6, 1.0, {'north': proj, 'south': COL, 'east': COL, 'west': COL, 'up': COL, 'down': COL}, d=8)

    # ================= hat =================
    hat = m.bone('hat', 'head', pivot=(0.5, GY - 16, 0))
    TOP = rowpick([25, 26, 27, 28, 29, 30], 1.2, 5.6)
    MID = rowpick([26, 27, 31, 32], 5.7, 8.2, row_up=6.2)
    BAND = rowpick([24, 25, 26, 27], 8.7, 9.9)
    BASE = rowpick([23, 24, 25, 26, 27], 10, 12.5, row_up=10.5)
    G(hat, 25, 31, 1.15, 5.7, -3, 3, TOP)
    G(hat, 31, 33, 4.6, 6.0, -2.5, 2.5, rowpick([31, 32], 4.7, 6))
    G(hat, 23.5, 34, 5.6, 8.8, -5.25, 5.25, MID)
    G(hat, 23.3, 34.2, 8.7, 10.0, -5.45, 5.45, BAND)
    G(hat, 22.4, 35.6, 10, 12.6, -6.6, 6.6, BASE)
    G(hat, 20.6, 37.2, 12.4, 13.7, -8.3, 8.3, rowpick([21, 22, 23, 24, 25, 26, 27, 34, 35, 36], 12.5, 13.6))
    G(hat, 17, 39.5, 13.4, 15.0, -12, 12, {'north': proj, 'south': proj, 'east': brim_strip, 'west': brim_strip, 'up': brim_top, 'down': None})
    # brim strips.  Their stepped tops give the slant of the gold rim in the picture; the outer strips
    # reach further down and form the two drooping ends (outline traced from the picture).
    TOPS = ((11.8, 14.95, 12.95), (14.95, 17.3, 13.4), (17.3, 21.5, 14.0), (21.5, 25.0, 14.4), (25.0, 34.0, 14.9), (34.0, 39.2, 15.05),
            (39.2, 41.6, 15.5), (41.6, 42.6, 15.05), (42.6, 44.1, 14.5), (44.1, 45.45, 14.0))
    BOT = ((11.8, 14.6), (12.0, 15.5), (12.75, 17.0), (14.0, 17.9), (15.0, 18.4), (16.0, 19.0), (17.0, 19.3), (18.6, 19.7), (19.5, 19.9), (21.0, 20.0),
           (21.01, 16.0), (34.99, 16.0), (35.0, 20.0), (36.1, 19.9), (38.0, 19.65), (39.2, 19.3), (41.0, 19.0), (42.5, 18.5), (43.4, 17.9), (44.5, 17.0), (45.45, 15.6))
    edges = sorted(set([11.8, 45.45, 21.0, 35.0] + [t[0] for t in TOPS] + [t[1] for t in TOPS] + list(np.arange(12.5, 21.0, 0.5)) + list(np.arange(35.5, 45.4, 0.5))))
    for c0, c1 in zip(edges[:-1], edges[1:]):
        if c1 - c0 < 0.05:
            continue
        cm = (c0 + c1) / 2
        rt = [t[2] for t in TOPS if t[0] <= cm < t[1]][0]
        rb = float(np.interp(cm, [p[0] for p in BOT], [p[1] for p in BOT]))
        rb = max(round(rb * 4) / 4, rt + 0.6)
        zh = 16.0 * math.sqrt(max(0.1, 1 - ((cm - 28.4) / 17.2) ** 2))
        G(hat, c0, c1, rt, rb, -zh, zh, brim_strip)

    # squared spiral on her left: chunky outer ring + cut-out inner hook, tail stepping back to the hat
    for c0, c1, r0, r1 in ((37.9, 42.7, 6.75, 7.8), (41.7, 42.7, 7.8, 11.1), (37.9, 39.0, 7.8, 10.95), (39.0, 40.5, 10.1, 10.95),
                           (38.2, 42.7, 11.1, 12.1), (37.1, 38.3, 11.1, 12.1), (36.0, 37.2, 10.6, 11.5), (35.0, 36.1, 9.7, 10.7), (34.0, 35.1, 8.8, 9.8)):
        G(hat, c0, c1, r0, r1, -0.75, 0.75, wrap())
    G(hat, 39.0, 41.7, 7.8, 11.1, 0, 0, with_alpha(proj, key=blue_key), faces=('north',), d=8)
    G(hat, 38.4, 39.8, 12.6, 14.0, -0.4, 0.4, wrap())

    # pumpkin
    pk = m.bone('pumpkin', 'hat', pivot=(30.4 - CX, GY - 10.8, -8))
    G(pk, 28.2, 32.7, 9.0, 12.5, -9.8, -6.4, wrap(side=0.95, top=1.0, bottom=0.8, inset=0.35), d=8)
    G(pk, 29.9, 30.7, 8.2, 9.1, -8.6, -7.8, wrap())
    G(pk, 28.4, 29.6, 8.5, 9.3, -9.6, -8.8, wrap())
    G(pk, 32.5, 35.6, 9.3, 12.9, -7.6, -7.6, with_alpha(proj, key=teal_key), faces=('north',), d=8)
    G(pk, 28.7, 31.5, 12.3, 14.2, -9.9, -9.9, with_alpha(proj, key=teal_key), faces=('north',), d=8)

    # ================= raven (hovering over the brim on her right) =================
    rv = m.bone('raven', 'hat', pivot=(11.9 - CX, GY - 7.2, 0))
    G(rv, 9.9, 13.9, 4.9, 9.6, -1.8, 1.8, rowpick([10.6, 11.2, 12.2, 12.8], 5.0, 9.5, streak=False), d=8)                  # body
    rh = m.bone('ravenHead', 'raven', pivot=(11.9 - CX, GY - 4.9, -0.5))
    G(rh, 9.85, 13.95, 1.4, 5.0, -2.8, 1.3, rowpick([11.3, 12.0, 12.4], 1.7, 2.6, streak=False, top=1.0, row_up=1.9), d=8)    # skull
    G(rh, 11.9, 12.8, 4.0, 5.9, -3.7, -2.8, wrap(), d=8)                                 # beak
    for c0, c1 in ((10.05, 10.6), (12.35, 12.9)):
        G(rv, c0, c1, 9.5, 10.9, -0.3, 0.3, wrap())                                      # legs
    for c0, c1 in ((9.6, 11.0), (11.9, 13.4)):
        G(rv, c0, c1, 10.7, 11.9, -1.3, 0.4, wrap())                                     # feet
    LW = [(9.95, 4.6), (9.4, 3.5), (8.8, 2.8), (8.1, 2.1), (7.6, 1.4), (6.8, 0.6), (5.2, 0.0), (4.0, 0.0), (3.2, 0.2), (2.9, 1.6), (3.3, 1.5),
          (3.4, 2.9), (3.9, 2.8), (3.6, 4.3), (4.4, 4.2), (4.4, 5.6), (5.3, 5.4), (5.4, 6.6), (6.4, 6.4), (6.6, 7.6), (7.6, 7.5),
          (7.9, 8.4), (8.8, 8.2), (9.2, 9.0), (9.9, 8.6)]
    RW = [(13.9, 5.3), (15.0, 5.2), (16.0, 5.0), (17.2, 4.6), (18.3, 4.2), (20.3, 3.1), (20.2, 4.2), (20.0, 5.0), (19.0, 5.6),
          (19.2, 6.6), (18.0, 6.6), (17.8, 7.6), (16.6, 7.6), (16.2, 8.5), (15.2, 8.6), (14.6, 9.0), (13.9, 8.6)]
    TL = [(7.0, 10.0), (8.5, 9.3), (10.5, 9.4), (13.0, 9.3), (14.6, 9.4), (15.2, 10.6), (14.4, 11.6), (13.6, 11.0), (12.0, 10.4), (10.9, 12.6), (9.6, 12.9), (9.3, 12.4), (8.4, 12.9), (8.0, 12.2), (7.2, 12.2), (6.6, 10.8)]
    wl = m.bone('ravenWingR', 'raven', pivot=(9.9 - CX, GY - 5.6, 0.6))      # the raven's own right wing (picture left)
    G(wl, 2.4, 10.2, 0.0, 9.4, 0.6, 0.6, with_alpha(proj, poly=LW), faces=('north',), d=8)
    wr = m.bone('ravenWingL', 'raven', pivot=(13.9 - CX, GY - 5.8, 0.6))
    G(wr, 13.6, 20.6, 2.8, 9.3, 0.6, 0.6, with_alpha(proj, poly=RW), faces=('north',), d=8)
    G(rv, 6.4, 15.4, 9.1, 13.1, 1.2, 1.2, with_alpha(proj, poly=TL), faces=('north',), d=8)

    # ================= body =================
    ROBE = rowpick([25, 26, 27, 28, 29, 30, 31], 33.2, 45.6)
    G(body, 24, 32.3, 25.5, 31, -4.5, 4.0, {'north': proj, 'south': ROBE, 'east': ROBE, 'west': ROBE, 'up': ROBE, 'down': None}, d=8)
    G(body, 24, 32.3, 24, 25.5, -4.5, 4.0, {'north': proj, 'south': ROBE, 'east': ROBE, 'west': ROBE, 'up': ROBE, 'down': None}, d=8)   # neck / shoulders
    G(body, 26.8, 29.0, 25.3, 28.7, -5.6, -4.5, wrap(), d=8)                             # brooch
    G(body, 26.8, 29.4, 29.8, 32.7, -5.3, -4.4, wrap(), d=8)                             # chevron ornament
    for r0, r1, c0, c1, zh, cols in ((28.8, 31, 20.6, 35.7, 3.2, [21, 22, 23, 33, 34, 35]), (31, 35, 20.0, 36.3, 4.0, [20, 21, 22, 23, 33, 34, 35]),
                                     (35, 37, 20.0, 36.3, 4.6, [22, 23, 25, 26, 28, 29, 30, 31, 33]), (37, 39, 19.5, 36.8, 5.2, [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33]),
                                     (39, 41, 18.7, 37.5, 5.9, [21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34]),
                                     (41, 43.5, 18.0, 38.2, 6.6, [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]),
                                     (43.5, 45.8, 17.3, 39.0, 7.3, [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36])):
        mt = rowpick(cols, r0, r1)
        G(body, c0, c1, r0, r1, 0.4 - zh, 0.4 + zh, {'north': proj, 'south': mt, 'east': mt, 'west': mt, 'up': mt, 'down': flat('#120A22')})

    # ================= arms (A-pose with hanging bell sleeves) =================
    def arm(name, mir):
        def mc(c0, c1):
            return (c0, c1) if not mir else (56.3 - c1, 56.3 - c0)
        px = (mc(23.6, 24.0)[0] if not mir else mc(23.6, 24.0)[1]) - CX
        a = m.bone(name, 'body', pivot=(px, GY - 26.4, 0))
        for c0, c1, r0, r1, zh in ((21, 24, 25.8, 28.8, 3.4), (19, 22, 27, 30, 3.5), (17, 20.6, 29, 31.4, 3.7), (14.9, 20.0, 31.2, 37.4, 4.0), (15.8, 18.4, 37.4, 38.2, 2.4)):
            a0, a1 = mc(c0, c1)
            G(a, a0, a1, r0, r1, -zh, zh, wrap())
    arm('rightArm', False)
    arm('leftArm', True)
    return m


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    m = build()
    atlas = m.bake(max_w=1024)
    atlas.save(os.path.join(out, 'raven_witch.png'))
    with open(os.path.join(out, 'raven_witch.geo.json'), 'w') as fh:
        json.dump(m.to_json(bounds=(7, 6, 2)), fh, separators=(',', ':'))
    n = sum(len(b.cubes) for b in m.bones)
    print('bones', len(m.bones), 'cubes', n, 'atlas', atlas.size)
