"""Shared terrain, shape, vegetation and decoration helpers."""
import math
import random

import numpy as np

from mcw import B, AIR, PAL, Area, sign_be, simple_be, flowerpot_be

# ---------------------------------------------------------------------------
# noise


def value_noise(sx, sz, scale, seed):
    rng = np.random.default_rng(seed)
    gx = int(sx / scale) + 3
    gz = int(sz / scale) + 3
    g = rng.random((gx, gz))
    xs = np.arange(sx) / scale
    zs = np.arange(sz) / scale
    xi = xs.astype(int)
    zi = zs.astype(int)
    xf = xs - xi
    zf = zs - zi
    xf = xf * xf * (3 - 2 * xf)
    zf = zf * zf * (3 - 2 * zf)
    a = g[np.ix_(xi, zi)]
    b = g[np.ix_(xi + 1, zi)]
    c = g[np.ix_(xi, zi + 1)]
    d = g[np.ix_(xi + 1, zi + 1)]
    xf = xf[:, None]
    zf = zf[None, :]
    return (a * (1 - xf) + b * xf) * (1 - zf) + (c * (1 - xf) + d * xf) * zf


def fbm(sx, sz, scale, octaves=4, seed=0, persistence=0.5):
    total = np.zeros((sx, sz))
    amp = 1.0
    norm = 0.0
    for o in range(octaves):
        total += amp * value_noise(sx, sz, max(scale / (2 ** o), 1.0), seed + o * 1013)
        norm += amp
        amp *= persistence
    return total / norm


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blur(arr, passes=1):
    a = arr.astype(float)
    for _ in range(passes):
        p = np.pad(a, 1, mode="edge")
        a = (p[1:-1, 1:-1] * 4 + p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 8.0
    return a


def limit_slope(h, mask=None, maxstep=1, iters=60):
    """Lower cells that stick up more than maxstep above every... (makes terrain walkable).
    Raises cells that sit more than maxstep below all neighbours (removes pits)."""
    h = h.copy()
    for _ in range(iters):
        p = np.pad(h, 1, mode="edge")
        nmax = np.maximum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
        nmin = np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
        # pit: lower than every neighbour by > maxstep  -> raise
        pit = h < nmin - maxstep
        # spike: higher than every neighbour by > maxstep -> lower
        spike = h > nmax + maxstep
        if mask is not None:
            pit &= mask
            spike &= mask
        if not pit.any() and not spike.any():
            break
        h = np.where(pit, nmin - maxstep, h)
        h = np.where(spike, nmax + maxstep, h)
    return h


def clamp_gradient(h, mask, maxstep=1, iters=200):
    """Make |h(a)-h(b)| <= maxstep for neighbouring cells inside mask (lowering the higher one)."""
    h = h.copy()
    for _ in range(iters):
        p = np.pad(h, 1, mode="edge")
        nmin = np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
        bad = (h > nmin + maxstep) & mask
        if not bad.any():
            break
        h = np.where(bad, nmin + maxstep, h)
    return h


# ---------------------------------------------------------------------------
# geometry helpers


def superdist(dx, dz, p=6.0):
    return (np.abs(dx) ** p + np.abs(dz) ** p) ** (1.0 / p)


def line_points(p0, p1, step=0.35):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    n = max(1, int(math.dist(p0, p1) / step))
    pts = []
    last = None
    for i in range(n + 1):
        t = i / n
        q = (round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), round(z0 + (z1 - z0) * t))
        if q != last:
            pts.append(q)
            last = q
    return pts


def axis_of(p0, p1):
    dx, dy, dz = abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), abs(p1[2] - p0[2])
    if dy >= dx and dy >= dz:
        return "y"
    return "x" if dx >= dz else "z"


def ellipsoid(area, cx, cy, cz, rx, ry, rz, block, rng=None, rough=0.0, only_air=True, chance=1.0):
    for x in range(int(cx - rx - 1), int(cx + rx + 2)):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for z in range(int(cz - rz - 1), int(cz + rz + 2)):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                lim = 1.0 - (rng.random() * rough if rng and rough else 0.0)
                if d <= lim and (chance >= 1.0 or rng.random() < chance):
                    if only_air:
                        area.put(x, y, z, block)
                    else:
                        area.set(x, y, z, block)


def disk(area, cx, y, cz, r, block, only_air=False):
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for z in range(int(cz - r - 1), int(cz + r + 2)):
            if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + 0.5:
                (area.put if only_air else area.set)(x, y, z, block)


def ring(area, cx, y, cz, r_in, r_out, block):
    for x in range(int(cx - r_out - 1), int(cx + r_out + 2)):
        for z in range(int(cz - r_out - 1), int(cz + r_out + 2)):
            d2 = (x - cx) ** 2 + (z - cz) ** 2
            if r_in * r_in - 0.5 < d2 <= r_out * r_out + 0.5:
                area.set(x, y, z, block)


