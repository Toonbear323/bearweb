"""Map 3 - Paradise ("에메랄드 라군"): a hidden tropical lagoon valley with a central island,
white beaches, palm trees, coral reefs, a tiki bar, boardwalks and waterfalls."""
import math
import random

import numpy as np

from mcw import B, AIR, simple_be, flowerpot_be
from gen_common import (fbm, clamp_gradient, smoothstep, palm_tree, cherry_tree, oak_tree, leaf_blob, leaves_of,
                        bush, boulder, lamp_post, stair, slab, disk, ring, tall_plant, FLOWERS, TALL_FLOWERS,
                        wall_sign, standing_sign, line_points, hanging_lamp)
from gen_mapbase import MapBase, catmull, bridge, cascade, cove, SIZE

WL = 63


def ell(DX, DZ, cx, cz, rx, rz):
    return ((DX - cx) / rx) ** 2 + ((DZ - cz) / rz) ** 2


class Paradise(MapBase):
    def __init__(self, cx, cz):
        super().__init__("paradise", cx, cz, seed=3303, biome=21)

    def build(self):
        self.terrain()
        self.paint()
        self.reef()
        self.gazebo()
        self.island_falls()
        self.boardwalks()
        self.tiki_bar(52, 2)
        self.huts()
        self.beach_props()
        self.lifeguard_tower(-8, 58)
        self.rock_arch()
        self.trees()
        self.flora()
        self.lights()
        self.falls()
        self.barrier()
        self.a.fix_walls()
        sp = [(0, -46), (-12, -44), (12, -44)]
        self.spawns = [(self.cx + dx, self.gy(self.cx + dx, self.cz + dz) + 1, self.cz + dz) for dx, dz in sp]
        return self.a

    # ------------------------------------------------------------------
    def terrain(self):
        DX, DZ = self.DX, self.DZ
        n = fbm(SIZE, SIZE, 26, 4, self.seed)
        n2 = fbm(SIZE, SIZE, 9, 2, self.seed + 1)
        # lagoon shape
        lag = ell(DX, DZ, 0, 14, 60, 44) + (n - 0.5) * 0.5
        island = ell(DX, DZ, 2, 8, 19, 15) + (n2 - 0.5) * 0.25
        islets = [(-36, 30, 6.5), (32, 34, 5.5), (16, 50, 4.5), (-20, 52, 4)]
        water = (lag < 1.0) & (island > 1.0)
        for (ix, iz, r) in islets:
            water &= ell(DX, DZ, ix, iz, r, r) + (n2 - 0.5) * 0.3 > 1.0
        water &= self.D < self.R - 4
        self.lagoon = water
        # distance to shore (approx, chamfer)
        dist = np.where(water, 0.0, 1e6)
        land_d = np.where(water, 1e6, 0.0)
        for _ in range(14):
            p = np.pad(land_d, 1, mode="edge")
            land_d = np.minimum(land_d, np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]) + 1)
            p = np.pad(dist, 1, mode="edge")
            dist = np.minimum(dist, np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]) + 1)
        self.shore_d = land_d          # inside water: distance to land
        self.sea_d = dist              # on land: distance to water
        # land heights: beach then rising inland
        inland = np.clip(dist - 3, 0, None)
        h_land = WL + np.minimum(inland * 0.45, 6) + (n - 0.5) * 3
        h_land = np.where(dist <= 3, WL + (dist >= 2), h_land)
        # central island hill
        hill = np.clip(1 - ell(DX, DZ, 2, 6, 14, 11), 0, 1)
        h_land = h_land + hill * 9
        depth = np.clip(np.round(land_d / 2.6 + 0.4), 1, 5)
        H = np.where(water, WL - depth, np.round(h_land)).astype(np.int32)
        self.H = np.where(self.D < self.R + 2, H, self.H0 + 3)
        self.water = np.where(water, WL, 0)
        self.reserved |= water
        # pads
        self.gz_h = self.flatten(2, 6, 4.5, h=int(self.H[2 + self.cx - self.a.x0 + 0, 6 + self.cz - self.a.z0]))
        self.flatten(52, 2, 6, h=WL + 1)
        self.flatten(0, -46, 6)
        land = ~water & (self.D < self.R + 1)
        Hc = clamp_gradient(self.H, land, 1)
        self.H = np.where(land, Hc, self.H)
        self.make_cliffs(base_jump=12, top=30, width=18, amp=8, bulge=4)
        self.fall_angles = (60, 140, 230, 300)
        for ang in self.fall_angles:
            d = cove(self, ang, 1.5, 3.5, WL, B("water"), depth=2)
        self.walkable_smooth()
        # materials
        m1 = fbm(SIZE, SIZE, 6, 2, self.seed + 40)
        m2 = fbm(SIZE, SIZE, 14, 2, self.seed + 41)
        top = np.full((SIZE, SIZE), B("grass_block"), np.int32)
        beach = (self.sea_d <= 4) & (self.water == 0)
        top[beach] = B("sand")
        top[beach & (m1 > 0.75)] = B("sandstone")
        top[self.water > 0] = np.where(m1[self.water > 0] > 0.7, B("gravel"), B("sand"))
        top[(self.water > 0) & (m2 > 0.72)] = B("clay")
        self.top = top
        self.sub[:] = B("dirt")
        self.sub[beach | (self.water > 0)] = B("sand")
        self.sub[self.H <= WL] = B("sandstone")
        self.deep[:] = B("stone")
        # biomes
        bio = np.full((SIZE, SIZE), 21, np.int32)
        bio[beach] = 16
        bio[self.water > 0] = 40
        bio[self.wall] = 21
        self.a.bio[:] = bio
        stone_set = [B("calcite"), B("diorite"), B("stone"), B("andesite"), B("calcite"), B("smooth_sandstone"),
                     B("diorite"), B("stone")]
        off = (fbm(SIZE, SIZE, 10, 2, self.seed + 91) * 9).astype(np.int32)
        moss = fbm(SIZE, SIZE, 6, 2, self.seed + 92)

        def strata(y):
            idx = ((y + off) // 3) % len(stone_set)
            arr = np.array(stone_set)[idx]
            arr = np.where((moss > 0.72) & (y > self.H0 + 4), B("moss_block"), arr)
            arr = np.where((moss < 0.12), B("mossy_cobblestone"), arr)
            arr = np.where(y >= self.H - 1, np.where(y == self.H, B("grass_block"), B("dirt")), arr)
            return arr
        self.strata = strata

    # ------------------------------------------------------------------
    def reef(self):
        a = self.a
        rng = random.Random(8)
        corals = ["tube", "brain", "bubble", "fire", "horn"]
        rn = fbm(SIZE, SIZE, 8, 2, self.seed + 70)
        for i in range(SIZE):
            for k in range(SIZE):
                if not self.water[i, k] or self.wall[i, k]:
                    continue
                x, z = i + self.a.x0, k + self.a.z0
                h = int(self.H[i, k])
                d = WL - h
                if d >= 2 and rn[i, k] > 0.58:
                    c = corals[int(rn[i, k] * 37) % 5]
                    r = rng.random()
                    a.set(x, h, z, B(c + "_coral_block"))
                    if r < 0.35:
                        a.setw(x, h + 1, z, B(c + "_coral"))
                    elif r < 0.6:
                        a.setw(x, h + 1, z, B(c + "_coral_fan", coral_fan_direction=rng.randint(0, 1)))
                    elif r < 0.7:
                        a.setw(x, h + 1, z, B("sea_pickle", cluster_count=rng.randint(1, 3)))
                    elif r < 0.75 and d >= 3:
                        a.set(x, h + 1, z, B(c + "_coral_block"))
                elif d >= 1 and rng.random() < 0.18:
                    if d >= 3 and rng.random() < 0.35:
                        top = h + rng.randint(1, d - 1)
                        for y in range(h + 1, top + 1):
                            a.setw(x, y, z, B("kelp", kelp_age=min(25, y - h)))
                    elif d >= 2 and rng.random() < 0.3:
                        a.setw(x, h + 1, z, B("seagrass", sea_grass_type="double_bot"))
                        a.setw(x, h + 2, z, B("seagrass", sea_grass_type="double_top"))
                    else:
                        a.setw(x, h + 1, z, B("seagrass"))
                elif d >= 2 and rng.random() < 0.01:
                    a.set(x, h, z, B("sea_lantern"))

    def gazebo(self):
        """White marble gazebo on the island hilltop."""
        a = self.a
        cx, cz = self.w(2, 6)
        g = self.gy(cx, cz)
        self.reserved[(self.DX - 2) ** 2 + (self.DZ - 6) ** 2 <= 49] = True
        q = B("smooth_quartz")
        for x in range(cx - 5, cx + 6):
            for z in range(cz - 5, cz + 6):
                d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                if d <= 4.6:
                    a.set(x, g, z, B("quartz_block") if (x + z) % 2 else q)
                if 4.6 < d <= 5.5:
                    a.set(x, g, z, B("quartz_bricks"))
        for k in range(8):
            ang = k * math.pi / 4
            px = cx + round(math.cos(ang) * 4)
            pz = cz + round(math.sin(ang) * 4)
            for y in range(g + 1, g + 5):
                a.set(px, y, pz, B("quartz_pillar", axis="y"))
            a.set(px, g + 5, pz, B("chiseled_quartz_block"))
        # dome
        for x in range(cx - 5, cx + 6):
            for z in range(cz - 5, cz + 6):
                for y in range(g + 5, g + 10):
                    d = math.sqrt((x - cx) ** 2 + ((y - g - 5) * 1.25) ** 2 + (z - cz) ** 2)
                    if 3.9 <= d < 4.9:
                        a.set(x, y, z, B("white_stained_glass") if (y - g) % 2 else B("smooth_quartz"))
        a.set(cx, g + 10, cz, B("end_rod", facing_direction=1))
        a.set(cx, g + 8, cz, B("chain"))
        a.set(cx, g + 7, cz, B("pearlescent_froglight", axis="y"))
        # flower planters inside
        for (ox, oz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            a.set(cx + ox, g + 1, cz + oz, B("flower_pot"))
            a.add_be(flowerpot_be(cx + ox, g + 1, cz + oz, rng_flower(ox + oz)))
        self.pois["gazebo"] = (cx, g + 1, cz)

    def island_falls(self):
        """A stepped stream from the hilltop spring down into the lagoon (south side)."""
        a = self.a
        cx, cz = self.w(2, 6)
        g = self.gy(cx, cz)
        x = cx + 7
        z0 = cz
        # walk south-east from the gazebo terrace toward the water: terraced pools
        for t in range(0, 14):
            xx = x + t // 2
            zz = z0 + t
            h = self.gy(xx, zz)
            if self.water[xx - self.a.x0, zz - self.a.z0]:
                break
            for o in (0, 1):
                a.set(xx + o, h, zz, B("water"))
                a.set(xx + o, h - 1, zz, B("mossy_cobblestone"))
            for o in (-1, 2):
                if a.get(xx + o, h, zz) != B("water"):
                    a.set(xx + o, h, zz, B("mossy_cobblestone") if t % 2 else B("calcite"))

    def boardwalks(self):
        a = self.a
        # north meadow -> island and island -> east beach, island -> west islet
        routes = [((2, -12), (2, -4)), ((18, 8), (40, 6)), ((-15, 12), (-30, 26)), ((10, 20), (30, 32))]
        for (p0, p1) in routes:
            w0, w1 = self.w(*p0), self.w(*p1)
            # extend the ends onto land
            f0 = max(self.gy(*w0) + 1, WL + 2)
            f1 = max(self.gy(*w1) + 1, WL + 2)
            pts = bridge(a, w0, w1, f0, f1, B("bamboo_planks"), slab("bamboo_slab"), B("bamboo_fence"),
                         lamp=B("lantern"), width=3, lamp_every=6)
            # support posts into the water
            for (x, f, z) in pts[::4]:
                y = int(f) - 2
                while y > 50 and a.get(x, y, z) in (AIR, B("water")):
                    a.set(x, y, z, B("stripped_bamboo_block", axis="y") if a.get(x, y, z) == AIR else B("bamboo_block", axis="y"))
                    y -= 1
        # little dock with a boat house on the north shore
        dx, dz = self.w(-26, -6)
        for t in range(0, 9):
            for o in (-1, 0, 1):
                x, z = dx + o, dz + t
                if self.gy(x, z) <= WL:
                    a.set(x, WL + 1, z, B("spruce_planks") if o == 0 else B("spruce_slab", half="top"))
        for t in (2, 5, 8):
            for o in (-2, 2):
                a.set(dx + o, WL + 1, dz + t, B("spruce_log", axis="y"))
                a.set(dx + o, WL, dz + t, B("spruce_log", axis="y"))
                a.set(dx + o, WL + 2, dz + t, B("spruce_fence"))
                if t == 8:
                    a.set(dx + o, WL + 3, dz + t, B("lantern"))

    def tiki_bar(self, dx, dz):
        a = self.a
        cx, cz = self.w(dx, dz)
        g = self.gy(cx, cz)
        self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 64] = True
        for x in range(cx - 6, cx + 7):
            for z in range(cz - 6, cz + 7):
                d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                if d <= 6.2:
                    a.set(x, g, z, B("bamboo_mosaic") if d > 3.4 else B("bamboo_planks"))
                if 2.6 < d <= 3.4:
                    ang = math.degrees(math.atan2(z - cz, x - cx)) % 360
                    if not (80 < ang < 110):
                        a.set(x, g + 1, z, B("bamboo_block", axis="y"))
                        a.set(x, g + 2, z, B("bamboo_slab"))
        # posts + thatched roof
        for k in range(6):
            ang = k * math.pi / 3
            px = cx + round(math.cos(ang) * 5)
            pz = cz + round(math.sin(ang) * 5)
            for y in range(g + 1, g + 5):
                a.set(px, y, pz, B("bamboo_block", axis="y"))
        for x in range(cx - 7, cx + 8):
            for z in range(cz - 7, cz + 8):
                d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                for y in range(g + 5, g + 9):
                    rr = 7 - (y - g - 5) * 2
                    if rr - 1 < d <= rr:
                        a.set(x, y, z, B("hay_block", axis="y"))
        a.set(cx, g + 8, cz, B("hay_block", axis="y"))
        a.set(cx, g + 4, cz, B("lantern", hanging=1))
        a.set(cx, g + 5, cz, B("bamboo_block", axis="y"))
        # bar props: stools, barrels, "drinks"
        for ang in range(0, 360, 40):
            if 60 < ang < 130:
                continue
            x = cx + round(math.cos(math.radians(ang)) * 4.4)
            z = cz + round(math.sin(math.radians(ang)) * 4.4)
            if a.get(x, g + 1, z) == AIR:
                a.set(x, g + 1, z, B("bamboo_fence"))
                a.set(x, g + 2, z, B("bamboo_pressure_plate"))
        a.set(cx, g + 1, cz, B("barrel", facing_direction=1))
        a.set(cx + 1, g + 1, cz, B("barrel", facing_direction=1))
        a.set(cx - 1, g + 1, cz, B("decorated_pot"))
        a.add_be(simple_be("DecoratedPot", cx - 1, g + 1, cz))
        standing_sign(a, cx - 7, g + 1, cz, 4, "§l§6TIKI BAR\n§r§e열대 음료 판매중\n§7(오늘은 휴무)", kind="bamboo_standing_sign")
        self.pois["tiki"] = (cx, g + 1, cz)

    def huts(self):
        a = self.a
        rng = random.Random(12)
        for (dx, dz, face) in ((48, -24, "west"), (54, 24, "west"), (-52, 6, "east")):
            cx, cz = self.w(dx, dz)
            g = self.gy(cx, cz)
            self.flatten(dx, dz, 4, h=g)
            self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 30] = True
            a.fill(cx - 3, g, cz - 3, cx + 3, g, cz + 3, B("bamboo_planks"))
            for (ox, oz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
                for y in range(g + 1, g + 4):
                    a.set(cx + ox, y, cz + oz, B("bamboo_block", axis="y"))
            # walls of bamboo on 3 sides (open front)
            for t in range(-2, 3):
                for y in range(g + 1, g + 3):
                    sides = {"west": [(3, t), (t, -3), (t, 3)], "east": [(-3, t), (t, -3), (t, 3)]}[face]
                    for (ox, oz) in sides:
                        a.set(cx + ox, y, cz + oz, B("bamboo_mosaic") if y == g + 1 else B("bamboo_fence"))
            # roof
            for lvl in range(0, 4):
                r = 4 - lvl
                for x in range(cx - r, cx + r + 1):
                    for z in range(cz - r, cz + r + 1):
                        if max(abs(x - cx), abs(z - cz)) == r:
                            a.set(x, g + 4 + lvl, z, B("hay_block", axis="y"))
            a.set(cx, g + 7, cz, B("hay_block", axis="y"))
            a.set(cx, g + 3, cz, B("lantern", hanging=1))
            # hammock / bed + towel
            a.set(cx, g + 1, cz + 1, B("light_blue_carpet"))
            a.set(cx + (1 if face == "east" else -1), g + 1, cz - 1, B("barrel", facing_direction=1))

    def beach_props(self):
        a = self.a
        rng = random.Random(4)
        cols = ["red", "yellow", "light_blue", "lime", "orange", "pink", "white"]
        spots = self.scatter(14, 9, lambda x, z: self.ok_spot(x, z, margin=6) and 1 <= self.sea_d[x + self.cx - self.a.x0, z + self.cz - self.a.z0] <= 4)
        for n, (dx, dz) in enumerate(spots):
            x, z = self.w(dx, dz)
            g = self.gy(x, z)
            if n % 3 == 2:
                # beach bonfire
                a.set(x, g + 1, z, B("campfire"))
                a.add_be(simple_be("Campfire", x, g + 1, z))
                for (ox, oz) in ((2, 0), (-2, 0)):
                    a.set(x + ox, g + 1, z + oz, B("stripped_birch_log", axis="z"))
                continue
            c = cols[n % len(cols)]
            for y in range(g + 1, g + 4):
                a.set(x, y, z, B("birch_fence"))
            for ox in range(-2, 3):
                for oz in range(-2, 3):
                    if abs(ox) + abs(oz) <= 3:
                        a.set(x + ox, g + 4, z + oz, B(c + "_wool") if (ox + oz) % 2 == 0 else B("white_wool"))
            a.set(x, g + 4, z, B(c + "_wool"))
            # towels + chair
            a.set(x + 1, g + 1, z + 1, B(c + "_carpet"))
            a.set(x + 1, g + 1, z + 2, B(c + "_carpet"))
            a.set(x - 1, g + 1, z + 1, stair("birch_stairs", "north"))

    def lifeguard_tower(self, dx, dz):
        a = self.a
        cx, cz = self.w(dx, dz)
        g = self.gy(cx, cz)
        self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 20] = True
        for (ox, oz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            for y in range(g + 1, g + 6):
                a.set(cx + ox, y, cz + oz, B("stripped_birch_log", axis="y"))
        a.fill(cx - 2, g + 6, cz - 2, cx + 2, g + 6, cz + 2, B("birch_planks"))
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                if max(abs(x - cx), abs(z - cz)) == 2 and not (x == cx and z == cz - 2):
                    a.set(x, g + 7, z, B("red_concrete") if (x + z) % 2 else B("white_concrete"))
        for y in range(g + 1, g + 7):
            a.set(cx, y, cz - 2, B("ladder", facing_direction=2))
        a.set(cx, g + 6, cz - 2, B("ladder", facing_direction=2))
        a.set(cx, g + 7, cz - 2, AIR)
        for (ox, oz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            a.set(cx + ox, g + 8, cz + oz, B("birch_fence"))
        a.fill(cx - 2, g + 9, cz - 2, cx + 2, g + 9, cz + 2, B("red_wool"))
        a.set(cx, g + 7, cz, B("lantern"))
        self.pois["lifeguard"] = (cx, g + 7, cz)

    def rock_arch(self):
        """Natural calcite arch spanning a lagoon arm in the south-west."""
        a = self.a
        rng = random.Random(6)
        p0 = self.w(-48, 30)
        p1 = self.w(-30, 46)
        mats = [B("calcite"), B("diorite"), B("calcite"), B("smooth_sandstone")]
        n = 40
        for k in range(n + 1):
            t = k / n
            x = p0[0] + (p1[0] - p0[0]) * t
            z = p0[1] + (p1[1] - p0[1]) * t
            yb = WL + 9 + math.sin(t * math.pi) * 4
            for ox in range(-2, 3):
                for oz in range(-2, 3):
                    for oy in range(-1, 2):
                        if ox * ox + oz * oz + oy * oy * 2 <= 5:
                            a.set(round(x) + ox, round(yb) + oy, round(z) + oz, rng.choice(mats))
        # legs down to the ground
        for (px, pz) in (p0, p1):
            top = WL + 10
            for y in range(self.gy(px, pz) - 2, top):
                for ox in range(-2, 3):
                    for oz in range(-2, 3):
                        if ox * ox + oz * oz <= 5 + (top - y) * 0.15:
                            a.set(px + ox, y, pz + oz, rng.choice(mats))
        # greenery on top
        for k in range(0, n + 1, 3):
            t = k / n
            x = round(p0[0] + (p1[0] - p0[0]) * t)
            z = round(p0[1] + (p1[1] - p0[1]) * t)
            yb = round(WL + 9 + math.sin(t * math.pi) * 4) + 2
            if a.get(x, yb, z) == AIR and a.get(x, yb - 1, z) != AIR:
                a.set(x, yb - 1, z, B("grass_block"))
                a.set(x, yb, z, leaves_of("jungle") if rng.random() < 0.5 else B("short_grass"))

    def trees(self):
        a = self.a
        rng = self.rng
        # palms along the beaches
        palms = self.scatter(60, 6.5, lambda x, z: self.ok_spot(x, z, margin=4)
                             and 1 <= self.sea_d[x + self.cx - self.a.x0, z + self.cz - self.a.z0] <= 7)
        for (dx, dz) in palms:
            x, z = self.w(dx, dz)
            palm_tree(a, x, self.gy(x, z) + 1, z, rng)
            self.reserved[x - self.a.x0, z - self.a.z0] = True
        # cherry blossoms on the island and the north meadow
        ch = self.scatter(30, 8, lambda x, z: self.ok_spot(x, z, margin=5)
                          and self.sea_d[x + self.cx - self.a.x0, z + self.cz - self.a.z0] > 6
                          and (z < -24 or ell(x, z, 2, 6, 15, 12) < 1))
        for (dx, dz) in ch:
            x, z = self.w(dx, dz)
            cherry_tree(a, x, self.gy(x, z) + 1, z, rng)
            self.reserved[x - self.a.x0, z - self.a.z0] = True
        # lush jungle trees inland (east/west edges)
        jt = self.scatter(40, 7, lambda x, z: self.ok_spot(x, z, margin=4)
                          and self.sea_d[x + self.cx - self.a.x0, z + self.cz - self.a.z0] > 8 and z >= -24)
        for (dx, dz) in jt:
            x, z = self.w(dx, dz)
            y = self.gy(x, z) + 1
            if rng.random() < 0.5:
                oak_tree(a, x, y, z, rng, kind="jungle", h=rng.randint(6, 9))
            else:
                bush(a, x, y, z, rng, leaves_of("jungle"))
        # cliff top jungle + palms
        t = self.wall_t
        cand = [tuple(c) for c in np.argwhere((t > 5) & (t < 16) & (self.D < 104))]
        rng.shuffle(cand)
        placed = []
        for (i, k) in cand[:5000]:
            if any((i - p) ** 2 + (k - q) ** 2 < 36 for p, q in placed[-80:]):
                continue
            if rng.random() > 0.3:
                continue
            x, z = i + self.a.x0, k + self.a.z0
            y = int(self.H[i, k]) + 1
            r = rng.random()
            if r < 0.4:
                palm_tree(a, x, y, z, rng)
            elif r < 0.8:
                oak_tree(a, x, y, z, rng, kind="jungle", h=rng.randint(5, 8))
            else:
                bush(a, x, y, z, rng, leaves_of("jungle"))
            placed.append((i, k))

    def flora(self):
        a = self.a
        rng = random.Random(30)
        fl = fbm(SIZE, SIZE, 9, 2, self.seed + 300)
        trop = ["allium", "blue_orchid", "pink_tulip", "oxeye_daisy", "azure_bluet", "cornflower", "red_tulip",
                "orange_tulip", "dandelion", "poppy"]
        for i in range(SIZE):
            for k in range(SIZE):
                if self.water[i, k]:
                    continue
                x, z = i + self.a.x0, k + self.a.z0
                y = int(self.H[i, k]) + 1
                if a.get(x, y, z) != AIR:
                    continue
                below = a.get(x, y - 1, z)
                r = rng.random()
                if below == B("grass_block"):
                    if self.wall[i, k]:
                        if r < 0.3:
                            a.set(x, y, z, B("short_grass"))
                        elif r < 0.36:
                            a.set(x, y, z, B(rng.choice(trop)))
                        continue
                    if fl[i, k] > 0.6 and r < 0.45:
                        a.set(x, y, z, B(rng.choice(trop)))
                    elif fl[i, k] > 0.66 and r < 0.55:
                        tall_plant(a, x, y, z, rng.choice(TALL_FLOWERS))
                    elif fl[i, k] < 0.3 and r < 0.4:
                        a.set(x, y, z, B("pink_petals", growth=rng.randint(1, 3),
                                         cardinal=rng.choice(["north", "south", "east", "west"])))
                    elif r < 0.25:
                        a.set(x, y, z, B("short_grass"))
                    elif r < 0.29:
                        tall_plant(a, x, y, z, "tall_grass")
                    elif r < 0.30:
                        a.set(x, y, z, B("fern"))
                elif below == B("sand") and not self.wall[i, k]:
                    if self.sea_d[i, k] >= 3 and r < 0.03:
                        a.set(x, y, z, B("short_grass"))
                    elif r < 0.004:
                        a.set(x, y, z, B("turtle_egg", turtle_egg_count="two_egg"))
        # sugar cane at the water's edge
        for i in range(SIZE):
            for k in range(SIZE):
                if self.water[i, k] or self.wall[i, k] or self.sea_d[i, k] != 1 or rng.random() > 0.06:
                    continue
                x, z = i + self.a.x0, k + self.a.z0
                y = int(self.H[i, k]) + 1
                if a.get(x, y, z) == AIR and a.get(x, y - 1, z) in (B("sand"), B("grass_block")):
                    for t in range(rng.randint(2, 3)):
                        a.set(x, y + t, z, B("reeds"))

    def lights(self):
        a = self.a
        rng = random.Random(41)
        # tiki torches along the shore
        spots = self.scatter(40, 10, lambda x, z: self.ok_spot(x, z, margin=5, allow_path=True)
                             and 2 <= self.sea_d[x + self.cx - self.a.x0, z + self.cz - self.a.z0] <= 5)
        for (dx, dz) in spots:
            x, z = self.w(dx, dz)
            g = self.gy(x, z)
            if a.get(x, g + 1, z) == AIR:
                a.set(x, g + 1, z, B("bamboo_fence"))
                a.set(x, g + 2, z, B("bamboo_fence"))
                a.set(x, g + 3, z, B("torch", torch_facing_direction="top"))
        # glow under the boardwalks: sea lanterns on the lagoon floor
        for (dx, dz) in self.scatter(26, 12, lambda x, z: self.water[x + self.cx - self.a.x0, z + self.cz - self.a.z0] > 0
                                     and self.H[x + self.cx - self.a.x0, z + self.cz - self.a.z0] <= WL - 2, margin=8):
            x, z = self.w(dx, dz)
            a.set(x, self.gy(x, z), z, B("sea_lantern"))

    def falls(self):
        for ang in self.fall_angles:
            cascade(self, ang, 1.5, self.H0 + 20, WL, B("water"), B("flowing_water", liquid_depth=8),
                    B("mossy_cobblestone"), fill_base=True)


def rng_flower(k):
    return ["allium", "blue_orchid", "pink_tulip", "azure_bluet"][k % 4]
