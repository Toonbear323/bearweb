"""Cave dungeon: Crystal Caverns (mine -> lush grotto -> dripstone lake -> amethyst geode -> deep shrine)."""
import math

import numpy as np

from . import blocks as bl
from . import dkit as dk
from . import kit
from .core import B, Mix
from .kit import Frame
from .layout import BIO_DARK, BIO_DRIP, BIO_LUSH, MINE, MINE_G

AIR = 0


def blob(w, cx, cy, cz, rx, ry, rz, rng, n=7, spread=0.55):
    w.ellipsoid(cx, cy, cz, rx, ry, rz, AIR)
    for _ in range(n):
        ox, oy, oz = (rng.random(3) * 2 - 1) * (rx * spread, ry * spread * 0.6, rz * spread)
        s = 0.45 + rng.random() * 0.4
        w.ellipsoid(cx + ox, cy + oy, cz + oz, rx * s, ry * s, rz * s, AIR)


def tunnel(w, pts, r, rng, flat=True):
    """Winding tunnel through the given points; flat keeps a walkable floor."""
    for (a, b_) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(b_[0] - a[0]), abs(b_[1] - a[1]), abs(b_[2] - a[2]))) + 1
        for i in range(n + 1):
            t = i / n
            x = a[0] + (b_[0] - a[0]) * t + math.sin(i * 0.5) * 0.8
            y = a[1] + (b_[1] - a[1]) * t
            z = a[2] + (b_[2] - a[2]) * t + math.cos(i * 0.4) * 0.8
            rr = r + rng.random() * 0.8
            w.ellipsoid(x, y + rr * 0.7, z, rr, rr * 0.95, rr, AIR)
            if flat:
                w.fill(int(x) - 1, int(round(y)), int(z) - 1, int(x) + 1, int(round(y)) + 2, int(z) + 1, AIR)


_CLUTTER = None


def clear_route(w, pts):
    """Remove walk-blocking decorations (never terrain) from a 3-wide corridor along the polyline."""
    global _CLUTTER
    from .core import REG
    if _CLUTTER is None or len(_CLUTTER) != len(REG.entries):
        _CLUTTER = [any(k in n for k in ("pointed_dripstone", "azalea", "dripleaf", "web", "amethyst_cluster",
                                         "amethyst_bud", "cave_vines", "sculk_sensor")) and n not in (
            "azalea_leaves", "azalea_leaves_flowered") for n, _ in REG.entries]
    for (a, b_) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(b_[0] - a[0]), abs(b_[2] - a[2]), 1))
        for i in range(n + 1):
            t = i / n
            x = int(round(a[0] + (b_[0] - a[0]) * t))
            z = int(round(a[2] + (b_[2] - a[2]) * t))
            yc = int(round(a[1] + (b_[1] - a[1]) * t))
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for y in range(yc - 3, yc + 5):
                        bid_ = w.get(x + dx, y, z + dz)
                        if bid_ and _CLUTTER[bid_]:
                            w.set(x + dx, y, z + dz, AIR)


def skin(w, box, floor=None, ceil=None, wall=None, p_floor=1.0, p_ceil=0.5, p_wall=0.4, base=None):
    """Re-texture the rock touching air inside box.  base = ids that may be replaced."""
    s = w._clip(*box)
    if s is None:
        return
    v = w.b[s]
    rng = w.rng
    air = v == 0
    rock = np.isin(v, list(base)) if base is not None else ~air
    up = np.zeros_like(air)
    up[:, :, :-1] = air[:, :, 1:]
    dn = np.zeros_like(air)
    dn[:, :, 1:] = air[:, :, :-1]
    side = np.zeros_like(air)
    side[1:, :, :] |= air[:-1, :, :]
    side[:-1, :, :] |= air[1:, :, :]
    side[:, 1:, :] |= air[:, :-1, :]
    side[:, :-1, :] |= air[:, 1:, :]
    rnd = rng.random(v.shape)
    for mask, blk, p in ((rock & side & ~up & ~dn, wall, p_wall), (rock & dn, ceil, p_ceil), (rock & up, floor, p_floor)):
        if blk is None:
            continue
        m = mask & (rnd < p)
        if isinstance(blk, Mix):
            v[m] = blk.sample(rng, int(m.sum()))
        else:
            v[m] = blk


def pond(w, cx, cz, rx, rz, y_top, y_bot, rim):
    """Fill a basin with still water and wall in every side / bottom opening so it can never flow."""
    R = int(max(rx, rz)) + 3
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            d_in = (dx / rx) ** 2 + (dz / rz) ** 2
            d_out = (dx / (rx + 1.6)) ** 2 + (dz / (rz + 1.6)) ** 2
            x, z = cx + dx, cz + dz
            if d_in <= 1.0:
                if w.get(x, y_bot - 1, z) == 0:
                    w.set(x, y_bot - 1, z, rim)
                for y in range(y_bot, y_top + 1):
                    if w.get(x, y, z) == 0:
                        w.set(x, y, z, bl.WATER)
            elif d_out <= 1.0:
                for y in range(y_bot, y_top + 1):
                    if w.get(x, y, z) == 0:
                        w.set(x, y, z, rim)


