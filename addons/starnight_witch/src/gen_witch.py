#!/usr/bin/env python3
"""Starnight Witch (original boss design) - Bedrock geometry + texture generator and preview renderer.

Usage: python3 gen_witch.py <out_dir>
Writes geometry json, texture png and preview renders.
Coordinates are Bedrock geometry-file coordinates: +Y up, front = -Z, character's left = +X.
"""
import numpy as np, json, math, os, sys
from PIL import Image

D = 4  # texels per model unit (1 unit = 1/16 block)


# ---------------------------------------------------------------- palettes
def hx(s):
    s = s.lstrip('#')
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], float)


def pal(*cs):
    return np.array([hx(c) for c in cs])


NAVY = pal('#0d1033', '#141a4c', '#1c2566', '#273285', '#3443a6', '#4a5cc4')
HAT = pal('#0a0c2a', '#11153f', '#192159', '#232e78', '#30409a')
LINING = pal('#33103f', '#4d1759', '#6c2274', '#8f3794')
PANEL = pal('#2a1a5e', '#3b2580', '#5234a3', '#6d4cc4')
GOLD = pal('#7a4a16', '#b9812a', '#e9b93f', '#ffe07a', '#fff6c8')
TEAL = pal('#0a4a5c', '#11788a', '#1fb0b8', '#7af0e6')
HAIR = pal('#6a68a6', '#9896cf', '#c3c4ec', '#e4e7fb', '#ffffff')
SKIN = pal('#d6979d', '#efbab6', '#fbd8ce', '#ffeae0', '#fff6f0')
WOOD = pal('#241631', '#38234a', '#4e3366', '#6a4a86')
PAGE = pal('#a8946a', '#cdbb8c', '#eadfb8', '#f8f1d8')
CRY = pal('#0b5f86', '#19a8d8', '#6fe8f4', '#e4ffff')
INK = hx('#4a3a6a')


def hash3(x, y, z, seed=0):
    h = (x.astype(np.int64) * 374761393 + y.astype(np.int64) * 668265263
         + z.astype(np.int64) * 40503 + seed * 1274126177) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF) / 65536.0


# ---------------------------------------------------------------- model store
BONES = {}
ORDER = []


def bone(name, parent=None, pivot=(0, 0, 0), rot=(0, 0, 0)):
    BONES[name] = dict(name=name, parent=parent, pivot=list(pivot), rot=list(rot), cubes=[])
    ORDER.append(name)


def cube(b, o, s, paint, rot=None, pivot=None, inflate=0.0, faces='nsewud'):
    c = dict(o=list(map(float, o)), s=list(map(float, s)), paint=paint, rot=rot, pivot=pivot,
             inflate=inflate, faces=faces, uv={})
    if rot is not None and pivot is None:
        c['pivot'] = [o[0] + s[0] / 2, o[1] + s[1] / 2, o[2] + s[2] / 2]
    BONES[b]['cubes'].append(c)
    return c


def face_point(c, face, u, v):
    """model-space point (unrotated) for face uv in [0,1] (u right, v down as seen from outside)."""
    x0, y0, z0 = c['o']
    sx, sy, sz = c['s']
    x1, y1, z1 = x0 + sx, y0 + sy, z0 + sz
    one = np.ones_like(u, dtype=float)
    if face == 'n':
        return x0 + u * sx, y1 - v * sy, z0 * one
    if face == 's':
        return x1 - u * sx, y1 - v * sy, z1 * one
    if face == 'e':  # file "east" = min-x side (character's right)
        return x0 * one, y1 - v * sy, z1 - u * sz
    if face == 'w':
        return x1 * one, y1 - v * sy, z0 + u * sz
    if face == 'u':
        return x0 + u * sx, y1 * one, z1 - v * sz
    if face == 'd':
        return x0 + u * sx, y0 * one, z0 + v * sz


class Ctx:
    def __init__(s, c, face):
        sx, sy, sz = c['s']
        w, h = (sx, sy) if face in 'ns' else (sz, sy) if face in 'ew' else (sx, sz)
        s.W = max(1, int(round(w * D)))
        s.H = max(1, int(round(h * D)))
        s.face = face
        s.c = c
        u = (np.arange(s.W) + 0.5) / s.W
        v = (np.arange(s.H) + 0.5) / s.H
        U, V = np.meshgrid(u, v)
        s.U, s.V = U, V
        s.X, s.Y, s.Z = face_point(c, face, U, V)
        s.px, s.py = np.meshgrid(np.arange(s.W), np.arange(s.H))
        s.S = s.X if face in 'nsud' else s.Z
        s.ty = (s.Y - c['o'][1]) / sy
        s.ix = np.floor(s.X * D + 1e-4)
        s.iy = np.floor(s.Y * D + 1e-4)
        s.iz = np.floor(s.Z * D + 1e-4)
        s.shape = U.shape
        s.side = face in 'nsew'


def rgba(rgb, a=255.0):
    return np.dstack([rgb, np.full(rgb.shape[:2], float(a))])


def pick(P, idx):
    return P[np.clip(np.rint(idx), 0, len(P) - 1).astype(int)]


# ---------------------------------------------------------------- painters
def cloth(P, bias=0.5, vgrad=0.3, pleat=0.0, pf=1.6, seed=1, noise=0.8, edge=True):
    def f(c):
        n = hash3(c.ix, c.iy, c.iz, seed)
        if c.face == 'u':
            t = np.full(c.shape, bias + 0.2)
        elif c.face == 'd':
            t = np.full(c.shape, bias - 0.3)
        else:
            t = bias + vgrad * (c.ty - 0.5) + pleat * np.sin(c.S * pf)
            if c.face in 'ew':
                t = t - 0.05
            if c.face == 's':
                t = t - 0.08
        idx = t * (len(P) - 1) + (n - 0.5) * noise
        if edge and c.side:
            idx[0, :] += 0.8
            idx[-1, :] -= 0.8
        return rgba(pick(P, idx))
    return f


def flat(col):
    return lambda c: rgba(np.broadcast_to(col, c.shape + (3,)).copy())


