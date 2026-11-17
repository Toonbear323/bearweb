"""Raven Witch boss - true 3D voxel model generator for a Bedrock add-on.

Every part is sculpted as a real voxel volume (see voxlib.py) on the voxel grid of the
reference art (../ref/front.png, one art voxel = 21.8 px = one model unit) and then merged
into boxes.  Nothing is a flat projected picture: silhouettes come from the art, depth is
modelled, and every voxel gets its own colour (art colour on the visible front voxels,
palette rules everywhere else).  Only the tiny ornaments (eye, mask, brooch panel) carry a
finer painted decal on their own voxels.

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
from paint import C as HEX, hashf  # noqa: E402
from voxlib import Vox, CX, GY  # noqa: E402

# ------------------------------------------------------------------ reference art helpers
PITCH, OX, OY = 21.8, -3.1, -3.1
_ART = Image.open(os.path.join(HERE, '..', 'ref', 'front.png')).convert('RGB')
ART = np.asarray(_ART, float) / 255.
ART4 = np.asarray(_ART.filter(ImageFilter.BoxBlur(PITCH / 8.0)), float) / 255.


def _cellgrid(s):
    nc, nr = int((ART.shape[1] - OX) / (PITCH * s)), int((ART.shape[0] - OY) / (PITCH * s))
    out = np.zeros((nr, nc, 3))
    p = PITCH * s
    for r in range(nr):
        for c in range(nc):
            xa, xb = int(max(0, OX + c * p + p * 0.18)), int(min(ART.shape[1], OX + (c + 1) * p - p * 0.18))
            ya, yb = int(max(0, OY + r * p + p * 0.18)), int(min(ART.shape[0], OY + (r + 1) * p - p * 0.18))
            if xb > xa and yb > ya:
                px = ART[ya:yb, xa:xb].reshape(-1, 3)
                l = px.sum(1)
                out[r, c] = px[l >= np.percentile(l, 40)].mean(0)
    return out


SPR = {1.0: _cellgrid(1.0), 0.5: _cellgrid(0.5)}


def spr(v, res=None):
    """art colour of the grid cell every voxel sits in (flat, one colour per voxel)"""
    res = res or v.s
    g = SPR[res]
    ci = np.clip(np.floor(v.C / res).astype(int), 0, g.shape[1] - 1)
    ri = np.clip(np.floor(v.R / res).astype(int), 0, g.shape[0] - 1)
    return g[ri, ci]


def sprcols(v, cols, seed=0, bs=(2, 1, 2)):
    """colour taken from the voxel's own art row, column picked (in coherent blocks) from `cols`"""
    g = SPR[1.0]
    cols = np.asarray(cols)
    h = hashf(v.I // bs[0], v.J // bs[1], v.K // bs[2], 40 + seed)
    ci = cols[(h * len(cols)).astype(int) % len(cols)]
    ri = np.clip(np.floor(v.R).astype(int), 0, g.shape[0] - 1)
    return g[ri, ci]


def decal(col, row):
    ax = np.clip(np.round(OX + col * PITCH).astype(int), 0, ART4.shape[1] - 1)
    ay = np.clip(np.round(OY + row * PITCH).astype(int), 0, ART4.shape[0] - 1)
    return ART4[ay, ax]


def pal(names):
    return np.array([HEX(n) for n in names])


def pick(p, h):
    return p[(np.clip(h, 0, 0.9999) * len(p)).astype(int)]


def hv(v, seed, bs=(1, 1, 1)):
    return hashf(v.I // bs[0], v.J // bs[1], v.K // bs[2], seed)


def lum(c):
    return c.max(-1)


def poly_mask(v, poly):
    """rasterise a polygon given in grid (col,row) coordinates onto the voxel columns/rows"""
    s = 4
    im = Image.new('L', (v.nx * s, v.ny * s), 0)
    ImageDraw.Draw(im).polygon([((c - v.c0) / v.s * s, (r - v.r0) / v.s * s) for c, r in poly], fill=255)
    a = np.asarray(im, float).reshape(v.ny, s, v.nx, s).mean((1, 3)) / 255.
    return (a >= 0.5).T          # [i, j]


# ------------------------------------------------------------------ palettes
PURPLE = pal(['#3A1688', '#44189A', '#4E1EAA', '#5A26BC', '#6630CC', '#4A1CA4'])
INDIGO = pal(['#1A0E56', '#201266', '#261678', '#1C1060'])
NAVY = pal(['#07051C', '#0B0828', '#100B34', '#0A0724'])
GOLD = pal(['#E89648', '#F0A858', '#DC8640', '#EFA050', '#D97A6A'])
SPIRAL = pal(['#2A22B0', '#221C98', '#3028C4', '#261EA6'])
ORANGE = pal(['#E88A2C', '#F09A3A', '#D8782A', '#E07E28'])
BONE = pal(['#EEF1F4', '#DDE3EA', '#F7F8FA', '#E4E9EF'])
RAVEN = pal(['#2A2470', '#342C88', '#241E60', '#3A3498', '#2E2880'])
ROBE = pal(['#150C36', '#1C1046', '#261456', '#30186A', '#3C1E80', '#221252'])
HAIR_RAMP = [(0.0, '#F4F7FA'), (0.2, '#E0EBF3'), (0.4, '#C2DDEB'), (0.58, '#A4C4E6'), (0.76, '#7E92D8'), (1.0, '#5560BC')]


def ramp(t, stops):
    xs = np.array([q[0] for q in stops])
    cs = np.array([HEX(q[1]) for q in stops])
    t = np.clip(t, xs[0], xs[-1])
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], -1)


