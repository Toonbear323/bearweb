"""Illager HQ (boss): a woodland-mansion style fortress in a dark oak forest west of the village.

Ground floor (feet y=66):
  E  entrance hall (two storeys, grand stairs)      x -136..-120, z 213..239
  C  hall of banners -> boss gate                    x -160..-136, z 219..233
  N  guard barracks = hunting ground (gated)         x -160..-136, z 203..219
  S  infiltrators' den = convenience space           x -160..-136, z 233..249
  T  ritual throne hall = boss arena (17 high)       x -184..-160, z 209..243
Upper floor (feet y=73): gallery around the entrance hall, portrait gallery with a barred
window overlooking the throne hall, library (north), war room (south).
"""
import math

import numpy as np

from mcw import B, AIR, simple_be
from gen_common import stair, slab, dark_oak_tree, clamp_gradient, leaf_blob
from rpg_world import G, X0, Z0
from rpg_parts import (wall_sign, hang_sign, stand_sign, lamp_post, crook_lamp, hanging_lantern, barrel, shop_kit,
                       paint_path, banner_wall, banner_stand, campfire, chest, light_grid, ender_chest, DV, FACE,
                       HUNT_LIGHT, pot)
from rpg_build import gable_roof, round_tower, tent
from layout import HQ_C, PASS_HQ

F1 = 65            # ground floor top block (feet 66)
F2 = 72            # upper floor top block (feet 73)
ATT = 79           # attic floor / ceiling of the upper floor
T_TOP = 83         # throne hall ceiling
PATH = [(-104, 227), (-110, 224), (-116, 226), (-119, 226)]

DO, DOL, BI = B("dark_oak_planks"), B("dark_oak_log"), B("birch_planks")
COB = B("cobblestone")


def shape(W):
    reg = W.regions["hq"]["mask"]
    W.H[reg & (W.din > 6)] = F1
    # mansion pad + courtyard
    W.H[W.rect(-190, 198, -98, 254)][reg[W.rect(-190, 198, -98, 254)]] = F1
    W.H = np.where(reg, clamp_gradient(W.H, reg, 1), W.H)


def walls(W, x1, z1, x2, z2, y_top, windows=("north", "south", "west", "east"), rows=((67, 69), (74, 76)),
          bands=(72, 79), every=5):
    a = W.a
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if not (x in (x1, x2) or z in (z1, z2)):
                continue
            side = "north" if z == z1 else "south" if z == z2 else "west" if x == x1 else "east"
            along = (x - x1) if side in ("north", "south") else (z - z1)
            corner = x in (x1, x2) and z in (z1, z2)
            col = corner or along % every == 0
            for y in range(F1 - 5, F1 + 1):
                a.set(x, y, z, COB)
            for y in range(F1 + 1, y_top + 1):
                if col:
                    b = DOL
                elif y in bands:
                    b = BI
                elif y == F1 + 1:
                    b = COB
                else:
                    b = DO
                    if side in windows and along % every in (2, 3) and any(lo <= y <= hi for lo, hi in rows):
                        b = B("glass_pane")
                a.set(x, y, z, b)


