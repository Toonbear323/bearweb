"""Norse building parts shared by the harbour and the dungeons.

Every part takes an Area plus world coordinates. Oriented parts use a Frame: local (u, v, w) where
u runs along the part's length (its 'front' direction), v is up and w runs to the part's right.
"""
import math
import random

import numpy as np

from mcw import B, AIR, PAL, sign_be, banner_be, simple_be
from gen_common import (stair, slab, leaves_of, log_of, leaf_blob, disk, ellipsoid, line_points, wall_sign,
                        standing_sign, hanging_lamp, lamp_post, boulder, spruce_tree, birch_tree, dark_oak_tree,
                        big_oak, bush, FLOWERS, tall_plant, FACING_INT)

DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
RIGHT = {"north": "east", "east": "south", "south": "west", "west": "north"}
LEFT = {v: k for k, v in RIGHT.items()}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
CARD = ["north", "east", "south", "west"]


class Frame:
    """Local -> world mapping. facing = direction local +u points to."""

    def __init__(self, area, x, y, z, facing):
        self.a, self.x, self.y, self.z, self.f = area, x, y, z, facing
        self.du = DIRS[facing]
        self.dw = DIRS[RIGHT[facing]]

    def w(self, u, v, w):
        return (self.x + self.du[0] * u + self.dw[0] * w, self.y + v, self.z + self.du[1] * u + self.dw[1] * w)

    def set(self, u, v, w, b):
        x, y, z = self.w(u, v, w)
        self.a.set(x, y, z, b)

    def put(self, u, v, w, b):
        x, y, z = self.w(u, v, w)
        self.a.put(x, y, z, b)

    def get(self, u, v, w):
        x, y, z = self.w(u, v, w)
        return self.a.get(x, y, z)

    def fill(self, u1, v1, w1, u2, v2, w2, b, only_air=False):
        for u in range(min(u1, u2), max(u1, u2) + 1):
            for v in range(min(v1, v2), max(v1, v2) + 1):
                for w in range(min(w1, w2), max(w1, w2) + 1):
                    if only_air:
                        self.put(u, v, w, b)
                    else:
                        self.set(u, v, w, b)

    def dir(self, local):
        """local direction name ('front','back','right','left') -> world cardinal."""
        return {"front": self.f, "back": OPP[self.f], "right": RIGHT[self.f], "left": LEFT[self.f]}[local]

    def stair(self, name, local, upside=False):
        return stair(name, self.dir(local), upside)

    def axis(self, local):
        """'u' or 'w' local axis -> world 'x'/'z'."""
        d = self.du if local == "u" else self.dw
        return "x" if d[0] != 0 else "z"

    def log(self, name, local="v"):
        return B(name, axis="y" if local == "v" else self.axis(local))

    def facing_int(self, local):
        return FACING_INT[self.dir(local)]

    def cardinal(self, local):
        return self.dir(local)


def wool(c):
    return B(c + "_wool")


# ---------------------------------------------------------------- small decorations
def brazier(a, x, y, z, soul=False, base="polished_blackstone"):
    """y = ground (block under the brazier stand is y-1)."""
    a.set(x, y, z, B(base + "_wall") if base + "_wall" in ("polished_blackstone_wall", "cobblestone_wall", "stone_brick_wall") else B(base))
    a.set(x, y + 1, z, B("soul_campfire" if soul else "campfire"))


def torch_post(a, x, y, z, height=2, soul=False):
    for i in range(height):
        a.set(x, y + i, z, B("spruce_fence"))
    a.set(x, y + height, z, B("soul_lantern" if soul else "lantern"))


