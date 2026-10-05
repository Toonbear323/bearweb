"""Demon king's castle in a black crater south of the volcano.

arrival (purple gatehouse) ─ heroes' camp (convenience) ─ moat bridge ─ gatehouse ─ courtyard ─ keep
keep great hall = hub of the two branches:
  east : stairwell down to the great underground prison (boss)      [area_dungeon]
  west : back gate ─ moat bridge ─ crater rim ─ abyss stairs ─ deep dark (warden habitat) [area_deepdark]
east of the castle: the demon army drill hall = hunting ground (roofed).
"""
import math

import numpy as np

from mcw import B, AIR, simple_be
from gen_common import stair, slab, dead_tree, fbm
from rpg_world import X0, Z0
from rpg_parts import (wall_sign, hang_sign, stand_sign, lamp_post, hanging_lantern, barrel, shop_kit, light_grid,
                       campfire, banner_wall, banner_stand, paint_path, DV, HUNT_LIGHT, leak_check, hunting_ground)
from rpg_build import round_tower, tent

CF = 66                     # crater floor
PT = 70                     # plateau top
PX1, PZ1, PX2, PZ2 = 166, 494, 222, 550
KX1, KZ1, KX2, KZ2 = 180, 512, 208, 540
HALL_TOP = 90
LAVA_Y = 64
PBB, PB, BS = B("polished_blackstone_bricks"), B("polished_blackstone"), B("blackstone")
DT = B("deepslate_tiles")


def in_plateau(x, z, grow=0):
    """Rounded rectangle PX1..PX2 x PZ1..PZ2 (corner radius 6), grown outward by `grow` blocks."""
    cx = min(max(x, PX1 + 6), PX2 - 6)
    cz = min(max(z, PZ1 + 6), PZ2 - 6)
    return math.hypot(x - cx, z - cz) <= 6 + grow + 0.3


def shape(W):
    for x in range(PX1 - 8, PX2 + 9):
        for z in range(PZ1 - 8, PZ2 + 9):
            i, k = x - X0, z - Z0
            if in_plateau(x, z):
                W.H[i, k] = PT
                W.top[i, k] = PB
                W.sub[i, k] = BS
            elif in_plateau(x, z, 5):
                W.H[i, k] = LAVA_Y - 3
                W.water[i, k] = LAVA_Y
                W.liquid[i, k] = B("lava")
                W.top[i, k] = BS


def moat_and_bridges(W, rng):
    a = W.a
    # guard wall along the outer moat edge (1.5 high walls cannot be jumped over)
    for x in range(PX1 - 7, PX2 + 8):
        for z in range(PZ1 - 7, PZ2 + 8):
            if in_plateau(x, z, 6) and not in_plateau(x, z, 5):
                a.set(x, CF + 1, z, B("polished_blackstone_wall"))
                if (x + z) % 8 == 0:
                    a.set(x, CF + 2, z, B("polished_blackstone_wall"))
                    a.set(x, CF + 3, z, B("soul_lantern"))
    # bridges: north (main) and west (to the deep dark)
    for (cx, cz, d, n) in ((194, PZ1 - 6, "north", 6), (PX1 - 6, 526, "west", 6)):
        dx, dz = DV[d]
        for t in range(-1, n + 2):
            for w in range(-3, 4):
                if d == "north":
                    x, z = cx + w, PZ1 + 1 - t
                else:
                    x, z = PX1 + 1 - t, cz + w
                y = PT if t <= 1 else max(CF, PT - (t - 1))
                for yy in range(LAVA_Y - 4, y + 1):
                    a.set(x, yy, z, PBB if abs(w) == 3 or yy < y else PB)
                for yy in range(y + 1, y + 5):
                    a.set(x, yy, z, AIR)
                if abs(w) == 3:
                    a.set(x, y + 1, z, B("polished_blackstone_brick_wall"))
                elif t > 1 and y > CF:
                    a.set(x, y, z, stair("polished_blackstone_brick_stairs", {"north": "south", "west": "east"}[d]))
                    a.set(x, y - 1, z, PBB)
        # lanterns on the bridge
    W.reserved[W.rect(PX1 - 14, PZ1 - 14, PX2 + 14, PZ2 + 14)] = True