# ================================================================== hat
BRIM = (16.85, 16.0, 28.6)       # radius x, radius z, centre column


def brim_height(C, Z):
    """top row of the brim sheet at (column, depth).  Front half: the stepped slant of the gold
    rim in the picture.  Back half: sags, so from the front you look *under* it at both ends -
    the two dark lobes outlined in gold in the picture are simply the far rim."""
    a_, b_, cc = BRIM
    N = np.where(C < 14.95, 12.95, np.where(C < 17.3, 13.4, np.where(C < 21.5, 14.0, np.where(C < 25, 14.4, np.where(C < 34, 14.9, np.where(
        C < 39.2, 15.05, np.where(C < 41.6, 15.5, np.where(C < 42.6, 15.05, np.where(C < 44.1, 14.5, 14.0)))))))))
    bx = [11.8, 12.0, 12.75, 14.0, 15.0, 16.0, 17.0, 18.6, 19.5, 21.0, 35.0, 36.1, 38.0, 39.2, 41.0, 42.5, 43.4, 44.5, 45.45]
    by = [14.6, 15.5, 17.0, 17.9, 18.4, 19.0, 19.3, 19.7, 19.9, 20.0, 20.0, 19.9, 19.65, 19.3, 19.0, 18.5, 17.9, 17.0, 15.6]
    F = np.interp(C, bx, by) - 0.5
    F = np.where((C > 21) & (C < 35), 19.5 - 3.4 * np.sin(np.pi * (C - 21) / 14.0), F)
    F = np.maximum(F, N)
    zb = b_ * np.sqrt(np.clip(1 - ((C - cc) / a_) ** 2, 0.02, 1))
    return N + (F - N) * np.clip(Z / zb, 0, 1) ** 1.6


def make_brim():
    v = Vox(11, 46.5, 12.5, 21.5, -16.5, 16.5, 0.5)
    C, R, Z = v.C, v.R, v.Z
    a_, b_, cc = BRIM
    rin = np.sqrt(((C - cc) / a_) ** 2 + (Z / b_) ** 2)
    inside = rin <= 1.0
    Hq = np.floor(brim_height(C, Z) * 2 + 0.5) / 2                  # snapped to half voxels
    H2 = np.where(inside[:, 0, :], Hq[:, 0, :], -1)
    low = H2.copy()
    for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        low = np.maximum(low, np.roll(H2, (di, dk), (0, 1)))
    low = np.broadcast_to(low[:, None, :], C.shape)
    rtop = np.floor(R * 2) / 2
    v.add(inside & (rtop >= Hq) & (rtop <= np.maximum(low - 0.5, Hq)))
    top = pick(PURPLE, hv(v, 5, (4, 4, 4)) * 0.6 + hv(v, 6, (2, 2, 2)) * 0.4)
    under = pick(INDIGO, hv(v, 7, (4, 4, 4)) * 0.7 + hv(v, 8, (2, 2, 2)) * 0.3)
    v.paint(v.occ, under, up=top, down=under * 0.9)
    gold = pick(GOLD, hv(v, 9, (2, 2, 2)))
    v.paint(v.occ & (rin > 1 - 0.75 / b_), gold, up=gold, down=gold * 0.85)
    return v


