"""Beginner dungeon: a compact cave inside the ridge between spawn and the village.

spawn ─ entrance arch ─ amber-window gallery above the main cavern ─ stair tunnel ─ cavern
cavern: miner's rest (convenience), pond, mine track, amethyst nook, west tunnel to the cave hunting chamber
cavern south ─ rising tunnel ─ lime-window gallery in the village cliff ─ village
"""
import math

import numpy as np

from mcw import B, AIR
from gen_common import stair, slab, clamp_gradient
from rpg_world import G, X0, Z0
from rpg_parts import (wall_sign, hang_sign, stand_sign, lamp_post, hanging_lantern, barrel, shop_kit, corridor,
                       run_cells, light_grid, ender_chest, DV, HUNT_LIGHT, chest, campfire)
from rpg_build import house
from rpg_carve import chamber, tunnel, decorate, box_carve

CF = 52                       # cavern floor (top block)
CAV = (4, 92, 30, 26)         # centre x, z, rx, rz
HUNT = (-44, 104, 12, 12)
GAL_Y = 64                    # entrance gallery floor
EXIT_Y = 66                   # village-side gallery floor


def shape(W):
    # open a little forecourt in front of the entrance arch and a terrace in front of the exit gallery
    W.H[W.rect(-5, 40, 5, 49)] = np.minimum(W.H[W.rect(-5, 40, 5, 49)], G)
    sl = W.rect(-4, 162, 30, 171)
    W.H[sl] = EXIT_Y
    W.extra_surface = getattr(W, "extra_surface", [])
    W.extra_surface += [W.rect(-5, 40, 5, 49), sl]


def stone_floor(rng):
    tab = [B("stone")] * 5 + [B("andesite")] * 3 + [B("gravel")] * 2 + [B("tuff")] * 2 + [B("coarse_dirt")]
    return lambda x, z: rng.choice(tab)


def entrance(W, rng):
    a = W.a
    sb, msb, csb = B("stone_bricks"), B("mossy_stone_bricks"), B("cracked_stone_bricks")

    def wallf():
        return rng.choice([sb, sb, sb, msb, csb])

    # arch on the cliff face
    for x in range(-5, 6):
        for y in range(G, G + 9):
            if abs(x) <= 2 and y <= G + 5:
                continue
            if abs(x) == 5 or y >= G + 6 or abs(x) >= 3:
                a.set(x, y, 49, wallf())
    for x in range(-6, 7):
        a.set(x, G + 9, 49, B("stone_brick_slab"))
    hang_sign(a, 0, G + 5, 48, "south", "§l§6초급 던전\n§r동굴", kind="spruce_hanging_sign")
    a.set(0, G + 6, 48, sb)
    for x in (-4, 4):
        a.set(x, G + 1, 47, B("stone_brick_wall"))
        a.set(x, G + 2, 47, B("stone_brick_wall"))
        a.set(x, G + 3, 47, B("lantern"))
    # corridor into the mountain, then east along the cavern's north wall (windows face the cavern)
    cells = run_cells(0, 49, "south", 14) + run_cells(0, 63, "east", 44)
    corridor(W, cells, GAL_Y, width=5, height=5, wall=sb, floor=B("polished_andesite"), roof=sb,
             window=B("orange_stained_glass_pane"), window_side="right", window_every=4, window_rows=(2, 3, 4),
             pillar=B("spruce_log"), lamp=B("lantern", hanging=1), lamp_every=6)
    # keep the windows only where they look into the cavern
    pane = B("orange_stained_glass_pane")
    for x in range(-4, 46):
        for z in range(46, 68):
            for y in range(GAL_Y + 1, GAL_Y + 6):
                if a.get(x, y, z) == pane and not (z == 66 and -6 <= x <= 32):
                    a.set(x, y, z, sb)
    wall_sign(a, 1, GAL_Y + 3, 61, "south", "§l§6초급 던전 · 동굴\n§r창밖이 동굴입니다\n§7→ 계단으로 내려가기")
    # stair tunnel down to the cavern floor (inside the rock east of the cavern)
    cells2 = run_cells(41, 66, "south", 20)
    fys = [GAL_Y] * 2 + [max(CF, GAL_Y - (i - 1)) for i in range(2, 20)]
    corridor(W, cells2, fys, width=5, height=5, wall=sb, floor=B("polished_andesite"), roof=sb,
             lamp=B("lantern", hanging=1), lamp_every=5)
    for i in range(1, len(cells2)):
        if fys[i] < fys[i - 1]:
            x, z = cells2[i]
            for w in range(-2, 3):
                a.set(x + w, fys[i] + 1, z, stair("stone_brick_stairs", "north"))
    # opening west into the cavern at floor level
    cells3 = run_cells(38, 83, "west", 7)
    corridor(W, cells3, CF, width=5, height=5, wall=sb, floor=B("polished_andesite"), roof=sb)
    for (x, z) in cells3[-2:]:
        for w in range(-2, 3):
            for y in range(CF + 1, CF + 6):
                a.set(x, y, z + w, AIR)