def clear(c):
    return np.zeros(c.shape + (4,))


def comp(base, *decos):
    def f(c):
        img = base(c)
        for d in decos:
            d(c, img)
        return img
    return f


def stars(seed=7, dens=0.012, big=0.15, faces='nsewud'):
    def d(c, img):
        if c.face not in faces:
            return
        h = hash3(c.ix, c.iy, c.iz, seed)
        h2 = hash3(c.ix, c.iy, c.iz, seed + 91)
        m = h < dens
        bigm = m & (h2 < big)
        arm = np.zeros_like(m)
        arm[1:, :] |= bigm[:-1, :]
        arm[:-1, :] |= bigm[1:, :]
        arm[:, 1:] |= bigm[:, :-1]
        arm[:, :-1] |= bigm[:, 1:]
        img[arm, :3] = GOLD[2]
        img[m & (h2 >= 0.6), :3] = hx('#dfe6ff')
        img[m & (h2 < 0.6), :3] = GOLD[3]
        img[bigm, :3] = GOLD[4]
    return d


def trim(rows=3, top=False, P=GOLD, faces='nsew'):
    seq = {1: [3], 2: [3, 1], 3: [3, 2, 1], 4: [4, 3, 2, 1]}[rows]
    def d(c, img):
        if c.face not in faces:
            return
        for i, k in enumerate(seq):
            r = i if top else c.H - rows + i
            if 0 <= r < c.H:
                img[r, :, :3] = P[k]
                g = (c.px[r] % 6 == 2)
                img[r, g, :3] = P[min(k + 1, len(P) - 1)]
    return d


def disc(c, img, cx, cy, r, col, hcoord=None, vcoord=None, inner=None):
    hc = c.X if hcoord is None else hcoord
    vc = c.Y if vcoord is None else vcoord
    d2 = (hc - cx) ** 2 + (vc - cy) ** 2
    m = d2 <= r * r
    if inner is not None:
        m &= ((hc - inner[0]) ** 2 + (vc - inner[1]) ** 2) > inner[2] ** 2
    img[m, :3] = col
    return m


def hair(seed=3, bias=0.62, ring=None, vgrad=0.22):
    def f(c):
        s = c.S
        col = np.floor(s * D + 1e-4)
        hc = hash3(col, col * 0, col * 0, seed)
        seg = hash3(col, np.floor(c.Y * D / 7.0), col * 0, seed + 5)
        strand = 0.5 * np.sin(s * 2.3 + seed) + 0.3 * np.sin(s * 5.9 + 1.7 * seed)
        if c.face == 'u':
            t = bias + 0.12 + 0.1 * strand
        elif c.face == 'd':
            t = np.full(c.shape, bias - 0.35)
        else:
            t = bias + 0.13 * strand + vgrad * (c.ty - 0.5)
            if c.face in 'ew':
                t = t - 0.04
            if c.face == 's':
                t = t - 0.06
        t = t + (hc - 0.5) * 0.16
        t = np.where((hc < 0.12) & (seg > 0.25), t - 0.26, t)
        if ring is not None and c.side:
            zz = ring + 0.25 * np.where(col % 2 == 0, 1, -1)
            t = t + 0.42 * np.exp(-((c.Y - zz) / 0.45) ** 2)
        n = hash3(c.ix, c.iy, c.iz, seed + 11)
        idx = t * (len(HAIR) - 1) + (n - 0.5) * 0.3
        return rgba(pick(HAIR, idx))
    return f


def fringe_depth(col):
    c = col if col < 26 else 51 - col
    base = np.interp(c, [0, 3, 6, 9, 12, 16, 19, 22, 25], [14, 14, 12.3, 9, 6.3, 5, 5.8, 8.6, 11.2])
    tooth = [0, 0.9, 1.7, 0.8][c % 4]
    return int(round(base + tooth))


FR_DEPTH = np.array([fringe_depth(i) for i in range(52)])


def fringe_paint(c):
    img = hair(seed=3, bias=0.66, ring=26.4)(c)
    if c.face == 'n':
        dep = FR_DEPTH[np.clip(c.px, 0, 51)]
        img[c.py >= dep, 3] = 0
        edge = (c.py == dep - 1)
        img[edge, :3] = HAIR[1]
        edge2 = (c.py == dep - 2)
        img[edge2, :3] = np.minimum(img[edge2, :3], HAIR[2])
    elif c.face in 'ew':
        pass
    return img


EYE_L = [
    "....LLLLLL..",
    "..LLLLLLLLL.",
    "LLLLDDDDDLLL",
    ".LLDDDPPDDDL",
    ".LSDDPPPPDDS",
    "..WDMPPPPMDW",
    "..WDMPPPPMDW",
    "..WDMMPPMMDW",
    "..WDMMMMMBDW",
    "..WDBBGGBBD.",
    "...kDBBBBDk.",
    "....kDDDDk..",
    ".....kkkk...",
]
EYE_COL = {
    'L': hx('#17112f'), 'D': hx('#0c3a78'), 'M': hx('#1aa6d6'), 'B': hx('#8ef4ea'),
    'P': hx('#06173a'), 'W': hx('#ffffff'), 'S': hx('#c3cdea'), 'G': hx('#ffe27a'),
    'k': hx('#d99aa0'),
}


def stamp(img, x, y, rows, cols, mirror=False):
    for j, r in enumerate(rows):
        r = r[::-1] if mirror else r
        for i, ch in enumerate(r):
            if ch in cols and 0 <= y + j < img.shape[0] and 0 <= x + i < img.shape[1]:
                img[y + j, x + i, :3] = cols[ch]
                img[y + j, x + i, 3] = 255


