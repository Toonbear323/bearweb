"""Skygen features built into the islands: generator blocks, mines, furnace rooms, plots, enchanting.

Generator blocks ("생성기"): ore/log/stone blocks that come back a few seconds after they are mined.
Players are in adventure mode; every generator column has a hidden allow block right under it, so the
generator itself can be mined and nothing else around it (the script also cancels everything else).
"""
import math
import random

import numpy as np

from mcw import B, AIR, simple_be, sign_be
from gen_common import (stair, slab, lamp_post, wall_sign, standing_sign, leaf_blob, leaves_of, fbm,
                        hanging_lamp, FLOWERS)

GEN_KINDS = {
    # kind: (seconds until it grows back, display name)
    "wood": (6, "원목"),
    "stone": (4, "돌"),
    "coal": (8, "석탄"),
    "iron": (12, "철"),
    "gold": (16, "금"),
    "diamond": (25, "다이아몬드"),
}


class Gens:
    """Collects generator blocks while islands are built (world coordinates)."""

    def __init__(self):
        self.items = {}            # (x, y, z) -> (block name, kind, island)

    def add(self, area, x, y, z, block, kind, island):
        area.set(x, y, z, B(block))
        self.items[(x, y, z)] = (block, kind, island)

    def finalize(self, area):
        """Hidden allow block under the lowest generator of every column."""
        cols = {}
        for (x, y, z) in self.items:
            cols[(x, z)] = min(y, cols.get((x, z), 10 ** 6))
        allow = B("allow")
        for (x, z), y in cols.items():
            if (x, y - 1, z) in self.items:
                continue
            area.set(x, y - 1, z, allow)
        return len(cols)

    def export(self):
        return [dict(x=x, y=y, z=z, block=b, kind=k, island=i, regen=GEN_KINDS[k][0])
                for (x, y, z), (b, k, i) in sorted(self.items.items())]


# ============================================================================ forest: lumber camp + quarry

