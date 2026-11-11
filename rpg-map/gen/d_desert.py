"""Desert dungeon: Pyramid of the Sun King."""
import math

from . import blocks as bl
from . import dkit as dk
from . import kit
from .core import B, Mix
from .kit import Frame
from .layout import PYRAMID, PYR_G

AIR = 0


def ss_mix():
    return Mix((bl.block("sandstone"), 8), (bl.block("smooth_sandstone"), 4), (bl.block("cut_sandstone"), 3))


def inner_mix():
    return Mix((bl.block("cut_sandstone"), 6), (bl.block("smooth_sandstone"), 4), (bl.block("sandstone"), 3),
               (B("sandstone", sand_stone_type="heiroglyphs"), 1))


HIERO = B("sandstone", sand_stone_type="heiroglyphs")


def obelisk(w, x, y, z, h=8):
    w.fill(x - 1, y, z - 1, x + 1, y, z + 1, bl.block("smooth_sandstone"))
    for d, (dx, dz) in (("E", (-1, 0)), ("W", (1, 0)), ("S", (0, -1)), ("N", (0, 1))):
        w.set(x + dx, y + 1, z + dz, bl.stairs("sandstone", d))
    for i in range(1, h):
        w.set(x, y + i, z, HIERO if i % 3 == 1 else bl.block("cut_sandstone"))
    w.set(x, y + h, z, B("gold_block"))
    w.set(x, y + h + 1, z, B("lightning_rod", facing_direction=1))


def sphinx(F, x, y, z):
    """Lion-bodied statue facing local west (toward the road); (x,z) = centre of the body."""
    s = bl.block("smooth_sandstone")
    c = bl.block("cut_sandstone")
    F.fill(x - 4, y, z - 2, x + 5, y, z + 2, bl.block("sandstone"))
    F.fill(x - 3, y + 1, z - 1, x + 4, y + 3, z + 1, s)
    F.fill(x + 3, y + 4, z - 1, x + 4, y + 4, z + 1, s)
    for dz in (-2, 2):                       # legs
        F.fill(x + 1, y + 1, z + dz, x + 4, y + 2, z + dz, c)
        F.fill(x - 6, y + 1, z + (1 if dz > 0 else -1), x - 4, y + 1, z + (1 if dz > 0 else -1), c)
        F.stairs(x - 7, y + 1, z + (1 if dz > 0 else -1), "sandstone", "E")
    # head with striped nemes
    F.fill(x - 5, y + 2, z - 1, x - 3, y + 5, z + 1, s)
    F.fill(x - 4, y + 4, z - 2, x - 3, y + 6, z + 2, B("gold_block"))
    for yy in (y + 4, y + 6):
        F.fill(x - 4, yy, z - 2, x - 3, yy, z + 2, B("lapis_block"))
    F.fill(x - 5, y + 6, z - 1, x - 3, y + 6, z + 1, B("gold_block"))
    F.fill(x - 5, y + 3, z - 1, x - 5, y + 5, z + 1, s)
    F.set(x - 6, y + 4, z, bl.block("cut_sandstone"))
    F.set(x - 5, y + 5, z - 1, B("black_concrete"))
    F.set(x - 5, y + 5, z + 1, B("black_concrete"))
    F.set(x - 6, y + 2, z, B("gold_block"))
    F.stairs(x + 5, y + 1, z, "sandstone", "W")


def pot(w, x, y, z):
    w.put(x, y, z, bl.pot("N"), {"id": "DecoratedPot"})