def head_paint(c):
    n = hash3(c.ix, c.iy, c.iz, 21)
    if c.face in 'us':
        return hair(seed=3)(c)
    img = rgba(np.broadcast_to(SKIN[3], c.shape + (3,)).copy())
    if c.face == 'd':
        img[..., :3] = SKIN[2]
        return img
    if c.face in 'ew':
        img[c.ty < 0.12, :3] = SKIN[2]
        front = c.Z < -4.6
        img[front, :3] = SKIN[2]
        # ear hint
        m = ((c.Z + 2.6) / 0.7) ** 2 + ((c.Y - 23.6) / 1.0) ** 2 <= 1
        img[m, :3] = SKIN[2]
        m2 = ((c.Z + 2.6) / 0.35) ** 2 + ((c.Y - 23.6) / 0.6) ** 2 <= 1
        img[m2, :3] = SKIN[1]
        return img
    # ------------- face (48 x 44)
    H, W = c.shape
    px, py = c.px, c.py
    # shadow cast by fringe
    dep = FR_DEPTH[np.clip(px + 2, 0, 51)] + 12
    img[py < dep + 1, :3] = SKIN[2]
    img[py < dep - 1, :3] = SKIN[1]
    # side shadow near the locks, chin
    img[(px < 5) | (px > W - 6), :3] = SKIN[2]
    img[py >= H - 1, :3] = SKIN[2]
    # cheeks light
    for cx in (12.5, 34.5):
        m = ((px - cx) / 5.5) ** 2 + ((py - 33) / 3.2) ** 2 <= 1
        img[m, :3] = hx('#ffd3cf')
        m = ((px - cx) / 3.6) ** 2 + ((py - 33) / 1.8) ** 2 <= 1
        img[m, :3] = hx('#ffb9bd')
        for k in (-2, 0, 2):
            for j in (0, 1):
                xx = int(cx + k + (1 - j))
                img[32 + j + 0, xx, :3] = hx('#ff8fa3')
    # eyes
    ex, ey = 9, 18
    stamp(img, ex, ey, EYE_L, EYE_COL)
    stamp(img, W - ex - 12, ey, EYE_L, EYE_COL, mirror=True)
    for x0 in (ex + 3, W - ex - 12 + 1):  # iris left col of each eye
        img[ey + 4:ey + 6, x0 + 1:x0 + 3, :3] = 255        # main highlight
        img[ey + 3, x0 + 1, :3] = hx('#bfeaff')
        img[ey + 8, x0 + 6, :3] = 255                        # small highlight
        img[ey + 7, x0 + 6, :3] = hx('#c9fbff')
    # eyelid crease / lower lash accents
    for (xa, m) in ((ex, False), (W - ex - 12, True)):
        stamp(img, xa, ey - 2, ["...kkkkkkk.."], {'k': SKIN[0]}, mirror=m)
    # nose + mouth
    img[32, 23, :3] = SKIN[1]
    img[32, 24, :3] = SKIN[1]
    mouth = hx('#a3425c')
    for (x, y) in ((20, 36), (21, 37), (22, 37), (23, 36), (24, 36), (25, 37), (26, 37), (27, 36)):
        img[y, x, :3] = mouth
    img[37, 23:25, :3] = hx('#ffffff')   # tiny fang hint
    img[38, 23:25, :3] = SKIN[2]
    return img


# ---- hat brim (shared radial painting in hat-local space)
BRIM = [(-5, 5, 14), (5, 8, 12.5), (8, 10.5, 10.5), (10.5, 12.5, 8), (12.5, 14, 5),
        (-8, -5, 12.5), (-10.5, -8, 10.5), (-12.5, -10.5, 8), (-14, -12.5, 5)]


def in_brim(x, z):
    m = np.zeros(np.shape(x), bool)
    for z0, z1, hw in BRIM:
        m |= (z >= z0) & (z <= z1) & (np.abs(x) <= hw)
    return m


def brim_paint(c):
    n = hash3(c.ix, c.iy, c.iz, 31)
    r = np.sqrt(c.X ** 2 + c.Z ** 2)
    ang = np.arctan2(c.Z, c.X)
    if c.side:
        img = rgba(np.broadcast_to(GOLD[2], c.shape + (3,)).copy())
        img[0, :, :3] = GOLD[3]
        img[-1, :, :3] = GOLD[1]
        return img
    e = 0.45
    edge = ~(in_brim(c.X + e, c.Z) & in_brim(c.X - e, c.Z) & in_brim(c.X, c.Z + e) & in_brim(c.X, c.Z - e))
    e2 = 0.95
    edge2 = ~(in_brim(c.X + e2, c.Z) & in_brim(c.X - e2, c.Z) & in_brim(c.X, c.Z + e2) & in_brim(c.X, c.Z - e2))
    if c.face == 'u':
        t = 0.62 - 0.035 * (r - 7) + 0.07 * np.sin(ang * 9)
        img = rgba(pick(HAT, t * 4 + (n - 0.5) * 0.8))
        stars(41, 0.01, 0.2)(c, img)
        ring = np.abs(r - 9.2) < 0.26
        img[ring & (np.floor(ang * 14) % 2 == 0), :3] = GOLD[1]
    else:
        t = 0.75 - 0.05 * (r - 6) + 0.08 * np.sin(ang * 12)
        img = rgba(pick(LINING, t * 3 + (n - 0.5) * 0.8))
        spoke = (np.abs(np.sin(ang * 6)) < 0.06) & (r > 7.5)
        img[spoke, :3] = LINING[0]
    img[edge2, :3] = GOLD[1]
    img[edge, :3] = GOLD[3] if c.face == 'u' else GOLD[2]
    return img


def crown(seed, bias=0.5):
    base = cloth(HAT, bias=bias, vgrad=0.35, seed=seed)
    def f(c):
        img = base(c)
        if c.side:
            n = hash3(c.ix, c.iy, c.iz, seed + 3)
            w = np.sin((c.S * 1.1 + c.Y * 1.9) + seed)
            img[(w > 0.93), :3] = HAT[4]
            img[(w < -0.95), :3] = HAT[0]
        stars(seed + 50, 0.012, 0.25)(c, img)
        return img
    return f


def band_paint(c):
    img = cloth(TEAL, bias=0.55, vgrad=0.5, seed=77, noise=0.5)(c)
    if c.side:
        img[:1, :, :3] = GOLD[3]
        img[-1:, :, :3] = GOLD[1]
        img[1, :, :3] = GOLD[2]
        m = (c.px % 8 == 4) & (c.py >= 3) & (c.py <= c.H - 4)
        img[m, :3] = TEAL[3]
    return img