def make_hat():
    v = Vox(9, 48, 0, 23, -18, 18)
    C, R, Z = v.C, v.R, v.Z

    def se(cc, a, b, n):
        return (np.abs((C - cc) / a) ** n + np.abs(Z / b) ** n) <= 1

    def rw(a, b):
        return (R > a) & (R < b)
    crown = (rw(1, 5) & se(28, 3, 3, 8)) | (rw(5, 6) & se(29, 4, 3.6, 4)) | (rw(6, 10) & se(28.5, 5.5, 5.5, 4)) \
        | (rw(10, 13) & se(29, 7, 7, 4)) | (rw(13, 14) & se(29, 8.6, 8.6, 3))
    # the brim rises in steps toward the crown (voxel dome) and the crown reaches down to the sheet
    a_, b_, cc = BRIM
    rin = np.sqrt(((C - cc) / a_) ** 2 + (Z / b_) ** 2)
    H = brim_height(C, Z)
    rowi = np.floor(R)
    dome = ((rin < 0.72) & (rowi >= np.floor(H) - 1) & (rowi < H - 0.01)) | ((rin < 0.5) & (rowi >= np.floor(H) - 2) & (rowi < H - 0.01))
    skirt = se(29, 8.6, 8.6, 3) & (rowi >= 14) & (rowi < H - 0.01)
    v.add(crown | dome | skirt)

    top = pick(PURPLE, hv(v, 5, (2, 2, 2)) * 0.6 + hv(v, 6) * 0.4)
    v.paint(v.occ, top * 0.9, up=top, down=top * 0.6)
    # crown: colours of the art's own rows, picked from clean columns, in coherent blocks
    for (r0, r1, cols) in ((1, 5, [25, 26, 27, 28, 29, 30]), (5, 6, [26, 27, 28, 29, 31, 32]), (6, 9, [26, 27, 31, 32, 33]),
                           (9, 10, [24, 25, 26, 27]), (10, 13, [23, 24, 25, 26, 27]), (13, 14, [21, 22, 23, 24, 25, 26, 27, 35, 36])):
        m = crown & rw(r0, r1)
        cl = sprcols(v, cols, r0)
        v.paint(m, cl, up=cl * 1.08, down=cl * 0.75)
    # the visible front voxels take the art colour of their own cell (when it is hat-coloured)
    s = spr(v)
    okc = (s[..., 2] > s[..., 0]) & ~((s[..., 1] > s[..., 0] + 0.08) & (s[..., 1] > 0.3) & (s[..., 2] < 0.75))
    m = v.front() & crown & okc
    v.paint(m, s, up=s * 1.08, down=s * 0.75)
    return v


def make_spiral():
    v = Vox(33.5, 43.5, 6.5, 15, -0.75, 0.75, 0.5)
    C, R = v.C, v.R
    m = np.zeros(v.occ.shape, bool)
    for c0, c1, r0, r1 in ((37.9, 42.7, 6.75, 7.8), (41.7, 42.7, 7.8, 11.1), (37.9, 39.0, 7.8, 10.95), (39.0, 40.5, 10.1, 10.95),
                           (38.2, 42.7, 11.1, 12.1), (37.1, 38.3, 11.1, 12.1), (36.0, 37.2, 10.6, 11.5), (35.0, 36.1, 9.7, 10.7), (34.0, 35.1, 8.8, 9.8)):
        m |= (C > c0) & (C < c1) & (R > r0) & (R < r1)
    s = spr(v)
    blue = (s[..., 2] > 0.36) & (s[..., 2] > s[..., 0] * 1.6)
    m |= (C > 39.0) & (C < 41.7) & (R > 7.8) & (R < 11.1) & blue
    charm = (C > 38.4) & (C < 39.8) & (R > 12.6) & (R < 14.0) & (np.abs(v.Z) < 0.5)
    v.add(m | charm)
    ok = (s[..., 2] > 0.25) & (s[..., 2] > s[..., 0])
    col = np.where(ok[..., None], s, pick(SPIRAL, hv(v, 3, (2, 2, 1))))
    v.paint(m, col, up=col * 1.1)
    v.paint(charm, np.where((lum(s) > 0.12)[..., None], s, HEX('#1E4A50')))
    return v


def make_pumpkin():
    v = Vox(27.5, 36.5, 7.5, 15, -11.5, -4.5, 0.5)
    C, R, Z = v.C, v.R, v.Z
    cc, rc, zc = 30.45, 10.75, -8.3
    body = np.abs((C - cc) / 2.25) ** 3.2 + np.abs((R - rc) / 1.78) ** 3.2 + np.abs((Z - zc) / 1.9) ** 3.2 <= 1
    stem = (C > 29.9) & (C < 30.9) & (R > 8.2) & (R < 9.2) & (Z > -8.9) & (Z < -7.9)
    flower = (C > 28.4) & (C < 29.6) & (R > 8.5) & (R < 9.4) & (Z > -9.7) & (Z < -8.7)
    s = spr(v)
    teal = (s[..., 1] > s[..., 0] + 0.06) & (s[..., 1] > 0.28)
    # leaves: 1-unit thick, wrapped round the hat (right one) / drooping over the brim (lower one)
    zr = -7.9 + np.clip(C - 33.0, 0, 9) * 0.9
    leaf_r = (C > 32.5) & (C < 35.7) & (R > 9.3) & (R < 12.9) & teal & (Z > zr - 0.55) & (Z < zr + 0.55)
    zl = -9.7 - (R - 12.3) * 0.5
    leaf_b = (C > 28.7) & (C < 31.5) & (R > 12.3) & (R < 14.2) & teal & (Z > zl - 0.55) & (Z < zl + 0.55)
    v.add(body | stem | flower | leaf_r | leaf_b)
    ang = np.arctan2(Z - zc, C - cc)
    rib = np.floor((ang / (2 * np.pi) + 0.5) * 12)
    oc = pick(ORANGE, (rib % 2) * 0.5 + hv(v, 3) * 0.45) * np.clip(1.12 - np.abs(R - rc + 0.4) * 0.14, 0.7, 1.1)[..., None]
    v.paint(body, oc, up=oc * 0.92, down=oc * 0.7)
    okb = (s[..., 0] > s[..., 2] * 1.2)
    m = v.front() & body & okb
    v.paint(m, s, up=s, down=s * 0.75)
    v.dec |= m & (np.abs(C - cc) < 1.9) & (np.abs(R - rc) < 1.5)
    v.paint(stem, pick(pal(['#2E3A22', '#3A2A18', '#27301C']), hv(v, 4)))
    v.paint(flower, pick(pal(['#E88AA8', '#F4B0C4', '#DC7096']), hv(v, 5)))
    lc = np.where(teal[..., None], s, HEX('#3FA890'))
    v.paint(leaf_r | leaf_b, lc, up=lc * 1.08, down=lc * 0.75)
    return v


