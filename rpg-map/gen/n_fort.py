"""Nether Fortress 'Citadel of the Wither' standing on pillars in a lava sea."""
from . import blocks as bl
from . import dkit as dk
from . import kit
from .core import B, Mix
from .kit import Frame
from .nether import LAVA_Y, NF, nb_mix

AIR = 0
AX = 64                     # fortress main axis (z)


def pier(w, x, z, top, r=1):
    """Support pier from `top` down into the lava sea floor."""
    nb = nb_mix()
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            for y in range(top, 18, -1):
                if w.get(x + dx, y, z + dz) not in (0, bl.LAVA):
                    break
                w.set(x + dx, y, z + dz, nb)
    for dx in range(-r - 1, r + 2):
        for dz in range(-r - 1, r + 2):
            if max(abs(dx), abs(dz)) == r + 1 and w.get(x + dx, top, z + dz) in (0, bl.LAVA):
                d = "E" if dx == -r - 1 else "W" if dx == r + 1 else "S" if dz == -r - 1 else "N"
                w.set(x + dx, top, z + dz, bl.stairs("nether_brick", d, top=True))


def bridge(w, x0, x1, z0, z1, piers=True):
    """Open bridge deck with fence rails; runs along the longer side."""
    nb = nb_mix()
    w.fill(x0, NF - 1, z0, x1, NF, z1, nb)
    w.fill(x0, NF + 1, z0, x1, NF + 8, z1, AIR)
    along_x = (x1 - x0) >= (z1 - z0)
    if along_x:
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                w.set(x, NF + 1, z, nb if (x - x0) % 4 == 0 else bl.fence("nether_brick"))
                if (x - x0) % 8 == 0:
                    w.set(x, NF + 2, z, bl.fence("nether_brick"))
                    w.set(x, NF + 3, z, bl.lantern(soul=True)) if (x - x0) % 16 == 0 else None
            if piers and (x - x0) % 10 == 5:
                pier(w, x, (z0 + z1) // 2, NF - 2)
            w.set(x, NF - 2, z0, bl.stairs("nether_brick", "S", top=True), keep=True)
            w.set(x, NF - 2, z1, bl.stairs("nether_brick", "N", top=True), keep=True)
    else:
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                w.set(x, NF + 1, z, nb if (z - z0) % 4 == 0 else bl.fence("nether_brick"))
                if (z - z0) % 8 == 0:
                    w.set(x, NF + 2, z, bl.fence("nether_brick"))
            if piers and (z - z0) % 10 == 5:
                pier(w, (x0 + x1) // 2, z, NF - 2)


def corridor(w, x0, x1, z0, z1):
    """Covered fortress corridor (5 wide outside) with fence windows."""
    nb = nb_mix()
    along_x = (x1 - x0) >= (z1 - z0)
    w.fill(x0, NF - 1, z0, x1, NF + 5, z1, nb)
    if along_x:
        w.fill(x0, NF + 1, z0 + 1, x1, NF + 4, z1 - 1, AIR)
        for x in range(x0, x1 + 1):
            if (x - x0) % 3 == 1:
                for z in (z0, z1):
                    w.set(x, NF + 2, z, bl.fence("nether_brick"))
                    w.set(x, NF + 3, z, bl.fence("nether_brick"))
            if (x - x0) % 9 == 4:
                pier(w, x, (z0 + z1) // 2, NF - 2)
            w.set(x, NF + 6, (z0 + z1) // 2, bl.slab("nether_brick"))
            w.set(x, NF + 4, z0 + 1, bl.stairs("nether_brick", "N", top=True))
            w.set(x, NF + 4, z1 - 1, bl.stairs("nether_brick", "S", top=True))
    else:
        w.fill(x0 + 1, NF + 1, z0, x1 - 1, NF + 4, z1, AIR)
        for z in range(z0, z1 + 1):
            if (z - z0) % 3 == 1:
                for x in (x0, x1):
                    w.set(x, NF + 2, z, bl.fence("nether_brick"))
                    w.set(x, NF + 3, z, bl.fence("nether_brick"))
            if (z - z0) % 9 == 4:
                pier(w, (x0 + x1) // 2, z, NF - 2)
            w.set((x0 + x1) // 2, NF + 6, z, bl.slab("nether_brick"))
            w.set(x0 + 1, NF + 4, z, bl.stairs("nether_brick", "W", top=True))
            w.set(x1 - 1, NF + 4, z, bl.stairs("nether_brick", "E", top=True))


def blaze_platform(w, x, y, z):
    nb = nb_mix()
    w.fill(x - 2, y, z - 2, x + 2, y, z + 2, nb)
    w.fill(x - 2, y + 1, z - 2, x + 2, y + 5, z + 2, AIR)
    w.set(x, y + 1, z, B("chiseled_nether_bricks"))
    dk.spawner(w, x, y + 2, z, "blaze", count=2, delay_min=200, delay_max=500)
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        w.set(x + dx, y + 1, z + dz, bl.fence("nether_brick"))
        w.set(x + dx, y + 2, z + dz, bl.fence("nether_brick"))
    for d, (dx, dz) in (("E", (-1, 0)), ("W", (1, 0)), ("S", (0, -1)), ("N", (0, 1))):
        w.set(x + dx, y + 1, z + dz, bl.stairs("nether_brick", d))


def tower(w, cx, cz, half=4, height=14):
    nb = nb_mix()
    x0, x1, z0, z1 = cx - half, cx + half, cz - half, cz + half
    for dx in (-half + 1, half - 1):
        for dz in (-half + 1, half - 1):
            pier(w, cx + dx, cz + dz, NF - 1, r=1)
    w.fill(x0, NF - 2, z0, x1, NF + height, z1, nb)
    w.fill(x0 + 1, NF + 1, z0 + 1, x1 - 1, NF + height - 1, z1 - 1, AIR)
    w.fill(x0 + 1, NF + 7, z0 + 1, x1 - 1, NF + 7, z1 - 1, nb)
    for y in range(NF + 1, NF + height):
        w.set(x0 + 1, y, z0 + 1, bl.ladder("E"))
    w.set(x0 + 1, NF + 7, z0 + 1, bl.ladder("E"))
    w.set(x0 + 1, NF + height, z0 + 1, bl.ladder("E"))
    for t in range(-half, half + 1):
        for (x, z) in ((cx + t, z0), (cx + t, z1), (x0, cz + t), (x1, cz + t)):
            if abs(t) in (0, 2) and abs(t) < half:
                for y in (NF + 3, NF + 4, NF + 10, NF + 11):
                    w.set(x, y, z, bl.fence("nether_brick"))
            w.set(x, NF + height + 1, z, nb if t % 2 == 0 else bl.fence("nether_brick"))
    blaze_platform(w, cx, NF + height, cz)
    w.set(x0 + 1, NF + height + 1, z0 + 1, AIR)
    return (x0, x1, z0, z1)


def build(w, log=print):
    rng = w.rng
    nb = nb_mix()
    red = B("red_nether_brick")
    # ---- approach bridge + gatehouse ----------------------------------------------------
    bridge(w, 84, 117, AX - 3, AX + 3)
    gx0, gx1 = 118, 128
    for sgn in (-1, 1):
        zc = AX + sgn * 6
        w.fill(gx0, NF - 2, zc - 3, gx1, NF + 13, zc + 3, nb)
        w.fill(gx0 + 1, NF + 1, zc - 2, gx1 - 1, NF + 12, zc + 2, AIR)
        w.fill(gx0 + 1, NF + 7, zc - 2, gx1 - 1, NF + 7, zc + 2, nb)
        pier(w, gx0 + 5, zc, NF - 3, r=2)
        for x in range(gx0, gx1 + 1, 2):
            w.set(x, NF + 14, zc - 3, nb)
            w.set(x, NF + 14, zc + 3, nb)
        for y in (NF + 4, NF + 5, NF + 10, NF + 11):
            w.set(gx0, y, zc, bl.fence("nether_brick"))
            w.set(gx1, y, zc, bl.fence("nether_brick"))
        w.put(gx0 - 1, NF + 9, zc, bl.wall_banner("W"), bl.be_banner(0))
        w.set(gx0 - 1, NF + 4, zc - sgn * 2, bl.torch("E", "soul_torch"))
    w.fill(gx0, NF - 2, AX - 2, gx1, NF, AX + 2, nb)
    w.fill(gx0, NF + 6, AX - 2, gx1, NF + 9, AX + 2, nb)
    w.fill(gx0, NF + 1, AX - 2, gx1, NF + 5, AX + 2, AIR)
    for x in range(gx0, gx1 + 1):
        w.set(x, NF + 5, AX - 2, bl.stairs("nether_brick", "N", top=True))
        w.set(x, NF + 5, AX + 2, bl.stairs("nether_brick", "S", top=True))
        w.set(x, NF + 10, AX - 2, nb) if x % 2 == 0 else None
        w.set(x, NF + 10, AX + 2, nb) if x % 2 == 0 else None
    for z in (AX - 1, AX, AX + 1):
        w.set(gx0 + 1, NF + 5, z, B("iron_bars"))
    dk.sign(w, gx0 - 1, NF + 7, AX, "W", "§4§l네더 요새\n§r위더의 성채\n§8권장 다이아 장비", wood="crimson", glow=True)
    dk.plate(w, gx0 + 5, NF + 1, AX, "function bear/enter/fortress", kind="polished_blackstone_pressure_plate",
             floor=B("chiseled_nether_bricks"))
    bridge(w, gx1 + 1, 141, AX - 3, AX + 3)
    # ---- central keep --------------------------------------------------------------------------
    kx0, kx1, kz0, kz1 = 142, 178, AX - 18, AX + 18
    for x in range(kx0 + 4, kx1, 14):
        for z in range(kz0 + 4, kz1, 14):
            pier(w, x, z, NF - 3, r=2)
    w.fill(kx0, NF - 4, kz0, kx1, NF, kz1, nb)
    w.fill(kx0, NF + 1, kz0, kx1, NF + 15, kz1, nb)
    w.fill(kx0 + 1, NF + 1, kz0 + 1, kx1 - 1, NF + 7, kz1 - 1, AIR)        # ground hall
    w.fill(kx0 + 1, NF + 9, kz0 + 1, kx1 - 1, NF + 14, kz1 - 1, AIR)       # upper floor
    cx = (kx0 + kx1) // 2
    for z in (AX - 1, AX, AX + 1):                                         # four doorways
        for y in range(NF + 1, NF + 5):
            w.set(kx0, y, z, AIR)
            w.set(kx1, y, z, AIR)
    for x in (cx - 1, cx, cx + 1):
        for y in range(NF + 1, NF + 5):
            w.set(x, y, kz0, AIR)
            w.set(x, y, kz1, AIR)
    # hall pillars + red carpet lines
    for x in range(kx0 + 6, kx1 - 3, 6):
        for z in range(kz0 + 6, kz1 - 3, 6):
            if abs(x - cx) > 2 and abs(z - AX) > 2:
                dk.pillar(w, x, NF + 1, NF + 7, z, "nether_brick", body=red)
    for x in range(kx0 + 1, kx1):
        w.set(x, NF, AX, red)
    for z in range(kz0 + 1, kz1):
        w.set(cx, NF, z, red)
    w.fill(cx - 2, NF, AX - 2, cx + 2, NF, AX + 2, B("chiseled_nether_bricks"))
    dk.spawner(w, cx, NF + 1, AX, "wither_skeleton", max_nearby=5)
    # windows
    for t in range(4, 33, 4):
        for (x, z) in ((kx0 + t, kz0), (kx0 + t, kz1), (kx0, kz0 + t), (kx1, kz0 + t)):
            if abs(x - cx) < 3 or abs(z - AX) < 3:
                continue
            for y in (NF + 3, NF + 4, NF + 11, NF + 12):
                w.set(x, y, z, bl.fence("nether_brick"))
    # stair to the upper floor (north-west corner) and roof
    for i in range(8):
        x = kx0 + 2 + i
        w.set(x, NF + 1 + i, kz0 + 2, bl.stairs("nether_brick", "E"))
        w.set(x, NF + 1 + i, kz0 + 3, bl.stairs("nether_brick", "E"))
        w.fill(x, NF + 1, kz0 + 2, x, NF + i, kz0 + 3, nb) if i > 0 else None
        w.fill(x, NF + 2 + i, kz0 + 2, x, NF + 11, kz0 + 3, AIR)
    for i in range(7):
        x = kx1 - 2 - i
        w.set(x, NF + 9 + i, kz1 - 2, bl.stairs("nether_brick", "W"))
        w.fill(x, NF + 9, kz1 - 2, x, NF + 8 + i, kz1 - 2, nb) if i > 0 else None
        w.fill(x, NF + 10 + i, kz1 - 2, x, NF + 18, kz1 - 2, AIR)
    # upper floor: nether wart garden + rooms
    w.fill(cx - 5, NF + 8, AX - 5, cx + 5, NF + 8, AX + 5, B("soul_sand"))
    for x in range(cx - 5, cx + 6):
        for z in range(AX - 5, AX + 6):
            if (x - cx) % 3 != 0:
                w.set(x, NF + 9, z, B("nether_wart", age=int(rng.integers(1, 4))))
    for (x, z) in ((cx - 6, AX - 6), (cx + 6, AX - 6), (cx - 6, AX + 6), (cx + 6, AX + 6)):
        dk.pillar(w, x, NF + 9, NF + 14, z, "nether_brick", body=red)
    dk.spawner(w, kx0 + 6, NF + 9, kz1 - 6, "wither_skeleton", max_nearby=5)
    dk.chest(w, kx1 - 2, NF + 9, kz0 + 2, "W", 4, rng)
    dk.chest(w, kx0 + 2, NF + 9, kz1 - 12, "E", 3, rng, extra=[bl.item("nether_wart", 12)])
    dk.chest(w, kx1 - 2, NF + 1, kz1 - 2, "W", 3, rng)
    w.set(cx, NF + 14, AX, bl.lantern(True, soul=True))
    # roof battlements + two blaze turrets
    for t in range(0, kx1 - kx0 + 1):
        for (x, z) in ((kx0 + t, kz0), (kx0 + t, kz1), (kx0, kz0 + t), (kx1, kz0 + t)):
            w.set(x, NF + 16, z, nb)
            if t % 2 == 0:
                w.set(x, NF + 17, z, nb)
    blaze_platform(w, kx0 + 6, NF + 15, kz0 + 6)
    blaze_platform(w, kx1 - 6, NF + 15, kz1 - 6)
    for (x, z) in ((kx0, kz0), (kx1, kz0), (kx0, kz1), (kx1, kz1)):
        w.fill(x - 1, NF + 1, z - 1, x + 1, NF + 20, z + 1, nb)
        w.set(x, NF + 21, z, B("netherrack"))
        w.set(x, NF + 22, z, B("fire", age=0))
    # ---- north / south arms with blaze towers ---------------------------------------------------------
    corridor(w, cx - 2, cx + 2, 26, kz0 - 1)
    tower(w, cx, 21)
    for y in range(NF + 1, NF + 5):
        for x in (cx - 1, cx, cx + 1):
            w.set(x, y, 25, AIR)
    corridor(w, cx - 2, cx + 2, kz1 + 1, 102)
    tower(w, cx, 107)
    for y in range(NF + 1, NF + 5):
        for x in (cx - 1, cx, cx + 1):
            w.set(x, y, 103, AIR)
    dk.chest(w, cx + 3, NF + 1, 18, "W", 4, rng, extra=[bl.item("blaze_rod", 4)])
    dk.chest(w, cx + 3, NF + 1, 110, "W", 4, rng, extra=[bl.item("diamond", 3)])
    # ---- east wing: hall of the Wither lord ------------------------------------------------------------
    corridor(w, kx1 + 1, 196, AX - 2, AX + 2)
    hx0, hx1, hz0, hz1 = 197, 236, AX - 12, AX + 12
    for x in range(hx0 + 5, hx1, 10):
        for z in (hz0 + 4, hz1 - 4):
            pier(w, x, z, NF - 3, r=2)
    w.fill(hx0, NF - 4, hz0, hx1, NF + 14, hz1, nb)
    w.fill(hx0 + 1, NF + 1, hz0 + 1, hx1 - 1, NF + 12, hz1 - 1, AIR)
    for y in range(NF + 1, NF + 5):
        for z in (AX - 1, AX, AX + 1):
            w.set(hx0, y, z, AIR)
    for x in range(hx0 + 4, hx1 - 3, 5):
        for z in (hz0 + 4, hz1 - 4):
            dk.pillar(w, x, NF + 1, NF + 12, z, "nether_brick", body=red)
            w.set(x, NF + 6, z, B("chiseled_nether_bricks"))
        # lava troughs behind the pillars
        for z in (hz0 + 1, hz1 - 1):
            for xx in range(x - 1, x + 2):
                w.set(xx, NF, z, bl.LAVA)
                w.set(xx, NF - 1, z, nb)
        for z in (hz0, hz1):
            for y in (NF + 6, NF + 7, NF + 8):
                w.set(x + 2, y, z, B("red_stained_glass"))
    for x in range(hx0 + 1, hx1):
        for z in (AX - 1, AX, AX + 1):
            w.set(x, NF, z, red)
        w.set(x, NF + 12, hz0 + 1, bl.stairs("nether_brick", "N", top=True))
        w.set(x, NF + 12, hz1 - 1, bl.stairs("nether_brick", "S", top=True))
    # throne dais
    w.fill(hx1 - 7, NF + 1, AX - 5, hx1 - 1, NF + 1, AX + 5, red)
    w.fill(hx1 - 4, NF + 2, AX - 3, hx1 - 1, NF + 2, AX + 3, nb)
    for z in range(AX - 5, AX + 6):
        w.set(hx1 - 8, NF + 1, z, bl.stairs("red_nether_brick", "E"))
    for z in range(AX - 3, AX + 4):
        w.set(hx1 - 5, NF + 2, z, bl.stairs("nether_brick", "E"))
    w.set(hx1 - 2, NF + 3, AX, bl.stairs("nether_brick", "W"))
    for z in (AX - 1, AX + 1):
        w.set(hx1 - 2, NF + 3, z, B("chiseled_nether_bricks"))
        w.set(hx1 - 2, NF + 4, z, B("gold_block"))
    w.fill(hx1 - 1, NF + 3, AX - 1, hx1 - 1, NF + 7, AX + 1, B("chiseled_nether_bricks"))
    dk.skull(w, hx1 - 1, NF + 8, AX, 1, 90.0)
    for z in (AX - 4, AX + 4):
        dk.brazier(w, hx1 - 3, NF + 3, z, soul=True, base="polished_blackstone")
        w.put(hx1 - 1, NF + 8, z, bl.wall_banner("W"), bl.be_banner(0))
    for z in (AX - 9, AX + 9):
        dk.brazier(w, hx0 + 2, NF + 1, z, soul=True, base="polished_blackstone")
    for z in (AX - 1, AX, AX + 1):
        dk.plate(w, hx0 + 2, NF + 1, z, "function bear/boss/fortress", kind="polished_blackstone_pressure_plate",
                 floor=B("chiseled_nether_bricks"))
    dk.sign(w, 190, NF + 3, AX - 1, "S", "§4§l위더 군주의 전당", wood="crimson", glow=True) if False else None
    # vault behind the throne (door on the south side of the dais wall)
    vx0, vx1, vz0, vz1 = hx1 + 1, hx1 + 10, AX - 6, AX + 6
    w.fill(vx0, NF - 4, vz0 - 1, vx1 + 1, NF + 8, vz1 + 1, nb)
    w.fill(vx0 + 1, NF + 1, vz0, vx1, NF + 6, vz1, AIR)
    pier(w, vx0 + 5, AX, NF - 5, r=2)
    for y in range(NF + 1, NF + 4):
        w.set(hx1, y, AX + 9, AIR)
        w.set(hx1 + 1, y, AX + 9, AIR) if False else None
    w.fill(hx1, NF + 1, AX + 8, vx0, NF + 3, AX + 9, AIR)
    w.fill(vx0, NF + 1, AX + 6, vx0 + 1, NF + 3, AX + 9, AIR)
    w.fill(vx0 - 1, NF, AX + 7, vx0 + 1, NF, AX + 10, nb)
    w.fill(vx0, NF + 4, AX + 7, vx0 + 1, NF + 4, AX + 10, nb)
    w.fill(vx0 + 2, NF, AX + 7, vx0 + 2, NF + 4, AX + 10, nb) if False else None
    w.fill(hx1, NF + 1, AX + 10, vx0 + 1, NF + 4, AX + 10, nb)
    for x in range(vx0 + 1, vx1 + 1):
        for z in range(vz0, vz1 + 1):
            w.set(x, NF, z, B("gold_block") if (x + z) % 6 == 0 else red if (x + z) % 2 else nb)
    dk.reward_altar(w, vx1, NF + 1, AX, "W", "fortress", "네더 요새 보상")
    dk.chest(w, vx0 + 2, NF + 1, vz0, "S", 4, rng, extra=[bl.item("netherite_scrap", 2), bl.item("diamond", 5)])
    dk.chest(w, vx0 + 5, NF + 1, vz0, "S", 4, rng)
    dk.exit_pad(w, vx1 - 2, NF + 1, vz0 + 3, None)
    # optional final challenge: the Wither
    dk.button(w, vx1 - 4, NF + 2, vz1, "N", "function bear/boss/wither", B("soul_sand"), kind="polished_blackstone_button")
    w.set(vx1 - 4, NF + 1, vz1, B("soul_sand"))
    w.set(vx1 - 5, NF + 2, vz1, B("soul_sand"))
    w.set(vx1 - 3, NF + 2, vz1, B("soul_sand"))
    for dx, kind in ((-5, 1), (-3, 1)):
        dk.skull(w, vx1 + dx, NF + 3, vz1, 1, 0.0)
    dk.sign(w, vx1 - 6, NF + 2, vz1 - 1, "N", "§4§l최종 도전\n§r버튼을 누르면\n§c위더§r가 전당에\n소환됩니다!", wood="crimson", glow=True)
    w.set(vx1 - 6, NF + 2, vz1, nb)
    w.set(vx0 + 3, NF + 6, AX, bl.lantern(True, soul=True))
    w.set(vx1 - 2, NF + 6, AX, bl.lantern(True, soul=True))
    dk.warp("fortress", 1, 100.5, NF + 1, AX + 0.5, (140, NF + 4, AX))
    bx, by, bz = hx1 - 12, NF + 1, AX
    dk.boss("fortress", {
        "pos": (hx0 + 2, NF + 1, AX),
        "spawn": [
            'summon wither_skeleton "§4위더 군주" %d %d %d' % (bx, by, bz),
            "tag @e[type=wither_skeleton,x=%d,y=%d,z=%d,r=3,c=1] add boss_fortress" % (bx, by, bz),
            "replaceitem entity @e[tag=boss_fortress] slot.armor.head 0 netherite_helmet",
            "replaceitem entity @e[tag=boss_fortress] slot.armor.chest 0 netherite_chestplate",
            "replaceitem entity @e[tag=boss_fortress] slot.armor.legs 0 netherite_leggings",
            "replaceitem entity @e[tag=boss_fortress] slot.armor.feet 0 netherite_boots",
            "replaceitem entity @e[tag=boss_fortress] slot.weapon.mainhand 0 netherite_sword",
            "effect @e[tag=boss_fortress] health_boost 99999 24 true",
            "effect @e[tag=boss_fortress] instant_damage 1 6 true",
            "effect @e[tag=boss_fortress] strength 99999 1 true",
            "effect @e[tag=boss_fortress] speed 99999 0 true",
            "summon wither_skeleton %d %d %d" % (bx - 4, by, bz - 6),
            "summon wither_skeleton %d %d %d" % (bx - 4, by, bz + 6),
            "summon wither_skeleton %d %d %d" % (bx - 10, by, bz - 4),
            "summon wither_skeleton %d %d %d" % (bx - 10, by, bz + 4),
            "summon blaze %d %d %d" % (bx - 6, by + 5, bz - 3),
            "summon blaze %d %d %d" % (bx - 6, by + 5, bz + 3),
        ],
        "title": "§4위더 군주", "sub": "§7네더 요새의 지배자",
    })
    dk.REG["wither_pos"] = (hx0 + 18, NF + 4, AX)