def cylinder(area, cx, y0, cz, r, h, block, hollow=False, inner=None):
    for y in range(y0, y0 + h):
        if hollow:
            ring(area, cx, y, cz, r - 1, r, block)
            if inner is not None:
                disk(area, cx, y, cz, r - 1.2, inner)
        else:
            disk(area, cx, y, cz, r, block)


# ---------------------------------------------------------------------------
# vegetation


def leaves_of(kind):
    return B(kind + "_leaves", persistent_bit=1, update_bit=0)


def log_of(kind, axis="y"):
    return B(kind + "_log", axis=axis)


def branch(area, p0, p1, log_kind):
    ax = axis_of(p0, p1)
    lb = log_of(log_kind, ax) if not log_kind.endswith("_wood") else B(log_kind, axis=ax)
    for q in line_points(p0, p1):
        area.set(q[0], q[1], q[2], lb)


def leaf_blob(area, cx, cy, cz, r, leaf, rng, flat=0.7, rough=0.35, extra=None, extra_chance=0.0):
    ry = max(1.5, r * flat)
    for x in range(int(cx - r - 1), int(cx + r + 2)):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = ((x - cx) / r) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / r) ** 2
                if d <= 1.0 - rng.random() * rough:
                    b = leaf
                    if extra is not None and rng.random() < extra_chance:
                        b = extra
                    area.put(x, y, z, b)


def oak_tree(area, x, y, z, rng, kind="oak", h=None, leaf=None, glow=None):
    """y = first trunk block (ground+1)."""
    h = h or rng.randint(5, 7)
    lb = log_of(kind)
    leaf = leaf or leaves_of(kind)
    for i in range(h):
        area.set(x, y + i, z, lb)
    top = y + h
    leaf_blob(area, x, top - 1, z, rng.uniform(2.6, 3.3), leaf, rng, flat=0.75,
              extra=glow, extra_chance=0.03 if glow is not None else 0)
    area.put(x, top, z, leaf)


def birch_tree(area, x, y, z, rng):
    h = rng.randint(6, 8)
    lb = log_of("birch")
    leaf = leaves_of("birch")
    for i in range(h):
        area.set(x, y + i, z, lb)
    for i, r in ((h - 3, 2.4), (h - 2, 2.4), (h - 1, 1.6), (h, 1.1)):
        disk(area, x, y + i, z, r, leaf, only_air=True)


def spruce_tree(area, x, y, z, rng, h=None):
    h = h or rng.randint(9, 13)
    lb = log_of("spruce")
    leaf = leaves_of("spruce")
    for i in range(h):
        area.set(x, y + i, z, lb)
    r = 0.6
    for i in range(h, 2, -1):
        disk(area, x, y + i, z, r, leaf, only_air=True)
        r += 0.55 if (h - i) % 3 != 2 else -0.9
        r = min(max(r, 0.6), 3.4)
    area.put(x, y + h, z, leaf)
    area.put(x, y + h + 1, z, leaf)


def dark_oak_tree(area, x, y, z, rng):
    h = rng.randint(6, 8)
    lb = log_of("dark_oak")
    leaf = leaves_of("dark_oak")
    for dx in (0, 1):
        for dz in (0, 1):
            for i in range(h):
                area.set(x + dx, y + i, z + dz, lb)
    leaf_blob(area, x + 0.5, y + h - 0.5, z + 0.5, rng.uniform(3.8, 4.6), leaf, rng, flat=0.45)
    for _ in range(3):
        a = rng.random() * 6.28
        ex, ez = x + 0.5 + math.cos(a) * 3, z + 0.5 + math.sin(a) * 3
        branch(area, (x, y + h - 3, z), (round(ex), y + h - 1, round(ez)), "dark_oak")