def curtain_walls(W, rng):
    a = W.a
    top = PT + 14
    for x in range(PX1, PX2 + 1):
        for z in range(PZ1, PZ2 + 1):
            if not in_plateau(x, z):
                continue
            ring = not in_plateau(x, z, -2)
            if ring:
                for y in range(PT + 1, top + 1):
                    band = (y - PT) % 5 == 0
                    a.set(x, y, z, DT if band else (PBB if rng.random() > 0.08 else B("cracked_polished_blackstone_bricks")))
                outer = not in_plateau(x, z, -1)
                if outer and (x + z) % 2 == 0:
                    a.set(x, top + 1, z, PBB)
                # arrow slits
                if outer and (x + z) % 7 == 0:
                    for y in (PT + 7, PT + 8):
                        a.set(x, y, z, B("iron_bars"))
    # corner towers with violet spires
    for (cx, cz) in ((PX1 + 4, PZ1 + 4), (PX2 - 4, PZ1 + 4), (PX1 + 4, PZ2 - 4), (PX2 - 4, PZ2 - 4)):
        round_tower(W, cx, cz, PT, 5, 22, PBB, floor=PB, roof=B("purple_terracotta"), roof_h=14,
                    windows={8: B("purple_stained_glass_pane"), 14: B("purple_stained_glass_pane"),
                             19: B("purple_stained_glass_pane")}, cap_block=B("end_rod", facing_direction=1),
                    inner=PBB)
        for k in range(1, 23, 5):
            for d in ((6, 0), (-6, 0), (0, 6), (0, -6)):
                if a.get(cx + d[0], PT + k, cz + d[1]) == AIR:
                    pass
    # gatehouse (north)
    gx = 194
    for cx in (gx - 8, gx + 8):
        round_tower(W, cx, PZ1, PT, 3, 20, PBB, floor=PB, roof=B("purple_terracotta"), roof_h=9, inner=PBB,
                    cap_block=B("end_rod", facing_direction=1))
    for x in range(gx - 5, gx + 6):
        for z in range(PZ1 - 1, PZ1 + 4):
            for y in range(PT + 1, PT + 18):
                arch = abs(x - gx) <= 2 and y <= PT + 7 + (1 if abs(x - gx) <= 1 else 0)
                a.set(x, y, z, AIR if arch else (DT if (y - PT) % 5 == 0 else PBB))
            a.set(x, PT, z, PB)
        if (x - gx) % 2 == 0:
            a.set(x, PT + 18, PZ1 - 1, PBB)
    for x in range(gx - 2, gx + 3):
        a.set(x, PT + 8, PZ1 - 1, B("iron_bars"))
    for x in (gx - 4, gx + 4):
        banner_wall(a, x, PT + 12, PZ1 - 2, "north", 0, [("bo", 5), ("sku", 5)])
    a.set(gx, PT + 7, PZ1 - 2, PBB)
    hang_sign(a, gx, PT + 6, PZ1 - 2, "north", "§5§l마왕성", kind="crimson_hanging_sign")
    # west back gate
    for z in range(523, 530):
        for x in range(PX1, PX1 + 4):
            for y in range(PT + 1, PT + 7):
                a.set(x, y, z, AIR if abs(z - 526) <= 2 and y <= PT + 5 else a.get(x, y, z))
    wall_sign(a, PX1 - 1, PT + 6, 526, "west", "§l§3워든 서식지 ←\n§r심연의 계단")
    a.set(PX1, PT + 6, 526, PBB)