def floor_cells(w, box, n, rng):
    """Random (x,y,z) air cells with solid ground below inside box."""
    x0, y0, z0, x1, y1, z1 = box
    out = []
    tries = 0
    while len(out) < n and tries < n * 30:
        tries += 1
        x, z = int(rng.integers(x0, x1 + 1)), int(rng.integers(z0, z1 + 1))
        ys = [y for y in range(y0, y1) if w.get(x, y, z) == 0 and w.get(x, y - 1, z) not in (0, bl.WATER)]
        if ys:
            out.append((x, ys[0], z))
    return out


def ceil_cells(w, box, n, rng):
    x0, y0, z0, x1, y1, z1 = box
    out = []
    tries = 0
    while len(out) < n and tries < n * 30:
        tries += 1
        x, z = int(rng.integers(x0, x1 + 1)), int(rng.integers(z0, z1 + 1))
        ys = [y for y in range(y1, y0, -1) if w.get(x, y, z) == 0 and w.get(x, y + 1, z) not in (0, bl.WATER)
              and w.get(x, y - 1, z) == 0]
        if ys:
            out.append((x, ys[0], z))
    return out


def stalactite(w, x, y, z, n, hanging=True):
    seq = ["base"] + ["middle"] * max(0, n - 3) + (["frustum"] if n >= 2 else []) + ["tip"]
    seq = seq[-n:] if n < len(seq) else seq
    for i, th in enumerate(seq):
        yy = y - i if hanging else y + i
        if w.get(x, yy, z) != 0:
            # stop early and put a tip on the previous segment
            if i > 0:
                py = y - (i - 1) if hanging else y + (i - 1)
                w.set(x, py, z, B("pointed_dripstone", dripstone_thickness="tip", hanging=hanging))
            return
        w.set(x, yy, z, B("pointed_dripstone", dripstone_thickness=th, hanging=hanging))


def mine_support(w, x, y, z, axis="z"):
    """Timber frame across a 3-wide tunnel centred at x (axis z) or z (axis x)."""
    for s in (-2, 2):
        px, pz = (x + s, z) if axis == "z" else (x, z + s)
        for i in range(0, 3):
            w.set(px, y + i, pz, bl.log("spruce") if i == 0 else bl.fence("spruce"))
    for s in range(-2, 3):
        px, pz = (x + s, z) if axis == "z" else (x, z + s)
        w.set(px, y + 3, pz, bl.planks("spruce") if abs(s) < 2 else bl.log("spruce", "x" if axis == "z" else "z"))


