"""Villager village occupied by illagers.

north: cave exit terrace ─ pillager barricade ─ main road ─ plaza (well, bell, cages, banner pole)
west road ─ green-window gatehouse ─ dark forest (illager HQ, boss)
south road ─ light-blue-window gatehouse ─ beach
east: occupied square = hunting ground (pillager tents inside a spiked palisade)
north-west: resistance hideout inn = convenience space
"""
import math

import numpy as np

from mcw import B, AIR
from gen_common import stair, slab, oak_tree, dead_tree, clamp_gradient, FLOWERS
from rpg_world import G, X0, Z0
from rpg_parts import (wall_sign, hang_sign, stand_sign, lamp_post, crook_lamp, hanging_lantern, barrel, shop_kit,
                       hunting_ground, paint_path, gatehouse, path_steps, banner_wall, banner_stand, bell, campfire,
                       chest, DV, FACE)
from rpg_build import house, tent, palisade_post, gable_roof
from layout import VILLAGE_C, PASS_HQ, PASS_BEACH

ROAD_N = [(24, 168), (22, 182), (12, 198), (4, 212)]
ROAD_S = [(4, 232), (10, 246), (18, 258), (22, 268), (22, 276)]
ROAD_W = [(-9, 223), (-30, 225), (-54, 226)]
ROAD_E = [(9, 223), (16, 234), (18, 243)]
PLAZA = (0, 222)


def shape(W):
    reg = W.regions["village"]["mask"]
    W.H[reg & (W.din > 7)] = G
    W.H = np.where(reg, clamp_gradient(W.H, reg, 1), W.H)


def plaza(W, rng):
    a = W.a
    cx, cz = PLAZA
    for x in range(cx - 10, cx + 11):
        for z in range(cz - 10, cz + 11):
            d = math.hypot(x - cx, z - cz)
            if d <= 9.5:
                a.set(x, G, z, rng.choice([B("cobblestone"), B("grass_path"), B("gravel"), B("cobblestone"),
                                           B("mossy_cobblestone")]))
                for y in (G + 1, G + 2):
                    if a.get(x, y, z) != AIR:
                        a.set(x, y, z, AIR)
    # well
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            edge = abs(x - cx) == 2 or abs(z - cz) == 2
            if edge:
                a.set(x, G + 1, z, B("cobblestone"))
            else:
                for y in range(G - 3, G + 1):
                    a.set(x, y, z, B("water"))
                a.set(x, G - 4, z, B("cobblestone"))
    for (x, z) in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2)):
        a.set(x, G + 2, z, B("oak_fence")); a.set(x, G + 3, z, B("oak_fence"))
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            a.set(x, G + 4, z, B("cobblestone_slab"))
    bell(a, cx, G + 3, cz, attach="hanging", d="south")
    # banner pole of the occupiers
    for y in range(G + 1, G + 7):
        a.set(cx + 6, y, cz - 6, B("dark_oak_fence"))
    for (dx, dz, f) in ((1, 0, "east"), (-1, 0, "west")):
        a.set(cx + 6 + dx, G + 6, cz - 6, B("dark_oak_planks"))
        banner_wall(a, cx + 6 + dx * 2, G + 6, cz - 6, f, 15, ominous=True)
    # cages with captured villagers
    for (x0, z0) in ((cx - 8, cz + 4), (cx + 5, cz + 5)):
        for x in range(x0, x0 + 3):
            for z in range(z0, z0 + 3):
                edge = x in (x0, x0 + 2) or z in (z0, z0 + 2)
                a.set(x, G, z, B("spruce_planks"))
                for y in (G + 1, G + 2):
                    a.set(x, y, z, B("iron_bars") if edge else AIR)
                a.set(x, G + 3, z, B("dark_oak_slab"))
        wall_sign(a, x0 + 1, G + 2, z0 - 1, "north", "§l§7갇힌 주민\n§r구해 주세요...")
        a.set(x0 + 1, G + 2, z0, B("dark_oak_planks"))
    stand_sign(a, cx - 4, G + 1, cz - 8, "north", "§l§2점령된 마을\n§r우민들이 마을을\n차지했다!")
    W.reserved[W.rect(cx - 11, cz - 11, cx + 11, cz + 11)] = True


