#!/usr/bin/env python3
"""Four original boss concepts for a Bedrock boss addon - blocky models + textures + preview cards.

Reuses the cube/texture/bake framework from the witch generator.
Usage: python3 concepts.py <out_dir>
Texture alpha 250 marks emissive (glowing) texels - rendered unshaded in previews.
"""
import math, os, sys, json, warnings
warnings.filterwarnings('ignore')
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'starnight_witch', 'src'))
import gen_witch as g
from gen_witch import hx, pal, hash3, rgba, pick, Ctx

GLOW = 250.0
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'


def B(name, parent=None, pivot=(0, 0, 0), rot=(0, 0, 0)):
    g.bone(name, parent, pivot, rot)


def C(b, o, s, paint, rot=None, pivot=None, inflate=0.0, faces='nsewud'):
    return g.cube(b, o, s, paint, rot=rot, pivot=pivot, inflate=inflate, faces=faces)


def reset():
    g.BONES.clear()
    g.ORDER.clear()


# ================================================================ generic painters
def face_hv(c):
    """continuous 2D texel coords on a face (h right, v up)."""
    if c.face in 'ns':
        h = c.X * g.D
    elif c.face in 'ew':
        h = c.Z * g.D
    else:
        h = c.X * g.D
    v = c.Y * g.D if c.side else c.Z * g.D
    return h, v


def shade_face(c, t):
    if c.face == 'u':
        return t + 0.18
    if c.face == 'd':
        return t - 0.3
    if c.face in 'ew':
        return t - 0.06
    if c.face == 's':
        return t - 0.1
    return t


def stone(P, seed=1, bias=0.5, bw=5, bh=4, vgrad=0.15):
    """irregular cobble/brick pattern."""
    def f(c):
        h, v = face_hv(c)
        row = np.floor(v / bh)
        shift = hash3(row, row * 0 + seed, row * 0, seed) * bw
        col = np.floor((h + shift) / bw)
        cell = hash3(col, row, row * 0 + (ord(c.face)), seed + 3)
        n = hash3(c.ix, c.iy, c.iz, seed + 7)
        t = bias + (cell - 0.5) * 0.35 + (n - 0.5) * 0.12
        if c.side:
            t = t + vgrad * (c.ty - 0.5)
        t = shade_face(c, t)
        img = rgba(pick(P, t * (len(P) - 1)))
        border = (np.floor(v) % bh == 0) | (np.floor(h + shift) % bw == 0)
        img[border, :3] = img[border, :3] * 0.62
        hi = (np.floor(v) % bh == bh - 1) & ~border
        img[hi, :3] = np.minimum(img[hi, :3] * 1.12 + 6, 255)
        return img
    return f


def mossy(base, M, amount=0.35, seed=5, flowers=True):
    def f(c):
        img = base(c)
        n = hash3(c.ix, c.iy, c.iz, seed)
        h, v = face_hv(c)
        colh = hash3(np.floor(h), h * 0, h * 0, seed + 2)
        if c.face == 'u':
            m = np.ones(c.shape, bool)
        elif c.face == 'd':
            m = np.zeros(c.shape, bool)
        else:
            m = c.ty > 1 - (amount + 0.28 * colh + 0.08 * np.sin(h * 0.9))
        t = 0.55 + (n - 0.5) * 0.5
        if c.side:
            t = t - 0.25 * (1 - c.ty)
        t = shade_face(c, t)
        mc = pick(M, t * (len(M) - 1))
        img[m, :3] = mc[m]
        if c.side:   # dark drip edge
            m2 = np.zeros_like(m)
            m2[:-1] = m[:-1] & ~m[1:]
            img[m2, :3] = M[0]
        if flowers and c.face == 'u':
            fl = (hash3(c.ix, c.iy, c.iz, seed + 9) < 0.02)
            k = hash3(c.ix, c.iy, c.iz, seed + 10)
            img[fl & (k < 0.5), :3] = hx('#ffe36e')
            img[fl & (k >= 0.5), :3] = hx('#ff8fc1')
        return img
    return f


def furp(P, seed=3, bias=0.55, vgrad=0.25, spine=None, saddle=None):
    def f(c):
        h, v = face_hv(c)
        col = np.floor(h)
        hc = hash3(col, col * 0 + ord(c.face), col * 0, seed)
        seg = hash3(col, np.floor(v / 5), col * 0, seed + 4)
        strand = 0.4 * np.sin(h * 1.7 + seed) + 0.25 * np.sin(h * 4.3)
        t = bias + 0.05 * strand + (hc - 0.5) * 0.09
        if c.side:
            t = t + vgrad * (c.ty - 0.5)
        if not c.side:
            t = t + 0.1 * np.sin(v * 1.3 + h * 0.5)
        t = shade_face(c, t)
        t = np.where((hc < 0.08) & (seg > 0.4), t - 0.14, t)
        n = hash3(c.ix, c.iy, c.iz, seed + 8)
        img = rgba(pick(P, t * (len(P) - 1) + (n - 0.5) * 0.3))
        if saddle is not None:
            if c.face == 'u':
                m = np.ones(c.shape, bool)
            elif c.side:
                m = c.ty > saddle + 0.08 * np.sin(h * 0.7) + 0.06 * hash3(np.floor(h / 2), h * 0, h * 0, seed)
            else:
                m = np.zeros(c.shape, bool)
            dc = pick(FURD, (t + 0.05) * (len(FURD) - 1) + (n - 0.5) * 0.4)
            img[m, :3] = dc[m]
            if c.side:
                e = np.zeros_like(m)
                e[1:] = m[:-1] & ~m[1:]
                img[e, :3] = FUR[1]
        if spine is not None and c.face == 'u':
            dm = np.abs(c.X) < spine
            img[dm, :3] = img[dm, :3] * 0.72
        return img
    return f


def crystalp(P, seed=9, glow=False):
    def f(c):
        n = hash3(c.ix, c.iy, c.iz, seed)
        t = (c.U * 0.4 + (1 - c.V) * 0.6)
        if c.face in 'ew':
            t = t - 0.15
        img = rgba(pick(P, t * (len(P) - 1) + (n - 0.5) * 0.7), GLOW if glow else 255)
        img[0, :, :3] = P[-1]
        img[:, 0, :3] = P[-1]
        diag = np.abs(c.U - (1 - c.V)) < 0.08
        img[diag, :3] = np.minimum(img[diag, :3] + 40, 255)
        return img
    return f


