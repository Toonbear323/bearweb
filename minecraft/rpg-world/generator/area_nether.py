"""Nether: a sealed cavern inside the volcano east of the beach.

beach ─ ruined-portal gate ─ tunnel ─ red-window gallery along the cavern wall ─ cavern
cavern: lava lake crossed by fortress bridges (island tower in the middle), basalt deltas (north),
warped forest (east), crimson forest (south-east), soul sand valley (south-west),
piglin trading post = convenience, fortress hall = hunting ground (roofed, for blazes too),
south shore ─ fortress corridor ─ purple-window gatehouse ─ demon king's crater
"""
import math

import numpy as np

from mcw import B, AIR
from gen_common import stair, slab, fbm, line_points
from rpg_world import X0, Z0, BIOME
from rpg_parts import (wall_sign, hang_sign, stand_sign, hanging_lantern, barrel, shop_kit, light_grid, corridor,
                       run_cells, gatehouse, campfire, DV, HUNT_LIGHT, leak_check, banner_wall)
from rpg_carve import chamber, tunnel, box_carve

C = (196, 356, 54, 64)        # cavern centre / radii
LAKE = (200, 355, 26, 20)
LAVA = 57
GAL_X = 141
NB, NBF = B("nether_brick"), B("nether_brick_fence")


def shape(W):
    sl = W.rect(188, 449, 204, 458)
    W.H[sl] = np.minimum(W.H[sl], W.H[W.rect(196, 462, 196, 462)].max())
    W.extra_surface = getattr(W, "extra_surface", []) + [sl]


def cavern(W, rng):
    a = W.a
    cx, cz, rx, rz = C
    rack = B("netherrack")
    ch = chamber(W, cx, cz, rx, rz, 60, 40, W.seed + 800, p=2.2, floor_noise=2.0, wall_noise=0.12, ceil_min=12,
                 floor_block=rack)
    X, Z, inside, fl = ch["X"], ch["Z"], ch["inside"], ch["floor"]
    lx, lz, lrx, lrz = LAKE
    dl = np.sqrt(((X - lx) / lrx) ** 2 + ((Z - lz) / lrz) ** 2)
    n = fbm(X.shape[0], X.shape[1], 6, 2, W.seed + 801)
    lake = inside & (dl + (n - 0.5) * 0.25 < 1.0)
    ring = inside & ~lake & (dl < 1.45)
    for (i, k) in np.argwhere(inside):
        x, z = int(X[i, k]), int(Z[i, k])
        f = int(fl[i, k])
        if lake[i, k]:
            for y in range(LAVA - 4, f + 1):
                a.set(x, y, z, rack)
            a.set(x, LAVA - 4, z, rack)
            for y in range(LAVA - 3, LAVA + 1):
                a.set(x, y, z, B("lava"))
            for y in range(LAVA + 1, f + 1):
                a.set(x, y, z, AIR)
            fl[i, k] = LAVA - 4
        elif ring[i, k] and f < LAVA + 2:
            for y in range(f, LAVA + 3):
                a.set(x, y, z, rack)
            fl[i, k] = LAVA + 2
    W.nether = dict(X=X, Z=Z, inside=inside, floor=fl, lake=lake, ceil=ch["ceil"], box=ch["box"])
    # biomes
    zone = np.full(X.shape, "hell", object)
    nz = fbm(X.shape[0], X.shape[1], 14, 2, W.seed + 802)
    jit = (nz - 0.5) * 16
    zone[(Z + jit < 322)] = "basalt_deltas"
    zone[(X + jit > 226) & (Z + jit >= 322) & (Z + jit < 382)] = "warped_forest"
    zone[(Z + jit >= 382) & (X + jit > 194)] = "crimson_forest"
    zone[(X + jit < 178) & (Z + jit >= 362)] = "soulsand_valley"
    W.nether["zone"] = zone
    x1, z1, x2, z2 = ch["box"]
    for (i, k) in np.argwhere(np.ones(X.shape, bool)):
        x, z = int(X[i, k]), int(Z[i, k])
        W.a.bio[x - X0, z - Z0] = BIOME[zone[i, k]]
    return ch


