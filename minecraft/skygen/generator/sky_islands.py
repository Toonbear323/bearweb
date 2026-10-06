"""The ability-tag maps rebuilt as floating islands (no boundary cliffs, no invisible walls).

forest  -> wood + stone mines      volcano -> gold + diamond mines
paradise-> residential plots       library -> enchanting library
skeld   -> coal + iron mines + personal furnace rooms (ship floating in the sky)
"""
import math
import random

import numpy as np

import gen_mapbase
import gen_paradise
import gen_volcano
import gen_forest
from mcw import B, AIR
from gen_mapbase import SIZE
from gen_forest import Forest
from gen_volcano import Volcano
from gen_paradise import Paradise
from gen_skeld import Skeld
from gen_library import Library, BX, BZ, F1
from gen_common import (fbm, superdist, oak_tree, birch_tree, spruce_tree, dark_oak_tree, big_oak)
from sky_world import coast_mask, shape_island


def _no_cove(m, *args, **kw):
    return np.full((SIZE, SIZE), 1e9)


# the lava/water pools under the old cliff cascades make no sense without cliffs
gen_paradise.cove = _no_cove
gen_volcano.cove = _no_cove


class SkyMixin:
    """Map without its boundary: no cliffs, cascades or barrier ring."""

    def make_cliffs(self, *args, **kw):
        self.wall = np.zeros((SIZE, SIZE), bool)
        self.wall_start = np.full((SIZE, SIZE), float(self.R + 40))
        self.wall_t = self.D - (self.R + 40)

    def barrier(self, *args, **kw):
        pass

    def cliff_top_trees(self):
        pass

    def waterfall_feature(self):
        pass

    def falls(self):
        pass


def solidify_below(W, x0, z0, foot, bottom_y=32):
    """Fill the air under each footprint column up to its lowest block (thin floors become solid ground)."""
    a = W.a
    sx, sz = foot.shape
    V = W.view(x0, z0, sx, sz)
    ys = W.ys()
    j0 = bottom_y - a.y0
    nonair = V[:, j0:, :] != AIR
    has = nonair.any(axis=1)
    first = np.argmax(nonair, axis=1) + j0
    for (i, k) in np.argwhere(foot & has):
        f = first[i, k]
        if f > j0:
            V[i, j0:f, k] = B("stone")
    return first