def cavern(W, rng):
    a = W.a
    cx, cz, rx, rz = CAV
    ch = chamber(W, cx, cz, rx, rz, CF, 22, W.seed + 300, p=3.0, floor_noise=0.6, floor_block=stone_floor(rng))
    # tall slot in front of the gallery windows
    box_carve(W, -6, CF + 1, 67, 33, 74, 70)
    for x in range(-6, 34):
        for z in range(67, 71):
            a.set(x, CF, z, stone_floor(rng)(x, z))
    W.cave_ch = ch
    return ch


def pond(W, rng):
    a = W.a
    cx, cz = -12, 98
    for x in range(cx - 8, cx + 9):
        for z in range(cz - 6, cz + 7):
            d = math.hypot((x - cx) / 7.5, (z - cz) / 5.5)
            if d < 1:
                dep = 2 if d < 0.6 else 1
                for k in range(dep):
                    a.set(x, CF - k, z, B("water"))
                a.set(x, CF - dep, z, B("clay"))
                if dep == 2 and rng.random() < 0.25:
                    a.setw(x, CF - 1, z, B("seagrass"))
            elif d < 1.3 and a.get(x, CF + 1, z) == AIR and a.get(x, CF, z) != AIR:
                a.set(x, CF, z, B("moss_block"))
                if rng.random() < 0.25:
                    a.set(x, CF + 1, z, B("moss_carpet"))
    W.reserved[W.rect(cx - 9, cz - 7, cx + 9, cz + 7)] = True


def miners_rest(W, rng):
    """Convenience space: a log cabin with a lantern-lit porch near the cavern entrance."""
    a = W.a
    x1, z1, x2, z2 = 14, 82, 26, 94
    for x in range(x1 - 2, x2 + 3):
        for z in range(z1 - 2, z2 + 3):
            a.set(x, CF, z, B("spruce_planks") if x1 <= x <= x2 and z1 <= z <= z2 else B("gravel"))
            for y in range(CF + 1, CF + 12):
                if a.get(x, y, z) != AIR and y < CF + 10:
                    a.set(x, y, z, AIR)
    house(W, x1, z1, x2, z2, CF, h=4, post=B("spruce_log"), wall=B("spruce_planks"), floor=B("spruce_planks"),
          roof_stairs="spruce_stairs", roof_ridge=B("spruce_slab"), gable=B("spruce_planks"), axis="z",
          lamp=False, base=B("cobblestone"))
    for z in range(z1 + 1, z2):
        for y in range(CF + 1, CF + 4):
            a.set(x2, y, z, AIR)
    for z in (z1 + 4, z1 + 8):
        for y in range(CF + 1, CF + 5):
            a.set(x2, y, z, B("spruce_log"))
    hang_sign(a, x2 + 1, CF + 4, 88, "east", "§l§6광부의 쉼터\n§r상점 · 엔더 상자")
    rec = shop_kit(W, "cave", "광부의 쉼터", 21, CF + 1, 87, "east", counter=B("spruce_planks"))
    for z in (85, 89):
        a.set(21, CF + 1, z, B("barrel", facing_direction=1))
    a.set(16, CF + 1, 84, B("furnace", cardinal="east"))
    a.set(16, CF + 1, 85, B("crafting_table"))
    a.set(16, CF + 1, 90, B("barrel", facing_direction=1))
    a.set(16, CF + 2, 90, B("barrel", facing_direction=1))
    for (x, z) in ((18, 85), (18, 91), (23, 88)):
        hanging_lantern(a, x, CF + 4, z, chain=0)
    # porch: campfire ring, benches, mine cart track end
    campfire(a, 30, CF + 1, 92)
    for (x, z, d) in ((29, 94, "north"), (31, 94, "north"), (32, 92, "west"), (28, 92, "east")):
        a.set(x, CF + 1, z, stair("spruce_stairs", {"north": "south", "west": "east", "east": "west"}[d]))
    wall_sign(a, 24, CF + 2, 93, "north", "§l엔더 상자\n§r오른쪽 →")
    W.reserved[W.rect(x1 - 3, z1 - 3, x2 + 8, z2 + 3)] = True
    return rec


