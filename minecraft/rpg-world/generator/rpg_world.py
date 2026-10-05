"""World container for the RPG map: one big Area, the surface heightfield, regions and registries.

Every region lives in one continuous world so all of them are linked by walkable paths:

    spawn (gacha) ─ farm
      └ cave ─ village ─ illager HQ (boss)
                 └ beach ─ deep sea (boss, under the bay)
                     └ nether ─ demon castle ─ dungeon (boss, under the castle)
                                     └ deep dark (warden habitat)

Surface regions are valleys / coast / crater carved out of one mountain heightfield;
underground regions (cave, nether cavern, monument, dungeon, deep dark) are dug into that mass.
"""
import math
import random

import numpy as np
from scipy import ndimage

from mcw import B, AIR, Area, PAL
from gen_common import fbm, smoothstep, superdist, clamp_gradient

X0, Z0, SX, SZ = -224, -96, 512, 704
Y0, SY = 0, 160
SEA = 62                     # water surface of the bay
G = 64                       # default valley floor (top block), feet at 65

BIOME = {"plains": 1, "forest": 4, "river": 7, "hell": 8, "beach": 16, "deep_ocean": 24,
         "roofed_forest": 29, "warm_ocean": 40, "lukewarm_ocean": 42, "deep_lukewarm_ocean": 43,
         "soulsand_valley": 178, "crimson_forest": 179, "warped_forest": 180, "basalt_deltas": 181,
         "stony_peaks": 189, "deep_dark": 190, "meadow": 186, "sunflower_plains": 129,
         "dripstone_caves": 188, "lush_caves": 187, "cherry_grove": 192}


def blob(X, Z, cx, cz, rx, rz, p=2.6, amp=0.10, seed=0, scale=22):
    """Noise-perturbed superellipse mask."""
    d = superdist((X - cx) / rx, (Z - cz) / rz, p)
    n = fbm(X.shape[0], X.shape[1], scale, 3, seed) - 0.5
    return d + n * 2 * amp < 1.0


def poly_mask(X, Z, pts, width):
    """Cells within width/2 of a polyline [(x,z),...]."""
    m = np.zeros(X.shape, bool)
    r2 = (width / 2.0) ** 2
    for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
        x1, x2 = sorted((ax, bx)); z1, z2 = sorted((az, bz))
        pad = width
        sl = (slice(max(0, int(x1 - pad) - X0), min(SX, int(x2 + pad) - X0 + 1)),
              slice(max(0, int(z1 - pad) - Z0), min(SZ, int(z2 + pad) - Z0 + 1)))
        xs, zs = X[sl], Z[sl]
        vx, vz = bx - ax, bz - az
        L2 = vx * vx + vz * vz or 1.0
        t = np.clip(((xs - ax) * vx + (zs - az) * vz) / L2, 0, 1)
        d2 = (xs - ax - t * vx) ** 2 + (zs - az - t * vz) ** 2
        m[sl] |= d2 <= r2
    return m


def poly_floor(X, Z, pts, heights, mask):
    """Floor height along a polyline: linear between the given point heights (nearest segment wins)."""
    out = np.zeros(X.shape)
    best = np.full(X.shape, 1e18)
    for (ax, az), (bx, bz), ha, hb in zip(pts[:-1], pts[1:], heights[:-1], heights[1:]):
        vx, vz = bx - ax, bz - az
        L2 = vx * vx + vz * vz or 1.0
        t = np.clip(((X - ax) * vx + (Z - az) * vz) / L2, 0, 1)
        d2 = (X - ax - t * vx) ** 2 + (Z - az - t * vz) ** 2
        better = (d2 < best) & mask
        out[better] = (ha + (hb - ha) * t)[better]
        best = np.where(better, d2, best)
    return np.round(out)


