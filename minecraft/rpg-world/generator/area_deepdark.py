"""Deep dark (warden habitat) under the black mountains west of the castle crater.

crater west road ─ abyss stairs (tube) ─ cyan-window gallery high on the cavern wall ─ cavern floor
cavern: ancient city (portal frame, ruined halls, sculk), explorers' hideout = convenience,
walled sunken plaza = hunting ground (roofed), sealed gate to the next region (coming later).
"""
import math

import numpy as np

from mcw import B, AIR, simple_be
from gen_common import stair, slab, fbm
from rpg_world import X0, Z0, BIOME
from rpg_parts import (wall_sign, hang_sign, stand_sign, hanging_lantern, barrel, shop_kit, light_grid, tube,
                       campfire, DV, HUNT_LIGHT)
from rpg_carve import chamber, box_carve
from rpg_build import tent

CC = (46, 522, 58, 64)
FL = 32
DB, DT, CD = B("deepslate_bricks"), B("deepslate_tiles"), B("cobbled_deepslate")
RD = B("reinforced_deepslate")


def shape(W):
    pass


def cavern(W, rng):
    a = W.a
    cx, cz, rx, rz = CC
    ch = chamber(W, cx, cz, rx, rz, FL, 26, W.seed + 1100, p=3.0, floor_noise=0.8, wall_noise=0.1, ceil_min=10,
                 floor_block=lambda x, z: rng.choice([B("deepslate"), B("deepslate"), CD, B("sculk")]))
    X, Z, inside = ch["X"], ch["Z"], ch["inside"]
    for (i, k) in np.argwhere(np.ones(X.shape, bool)):
        W.a.bio[int(X[i, k]) - X0, int(Z[i, k]) - Z0] = BIOME["deep_dark"]
    W.dd = ch
    return ch


def dfloor(W, x, z):
    ch = W.dd
    x1, z1, x2, z2 = ch["box"]
    if x1 <= x <= x2 and z1 <= z <= z2 and ch["inside"][x - x1, z - z1]:
        return int(ch["floor"][x - x1, z - z1])
    return None


def city_floor(W, rng):
    """Flatten the city core to FL and pave it."""
    a = W.a
    tiles = [DT, DT, DB, B("cracked_deepslate_tiles"), B("polished_deepslate")]
    for x in range(8, 84):
        for z in range(492, 560):
            f = dfloor(W, x, z)
            if f is None:
                continue
            for y in range(min(f, FL), FL + 1):
                a.set(x, y, z, DB)
            for y in range(FL + 1, max(f, FL) + 1):
                a.set(x, y, z, AIR)
            a.set(x, FL, z, rng.choice(tiles) if (abs(z - 525) <= 2 or abs(x - 60) <= 2) else
                  (B("sculk") if rng.random() < 0.25 else rng.choice(tiles)))
            W.dd["floor"][x - W.dd["box"][0], z - W.dd["box"][1]] = FL


def portal(W):
    """The ancient city's great frame (reinforced deepslate), facing east."""
    a = W.a
    px, pz = 26, 525
    # stepped platform
    for k, r in enumerate((14, 12, 10)):
        for x in range(px - 6 + k, px + 6 - k):
            for z in range(pz - r, pz + r + 1):
                a.set(x, FL + 1 + k, z, DB if k < 2 else DT)
    top = FL + 3
    for z in range(pz - 10, pz + 11):
        for y in range(top + 1, top + 15):
            side = abs(z - pz) >= 7
            lintel = y >= top + 12
            if side or lintel:
                inner = abs(z - pz) == 7 or y == top + 12
                a.set(px, y, z, RD if inner else DB)
                a.set(px - 1, y, z, DB)
    for z in range(pz - 6, pz + 7):
        a.set(px, top + 11, z, RD) if abs(z - pz) >= 5 else None
    for z in (pz - 9, pz + 9):
        for y in range(top + 15, top + 18):
            a.set(px, y, z, DB)
    for z in range(pz - 3, pz + 4):
        a.set(px, top + 15, z, DB)
        a.set(px, top + 16, z, DT) if abs(z - pz) <= 1 else None
    # stairs up the platform from the east
    for z in range(pz - 3, pz + 4):
        for k in range(3):
            a.set(px + 6 - k, FL + 1 + k, z, stair("deepslate_tile_stairs", "west"))
    for (dz, s) in ((-12, -1), (12, 1)):
        a.set(px + 3, FL + 4, pz + dz, B("soul_lantern")) if abs(dz) <= 10 else None
    for z in (pz - 5, pz + 5):
        a.set(px + 2, FL + 4, z, B("sculk_catalyst"))
    W.reserved[W.rect(px - 8, pz - 15, px + 8, pz + 15)] = True