HOUSES = [
    # x1, z1, x2, z2, door side, door offset, burnt?, kind
    (-44, 200, -36, 208, "east", 4, 0.0, "a"),
    (-22, 238, -14, 245, "north", 4, 0.25, "b"),
    (-16, 252, -8, 259, "north", 4, 0.0, "a"),
    (-44, 246, -36, 253, "east", 3, 0.3, "b"),
    (12, 190, 19, 198, "west", 4, 0.0, "a"),
    (-20, 200, -14, 206, "east", 3, 0.0, "c"),
    (14, 248, 21, 254, "west", 3, 0.2, "b"),
    (-34, 230, -28, 236, "north", 3, 0.0, "c"),
]


def village_houses(W, rng):
    a = W.a
    for (x1, z1, x2, z2, side, off, burnt, kind) in HOUSES:
        if kind == "a":
            post, wall, roof = B("oak_log"), B("oak_planks"), "oak_stairs"
        elif kind == "b":
            post, wall, roof = B("oak_log"), B("cobblestone"), "spruce_stairs"
        else:
            post, wall, roof = B("stripped_oak_log"), B("white_terracotta"), "oak_stairs"
        house(W, x1, z1, x2, z2, G, h=4, post=post, wall=wall, floor=B("oak_planks"), roof_stairs=roof,
              roof_ridge=B("oak_slab"), gable=B("oak_planks"), doors=[(side, off)], lamp=True,
              burnt=burnt, rng=rng, roof_holes=0.18 if burnt else 0.0)
        # doors were replaced by planks barricades on some houses
        dx = {"north": (x1 + off, z1), "south": (x1 + off, z2), "west": (x1, z1 + off), "east": (x2, z1 + off)}[side]
        if burnt:
            for (bx, bz) in ((x1 + 1, z1 + 1), (x2 - 1, z2 - 1)):
                campfire(a, bx, G + 1, bz) if rng.random() < 0.0 else a.set(bx, G + 1, bz, B("coal_block"))
        else:
            ox, oz = DV[side]
            banner_wall(a, dx[0] + ox, G + 3, dx[1] + oz, side, 15, ominous=True)
        # simple interior
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        a.set(x1 + 1, G + 1, z1 + 1, B("crafting_table") if rng.random() < 0.5 else B("barrel", facing_direction=1))
        a.set(x2 - 1, G + 1, z2 - 1, B("barrel", facing_direction=1))
        if not burnt:
            a.set(x2 - 1, G + 1, z1 + 1, B("composter", composter_fill_level=3))
        W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 2, z2 + 2)] = True


def resistance_inn(W, rng):
    """Convenience space: the one house the villagers still hold - a fortified inn."""
    a = W.a
    x1, z1, x2, z2 = -40, 182, -26, 192
    house(W, x1, z1, x2, z2, G, h=5, post=B("spruce_log"), wall=B("cobblestone"), floor=B("spruce_planks"),
          roof_stairs="spruce_stairs", roof_ridge=B("spruce_slab"), gable=B("spruce_planks"), axis="x",
          doors=[("south", 6), ("south", 7), ("south", 8)], lamp=False, base=B("mossy_cobblestone"))
    for x in range(x1 + 1, x2):
        a.set(x, G + 5, z1, B("spruce_planks"))
        a.set(x, G + 5, z2, B("spruce_planks"))
    # porch
    for x in range(x1 + 4, x1 + 11):
        a.set(x, G, z2 + 1, B("spruce_planks"))
        a.set(x, G, z2 + 2, B("spruce_planks"))
    for x in (x1 + 4, x1 + 10):
        for y in range(G + 1, G + 5):
            a.set(x, y, z2 + 2, B("spruce_fence"))
    for x in range(x1 + 4, x1 + 11):
        a.set(x, G + 5, z2 + 1, stair("spruce_stairs", "north"))
        a.set(x, G + 5, z2 + 2, stair("spruce_stairs", "north"))
    hang_sign(a, x1 + 7, G + 4, z2 + 2, "south", "§l§a저항군 은신처\n§r상점 · 엔더 상자", kind="spruce_hanging_sign")
    banner_wall(a, x1 + 5, G + 3, z2 + 1, "south", 4, [("cbo", 11), ("mc", 11)])
    banner_wall(a, x1 + 9, G + 3, z2 + 1, "south", 4, [("cbo", 11), ("mc", 11)])
    rec = shop_kit(W, "village", "저항군 은신처", -33, G + 1, 187, "south", counter=B("spruce_planks"))
    for x in (-35, -31):
        a.set(x, G + 1, 187, B("barrel", facing_direction=1))
    a.set(-39, G + 1, 183, B("cartography_table"))
    a.set(-38, G + 1, 183, B("lectern", cardinal="south"))
    a.set(-27, G + 1, 183, B("barrel", facing_direction=1)); a.set(-27, G + 2, 183, B("barrel", facing_direction=1))
    a.set(-28, G + 1, 183, B("smoker", cardinal="south"))
    for (x, z) in ((-36, 185), (-30, 185), (-33, 190)):
        hanging_lantern(a, x, G + 4, z, chain=0)
    for x in (-39, -38):
        a.set(x, G + 1, 191, stair("spruce_stairs", "west"))
    wall_sign(a, -39, G + 3, 188, "east", "§l저항군 게시판\n§r마을을 되찾자!\n§7보스: 서쪽 숲")
    W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 2, z2 + 4)] = True
    return rec