def emissive(col, noise=0.0, seed=1):
    def f(c):
        base = np.broadcast_to(col, c.shape + (3,)).astype(float)
        if noise:
            n = hash3(c.ix, c.iy, c.iz, seed)
            base = np.clip(base * (1 + (n[..., None] - 0.5) * noise), 0, 255)
        return rgba(base, GLOW)
    return f


def flatp(col, a=255):
    return lambda c: rgba(np.broadcast_to(col, c.shape + (3,)).astype(float), a)


def cracks(img, c, P, scale=1.0, dens=0.11, seed=0, faces='nsewu', halo=True):
    """branching lava/energy veins painted as emissive."""
    if c.face not in faces:
        return
    h, v = face_hv(c)
    h = h * scale
    v = v * scale
    a = np.abs(np.sin(h * 0.33 + 2.1 * np.sin(v * 0.21 + seed) + seed))
    b = np.abs(np.sin(v * 0.29 + 1.7 * np.sin(h * 0.19 + 2 * seed) + 0.5 * seed))
    w = np.minimum(a, b)
    gate = hash3(np.floor(h / 6), np.floor(v / 6), h * 0, seed + 31) > 0.35
    core = (w < dens * 0.45) & gate
    glow = (w < dens) & gate
    if halo:
        img[glow & ~core, :3] = P[0]
        img[glow & ~core, 3] = GLOW
    img[core, :3] = P[1]
    img[core, 3] = GLOW
    hot = core & (hash3(c.ix, c.iy, c.iz, seed + 5) < 0.3)
    img[hot, :3] = P[2]


def edges(img, c, col, w=1, faces='nsew'):
    if c.face not in faces:
        return
    img[:w, :, :3] = col
    img[:, :w, :3] = np.minimum(img[:, :w, :3], col)


def stamp(img, x, y, rows, cols, mirror=False, glow=()):
    for j, r in enumerate(rows):
        r = r[::-1] if mirror else r
        for i, ch in enumerate(r):
            if ch in cols and 0 <= y + j < img.shape[0] and 0 <= x + i < img.shape[1]:
                img[y + j, x + i, :3] = cols[ch]
                img[y + j, x + i, 3] = GLOW if ch in glow else 255


def withf(base, face, fn):
    def f(c):
        img = base(c)
        if c.face in face:
            fn(c, img)
        return img
    return f


def comp(base, *decos):
    def f(c):
        img = base(c)
        for d in decos:
            d(c, img)
        return img
    return f


# ================================================================ 1. Mossheart Colossus
STONE = pal('#2f3534', '#434a47', '#59605b', '#707870', '#8a9288', '#a3ab9f')
MOSS = pal('#1d3a17', '#2c5a1f', '#3f7a29', '#5a9b34', '#7dbd45', '#a6d95e')
JADE = pal('#0b4a3a', '#13806a', '#25c49a', '#7affd0', '#e8fff4')
AMETH = pal('#3a1d5c', '#5b2e8c', '#8a52c4', '#bb8af0', '#eedcff')
VEIN = [hx('#1aa57e'), hx('#5dffc4'), hx('#e6fff5')]


def vine(seed):
    def f(c):
        img = np.zeros(c.shape + (4,))
        if c.face not in 'ns':
            return img
        h = c.px
        hc = hash3(h, h * 0, h * 0, seed)
        length = (0.45 + 0.55 * hash3(np.floor(h / 2), h * 0, h * 0, seed + 1)) * c.H
        strand = (h % 3 != 2) & (c.py < length)
        img[strand, :3] = pick(MOSS, 1.5 + hc[strand] * 2)
        img[strand, 3] = 255
        leaf = strand & (hash3(c.px, c.py, c.px * 0, seed + 2) < 0.18)
        img[leaf, :3] = MOSS[4]
        tip = (c.py >= length - 1) & (c.py < length) & (h % 3 != 2)
        img[tip & (hc < 0.3), :3] = hx('#ff9fd0')
        return img
    return f


def golem_eyes(c, img):
    W, H = c.W, c.H
    eye = ["BBBBBBBBB.", "BdGGWWGGdB", ".BdGWWGdB.", "..BdGGdB..", "...BBBB..."]
    cols = {'B': hx('#141816'), 'G': VEIN[1], 'W': VEIN[2], 'd': VEIN[0]}
    stamp(img, 6, 12, eye, cols, glow='GWd')
    stamp(img, W - 16, 12, eye, cols, mirror=True, glow='GWd')
    # cracked jaw line
    img[H - 9, 12:W - 12, :3] = hx('#1c211f')
    for x in range(14, W - 14, 4):
        img[H - 8:H - 6, x, :3] = hx('#1c211f')


def core_paint(c):
    img = crystalp(JADE, 21, glow=True)(c)
    if c.face == 'n':
        H, W = c.shape
        frame = (c.px < 3) | (c.px >= W - 3) | (c.py < 3) | (c.py >= H - 3)
        img[frame, :3] = STONE[1]
        img[frame, 3] = 255
        cx, cy = W / 2 - 0.5, H / 2 - 0.5
        d = np.abs(c.px - cx) + np.abs(c.py - cy)
        img[(d < 9) & ~frame, :3] = JADE[3]
        img[(d < 5) & ~frame, :3] = JADE[4]
    return img


def golem_torso(c):
    img = mossy(stone(STONE, 2, 0.5), MOSS, 0.3, 7)(c)
    if c.face == 'n':   # energy veins radiate from the core
        cx, cy = 0, 30.5
        ang = np.arctan2(c.Y - cy, c.X - cx)
        r = np.hypot(c.X - cx, c.Y - cy)
        k = np.abs(np.sin(ang * 4 + 0.35 * np.sin(r * 0.9))) < 0.06 + 0.08 / (1 + r * 0.3)
        k &= (r < 11) & (r > 4)
        img[k, :3] = VEIN[0]
        img[k, 3] = GLOW
        k2 = k & (r < 8)
        img[k2, :3] = VEIN[1]
    return img


