"""Piglin Bastion 'The Golden Bulwark': ramparts, stables, housing and a treasure keep."""
import math

from . import blocks as bl
from . import dkit as dk
from . import kit
from .core import B, Mix
from .layout import BIO_CRIMSON
from .nether import BAST, NF, bb_mix

AIR = 0
AX = 64
GILD = B("gilded_blackstone")
GOLD = B("gold_block")


def wallmix():
    return Mix((B("polished_blackstone_bricks"), 9), (B("cracked_polished_blackstone_bricks"), 3),
               (B("blackstone"), 3), (B("polished_blackstone"), 1), (GILD, 0.5))


def rampart(w, x0, z0, x1, z1, h=9):
    wm = wallmix()
    for (xa, za, xb, zb) in ((x0, z0, x1, z0 + 2), (x0, z1 - 2, x1, z1), (x0, z0, x0 + 2, z1), (x1 - 2, z0, x1, z1)):
        w.fill(xa, NF - 3, za, xb, NF + h, zb, wm)
        w.fill(xa, NF + h + 1, za, xb, NF + h + 12, zb, AIR)
    # crenellations + walkway lights
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if (x - x0) % 3 != 2:
                w.set(x, NF + h + 1, z, wm)
            if (x - x0) % 12 == 6:
                w.set(x, NF + h + 2, z, bl.lantern(soul=False))
                w.set(x, NF + h + 1, z, GILD)
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            if (z - z0) % 3 != 2:
                w.set(x, NF + h + 1, z, wm)
            if (z - z0) % 12 == 6:
                w.set(x, NF + h + 2, z, bl.lantern())
                w.set(x, NF + h + 1, z, GILD)
    # base batter
    for x in range(x0 - 1, x1 + 2):
        w.set(x, NF + 1, z0 - 1, bl.stairs("polished_blackstone_brick", "S"), keep=True)
        w.set(x, NF + 1, z1 + 1, bl.stairs("polished_blackstone_brick", "N"), keep=True)
    for z in range(z0, z1 + 1):
        w.set(x0 - 1, NF + 1, z, bl.stairs("polished_blackstone_brick", "E"), keep=True)
        w.set(x1 + 1, NF + 1, z, bl.stairs("polished_blackstone_brick", "W"), keep=True)


def corner_bastion(w, cx, cz, h=15):
    wm = wallmix()
    w.fill(cx - 5, NF - 3, cz - 5, cx + 5, NF + h, cz + 5, wm)
    w.fill(cx - 3, NF + 1, cz - 3, cx + 3, NF + h - 1, cz + 3, AIR)
    w.fill(cx - 3, NF + 8, cz - 3, cx + 3, NF + 8, cz + 3, wm)
    for t in range(-5, 6):
        for (x, z) in ((cx + t, cz - 5), (cx + t, cz + 5), (cx - 5, cz + t), (cx + 5, cz + t)):
            w.set(x, NF + h + 1, z, wm if t % 2 == 0 else AIR)
            if abs(t) == 2:
                for y in (NF + 4, NF + 5, NF + 11, NF + 12):
                    w.set(x, y, z, AIR)
            w.set(x, NF + 7, z, GILD) if t % 2 else None
    w.fill(cx - 1, NF + h + 1, cz - 1, cx + 1, NF + h + 1, cz + 1, B("netherrack"))
    w.set(cx, NF + h + 2, cz, B("fire", age=0))
    w.fill(cx - 1, NF + h, cz - 1, cx + 1, NF + h, cz + 1, B("basalt", pillar_axis="y"))


