"""Deep-sea temple (boss) under the bay, reached by a glass tunnel from the lighthouse islet.

tunnel (blue-glass bands) ─ E entrance hall ─┬ H sunken gallery = hunting ground (gated, north strip)
                                             ├ D divers' base = convenience space (south)
                                             └ A abyss shrine = boss arena (west): glass dome, central pool
Everything inside is dry; the tunnel and the temple are sealed against the ocean.
"""
import math

import numpy as np

from mcw import B, AIR, simple_be
from gen_common import stair, slab
from rpg_world import X0, Z0, SEA
from rpg_parts import (wall_sign, hang_sign, hanging_lantern, barrel, shop_kit, light_grid, ender_chest, tube,
                       DV, HUNT_LIGHT, leak_check)
from area_beach import TUBE_START

FY = 30                      # temple floor (top block), feet 31
X1, Z1, X2, Z2 = -148, 382, -96, 426
ROOF = 38                    # ceiling of the low rooms
A_ROOF = 40                  # flat roof of the boss room around the dome
PB, DP, PR = B("prismarine_bricks"), B("dark_prismarine"), B("prismarine")
SL = B("sea_lantern")
POOL = (-132, 412)


def shape(W):
    pass


def tunnel(W):
    sx, sz = TUBE_START
    wp = [(sx, sz, 64), (-62, sz, 58), (-62, 404, 40), (-96, 404, FY)]
    tube(W, wp, width=3, height=4, shell=B("glass"), floor=PB, accent=B("light_blue_stained_glass"),
         accent_every=3, ring=DP, ring_every=9, lamp=SL, lamp_every=6, stairs="prismarine_bricks_stairs",
         pillar=PR)
    a = W.a
    # invisible barrier on the part of the tunnel roof near the water line, so swimmers cannot
    # climb onto the roof and walk up to a high drop next to the islet
    wbar = B("barrier")
    shell_ids = (B("glass"), B("light_blue_stained_glass"), DP, PB)
    for x in range(-64, sx + 1):
        for z in range(sz - 2, sz + 3):
            top = None
            for y in range(72, 50, -1):
                if a.get(x, y, z) not in (AIR, B("water")):
                    top = y
                    break
            if top is not None and top >= SEA - 3 and a.get(x, top, z) in shell_ids:
                for k in (1, 2):
                    if a.get(x, top + k, z) in (AIR, B("water")):
                        a.set(x, top + k, z, wbar)
    # entrance pavilion on the islet
    for x in range(sx - 1, sx + 4):
        for z in range(sz - 3, sz + 4):
            edge = abs(z - sz) == 3 or x == sx + 3
            a.set(x, 64, z, PB)
            for y in range(65, 69):
                if edge and not (x == sx + 3 and abs(z - sz) <= 1 and y <= 67):
                    a.set(x, y, z, DP if abs(z - sz) == 3 and x in (sx - 1, sx + 3) else B("blue_stained_glass"))
                elif not edge:
                    a.set(x, y, z, AIR)
            a.set(x, 69, z, DP)
    a.set(sx + 4, 68, sz, DP)
    hang_sign(a, sx + 4, 67, sz, "east", "§l§9심해 신전\n§r보스 · 유리 터널", kind="birch_hanging_sign")
    wall_sign(a, sx + 2, 66, sz - 2, "south", "§l§9심해 신전 ↓\n§r바다 밑 유리 터널\n§7(보스 구역)")
    W.allow("deepsea_tube", -66, FY - 1, 346, sx + 5, 70, 408)


def temple_shell(W):
    a = W.a
    # platform down to the sea floor
    for x in range(X1 - 2, X2 + 3):
        for z in range(Z1 - 2, Z2 + 3):
            for y in range(20, FY + 1):
                a.set(x, y, z, DP if y < FY else PB)
    # outer and inner walls of the low part
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            outer = x in (X1, X2) or z in (Z1, Z2)
            inner = (z in (395, 396) and x < X2) or (x in (-112, -111) and z > 396) or (z in (411, 412) and x > -112)
            top = A_ROOF if (x <= -111 and z >= 395) else ROOF
            for y in range(FY + 1, top + 1):
                if outer or inner:
                    band = y in (FY + 1, ROOF, top)
                    col = (outer and ((x - X1) % 6 == 0 or (z - Z1) % 6 == 0))
                    a.set(x, y, z, DP if (band or col) else PB)
                elif y == top:
                    a.set(x, y, z, PB)
                else:
                    a.set(x, y, z, AIR)
            a.set(x, top + 1, z, DP if outer else PR)
    # ceiling lights of the low rooms
    for x in range(X1 + 3, X2 - 1, 5):
        for z in range(Z1 + 3, Z2 - 1, 5):
            if a.get(x, ROOF, z) == PB and not (x < -112 and z > 396):
                a.set(x, ROOF, z, SL)
    # windows to the deep sea (glass blocks keep the water out)
    for z in range(Z1 + 2, Z2 - 1):
        if (z - Z1) % 6 in (2, 3, 4):
            for y in range(FY + 3, FY + 7):
                a.set(X1, y, z, B("glass"))
    for x in range(X1 + 2, X2 - 1):
        if (x - X1) % 6 in (2, 3, 4):
            for y in range(FY + 3, FY + 6):
                a.set(x, y, Z1, B("glass"))
                if x <= -113:
                    a.set(x, y, Z2, B("glass"))
    # glass dome over the boss room
    cx, cz = POOL[0] + 2, POOL[1] - 1
    rx, rz, ry = 15, 12, 8
    for x in range(cx - rx - 2, cx + rx + 3):
        for z in range(cz - rz - 2, cz + rz + 3):
            for y in range(A_ROOF - 1, A_ROOF + ry + 3):
                dy = y - (A_ROOF - 1)
                din = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2 + (dy / ry) ** 2
                dout = ((x - cx) / (rx + 1.2)) ** 2 + ((z - cz) / (rz + 1.2)) ** 2 + (dy / (ry + 1.2)) ** 2
                if din <= 1.0:
                    a.set(x, y, z, AIR)
                elif dout <= 1.0:
                    rib = (x - cx) % 5 == 0 or (z - cz) % 5 == 0
                    a.set(x, y, z, DP if rib else (B("glass") if (x + z) % 7 else B("cyan_stained_glass")))
    a.set(cx, A_ROOF + ry + 1, cz, SL)


