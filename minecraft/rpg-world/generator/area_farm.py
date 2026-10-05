"""Farm valley west of spawn: fields, barn, silo, windmill, animal pens, farm market, field hunting ground."""
import math

import numpy as np

from mcw import B, AIR
from gen_common import stair, slab, oak_tree, birch_tree, FLOWERS, clamp_gradient, tall_plant
from rpg_world import G, X0, Z0
from rpg_parts import (wall_sign, hang_sign, stand_sign, lamp_post, hanging_lantern, barrel, pot, shop_kit,
                       hunting_ground, paint_path, gatehouse, path_steps, fence_line, DV, chest)
from rpg_build import house, round_tower, gable_roof
from layout import FARM_C, PASS_FARM

ROAD = [(-98, -8), (-125, -8), (-150, -6), (-158, -2)]
SPUR_S = [(-118, -8), (-118, 3)]
SPUR_HUNT = [(-158, -2), (-161, 4)]
SPUR_N = [(-139, -8), (-139, -15)]


def shape(W):
    reg = W.regions["farm"]["mask"]
    W.H[reg & (W.din > 6)] = G
    pad = W.rect(-112, -2, -90, 26)                # silo + animal pens
    W.H[pad][reg[pad]] = G
    W.H = np.where(reg, clamp_gradient(W.H, reg, 1), W.H)


def fields(W, rng):
    a = W.a
    crops = [("wheat", "growth", 7), ("carrots", "growth", 7), ("potatoes", "growth", 7), ("beetroot", "growth", 7)]
    x0, z1, z2 = -158, -42, -18
    fence = B("oak_fence")
    for p in range(4):
        px = x0 + p * 10
        name, st, v = crops[p]
        for dx in range(9):
            x = px + dx
            for z in range(z1, z2 + 1):
                if dx == 4:
                    a.set(x, G - 1, z, B("dirt"))
                    a.set(x, G, z, B("water"))
                else:
                    a.set(x, G, z, B("farmland", moisturized_amount=7))
                    a.set(x, G + 1, z, B(name, **{st: v}))
        if p < 3:
            for z in range(z1, z2 + 1):
                a.set(px + 9, G, z, B("grass_path"))
                a.set(px + 9, G + 1, z, AIR)
    # fence around the fields with gates toward the road
    fx1, fx2, fz1, fz2 = x0 - 1, x0 + 39, z1 - 1, z2 + 1
    for x in range(fx1, fx2 + 1):
        a.set(x, G + 1, fz1, fence)
        a.set(x, G + 1, fz2, fence)
        a.set(x, G, fz1, B("grass_block")); a.set(x, G, fz2, B("grass_block"))
    for z in range(fz1, fz2 + 1):
        a.set(fx1, G + 1, z, fence)
        a.set(fx2, G + 1, z, fence)
        a.set(fx1, G, z, B("grass_block")); a.set(fx2, G, z, B("grass_block"))
    for gx in (x0 + 9, x0 + 19, x0 + 29):
        a.set(gx, G + 1, fz2, B("fence_gate", cardinal="south"))
        a.set(gx, G, fz2, B("grass_path"))
    for x in (fx1, x0 + 4, x0 + 14, x0 + 24, x0 + 34, fx2):
        a.set(x, G + 2, fz2, B("lantern"))
    # scarecrows
    for (x, z) in ((x0 + 2, -30), (x0 + 22, -26)):
        a.set(x, G + 1, z, B("oak_fence"))
        a.set(x, G + 2, z, B("hay_block"))
        a.set(x, G + 3, z, B("carved_pumpkin", cardinal="south"))
        a.set(x - 1, G + 2, z, B("oak_fence")); a.set(x + 1, G + 2, z, B("oak_fence"))
    W.reserved[W.rect(fx1 - 1, fz1 - 1, fx2 + 1, fz2 + 1)] = True
    stand_sign(a, x0 + 19, G + 1, fz2 + 2, "south", "§l§a농장 밭\n§r밀 · 당근\n감자 · 비트")


