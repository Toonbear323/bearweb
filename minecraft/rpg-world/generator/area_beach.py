"""Beach on the bay south of the village.

arrival from the light-blue gatehouse ─ boardwalk
  ├ west: pier ─ lighthouse islet ─ glass tunnel down to the deep-sea temple (boss)   [area_deepsea]
  └ east: along the beach ─ volcanic headland ─ nether gate                           [area_nether]
beach bar = convenience space, driftwood cove = hunting ground, shipwreck, palms, coral reef.
"""
import math

import numpy as np

from mcw import B, AIR
from gen_common import stair, slab, palm_tree, boulder
from rpg_world import G, X0, Z0, SEA
from rpg_parts import (wall_sign, hang_sign, stand_sign, lamp_post, hanging_lantern, barrel, shop_kit,
                       hunting_ground, paint_path, path_steps, campfire, chest, DV, pot)
from rpg_build import round_tower
from layout import shore_z

WALK_W = [(22, 310), (22, 316), (6, 326), (-4, 334)]
WALK_E = [(22, 316), (48, 326), (84, 330), (112, 328), (126, 325)]
PIER = [(-4, 334), (-14, 342), (-29, 351)]
ISLET = (-33, 354)
TUBE_START = (-40, 352)


def shape(W):
    # islet for the lighthouse
    cx, cz = ISLET
    for x in range(cx - 9, cx + 10):
        for z in range(cz - 9, cz + 10):
            d = math.hypot(x - cx, z - cz)
            if d < 9.5:
                i, k = x - X0, z - Z0
                h = int(round(G - max(0, d - 6.0) * 1.8))
                if h > W.H[i, k]:
                    W.H[i, k] = h
                    W.top[i, k] = B("stone") if d > 6 else B("gravel")
                    W.sub[i, k] = B("stone")
                    if h > SEA:
                        W.water[i, k] = 0
    # boardwalk dunes are flattened a little
    land = W.land_beach
    W.H = np.where(land, np.minimum(W.H, 66), W.H)


def coral_reef(W, rng):
    a = W.a
    ocean = W.ocean
    corals = ["tube", "brain", "bubble", "fire", "horn"]
    for (i, k) in np.argwhere(ocean):
        x, z = i + X0, k + Z0
        if not (-30 <= x <= 110 and z <= 400):
            continue
        y = int(W.H[i, k])
        depth = SEA - y
        if depth < 3 or depth > 16:
            continue
        r = rng.random()
        if r < 0.10:
            c = rng.choice(corals)
            a.set(x, y, z, B(c + "_coral_block") if c != "fire" or True else B("tube_coral_block"))
        if r < 0.05:
            c = rng.choice(corals)
            a.setw(x, y + 1, z, B(c + "_coral"))
        elif r < 0.09:
            a.setw(x, y + 1, z, B("seagrass"))
        elif r < 0.10 and depth > 5:
            h = rng.randint(2, depth - 2)
            for t in range(h):
                a.setw(x, y + 1 + t, z, B("kelp", kelp_age=rng.randint(0, 20)))
        elif r < 0.105:
            a.setw(x, y + 1, z, B("sea_pickle", cluster_count=rng.randint(0, 3), dead_bit=0))


def beach_props(W, rng):
    a = W.a
    land = W.land_beach & ~W.reserved
    cand = [tuple(c) for c in np.argwhere(land)]
    rng.shuffle(cand)
    occ = []
    for (i, k) in cand:
        x, z = i + X0, k + Z0
        if any((x - ox) ** 2 + (z - oz) ** 2 < 100 for ox, oz in occ) or len(occ) > 26:
            continue
        y = W.gy(x, z)
        if a.get(x, y, z) != B("sand") or a.get(x, y + 1, z) != AIR:
            continue
        if z > shore_z(x) - 3:
            continue
        palm_tree(a, x, y + 1, z, rng)
        occ.append((x, z))
    # umbrellas and loungers on the sand
    for (x, z, col) in ((4, 318, "red"), (30, 334, "yellow"), (62, 338, "light_blue"), (-2, 322, "lime"),
                        (90, 336, "orange")):
        y = W.gy(x, z)
        for k in range(1, 4):
            a.set(x, y + k, z, B("birch_fence"))
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) + abs(dz) <= 3:
                    a.set(x + dx, y + 4, z + dz, B(col + "_wool") if (dx + dz) % 2 == 0 else B("white_wool"))
        a.set(x, y + 4, z, B(col + "_wool"))
        for dx in (-2, 2):
            ly = W.gy(x + dx, z + 1)
            a.set(x + dx, ly + 1, z + 1, B("white_carpet"))
            a.set(x + dx, ly + 1, z + 2, B("birch_slab"))
        W.reserved[W.rect(x - 3, z - 3, x + 3, z + 3)] = True
    # sandcastle
    x, z = 12, 338
    y = W.gy(x, z)
    for dx in range(3):
        for dz in range(3):
            a.set(x + dx, y + 1, z + dz, B("sandstone"))
    for (dx, dz) in ((0, 0), (2, 0), (0, 2), (2, 2)):
        a.set(x + dx, y + 2, z + dz, B("sandstone_wall"))
    a.set(x + 1, y + 2, z + 1, B("chiseled_sandstone"))
    # driftwood and shells
    for (x, z) in ((40, 342), (70, 340), (-6, 340), (104, 338)):
        y = W.gy(x, z)
        for t in range(3):
            a.set(x + t, y + 1, z, B("stripped_oak_log", axis="x"))
    for _ in range(40):
        i, k = cand[rng.randrange(len(cand))]
        x, z = i + X0, k + Z0
        y = W.gy(x, z)
        if a.get(x, y, z) == B("sand") and a.get(x, y + 1, z) == AIR:
            a.set(x, y + 1, z, B("sea_pickle", cluster_count=0, dead_bit=1) if rng.random() < 0.5 else B("deadbush"))