def nfloor(W, x, z):
    N = W.nether
    x1, z1, x2, z2 = N["box"]
    if x1 <= x <= x2 and z1 <= z <= z2:
        i, k = x - x1, z - z1
        if N["inside"][i, k] and not N["lake"][i, k]:
            return int(N["floor"][i, k])
    return None


def huge_fungus(a, x, y, z, rng, kind):
    stem = B(kind + "_stem")
    wart = B("nether_wart_block") if kind == "crimson" else B("warped_wart_block")
    h = rng.randint(6, 10)
    for k in range(h):
        a.set(x, y + k, z, stem)
    top = y + h
    r = rng.choice([2, 3, 3])
    for k in range(-1, 3):
        rr = r if k <= 0 else r - k
        for dx in range(-rr, rr + 1):
            for dz in range(-rr, rr + 1):
                if dx * dx + dz * dz > rr * rr + 1:
                    continue
                if k == -1 and abs(dx) < rr and abs(dz) < rr:
                    continue
                b = B("shroomlight") if rng.random() < 0.08 else wart
                a.put(x + dx, top + k, z + dz, b)
    if kind == "crimson":
        for _ in range(5):
            dx, dz = rng.randint(-r, r), rng.randint(-r, r)
            ln = rng.randint(1, 3)
            yy = top - 2
            if a.get(x + dx, yy + 1, z + dz) != AIR:
                for t in range(ln):
                    if a.get(x + dx, yy - t, z + dz) == AIR:
                        a.set(x + dx, yy - t, z + dz, B("weeping_vines", weeping_vines_age=20))


def decorate(W, rng):
    a = W.a
    N = W.nether
    X, Z, inside, fl, zone = N["X"], N["Z"], N["inside"], N["floor"], N["zone"]
    ce = N["ceil"]
    occ = []
    for (i, k) in np.argwhere(inside & ~N["lake"]):
        x, z = int(X[i, k]), int(Z[i, k])
        if W.reserved[x - X0, z - Z0]:
            continue
        f = int(fl[i, k])
        zn = zone[i, k]
        r = rng.random()
        if zn == "crimson_forest":
            a.set(x, f, z, B("crimson_nylium"))
            if r < 0.06:
                a.set(x, f + 1, z, B("crimson_roots"))
            elif r < 0.08:
                a.set(x, f + 1, z, B("crimson_fungus"))
        elif zn == "warped_forest":
            a.set(x, f, z, B("warped_nylium"))
            if r < 0.06:
                a.set(x, f + 1, z, B("warped_roots"))
            elif r < 0.09:
                a.set(x, f + 1, z, B("nether_sprouts"))
            elif r < 0.095:
                for t in range(rng.randint(1, 4)):
                    a.set(x, f + 1 + t, z, B("twisting_vines", twisting_vines_age=20))
        elif zn == "soulsand_valley":
            a.set(x, f, z, B("soul_soil") if r < 0.75 else B("soul_sand"))
            if r < 0.01:
                a.set(x, f + 1, z, B("soul_fire"))
        elif zn == "basalt_deltas":
            a.set(x, f, z, B("basalt", axis="y") if r < 0.45 else (B("blackstone") if r < 0.8 else B("magma")))
        else:
            if r < 0.04:
                a.set(x, f, z, B("magma"))
            elif r < 0.06:
                a.set(x, f, z, B("soul_sand"))
            elif r < 0.07:
                a.set(x, f, z, B("quartz_ore"))
            elif r < 0.075:
                a.set(x, f, z, B("nether_gold_ore"))
            if 0.5 < r < 0.508 and a.get(x, f + 1, z) == AIR:
                a.set(x, f + 1, z, B("fire"))
    # big features: fungi, basalt pillars, fossils
    cand = [tuple(c) for c in np.argwhere(inside & ~N["lake"])]
    rng.shuffle(cand)
    for (i, k) in cand:
        x, z = int(X[i, k]), int(Z[i, k])
        if W.reserved[x - X0, z - Z0] or any((x - ox) ** 2 + (z - oz) ** 2 < 49 for ox, oz in occ):
            continue
        f = int(fl[i, k])
        if ce[i, k] - f < 16:
            continue
        zn = zone[i, k]
        r = rng.random()
        if zn in ("crimson_forest", "warped_forest") and r < 0.5:
            huge_fungus(a, x, f + 1, z, rng, "crimson" if zn == "crimson_forest" else "warped")
            occ.append((x, z))
        elif zn == "basalt_deltas" and r < 0.4:
            h = rng.randint(4, 12)
            for t in range(h):
                for (dx, dz) in ((0, 0), (1, 0), (0, 1)) if h > 8 else ((0, 0),):
                    a.set(x + dx, f + 1 + t, z + dz, B("basalt", axis="y"))
            occ.append((x, z))
        elif zn == "soulsand_valley" and r < 0.2:
            # rib-cage fossil, every bone sits on its own column's floor
            for t in range(7):
                fx = x + t
                fs = nfloor(W, fx, z)
                if fs is None:
                    continue
                a.set(fx, fs + 1, z, B("bone_block", axis="x"))
                if t % 2 == 0:
                    for dz in (-2, 2):
                        fz = nfloor(W, fx, z + dz)
                        if fz is not None:
                            for k2 in (1, 2):
                                a.set(fx, fz + k2, z + dz, B("bone_block"))
            occ.append((x, z))
        elif zn == "soulsand_valley" and r < 0.35:
            h = rng.randint(5, 10)
            for t in range(h):
                a.set(x, f + 1 + t, z, B("basalt", axis="y"))
            occ.append((x, z))
    # ceiling: glowstone clusters and weeping vines
    for (i, k) in np.argwhere(inside):
        x, z = int(X[i, k]), int(Z[i, k])
        c = int(ce[i, k])
        r = rng.random()
        if r < 0.012:
            for (dx, dy, dz) in ((0, 0, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0), (-1, 0, 0), (0, 0, -1), (0, -2, 0)):
                if rng.random() < 0.8 and a.get(x + dx, c + dy, z + dz) == AIR:
                    a.set(x + dx, c + dy, z + dz, B("glowstone"))
        elif r < 0.03 and zone[i, k] == "crimson_forest":
            for t in range(rng.randint(2, 6)):
                if a.get(x, c - t, z) == AIR:
                    a.set(x, c - t, z, B("weeping_vines", weeping_vines_age=20))