def big_oak(area, x, y, z, rng, h=None, glow=None, lantern_ok=True, kind="oak"):
    """2x2 trunk giant oak with branches; y = first trunk block."""
    h = h or rng.randint(10, 13)
    lb = log_of(kind)
    leaf = leaves_of(kind)
    wood = B(kind + "_wood", axis="y")
    for dx in (0, 1):
        for dz in (0, 1):
            for i in range(h):
                area.set(x + dx, y + i, z + dz, lb)
    # roots
    for dx, dz in ((-1, 0), (2, 1), (0, 2), (1, -1), (-1, 1), (2, 0), (1, 2), (0, -1)):
        if rng.random() < 0.6:
            rh = rng.randint(1, 2)
            for i in range(rh):
                area.set(x + dx, y + i, z + dz, wood)
    cx, cz = x + 0.5, z + 0.5
    tips = []
    nb = rng.randint(4, 6)
    a0 = rng.random() * 6.28
    for i in range(nb):
        a = a0 + i * 6.28 / nb + rng.uniform(-0.3, 0.3)
        sy = y + rng.randint(h // 2 + 1, h - 1)
        L = rng.uniform(4.0, 6.5)
        ex, ez = cx + math.cos(a) * L, cz + math.sin(a) * L
        ey = sy + rng.randint(2, 4)
        branch(area, (round(cx), sy, round(cz)), (round(ex), ey, round(ez)), kind)
        tips.append((ex, ey, ez))
    for (ex, ey, ez) in tips:
        leaf_blob(area, ex, ey + 0.5, ez, rng.uniform(3.0, 3.8), leaf, rng, flat=0.6,
                  extra=glow, extra_chance=0.012 if glow is not None else 0)
    leaf_blob(area, cx, y + h + 0.5, cz, rng.uniform(4.0, 5.0), leaf, rng, flat=0.6,
              extra=glow, extra_chance=0.01 if glow is not None else 0)
    # hanging lanterns under a couple of branch tips
    if lantern_ok:
        for (ex, ey, ez) in tips[:2]:
            hx, hz = round(ex), round(ez)
            yy = int(ey) - 1
            # walk down to the bottom of the canopy
            while yy > y + 2 and area.get(hx, yy, hz) != AIR:
                yy -= 1
            if yy > y + 3 and area.get(hx, yy + 1, hz) != AIR:
                area.set(hx, yy, hz, B("chain"))
                area.set(hx, yy - 1, hz, B("lantern", hanging=1))
    return tips


def palm_tree(area, x, y, z, rng, h=None):
    h = h or rng.randint(7, 11)
    lb_y = log_of("jungle", "y")
    leaf = leaves_of("jungle")
    a = rng.random() * 6.28
    dx, dz = math.cos(a), math.sin(a)
    px, pz = float(x), float(z)
    last = (x, y, z)
    for i in range(h):
        lean = (i / h) ** 2 * rng.uniform(2.0, 3.5) / h * 2
        px += dx * lean
        pz += dz * lean
        q = (round(px), y + i, round(pz))
        if (q[0], q[2]) != (last[0], last[2]) and i > 0:
            area.set(q[0], q[1] - 1, q[2], log_of("jungle", "x" if abs(dx) > abs(dz) else "z"))
        area.set(q[0], q[1], q[2], lb_y)
        last = q
    tx, ty, tz = last
    area.set(tx, ty + 1, tz, leaf)
    for k in range(8):
        ang = k * math.pi / 4 + rng.uniform(-0.2, 0.2)
        ux, uz = math.cos(ang), math.sin(ang)
        length = rng.randint(3, 5)
        for r in range(1, length + 1):
            dy = 1 if r == 1 else (0 if r < length - 1 else -1)
            if r == length:
                dy = -2 if length > 3 else -1
            area.put(round(tx + ux * r), ty + 1 + dy, round(tz + uz * r), leaf)
            if r == length - 1:
                area.put(round(tx + ux * r), ty + dy, round(tz + uz * r), leaf)
    # coconuts
    for (cx, cz, d) in ((1, 0, 1), (-1, 0, 3), (0, 1, 2), (0, -1, 0)):
        if rng.random() < 0.5 and area.get(tx + cx, ty - 1, tz + cz) == AIR:
            area.set(tx + cx, ty - 1, tz + cz, B("cocoa", age=2, direction=d))
    return last


def cherry_tree(area, x, y, z, rng, h=None):
    h = h or rng.randint(5, 7)
    lb = log_of("cherry")
    leaf = leaves_of("cherry")
    for i in range(h):
        area.set(x, y + i, z, lb)
    tips = [(x, y + h, z)]
    for k in range(rng.randint(2, 3)):
        a = rng.random() * 6.28
        L = rng.uniform(2.5, 4)
        ex, ez = x + math.cos(a) * L, z + math.sin(a) * L
        ey = y + h + rng.randint(0, 2)
        branch(area, (x, y + h - 2, z), (round(ex), ey, round(ez)), "cherry")
        tips.append((ex, ey, ez))
    for (tx, ty, tz) in tips:
        leaf_blob(area, tx, ty + 0.5, tz, rng.uniform(2.8, 3.6), leaf, rng, flat=0.55)
        # drooping strands
        for _ in range(6):
            a = rng.random() * 6.28
            r = rng.uniform(2.0, 3.2)
            hx, hz = round(tx + math.cos(a) * r), round(tz + math.sin(a) * r)
            yy = int(ty) - 1
            if area.get(hx, yy + 1, hz) != AIR:
                for d in range(rng.randint(1, 2)):
                    area.put(hx, yy - d, hz, leaf)


def dead_tree(area, x, y, z, rng, kind="dark_oak"):
    h = rng.randint(4, 7)
    lb = B("stripped_" + kind + "_log", axis="y") if rng.random() < 0.4 else log_of(kind)
    for i in range(h):
        area.set(x, y + i, z, lb)
    for _ in range(rng.randint(1, 3)):
        a = rng.random() * 6.28
        L = rng.uniform(1.5, 3)
        sy = y + rng.randint(h // 2, h - 1)
        branch(area, (x, sy, z), (round(x + math.cos(a) * L), sy + rng.randint(1, 2), round(z + math.sin(a) * L)), kind)


def bush(area, x, y, z, rng, leaf):
    area.put(x, y, z, leaf)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if rng.random() < 0.55:
            area.put(x + dx, y, z + dz, leaf)
    if rng.random() < 0.4:
        area.put(x, y + 1, z, leaf)


def boulder(area, x, y, z, rng, r, blocks):
    for xx in range(int(x - r - 1), int(x + r + 2)):
        for yy in range(int(y - r - 1), int(y + r + 2)):
            for zz in range(int(z - r - 1), int(z + r + 2)):
                d = ((xx - x) ** 2 + ((yy - y) * 1.3) ** 2 + (zz - z) ** 2) ** 0.5
                if d <= r - rng.random() * 0.6:
                    area.set(xx, yy, zz, rng.choice(blocks))


# ---------------------------------------------------------------------------
# lights & props


def lamp_post(area, x, y, z, post, lamp, height=3, cap=None):
    """Post of `height` blocks from y, lamp on top."""
    for i in range(height):
        area.set(x, y + i, z, post)
    area.set(x, y + height, z, lamp)
    if cap is not None:
        area.set(x, y + height + 1, z, cap)


def hanging_lamp(area, x, ytop, z, length, lamp=None):
    """Chain from ytop downwards `length` blocks then a hanging lantern."""
    lamp = lamp or B("lantern", hanging=1)
    for i in range(length):
        area.set(x, ytop - i, z, B("chain"))
    area.set(x, ytop - length, z, lamp)


def crook_lamp(area, x, y, z, dx, dz, post, lamp=None, height=4):
    for i in range(height):
        area.set(x, y + i, z, post)
    area.set(x + dx, y + height - 1, z + dz, post)
    area.set(x + dx, y + height - 2, z + dz, lamp or B("lantern", hanging=1))


def wall_sign(area, x, y, z, facing, text, glow=True, kind="wall_sign", color=-16777216):
    """facing: 2=north 3=south 4=west 5=east (direction the text faces)."""
    area.set(x, y, z, B(kind, facing_direction=facing))
    area.add_be(sign_be(x, y, z, text, glow=glow, color=color))


def standing_sign(area, x, y, z, rot, text, kind="standing_sign", glow=True):
    area.set(x, y, z, B(kind, ground_sign_direction=rot))
    area.add_be(sign_be(x, y, z, text, glow=glow))


FLOWERS = ["dandelion", "poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip", "orange_tulip",
           "white_tulip", "pink_tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley"]
TALL_FLOWERS = ["sunflower", "lilac", "rose_bush", "peony"]


def tall_plant(area, x, y, z, name):
    if area.get(x, y, z) == AIR and area.get(x, y + 1, z) == AIR:
        area.set(x, y, z, B(name, upper_block_bit=0))
        area.set(x, y + 1, z, B(name, upper_block_bit=1))


def stair(name, ascend, upside=False):
    """ascend: direction the stair rises toward: 'east','west','south','north'."""
    return B(name, weirdo_direction={"east": 0, "west": 1, "south": 2, "north": 3}[ascend],
             upside_down_bit=1 if upside else 0)


def slab(name, top=False):
    return B(name, half="top" if top else "bottom")


OPP = {"east": "west", "west": "east", "north": "south", "south": "north"}
FACING_INT = {"north": 2, "south": 3, "west": 4, "east": 5}
DIRV = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}


def barrier_ring(area, cx, cz, r_in, r_out, y0, y1, p=6.0):
    """Fill air in the band r_in<d<=r_out (superellipse distance) with barrier from y0..y1."""
    bar = B("barrier")
    xs = np.arange(area.x0, area.x0 + area.sx) - cx
    zs = np.arange(area.z0, area.z0 + area.sz) - cz
    d = superdist(xs[:, None], zs[None, :], p)
    mask = (d > r_in) & (d <= r_out)
    ya, yb = y0 - area.y0, y1 - area.y0 + 1
    sub = area.blk[:, ya:yb, :]
    m3 = np.repeat(mask[:, None, :], yb - ya, axis=1) & (sub == 0)
    sub[m3] = bar