def hut(w, x0, z0, rng, ent="piglin"):
    """Small piglin dwelling 9x7 with the door on the north side."""
    wm = wallmix()
    w.fill(x0, NF, z0, x0 + 8, NF + 6, z0 + 6, wm)
    w.fill(x0 + 1, NF + 1, z0 + 1, x0 + 7, NF + 5, z0 + 5, AIR)
    w.fill(x0, NF + 6, z0, x0 + 8, NF + 6, z0 + 6, B("polished_blackstone"))
    for x in range(x0 - 1, x0 + 10):
        w.set(x, NF + 6, z0 - 1, bl.slab("polished_blackstone_brick", top=True))
        w.set(x, NF + 6, z0 + 7, bl.slab("polished_blackstone_brick", top=True))
    w.set(x0 + 4, NF + 1, z0, AIR)
    w.set(x0 + 4, NF + 2, z0, AIR)
    for x in (x0 + 2, x0 + 6):
        w.set(x, NF + 3, z0, B("iron_bars"))
        w.set(x, NF + 3, z0 + 6, B("iron_bars"))
    w.set(x0 + 4, NF + 5, z0 + 3, bl.lantern(True))
    w.fill(x0 + 1, NF, z0 + 1, x0 + 7, NF, z0 + 5, Mix((B("polished_blackstone_bricks"), 3), (B("nether_wart_block"), 1),
                                                       (GILD, 0.6)))
    dk.spawner(w, x0 + 6, NF + 1, z0 + 4, ent, max_nearby=4)
    dk.chest(w, x0 + 1, NF + 1, z0 + 5, "N", 3, rng, extra=[bl.item("gold_ingot", int(rng.integers(4, 12)))])
    w.set(x0 + 2, NF + 1, z0 + 5, GOLD) if rng.random() < 0.5 else None
    w.put(x0 + 4, NF + 4, z0 - 1, bl.wall_banner("N"), bl.be_banner(11))