def keep(W, rng):
    a = W.a
    # shell
    for x in range(KX1, KX2 + 1):
        for z in range(KZ1, KZ2 + 1):
            edge = x in (KX1, KX2) or z in (KZ1, KZ2)
            corner = x in (KX1, KX2) and z in (KZ1, KZ2)
            a.set(x, PT, z, PB if edge else (B("purple_terracotta") if (x + z) % 2 else B("polished_deepslate")))
            for y in range(PT + 1, 100):
                if edge:
                    along = (x - KX1) if z in (KZ1, KZ2) else (z - KZ1)
                    col = corner or along % 7 == 0
                    win = (not col) and along % 7 in (3, 4) and PT + 6 <= y <= PT + 16
                    a.set(x, y, z, B("purple_stained_glass_pane") if win else (DT if col or (y - PT) % 6 == 0 else PBB))
                elif y == HALL_TOP:
                    a.set(x, y, z, PBB)
                elif y < HALL_TOP:
                    a.set(x, y, z, AIR)
                else:
                    a.set(x, y, z, PBB)
            if edge and (x + z) % 2 == 0:
                a.set(x, 100, z, PBB)
    # central spire
    round_tower(W, 194, 526, 99, 5, 12, PBB, floor=PBB, roof=B("purple_terracotta"), roof_h=16, inner=PBB,
                cap_block=B("end_rod", facing_direction=1))
    for (cx, cz) in ((KX1 + 1, KZ1 + 1), (KX2 - 1, KZ1 + 1), (KX1 + 1, KZ2 - 1), (KX2 - 1, KZ2 - 1)):
        for y in range(100, 108):
            a.set(cx, y, cz, PBB)
        a.set(cx, 108, cz, B("purple_terracotta"))
        a.set(cx, 109, cz, B("end_rod", facing_direction=1))
    # doors: north (main), west (back gate route), with stairs
    for x in range(191, 198):
        for y in range(PT + 1, PT + 9):
            a.set(x, y, KZ1, AIR if abs(x - 194) <= 2 or y <= PT + 6 else a.get(x, y, KZ1))
    for x in range(190, 199):
        a.set(x, PT + 9, KZ1, DT)
    for z in range(524, 529):
        for y in range(PT + 1, PT + 6):
            a.set(KX1, y, z, AIR)
    hang_sign(a, 194, PT + 8, KZ1 - 1, "north", "§5§l마왕의 대전\n§r동: 지하감옥 · 서: 심연", kind="crimson_hanging_sign")
    a.set(194, PT + 9, KZ1 - 1, PBB)
    # great hall: pillars, carpet, throne
    for x in (185, 203):
        for z in range(516, 538, 5):
            for y in range(PT + 1, HALL_TOP):
                a.set(x, y, z, DT if (y - PT) % 6 == 0 else B("polished_deepslate"))
            a.set(x + (1 if x < 194 else -1), PT + 9, z, DT)
            a.set(x + (1 if x < 194 else -1), PT + 8, z, B("soul_lantern", hanging=1))
    for z in range(KZ1 + 1, 534):
        for x in (193, 194, 195):
            a.set(x, PT + 1, z, B("purple_carpet"))
    for x in range(187, 202):
        for z in range(534, 540):
            a.set(x, PT + 1, z, B("obsidian"))
            if z >= 536:
                a.set(x, PT + 2, z, B("obsidian"))
    for x in range(187, 202):
        a.set(x, PT + 1, 533, stair("polished_blackstone_stairs", "south"))
        a.set(x, PT + 2, 535, stair("polished_blackstone_stairs", "south"))
    # the empty throne
    tx, tz = 194, 538
    a.set(tx, PT + 3, tz, stair("polished_blackstone_stairs", "south"))
    for dx in (-1, 1):
        a.set(tx + dx, PT + 3, tz, B("crying_obsidian"))
        a.set(tx + dx, PT + 4, tz, B("polished_blackstone_wall"))
    for y in range(PT + 3, PT + 12):
        a.set(tx, y, tz + 1, B("crying_obsidian") if y < PT + 11 else B("amethyst_block"))
    for dx in (-2, 2):
        for y in range(PT + 3, PT + 9):
            a.set(tx + dx, y, tz + 1, B("purple_wool") if y % 2 else B("black_wool"))
    stand_sign(a, tx - 3, PT + 2, 533, "north", "§5§l빈 옥좌\n§r마왕은 지하에...")
    # chandeliers
    for (x, z) in ((194, 518), (194, 526), (189, 530), (199, 530)):
        for k in range(1, 6):
            a.set(x, HALL_TOP - k, z, B("chain"))
        a.set(x, HALL_TOP - 6, z, PBB)
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a.set(x + d[0], HALL_TOP - 6, z + d[1], B("polished_blackstone_slab"))
            a.set(x + d[0], HALL_TOP - 5, z + d[1], B("soul_lantern"))
        a.set(x, HALL_TOP - 7, z, B("soul_lantern", hanging=1))
    for z in range(516, 538, 5):
        banner_wall(a, KX1 + 1, PT + 10, z, "east", 0, [("bo", 5), ("sku", 5)])
        banner_wall(a, KX2 - 1, PT + 10, z, "west", 0, [("bo", 5), ("sku", 5)])
    wall_sign(a, KX1 + 1, PT + 3, 522, "east", "§l§3← 워든 서식지\n§r뒷문 · 심연의 계단")
    wall_sign(a, KX2 - 1, PT + 3, 522, "west", "§l§4지하감옥 →\n§r보스")
    W.reserved[W.rect(KX1 - 2, KZ1 - 2, KX2 + 2, KZ2 + 2)] = True