class World:
    def __init__(self, seed=20261005):
        self.seed = seed
        self.rng = random.Random(seed)
        self.a = Area("rpg", X0, Z0, SX, SZ, y0=Y0, sy=SY, biome=BIOME["plains"])
        xs = np.arange(SX) + X0
        zs = np.arange(SZ) + Z0
        self.X, self.Z = np.meshgrid(xs, zs, indexing="ij")
        self.open_id = np.zeros((SX, SZ), np.int16)     # 0 = mountain, else region index
        self.floor = np.full((SX, SZ), float(G))         # floor height of open cells
        self.H = np.full((SX, SZ), G, np.int32)          # surface top block
        self.water = np.zeros((SX, SZ), np.int32)        # liquid surface y (0 = none)
        self.liquid = np.full((SX, SZ), B("water"), np.int32)
        self.top = np.full((SX, SZ), B("grass_block"), np.int32)
        self.sub = np.full((SX, SZ), B("dirt"), np.int32)
        self.style = np.zeros((SX, SZ), np.int8)         # mountain style
        self.reserved = np.zeros((SX, SZ), bool)         # no random decoration here
        self.regions = {}                                # name -> dict(id, mask, style, biome)
        self.min_h = np.zeros((SX, SZ), np.int32)        # mountains at least this high (cover underground)
        # registries filled by the area builders
        self.surface_ok = np.zeros((SX, SZ), bool)       # columns where walking on the surface is allowed
        self.volumes = []                                # (name, x1, y1, z1, x2, y2, z2) allowed 3D boxes
        self.spawns = {}                                 # region -> (x, y, z) arrival point
        self.shops = []                                  # convenience spaces
        self.hunts = []                                  # hunting grounds
        self.bosses = []                                 # boss arenas
        self.gates = []                                  # region links (for the README)
        self.light_boxes = []                            # (name, x1, z1, x2, z2, y1, y2, threshold, level)
        self.markers = []                                # (x, y, z) lodestone markers for first-run setup
        self.animals = []                                # (entity, x, y, z)

    # ---------------------------------------------------------------- coords
    def li(self, x, z):
        return x - X0, z - Z0

    def gy(self, x, z):
        return int(self.H[x - X0, z - Z0])

    def rect(self, x1, z1, x2, z2):
        xa, xb = sorted((x1, x2)); za, zb = sorted((z1, z2))
        return slice(xa - X0, xb - X0 + 1), slice(za - Z0, zb - Z0 + 1)

    def allow(self, name, x1, y1, z1, x2, y2, z2):
        xa, xb = sorted((x1, x2)); ya, yb = sorted((y1, y2)); za, zb = sorted((z1, z2))
        self.volumes.append((name, xa, ya, za, xb, yb, zb))

    # --------------------------------------------------------------- regions
    def add_region(self, name, mask, floor, style=0, biome=None, top=None, sub=None):
        rid = len(self.regions) + 1
        new = mask & (self.open_id == 0)
        self.open_id[new] = rid
        if np.isscalar(floor):
            self.floor[new] = floor
        else:
            self.floor[new] = floor[new]
        if biome is not None:
            self.a.bio[mask] = BIOME[biome]
        if top is not None:
            self.top[new] = top
        if sub is not None:
            self.sub[new] = sub
        self.regions[name] = dict(id=rid, mask=new, style=style, biome=biome)
        return new

    def terrain(self):
        """Mountains everywhere that is not open; valley floors gently rise toward their rims."""
        op = self.open_id > 0
        din = ndimage.distance_transform_edt(op)
        dout, (ii, kk) = ndimage.distance_transform_edt(~op, return_indices=True)
        nearest = self.open_id[ii, kk]
        self.near_id = nearest
        fl = self.floor.copy()
        # valley bowl: up to +3 near the rim, smoothed to walkable steps
        bowl = fbm(SX, SZ, 18, 3, self.seed + 5)
        rim = (1 - smoothstep(0, 12, din)) * (1.0 + 2.5 * bowl)
        no_bowl = np.zeros_like(op)
        no_clamp = np.zeros_like(op)
        for r in self.regions.values():
            if r.get("flat"):
                no_bowl |= r["mask"]
            if r.get("noclamp"):
                no_clamp |= r["mask"]
        fl = np.where(op & ~no_bowl, fl + rim, fl)
        fl = np.round(fl).astype(np.int32)
        fl = clamp_gradient(fl, op & ~no_clamp, 1)
        # mountains
        fn = np.maximum(fl[ii, kk].astype(float), G)
        big = fbm(SX, SZ, 64, 4, self.seed + 11)
        mid = fbm(SX, SZ, 20, 3, self.seed + 12)
        small = fbm(SX, SZ, 6, 2, self.seed + 13)
        rise = 6 + np.minimum(dout * 1.1, 20) + (big * 36 + mid * 10) * smoothstep(2, 30, dout) + small * 3
        style = np.zeros((SX, SZ), np.int8)
        for r in self.regions.values():
            style[nearest == r["id"]] = r["style"]
        style = np.where((style == 1) & (dout > 26), 0, style)      # sea cliffs only near the coast
        self.style = np.where(op, 0, style)
        # jagged dark peaks / volcano get extra height
        rise = np.where(style == 3, rise * 1.15 + small * 6, rise)
        mh = np.minimum(fn + rise, SY - 8)
        mh = np.maximum(mh, self.min_h)
        self.H = np.where(op, fl, np.round(mh)).astype(np.int32)
        self.din, self.dout = din, dout

    # ---------------------------------------------------------------- paint
    def paint(self):
        a = self.a
        H = self.H
        stone, andes, tuff, grass, dirt = B("stone"), B("andesite"), B("tuff"), B("grass_block"), B("dirt")
        snow, deep = B("snow"), B("deepslate")
        coarse, gravel = B("coarse_dirt"), B("gravel")
        p = np.pad(H, 1, mode="edge")
        slope = np.maximum.reduce([np.abs(p[2:, 1:-1] - H), np.abs(p[:-2, 1:-1] - H),
                                   np.abs(p[1:-1, 2:] - H), np.abs(p[1:-1, :-2] - H)])
        n1 = fbm(SX, SZ, 9, 2, self.seed + 31)
        mount = self.open_id == 0
        top = self.top.copy()
        sub = self.sub.copy()
        st = self.style
        # normal mountains
        m0 = mount & (st == 0)
        top[m0] = np.where(slope[m0] <= 2, grass, np.where(n1[m0] > 0.55, andes, stone))
        top[m0 & (H >= 112 + (n1 * 8).astype(int))] = snow
        sub[m0] = np.where(slope[m0] <= 2, dirt, stone)
        # coast cliffs
        m1 = mount & (st == 1)
        top[m1] = np.where(slope[m1] <= 1, grass, np.where(n1[m1] > 0.5, B("sandstone"), stone))
        sub[m1] = stone
        # volcano
        m2 = mount & (st == 2)
        top[m2] = np.where(n1[m2] > 0.74, B("magma"), np.where(n1[m2] > 0.42, B("basalt"), B("blackstone")))
        sub[m2] = B("blackstone")
        # dark lands
        m3 = mount & (st == 3)
        top[m3] = np.where(n1[m3] > 0.6, B("basalt"), np.where(n1[m3] > 0.4, B("blackstone"), B("deepslate")))
        sub[m3] = B("blackstone")
        self.top_final = top
        ymax = int(H.max())
        strata_n = fbm(SX, SZ, 30, 2, self.seed + 33)
        for y in range(1, ymax + 1):
            lay = a.blk[:, y - Y0, :]
            deep_m = y <= H - 4
            sub_m = (y > H - 4) & (y < H)
            top_m = y == H
            base = deep if y < 20 + int(4 * math.sin(y)) else stone
            lay[deep_m] = base
            # stone strata in mountain faces
            if y >= 40:
                band = ((y + (strata_n * 9).astype(int)) % 11 == 0) & mount & deep_m
                lay[band & (st == 0)] = tuff
                lay[band & (st == 2)] = B("basalt", axis="y")
                lay[band & (st == 3)] = B("deepslate")
            lay[sub_m] = sub[sub_m]
            lay[top_m] = top[top_m]
        wm = self.water > 0
        if wm.any():
            for y in range(1, int(self.water.max()) + 1):
                lay = a.blk[:, y - Y0, :]
                m = wm & (y > H) & (y <= self.water)
                lay[m] = self.liquid[m]

    # ----------------------------------------------------------- utilities
    def surface_y(self, x, z):
        """Feet y on the current blocks (first air above the highest solid-ish block at/below H+30)."""
        a = self.a
        top = a.column_top(x, z, ymax=self.gy(x, z) + 30)
        return (top or 0) + 1

    def mark_surface(self, mask):
        self.surface_ok |= mask
