"""Spawn valley: gacha hall (뽑기장), central plaza, adventurer's rest, beginner training ground."""
import math

import numpy as np

from mcw import B, AIR
from gen_common import stair, slab, oak_tree, birch_tree, spruce_tree, cherry_tree, FLOWERS, tall_plant, clamp_gradient
from rpg_world import G, X0, Z0
from rpg_parts import (wall_sign, hang_sign, stand_sign, lamp_post, hanging_lantern, ender_chest, barrel, pot,
                       banner_wall, shop_kit, hunting_ground, paint_path, light_grid, DV, FACE, chest)
from rpg_build import house, gable_roof
from layout import SPAWN_C, PASS_FARM

PLAZA = (0, 4)
SPAWN = (0, 65, 16)
TIERS = [("common", "§f§l일반 뽑기", "white_concrete", "light_gray_concrete", "iron_block", "sea_lantern",
          ["white_wool", "light_gray_wool", "lime_wool", "white_wool"]),
         ("rare", "§b§l고급 뽑기", "light_blue_concrete", "blue_concrete", "lapis_block", "verdant_froglight",
          ["light_blue_wool", "cyan_wool", "blue_wool", "white_wool"]),
         ("epic", "§d§l희귀 뽑기", "purple_concrete", "magenta_concrete", "amethyst_block", "pearlescent_froglight",
          ["purple_wool", "magenta_wool", "pink_wool", "white_wool"]),
         ("legend", "§6§l전설 뽑기", "yellow_concrete", "orange_concrete", "gold_block", "ochre_froglight",
          ["yellow_wool", "orange_wool", "red_wool", "yellow_wool"])]

ROADS = {
    "north": [(0, -10), (0, -20)],
    "south": [(0, 19), (0, 30), (0, 46)],
    "west": [(-15, 4), (-28, 1), (-44, -5)],
    "east": [(15, 4), (24, 0)],
}


def shape(W):
    reg = W.regions["spawn"]["mask"]
    core = reg & (W.din > 7)
    W.H[core] = G
    sl = W.rect(-24, -50, 24, -18)
    W.H[sl][reg[sl]] = G
    for pts in ROADS.values():
        for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
            n = int(max(abs(bx - ax), abs(bz - az))) + 1
            for t in range(n + 1):
                x = round(ax + (bx - ax) * t / n); z = round(az + (bz - az) * t / n)
                W.H[W.rect(x - 3, z - 3, x + 3, z + 3)] = G
    W.H = np.where(reg, clamp_gradient(W.H, reg, 1), W.H)


def gacha_machine(W, cx, zf, tier, rng):
    a = W.a
    key, label, c1, c2, corner, light, caps = tier
    for x in range(cx - 2, cx + 3):
        for z in range(zf - 4, zf + 1):
            cor = x in (cx - 2, cx + 2) and z in (zf - 4, zf)
            edge = x in (cx - 2, cx + 2) or z in (zf - 4, zf)
            a.set(x, 66, z, B(corner) if cor else B(c2))
            a.set(x, 67, z, B(corner) if cor else B(c1))
            for y in range(68, 72):
                if edge:
                    a.set(x, y, z, B(corner) if cor and y == 68 else B("glass"))
                elif y == 68 or (y == 69 and rng.random() < 0.55):
                    a.set(x, y, z, B(rng.choice(caps)))
                else:
                    a.set(x, y, z, AIR)
            a.set(x, 72, z, B(corner) if cor else B(c2))
            if cor:
                a.set(x, 73, z, B("smooth_quartz_slab"))
    a.set(cx, 73, zf - 2, B(light))
    a.set(cx, 74, zf - 2, B("end_rod", facing_direction=1))
    # front: button, labels
    a.set(cx, 67, zf, B("chiseled_quartz_block"))
    a.set(cx, 67, zf + 1, B("stone_button", facing_direction=3))
    wall_sign(a, cx, 72, zf + 1, "south", label + "\n§r§7▼ 버튼을 눌러 주세요")
    wall_sign(a, cx - 1, 67, zf + 1, "south", label)
    wall_sign(a, cx + 1, 67, zf + 1, "south", label)
    a.set(cx, 66, zf + 1, B("quartz_stairs", weirdo_direction=3, upside_down_bit=0))
    W.gacha.append(dict(tier=key, label=label, button=(cx, 67, zf + 1), function="rpg/gacha/" + key))