def build_golem():
    reset()
    st = stone(STONE, 1, 0.5)
    ms = lambda a=0.35, s=5: mossy(stone(STONE, s, 0.5), MOSS, a, s)
    B('root')
    for s, nm in ((-1, 'legR'), (1, 'legL')):
        B(nm, 'root', (s * 7, 16, 0))
        C(nm, (s * 7 - 4, 3, -4), (8, 13, 8), stone(STONE, 3, 0.45))
        C(nm, (s * 7 - 5.5, 0, -6.5), (11, 4, 11), ms(0.25, 4))
    B('body', 'root', (0, 16, 0))
    C('body', (-11, 14, -6.5), (22, 7, 13), stone(STONE, 6, 0.42))
    B('torso', 'body', (0, 20, 2), (14, 0, 0))
    C('torso', (-14, 20, -8), (28, 18, 16), golem_torso)
    C('torso', (-11, 37, -5), (22, 6, 13), ms(0.6, 8))
    C('torso', (-4.5, 26, -8.8), (9, 9, 1), core_paint, faces='nsewu')
    for i, (x, z, hgt, rx, rz) in enumerate(((-6, -1, 9, -18, 14), (-1.5, 2, 12, -26, -4), (4, -1, 8, -14, -18),
                                              (8.5, 3, 6, -30, -26), (-9.5, 4, 6, -32, 28))):
        C('torso', (x - 1.5, 41, z - 1.5), (3, hgt, 3), crystalp(JADE, 30 + i, glow=True), rot=(rx, 0, rz),
          pivot=(x, 41, z))
    for i, x in enumerate((-13.5, -8, 6, 11.5)):
        C('torso', (x, 27 - 2 * (i % 2), -8.4), (3, 11, 0), vine(40 + i), faces='ns')
    B('head', 'torso', (0, 35, -6), (-10, 0, 0))
    C('head', (-5.5, 32, -14.5), (11, 9, 9), withf(stone(STONE, 11, 0.55), 'n', golem_eyes))
    C('head', (-6.5, 39.5, -15.5), (13, 3, 10), ms(0.7, 12))
    for s, nm in ((-1, 'armR'), (1, 'armL')):
        B(nm, 'torso', (s * 16, 34, 0), (-6, 0, s * -4))
        C(nm, (s * 19 - 6, 28, -6.5), (12, 12, 13), ms(0.55, 13 + s))
        C(nm, (s * 21 - 2.5, 31, -1), (2.5, 7, 2.5), crystalp(AMETH, 50 + s), rot=(-20, 0, s * -25),
          pivot=(s * 21, 39, 0))
        C(nm, (s * 18.5 - 4, 17, -4), (8, 11, 8), stone(STONE, 15 + s, 0.48))
        B(nm + 'F', nm, (s * 18.5, 18, 0), (-22, 0, 0))
        C(nm + 'F', (s * 19 - 5.5, 6, -6), (11, 13, 12), ms(0.25, 17 + s))
        C(nm + 'F', (s * 19 - 6.5, -1, -7.5), (13, 8, 14), stone(STONE, 19 + s, 0.42))
        for k in range(4):   # knuckles
            C(nm + 'F', (s * 19 - 6 + k * 3.2, -2, -8.5), (2.6, 4, 2.6), stone(STONE, 60 + k, 0.55))
        C(nm + 'F', (s * 19 - 5.6 + 4, 9, -6.4), (3, 9, 0), vine(70 + s), faces='ns')
    return dict(center=(0, 24, -2), scale=7.6)


# ================================================================ 2. Frostfang
FUR = pal('#4d6688', '#7d97bb', '#adc4e0', '#d5e4f4', '#f1f7ff', '#ffffff')
FURD = pal('#232f4c', '#34466b', '#4b628e', '#6a83ad', '#8ea6cc')
ICE = pal('#1b5d9c', '#2f8fd0', '#62c2f0', '#a9e8ff', '#f0fdff')