def watchtower(W, rng):
    """Pillager watchtower near the north entrance."""
    a = W.a
    cx, cz = 38, 192
    log, pl = B("dark_oak_log"), B("dark_oak_planks")
    for x in range(cx - 3, cx + 4):
        for z in range(cz - 3, cz + 4):
            a.set(x, G, z, B("cobblestone"))
            corner = abs(x - cx) == 3 and abs(z - cz) == 3
            edge = abs(x - cx) == 3 or abs(z - cz) == 3
            for y in range(G + 1, G + 16):
                if corner:
                    a.set(x, y, z, log)
                elif edge and y in (G + 1, G + 2) and abs(x - cx) == 3 and z == cz:
                    a.set(x, y, z, AIR) if x == cx - 3 else a.set(x, y, z, pl)
                elif edge and (y % 5 == 0):
                    a.set(x, y, z, pl)
                elif edge:
                    a.set(x, y, z, B("birch_planks") if y < G + 4 else (pl if rng.random() < 0.5 else B("dark_oak_fence")))
                else:
                    a.set(x, y, z, AIR)
    # lookout platform
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            a.set(x, G + 16, z, pl)
            edge = abs(x - cx) == 4 or abs(z - cz) == 4
            if edge:
                a.set(x, G + 17, z, B("dark_oak_fence"))
    for (x, z) in ((cx - 4, cz - 4), (cx + 4, cz - 4), (cx - 4, cz + 4), (cx + 4, cz + 4)):
        for y in range(G + 17, G + 21):
            a.set(x, y, z, log)
    gable_roof(a, cx - 4, cz - 4, cx + 4, cz + 4, G + 21, "dark_oak_stairs", pl, pl, axis="x")
    for (dx, dz, f) in ((-4, 0, "west"), (4, 0, "east"), (0, -4, "north"), (0, 4, "south")):
        a.set(cx + dx + DV[f][0], G + 15, cz + dz + DV[f][1], AIR)
        banner_wall(a, cx + dx + DV[f][0], G + 14, cz + dz + DV[f][1], f, 15, ominous=True)
    hanging_lantern(a, cx, G + 15, cz, chain=3)
    W.reserved[W.rect(cx - 6, cz - 6, cx + 6, cz + 6)] = True


def barricade(W, rng):
    """Pillager checkpoint across the north road."""
    a = W.a
    z = 176
    for x in range(8, 40):
        if 16 <= x <= 28:
            continue
        y = W.gy(x, z)
        h = 2 + (x % 3 == 0)
        for k in range(1, h + 1):
            a.set(x, y + k, z, B("dark_oak_log", axis="y") if k < h or x % 2 else B("dark_oak_fence"))
    for x in (15, 29):
        y = W.gy(x, z)
        for k in range(1, 6):
            a.set(x, y + k, z, B("dark_oak_log"))
        banner_wall(a, x, y + 4, z + 1, "south", 15, ominous=True)
        a.set(x, y + 6, z, B("lantern"))
    for (x, zz) in ((12, 178), (33, 179), (10, 174)):
        y = W.gy(x, zz)
        a.set(x, y + 1, zz, B("hay_block")); a.set(x + 1, y + 1, zz, B("barrel", facing_direction=1))
    campfire(a, 34, W.gy(34, 182) + 1, 182)
    stand_sign(a, 30, W.gy(30, 172) + 1, 172, "north", "§l§4경고!\n§r이 마을은\n우민들의 것이다")
    W.reserved[W.rect(8, 172, 40, 182)] = True


