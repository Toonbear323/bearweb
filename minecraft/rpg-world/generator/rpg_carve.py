"""Digging helpers for underground regions: chambers, tunnels, cave decoration."""
import math

import numpy as np

from mcw import B, AIR, physics_tables
from gen_common import fbm, superdist, clamp_gradient


def chamber(W, cx, cz, rx, rz, fy, height, seed, p=2.0, floor_noise=1.0, wall_noise=0.22, ceil_min=4,
            floor_block=None, rng=None, flat=False):
    """Carve a cave chamber (floor top block at about fy). Returns a dict with the column data."""
    a = W.a
    x1, x2 = int(cx - rx - 3), int(cx + rx + 3)
    z1, z2 = int(cz - rz - 3), int(cz + rz + 3)
    xs = np.arange(x1, x2 + 1)
    zs = np.arange(z1, z2 + 1)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    n = fbm(len(xs), len(zs), 7, 3, seed)
    n2 = fbm(len(xs), len(zs), 5, 2, seed + 1)
    d = superdist((X - cx) / rx, (Z - cz) / rz, p) + (n - 0.5) * 2 * wall_noise
    inside = d < 1.0
    fl = np.full(X.shape, fy, np.int32)
    if not flat:
        fl = (fy + np.round((n2 - 0.5) * 2 * floor_noise)).astype(np.int32)
        fl = clamp_gradient(fl, inside, 1)
    ce = fl + ceil_min + (height - ceil_min) * np.sqrt(np.clip(1 - d ** 2, 0, 1)) * (0.8 + 0.4 * n)
    ce = np.round(ce).astype(np.int32)
    for (i, k) in np.argwhere(inside):
        x, z = int(X[i, k]), int(Z[i, k])
        f, c = int(fl[i, k]), int(ce[i, k])
        for y in range(f + 1, c + 1):
            a.set(x, y, z, AIR)
        if floor_block is not None:
            a.set(x, f, z, floor_block(x, z) if callable(floor_block) else floor_block)
    return dict(X=X, Z=Z, inside=inside, floor=fl, ceil=ce, box=(x1, z1, x2, z2))


def box_carve(W, x1, y1, z1, x2, y2, z2):
    W.a.fill(x1, y1, z1, x2, y2, z2, AIR)


def tunnel(W, pts, width=5, height=5, floor_block=None, arch=True, fill_below=None):
    """Carve a tunnel along [(x, floor_y, z), ...]; floor_y = top block of the walkway (interpolated)."""
    a = W.a
    r = width / 2.0
    done = set()
    for (ax, ay, az), (bx, by, bz) in zip(pts[:-1], pts[1:]):
        L = max(1.0, math.hypot(bx - ax, bz - az))
        n = int(L * 3) + 1
        for s in range(n + 1):
            t = s / n
            x = ax + (bx - ax) * t
            z = az + (bz - az) * t
            fy = int(round(ay + (by - ay) * t))
            for ix in range(int(math.floor(x - r)), int(math.ceil(x + r)) + 1):
                for iz in range(int(math.floor(z - r)), int(math.ceil(z + r)) + 1):
                    dd = math.hypot(ix - x, iz - z)
                    if dd > r:
                        continue
                    key = (ix, iz)
                    hh = height
                    if arch and dd > r - 1.0:
                        hh = height - 1
                    prev = done and None
                    for y in range(fy + 1, fy + hh + 1):
                        a.set(ix, y, iz, AIR)
                    if (ix, iz, fy) not in done:
                        if fill_below is not None and a.get(ix, fy, iz) == AIR:
                            yy = fy
                            while yy > fy - 20 and a.get(ix, yy, iz) == AIR:
                                a.set(ix, yy, iz, fill_below)
                                yy -= 1
                        if floor_block is not None:
                            a.set(ix, fy, iz, floor_block(ix, iz) if callable(floor_block) else floor_block)
                        done.add((ix, iz, fy))


ORES = [("coal_ore", 30), ("iron_ore", 20), ("copper_ore", 22), ("gold_ore", 6), ("lapis_ore", 6),
        ("redstone_ore", 6), ("diamond_ore", 2), ("emerald_ore", 1)]


def pick(rng, table):
    tot = sum(w for _, w in table)
    r = rng.random() * tot
    for n, w in table:
        r -= w
        if r <= 0:
            return n
    return table[-1][0]


def decorate(W, box, ymin, ymax, rng, ore_p=0.04, drip_p=0.025, mite_p=0.01, lichen_p=0.02,
             vine_p=0.004, moss_p=0.0, rock=("stone", "andesite", "tuff", "deepslate", "granite", "diorite"),
             deep_ores=False, keep=None, ores=None):
    """Ores in exposed walls, dripstone from the ceiling, stalagmites, glow lichen on floors, glow berries."""
    a = W.a
    x1, z1, x2, z2 = box
    rock_ids = {B(n) for n in rock}
    sl = (slice(x1 - a.x0, x2 - a.x0 + 1), slice(ymin - a.y0, ymax - a.y0 + 1), slice(z1 - a.z0, z2 - a.z0 + 1))
    blk = a.blk[sl]
    air = blk == 0
    pos = np.argwhere(air)
    nx, ny, nz = blk.shape
    for (i, j, k) in pos:
        x, y, z = i + x1, j + ymin, k + z1
        if keep is not None and keep(x, y, z):
            continue
        above = blk[i, j + 1, k] if j + 1 < ny else 1
        below = blk[i, j - 1, k] if j > 0 else 1
        # ceiling: stalactites / glow berries
        if above in rock_ids and below == 0:
            r = rng.random()
            if r < drip_p:
                ln = rng.choice([1, 1, 2, 2, 3])
                ok = all(j - t >= 1 and blk[i, j - t, k] == 0 for t in range(ln + 2))
                if ok:
                    names = {1: ["tip"], 2: ["base", "tip"], 3: ["base", "frustum", "tip"]}[ln]
                    for t, th in enumerate(names):
                        a.set(x, y - t, z, B("pointed_dripstone", hanging=1, dripstone_thickness=th))
                    a.set(x, y + 1, z, B("dripstone_block"))
                continue
            if r < drip_p + vine_p:
                ln = rng.randint(1, 3)
                if all(j - t >= 1 and blk[i, j - t, k] == 0 for t in range(ln + 2)):
                    for t in range(ln):
                        last = t == ln - 1
                        a.set(x, y - t, z, B("cave_vines_head_with_berries" if last else "cave_vines_body_with_berries"))
                continue
        # floor: lichen / stalagmites
        if below in rock_ids and above == 0:
            r = rng.random()
            if r < lichen_p:
                a.set(x, y, z, B("glow_lichen", multi_face_direction_bits=1))
            elif r < lichen_p + mite_p:
                a.set(x, y, z, B("pointed_dripstone", hanging=0, dripstone_thickness="tip"))
                a.set(x, y - 1, z, B("dripstone_block"))
    # ores: replace rock that touches air on a side
    if ore_p > 0:
        solid = np.isin(blk, list(rock_ids))
        touch = np.zeros_like(solid)
        touch[1:] |= air[:-1]; touch[:-1] |= air[1:]
        touch[:, :, 1:] |= air[:, :, :-1]; touch[:, :, :-1] |= air[:, :, 1:]
        for (i, j, k) in np.argwhere(solid & touch):
            if rng.random() < ore_p:
                name = pick(rng, ores or ORES)
                if deep_ores:
                    name = "deepslate_" + name
                a.set(i + x1, j + ymin, k + z1, B(name))