# ================================================================== head
def make_head():
    v = Vox(17, 41, 15, 39, -9, 10)
    C, R, Z = v.C, v.R, v.Z
    rowi = np.floor(R)

    def se(cc, a, b, n, zc=0.0):
        return (np.abs((C - cc) / a) ** n + np.abs((Z - zc) / b) ** n) <= 1
    hair = ((rowi >= 16) & (rowi <= 19) & se(28, 7, 7, 2.6)) | ((rowi >= 20) & (rowi <= 21) & se(28.5, 8.5, 7.4, 2.6)) \
        | ((rowi >= 22) & (rowi <= 23) & se(28.5, 7.5, 7, 2.6)) | ((rowi == 24) & se(28, 8, 6.6, 2.6))
    hair |= (rowi == 21) & (C > 37) & (C < 38) & (Z > -4) & (Z < 2)
    # front locks over the shoulders
    hair |= (((C > 22) & (C < 24)) | ((C > 31.6) & (C < 33.6))) & (R > 25) & (R < 26.6) & (Z > -7) & (Z < -4.5)
    # room for the neck / mask below the face
    hair &= ~((C > 25) & (C < 31) & (rowi >= 21) & (Z < 1))
    hair &= ~((np.abs(C - 28.15) < 4.2) & (rowi >= 22) & (np.abs(Z) < 4.2))
    # mane down the back: a thick tapering mass
    for r0, r1, w, d in ((22, 26, 8.0, 3.6), (26, 29, 6.6, 3.3), (29, 32, 5.0, 3.0), (32, 34, 3.4, 2.6), (34, 36, 1.9, 2.2), (36, 37.2, 0.9, 1.6)):
        hair |= (R > r0) & (R < r1) & ((np.abs((C - 28.5) / w) ** 2.4 + np.abs((Z - 5.2) / d) ** 2.4) <= 1) & (Z > 3.0)
    # face window: bangs stay one voxel proud of the skin
    win = np.zeros(v.occ.shape, bool)
    for c0, c1, r in ((28, 31, 17), (27, 31, 18), (26, 31, 19), (25, 31, 20)):
        win |= (C > c0) & (C < c1) & (rowi == r)
    hair &= ~(win & (Z < -6))
    # strand relief: every third column of the back surface is carved one voxel deep, so the
    # mane reads as separate locks (and the locks end at different lengths)
    hp_ = np.pad(hair, ((0, 0), (0, 0), (0, 1)))[:, :, 1:]
    coli = np.floor(C).astype(int)
    groove = hair & ~hp_ & (Z > 3) & (rowi >= 20) & (coli % 3 == 1)
    hair &= ~groove
    hd_ = np.pad(hair, ((0, 0), (0, 1), (0, 0)))[:, 1:, :]
    hair &= ~(hair & ~hd_ & (Z > 3) & (rowi >= 27) & (coli % 3 == 2) & (hashf(v.I, 0, 0, 77) > 0.4))
    v.add(hair)
    v.parts = {'mane': hair & (R > 25) & (Z > 3.0), 'tip': hair & (R > 31) & (Z > 3.0)}
    # ---- hair colours: white crown -> cyan -> blue tips, in vertical strands with the odd dark voxel
    strand = hashf(v.I, v.K, 0, 29)
    cell = hv(v, 31)
    lat = np.clip(np.sqrt((C - 28.3) ** 2 + Z ** 2) / 9.0, 0, 1)
    t = 0.03 + np.clip((R - 18.0) / 19.0, 0, 1) ** 1.2 * 0.9 + lat * 0.16 + (strand - 0.5) * 0.2 + (cell - 0.5) * 0.08 + (cell > 0.93) * 0.2 + ((coli % 3 == 0) & (Z > 3)) * 0.07
    hc = ramp(t, HAIR_RAMP)
    v.paint(hair, hc, up=hc, down=hc * 0.8)
    s = spr(v)
    ok = (lum(s) > 0.55) & (s[..., 1] > 0.36)
    m = v.front() & hair & ok & ~win & (Z < 0)
    sb = 1 - (1 - s) * 0.72            # the art's hair is almost white: lift the sampled cells a little
    v.paint(m, sb, up=sb, down=sb * 0.8)
    # ---- face (skin voxels carry the eye decal)
    face = v.front() & win
    v.paint(face, HEX('#E6CCEE'))
    v.dec |= face
    # ---- mask collar
    collar = (C > 25) & (C < 31) & (rowi >= 21) & (rowi <= 24) & (Z > -7) & (Z < 0)
    v.add(collar)
    cc_ = pick(pal(['#22104A', '#2A1458', '#1C0C40']), hv(v, 8))
    cc_ = np.where((rowi == 21)[..., None], HEX('#1E5A6A'), cc_)
    v.paint(collar, cc_, up=HEX('#1E5A6A') * np.ones(3), down=cc_ * 0.8)
    v.dec |= v.front() & collar
    return v