def occupied_square(W, rng):
    """Hunting ground: the old market square fenced in by the illagers' spiked palisade."""
    a = W.a
    x1, z1, x2, z2 = 24, 232, 52, 258
    pl = B("dark_oak_planks")

    def floor(x, z):
        return rng.choice([B("coarse_dirt"), B("grass_path"), B("coarse_dirt"), B("gravel"), B("grass_block")])

    def wall(x, y, z):
        return B("dark_oak_log") if (x + z) % 3 else B("stripped_dark_oak_log")

    def props(box):
        tent(W, x1 + 4, z1 + 4, G, 5, "gray", axis="x")
        tent(W, x2 - 9, z2 - 6, G, 5, "white", axis="x")
        for (x, z) in ((x1 + 14, z1 + 12), (x1 + 6, z2 - 5)):
            a.set(x, G + 1, z, B("dark_oak_fence")); a.set(x, G + 2, z, B("hay_block"))
            a.set(x, G + 3, z, B("carved_pumpkin", cardinal="west"))
        for (x, z) in ((x2 - 4, z1 + 3), (x2 - 3, z1 + 3), (x2 - 4, z1 + 4)):
            a.set(x, G + 1, z, B("barrel", facing_direction=1))
        a.set(x1 + 12, G + 1, z2 - 3, B("hay_block")); a.set(x1 + 13, G + 1, z2 - 3, B("hay_block"))

    rec = hunting_ground(W, "village", "점령지 광장", x1, z1, x2, z2, G, floor, wall, gates=[("west", 11)],
                         wall_h=6, cap=pl, props=props, spawn_n=7, gate_block="dark_oak_fence_gate")
    # spikes on top, banners outside
    for x in range(x1 - 1, x2 + 2):
        for z in (z1 - 1, z2 + 1):
            if (x + z) % 2 == 0:
                a.set(x, G + 8, z, B("dark_oak_fence"))
    for z in range(z1 - 1, z2 + 2):
        for x in (x1 - 1, x2 + 1):
            if (x + z) % 2 == 0:
                a.set(x, G + 8, z, B("dark_oak_fence"))
    for z in range(z1 + 2, z2 - 1, 6):
        if abs(z - (z1 + 11)) > 3:
            banner_wall(a, x1 - 2, G + 4, z, "west", 15, ominous=True)
    for x in range(x1 + 3, x2 - 1, 6):
        banner_wall(a, x, G + 4, z1 - 2, "north", 15, ominous=True)
    W.reserved[W.rect(x1 - 7, z1 - 3, x2 + 3, z2 + 3)] = True
    return rec


def farms(W, rng):
    a = W.a
    for (x1, z1) in ((-30, 206), (30, 208)):
        for x in range(x1, x1 + 9):
            for z in range(z1, z1 + 7):
                if x == x1 + 4:
                    a.set(x, G, z, B("water"))
                    continue
                if rng.random() < 0.6:
                    a.set(x, G, z, B("farmland", moisturized_amount=7))
                    if rng.random() < 0.55:
                        a.set(x, G + 1, z, B("wheat", growth=rng.randint(3, 7)))
                else:
                    a.set(x, G, z, B("coarse_dirt"))
                    if rng.random() < 0.2:
                        a.set(x, G + 1, z, B("deadbush"))
        for x in range(x1 - 1, x1 + 10):
            for z in (z1 - 1, z1 + 7):
                if a.get(x, G + 1, z) == AIR and rng.random() < 0.7:
                    a.set(x, G + 1, z, B("oak_fence"))
        W.reserved[W.rect(x1 - 2, z1 - 2, x1 + 10, z1 + 8)] = True