def lake_rim(W):
    """Railing on every shore cell next to the lava (no accidental swims in lava)."""
    a = W.a
    N = W.nether
    X, Z, lake, fl = N["X"], N["Z"], N["lake"], N["floor"]
    x1, z1, x2, z2 = N["box"]
    nx, nz = lake.shape
    for i in range(1, nx - 1):
        for k in range(1, nz - 1):
            if lake[i, k] or not N["inside"][i, k]:
                continue
            if lake[i + 1, k] or lake[i - 1, k] or lake[i, k + 1] or lake[i, k - 1]:
                x, z = i + x1, k + z1
                f = int(fl[i, k])
                # the rim stands as high as the highest dry neighbour so it cannot be stepped over
                m = max(int(fl[i + di, k + dk]) for di in (-1, 0, 1) for dk in (-1, 0, 1)
                        if not lake[i + di, k + dk] and N["inside"][i + di, k + dk])
                if m > f and a.get(x, f + 1, z) == AIR:
                    for y in range(f + 1, m + 1):
                        a.set(x, y, z, B("netherrack"))
                    f = m
                    fl[i, k] = m
                if a.get(x, f + 1, z) == AIR:
                    a.set(x, f + 1, z, NBF if (x + z) % 5 else B("nether_brick_wall"))
                    W.reserved[x - X0, z - Z0] = True


def lavafalls(W):
    a = W.a
    N = W.nether
    X, Z, ce = N["X"], N["Z"], N["ceil"]
    x1, z1, x2, z2 = N["box"]
    for (x, z) in ((188, 345), (214, 362), (209, 371)):
        i, k = x - x1, z - z1
        c = int(ce[i, k])
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)):
            a.set(x + dx, c + 2, z + dz, B("netherrack"))
            if (dx, dz) != (0, 0):
                a.set(x + dx, c + 1, z + dz, B("netherrack"))
        a.set(x, c + 1, z, B("lava"))
        for y in range(LAVA + 1, c + 1):
            a.set(x, y, z, B("flowing_lava", liquid_depth=8))


