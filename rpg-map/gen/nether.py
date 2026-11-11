"""Nether dimension: enclosed cavern terrain, the hub, and the Burning Canyon dungeon.
Also builds the overworld hell gate inside the volcano crater."""
import math

import numpy as np

from . import blocks as bl
from . import dkit as dk
from . import kit
from .core import B, Mix, World
from .kit import Frame
from .layout import *  # noqa: F401,F403
from .terrain import fbm, polyline_field, smooth

AIR = 0
LAVA_Y = 31
NF = 40                                  # common floor block level
HUB = (0, 64)
CANYON = [(0, 34), (-16, 0), (12, -34), (0, -62), (-8, -100), (10, -140), (0, -172)]
ARENA = (0, -206, 36)
FORT = (96, 6, 250, 122)                 # cavern x0,z0,x1,z1
BAST = (-250, 6, -96, 122)


def bb_mix():
    return Mix((B("polished_blackstone_bricks"), 8), (B("cracked_polished_blackstone_bricks"), 2),
               (B("blackstone"), 2), (B("polished_blackstone"), 1))


def nb_mix():
    return Mix((B("nether_brick"), 10), (B("cracked_nether_bricks"), 2), (B("red_nether_brick"), 0.6))


def make_world(log=print):
    w = World(NX0, NZ0, NX1, NZ1, NY0, NY1, dim=1, biome=BIO_HELL, seed=23)
    rng = w.rng
    sx, sz, sy = w.sx, w.sz, w.sy
    X, Z = np.meshgrid(np.arange(NX0, NX1, dtype=np.float32), np.arange(NZ0, NZ1, dtype=np.float32), indexing="ij")
    n1 = fbm(sx, sz, 40, rng, 3) * 2 - 1
    n2 = fbm(sx, sz, 16, rng, 3) * 2 - 1
    n3 = fbm(sx, sz, 6, rng, 2) * 2 - 1
    n4 = fbm(sx, sz, 64, rng, 2) * 2 - 1
    w.noise = (n1, n2, n3, n4)
    # ---- solid rock with variety ---------------------------------------------
    log("  nether rock")
    rack = B("netherrack")
    Y = np.arange(sy, dtype=np.int32)[None, None, :]
    w.b[:] = rack
    rnd = rng.random((sx, sz, sy), dtype=np.float32)
    w.b[rnd < 0.012] = B("quartz_ore")
    w.b[(rnd >= 0.012) & (rnd < 0.017)] = B("nether_gold_ore")
    w.b[(rnd >= 0.017) & (rnd < 0.0174) & (Y < 24)] = B("ancient_debris")
    bs = (n1[:, :, None] + (Y - 40) * -0.012) > 0.42
    w.b[bs] = B("blackstone")
    ba = (n4[:, :, None] * 0.8 + n2[:, :, None] * 0.4) > 0.5
    w.b[ba & ~bs] = B("basalt")
    w.b[(n2[:, :, None] > 0.45) & (Y < 36)] = B("magma")
    del rnd
    # ---- cavern floor / ceiling fields -------------------------------------------
    F = np.full((sx, sz), 127, np.float32)
    C = np.full((sx, sz), 0, np.float32)

    def carve(mask, floor, ceil):
        nonlocal F, C
        F = np.where(mask, np.minimum(F, floor), F)
        C = np.where(mask, np.maximum(C, ceil), C)

    spikes = np.clip(n3 - 0.35, 0, 1) * 14 + np.clip(n2 - 0.4, 0, 1) * 10
    # hub dome
    dh = np.hypot((X - HUB[0]) / 40.0, (Z - HUB[1]) / 34.0)
    carve(dh < 1, NF, NF + 6 + 22 * np.sqrt(np.clip(1 - dh * dh, 0, 1)) + n2 * 2 - spikes * 0.4)
    # tunnels hub -> fortress / bastion
    for sgn in (1, -1):
        m = (np.abs(Z - HUB[1]) < 6.5 + n3 * 1.2) & (X * sgn > 30) & (X * sgn < 104)
        carve(m, NF, NF + 9 + n2 * 1.5 - np.abs(Z - HUB[1]) * 0.5)
    # canyon
    dcan, pcan = polyline_field(X, Z, CANYON, 60)
    wid = 11 + n2 * 2.5
    crim = np.exp(-((Z + 66) / 26.0) ** 2)                 # crimson cavern bulge
    soul = np.exp(-((Z + 128) / 24.0) ** 2)
    wid = wid + crim * 22 + soul * 9
    in_can = (dcan < wid) & (Z < 40) & (Z > -182)
    edge = np.clip(1 - dcan / np.maximum(wid, 1), 0, 1)
    carve(in_can, NF + np.round(n2 * 1.2), NF + 9 + 15 * np.sqrt(edge) + crim * 10 + soul * 4 + n1 * 3 - spikes * 0.5)
    chasm = in_can & (dcan < 2.6 + n3) & (crim < 0.5) & (soul < 0.5) & (Z < 24) & (Z > -176)
    F = np.where(chasm, 24, F)
    # boss arena (lava lake)
    da = np.hypot(X - ARENA[0], Z - ARENA[1]) / ARENA[2]
    carve(da < 1, 23, NF + 10 + 28 * np.sqrt(np.clip(1 - da * da, 0, 1)) + n2 * 2 - spikes * 0.5)
    # fortress + bastion caverns
    for (x0, z0, x1, z1), floor in ((FORT, 22), (BAST, NF)):
        ex = np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Z - z0, z1 - Z)) + n2 * 5
        m = ex > 0
        dome = np.clip(ex / 26.0, 0, 1)
        carve(m, floor if floor != NF else NF + np.round(n3 * 0.8),
              NF + 14 + 44 * np.sqrt(dome) + n1 * 5 - spikes)
    w.cav_F, w.cav_C = F, C
    Fi = np.round(F).astype(np.int32)
    Ci = np.round(C).astype(np.int32)
    log("  nether carve")
    for xa in range(0, sx, 64):
        sl = slice(xa, xa + 64)
        f, c = Fi[sl][:, :, None], Ci[sl][:, :, None]
        air = (Y > f) & (Y < c)
        blk = w.b[sl]
        blk[air] = AIR
        blk[air & (Y <= LAVA_Y)] = bl.LAVA
        # bedrock shell
        blk[:, :, 0:2] = B("bedrock")
        blk[:, :, 126:128] = B("bedrock")
    # region border = bedrock wall so the vanilla nether never shows through
    w.b[0:2, :, :] = B("bedrock")
    w.b[-2:, :, :] = B("bedrock")
    w.b[:, 0:2, :] = B("bedrock")
    w.b[:, -2:, :] = B("bedrock")
    # glowstone clusters on ceilings
    has = Ci > Fi + 4
    xs, zs = np.nonzero(has & (rng.random((sx, sz)) < 0.004))
    for x, z in zip(xs, zs):
        cy = int(Ci[x, z])
        for _ in range(int(rng.integers(6, 16))):
            dx, dz, dy = int(rng.integers(-2, 3)), int(rng.integers(-2, 3)), int(rng.integers(-3, 1))
            xx, zz, yy = x + dx, z + dz, cy + dy
            if 2 <= xx < sx - 2 and 2 <= zz < sz - 2 and 2 < yy < 125 and w.b[xx, zz, yy] == 0:
                w.b[xx, zz, yy] = B("glowstone")
    # biomes
    w.biome[(crim > 0.35) & in_can] = BIO_CRIMSON
    w.biome[(soul > 0.35) & in_can] = BIO_SOUL
    w.biome[da < 1.05] = BIO_BASALT
    w.masks = dict(crim=crim, soul=soul, in_can=in_can, dcan=dcan, da=da, chasm=chasm)
    return w