def courtyard(W, rng):
    a = W.a
    tiles = [PBB, PB, B("cracked_polished_blackstone_bricks"), DT]
    for x in range(PX1 + 3, PX2 - 2):
        for z in range(PZ1 + 4, PZ2 - 2):
            if a.get(x, PT + 1, z) != AIR:
                continue
            if abs(x - 194) <= 2 or (abs(z - 526) <= 2 and x < KX1) or (abs(z - 506) <= 1):
                a.set(x, PT, z, rng.choice(tiles))
            elif rng.random() < 0.25:
                a.set(x, PT, z, rng.choice([BS, B("basalt", axis="y"), B("soul_soil")]))
    # dead trees, braziers, statues, skull piles
    for (x, z) in ((176, 504), (212, 504), (175, 544), (213, 544), (172, 530), (216, 520)):
        dead_tree(a, x, PT + 1, z, rng, kind="dark_oak")
    for (x, z) in ((189, 502), (199, 502), (189, 509), (199, 509)):
        a.set(x, PT + 1, z, PBB)
        campfire(a, x, PT + 2, z, soul=True)
    for (x, z, f) in ((176, 518, "east"), (212, 518, "west"), (176, 534, "east"), (212, 534, "west")):
        for y in range(PT + 1, PT + 4):
            a.set(x, y, z, B("polished_blackstone") if y < PT + 3 else B("chiseled_polished_blackstone"))
        a.set(x, PT + 4, z, B("wither_skeleton_skull", facing_direction=1))
        a.add_be(simple_be("Skull", x, PT + 4, z, Rotation=__import__("amulet_nbt").FloatTag(
            {"east": 270.0, "west": 90.0}[f]), SkullType=__import__("amulet_nbt").ByteTag(1)))
    for (x, z) in ((180, 548), (208, 548)):
        for (dx, dz) in ((0, 0), (1, 0), (0, 1)):
            a.set(x + dx, PT + 1, z + dz, B("bone_block"))
    W.reserved[W.rect(PX1, PZ1, PX2, PZ2)] = True