def entry(W, rng):
    a = W.a
    bs, pb = B("blackstone"), B("polished_blackstone_bricks")
    # forecourt cut into the volcano's foot, then the ruined portal arch
    gx, gz = 128, 325
    for x in range(121, 130):
        for z in range(gz - 4, gz + 5):
            for y in range(66, 74):
                a.set(x, y, z, AIR)
            if a.get(x, 65, z) == AIR or x >= 125:
                a.set(x, 65, z, rng.choice([bs, B("basalt", axis="y"), bs, B("magma")]) if abs(z - gz) > 2
                      else B("polished_blackstone"))
            yy = 64
            while yy > 55 and a.get(x, yy, z) == AIR:
                a.set(x, yy, z, bs)
                yy -= 1
    for x in range(121, 130):
        for z in (gz - 5, gz + 5):
            for y in range(66, 74 - (129 - x) // 2):
                a.set(x, y, z, bs if (x + y) % 3 else B("basalt", axis="y"))
    for y in range(65, 72):
        for dz in (-3, 3):
            a.set(gx, y, gz + dz, B("obsidian") if (y + dz) % 3 else B("crying_obsidian"))
    for dz in range(-3, 4):
        a.set(gx, 72, gz + dz, B("obsidian") if dz % 2 else B("crying_obsidian"))
    for dz in (-2, 2):
        a.set(gx, 71, gz + dz, B("obsidian"))
    for (dx, dz) in ((-1, -4), (-1, 4), (1, -5), (-2, 3)):
        a.set(gx + dx, 65, gz + dz, B("magma"))
        a.set(gx + dx, 66, gz + dz, B("netherrack"))
    a.set(gx - 1, 66, gz - 4, B("fire"))
    wall_sign(a, gx - 1, 67, gz - 3, "west", "§l§c지옥\n§r→ 화산 안으로")
    # tunnel into the volcano, then the windowed gallery along the cavern wall
    cells = run_cells(129, 325, "east", 13) + run_cells(GAL_X, 326, "south", 21)
    corridor(W, cells, 65, width=5, height=5, wall=pb, floor=B("polished_blackstone"), roof=pb,
             window=B("red_stained_glass_pane"), window_side="left", window_every=4, window_rows=(2, 3, 4),
             pillar=B("polished_basalt"), lamp=B("soul_lantern", hanging=1), lamp_every=6)
    pane = B("red_stained_glass_pane")
    for x in range(120, 150):
        for z in range(318, 356):
            for y in range(66, 71):
                if a.get(x, y, z) == pane and not (x == GAL_X + 3 and 329 <= z <= 340):
                    a.set(x, y, z, pb)
    box_carve(W, GAL_X + 4, 62, 327, GAL_X + 12, 82, 349)
    for x in range(GAL_X + 4, GAL_X + 13):
        for z in range(327, 350):
            f = nfloor(W, x, z)
            for y in range(56, 63):
                a.set(x, y, z, B("netherrack"))
    # down into the cavern: east through the gallery wall
    cells2 = run_cells(GAL_X + 3, 344, "east", 14)
    fys = [65, 65] + [max(60, 65 - (i - 1)) for i in range(2, 14)]
    corridor(W, cells2, fys, width=5, height=5, wall=pb, floor=B("polished_blackstone"), roof=pb,
             lamp=B("soul_lantern", hanging=1), lamp_every=5)
    for i in range(1, len(cells2)):
        if fys[i] < fys[i - 1]:
            x, z = cells2[i]
            for w in range(-2, 3):
                a.set(x, fys[i] + 1, z + w, stair("polished_blackstone_brick_stairs", "west"))
    for (x, z) in cells2[-3:]:
        for w in range(-2, 3):
            for y in range(61, 67):
                a.set(x, y, z + w, AIR)
            a.set(x, 60, z + w, B("polished_blackstone"))
    wall_sign(a, GAL_X - 2, 67, 330, "east", "§l§c지옥\n§r창밖이 용암 동굴입니다")


def bridge(W, x1, z1, x2, z2, y, rng):
    """Fortress bridge (3 wide deck, fence railings, arches down into the lava)."""
    a = W.a
    horiz = z1 == z2
    n = abs(x2 - x1) + abs(z2 - z1)
    dx = (1 if x2 > x1 else -1) if horiz else 0
    dz = 0 if horiz else (1 if z2 > z1 else -1)
    for t in range(n + 1):
        x, z = x1 + dx * t, z1 + dz * t
        for w in range(-2, 3):
            cx, cz = (x, z + w) if horiz else (x + w, z)
            a.set(cx, y, cz, NB)
            a.set(cx, y - 1, cz, NB)
            for yy in range(y + 1, y + 4):
                if a.get(cx, yy, cz) != AIR:
                    a.set(cx, yy, cz, AIR)
            if abs(w) == 2:
                a.set(cx, y + 1, cz, NBF)
        if t % 6 == 0:
            for w in (-2, 2):
                cx, cz = (x, z + w) if horiz else (x + w, z)
                yy = y - 2
                while yy > LAVA - 4 and a.get(cx, yy, cz) in (AIR, B("lava"), B("flowing_lava")):
                    a.set(cx, yy, cz, NB)
                    yy -= 1
                a.set(cx, y + 2, cz, B("nether_brick_wall"))
                a.set(cx, y + 3, cz, B("soul_lantern"))


def lake_crossing(W, rng):
    a = W.a
    y = 63
    lx, lz = LAKE[0], LAKE[1]
    bridge(W, 168, lz, lx - 4, lz, y, rng)
    bridge(W, lx, lz + 4, lx, 382, y, rng)
    # island tower
    for x in range(lx - 4, lx + 5):
        for z in range(lz - 4, lz + 5):
            for yy in range(LAVA - 4, y + 1):
                a.set(x, yy, z, NB)
            edge = abs(x - lx) == 4 or abs(z - lz) == 4
            if edge:
                a.set(x, y + 1, z, NBF)
    for (dx, dz) in ((-4, 0), (0, 4)):
        for w in (-1, 0, 1):
            a.set(lx + dx + (w if dx == 0 else 0), y + 1, lz + dz + (w if dz == 0 else 0), AIR)
    for (dx, dz) in ((3, -3), (3, 3), (-3, -3), (-3, 3)):
        for yy in range(y + 1, y + 7):
            a.set(lx + dx, yy, lz + dz, NB)
        a.set(lx + dx, y + 7, lz + dz, B("soul_lantern"))
    for x in range(lx - 3, lx + 4):
        for z in range(lz - 3, lz + 4):
            a.set(x, y + 7, z, NB if (abs(x - lx) == 3 or abs(z - lz) == 3) else B("nether_brick_slab"))
    campfire(a, lx, y + 1, lz, soul=True)
    stand_sign(a, lx - 2, y + 1, lz - 2, "west", "§l§c용암 호수\n§r남쪽: 마왕성\n§7북동: 요새 사냥터")
    # ramps from the bridge heads down to the cavern floor
    for (x, z, d) in ((167, lz, "west"), (lx, 383, "south")):
        f = nfloor(W, x + DV[d][0] * 3, z + DV[d][1] * 3) or 60
        yy = y
        t = 0
        while yy > f:
            cx, cz = x + DV[d][0] * t, z + DV[d][1] * t
            for w in range(-2, 3):
                px, pz = (cx, cz + w) if d in ("west", "east") else (cx + w, cz)
                for k in range(f, yy):
                    a.set(px, k, pz, NB)
                a.set(px, yy, pz, stair("nether_brick_stairs", {"west": "east", "south": "north"}[d]))
                for k in range(yy + 1, yy + 4):
                    a.set(px, k, pz, AIR)
            yy -= 1
            t += 1
    W.reserved[W.rect(166, lz - 6, lx + 6, 384)] = True


def trading_post(W, rng):
    """Convenience space: bastion-style piglin trading post near the arrival."""
    a = W.a
    x1, z1, x2, z2 = 150, 366, 166, 380
    f = 61
    pb, gb, bs = B("polished_blackstone_bricks"), B("gilded_blackstone"), B("blackstone")
    for x in range(x1 - 1, x2 + 2):
        for z in range(z1 - 1, z2 + 2):
            for y in range(f - 4, f + 1):
                a.set(x, y, z, pb if y == f else bs)
            for y in range(f + 1, f + 9):
                a.set(x, y, z, AIR)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            for y in range(f + 1, f + 6):
                if corner:
                    a.set(x, y, z, B("polished_basalt"))
                elif edge:
                    win = 2 <= y - f <= 3 and (x + z) % 3 == 0
                    a.set(x, y, z, B("iron_bars") if win else (gb if rng.random() < 0.15 else pb))
            a.set(x, f + 6, z, pb if edge else B("polished_blackstone_slab", half="top"))
            if edge and (x + z) % 2 == 0:
                a.set(x, f + 7, z, B("polished_blackstone_wall"))
    for z in range(z1 + 5, z1 + 10):
        for y in range(f + 1, f + 5):
            a.set(x2, y, z, AIR)
    hang_sign(a, x2 + 1, f + 5, z1 + 7, "east", "§l§6피글린 교역소\n§r상점 · 엔더 상자", kind="crimson_hanging_sign")
    a.set(x2 + 1, f + 6, z1 + 7, pb)
    rec = shop_kit(W, "nether", "피글린 교역소", 158, f + 1, 373, "east", counter=pb)
    for (x, z) in ((152, 368), (152, 378), (164, 368)):
        a.set(x, f + 1, z, B("gold_block") if (x + z) % 2 else B("raw_gold_block"))
    a.set(152, f + 1, 373, B("respawn_anchor", respawn_anchor_charge=4))
    for (x, z) in ((154, 369), (162, 377), (158, 369)):
        hanging_lantern(a, x, f + 5, z, chain=1, lamp=B("soul_lantern", hanging=1))
    for (x, z) in ((168, 370), (168, 377)):
        campfire(a, x, f + 1, z, soul=True)
    W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 4, z2 + 2)] = True
    return rec