def entrance(W):
    a = W.a
    for z in range(403, 406):
        for y in range(FY + 1, FY + 5):
            a.set(X2, y, z, AIR)
    for x in range(-109, -97):
        for z in range(398, 410):
            if (x + z) % 4 == 0:
                a.set(x, FY, z, SL)
    for z in (400, 408):
        for y in range(FY + 1, ROOF):
            a.set(-103, y, z, DP)
    wall_sign(a, -97, FY + 3, 401, "west", "§l§9심해 신전\n§r서쪽: 심연의 제단 (보스)\n§7북: 사냥터 · 남: 기지")
    # E -> A big doorway
    for z in range(401, 407):
        for y in range(FY + 1, FY + 6):
            for x in (-112, -111):
                a.set(x, y, z, AIR)
    for z in (400, 407):
        for y in range(FY + 1, FY + 7):
            a.set(-110, y, z, DP)
    wall_sign(a, -110, FY + 6, 403, "east", "§l§4⚠ 보스 ⚠\n§r심연의 제단") if False else None
    for x in (-111, -112):
        a.set(x, FY + 6, 403, DP)
    wall_sign(a, -110, FY + 6, 404, "east", "§l§4⚠ 보스 ⚠\n§r심연의 제단")
    # E -> D doorway
    for x in range(-106, -101):
        for z in (411, 412):
            for y in range(FY + 1, FY + 5):
                a.set(x, y, z, AIR)
    # E -> H: two fence gates in the double wall
    for x in (-105, -104):
        for z in (395, 396):
            a.set(x, FY + 1, z, B("warped_fence_gate", cardinal="north"))
            a.set(x, FY + 2, z, AIR)
    wall_sign(a, -103, FY + 3, 397, "south", "§l§c⚔ 사냥터 ⚔\n§r가라앉은 회랑")


def hunt_gallery(W, rng):
    a = W.a
    x1, z1, x2, z2 = X1 + 1, Z1 + 1, X2 - 1, 394
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            r = rng.random()
            a.set(x, FY, z, B("sand") if r < 0.25 else (B("gravel") if r < 0.32 else PB))
    for x in range(x1 + 5, x2 - 3, 8):
        for z in (z1 + 3, z2 - 3):
            for y in range(FY + 1, ROOF):
                a.set(x, y, z, DP if y % 3 else SL)
    # wreck debris and dead coral as cover
    for t in range(6):
        a.set(x1 + 14 + t, FY + 1, z1 + 6, B("spruce_planks") if t % 2 else B("dark_oak_planks"))
    a.set(x1 + 15, FY + 2, z1 + 6, B("spruce_planks"))
    for (x, z) in ((x1 + 30, z1 + 4), (x1 + 31, z1 + 4), (x1 + 38, z2 - 4), (x1 + 6, z2 - 2)):
        a.set(x, FY + 1, z, rng.choice([B("dead_tube_coral_block"), B("dead_brain_coral_block"),
                                        B("dead_horn_coral_block")]))
    lights = []
    for x in range(x1 + 2, x2 + 1, 5):
        for z in range(z1 + 2, z2 + 1, 5):
            if a.get(x, FY + 5, z) == AIR:
                a.set(x, FY + 5, z, B("light_block_%d" % HUNT_LIGHT))
                lights.append((x, FY + 5, z))
    pts = [(x, FY + 1, z) for x in (x1 + 8, x1 + 20, x1 + 34, x1 + 44) for z in (z1 + 5, z2 - 5)]
    pts = [p for p in pts if a.get(*p) == AIR][:8]
    W.hunts.append(dict(region="deepsea", name="가라앉은 회랑", box=(x1, FY + 1, z1, x2, ROOF - 1, z2), floor_y=FY,
                        entrances=[(-105, FY + 1, 397)], spawn_points=pts, lights=lights, roofed=True))