def barn(W, rng):
    a = W.a
    x1, z1, x2, z2 = -130, 4, -110, 20
    red, trim = B("red_terracotta"), B("stripped_birch_log", axis="y")
    house(W, x1, z1, x2, z2, G, h=6, post=trim, wall=red, floor=B("spruce_planks"), roof_stairs="dark_oak_stairs",
          roof_ridge=B("dark_oak_planks"), gable=red, window=B("white_stained_glass_pane"), axis="z", lamp=False,
          base=B("cobblestone"))
    # big barn door on the north side, X trim
    for x in range(-122, -117):
        for y in range(G + 1, G + 6):
            a.set(x, y, z1, AIR)
    for y in range(G + 1, G + 7):
        a.set(-123, y, z1, trim); a.set(-117, y, z1, trim)
    for x in range(-123, -116):
        a.set(x, G + 6, z1, trim)
    for x in range(x1, x2 + 1):
        a.set(x, G + 7, z1, B("white_concrete"))
        a.set(x, G + 7, z2, B("white_concrete"))
    hang_sign(a, -120, G + 5, z1 - 1, "north", "§l§c헛간", kind="spruce_hanging_sign")
    a.set(-120, G + 6, z1 - 1, trim)
    # stalls and hay inside
    for z in range(z1 + 2, z2 - 1, 4):
        for x in (x1 + 1, x1 + 2, x1 + 3):
            a.set(x, G + 1, z, B("spruce_fence"))
        for x in (x2 - 1, x2 - 2, x2 - 3):
            a.set(x, G + 1, z, B("spruce_fence"))
    for (x, z) in ((x1 + 2, z1 + 4), (x1 + 2, z1 + 8), (x2 - 2, z1 + 4), (x2 - 2, z1 + 12)):
        a.set(x, G + 1, z, B("hay_block"))
        a.set(x, G + 2, z, B("hay_block")) if rng.random() < 0.5 else None
    for (x, z) in ((x1 + 2, z2 - 2), (x2 - 2, z2 - 2)):
        a.set(x, G + 1, z, B("cauldron", cauldron_liquid="water", fill_level=6))
        from mcw import simple_be
        a.add_be(simple_be("Cauldron", x, G + 1, z))
    for z in range(z1 + 3, z2 - 1, 5):
        hanging_lantern(a, -120, G + 6, z, chain=1)
    W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 2, z2 + 2)] = True


def silo(W):
    round_tower(W, -101, 20, G, 3, 13, B("smooth_stone"), floor=B("smooth_stone"), roof=B("iron_block"),
                roof_h=4, cap_block=B("lightning_rod"))
    a = W.a
    for k in range(1, 13, 3):
        a.set(-101, G + k, 16, B("iron_bars"))
    W.reserved[W.rect(-106, 15, -96, 25)] = True


def windmill(W, rng):
    a = W.a
    cx, cz = -168, -26
    round_tower(W, cx, cz, G, 3, 11, B("cobblestone"), floor=B("spruce_planks"), roof=B("spruce_planks"),
                roof_h=6, windows=[3, 7], door="east")
    a.set(cx + 3, G + 3, cz, B("glass_pane"))
    # sails on the east face
    hx, hy, hz = cx + 5, G + 10, cz
    a.set(cx + 4, hy, cz, B("spruce_log", axis="x"))
    a.set(hx, hy, hz, B("spruce_log", axis="x"))
    for k in range(1, 7):
        for (dy, dz) in ((k, 0), (-k, 0), (0, k), (0, -k)):
            a.set(hx, hy + dy, hz + dz, B("spruce_fence"))
            # cloth on one side of every arm
            if k > 1:
                if dz == 0:
                    a.set(hx, hy + dy, hz + (1 if dy > 0 else -1), B("white_wool"))
                else:
                    a.set(hx, hy + (-1 if dz > 0 else 1), hz + dz, B("white_wool"))
    # keep the sails above head height
    for y in range(G + 1, G + 4):
        for z in range(cz - 1, cz + 2):
            if a.get(hx, y, z) in (B("spruce_fence"), B("white_wool")):
                a.set(hx, y, z, AIR)
    W.reserved[W.rect(cx - 5, cz - 8, cx + 7, cz + 8)] = True