def lumber_camp(m, gens, dx=38, dz=40):
    a = m.a
    rng = random.Random(31)
    cx, cz = m.w(dx, dz)
    h = m.gy(cx, cz)
    # clear the pad and pave it with wood chips
    for x in range(cx - 13, cx + 14):
        for z in range(cz - 13, cz + 14):
            r = math.hypot(x - cx, z - cz)
            if r > 13:
                continue
            g = m.gy(x, z)
            for y in range(g + 1, g + 18):
                if a.get(x, y, z) != AIR:
                    a.set(x, y, z, AIR)
            if r <= 12:
                for y in range(h + 1, g + 1):
                    a.set(x, y, z, AIR)
                for y in range(g + 1, h + 1):
                    a.set(x, y, z, B("dirt"))
                k = rng.random()
                a.set(x, h, z, B("coarse_dirt") if k < 0.45 else B("podzol") if k < 0.7 else B("dirt_with_roots") if k < 0.85 else B("mud_bricks"))
                m.H[x - a.x0, z - a.z0] = h
    woods = ["oak_log", "birch_log", "spruce_log", "dark_oak_log"]
    leaves = ["oak_leaves", "birch_leaves", "spruce_leaves", "dark_oak_leaves"]
    for row, (wood, leaf) in enumerate(zip(woods, leaves)):
        for col in range(4):
            x, z = cx - 5 + col * 3, cz - 5 + row * 3
            for y in range(h + 1, h + 4):
                gens.add(a, x, y, z, wood, "wood", "forest")
            # small leafy crown so the rows read as young trees
            for (ox, oz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                a.set(x + ox, h + 5, z + oz, B(leaf, persistent_bit=1))
            a.set(x, h + 4, z, B(leaf, persistent_bit=1))
            a.set(x, h + 6, z, B(leaf, persistent_bit=1))
    # sawmill shed on the north side: posts, plank roof, log piles, barrels
    sx1, sx2, sz1, sz2 = cx - 6, cx + 6, cz - 12, cz - 9
    for (x, z) in ((sx1, sz1), (sx2, sz1), (sx1, sz2), (sx2, sz2)):
        for y in range(h + 1, h + 5):
            a.set(x, y, z, B("stripped_spruce_log", axis="y"))
    for x in range(sx1 - 1, sx2 + 2):
        for z in range(sz1 - 1, sz2 + 2):
            a.set(x, h + 5, z, B("spruce_slab", half="bottom") if z in (sz1 - 1, sz2 + 1) else B("spruce_planks"))
    for x in range(sx1 + 1, sx2):
        a.set(x, h + 1, sz1, B("stripped_oak_log", axis="x"))
        a.set(x, h + 2, sz1, B("stripped_birch_log", axis="x") if x % 2 else B("stripped_oak_log", axis="x"))
    for x in (sx1 + 1, sx2 - 1):
        a.set(x, h + 1, sz2, B("barrel", facing_direction=1))
    a.set(cx, h + 1, sz2, B("stonecutter_block", cardinal="south"))
    a.set(cx, h + 4, sz2 - 1, B("lantern", hanging=1))
    # chopping blocks with an axe-ish look
    for (x, z) in ((cx + 8, cz + 8), (cx - 8, cz + 8)):
        a.set(x, h + 1, z, B("stripped_oak_log", axis="y"))
    for (x, z) in ((cx - 9, cz - 3), (cx + 9, cz - 3), (cx - 9, cz + 5), (cx + 9, cz + 5)):
        lamp_post(a, x, h + 1, z, B("spruce_fence"), B("lantern"), height=3)
    a.set(cx, h + 1, cz + 9, B("spruce_planks"))
    standing_sign(a, cx, h + 2, cz + 9, 0, "§l§2벌목장\n§r§f원목 생성기 16개\n§7캐면 6초 뒤 다시 자라요",
                  kind="spruce_standing_sign")
    m.reserved[(m.DX - dx) ** 2 + (m.DZ - dz) ** 2 <= 14 ** 2] = True
    return (cx, h + 1, cz)


def quarry(m, gens, dx=-42, dz=-44):
    a = m.a
    rng = random.Random(32)
    cx, cz = m.w(dx, dz)
    h = m.gy(cx, cz)
    x1, x2, z1, z2 = cx - 6, cx + 6, cz - 5, cz + 5          # pit interior
    # level and clear the surroundings
    for x in range(cx - 12, cx + 13):
        for z in range(cz - 11, cz + 12):
            g = m.gy(x, z)
            for y in range(min(g, h) + 1, max(g, h) + 18):
                a.set(x, y, z, AIR)
            for y in range(g + 1, h + 1):
                a.set(x, y, z, B("dirt"))
            a.set(x, h, z, B("gravel") if rng.random() < 0.35 else B("coarse_dirt") if rng.random() < 0.5 else B("grass_block"))
            m.H[x - a.x0, z - a.z0] = h
    floor = h - 3
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(floor + 1, h + 1):
                a.set(x, y, z, AIR)
            a.set(x, floor, z, B("gravel") if (x + z) % 3 == 0 else B("cobblestone") if (x * z) % 4 == 0 else B("stone"))
    # generator faces: north wall and the two side walls, two high
    for x in range(x1, x2 + 1):
        for y in (floor + 1, floor + 2):
            gens.add(a, x, y, z1 - 1, "stone", "stone", "forest")
    for z in range(z1, z2 - 1):
        for y in (floor + 1, floor + 2):
            gens.add(a, x1 - 1, y, z, "stone", "stone", "forest")
            gens.add(a, x2 + 1, y, z, "stone", "stone", "forest")
    # stone rim course
    for x in range(x1 - 1, x2 + 2):
        for z in (z1 - 1, z2 + 1):
            if a.get(x, h, z) != AIR:
                a.set(x, h, z, B("cobblestone"))
    for z in range(z1 - 1, z2 + 2):
        for x in (x1 - 1, x2 + 1):
            if a.get(x, h, z) != AIR:
                a.set(x, h, z, B("cobblestone"))
    # stairs down on the south side (3 wide)
    for i, y in enumerate((h, h - 1, h - 2)):
        z = z2 + 1 - i
        for x in range(cx - 1, cx + 2):
            for yy in range(y, h + 3):
                a.set(x, yy, z, AIR)
            a.set(x, y - 1, z, stair("stone_stairs", "south") if False else B("cobblestone"))
            a.set(x, y, z, stair("stone_stairs", "south"))
    # timber crane at the north-east corner
    for y in range(h + 1, h + 8):
        a.set(x2 + 2, y, z1 - 2, B("spruce_log", axis="y"))
    for t in range(0, 6):
        a.set(x2 + 2 - t, h + 8, z1 - 2, B("spruce_log", axis="x"))
    for y in range(h + 4, h + 8):
        a.set(x2 - 3, y, z1 - 2, B("chain"))
    a.set(x2 - 3, h + 3, z1 - 2, B("lantern", hanging=1))
    for (x, z) in ((x1 - 3, z2 + 3), (x2 + 3, z2 + 3), (x1 - 3, z1 - 3)):
        lamp_post(a, x, h + 1, z, B("spruce_fence"), B("lantern"), height=3)
    a.set(cx + 4, h + 1, z2 + 3, B("cobblestone"))
    standing_sign(a, cx + 4, h + 2, z2 + 3, 0, "§l§7채석장\n§r§f돌 생성기 58개\n§7곡괭이로 캐세요 (4초)",
                  kind="spruce_standing_sign")
    m.reserved[(np.abs(m.DX - dx) <= 13) & (np.abs(m.DZ - dz) <= 12)] = True
    return (cx, h + 1, z2 + 4)


# ============================================================================ volcano: gold + diamonds

def volcano_mines(m, gens):
    from gen_volcano import CONE_R, CRATER_R
    a = m.a
    cx, cz = m.w(0, 0)
    # diamonds set into the crater terraces, around the lava lake
    placed = 0
    for ang in range(0, 360, 20):
        for rr in (7.3, 9.6):
            t = math.radians(ang + (10 if rr > 8 else 0))
            x, z = cx + round(math.cos(t) * rr), cz + round(math.sin(t) * rr)
            if m.road[x - a.x0, z - a.z0]:
                continue
            y = m.gy(x, z)
            if a.get(x, y + 1, z) != AIR or a.get(x, y, z) in (AIR, B("campfire")):
                continue
            gens.add(a, x, y, z, "diamond_ore", "diamond", "volcano")
            placed += 1
    # gold veins along the west wall of the lava tube
    y0 = m.H0
    tx = cx - 3
    for z in range(cz - CONE_R + 6, cz + CONE_R - 5, 3):
        if m.gy(cx, z) < y0 + 5:
            continue
        for y in (y0 + 1, y0 + 2):
            if a.get(tx, y, z) != AIR and a.get(tx + 1, y, z) == AIR:
                gens.add(a, tx, y, z, "gold_ore", "gold", "volcano")
    # gold in the temple sanctum: two treasure piles
    tcx, tcz = m.w(40, 42)
    g = m.H0 + 3
    for (ox, oz) in ((-4, -2), (-4, 2), (4, -2), (4, 2)):
        x, z = tcx + ox, tcz + oz
        if a.get(x, g, z) == AIR:
            gens.add(a, x, g, z, "gold_ore", "gold", "volcano")
    return placed


# ============================================================================ library: more enchanting tables

def enchant_dais(lib, cx, cz, enchants):
    """Enchanting table with a 2-high bookshelf ring (28 shelves = maximum power)."""
    from gen_library import P, F1
    lib.fill(cx - 3, P, cz - 3, cx + 3, P + 3, cz + 3, AIR)
    lib.fill(cx - 3, F1, cz - 3, cx + 3, F1, cz + 3, B("polished_deepslate"))
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            if max(abs(x - cx), abs(z - cz)) == 2 and not (abs(x - cx) == 0):
                lib.set(x, P, z, B("bookshelf"))
                lib.set(x, P + 1, z, B("bookshelf"))
    lib.set(cx, P, cz, B("enchanting_table"))
    lib.be("EnchantTable", cx, P, cz)
    for (x, z) in ((cx - 3, cz - 3), (cx + 3, cz - 3), (cx - 3, cz + 3), (cx + 3, cz + 3)):
        lib.set(x, P, z, B("purple_candle", candles=3, lit=1))
    enchants.append((lib.cx + cx, P, lib.cz + cz))