def build(w, T, log=print):
    rng = w.rng
    mx, mz = MINE
    g = MINE_G
    F = Frame(w, 0, 0, 0, 0)
    xi, zi = mx - 16 - w.x0, mz - 12 - w.z0
    T.reserved[xi:xi + 32, zi:zi + 26] = True
    stone = B("stone")
    rockset = {stone, B("deepslate"), B("andesite"), B("diorite"), B("granite"), B("tuff"), B("gravel"), B("dirt"),
               B("coal_ore"), B("iron_ore"), B("copper_ore")}
    # ------------------------------------------------------------------ entrance
    ez = mz - 5                                   # portal plane (faces south)
    w.fill(mx - 6, g, mz - 4, mx + 6, g, mz + 8, Mix((B("gravel"), 4), (bl.block("cobblestone"), 4),
                                                     (B("dirt", dirt_type="coarse"), 3), (B("grass_path"), 2)))
    w.fill(mx - 6, g + 1, mz - 4, mx + 6, g + 14, mz + 8, AIR)
    facade = Mix((bl.block("cobblestone"), 5), (bl.block("stone_brick"), 4), (bl.block("mossy_cobblestone"), 3),
                 (bl.block("andesite"), 2))
    w.fill(mx - 6, g + 1, ez - 2, mx + 6, g + 9, ez, facade)
    w.fill(mx - 2, g + 1, ez - 2, mx + 2, g + 5, ez, AIR)
    for z in range(ez - 2, ez + 1):
        w.set(mx - 2, g + 5, z, bl.stairs("stone_brick", "W", top=True))
        w.set(mx + 2, g + 5, z, bl.stairs("stone_brick", "E", top=True))
    for s in (-3, 3):
        for y in range(g + 1, g + 7):
            w.set(mx + s, y, ez + 1, bl.log("spruce"))
        w.set(mx + s, g + 7, ez + 1, bl.block("stone_brick"))
        w.set(mx + s, g + 8, ez + 1, bl.lantern())
    for x in range(mx - 4, mx + 5):
        w.set(x, g + 6, ez + 1, bl.log("spruce", "x"))
        w.set(x, g + 7, ez + 2, bl.slab("spruce")) if abs(x - mx) < 4 else None
        w.set(x, g + 7, ez + 1, bl.slab("spruce")) if abs(x - mx) < 3 else None
    w.set(mx - 2, g + 5, ez + 1, bl.lantern(True))
    w.set(mx + 2, g + 5, ez + 1, bl.lantern(True))
    dk.sign(w, mx, g + 6, ez + 2, "S", "§8§l동굴 던전\n§r수정 동굴\n§8권장 철 장비·횃불", wood="spruce", glow=True)
    # yard props: carts of ore, crates, campfire
    for i, x in enumerate(range(mx - 1, mx + 2)):
        pass
    for z in range(ez + 2, mz + 7):
        w.set(mx, g + 1, z, B("rail", rail_direction=0))
    w.set(mx - 4, g + 1, mz + 2, B("raw_iron_block"))
    w.set(mx - 5, g + 1, mz + 2, B("coal_block"))
    w.set(mx - 4, g + 1, mz + 3, B("raw_copper_block"))
    w.set(mx - 4, g + 2, mz + 2, B("coal_block"))
    kit.crate_pile(F, mx + 4, g + 1, mz + 1, rng, 5)
    w.set(mx + 4, g + 1, mz + 5, bl.campfire())
    w.set(mx + 5, g + 1, mz + 5, bl.log("spruce", "z"))
    w.set(mx + 3, g + 1, mz + 6, bl.log("spruce", "x"))
    kit.lamp_arm(F, mx - 6, g + 1, mz + 7, "E", h=4, wood="spruce")
    kit.lamp_arm(F, mx + 6, g + 1, mz + 7, "W", h=4, wood="spruce")
    # ------------------------------------------------------------------ mine tunnel (north)
    tz_end = mz - 40
    for z in range(ez - 3, tz_end - 1, -1):
        w.fill(mx - 2, g + 1, z, mx + 2, g + 4, z, AIR)
        w.fill(mx - 1, g + 5, z, mx + 1, g + 5, z, AIR) if rng.random() < 0.3 else None
        for x in range(mx - 2, mx + 3):
            w.set(x, g, z, Mix((B("gravel"), 4), (bl.block("cobblestone"), 3), (B("stone"), 3),
                               (B("dirt", dirt_type="coarse"), 2)))
        w.set(mx, g + 1, z, B("rail", rail_direction=0))
        for s in (-3, 3):                      # ore-streaked walls
            if rng.random() < 0.25:
                w.set(mx + s, g + int(rng.integers(1, 4)), z, Mix(B("coal_ore"), B("iron_ore"), B("copper_ore"),
                                                                 B("coal_ore")))
        k = (ez - 3 - z)
        if k % 5 == 2:
            mine_support(w, mx, g + 1, z, "z")
            if k % 10 == 2:
                w.set(mx, g + 3, z, bl.lantern(True))
    w.set(mx, g + 1, tz_end, bl.block("spruce"))
    for px in (mx - 1, mx + 1):
        dk.plate(w, px, g + 1, ez - 4, "function bear/enter/cave", floor=bl.block("cobblestone"))
    # mine hub with side stope
    hz = tz_end - 6
    blob(w, mx, g + 4, hz, 8, 4.5, 7, rng, n=5)
    w.fill(mx - 6, g + 1, hz - 5, mx + 6, g + 2, hz + 5, AIR)
    skin(w, (mx - 10, g - 1, hz - 9, mx + 10, g + 10, hz + 9),
         floor=Mix((B("gravel"), 3), (bl.block("cobblestone"), 3), (stone, 3), (B("dirt", dirt_type="coarse"), 2)),
         wall=Mix((B("coal_ore"), 2), (B("iron_ore"), 2), (B("copper_ore"), 1), (bl.block("cobblestone"), 2)),
         p_wall=0.12, base=rockset)
    kit.crate_pile(F, mx - 5, g + 1, hz - 2, rng, 5)
    dk.chest(w, mx - 6, g + 1, hz + 2, "E", 1, rng, extra=[bl.item("iron_pickaxe"), bl.item("torch", 24)])
    w.set(mx + 4, g + 1, hz - 3, B("crafting_table"))
    w.set(mx + 5, g + 1, hz - 3, bl.furnace("S"))
    w.set(mx + 3, g + 3, hz, bl.lantern(True)) if w.get(mx + 3, g + 4, hz) != 0 else w.set(mx + 3, g + 1, hz + 3,
                                                                                         bl.lantern())
    w.set(mx - 3, g + 1, hz + 4, bl.lantern())
    # ------------------------------------------------------------------ lush grotto
    L = (mx + 24, 68, mz - 64)                    # centre
    # gentle switch-back descent (never steeper than one block per two) from the hub to the grotto
    T1 = [(mx - 4, g + 1, hz - 5), (mx - 12, g - 4, hz - 12), (mx - 10, g - 9, hz - 22), (mx, g - 13, hz - 24),
          (L[0] - 15, 69, L[2] - 2)]
    tunnel(w, T1, 2.2, rng)
    w.set(mx - 4, g, hz - 4, bl.block("cobblestone"))
    w.set(mx - 4, g + 1, hz - 4, 0)
    dk.sign(w, mx - 4, g + 1, hz - 4, "S", "§l동쪽 굴 아래로\n§r이끼 동굴을 지나\n수정 동굴로", standing=True, wood="spruce")
    blob(w, L[0], L[1] + 5, L[2], 17, 8, 14, rng, n=9)
    w.ellipsoid(L[0], L[1] - 1, L[2], 15, 2.5, 12, AIR)
    # pools
    pools = ((L[0] - 5, L[2] + 5, 4.5), (L[0] + 3, L[2] + 8, 3.5))
    for (px, pz, pr) in pools:
        w.ellipsoid(px, L[1] - 3, pz, pr, 2.5, pr, AIR)
    lbox = (L[0] - 22, L[1] - 8, L[2] - 20, L[0] + 22, L[1] + 18, L[2] + 20)
    for (px, pz, pr) in pools:               # contained pools, water surface one below the cavern floor
        pond(w, px, pz, pr + 1.0, pr + 1.0, L[1] - 4, L[1] - 7, B("clay"))
    skin(w, lbox, floor=Mix((B("moss_block"), 8), (B("clay"), 1), (B("dirt_with_roots"), 1), (B("grass_block"), 1)),
         ceil=Mix((B("moss_block"), 3), (B("dirt_with_roots"), 2), (stone, 4)),
         wall=Mix((B("moss_block"), 3), (stone, 3), (B("clay"), 0.5)), p_floor=0.95, p_ceil=0.6, p_wall=0.5,
         base=rockset)
    w.biome_boxes.append((lbox[0], lbox[1], lbox[2], lbox[3], lbox[4], lbox[5], BIO_LUSH))
    for (x, y, z) in floor_cells(w, lbox, 240, rng):
        r = rng.random()
        if w.get(x, y - 1, z) not in (B("moss_block"), B("grass_block"), B("dirt_with_roots")):
            continue
        if r < 0.30:
            w.set(x, y, z, B("moss_carpet"))
        elif r < 0.5:
            w.set(x, y, z, B("short_grass"))
        elif r < 0.62:
            w.set(x, y, z, B("azalea") if rng.random() < 0.6 else B("flowering_azalea"))
        elif r < 0.70 and w.get(x, y + 1, z) == 0 and w.get(x, y + 2, z) == 0:
            hh = int(rng.integers(1, 3))
            for i in range(hh):
                w.set(x, y + i, z, B("big_dripleaf", big_dripleaf_head=False, cardinal_direction="south"))
            w.set(x, y + hh, z, B("big_dripleaf", big_dripleaf_head=True, cardinal_direction="south"))
        elif r < 0.75:
            w.set(x, y, z, B("fern"))
        elif r < 0.78 and w.get(x, y + 5, z) == 0:
            # small azalea tree
            hh = int(rng.integers(3, 5))
            for i in range(hh):
                w.set(x, y + i, z, bl.log("oak"))
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    for dy in (0, 1):
                        if abs(dx) + abs(dz) + dy < 4 and rng.random() < 0.85:
                            w.set(x + dx, y + hh + dy - 1, z + dz, bl.leaves(
                                "flowering_azalea" if rng.random() < 0.4 else "azalea"), keep=True)
    for (x, y, z) in ceil_cells(w, lbox, 150, rng):
        r = rng.random()
        if r < 0.55:
            n = int(rng.integers(1, 6))
            for i in range(n):
                if w.get(x, y - i, z) != 0:
                    break
                last = (i == n - 1) or w.get(x, y - i - 1, z) != 0
                berries = rng.random() < 0.45
                if last:
                    w.set(x, y - i, z, B("cave_vines_head_with_berries", growing_plant_age=25) if berries else B(
                        "cave_vines", growing_plant_age=25))
                else:
                    w.set(x, y - i, z, B("cave_vines_body_with_berries", growing_plant_age=0) if berries else B(
                        "cave_vines", growing_plant_age=0))
        elif r < 0.68:
            w.set(x, y, z, B("spore_blossom"))
        elif r < 0.8:
            w.set(x, y, z, B("hanging_roots"))
    for (x, y, z) in floor_cells(w, (L[0] - 12, L[1] - 6, L[2] - 10, L[0] + 12, L[1] - 2, L[2] + 10), 0, rng):
        pass
    # lily pads + dripleaf on the pools
    for _ in range(30):
        x, z = L[0] + int(rng.integers(-14, 15)), L[2] + int(rng.integers(-12, 13))
        if w.get(x, L[1] - 4, z) == bl.WATER and w.get(x, L[1] - 3, z) == 0:
            w.set(x, L[1] - 3, z, B("waterlily"))
    dk.spawner(w, L[0] + 13, L[1] - 1, L[2] + 8, "zombie")
    w.ellipsoid(L[0] + 13, L[1] + 1, L[2] + 8, 3.5, 2.5, 3.5, AIR)
    dk.spawner(w, L[0] + 13, L[1] - 1, L[2] + 8, "zombie")
    w.set(L[0] + 13, L[1] - 2, L[2] + 8, B("mossy_cobblestone"))
    dk.spawner(w, L[0] - 12, L[1], L[2] - 8, "cave_spider")
    for _ in range(14):
        x, y, z = L[0] - 12 + int(rng.integers(-3, 4)), L[1] + int(rng.integers(0, 4)), L[2] - 8 + int(
            rng.integers(-3, 4))
        if w.get(x, y, z) == 0:
            w.set(x, y, z, B("web"))
    cs = floor_cells(w, (L[0] - 3, L[1] - 3, L[2] - 12, L[0] + 3, L[1] + 2, L[2] - 8), 1, rng)
    if cs:
        dk.chest(w, cs[0][0], cs[0][1], cs[0][2], "S", 2, rng)
    # ------------------------------------------------------------------ dripstone cavern
    Dc = (mx + 58, 56, mz - 80)
    T2 = [(L[0] + 13, L[1] - 1, L[2] - 3), (L[0] + 10, 62, L[2] - 11), (Dc[0] - 16, 57, Dc[2] + 2)]
    tunnel(w, T2, 2.2, rng)
    blob(w, Dc[0], Dc[1] + 6, Dc[2], 18, 10, 15, rng, n=9)
    w.ellipsoid(Dc[0], Dc[1] - 1, Dc[2], 16, 4, 13, AIR)
    dbox = (Dc[0] - 24, Dc[1] - 8, Dc[2] - 21, Dc[0] + 24, Dc[1] + 22, Dc[2] + 21)
    pond(w, Dc[0], Dc[2], 17.5, 14.5, Dc[1] - 3, Dc[1] - 8, B("dripstone_block"))
    skin(w, dbox, floor=Mix((B("dripstone_block"), 4), (stone, 4), (B("gravel"), 1), (B("calcite"), 1)),
         ceil=Mix((B("dripstone_block"), 5), (stone, 4)), wall=Mix((B("dripstone_block"), 2), (stone, 5),
                                                                   (B("copper_ore"), 0.4), (B("tuff"), 1)),
         p_floor=0.8, p_ceil=0.7, p_wall=0.5, base=rockset)
    w.biome_boxes.append((dbox[0], dbox[1], dbox[2], dbox[3], dbox[4], dbox[5], BIO_DRIP))
    for (x, y, z) in ceil_cells(w, dbox, 260, rng):
        stalactite(w, x, y, z, int(rng.integers(1, 7)), hanging=True)
    for (x, y, z) in floor_cells(w, dbox, 150, rng):
        if abs(x - Dc[0]) < 3 and abs(z - Dc[2]) < 20:
            continue
        stalactite(w, x, y, z, int(rng.integers(1, 5)), hanging=False)
    for k in range(5):                                   # big columns
        a = k * 1.3 + 0.4
        px, pz = Dc[0] + int(11 * math.cos(a)), Dc[2] + int(9 * math.sin(a))
        for y in range(Dc[1] - 6, Dc[1] + 20):
            if w.get(px, y, pz) in (0, bl.WATER):
                w.set(px, y, pz, B("dripstone_block"))
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if rng.random() < 0.35 and w.get(px + dx, y, pz + dz) in (0, bl.WATER):
                        w.set(px + dx, y, pz + dz, B("dripstone_block"))
    # plank bridge across the lake (west -> east)
    by = Dc[1] - 2
    for x in range(Dc[0] - 17, Dc[0] + 18):
        for z in (Dc[2] + 3, Dc[2] + 4, Dc[2] + 5):
            if w.get(x, by, z) in (0, bl.WATER) or w.get(x, by + 1, z) != 0:
                w.fill(x, by + 1, z, x, by + 3, z, AIR)
                w.set(x, by, z, bl.slab("spruce", top=True) if (x + z) % 5 else bl.planks("spruce"))
        for z in (Dc[2] + 2, Dc[2] + 6):
            if w.get(x, by, z) in (0, bl.WATER) and x % 4 == 0:
                w.set(x, by, z, bl.log("spruce", "y"))
                w.set(x, by + 1, z, bl.fence("spruce"))
                yy = by - 1
                while yy > Dc[1] - 9 and w.get(x, yy, z) in (0, bl.WATER):
                    w.set(x, yy, z, bl.log("spruce", "y"))
                    yy -= 1
                if x % 8 == 0:
                    w.set(x, by + 2, z, bl.lantern(soul=True))
    dk.spawner(w, Dc[0] - 2, Dc[1] + 1, Dc[2] - 9, "skeleton")
    w.set(Dc[0] - 2, Dc[1], Dc[2] - 9, B("dripstone_block"))
    w.ellipsoid(Dc[0] - 2, Dc[1] + 3, Dc[2] - 9, 3, 2.5, 3, AIR)
    dk.spawner(w, Dc[0] - 2, Dc[1] + 1, Dc[2] - 9, "skeleton")
    dk.spawner(w, Dc[0] + 10, Dc[1] - 1, Dc[2] + 11, "spider")
    w.set(Dc[0] + 10, Dc[1] - 2, Dc[2] + 11, B("dripstone_block"))
    cs = floor_cells(w, (Dc[0] + 12, Dc[1] - 2, Dc[2] - 12, Dc[0] + 17, Dc[1] + 4, Dc[2] - 6), 1, rng)
    if cs:
        dk.chest(w, cs[0][0], cs[0][1], cs[0][2], "W", 2, rng, extra=[bl.item("diamond", 1)])
    # ------------------------------------------------------------------ amethyst geode
    Gc = (mx + 74, 50, mz - 46)
    R = 14
    T3 = [(Dc[0] + 16, Dc[1] - 1, Dc[2] + 6), (Dc[0] + 21, Dc[1] - 1, Dc[2] + 7), (Dc[0] + 28, 50, Dc[2] + 12),
          (Gc[0] + 4, 46, Gc[2] - R - 5), (Gc[0], 44, Gc[2] - R - 2)]
    tunnel(w, T3, 2.0, rng)
    w.sphere(Gc[0], Gc[1], Gc[2], R + 2.5, B("smooth_basalt"), only=rockset | {AIR})
    w.sphere(Gc[0], Gc[1], Gc[2], R + 1.5, B("calcite"))
    w.sphere(Gc[0], Gc[1], Gc[2], R + 0.5, Mix((B("amethyst_block"), 12), (B("budding_amethyst"), 1)))
    w.sphere(Gc[0], Gc[1], Gc[2], R - 0.5, AIR)
    fy = Gc[1] - 7
    w.fill(Gc[0] - R, Gc[1] - R, Gc[2] - R, Gc[0] + R, fy, Gc[2] + R,
           Mix((B("amethyst_block"), 10), (B("calcite"), 2), (B("budding_amethyst"), 1)), only={AIR})
    # re-open the entrance tunnel mouth through the shell
    w.fill(Gc[0] - 1, fy + 1, Gc[2] - R - 6, Gc[0] + 1, fy + 3, Gc[2] - R + 2, AIR)
    for z in range(Gc[2] - R - 6, Gc[2] - R + 3):
        for x in (Gc[0] - 1, Gc[0], Gc[0] + 1):
            if w.get(x, fy, z) == 0:
                w.set(x, fy, z, B("calcite"))
    # crystals
    glass = [B("purple_stained_glass"), B("magenta_stained_glass"), B("amethyst_block"), B("amethyst_block")]

    def crystal(x, y, z, h, fat=False):
        for i in range(h):
            b = glass[int(rng.integers(0, 4))]
            w.set(x, y + i, z, b)
            if fat and i < h - 2:
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if i < h - 2 - abs(dx + dz) * int(rng.integers(0, 3)):
                        w.set(x + dx, y + i, z + dz, glass[int(rng.integers(0, 4))])
        w.set(x, y + h, z, B("amethyst_cluster", block_face="up"))

    crystal(Gc[0], fy + 1, Gc[2], 9, fat=True)
    w.set(Gc[0], fy + 3, Gc[2], B("pearlescent_froglight"))
    w.set(Gc[0], fy + 6, Gc[2], B("pearlescent_froglight"))
    for k in range(16):
        a = k * 2.4
        rr = 4 + (k % 4) * 2.2
        x, z = Gc[0] + int(rr * math.cos(a)), Gc[2] + int(rr * math.sin(a))
        if abs(x - Gc[0]) <= 1 and z < Gc[2] - 4:
            continue
        if w.get(x, fy + 1, z) == 0:
            crystal(x, fy + 1, z, int(rng.integers(2, 6)), fat=(k % 5 == 0))
    # clusters on the inner surface
    gb = (Gc[0] - R, fy + 1, Gc[2] - R, Gc[0] + R, Gc[1] + R, Gc[2] + R)
    faces = {"up": (0, -1, 0), "down": (0, 1, 0), "north": (0, 0, 1), "south": (0, 0, -1), "west": (1, 0, 0),
             "east": (-1, 0, 0)}
    am = {B("amethyst_block"), B("budding_amethyst")}
    for _ in range(1500):
        x, y, z = (int(rng.integers(gb[0], gb[3] + 1)), int(rng.integers(gb[1], gb[4] + 1)),
                   int(rng.integers(gb[2], gb[5] + 1)))
        if w.get(x, y, z) != 0:
            continue
        for face, (dx, dy, dz) in faces.items():
            if w.get(x + dx, y + dy, z + dz) in am:
                r = rng.random()
                nm = "amethyst_cluster" if r < 0.5 else ("large_amethyst_bud" if r < 0.8 else "medium_amethyst_bud")
                w.set(x, y, z, B(nm, block_face=face))
                break
    for (dx, dz) in ((6, 6), (-6, 6), (6, -6), (-6, -6)):
        w.set(Gc[0] + dx, fy, Gc[2] + dz, B("pearlescent_froglight"))
    dk.chest(w, Gc[0] + 9, fy + 1, Gc[2] + 2, "W", 3, rng, extra=[bl.item("amethyst_shard", 12)])
    dk.sign(w, Gc[0] + 2, fy + 1, Gc[2] - R + 3, "S", "§d§l자수정 정동\n§r서쪽 계단 아래\n심층 제단", standing=True,
            wood="crimson")
    # ------------------------------------------------------------------ deep shrine
    SY = 30                                       # shrine floor block
    deep = Mix((B("deepslate_bricks"), 8), (B("cracked_deepslate_bricks"), 2), (B("deepslate_tiles"), 4),
               (B("cobbled_deepslate"), 2), (B("polished_deepslate"), 1))
    sfloor = Mix((B("deepslate_tiles"), 6), (B("polished_deepslate"), 3), (B("sculk"), 3),
                 (B("cracked_deepslate_tiles"), 1))
    # stair corridor from the geode's west side heading west and down
    sx_, sz_ = Gc[0] - R + 1, Gc[2]
    n_steps = fy - SY
    for i in range(n_steps + 1):
        x = sx_ - 2 - i
        y = fy - i
        w.fill(x, y - 1, sz_ - 2, x, y + 5, sz_ + 2, deep)
        w.fill(x, y + 1, sz_ - 1, x, y + 4, sz_ + 1, AIR)
        for z in (sz_ - 1, sz_, sz_ + 1):
            w.set(x, y, z, bl.stairs("deepslate_tile", "E") if i > 0 else B("calcite"))
        if i % 5 == 3:
            w.set(x, y + 4, sz_, bl.lantern(True, soul=True))
            w.set(x, y + 1, sz_ - 1, B("sculk_vein", multi_face_direction_bits=1)) if False else None
    w.fill(sx_ - 2, fy + 1, sz_ - 1, sx_ + 1, fy + 3, sz_ + 1, AIR)
    hx1 = sx_ - 3 - n_steps                        # east end of the shrine hall
    P = dk.Plan(w, deep, floor=sfloor, ceil=Mix((B("deepslate_tiles"), 5), (B("deepslate_bricks"), 3)))
    P.room(hx1 - 5, SY + 1, sz_ - 2, hx1, SY + 5, sz_ + 2)                     # antechamber
    HALL = P.room(hx1 - 32, SY + 1, sz_ - 9, hx1 - 7, SY + 10, sz_ + 9)         # shrine hall
    P.room(hx1 - 6, SY + 1, sz_ - 1, hx1 - 6, SY + 4, sz_ + 1)
    VAULT = P.room(hx1 - 43, SY + 1, sz_ - 4, hx1 - 35, SY + 5, sz_ + 4)
    P.room(hx1 - 34, SY + 1, sz_ - 1, hx1 - 33, SY + 3, sz_ + 1)
    P.carve()
    w.fill(hx1 + 1, SY + 1, sz_ - 1, hx1 + 2, SY + 4, sz_ + 1, AIR)
    hx0 = hx1 - 32
    w.biome_boxes.append((hx0 - 14, SY - 4, sz_ - 14, hx1 + 4, SY + 16, sz_ + 14, BIO_DARK))
    for x in range(hx0 + 4, hx1 - 8, 6):
        for z in (sz_ - 6, sz_ + 6):
            dk.pillar(w, x, SY + 1, SY + 10, z, "deepslate_brick", body=B("polished_deepslate"))
            w.set(x, SY + 4, z, B("chiseled_deepslate"))
            w.set(x, SY + 5, z + (1 if z < sz_ else -1), bl.lantern(soul=True)) if False else None
            w.set(x, SY + 6, z + (1 if z < sz_ else -1), bl.torch("N" if z < sz_ else "S", "soul_torch"))
    # sculk growth + ancient-city details
    hb = (hx0, SY + 1, sz_ - 9, hx1 - 7, SY + 10, sz_ + 9)
    for (x, y, z) in floor_cells(w, hb, 70, rng):
        r = rng.random()
        if w.get(x, y - 1, z) == B("sculk"):
            if r < 0.12:
                w.set(x, y, z, B("sculk_sensor", sculk_sensor_phase=0))
            elif r < 0.5:
                w.set(x, y, z, B("sculk_vein", multi_face_direction_bits=1))
    for (x, z) in ((hx0 + 7, sz_ - 3), (hx0 + 19, sz_ + 4)):
        w.set(x, SY, z, B("sculk_catalyst"))
    for z in range(sz_ - 1, sz_ + 2):
        for x in range(hx0 + 6, hx1 - 7):
            w.set(x, SY + 1, z, B("cyan_carpet") if z == sz_ else B("light_blue_carpet"))
    # reinforced-deepslate frame behind the dais (west end)
    w.fill(hx0, SY + 1, sz_ - 5, hx0 + 4, SY + 1, sz_ + 5, B("polished_deepslate"))
    for z in range(sz_ - 5, sz_ + 6):
        w.set(hx0 + 5, SY + 1, z, bl.stairs("polished_deepslate", "W"))
    for z in range(sz_ - 4, sz_ + 5):
        for y in range(SY + 2, SY + 9):
            edge = abs(z - sz_) == 4 or y == SY + 8
            w.set(hx0 - 1, y, z, B("reinforced_deepslate") if edge else B("sculk"))
            if not edge and (y + z) % 3 == 0:
                w.set(hx0 - 1, y, z, B("deepslate_tiles"))
    # doorway to the vault through the middle of the frame
    w.fill(hx0 - 2, SY + 1, sz_ - 1, hx0 - 1, SY + 1, sz_ + 1, B("polished_deepslate"))
    w.fill(hx0 - 2, SY + 2, sz_ - 1, hx0 - 1, SY + 4, sz_ + 1, AIR)
    for z in (sz_ - 5, sz_ + 5):
        w.set(hx0 + 1, SY + 2, z, B("soul_lantern", hanging=False))
        dk.brazier(w, hx0 + 3, SY + 2, z, soul=True)
    for z in (sz_ - 8, sz_ + 8):
        dk.brazier(w, hx1 - 9, SY + 1, z, soul=True)
    for z in (sz_ - 1, sz_, sz_ + 1):
        dk.plate(w, hx1 - 8, SY + 1, z, "function bear/boss/cave", kind="polished_blackstone_pressure_plate",
                 floor=B("polished_deepslate"))
        w.set(hx1 - 8, SY + 1, z, B("polished_blackstone_pressure_plate"))
    dk.sign(w, hx1 - 2, SY + 3, sz_ - 2, "S", "§3§l심층 제단\n§r깊은 어둠의 주인이\n기다린다", glow=True) if False else None
    dk.sign(w, hx1 - 1, SY + 2, sz_ - 3, "S", "§3§l심층 제단\n§r어둠의 주인이\n기다린다", glow=True)
    w.set(hx1 - 1, SY + 2, sz_ - 4, deep) if False else None
    w.set(hx1 - 3, SY + 5, sz_, bl.lantern(True, soul=True))
    # vault
    vx0, _, vz0, vx1, _, vz1 = VAULT
    dk.reward_altar(w, vx0, SY + 1, sz_, "E", "cave", "동굴 던전 보상")
    dk.chest(w, vx0 + 2, SY + 1, vz0, "S", 2, rng, extra=[bl.item("diamond", 3)])
    dk.chest(w, vx0 + 5, SY + 1, vz0, "S", 3, rng)
    dk.chest(w, vx0 + 2, SY + 1, vz1, "N", 2, rng, extra=[bl.item("iron_pickaxe", ench=dk.ench(("efficiency", 3)))])
    dk.exit_pad(w, vx0 + 6, SY + 1, vz1 - 1, None)
    w.set(vx1, SY + 5, vz0, bl.lantern(True, soul=True))
    w.set(vx1, SY + 5, vz1, bl.lantern(True, soul=True))
    # keep the main route free of stalagmites / bushes
    route = T1 + [(L[0], L[1], L[2])] + T2 + [(Dc[0] - 16, Dc[1] - 1, Dc[2] + 4), (Dc[0] + 16, Dc[1] - 1, Dc[2] + 4)] + T3
    clear_route(w, route)
    # registry
    dk.warp("cave", 0, mx + 0.5, g + 1, mz + 5.5, (mx, g + 2, mz - 10))
    dk.zone(0, mx - 10, 15, mz - 104, mx + 96, 100, mz + 10)
    bx, by, bz = hx0 + 8, SY + 1, sz_
    dk.boss("cave", {
        "pos": (hx1 - 8, SY + 1, sz_),
        "spawn": [
            'summon vindicator "§3심연의 광부 대장" %d %d %d' % (bx, by, bz),
            "tag @e[type=vindicator,x=%d,y=%d,z=%d,r=3,c=1] add boss_cave" % (bx, by, bz),
            "effect @e[tag=boss_cave] health_boost 99999 14 true",
            "effect @e[tag=boss_cave] instant_health 1 6 true",
            "effect @e[tag=boss_cave] resistance 99999 0 true",
            "summon cave_spider %d %d %d" % (bx + 3, by, bz - 5),
            "summon cave_spider %d %d %d" % (bx + 3, by, bz + 5),
            "summon cave_spider %d %d %d" % (bx + 8, by, bz - 3),
            "summon skeleton %d %d %d" % (bx + 2, by + 1, bz - 3),
            "summon skeleton %d %d %d" % (bx + 2, by + 1, bz + 3),
            "summon witch %d %d %d" % (bx - 4, by + 1, bz),
        ],
        "title": "§3심연의 광부 대장", "sub": "§7수정 동굴의 지배자",
    })