def pens(W, rng):
    a = W.a
    x1, z1, x2, z2 = -108, 0, -94, 12
    fence = B("spruce_fence")
    for x in range(x1, x2 + 1):
        a.set(x, G + 1, z1, fence); a.set(x, G + 1, z2, fence)
    for z in range(z1, z2 + 1):
        a.set(x1, G + 1, z, fence); a.set(x2, G + 1, z, fence)
    mid = (x1 + x2) // 2
    for z in range(z1, z2 + 1):
        a.set(mid, G + 1, z, fence)
    for gx in (x1 + 4, x2 - 4):
        a.set(gx, G + 1, z1, B("spruce_fence_gate", cardinal="north"))
    for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2), (mid, z1), (mid, z2)):
        a.set(x, G + 2, z, B("lantern"))
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            if x != mid:
                a.set(x, G, z, B("grass_block") if rng.random() < 0.7 else B("coarse_dirt"))
    a.set(x1 + 2, G + 1, z2 - 2, B("hay_block"))
    a.set(x2 - 2, G + 1, z2 - 2, B("hay_block"))
    a.set(x1 + 3, G + 1, z2 - 1, B("composter", composter_fill_level=4))
    stand_sign(a, mid, G + 1, z1 - 2, "north", "§l§6동물 우리\n§r소 · 양 | 돼지 · 닭")
    for e, (x, z) in (("cow", (x1 + 3, z1 + 5)), ("cow", (x1 + 5, z1 + 8)), ("sheep", (x1 + 4, z1 + 3)),
                      ("sheep", (x1 + 6, z1 + 6)), ("pig", (x2 - 3, z1 + 4)), ("pig", (x2 - 5, z1 + 7)),
                      ("chicken", (x2 - 3, z1 + 8)), ("chicken", (x2 - 6, z1 + 3)), ("chicken", (x2 - 2, z1 + 6))):
        W.animals.append((e, x, G + 1, z))
    # one marker under an animal in every chunk the animals stand in: the first-run summon waits
    # until all of those chunks are loaded
    seen = set()
    for (e, x, y, z) in W.animals:
        if (x >> 4, z >> 4) not in seen:
            seen.add((x >> 4, z >> 4))
            a.set(x, G - 1, z, B("lodestone"))
            W.markers.append((x, G - 1, z))
    W.reserved[W.rect(x1 - 1, z1 - 3, x2 + 1, z2 + 1)] = True


def market(W, rng):
    """Convenience space: farm market with a striped awning."""
    a = W.a
    x1, z1, x2, z2 = -112, -30, -98, -20
    house(W, x1, z1, x2, z2, G, h=4, post=B("oak_log"), wall=B("oak_planks"), floor=B("spruce_planks"),
          roof_stairs="spruce_stairs", roof_ridge=B("spruce_slab"), gable=B("oak_planks"), axis="x", lamp=False)
    for x in range(x1 + 1, x2):
        for y in range(G + 1, G + 4):
            a.set(x, y, z2, AIR)
    for x in (x1 + 5, x2 - 5):
        for y in range(G + 1, G + 4):
            a.set(x, y, z2, B("oak_log"))
    # awning
    for x in range(x1, x2 + 1):
        col = B("red_wool") if (x - x1) % 2 == 0 else B("white_wool")
        a.set(x, G + 4, z2 + 1, col)
        a.set(x, G + 3, z2 + 2, B("red_carpet") if (x - x1) % 2 == 0 else B("white_carpet"))
        a.set(x, G + 3, z2 + 2, AIR)
    for x in (x1, x2):
        for y in range(G + 1, G + 4):
            a.set(x, y, z2 + 1, B("oak_fence"))
    hang_sign(a, (x1 + x2) // 2, G + 3, z2 + 1, "south", "§l§a농장 직판장\n§r상점 · 엔더 상자", kind="oak_hanging_sign")
    rec = shop_kit(W, "farm", "농장 직판장", -105, G + 1, -24, "south", counter=B("oak_planks"))
    for (x, z) in ((-111, -29), (-110, -29), (-99, -29), (-100, -29)):
        a.set(x, G + 1, z, rng.choice([B("hay_block"), B("pumpkin", cardinal="south"), B("melon_block"),
                                       B("composter", composter_fill_level=8)]))
    for (x, z) in ((-108, -25), (-102, -25)):
        a.set(x, G + 1, z, B("barrel", facing_direction=1))
    hanging_lantern(a, -105, G + 4, -26, chain=0)
    hanging_lantern(a, -101, G + 4, -22, chain=0)
    wall_sign(a, x1 + 1, G + 2, -23, "east", "§l엔더 상자\n§r개인 보관함")
    W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 2, z2 + 3)] = True
    return rec