def build(w, T, log=print):
    rng = w.rng
    cx, cz = PYRAMID
    g = PYR_G
    half = 30
    F = Frame(w, 0, 0, 0, 0)
    xi, zi = cx - 62 - w.x0, cz - 52 - w.z0
    T.reserved[max(0, xi):xi + 110, max(0, zi):zi + 104] = True
    ss, inner = ss_mix(), inner_mix()
    # --- pyramid shell --------------------------------------------------------
    w.fill(cx - half - 2, g - 3, cz - half - 2, cx + half + 2, g, cz + half + 2, bl.block("sandstone"))
    for i in range(half + 1):
        r = half - i
        y = g + 1 + i
        band = bl.block("smooth_sandstone") if i % 6 == 5 else None
        if r == 0:
            w.set(cx, y, cz, B("gold_block"))
            break
        w.fill(cx - r, y, cz - r, cx + r, y, cz + r, B("gold_block") if i >= half - 2 else (band or ss))
        cap = "sandstone" if i < half - 2 else None
        if cap:
            for t in range(-r, r + 1):
                w.set(cx + t, y, cz - r, bl.stairs("smooth_sandstone" if i % 6 == 5 else "sandstone", "S"))
                w.set(cx + t, y, cz + r, bl.stairs("smooth_sandstone" if i % 6 == 5 else "sandstone", "N"))
                w.set(cx - r, y, cz + t, bl.stairs("smooth_sandstone" if i % 6 == 5 else "sandstone", "E"))
                w.set(cx + r, y, cz + t, bl.stairs("smooth_sandstone" if i % 6 == 5 else "sandstone", "W"))
    w.set(cx, g + half + 2, cz, B("lightning_rod", facing_direction=1))
    # plaza around the base
    plaza = Mix((bl.block("smooth_sandstone"), 5), (bl.block("sandstone"), 4), (bl.block("cut_sandstone"), 3),
                (B("sand"), 2))
    for x in range(cx - half - 8, cx + half + 9):
        for z in range(cz - half - 8, cz + half + 9):
            if max(abs(x - cx), abs(z - cz)) > half:
                w.set(x, g, z, plaza)
                w.fill(x, g + 1, z, x, g + 12, z, AIR)
    # --- entrance pylon (west face) --------------------------------------------
    wx = cx - half
    for sz in (-1, 1):
        z0, z1 = sorted((cz + sz * 2, cz + sz * 8))
        w.fill(wx - 5, g + 1, z0, wx + 2, g + 11, z1, ss)
        w.fill(wx - 5, g + 12, z0, wx + 2, g + 12, z1, bl.block("cut_sandstone"))
        for z in range(z0 - 1, z1 + 2):
            w.set(wx - 6, g + 12, z, bl.stairs("sandstone", "E", top=True))
        for x in range(wx - 5, wx + 3):
            w.set(x, g + 12, z0 - 1 if sz < 0 else z1 + 1, bl.stairs("sandstone", "S" if sz < 0 else "N", top=True))
        w.fill(wx - 5, g + 13, z0, wx + 1, g + 13, z1, bl.block("smooth_sandstone"))
        for z in range(z0, z1 + 1, 2):
            w.set(wx - 5, g + 14, z, bl.block("cut_sandstone"))
        for y in (g + 4, g + 8):
            for z in range(z0 + 1, z1, 2):
                w.set(wx - 5, y, z, HIERO)
        w.fill(wx - 5, g + 6, z0, wx - 5, g + 6, z1, B("orange_terracotta"))
        w.fill(wx - 5, g + 10, z0, wx - 5, g + 10, z1, B("blue_terracotta"))
        w.put(wx - 6, g + 9, (z0 + z1) // 2, bl.wall_banner("W"), bl.be_banner(11))
        w.set(wx - 6, g + 3, cz + sz * 2, bl.torch("E"))
    w.fill(wx - 5, g + 6, cz - 1, wx + 2, g + 9, cz + 1, ss)
    w.fill(wx - 5, g + 6, cz - 1, wx - 5, g + 6, cz + 1, B("gold_block"))
    w.set(wx - 5, g + 8, cz, B("gold_block"))
    w.fill(wx - 5, g + 1, cz - 1, wx + 2, g + 5, cz + 1, AIR)
    w.set(wx - 5, g + 5, cz - 1, bl.stairs("sandstone", "N", top=True))
    w.set(wx - 5, g + 5, cz + 1, bl.stairs("sandstone", "S", top=True))
    dk.sign(w, wx - 6, g + 3, cz - 2, "W", "§6§l사막 던전\n§r태양왕의 피라미드\n§8권장: 철 장비, 활", glow=True)
    # --- avenue with obelisks + sphinxes -------------------------------------------
    for x in range(wx - 34, wx - 5):
        for z in range(cz - 3, cz + 4):
            w.set(x, g, z, bl.block("cut_sandstone") if abs(z - cz) == 3 else plaza)
            w.fill(x, g + 1, z, x, g + 14, z, AIR)
    for x in range(wx - 32, wx - 8, 8):
        obelisk(w, x, g + 1, cz - 6)
        obelisk(w, x, g + 1, cz + 6)
    sphinx(F, wx - 12, g + 1, cz - 13)
    sphinx(F, wx - 12, g + 1, cz + 13)
    # broken columns + pots around the plaza
    for _ in range(26):
        x, z = cx + int(rng.integers(-half - 7, half + 8)), cz + int(rng.integers(-half - 7, half + 8))
        if max(abs(x - cx), abs(z - cz)) > half + 2 and not (x < wx and abs(z - cz) < 18):
            hh = int(rng.integers(1, 5))
            for i in range(hh):
                w.set(x, g + 1 + i, z, B("quartz_block", chisel_type="lines", pillar_axis="y") if False else bl.block(
                    "cut_sandstone") if i % 2 else bl.block("smooth_sandstone"))
            if rng.random() < 0.4:
                w.set(x, g + 1 + hh, z, bl.slab("sandstone"))
    # --- oasis north-west ----------------------------------------------------------------
    ox, oz = wx - 20, cz - 34
    for (dx, dz) in kit.disc_cells(11.5):
        d = math.hypot(dx, dz * 1.15)
        x, z = ox + dx, oz + dz
        top = w.top(x, z)
        if top is None:
            continue
        if d <= 6:
            w.fill(x, g - 2, z, x, top, z, AIR)
            w.set(x, g - 3, z, B("clay") if rng.random() < 0.4 else B("sand"))
            w.fill(x, g - 2, z, x, g - 1, z, bl.WATER)
            if d > 4.5:
                w.set(x, g - 2, z, B("sand"))
            if rng.random() < 0.08:
                w.set(x, g, z, B("waterlily"))
        elif d <= 11.5:
            w.fill(x, g, z, x, top + 3, z, AIR)
            w.set(x, g - 1, z, B("grass_block"))
            w.set(x, g - 2, z, B("dirt"))
            r_ = rng.random()
            if d < 7.2 and r_ < 0.4:
                for i in range(int(rng.integers(1, 4))):
                    w.set(x, g + i, z, B("reeds", age=0))
            elif r_ < 0.3:
                w.set(x, g, z, B("short_grass"))
            elif r_ < 0.36:
                w.set(x, g, z, kit.flowers(rng, ["poppy", "yellow_flower", "blue_orchid", "allium"]))
    for k in range(7):
        a = k * 0.9 + 0.3
        kit.tree_palm(w, ox + int(9 * math.cos(a)), g, oz + int(8 * math.sin(a)), rng)
    for k in range(5):
        kit.tree_palm(w, wx - 30 + k * 6, g + 1, cz + 22 + int(rng.integers(-3, 4)), rng)
    # --- interior --------------------------------------------------------------------------
    LY = g - 10               # lower level floor
    KY = g + 10               # king's chamber floor
    P = dk.Plan(w, inner, floor=Mix((bl.block("smooth_sandstone"), 4), (bl.block("cut_sandstone"), 3),
                                    (bl.block("sandstone"), 2)))
    P.room(wx + 3, g + 1, cz - 1, wx + 15, g + 4, cz + 1)                    # entrance corridor
    ANT = P.room(cx - 14, g + 1, cz - 6, cx - 2, g + 6, cz + 6)              # antechamber
    HALL = P.room(cx + 9, LY + 1, cz - 12, cx + 27, LY + 6, cz + 12)         # hall of pillars
    P.room(cx + 16, LY + 1, cz - 14, cx + 18, LY + 4, cz - 13)               # door north
    NT = P.room(cx + 13, LY + 1, cz - 24, cx + 23, LY + 5, cz - 15)          # treasure of servants
    P.room(cx + 16, LY + 1, cz + 13, cx + 18, LY + 4, cz + 14)               # door south
    ST = P.room(cx + 13, LY + 1, cz + 15, cx + 23, LY + 5, cz + 24)          # tomb
    KING = P.room(cx - 8, KY + 1, cz - 8, cx + 8, KY + 8, cz + 8)            # king's chamber
    P.room(cx - 14, KY + 1, cz - 1, cx - 9, KY + 4, cz + 1)                  # door corridor west of chamber
    P.room(cx - 14, KY + 1, cz + 2, cx - 12, KY + 4, cz + 11)                # landing corridor
    TR = P.room(cx + 10, KY + 1, cz - 4, cx + 13, KY + 4, cz + 4)            # treasure room
    P.room(cx + 9, KY + 1, cz - 1, cx + 9, KY + 3, cz + 1)
    P.carve()
    # descending stair antechamber -> hall
    for i in range(10):
        x = cx - 1 + i
        y = g - i
        w.fill(x, y - 1, cz - 2, x, y + 5, cz + 2, inner)
        w.fill(x, y + 1, cz - 1, x, y + 4, cz + 1, AIR)
        for z in (cz - 1, cz, cz + 1):
            w.set(x, y, z, bl.stairs("sandstone", "W"))
    w.fill(cx - 1, g + 1, cz - 1, cx - 1, g + 4, cz + 1, AIR)
    w.fill(cx + 8, LY + 1, cz - 1, cx + 8, LY + 4, cz + 1, AIR)
    # grand gallery: hall (south-west corner) up to the landing
    gz = cz + 10
    for i in range(20):
        x = cx + 8 - i
        y = LY + 1 + i
        w.fill(x, y - 1, gz - 1, x, y + 6, gz + 3, inner)
        w.fill(x, y + 1, gz, x, y + 5, gz + 2, AIR)
        for z in (gz, gz + 1, gz + 2):
            w.set(x, y, z, bl.stairs("smooth_sandstone", "W"))
        if i % 4 == 2:
            w.set(x, y + 4, gz, bl.torch("N"))
    w.fill(cx + 8, LY + 1, gz, cx + 8, LY + 5, gz + 2, AIR)
    w.fill(cx - 14, KY, gz - 1, cx - 12, KY, gz + 2, bl.block("cut_sandstone"))
    w.fill(cx - 14, KY + 1, gz, cx - 12, KY + 5, gz + 2, AIR)
    w.fill(cx - 12, KY + 1, gz, cx - 11, KY + 5, gz + 2, AIR)
    # --- decoration: corridor + antechamber ---------------------------------------------------
    for x in range(wx + 4, wx + 15, 4):
        w.set(x, g + 3, cz - 1, bl.torch("N"))
        w.set(x, g + 3, cz + 1, bl.torch("S"))
        w.set(x, g + 2, cz - 2, HIERO)
        w.set(x, g + 2, cz + 2, HIERO)
    dk.plate(w, wx + 4, g + 1, cz, "function bear/enter/desert", floor=bl.block("cut_sandstone"))
    ax0, _, az0, ax1, _, az1 = ANT
    for (px, pz) in ((ax0 + 2, az0 + 2), (ax1 - 2, az0 + 2), (ax0 + 2, az1 - 2), (ax1 - 2, az1 - 2)):
        dk.pillar(w, px, g + 1, g + 6, pz, "sandstone", body=bl.block("cut_sandstone"))
        w.set(px, g + 3, pz, HIERO)
    for z in range(az0, az1 + 1):
        for x in (ax0 - 1, ax1 + 1):
            if abs(z - cz) > 2:
                w.set(x, g + 3, z, HIERO if z % 2 else B("orange_terracotta"))
    for x in range(ax0, ax1 + 1):
        for z in (az0 - 1, az1 + 1):
            w.set(x, g + 3, z, HIERO if x % 2 else B("blue_terracotta"))
    for (x, z) in ((ax0, az0), (ax1, az0), (ax0, az1), (ax1, az1)):
        pot(w, x, g + 1, z)
    for (x, z) in ((ax0 + 6, az0), (ax0 + 6, az1)):
        dk.brazier(w, x, g + 1, z, base="stone")
    w.fill(ax0 + 4, g, cz - 2, ax1 - 4, g, cz + 2, B("lapis_block"))
    w.fill(ax0 + 5, g, cz - 1, ax1 - 5, g, cz + 1, B("gold_block"))
    dk.chest(w, ax0, g + 1, cz + 4, "E", 1, rng)
    # --- hall of pillars -------------------------------------------------------------------------
    hx0, _, hz0, hx1, _, hz1 = HALL
    for x in range(hx0 + 3, hx1 - 1, 5):
        for z in range(hz0 + 3, hz1 - 1, 6):
            if not (abs(z - cz) < 3):
                dk.pillar(w, x, LY + 1, LY + 6, z, "sandstone", body=bl.block("cut_sandstone"))
                w.set(x, LY + 3, z, HIERO)
    dk.spawner(w, cx + 18, LY + 1, cz - 7, "husk")
    dk.spawner(w, cx + 18, LY + 1, cz + 7, "husk")
    dk.scatter(w, (hx0, LY + 1, hz0, hx1, LY + 1, hz1), [B("sand"), bl.slab("sandstone"), B("deadbush")], 30, rng)
    dk.cobwebs(w, HALL, 20, rng)
    for (x, z) in ((hx0, hz0), (hx1, hz0), (hx0, hz1), (hx1, hz1), (hx1, cz - 2), (hx1, cz + 2)):
        pot(w, x, LY + 1, z)
    dk.chest(w, hx1, LY + 1, cz, "W", 2, rng)
    w.set(cx + 3, g - 4, cz - 1, bl.torch("N"))
    dk.sign(w, cx + 9, LY + 3, cz + 9, "E", "§l대회랑\n§r계단을 올라\n왕의 방으로", glow=True)
    # --- north: treasure of the servants (spider nest) -----------------------------------------
    nx0, _, nz0, nx1, _, nz1 = NT
    dk.spawner(w, cx + 18, LY + 1, cz - 20, "spider")
    dk.chest(w, nx0, LY + 1, nz0, "S", 2, rng, extra=[bl.item("gold_ingot", 6)])
    dk.chest(w, nx1, LY + 1, nz0, "S", 2, rng, extra=[bl.item("bow", ench=dk.ench(("power", 2)))])
    for x in range(nx0, nx1 + 1, 2):
        w.set(x, LY + 1, nz0, B("gold_block")) if x not in (nx0, nx1) and rng.random() < 0.5 else None
    dk.cobwebs(w, NT, 30, rng)
    for _ in range(18):
        x, z = int(rng.integers(nx0, nx1 + 1)), int(rng.integers(nz0, nz1 + 1))
        y = LY + int(rng.integers(2, 6))
        if w.get(x, y, z) == 0:
            w.set(x, y, z, B("web"))
    # --- south: tomb of the guards -----------------------------------------------------------------
    sx0, _, sz0, sx1, _, sz1 = ST
    dk.spawner(w, cx + 18, LY + 1, cz + 20, "skeleton")
    for x in (sx0 + 1, sx0 + 5, sx0 + 9):
        w.fill(x, LY + 1, sz1 - 3, x, LY + 1, sz1 - 1, B("gold_block") if x == sx0 + 5 else bl.block("cut_sandstone"))
        for z in range(sz1 - 3, sz1):
            w.set(x, LY + 2, z, bl.slab("smooth_sandstone"))
        dk.skull(w, x, LY + 2, sz1, 0, 180.0)
        w.set(x, LY + 1, sz1, HIERO)
    dk.chest(w, sx0, LY + 1, sz0, "S", 2, rng)
    dk.chest(w, sx1, LY + 1, sz1, "N", 2, rng, extra=[bl.item("iron_helmet", ench=dk.ench(("protection", 2)))])
    dk.cobwebs(w, ST, 12, rng)
    # --- king's chamber -----------------------------------------------------------------------------
    kx0, _, kz0, kx1, _, kz1 = KING
    w.fill(kx0, KY, kz0, kx1, KY, kz1, Mix((bl.block("smooth_sandstone"), 3), (bl.block("cut_sandstone"), 2)))
    for t in range(-8, 9):
        w.set(cx + t, KY, cz, B("lapis_block"))
        w.set(cx, KY, cz + t, B("lapis_block"))
    w.fill(cx - 1, KY, cz - 1, cx + 1, KY, cz + 1, B("gold_block"))
    for (px, pz) in ((-5, -5), (5, -5), (-5, 5), (5, 5), (-5, 0), (0, -5), (0, 5)):
        dk.pillar(w, cx + px, KY + 1, KY + 8, cz + pz, "sandstone", body=bl.block("cut_sandstone"))
        w.set(cx + px, KY + 4, cz + pz, B("gold_block"))
    for y in (KY + 3, KY + 6):
        for t in range(-8, 9):
            for (x, z) in ((cx + t, kz0 - 1), (cx + t, kz1 + 1), (kx0 - 1, cz + t), (kx1 + 1, cz + t)):
                if w.get(x, y, z) != 0:
                    w.set(x, y, z, HIERO if (t + y) % 2 else B("orange_terracotta") if y == KY + 3 else B(
                        "blue_terracotta"))
    # sarcophagus on a dais (east side)
    w.fill(cx + 4, KY + 1, cz - 3, cx + 8, KY + 1, cz + 3, bl.block("smooth_sandstone"))
    for z in range(cz - 3, cz + 4):
        w.set(cx + 3, KY + 1, z, bl.stairs("smooth_sandstone", "E"))
    w.fill(cx + 5, KY + 2, cz - 1, cx + 7, KY + 2, cz + 1, B("gold_block"))
    w.fill(cx + 5, KY + 3, cz - 1, cx + 7, KY + 3, cz + 1, B("lapis_block"))
    w.fill(cx + 5, KY + 3, cz, cx + 7, KY + 3, cz, B("gold_block"))
    w.set(cx + 5, KY + 4, cz, bl.slab("smooth_sandstone"))
    dk.skull(w, cx + 7, KY + 4, cz, 0, 90.0)
    for (x, z) in ((kx0, kz0), (kx0, kz1), (kx1, kz0), (kx1, kz1)):
        dk.brazier(w, x, KY + 1, z, base="stone")
    for z in (cz - 6, cz + 6):
        dk.brazier(w, cx + 6, KY + 2, z, base="stone") if False else None
        pot(w, cx + 7, KY + 1, z)
        w.put(cx + 8, KY + 5, z, bl.wall_banner("W"), bl.be_banner(11))
    for z in (cz - 1, cz, cz + 1):
        dk.plate(w, kx0 + 1, KY + 1, z, "function bear/boss/desert", floor=bl.block("cut_sandstone"))
    dk.sign(w, cx - 12, KY + 3, cz - 2, "S", "§6§l왕의 방\n§r태양왕 파라오가\n잠들어 있다", glow=True) if False else None
    dk.sign(w, cx - 11, KY + 3, cz - 1, "E", "§6§l왕의 방\n§r태양왕이 잠든 곳", glow=True) if False else None
    w.set(cx - 12, KY + 3, gz - 1, bl.torch("N")) if False else None
    w.set(cx - 14, KY + 3, cz + 5, bl.torch("W"))
    # --- treasure room -------------------------------------------------------------------------------
    tx0, _, tz0, tx1, _, tz1 = TR
    w.fill(tx0, KY, tz0, tx1, KY, tz1, B("gold_block"))
    dk.reward_altar(w, tx1, KY + 1, cz, "W", "desert", "사막 던전 보상")
    dk.chest(w, tx0 + 1, KY + 1, tz0, "S", 2, rng, extra=[bl.item("diamond", 2), bl.item("golden_apple", 2)])
    dk.chest(w, tx0 + 1, KY + 1, tz1, "N", 3, rng)
    dk.exit_pad(w, tx0 + 1, KY + 1, cz + 2, None)
    dk.sign(w, tx0, KY + 2, cz + 3, "N", "§b§l귀환 발판\n§r마을로 이동") if False else None
    w.set(tx1, KY + 4, tz0, bl.lantern(True))
    w.set(tx1, KY + 4, tz1, bl.lantern(True))
    # registry
    dk.warp("desert", 0, wx - 20 + 0.5, g + 1, cz + 0.5, (cx, g + 6, cz))
    dk.zone(0, cx - 68, 40, cz - 50, cx + 42, 125, cz + 42)
    bx, by, bz = cx + 2, KY + 1, cz
    dk.boss("desert", {
        "pos": (kx0 + 1, KY + 1, cz),
        "spawn": [
            'summon husk "§6태양왕 파라오" %d %d %d' % (bx, by, bz),
            "tag @e[type=husk,x=%d,y=%d,z=%d,r=3,c=1] add boss_desert" % (bx, by, bz),
            "replaceitem entity @e[tag=boss_desert] slot.armor.head 0 golden_helmet",
            "replaceitem entity @e[tag=boss_desert] slot.armor.chest 0 golden_chestplate",
            "replaceitem entity @e[tag=boss_desert] slot.armor.legs 0 golden_leggings",
            "replaceitem entity @e[tag=boss_desert] slot.armor.feet 0 golden_boots",
            "replaceitem entity @e[tag=boss_desert] slot.weapon.mainhand 0 golden_sword",
            "effect @e[tag=boss_desert] health_boost 99999 14 true",
            "effect @e[tag=boss_desert] instant_damage 1 5 true",
            "effect @e[tag=boss_desert] strength 99999 1 true",
            "effect @e[tag=boss_desert] resistance 99999 0 true",
            "summon husk %d %d %d" % (bx - 2, by, bz - 5),
            "summon husk %d %d %d" % (bx - 2, by, bz + 5),
            "summon husk %d %d %d" % (bx + 1, by, bz - 6),
            "summon husk %d %d %d" % (bx + 1, by, bz + 6),
            "summon skeleton %d %d %d" % (bx + 3, by + 1, bz - 3),
            "summon skeleton %d %d %d" % (bx + 3, by + 1, bz + 3),
        ],
        "title": "§6태양왕 파라오", "sub": "§7피라미드의 주인",
    })
