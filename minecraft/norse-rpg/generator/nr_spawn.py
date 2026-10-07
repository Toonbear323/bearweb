"""Spawn harbour 'Vik' (512 x 800): a fjord harbour town between snowy mountains and the open sea.

World box x -256..255, z -400..399. North (-Z) = mountains and the head of the fjord, south (+Z) = open sea.
The town sits on the east bank of the fjord; ten longships (one per dungeon) are moored at its piers.
"""
import math
import random

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from mcw import Area, B, AIR, PAL, sign_be, banner_be
from gen_common import fbm, smoothstep, stair, slab, leaves_of, log_of, leaf_blob, disk, spruce_tree, birch_tree, bush, \
    FLOWERS, tall_plant, wall_sign, standing_sign, hanging_lamp, lamp_post, boulder, line_points, big_oak
import nr_parts as P

X0, Z0, SX, SZ = -256, -400, 512, 800
Y0, SY = 16, 192
SEA = 62                       # top water block
TOWN_Y = 64                    # boardwalk / quay top


class Spawn:
    def __init__(self, seed=7):
        self.a = Area("spawn", X0, Z0, SX, SZ, y0=Y0, sy=SY, biome=1)
        self.rng = random.Random(seed)
        self.seed = seed
        xs = np.arange(X0, X0 + SX)
        zs = np.arange(Z0, Z0 + SZ)
        self.X, self.Z = np.meshgrid(xs, zs, indexing="ij")
        self.ships = []            # dict(dungeon, deck box, sign)
        self.stations = {}
        self.points = {}
        self.npcs = []
        self.no_walk = []

    # ------------------------------------------------------------ helpers
    def idx(self, x, z):
        return x - X0, z - Z0

    def h(self, x, z):
        i, k = self.idx(x, z)
        return int(self.H[i, k])

    def top(self, x, z):
        return P.surface_y(self.a, x, z)

    # ------------------------------------------------------------ terrain
    def fjord_center(self, z):
        z = np.asarray(z, float)
        north = smoothstep(-130, -270, z)
        return -45.0 - 38.0 * north + 9.0 * np.sin(z / 37.0) * north

    def fjord_half(self, z):
        z = np.asarray(z, float)
        hw = 50.0 - 26.0 * smoothstep(-140, -280, z)
        return hw

    def terrain(self):
        X, Z = self.X, self.Z
        s = self.seed
        n1 = fbm(SX, SZ, 110, 5, s + 1)
        n2 = fbm(SX, SZ, 34, 4, s + 2)
        wx = (fbm(SX, SZ, 80, 3, s + 11) - 0.5) * 70              # domain warp
        wz = (fbm(SX, SZ, 80, 3, s + 12) - 0.5) * 70
        ridge = 1 - np.abs(fbm(SX, SZ, 60, 5, s + 3) * 2 - 1)
        ridge2 = 1 - np.abs(fbm(SX, SZ, 26, 4, s + 5) * 2 - 1)
        # ---- water: open sea to the south, fjord running north
        coast = 176 + 18 * (fbm(SX, 1, 50, 3, s + 4)[:, 0] - 0.5) * 2
        coast = coast[:, None] + np.zeros_like(Z, float)
        Zw = Z + wz * 0.35
        Xw = X + wx * 0.35
        coast = coast + 58 * np.exp(-((Xw - 112) / 30.0) ** 2) ** 0.7       # rounded east headland (lighthouse)
        coast = coast + 34 * np.exp(-((Xw + 185) / 52.0) ** 2)
        sea = Zw > coast
        fc = self.fjord_center(Z) + (wx * 0.12) * smoothstep(-120, -200, Z)
        fh = self.fjord_half(Z) + (n2 - 0.5) * 8
        fj = (np.abs(X - fc) < fh) & (Z > -282)
        fj &= ~((Z < -262) & (np.hypot(X - fc, Z + 262) > fh))
        water = sea | fj
        for (ix, iz, r) in ((-120, 300, 15), (-30, 342, 9), (170, 330, 13), (62, 368, 7), (-205, 250, 10)):
            water &= ~(np.hypot(X - ix + wx * 0.1, Z - iz + wz * 0.1) < r)
        self.water = water
        d_land = distance_transform_edt(~water)
        d_water = distance_transform_edt(water)
        self.d_land, self.d_water = d_land, d_water
        # ---- town: an organic terrace on the east bank
        east = X - (fc + fh)
        tdist = np.hypot((Xw - 92) / 118.0, (Zw - 18) / 168.0)
        town = (1 - smoothstep(0.7, 1.05, tdist)) * (east > -3)
        town = gaussian_filter(town.astype(float), 3)
        self.town_soft = town
        d_town = distance_transform_edt(town < 0.5)
        # ---- mountains: foothills rising away from the town and the water, ridged peaks
        base = np.minimum(d_land, d_town * 0.8 + 6)
        env = np.clip(base * 0.75, 0, 62) * (0.45 + 0.9 * n1)
        peaks = (ridge * 0.7 + ridge2 * 0.3) ** 1.6 * np.clip(base - 6, 0, 80) * 1.15
        mtn = 64 + env + peaks
        # the west bank rises as steep cliffs straight out of the fjord
        west = (X < fc - fh + 2) & (Z < 175)
        ledge = np.floor((d_land * (2.2 + 1.6 * n2)) / 9.0) * 9.0 * 0.85 + (d_land * (2.2 + 1.6 * n2)) % 9.0 * 0.15
        ribs = (0.5 + 0.5 * np.sin(Z / 7.0 + n2 * 9.0)) * np.clip(d_land, 0, 24) * 0.55
        mtn = np.where(west, 63 + np.minimum(ledge, 34 + 18 * n1) + ribs + np.clip(d_land - 12, 0, None) * (0.7 + 0.6 * n1) + peaks * 0.9, mtn)
        mtn = np.minimum(mtn, 188)
        town_h = 64 + np.clip(east, 0, 220) * 0.045 + (n2 - 0.5) * 2.0
        land_h = mtn * (1 - town) + town_h * town
        # east headland: grassy rolling plateau ending in sea cliffs
        head = np.exp(-((Xw - 112) / 42.0) ** 2) * smoothstep(140, 182, Zw) * (~west)
        head = np.clip(head * 1.4, 0, 1)
        head_h = 67 + np.minimum(d_land * 0.9, 9) + (n2 - 0.5) * 3
        land_h = land_h * (1 - head) + np.minimum(land_h, head_h) * head
        beach = (d_land < 8) & ~fj & (Zw > 140) & (head < 0.5)
        land_h = np.where(beach, np.minimum(land_h, 63 + d_land * 0.4), land_h)
        # ---- sea floor
        floor = SEA - 2 - np.minimum(d_water * 0.55, 22) + (n2 - 0.5) * 4
        floor = np.where(fj & ~sea, np.minimum(floor, SEA - 4 - np.minimum(d_water * 0.8, 18)), floor)
        H = np.where(water, floor, land_h)
        H = gaussian_filter(H, 1.1)
        H = np.where(water, np.minimum(H, SEA - 1), np.maximum(H, SEA + 1))
        self.H = np.round(H).astype(int)
        self.town_mask = town > 0.5
        self.fj = fj
        self.sea = sea
        self.west = west

    def paint(self):
        a, H, rng = self.a, self.H, np.random.default_rng(self.seed)
        n = fbm(SX, SZ, 12, 3, self.seed + 9)
        gy, gx = np.gradient(H.astype(float))
        slope = np.hypot(gx, gy)
        stone = [B("stone"), B("stone"), B("andesite"), B("stone"), B("tuff"), B("stone"), B("andesite"), B("stone"), B("cobblestone")]
        warp = (fbm(SX, SZ, 40, 3, self.seed + 21) * 9).astype(int)
        Bdirt, Bgrass, Bsand, Bgravel, Bsnow = B("dirt"), B("grass_block"), B("sand"), B("gravel"), B("snow")
        Bdeep, Bwater, Bclay = B("deepslate"), B("water"), B("clay")
        for i in range(SX):
            for k in range(SZ):
                h = H[i, k]
                ya = h - Y0
                col = a.blk[i, :, k]
                # rock body with strata
                for y in range(0, ya + 1):
                    wy = y + Y0
                    col[y] = Bdeep if wy < 30 else stone[((wy + warp[i, k]) // 5) % len(stone)]
                w = self.water[i, k]
                sl = slope[i, k]
                if w:
                    top = Bsand if (h > SEA - 6 and self.sea[i, k]) else (Bgravel if n[i, k] > 0.45 else Bclay if n[i, k] < 0.25 else Bsand)
                    col[ya] = top
                    col[ya - 1] = Bdirt if top != Bsand else Bsand
                    for y in range(ya + 1, SEA - Y0 + 1):
                        col[y] = Bwater
                    continue
                if h <= SEA + 2 and self.d_land[i, k] < 5 and not self.town_mask[i, k]:
                    col[ya] = Bsand if n[i, k] > 0.35 else Bgravel
                    col[ya - 1] = Bsand
                    continue
                if sl > 1.6 and h > 70:
                    # bare rock: patches of darker / mossy rock and vertical water stains
                    v = n[i, k]
                    for d in range(0, 3):
                        if ya - d < 0:
                            break
                        if v < 0.25:
                            col[ya - d] = Bdeep if d else B("cobbled_deepslate")
                        elif v < 0.4:
                            col[ya - d] = B("tuff")
                        elif v > 0.78:
                            col[ya - d] = B("mossy_cobblestone") if h < 110 else B("cobblestone")
                        elif v > 0.62:
                            col[ya - d] = B("andesite")
                    continue       # bare rock cliff
                if h >= 160 or (h >= 142 and n[i, k] > 0.62 - (h - 142) * 0.025):
                    col[ya] = Bsnow
                    col[ya - 1] = Bsnow
                    continue
                col[ya] = Bgrass
                for d in range(1, 4):
                    if ya - d >= 0:
                        col[ya - d] = Bdirt
        # snow layers on gentle high ground
        snowl = B("snow_layer", height=1)
        for i in range(0, SX):
            for k in range(0, SZ):
                h = H[i, k]
                if 136 <= h < 160 and slope[i, k] < 1.3 and self.a.blk[i, h - Y0, k] == Bgrass and n[i, k] > 0.4:
                    self.a.blk[i, h - Y0 + 1, k] = snowl

    # ------------------------------------------------------------ boundary
    def boundary(self):
        a = self.a
        bar = B("barrier")
        bb = B("border_block")
        top = Y0 + SY - 1
        for x in range(X0, X0 + SX):
            for z in (Z0, Z0 + SZ - 1):
                self._wall(x, z, bar, bb, top)
        for z in range(Z0, Z0 + SZ):
            for x in (X0, X0 + SX - 1):
                self._wall(x, z, bar, bb, top)

    def _wall(self, x, z, bar, bb, top):
        a = self.a
        i, k = x - X0, z - Z0
        col = a.blk[i, :, k]
        hb = self.H[i, k] - Y0
        col[max(0, hb - 1)] = bb
        for y in range(hb + 1, SY):
            if col[y] == 0 or PAL.names[col[y]] in ("water", "snow_layer"):
                col[y] = bar
                a.wet[i, y, k] = PAL.names[col[y]] == "water"



# ======================================================================== town
DUNGEON_ORDER = ["d01", "d02", "d03", "d04", "d05", "d06", "d07", "d08", "d09", "d10"]
TIER_OF = {"d01": "beginner", "d02": "beginner", "d03": "beginner", "d04": "beginner", "d05": "mid", "d06": "mid",
           "d07": "mid", "d08": "high", "d09": "high", "d10": "high"}
PIER_Z = [-122 + 24 * i for i in range(10)]
BANNER = {"beginner": 1, "mid": 4, "high": 0}          # red / blue / black banner base colour ids


def _mixer(rng, items):
    tot = sum(w for _, w in items)

    def f():
        r = rng.random() * tot
        for b, w in items:
            r -= w
            if r <= 0:
                return b
        return items[-1][0]
    return f


class Town:
    def __init__(self, S):
        self.S = S
        self.a = S.a
        self.rng = random.Random(S.seed + 100)

    # ------------------------------------------------------------ ground shaping
    def pad(self, x1, z1, x2, z2, y, top=None, found=None, clear=24, round_r=None):
        """Level the ground to `y` (top block at y) over the box; foundation fills down to the terrain."""
        a, S = self.a, self.S
        top = top or B("grass_block")
        found = found or B("cobblestone")
        cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if round_r and math.hypot(x - cx, z - cz) > round_r:
                    continue
                i, k = x - X0, z - Z0
                if not (0 <= i < SX and 0 <= k < SZ):
                    continue
                h = S.H[i, k]
                for yy in range(y + 1, y + clear):
                    a.set(x, yy, z, AIR)
                a.set(x, y, z, top)
                for yy in range(min(h, y) - 2, y):
                    if yy < y - 3 or h < y:
                        a.set(x, yy, z, found if yy < y - 1 or h < y - 1 else B("dirt"))
                    else:
                        a.set(x, yy, z, B("dirt"))
                S.H[i, k] = y

    def ground(self, x, z):
        i, k = x - X0, z - Z0
        return int(self.S.H[i, k])

    def road(self, pts, width=3, kind="cobble", lamps=8, lamp_side=1):
        """Road along a polyline, following (smoothed) terrain; returns visited cells."""
        a, S, rng = self.a, self.S, self.rng
        mats = {"cobble": _mixer(rng, [(B("cobblestone"), 4), (B("andesite"), 2), (B("gravel"), 2), (B("mossy_cobblestone"), 1)]),
                "path": _mixer(rng, [(B("grass_path"), 6), (B("coarse_dirt"), 2), (B("gravel"), 1)]),
                "stone": _mixer(rng, [(B("stone_bricks"), 5), (B("polished_andesite"), 3), (B("cracked_stone_bricks"), 1), (B("mossy_stone_bricks"), 1)])}[kind]
        cells = []
        dist = 0.0
        last = None
        for (p0, p1) in zip(pts[:-1], pts[1:]):
            for q in line_points((p0[0], 0, p0[1]), (p1[0], 0, p1[1]), step=0.5):
                x, _, z = q
                if last is not None:
                    dist += math.hypot(x - last[0], z - last[1])
                last = (x, z)
                for dx in range(-width // 2, width // 2 + 1):
                    for dz in range(-width // 2, width // 2 + 1):
                        if abs(dx) + abs(dz) > width // 2 + (1 if width >= 4 else 0):
                            continue
                        xx, zz = x + dx, z + dz
                        i, k = xx - X0, zz - Z0
                        if not (0 <= i < SX and 0 <= k < SZ) or S.water[i, k]:
                            continue
                        h = S.H[i, k]
                        top = a.get(xx, h, zz)
                        if top in (B("grass_block"), B("dirt"), B("snow"), B("sand"), B("gravel"), B("coarse_dirt"), B("podzol")) or kind == "stone":
                            a.set(xx, h, zz, mats())
                            for yy in range(h + 1, h + 4):
                                if PAL.names[a.get(xx, yy, zz)] in ("short_grass", "tall_grass", "fern", "large_fern", "snow_layer", "poppy", "dandelion"):
                                    a.set(xx, yy, zz, AIR)
                            cells.append((xx, zz))
                if lamps and int(dist) % lamps == 0 and int(dist) > 0:
                    f = (p1[0] - p0[0], p1[1] - p0[1])
                    L = math.hypot(*f) or 1
                    nx, nz = -f[1] / L * (width // 2 + 1) * lamp_side, f[0] / L * (width // 2 + 1) * lamp_side
                    lx, lz = int(round(x + nx)), int(round(z + nz))
                    i, k = lx - X0, lz - Z0
                    if 0 <= i < SX and 0 <= k < SZ and not S.water[i, k]:
                        h = S.H[i, k]
                        if a.get(lx, h + 1, lz) == AIR:
                            lamp_post(a, lx, h + 1, lz, B("spruce_fence"), B("lantern"), height=3)
                    dist += 1.0
        return cells

    # ------------------------------------------------------------ waterfront
    def boardwalk(self):
        a = self.a
        deck = B("spruce_planks")
        for z in range(-134, 152):
            for x in range(-3, 10):
                i, k = x - X0, z - Z0
                a.set(x, TOWN_Y, z, deck if (x + z) % 7 else B("stripped_spruce_log", axis="x"))
                for yy in range(TOWN_Y + 1, TOWN_Y + 10):
                    if PAL.names[a.get(x, yy, z)] not in ("air",):
                        a.set(x, yy, z, AIR)
                if x in (-3, 9) and z % 4 == 0:
                    for yy in range(self.S.H[i, k], TOWN_Y):
                        a.set(x, yy, z, B("spruce_log", axis="y"))
                # fill below the deck on land so there are no holes
                if not self.S.water[i, k]:
                    for yy in range(self.S.H[i, k], TOWN_Y):
                        a.set(x, yy, z, B("dirt"))
                self.S.H[i, k] = TOWN_Y
            # mooring posts on the water edge
            if z % 6 == 0:
                a.set(-3, TOWN_Y + 1, z, B("spruce_fence"))
        # land behind the boardwalk: raise/level the strip x 10..18 so the walk meets the town smoothly
        for z in range(-134, 152):
            for x in range(10, 20):
                h = self.ground(x, z)
                y = max(TOWN_Y, min(h, TOWN_Y + (x - 9) // 3))
                self.pad(x, z, x, z, y, top=B("grass_block") if x > 12 else B("gravel"))

    def piers_and_ships(self):
        a, rng = self.a, self.rng
        S = self.S
        for n, (did, pz) in enumerate(zip(DUNGEON_ORDER, PIER_Z)):
            tier = TIER_OF[did]
            for x in range(-33, -2):
                for z in range(pz, pz + 4):
                    a.set(x, TOWN_Y, z, B("spruce_planks") if (x % 5) else B("stripped_spruce_log", axis="z"))
                    for yy in range(TOWN_Y + 1, TOWN_Y + 4):
                        a.set(x, yy, z, AIR)
                if x % 5 == 0:
                    for z in (pz, pz + 3):
                        i, k = x - X0, z - Z0
                        for yy in range(S.H[i, k], TOWN_Y):
                            a.set(x, yy, z, B("spruce_log", axis="y"))
                        a.set(x, TOWN_Y + 1, z, B("spruce_fence"))
                        if x % 10 == 0:
                            a.set(x, TOWN_Y + 2, z, B("lantern"))
            # the ship, moored south of the pier, bow to the open water
            sail = tier
            info = P.longship(a, -5, SEA, pz + 9, "west", rng, sail=sail)
            # gangway from the pier to the deck
            for x in (-18, -19):
                a.set(x, TOWN_Y, pz + 4, B("spruce_slab", half="top"))
                a.set(x, TOWN_Y - 1 + 1, pz + 5, a.get(x, TOWN_Y, pz + 5))
            # sign + banner at the pier root
            sx, sz = 1, pz + 1
            banner_c = {"beginner": 1, "mid": 4, "high": 0}[tier]
            P.banner_pole(a, 4, TOWN_Y + 1, pz - 1, banner_c, [("cre", 15)] if tier == "high" else [("bri", 15)], height=4, facing="south")
            self.S.ships.append(dict(dungeon=did, deck=info["deck"], center=info["center"], pier=(-10, TOWN_Y + 1, pz + 1.5),
                                     sign=(2, TOWN_Y + 2, pz + 1), tier=tier, no=n + 1))
            self.S.no_walk.append(info["deck"])

    def ship_signs(self, dungeons):
        """Signs need the dungeon names: called by the world builder with the design data."""
        a = self.a
        for sh in self.S.ships:
            d = dungeons[sh["dungeon"]]
            x, y, z = sh["sign"]
            a.set(x, y - 1, z, B("spruce_fence"))
            text = "§l%s %d번 항로\n§r%s\n§7%s · %s" % ({"beginner": "§a", "mid": "§9", "high": "§6"}[sh["tier"]], sh["no"], d["ko"], d["tier_ko"], d["lv"])
            standing_sign(a, x, y, z, 4, text, kind="spruce_standing_sign")

    def landing_quay(self):
        a, rng = self.a, self.rng
        S = self.S
        Bq = _mixer(rng, [(B("polished_andesite"), 4), (B("stone_bricks"), 3), (B("andesite"), 1), (B("cracked_stone_bricks"), 1)])
        for x in range(-38, 10):
            for z in range(116, 148):
                i, k = x - X0, z - Z0
                edge = x == -38 or z in (116, 147)
                for yy in range(min(S.H[i, k], SEA - 4), TOWN_Y):
                    a.set(x, yy, z, B("stone_bricks") if edge else B("cobblestone"))
                a.set(x, TOWN_Y, z, B("stone_bricks") if edge else Bq())
                for yy in range(TOWN_Y + 1, TOWN_Y + 12):
                    a.set(x, yy, z, AIR)
                S.H[i, k] = TOWN_Y
                if edge and (x + z) % 4 == 0:
                    a.set(x, TOWN_Y + 1, z, B("stone_brick_wall"))
                    if (x + z) % 8 == 0:
                        a.set(x, TOWN_Y + 2, z, B("lantern"))
        # arrival rune circle
        cx, cz = -15, 132
        for x in range(cx - 5, cx + 6):
            for z in range(cz - 5, cz + 6):
                d = math.hypot(x - cx, z - cz)
                if d <= 5.4:
                    a.set(x, TOWN_Y, z, B("polished_deepslate") if 3.6 < d <= 5.4 else B("chiseled_stone_bricks") if d < 1.5 else B("smooth_stone"))
                if 4.3 < d <= 4.9 and (x + z) % 2 == 0:
                    a.set(x, TOWN_Y, z, B("gold_block"))
        for dx, dz in ((-6, -6), (6, -6), (-6, 6), (6, 6)):
            P.brazier(a, cx + dx, TOWN_Y + 1, cz + dz)
        self.S.points["arrival"] = (cx + 0.5, TOWN_Y + 1, cz + 0.5, -90)
        # the big return ship moored south of the quay
        info = P.longship(a, -6, SEA, 156, "west", rng, length=35, beam=11, sail="return")
        self.S.no_walk.append(info["deck"])
        # gate towards the town
        for z in range(127, 138):
            for yy in range(TOWN_Y + 1, TOWN_Y + 9):
                if z in (127, 128, 136, 137):
                    a.set(10, yy, z, B("stone_bricks") if yy < TOWN_Y + 8 else B("chiseled_stone_bricks"))
                    a.set(11, yy, z, B("stone_bricks"))
            for yy in (TOWN_Y + 8, TOWN_Y + 9):
                a.set(10, yy, z, B("stone_bricks") if yy == TOWN_Y + 8 else B("stone_brick_slab"))
                a.set(11, yy, z, B("stone_bricks") if yy == TOWN_Y + 8 else B("stone_brick_slab"))
        for z in (127, 137):
            a.set(9, TOWN_Y + 6, z, B("wall_banner", facing_direction=4))
            a.add_be(banner_be(9, TOWN_Y + 6, z, 1, [("bri", 4), ("bo", 15)]))
        wall_sign(a, 9, TOWN_Y + 7, 132, 4, "§l§6상륙장\n§r§f아홉 세계의 항구\n§7비크에 오신 것을\n§7환영합니다", kind="spruce_wall_sign")



# ------------------------------------------------------------------ sculpting helpers
def cyl(a, cx, y0, cz, r0, r1, h, block, hollow=False):
    for dy in range(h):
        r = r0 + (r1 - r0) * dy / max(1, h - 1)
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.3 and (not hollow or d > r - 1.2):
                    a.set(x, y0 + dy, z, block)


def ell(a, cx, cy, cz, rx, ry, rz, block, only_air=False):
    for x in range(int(cx - rx - 1), int(cx + rx + 2)):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for z in range(int(cz - rz - 1), int(cz + rz + 2)):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2 <= 1.0:
                    if only_air:
                        a.put(x, y, z, block)
                    else:
                        a.set(x, y, z, block)


def thick_line(a, p0, p1, r, block, only_air=False):
    for q in line_points(p0, p1, step=0.5):
        if r <= 0.6:
            (a.put if only_air else a.set)(q[0], q[1], q[2], block)
        else:
            ell(a, q[0], q[1], q[2], r, r, r, block, only_air)


class Town2(Town):
    # ------------------------------------------------------------ plaza + world tree
    def plaza(self):
        a, rng = self.a, self.rng
        cx, cz, r = 44, 132, 18
        y = 66
        self.pad(cx - r - 2, cz - r - 2, cx + r + 2, cz + r + 2, y, top=B("grass_block"), round_r=r + 2.5)
        mats = _mixer(rng, [(B("stone_bricks"), 5), (B("polished_andesite"), 3), (B("mossy_stone_bricks"), 1), (B("cracked_stone_bricks"), 1)])
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                d = math.hypot(x - cx, z - cz)
                if d <= r:
                    ring = int(d) % 5 == 0
                    a.set(x, y, z, B("polished_deepslate") if ring and d > 6 else mats())
                elif d <= r + 1.2:
                    a.set(x, y, z, B("stone_bricks"))
                    if (x * 7 + z * 3) % 23 == 0:
                        lamp_post(a, x, y + 1, z, B("spruce_fence"), B("lantern"), height=3)
        # the world-tree: tapered trunk, roots, branches, a wide crown with blossoms and hanging lanterns
        bark = B("oak_wood")
        cyl(a, cx, y + 1, cz, 2.6, 1.4, 24, bark)
        roots = 7
        for k in range(roots):
            ang = k / roots * 2 * math.pi + rng.uniform(-0.2, 0.2)
            L = rng.uniform(6, 9)
            p0 = (cx + math.cos(ang) * 1.8, y + 3, cz + math.sin(ang) * 1.8)
            p1 = (cx + math.cos(ang) * L, y, cz + math.sin(ang) * L)
            thick_line(a, p0, p1, 0.9, bark)
        leaf = leaves_of("oak")
        flower = B("azalea_leaves_flowered", persistent_bit=1)
        tops = []
        for k in range(8):
            ang = k / 8 * 2 * math.pi + rng.uniform(-0.25, 0.25)
            h0 = y + rng.uniform(13, 20)
            L = rng.uniform(8, 12)
            p0 = (cx, h0, cz)
            p1 = (cx + math.cos(ang) * L, h0 + rng.uniform(3, 6), cz + math.sin(ang) * L)
            thick_line(a, p0, p1, 0.7, bark)
            tops.append(p1)
        tops.append((cx, y + 26, cz))
        for (tx, ty, tz) in tops:
            leaf_blob(a, tx, ty + 1.5, tz, rng.uniform(4.5, 6.0), leaf, rng, flat=0.6, extra=flower, extra_chance=0.18)
        leaf_blob(a, cx, y + 25, cz, 9, leaf, rng, flat=0.45, extra=flower, extra_chance=0.12)
        for (tx, ty, tz) in tops[:-1]:
            hx, hz = int(round((tx + cx) / 2)), int(round((tz + cz) / 2))
            for yy in range(int(ty) + 2, int(y) + 8, -1):
                if a.get(hx, yy, hz) != AIR and a.get(hx, yy - 1, hz) == AIR:
                    hanging_lamp(a, hx, yy - 1, hz, rng.randint(2, 4))
                    break
        # bench ring around the trunk
        for k in range(36):
            ang = k / 36 * 2 * math.pi
            bx, bz = int(round(cx + math.cos(ang) * 5.6)), int(round(cz + math.sin(ang) * 5.6))
            if a.get(bx, y + 1, bz) == AIR:
                d = "east" if abs(math.cos(ang)) > abs(math.sin(ang)) and math.cos(ang) < 0 else "west" if abs(math.cos(ang)) > abs(math.sin(ang)) else "south" if math.sin(ang) < 0 else "north"
                a.set(bx, y + 1, bz, stair("spruce_stairs", d))
        for (dx, dz) in ((-12, -12), (12, -12), (-12, 12), (12, 12)):
            P.banner_pole(a, cx + dx, y + 1, cz + dz, 1 if dx < 0 else 4, [("bri", 15), ("bo", 0)], height=5, facing="south" if dz < 0 else "north")
        standing_sign(a, cx - 8, y + 1, cz, 12, "§l§2세계수 광장\n§r§f항구 마을 비크\n§7동: 대연회장  북: 대장간\n§7남: 노른의 샘", kind="spruce_standing_sign")
        self.S.points["plaza"] = (cx + 0.5, y + 1, cz - 8.5, 0)

    # ------------------------------------------------------------ forge (enhancement)
    def forge(self):
        a, rng = self.a, self.rng
        x0, z0, y = 68, 100, 67
        L, W = 22, 15
        self.pad(x0 - 3, z0 - 3, x0 + L + 2, z0 + W + 2, y, top=B("cobblestone"))
        floor = _mixer(rng, [(B("stone_bricks"), 3), (B("cobblestone"), 2), (B("andesite"), 1)])
        for x in range(x0, x0 + L):
            for z in range(z0, z0 + W):
                a.set(x, y, z, floor())
        # walls: stone base + timber frame, open towards the plaza (west side, x = x0)
        for x in range(x0, x0 + L):
            for z in range(z0, z0 + W):
                edge_e = x == x0 + L - 1
                edge_ns = z in (z0, z0 + W - 1)
                if not (edge_e or edge_ns):
                    continue
                for yy in range(y + 1, y + 7):
                    if yy <= y + 2:
                        a.set(x, yy, z, B("cobblestone"))
                    elif (x - x0) % 4 == 0 or edge_e and (z - z0) % 4 == 0:
                        a.set(x, yy, z, B("stripped_spruce_log", axis="y"))
                    else:
                        a.set(x, yy, z, B("spruce_planks"))
            if (x - x0) % 4 == 2:
                a.set(x, y + 4, z0, B("glass_pane"))
                a.set(x, y + 4, z0 + W - 1, B("glass_pane"))
        for z in range(z0, z0 + W, 4):
            for yy in range(y + 1, y + 7):
                a.set(x0, yy, z, B("stripped_spruce_log", axis="y"))
        # roof: pitched along x, stairs down to the north and south
        rise = W // 2 + 1
        for x in range(x0 - 1, x0 + L + 1):
            for k in range(rise + 1):
                zl, zr = z0 - 1 + k, z0 + W - k
                if zl >= zr:
                    a.set(x, y + 7 + k, zl, B("dark_oak_slab"))
                    break
                a.set(x, y + 7 + k, zl, stair("dark_oak_stairs", "south"))
                a.set(x, y + 7 + k, zr, stair("dark_oak_stairs", "north"))
            if x in (x0 + L - 1,):
                for k in range(rise):
                    for zz in range(z0 + k, z0 + W - k):
                        a.put(x, y + 7 + k, zz, B("spruce_planks"))
        # chimney + forge hearth on the east wall
        hx, hz = x0 + L - 3, z0 + W // 2
        for dx in range(-1, 3):
            for dz in range(-2, 3):
                for yy in range(y + 1, y + 18):
                    if yy > y + 3 and (dx in (-1, 2) or dz in (-2, 2)) or yy <= y + 1:
                        a.set(hx + dx, yy, hz + dz, B("stone_bricks") if yy % 5 else B("mossy_stone_bricks"))
        for dz in (-1, 0, 1):
            a.set(hx, y + 1, hz + dz, B("lava"))
            a.set(hx, y + 2, hz + dz, B("iron_bars"))
            a.set(hx + 1, y + 2, hz + dz, B("magma"))
        a.set(hx, y + 18, hz, B("campfire"))
        # work floor
        a.set(x0 + 8, y + 1, z0 + 3, B("anvil", cardinal="east"))
        a.set(x0 + 12, y + 1, z0 + 3, B("grindstone", attachment="standing", direction=1))
        a.set(x0 + 15, y + 1, z0 + 3, B("smithing_table"))
        a.set(x0 + 16, y + 1, z0 + 3, B("blast_furnace", cardinal="south"))
        a.set(x0 + 8, y + 1, z0 + W - 4, B("anvil", cardinal="east"))
        a.set(x0 + 12, y + 1, z0 + W - 4, B("cauldron", cauldron_liquid="water", fill_level=6))
        for k in range(3):
            a.set(x0 + 18, y + 1, z0 + 2 + k, B("barrel", facing_direction=1))
        # the rune anvil (enhancement station) on a glowing pedestal, centre stage
        sx, sz = x0 + 6, z0 + W // 2
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                a.set(sx + dx, y, sz + dz, B("polished_deepslate"))
        a.set(sx, y + 1, sz, B("chiseled_deepslate"))
        a.set(sx, y + 2, sz, B("anvil", cardinal="north"))
        for dz in (-2, 2):
            a.set(sx, y + 1, sz + dz, B("amethyst_block"))
            a.set(sx, y + 2, sz + dz, B("amethyst_cluster", block_face="up"))
            a.set(sx - 1, y + 1, sz + dz, B("soul_lantern"))
        wall_sign(a, sx - 1, y + 2, sz, 4, "§l§5룬 모루\n§r§f강화할 장비를\n§f손에 들고\n§f모루를 누르세요", kind="spruce_wall_sign")
        self.S.stations["enhance"] = [(sx, y + 2, sz)]
        for yy in (y + 6,):
            for xx in range(x0 + 3, x0 + L - 3, 5):
                hanging_lamp(a, xx, y + 8, z0 + W // 2, 2)
        a.set(x0 - 1, y + 4, z0 + 2, B("wall_banner", facing_direction=4))
        a.add_be(banner_be(x0 - 1, y + 4, z0 + 2, 0, [("cr", 1), ("bo", 4)]))
        wall_sign(a, x0 - 1, y + 3, z0 + W - 3, 4, "§l§6룬 대장간\n§r§f장비 강화\n§7룬 조각 · 룬 정수", kind="spruce_wall_sign")
        self.S.points["forge"] = (x0 - 2.5, y + 1, sz + 0.5, -90)

    # ------------------------------------------------------------ Norns' well (daily reward)
    def norn_well(self):
        a, rng = self.a, self.rng
        cx, cz, y = 72, 156, 67
        self.pad(cx - 13, cz - 11, cx + 13, cz + 11, y, top=B("grass_block"), round_r=13)
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                d = math.hypot(x - cx, z - cz)
                if d <= 4.4:
                    if d > 3.2:
                        for yy in range(y - 1, y + 2):
                            a.set(x, yy, z, B("mossy_stone_bricks") if (x + z + yy) % 3 else B("stone_bricks"))
                        a.set(x, y + 1, z, B("mossy_stone_brick_wall") if (x + z) % 2 else B("stone_brick_wall"))
                    else:
                        for yy in range(y - 4, y + 1):
                            a.set(x, yy, z, B("water"))
                        a.set(x, y - 5, z, B("sea_lantern") if d < 1 else B("prismarine_bricks"))
        # three Norns: hooded statues facing the well
        for k, (name, ang) in enumerate((("우르드", 200), ("베르단디", 320), ("스쿨드", 80))):
            r = 7.5
            sx = int(round(cx + math.cos(math.radians(ang)) * r))
            sz = int(round(cz + math.sin(math.radians(ang)) * r))
            a.set(sx, y, sz, B("chiseled_stone_bricks"))
            cyl(a, sx, y + 1, sz, 1.6, 0.9, 5, B("white_wool") if k == 1 else B("light_gray_wool"))
            ell(a, sx, y + 6.5, sz, 1.2, 1.3, 1.2, B("light_gray_wool") if k != 1 else B("white_wool"))
            a.set(sx, y + 7, sz, B("calcite"))
            a.set(sx, y + 8, sz, B("light_gray_wool") if k != 1 else B("white_wool"))
            # a lantern held towards the well
            fx = int(round(cx + math.cos(math.radians(ang)) * (r - 1.5)))
            fz = int(round(cz + math.sin(math.radians(ang)) * (r - 1.5)))
            a.set(fx, y + 4, fz, B("soul_lantern"))
            a.set(fx, y + 3, fz, B("spruce_fence"))
        # giant root arch over the well (the roots of the world tree)
        for side in (-1, 1):
            pts = [(cx + side * 10, y, cz - 2), (cx + side * 7, y + 7, cz - 1), (cx + side * 3, y + 11, cz), (cx, y + 12, cz + 1)]
            for p0, p1 in zip(pts[:-1], pts[1:]):
                thick_line(a, p0, p1, 1.0, B("oak_wood"))
        for k in range(10):
            vx, vz = cx + rng.randint(-5, 5), cz + rng.randint(-2, 3)
            for yy in range(y + 12, y + 2, -1):
                if a.get(vx, yy, vz) != AIR and a.get(vx, yy - 1, vz) == AIR:
                    for t in range(rng.randint(2, 5)):
                        if a.get(vx, yy - 1 - t, vz) == AIR:
                            a.set(vx, yy - 1 - t, vz, B("cave_vines_body_with_berries") if t % 2 else B("cave_vines"))
                    break
        # flowers
        fl = ["poppy", "dandelion", "oxeye_daisy", "cornflower", "lily_of_the_valley", "allium", "white_tulip", "blue_orchid"]
        for _ in range(70):
            fx, fz = cx + rng.randint(-12, 12), cz + rng.randint(-10, 10)
            if 5.5 < math.hypot(fx - cx, fz - cz) < 12 and a.get(fx, y + 1, fz) == AIR and a.get(fx, y, fz) == B("grass_block"):
                a.set(fx, y + 1, fz, B(rng.choice(fl)))
        # the reward station: a lodestone on a pedestal in front of the well
        lx, lz = cx - 6, cz
        a.set(lx, y, lz, B("chiseled_stone_bricks"))
        a.set(lx, y + 1, lz, B("lodestone"))
        a.set(lx, y + 2, lz, B("amethyst_cluster", block_face="up"))
        wall_sign(a, lx - 1, y + 1, lz, 4, "§l§b노른의 축복\n§r§f하루 한 번\n§f돌을 누르면\n§f선물을 받아요", kind="spruce_wall_sign")
        self.S.stations["daily"] = [(lx, y + 1, lz)]
        self.S.points["well"] = (lx - 2.5, y + 1, lz + 0.5, -90)

    # ------------------------------------------------------------ mead hall
    def mead_hall(self):
        a, rng = self.a, self.rng
        x0, z0, y = 96, 120, 69
        L, W = 52, 21
        self.pad(x0 - 6, z0 - 4, x0 + L + 3, z0 + W + 3, y, top=B("stone_bricks"))
        # terrace steps down to the plaza side (west)
        for k in range(1, 5):
            for z in range(z0 + 6, z0 + W - 6):
                a.set(x0 - 6 - k, y - k, z, stair("stone_brick_stairs", "east"))
        wall_h = 7
        for x in range(x0, x0 + L):
            for z in range(z0, z0 + W):
                a.set(x, y, z, B("spruce_planks") if (x // 2 + z) % 5 else B("dark_oak_planks"))
                edge = x in (x0, x0 + L - 1) or z in (z0, z0 + W - 1)
                if edge:
                    for yy in range(y + 1, y + 1 + wall_h):
                        post = (x - x0) % 6 == 0 or z in (z0, z0 + W - 1) and x in (x0, x0 + L - 1) or (x in (x0, x0 + L - 1) and (z - z0) % 5 == 0)
                        a.set(x, yy, z, B("stripped_dark_oak_log", axis="y") if post else B("stone_bricks") if yy <= y + 1 else B("spruce_planks"))
        for x in range(x0 + 3, x0 + L - 3, 6):
            for z in (z0, z0 + W - 1):
                a.set(x, y + 4, z, B("glass_pane"))
                a.set(x, y + 5, z, B("glass_pane"))
        # great doors on the west gable
        mz = z0 + W // 2
        for z in range(mz - 2, mz + 3):
            for yy in range(y + 1, y + 6):
                a.set(x0, yy, z, AIR)
        for z in (mz - 3, mz + 3):
            for yy in range(y + 1, y + 7):
                a.set(x0 - 1, yy, z, B("dark_oak_log", axis="y"))
            a.set(x0 - 1, y + 7, z, B("lantern"))
        # roof: steep, dark shingles with a ridge running along x
        rise = W // 2 + 2
        for x in range(x0 - 2, x0 + L + 2):
            for k in range(rise + 1):
                zl, zr = z0 - 2 + k, z0 + W + 1 - k
                yy = y + wall_h + 1 + k
                if zl >= zr:
                    a.set(x, yy, zl, B("dark_oak_slab"))
                    break
                a.set(x, yy, zl, stair("dark_oak_stairs", "south"))
                a.set(x, yy, zr, stair("dark_oak_stairs", "north"))
                if zl + 1 < zr:
                    a.set(x, yy - 1, zl + 1, B("dark_oak_planks")) if k > 0 else None
                    a.set(x, yy - 1, zr - 1, B("dark_oak_planks")) if k > 0 else None
            if x in (x0, x0 + L - 1):
                for k in range(rise):
                    for zz in range(z0 + k, z0 + W - k):
                        if a.get(x, y + wall_h + 1 + k, zz) == AIR:
                            a.set(x, y + wall_h + 1 + k, zz, B("spruce_planks"))
        # crossed dragon horns on both gables
        for x in (x0 - 3, x0 + L + 2):
            top = y + wall_h + 1 + rise - 1
            for k in range(4):
                a.set(x, top + k, mz - 1 - k, B("dark_oak_fence"))
                a.set(x, top + k, mz + 1 + k, B("dark_oak_fence"))
            a.set(x, top + 4, mz - 5, B("shroomlight"))
            a.set(x, top + 4, mz + 5, B("shroomlight"))
        # interior: pillar rows, long tables, fire trench, throne
        for x in range(x0 + 4, x0 + L - 4, 6):
            for z in (z0 + 5, z0 + W - 6):
                for yy in range(y + 1, y + wall_h + 4):
                    a.set(x, yy, z, B("stripped_spruce_log", axis="y"))
                a.set(x, y + 3, z + (1 if z < mz else -1), B("wall_banner", facing_direction=3 if z < mz else 2))
                a.add_be(banner_be(x, y + 3, z + (1 if z < mz else -1), 1 if (x // 6) % 2 else 4, [("cre", 15)]))
        for x in range(x0 + 6, x0 + L - 8):
            a.set(x, y, mz, B("stone_bricks"))
            if (x - x0) % 5 == 0:
                a.set(x, y + 1, mz, B("campfire"))
            for z in (mz - 3, mz + 3):
                a.set(x, y + 1, z, B("spruce_fence"))
                a.set(x, y + 2, z, B("spruce_slab"))
            for z in (mz - 4, mz + 4):
                a.set(x, y + 1, z, stair("spruce_stairs", "north" if z < mz else "south"))
        # throne at the east end
        tx = x0 + L - 4
        for z in range(mz - 2, mz + 3):
            a.set(tx, y + 1, z, B("polished_deepslate"))
        a.set(tx, y + 2, mz, stair("dark_oak_stairs", "east"))
        a.set(tx + 1, y + 2, mz, B("dark_oak_planks"))
        a.set(tx + 1, y + 3, mz, B("dark_oak_planks"))
        a.set(tx + 1, y + 4, mz, B("gold_block"))
        for z in (mz - 1, mz + 1):
            a.set(tx, y + 2, z, B("dark_oak_fence"))
            a.set(tx, y + 3, z, B("lantern"))
        for x in range(x0 + 3, x0 + L - 3, 5):
            hanging_lamp(a, x, y + wall_h + 5, mz, 3)
        wall_sign(a, x0 - 1, y + 5, mz - 4, 4, "§l§6대연회장\n§r§f발할라를 꿈꾸는\n§f전사들의 집", kind="spruce_wall_sign")
        self.S.points["hall"] = (x0 - 3.5, y + 1, mz + 0.5, -90)

    # ------------------------------------------------------------ Odin statue on the hill
    def odin(self):
        a, rng = self.a, self.rng
        cx, cz = 176, 54
        g = self.ground(cx, cz)
        y = max(g, 78)
        self.pad(cx - 9, cz - 9, cx + 9, cz + 9, y, top=B("stone_bricks"), round_r=9.5)
        for x in range(cx - 9, cx + 10):
            for z in range(cz - 9, cz + 10):
                if 8.5 < math.hypot(x - cx, z - cz) <= 9.5:
                    a.set(x, y + 1, z, B("stone_brick_wall"))
        base = y + 1
        for k in range(3):
            for x in range(cx - 4 + k, cx + 5 - k):
                for z in range(cz - 4 + k, cz + 5 - k):
                    a.set(x, base + k, z, B("chiseled_stone_bricks") if k == 2 else B("stone_bricks"))
        b0 = base + 3
        robe, cloak, beard, hat, skin = B("andesite"), B("polished_deepslate"), B("calcite"), B("deepslate_tiles"), B("smooth_stone")
        # robe (cone), cloak behind
        cyl(a, cx, b0, cz, 3.6, 2.2, 11, robe)
        for dy in range(0, 13):
            r = 3.9 - dy * 0.12
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                for z in range(int(cz), int(cz + r + 2)):
                    d = math.hypot(x - cx, z - cz)
                    if r - 0.9 < d <= r + 0.4:
                        a.set(x, b0 + dy, z, cloak)
        # torso, shoulders, arms
        ell(a, cx, b0 + 13, cz, 3.2, 2.6, 2.2, robe)
        ell(a, cx - 3.2, b0 + 14, cz, 1.4, 1.4, 1.4, cloak)
        ell(a, cx + 3.2, b0 + 14, cz, 1.4, 1.4, 1.4, cloak)
        thick_line(a, (cx + 3.5, b0 + 13, cz), (cx + 4, b0 + 9, cz - 2), 1.0, robe)          # left arm holding the spear
        thick_line(a, (cx - 3.5, b0 + 13, cz), (cx - 3, b0 + 9, cz - 1.5), 1.0, robe)
        # head, beard, the single glowing eye, broad hat
        ell(a, cx, b0 + 17.5, cz - 0.2, 1.7, 2.0, 1.7, skin)
        ell(a, cx, b0 + 15.2, cz - 1.4, 1.6, 2.6, 0.9, beard)
        a.set(cx - 1, b0 + 18, cz - 2, B("polished_deepslate"))                                 # eye patch
        a.set(cx + 1, b0 + 18, cz - 2, B("sea_lantern"))                                        # the one eye
        cyl(a, cx, b0 + 19, cz, 4.4, 4.4, 1, hat)
        cyl(a, cx, b0 + 20, cz, 1.9, 0.6, 4, hat)
        # Gungnir
        sx, sz = cx + 4, cz - 2
        for yy in range(base + 3, b0 + 24):
            a.set(sx, yy, sz, B("spruce_fence") if yy < b0 + 21 else B("iron_bars"))
        a.set(sx, b0 + 24, sz, B("gold_block"))
        a.set(sx, b0 + 25, sz, B("lightning_rod"))
        # Huginn and Muninn on the shoulders
        for side in (-1, 1):
            rx = cx + side * 3
            ell(a, rx, b0 + 16.3, cz, 0.9, 0.8, 1.4, B("black_wool"))
            a.set(rx, b0 + 17, cz - 1, B("black_wool"))
            a.set(rx, b0 + 17, cz - 2, B("black_concrete"))
        # braziers around the platform
        for (dx, dz) in ((-7, -7), (7, -7), (-7, 7), (7, 7)):
            P.brazier(a, cx + dx, y + 1, cz + dz)
        wall_sign(a, cx - 5, base + 1, cz, 4, "§l§6만물의 아버지 오딘\n§r§f지혜를 위해\n§f한쪽 눈을 바친 신", kind="spruce_wall_sign")
        self.S.points["odin"] = (cx - 7.5, y + 1, cz + 0.5, -90)
        return (cx, y, cz)



RESERVED = [  # x1, z1, x2, z2 boxes kept free of houses
    (-40, -140, 22, 152),      # boardwalk, piers, quay
    (20, 108, 70, 156),        # plaza
    (60, 94, 96, 120),         # forge
    (56, 140, 90, 172),        # well
    (86, 112, 156, 148),       # mead hall
    (96, 62, 126, 92),         # training yard
    (162, 40, 192, 70),        # odin
]


def _free(x1, z1, x2, z2, extra=()):
    for (a1, b1, a2, b2) in list(RESERVED) + list(extra):
        if x1 <= a2 and x2 >= a1 and z1 <= b2 and z2 >= b1:
            return False
    return True


class Town3(Town2):
    def houses(self):
        a, rng, S = self.a, self.rng, self.S
        placed = []
        cand = []
        for x in range(26, 170, 19):
            for z in range(-126, 100, 17):
                cand.append((x + rng.randint(-3, 3), z + rng.randint(-3, 3)))
        rng.shuffle(cand)
        n = 0
        for (x, z) in cand:
            if n >= 22:
                break
            facing = rng.choice(["west", "west", "south", "north", "east"])
            L, W = rng.choice([(11, 7), (13, 8), (15, 9), (17, 9)])
            if facing in ("north", "south"):
                fx1, fz1, fx2, fz2 = x, z, x + W, z + L
            else:
                fx1, fz1, fx2, fz2 = x, z, x + L, z + W
            if not _free(fx1 - 3, fz1 - 3, fx2 + 3, fz2 + 3, placed):
                continue
            # stay on the town terrace (not up the mountain)
            hs = [self.ground(xx, zz) for xx in (fx1, fx2) for zz in (fz1, fz2)]
            if max(hs) - min(hs) > 4 or max(hs) > 78 or not all(S.town_mask[xx - X0, zz - Z0] for xx in (fx1, fx2) for zz in (fz1, fz2)):
                continue
            y = int(round(sum(hs) / 4))
            self.pad(fx1 - 1, fz1 - 1, fx2 + 1, fz2 + 1, y, top=B("grass_block"))
            # Frame origin: front-left corner
            if facing == "west":
                ox, oz = fx2, fz1
            elif facing == "east":
                ox, oz = fx1, fz2
            elif facing == "north":
                ox, oz = fx1, fz2
            else:
                ox, oz = fx2, fz1
            ox, oz = {"west": (fx2, fz2), "east": (fx1, fz1), "north": (fx1, fz2), "south": (fx2, fz1)}[facing]
            P.longhouse(a, ox, y + 1, oz, facing, rng, length=L, width=W, turf=rng.random() < 0.6,
                        wall=rng.choice(["spruce", "spruce", "dark_oak", "oak"]))
            placed.append((fx1, fz1, fx2, fz2))
            # yard details
            dx, dz = P.DIRS[facing]
            yx, yz = (fx1 + fx2) // 2 + dx * ((fx2 - fx1) // 2 + 3), (fz1 + fz2) // 2 + dz * ((fz2 - fz1) // 2 + 3)
            r = rng.random()
            if r < 0.3:
                P.barrels(a, yx + 2, y + 1, yz + 2, rng, 3)
            elif r < 0.5:
                P.fish_rack(a, yx - 2, y + 1, yz + 2, along="x" if facing in ("north", "south") else "z")
            elif r < 0.7:
                for k in range(3):
                    a.put(yx + k, y + 1, yz - 2, B("sweet_berry_bush", growth=3))
            n += 1
        self.S.houses = placed
        return placed

    def market(self):
        a, rng = self.a, self.rng
        cols = ["red", "blue", "yellow", "white", "green", "orange"]
        for i, pz in enumerate(PIER_Z[:-1]):
            z = pz + 10
            x = 13
            y = self.ground(x, z)
            c = cols[i % len(cols)]
            for (dx, dz) in ((0, 0), (4, 0), (0, 5), (4, 5)):
                for k in range(1, 4):
                    a.set(x + dx, y + k, z + dz, B("spruce_fence"))
            for dx in range(-1, 6):
                for dz in range(-1, 7):
                    a.set(x + dx, y + 4, z + dz, B(c + "_wool") if (dz % 2 == 0) else B("white_wool"))
            for dz in range(0, 6):
                a.set(x + 1, y + 1, z + dz, B("spruce_slab", half="top") if dz % 3 else B("barrel", facing_direction=1))
            a.set(x + 2, y + 1, z + 2, B("hay_block", axis="y"))
            a.set(x + 3, y + 1, z + 4, B("barrel", facing_direction=1))

    def training_yard(self):
        a, rng = self.a, self.rng
        x1, z1, x2, z2 = 100, 66, 122, 88
        y = int(round(sum(self.ground(x, z) for x in (x1, x2) for z in (z1, z2)) / 4))
        self.pad(x1, z1, x2, z2, y, top=B("coarse_dirt"))
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x in (x1, x2) or z in (z1, z2):
                    if not (x == x1 and 75 <= z <= 78):
                        a.set(x, y + 1, z, B("spruce_fence"))
                elif rng.random() < 0.25:
                    a.set(x, y, z, B("gravel"))
        for (x, z) in ((104, 70), (108, 70), (112, 70), (116, 70)):
            a.set(x, y + 1, z + 14, B("hay_block", axis="y"))
            a.set(x, y + 2, z + 14, B("target"))
        pts = [(105.5, y + 1, 76.5), (110.5, y + 1, 76.5), (115.5, y + 1, 76.5), (110.5, y + 1, 80.5)]
        self.S.points["dummies"] = pts
        P.banner_pole(a, x1 + 2, y + 1, z1 + 2, 1, [("cr", 15)], 4, "south")
        standing_sign(a, x1 - 1, y + 1, 77, 4, "§l§c훈련장\n§r§f허수아비를 때려\n§f강화 효과를\n§f시험해 보세요", kind="spruce_standing_sign")

    def lighthouse(self):
        a, rng = self.a, self.rng
        cx, cz = 112, 216
        g = max(self.ground(cx + dx, cz + dz) for dx in (-6, 6) for dz in (-6, 6))
        y = g
        self.pad(cx - 8, cz - 8, cx + 8, cz + 8, y, top=B("stone_bricks"), round_r=8.5)
        H = 34
        for dy in range(H):
            r = 5.2 - dy * 0.05
            band = (dy // 4) % 2
            for x in range(cx - 7, cx + 8):
                for z in range(cz - 7, cz + 8):
                    d = math.hypot(x - cx, z - cz)
                    if d <= r + 0.3:
                        if d > r - 1.1:
                            a.set(x, y + 1 + dy, z, B("stone_bricks") if band else B("mossy_stone_bricks") if rng.random() < 0.2 else B("polished_andesite"))
                        else:
                            a.set(x, y + 1 + dy, z, AIR)
        # spiral stairs inside (slabs)
        for dy in range(H - 1):
            ang = dy * 0.7
            sx = int(round(cx + math.cos(ang) * 2.4))
            sz = int(round(cz + math.sin(ang) * 2.4))
            a.set(sx, y + 1 + dy, sz, B("spruce_planks"))
        a.set(cx - 5, y + 1, cz, AIR)
        a.set(cx - 5, y + 2, cz, AIR)
        # gallery + fire basket
        top = y + H + 1
        for x in range(cx - 7, cx + 8):
            for z in range(cz - 7, cz + 8):
                d = math.hypot(x - cx, z - cz)
                if d <= 6.5:
                    a.set(x, top, z, B("stone_bricks"))
                    if d > 5.6:
                        a.set(x, top + 1, z, B("stone_brick_wall"))
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                a.set(x, top + 1, z, B("magma"))
                a.set(x, top + 2, z, B("campfire") if (x + z) % 2 == 0 else B("shroomlight"))
        for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            for k in range(1, 6):
                a.set(cx + dx, top + k, cz + dz, B("dark_oak_fence"))
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                if max(abs(x - cx), abs(z - cz)) == 4 or (x - cx) % 2 == 0:
                    a.set(x, top + 6, z, B("dark_oak_slab"))
        a.set(cx, top + 7, cz, B("glowstone"))
        P.banner_pole(a, cx - 7, y + 1, cz - 3, 1, [("bri", 15)], 4, "west")
        P.longhouse(a, cx - 18, y + 1, cz - 4, "west", rng, length=9, width=7, turf=True)
        self.S.points["lighthouse"] = (cx - 7.5, y + 1, cz + 0.5, -90)

    def roads(self):
        R = self.road
        R([(22, -130), (22, -60), (24, 0), (24, 60), (26, 110)], width=4, kind="cobble", lamps=16)
        for z in (-108, -64, -20, 26, 74):
            R([(24, z), (70, z + 3), (120, z - 2), (160, z + 2)], width=3, kind="path", lamps=22)
        R([(12, 132), (26, 132)], width=5, kind="stone", lamps=0)
        R([(62, 132), (88, 131)], width=4, kind="stone", lamps=6)
        R([(50, 114), (64, 108)], width=3, kind="stone", lamps=6)
        R([(54, 146), (64, 154)], width=3, kind="stone", lamps=6)
        R([(60, 150), (84, 176), (100, 196), (108, 206)], width=3, kind="path", lamps=9)
        R([(150, 118), (160, 96), (170, 76), (174, 64)], width=3, kind="cobble", lamps=8)
        R([(110, 100), (111, 92)], width=3, kind="path", lamps=0)

    def vegetation(self):
        a, S = self.a, self.S
        rng = self.rng
        n = fbm(SX, SZ, 40, 3, S.seed + 31)
        gy, gx = np.gradient(S.H.astype(float))
        slope = np.hypot(gx, gy)

        def forest(x, z):
            i, k = x - X0, z - Z0
            if S.water[i, k] or S.town_mask[i, k] and not (n[i, k] > 0.66):
                return False
            return slope[i, k] < 1.25 and n[i, k] > 0.42 and S.H[i, k] < 128 and not _occupied(x, z)

        def _occupied(x, z):
            for (x1, z1, x2, z2) in RESERVED + getattr(S, "houses", []):
                if x1 - 3 <= x <= x2 + 3 and z1 - 3 <= z <= z2 + 3:
                    return True
            return False

        def kinds(r, y):
            if y > 100:
                return "spruce_small"
            return r.choice(["spruce", "spruce", "spruce", "birch", "spruce_small", "bush"])
        P.scatter_trees(a, rng, forest, 1500, kinds, X0 + 2, Z0 + 2, X0 + SX - 3, Z0 + SZ - 3, ymin=63, ymax=128, spacing=4)
        # ground cover: grass, ferns, flowers on open grass
        flowers = ["poppy", "dandelion", "oxeye_daisy", "cornflower", "azure_bluet", "allium"]
        for _ in range(26000):
            x, z = rng.randint(X0 + 1, X0 + SX - 2), rng.randint(Z0 + 1, Z0 + SZ - 2)
            i, k = x - X0, z - Z0
            if S.water[i, k]:
                continue
            y = S.H[i, k]
            if a.get(x, y, z) != B("grass_block") or a.get(x, y + 1, z) != AIR:
                continue
            r = rng.random()
            if r < 0.55:
                a.set(x, y + 1, z, B("short_grass"))
            elif r < 0.72:
                a.set(x, y + 1, z, B("fern"))
            elif r < 0.8 and a.get(x, y + 2, z) == AIR:
                a.set(x, y + 1, z, B("tall_grass", upper_block_bit=0))
                a.set(x, y + 2, z, B("tall_grass", upper_block_bit=1))
            elif r < 0.9 and S.H[i, k] < 100:
                a.set(x, y + 1, z, B(rng.choice(flowers)))
            else:
                a.set(x, y, z, B("podzol") if rng.random() < 0.5 else B("coarse_dirt"))
        # boulders on the mountains
        for _ in range(140):
            x, z = rng.randint(X0 + 4, X0 + SX - 5), rng.randint(Z0 + 4, Z0 + SZ - 5)
            i, k = x - X0, z - Z0
            if S.water[i, k] or S.town_mask[i, k]:
                continue
            boulder(a, x, S.H[i, k] + 1, z, rng, rng.uniform(1.2, 2.6), [B("stone"), B("andesite"), B("mossy_cobblestone"), B("cobblestone")])

    def waterfall(self, ex, ez, dx, dz, width=3, depth_in=None):
        """Slot canyon cut into a cliff with a waterfall curtain at its back.
        (ex, ez): point on the water's edge; (dx, dz): direction into the cliff."""
        a, S = self.a, self.S
        nx, nz = -dz, dx                                  # across the slot
        # walk into the cliff until the ground is high
        top, back = None, None
        for t in range(2, 70):
            x, z = ex + dx * t, ez + dz * t
            i, k = x - X0, z - Z0
            if not (2 <= i < SX - 2 and 2 <= k < SZ - 2):
                break
            if S.H[i, k] >= 84 and t >= 3:
                top, back = S.H[i, k], t
                break
        if top is None:
            return False
        half = width // 2
        stone = B("stone")
        for t in range(0, back + 1):
            x, z = ex + dx * t, ez + dz * t
            for w in range(-half - 1, half + 2):
                xx, zz = x + nx * w, z + nz * w
                i, k = xx - X0, zz - Z0
                hcol = S.H[i, k]
                inside = abs(w) <= half
                for yy in range(SEA - 2, max(hcol, top) + 1):
                    if inside:
                        if t == back:
                            a.set(xx, yy, zz, B("flowing_water", liquid_depth=8) if SEA + 1 <= yy < top else B("water") if yy <= SEA else B("water"))
                        elif yy > SEA:
                            a.set(xx, yy, zz, AIR)
                        else:
                            a.set(xx, yy, zz, B("water"))
                    elif yy <= max(hcol, SEA) and a.get(xx, yy, zz) == AIR:
                        a.set(xx, yy, zz, stone)
                    elif yy > hcol and yy <= top and t >= back - 2:
                        a.set(xx, yy, zz, stone)
                if inside:
                    S.H[i, k] = SEA if t < back else top
        # pool on the top that feeds the curtain
        x, z = ex + dx * (back + 1), ez + dz * (back + 1)
        for t in range(back + 1, back + 4):
            for w in range(-half - 1, half + 2):
                xx, zz = ex + dx * t + nx * w, ez + dz * t + nz * w
                inside = abs(w) <= half
                a.set(xx, top - 1, zz, stone)
                a.set(xx, top, zz, B("water") if inside else stone)
                for yy in range(top + 1, top + 4):
                    a.set(xx, yy, zz, AIR)
        # moss and vines on the slot walls
        rng = self.rng
        for t in range(1, back):
            for w in (-half - 1, half + 1):
                xx, zz = ex + dx * t + nx * w, ez + dz * t + nz * w
                for yy in range(SEA + 1, top, 3):
                    if rng.random() < 0.35:
                        a.set(xx, yy, zz, B("moss_block"))
        return True

    def waterfalls(self):
        S = self.S
        made = 0
        for zt in (-200, -120, -40, 60):
            fc = float(S.fjord_center(zt))
            fh = float(S.fjord_half(zt))
            ex = int(fc - fh)
            while not S.water[ex - X0, zt - Z0] and ex < int(fc):
                ex += 1
            made += self.waterfall(ex, zt, -1, 0, width=5)
        # the big fall at the head of the fjord
        fc = float(S.fjord_center(-270))
        z = -270
        while S.water[int(fc) - X0, z - Z0]:
            z -= 1
        made += self.waterfall(int(fc), z + 1, 0, -1, width=7)
        return made



def build(seed=7, dungeons=None):
    S = Spawn(seed)
    S.terrain()
    S.paint()
    T = Town3(S)
    T.boardwalk()
    T.piers_and_ships()
    if dungeons:
        T.ship_signs(dungeons)
    T.landing_quay()
    T.plaza()
    T.forge()
    T.norn_well()
    T.mead_hall()
    T.odin()
    T.training_yard()
    T.lighthouse()
    T.houses()
    T.market()
    T.roads()
    T.vegetation()
    T.waterfalls()
    S.boundary()
    S.a.fix_walls()
    return S


if __name__ == "__main__":
    import sys, time
    import render
    t0 = time.time()
    S = build()
    print("built %.1fs" % (time.time() - t0))
    render.topdown(S.a, sys.argv[1], scale=1)