def beach_bar(W, rng):
    """Convenience space: a thatched beach bar facing the sea."""
    a = W.a
    x1, z1, x2, z2 = 32, 310, 48, 320
    jp, post = B("jungle_planks"), B("stripped_jungle_log")
    Y = W.gy(40, 315)
    for x in range(x1 - 1, x2 + 2):
        for z in range(z1 - 1, z2 + 2):
            a.set(x, Y, z, jp if x1 <= x <= x2 and z1 <= z <= z2 else B("sand"))
            for y in range(Y + 1, Y + 9):
                a.set(x, y, z, AIR)
            yy = Y - 1
            while yy > 55 and a.get(x, yy, z) == AIR:
                a.set(x, yy, z, B("sand"))
                yy -= 1
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            if corner or (edge and (x - x1) % 4 == 0 and z in (z1, z2)):
                for y in range(Y + 1, Y + 5):
                    a.set(x, y, z, post)
            elif edge and z == z1:
                for y in range(Y + 1, Y + 5):
                    a.set(x, y, z, B("bamboo_planks") if y < Y + 3 else AIR)
            elif edge and x in (x1, x2):
                a.set(x, Y + 1, z, B("bamboo_planks"))
    # thatch roof (leaves) with a peak
    leaf = B("jungle_leaves", persistent_bit=1, update_bit=0)
    for k in range(4):
        for x in range(x1 - 2 + k, x2 + 3 - k):
            for z in range(z1 - 2 + k, z2 + 3 - k):
                if k == 3 or x in (x1 - 2 + k, x2 + 2 - k) or z in (z1 - 2 + k, z2 + 2 - k):
                    a.set(x, Y + 5 + k, z, leaf)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            a.set(x, Y + 5, z, B("bamboo_planks"))
    hang_sign(a, 40, Y + 4, z2 + 1, "south", "§l§b해변 매점\n§r상점 · 엔더 상자", kind="jungle_hanging_sign")
    a.set(40, Y + 5, z2 + 1, leaf)
    rec = shop_kit(W, "beach", "해변 매점", 40, Y + 1, 316, "south", counter=B("bamboo_planks"))
    for (x, z) in ((34, 312), (35, 312), (46, 312)):
        a.set(x, Y + 1, z, B("barrel", facing_direction=1))
    a.set(37, Y + 2, 316, B("melon_block"))
    for (x, z) in ((35, 318), (45, 318)):
        a.set(x, Y + 1, z, B("jungle_fence"))
        a.set(x, Y + 2, z, B("jungle_pressure_plate"))
    for (x, z) in ((36, 314), (44, 314), (40, 318)):
        hanging_lantern(a, x, Y + 4, z, chain=0)
    W.reserved[W.rect(x1 - 3, z1 - 3, x2 + 3, z2 + 3)] = True
    return rec


def cove_hunt(W, rng):
    """Hunting ground: driftwood-and-sandstone enclosure on the upper beach."""
    a = W.a
    x1, z1, x2, z2 = 62, 300, 88, 320
    y = W.gy(75, 322)

    def floor(x, z):
        return B("sand") if rng.random() < 0.8 else B("gravel")

    def wall(x, yy, z):
        if (x + z) % 5 == 0:
            return B("stripped_oak_log")
        return B("cut_sandstone") if yy > y + 3 else B("sandstone")

    def props(box):
        for (x, z) in ((x1 + 6, z1 + 5), (x2 - 7, z2 - 5)):
            boulder(a, x, y + 1, z, rng, 1.6, [B("sandstone"), B("stone"), B("andesite")])
        for t in range(4):
            a.set(x1 + 14 + t, y + 1, z1 + 12, B("stripped_oak_log", axis="x"))
        a.set(x2 - 4, y + 1, z1 + 4, B("barrel", facing_direction=1))

    rec = hunting_ground(W, "beach", "해안 사냥터", x1, z1, x2, z2, y, floor, wall, gates=[("south", 12)],
                         wall_h=6, cap=B("smooth_sandstone"), props=props, spawn_n=6, gate_block="jungle_fence_gate",
                         sign_kind="jungle_wall_sign")
    for x in range(x1 - 1, x2 + 2, 6):
        a.set(x, y + 8, z2 + 1, B("lantern")) if a.get(x, y + 7, z2 + 1) != AIR else None
    W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 2, z2 + 7)] = True
    return rec