def gacha_hall(W, rng):
    a = W.a
    X1, X2, ZB, ZF = -20, 20, -46, -22
    q, qp, sq = B("smooth_quartz"), B("quartz_pillar"), B("quartz_block")
    # platform
    for x in range(X1 - 1, X2 + 2):
        for z in range(ZB - 1, ZF + 2):
            for y in range(58, 65):
                a.set(x, y, z, B("stone_bricks"))
            a.set(x, 65, z, B("smooth_quartz") if (x + z) % 2 == 0 else B("polished_diorite"))
            for y in range(66, 78):
                a.set(x, y, z, AIR)
    for x in range(-7, 8):
        a.set(x, 65, ZF + 2, stair("quartz_stairs", "north"))
    for x in (X1 - 1, X2 + 1):
        for z in range(ZB - 1, ZF + 2):
            a.set(x, 65, z, B("chiseled_quartz_block"))
    # walls
    for y in range(66, 77):
        for z in range(ZB, ZF + 1):
            for x in (X1, X2):
                pil = (z - ZB) % 5 == 0 or z == ZF
                win = 69 <= y <= 73 and not pil
                glass = ["light_blue_stained_glass", "purple_stained_glass", "yellow_stained_glass",
                         "pink_stained_glass"][((z - ZB) // 5) % 4]
                a.set(x, y, z, qp if pil else (B(glass) if win else q))
        for x in range(X1, X2 + 1):
            pil = (x - X1) % 5 == 0
            a.set(x, y, ZB, qp if pil else q)
    for x in range(X1, X2 + 1):
        a.set(x, 66, ZB, B("gold_block") if (x - X1) % 5 == 0 else B("chiseled_quartz_block"))
    # front colonnade
    for x in range(X1, X2 + 1, 5):
        for y in range(66, 77):
            a.set(x, y, ZF, qp)
        a.set(x, 66, ZF, B("chiseled_quartz_block"))
    for x in range(X1, X2 + 1):
        a.set(x, 76, ZF, q)
        a.set(x, 75, ZF, B("quartz_stairs", weirdo_direction=3, upside_down_bit=1) if (x - X1) % 5 else qp)
    # roof with a coloured skylight
    sky = ["light_blue_stained_glass", "white_stained_glass", "yellow_stained_glass", "white_stained_glass"]
    for x in range(X1 - 1, X2 + 2):
        for z in range(ZB - 1, ZF + 2):
            inner = -13 <= x <= 13 and ZB + 6 <= z <= ZF - 4
            if inner:
                a.set(x, 77, z, B(sky[(abs(x) // 3 + abs(z) // 3) % 4]))
            else:
                a.set(x, 77, z, q)
            if x in (X1 - 1, X2 + 1) or z in (ZB - 1, ZF + 1):
                a.set(x, 78, z, B("smooth_quartz_slab"))
    # pediment over the entrance
    for k in range(6):
        for x in range(-12 + 2 * k, 13 - 2 * k):
            a.set(x, 78 + k, ZF + 1, q)
        a.set(-13 + 2 * k, 78 + k, ZF + 1, stair("quartz_stairs", "east"))
        a.set(13 - 2 * k, 78 + k, ZF + 1, stair("quartz_stairs", "west"))
    a.set(0, 81, ZF + 2, B("gold_block"))
    for x in (-1, 0, 1):
        a.set(x, 75, ZF, q)                 # hanging signs need a full block above (not upside-down stairs)
        hang_sign(a, x, 74, ZF, "south", "§6§l✦ 뽑기장 ✦", kind="birch_hanging_sign", color=-1)
    # carpet aisle and the jackpot display
    for z in range(-35, ZF + 1):
        for x in (-1, 0, 1):
            a.set(x, 66, z, B("red_carpet"))
    for x in (-1, 0, 1):
        for z in (-31, -30, -29):
            a.set(x, 66, z, B("gold_block"))
            a.set(x, 67, z, B("chiseled_quartz_block"))
    a.set(0, 68, -30, B("enchanting_table"))
    from mcw import simple_be
    a.add_be(simple_be("EnchantTable", 0, 68, -30))
    for (x, z) in ((-1, -31), (1, -31), (-1, -29), (1, -29)):
        a.set(x, 68, z, B("amethyst_cluster", face="up"))
    # machines
    for i, tier in enumerate(TIERS):
        gacha_machine(W, -15 + 10 * i, -38, tier, rng)
    # chandeliers
    for (x, z) in ((-10, -30), (10, -30), (0, -41), (-10, -41), (10, -41), (0, -25)):
        a.set(x, 76, z, B("gold_block"))
        hanging_lantern(a, x, 75, z, chain=2)
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a.set(x + d[0], 73, z + d[1], B("lantern", hanging=0))
            a.set(x + d[0], 74, z + d[1], B("chain"))
    # wall decoration: banners between pillars
    for z in range(ZB + 2, ZF - 1, 5):
        banner_wall(a, X1 + 1, 72, z, "east", 15, [("bri", 11), ("cbo", 4)])
        banner_wall(a, X2 - 1, 72, z, "west", 15, [("bri", 11), ("cbo", 4)])
    for x in range(X1 + 3, X2 - 2, 5):
        if abs(x) > 2:
            banner_wall(a, x, 73, ZB + 1, "south", 15, [("bri", 11), ("cbo", 4)])
    wall_sign(a, 0, 73, ZB + 1, "south", "§6§l✦ 뽑기장 ✦\n§r뽑기 기계의 버튼을\n눌러 보세요")
    # benches along the side walls
    for z in range(-34, -23, 3):
        a.set(X1 + 1, 66, z, stair("quartz_stairs", "west"))
        a.set(X2 - 1, 66, z, stair("quartz_stairs", "east"))
    W.reserved[W.rect(X1 - 2, ZB - 2, X2 + 2, ZF + 3)] = True


def plaza(W, rng):
    a = W.a
    cx, cz = PLAZA
    for x in range(cx - 16, cx + 17):
        for z in range(cz - 16, cz + 17):
            d = math.hypot(x - cx, z - cz)
            if d <= 15.5:
                ring = int(d) % 4
                b = [B("polished_andesite"), B("stone_bricks"), B("polished_andesite"), B("smooth_stone")][ring]
                if d > 14.5:
                    b = B("chiseled_stone_bricks") if (x + z) % 3 == 0 else B("stone_bricks")
                a.set(x, G, z, b)
                for y in (G + 1, G + 2):
                    a.set(x, y, z, AIR)
    W.reserved[W.rect(cx - 16, cz - 16, cx + 16, cz + 16)] = True
    # fountain
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            d = math.hypot(x - cx, z - cz)
            if d <= 4.6:
                a.set(x, G - 1, z, B("stone_bricks"))
                a.set(x, G, z, B("water"))
            elif d <= 5.6:
                a.set(x, G, z, B("chiseled_stone_bricks"))
                a.set(x, G + 1, z, B("stone_brick_slab"))
    for y in range(G - 1, G + 4):
        for (x, z) in ((cx, cz), (cx + 1, cz), (cx, cz + 1), (cx + 1, cz + 1), (cx - 1, cz), (cx, cz - 1)):
            pass
    for y in range(G, G + 4):
        a.set(cx, y, cz, B("quartz_pillar"))
    a.set(cx, G + 4, cz, B("chiseled_quartz_block"))
    a.set(cx, G + 5, cz, B("amethyst_block"))
    a.set(cx, G + 6, cz, B("amethyst_cluster", face="up"))
    for d in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        a.set(cx + d[0], G + 4, cz + d[1], stair("quartz_stairs", {"east": "west", "west": "east", "south": "north", "north": "south"}[d[2]], True))
        a.set(cx + d[0], G + 1, cz + d[1], B("sea_lantern"))
    # benches facing the fountain
    for ang in range(0, 360, 45):
        if ang in (90, 270, 0, 180):
            continue
        r = 11
        x = int(round(cx + math.cos(math.radians(ang)) * r))
        z = int(round(cz + math.sin(math.radians(ang)) * r))
        face = "east" if x < cx else "west"
        a.set(x, G + 1, z, stair("spruce_stairs", {"east": "west", "west": "east"}[face]))
        a.set(x, G + 1, z + 1, stair("spruce_stairs", {"east": "west", "west": "east"}[face]))
    # lamp posts around the plaza
    for ang in range(0, 360, 45):
        r = 14
        x = int(round(cx + math.cos(math.radians(ang + 22.5)) * r))
        z = int(round(cz + math.sin(math.radians(ang + 22.5)) * r))
        lamp_post(a, x, G + 1, z, post=B("stone_brick_wall"), lamp=B("lantern"), h=3)
    # spawn marker + directory board
    sx, sy, sz = SPAWN
    a.set(sx, G, sz, B("chiseled_quartz_block"))
    board(W, 7, 18)


def board(W, x, z):
    a = W.a
    for dx in range(-2, 3):
        for y in (G + 1, G + 2, G + 3):
            a.set(x + dx, y, z, B("spruce_planks"))
        a.set(x + dx, G + 4, z, B("spruce_slab"))
    for dx in (-2, 2):
        a.set(x + dx, G + 1, z, B("spruce_log"))
        a.set(x + dx, G + 2, z, B("spruce_log"))
        a.set(x + dx, G + 3, z, B("spruce_log"))
    lines = [("§l§6모험 안내판", "§f북쪽: 뽑기장\n§a서쪽: 농장\n§e동쪽: 모험가 쉼터"),
             ("§l§c던전 순서", "§f1 동굴(남쪽)\n2 점령된 마을\n3 해변"),
             ("§l§c던전 순서", "§f4 지옥\n5 마왕성\n6 워든 서식지"),
             ("§l§4보스", "§f우민 본거지\n심해 신전\n마왕성 지하감옥")]
    for i, (t1, t2) in enumerate(lines):
        wall_sign(a, x - 2 + [0, 1, 3, 4][i] if i < 4 else x, G + 2, z + 1, "south", t1 + "\n" + t2)
    wall_sign(a, x, G + 3, z + 1, "south", "§l§6✦ RPG 월드 ✦\n§r스폰")


def adventurer_rest(W, rng):
    """Convenience space at spawn: timber market hall open toward the plaza."""
    a = W.a
    x1, z1, x2, z2 = 24, -10, 38, 8
    house(W, x1, z1, x2, z2, G, h=4, post=B("spruce_log"), wall=B("white_terracotta"), floor=B("spruce_planks"),
          roof_stairs="dark_oak_stairs", roof_ridge=B("dark_oak_slab"), gable=B("spruce_planks"),
          window=B("glass_pane"), axis="z", lamp=False, base=B("cobblestone"))
    # open front with timber columns
    for z in range(z1 + 1, z2):
        for y in range(G + 1, G + 4):
            a.set(x1, y, z, AIR)
        a.set(x1, G, z, B("spruce_planks"))
    for z in (z1 + 6, z1 + 12):
        for y in range(G + 1, G + 5):
            a.set(x1, y, z, B("spruce_log"))
    for z in range(z1, z2 + 1):
        a.set(x1, G + 4, z, B("stripped_spruce_log", axis="z"))
    for z in range(z1 + 1, z2):
        a.set(x1 - 1, G, z, B("spruce_slab"))
    hang_sign(a, x1 - 1, G + 4, -1, "west", "§l§e모험가 쉼터\n§r상점 · 엔더 상자")
    rec = shop_kit(W, "spawn", "모험가 쉼터", 30, G + 1, -1, "west", counter=B("spruce_planks"))
    a.set(30, G + 2, -3, B("lantern"))
    for z in (-3, -2, -1, 0, 1):
        a.set(30, G + 1, z, B("barrel", facing_direction=1) if z in (-3, 1) else B("spruce_planks"))
        a.set(30, G + 2, z, AIR if z in (-2, -1, 0) else a.get(30, G + 2, z))
    for z in (-2, 0):
        a.set(30, G + 2, z, B("spruce_slab", half="bottom"))
    # goods behind the counter
    for z in (-4, -3, 1, 2):
        barrel(a, 36, G + 1, z)
        barrel(a, 36, G + 2, z) if z in (-4, 2) else None
    a.set(36, G + 1, -1, B("crafting_table"))
    a.set(36, G + 1, 0, B("smithing_table"))
    a.set(36, G + 1, -2, B("cartography_table"))
    a.set(26, G + 1, 6, B("anvil", cardinal="east"))
    a.set(27, G + 1, 6, B("grindstone", attachment="standing", direction=0))
    for z in (-8, -7):
        a.set(37, G + 1, z, stair("spruce_stairs", "east"))
    a.set(26, G + 1, -8, B("spruce_planks"))
    pot(a, 26, G + 2, -8, "red_tulip")
    for (x, z) in ((28, -6), (34, -6), (28, 4), (34, 4), (31, 7)):
        hanging_lantern(a, x, G + 4, z, chain=0)
    wall_sign(a, 37, G + 2, -6, "west", "§l엔더 상자 →\n§r어디서 열어도\n같은 보관함")
    W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 2, z2 + 2)] = True
    return rec


def training_ground(W, rng):
    a = W.a
    x1, z1, x2, z2 = 22, 24, 42, 40

    def floor(x, z):
        return B("coarse_dirt") if rng.random() < 0.3 else B("grass_block")

    def wall(x, y, z):
        return B("spruce_log") if (x + z) % 4 == 0 else B("stripped_spruce_log")

    def props(box):
        bx1, bz1, bx2, bz2 = box
        for (x, z) in ((bx1 + 4, bz1 + 4), (bx2 - 4, bz1 + 4), (bx1 + 4, bz2 - 4), (bx2 - 4, bz2 - 4)):
            a.set(x, G + 1, z, B("hay_block"))
            a.set(x, G + 2, z, B("carved_pumpkin", cardinal="west"))
        for z in range(bz1 + 6, bz2 - 5, 3):
            a.set(bx2, G + 1, z, B("target"))
            a.set(bx2, G + 2, z, B("target"))
        a.set(bx1 + 10, G + 1, bz1 + 8, B("spruce_fence"))
        a.set(bx1 + 10, G + 2, bz1 + 8, B("target"))

    rec = hunting_ground(W, "spawn", "초보자 훈련장", x1, z1, x2, z2, G, floor, wall, gates=[("west", 3)],
                         wall_h=5, cap=B("spruce_slab", half="top"), props=props, spawn_n=6)
    for x in range(x1 - 1, x2 + 2, 5):
        a.set(x, G + 6, z1 - 1, B("spruce_fence"))
        a.set(x, G + 7, z1 - 1, B("lantern"))
    W.reserved[W.rect(x1 - 6, z1 - 3, x2 + 2, z2 + 2)] = True
    return rec


def roads(W, rng):
    blocks = [B("grass_path"), B("grass_path"), B("grass_path"), B("coarse_dirt"), B("gravel")]
    for name, pts in ROADS.items():
        paint_path(W, pts, 2, blocks, rng)
    # path to the training ground gate
    paint_path(W, [(3, 28), (16, 28)], 1, blocks, rng)
    a = W.a
    for name, pts in ROADS.items():
        for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
            L = max(abs(bx - ax), abs(bz - az))
            for t in range(4, int(L), 10):
                x = round(ax + (bx - ax) * t / L); z = round(az + (bz - az) * t / L)
                if abs(bx - ax) > abs(bz - az):
                    lx, lz = x, z + (4 if (t // 10) % 2 else -4)
                else:
                    lx, lz = x + (4 if (t // 10) % 2 else -4), z
                if W.reserved[lx - X0, lz - Z0] and a.get(lx, W.gy(lx, lz) + 1, lz) != AIR:
                    continue
                lamp_post(a, lx, W.gy(lx, lz) + 1, lz, post=B("spruce_fence"), lamp=B("lantern"), h=3)


def nature(W, rng):
    a = W.a
    reg = W.regions["spawn"]["mask"]
    occupied = []
    cand = np.argwhere(reg & (W.din > 4) & (W.din < 22) & ~W.reserved)
    rng.shuffle(cand_list := [tuple(c) for c in cand])
    for (i, k) in cand_list:
        x, z = i + X0, k + Z0
        if any((x - ox) ** 2 + (z - oz) ** 2 < 49 for ox, oz in occupied):
            continue
        if len(occupied) > 70:
            break
        y = W.gy(x, z)
        if a.get(x, y, z) != B("grass_block") or a.get(x, y + 1, z) != AIR:
            continue
        r = rng.random()
        if W.din[i, k] > 9 and r < 0.35:
            cherry_tree(a, x, y + 1, z, rng)
        elif r < 0.6:
            oak_tree(a, x, y + 1, z, rng)
        elif r < 0.8:
            birch_tree(a, x, y + 1, z, rng)
        else:
            spruce_tree(a, x, y + 1, z, rng, h=rng.randint(7, 10))
        occupied.append((x, z))
    # flowers and grass
    for (i, k) in np.argwhere(reg & ~W.reserved):
        x, z = i + X0, k + Z0
        y = W.gy(x, z)
        if a.get(x, y, z) != B("grass_block") or a.get(x, y + 1, z) != AIR:
            continue
        r = rng.random()
        if r < 0.10:
            a.set(x, y + 1, z, B("short_grass"))
        elif r < 0.13:
            a.set(x, y + 1, z, B(rng.choice(FLOWERS)))
        elif r < 0.14:
            a.set(x, y + 1, z, B("pink_petals", growth=3, cardinal=rng.choice(["north", "east", "south", "west"])))


def build(W):
    import random
    rng = random.Random(W.seed + 100)
    W.gacha = []
    plaza(W, rng)
    gacha_hall(W, rng)
    adventurer_rest(W, rng)
    training_ground(W, rng)
    roads(W, rng)
    nature(W, rng)
    W.spawns["spawn"] = SPAWN
    W.mark_surface(W.regions["spawn"]["mask"])
    W.light_boxes.append(("spawn", -56, -54, 56, 50, G - 2, G + 14, 1, 8))