def sprite(rows, cols):
    def f(c):
        img = np.zeros(c.shape + (4,))
        if c.face in 'ns':
            stamp(img, 0, 0, rows, cols, mirror=(c.face == 's'))
        return img
    return f


MOON = [
    "......ggGGGg........",
    "....gGGYYYg.........",
    "...gGYYYg...........",
    "..gGYYYg............",
    ".gGYYYg.............",
    ".gGYYg..............",
    "gGYYYg..............",
    "gGYYYg..............",
    "gGYYYg.........w....",
    "gGYYYg........wWw...",
    "gGYYYGg........w....",
    "gGYYYYg.............",
    ".gGYYYGg..........g.",
    ".gGYYYYGg........gG.",
    "..gGYYYYGgg....ggGg.",
    "...gGYYYYYGggggGGg..",
    "....gGGYYYYYYYYGg...",
    "......gGGGGGGGGg....",
    "........gggggg......",
    "....................",
]
MOON_COL = {'g': GOLD[1], 'G': GOLD[2], 'Y': GOLD[3], 'w': hx('#bff6ff'), 'W': hx('#ffffff')}
STAR6 = [
    "..gg..",
    "..GG..",
    "gGYYGg",
    "gGYYGg",
    "..GG..",
    "..gg..",
]


def skirt(tier):
    base = cloth(NAVY, bias=0.42 + 0.03 * tier, vgrad=0.28, pleat=0.11, pf=2.2, seed=10 + tier)
    def f(c):
        img = base(c)
        stars(60 + tier, 0.009, 0.2, faces='nsew')(c, img)
        if c.side:
            trim(3 if tier == 0 else 1)(c, img)
            if tier == 0:   # scalloped embroidery above the hem
                r = c.H - 6
                q = c.px[0] % 8
                img[r, q < 5, :3] = GOLD[1]
                img[r - 1, (q >= 1) & (q <= 3), :3] = GOLD[1]
                img[r - 2, c.px[0] % 8 == 2, :3] = GOLD[2]
        if c.face == 'n':   # centre panel with moon phases
            pm = np.abs(c.X) < 2.5
            n = hash3(c.ix, c.iy, c.iz, 15)
            pc = pick(PANEL, (0.45 + 0.3 * (c.ty - 0.5)) * 3 + (n - 0.5) * 0.8)
            img[pm, :3] = pc[pm]
            img[np.abs(np.abs(c.X) - 2.37) < 0.13, :3] = GOLD[2]
            for (cy, ph) in ((10.5, 0), (7.5, 1), (4.6, 2)):
                if ph == 0:
                    disc(c, img, 0, cy, 0.95, GOLD[3], inner=(0.55, cy + 0.1, 0.85))
                elif ph == 1:
                    disc(c, img, 0, cy, 0.95, GOLD[2])
                    disc(c, img, -0.2, cy + 0.2, 0.5, GOLD[4])
                else:
                    disc(c, img, 0, cy, 0.95, GOLD[3], inner=(-0.55, cy + 0.1, 0.85))
        return img
    return f


def torso_paint(c):
    img = cloth(NAVY, bias=0.5, vgrad=0.2, seed=18)(c)
    if c.side:
        # belt
        img[-5:, :, :3] = GOLD[2]
        img[-5, :, :3] = GOLD[3]
        img[-1, :, :3] = GOLD[0]
    if c.face == 'n':
        cx = c.W // 2
        img[:, cx - 3:cx + 3, :3] = PANEL[1]
        img[:, cx - 4, :3] = GOLD[1]
        img[:, cx + 3, :3] = GOLD[1]
        for r in range(3, c.H - 6, 4):   # lacing
            img[r, cx - 2:cx + 2, :3] = hx('#dfe6ff')
            img[r + 1, cx - 1:cx + 1, :3] = hx('#9aa6dd')
        img[-6:, cx - 3:cx + 3, :3] = GOLD[3]   # buckle
        img[-5:-1, cx - 2:cx + 2, :3] = TEAL[2]
        img[-4:-2, cx - 1:cx + 1, :3] = TEAL[3]
    return img


def cape_paint(c):
    img = cloth(NAVY, bias=0.66, vgrad=0.3, seed=19, pleat=0.07, pf=3.0)(c)
    stars(63, 0.012, 0.2)(c, img)
    if c.side:
        trim(3)(c, img)
        m = (c.px % 6 == 3)
        img[c.H - 4, m[0], :3] = GOLD[2]
    if c.face == 'u':
        r = np.maximum(np.abs(c.X) / 5.5, np.abs(c.Z) / 3.3)
        img[r > 0.9, :3] = NAVY[3]
    return img


def bow_paint(c):
    img = cloth(TEAL, bias=0.6, vgrad=0.4, seed=5, noise=0.5)(c)
    if c.face == 'n':
        cx = c.W / 2
        d = np.abs(c.px + 0.5 - cx)
        pinch = np.abs(c.py + 0.5 - c.H / 2) > (1.0 + d * 0.55)
        img[pinch, 3] = 0
        img[(d < 1.6), :3] = GOLD[3]
        img[(d < 1.6) & (np.abs(c.py + 0.5 - c.H / 2) > 1.5), 3] = 0
        img[(d < 0.6) & (np.abs(c.py + 0.5 - c.H / 2) < 1.2), :3] = GOLD[4]
    else:
        img[..., 3] = 0
    return img


def sleeve(flare=False):
    base = cloth(NAVY, bias=0.55, vgrad=0.3, seed=23, pleat=0.08, pf=4)
    def f(c):
        img = base(c)
        stars(66, 0.01, 0.15, faces='nsew')(c, img)
        if flare:
            trim(3)(c, img)
            if c.face == 'd':
                img[..., :3] = NAVY[1]
                e = (c.px < 3) | (c.py < 3) | (c.px >= c.W - 3) | (c.py >= c.H - 3)
                img[e, :3] = NAVY[2]
                e = (c.px < 1) | (c.py < 1) | (c.px >= c.W - 1) | (c.py >= c.H - 1)
                img[e, :3] = GOLD[1]
        return img
    return f


