"""Plains dungeon: the Ruined Keep (overgrown castle ruins above, crypt below)."""
import math

from . import blocks as bl
from . import dkit as dk
from . import kit
from .core import B, Mix
from .kit import Frame
from .layout import KEEP, KEEP_G

AIR = 0


def ruin_mix():
    return Mix((bl.block("stone_brick"), 6), (B("stonebrick", stone_brick_type="cracked"), 4),
               (bl.block("mossy_stone_brick"), 5), (bl.block("cobblestone"), 3), (bl.block("mossy_cobblestone"), 3),
               (bl.block("andesite"), 2))


def crypt_mix():
    return Mix((bl.block("stone_brick"), 8), (B("stonebrick", stone_brick_type="cracked"), 3),
               (bl.block("mossy_stone_brick"), 2), (bl.block("cobblestone"), 2), (B("deepslate_bricks"), 1))


def floor_mix():
    return Mix((bl.block("stone_brick"), 5), (bl.block("cobblestone"), 4), (bl.block("andesite"), 3), (B("gravel"), 2),
               (bl.block("mossy_cobblestone"), 2), (B("stonebrick", stone_brick_type="cracked"), 2))


def _profile(n, rng, full, breaches):
    """Ragged height profile with collapsed sections."""
    h = [float(full)] * n
    for _ in range(breaches):
        c = int(rng.integers(6, n - 6))
        wdt = int(rng.integers(3, 8))
        low = float(rng.integers(0, 3))
        for i in range(n):
            d = abs(i - c)
            if d <= wdt + 4:
                t = max(0.0, (d - wdt) / 4.0)
                h[i] = min(h[i], low + (full - low) * t)
    return [max(0, int(round(v + rng.integers(-1, 1)))) for v in h]


def curtain(w, rng, g, cx, cz, half):
    mix = ruin_mix()
    rub = Mix((bl.block("cobblestone"), 3), (bl.block("mossy_cobblestone"), 3), (bl.slab("cobblestone"), 2),
              (bl.slab("mossy_cobblestone"), 2), (bl.block("stone_brick"), 1))
    n = 2 * half + 1
    for side in range(4):
        prof = _profile(n, rng, 8, 2 if side != 2 else 1)
        for i in range(n):
            t = -half + i
            for k in range(3):
                off = half - k
                x, z = {0: (cx + t, cz - off), 1: (cx + off, cz + t), 2: (cx + t, cz + off), 3: (cx - off, cz + t)}[
                    side]
                if side == 2 and abs(t) <= 2:
                    continue
                h = max(0, prof[i] - (1 if k == 1 and prof[i] < 8 else 0))
                w.fill(x, g - 2, z, x, g, z, mix)
                if h > 0:
                    w.fill(x, g + 1, z, x, g + h, z, mix)
                if k == 0 and prof[i] >= 8 and i % 3 != 2:
                    w.set(x, g + 9, z, mix)
                if k == 2 and prof[i] >= 8:
                    w.set(x, g + 8, z, AIR)
            if prof[i] < 4:        # rubble around breaches
                for _ in range(4):
                    off = half + int(rng.integers(-5, 4))
                    tt = t + int(rng.integers(-2, 3))
                    x, z = {0: (cx + tt, cz - off), 1: (cx + off, cz + tt), 2: (cx + tt, cz + off),
                            3: (cx - off, cz + tt)}[side]
                    if w.get(x, g + 1, z) == 0 and not (side == 2 and abs(tt) <= 3):
                        w.set(x, g + 1, z, rub)
            # vines on standing sections
            if prof[i] >= 6 and rng.random() < 0.25:
                off = half + 1
                x, z = {0: (cx + t, cz - off), 1: (cx + off, cz + t), 2: (cx + t, cz + off), 3: (cx - off, cz + t)}[
                    side]
                att = {0: "S", 1: "W", 2: "N", 3: "E"}[side]
                for y in range(g + int(rng.integers(2, 5)), g + 8):
                    if w.get(x, y, z) == 0:
                        w.set(x, y, z, bl.vine(att))