def hunt_chamber(W, rng):
    a = W.a
    cx, cz, rx, rz = HUNT
    ch = chamber(W, cx, cz, rx, rz, CF, 10, W.seed + 310, p=2.6, floor_noise=0, wall_noise=0.12, ceil_min=6,
                 floor_block=lambda x, z: rng.choice([B("stone"), B("andesite"), B("gravel"), B("tuff")]), flat=True)
    # connecting tunnel with a two-gate airlock (mobs cannot open fence gates)
    tunnel(W, [(-34, CF, 104), (-24, CF, 104)], width=3, height=4, floor_block=B("gravel"))
    for z in range(102, 107):
        for x in range(-34, -23):
            if z in (102, 106):
                for y in range(CF + 1, CF + 5):
                    a.set(x, y, z, B("spruce_planks") if x % 3 else B("spruce_log"))
            else:
                a.set(x, CF + 4, z, B("spruce_planks"))
                for y in range(CF + 1, CF + 4):
                    a.set(x, y, z, AIR)
    for gx in (-32, -26):
        for z in (103, 104, 105):
            a.set(gx, CF + 1, z, B("spruce_fence_gate", cardinal="east"))
            a.set(gx, CF + 2, z, AIR)
            a.set(gx, CF + 3, z, B("spruce_planks"))
    wall_sign(a, -25, CF + 3, 103, "east", "§l§c⚔ 사냥터 ⚔\n§r동굴 사냥터")
    wall_sign(a, -25, CF + 3, 105, "east", "§l§c⚔ 사냥터 ⚔\n§r동굴 사냥터")
    hanging_lantern(a, -29, CF + 3, 104, chain=0)
    # spawn points on the flat floor, light grid (toggle level)
    pts = []
    for (dx, dz) in ((-6, -5), (0, -6), (6, -4), (-6, 4), (1, 6), (6, 3), (0, 0)):
        pts.append((cx + dx, CF + 1, cz + dz))
    lights = []
    for x in range(cx - rx + 2, cx + rx - 1, 5):
        for z in range(cz - rz + 2, cz + rz - 1, 5):
            if a.get(x, CF + 5, z) == AIR and a.get(x, CF + 1, z) == AIR:
                a.set(x, CF + 5, z, B("light_block_%d" % HUNT_LIGHT))
                lights.append((x, CF + 5, z))
    # a few boulders for cover
    for (dx, dz) in ((-3, 2), (4, -1)):
        a.set(cx + dx, CF + 1, cz + dz, B("cobblestone"))
        a.set(cx + dx + 1, CF + 1, cz + dz, B("mossy_cobblestone"))
    W.hunts.append(dict(region="cave", name="동굴 사냥터", box=(cx - rx, CF + 1, cz - rz, cx + rx, CF + 10, cz + rz),
                        floor_y=CF, entrances=[(-23, CF + 1, 104)], spawn_points=pts, lights=lights, roofed=True))
    W.reserved[W.rect(cx - rx - 2, cz - rz - 2, -22, cz + rz + 2)] = True


def amethyst_nook(W, rng):
    a = W.a
    ch = chamber(W, -22, 76, 6, 5, CF + 1, 6, W.seed + 320, p=2.0, floor_noise=0, flat=True,
                 floor_block=B("calcite"))
    for x in range(-30, -13):
        for z in range(69, 84):
            for y in range(CF + 1, CF + 9):
                if a.get(x, y, z) in (B("stone"), B("andesite"), B("tuff"), B("deepslate")):
                    near_air = any(a.get(x + dx, y + dy, z + dz) == AIR for dx, dy, dz in
                                   ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))
                    if near_air:
                        a.set(x, y, z, B("amethyst_block") if rng.random() < 0.7 else B("budding_amethyst"))
                        if a.get(x, y - 1, z) == AIR and rng.random() < 0.15:
                            a.set(x, y - 1, z, B("amethyst_cluster", face="down"))
    for (x, z) in ((-24, 75), (-20, 77), (-22, 78)):
        if a.get(x, CF + 2, z) == AIR:
            a.set(x, CF + 2, z, B("amethyst_cluster", face="up"))


def mine_track(W, rng):
    """Decorative rails from the miner's rest toward the exit tunnel, with timber frames."""
    a = W.a
    pts = [(12, 96), (8, 104), (6, 112), (5, 117)]
    from gen_common import line_points
    last = None
    for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
        for (x, _, z) in line_points((ax, 0, az), (bx, 0, bz), 0.4):
            x2 = x + 3
            y = W.cave_floor(x2, z)
            if y is None:
                continue
            if a.get(x2, y + 1, z) == AIR and a.get(x2, y, z) != AIR:
                a.set(x2, y + 1, z, B("rail", rail_direction=0))