def fortress_hunt(W, rng):
    """Hunting ground: a roofed nether-fortress hall (flying blazes stay inside)."""
    a = W.a
    x1, z1, x2, z2 = 212, 300, 240, 322
    f = nfloor(W, x1 + 13, z2 + 7) or 61
    for x in range(x1 - 1, x2 + 2):
        for z in range(z1 - 1, z2 + 2):
            edge = x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)
            for y in range(f - 5, f + 1):
                a.set(x, y, z, NB)
            for y in range(f + 1, f + 11):
                if edge:
                    win = y in (f + 5, f + 6) and (x + z) % 4 == 0
                    a.set(x, y, z, NBF if win else (B("cracked_nether_bricks") if rng.random() < 0.1 else NB))
                else:
                    a.set(x, y, z, AIR)
            a.set(x, f + 11, z, NB)
            if not edge and rng.random() < 0.15:
                a.set(x, f, z, B("red_nether_brick"))
    # columns and soul lanterns
    for x in range(x1 + 4, x2 - 2, 8):
        for z in (z1 + 5, z2 - 5):
            for y in range(f + 1, f + 11):
                a.set(x, y, z, B("chiseled_nether_bricks") if y % 4 == 0 else NB)
    # nether wart beds as cover
    for (x, z) in ((x1 + 3, z1 + 10), (x2 - 6, z1 + 10)):
        for dx in range(3):
            a.set(x + dx, f, z, B("soul_sand"))
            a.set(x + dx, f + 1, z, B("nether_wart", age=3))
        for dx in (-1, 3):
            a.set(x + dx, f + 1, z, NB)
    # gate: two crimson fence gates in series through a short vestibule (south wall)
    gx = x1 + 13
    for z in (z2 + 1, z2 + 2, z2 + 3, z2 + 4):
        for dx in (-1, 0, 1, 2):
            for y in range(f + 1, f + 5):
                side = dx in (-1, 2)
                a.set(gx + dx, y, z, NB if (side or y == f + 4) else AIR)
            a.set(gx + dx, f, z, NB)
    for z in (z2 + 1, z2 + 4):
        for dx in (0, 1):
            a.set(gx + dx, f + 1, z, B("crimson_fence_gate", cardinal="south"))
            a.set(gx + dx, f + 2, z, AIR)
            a.set(gx + dx, f + 3, z, NB)
    wall_sign(a, gx, f + 3, z2 + 5, "south", "§l§c⚔ 사냥터 ⚔\n§r요새 사냥터", kind="crimson_wall_sign")
    wall_sign(a, gx + 1, f + 3, z2 + 5, "south", "§l§c⚔ 사냥터 ⚔\n§r요새 사냥터", kind="crimson_wall_sign")
    lights = []
    for x in range(x1 + 2, x2 + 1, 5):
        for z in range(z1 + 2, z2 + 1, 5):
            if a.get(x, f + 6, z) == AIR:
                a.set(x, f + 6, z, B("light_block_%d" % HUNT_LIGHT))
                lights.append((x, f + 6, z))
    pts = [(x, f + 1, z) for x in (x1 + 7, x1 + 15, x1 + 23) for z in (z1 + 4, z2 - 4)]
    pts = [p for p in pts if a.get(*p) == AIR]
    W.hunts.append(dict(region="nether", name="요새 사냥터", box=(x1, f + 1, z1, x2, f + 10, z2), floor_y=f,
                        entrances=[(gx, f + 1, z2 + 5)], spawn_points=pts, lights=lights, roofed=True))
    W.reserved[W.rect(x1 - 2, z1 - 2, x2 + 2, z2 + 6)] = True