def ruins(W, rng):
    a = W.a
    bldgs = [(40, 500, 52, 510), (40, 540, 52, 550), (64, 498, 76, 508), (66, 540, 78, 550), (14, 498, 22, 508)]
    for (x1, z1, x2, z2) in bldgs:
        h = rng.randint(6, 9)
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                corner = x in (x1, x2) and z in (z1, z2)
                a.set(x, FL, z, DT)
                for y in range(FL + 1, FL + h + 1):
                    if corner:
                        a.set(x, y, z, B("polished_deepslate"))
                    elif edge:
                        broken = rng.random() < 0.18 and y > FL + 3
                        door = (z in (z1, z2) and abs(x - (x1 + x2) // 2) <= 1 and y <= FL + 3) or \
                               (x in (x1, x2) and abs(z - (z1 + z2) // 2) <= 1 and y <= FL + 3)
                        a.set(x, y, z, AIR if (broken or door) else (B("cracked_deepslate_bricks") if rng.random() < 0.2 else DB))
                    else:
                        a.set(x, y, z, AIR)
                if not edge and rng.random() < 0.7:
                    a.set(x, FL + h, z, DT)
        # interior: carpets, candles, chests
        for x in range(x1 + 1, x2):
            for z in range(z1 + 1, z2):
                if rng.random() < 0.3:
                    a.set(x, FL + 1, z, B("gray_carpet") if rng.random() < 0.6 else B("light_blue_carpet"))
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        a.set(cx, FL + 1, cz, B("black_candle", candles=3, lit=1))
        a.set(x1 + 1, FL + 1, z1 + 1, B("skeleton_skull", facing_direction=1))
        a.add_be(simple_be("Skull", x1 + 1, FL + 1, z1 + 1, Rotation=__import__("amulet_nbt").FloatTag(45.0),
                           SkullType=__import__("amulet_nbt").ByteTag(0)))
        a.set(x2 - 1, FL + 1, z2 - 1, B("sculk_sensor"))
        W.reserved[W.rect(x1 - 1, z1 - 1, x2 + 1, z2 + 1)] = True
    # column rows along the main avenue
    for x in range(34, 84, 8):
        for z in (518, 532):
            for y in range(FL + 1, FL + 7):
                a.set(x, y, z, B("polished_deepslate") if y < FL + 6 else DT)
            a.set(x, FL + 7, z, B("soul_lantern"))
    W.reserved[W.rect(30, 516, 86, 534)] = True


def sculk_dressing(W, rng):
    a = W.a
    ch = W.dd
    X, Z, inside, fl, ce = ch["X"], ch["Z"], ch["inside"], ch["floor"], ch["ceil"]
    for (i, k) in np.argwhere(inside):
        x, z = int(X[i, k]), int(Z[i, k])
        if W.reserved[x - X0, z - Z0]:
            continue
        f = int(fl[i, k])
        if a.get(x, f + 1, z) != AIR:
            continue
        r = rng.random()
        if r < 0.05:
            a.set(x, f + 1, z, B("sculk_vein", multi_face_direction_bits=1))
        elif r < 0.058:
            a.set(x, f, z, B("sculk"))
            a.set(x, f + 1, z, B("sculk_sensor"))
        elif r < 0.061:
            a.set(x, f, z, B("sculk"))
            a.set(x, f + 1, z, B("sculk_shrieker", can_summon=0))
        elif r < 0.063:
            a.set(x, f, z, B("sculk_catalyst"))
        elif r < 0.066:
            a.set(x, f + 1, z, B("black_candle", candles=rng.randint(0, 3), lit=1))
        c = int(ce[i, k])
        if rng.random() < 0.01 and a.get(x, c, z) == AIR and a.get(x, c + 1, z) != AIR:
            a.set(x, c + 1, z, B("sculk"))
    # deepslate pillars and dripstone-like spikes in the wild part
    for _ in range(30):
        i = rng.randrange(X.shape[0]); k = rng.randrange(X.shape[1])
        if not inside[i, k]:
            continue
        x, z = int(X[i, k]), int(Z[i, k])
        if W.reserved[x - X0, z - Z0] or 8 <= x <= 84 and 492 <= z <= 560:
            continue
        f, c = int(fl[i, k]), int(ce[i, k])
        if c - f < 8:
            continue
        for y in range(f + 1, c + 1):
            a.set(x, y, z, B("deepslate", axis="y") if False else B("polished_deepslate"))


def hideout(W, rng):
    """Convenience space: explorers' hideout near the arrival, wool walls muffle the noise."""
    a = W.a
    x1, z1, x2, z2 = 74, 470, 90, 484
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            f = dfloor(W, x, z)
            for y in range((f or FL) - 1, FL + 1):
                a.set(x, y, z, CD)
            a.set(x, FL, z, B("spruce_planks"))
            for y in range(FL + 1, FL + 8):
                a.set(x, y, z, AIR)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            if edge:
                for y in range(FL + 1, FL + 5):
                    door = x == x2 and abs(z - 477) <= 1 and y <= FL + 3
                    a.set(x, y, z, AIR if door else (B("spruce_log") if (x in (x1, x2) and z in (z1, z2))
                                                     else B("gray_wool")))
            a.set(x, FL + 5, z, B("spruce_planks") if edge else B("light_gray_wool"))
    hang_sign(a, x2 + 1, FL + 4, 477, "east", "§l§3탐험가 은신처\n§r상점 · 엔더 상자", kind="spruce_hanging_sign")
    a.set(x2 + 1, FL + 5, 477, B("spruce_planks"))
    rec = shop_kit(W, "deepdark", "탐험가 은신처", 82, FL + 1, 477, "east", counter=B("spruce_planks"))
    for (x, z) in ((76, 472), (76, 482), (88, 472)):
        a.set(x, FL + 1, z, B("barrel", facing_direction=1))
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            if a.get(x, FL + 1, z) == AIR and rng.random() < 0.5:
                a.set(x, FL + 1, z, B("gray_carpet"))
    campfire(a, 77, FL + 1, 477, soul=True)
    for (x, z) in ((79, 473), (86, 481)):
        hanging_lantern(a, x, FL + 4, z, chain=0, lamp=B("soul_lantern", hanging=1))
    wall_sign(a, x1 + 1, FL + 2, 476, "east", "§l조용히!\n§r워든이 소리를\n듣고 있다...")
    W.reserved[W.rect(x1 - 1, z1 - 1, x2 + 3, z2 + 1)] = True
    return rec


def plaza_hunt(W, rng):
    """Hunting ground: a walled, roofed sunken plaza at the city's south-west."""
    a = W.a
    x1, z1, x2, z2 = 8, 548, 32, 572
    f = FL
    for x in range(x1 - 1, x2 + 2):
        for z in range(z1 - 1, z2 + 2):
            edge = x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)
            for y in range(f - 4, f + 1):
                a.set(x, y, z, DB)
            if not edge:
                a.set(x, f, z, B("sculk") if rng.random() < 0.35 else rng.choice([DT, B("cracked_deepslate_tiles")]))
            for y in range(f + 1, f + 10):
                a.set(x, y, z, (DB if (y - f) % 4 else DT) if edge else AIR)
            a.set(x, f + 10, z, DT)
    for (x, z) in ((x1 + 5, z1 + 6), (x2 - 5, z1 + 6), (x1 + 5, z2 - 6), (x2 - 5, z2 - 6)):
        for y in range(f + 1, f + 10):
            a.set(x, y, z, B("polished_deepslate"))
    # gate (north): two warped fence gates in series
    gx = x1 + 12
    for z in (z1 - 1, z1 - 2, z1 - 3, z1 - 4):
        for dx in (-1, 0, 1, 2):
            for y in range(f + 1, f + 5):
                side = dx in (-1, 2)
                a.set(gx + dx, y, z, DB if (side or y == f + 4) else AIR)
            a.set(gx + dx, f, z, DT)
    for z in (z1 - 1, z1 - 4):
        for dx in (0, 1):
            a.set(gx + dx, f + 1, z, B("warped_fence_gate", cardinal="north"))
            a.set(gx + dx, f + 2, z, AIR)
            a.set(gx + dx, f + 3, z, DB)
    wall_sign(a, gx, f + 3, z1 - 5, "north", "§l§c⚔ 사냥터 ⚔\n§r고대 도시 사냥터")
    wall_sign(a, gx + 1, f + 3, z1 - 5, "north", "§l§c⚔ 사냥터 ⚔\n§r고대 도시 사냥터")
    lights = []
    for x in range(x1 + 2, x2 + 1, 5):
        for z in range(z1 + 2, z2 + 1, 5):
            if a.get(x, f + 5, z) == AIR:
                a.set(x, f + 5, z, B("light_block_%d" % HUNT_LIGHT))
                lights.append((x, f + 5, z))
    pts = [(x, f + 1, z) for x in (x1 + 8, x1 + 16) for z in (z1 + 5, z1 + 12, z2 - 4)]
    pts = [p for p in pts if a.get(*p) == AIR]
    W.hunts.append(dict(region="deepdark", name="고대 도시 사냥터", box=(x1, f + 1, z1, x2, f + 9, z2), floor_y=f,
                        entrances=[(gx, f + 1, z1 - 5)], spawn_points=pts, lights=lights, roofed=True))
    W.reserved[W.rect(x1 - 2, z1 - 6, x2 + 2, z2 + 2)] = True


def sealed_gate(W):
    a = W.a
    x = -9
    zc = 525
    for z in range(zc - 6, zc + 7):
        f = dfloor(W, x + 3, z) or FL
        for y in range(FL, FL + 12):
            frame = abs(z - zc) >= 4 or y >= FL + 9
            a.set(x, y, z, RD if frame else B("iron_bars"))
            a.set(x - 1, y, z, DB)
    for z in range(zc - 3, zc + 4):
        for xx in range(x + 1, x + 6):
            a.set(xx, FL, z, DT)
            for y in range(FL + 1, FL + 5):
                if a.get(xx, y, z) != AIR:
                    a.set(xx, y, z, AIR)
    a.set(x, FL + 1, zc, B("reinforced_deepslate"))
    wall_sign(a, x + 1, FL + 3, zc, "east", "§l§8다음 지역\n§r(준비 중)")
    for z in (zc - 5, zc + 5):
        a.set(x + 1, FL + 1, z, B("polished_deepslate"))
        a.set(x + 1, FL + 2, z, B("soul_lantern"))


def abyss_stairs(W, rng):
    a = W.a
    wp = [(130, 526, 66), (113, 526, 58), (113, 480, 40), (92, 480, 33)]
    tube(W, wp, width=3, height=4, shell=DB, floor=DT, ring=B("polished_deepslate"), ring_every=7,
         lamp=B("sea_lantern"), lamp_every=7, stairs="deepslate_tile_stairs")
    # open the view between the gallery and the cavern, cyan windows in the west wall
    box_carve(W, 103, 36, 483, 110, 62, 523)
    for x in range(103, 111):
        for z in range(483, 524):
            for y in range(28, 36):
                a.set(x, y, z, B("deepslate"))
    for z in range(482, 526):
        if z % 3 == 0:
            continue
        fy = None
        for y in range(38, 62):
            if a.get(113, y, z) in (DT, B("sea_lantern"), B("polished_deepslate")):
                fy = y
                break
        if fy is None:
            continue
        for y in range(fy + 1, fy + 5):
            a.set(111, y, z, B("cyan_stained_glass"))
    # entrance arch on the crater side
    for z in range(522, 531):
        for y in range(66, 74):
            if abs(z - 526) >= 3 or y >= 71:
                if a.get(131, y, z) in (AIR,):
                    a.set(131, y, z, DB)
    wall_sign(a, 132, 71, 526, "east", "§l§3워든 서식지\n§r심연의 계단 ↓")
    W.allow("abyss", 90, 31, 476, 134, 72, 532)


def build(W):
    import random
    rng = random.Random(W.seed + 1100)
    cavern(W, rng)
    city_floor(W, rng)
    portal(W)
    ruins(W, rng)
    hideout(W, rng)
    plaza_hunt(W, rng)
    sealed_gate(W)
    abyss_stairs(W, rng)
    sculk_dressing(W, rng)
    W.spawns["deepdark"] = (90, FL + 2, 480)
    x1, z1, x2, z2 = W.dd["box"]
    W.allow("deepdark", x1, FL - 3, z1, x2, 62, z2)
    W.light_boxes.append(("deepdark", x1, z1, x2, z2, FL - 2, 60, 1, 6))