def divers_base(W, rng):
    a = W.a
    wall_sign(a, -104, FY + 5, 410, "north", "§l§b잠수부 기지 ↓\n§r상점 · 엔더 상자", kind="birch_wall_sign")
    rec = shop_kit(W, "deepsea", "잠수부 기지", -104, FY + 1, 420, "north", counter=DP)
    for x in (-108, -100):
        a.set(x, FY + 1, 420, B("barrel", facing_direction=1))
    # aquarium tanks
    for (x, z) in ((-109, 415), (-98, 415)):
        for y in range(FY + 1, FY + 5):
            a.set(x, y, z, B("glass"))
    tx, tz = -108, 423
    for y in range(FY + 1, FY + 5):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dz == 0 and y < FY + 4:
                    a.set(tx, y, tz, B("water"))
                else:
                    a.set(tx + dx, y, tz + dz, B("glass"))
    a.setw(tx, FY + 1, tz, B("sea_pickle", cluster_count=3))
    a.set(-99, FY + 1, 424, B("crafting_table"))
    a.set(-100, FY + 1, 424, B("cartography_table"))
    wall_sign(a, -97, FY + 2, 417, "west", "§l잠수부 기지\n§r보스전 전에\n엔더 상자를 쓰세요")
    return rec


def boss_shrine(W, rng):
    a = W.a
    x1, z1, x2, z2 = X1 + 1, 397, -113, Z2 - 1
    px, pz = POOL
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            d = max(abs(x - px), abs(z - pz))
            if d <= 5:
                for y in range(FY - 3, FY + 1):
                    a.set(x, y, z, B("water"))
                a.set(x, FY - 4, z, DP)
            elif d == 6:
                a.set(x, FY, z, SL if (x + z) % 3 == 0 else DP)
            else:
                a.set(x, FY, z, PB if (x // 3 + z // 3) % 2 else PR)
    # pillars around the pool
    for ang in range(0, 360, 45):
        x = int(round(px + 2 + math.cos(math.radians(ang)) * 11))
        z = int(round(pz - 1 + math.sin(math.radians(ang)) * 9.5))
        if x1 + 1 <= x <= x2 - 1 and z1 + 1 <= z <= z2 - 1:
            for y in range(FY + 1, A_ROOF):
                a.set(x, y, z, SL if y in (FY + 4, FY + 8) else DP)
    # altar with a conduit at the west end
    for x in range(x1, x1 + 4):
        for z in range(pz - 3, pz + 4):
            a.set(x, FY + 1, z, DP)
    for z in range(pz - 3, pz + 4):
        a.set(x1 + 4, FY + 1, z, stair("dark_prismarine_stairs", "west"))
    a.set(x1 + 1, FY + 2, pz, B("gold_block"))
    a.set(x1 + 1, FY + 3, pz, B("conduit"))
    a.add_be(simple_be("Conduit", x1 + 1, FY + 3, pz, Active=__import__("amulet_nbt").ByteTag(0)))
    for dz in (-2, 2):
        a.set(x1 + 1, FY + 2, pz + dz, PR)
        a.set(x1 + 1, FY + 3, pz + dz, SL)
    # kelp tanks in the corners
    for (x, z) in ((x1 + 1, z1 + 1), (x2 - 1, z1 + 1), (x1 + 1, z2 - 1), (x2 - 1, z2 - 1)):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for y in range(FY + 1, FY + 6):
                    if dx == 0 and dz == 0 and y < FY + 5:
                        a.set(x, y, z, B("water"))
                        a.setw(x, y, z, B("kelp", kelp_age=10)) if y < FY + 4 else None
                    else:
                        if x1 <= x + dx <= x2 and z1 <= z + dz <= z2:
                            a.set(x + dx, y, z + dz, B("glass"))
    lights = light_grid(W, x1, z1, x2, z2, FY + 6, level=10, spacing=5)
    W.bosses.append(dict(region="deepsea", name="심연의 제단", boss_spawn=(px, FY - 1, pz),
                         boss_spawn_floor=(px + 9, FY + 1, pz), box=(x1, FY + 1, z1, x2, A_ROOF + 8, z2),
                         entrance=(-110, FY + 1, 404)))
    a.set(px + 9, FY - 1, pz, B("lodestone"))


def build(W):
    import random
    rng = random.Random(W.seed + 700)
    temple_shell(W)
    tunnel(W)
    entrance(W)
    hunt_gallery(W, rng)
    rec = divers_base(W, rng)
    boss_shrine(W, rng)
    W.spawns["deepsea"] = (-100, FY + 1, 404)
    W.allow("deepsea_temple", X1 - 1, FY - 6, Z1 - 1, X2 + 1, A_ROOF + 10, Z2 + 1)
    W.light_boxes.append(("deepsea", X1, Z1, X2, Z2, FY - 4, A_ROOF + 8, 6, 10))
    leaks = leak_check(W, (X1 - 70, 15, Z1 - 60, X2 + 60, SEA, Z2 + 4))
    print("  deepsea leaks:", len(leaks), leaks[:10])