def heroes_camp(W, rng):
    """Convenience space: the heroes' camp just inside the crater."""
    a = W.a
    x1, z1, x2, z2 = 150, 456, 176, 476
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if a.get(x, CF + 1, z) == AIR:
                a.set(x, CF, z, rng.choice([B("coarse_dirt"), B("gravel"), B("podzol"), B("coarse_dirt")]))
    tent(W, 152, 458, CF, 6, "blue", axis="x")
    tent(W, 152, 470, CF, 6, "white", axis="x")
    campfire(a, 166, CF + 1, 466)
    for (x, z, d) in ((164, 466, "west"), (168, 466, "east"), (166, 464, "north"), (166, 468, "south")):
        a.set(x, CF + 1, z, stair("spruce_stairs", {"west": "east", "east": "west", "north": "south", "south": "north"}[d]))
    # stall
    for x in range(169, 176):
        for z in range(457, 462):
            if x in (169, 175) and z in (457, 461):
                for y in range(CF + 1, CF + 4):
                    a.set(x, y, z, B("spruce_log"))
            a.set(x, CF + 4, z, B("blue_wool") if (x % 2) else B("yellow_wool"))
    rec = shop_kit(W, "castle", "용사의 야영지", 172, CF + 1, 459, "south", counter=B("spruce_planks"),
                   chests=2)
    for (x, z) in ((150, 474), (176, 474)):
        for y in range(CF + 1, CF + 6):
            a.set(x, y, z, B("spruce_fence"))
        banner_stand(a, x, CF + 6, z, "north", 4, [("cbo", 11), ("cr", 11)])
    hang_sign(a, 172, CF + 3, 461, "south", "§l§b용사의 야영지\n§r상점 · 엔더 상자", kind="spruce_hanging_sign")
    for (x, z) in ((158, 466), (176, 466)):
        lamp_post(a, x, CF + 1, z, post=B("spruce_fence"), lamp=B("lantern"), h=3)
    W.reserved[W.rect(x1 - 1, z1 - 1, x2 + 1, z2 + 1)] = True
    return rec


def drill_hall(W, rng):
    a = W.a
    x1, z1, x2, z2 = 233, 478, 252, 500

    def floor(x, z):
        return rng.choice([PB, PBB, BS, B("cracked_polished_blackstone_bricks")])

    def wall(x, y, z):
        return DT if (y - CF) % 5 == 0 else PBB

    def props(box):
        for (x, z) in ((x1 + 4, z1 + 5), (x2 - 4, z1 + 5), (x1 + 4, z2 - 5), (x2 - 4, z2 - 5)):
            for y in range(CF + 1, CF + 9):
                a.set(x, y, z, PBB)
        for (x, z) in ((x1 + 9, z1 + 3), (x1 + 10, z1 + 3)):
            a.set(x, CF + 1, z, B("polished_blackstone_wall"))
            a.set(x, CF + 2, z, B("wither_skeleton_skull", facing_direction=1))
            a.add_be(simple_be("Skull", x, CF + 2, z, Rotation=__import__("amulet_nbt").FloatTag(180.0),
                               SkullType=__import__("amulet_nbt").ByteTag(1)))

    rec = hunting_ground(W, "castle", "마왕군 연병장", x1, z1, x2, z2, CF, floor, wall, gates=[("west", 10)],
                         wall_h=9, roof=PBB, roof_h=9, props=props, spawn_n=6,
                         gate_block="crimson_fence_gate", sign_kind="crimson_wall_sign")
    for x in range(x1, x2 + 1, 4):
        for z in range(z1, z2 + 1, 4):
            a.set(x, CF + 10, z, B("purple_stained_glass")) if (x + z) % 8 == 0 else None
    W.reserved[W.rect(x1 - 7, z1 - 2, x2 + 2, z2 + 2)] = True
    return rec


