"""Great underground prison under the demon king's castle (boss).

keep great hall ─ stairwell (tube) ─ watch gallery descending along the prison hall with red windows
─ warden's post = convenience (gated side door to the cell block = hunting ground) ─ boss gate ─
judgement hall = boss arena (37 x 37, 22 high, cell tiers, hanging cage)
"""
import math

from mcw import B, AIR, simple_be
from gen_common import stair, slab
from rpg_world import X0, Z0
from rpg_parts import (wall_sign, hang_sign, hanging_lantern, barrel, shop_kit, light_grid, tube, campfire,
                       DV, HUNT_LIGHT)
from area_castle import PT

FL = 24                       # prison floor (top block), feet 25
HX1, HZ1, HX2, HZ2 = 176, 500, 212, 536        # hall interior
H_TOP = 47
AX1, AZ1, AX2, AZ2 = 162, 512, 172, 528        # antechamber interior
CX1, CZ1, CX2, CZ2 = 140, 504, 159, 532        # cell block interior
PBB, PB, DT = B("polished_blackstone_bricks"), B("polished_blackstone"), B("deepslate_tiles")
DB = B("deepslate_bricks")


def shape(W):
    pass


def room(W, x1, z1, x2, z2, y_floor, y_ceil, wall, floor, thick=1):
    a = W.a
    for x in range(x1 - thick, x2 + thick + 1):
        for z in range(z1 - thick, z2 + thick + 1):
            inside = x1 <= x <= x2 and z1 <= z <= z2
            for y in range(y_floor - 2, y_ceil + 2):
                if inside and y_floor < y <= y_ceil:
                    a.set(x, y, z, AIR)
                elif inside and y == y_floor:
                    a.set(x, y, z, floor(x, z) if callable(floor) else floor)
                else:
                    a.set(x, y, z, wall(x, y, z) if callable(wall) else wall)