def runestone(a, x, y, z, rng, h=None, glow=True, mat="stone"):
    """Rounded standing stone with carved rune bands; y = ground level (first block)."""
    h = h or rng.randint(4, 6)
    mats = {"stone": [B("stone"), B("andesite"), B("smooth_stone")], "dark": [B("deepslate"), B("cobbled_deepslate"), B("tuff")],
            "red": [B("red_sandstone"), B("granite"), B("smooth_red_sandstone")]}[mat]
    w2 = rng.random() < 0.5
    for i in range(h):
        for dx in (0, 1) if w2 else (0,):
            a.set(x + dx, y + i, z, mats[i % len(mats)] if i not in (1, h - 2) else B("chiseled_stone_bricks"))
    top = y + h
    if rng.random() < 0.6:
        a.set(x, top, z, B("normal_stone_slab") if mat == "stone" else B("cobbled_deepslate_slab"))
    if glow:
        side = rng.choice(["north", "south", "east", "west"])
        dx, dz = DIRS[side]
        a.put(x + dx, y + 2, z + dz, B("glow_lichen", multi_face_direction_bits={"north": 16, "south": 4, "east": 32, "west": 8}[OPP[side]]))
    a.put(x, y - 1, z, B("cobblestone"))


def banner_pole(a, x, y, z, base_color, patterns=(), height=4, facing="south"):
    for i in range(height):
        a.set(x, y + i, z, B("spruce_fence"))
    a.set(x, y + height, z, B("lantern"))
    dx, dz = DIRS[facing]
    bx, bz = x + dx, z + dz
    a.set(bx, y + height - 1, bz, B("wall_banner", facing_direction=FACING_INT[facing]))
    a.add_be(banner_be(bx, y + height - 1, bz, base_color, patterns))


def barrels(a, x, y, z, rng, n=3):
    for i in range(n):
        dx, dz = rng.randint(-1, 1), rng.randint(-1, 1)
        a.put(x + dx, y, z + dz, B("barrel", facing_direction=1))
        if rng.random() < 0.3:
            a.put(x + dx, y + 1, z + dz, B("barrel", facing_direction=rng.randint(2, 5)))


def crates(a, x, y, z, rng):
    a.put(x, y, z, B("spruce_planks"))
    a.put(x + 1, y, z, B("barrel", facing_direction=1))
    a.put(x, y + 1, z, B("hay_block", axis="x"))


def fish_rack(a, x, y, z, along="x"):
    """A-frame drying rack, 5 long."""
    for i in range(5):
        px, pz = (x + i, z) if along == "x" else (x, z + i)
        if i in (0, 4):
            for k in range(3):
                a.set(px, y + k, pz, B("spruce_fence"))
        a.set(px, y + 3, pz, B("stripped_spruce_log", axis=along))
        if 0 < i < 4:
            a.set(px, y + 2, pz, B("dried_kelp_block") if i % 2 else B("spruce_trapdoor", direction=0, open_bit=1))


# ---------------------------------------------------------------- longship
SAILS = {
    "beginner": ("white_wool", "red_wool"),
    "mid": ("white_wool", "blue_wool"),
    "high": ("black_wool", "yellow_wool"),
    "return": ("white_wool", "green_wool"),
}
SHIELDS = [("red_wool", "yellow_wool"), ("blue_wool", "white_wool"), ("yellow_wool", "black_wool"), ("white_wool", "red_wool"),
           ("green_wool", "white_wool"), ("black_wool", "red_wool")]