def build(w, log=print):
    rng = w.rng
    wm = wallmix()
    floor = bb_mix()
    x0c, z0c, x1c, z1c = BAST
    w.biome[x0c - w.x0:x1c - w.x0, z0c - w.z0:z1c - w.z0] = BIO_CRIMSON
    # ---- cavern floor dressing --------------------------------------------------------------
    for x in range(x0c + 2, x1c - 1):
        for z in range(z0c + 2, z1c - 1):
            for y in range(NF + 3, NF - 4, -1):
                b = w.get(x, y, z)
                if b != 0:
                    if w.get(x, y + 1, z) == 0 and b not in (bl.LAVA,):
                        r = rng.random()
                        w.set(x, y, z, B("blackstone") if r < 0.45 else B("basalt", pillar_axis="y") if r < 0.7 else B(
                            "smooth_basalt") if r < 0.85 else B("crimson_nylium") if r < 0.95 else B("magma"))
                        if r > 0.93 and r < 0.95:
                            w.set(x, y + 1, z, B("crimson_roots"))
                    break
    # lava lakes outside the ramparts (north-west / south-west)
    for (lx, lz, lr) in ((-240, 20, 9), (-242, 104, 10), (-112, 22, 8), (-110, 108, 9)):
        for (dx, dz) in kit.disc_cells(lr):
            if math.hypot(dx, dz) < lr - rng.random() * 2:
                w.fill(lx + dx, NF - 1, lz + dz, lx + dx, NF, lz + dz, bl.LAVA)
                w.set(lx + dx, NF - 2, lz + dz, B("magma"))
                w.fill(lx + dx, NF + 1, lz + dz, lx + dx, NF + 3, lz + dz, AIR)
    # ---- approach road -------------------------------------------------------------------------
    for x in range(-124, -95):
        for z in range(AX - 3, AX + 4):
            w.set(x, NF, z, floor if abs(z - AX) < 3 else B("polished_blackstone"))
            w.fill(x, NF + 1, z, x, NF + 7, z, AIR)
        if x % 8 == 0:
            for z in (AX - 4, AX + 4):
                w.set(x, NF + 1, z, B("polished_blackstone_brick_wall", wall_post_bit=True))
                w.set(x, NF + 2, z, B("polished_blackstone_brick_wall", wall_post_bit=True))
                w.set(x, NF + 3, z, bl.lantern())
    # ---- ramparts + corner bastions + gate ------------------------------------------------------------
    rx0, rz0, rx1, rz1 = -236, 18, -124, 110
    w.fill(rx0, NF + 1, rz0, rx1, NF + 40, rz1, AIR)
    w.fill(rx0, NF - 2, rz0, rx1, NF, rz1, Mix((B("blackstone"), 5), (B("polished_blackstone_bricks"), 3),
                                               (B("basalt", pillar_axis="y"), 2), (GILD, 0.2)))
    rampart(w, rx0, rz0, rx1, rz1)
    for (cx, cz) in ((rx0, rz0), (rx1, rz0), (rx0, rz1), (rx1, rz1)):
        corner_bastion(w, cx, cz)
    # gate house on the east wall
    gx = rx1
    w.fill(gx - 4, NF - 3, AX - 8, gx + 2, NF + 15, AX + 8, wm)
    w.fill(gx - 4, NF + 1, AX - 2, gx + 2, NF + 7, AX + 2, AIR)
    for x in range(gx - 4, gx + 3):
        w.set(x, NF + 7, AX - 2, bl.stairs("polished_blackstone_brick", "N", top=True))
        w.set(x, NF + 7, AX + 2, bl.stairs("polished_blackstone_brick", "S", top=True))
        w.set(x, NF + 6, AX - 2, bl.stairs("polished_blackstone_brick", "N", top=True)) if False else None
        w.set(x, NF, AX, GILD)
    # snout emblem above the arch
    for (dz, dy, b) in ((-3, 12, GOLD), (3, 12, GOLD), (-1, 10, GOLD), (0, 10, GOLD), (1, 10, GOLD), (-1, 9, GOLD),
                        (1, 9, GOLD), (0, 9, B("crying_obsidian")), (-4, 9, GILD), (4, 9, GILD), (-5, 8, GOLD),
                        (5, 8, GOLD), (-3, 13, B("crying_obsidian")), (3, 13, B("crying_obsidian"))):
        w.set(gx + 3, NF + dy, AX + dz, b)
    for dz in (-7, 7):
        w.fill(gx + 3, NF + 1, AX + dz - 1, gx + 3, NF + 13, AX + dz + 1, wm)
        w.set(gx + 3, NF + 14, AX + dz, B("netherrack"))
        w.set(gx + 3, NF + 15, AX + dz, B("fire", age=0))
        w.put(gx + 4, NF + 9, AX + dz, bl.wall_banner("E"), bl.be_banner(11))
    for x in range(gx - 4, gx + 3, 2):
        for z in (AX - 8, AX + 8):
            w.set(x, NF + 16, z, wm)
    dk.sign(w, gx + 4, NF + 4, AX - 3, "E", "§6§l피글린 요새\n§r황금 보루\n§8황금 갑옷 권장", wood="crimson", glow=True)
    dk.plate(w, gx - 1, NF + 1, AX, "function bear/enter/bastion", kind="polished_blackstone_pressure_plate", floor=GILD)
    # ---- courtyard: road, stables, housing ----------------------------------------------------------------
    for x in range(-170, gx - 4):
        for z in range(AX - 2, AX + 3):
            w.set(x, NF, z, floor if abs(z - AX) < 2 else B("polished_blackstone"))
    # hoglin stables (north-east quarter)
    sx0, sz0 = -160, 26
    for k in range(3):
        px = sx0 + k * 11
        w.fill(px, NF, sz0, px + 9, NF, sz0 + 12, B("crimson_nylium"))
        for x in range(px, px + 10):
            for z in (sz0, sz0 + 12):
                w.set(x, NF + 1, z, B("blackstone_wall", wall_post_bit=True) if (x - px) % 3 else wm)
                w.set(x, NF + 2, z, bl.fence("crimson")) if (x - px) % 3 else w.set(x, NF + 2, z, wm)
        for z in range(sz0, sz0 + 13):
            for x in (px, px + 9):
                w.set(x, NF + 1, z, B("blackstone_wall", wall_post_bit=True) if (z - sz0) % 3 else wm)
        w.set(px + 4, NF + 1, sz0 + 12, bl.gate("crimson", "S"))
        w.set(px + 5, NF + 1, sz0 + 12, bl.gate("crimson", "S"))
        w.set(px + 4, NF + 2, sz0 + 12, AIR)
        w.set(px + 5, NF + 2, sz0 + 12, AIR)
        for _ in range(6):
            fx, fz = px + int(rng.integers(1, 9)), sz0 + int(rng.integers(1, 12))
            w.set(fx, NF + 1, fz, B("crimson_fungus") if rng.random() < 0.6 else B("crimson_roots"))
        w.set(px + 2, NF + 1, sz0 + 2, B("hay_block")) if False else w.set(px + 2, NF + 1, sz0 + 2, B("nether_wart_block"))
    dk.spawner(w, sx0 + 15, NF + 1, sz0 + 5, "hoglin", max_nearby=4)
    w.set(sx0 + 15, NF, sz0 + 5, GILD)
    # housing (south-east quarter)
    hut(w, -160, 90, rng, "piglin")
    hut(w, -146, 90, rng, "piglin")
    hut(w, -132 - 4, 78, rng, "piglin_brute")
    # basalt columns + braziers in the yard
    for (bx, bz) in ((-140, 50), (-140, 78), (-164, 50), (-164, 78), (-150, 56), (-150, 72)):
        for y in range(NF + 1, NF + 7):
            w.set(bx, y, bz, B("polished_basalt", pillar_axis="y"))
        w.set(bx, NF + 7, bz, B("netherrack"))
        w.set(bx, NF + 8, bz, B("fire", age=0))
    # ---- treasure keep ---------------------------------------------------------------------------------------
    kx0, kx1, kz0, kz1 = -216, -172, AX - 22, AX + 22
    H = 26
    w.fill(kx0 - 1, NF - 3, kz0 - 1, kx1 + 1, NF + 3, kz1 + 1, wm)          # battered base
    w.fill(kx0, NF - 10, kz0, kx1, NF + H, kz1, wm)
    w.fill(kx0 + 3, NF + 1, kz0 + 3, kx1 - 3, NF + H - 2, kz1 - 3, AIR)
    cx, cz = (kx0 + kx1) // 2, AX
    # east door
    w.fill(kx1 - 2, NF + 1, AX - 2, kx1 + 1, NF + 6, AX + 2, AIR)
    for x in range(kx1 - 2, kx1 + 2):
        w.set(x, NF + 6, AX - 2, bl.stairs("polished_blackstone_brick", "N", top=True))
        w.set(x, NF + 6, AX + 2, bl.stairs("polished_blackstone_brick", "S", top=True))
    for dz in (-4, 4):
        w.fill(kx1 + 1, NF + 1, AX + dz, kx1 + 2, NF + 9, AX + dz, wm)
        w.set(kx1 + 2, NF + 10, AX + dz, GOLD)
        w.set(kx1 + 3, NF + 5, AX + dz, bl.torch("W", "soul_torch"))
    # exterior ribs + gold bands + slit windows
    for t in range(4, 41, 6):
        for (x, z, ox, oz) in ((kx0 + t, kz0, 0, -1), (kx0 + t, kz1, 0, 1), (kx0, kz0 + t, -1, 0), (kx1, kz0 + t, 1, 0)):
            if (ox == 1) and abs(z - AX) < 6:
                continue
            w.fill(x + ox, NF + 1, z + oz, x + ox, NF + H - 4, z + oz, B("polished_basalt", pillar_axis="y"))
            w.set(x + ox, NF + H - 3, z + oz, GOLD)
            for y in (NF + 12, NF + 13, NF + 18, NF + 19):
                for k in (2, 3):
                    wx_, wz_ = (x + k, z) if oz else (x, z + k)
                    w.set(wx_, y, wz_, AIR)
                    w.set(wx_ - ox if False else wx_, y, wz_, AIR)
                    for dd in (1, 2):
                        w.set(wx_ - ox * dd, y, wz_ - oz * dd, AIR)
    for t in range(0, 45):
        for (x, z) in ((kx0 + t, kz0), (kx0 + t, kz1), (kx0, kz0 + t), (kx1, kz0 + t)):
            w.set(x, NF + 9, z, GILD if t % 2 else B("polished_blackstone"))
            w.set(x, NF + H + 1, z, wm if t % 3 != 2 else AIR)
    # interior: ring floor around a lava pit with the hoard pillar
    w.fill(kx0 + 3, NF, kz0 + 3, kx1 - 3, NF, kz1 - 3, floor)
    pit = 8
    w.fill(cx - pit, NF - 6, cz - pit, cx + pit, NF, cz + pit, AIR)
    w.fill(cx - pit, NF - 7, cz - pit, cx + pit, NF - 7, cz + pit, B("magma"))
    w.fill(cx - pit, NF - 6, cz - pit, cx + pit, NF - 4, cz + pit, bl.LAVA)
    w.fill(cx - 2, NF - 7, cz - 2, cx + 2, NF, cz + 2, wm)
    w.fill(cx - 3, NF, cz - 3, cx + 3, NF, cz + 3, B("polished_blackstone"))
    w.fill(cx - 2, NF, cz - 2, cx + 2, NF, cz + 2, GILD)
    for (dx, dz, hh) in ((0, 0, 3), (1, 0, 2), (-1, 0, 2), (0, 1, 2), (0, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)):
        w.fill(cx + dx, NF + 1, cz + dz, cx + dx, NF + hh, cz + dz, GOLD)
    dk.chest(w, cx + 2, NF + 1, cz - 1, "E", 4, rng, extra=[bl.item("gold_block", 4), bl.item("netherite_scrap", 2)])
    dk.chest(w, cx - 2, NF + 1, cz + 1, "W", 4, rng, extra=[bl.item("enchanted_golden_apple", 1)])
    for d in range(4, pit + 1):               # bridges east and west
        for dz in (-1, 0, 1):
            w.set(cx + d, NF, cz + dz, floor)
            w.set(cx - d, NF, cz + dz, floor)
    for (x, z) in ((cx - pit - 1, cz - pit - 1), (cx + pit + 1, cz - pit - 1), (cx - pit - 1, cz + pit + 1),
                   (cx + pit + 1, cz + pit + 1)):
        for y in range(NF + 1, NF + H - 2):
            w.set(x, y, z, B("polished_basalt", pillar_axis="y") if y % 6 else GILD)
    for t in range(-pit - 1, pit + 2):
        for (x, z) in ((cx + t, cz - pit - 1), (cx + t, cz + pit + 1), (cx - pit - 1, cz + t), (cx + pit + 1, cz + t)):
            if abs(t) > 1 or (x != cx - pit - 1 and x != cx + pit + 1):
                if w.get(x, NF + 1, z) == 0 and abs(t) != pit + 1:
                    w.set(x, NF + 1, z, B("polished_blackstone_brick_wall", wall_post_bit=True)) if (
                        not (abs(t) <= 1 and z == cz + t and False)) else None
    for dz in (-1, 0, 1):
        w.set(cx - pit - 1, NF + 1, cz + dz, AIR)
        w.set(cx + pit + 1, NF + 1, cz + dz, AIR)
    # gallery level with stairs
    gy = NF + 9
    for x in range(kx0 + 3, kx1 - 2):
        for z in range(kz0 + 3, kz1 - 2):
            if min(x - kx0 - 3, kx1 - 3 - x, z - kz0 - 3, kz1 - 3 - z) < 5:
                w.set(x, gy, z, floor)
                if min(x - kx0 - 3, kx1 - 3 - x, z - kz0 - 3, kz1 - 3 - z) == 4:
                    w.set(x, gy + 1, z, B("polished_blackstone_brick_wall", wall_post_bit=True))
    for i in range(9):
        z = kz0 + 4 + i
        for x in (kx1 - 5, kx1 - 4):
            w.set(x, NF + 1 + i, z, bl.stairs("polished_blackstone_brick", "S"))
            w.fill(x, NF + 1, z, x, NF + i, z, wm) if i > 0 else None
            w.fill(x, NF + 2 + i, z, x, gy + 3, z, AIR)
    w.set(kx1 - 6, gy + 1, kz0 + 12, AIR) if False else None
    for x in (kx1 - 7, kx1 - 6):
        for z in range(kz0 + 12, kz0 + 14):
            w.set(x, gy + 1, z, AIR)
    dk.spawner(w, kx0 + 5, gy + 1, kz0 + 5, "piglin_brute", max_nearby=3, count=1)
    dk.spawner(w, kx0 + 5, gy + 1, kz1 - 5, "piglin", max_nearby=4)
    dk.spawner(w, cx, NF - 3, cz - pit + 1, "magma_cube", max_nearby=4)
    w.set(cx, NF - 4, cz - pit + 1, B("chiseled_polished_blackstone"))
    dk.chest(w, kx0 + 4, gy + 1, AX, "E", 4, rng, extra=[bl.item("diamond", 4)])
    dk.chest(w, kx1 - 4, gy + 1, kz1 - 4, "W", 4, rng, extra=[bl.item("golden_carrot", 12)])
    # chandeliers of chains + lanterns over the pit
    for (dx, dz) in ((-5, -5), (5, -5), (-5, 5), (5, 5), (0, 0)):
        top = NF + H - 2
        n = 8 if (dx, dz) != (0, 0) else 12
        for i in range(n):
            w.set(cx + dx, top - i, cz + dz, B("chain", pillar_axis="y"))
        w.set(cx + dx, top - n, cz + dz, bl.lantern(True))
    for dz in (-12, 12):
        w.put(kx0 + 3, NF + 16, cz + dz, bl.wall_banner("E"), bl.be_banner(11))
        w.put(kx0 + 3, NF + 16, cz + dz + 1, bl.wall_banner("E"), bl.be_banner(0))
    # boss plates at the door
    for dz in (-1, 0, 1):
        dk.plate(w, kx1 - 4, NF + 1, AX + dz, "function bear/boss/bastion", kind="polished_blackstone_pressure_plate",
                 floor=GILD)
    # ---- vault on the west side of the keep ---------------------------------------------------------------------
    vx0, vx1 = kx0 - 12, kx0 - 1
    w.fill(vx0 - 1, NF - 3, AX - 7, vx1, NF + 8, AX + 7, wm)
    w.fill(vx0, NF + 1, AX - 6, vx1 - 1, NF + 6, AX + 6, AIR)
    w.fill(kx0 - 1, NF + 1, AX - 1, kx0 + 3, NF + 4, AX + 1, AIR)
    for x in range(vx0, vx1):
        for z in range(AX - 6, AX + 7):
            w.set(x, NF, z, GOLD if (x + z) % 4 == 0 else GILD if (x + z) % 2 else B("polished_blackstone"))
    dk.reward_altar(w, vx0, NF + 1, AX, "E", "bastion", "피글린 요새 보상")
    dk.chest(w, vx0 + 2, NF + 1, AX - 6, "S", 4, rng, extra=[bl.item("netherite_ingot", 1), bl.item("gold_block", 6)])
    dk.chest(w, vx0 + 6, NF + 1, AX - 6, "S", 4, rng, extra=[bl.item("diamond", 6)])
    dk.chest(w, vx0 + 2, NF + 1, AX + 6, "N", 4, rng, extra=[bl.item("ancient_debris", 2)])
    dk.exit_pad(w, vx0 + 7, NF + 1, AX + 4, None)
    for (x, z) in ((vx0, AX - 6), (vx0, AX + 6)):
        w.fill(x, NF + 1, z, x, NF + 3, z, GOLD)
        w.set(x, NF + 4, z, bl.lantern())
    w.set(vx0 + 5, NF + 6, AX, bl.lantern(True))
    dk.warp("bastion", 1, -100.5, NF + 1, AX + 0.5, (-124, NF + 6, AX))
    bx, by, bz = cx + pit + 4, NF + 1, cz
    dk.boss("bastion", {
        "pos": (kx1 - 4, NF + 1, AX),
        "spawn": [
            'summon piglin_brute "§6피글린 족장" %d %d %d' % (bx, by, bz),
            "tag @e[type=piglin_brute,x=%d,y=%d,z=%d,r=3,c=1] add boss_bastion" % (bx, by, bz),
            "replaceitem entity @e[tag=boss_bastion] slot.armor.head 0 golden_helmet",
            "replaceitem entity @e[tag=boss_bastion] slot.armor.chest 0 netherite_chestplate",
            "effect @e[tag=boss_bastion] health_boost 99999 29 true",
            "effect @e[tag=boss_bastion] instant_health 1 7 true",
            "effect @e[tag=boss_bastion] strength 99999 1 true",
            "effect @e[tag=boss_bastion] resistance 99999 1 true",
            "effect @e[tag=boss_bastion] fire_resistance 99999 0 true",
            "summon piglin_brute %d %d %d" % (bx - 2, by, bz - 8),
            "summon piglin_brute %d %d %d" % (bx - 2, by, bz + 8),
            "summon piglin_brute %d %d %d" % (cx - pit - 4, by, bz),
            "summon piglin %d %d %d" % (bx, by, bz - 12),
            "summon piglin %d %d %d" % (bx, by, bz + 12),
        ],
        "title": "§6피글린 족장", "sub": "§7황금 보루의 지배자",
    })