# ================================================================== body
def make_body():
    v = Vox(13, 44, 24, 46, -11, 11)
    C, R, Z = v.C, v.R, v.Z
    rowi = np.floor(R)
    cc, zc = 28.15, 0.4
    aw = {25: 4.0, 26: 4.3, 27: 4.3, 28: 4.3, 29: 4.4, 30: 4.5, 31: 4.7, 32: 5.0, 33: 5.4, 34: 5.8, 35: 6.4, 36: 7.1, 37: 7.8,
          38: 8.5, 39: 9.0, 40: 9.5, 41: 9.9, 42: 10.2, 43: 10.5, 44: 10.75, 45: 10.9}
    a = np.zeros(R.shape)
    for r, w in aw.items():
        a[rowi == r] = w
    b = np.where(rowi <= 30, 3.6, a * 0.72)
    # twelve pleats run down the skirt: ridges at the front / sides / back, grooves between them
    ang0 = np.arctan2((Z - zc) / np.maximum(b, 1e-3), (C - cc) / np.maximum(a, 1e-3))
    pl = 0.5 + 0.5 * np.cos(12 * ang0)
    shrink = 1 - 0.10 * np.clip((R - 32.5) / 7.0, 0, 1) * (1 - pl)
    body = (a > 0) & ((np.abs((C - cc) / np.maximum(a * shrink, 1e-3)) ** 2.3 + np.abs((Z - zc) / np.maximum(b * shrink, 1e-3)) ** 2.3) <= 1)
    v.add(body)
    # brooch: a little lump proud of the chest
    fr = v.front()
    zfront = np.where(fr, Z, 99).min(axis=2, keepdims=True)
    brooch = (C > 27) & (C < 29) & (rowi >= 25) & (rowi <= 28) & (Z > zfront - 1.5) & (Z < zfront - 0.5)
    v.add(brooch)
    # ---- colours: dark robe with vertical folds running round the cone
    sec = np.floor((ang0 / (2 * np.pi) + 0.5) * 12 + 0.5).astype(np.int64)
    fold = np.clip(0.08 + 0.62 * pl + (hashf(sec, 0, 0, 11) - 0.5) * 0.22 + (hv(v, 12, (1, 3, 1)) - 0.5) * 0.10, 0, 0.83)
    rc = pick(ROBE, fold) * np.where(rowi >= 44, 0.82, 1.0)[..., None]
    v.paint(v.occ, rc, up=rc * 1.1, down=HEX('#0E0820') * np.ones(3))
    s = spr(v)
    flame = (s[..., 0] > 0.40) & (s[..., 2] > 0.72) & (s[..., 1] < 0.45)
    edge = np.abs(C - cc) > a - 1.6
    glow = (lum(s) > 0.66) & (np.abs(C - cc) > 3.6)          # aura sparks in the picture, not cloth
    glow |= (lum(s) > 0.5) & (np.abs(C - cc) > 5.0) & (rowi >= 36)
    side = (rowi >= 30) & (np.abs(C - cc) > a - 0.9) & (np.abs(Z - zc) > 1.5)   # the cone turning away
    m = v.front() & ~(flame & edge) & ~glow & ~side & (lum(s) > 0.07)
    v.paint(m, s, up=s * 1.1, down=s * 0.75)
    # the ornate chest panel (thin gold A-lines, brooch, chevron) is finer than one voxel, so those
    # front voxels carry a finer painted decal
    fr = v.front()
    v.dec |= fr & (C > 23) & (C < 33.4) & (rowi >= 25) & (rowi <= 35)
    return v