def field_hunt(W, rng):
    a = W.a
    x1, z1, x2, z2 = -176, 8, -152, 32

    def floor(x, z):
        return B("grass_block") if rng.random() < 0.75 else B("coarse_dirt")

    def wall(x, y, z):
        return B("oak_log") if (x * 7 + z) % 5 else B("stripped_oak_log")

    def props(box):
        for (x, z) in ((x1 + 6, z1 + 6), (x2 - 6, z2 - 7), (x1 + 12, z2 - 5)):
            a.set(x, G + 1, z, B("hay_block"))
        for (x, z) in ((x2 - 5, z1 + 5), (x1 + 5, z2 - 4)):
            a.set(x, G + 1, z, B("oak_fence")); a.set(x, G + 2, z, B("hay_block"))
            a.set(x, G + 3, z, B("carved_pumpkin", cardinal="north"))

    rec = hunting_ground(W, "farm", "들판 사냥터", x1, z1, x2, z2, G, floor, wall, gates=[("north", 14)],
                         wall_h=5, cap=B("oak_slab", half="top"), props=props, spawn_n=6)
    for x in range(x1 - 1, x2 + 2, 6):
        a.set(x, G + 6, z1 - 1, B("oak_fence")); a.set(x, G + 7, z1 - 1, B("lantern"))
    W.reserved[W.rect(x1 - 2, z1 - 6, x2 + 2, z2 + 2)] = True
    return rec


def pond(W, rng):
    a = W.a
    cx, cz = -138, 28
    # level the banks to the water line so you can climb out anywhere
    for x in range(cx - 10, cx + 11):
        for z in range(cz - 9, cz + 10):
            d = math.hypot((x - cx) / 6.5, (z - cz) / 5.0)
            if d < 1.6 and W.gy(x, z) > G and W.regions["farm"]["mask"][x - X0, z - Z0]:
                for y in range(G + 1, W.gy(x, z) + 1):
                    a.set(x, y, z, AIR)
                a.set(x, G, z, B("grass_block"))
                a.set(x, G - 1, z, B("dirt"))
    for x in range(cx - 7, cx + 8):
        for z in range(cz - 6, cz + 7):
            d = math.hypot((x - cx) / 6.5, (z - cz) / 5.0)
            if d < 1.0:
                depth = 2 if d < 0.55 else 1
                for k in range(depth):
                    a.set(x, G - k, z, B("water"))
                a.set(x, G - depth, z, B("sand") if d > 0.5 else B("clay"))
                if rng.random() < 0.08 and depth == 2:
                    a.set(x, G + 1, z, B("waterlily"))
            elif d < 1.25 and a.get(x, G, z) == B("grass_block") and rng.random() < 0.3:
                if a.get(x, G + 1, z) == AIR:
                    a.set(x, G + 1, z, B("reeds"))
                    a.set(x, G + 2, z, B("reeds"))
    W.reserved[W.rect(cx - 8, cz - 7, cx + 8, cz + 7)] = True