def ruin_tower(w, rng, cx, cz, g, r, full, broken):
    mix = ruin_mix()
    ph = rng.random() * 6.28
    for (dx, dz) in kit.disc_cells(r):
        d = math.hypot(dx, dz)
        w.fill(cx + dx, g - 2, cz + dz, cx + dx, g, cz + dz, mix)
        if d > r - 1.2:
            a = math.atan2(dz, dx)
            h = full - broken * (0.5 + 0.5 * math.sin(a * 1.5 + ph)) + rng.integers(-1, 2)
            h = int(max(2, h))
            w.fill(cx + dx, g + 1, cz + dz, cx + dx, g + h, cz + dz, mix)
            if h >= full and (int(a * 6) % 2 == 0):
                w.set(cx + dx, g + h + 1, cz + dz, mix)
        else:
            w.fill(cx + dx, g + 1, cz + dz, cx + dx, g + full + 3, cz + dz, AIR)
            w.set(cx + dx, g, cz + dz, floor_mix())
            if rng.random() < 0.25:
                w.set(cx + dx, g + 1, cz + dz, Mix(bl.block("cobblestone"), bl.slab("cobblestone"),
                                                   B("moss_carpet"), bl.block("mossy_cobblestone")))


def tent(F, x, y, z, color="white"):
    """A-frame tent 5 long (local z), opening to the south."""
    wool = B(color + "_wool")
    for dz in range(0, 5):
        F.set(x - 2, y, z + dz, wool)
        F.set(x + 2, y, z + dz, wool)
        F.set(x - 1, y + 1, z + dz, wool)
        F.set(x + 1, y + 1, z + dz, wool)
        F.set(x, y + 2, z + dz, wool)
        F.set(x - 1, y, z + dz, AIR)
        F.set(x, y, z + dz, AIR)
        F.set(x + 1, y, z + dz, AIR)
        F.set(x, y + 1, z + dz, AIR)
    F.set(x - 1, y, z, wool)
    F.set(x, y, z, wool)
    F.set(x + 1, y, z, wool)
    F.set(x, y + 1, z, wool)
    F.set(x, y, z + 4, bl.fence("spruce"))
    F.set(x, y + 1, z + 4, bl.fence("spruce"))
    F.bed(x - 1, y, z + 1, "S", 14)
    F.set(x + 1, y, z + 1, bl.barrel("U"))
    F.set(x, y, z + 4, AIR)
    F.set(x, y + 1, z + 4, AIR)