def skin_paint(c):
    n = hash3(c.ix, c.iy, c.iz, 4)
    t = 0.72 + 0.2 * (c.ty - 0.5) if c.side else (0.8 if c.face == 'u' else 0.45)
    return rgba(pick(SKIN, t * 4 + (n - 0.5) * 0.4))


def gold_paint(seed=2, bias=0.6):
    return cloth(GOLD, bias=bias, vgrad=0.45, seed=seed, noise=0.6)


def wood_paint(c):
    img = cloth(WOOD, bias=0.5, vgrad=0.0, seed=8, noise=1.2, edge=False)(c)
    if c.side:
        yy = np.floor(c.Y * D)
        for y0 in (20, 24, 52, 56, 110, 114):
            img[(yy == y0) | (yy == y0 + 1), :3] = GOLD[2]
            img[(yy == y0 + 1), :3] = GOLD[1]
        img[:, 0, :3] = np.minimum(img[:, 0, :3] + 25, 255)
    return img


def crystal_paint(c):
    n = hash3(c.ix, c.iy, c.iz, 9)
    t = (c.U + (1 - c.V)) / 2
    img = rgba(pick(CRY, t * 3 + (n - 0.5) * 0.6))
    img[0, :, :3] = CRY[3]
    img[:, 0, :3] = CRY[3]
    return img


def cover_paint(c):
    img = cloth(TEAL, bias=0.3, vgrad=0.1, seed=12, noise=0.9, edge=False)(c)
    if c.face in 'ud':
        e = (c.px < 2) | (c.py < 2) | (c.px >= c.W - 2) | (c.py >= c.H - 2)
        img[e, :3] = GOLD[2]
        k = 5
        cm = ((c.px < k) | (c.px >= c.W - k)) & ((c.py < k) | (c.py >= c.H - k))
        img[cm, :3] = GOLD[3]
        cx, cy = c.W / 2 - 0.5, c.H / 2 - 0.5
        d2 = (c.px - cx) ** 2 + (c.py - cy) ** 2
        img[(d2 <= 30) & (d2 > 17), :3] = GOLD[2]
        img[d2 <= 6, :3] = CRY[2]
        img[d2 <= 1.5, :3] = CRY[3]
    else:
        img[..., :3] = GOLD[1]
        img[0, :, :3] = GOLD[3]
    return img


def page_paint(side):
    def f(c):
        n = hash3(c.ix, c.iy, c.iz, 13)
        if c.face != 'u':
            img = rgba(pick(PAGE, 1.4 + (n - 0.5) * 0.5 + np.where(c.py % 2 == 0, 0.8, -0.3)))
            return img
        img = rgba(pick(PAGE, 2.6 + (n - 0.5) * 0.9))
        H, W = c.shape
        # margin shading toward the spine
        sp = c.px if side > 0 else (W - 1 - c.px)
        img[sp < 2, :3] = PAGE[1]
        cx, cy = W / 2 - 0.5, H / 2 - 0.5
        d2 = (c.px - cx) ** 2 + (c.py - cy) ** 2
        # text lines (point-symmetric layout)
        for r in range(3, H - 3, 3):
            if abs(r - cy) < 6.5:
                continue
            line = (c.py == r) & (c.px >= 3) & (c.px < W - 3) & (hash3(c.px, c.py, c.px * 0, 14 + side) > 0.22)
            img[line, :3] = INK
        # sigil
        img[(d2 <= 30) & (d2 > 20), :3] = CRY[1]
        img[(d2 <= 12) & (d2 > 6.5), :3] = INK
        img[d2 <= 2.5, :3] = CRY[2]
        for a in range(4):
            xx = int(round(cx + 4.2 * math.cos(a * math.pi / 2 + 0.785)))
            yy = int(round(cy + 4.2 * math.sin(a * math.pi / 2 + 0.785)))
            img[yy, xx, :3] = CRY[0]
        return img
    return f


def xf(bn, p):
    p = np.array(p, float)
    b = BONES[bn]
    while b:
        pv = np.array(b['pivot'], float)
        p = pv + rotm(*b['rot']) @ (p - pv)
        b = BONES[b['parent']] if b['parent'] else None
    return p