def wolf_head(c):
    img = furp(FUR, 31, 0.62, saddle=0.78)(c)
    if c.face == 'u':
        dm = np.abs(c.X) < 2
        img[dm, :3] = pick(FURD, 1 + hash3(c.ix, c.iy, c.iz, 3)[dm])
    if c.face == 'n':
        W, H = c.W, c.H
        eye = ["KK.......",
               ".KKKK....",
               "..KIIWKK.",
               "..KCIIIKK",
               "...KKKKK."]
        cols = {'K': hx('#141a2e'), 'I': ICE[2], 'C': ICE[4], 'W': hx('#ffffff')}
        stamp(img, 2, 17, eye, cols, glow='ICW')
        stamp(img, W - 11, 17, eye, cols, mirror=True, glow='ICW')
        # frost markings
        for (x, y) in ((6, 24), (7, 25), (8, 26), (W - 7, 24), (W - 8, 25), (W - 9, 26)):
            img[y, x, :3] = ICE[3]
            img[y, x, 3] = GLOW
        img[6:14, W // 2 - 1:W // 2 + 1, :3] = FURD[2]
    return img


def snout(c):
    img = furp(FUR, 33, 0.66)(c)
    if c.face == 'u':
        img[:, c.W // 2 - 1:c.W // 2 + 1, :3] = FUR[2]
    if c.face == 'n':
        W = c.W
        img[0:5, W // 2 - 6:W // 2 + 6, :3] = hx('#1b2033')
        img[0, W // 2 - 5:W // 2 + 5, :3] = hx('#59627e')
        img[2:4, W // 2 - 4:W // 2 - 2, :3] = hx('#05070d')
        img[2:4, W // 2 + 2:W // 2 + 4, :3] = hx('#05070d')
        img[5:, W // 2, :3] = FUR[1]
    return img


def jaw(c):
    img = furp(FUR, 35, 0.7)(c)
    if c.face == 'u':
        img[..., :3] = hx('#5a1f35')
    if c.face == 'n':
        img[:2, :, :3] = hx('#f4f8ff')
        img[:2, ::3, :3] = hx('#5a1f35')
    return img


def fang(c):
    img = rgba(pick(pal('#b9c7d8', '#e3ecf7', '#ffffff'), 1 + (1 - c.V) + c.U * 0.4))
    return img


def build_wolf():
    reset()
    fur = lambda s, b=0.55, sd=0.62: furp(FUR, s, b, saddle=sd)
    B('root')
    B('body', 'root', (0, 20, 0), (-4, 0, 0))
    C('body', (-7.5, 14, -8), (15, 14, 20), fur(1, 0.55))
    C('body', (-9, 13, -16), (18, 18, 10), fur(2, 0.62))
    C('body', (-11.5, 16, -19), (23, 17, 8), furp(FUR, 3, 0.72, saddle=0.8), inflate=0.2)
    C('body', (-6.5, 14, 11), (13, 12, 9), fur(4, 0.5))
    # ice spikes along the spine
    for i, (z, hgt, rx, rz) in enumerate(((-15, 11, -18, 0), (-10, 9, -26, 12), (-10, 8, -26, -14), (-4, 9, -30, 0),
                                          (2, 7, -36, 8), (8, 6, -40, -6), (13, 5, -44, 0))):
        x = 0 if rz == 0 else (2.2 if rz < 0 else -2.2)
        top = 30 if z < -6 else 27.5
        C('body', (x - 1.4, top, z - 1.4), (2.8, hgt, 2.8), crystalp(ICE, 80 + i, glow=True), rot=(rx, 45, rz),
          pivot=(x, top, z))
    for s in (-1, 1):   # shoulder ice armour
        C('body', (s * 9.5 - 2.5, 24, -15), (5, 5, 7), crystalp(ICE, 90 + s), rot=(0, 0, s * -18))
        C('body', (s * 10.6 - 1, 27, -13), (2, 6, 2), crystalp(ICE, 92 + s, glow=True), rot=(-15, 0, s * -35),
          pivot=(s * 10.6, 27, -12))
    for s, nm in ((-1, 'legFR'), (1, 'legFL')):
        B(nm, 'body', (s * 5, 18, -12), (-4, 0, 0))
        C(nm, (s * 5 - 3, 3, -15), (6, 15, 6), fur(10 + s, 0.58, 0.85))
        C(nm, (s * 5 - 3.5, 0, -17.5), (7, 3.5, 8), furp(FURD, 12 + s, 0.4))
        for k in range(3):
            C(nm, (s * 5 - 3 + k * 2.3, 0, -18.3), (1.3, 1.2, 1.3), fang)
    for s, nm in ((-1, 'legBR'), (1, 'legBL')):
        B(nm, 'body', (s * 5, 20, 14), (6, 0, 0))
        C(nm, (s * 5 - 3.5, 9, 10), (7, 11, 9), fur(14 + s, 0.5, 0.6))
        C(nm, (s * 5 - 2.5, 2, 14), (5, 8, 5), fur(16 + s, 0.5, 0.9))
        C(nm, (s * 5 - 3.5, 0, 11.5), (7, 3, 8), furp(FURD, 18 + s, 0.4))
    B('tail', 'body', (0, 25, 19), (-38, 0, 0))
    C('tail', (-3, 22, 19), (6, 6, 9), furp(FUR, 20, 0.6, saddle=0.45))
    B('tail2', 'tail', (0, 25, 27), (-20, 0, 0))
    C('tail2', (-2.5, 22.5, 27), (5, 5, 8), furp(FUR, 21, 0.68, saddle=0.5))
    C('tail2', (-1.2, 23.8, 34), (2.4, 2.4, 6), crystalp(ICE, 22, glow=True), rot=(0, 0, 45))
    B('head', 'body', (0, 28, -18), (8, 0, 0))
    C('head', (-6.5, 23, -29), (13, 12, 12), wolf_head)
    C('head', (-8.5, 22, -24), (17, 10, 6), furp(FUR, 37, 0.75), faces='nsewd')   # cheek ruff
    C('head', (-3.5, 23.5, -36), (7, 6, 8), snout)
    B('jaw', 'head', (0, 23.5, -29), (14, 0, 0))
    C('jaw', (-3.2, 21.5, -35.5), (6.4, 2.5, 7), jaw)
    for s in (-1, 1):
        C('head', (s * 2.3 - 0.5, 21.2, -35.6), (1, 2.6, 1), fang)
        C('jaw', (s * 2.2 - 0.5, 23.5, -35), (1, 1.6, 1), fang)
        C('head', (s * 4 - 2, 34, -25), (4, 6, 3), furp(FUR, 40 + s, 0.6), rot=(-10, 0, s * -14))
        C('head', (s * 4 - 1, 35, -25.4), (2, 4, 0.5), flatp(FURD[1]), rot=(-10, 0, s * -14),
          pivot=(s * 4, 37, -23.5))
        C('head', (s * 4.6 - 0.8, 33, -22), (1.6, 7, 1.6), crystalp(ICE, 44 + s, glow=True), rot=(-35, 0, s * -30),
          pivot=(s * 4.6, 33, -21))
    return dict(center=(0, 20, -6), scale=7.6)


# ================================================================ 3. Cinderforge Knight
OBS = pal('#141017', '#211b26', '#2f2836', '#423a4a', '#5a5163', '#7b7186')
LAVA = [hx('#b3270c'), hx('#ff7a1a'), hx('#ffe36b')]
CLOTH = pal('#2a0a0c', '#43101a', '#651a22', '#87262a')
BRASS = pal('#4a2a12', '#7e4b1f', '#b8752e', '#e3a548', '#ffd27d')


def armor(seed, bias=0.5, crack=True, dens=0.11):
    base = stone(OBS, seed, bias, bw=8, bh=6, vgrad=0.2)
    def f(c):
        img = base(c)
        if c.side:
            img[0, :, :3] = OBS[5]
            img[1, :, :3] = OBS[4]
            img[-1, :, :3] = OBS[0]
        if crack:
            cracks(img, c, LAVA, 1.0, dens, seed)
        return img
    return f


def helm_paint(c):
    img = armor(51, 0.55, dens=0.07)(c)
    if c.face == 'n':
        W, H = c.W, c.H
        img[16:22, 4:W - 4, :3] = hx('#0a080c')
        img[16:22, 4:W - 4, 3] = 255
        img[18:20, 7:W // 2 - 3, :3] = LAVA[2]
        img[18:20, W // 2 + 3:W - 7, :3] = LAVA[2]
        img[17, 7:W // 2 - 3, :3] = LAVA[1]
        img[17, W // 2 + 3:W - 7, :3] = LAVA[1]
        img[17:20, 7:W // 2 - 3, 3] = GLOW
        img[17:20, W // 2 + 3:W - 7, 3] = GLOW
        img[22:H - 2, W // 2 - 2:W // 2 + 2, :3] = OBS[4]
        for y in range(24, H - 3, 3):
            img[y, 8:W // 2 - 4, :3] = OBS[0]
            img[y, W // 2 + 4:W - 8, :3] = OBS[0]
    return img


def chest_paint(c):
    img = armor(52, 0.5)(c)
    if c.face == 'n':
        W, H = c.W, c.H
        x0, x1, y0, y1 = W // 2 - 12, W // 2 + 12, 12, 34
        img[y0:y1, x0:x1, :3] = BRASS[1]
        img[y0 + 2:y1 - 2, x0 + 2:x1 - 2, :3] = hx('#120806')
        for x in range(x0 + 4, x1 - 3, 4):
            img[y0 + 2:y1 - 2, x:x + 2, :3] = LAVA[1]
            img[y0 + 2:y1 - 2, x:x + 2, 3] = GLOW
            img[y0 + 9:y1 - 4, x:x + 2, :3] = LAVA[2]
        img[y0, x0:x1, :3] = BRASS[3]
        img[y1 - 1, x0:x1, :3] = BRASS[0]
    return img


def cape(c):
    n = hash3(c.ix, c.iy, c.iz, 61)
    t = 0.55 + 0.25 * (c.ty - 0.5) + 0.12 * np.sin(c.S * 2.4)
    img = rgba(pick(CLOTH, t * 3 + (n - 0.5) * 0.7))
    if c.face in 'ns':
        tear = c.py >= c.H - (2 + 6 * hash3(np.floor(c.px / 3), c.px * 0, c.px * 0, 62))
        img[tear, 3] = 0
        e = np.zeros_like(tear)
        e[:-1] = ~tear[:-1] & tear[1:]
        img[e, :3] = LAVA[1]
        img[e, 3] = GLOW
    return img


def flame_paint(c):
    img = np.zeros(c.shape + (4,))
    if c.face not in 'ewns':
        return img
    H, W = c.shape
    xs = (c.px + 0.5) / W
    hgt = 0.35 + 0.65 * np.abs(np.sin(xs * 9.5 + 1)) * (1 - np.abs(xs - 0.5) * 1.4)
    m = (1 - (c.py + 0.5) / H) < hgt
    img[m, :3] = LAVA[0]
    inner = (1 - (c.py + 0.5) / H) < hgt * 0.7
    img[inner, :3] = LAVA[1]
    core = (1 - (c.py + 0.5) / H) < hgt * 0.35
    img[core, :3] = LAVA[2]
    img[m, 3] = GLOW
    return img


def build_knight():
    reset()
    B('root')
    for s, nm in ((-1, 'legR'), (1, 'legL')):
        B(nm, 'root', (s * 4, 22, 0), (0, 0, s * -3))
        C(nm, (s * 4 - 3.5, 0, -4.5), (7, 5, 8.5), armor(1 + s, 0.45))
        C(nm, (s * 4 - 2.75, 5, -2.75), (5.5, 9, 5.5), armor(3 + s, 0.5))
        C(nm, (s * 4 - 3.25, 11, -3.75), (6.5, 4, 3), armor(5 + s, 0.62), rot=(-10, 0, 0))
        C(nm, (s * 4 - 3.25, 14, -3.25), (6.5, 8, 6.5), armor(7 + s, 0.48))
    B('body', 'root', (0, 22, 0))
    C('body', (-8.5, 17, -5.5), (17, 7, 11), armor(9, 0.42), faces='nsewu')
    for i, x in enumerate((-8.5, -2.5, 3.5)):
        C('body', (x, 15, -6.2), (5, 7, 1), armor(10 + i, 0.6, dens=0.08), rot=(-8, 0, 0))
    B('torso', 'body', (0, 24, 0), (4, 0, 0))
    C('torso', (-8.5, 24, -5.5), (17, 14, 11), chest_paint)
    C('torso', (-5, 37, -4), (10, 2.5, 8), armor(13, 0.4))
    C('torso', (-8, 15, 5.4), (16, 23, 0), cape, faces='ns', rot=(10, 0, 0), pivot=(0, 38, 5.4))
    B('head', 'torso', (0, 38, 0))
    C('head', (-5.5, 38.5, -6), (11, 11, 11), helm_paint)
    C('head', (-1, 49.5, -6.5), (2, 2, 12), armor(14, 0.65, crack=False))
    C('head', (-0.1, 50, -5), (0.2, 7, 10), flame_paint, faces='ew')
    for s in (-1, 1):
        B('horn' + str(s), 'head', (s * 5.5, 46, -1), (0, 0, s * -55))
        C('horn' + str(s), (s * 5.5 - 1.5, 46, -2.5), (3, 6, 3), armor(15 + s, 0.6, crack=False))
        B('hornT' + str(s), 'horn' + str(s), (s * 5.5, 52, -1), (0, 0, s * 50))
        C('hornT' + str(s), (s * 5.5 - 1, 52, -2), (2, 5, 2), armor(17 + s, 0.75, crack=False))
        C('hornT' + str(s), (s * 5.5 - 0.6, 56.5, -1.6), (1.2, 2.5, 1.2), emissive(LAVA[2]))
    for s, nm in ((-1, 'armR'), (1, 'armL')):
        B(nm, 'torso', (s * 10, 35, 0), ((-30, 0, 8) if s < 0 else (-8, 0, -10)))
        C(nm, (s * 12 - 6, 32, -7), (12, 8, 14), armor(20 + s, 0.55), rot=(0, 0, s * -10))
        for k in range(2):
            C(nm, (s * (13 + k * 3) - 1, 39.5 - k, -4 + k * 4), (2, 5 - k, 2), armor(22 + k, 0.7, crack=False),
              rot=(0, 0, s * -25))
        C(nm, (s * 11.5 - 3, 25, -3), (6, 9, 6), armor(24 + s, 0.48))
        C(nm, (s * 11.5 - 3.75, 16, -3.75), (7.5, 9, 7.5), armor(26 + s, 0.52))
        C(nm, (s * 11.5 - 4.25, 20, -4.25), (8.5, 2.5, 8.5), flatp(BRASS[2]))
    # war hammer in the right hand, head resting low on the ground side
    hp = g.xf('armR', (-11.5, 18, 0))
    B('hammer', 'root', tuple(float(v) for v in hp), (-12, 0, 32))
    hx_, hy_, hz_ = (float(v) for v in hp)
    C('hammer', (hx_ - 1, hy_ - 22, hz_ - 1), (2, 36, 2), stone(pal('#2a1c14', '#3d2a1c', '#56402b'), 70, 0.5, 2, 3))
    C('hammer', (hx_ - 1.5, hy_ - 1, hz_ - 1.5), (3, 3, 3), flatp(BRASS[2]))
    C('hammer', (hx_ - 7, hy_ - 32, hz_ - 5), (14, 10, 10), armor(71, 0.55, dens=0.14))
    C('hammer', (hx_ - 7.5, hy_ - 29, hz_ - 5.5), (15, 1.5, 11), flatp(BRASS[2]))
    C('hammer', (hx_ - 7.5, hy_ - 25.5, hz_ - 5.5), (15, 1.5, 11), flatp(BRASS[2]))
    C('hammer', (hx_ - 1.5, hy_ - 23, hz_ - 1.5), (3, 2, 3), flatp(BRASS[3]))
    return dict(center=(-3, 27, 0), scale=7.0)


# ================================================================ 4. Abyssal Lantern Angler
ABY = pal('#090a1c', '#121530', '#1d2148', '#2b3163', '#3d4682', '#5762a6')
BELLY = pal('#2b2650', '#3f3a73', '#5a5596', '#7a76b8')
BIO = [hx('#14b7c7'), hx('#6ff6ff'), hx('#ffffff')]
GUM = pal('#3d0a1f', '#64122f', '#8f2041', '#c03a57')
LURE = [hx('#ffb93d'), hx('#fff07a'), hx('#ffffff')]


def aby_skin(seed, bias=0.5, spots=0.014, belly=True):
    def f(c):
        n = hash3(c.ix, c.iy, c.iz, seed)
        t = bias + 0.25 * ((c.ty - 0.5) if c.side else 0) + (n - 0.5) * 0.25
        h, v = face_hv(c)
        t = t + 0.06 * np.sin(h * 0.8 + v * 0.5)
        t = shade_face(c, t)
        img = rgba(pick(ABY, t * (len(ABY) - 1)))
        if belly:
            bm = (c.face == 'd') | (c.side & (c.ty < 0.28))
            bc = pick(BELLY, 1.5 + (n - 0.5) * 1.2)
            img[bm, :3] = bc[bm]
        # scales
        sc = ((np.floor(h) + np.floor(v / 3) * 2) % 6 == 0) & (np.floor(v) % 3 == 0)
        img[sc, :3] = img[sc, :3] * 0.7
        sp = hash3(c.ix, c.iy, c.iz, seed + 40) < spots
        img[sp, :3] = BIO[1]
        img[sp, 3] = GLOW
        lines = c.side & (np.abs(c.ty - 0.55) < 0.02) & (np.floor(h) % 3 != 0)
        img[lines, :3] = BIO[0]
        img[lines, 3] = GLOW
        return img
    return f


def mouth_top(c):   # head underside = roof of mouth
    img = aby_skin(81)(c)
    if c.face == 'd':
        n = hash3(c.ix, c.iy, c.iz, 82)
        img[..., :3] = pick(GUM, 1.4 + (n - 0.5) + 0.8 * c.V)
        img[..., 3] = 255
    return img


def jaw_paint(c):
    img = aby_skin(83, 0.42)(c)
    if c.face == 'u':
        n = hash3(c.ix, c.iy, c.iz, 84)
        img[..., :3] = pick(GUM, 1.6 + (n - 0.5) + 0.6 * (1 - c.V))
        img[..., 3] = 255
        tongue = (np.abs(c.U - 0.5) < 0.18) & (c.V > 0.25)
        img[tongue, :3] = GUM[3]
    return img


def tooth(c):
    return rgba(pick(pal('#a9a6b8', '#d9d6e6', '#f6f3ff', '#ffffff'), 1 + 1.6 * (1 - c.V) + c.U * 0.3))


def fin(seed, kind='tail', side=1):
    """translucent-looking fan fins. kind: tail (root min-z, spread y), dorsal (root min-y, sweep z),
    pect (root near body on x, spread z)."""
    def f(c):
        img = np.zeros(c.shape + (4,))
        (x0, y0, z0), (sx, sy, sz) = c.c['o'], c.c['s']
        if kind == 'tail':
            L = (c.Z - z0) / sz
            Wd = (c.Y - y0) / sy
            inside = np.abs(Wd - 0.5) * 2 < 0.25 + 0.75 * L
            inside &= L < 0.9 + 0.1 * np.abs(np.sin((Wd - 0.5) * 9))
            inside &= ~((L > 0.55) & (np.abs(Wd - 0.5) < 0.42 * (L - 0.55) / 0.45))   # forked tail
        elif kind == 'dorsal':
            L = (c.Y - y0) / sy
            Wd = (c.Z - z0) / sz
            inside = L < (1 - Wd * 0.85) * (0.92 + 0.08 * np.sin(Wd * 25))
        else:
            L = np.abs(c.X - (x0 if side > 0 else x0 + sx)) / sx
            Wd = (c.Z - z0) / sz
            inside = np.abs(Wd - 0.3) < 0.18 + 0.5 * L
            inside &= L < 0.88 + 0.12 * np.abs(np.sin(Wd * 12))
        ray = np.abs(np.sin(Wd * (26 if kind != 'pect' else 18) + seed)) < 0.3
        n = hash3(c.ix, c.iy, c.iz, seed)
        memb = pick(ABY, 3.2 + 0.8 * L + (n - 0.5) * 0.6)
        img[inside, :3] = memb[inside]
        img[inside & ray, :3] = ABY[1]
        img[inside, 3] = 255
        e = inside.copy()
        e[1:-1, 1:-1] = inside[1:-1, 1:-1] & ~(inside[:-2, 1:-1] & inside[2:, 1:-1] & inside[1:-1, :-2] & inside[1:-1, 2:])
        tip = e & (L > 0.35)
        img[tip, :3] = BIO[1]
        img[tip, 3] = GLOW
        spots = inside & (hash3(c.ix, c.iy, c.iz, seed + 3) < 0.02)
        img[spots, :3] = BIO[0]
        img[spots, 3] = GLOW
        return img
    return f


def eye_paint(c):
    img = emissive(hx('#e9fdff'))(c)
    if c.face in 'ew':
        H, W = c.shape
        cx, cy = W / 2 - 0.5, H / 2 - 0.5
        d = np.hypot(c.px - cx, c.py - cy)
        img[d < W * 0.32, :3] = BIO[0]
        img[d < W * 0.16, :3] = hx('#03121c')
        img[(c.px == int(cx) - 1) & (c.py == int(cy) - 1), :3] = 255
    return img


def build_angler():
    reset()
    B('root')
    B('body', 'root', (0, 26, 0), (-6, 0, 0))
    C('body', (-11, 21, -14), (22, 16, 18), mouth_top)
    C('body', (-11.5, 30, -15), (23, 7, 4), aby_skin(85, 0.55), faces='nsewu')   # brow ridge
    C('body', (-8.5, 21, 4), (17, 14, 9), aby_skin(86, 0.5))
    C('body', (-6, 23, 13), (12, 10, 8), aby_skin(87, 0.5))
    C('body', (-3.5, 25, 21), (7, 6, 6), aby_skin(88, 0.5))
    C('body', (0, 15, 25), (0, 26, 14), fin(1, 'tail'), faces='ew')   # tail fin
    C('body', (0, 34, 2), (0, 9, 20), fin(2, 'dorsal'), faces='ew', rot=(-6, 0, 0), pivot=(0, 34, 2))   # dorsal fin
    for s in (-1, 1):
        C('body', (s * (11.4 if s > 0 else 11.4) - 1.5 * (s < 0) - 0 * s, 30, -9) if False else
          ((11.0 if s > 0 else -12.5), 29.5, -10.5), (1.5, 3.5, 3.5), eye_paint)
        C('body', ((s * 8.5) if s > 0 else -8.5 - 11, 23, 2), (11, 0, 10), fin(3 + s, 'pect', s), faces='ud',
          rot=(0, s * 20, s * -35), pivot=(s * 8.5, 23, 6))
        for k in range(6):   # side spines
            C('body', (s * 11 - 0.5 + s * 0.3, 33 - k * 2.2, -4 + k * 1.2), (1, 1, 3), tooth, rot=(0, s * 30, 0))
    # upper teeth (hang down from the roof edge)
    for i, x in enumerate(np.linspace(-9.5, 9.5, 8)):
        L = 5.5 if i in (1, 6) else (3.5 if i % 2 else 4.5)
        C('body', (x - 0.7, 21 - L, -13.6), (1.4, L, 1.4), tooth, rot=(0, 0, (i - 3.5) * 3))
    for i, z in enumerate((-10, -6, -2)):
        for s in (-1, 1):
            C('body', (s * 10 - 0.7, 18, z), (1.4, 3, 1.4), tooth)
    B('jaw', 'body', (0, 21, 2), (24, 0, 0))
    C('jaw', (-12, 15, -17), (24, 6, 19), jaw_paint)
    for i, x in enumerate(np.linspace(-10.5, 10.5, 9)):
        L = 7 if i in (0, 8) else (4.5 if i % 2 else 3.5)
        C('jaw', (x - 0.75, 21, -16.6), (1.5, L, 1.5), tooth, rot=(0, 0, (i - 4) * -4))
    # lure
    B('lure', 'body', (0, 37, -8), (22, 0, 0))
    C('lure', (-0.6, 37, -8.6), (1.2, 10, 1.2), aby_skin(90, 0.6, 0, belly=False))
    B('lure2', 'lure', (0, 47, -8), (48, 0, 0))
    C('lure2', (-0.55, 47, -8.55), (1.1, 9, 1.1), aby_skin(91, 0.6, 0, belly=False))
    B('lure3', 'lure2', (0, 56, -8), (62, 0, 0))
    C('lure3', (-0.5, 56, -8.5), (1, 6, 1), aby_skin(92, 0.6, 0, belly=False))
    C('lure3', (-2.5, 60, -10.5), (5, 5, 5), crystalp(np.array(LURE + [hx('#ffffff'), hx('#ffffff')]), 93,
                                                         glow=True))
    C('lure3', (-1.5, 59, -9.5), (3, 7, 3), crystalp(np.array([LURE[0], LURE[1], LURE[2]]), 94, glow=True),
      rot=(0, 45, 0))
    return dict(center=(0, 30, -4), scale=7.4)


# ================================================================ preview renderer (emissive + alpha)
def render(tex, yaw=0, pitch=0, size=(700, 700), center=(0, 25, 0), scale=10.0, ss=2):
    W, H = size[0] * ss, size[1] * ss
    sc = scale * ss
    col = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), np.float32)
    zb = np.full((H, W), 1e9, np.float32)
    ya, pa = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
    Rp = np.array([[1, 0, 0], [0, math.cos(pa), math.sin(pa)], [0, -math.sin(pa), math.cos(pa)]])
    V = Rp @ Ry
    L = np.array([-0.45, 0.8, -0.45])
    L /= np.linalg.norm(L)
    cen = np.array(center, float)
    for P, cc, (u0, v0, w, h) in g.quads():
        nrm = np.cross(P[1] - P[0], P[3] - P[0])
        ln = np.linalg.norm(nrm)
        if ln < 1e-9:
            continue
        nrm /= ln
        if np.dot(nrm, P.mean(0) - cc) < 0:
            nrm = -nrm
        Q = (P - cen) @ V.T
        vn = V @ nrm
        if np.dot(nrm, P.mean(0) - cc) == 0 or abs(np.dot(P.mean(0) - cc, nrm)) < 1e-6:
            vn = vn if vn[2] < 0 else -vn   # flat plane: face the camera
        shade = 0.55 + 0.45 * max(0.0, float(np.dot(nrm if vn[2] <= 0 else -nrm, L)))
        shade = min(shade + 0.05 * max(0.0, float(nrm[1])), 1.0)
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
            em = (t[..., 3] > 200) & (t[..., 3] < 255)
            sh = np.where(em, 1.0, shade)
            col[y0:y1, x0:x1][ok] = (t[..., :3] * sh[..., None])[ok]
            alpha[y0:y1, x0:x1][ok] = np.where(em, 2.0, 1.0)[ok]
    rgb = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    a = Image.fromarray(((alpha > 0) * 255).astype(np.uint8))
    glow = Image.fromarray(((alpha > 1.5) * 255).astype(np.uint8))
    if ss > 1:
        rgb = rgb.resize(size, Image.LANCZOS)
        a = a.resize(size, Image.LANCZOS)
        glow = glow.resize(size, Image.LANCZOS)
    return rgb, a, glow


def compose(rgb, a, glow, bg_top, bg_bot, accent):
    W, H = rgb.size
    y = np.linspace(0, 1, H)[:, None, None]
    bg = (np.array(bg_top) * (1 - y) + np.array(bg_bot) * y) * np.ones((1, W, 1))
    # floor glow ellipse
    yy, xx = np.mgrid[0:H, 0:W]
    e = np.exp(-(((xx - W / 2) / (W * 0.32)) ** 2 + ((yy - H * 0.86) / (H * 0.06)) ** 2))
    bg = bg * (1 - 0.55 * e[..., None]) + np.array(accent) * 0.0 * e[..., None]
    base = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))
    # bloom from emissive texels
    gl = Image.composite(rgb, Image.new('RGB', rgb.size), glow).filter(ImageFilter.GaussianBlur(9))
    base = Image.fromarray(np.clip(np.asarray(base, float) + np.asarray(gl, float) * 0.9, 0, 255).astype(np.uint8))
    # dark outline
    outline = a.filter(ImageFilter.MaxFilter(5))
    base.paste(Image.new('RGB', rgb.size, (8, 6, 10)), (0, 0), outline)
    base.paste(rgb, (0, 0), a)
    gl2 = Image.composite(rgb, Image.new('RGB', rgb.size), glow).filter(ImageFilter.GaussianBlur(4))
    out = np.clip(np.asarray(base, float) + np.asarray(gl2, float) * 0.35, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


BOSSES = [
    dict(key='mossheart', build=build_golem, name='이끼심장 거상', en='Mossheart Colossus',
         tag='숲 · 탱커형 · 지형 파괴', bg=((22, 40, 30), (8, 14, 10)), accent=(60, 255, 190),
         desc=['가슴의 비취 핵이 약점 (빛날 때만 피해)', '주먹 내려찍기 → 충격파 링', '등의 수정이 하나씩 깨지며 페이즈 전환',
               '덩굴로 플레이어를 끌어당김'],
         views=[(-24, 6), (0, 0), (150, 10)], labels=('정면', '후면')),
    dict(key='frostfang', build=build_wolf, name='서리송곳니 늑대왕', en='Frostfang',
         tag='설원 · 고속 근접형', bg=((24, 34, 56), (8, 10, 20)), accent=(140, 220, 255),
         desc=['돌진 + 물기 연계, 빠른 이동', '서리 포효: 주변 슬로우 + 얼음 가시 소환', '체력 50% 이하: 등 얼음 가시 발사',
               '눈보라 페이즈 (시야 감소)'],
         views=[(-38, 9), (-90, 4), (0, 6)], labels=('측면', '정면')),
    dict(key='cinderforge', build=build_knight, name='잿불 대장장이 기사', en='Cinderforge Knight',
         tag='네더 · 파워형 · 패턴 회피', bg=((48, 18, 14), (14, 6, 6)), accent=(255, 120, 40),
         desc=['거대 망치 내려찍기 → 용암 균열', '가슴 용광로 개방 시 화염 브레스', '모루 소환 낙하 패턴',
               '갑옷 균열이 커질수록 강해지는 광폭화'],
         views=[(-30, 8), (0, 0), (160, 8)], labels=('정면', '후면')),
    dict(key='abyss_angler', build=build_angler, name='심연등불 아귀', en='Abyssal Lantern',
         tag='심해 · 비행/수중 · 유인형', bg=((12, 18, 46), (2, 4, 12)), accent=(110, 240, 255),
         desc=['초롱 불빛 외엔 주변이 암흑 (시야 제한)', '초롱으로 유인 → 큰 입 삼키기', '발광 포자 탄막',
               '수중/공중 자유 이동, 초롱을 맞히면 기절'],
         views=[(-34, 8), (-90, 2), (0, 2)], labels=('측면', '정면')),
]


def make_card(b, out):
    info = b['build']()
    tex = g.bake(tw=1024)
    Image.fromarray(tex).save(os.path.join(out, b['key'] + '.png'))
    with open(os.path.join(out, b['key'] + '.geo.json'), 'w') as f:
        json.dump(g.geometry(tex, 'geometry.' + b['key']), f, separators=(',', ':'))
    ncubes = sum(len(g.BONES[n]['cubes']) for n in g.ORDER)
    (y1, p1), (y2, p2), (y3, p3) = b['views']
    HS, SW, SH = 780, 340, 390
    big = compose(*render(tex, y1, p1, (HS, HS), info['center'], info['scale']), *b['bg'], b['accent'])
    v2 = compose(*render(tex, y2, p2, (SW, SH), info['center'], info['scale'] * 0.5), *b['bg'], b['accent'])
    v3 = compose(*render(tex, y3, p3, (SW, SH), info['center'], info['scale'] * 0.5), *b['bg'], b['accent'])
    W, H = HS + SW, HS + 300
    card = Image.new('RGB', (W, H), (14, 12, 18))
    card.paste(big, (0, 0))
    card.paste(v2, (HS, 0))
    card.paste(v3, (HS, SH))
    d = ImageDraw.Draw(card)
    acc = tuple(int(v * 0.7) for v in b['accent'])
    d.line((HS, 0, HS, HS), fill=acc, width=2)
    d.line((HS, SH, W, SH), fill=acc, width=2)
    d.line((0, HS, W, HS), fill=acc, width=2)
    f1 = ImageFont.truetype(FONT, 46)
    f2 = ImageFont.truetype(FONT, 23)
    f3 = ImageFont.truetype(FONT, 26)
    fs = ImageFont.truetype(FONT, 18)
    d.text((HS + 10, 8), b['labels'][0], font=fs, fill=(170, 170, 185))
    d.text((HS + 10, SH + 8), b['labels'][1], font=fs, fill=(170, 170, 185))
    y = HS + 20
    d.text((34, y), b['name'], font=f1, fill=(255, 255, 255))
    d.text((36, y + 60), b['en'] + '   |   ' + b['tag'], font=f2, fill=b['accent'])
    for i, line in enumerate(b['desc']):
        d.text((40 + (i % 2) * 560, y + 112 + (i // 2) * 46), '- ' + line, font=f3, fill=(215, 215, 225))
    d.text((W - 220, H - 34), '%d bones · %d cubes' % (len(g.ORDER), ncubes), font=f2, fill=(110, 110, 125))
    card.save(os.path.join(out, 'card_' + b['key'] + '.png'))
    print(b['key'], 'bones', len(g.ORDER), 'cubes', ncubes, 'tex', tex.shape)
    return card


def main(out):
    os.makedirs(out, exist_ok=True)
    cards = [make_card(b, out) for b in BOSSES]
    W, H = cards[0].size
    sheet = Image.new('RGB', (W * 2 + 30, H * 2 + 30), (6, 6, 8))
    for i, c in enumerate(cards):
        sheet.paste(c, ((i % 2) * (W + 30), (i // 2) * (H + 30)))
    sheet.save(os.path.join(out, 'boss_concepts.png'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'out')