def make_arm(mirror):
    """one arm with its hanging bell sleeve; mirror=False: picture-left (her right)"""
    v = Vox(13, 26, 24, 40, -5, 5)
    C, R, Z = v.C, v.R, v.Z
    rowi = np.floor(R)
    spans = {26: (21, 24), 27: (20, 24), 28: (19, 24), 29: (17, 23.6), 30: (17, 23.2), 31: (15, 22.8), 32: (15, 22.4), 33: (15, 22.0),
             34: (15, 21.6), 35: (15, 21.2), 36: (15, 20.8), 37: (15.4, 20.2), 38: (16, 18.6)}
    dep = {26: 2.4, 27: 2.6, 28: 2.9, 29: 3.2, 30: 3.4, 31: 3.7, 32: 3.9, 33: 4.0, 34: 4.0, 35: 3.9, 36: 3.7, 37: 3.2, 38: 2.2}
    m = np.zeros(v.occ.shape, bool)
    for r, (c0, c1) in spans.items():
        mid, hw = (c0 + c1) / 2, (c1 - c0) / 2
        m |= (rowi == r) & ((np.abs((C - mid) / hw) ** 3 + np.abs(Z / dep[r]) ** 3) <= 1)
    v.add(m)
    # the sleeve really opens toward the front: hollow out the bell
    hole = (C > 16) & (C < 19.6) & (rowi >= 32) & (rowi <= 36) & (Z < -0.5)
    hole &= ((C - 17.8) / 1.9) ** 2 + ((R - 34.5) / 2.7) ** 2 <= 1
    v.cut(hole)
    # ---- colours (bands run all the way round the arm)
    n = hv(v, 3)
    purple = pick(pal(['#4420A0', '#5028B4', '#5C30C8', '#3A1A8C']), n)
    bell = pick(pal(['#1A1050', '#221464', '#2A1A78', '#160C44']), hv(v, 4, (1, 2, 1)))
    lilac = pick(pal(['#E8C4F2', '#D8A4EA', '#C486E2', '#F4DEFA', '#B070DA']), hv(v, 5))
    teal = pick(pal(['#62BCD4', '#7CD0E2', '#4A94C4', '#8AD8D0']), hv(v, 6))
    col = purple.copy()
    isbell = (rowi >= 31) & (C < 20.6)
    col[isbell] = bell[isbell]
    cuff = (rowi >= 29) & (rowi <= 30) & (C < 21)
    col[cuff] = lilac[cuff]
    ruff = (((rowi == 28) & (C < 22)) | ((rowi == 27) & (C < 21.6)))
    col[ruff] = teal[ruff]
    v.paint(v.occ, col, up=col * 1.08, down=col * 0.72)
    # inside of the bell is almost black
    p = np.pad(v.occ, 1)
    near = np.zeros(v.occ.shape, bool)
    hp = np.pad(hole, 1)
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        near |= hp[1 + d[0]:1 + d[0] + v.nx, 1 + d[1]:1 + d[1] + v.ny, 1 + d[2]:1 + d[2] + v.nz]
    inner = v.occ & near & (Z > -0.5) | (v.occ & near & (np.abs(C - 17.8) < 1.6) & (np.abs(R - 34.5) < 2.4))
    nav = pick(NAVY, hv(v, 7))
    v.paint(inner, nav, up=nav, down=nav)
    if mirror:
        v.occ = v.occ[::-1].copy()
        v.col, v.colU, v.colD, v.dec = v.col[::-1].copy(), v.colU[::-1].copy(), v.colD[::-1].copy(), v.dec[::-1].copy()
        v.c0 = 56.3 - (13 + v.nx)
        v.C = v.c0 + (v.I + .5)
    return v


# ================================================================== raven
def make_raven_body():
    v = Vox(6, 16, 4.5, 13.5, -3, 4, 0.5)
    C, R, Z = v.C, v.R, v.Z
    body = ((C - 11.9) / 2.05) ** 2 + ((R - 7.2) / 2.5) ** 2 + (Z / 1.9) ** 2 <= 1
    legs = np.zeros(v.occ.shape, bool)
    feet = np.zeros(v.occ.shape, bool)
    for c0 in (10.0, 12.4):
        legs |= (C > c0) & (C < c0 + 0.5) & (R > 9.3) & (R < 11.0) & (np.abs(Z) < 0.3)
        feet |= (C > c0 - 0.5) & (C < c0 + 1.0) & (R > 10.9) & (R < 11.9) & (Z > -1.4) & (Z < 0.5)
    # tail: a fan of feathers sweeping down and back
    tl = poly_mask(v, [(7.0, 10.0), (8.5, 9.3), (10.5, 9.4), (13.0, 9.3), (14.6, 9.4), (15.2, 10.6), (14.4, 11.6), (13.6, 11.0),
                       (12.0, 10.4), (10.9, 12.6), (9.6, 12.9), (9.3, 12.4), (8.4, 12.9), (8.0, 12.2), (7.2, 12.2), (6.6, 10.8)])
    zt = 1.1 + (R - 9.3) * 0.35
    tail = tl[:, :, None] & (Z > zt - 0.55) & (Z < zt + 0.55)
    v.add(body | legs | feet | tail)
    v.parts = {'tail': tail & ~body}
    s = spr(v)
    rc = pick(RAVEN, hv(v, 3))
    v.paint(v.occ, rc, up=rc * 1.1, down=rc * 0.75)
    m = v.front() & (body | tail) & (lum(s) > 0.16)
    v.paint(m, s, up=s, down=s * 0.75)
    lg = np.where(((s[..., 0] > s[..., 2]) & (s[..., 0] > 0.25))[..., None], s, HEX('#7A4A30'))
    v.paint(legs | feet, lg)
    return v