def hall(W, rng):
    a = W.a

    def wall(x, y, z):
        return DT if (y - FL) % 6 == 0 else (B("cracked_deepslate_bricks") if rng.random() < 0.12 else DB)

    def floor(x, z):
        d = math.hypot(x - 194, z - 518)
        if 9.5 <= d <= 10.5:
            return B("crying_obsidian") if (x + z) % 3 == 0 else B("polished_blackstone")
        if d < 2:
            return B("chiseled_polished_blackstone")
        return PB if (x // 3 + z // 3) % 2 else DT

    room(W, HX1, HZ1, HX2, HZ2, FL, H_TOP - 1, wall, floor, thick=2)
    # cell tiers along the east and west walls (decorative, barred)
    for (xs, front, inward) in (((HX1, HX1 + 1, HX1 + 2), HX1 + 2, 1), ((HX2, HX2 - 1, HX2 - 2), HX2 - 2, -1)):
        for tier_y in (FL, FL + 9):
            for z in range(HZ1 + 2, HZ2 - 1):
                cell = (z - HZ1 - 2) % 5
                if inward > 0 and tier_y == FL and 513 <= z <= 523:
                    for x in xs:
                        for y in range(tier_y + 1, tier_y + 7):
                            a.set(x, y, z, AIR)
                    continue
                for x in xs:
                    for y in range(tier_y + 1, tier_y + 5):
                        if cell == 0:
                            a.set(x, y, z, DB)
                        elif x == front:
                            a.set(x, y, z, B("iron_bars"))
                        else:
                            a.set(x, y, z, AIR)
                    a.set(x, tier_y, z, DB)
                    a.set(x, tier_y + 5, z, DT)
                if cell == 2:
                    a.set(xs[0], tier_y + 1, z, B("skeleton_skull", facing_direction=1))
                    a.add_be(simple_be("Skull", xs[0], tier_y + 1, z,
                                       Rotation=__import__("amulet_nbt").FloatTag(90.0 if inward > 0 else 270.0),
                                       SkullType=__import__("amulet_nbt").ByteTag(0)))
                    a.set(xs[0], tier_y + 4, z, B("chain"))
            # ledge in front of the upper tier
            if tier_y > FL:
                for z in range(HZ1 + 2, HZ2 - 1):
                    a.set(front + inward, tier_y, z, B("polished_blackstone_slab", half="top"))
    # four great pillars with chains
    for (px, pz) in ((184, 508), (204, 508), (184, 528), (204, 528)):
        for x in range(px - 1, px + 2):
            for z in range(pz - 1, pz + 2):
                for y in range(FL + 1, H_TOP):
                    a.set(x, y, z, DT if (y - FL) % 6 == 0 else PBB)
        for (dx, dz) in ((0, -2), (0, 2), (-2, 0), (2, 0)):
            a.set(px + dx, FL + 7, pz + dz, PBB)
            a.set(px + dx, FL + 6, pz + dz, B("soul_lantern", hanging=1))
    # hanging cage of the demon king above the centre
    cx, cz = 194, 518
    for k in range(H_TOP - 1, H_TOP - 6, -1):
        a.set(cx, k, cz, B("chain"))
    for x in range(cx - 2, cx + 3):
        for z in range(cz - 2, cz + 3):
            edge = abs(x - cx) == 2 or abs(z - cz) == 2
            for y in range(H_TOP - 11, H_TOP - 5):
                if y in (H_TOP - 11, H_TOP - 6):
                    a.set(x, y, z, PBB)
                elif edge:
                    a.set(x, y, z, B("iron_bars"))
    a.set(cx, H_TOP - 10, cz, B("wither_skeleton_skull", facing_direction=1))
    a.add_be(simple_be("Skull", cx, H_TOP - 10, cz, Rotation=__import__("amulet_nbt").FloatTag(180.0),
                       SkullType=__import__("amulet_nbt").ByteTag(1)))
    # long chains from the ceiling
    for (x, z) in ((180, 504), (208, 504), (180, 532), (208, 532), (194, 504), (194, 532), (190, 518), (198, 518)):
        ln = 6 + (x + z) % 5
        for k in range(1, ln + 1):
            a.set(x, H_TOP - k, z, B("chain"))
        a.set(x, H_TOP - ln - 1, z, B("soul_lantern", hanging=1))
    # braziers
    for (x, z) in ((180, 518), (208, 518), (194, 503), (194, 533)):
        a.set(x, FL + 1, z, PBB)
        campfire(a, x, FL + 2, z, soul=True)
    a.set(cx, FL - 1, cz, B("lodestone"))
    lights = light_grid(W, HX1 + 3, HZ1, HX2 - 3, HZ2, FL + 8, level=9, spacing=6)
    W.bosses.append(dict(region="dungeon", name="대감옥 심판장", boss_spawn=(cx, FL + 1, cz),
                         box=(HX1, FL + 1, HZ1, HX2, H_TOP - 1, HZ2), entrance=(176, FL + 1, 518)))


def antechamber(W, rng):
    a = W.a

    def wall(x, y, z):
        return DB

    def floor(x, z):
        return PB if (x + z) % 2 else B("polished_deepslate")

    room(W, AX1, AZ1, AX2, AZ2, FL, FL + 7, wall, floor)
    # boss gate east (through the antechamber wall and the 2-thick hall wall)
    for x in range(AX2 + 1, HX1):
        for z in range(516, 521):
            for y in range(FL + 1, FL + 7):
                a.set(x, y, z, AIR)
            a.set(x, FL, z, DT)
    for z in (515, 521):
        for y in range(FL + 1, FL + 8):
            a.set(AX2, y, z, PBB)
    for z in range(516, 521):
        a.set(AX2 + 1, FL + 7, z, B("iron_bars"))
    wall_sign(a, AX2, FL + 4, 514, "west", "§l§4⚠ 보스 ⚠\n§r대감옥 심판장")
    wall_sign(a, AX2, FL + 4, 522, "west", "§l§4⚠ 보스 ⚠\n§r대감옥 심판장")
    hang_sign(a, 167, FL + 7, 527, "north", "§l§c간수 초소\n§r상점 · 엔더 상자", kind="crimson_hanging_sign")
    rec = shop_kit(W, "dungeon", "간수 초소", 166, FL + 1, 516, "east", counter=B("dark_oak_planks"))
    for (x, z) in ((163, 513), (163, 514), (163, 524)):
        a.set(x, FL + 1, z, B("barrel", facing_direction=1))
    a.set(163, FL + 1, 520, B("lectern", cardinal="east"))
    a.set(163, FL + 1, 521, B("crafting_table"))
    for z in range(523, 528, 2):
        a.set(171, FL + 1, z, B("dark_oak_fence"))
        a.set(171, FL + 2, z, B("iron_bars"))
    for (x, z) in ((165, 515), (169, 524), (165, 524)):
        hanging_lantern(a, x, FL + 7, z, chain=1, lamp=B("soul_lantern", hanging=1))
    wall_sign(a, 162, FL + 3, 518, "east", "§l간수 초소\n§r보스전 전에\n장비를 정비하세요")
    wall_sign(a, AX1, FL + 3, 521, "east", "§l§c⚔ 사냥터 ⚔\n§r감방 구역")
    return rec


def cell_block(W, rng):
    a = W.a

    def wall(x, y, z):
        return DB if rng.random() > 0.1 else B("cracked_deepslate_bricks")

    def floor(x, z):
        return rng.choice([PB, DT, B("polished_deepslate"), B("cobbled_deepslate")])

    room(W, CX1, CZ1, CX2, CZ2, FL, FL + 8, wall, floor)
    # gated door from the warden's post (two fence gates in series through the double wall)
    for x in (AX1 - 1, AX1 - 2):
        for z in (519, 520):
            a.set(x, FL + 1, z, B("crimson_fence_gate", cardinal="west"))
            a.set(x, FL + 2, z, AIR)
            a.set(x, FL + 3, z, DB)
    # cells along the north and south walls, some doors broken open
    for (zs, front) in (((CZ1, CZ1 + 1, CZ1 + 2), CZ1 + 2), ((CZ2, CZ2 - 1, CZ2 - 2), CZ2 - 2)):
        for x in range(CX1, CX2 + 1):
            cell = (x - CX1) % 4
            for z in zs:
                for y in range(FL + 1, FL + 5):
                    if cell == 0:
                        a.set(x, y, z, DB)
                    elif z == front:
                        broken = (x // 4) % 3 == 1 and cell == 2
                        a.set(x, y, z, AIR if broken and y <= FL + 2 else B("iron_bars"))
                    else:
                        a.set(x, y, z, AIR)
                a.set(x, FL + 5, z, DB)
            if cell == 2:
                a.set(x, FL + 1, zs[0], B("bone_block"))
    for z in range(CZ1 + 5, CZ2 - 4, 7):
        for x in (CX1 + 6, CX1 + 13):
            for y in range(FL + 1, FL + 9):
                a.set(x, y, z, PBB)
    lights = []
    for x in range(CX1 + 2, CX2 + 1, 5):
        for z in range(CZ1 + 4, CZ2 - 3, 5):
            if a.get(x, FL + 6, z) == AIR:
                a.set(x, FL + 6, z, B("light_block_%d" % HUNT_LIGHT))
                lights.append((x, FL + 6, z))
    pts = [(x, FL + 1, z) for x in (CX1 + 3, CX1 + 9, CX1 + 16) for z in (CZ1 + 6, CZ2 - 6)]
    pts = [p for p in pts if a.get(*p) == AIR]
    W.hunts.append(dict(region="dungeon", name="감방 구역", box=(CX1, FL + 1, CZ1, CX2, FL + 8, CZ2), floor_y=FL,
                        entrances=[(AX1, FL + 1, 519)], spawn_points=pts, lights=lights, roofed=True))


def descent(W, rng):
    """Stairwell from the keep's great hall down to the prison, past the windows of the watch gallery."""
    a = W.a
    wp = [(199, 524, PT), (227, 524, 52), (227, 540, 42), (176, 540, FL), (168, 540, FL), (168, 529, FL)]
    tube(W, wp, width=3, height=4, shell=PBB, floor=DT, ring=B("chiseled_polished_blackstone"), ring_every=6,
         lamp=B("crying_obsidian"), lamp_every=6, stairs="deepslate_tile_stairs")
    # windows from the gallery into the hall (iron bars + red glass through the double wall)
    for x in range(HX1, HX2 + 1):
        if x % 4 == 0:
            continue
        fy = None
        for y in range(FL, 50):
            if a.get(x, y, 540) == DT or a.get(x, y, 540) == B("crying_obsidian") or \
                    a.get(x, y, 540) == B("chiseled_polished_blackstone"):
                fy = y
                break
        if fy is None:
            continue
        for y in range(fy + 1, fy + 5):
            a.set(x, y, HZ2 + 2, B("red_stained_glass"))
            a.set(x, y, HZ2 + 1, B("iron_bars"))
    # inside the great hall the stairwell is a solid stepped block (nobody walks up its roof)
    for x in range(199, 208):
        for z in range(521, 528):
            top = max((y for y in range(PT, PT + 6) if a.get(x, y, z) != AIR), default=None)
            if top is None:
                continue
            if 522 <= z <= 526 and a.get(x, top, z) != AIR:
                for y in range(top + 1, PT + 6):
                    if a.get(x, y, z) == AIR and not (523 <= z <= 525 and y <= top):
                        a.set(x, y, z, B("polished_deepslate"))
    # stairwell entrance arch in the great hall
    for z in (522, 526):
        for y in range(PT + 1, PT + 6):
            a.set(199, y, z, B("polished_deepslate"))
    for z in range(522, 527):
        a.set(199, PT + 5, z, B("polished_deepslate"))
    wall_sign(a, 198, PT + 4, 522, "west", "§l§4지하감옥\n§r↓ 계단 (보스)")
    W.allow("dungeon_stairs", 160, FL - 1, 520, 232, PT + 6, 546)


def build(W):
    import random
    rng = random.Random(W.seed + 1000)
    hall(W, rng)
    antechamber(W, rng)
    cell_block(W, rng)
    descent(W, rng)
    W.spawns["dungeon"] = (166, FL + 1, 522)
    W.allow("dungeon", CX1 - 2, FL - 2, HZ1 - 3, HX2 + 3, H_TOP + 1, HZ2 + 8)
    W.light_boxes.append(("dungeon", CX1, HZ1 - 2, HX2, HZ2 + 6, FL, H_TOP, 4, 9))
