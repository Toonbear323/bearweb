"""Warning marks (telegraphs) of the Raven Witch's attacks - 3D voxel rune circles.

Every mark is a little entity lying on the ground: a raised crenellated rim, a rune floating just
above a disc that grows from the centre until it touches the rim (that moment is the hit), and an
eruption of spikes that shoots up when it goes off.

Run:  python3 build_marks.py <out_dir>
"""
import json
import math
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mclib import Model  # noqa: E402
from paint import C as HEX, hashf  # noqa: E402
from voxlib import Vox, CX, GY  # noqa: E402

#        name      radius  inner  voxel  warn   damage  colours: rim, rim light, rune, fill dark, fill light, burst (low -> high)
MARKS = {
    'hex':  dict(R=3.0, r0=0.0, s=1, warn=1.25, dmg=8,  rim='#FF4FD8', hi='#FFD6FA', rune='#FFE27A', f0='#2C0A66', f1='#7A2AD0',
                 burst=['#3A0E8A', '#8A2AE0', '#E66AF8', '#FFE8FF'], spikes=26),
    'seed': dict(R=2.5, r0=0.0, s=1, warn=1.5,  dmg=10, rim='#FF9A28', hi='#FFE2A0', rune='#FFF0B8', f0='#4A1C06', f1='#B0520E',
                 burst=['#7A2A08', '#E8741A', '#FFC23A', '#FFF6C0'], spikes=20, bomb=True),
    'wave': dict(R=1.9, r0=0.0, s=1, warn=0.9,  dmg=7,  rim='#5ADCFF', hi='#E0FAFF', rune='#FFFFFF', f0='#0C1250', f1='#2A3CB8',
                 burst=['#141A60', '#3A4AD0', '#6AD0FF', '#F0FFFF'], spikes=14),
    'nova': dict(R=6.0, r0=0.0, s=2, warn=1.5,  dmg=12, rim='#FF4A78', hi='#FFD0DC', rune='#FFD25A', f0='#3A0828', f1='#A01E6A',
                 burst=['#4A0A50', '#C02A90', '#FF7AC0', '#FFF0F8'], spikes=44),
    'ring': dict(R=11.0, r0=6.0, s=4, warn=1.5, dmg=12, rim='#FF4A78', hi='#FFD0DC', rune='#FFD25A', f0='#3A0828', f1='#A01E6A',
                 burst=['#4A0A50', '#C02A90', '#FF7AC0', '#FFF0F8'], spikes=70),
}


def ramp(t, cols):
    cs = np.array([HEX(c) for c in cols])
    xs = np.linspace(0, 1, len(cs))
    t = np.clip(t, 0, 1)
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], -1)


def vol(n, h, s):
    """volume centred on the entity, n voxels wide, h voxels high, resting on the ground"""
    return Vox(CX - n * s / 2, CX + n * s / 2, GY - h * s, GY, -n * s / 2, n * s / 2, s)