def under_rock(mats, accent=None, accent_chance=0.0, soil=None):
    def f(rng, x, y, z, dg):
        if soil is not None and dg <= 3:
            return soil
        if accent is not None and rng.random() < accent_chance:
            return accent
        return mats[(y // 3 + (x * 7 + z * 13) % 3) % len(mats)]
    return f


def ground_heights(W, x0, z0, sx, sz, ymax=150):
    """Highest solid-ish block per column (for islands built as buildings)."""
    a = W.a
    V = W.view(x0, z0, sx, sz)
    nonair = V != AIR
    has = nonair.any(axis=1)
    top = a.sy - 1 - np.argmax(nonair[:, ::-1, :], axis=1)
    return np.where(has, top + a.y0, 0)


# ============================================================================ islands from MapBase maps

class SkyForest(SkyMixin, Forest):
    R_SKY = 90

    def __init__(self, cx, cz, gens=None):
        Forest.__init__(self, cx, cz)
        self.R = self.R_SKY
        self.gens = gens

    def build(self):
        from sky_features import lumber_camp, quarry
        self.terrain()
        self.paint()
        self.world_tree()
        self.satellites()
        self.watchtower(42, -40)
        self.cabin(-48, -8)
        self.pond_details()
        self.stream_bridges()
        self.reserved[(self.DX - 38) ** 2 + (self.DZ - 40) ** 2 <= 15 ** 2] = True
        self.reserved[(np.abs(self.DX + 42) <= 14) & (np.abs(self.DZ + 44) <= 13)] = True
        self.reserved[(np.abs(self.DX) <= 7) & (self.DZ >= 72)] = True
        self.trees()
        self.undergrowth()
        self.lamps()
        self.camp = lumber_camp(self, self.gens)
        self.quarry_spot = quarry(self, self.gens)
        self.a.fix_walls()
        return self.a

    def trees(self):
        """Thinner forest than the tag map: room for fights and the lumber camp."""
        a = self.a
        rng = self.rng
        big = self.scatter(16, 22, lambda x, z: self.ok_spot(x, z, margin=8) and math.hypot(x, z) > 20)
        for (dx, dz) in big:
            x, z = self.w(dx, dz)
            big_oak(a, x, self.gy(x, z) + 1, z, rng, glow=B("shroomlight"))
            self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 30] = True
        pts = self.scatter(170, 8.5, lambda x, z: self.ok_spot(x, z, margin=5) and math.hypot(x, z) > 16)
        for (dx, dz) in pts:
            x, z = self.w(dx, dz)
            y = self.gy(x, z) + 1
            r = rng.random()
            if dz < -30:
                (spruce_tree if r < 0.6 else oak_tree if r < 0.85 else birch_tree)(a, x, y, z, rng)
            elif dx < -30:
                (birch_tree if r < 0.45 else oak_tree if r < 0.8 else dark_oak_tree)(a, x, y, z, rng)
            else:
                if r < 0.55:
                    oak_tree(a, x, y, z, rng)
                elif r < 0.8:
                    birch_tree(a, x, y, z, rng)
                else:
                    dark_oak_tree(a, x, y, z, rng)
            i, k = x - self.a.x0, z - self.a.z0
            self.reserved[max(0, i - 1):i + 2, max(0, k - 1):k + 2] = True


class SkyVolcano(SkyMixin, Volcano):
    R_SKY = 86

    def __init__(self, cx, cz):
        Volcano.__init__(self, cx, cz)
        self.R = self.R_SKY

    def build(self):
        self.terrain()
        self.paint()
        self.road_details()
        self.crater_details()
        self.lava_tube()
        self.temple(40, 42)
        self.pillars()
        self.spires()
        self.ash_field()
        self.bridges()
        self.decorate()
        self.a.fix_walls()
        return self.a


class SkyParadise(SkyMixin, Paradise):
    R_SKY = 100

    def __init__(self, cx, cz):
        Paradise.__init__(self, cx, cz)
        self.R = self.R_SKY

    def build(self):
        self.terrain()
        self.paint()
        self.reef()
        self.gazebo()
        self.island_falls()
        self.boardwalks()
        self.tiki_bar(52, 2)
        self.huts()
        self.beach_props()
        self.lifeguard_tower(-8, 58)
        self.rock_arch()
        self.trees()
        self.flora()
        self.lights()
        self.a.fix_walls()
        return self.a


class SkySkeld(Skeld):
    def space(self):
        pass                # no starfield box: the ship floats in the open sky


# ============================================================================ placing islands

def place_mapbase(W, m, seed, under, max_depth=30, spikes=10, wobble=4.0, extra=3.0, force=()):
    """Paste a MapBase map and cut it into an island; returns (foot, bottom) in the map's local grid.
    force: world-coordinate boxes (x1, z1, x2, z2) that stay part of the island (bridge landings)."""
    W.paste(m.a)
    foot = coast_mask(m.DX, m.DZ, m.R, m.p, seed, wobble=wobble, extra=extra)
    for (x1, z1, x2, z2) in force:
        X = m.DX + m.cx
        Z = m.DZ + m.cz
        foot |= (X >= x1) & (X <= x2) & (Z >= z1) & (Z <= z2)
    solidify_below(W, m.a.x0, m.a.z0, foot)        # the tag maps were only painted from y 46 up
    H = m.H.copy()
    H = np.where(m.water > 0, np.maximum(H, m.water), H)
    bottom = shape_island(W, m.a.x0, m.a.z0, foot, H, seed, under, max_depth=max_depth, spikes=spikes)
    return foot, bottom


def library_island(W, lib, seed, R=96, force=()):
    W.paste(lib.a)
    lx = np.arange(lib.a.sx) + lib.a.x0 - lib.cx
    lz = np.arange(lib.a.sz) + lib.a.z0 - lib.cz
    DX, DZ = np.meshgrid(lx, lz, indexing="ij")
    foot = coast_mask(DX, DZ, R, 8.0, seed, wobble=3.0, extra=2.0)
    foot |= (np.abs(DX) <= BX + 6) & (np.abs(DZ) <= BZ + 6)
    for (x1, z1, x2, z2) in force:
        foot |= (DX + lib.cx >= x1) & (DX + lib.cx <= x2) & (DZ + lib.cz >= z1) & (DZ + lib.cz <= z2)
    solidify_below(W, lib.a.x0, lib.a.z0, foot)
    H = np.full(foot.shape, F1, np.int32)
    under = under_rock([B("stone"), B("andesite"), B("stone"), B("tuff")], accent=B("moss_block"), accent_chance=0.05)
    bottom = shape_island(W, lib.a.x0, lib.a.z0, foot, H, seed, under, max_depth=32, spikes=12)
    return foot, bottom, DX, DZ