def paths(W, rng):
    a = W.a
    tiles = [B("polished_blackstone_bricks"), B("polished_blackstone"), B("blackstone"),
             B("cracked_polished_blackstone_bricks")]
    routes = [[(GAL_X + 16, 344), (162, 350), (167, 355)],
              [(160, 354), (160, 364), (166, 372)],
              [(172, 345), (190, 332), (210, 330), (226, 328)],
              [(200, 384), (198, 398), (196, 414)]]
    for pts in routes:
        for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
            for (x, _, z) in line_points((ax, 0, az), (bx, 0, bz), 0.5):
                for ox in (-1, 0, 1):
                    for oz in (-1, 0, 1):
                        f = nfloor(W, x + ox, z + oz)
                        if f is None:
                            continue
                        a.set(x + ox, f, z + oz, rng.choice(tiles))
                        for y in range(f + 1, f + 4):
                            if a.get(x + ox, y, z + oz) not in (AIR,):
                                a.set(x + ox, y, z + oz, AIR)
                        W.reserved[x + ox - X0, z + oz - Z0] = True
    for (x, z) in ((165, 350), (178, 337), (205, 326), (199, 392), (156, 360)):
        f = nfloor(W, x, z)
        if f is not None:
            a.set(x, f + 1, z, B("nether_brick_wall"))
            a.set(x, f + 2, z, B("nether_brick_wall"))
            a.set(x, f + 3, z, B("soul_lantern"))