def top_floor(w, x, z, y_hi=70, y_lo=20):
    for y in range(y_hi, y_lo, -1):
        if w.get(x, y, z) not in (0,) and w.get(x, y + 1, z) == 0:
            return y
    return None


def portal_gate(w, x, y, z, axis, plate_cmd, face, label):
    """Obsidian gate with live portal blocks; pressure plates in front do the actual teleport.
    (x,y,z) = centre of the threshold; the portal plane is perpendicular to `face`."""
    F = Frame(w, x, y, z, {"S": 0, "W": 1, "N": 2, "E": 3}[face])
    ob = B("obsidian")
    # dais
    for (dx, dz) in kit.disc_cells(8.5):
        r = math.hypot(dx, dz)
        F.set(dx, -1, dz, B("polished_blackstone_bricks") if r < 7.5 else B("blackstone"))
        F.set(dx, 0, dz, (B("gilded_blackstone") if (dx * dx + dz * dz) % 9 == 0 else bb_mix()) if r < 6.5 else (
            bl.slab("polished_blackstone_brick") if r < 7.5 else AIR))
        for yy in range(1, 14):
            F.set(dx, yy, dz, AIR)
    # frame (7 wide, 9 tall) at local z=-3, opening 5x7
    for lx in range(-3, 4):
        for ly in range(1, 10):
            edge = abs(lx) == 3 or ly in (1, 9)
            F.set(lx, ly, -3, ob if edge else B("portal", portal_axis=F.ax("x")))
    F.fill(-3, 0, -3, 3, 0, -3, ob)
    # decorative outer arch
    cr = B("crying_obsidian")
    for lx in (-5, -4, 4, 5):
        hgt = 11 if abs(lx) == 4 else 8
        for ly in range(1, hgt):
            F.set(lx, ly, -3, cr if (ly + lx) % 4 == 0 else B("polished_blackstone_bricks"))
        F.set(lx, hgt, -3, B("chiseled_polished_blackstone"))
    for lx in range(-4, 5):
        F.set(lx, 10, -3, B("polished_blackstone_bricks") if abs(lx) < 4 else B("chiseled_polished_blackstone"))
        F.set(lx, 11, -3, B("gilded_blackstone") if lx % 2 == 0 and abs(lx) < 4 else (
            bl.slab("polished_blackstone_brick") if abs(lx) < 4 else AIR))
    F.set(0, 12, -3, B("gold_block"))
    for lx in (-5, 5):
        F.set(lx, 9, -3, B("netherrack"))
        F.set(lx, 10, -3, B("fire", age=0))
    for lx in (-2, 2):
        F.set(lx, 10, -2, B("chain", pillar_axis="y")) if False else None
    # side fences so the portal itself can only be approached over the plates
    for lx in (-3, 3):
        for lz in (-2, -1):
            F.set(lx, 1, lz, B("polished_blackstone_brick_wall", wall_post_bit=True))
            F.set(lx, 2, lz, B("polished_blackstone_brick_wall", wall_post_bit=True))
    for lx in range(-2, 3):
        F.plate_cmd(lx, 1, -1, plate_cmd, plate="polished_blackstone_pressure_plate",
                    floor=B("chiseled_polished_blackstone"))
        F.set(lx, 0, -2, B("magma"))
    for lx in (-6, 6):
        F.set(lx, 1, 0, B("polished_blackstone_brick_wall", wall_post_bit=True))
        F.set(lx, 2, 0, bl.lantern(soul=True))
    F.sign(-4, 3, -2, "S", label, wood="crimson", glow=True)
    F.sign(4, 3, -2, "S", label, wood="crimson", glow=True)
    # guard: anyone who jumps past the plates into the portal blocks is warped the same way
    ax_, ay_, az_ = F.p(-2, 2, -3)
    bx_, by_, bz_ = F.p(2, 8, -3)
    F.put(0, -1, -3, bl.cmd("repeat", "U"), bl.be_cmd(
        "execute if entity @a[x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d] run %s" % (
            min(ax_, bx_), ay_, min(az_, bz_), abs(bx_ - ax_), by_ - ay_, abs(bz_ - az_), plate_cmd),
        auto=True, tick_delay=0, repeat=True))
    return F