def build_mark(name):
    q = MARKS[name]
    s = q['s']
    R, r0 = q['R'] * 16 / s, q['r0'] * 16 / s          # radii in voxels
    n = int(math.ceil(R)) * 2 + 2
    m = Model('geometry.bear_mark_' + name)
    m.bone('mark', pivot=(0, 0, 0))
    bones = {k: m.bone(k, 'mark', pivot=(0, 0, 0)) for k in ('fill', 'rune', 'rim', 'burst')}
    w = max(2.0, R * 0.07)                              # rim width

    def polar(v):
        X, Z = (v.C - CX) / s, v.Z / s
        return X, Z, np.sqrt(X * X + Z * Z), np.arctan2(Z, X)

    # ---- rim: three voxels high, with battlements
    v = vol(n, 3, s)
    X, Z, rho, ang = polar(v)
    lvl = (GY - v.R) / s                                 # 0.5, 1.5, 2.5 (height in voxels)
    seg = np.floor((ang / (2 * np.pi) + 0.5) * max(12, int(R * 0.9) // 2 * 2))
    ring = (rho <= R) & (rho > R - w)
    if r0:
        ring |= (rho >= r0) & (rho < r0 + w)
    v.add(ring & ((lvl < 2) | (seg % 2 == 0)))
    c = np.where((lvl > 2)[..., None], HEX(q['hi']), HEX(q['rim']) * (0.86 + 0.14 * hashf(v.I, v.K, 0, 3))[..., None])
    v.paint(v.occ, c, up=np.where((lvl > 2)[..., None], HEX('#FFFFFF'), HEX(q['hi'])))
    v.emit(bones['rim'], skip=('down',))

    # ---- fill: one voxel thick disc that grows (scaled by the animation)
    v = vol(n, 1, s)
    X, Z, rho, ang = polar(v)
    disc = (rho <= R - w) & (rho >= (r0 + w if r0 else 0))
    v.add(disc)
    t = (rho - r0) / max(R - r0, 1)
    band = (np.floor(rho / max(2.0, R / 8)) % 2) * 0.22
    c = ramp(0.25 + 0.55 * t + band + (hashf(v.I, v.K, 0, 5) - 0.5) * 0.12, [q['f0'], q['f1']])
    v.paint(v.occ, c, up=c)
    v.emit(bones['fill'], skip=('down',))

    # ---- rune: floats one voxel above the fill
    v = vol(n, 2, s)
    X, Z, rho, ang = polar(v)
    top = (GY - v.R) / s > 1
    Rm = (R + r0) / 2 if r0 else R * 0.62
    rune = np.abs(rho - Rm) < 0.75
    if r0:
        k = 16
        d = np.abs(np.sin((ang + np.pi / k) * k / 2)) * rho      # spokes across the band
        rune |= (d < 0.8) & (rho > r0 + w + 1) & (rho < R - w - 1)
    else:
        for a0 in (0, np.pi):                                     # hexagram
            for j in range(3):
                a = a0 + j * 2 * np.pi / 3 + np.pi / 2
                d = X * np.cos(a) + Z * np.sin(a)
                rune |= (np.abs(d - Rm * 0.5) < 0.7) & (rho < Rm)
        rune |= rho < max(1.5, R * 0.07)
        for j in range(6):
            a = j * np.pi / 3
            rune |= ((X - (R - w - Rm) * 0 - np.cos(a) * (Rm + R - w) / 2) ** 2 + (Z - np.sin(a) * (Rm + R - w) / 2) ** 2) < max(1.2, R * 0.05) ** 2
    v.add(rune & top)
    c = HEX(q['rune']) * (0.85 + 0.15 * hashf(v.I, v.K, 0, 7))[..., None]
    v.paint(v.occ, c, up=np.minimum(c * 1.12, 1))
    v.emit(bones['rune'], skip=('down',))

    # ---- burst: spikes of different heights all over the area (stepped pyramids)
    hmax = int(max(10, min(R * 1.5, 56 / s * 1.0 + 12)))
    v = vol(n, hmax, s)
    X, Z, rho, ang = polar(v)
    lvl = (GY - v.R) / s
    rng = np.random.RandomState(sum(map(ord, name)) + 5)
    occ = np.zeros(v.occ.shape, bool)
    for i in range(q['spikes']):
        while True:
            x, z = rng.uniform(-R, R, 2)
            rr = math.hypot(x, z)
            if rr < R - 2 and rr > (r0 + 2 if r0 else -1):
                break
        hw = rng.uniform(1.0, 2.4) if s == 1 else rng.uniform(0.8, 1.6)
        hh = rng.uniform(0.45, 1.0) * hmax
        taper = hw * (1 - np.clip(lvl / hh, 0, 1) ** 1.5) + 0.35
        occ |= (np.abs(X - x) < taper) & (np.abs(Z - z) < taper) & (lvl < hh)
    v.add(occ)
    c = ramp(lvl / hmax * 1.15 + (hashf(v.I, v.J, v.K, 9) - 0.5) * 0.18, q['burst'])
    v.paint(v.occ, c, up=np.minimum(c * 1.25, 1))
    v.emit(bones['burst'], skip=('down',))

    # ---- the pumpkin bomb that drops onto the seed mark
    if q.get('bomb'):
        b = m.bone('bomb', 'mark', pivot=(0, 9, 0))
        v = Vox(CX - 10, CX + 10, GY - 22, GY, -10, 10, 1)
        X, Y, Z = v.C - CX, GY - v.R, v.Z
        body = np.abs(X / 8.5) ** 2.8 + np.abs((Y - 8.5) / 7.2) ** 2.8 + np.abs(Z / 8.5) ** 2.8 <= 1
        ang = np.arctan2(Z, X)
        ribs = 0.5 + 0.5 * np.cos(ang * 10)
        body &= np.sqrt(X * X + Z * Z) <= 8.5 * (0.93 + 0.07 * ribs) * np.sqrt(np.clip(1 - np.abs((Y - 8.5) / 7.2) ** 2.8, 0, 1)) ** (2 / 2.8) + 0.3
        stem = (np.abs(X - 0.5) < 1.5) & (np.abs(Z) < 1.5) & (Y > 15) & (Y < 19.5 - np.abs(X - 0.5))
        v.add(body | stem)
        oc = ramp(0.2 + 0.6 * ribs + (hashf(v.I, v.J, v.K, 3) - 0.5) * 0.15, ['#B8500E', '#E87A1C', '#FFA436']) * np.clip(0.8 + Y / 34, 0.8, 1.15)[..., None]
        v.paint(body, oc, up=np.minimum(oc * 1.1, 1), down=oc * 0.7)
        v.paint(stem, HEX('#3A5A22'))
        # carved, glowing face on all four sides
        for ax, sgn in ((2, -1), (2, 1), (0, -1), (0, 1)):
            U = X if ax == 2 else Z
            D = (Z if ax == 2 else X) * sgn
            face = (((np.abs(np.abs(U) - 3.2) < 1.6 - (Y - 9.5) * 0.8) & (Y > 9.5) & (Y < 12.5))
                    | ((np.abs(U) < 5.2) & (Y > 4.2 + np.abs(U) * 0.45) & (Y < 6.6 + np.abs(U) * 0.45) & ~((np.abs(np.abs(U) - 1.6) < 0.6) & (Y > 5.8))))
            sh = v.occ & face & (D > 5.0)
            first = sh & ~np.roll(v.occ, -sgn, 2 if ax == 2 else 0)
            v.cut(first)
            p_ = sh & ~first
            v.paint(p_, HEX('#FFE66A'), up=HEX('#FFE66A'), down=HEX('#FFE66A'))
        v.emit(b)
    return m, q


def build_all(out):
    os.makedirs(out, exist_ok=True)
    res = {}
    for name in MARKS:
        m, q = build_mark(name)
        atlas = m.bake(max_w=1024)
        geo = m.to_json(bounds=(q['R'] * 2 + 3, 22 if q.get('bomb') else 8, 5 if q.get('bomb') else 2))
        atlas.save(os.path.join(out, 'mark_%s.png' % name))
        with open(os.path.join(out, 'mark_%s.geo.json' % name), 'w') as fh:
            json.dump(geo, fh, separators=(',', ':'))
        res[name] = (geo, atlas)
        print(name, 'cubes', sum(len(b.cubes) for b in m.bones), 'atlas', atlas.size)
    return res


if __name__ == '__main__':
    build_all(sys.argv[1] if len(sys.argv) > 1 else '.')