def exit_route(W, rng):
    a = W.a
    sb = B("stone_bricks")
    # rising tunnel from the cavern's south side to the village cliff
    pts = [(4, CF, 115), (4, CF, 122), (4, EXIT_Y, 150), (4, EXIT_Y, 156)]
    tunnel(W, pts, width=5, height=5, floor_block=lambda x, z: rng.choice([B("gravel"), B("stone"), B("andesite")]))
    # stair-smooth the climb
    for z in range(122, 151):
        fy = int(round(CF + (EXIT_Y - CF) * (z - 122) / 28))
        for x in range(2, 7):
            for y in range(fy + 1, fy + 6):
                a.set(x, y, z, AIR)
            a.set(x, fy, z, B("stone_bricks") if x in (2, 6) else B("polished_andesite"))
            nxt = int(round(CF + (EXIT_Y - CF) * (z + 1 - 122) / 28))
            if nxt > fy and 3 <= x <= 5:
                a.set(x, fy + 1, z, stair("stone_brick_stairs", "south"))
    for z in range(124, 152, 6):
        fy = int(round(CF + (EXIT_Y - CF) * (z - 122) / 28))
        for y in range(fy + 1, fy + 5):
            a.set(1, y, z, B("spruce_log")); a.set(7, y, z, B("spruce_log"))
        for x in range(1, 8):
            a.set(x, fy + 5, z, B("spruce_planks"))
        hanging_lantern(a, 4, fy + 4, z, chain=0)
    # gallery along the cliff with lime windows toward the village, exit at its east end
    cells = run_cells(4, 158, "east", 23)
    corridor(W, cells, EXIT_Y, width=5, height=5, wall=sb, floor=B("polished_andesite"), roof=sb,
             window=B("lime_stained_glass_pane"), window_side="right", window_every=4, window_rows=(2, 3, 4),
             pillar=B("spruce_log"), lamp=B("lantern", hanging=1), lamp_every=6)
    pane = B("lime_stained_glass_pane")
    for x in range(0, 30):
        for y in range(EXIT_Y + 1, EXIT_Y + 6):
            if a.get(x, y, 155) == pane:
                a.set(x, y, 155, sb)
    cells2 = run_cells(24, 161, "south", 5)
    corridor(W, cells2, EXIT_Y, width=5, height=5, wall=sb, floor=B("polished_andesite"), roof=sb)
    for x in range(22, 27):
        for y in range(EXIT_Y + 1, EXIT_Y + 6):
            a.set(x, y, 165, AIR)
    for x in range(21, 28):
        for y in range(EXIT_Y + 1, EXIT_Y + 7):
            if x in (21, 27) or y == EXIT_Y + 6:
                a.set(x, y, 165, sb)
    a.set(24, EXIT_Y + 6, 166, sb)
    hang_sign(a, 24, EXIT_Y + 5, 166, "south", "§l§6초급 던전\n§r동굴 (스폰 방향)", kind="spruce_hanging_sign")
    wall_sign(a, 6, EXIT_Y + 3, 156, "south", "§l§a다음 지역\n§r점령된 마을\n§7창밖을 보세요")
    for x in (20, 28):
        a.set(x, EXIT_Y + 1, 167, B("stone_brick_wall")); a.set(x, EXIT_Y + 2, 167, B("lantern"))


def lights(W, rng):
    """Lanterns on posts along the walk; the rest of the cave gets soft invisible light."""
    a = W.a
    for (x, z) in ((30, 80), (20, 100), (6, 110), (-4, 88), (-14, 108), (12, 74), (-20, 92)):
        y = W.cave_floor(x, z)
        if y is not None and a.get(x, y + 1, z) == AIR:
            lamp_post(a, x, y + 1, z, post=B("spruce_fence"), lamp=B("lantern"), h=2)


def build(W):
    import random
    rng = random.Random(W.seed + 300)
    ch = cavern(W, rng)

    def cave_floor(x, z):
        X1, Z1, X2, Z2 = ch["box"]
        if X1 <= x <= X2 and Z1 <= z <= Z2:
            i, k = x - X1, z - Z1
            if ch["inside"][i, k]:
                return int(ch["floor"][i, k])
        return None
    W.cave_floor = cave_floor
    entrance(W, rng)
    pond(W, rng)
    amethyst_nook(W, rng)
    hunt_chamber(W, rng)
    exit_route(W, rng)
    miners_rest(W, rng)
    mine_track(W, rng)
    keep = lambda x, y, z: W.reserved[x - X0, z - Z0]
    decorate(W, (-60, 60, 48, 125), CF - 2, 76, rng, ore_p=0.05, drip_p=0.03, mite_p=0.004, lichen_p=0.015,
             vine_p=0.006, keep=keep)
    lights(W, rng)
    W.spawns["cave"] = (30, CF + 1, 82)
    W.allow("cave", -60, CF - 3, 44, 50, 80, 170)
    W.light_boxes.append(("cave", -60, 44, 50, 168, CF - 2, 76, 2, 9))