def hell_gate_overworld(w, T, log=print):
    """Volcano crater with the gate to the Nether."""
    rng = w.rng
    hx, hz = HELLGATE
    g = HELL_G
    xi, zi = hx - 70 - w.x0, hz - 70 - w.z0
    T.reserved[max(0, xi):xi + 140, max(0, zi):zi + 140] = True
    # lava pools in the crater floor
    for k in range(7):
        a = k * 0.9 + 0.6
        rr = 18 + (k % 3) * 5
        px, pz = hx + int(rr * math.cos(a)), hz + int(rr * math.sin(a))
        if pz < hz - 4 and abs(px - hx) < 12:
            continue
        for (dx, dz) in kit.disc_cells(2.5 + (k % 2)):
            y = w.top(px + dx, pz + dz)
            if y is not None and abs(y - g) <= 1:
                w.set(px + dx, y, pz + dz, bl.LAVA)
                w.set(px + dx, y - 1, pz + dz, B("magma"))
        for (dx, dz) in kit._ring(3.6 + (k % 2)):
            y = w.top(px + dx, pz + dz)
            if y is not None and w.get(px + dx, y, pz + dz) != bl.LAVA:
                w.set(px + dx, y, pz + dz, B("magma") if rng.random() < 0.4 else B("blackstone"))
        for _pass in range(3):                       # keep every lava cell boxed in
            for (dx, dz) in kit.disc_cells(4.5):
                x, z = px + dx, pz + dz
                for y in range(g - 2, g + 4):
                    if w.get(x, y, z) == bl.LAVA and any(
                            w.get(x + ax, y, z + az) == 0 for ax, az in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        w.set(x, y, z, B("magma"))
    for (dx, dz) in kit.disc_cells(11):
        w.fill(hx + dx, g - 3, hz + dz + 2, hx + dx, g, hz + dz + 2, B("blackstone"))
    portal_gate(w, hx, g + 1, hz + 4, "x", "function bear/warp/hell", "N",
                "§c§l지옥문\n§r발판을 밟으면\n지옥으로 이동")
    # basalt spires around the crater
    for k in range(10):
        a = k * 0.63
        rr = 24 + (k % 4) * 3
        px, pz = hx + int(rr * math.cos(a)), hz + int(rr * math.sin(a))
        if abs(px - hx) < 9 and pz < hz:
            continue
        y = w.top(px, pz)
        if y is None:
            continue
        hh = int(rng.integers(4, 11))
        for i in range(hh):
            w.set(px, y + 1 + i, pz, B("basalt", pillar_axis="y") if rng.random() < 0.7 else B("polished_basalt", pillar_axis="y"))
            if i < hh // 2:
                for (dx, dz) in ((1, 0), (0, 1)):
                    w.set(px + dx, y + 1 + i, pz + dz, B("basalt", pillar_axis="y"))
        if k % 3 == 0:
            w.set(px, y + 1 + hh, pz, B("netherrack"))
            w.set(px, y + 2 + hh, pz, B("fire", age=0))
    dk.warp("hellgate", 0, hx + 0.5, g + 1, hz - 8.5, (hx, g + 3, hz + 4))
    dk.zone(0, hx - 14, g - 6, hz - 14, hx + 14, g + 30, hz + 14)


def hub(w, log=print):
    rng = w.rng
    hx, hz = HUB
    y = NF
    # plaza
    for (dx, dz) in kit.disc_cells(17.5):
        r = math.hypot(dx, dz)
        ang = math.degrees(math.atan2(dz, dx)) % 90
        spoke = min(ang, 90 - ang) * math.pi / 180 * r < 1.1
        b = B("gilded_blackstone") if (spoke and int(r) % 4 == 2) else (
            B("polished_blackstone") if spoke or 11.5 < r <= 12.5 else bb_mix())
        w.set(hx + dx, y, hz + dz, b if r <= 16.5 else B("blackstone"))
        w.fill(hx + dx, y + 1, hz + dz, hx + dx, y + 8, hz + dz, AIR)
    portal_gate(w, hx, y + 1, hz + 9, "x", "function bear/warp/town", "N", "§b§l귀환의 문\n§r발판을 밟으면\n마을로 이동")
    # three exits with arches
    gates = [("N", 0, -20, "§c§l지옥 던전\n§r불타는 협곡\n§8북쪽 협곡", nb_mix(), "red_nether_brick"),
             ("E", 22, 0, "§4§l네더 요새\n§r위더의 성채\n§8동쪽 터널", nb_mix(), "nether_brick"),
             ("W", -22, 0, "§6§l피글린 요새\n§r황금 보루\n§8서쪽 터널", bb_mix(), "polished_blackstone_brick")]
    for face, ox, oz, text, mat, stair in gates:
        F = Frame(w, hx + ox, y, hz + oz, {"S": 0, "W": 1, "N": 2, "E": 3}[face])
        for lx in (-5, -4, 4, 5):
            for ly in range(1, 9):
                F.set(lx, ly, 0, mat)
                F.set(lx, ly, 1, mat) if abs(lx) == 5 else None
            F.set(lx, 0, 0, mat)
        for lx in range(-5, 6):
            F.set(lx, 8, 0, mat)
            F.set(lx, 9, 0, mat if lx % 2 == 0 else bl.slab(stair))
        F.stairs(-3, 7, 0, stair, "W", top=True)
        F.stairs(3, 7, 0, stair, "E", top=True)
        F.stairs(-3, 6, 0, stair, "W", top=True) if False else None
        F.set(0, 7, 0, bl.lantern(True, soul=(face != "E")))
        F.sign(-4, 4, -1, "N", text, wood="crimson", glow=True)
        F.sign(4, 4, -1, "N", text, wood="crimson", glow=True)
        for lx in range(-3, 4):
            for lz in range(-3, 8):
                F.set(lx, 0, lz, mat)
        for lx in (-5, 5):
            F.set(lx, 9, 0, B("netherrack"))
            F.set(lx, 10, 0, B("fire", age=0))
    # lamps + info
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        lx, lz = hx + int(round(14 * math.cos(a))), hz + int(round(14 * math.sin(a)))
        w.set(lx, y + 1, lz, B("polished_blackstone_brick_wall", wall_post_bit=True))
        w.set(lx, y + 2, lz, B("polished_blackstone_brick_wall", wall_post_bit=True))
        w.set(lx, y + 3, lz, bl.lantern(soul=(k % 2 == 0)))
    dk.sign(w, hx - 2, y + 1, hz - 3, "N", "§l지옥 허브\n§r세 갈래 길이\n던전으로 이어진다", wood="crimson", standing=True)
    dk.sign(w, hx + 2, y + 1, hz - 3, "N", "§l주의!\n§r화염 저항 물약과\n황금 투구를\n준비하세요", wood="crimson", standing=True)
    w.put(hx + 6, y + 1, hz + 3, bl.chest("W"), bl.be_chest([bl.item("potion", 2, 13), bl.item("golden_carrot", 8),
                                                            bl.item("golden_helmet", 1)]))
    dk.warp("hell", 1, hx + 0.5, y + 1, hz + 3.5, (hx, y + 2, hz - 20))
    dk.zone(1, NX0, 0, NZ0, NX1 - 1, 127, NZ1 - 1)


def huge_fungus(w, x, y, z, rng, warped=False):
    stem = B("warped_stem" if warped else "crimson_stem", pillar_axis="y")
    cap = B("warped_wart_block" if warped else "nether_wart_block")
    h = int(rng.integers(6, 13))
    for i in range(h):
        w.set(x, y + i, z, stem)
    r = 2.5 + rng.random() * 1.5
    for dy, rr in ((h - 3, r), (h - 2, r + 0.6), (h - 1, r), (h, r - 1.0), (h + 1, 0.8)):
        for (dx, dz) in kit.disc_cells(rr):
            if w.get(x + dx, y + dy, z + dz) == 0:
                b = B("shroomlight") if rng.random() < 0.06 else cap
                w.set(x + dx, y + dy, z + dz, b)
                if dy == h - 3 and not warped and rng.random() < 0.35:
                    for k in range(1, int(rng.integers(2, 6))):
                        if w.get(x + dx, y + dy - k, z + dz) == 0:
                            w.set(x + dx, y + dy - k, z + dz, B("weeping_vines", weeping_vines_age=25 if k > 3 else 0))
                        else:
                            break


def canyon(w, log=print):
    rng = w.rng
    m = w.masks
    sx, sz = w.sx, w.sz
    Fi = np.round(w.cav_F).astype(int)
    # ---- surface dressing by section -------------------------------------------
    xs, zs = np.nonzero(m["in_can"] & ~m["chasm"])
    for x, z in zip(xs, zs):
        y = Fi[x, z]
        wx, wz = x + w.x0, z + w.z0
        if w.b[x, z, y] == 0 or w.b[x, z, y + 1] != 0:
            continue
        c, s_ = m["crim"][x, z], m["soul"][x, z]
        r = rng.random()
        if c > 0.35:
            warped = (wx > 14) and r < 0.9
            w.b[x, z, y] = B("warped_nylium") if warped else B("crimson_nylium")
            if r < 0.10:
                w.b[x, z, y + 1] = B("warped_roots") if warped else B("crimson_roots")
            elif r < 0.14:
                w.b[x, z, y + 1] = B("warped_fungus") if warped else B("crimson_fungus")
            elif r < 0.17 and warped:
                w.b[x, z, y + 1] = B("nether_sprouts")
            elif r < 0.19 and warped:
                for k in range(1, int(rng.integers(2, 6))):
                    w.b[x, z, y + k] = B("twisting_vines", twisting_vines_age=25)
        elif s_ > 0.35:
            w.b[x, z, y] = B("soul_sand") if r < 0.6 else B("soul_soil")
            w.b[x, z, y - 1] = B("soul_soil")
            if r > 0.985 and w.b[x, z, y] == B("soul_soil"):
                w.b[x, z, y + 1] = B("soul_fire", age=0)
        else:
            if r < 0.006:
                w.b[x, z, y + 1] = B("fire", age=0)
                w.b[x, z, y] = B("netherrack")
            elif r < 0.03:
                w.b[x, z, y] = B("magma")
    # huge fungi
    for _ in range(140):
        wx, wz = int(rng.integers(-48, 49)), int(rng.integers(-98, -36))
        x, z = wx - w.x0, wz - w.z0
        if m["crim"][x, z] > 0.4 and m["in_can"][x, z]:
            y = Fi[x, z]
            if w.b[x, z, y] in (B("crimson_nylium"), B("warped_nylium")) and w.b[x, z, y + 8] == 0:
                near = any(w.get(wx + dx, y + 2, wz + dz) != 0 for dx in range(-3, 4) for dz in range(-3, 4))
                if not near:
                    huge_fungus(w, wx, y + 1, wz, rng, warped=(w.b[x, z, y] == B("warped_nylium")))
    # walking path through the crimson cavern
    path = Mix((B("blackstone"), 3), (B("polished_blackstone_bricks"), 3), (B("netherrack"), 1))
    for (a, b_) in zip(CANYON[:-1], CANYON[1:]):
        n = int(max(abs(b_[0] - a[0]), abs(b_[1] - a[1]))) + 1
        for i in range(n + 1):
            px = int(round(a[0] + (b_[0] - a[0]) * i / n))
            pz = int(round(a[1] + (b_[1] - a[1]) * i / n))
            x, z = px - w.x0, pz - w.z0
            if m["crim"][x, z] > 0.3 or m["soul"][x, z] > 0.3:
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        y = top_floor(w, px + dx, pz + dz, NF + 6, NF - 5)
                        if y is not None and w.get(px + dx, y + 1, pz + dz) == 0 and rng.random() < 0.8:
                            w.set(px + dx, y, pz + dz, path)
                        elif y is not None and w.get(px + dx, y + 1, pz + dz) in (
                                B("crimson_roots"), B("crimson_fungus"), B("warped_roots"), B("soul_fire", age=0)):
                            w.set(px + dx, y + 1, pz + dz, AIR)
                            w.set(px + dx, y, pz + dz, path)
    # ---- bridges over the lava chasm (section 1 + 3) -----------------------------------
    nb = nb_mix()
    for (bx, bz) in ((-9, 16), (-2, -20), (5, -150)):
        for dz in (-1, 0, 1):
            for dx in range(-9, 10):
                x, z = bx + dx, bz + dz
                if w.get(x, NF, z) in (0, bl.LAVA) or w.get(x, NF + 1, z) == 0:
                    if w.get(x, NF, z) in (0, bl.LAVA):
                        w.set(x, NF, z, nb)
                        w.set(x, NF - 1, z, bl.stairs("nether_brick", "E" if dx < 0 else "W", top=True)) if abs(
                            dx) in (3, 4) and dz == 0 else None
            for dx in range(-9, 10):
                x, z = bx + dx, bz + dz
                if abs(dz) == 1 and w.get(x, NF + 1, z) == 0 and w.get(x, NF - 1, z) in (0, bl.LAVA):
                    w.set(x, NF + 1, z, bl.fence("nether_brick"))
    # ---- section 1: magma cube den + chest ---------------------------------------------------
    for (sxp, szp, ent) in ((12, 8, "magma_cube"), (-20, -18, "zombie_pigman")):
        y = top_floor(w, sxp, szp, NF + 6, NF - 4)
        if y is not None:
            w.set(sxp, y, szp, B("chiseled_nether_bricks"))
            dk.spawner(w, sxp, y + 1, szp, ent)
            for (dx, dz) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                w.set(sxp + dx, y, szp + dz, nb)
                w.set(sxp + dx, y + 1, szp + dz, bl.fence("nether_brick"))
    y = top_floor(w, -12, 4, NF + 6, NF - 4)
    if y:
        dk.chest(w, -12, y + 1, 4, "E", 3, rng)
    dk.plate(w, 0, NF + 1, 36, "function bear/enter/hell", kind="polished_blackstone_pressure_plate", floor=nb)
    w.set(-1, NF + 1, 36, B("polished_blackstone_pressure_plate"))
    w.set(1, NF + 1, 36, B("polished_blackstone_pressure_plate"))
    w.put(-1, NF - 1, 36, bl.cmd("impulse", "U"), bl.be_cmd("function bear/enter/hell"))
    w.put(1, NF - 1, 36, bl.cmd("impulse", "U"), bl.be_cmd("function bear/enter/hell"))
    w.set(-1, NF, 36, nb)
    w.set(1, NF, 36, nb)
    # ---- section 2: hoglin pen + chest in the crimson forest ---------------------------------------
    for (sxp, szp, ent) in ((-22, -70, "hoglin"), (24, -58, "piglin")):
        y = top_floor(w, sxp, szp, NF + 8, NF - 4)
        if y is not None:
            w.set(sxp, y, szp, B("chiseled_polished_blackstone"))
            dk.spawner(w, sxp, y + 1, szp, ent, max_nearby=4)
    y = top_floor(w, 30, -72, NF + 8, NF - 4)
    if y:
        dk.chest(w, 30, y + 1, -72, "W", 3, rng, extra=[bl.item("golden_helmet"), bl.item("gold_ingot", 8)])
    # ---- section 3: soul sand valley with a giant fossil -------------------------------------------
    bone = B("bone_block", pillar_axis="y")
    fx, fz = -4, -128
    fy = (top_floor(w, fx, fz, NF + 8, NF - 4) or NF)
    for k in range(-10, 11, 3):                      # ribs along z
        for t in range(0, 11):
            a = math.pi * t / 10
            rx, ry = int(round(6 * math.cos(a))), int(round(7 * math.sin(a)))
            if w.get(fx + rx, fy + 1 + ry, fz + k) == 0:
                w.set(fx + rx, fy + 1 + ry, fz + k, B("bone_block", pillar_axis="x" if 3 < t < 7 else "y"))
    for k in range(-12, 13):
        w.set(fx, fy + 8, fz + k, B("bone_block", pillar_axis="z"))
    for (dx, dy, dz) in [(a, b_, c) for a in range(-2, 3) for b_ in range(0, 4) for c in range(0, 4)]:
        if abs(dx) == 2 or dy in (0, 3) or dz in (0, 3):
            w.set(fx + dx, fy + 5 + dy, fz - 16 + dz - 3, bone)
    w.set(fx - 1, fy + 7, fz - 20, AIR)
    w.set(fx + 1, fy + 7, fz - 20, AIR)
    for k in range(10):                              # basalt pillars
        a = k * 1.9
        px, pz = int(rng.integers(-22, 23)), int(rng.integers(-150, -108))
        x, z = px - w.x0, pz - w.z0
        if m["in_can"][x, z] and m["dcan"][x, z] > 4:
            y0 = Fi[x, z]
            for yy in range(y0 + 1, y0 + 40):
                if w.get(px, yy, pz) != 0:
                    break
                w.set(px, yy, pz, B("basalt", pillar_axis="y"))
                if (yy - y0) < 6:
                    w.set(px + 1, yy, pz, B("polished_basalt", pillar_axis="y"), keep=True)
    for (sxp, szp, ent) in ((-14, -118, "skeleton"), (14, -138, "skeleton"), (6, -112, "wither_skeleton")):
        y = top_floor(w, sxp, szp, NF + 8, NF - 4)
        if y is not None:
            w.set(sxp, y, szp, B("polished_basalt", pillar_axis="y"))
            dk.spawner(w, sxp, y + 1, szp, ent)
    y = top_floor(w, -18, -134, NF + 8, NF - 4)
    if y:
        dk.chest(w, -18, y + 1, -134, "E", 3, rng, extra=[bl.item("potion", 1, 13), bl.item("diamond", 2)])
    # ---- section 4: arena on the lava lake ------------------------------------------------------
    ax, az, ar = ARENA
    isl = Mix((B("polished_blackstone_bricks"), 5), (B("blackstone"), 3), (B("basalt"), 2), (B("smooth_basalt"), 2))
    for (dx, dz) in kit.disc_cells(15.5):
        r = math.hypot(dx, dz)
        w.fill(ax + dx, 20, az + dz, ax + dx, NF - 1, az + dz, isl)
        w.set(ax + dx, NF, az + dz, B("gilded_blackstone") if (int(r) % 5 == 4 and (dx + dz) % 2 == 0) else (
            B("polished_blackstone") if r > 14.5 or int(r) % 5 == 0 else bb_mix()))
        w.fill(ax + dx, NF + 1, az + dz, ax + dx, NF + 14, az + dz, AIR)
    for k in range(6):
        a = math.radians(k * 60 + 30)
        px, pz = ax + int(round(12 * math.cos(a))), az + int(round(12 * math.sin(a)))
        for yy in range(NF + 1, NF + 7):
            w.set(px, yy, pz, B("polished_basalt", pillar_axis="y"))
        w.set(px, NF + 7, pz, B("netherrack"))
        w.set(px, NF + 8, pz, B("fire", age=0))
    # bridges: south (from the canyon) and north (to the reward ledge)
    for z in range(az + 15, az + ar + 2):
        for dx in (-2, -1, 0, 1, 2):
            w.fill(dx, NF - 2, z, dx, NF, z, isl if abs(dx) < 2 else B("polished_blackstone"))
            w.fill(dx, NF + 1, z, dx, NF + 6, z, AIR)
        if z % 4 == 0:
            for dx in (-2, 2):
                w.set(dx, NF + 1, z, B("polished_blackstone_brick_wall", wall_post_bit=True))
            for dx in (-1, 0, 1):
                for yy in range(22, NF - 2):
                    if w.get(dx, yy, z) in (bl.LAVA, 0) and dx == 0:
                        w.set(dx, yy, z, B("basalt", pillar_axis="y"))
    for z in range(az - ar - 4, az - 15):
        for dx in (-2, -1, 0, 1, 2):
            w.fill(dx, NF - 2, z, dx, NF, z, isl if abs(dx) < 2 else B("polished_blackstone"))
            w.fill(dx, NF + 1, z, dx, NF + 6, z, AIR)
    # reward ledge (north)
    lz = az - ar - 6
    w.fill(-8, 20, lz - 8, 8, NF, lz + 3, isl)
    w.fill(-7, NF + 1, lz - 7, 7, NF + 6, lz + 3, AIR)
    w.fill(-8, NF + 7, lz - 8, 8, NF + 8, lz + 3, B("blackstone"), keep=True)
    for x in range(-7, 8):
        for z in range(lz - 7, lz + 3):
            w.set(x, NF, z, B("gilded_blackstone") if (x + z) % 5 == 0 else bb_mix())
    dk.reward_altar(w, 0, NF + 1, lz - 7, "S", "hell", "지옥 던전 보상")
    dk.chest(w, -6, NF + 1, lz - 7, "S", 4, rng, extra=[bl.item("diamond", 4)])
    dk.chest(w, 6, NF + 1, lz - 7, "S", 3, rng, extra=[bl.item("golden_apple", 3)])
    dk.exit_pad(w, 5, NF + 1, lz - 2, None)
    w.set(-6, NF + 1, lz - 2, B("netherrack"))
    w.set(-6, NF + 2, lz - 2, B("fire", age=0))
    for x in (-1, 0, 1):
        dk.plate(w, x, NF + 1, az + 14, "function bear/boss/hell", kind="polished_blackstone_pressure_plate",
                 floor=B("chiseled_polished_blackstone"))
    dk.sign(w, 3, NF + 1, az + ar - 2, "S", "§c§l용암 투기장\n§r광폭한 군주가\n기다린다", wood="crimson", standing=True, glow=True)
    dk.warp("hell_dungeon", 1, 0.5, NF + 1, 30.5, (0, NF + 2, 0))
    bx, by, bz = ax, NF + 1, az - 4
    dk.boss("hell", {
        "pos": (ax, NF + 1, az + 14),
        "spawn": [
            'summon zoglin "§c용암의 군주" %d %d %d' % (bx, by, bz),
            "tag @e[type=zoglin,x=%d,y=%d,z=%d,r=3,c=1] add boss_hell" % (bx, by, bz),
            "effect @e[tag=boss_hell] health_boost 99999 19 true",
            "effect @e[tag=boss_hell] instant_damage 1 6 true",
            "effect @e[tag=boss_hell] strength 99999 1 true",
            "effect @e[tag=boss_hell] resistance 99999 0 true",
            "summon zoglin %d %d %d" % (bx - 7, by, bz + 2),
            "summon zoglin %d %d %d" % (bx + 7, by, bz + 2),
            "summon blaze %d %d %d" % (bx - 5, by + 4, bz - 5),
            "summon blaze %d %d %d" % (bx + 5, by + 4, bz - 5),
            "summon magma_cube %d %d %d" % (bx, by + 1, bz - 8),
        ],
        "title": "§c용암의 군주", "sub": "§7불타는 협곡의 지배자",
    })