def longship(a, x, y, z, facing, rng, length=31, beam=9, sail="beginner", dragon=True, sail_up=True):
    """Viking longship. (x, y, z): stern end of the keel line, y = water level (top water block).
    The bow points along `facing`. Deck is at y+1 (stand at y+2).
    Returns dict(deck=box players stand in, center, bow, mast, gangway=(u-range world points on the left side))."""
    F = Frame(a, x, y, z, facing)
    L = length
    half = beam / 2.0
    plank_a, plank_b = B("spruce_planks"), B("dark_oak_planks")
    deckb = B("spruce_planks")
    rail = B("stripped_dark_oak_log", axis=F.axis("u"))
    bottom = -1
    deck_cells = []
    prof = []
    for u in range(L):
        t = (u + 0.5) / L
        hw = max(0.6, half * (math.sin(math.pi * t) ** 0.5))
        gv = 2 + int(round(4.5 * (2 * t - 1) ** 4))          # gunwale row above water
        prof.append((hw, gv))
        for v in range(bottom, gv + 1):
            f = 0.55 + 0.45 * min(1.0, (v - bottom) / 2.5)    # hull flares out above the waterline
            width = hw * f
            wmax = int(math.floor(width + 0.45))
            for w in range(-wmax, wmax + 1):
                side = abs(w) == wmax
                if v == gv:
                    if side or wmax <= 1:
                        F.set(u, v, w, rail)
                    else:
                        F.set(u, v, w, AIR)
                elif v <= 0:
                    F.set(u, v, w, plank_b if side else plank_a)          # solid below the deck
                elif v == 1:
                    F.set(u, v, w, (plank_a if (u // 3) % 2 else plank_b) if side else deckb)
                    if not side and 2 <= u <= L - 3:
                        deck_cells.append((u, w))
                else:
                    F.set(u, v, w, (plank_a if (v + u // 5) % 2 else plank_b) if side else AIR)
    # shields hung on the outside of the gunwale (midship)
    pair = SHIELDS[rng.randrange(len(SHIELDS))]
    for u in range(5, L - 5, 2):
        hw, gv = prof[u]
        wmax = int(math.floor(hw + 0.45))
        for sgn in (-1, 1):
            F.set(u, gv - 1, sgn * (wmax + 1), B(pair[(u // 2) % 2]))
    # stem (bow) and stern posts curling upwards
    hb, gb = prof[L - 1]
    for k in range(5):
        F.set(L - 1 + (1 if k >= 2 else 0), gb + k, 0, B("dark_oak_log", axis="y"))
    F.set(L, gb + 5, 0, B("dark_oak_log", axis=F.axis("u")))
    F.set(L + 1, gb + 5, 0, B("dark_oak_log", axis=F.axis("u")))
    if dragon:
        # dragon head: neck, head block, jaw, glowing eyes, horns
        F.set(L + 1, gb + 6, 0, B("dark_oak_planks"))
        F.set(L + 2, gb + 6, 0, B("dark_oak_planks"))
        F.set(L + 3, gb + 6, 0, F.stair("dark_oak_stairs", "back"))
        F.set(L + 2, gb + 5, 0, F.stair("dark_oak_stairs", "back", upside=True))
        F.set(L + 1, gb + 7, 0, F.stair("dark_oak_stairs", "front"))
        F.set(L + 2, gb + 7, 0, B("dark_oak_slab"))
        F.set(L + 1, gb + 6, -1, B("shroomlight"))
        F.set(L + 1, gb + 6, 1, B("shroomlight"))
        F.set(L, gb + 7, -1, B("dark_oak_fence"))
        F.set(L, gb + 7, 1, B("dark_oak_fence"))
    hs, gs = prof[0]
    for k in range(5):
        F.set(0 - (1 if k >= 2 else 0), gs + k, 0, B("dark_oak_log", axis="y"))
    F.set(-2, gs + 5, 0, B("dark_oak_log", axis=F.axis("u")))
    F.set(-3, gs + 5, 0, F.stair("dark_oak_stairs", "front", upside=True))
    F.set(-3, gs + 6, 0, F.stair("dark_oak_stairs", "front"))
    # mast, yard, sail
    mu = int(L * 0.45)
    mh = 15
    for v in range(1, mh):
        F.set(mu, v, 0, B("spruce_log", axis="y"))
    F.set(mu, mh, 0, B("spruce_fence"))
    F.set(mu, mh + 1, 0, B("lantern"))
    yard_v = mh - 1
    sw = int(half) + 2
    for w in range(-sw, sw + 1):
        F.set(mu + 1, yard_v, w, B("stripped_spruce_log", axis=F.axis("w")))
    s1, s2 = SAILS[sail]
    if sail_up:
        for v in range(yard_v - 8, yard_v):
            billow = 1 if yard_v - 7 <= v <= yard_v - 2 else 0
            edge_w = sw - (1 if v < yard_v - 6 else 0)
            for w in range(-edge_w + 1, edge_w):
                stripe = ((w + sw) // 2) % 2
                F.set(mu + 1 + billow, v, w, B(s2) if stripe else B(s1))
    else:
        for w in range(-sw + 1, sw):
            F.set(mu + 1, yard_v - 1, w, B(s1) if (w + 10) % 3 else B(s2))
    # oars stowed out of the oar ports, cargo on deck, steering oar on the right of the stern
    for u in range(6, L - 6, 3):
        hw, gv = prof[u]
        wmax = int(math.floor(hw + 0.45))
        for sgn in (-1, 1):
            F.set(u, 2, sgn * (wmax + 1), B("spruce_fence"))
            F.set(u, 1, sgn * (wmax + 2), B("spruce_fence"))
    for (u, w, blk) in ((mu - 3, -1, B("barrel", facing_direction=1)), (mu + 4, 1, B("barrel", facing_direction=1)),
                        (mu - 6, 1, B("chest")), (mu + 7, -1, B("hay_block", axis="y"))):
        F.set(u, 2, w, blk)
    hw0, g0 = prof[3]
    wr = int(math.floor(hw0 + 0.45)) + 1
    for v in range(-1, 4):
        F.set(2, v, wr, B("dark_oak_fence"))
    F.set(2, 4, wr, B("dark_oak_log", axis=F.axis("w")))
    us = [c[0] for c in deck_cells]
    ws = [c[1] for c in deck_cells]
    p1 = F.w(min(us), 2, min(ws))
    p2 = F.w(max(us), 4, max(ws))
    box = (min(p1[0], p2[0]), min(p1[1], p2[1]), min(p1[2], p2[2]), max(p1[0], p2[0]), max(p1[1], p2[1]), max(p1[2], p2[2]))
    left_side = [F.w(u, 1, -int(math.floor(prof[u][0] + 0.45)) - 1) for u in range(L)]
    return dict(deck=box, center=F.w(L // 2, 2, 0), bow=F.w(L + 2, gb + 6, 0), mast=F.w(mu, 2, 0), frame=F, prof=prof)


# ---------------------------------------------------------------- longhouse
def longhouse(a, x, y, z, facing, rng, length=15, width=9, turf=True, wall="spruce", door_side="front", lamp=True, interior=True):
    """Norse longhouse. (x,y,z): front-left corner at floor level (y = floor block). Roof ridge along u.
    Returns door world position (outside the door)."""
    F = Frame(a, x, y, z, facing)
    L, W = length, width
    logb = B("stripped_%s_log" % wall, axis="y") if wall != "stone" else B("stone_bricks")
    plank = B("%s_planks" % wall) if wall != "stone" else B("stone_bricks")
    roof = "dark_oak_stairs" if wall != "dark_oak" else "spruce_stairs"
    wall_h = 4
    # floor + foundation
    F.fill(0, -1, 0, L - 1, -1, W - 1, B("cobblestone"))
    F.fill(1, 0, 1, L - 2, 0, W - 2, B("spruce_planks"))
    for u in range(L):
        for w in range(W):
            edge = u in (0, L - 1) or w in (0, W - 1)
            if not edge:
                continue
            corner = u in (0, L - 1) and w in (0, W - 1)
            for v in range(0, wall_h):
                F.set(u, v, w, logb if (corner or u % 4 == 0) else plank)
    # windows (trapdoor shutters)
    for u in range(3, L - 2, 4):
        for w in (0, W - 1):
            F.set(u, 2, w, B("glass_pane"))
    # door at the front gable middle
    mw = W // 2
    door = F.w(-1, 0, mw)
    if door_side == "front":
        F.set(0, 0, mw, AIR)
        F.set(0, 1, mw, AIR)
        F.set(0, 2, mw, B("dark_oak_planks"))
        if lamp:
            F.set(-1, 2, mw - 1, B("lantern"))
            F.set(-1, 1, mw - 1, B("spruce_fence"))
            F.set(-1, 0, mw - 1, B("spruce_fence"))
    # roof: stepped stairs from both long walls to a ridge along u
    rise = (W + 1) // 2
    for u in range(-1, L + 1):
        for k in range(rise + 1):
            vv = wall_h + k
            wl, wr = -1 + k, W - k
            if wl > wr:
                break
            if wl == wr or wl + 1 == wr:
                for ww in range(wl, wr + 1):
                    F.set(u, vv, ww, B("dark_oak_slab") if not turf else B("moss_block"))
                break
            F.set(u, vv, wl, F.stair(roof, "right"))
            F.set(u, vv, wr, F.stair(roof, "left"))
            if turf and 0 <= u < L:
                for ww in range(wl + 1, wr):
                    if F.get(u, vv, ww) == AIR and (k > 0):
                        pass
        # gable walls
        if u in (0, L - 1):
            for k in range(rise):
                for ww in range(k, W - k):
                    F.put(u, wall_h + k, ww, plank)
    if turf:
        # turf layer on the roof slopes
        for u in range(-1, L + 1):
            for k in range(rise):
                for ww in (-1 + k, W - k):
                    xx, yy, zz = F.w(u, wall_h + k + 1, ww)
                    if a.get(xx, yy, zz) == AIR and rng.random() < 0.85:
                        a.set(xx, yy, zz, B("moss_carpet") if rng.random() < 0.7 else B("grass_block"))
    # crossed gable beams (dragon horns)
    for u, out in ((-1, "back"), (L, "front")):
        top = wall_h + rise
        F.set(u, top, mw - 1, F.stair("dark_oak_stairs", "left"))
        F.set(u, top, mw + 1 if W % 2 else mw, F.stair("dark_oak_stairs", "right"))
        F.set(u, top + 1, mw, B("dark_oak_fence"))
    # interior: long hearth, benches, lamps
    if interior:
        for u in range(3, L - 3):
            F.set(u, 0, mw, B("stone_bricks"))
        for u in range(4, L - 3, 4):
            F.set(u, 1, mw, B("campfire"))
        for u in range(2, L - 2):
            F.set(u, 1, 1, F.stair("spruce_stairs", "left"))
            F.set(u, 1, W - 2, F.stair("spruce_stairs", "right"))
        for u in range(2, L - 2, 4):
            xx, yy, zz = F.w(u, wall_h + 1, mw)
            a.set(xx, yy, zz, B("lantern", hanging=1))
    return door


# ---------------------------------------------------------------- terrain helpers
def surface_y(a, x, z, ymax=None):
    """Highest non-air (and non-plant) block; returns y or None."""
    ys = range((ymax or a.y0 + a.sy - 1), a.y0 - 1, -1)
    for y in ys:
        b = a.get(x, y, z)
        if b != AIR:
            n = PAL.names[b]
            if n in ("short_grass", "tall_grass", "fern", "large_fern", "snow_layer", "deadbush", "poppy", "dandelion", "sweet_berry_bush") or "leaves" in n:
                continue
            return y
    return None


def scatter_trees(a, rng, mask_fn, n, kinds, x1, z1, x2, z2, ymin=63, ymax=150, spacing=4):
    placed = []
    tries = 0
    while len(placed) < n and tries < n * 30:
        tries += 1
        x, z = rng.randint(x1, x2), rng.randint(z1, z2)
        if not mask_fn(x, z):
            continue
        if any(abs(px - x) < spacing and abs(pz - z) < spacing for px, pz in placed):
            continue
        y = surface_y(a, x, z)
        if y is None or y < ymin or y > ymax:
            continue
        top = PAL.names[a.get(x, y, z)]
        if top not in ("grass_block", "podzol", "dirt", "coarse_dirt", "moss_block", "dirt_with_roots"):
            continue
        k = kinds(rng, y) if callable(kinds) else rng.choice(kinds)
        if k == "spruce":
            spruce_tree(a, x, y + 1, z, rng, h=rng.randint(9, 15))
        elif k == "spruce_small":
            spruce_tree(a, x, y + 1, z, rng, h=rng.randint(6, 9))
        elif k == "birch":
            birch_tree(a, x, y + 1, z, rng)
        elif k == "dark_oak":
            dark_oak_tree(a, x, y + 1, z, rng)
        elif k == "bush":
            bush(a, x, y + 1, z, rng, leaves_of(rng.choice(["oak", "spruce", "azalea"])))
        a.set(x, y, z, B("dirt"))
        placed.append((x, z))
    return placed