def roads(W, rng):
    blocks = [B("grass_path")] * 4 + [B("coarse_dirt"), B("gravel")]
    cells = set()
    for pts in (ROAD, SPUR_S, SPUR_HUNT, SPUR_N, [(-101, -6), (-101, -2)]):
        cells |= paint_path(W, pts, 2, blocks, rng)
    # pass road (stone path) with stair-smoothed steps
    pc = paint_path(W, PASS_FARM, 2, [B("cobblestone"), B("gravel"), B("grass_path")], rng)
    a = W.a
    for (x, z) in pc:
        y = W.gy(x, z)
        if a.get(x, y, z) in (B("grass_block"), B("dirt"), B("stone"), B("andesite")):
            a.set(x, y, z, rng.choice([B("cobblestone"), B("gravel"), B("grass_path")]))
    path_steps(W, pc, "cobblestone_stairs")
    for (x, z) in ((-100, -12), (-112, -4), (-126, -12), (-140, -2), (-152, -10)):
        lamp_post(a, x, W.gy(x, z) + 1, z, post=B("oak_fence"), lamp=B("lantern"), h=3)
    for (x, z) in ((-50, -9), (-58, -4), (-86, -14), (-92, -4)):
        lamp_post(a, x, W.gy(x, z) + 1, z, post=B("spruce_fence"), lamp=B("lantern"), h=3)


def nature(W, rng):
    a = W.a
    reg = W.regions["farm"]["mask"]
    cand = [tuple(c) for c in np.argwhere(reg & (W.din > 3) & (W.din < 14) & ~W.reserved)]
    rng.shuffle(cand)
    occ = []
    for (i, k) in cand:
        x, z = i + X0, k + Z0
        if any((x - ox) ** 2 + (z - oz) ** 2 < 64 for ox, oz in occ) or len(occ) > 40:
            continue
        y = W.gy(x, z)
        if a.get(x, y, z) != B("grass_block") or a.get(x, y + 1, z) != AIR:
            continue
        (oak_tree if rng.random() < 0.65 else birch_tree)(a, x, y + 1, z, rng)
        occ.append((x, z))
    for (i, k) in np.argwhere(reg & ~W.reserved):
        x, z = i + X0, k + Z0
        y = W.gy(x, z)
        if a.get(x, y, z) != B("grass_block") or a.get(x, y + 1, z) != AIR:
            continue
        r = rng.random()
        if r < 0.14:
            a.set(x, y + 1, z, B("short_grass"))
        elif r < 0.18:
            a.set(x, y + 1, z, B(rng.choice(["dandelion", "poppy", "cornflower", "oxeye_daisy", "azure_bluet"])))
    # pumpkin / melon patch and hay stacks
    for x in range(-146, -135):
        for z in range(6, 16):
            if rng.random() < 0.18 and a.get(x, G + 1, z) == AIR:
                a.set(x, G + 1, z, B("pumpkin", cardinal="south") if rng.random() < 0.5 else B("melon_block"))
    for (x, z) in ((-96, 0), (-150, 14), (-134, 0)):
        a.set(x, G + 1, z, B("hay_block")); a.set(x + 1, G + 1, z, B("hay_block")); a.set(x, G + 2, z, B("hay_block"))


def build(W):
    import random
    rng = random.Random(W.seed + 200)
    fields(W, rng)
    barn(W, rng)
    silo(W)
    windmill(W, rng)
    pens(W, rng)
    market(W, rng)
    field_hunt(W, rng)
    pond(W, rng)
    gatehouse(W, -71, -9, "west", 69, "yellow", wall=B("cobblestone"), pillar=B("oak_log"),
              roof_stairs="spruce_stairs", roof_ridge=B("spruce_slab"), floor=B("spruce_planks"),
              next_name="§a농장", prev_name="§f스폰 (뽑기장)", gable=B("oak_planks"))
    roads(W, rng)
    nature(W, rng)
    W.spawns["farm"] = (-104, G + 1, -14)
    W.mark_surface(W.regions["farm"]["mask"] | W.regions["pass_farm"]["mask"])
    W.light_boxes.append(("farm", -180, -54, -40, 38, G - 2, G + 14, 1, 8))