def floor(W, x1, z1, x2, z2, y, a_blk, b_blk=None, checker=2):
    a = W.a
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            b = a_blk if b_blk is None or ((x // checker + z // checker) % 2 == 0) else b_blk
            a.set(x, y, z, b)


def clear(W, x1, y1, z1, x2, y2, z2):
    W.a.fill(x1, y1, z1, x2, y2, z2, AIR)


def opening(W, x1, z1, x2, z2, y1, y2):
    W.a.fill(x1, y1, z1, x2, y2, z2, AIR)


def shell(W):
    a = W.a
    # foundations / pad
    for x in range(-186, -118):
        for z in range(201, 252):
            for y in range(F1 - 6, F1 + 1):
                a.set(x, y, z, COB)
    # interiors cleared first
    clear(W, -184, F1 + 1, 209, -120, 100, 249)
    clear(W, -160, F1 + 1, 203, -120, 100, 249)
    # section walls
    walls(W, -136, 213, -120, 239, ATT)                                  # E
    walls(W, -160, 203, -136, 219, ATT, windows=("north",))               # N
    walls(W, -160, 233, -136, 249, ATT, windows=("south",))               # S
    walls(W, -160, 219, -136, 233, ATT, windows=())                      # C
    walls(W, -184, 209, -160, 243, T_TOP + 1, windows=("north", "south", "west"),
          rows=((75, 80),), bands=(72, T_TOP + 1), every=6)               # T
    # floors
    floor(W, -135, 214, -121, 238, F1, DO, BI)
    floor(W, -159, 220, -137, 232, F1, DO, BI)
    floor(W, -159, 204, -137, 218, F1, B("spruce_planks"))
    floor(W, -159, 234, -137, 248, F1, DO)
    floor(W, -183, 210, -161, 242, F1, B("polished_blackstone_bricks"), B("polished_deepslate"), checker=3)
    # upper floors (the entrance hall keeps an open centre; the throne hall is double height)
    floor(W, -159, 220, -137, 232, F2, DO, BI)
    floor(W, -159, 204, -137, 218, F2, DO)
    floor(W, -159, 234, -137, 248, F2, DO)
    floor(W, -135, 214, -131, 238, F2, DO)          # west gallery of the hall
    for y in (ATT,):
        floor(W, -159, 204, -121, 248, y, DO)
        floor(W, -135, 214, -121, 238, y, DO)
    floor(W, -183, 210, -161, 242, T_TOP + 1, DO)
    # ceiling beams under the attic floor
    for x in range(-159, -120, 4):
        for z in range(204, 249):
            if a.get(x, ATT, z) == DO:
                a.set(x, ATT, z, B("dark_oak_log", axis="z"))
    # roofs
    gable_roof(a, -136, 213, -120, 239, ATT + 1, "dark_oak_stairs", DO, DO, axis="z")
    gable_roof(a, -160, 203, -136, 219, ATT + 1, "dark_oak_stairs", DO, DO, axis="x")
    gable_roof(a, -160, 233, -136, 249, ATT + 1, "dark_oak_stairs", DO, DO, axis="x")
    gable_roof(a, -160, 219, -136, 233, ATT + 1, "dark_oak_stairs", DO, DO, axis="x")
    gable_roof(a, -184, 209, -160, 243, T_TOP + 2, "dark_oak_stairs", DO, DO, axis="z")
    # chimneys with smoking campfires
    for (cx, cz, top) in ((-150, 205, 92), (-150, 247, 92), (-128, 215, 92), (-172, 211, 100)):
        for x in (cx, cx + 1):
            for z in (cz, cz + 1):
                for y in range(ATT, top + 1):
                    a.set(x, y, z, COB)
        campfire(a, cx, top + 1, cz)
    # cobblestone band at the base
    for x in range(-186, -118):
        for z in (201, 251):
            pass


def entrance_hall(W, rng):
    a = W.a
    # main door (east) and porch
    opening(W, -120, 224, -120, 228, F1 + 1, F1 + 5)
    for z in range(222, 231):
        for x in range(-119, -114):
            a.set(x, F1, z, COB if x > -116 else DO)
            if z in (222, 230) and x in (-118, -115):
                for y in range(F1 + 1, F1 + 7):
                    a.set(x, y, z, DOL)
        for x in range(-119, -114):
            a.set(x, F1 + 7, z, stair("dark_oak_stairs", "west") if z not in (222, 230) else DO)
    for z in range(222, 231):
        a.set(-114, F1, z, stair("cobblestone_stairs", "west"))
    for z in (223, 229):
        banner_wall(a, -119, F1 + 5, z, "east", 15, ominous=True)
    hang_sign(a, -116, F1 + 6, 226, "east", "§l§4우민 본거지\n§r보스 구역", kind="dark_oak_hanging_sign")
    a.set(-116, F1 + 7, 226, DO)
    # flanking towers
    for cz in (214, 238):
        round_tower(W, -117, cz, F1, 3, 16, COB, floor=DO, roof=DO, roof_h=8, windows=[4, 9, 13],
                    cap_block=B("lightning_rod"))
        for k in range(1, 17):
            a.set(-117, F1 + k, cz, DOL)
    # grand stairs along the north and south walls, rising west to the gallery
    for zs in ((214, 215, 216), (236, 237, 238)):
        for k in range(7):
            x = -124 - k
            for z in zs:
                for y in range(F1 + 1, F1 + 1 + k):
                    a.set(x, y, z, DO)
                a.set(x, F1 + 1 + k, z, stair("dark_oak_stairs", "west"))
    # gallery railing and columns
    for z in range(217, 236):
        a.set(-131, F2 + 1, z, B("dark_oak_fence"))
    for z in range(218, 236, 4):
        for y in range(F1 + 1, F2):
            a.set(-131, y, z, DOL)
    for z in (214, 215, 216, 236, 237, 238):
        for y in range(F1 + 1, F2 + 1):
            if a.get(-131, y, z) == AIR:
                a.set(-131, y, z, DO)
    # balustrades on the stairs' open side (solid stringer + fence)
    for k in range(7):
        x = -124 - k
        for zz in (217, 235):
            for y in range(F1 + 1, F1 + 2 + k):
                a.set(x, y, zz, DO)
            a.set(x, F1 + 2 + k, zz, B("dark_oak_fence"))
    # centrepiece: red carpet, chandelier, statue-like banner stand
    for x in range(-129, -120):
        for z in range(224, 229):
            a.set(x, F1 + 1, z, B("red_carpet"))
    for (cx, cz) in ((-125, 226),):
        a.set(cx, ATT, cz, DOL)
        hanging_lantern(a, cx, ATT - 1, cz, chain=3)
        for d in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            a.set(cx + d[0], ATT - 1, cz + d[1], B("chain"))
            a.set(cx + d[0], ATT - 2, cz + d[1], B("lantern", hanging=1))
    for z in (218, 234):
        banner_wall(a, -121, F1 + 4, z, "west", 15, ominous=True)
    wall_sign(a, -121, F1 + 2, 222, "west", "§l§4우민 본거지\n§r서쪽 문: 대전당 (보스)\n§7위층: 서재 · 작전실")
    # doors: hall -> banner hall (both floors)
    opening(W, -136, 224, -136, 228, F1 + 1, F1 + 5)
    opening(W, -136, 224, -136, 228, F2 + 1, F2 + 4)


def banner_hall(W, rng):
    """C: hall of banners on the ground floor, portrait gallery above."""
    a = W.a
    for x in range(-158, -137, 4):
        for z in (221, 231):
            for y in range(F1 + 1, F2):
                a.set(x, y, z, DOL)
    for x in range(-156, -138, 4):
        banner_wall(a, x, F1 + 4, 220, "south", 15, ominous=True)
        banner_wall(a, x, F1 + 4, 232, "north", 15, ominous=True)
    for x in range(-159, -136):
        for z in (225, 226, 227):
            a.set(x, F1 + 1, z, B("red_carpet"))
    for x in (-155, -147, -139):
        a.set(x, F2, 226, DOL)
        hanging_lantern(a, x, F2 - 1, 226, chain=1)
    # boss gate with a portcullis frame
    opening(W, -160, 224, -160, 228, F1 + 1, F1 + 6)
    for z in range(223, 230):
        a.set(-159, F1 + 7, z, B("polished_blackstone_bricks"))
        a.set(-159, F1 + 6, z, B("iron_bars") if 224 <= z <= 228 else B("polished_blackstone_bricks"))
    for z in (222, 230):
        for y in range(F1 + 1, F1 + 7):
            a.set(-159, y, z, B("polished_blackstone_bricks"))
    for z in (223, 229):
        a.set(-158, F1 + 1, z, B("polished_blackstone_wall"))
        a.set(-158, F1 + 2, z, B("soul_lantern"))
    wall_sign(a, -158, F1 + 5, 222, "east", "§l§4⚠ 보스 ⚠\n§r의식의 대전당")
    wall_sign(a, -158, F1 + 5, 230, "east", "§l§4⚠ 보스 ⚠\n§r의식의 대전당")
    # doors to the barracks (north, gated) and the den (south)
    for x in (-149, -148):
        a.set(x, F1 + 1, 219, B("dark_oak_fence_gate", cardinal="north"))
        a.set(x, F1 + 2, 219, AIR)
        a.set(x, F1 + 3, 219, DO)
    opening(W, -146, 233, -144, 233, F1 + 1, F1 + 3)
    # upper floor: portrait gallery with a barred window into the throne hall
    for z in range(222, 231):
        for y in range(F2 + 2, F2 + 6):
            a.set(-160, y, z, B("iron_bars"))
    for x in range(-158, -137, 5):
        a.set(x, F2 + 3, 220, B("dark_oak_planks"))
    for x in range(-156, -138, 5):
        banner_wall(a, x, F2 + 4, 220, "south", 14, [("bo", 15), ("mc", 1)])
        banner_wall(a, x, F2 + 4, 232, "north", 14, [("bo", 15), ("mc", 1)])
    for x in range(-158, -137):
        for z in (225, 226, 227):
            a.set(x, F2 + 1, z, B("gray_carpet"))
    for x in (-153, -143):
        hanging_lantern(a, x, ATT - 1, 226, chain=1)
    wall_sign(a, -159, F2 + 2, 221, "east", "§l관람창\n§r아래가 대전당이다")
    opening(W, -150, 219, -148, 219, F2 + 1, F2 + 3)   # to the library
    opening(W, -150, 233, -148, 233, F2 + 1, F2 + 3)   # to the war room


def barracks(W, rng):
    """N wing ground floor: guard barracks = hunting ground (two fence gates in series)."""
    a = W.a
    x1, z1, x2, z2 = -159, 204, -137, 218
    # inner gate pen
    for x in range(-151, -145):
        a.set(x, F1 + 1, 216, B("dark_oak_fence"))
    for z in (217, 218):
        a.set(-151, F1 + 1, z, B("dark_oak_fence"))
        a.set(-146, F1 + 1, z, B("dark_oak_fence"))
    for x in (-149, -148):
        a.set(x, F1 + 1, 216, B("dark_oak_fence_gate", cardinal="north"))
    # training props
    for (x, z) in ((-156, 207), (-152, 207), (-142, 207), (-156, 213), (-140, 212)):
        a.set(x, F1 + 1, z, B("dark_oak_fence")); a.set(x, F1 + 2, z, B("hay_block"))
        a.set(x, F1 + 3, z, B("carved_pumpkin", cardinal="south"))
    for x in range(-158, -138, 3):
        a.set(x, F1 + 2, 204, B("target")) if x % 2 else None
    for x in range(-157, -139, 6):
        banner_wall(a, x, F1 + 4, 204, "south", 15, ominous=True)
    for (x, z) in ((-158, 216), (-138, 216), (-138, 205)):
        a.set(x, F1 + 1, z, B("barrel", facing_direction=1))
        a.set(x, F1 + 2, z, B("grindstone", attachment="standing", direction=0)) if x == -138 and z == 216 else None
    a.set(-158, F1 + 1, 205, B("anvil", cardinal="east"))
    a.set(-158, F1 + 1, 206, B("smithing_table"))
    for x in range(-157, -138, 5):
        hanging_lantern(a, x, F2 - 1, 211, chain=1)
    wall_sign(a, -147, F1 + 3, 220, "south", "§l§c⚔ 사냥터 ⚔\n§r근위대 훈련장")
    lights = []
    for x in range(x1 + 2, x2, 5):
        for z in range(z1 + 2, z2 - 1, 5):
            if a.get(x, F1 + 5, z) == AIR:
                a.set(x, F1 + 5, z, B("light_block_%d" % HUNT_LIGHT))
                lights.append((x, F1 + 5, z))
    pts = [(-154, F1 + 1, 210), (-148, F1 + 1, 209), (-143, F1 + 1, 210), (-154, F1 + 1, 215), (-142, F1 + 1, 215),
           (-148, F1 + 1, 212)]
    W.hunts.append(dict(region="hq", name="근위대 훈련장", box=(x1, F1 + 1, z1, x2, F2 - 1, z2), floor_y=F1,
                        entrances=[(-149, F1 + 1, 220)], spawn_points=pts, lights=lights, roofed=True))


def den(W, rng):
    """S wing ground floor: infiltrators' den = convenience space."""
    a = W.a
    wall_sign(a, -145, F1 + 4, 232, "north", "§l§a잠입 거점\n§r상점 · 엔더 상자", kind="darkoak_wall_sign")
    rec = shop_kit(W, "hq", "잠입 거점", -148, F1 + 1, 241, "north", counter=B("spruce_planks"))
    for x in (-151, -152, -138, -139):
        a.set(x, F1 + 1, 247, B("barrel", facing_direction=1))
        a.set(x, F1 + 2, 247, B("barrel", facing_direction=1)) if x in (-151, -139) else None
    a.set(-158, F1 + 1, 235, B("cartography_table"))
    a.set(-158, F1 + 1, 236, B("crafting_table"))
    a.set(-158, F1 + 1, 237, B("loom", direction=1))
    for z in (240, 241, 242):
        a.set(-158, F1 + 1, z, stair("spruce_stairs", "west"))
    for (x, z) in ((-155, 238), (-141, 238), (-148, 245)):
        hanging_lantern(a, x, F2 - 1, z, chain=1)
    for x in range(-159, -136):
        for z in range(235, 238):
            if a.get(x, F1 + 1, z) == AIR and -150 <= x <= -140:
                a.set(x, F1 + 1, z, B("green_carpet"))
    banner_wall(a, -145, F1 + 4, 248, "north", 4, [("cbo", 11), ("mc", 11)])
    wall_sign(a, -137, F1 + 2, 240, "west", "§l엔더 상자 →\n§r보스전 전에\n장비를 챙기세요")
    return rec


def library(W, rng):
    a = W.a
    x1, z1, x2, z2 = -159, 204, -137, 218
    for x in range(x1, x2 + 1):
        for z in (z1,):
            for y in range(F2 + 1, ATT):
                if a.get(x, y, z - 1) != B("glass_pane"):
                    pass
    for x in range(x1 + 1, x2, 1):
        if (x - x1) % 5 in (2, 3):
            continue
        for y in range(F2 + 1, F2 + 5):
            a.set(x, y, z1, B("bookshelf"))
    for z in range(z1 + 1, z2 - 1):
        for y in range(F2 + 1, F2 + 5):
            a.set(x1, y, z, B("bookshelf"))
            a.set(x2, y, z, B("bookshelf"))
    for row in (z1 + 5, z1 + 9):
        for x in range(x1 + 4, x2 - 3):
            if x in (-149, -148, -147):
                continue
            for y in range(F2 + 1, F2 + 4):
                a.set(x, y, row, B("bookshelf"))
    for (x, z) in ((-153, 216), (-142, 216)):
        a.set(x, F2 + 1, z, B("lectern", cardinal="north"))
    for x in (-155, -141):
        hanging_lantern(a, x, ATT - 1, 211, chain=1)
    a.set(-148, F2 + 1, 207, B("enchanting_table"))
    a.add_be(simple_be("EnchantTable", -148, F2 + 1, 207))
    wall_sign(a, -148, F2 + 3, 218, "north", "§l서재\n§r우민 마법서 보관소")


def war_room(W, rng):
    a = W.a
    for x in range(-152, -144):
        for z in range(239, 243):
            a.set(x, F2 + 1, z, B("dark_oak_planks") if x in (-152, -145) or z in (239, 242) else B("cartography_table"))
    for x in range(-157, -138, 5):
        banner_wall(a, x, F2 + 4, 248, "north", 15, ominous=True)
    for (x, z) in ((-155, 241), (-141, 241)):
        hanging_lantern(a, x, ATT - 1, z, chain=1)
    for z in range(236, 247, 3):
        a.set(-158, F2 + 1, z, B("dark_oak_fence")); a.set(-158, F2 + 2, z, B("iron_bars"))
    wall_sign(a, -152, F2 + 3, 234, "south", "§l작전실\n§r마을 습격 계획...")


def throne_hall(W, rng):
    """T: boss arena."""
    a = W.a
    x1, z1, x2, z2 = -183, 210, -161, 242
    # columns with soul lanterns
    for x in range(-179, -162, 6):
        for z in (213, 239):
            for y in range(F1 + 1, T_TOP + 1):
                a.set(x, y, z, DOL if (y - F1) % 6 else B("polished_blackstone_bricks"))
    for x in range(-179, -162, 6):
        for z in (214, 238):
            a.set(x, F1 + 6, z, B("dark_oak_planks"))
            a.set(x, F1 + 5, z, B("soul_lantern", hanging=1))
    # throne dais (west)
    for x in range(-183, -176):
        for z in range(220, 233):
            a.set(x, F1 + 1, z, B("polished_blackstone_bricks"))
            if x <= -179 and 222 <= z <= 230:
                a.set(x, F1 + 2, z, B("polished_blackstone_bricks"))
    for z in range(220, 233):
        a.set(-176, F1 + 1, z, stair("polished_blackstone_brick_stairs", "west"))
    for z in range(222, 231):
        a.set(-178, F1 + 2, z, stair("polished_blackstone_brick_stairs", "west"))
    # the throne
    tx, tz = -182, 226
    a.set(tx, F1 + 3, tz, stair("dark_oak_stairs", "west"))
    for dz in (-1, 1):
        a.set(tx, F1 + 3, tz + dz, B("dark_oak_planks"))
        a.set(tx, F1 + 4, tz + dz, B("dark_oak_fence"))
        a.set(tx, F1 + 5, tz + dz, B("gold_block"))
    for y in range(F1 + 3, F1 + 9):
        a.set(tx - 1, y, tz, B("gold_block") if y == F1 + 8 else B("dark_oak_planks"))
    banner_wall(a, -182, F1 + 7, tz - 2, "east", 15, ominous=True)
    banner_wall(a, -182, F1 + 7, tz + 2, "east", 15, ominous=True)
    for y in range(F1 + 6, T_TOP - 1):
        a.set(-183, y, tz, B("red_wool") if y % 2 else B("black_wool"))
    # ritual circle in front of the throne
    cx, cz = -170, 226
    for x in range(cx - 6, cx + 7):
        for z in range(cz - 6, cz + 7):
            d = math.hypot(x - cx, z - cz)
            if 4.5 <= d <= 5.5:
                a.set(x, F1, z, B("red_glazed_terracotta") if (x + z) % 2 else B("crimson_planks"))
            elif d < 1.2:
                a.set(x, F1, z, B("gold_block"))
            elif abs(x - cx) == abs(z - cz) and d < 4.5:
                a.set(x, F1, z, B("black_concrete"))
    # aisle carpet from the gate
    for x in range(-176, -160):
        for z in (225, 226, 227):
            if a.get(x, F1 + 1, z) == AIR and not (math.hypot(x - cx, z - cz) <= 5.5):
                a.set(x, F1 + 1, z, B("red_carpet"))
    # chandeliers
    for (x, z) in ((-176, 220), (-176, 232), (-166, 220), (-166, 232), (-170, 226)):
        a.set(x, T_TOP, z, DOL)
        for k in range(1, 5):
            a.set(x, T_TOP - k, z, B("chain"))
        a.set(x, T_TOP - 5, z, B("dark_oak_planks"))
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a.set(x + d[0], T_TOP - 5, z + d[1], B("dark_oak_slab"))
            a.set(x + d[0], T_TOP - 4, z + d[1], B("lantern"))
        a.set(x, T_TOP - 6, z, B("lantern", hanging=1))
    # high banners on the walls
    for x in range(-180, -162, 6):
        banner_wall(a, x, F1 + 9, z1, "south", 14, [("bo", 15), ("mc", 1)])
        banner_wall(a, x, F1 + 9, z2, "north", 14, [("bo", 15), ("mc", 1)])
    for (x, z) in ((-181, 212), (-181, 240), (-163, 212), (-163, 240)):
        campfire(a, x, F1 + 1, z, soul=True)
    a.set(cx, F1 - 1, cz, B("lodestone"))
    lights = light_grid(W, x1, z1, x2, z2, F1 + 7, level=10, spacing=5)
    W.bosses.append(dict(region="hq", name="의식의 대전당", boss_spawn=(cx, F1 + 1, cz),
                         box=(x1, F1 + 1, z1, x2, T_TOP, z2), entrance=(-159, F1 + 1, 226),
                         view=(-150, F2 + 1, 226)))


def courtyard(W, rng):
    a = W.a
    for x in range(-114, -100):
        for z in range(214, 240):
            if W.regions["hq"]["mask"][x - X0, z - Z0] or True:
                a.set(x, F1, z, rng.choice([COB, B("gravel"), B("mossy_cobblestone"), B("coarse_dirt"), COB]))
                for y in range(F1 + 1, F1 + 4):
                    a.set(x, y, z, AIR)
    tent(W, -112, 216, F1, 5, "gray", axis="x")
    tent(W, -112, 236, F1, 5, "white", axis="x")
    for (x, z) in ((-104, 218), (-104, 234)):
        for y in range(F1 + 1, F1 + 6):
            a.set(x, y, z, B("dark_oak_fence"))
        a.set(x + 1, F1 + 5, z, B("dark_oak_planks"))
        banner_stand(a, x, F1 + 6, z, "east", 15, ominous=True)
    campfire(a, -108, F1 + 1, 226 - 7)
    campfire(a, -108, F1 + 1, 226 + 7)
    # caged iron golem spot (empty cage)
    for x in range(-103, -100):
        for z in range(224, 229):
            edge = x in (-103, -101) or z in (224, 228)
            for y in (F1 + 1, F1 + 2, F1 + 3):
                a.set(x, y, z, B("iron_bars") if edge else AIR)
            a.set(x, F1 + 4, z, DO)
    wall_sign(a, -104, F1 + 2, 226, "west", "§l§7부서진 우리\n§r골렘이 탈출했다")
    W.reserved[W.rect(-120, 205, -98, 250)] = True


def forest(W, rng):
    a = W.a
    reg = W.regions["hq"]["mask"]
    W.reserved[W.rect(-188, 199, -116, 253)] = True
    occ = []
    cand = [tuple(c) for c in np.argwhere(reg & (W.din > 4) & ~W.reserved)]
    rng.shuffle(cand)
    for (i, k) in cand:
        x, z = i + X0, k + Z0
        if any((x - ox) ** 2 + (z - oz) ** 2 < 42 for ox, oz in occ):
            continue
        y = W.gy(x, z)
        if a.get(x, y, z) not in (B("grass_block"), B("podzol"), B("coarse_dirt")) or a.get(x, y + 1, z) != AIR:
            continue
        if any(W.reserved[i + dx, k + dz] for dx in (-2, 0, 3) for dz in (-2, 0, 3)):
            continue
        r = rng.random()
        if r < 0.10:
            giant_mushroom(a, x, y + 1, z, rng)
        else:
            dark_oak_tree(a, x, y + 1, z, rng)
        occ.append((x, z))
    for (i, k) in np.argwhere(reg & ~W.reserved):
        x, z = i + X0, k + Z0
        y = W.gy(x, z)
        if a.get(x, y, z) != B("grass_block"):
            continue
        r = rng.random()
        if r < 0.2:
            a.set(x, y, z, B("podzol"))
        elif r < 0.27:
            a.set(x, y, z, B("coarse_dirt"))
        if a.get(x, y + 1, z) == AIR:
            r = rng.random()
            if r < 0.1:
                a.set(x, y + 1, z, B("fern"))
            elif r < 0.13:
                a.set(x, y + 1, z, B("brown_mushroom" if r < 0.115 else "red_mushroom"))
            elif r < 0.2:
                a.set(x, y + 1, z, B("short_grass"))


def giant_mushroom(a, x, y, z, rng):
    h = rng.randint(5, 7)
    red = rng.random() < 0.5
    for k in range(h):
        a.set(x, y + k, z, B("mushroom_stem"))
    cap = B("red_mushroom_block") if red else B("brown_mushroom_block")
    if red:
        for k in range(h - 3, h + 1):
            r = 2 if k < h else 1
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if k < h and abs(dx) < r and abs(dz) < r:
                        continue
                    a.put(x + dx, y + k, z + dz, cap)
    else:
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if abs(dx) == 3 and abs(dz) == 3:
                    continue
                a.put(x + dx, y + h, z + dz, cap)


def path(W, rng):
    a = W.a
    cells = paint_path(W, PATH, 2, [B("gravel"), B("coarse_dirt"), B("cobblestone"), B("mossy_cobblestone")], rng)
    for (x, z) in ((-106, 221), (-112, 230)):
        lamp_post(a, x, W.gy(x, z) + 1, z, post=B("dark_oak_fence"), lamp=B("soul_lantern"), h=3)


def build(W):
    import random
    rng = random.Random(W.seed + 500)
    courtyard(W, rng)
    shell(W)
    entrance_hall(W, rng)
    banner_hall(W, rng)
    barracks(W, rng)
    rec = den(W, rng)
    library(W, rng)
    war_room(W, rng)
    throne_hall(W, rng)
    path(W, rng)
    forest(W, rng)
    W.spawns["hq"] = (-108, F1 + 1, 226)
    W.mark_surface(W.regions["hq"]["mask"])
    W.allow("hq_mansion", -186, F1 - 1, 200, -114, ATT + 1, 252)
    W.light_boxes.append(("hq_out", -200, 168, -94, 284, F1 - 2, F1 + 14, 1, 8))
    W.light_boxes.append(("hq_in", -185, 202, -119, 250, F1, ATT, 6, 10))