def make_raven_head():
    v = Vox(9, 15, 1, 6.5, -4.5, 2, 0.5)
    C, R, Z = v.C, v.R, v.Z
    skull = (np.abs((C - 11.9) / 2.1) ** 3 + np.abs((R - 3.2) / 1.85) ** 3 + np.abs((Z + 0.8) / 2.1) ** 3) <= 1
    beak = (C > 11.9) & (C < 12.9 - (R > 5.0) * 0.5) & (R > 4.0) & (R < 5.9) & (Z > -3.9 + (R - 4.0) * 0.45) & (Z < -2.4)
    v.add(skull | beak)
    s = spr(v)
    bc = pick(BONE, hv(v, 3)) * np.where(Z > 0.2, 0.9, 1.0)[..., None]
    v.paint(skull, bc, up=bc, down=bc * 0.8)
    m = v.front() & skull & (lum(s) > 0.2)
    v.paint(m, s, up=s, down=s * 0.8)
    v.dec |= m & (R < 4.6)
    kc = ramp((R - 4.0) / 1.9, [(0, '#D9B49A'), (0.5, '#E0A080'), (1, '#D8788A')]) * (0.94 + 0.12 * hv(v, 5))[..., None]
    v.paint(beak, kc, up=kc, down=kc * 0.8)
    return v


def make_wing(poly, c0, c1, r0, r1, sx, sy):
    """feathered wing: a curved sheet, two voxels thick at the root"""
    v = Vox(c0, c1, r0, r1, -0.5, 3.5, 0.5)
    C, R, Z = v.C, v.R, v.Z
    pm = poly_mask(v, poly)[:, :, None]
    dist = np.sqrt((C - sx) ** 2 + (R - sy) ** 2)
    zc = 0.35 + 0.16 * dist
    thick = np.where(dist < 3.2, 0.8, 0.52)
    v.add(pm & (np.abs(Z - zc) < thick))
    s = spr(v, 1.0)
    rc = pick(RAVEN, hv(v, 3, (2, 2, 1)))
    col = np.where((lum(s) > 0.17)[..., None], s, rc)
    v.paint(v.occ, col, up=col * 1.08, down=col * 0.78)
    return v


# ================================================================== assemble (rig)
def P(col, row, z=0.0):
    """grid position -> model coordinates"""
    return (col - CX, GY - row, z)