# ---------------------------------------------------------------- build the model
def build(pose=True):
    BONES.clear()
    ORDER.clear()
    bone('root', None, (0, 0, 0))
    bone('body', 'root', (0, 12, 0))

    # --- skirt (three tiers, bell shape)
    prev = 'body'
    for i, (w, d) in enumerate(((9.5, 7.5), (11.5, 9), (13.5, 10.5), (15.5, 12))):
        nm = 'skirt' if i == 0 else 'skirt%d' % (i + 1)
        bone(nm, prev, (0, 12 - 3 * i, 0))
        cube(nm, (-w / 2, 9 - 3 * i, -d / 2), (w, 3, d), skirt(3 - i), faces='nsewud' if i == 3 else 'nsewu')
        prev = nm

    # --- torso
    bone('torso', 'body', (0, 12, 0))
    cube('torso', (-3.5, 12, -2.25), (7, 6, 4.5), torso_paint)
    cube('torso', (-1.5, 17.6, -1.5), (3, 1.6, 3), skin_paint, faces='nsew')
    cube('torso', (-5.5, 15.4, -3.25), (11, 3, 6.5), cape_paint)
    cube('torso', (-2.5, 16.4, -3.7), (5, 2, 0.45), bow_paint, faces='n')

    # --- arms
    for s, nm in ((-1, 'rightArm'), (1, 'leftArm')):
        bone(nm, 'torso', (s * 4.6, 17.4, 0),
             ((-42, 0, 38) if s < 0 else (-62, 0, -14)) if pose else (0, 0, 0))
        cx = s * 5.6
        cube(nm, (cx - 1.5, 13.4, -1.5), (3, 4.6, 3), sleeve())
        cube(nm, (cx - 2.0, 10.4, -2.0), (4, 3.2, 4), sleeve(), faces='nsewu')
        cube(nm, (cx - 2.7, 8.0, -2.7), (5.4, 2.6, 5.4), sleeve(True))
        cube(nm, (cx - 1.25, 5.9, -1.25), (2.5, 2.6, 2.5), skin_paint)

    # --- head
    bone('head', 'torso', (0, 19, 0))
    cube('head', (-6, 19, -5.5), (12, 11, 11), head_paint)
    cube('head', (-6.5, 27, -6), (13, 3.6, 12.6), hair(seed=3, bias=0.66, ring=28.3))
    cube('head', (-6.5, 18, -2), (13, 9, 8.6), hair(seed=3, bias=0.6))
    cube('head', (-6.5, 23.5, -6), (13, 3.5, 0.55), fringe_paint, faces='new')
    for s in (-1, 1):   # side locks, tapered
        x = -7 if s < 0 else 5
        cube('head', (x, 18.5, -6.2), (2, 8.5, 2.2), hair(seed=4 + s, bias=0.66), faces='nsewd')
        cube('head', (x + (0 if s < 0 else 0.6), 16.2, -6.0), (1.4, 2.3, 1.8), hair(seed=4 + s, bias=0.6), faces='nsewd')
        cube('head', (x + (0 if s < 0 else 1.2), 14.8, -5.8), (0.8, 1.4, 1.2), hair(seed=4 + s, bias=0.55), faces='nsewd')

    bone('hairBack', 'head', (0, 18, 5.5), (-7, 0, 0) if pose else (0, 0, 0))
    cube('hairBack', (-6, 10.5, 4.3), (12, 7.5, 2.3), hair(seed=6, bias=0.56), faces='nsewd')
    cube('hairBack', (-5, 8, 4.5), (10, 2.5, 1.9), hair(seed=6, bias=0.52), faces='nsewd')
    cube('hairBack', (-3.5, 6.2, 4.7), (7, 1.8, 1.5), hair(seed=6, bias=0.48), faces='nsewd')

    for s, nm in ((-1, 'tailR'), (1, 'tailL')):   # twin tails
        bone(nm, 'head', (s * 6.6, 21.5, 2.6), (5, 0, s * -7) if pose else (0, 0, 0))
        cx = s * 6.9
        cube(nm, (cx - 1.8, 19.4, 0.8), (3.6, 1.2, 3.6), gold_paint(3))
        cube(nm, (cx - 1.6, 13.6, 1.0), (3.2, 6, 3.2), hair(seed=8 + s, bias=0.6), faces='nsewd')
        bone(nm + '2', nm, (cx, 13.6, 2.6), (3, 0, s * -9) if pose else (0, 0, 0))
        cube(nm + '2', (cx - 1.3, 8.6, 1.3), (2.6, 5, 2.6), hair(seed=9 + s, bias=0.55), faces='nsewd')
        cube(nm + '2', (cx - 0.8, 6, 1.8), (1.6, 2.6, 1.6), hair(seed=9 + s, bias=0.5), faces='nsewd')
        cube(nm + '2', (cx - 0.4, 4.6, 2.2), (0.8, 1.4, 0.8), hair(seed=9 + s, bias=0.45), faces='nsewd')

    # --- hat
    bone('hat', 'head', (0, 28.4, 0), (9, 0, -4) if pose else (0, 0, 0))
    for z0, z1, hw in BRIM:
        cube('hat', (-hw, 28.4, z0), (2 * hw, 1, z1 - z0), brim_paint)
    cube('hat', (-7, 29.4, -7), (14, 3.4, 14), crown(1, 0.42), faces='nsewu')
    cube('hat', (-7, 29.4, -7), (14, 2.2, 14), band_paint, inflate=0.3, faces='nsewu')
    cube('hat', (-2.5, 28.9, -7.9), (5, 5, 0.5), sprite(MOON, MOON_COL), faces='n')
    cube('hat', (-5.75, 32.8, -5.75), (11.5, 3.4, 11.5), crown(2, 0.47), faces='nsewu')
    cube('hat', (-4.5, 36.2, -4.5), (9, 3.3, 9), crown(3, 0.52), faces='nsewu')
    hz = (-10, 0, -20) if pose else (0, 0, 0)
    bone('hat2', 'hat', (0, 39.3, 0), hz)
    cube('hat2', (-3.4, 38.9, -3.4), (6.8, 3.7, 6.8), crown(4, 0.56), faces='nsewu')
    bone('hat3', 'hat2', (0, 42.4, 0), hz)
    cube('hat3', (-2.4, 42.0, -2.4), (4.8, 3.6, 4.8), crown(5, 0.6), faces='nsewu')
    bone('hat4', 'hat3', (0, 45.4, 0), hz)
    cube('hat4', (-1.5, 45.0, -1.5), (3, 3.4, 3), crown(6, 0.64), faces='nsewu')
    bone('hat5', 'hat4', (0, 48.2, 0), hz)
    cube('hat5', (-0.8, 47.9, -0.8), (1.6, 3, 1.6), crown(7, 0.7))
    cube('hat5', (-0.9, 50.6, -0.9), (1.8, 1.8, 1.8), gold_paint(5, 0.7), rot=(0, 0, 45))
    # star charms hanging from the brim
    scol = {'g': GOLD[1], 'G': GOLD[3], 'Y': GOLD[4]}
    for i, (x, z, ln) in enumerate(((-11.2, -8.6, 3.0), (11.2, -8.6, 2.2), (-13.4, 1.5, 2.4), (13.4, 1.5, 3.2))):
        bn = 'charm%d' % i
        bone(bn, 'hat', (x, 28.4, z))
        cube(bn, (x - 0.15, 28.4 - ln, z - 0.15), (0.3, ln, 0.3), flat(GOLD[1]), faces='nsew')
        cube(bn, (x - 0.75, 28.4 - ln - 1.5, z - 0.2), (1.5, 1.5, 0.4), sprite(STAR6, scol), faces='ns')

    # --- staff (crescent moon head, floating crystal)
    hp = xf('rightArm', (-5.6, 7.2, 0)) if pose else np.array([-12.5, 14, -5.0])
    sx_, sy_, sz_ = float(round(hp[0] * 4) / 4), float(round(hp[1] * 4) / 4), float(round(hp[2] * 4) / 4)
    bone('staff', 'root', (sx_, sy_, sz_), (-5, 0, -15) if pose else (0, 0, 0))
    y0s = sy_ - 13
    cube('staff', (sx_ - 0.5, y0s, sz_ - 0.5), (1, 34, 1), wood_paint)
    cube('staff', (sx_ - 0.9, y0s - 0.8, sz_ - 0.9), (1.8, 1.2, 1.8), gold_paint(6))
    cube('staff', (sx_ - 1.1, y0s + 33.6, sz_ - 1.1), (2.2, 1.4, 2.2), gold_paint(6))
    ccx, ccy, R = sx_, y0s + 40.2, 5.2
    icx, icy, r = ccx, ccy + 2.2, 4.4
    def moon_paint(c):
        n = hash3(c.ix, c.iy, c.iz, 44)
        d = np.sqrt((c.X - ccx) ** 2 + (c.Y - ccy) ** 2) / R
        t = 0.25 + 0.6 * d if c.face in 'ns' else (0.8 if c.face == 'u' else 0.45)
        return rgba(pick(GOLD, t * 4 + (n - 0.5) * 0.7))
    step = 0.5
    y = ccy - R
    while y < ccy + R - 1e-6:
        ym = y + step / 2
        xs = np.arange(ccx - R, ccx + R, step) + step / 2
        ins = ((xs - ccx) ** 2 + (ym - ccy) ** 2 <= R * R) & ((xs - icx) ** 2 + (ym - icy) ** 2 > r * r)
        i = 0
        while i < len(xs):
            if ins[i]:
                j = i
                while j < len(xs) and ins[j]:
                    j += 1
                cube('staff', (xs[i] - step / 2, y, sz_ - 0.6), ((j - i) * step, step, 1.2), moon_paint)
                i = j
            else:
                i += 1
        y += step
    bone('crystal', 'staff', (icx, icy + 0.6, sz_))
    cube('crystal', (icx - 1.1, icy - 0.5, sz_ - 1.1), (2.2, 2.2, 2.2), crystal_paint, rot=(35, 0, 45))

    # --- grimoire (floating open book)
    bx, by, bz = 10.5, 17, -9
    bone('grimoire', 'root', (bx, by, bz), (62, 14, 6) if pose else (0, 0, 0))
    cube('grimoire', (bx - 0.6, by - 0.75, bz - 3.6), (1.2, 0.7, 7.2), cover_paint)
    for s, nm in ((1, 'bookL'), (-1, 'bookR')):
        bone(nm, 'grimoire', (bx, by - 0.4, bz), (0, 0, s * -13) if pose else (0, 0, 0))
        x0 = bx if s > 0 else bx - 5.6
        cube(nm, (x0, by - 0.6, bz - 3.6), (5.6, 0.5, 7.2), cover_paint)
        xp = bx + 0.1 if s > 0 else bx - 5.2
        cube(nm, (xp, by - 0.1, bz - 3.3), (5.1, 0.9, 6.6), page_paint(s), faces='nsewu')
    return BONES