def crater_decor(W, rng):
    a = W.a
    reg = W.regions["crater"]["mask"]
    cand = [tuple(c) for c in np.argwhere(reg & ~W.reserved & (W.din > 3))]
    rng.shuffle(cand)
    occ = []
    for (i, k) in cand:
        x, z = i + X0, k + Z0
        if any((x - ox) ** 2 + (z - oz) ** 2 < 100 for ox, oz in occ) or len(occ) > 40:
            continue
        y = W.gy(x, z)
        if a.get(x, y + 1, z) != AIR:
            continue
        r = rng.random()
        if r < 0.35:
            dead_tree(a, x, y + 1, z, rng, kind="dark_oak")
        elif r < 0.6:
            h = rng.randint(3, 8)
            for t in range(h):
                a.set(x, y + 1 + t, z, B("basalt", axis="y"))
            if h > 5:
                a.set(x + 1, y + 1, z, B("basalt", axis="y"))
        elif r < 0.75:
            a.set(x, y, z, B("soul_soil"))
            a.set(x, y + 1, z, B("soul_fire"))
        elif r < 0.9:
            a.set(x, y + 1, z, B("bone_block"))
            a.set(x + 1, y + 1, z, B("bone_block", axis="x"))
        else:
            a.set(x, y + 1, z, B("crying_obsidian"))
            a.set(x, y + 2, z, B("crying_obsidian")) if rng.random() < 0.5 else None
        occ.append((x, z))
    for (i, k) in np.argwhere(reg & ~W.reserved):
        x, z = i + X0, k + Z0
        y = W.gy(x, z)
        r = rng.random()
        if a.get(x, y, z) == BS:
            if r < 0.12:
                a.set(x, y, z, B("basalt", axis="y"))
            elif r < 0.17:
                a.set(x, y, z, B("magma"))
            elif r < 0.22:
                a.set(x, y, z, B("soul_soil"))


def roads(W, rng):
    a = W.a
    tiles = [PBB, PB, B("cracked_polished_blackstone_bricks"), DT]
    paint = [(196, 450), (194, 462), (194, 486)]
    cells = paint_path(W, paint, 2, tiles, rng)
    cells |= paint_path(W, [(196, 452), (180, 464), (176, 466)], 1, tiles, rng)
    cells |= paint_path(W, [(194, 470), (222, 482), (226, 488)], 1, tiles, rng)
    cells |= paint_path(W, [(PX1 - 9, 526), (140, 526), (131, 526)], 2, tiles, rng)
    for (x, z) in ((190, 458), (199, 470), (190, 480), (150, 522), (140, 530), (214, 478)):
        y = W.gy(x, z)
        a.set(x, y + 1, z, B("polished_blackstone_wall"))
        a.set(x, y + 2, z, B("polished_blackstone_wall"))
        a.set(x, y + 3, z, B("soul_lantern"))
    stand_sign(a, 198, W.gy(198, 456) + 1, 456, "north", "§5§l마왕성\n§r남쪽: 성문\n§7북서: 용사의 야영지")


def build(W):
    import random
    rng = random.Random(W.seed + 900)
    moat_and_bridges(W, rng)
    curtain_walls(W, rng)
    keep(W, rng)
    courtyard(W, rng)
    heroes_camp(W, rng)
    drill_hall(W, rng)
    roads(W, rng)
    crater_decor(W, rng)
    W.spawns["castle"] = (196, CF + 1, 452)
    W.mark_surface(W.regions["crater"]["mask"])
    W.allow("castle", PX1 - 2, PT - 1, PZ1 - 2, PX2 + 2, HALL_TOP, PZ2 + 2)
    W.light_boxes.append(("crater", 128, 446, 258, 584, CF - 2, CF + 14, 1, 8))
    W.light_boxes.append(("keep", KX1, KZ1, KX2, KZ2, PT, HALL_TOP, 5, 10))
    leaks = leak_check(W, (PX1 - 8, LAVA_Y - 4, PZ1 - 8, PX2 + 8, LAVA_Y + 1, PZ2 + 8))
    print("  moat lava leaks:", len(leaks), leaks[:8])