def shipwreck(W, rng):
    a = W.a
    x0, z0 = 96, 348
    y0 = 60
    for t in range(16):
        half = 3 if 3 <= t <= 12 else 2
        for w in range(-half, half + 1):
            for k in range(0, 5):
                x, z = x0 + t, z0 + w
                edge = abs(w) == half or k == 0
                if edge and rng.random() < 0.85:
                    a.set(x, y0 + k, z, B("spruce_planks") if k > 0 else B("dark_oak_planks"))
                elif not edge:
                    a.set(x, y0 + k, z, B("water") if y0 + k <= SEA else AIR)
    for k in range(1, 9):
        a.set(x0 + 6, y0 + k, z0, B("spruce_log"))
    for w in range(-3, 4):
        a.set(x0 + 6, y0 + 7, z0 + w, B("spruce_fence"))
        if abs(w) < 3:
            a.set(x0 + 7, y0 + 6, z0 + w, B("white_wool"))
    W.reserved[W.rect(x0 - 2, z0 - 5, x0 + 18, z0 + 5)] = True


def pier_and_lighthouse(W, rng):
    a = W.a
    # pier: planks on log posts, rope railing
    from gen_common import line_points
    for (ax, az), (bx, bz) in zip(PIER[:-1], PIER[1:]):
        for (x, _, z) in line_points((ax, 0, az), (bx, 0, bz), 0.4):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    if a.get(x + dx, 64, z + dz) in (AIR, B("water")) or True:
                        a.set(x + dx, 64, z + dz, B("spruce_planks"))
                        a.set(x + dx, 65, z + dz, AIR) if a.get(x + dx, 65, z + dz) != B("spruce_planks") else None
            if (x + z) % 4 == 0:
                for dx, dz in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                    yy = 63
                    while yy > 40 and a.get(x + dx, yy, z + dz) in (AIR, B("water")):
                        a.set(x + dx, yy, z + dz, B("spruce_log"))
                        yy -= 1
    # lighthouse
    cx, cz = ISLET[0] + 2, ISLET[1] + 3
    for k in range(1, 23):
        band = B("red_concrete") if (k // 3) % 2 else B("white_concrete")
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                d = math.hypot(x - cx, z - cz)
                if d <= 3.4:
                    a.set(x, G + k, z, band)
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.4:
                a.set(x, G + 23, z, B("smooth_stone_slab", half="top") if d > 3.4 else B("smooth_stone"))
                if 3.4 < d <= 4.4:
                    a.set(x, G + 24, z, B("iron_bars"))
            if d <= 2.4:
                a.set(x, G + 24, z, B("glass") if d > 1.2 else AIR)
                a.set(x, G + 25, z, B("glass") if d > 1.2 else AIR)
                a.set(x, G + 26, z, B("red_concrete"))
    a.set(cx, G + 24, cz, B("sea_lantern"))
    a.set(cx, G + 25, cz, B("sea_lantern"))
    a.set(cx, G + 27, cz, B("lightning_rod"))
    wall_sign(a, cx - 4, G + 2, cz, "west", "§l등대\n§r심해 신전 입구는\n서쪽 터널")
    W.reserved[W.rect(ISLET[0] - 9, ISLET[1] - 9, ISLET[0] + 9, ISLET[1] + 9)] = True


def walks(W, rng):
    a = W.a
    cells = set()
    for pts in (WALK_W, WALK_E):
        cells |= paint_path(W, pts, 1, [B("spruce_planks"), B("spruce_planks"), B("birch_planks")], rng)
    path_steps(W, cells, "spruce_stairs")
    for (x, z) in ((20, 312), (10, 324), (36, 326), (60, 332), (96, 332), (116, 330), (-2, 331)):
        y = W.gy(x, z)
        lamp_post(a, x, y + 1, z, post=B("birch_fence"), lamp=B("lantern"), h=3)
    stand_sign(a, 25, W.gy(25, 318) + 1, 318, "south", "§l§b해변\n§r← 서쪽: 심해 신전 (보스)\n→ 동쪽: 지옥")


def build(W):
    import random
    rng = random.Random(W.seed + 600)
    beach_bar(W, rng)
    cove_hunt(W, rng)
    shipwreck(W, rng)
    pier_and_lighthouse(W, rng)
    walks(W, rng)
    beach_props(W, rng)
    coral_reef(W, rng)
    W.spawns["beach"] = (22, 66, 312)
    W.mark_surface(W.regions["coast"]["mask"])
    W.light_boxes.append(("beach", -60, 292, 130, 360, 60, 80, 1, 8))