# ---------------------------------------------------------------- texture atlas
def bake(tw=512):
    rects = []
    for bn in ORDER:
        for c in BONES[bn]['cubes']:
            for f in c['faces']:
                ctx = Ctx(c, f)
                img = c['paint'](ctx)
                rects.append((c, f, np.clip(img, 0, 255).astype(np.uint8)))
    rects.sort(key=lambda r: (-r[2].shape[0], -r[2].shape[1]))
    x = y = 0
    rowh = 0
    places = []
    for c, f, img in rects:
        h, w = img.shape[:2]
        if x + w + 2 > tw:
            x = 0
            y += rowh
            rowh = 0
        places.append((c, f, img, x + 1, y + 1))
        x += w + 2
        rowh = max(rowh, h + 2)
    th = 1
    while th < y + rowh:
        th *= 2
    tex = np.zeros((th, tw, 4), np.uint8)
    for c, f, img, px, py in places:
        h, w = img.shape[:2]
        pad = np.pad(img, ((1, 1), (1, 1), (0, 0)), mode='edge')
        tex[py - 1:py + h + 1, px - 1:px + w + 1] = pad
        c['uv'][f] = (px, py, w, h)
    return tex


FN = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'u': 'up', 'd': 'down'}


def r3(v):
    return [round(float(a), 4) for a in v]


def geometry(tex, ident='geometry.starnight_witch'):
    th, tw = tex.shape[:2]
    bones = []
    for bn in ORDER:
        b = BONES[bn]
        o = {'name': bn}
        if b['parent']:
            o['parent'] = b['parent']
        o['pivot'] = r3(b['pivot'])
        if any(b['rot']):
            o['rotation'] = r3(b['rot'])
        cs = []
        for c in b['cubes']:
            cc = {'origin': r3(c['o']), 'size': r3(c['s'])}
            if c['rot'] is not None:
                cc['pivot'] = r3(c['pivot'])
                cc['rotation'] = r3(c['rot'])
            if c['inflate']:
                cc['inflate'] = c['inflate']
            cc['uv'] = {FN[f]: {'uv': [u, v], 'uv_size': [w, h]} for f, (u, v, w, h) in c['uv'].items()}
            cs.append(cc)
        if cs:
            o['cubes'] = cs
        bones.append(o)
    return {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': ident, 'texture_width': tw, 'texture_height': th,
                        'visible_bounds_width': 6, 'visible_bounds_height': 5.5,
                        'visible_bounds_offset': [0, 2, 0]},
        'bones': bones}]}


# ---------------------------------------------------------------- software renderer (preview)
def rotm(rx, ry, rz):
    """Bedrock file-space rotation (matches Blockbench: flip x/y angle signs, order ZYX, mirrored X)."""
    ax, ay, az = math.radians(-rx), math.radians(-ry), math.radians(rz)
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    F = np.diag([-1.0, 1, 1])
    return F @ (Rz @ Ry @ Rx) @ F


