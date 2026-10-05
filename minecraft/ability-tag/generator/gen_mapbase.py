"""Common machinery for the four game maps (terrain, boundary cliffs, barriers, paths, water)."""
import math
import random

import numpy as np

from mcw import B, AIR, Area, physics_tables
from gen_common import fbm, smoothstep, blur, clamp_gradient, superdist, barrier_ring, line_points

SIZE = 224
HALF = 112


def catmull(points, step=0.5):
    """Sample a Catmull-Rom spline through points [(x,z),...]."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        seg = math.dist(p1, p2)
        n = max(2, int(seg / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            z = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, z))
    out.append(points[-1])
    return out


def poisson(rng, w, h, r, k=20, accept=None, max_pts=100000):
    """Bridson-ish dart throwing in [0,w)x[0,h). accept(x,z)->bool filters."""
    cell = r / math.sqrt(2)
    gw, gh = int(w / cell) + 1, int(h / cell) + 1
    grid = [[None] * gh for _ in range(gw)]
    pts = []
    tries = 0
    while tries < k * 400 and len(pts) < max_pts:
        tries += 1
        x, z = rng.uniform(0, w), rng.uniform(0, h)
        gx, gz = int(x / cell), int(z / cell)
        ok = True
        for ix in range(max(0, gx - 2), min(gw, gx + 3)):
            for iz in range(max(0, gz - 2), min(gh, gz + 3)):
                q = grid[ix][iz]
                if q is not None and (q[0] - x) ** 2 + (q[1] - z) ** 2 < r * r:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        if accept is not None and not accept(x, z):
            continue
        grid[gx][gz] = (x, z)
        pts.append((x, z))
        tries = 0
    return pts


class MapBase:
    def __init__(self, name, cx, cz, seed, biome, R=76, H0=64, p=6.0):
        self.name = name
        self.p = p
        self.cx, self.cz = cx, cz
        self.R = R
        self.H0 = H0
        self.seed = seed
        self.rng = random.Random(seed)
        self.a = Area(name, cx - HALF, cz - HALF, SIZE, SIZE, y0=32, sy=112, biome=biome)
        lx = np.arange(SIZE) + self.a.x0 - cx
        lz = np.arange(SIZE) + self.a.z0 - cz
        self.DX, self.DZ = np.meshgrid(lx, lz, indexing="ij")
        self.D = superdist(self.DX, self.DZ, p)
        self.H = np.full((SIZE, SIZE), H0, np.int32)
        self.top = np.full((SIZE, SIZE), B("grass_block"), np.int32)
        self.sub = np.full((SIZE, SIZE), B("dirt"), np.int32)
        self.deep = np.full((SIZE, SIZE), B("stone"), np.int32)
        self.water = np.zeros((SIZE, SIZE), np.int32)     # water surface y (0 = none)
        self.liquid = np.full((SIZE, SIZE), B("water"), np.int32)
        self.reserved = np.zeros((SIZE, SIZE), bool)      # no trees / props
        self.path = np.zeros((SIZE, SIZE), bool)
        self.wall = np.zeros((SIZE, SIZE), bool)
        self.wall_start = np.full((SIZE, SIZE), float(R))
        self.spawns = []
        self.pois = {}
        self.strata = None

    # coordinates ----------------------------------------------------------
    def w(self, dx, dz):
        return self.cx + dx, self.cz + dz

    def li(self, x, z):
        return x - self.a.x0, z - self.a.z0

    def gy(self, x, z):
        i, k = self.li(x, z)
        return int(self.H[i, k])

    def inside(self, x, z):
        i, k = self.li(x, z)
        if not (0 <= i < SIZE and 0 <= k < SIZE):
            return False
        return self.D[i, k] <= self.R + 0.5

    def interior(self, x, z, margin=0):
        i, k = self.li(x, z)
        if not (0 <= i < SIZE and 0 <= k < SIZE):
            return False
        return self.D[i, k] < self.wall_start[i, k] - margin and not self.wall[i, k]

    # terrain --------------------------------------------------------------
    def make_cliffs(self, base_jump=10, top=24, width=16, amp=7, bulge=4.0, seed_off=0, outer_drop=1.2):
        n1 = fbm(SIZE, SIZE, 24, 4, self.seed + 11 + seed_off)
        n2 = fbm(SIZE, SIZE, 10, 3, self.seed + 23 + seed_off)
        nb = fbm(SIZE, SIZE, 30, 3, self.seed + 37 + seed_off)
        start = self.R - bulge * nb
        self.wall_start = start
        t = self.D - start
        wall_h = self.H0 + base_jump + (top - base_jump) * smoothstep(0, 7, t) + (n1 - 0.5) * 2 * amp + (n2 - 0.5) * 4
        wall_h = np.maximum(wall_h, self.H0 + base_jump)
        beyond = np.maximum(0, t - width)
        wall_h = wall_h - beyond * outer_drop
        wall_h = np.maximum(wall_h, self.H0 + 2)
        self.wall = t > 0
        # guarantee the barrier ring sits inside solid cliff
        self.wall |= self.D > self.R - 0.5
        self.H = np.where(self.wall, np.maximum(self.H, np.round(wall_h).astype(np.int32)), self.H)
        self.wall_t = t

    def flatten(self, dx, dz, r, h=None, square=False, blend=3):
        """Flatten a pad around local (dx,dz) to height h (default: median)."""
        m = (np.maximum(np.abs(self.DX - dx), np.abs(self.DZ - dz)) if square
             else np.sqrt((self.DX - dx) ** 2 + (self.DZ - dz) ** 2))
        core = m <= r
        if h is None:
            h = int(np.median(self.H[core]))
        ring = (m > r) & (m <= r + blend)
        tt = (m[ring] - r) / blend
        self.H[core] = h
        self.H[ring] = np.round(h * (1 - tt) + self.H[ring] * tt).astype(np.int32)
        return h

    def paint(self, ybase=46):
        a = self.a
        top_y = int(self.H.max())
        st = self.strata
        for y in range(ybase, top_y + 1):
            lay = a.blk[:, y - a.y0, :]
            m_top = self.H == y
            m_sub = (self.H - 4 < y) & (y < self.H)
            m_deep = y <= self.H - 4
            lay[m_deep] = self.deep[m_deep]
            lay[m_sub] = self.sub[m_sub]
            lay[m_top] = self.top[m_top]
            if st is not None:
                mw = self.wall & (y <= self.H) & (y >= self.H0 - 2)
                if mw.any():
                    lay[mw] = st(y)[mw]
        # water / lava
        wm = self.water > 0
        for y in range(ybase, int(self.water.max()) + 1 if wm.any() else ybase):
            lay = a.blk[:, y - a.y0, :]
            m = wm & (y > self.H) & (y <= self.water)
            lay[m] = self.liquid[m]

    def barrier(self, y_top=None):
        barrier_ring(self.a, self.cx, self.cz, self.R + 0.5, self.R + 1.6, self.H0 - 4,
                     y_top or self.H0 + 60, p=self.p)

    def walkable_smooth(self, mask=None):
        """Limit height steps on land to 1 (water surfaces count as their surface level)."""
        land = (~self.wall) & (self.D < self.R + 1)
        if mask is not None:
            land &= mask
        Hs = np.where(self.water > 0, self.water, self.H)
        Hs = clamp_gradient(Hs, land & (self.water == 0), 1)
        self.H = np.where(self.water > 0, self.H, Hs)

    # paths & water ------------------------------------------------------------
    def raster_path(self, pts, width=2.0, jitter=0.6, mark=True):
        rr = self.rng
        cells = set()
        for (x, z) in pts:
            wdt = width + rr.uniform(-jitter, jitter)
            for ix in range(int(x - wdt - 1), int(x + wdt + 2)):
                for iz in range(int(z - wdt - 1), int(z + wdt + 2)):
                    if (ix - x) ** 2 + (iz - z) ** 2 <= wdt * wdt * 0.5:
                        cells.add((ix, iz))
        out = []
        for (dx, dz) in cells:
            i, k = dx + self.cx - self.a.x0, dz + self.cz - self.a.z0
            if 0 <= i < SIZE and 0 <= k < SIZE and not self.wall[i, k]:
                if mark:
                    self.path[i, k] = True
                out.append((dx, dz))
        return out

    def carve_river(self, pts, width_fn, depth_fn, wl, bank=4):
        """pts in local coords. Lowers terrain, fills water to level wl (surface block y)."""
        dist = np.full((SIZE, SIZE), 1e9)
        for (x, z) in pts[::2]:
            i0, k0 = int(x + self.cx - self.a.x0), int(z + self.cz - self.a.z0)
            r = 12
            i1, i2 = max(0, i0 - r), min(SIZE, i0 + r + 1)
            k1, k2 = max(0, k0 - r), min(SIZE, k0 + r + 1)
            sub = np.sqrt((self.DX[i1:i2, k1:k2] - x) ** 2 + (self.DZ[i1:i2, k1:k2] - z) ** 2)
            dist[i1:i2, k1:k2] = np.minimum(dist[i1:i2, k1:k2], sub)
        return dist

    def apply_water_body(self, dist, half_width, wl, max_depth=2, bank=5, liquid=None):
        inner = (dist <= half_width) & ~self.wall
        depth = np.clip(np.round((1 - dist / max(half_width, 0.1)) * max_depth + 0.6), 1, max_depth).astype(np.int32)
        self.H = np.where(inner, np.minimum(self.H, wl - depth), self.H)
        self.water = np.where(inner, wl, self.water)
        if liquid is not None:
            self.liquid = np.where(inner, liquid, self.liquid)
        # banks: slope down to wl (ground surface y = wl means standing just above water)
        bandm = (dist > half_width) & (dist <= half_width + bank) & ~self.wall
        tt = np.clip((dist - half_width) / bank, 0, 1)
        target = np.round(wl + tt * (self.H - wl)).astype(np.int32)
        self.H = np.where(bandm, np.minimum(self.H, np.maximum(target, wl)), self.H)
        self.reserved |= dist <= half_width + 1.5

    # misc -----------------------------------------------------------------
    def column_free(self, x, z, h=3):
        y = self.gy(x, z)
        return all(self.a.get(x, y + k, z) == AIR for k in range(1, h + 1))

    def scatter(self, n, r, accept, margin=3):
        R = self.R - margin
        pts = poisson(self.rng, 2 * R, 2 * R, r,
                      accept=lambda x, z: accept(int(round(x - R)), int(round(z - R))))
        return [(int(round(x - R)), int(round(z - R))) for (x, z) in pts[:n]]

    def ok_spot(self, dx, dz, margin=4, allow_path=False):
        i, k = dx + self.cx - self.a.x0, dz + self.cz - self.a.z0
        if not (0 <= i < SIZE and 0 <= k < SIZE):
            return False
        if self.wall[i, k] or self.D[i, k] > self.wall_start[i, k] - margin:
            return False
        if self.reserved[i, k] or (self.path[i, k] and not allow_path) or self.water[i, k]:
            return False
        return True


def _ang_diff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def cascade(m, angle_deg, half_width, top_y, base_y, src, flow, rim_block, fill_base=False):
    """Waterfall / lavafall pouring out of the boundary cliff at a given angle (deg, 0 = +x).
    The falling column sits just behind the barrier ring so it is visible but unreachable."""
    a = m.a
    ang = math.radians(angle_deg)
    hw = half_width / m.R
    A = np.arctan2(m.DZ, m.DX)
    win = np.abs(((A - ang + np.pi) % (2 * np.pi)) - np.pi) <= hw
    col = win & (m.D > m.R + 1.7) & (m.D <= m.R + 3.3)
    notch = win & m.wall & (m.D <= m.R + 1.7)
    ca, sa = math.cos(ang), math.sin(ang)
    for (i, k) in np.argwhere(notch):
        x, z = i + a.x0, k + a.z0
        floor = base_y
        if m.D[i, k] <= m.R + 0.6:
            # match the floor of the walkable ground just inside, so the notch is never a pit
            for step in range(1, 8):
                ii, kk = int(round(i - ca * step)), int(round(k - sa * step))
                if 0 <= ii < SIZE and 0 <= kk < SIZE and not m.wall[ii, kk]:
                    floor = max(base_y, int(m.H[ii, kk]) if m.water[ii, kk] == 0 else base_y)
                    break
        for y in range(floor + 1, top_y + 2):
            a.set(x, y, z, AIR)
        for y in range(base_y, floor + 1):
            a.set(x, y, z, rim_block)
    for (i, k) in np.argwhere(col):
        x, z = i + a.x0, k + a.z0
        a.set(x, top_y, z, src)
        for y in range(base_y + 1, top_y):
            a.set(x, y, z, flow)
        a.set(x, base_y, z, src if fill_base else rim_block)
        if fill_base:
            a.set(x, base_y - 1, z, rim_block)
        a.set(x, top_y + 1, z, rim_block)
        # make sure the source is enclosed behind/sides
    ring = win & (m.D > m.R + 3.3) & (m.D <= m.R + 4.5)
    for (i, k) in np.argwhere(ring):
        x, z = i + a.x0, k + a.z0
        for y in range(base_y, top_y + 2):
            if a.get(x, y, z) == AIR:
                a.set(x, y, z, rim_block)
    side = (np.abs(((A - ang + np.pi) % (2 * np.pi)) - np.pi) <= hw + 1.6 / m.R) & ~win & \
        (m.D > m.R + 1.7) & (m.D <= m.R + 3.3)
    for (i, k) in np.argwhere(side):
        x, z = i + a.x0, k + a.z0
        for y in range(base_y, top_y + 2):
            if a.get(x, y, z) == AIR:
                a.set(x, y, z, rim_block)
    cx = m.cx + round(math.cos(ang) * (m.R - 2))
    cz = m.cz + round(math.sin(ang) * (m.R - 2))
    return cx, cz


def cove(m, angle_deg, half_width, pool_r, level, liquid, depth=1):
    """Open a small cove in the cliff bulge at the base of a cascade and put a pool there."""
    ang = math.radians(angle_deg)
    A = np.arctan2(m.DZ, m.DX)
    win = np.abs(((A - ang + np.pi) % (2 * np.pi)) - np.pi) <= (half_width + 3) / m.R
    opened = win & m.wall & (m.D <= m.R - 0.5)
    m.wall &= ~opened
    m.H = np.where(opened & (m.H > m.H0 + 1), m.H0 + 1, m.H)
    pcx, pcz = math.cos(ang) * (m.R - pool_r + 0.5), math.sin(ang) * (m.R - pool_r + 0.5)
    d = np.sqrt((m.DX - pcx) ** 2 + (m.DZ - pcz) ** 2)
    m.apply_water_body(d, pool_r, level, max_depth=depth, bank=4, liquid=liquid)
    return d


def bridge(area, p0, p1, f0, f1, deck, slab_b, rail, post=None, lamp=None, width=3, lamp_every=6):
    """Straight bridge between local-world points p0,p1 (x,z) with floor heights f0,f1 (world y of
    the walking surface, may be .5). Builds planks/slabs + fence rails."""
    (x0, z0), (x1, z1) = p0, p1
    n = max(1, int(round(max(abs(x1 - x0), abs(z1 - z0)))))
    dxs = (x1 - x0) / n
    dzs = (z1 - z0) / n
    horiz = abs(x1 - x0) >= abs(z1 - z0)
    half = width // 2
    placed = []
    for k in range(n + 1):
        cx_ = x0 + dxs * k
        cz_ = z0 + dzs * k
        f = f0 + (f1 - f0) * k / n
        f2 = int(round(f * 2))
        for o in range(-half, half + 1):
            x = int(round(cx_)) + (0 if horiz else o)
            z = int(round(cz_)) + (o if horiz else 0)
            if f2 % 2 == 0:
                area.set(x, f2 // 2 - 1, z, deck)
                feet = f2 // 2
            else:
                area.set(x, (f2 - 1) // 2, z, slab_b)
                feet = (f2 - 1) // 2 + 1
            for c in range(feet, feet + 3):
                if area.get(x, c, z) != AIR and c > feet:
                    pass
            area.set(x, feet, z, AIR)
            area.set(x, feet + 1, z, AIR)
            if abs(o) == half and rail is not None:
                rx = x + (0 if horiz else (1 if o > 0 else -1))
                rz = z + ((1 if o > 0 else -1) if horiz else 0)
                if f2 % 2 == 0:
                    area.set(rx, feet - 1, rz, deck)
                else:
                    area.set(rx, feet - 1, rz, slab_b)
                area.set(rx, feet, rz, rail)
                if lamp is not None and k % lamp_every == lamp_every // 2:
                    area.set(rx, feet + 1, rz, rail)
                    area.set(rx, feet + 2, rz, lamp)
        placed.append((int(round(cx_)), f, int(round(cz_))))
    return placed