def build(w, T, log=print):
    rng = w.rng
    cx, cz = KEEP
    g = KEEP_G
    F = Frame(w, 0, 0, 0, 0)
    mix = ruin_mix()
    half = 30
    x0i, z0i = cx - 48 - w.x0, cz - 52 - w.z0
    T.reserved[x0i:x0i + 112, z0i:z0i + 104] = True
    # overgrown courtyard ground
    for (dx, dz) in kit.disc_cells(46):
        x, z = cx + dx, cz + dz
        if abs(dx) <= half and abs(dz) <= half:
            w.set(x, g, z, Mix((B("grass_block"), 10), (B("dirt", dirt_type="coarse"), 3), (B("moss_block"), 2),
                               (bl.block("cobblestone"), 1), (bl.block("mossy_cobblestone"), 1), (B("podzol"), 1)))
    curtain(w, rng, g, cx, cz, half)
    for (sx, sz, full, broken) in ((-1, -1, 15, 6), (1, -1, 7, 4), (-1, 1, 13, 5), (1, 1, 10, 7)):
        ruin_tower(w, rng, cx + sx * half, cz + sz * half, g, 5.5, full, broken)
    dk.chest(w, cx - half, g + 1, cz - half, "S", 1, rng)
    # gate piers with a broken arch
    gz = cz + half
    for sx in (-1, 1):
        w.fill(cx + sx * 3, g - 2, gz - 3, cx + sx * 6, g + 9 - (3 if sx > 0 else 0), gz + 1, mix)
        for y in range(g + 10 - (3 if sx > 0 else 0), g + 12 - (4 if sx > 0 else 0)):
            w.set(cx + sx * 5, y, gz, mix)
        w.set(cx + sx * 4, g + 4, gz + 2, bl.torch("N"))
    for z in range(gz - 3, gz + 2):
        w.set(cx - 2, g + 7, z, bl.stairs("stone_brick", "W", top=True))
        w.set(cx - 1, g + 8, z, bl.stairs("mossy_stone_brick", "W", top=True))
        w.set(cx - 2, g + 8, z, mix)
        w.set(cx, g + 8, z, bl.slab("stone_brick", top=True)) if z % 2 else None
    w.fill(cx - 2, g, gz - 4, cx + 2, g, gz + 4, Mix((bl.block("cobblestone"), 4), (B("gravel"), 3),
                                                     (bl.block("mossy_cobblestone"), 3), (B("grass_path"), 2)))
    dk.sign(w, cx - 3, g + 2, gz + 2, "S", "§2§l초원 던전\n§r폐허의 성채\n§8권장 돌~철 장비", wood="dark_oak", glow=True)
    # path gate -> keep
    for z in range(cz + 12, gz - 3):
        for x in range(cx - 1, cx + 2):
            if rng.random() < 0.8:
                w.set(x, g, z, Mix((bl.block("cobblestone"), 4), (B("gravel"), 3), (B("grass_path"), 3),
                                   (bl.block("mossy_cobblestone"), 2)))
    # ---------------- the keep ------------------------------------------------
    kh = 11
    k0x, k1x, k0z, k1z = cx - kh, cx + kh, cz - kh, cz + kh
    w.fill(k0x, g - 3, k0z, k1x, g, k1z, mix)
    w.fill(k0x + 2, g, k0z + 2, k1x - 2, g, k1z - 2, floor_mix())
    ph = rng.random() * 6.28
    for x in range(k0x, k1x + 1):
        for z in range(k0z, k1z + 1):
            edge = min(x - k0x, k1x - x, z - k0z, k1z - z)
            if edge < 2:
                a = math.atan2(z - cz, x - cx)
                h = 15 - 5 * (0.5 + 0.5 * math.sin(a * 2 + ph)) + rng.integers(-1, 2)
                w.fill(x, g + 1, z, x, g + int(h), z, mix)
            else:
                w.fill(x, g + 1, z, x, g + 20, z, AIR)
    for sx in (-1, 1):          # corner buttresses
        for sz in (-1, 1):
            bx, bz = cx + sx * (kh + 1), cz + sz * (kh + 1)
            w.fill(bx - 1, g - 2, bz - 1, bx + 1, g + 10 + int(rng.integers(0, 4)), bz + 1, mix)
    # windows + door
    for y in (g + 3, g + 4, g + 8, g + 9):
        for t in (-6, 0, 6):
            for (x, z) in ((cx + t, k0z), (cx + t, k0z + 1), (cx + t, k1z), (cx + t, k1z - 1), (k0x, cz + t),
                           (k0x + 1, cz + t), (k1x, cz + t), (k1x - 1, cz + t)):
                if not (z >= k1z - 1 and t == 0 and y < g + 6):
                    w.set(x, y, z, AIR)
    w.fill(cx - 1, g + 1, k1z - 1, cx + 1, g + 4, k1z, AIR)
    w.set(cx - 1, g + 4, k1z, bl.stairs("stone_brick", "W", top=True))
    w.set(cx + 1, g + 4, k1z, bl.stairs("stone_brick", "E", top=True))
    # remains of upper floors
    for fy in (g + 6, g + 11):
        for x in range(k0x + 2, k1x - 1):
            for z in range(k0z + 2, k1z - 1):
                d = math.hypot(x - cx - 3, z - cz + 1)
                if d > 6.5 + rng.random() * 2.5 and rng.random() < 0.85:
                    w.set(x, fy, z, bl.planks("spruce") if rng.random() < 0.8 else bl.slab("spruce"))
        for z in range(k0z + 2, k1z - 1, 4):
            for x in range(k0x + 2, k1x - 1):
                if rng.random() < 0.8:
                    w.set(x, fy, z, bl.log("dark_oak", "x"))
    # hall pillars, rubble, moss
    for (px, pz, hh) in ((-6, -6, 5), (6, -6, 3), (-6, 6, 5), (6, 6, 4)):
        dk.pillar(w, cx + px, g + 1, g + hh, cz + pz, "stone_brick", cap=(hh == 5))
    dk.scatter(w, (k0x + 2, g + 1, k0z + 2, k1x - 2, g + 1, k1z - 2),
               [bl.block("cobblestone"), bl.slab("cobblestone"), B("moss_carpet"), bl.block("mossy_cobblestone"),
                B("moss_carpet"), bl.slab("stone_brick")], 60, rng)
    w.put(cx - 9, g + 1, cz - 9, bl.chest("S"), bl.be_chest(dk.loot(1, rng)))
    for (bx, bz, f) in ((cx - 5, k1z + 1, "S"), (cx + 5, k1z + 1, "S")):
        w.put(bx, g + 6, bz, bl.wall_banner(f), bl.be_banner(0))
    w.set(cx - 2, g + 3, k1z + 1, bl.torch("N"))
    w.set(cx + 2, g + 3, k1z + 1, bl.torch("N"))
    # bandit camp in the courtyard
    tent(F, cx - 18, g + 1, cz + 10, "white")
    tent(F, cx - 22, g + 1, cz - 4, "light_gray")
    tent(F, cx + 19, g + 1, cz + 8, "white")
    w.set(cx - 15, g + 1, cz + 18, bl.campfire())
    w.set(cx + 17, g + 1, cz + 17, bl.campfire())
    for (lx, lz) in ((cx - 14, cz + 16), (cx - 17, cz + 19), (cx + 15, cz + 15)):
        w.set(lx, g + 1, lz, bl.log("spruce", "x"))
    kit.crate_pile(F, cx + 21, g + 1, cz + 15, rng, 5)
    kit.crate_pile(F, cx - 24, g + 1, cz + 4, rng, 4)
    kit.well(F, cx + 18, g, cz - 14, stone="mossy_stone_brick")
    for _ in range(14):
        tx, tz = cx + int(rng.integers(-26, 27)), cz + int(rng.integers(-26, 27))
        if abs(tx - cx) < 15 and abs(tz - cz) < 15:
            continue
        if w.get(tx, g + 1, tz) == 0 and w.get(tx, g + 3, tz) == 0:
            if rng.random() < 0.5:
                kit.tree_dead(w, tx, g + 1, tz, rng)
            else:
                kit.bush(w, tx, g + 1, tz, rng)
    for _ in range(500):
        tx, tz = cx + int(rng.integers(-28, 29)), cz + int(rng.integers(-28, 29))
        if w.get(tx, g + 1, tz) == 0 and w.get(tx, g, tz) in (B("grass_block"), B("moss_block"), B("podzol")):
            w.set(tx, g + 1, tz, Mix((B("short_grass"), 6), (B("fern"), 2), (B("deadbush"), 0.1), (B("poppy"), 0.6),
                                     (B("oxeye_daisy"), 0.4), (B("moss_carpet"), 1)))
    # ---------------- crypt ---------------------------------------------------
    FY = g - 10
    BY = FY - 4
    P = dk.Plan(w, crypt_mix(), floor=floor_mix())
    A = P.room(-6, FY + 1, cz - 18, 6, FY + 6, cz - 4)
    P.room(-1, FY + 1, cz - 27, 1, FY + 4, cz - 19)
    Bm = P.room(-8, FY + 1, cz - 44, 8, FY + 6, cz - 28)
    P.room(9, FY + 1, cz - 37, 17, FY + 4, cz - 35)
    C = P.room(18, FY + 1, cz - 42, 34, FY + 5, cz - 30)
    P.room(25, FY + 1, cz - 29, 27, FY + 4, cz - 23)
    D = P.room(16, FY + 1, cz - 22, 40, FY + 6, cz - 2)
    E = P.room(16, BY + 1, cz + 6, 40, BY + 10, cz + 28)
    Fv = P.room(42, BY + 1, cz + 12, 52, BY + 5, cz + 22)
    P.room(41, BY + 1, cz + 16, 41, BY + 3, cz + 18)
    P.carve()
    # stair tunnel from the keep down to hall A
    for i in range(10):
        z = cz + 6 - i
        y = g - i
        w.fill(-2, y - 1, z, 2, y + 5, z, crypt_mix())
        w.fill(-1, y + 1, z, 1, y + 4, z, AIR)
        for x in (-1, 0, 1):
            w.set(x, y, z, bl.stairs("stone_brick" if rng.random() < 0.7 else "mossy_stone_brick", "S"))
    w.fill(-1, FY + 1, cz - 4, 1, FY + 5, cz - 3, AIR)
    w.fill(-1, g + 1, cz + 7, 1, g + 4, cz + 7, AIR)
    for x in (-2, 2):
        w.fill(x, g + 1, cz + 3, x, g + 2, cz + 7, mix)
    w.set(-2, g + 3, cz + 7, bl.torch())
    w.set(2, g + 3, cz + 7, bl.torch())
    dk.plate(w, 0, g + 1, cz + 8, "function bear/enter/plains", floor=bl.block("stone_brick"))
    # corridor D -> E: steps down
    for i in range(7):
        z = cz - 1 + i
        y = FY - min(i, 4)
        w.fill(26, y - 1, z, 30, y + 6, z, crypt_mix())
        w.fill(27, y + 1, z, 29, y + 4, z, AIR)
        for x in (27, 28, 29):
            w.set(x, y, z, bl.stairs("stone_brick", "N") if i < 4 else floor_mix())
    w.fill(27, BY + 1, cz + 5, 29, BY + 5, cz + 5, AIR)
    w.fill(27, FY + 1, cz - 2, 29, FY + 4, cz - 2, AIR)
    # --- hall A: entrance ------------------------------------------------------
    for (px, pz) in ((-4, cz - 15), (4, cz - 15), (-4, cz - 7), (4, cz - 7)):
        dk.pillar(w, px, FY + 1, FY + 6, pz)
        w.set(px, FY + 4, pz + 1, bl.torch("N", "soul_torch"))
    dk.sign(w, 0, FY + 3, cz - 5, "N", "§l지하 묘지\n§r이 아래 잠든 왕을\n깨우지 마라", standing=False)
    w.set(0, FY + 3, cz - 4, crypt_mix())
    w.fill(-1, FY + 1, cz - 4, 1, FY + 4, cz - 4, AIR)
    kit.crate_pile(F, -6, FY + 1, cz - 17, rng, 4)
    w.put(5, FY + 1, cz - 17, bl.chest("W"), bl.be_chest([bl.item("torch", 16), bl.item("bread", 4)]))
    dk.cobwebs(w, A, 14, rng)
    w.set(0, FY + 4, cz - 23, bl.lantern(True, soul=True))
    w.set(0, FY + 5, cz - 23, B("chain", pillar_axis="y")) if False else None
    # --- room B: barracks ------------------------------------------------------
    dk.spawner(w, 0, FY + 1, cz - 36, "zombie")
    for i, z in enumerate(range(cz - 43, cz - 29, 3)):
        F2 = Frame(w, 0, 0, 0, 0)
        F2.bed(-7, FY + 1, z, "W", 12)
        F2.bed(7, FY + 1, z, "E", 12)
        w.set(-8, FY + 1, z + 1, bl.barrel("U")) if i % 2 == 0 else None
    kit.table(F, -3, FY + 1, cz - 31, "spruce")
    kit.table(F, 3, FY + 1, cz - 41, "spruce")
    dk.chest(w, -8, FY + 1, cz - 29, "E", 1, rng)
    dk.chest(w, 8, FY + 1, cz - 44, "W", 1, rng)
    for x in (-5, 5):
        w.set(x, FY + 1, cz - 44, bl.fence("dark_oak"))
        w.set(x, FY + 2, cz - 44, bl.fence("dark_oak"))
        w.set(x, FY + 3, cz - 44, B("iron_bars"))
    dk.cobwebs(w, Bm, 16, rng)
    dk.scatter(w, (-7, FY + 1, cz - 43, 7, FY + 1, cz - 29), [B("moss_carpet"), bl.slab("cobblestone")], 14, rng)
    w.set(13, FY + 4, cz - 36, bl.lantern(True, soul=True))
    # --- room C: prison ----------------------------------------------------------
    dk.spawner(w, 26, FY + 1, cz - 36, "skeleton")
    for x0 in range(18, 34, 4):
        for (zc, zf) in ((cz - 42, cz - 39), (cz - 30, cz - 33)):
            w.fill(x0 + 3, FY + 1, min(zc, zf), x0 + 3, FY + 5, max(zc, zf), crypt_mix())
            for x in range(x0, x0 + 3):
                for y in range(FY + 1, FY + 4):
                    w.set(x, y, zf, B("iron_bars"))
                w.fill(x, FY + 4, zf, x, FY + 5, zf, crypt_mix())
            w.set(x0 + 1, FY + 1, zf, AIR)
            w.set(x0 + 1, FY + 2, zf, AIR)
            if rng.random() < 0.6:
                dk.skull(w, x0 + int(rng.integers(0, 3)), FY + 1, zc, 0, float(rng.integers(0, 360)))
            if rng.random() < 0.5:
                w.set(x0 + 1, FY + 5, zc, B("chain", pillar_axis="y"))
                w.set(x0 + 1, FY + 4, zc, B("chain", pillar_axis="y"))
            if rng.random() < 0.5:
                w.set(x0, FY + 1, zc, B("bone_block", pillar_axis="x"))
    dk.chest(w, 19, FY + 1, cz - 42, "S", 1, rng)
    dk.chest(w, 31, FY + 1, cz - 30, "N", 2, rng)
    dk.cobwebs(w, C, 12, rng)
    # --- room D: catacombs -------------------------------------------------------
    dk.spawner(w, 22, FY + 1, cz - 12, "zombie")
    dk.spawner(w, 34, FY + 1, cz - 12, "spider")
    for x in range(19, 40, 6):
        for z in (cz - 19, cz - 6):
            w.fill(x, FY + 1, z, x + 1, FY + 1, z + 2, B("stonebrick", stone_brick_type="chiseled"))
            for zz in range(z, z + 3):
                w.set(x, FY + 2, zz, bl.slab("stone_brick"))
                w.set(x + 1, FY + 2, zz, bl.slab("stone_brick"))
            w.set(x, FY + 1, z - 1, bl.stairs("stone_brick", "S"))
            w.set(x + 1, FY + 1, z - 1, bl.stairs("stone_brick", "S"))
            w.set(x, FY + 1, z + 3, bl.stairs("stone_brick", "N"))
            w.set(x + 1, FY + 1, z + 3, bl.stairs("stone_brick", "N"))
            if rng.random() < 0.6:
                w.set(x, FY + 3, z + 1, B("candle", candles=int(rng.integers(0, 3)), lit=False))
    for z in range(cz - 21, cz - 2, 3):      # wall niches with bones
        for (x, dx) in ((15, 1), (41, -1)):
            w.set(x, FY + 2, z, AIR)
            w.set(x, FY + 3, z, AIR)
            if rng.random() < 0.7:
                dk.skull(w, x, FY + 2, z, 0, 90.0 if dx > 0 else 270.0)
            else:
                w.set(x, FY + 2, z, B("bone_block", pillar_axis="y"))
            w.set(x - dx, FY + 2, z, crypt_mix())
            w.set(x - dx, FY + 3, z, crypt_mix())
    for (px, pz) in ((22, cz - 16), (34, cz - 16), (22, cz - 8), (34, cz - 8), (28, cz - 12)):
        dk.pillar(w, px, FY + 2 if (px, pz) != (28, cz - 12) else FY + 1, FY + 6, pz)
    dk.chest(w, 17, FY + 1, cz - 3, "N", 1, rng)
    dk.chest(w, 39, FY + 1, cz - 21, "S", 2, rng, extra=[bl.item("iron_sword", ench=dk.ench(("sharpness", 1)))])
    dk.cobwebs(w, D, 22, rng)
    dk.scatter(w, (17, FY + 1, cz - 21, 39, FY + 1, cz - 3),
               [B("moss_carpet"), bl.slab("cobblestone"), B("bone_block", pillar_axis="x")], 20, rng)
    w.set(26, FY + 4, cz - 26, bl.lantern(True, soul=True))
    # --- boss hall E ---------------------------------------------------------------
    ex0, ex1, ez0, ez1 = 16, 40, cz + 6, cz + 28
    for z in range(ez0 + 3, ez1 - 3, 5):
        for x in (20, 36):
            dk.pillar(w, x, BY + 1, BY + 9, z, "stone_brick")
            w.set(x, BY + 5, z + 1, bl.lantern()) if False else None
    for z in range(ez0, ez1 + 1):        # vaulted ceiling edges
        w.set(ex0, BY + 10, z, bl.stairs("stone_brick", "W", top=True))
        w.set(ex1, BY + 10, z, bl.stairs("stone_brick", "E", top=True))
        w.set(ex0, BY + 9, z, bl.stairs("stone_brick", "W", top=True)) if z % 5 == (ez0 + 3) % 5 else None
        w.set(ex1, BY + 9, z, bl.stairs("stone_brick", "E", top=True)) if z % 5 == (ez0 + 3) % 5 else None
        for x in (27, 28, 29):
            w.set(x, BY + 1, z, B("red_carpet"))
    for x in range(ex0, ex1 + 1):
        w.set(x, BY, ez0 + 1, bl.block("polished_andesite"))
    # dais + throne
    w.fill(23, BY + 1, ez1 - 4, 33, BY + 1, ez1, bl.block("polished_andesite"))
    w.fill(25, BY + 2, ez1 - 2, 31, BY + 2, ez1, bl.block("stone_brick"))
    for x in range(23, 34):
        w.set(x, BY + 1, ez1 - 5, bl.stairs("polished_andesite", "S"))
    for x in range(25, 32):
        w.set(x, BY + 2, ez1 - 3, bl.stairs("stone_brick", "S"))
    w.set(28, BY + 3, ez1, B("gold_block"))
    w.set(28, BY + 4, ez1, B("gold_block"))
    w.set(28, BY + 5, ez1, bl.stairs("stone_brick", "N"))
    w.set(28, BY + 3, ez1 - 1, bl.stairs("dark_oak", "S"))
    w.set(27, BY + 3, ez1 - 1, bl.stairs("stone_brick", "E"))
    w.set(29, BY + 3, ez1 - 1, bl.stairs("stone_brick", "W"))
    w.set(27, BY + 3, ez1, B("stonebrick", stone_brick_type="chiseled"))
    w.set(29, BY + 3, ez1, B("stonebrick", stone_brick_type="chiseled"))
    for x in (24, 32):
        w.put(x, BY + 6, ez1, bl.wall_banner("N"), bl.be_banner(1))
        dk.brazier(w, x, BY + 2, ez1 - 3, base="stone")
    for z in (ez0 + 5, ez0 + 15):
        for x in (ex0, ex1):
            w.set(x, BY + 4, z, bl.torch("W" if x == ex0 else "E"))
    for (x, z) in ((18, ez0 + 2), (38, ez0 + 2), (18, ez1 - 2), (38, ez1 - 2)):
        dk.brazier(w, x, BY + 1, z, base="stone")
    for x in (27, 28, 29):
        dk.plate(w, x, BY + 1, ez0 + 1, "function bear/boss/plains", floor=bl.block("polished_andesite"))
    dk.sign(w, 26, BY + 3, ez0, "S", "§c§l왕좌의 방\n§r폐허의 왕이\n기다리고 있다", glow=True)
    # --- vault F -------------------------------------------------------------------------
    w.fill(42, BY, cz + 12, 52, BY, cz + 22, Mix((bl.block("polished_andesite"), 3), (bl.block("stone_brick"), 2)))
    dk.reward_altar(w, 52, BY + 1, cz + 17, "W", "plains", "초원 던전 보상")
    dk.chest(w, 44, BY + 1, cz + 12, "S", 2, rng, extra=[bl.item("iron_chestplate"), bl.item("emerald", 4)])
    dk.chest(w, 48, BY + 1, cz + 12, "S", 1, rng)
    dk.chest(w, 44, BY + 1, cz + 22, "N", 2, rng, extra=[bl.item("golden_apple", 2)])
    dk.exit_pad(w, 48, BY + 1, cz + 20, facing_sign="N")
    for (x, z) in ((42, cz + 12), (52, cz + 12), (42, cz + 22), (52, cz + 22)):
        w.set(x, BY + 4, z, bl.lantern(True)) if False else w.set(x, BY + 5, z, bl.lantern(True))
    w.set(52, BY + 1, cz + 13, B("gold_block"))
    w.set(52, BY + 2, cz + 13, B("gold_block"))
    w.set(52, BY + 1, cz + 14, B("gold_block"))
    w.set(51, BY + 1, cz + 13, B("raw_gold_block"))
    # registry
    dk.warp("plains", 0, cx + 0.5, g + 1, cz + half + 8.5, (cx, g + 2, cz))
    dk.zone(0, cx - 46, 30, cz - 52, cx + 62, 120, cz + 48)
    bx, by, bz = 28, BY + 3, ez1 - 6
    dk.boss("plains", {
        "pos": (28, BY + 2, ez0 + 3),
        "spawn": [
            'summon zombie "§c폐허의 왕" %d %d %d' % (bx, by, bz),
            "tag @e[type=zombie,x=%d,y=%d,z=%d,r=3,c=1] add boss_plains" % (bx, by, bz),
            "replaceitem entity @e[tag=boss_plains] slot.armor.head 0 golden_helmet",
            "replaceitem entity @e[tag=boss_plains] slot.armor.chest 0 iron_chestplate",
            "replaceitem entity @e[tag=boss_plains] slot.armor.legs 0 iron_leggings",
            "replaceitem entity @e[tag=boss_plains] slot.armor.feet 0 iron_boots",
            "replaceitem entity @e[tag=boss_plains] slot.weapon.mainhand 0 iron_sword",
            "effect @e[tag=boss_plains] health_boost 99999 9 true",
            "effect @e[tag=boss_plains] instant_damage 1 4 true",
            "effect @e[tag=boss_plains] strength 99999 0 true",
            "effect @e[tag=boss_plains] speed 99999 0 true",
            "summon skeleton %d %d %d" % (bx - 6, by - 1, bz),
            "summon skeleton %d %d %d" % (bx + 6, by - 1, bz),
            "summon zombie %d %d %d" % (bx - 3, by - 1, bz - 4),
            "summon zombie %d %d %d" % (bx + 3, by - 1, bz - 4),
        ],
        "title": "§c폐허의 왕", "sub": "§7초원 던전의 주인",
    })
    return dict(E=E)