def quads():
    out = []
    for bn in ORDER:
        chain = []
        b = BONES[bn]
        while b:
            chain.append((np.array(b['pivot'], float), rotm(*b['rot'])))
            b = BONES[b['parent']] if b['parent'] else None
        for c in BONES[bn]['cubes']:
            ctr = np.array(c['o']) + np.array(c['s']) / 2
            scl = 1 + 2 * c['inflate'] / np.maximum(np.array(c['s']), 1e-6)
            for f in c['faces']:
                us = np.array([0., 1, 1, 0])
                vs = np.array([0., 0, 1, 1])
                P = np.stack(face_point(c, f, us, vs), 1)
                P = ctr + (P - ctr) * scl
                cen = ctr.copy()[None]
                pts = np.vstack([P, cen])
                if c['rot'] is not None:
                    pv = np.array(c['pivot'], float)
                    pts = pv + (pts - pv) @ rotm(*c['rot']).T
                for pv, R in chain:
                    pts = pv + (pts - pv) @ R.T
                out.append((pts[:4], pts[4], c['uv'][f]))
    return out


def render(tex, yaw=0, pitch=0, size=(640, 900), center=(0, 25, 0), scale=15.0, ss=2, bg=(58, 40, 34)):
    W, H = size[0] * ss, size[1] * ss
    sc = scale * ss
    col = np.zeros((H, W, 3), np.float32)
    col[:] = bg
    zb = np.full((H, W), 1e9, np.float32)
    ya, pa = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
    Rp = np.array([[1, 0, 0], [0, math.cos(pa), math.sin(pa)], [0, -math.sin(pa), math.cos(pa)]])
    V = Rp @ Ry
    L = np.array([-0.45, 0.75, -0.5])
    L /= np.linalg.norm(L)
    cen = np.array(center, float)
    for P, cc, (u0, v0, w, h) in quads():
        nrm = np.cross(P[1] - P[0], P[3] - P[0])
        ln = np.linalg.norm(nrm)
        if ln < 1e-9:
            continue
        nrm /= ln
        if np.dot(nrm, P.mean(0) - cc) < 0:
            nrm = -nrm
        shade = 0.60 + 0.40 * max(0.0, float(np.dot(nrm, L))) + 0.06 * max(0.0, float(nrm[1]))
        shade = min(shade, 1.0)
        Q = (P - cen) @ V.T
        sx = W / 2 + Q[:, 0] * sc
        sy = H / 2 - Q[:, 1] * sc
        sz = Q[:, 2]
        uvs = np.array([[0, 0], [w, 0], [w, h], [0, h]], float)
        for tri in ((0, 1, 2), (0, 2, 3)):
            ax, ay, bx, by, cx, cy = sx[tri[0]], sy[tri[0]], sx[tri[1]], sy[tri[1]], sx[tri[2]], sy[tri[2]]
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-9:
                continue
            x0 = max(int(math.floor(min(ax, bx, cx))), 0)
            x1 = min(int(math.ceil(max(ax, bx, cx))) + 1, W)
            y0 = max(int(math.floor(min(ay, by, cy))), 0)
            y1 = min(int(math.ceil(max(ay, by, cy))) + 1, H)
            if x0 >= x1 or y0 >= y1:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            l0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
            l1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
            l2 = 1 - l0 - l1
            ins = (l0 >= -1e-5) & (l1 >= -1e-5) & (l2 >= -1e-5)
            if not ins.any():
                continue
            z = l0 * sz[tri[0]] + l1 * sz[tri[1]] + l2 * sz[tri[2]]
            uu = l0 * uvs[tri[0], 0] + l1 * uvs[tri[1], 0] + l2 * uvs[tri[2], 0]
            vv = l0 * uvs[tri[0], 1] + l1 * uvs[tri[1], 1] + l2 * uvs[tri[2], 1]
            ui = np.clip(uu.astype(int), 0, w - 1) + u0
            vi = np.clip(vv.astype(int), 0, h - 1) + v0
            t = tex[vi, ui]
            sub_z = zb[y0:y1, x0:x1]
            ok = ins & (t[..., 3] >= 128) & (z < sub_z)
            sub_z[ok] = z[ok]
            col[y0:y1, x0:x1][ok] = t[..., :3][ok] * shade
    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    if ss > 1:
        img = img.resize(size, Image.LANCZOS)
    return img


def main(out):
    os.makedirs(out, exist_ok=True)
    build(True)
    tex = bake()
    Image.fromarray(tex).save(os.path.join(out, 'starnight_witch.png'))
    with open(os.path.join(out, 'starnight_witch.geo.json'), 'w') as f:
        json.dump(geometry(tex), f, separators=(',', ':'))
    ncubes = sum(len(BONES[b]['cubes']) for b in ORDER)
    print('texture', tex.shape, 'bones', len(ORDER), 'cubes', ncubes)
    views = {
        'front': dict(yaw=0, pitch=0),
        'q34': dict(yaw=-32, pitch=12),
        'q34b': dict(yaw=35, pitch=12),
        'side': dict(yaw=-90, pitch=0),
        'back': dict(yaw=180, pitch=8),
        'low': dict(yaw=-20, pitch=-14),
    }
    ims = []
    for k, v in views.items():
        im = render(tex, size=(560, 860), center=(-2, 26, 0), scale=13.5, **v)
        im.save(os.path.join(out, 'view_%s.png' % k))
        ims.append(im)
    sheet = Image.new('RGB', (560 * 3, 860 * 2))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % 3) * 560, (i // 3) * 860))
    sheet.save(os.path.join(out, 'sheet.png'))
    render(tex, yaw=0, pitch=0, size=(900, 760), center=(0, 24.5, 0), scale=56, bg=(58, 40, 34)).save(os.path.join(out, 'face_front.png'))
    render(tex, yaw=-28, pitch=6, size=(900, 760), center=(0, 24.5, 0), scale=52).save(os.path.join(out, 'face_q.png'))
    render(tex, yaw=-10, pitch=-18, size=(900, 760), center=(0, 24.5, 0), scale=52).save(os.path.join(out, 'face_low.png'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'out')