def exit_route(W, rng):
    a = W.a
    pb = B("polished_blackstone_bricks")
    f0 = nfloor(W, 196, 414) or 62
    pts = [(196, f0, 412), (196, f0, 418), (196, 66, 432), (196, 66, 440)]
    tunnel(W, pts, width=5, height=5, floor_block=NB)
    for z in range(418, 433):
        fy = int(round(f0 + (66 - f0) * (z - 418) / 14))
        nxt = int(round(f0 + (66 - f0) * (z + 1 - 418) / 14))
        for x in range(194, 199):
            a.set(x, fy, z, NB)
            for y in range(fy + 1, fy + 5):
                a.set(x, y, z, AIR)
            if nxt > fy:
                a.set(x, fy + 1, z, stair("nether_brick_stairs", "south"))
    gatehouse(W, 196, 444, "south", 66, "purple", wall=pb, pillar=B("polished_basalt"),
              roof_stairs="polished_blackstone_brick_stairs", roof_ridge=B("polished_blackstone_slab"),
              floor=B("polished_blackstone"), next_name="§5마왕성", prev_name="§c지옥",
              gable=pb, foundation=B("blackstone"), sign_kind="crimson_wall_sign")


def build(W):
    import random
    rng = random.Random(W.seed + 800)
    cavern(W, rng)
    entry(W, rng)
    lake_crossing(W, rng)
    trading_post(W, rng)
    fortress_hunt(W, rng)
    paths(W, rng)
    exit_route(W, rng)
    lake_rim(W)
    decorate(W, rng)
    lavafalls(W)
    W.spawns["nether"] = (GAL_X + 15, 61, 344)
    x1, z1, x2, z2 = W.nether["box"]
    W.allow("nether", 120, 54, 316, x2 + 2, 104, 450)
    W.allow("nether_cavern", x1, 54, z1, x2, 104, z2)
    W.light_boxes.append(("nether", x1, z1, x2, z2, 55, 100, 1, 9))
    leaks = leak_check(W, (x1 - 2, 50, z1 - 2, x2 + 2, 104, z2 + 2))
    print("  nether lava leaks:", len(leaks), leaks[:8])