def roads(W, rng):
    a = W.a
    blocks = [B("grass_path")] * 4 + [B("gravel"), B("coarse_dirt")]
    cells = set()
    for pts in (ROAD_N, ROAD_S, ROAD_W, ROAD_E):
        cells |= paint_path(W, pts, 2, blocks, rng)
    for pts in (PASS_HQ, PASS_BEACH):
        pc = paint_path(W, pts, 2, [B("grass_path"), B("gravel"), B("coarse_dirt"), B("cobblestone")], rng)
        for (x, z) in pc:
            y = W.gy(x, z)
            if a.get(x, y, z) in (B("grass_block"), B("dirt"), B("stone"), B("andesite")):
                a.set(x, y, z, rng.choice([B("gravel"), B("grass_path"), B("cobblestone")]))
        path_steps(W, pc, "cobblestone_stairs")
    # cave terrace path down to the road
    cells |= paint_path(W, [(24, 166), (24, 170)], 2, blocks, rng)
    path_steps(W, cells, "oak_stairs")
    for (x, z, ok) in ((18, 186, True), (8, 204, False), (-20, 228, True), (-42, 222, True), (14, 240, True),
                       (24, 262, True), (-60, 231, True), (16, 272, True), (28, 276, True), (6, 214, True)):
        y = W.gy(x, z)
        if ok:
            lamp_post(a, x, y + 1, z, post=B("oak_fence"), lamp=B("lantern"), h=3)
        else:
            for k in range(1, 3):
                a.set(x, y + k, z, B("oak_fence"))


def nature(W, rng):
    a = W.a
    reg = W.regions["village"]["mask"]
    cand = [tuple(c) for c in np.argwhere(reg & (W.din > 3) & (W.din < 12) & ~W.reserved)]
    rng.shuffle(cand)
    occ = []
    for (i, k) in cand:
        x, z = i + X0, k + Z0
        if any((x - ox) ** 2 + (z - oz) ** 2 < 81 for ox, oz in occ) or len(occ) > 28:
            continue
        y = W.gy(x, z)
        if a.get(x, y, z) != B("grass_block") or a.get(x, y + 1, z) != AIR:
            continue
        if rng.random() < 0.3:
            dead_tree(a, x, y + 1, z, rng, kind="oak")
        else:
            oak_tree(a, x, y + 1, z, rng)
        occ.append((x, z))
    for (i, k) in np.argwhere(reg & ~W.reserved):
        x, z = i + X0, k + Z0
        y = W.gy(x, z)
        if a.get(x, y, z) != B("grass_block") or a.get(x, y + 1, z) != AIR:
            continue
        r = rng.random()
        if r < 0.12:
            a.set(x, y + 1, z, B("short_grass"))
        elif r < 0.14:
            a.set(x, y + 1, z, B(rng.choice(["dandelion", "poppy", "oxeye_daisy"])))
        elif r < 0.15:
            a.set(x, y, z, B("coarse_dirt"))
    # scattered occupation debris
    for (x, z) in ((-6, 236), (6, 206), (-24, 216), (10, 240), (-46, 230)):
        y = W.gy(x, z)
        if a.get(x, y + 1, z) == AIR:
            campfire(a, x, y + 1, z) if (x + z) % 2 == 0 else a.set(x, y + 1, z, B("barrel", facing_direction=1))
    for (x, z) in ((-12, 214), (12, 232), (-36, 240)):
        y = W.gy(x, z)
        if a.get(x, y + 1, z) == AIR:
            banner_stand(a, x, y + 1, z, "south", 15, ominous=True)


def build(W):
    import random
    rng = random.Random(W.seed + 400)
    plaza(W, rng)
    village_houses(W, rng)
    resistance_inn(W, rng)
    watchtower(W, rng)
    barricade(W, rng)
    occupied_square(W, rng)
    farms(W, rng)
    gatehouse(W, -78, 229, "west", 69, "green", wall=B("dark_oak_planks"), pillar=B("dark_oak_log"),
              roof_stairs="dark_oak_stairs", roof_ridge=B("dark_oak_slab"), floor=B("spruce_planks"),
              next_name="§2보스: 우민 본거지", prev_name="§a점령된 마을", gable=B("dark_oak_planks"),
              foundation=B("cobblestone"), sign_kind="darkoak_wall_sign")
    gatehouse(W, 22, 289, "south", 70, "light_blue", wall=B("smooth_sandstone"), pillar=B("birch_log"),
              roof_stairs="birch_stairs", roof_ridge=B("birch_slab"), floor=B("smooth_sandstone"),
              next_name="§b해변", prev_name="§a점령된 마을", gable=B("birch_planks"),
              foundation=B("sandstone"), sign_kind="birch_wall_sign")
    roads(W, rng)
    nature(W, rng)
    W.spawns["village"] = (24, 67, 168)
    W.mark_surface(W.regions["village"]["mask"] | W.regions["pass_hq"]["mask"] | W.regions["pass_beach"]["mask"])
    W.light_boxes.append(("village", -66, 160, 66, 290, G - 2, G + 22, 1, 8))