def build():
    """Joint layout (parent -> child):
    root > body > skirt
                > torso > head > hat > hatTop > hatTip
                               |      > pumpkin, spiral > charm
                               > hairBack > hairBackTip
                        > rightArm > rightSleeve      (shoulder / elbow)
                        > leftArm  > leftSleeve
    root > raven > ravenHead, ravenTail, ravenWingR > ravenWingRTip, ravenWingL > ravenWingLTip
    """
    m = Model('geometry.raven_witch')
    B = {}

    def bone(name, parent, pivot):
        B[name] = m.bone(name, parent, pivot=pivot)
    bone('root', None, (0, 0, 0))
    bone('body', 'root', (0.15, 0, 0.4))
    bone('skirt', 'body', P(28.15, 36, 0.4))
    bone('torso', 'body', P(28.15, 35.5, 0.4))
    bone('head', 'torso', P(28.3, 24.5, 0))
    bone('hat', 'head', P(28.8, 15.5, 0))
    bone('hatTop', 'hat', P(28.5, 10, 0))
    bone('hatTip', 'hatTop', P(28.2, 5, 0))
    bone('pumpkin', 'hat', P(30.45, 12.4, -8.3))
    bone('spiral', 'hat', P(40.3, 12.1, 0))
    bone('charm', 'spiral', P(39.1, 12.5, 0))
    bone('hairBack', 'head', P(28.5, 25, 5.0))
    bone('hairBackTip', 'hairBack', P(28.5, 31, 5.6))
    bone('rightArm', 'torso', P(23.6, 26.6, 0))
    bone('rightSleeve', 'rightArm', P(19.2, 30.8, 0))
    bone('leftArm', 'torso', P(56.3 - 23.6, 26.6, 0))
    bone('leftSleeve', 'leftArm', P(56.3 - 19.2, 30.8, 0))
    bone('raven', 'root', P(11.9, 7.2, 0))
    bone('ravenHead', 'raven', P(11.9, 4.9, -0.5))
    bone('ravenTail', 'raven', P(11.9, 9.5, 1.1))
    bone('ravenWingR', 'raven', P(9.9, 5.6, 0.6))        # the raven's own right wing (picture left)
    bone('ravenWingRTip', 'ravenWingR', P(6.2, 3.4, 1.2))
    bone('ravenWingL', 'raven', P(13.9, 5.8, 0.6))
    bone('ravenWingLTip', 'ravenWingL', P(17.4, 5.0, 1.2))
    B['body'].locators['aura'] = [0.15, 14.0, 0.4]
    B['rightSleeve'].locators['hand_r'] = list(P(17.8, 37, -1.0))
    B['leftSleeve'].locators['hand_l'] = list(P(56.3 - 17.8, 37, -1.0))

    LW = [(9.95, 4.6), (9.4, 3.5), (8.8, 2.8), (8.1, 2.1), (7.6, 1.4), (6.8, 0.6), (5.2, 0.0), (4.0, 0.0), (3.2, 0.2), (2.9, 1.6), (3.3, 1.5),
          (3.4, 2.9), (3.9, 2.8), (3.6, 4.3), (4.4, 4.2), (4.4, 5.6), (5.3, 5.4), (5.4, 6.6), (6.4, 6.4), (6.6, 7.6), (7.6, 7.5),
          (7.9, 8.4), (8.8, 8.2), (9.2, 9.0), (9.9, 8.6)]
    RW = [(13.9, 5.3), (15.0, 5.2), (16.0, 5.0), (17.2, 4.6), (18.3, 4.2), (20.3, 3.1), (20.2, 4.2), (20.0, 5.0), (19.0, 5.6),
          (19.2, 6.6), (18.0, 6.6), (17.8, 7.6), (16.6, 7.6), (16.2, 8.5), (15.2, 8.6), (14.6, 9.0), (13.9, 8.6)]
    parts = []        # (bone, volume, decal)

    # ---- hat: brim + lower tiers / upper tiers / tip
    hv_ = make_hat()
    top = hv_.split(hv_.R < 10)
    tip = top.split(top.R < 5)
    parts += [('hat', hv_, None), ('hatTop', top, None), ('hatTip', tip, None), ('hat', make_brim(), None)]
    sp = make_spiral()
    parts += [('charm', sp.split(sp.R > 12.4), None), ('spiral', sp, None), ('pumpkin', make_pumpkin(), decal)]

    # ---- head, back mane in two segments
    hd = make_head()
    mane = hd.split(hd.parts['mane'])
    mtip = mane.split(hd.parts['tip'])
    parts += [('head', hd, decal), ('hairBack', mane, None), ('hairBackTip', mtip, None)]

    # ---- robe: torso / skirt with a hidden plug inside the waist joint
    bd = make_body()
    plug = bd.eroded(2) & (bd.R > 36) & (bd.R < 38)
    skirt = bd.split(bd.R > 36)
    bd.occ |= plug
    parts += [('torso', bd, decal), ('skirt', skirt, None)]

    # ---- arms: shoulder + elbow
    for side, mirror in (('right', False), ('left', True)):
        av = make_arm(mirror)
        plug = av.eroded(1) & (av.R > 31) & (av.R < 32)
        sl = av.split(av.R > 31)
        av.occ |= plug
        parts += [(side + 'Arm', av, None), (side + 'Sleeve', sl, None)]

    # ---- raven
    rb = make_raven_body()
    parts += [('ravenTail', rb.split(rb.parts['tail']), None), ('raven', rb, None), ('ravenHead', make_raven_head(), decal)]
    wr = make_wing(LW, 2, 10.5, 0, 9.5, 9.9, 5.4)
    wl = make_wing(RW, 13.5, 21, 2.5, 9.5, 13.9, 5.6)
    parts += [('ravenWingRTip', wr.split(wr.C < 6.2), None), ('ravenWingR', wr, None),
              ('ravenWingLTip', wl.split(wl.C > 17.4), None), ('ravenWingL', wl, None)]

    stats = {}
    for name, vox, dc in parts:
        n, k = stats.get(name, (0, 0))
        stats[name] = (n + vox.emit(B[name], dc), k + int(vox.occ.sum()))
    m.stats = stats
    return m


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    m = build()
    atlas = m.bake(max_w=1024)
    atlas.save(os.path.join(out, 'raven_witch.png'))
    with open(os.path.join(out, 'raven_witch.geo.json'), 'w') as fh:
        json.dump(m.to_json(bounds=(7, 6, 2)), fh, separators=(',', ':'))
    print({k: v for k, v in m.stats.items()})
    print('bones', len(m.bones), 'cubes', sum(len(b.cubes) for b in m.bones), 'atlas', atlas.size)
