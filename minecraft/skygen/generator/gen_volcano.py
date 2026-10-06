"""Map 2 - Volcano ("불의 화산지대"): a smoking volcano with a crater lava lake, lava rivers,
basalt pillars, a ruined nether temple and jagged volcanic cliffs with lava falls."""
import math
import random

import numpy as np

from mcw import B, AIR, simple_be
from gen_common import (fbm, clamp_gradient, smoothstep, dead_tree, boulder, lamp_post, stair, slab, disk,
                        line_points, wall_sign, hanging_lamp)
from gen_mapbase import MapBase, catmull, bridge, cascade, cove, SIZE

LL = 64          # lava level of rivers / lakes (lava block y)
RIM = 27         # crater rim height above H0
CONE_R = 31
CRATER_R = 12


class Volcano(MapBase):
    def __init__(self, cx, cz):
        super().__init__("volcano", cx, cz, seed=2202, biome=37)

    def build(self):
        self.terrain()
        self.paint()
        self.road_details()
        self.crater_details()
        self.lava_tube()
        self.temple(40, 42)
        self.pillars()
        self.spires()
        self.ash_field()
        self.bridges()
        self.decorate()
        self.falls()
        self.barrier()
        self.a.fix_walls()
        sp = [(46, -6), (44, 6), (-46, 6)]
        self.spawns = [(self.cx + dx, self.gy(self.cx + dx, self.cz + dz) + 1, self.cz + dz) for dx, dz in sp]
        return self.a

    # ------------------------------------------------------------------
    def cone_h(self, r):
        t = np.clip((CONE_R - r) / (CONE_R - CRATER_R), 0, 1)
        return self.H0 + RIM * t ** 0.85

    def apply_road(self):
        for (i, kk), hh in self.road_h.items():
            self.H[i, kk] = int(round(hh))

    def terrain(self):
        n = fbm(SIZE, SIZE, 30, 4, self.seed)
        n2 = fbm(SIZE, SIZE, 8, 2, self.seed + 3)
        base = self.H0 + np.round((n - 0.5) * 8 + (n2 - 0.5) * 2).astype(np.int32)
        r = np.sqrt(self.DX ** 2 + self.DZ ** 2)
        self.r = r
        cone = self.cone_h(r) + (n2 - 0.5) * 3 * (r > CRATER_R + 1)
        H = np.maximum(base, np.round(cone).astype(np.int32))
        # crater terraces: 1 block per ring down to the lava lake
        crater = r < CRATER_R
        terr = self.H0 + RIM - np.ceil(CRATER_R - r).astype(np.int32)
        H = np.where(crater, np.maximum(terr, self.H0 + 20), H)
        self.H = np.where(self.D < self.R + 2, H, self.H0 + 3)
        # spiral road up the cone
        self.road = np.zeros((SIZE, SIZE), bool)
        self.road_h = {}
        th0 = math.radians(-20)
        turns = 1.35
        samples = 2400
        for k in range(samples + 1):
            s = k / samples
            th = th0 + s * turns * 2 * math.pi
            rr = (CONE_R + 1) - s * (CONE_R + 1 - (CRATER_R + 0.5))
            hh = self.H0 + 1 + s * (RIM - 1)
            for o in np.linspace(-1.6, 1.6, 7):
                x = (rr + o) * math.cos(th)
                z = (rr + o) * math.sin(th)
                i, kk = int(round(x)) + self.cx - self.a.x0, int(round(z)) + self.cz - self.a.z0
                if (i, kk) not in self.road_h or self.road_h[(i, kk)] > hh:
                    self.road_h[(i, kk)] = hh
                self.road[i, kk] = True
        self.apply_road()
        self.road_start = (round((CONE_R + 1) * math.cos(th0)), round((CONE_R + 1) * math.sin(th0)))
        self.reserved |= self.road
        # lava rivers + lake (lava surface y = LL)
        self.river1 = catmull([(-37, -6), (-44, -22), (-52, -40), (-62, -52), (-84, -60)])
        self.river2 = catmull([(6, 37), (14, 48), (10, 60), (-4, 67), (-20, 72), (-30, 88)])
        d1 = self.carve_river(self.river1, None, None, LL)
        d2 = self.carve_river(self.river2, None, None, LL)
        lake = np.sqrt(((self.DX - 52) / 1.2) ** 2 + (self.DZ + 44) ** 2)
        lava = B("lava")
        for d, hw in ((d1, 1.8), (d2, 1.8), (lake, 7.5)):
            self.apply_water_body(d, hw, LL, max_depth=1 if hw < 3 else 2, bank=5, liquid=lava)
        self.lava_dist = np.minimum(np.minimum(d1, d2), lake)
        self.water[self.road] = 0
        self.apply_road()
        # flatten pads
        self.flatten(40, 42, 13, square=True, h=self.H0 + 1)
        self.flatten(46, 0, 7)
        self.flatten(0, -(CONE_R + 5), 4, h=self.H0)
        self.flatten(0, CONE_R + 5, 4, h=self.H0)
        # keep the cone, road and crater as built; smooth only the plains
        plains = (r > CONE_R + 2) & (self.D < self.R + 1)
        Hc = clamp_gradient(self.H, plains, 1)
        self.H = np.where(plains, Hc, self.H)
        self.H = np.where(self.water > 0, np.minimum(self.H, LL - 1), self.H)
        self.make_cliffs(base_jump=11, top=30, width=18, amp=9, bulge=5)
        self.fall_angles = (90, 200, 320)
        for ang in self.fall_angles:
            d = cove(self, ang, 1.2, 3.2, LL, B("lava"))
            self.lava_dist = np.minimum(self.lava_dist, d)
        # materials --------------------------------------------------------
        m1 = fbm(SIZE, SIZE, 7, 2, self.seed + 40)
        m2 = fbm(SIZE, SIZE, 15, 2, self.seed + 41)
        m3 = fbm(SIZE, SIZE, 4, 1, self.seed + 42)
        top = np.full((SIZE, SIZE), B("blackstone"), np.int32)
        top[m1 > 0.55] = B("basalt")
        top[m1 < 0.32] = B("smooth_basalt")
        top[(m2 > 0.62)] = B("tuff")
        top[(m2 < 0.3)] = B("gravel")
        top[(m3 > 0.82)] = B("magma")
        top[(m3 < 0.12)] = B("coarse_dirt")
        # scorched red badlands in the north-east
        red = (self.DX > 20) & (self.DZ < -15) & (m2 > 0.4)
        top[red & (m1 > 0.5)] = B("red_sandstone")
        top[red & (m1 <= 0.5)] = B("orange_terracotta")
        top[red & (m3 > 0.7)] = B("red_terracotta")
        top[red & (m3 < 0.25)] = B("red_sand")
        # ash field in the south-west
        ash = (self.DX < -22) & (self.DZ > 15)
        top[ash] = np.where(m1[ash] > 0.6, B("gray_concrete_powder"), np.where(m1[ash] > 0.35, B("tuff"), B("gravel")))
        # cone + crater
        cone = r < CONE_R + 1
        top[cone] = np.where(m1[cone] > 0.5, B("basalt"), np.where(m3[cone] > 0.7, B("magma"), B("blackstone")))
        crater_m = r < CRATER_R + 0.5
        top[crater_m] = np.where(m3[crater_m] > 0.45, B("magma"), B("netherrack"))
        # next to lava
        near = (self.lava_dist < 3.5) & (self.water == 0)
        top[near] = np.where(m3[near] > 0.5, B("magma"), np.where(m1[near] > 0.5, B("netherrack"), B("blackstone")))
        top[self.water > 0] = B("blackstone")
        # road surface
        top[self.road] = np.where(m3[self.road] > 0.55, B("polished_blackstone_bricks"),
                                  np.where(m3[self.road] > 0.3, B("cobbled_deepslate"), B("cracked_polished_blackstone_bricks")))
        self.top = top
        self.sub[:] = B("blackstone")
        self.deep[:] = B("deepslate")
        self.sub[cone] = B("basalt")
        stone_set = [B("blackstone"), B("basalt"), B("tuff"), B("deepslate"), B("smooth_basalt"),
                     B("blackstone"), B("cobbled_deepslate"), B("basalt")]
        off = (fbm(SIZE, SIZE, 10, 2, self.seed + 91) * 11).astype(np.int32)
        vein = fbm(SIZE, SIZE, 5, 2, self.seed + 93)
        speck = fbm(SIZE, SIZE, 3, 1, self.seed + 94)

        def strata(y):
            idx = ((y + off) // 3) % len(stone_set)
            arr = np.array(stone_set)[idx]
            arr = np.where((vein > 0.76) & (vein < 0.8), B("magma"), arr)
            arr = np.where(speck > 0.92, B("crying_obsidian"), arr)
            arr = np.where((vein > 0.8) & (vein < 0.81), B("ochre_froglight", axis="y"), arr)
            arr = np.where(y >= self.H, np.where(speck > 0.5, B("blackstone"), B("basalt")), arr)
            return arr
        self.strata = strata

    # ------------------------------------------------------------------
    def road_details(self):
        a = self.a
        rng = random.Random(1)
        # posts with lanterns on the inner side of the road, low walls on the outer side
        th0 = math.radians(-20)
        turns = 1.35
        for k in range(0, 100):
            s = k / 100
            th = th0 + s * turns * 2 * math.pi
            rr = (CONE_R + 1) - s * (CONE_R + 1 - (CRATER_R + 0.5))
            if k % 6 == 3 and s < 0.97:
                x = self.cx + round((rr - 2.6) * math.cos(th))
                z = self.cz + round((rr - 2.6) * math.sin(th))
                xr = self.cx + round((rr - 1.6) * math.cos(th))
                zr = self.cz + round((rr - 1.6) * math.sin(th))
                y = self.gy(xr, zr) + 1
                if a.get(xr, y, zr) == AIR:
                    a.set(xr, y, zr, B("polished_blackstone_wall"))
                    a.set(xr, y + 1, zr, B("lantern"))
            if k % 4 != 0 and s > 0.05:
                x = self.cx + round((rr + 2.4) * math.cos(th))
                z = self.cz + round((rr + 2.4) * math.sin(th))
                i, kk = x - self.a.x0, z - self.a.z0
                if not self.road[i, kk]:
                    y = self.gy(x, z)
                    ry = self.road_h.get((round((rr + 1.6) * math.cos(th)) + self.cx - self.a.x0,
                                          round((rr + 1.6) * math.sin(th)) + self.cz - self.a.z0))
                    if ry is not None and y <= round(ry) and a.get(x, int(round(ry)) + 1, z) == AIR:
                        a.set(x, int(round(ry)), z, B("blackstone"))
                        a.set(x, int(round(ry)) + 1, z, B("blackstone_wall"))
        # road entrance arch (spans the road, which starts heading north/+z)
        sx, sz = self.w(*self.road_start)
        az = sz - 2
        y = max(self.gy(sx + o, az) for o in range(-3, 4))
        for o in (-3, 3):
            for t in range(self.gy(sx + o, az) + 1, y + 7):
                a.set(sx + o, t, az, B("polished_blackstone_bricks"))
            a.set(sx + o, y + 7, az, B("soul_campfire", cardinal="south"))
            a.add_be(simple_be("Campfire", sx + o, y + 7, az))
        for o in range(-3, 4):
            a.set(sx + o, y + 6, az, B("polished_blackstone_bricks"))
        for o in (-1, 1):
            a.set(sx + o, y + 5, az, B("chain"))
            a.set(sx + o, y + 4, az, B("soul_lantern", hanging=1))
        a.set(sx + 4, self.gy(sx + 4, az) + 1, az, B("polished_blackstone_bricks"))
        wall_sign(a, sx + 4, self.gy(sx + 4, az) + 1, az - 1, 2, "§l§c▲ 화산 정상\n§r§f분화구까지\n§f오르는 길", kind="crimson_wall_sign")

    def crater_details(self):
        a = self.a
        cx, cz = self.w(0, 0)
        lava = B("lava")
        rng = random.Random(9)
        for x in range(cx - CRATER_R, cx + CRATER_R + 1):
            for z in range(cz - CRATER_R, cz + CRATER_R + 1):
                r = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                if r < 5.5:
                    yl = self.H0 + 21
                    a.set(x, yl, z, lava)
                    a.set(x, yl - 1, z, B("magma"))
                    for y in range(yl + 1, yl + 6):
                        a.set(x, y, z, AIR)
        # smoke vents on the crater terraces
        for ang in range(0, 360, 60):
            x = cx + round(math.cos(math.radians(ang + 15)) * 8)
            z = cz + round(math.sin(math.radians(ang + 15)) * 8)
            y = self.gy(x, z)
            a.set(x, y, z, B("campfire"))
            a.add_be(simple_be("Campfire", x, y, z))
        # rim braziers
        for ang in range(0, 360, 45):
            x = cx + round(math.cos(math.radians(ang)) * 12.5)
            z = cz + round(math.sin(math.radians(ang)) * 12.5)
            y = self.gy(x, z)
            if not self.road[x - self.a.x0, z - self.a.z0]:
                a.set(x, y + 1, z, B("netherrack"))
                a.set(x, y + 2, z, B("fire", age=0))
        self.pois["crater"] = (cx, self.H0 + 22, cz)

    def lava_tube(self):
        """North-south lava tube through the base of the volcano, lit by a lava trench.
        Roofed where the cone is thick enough, open cut near the mouths."""
        a = self.a
        cx, cz = self.w(0, 0)
        y0 = self.H0
        lava = B("lava")
        for z in range(cz - CONE_R - 4, cz + CONE_R + 5):
            for x in range(cx - 2, cx + 3):
                g = self.gy(x, z)
                if g <= y0:
                    continue
                a.set(x, y0, z, B("polished_blackstone_bricks") if abs(x - cx) < 2 else B("blackstone"))
                if g >= y0 + 5:
                    for y in range(y0 + 1, y0 + 5):
                        a.set(x, y, z, AIR)
                    if g >= y0 + 7 and z % 5 == 0:
                        a.set(x, y0 + 5, z, B("magma"))
                else:
                    for y in range(y0 + 1, g + 1):
                        a.set(x, y, z, AIR)
                    self.H[x - self.a.x0, z - self.a.z0] = y0
            # lava trench along the east side, behind a low wall
            g = self.gy(cx + 3, z)
            if g >= y0 + 5 and abs(z - cz) < CONE_R - 6:
                a.set(cx + 3, y0, z, lava)
                a.set(cx + 3, y0 - 1, z, B("magma"))
                for y in range(y0 + 1, y0 + 5):
                    a.set(cx + 3, y, z, AIR)
                a.set(cx + 2, y0 + 1, z, B("polished_blackstone_wall") if z % 6 else AIR)
            if abs(z - cz) < CONE_R - 4 and z % 8 == 0 and self.gy(cx, z) >= y0 + 6:
                a.set(cx - 2, y0 + 4, z, B("chain"))
                a.set(cx - 2, y0 + 3, z, B("soul_lantern", hanging=1))
        self.pois["tube"] = (cx, y0 + 1, cz)

    # ------------------------------------------------------------------
    def temple(self, dx, dz):
        a = self.a
        rng = random.Random(55)
        cx, cz = self.w(dx, dz)
        g = self.H0 + 1
        self.reserved[(np.abs(self.DX - dx) <= 14) & (np.abs(self.DZ - dz) <= 14)] = True
        nb = B("nether_brick")
        rnb = B("red_nether_brick")
        pbb = B("polished_blackstone_bricks")
        # raised platform 2 high with stairs on all sides
        a.fill(cx - 11, g, cz - 9, cx + 11, g + 1, cz + 9, pbb)
        for x in range(cx - 11, cx + 12):
            a.set(x, g, cz - 10, stair("polished_blackstone_brick_stairs", "south"))
            a.set(x, g, cz + 10, stair("polished_blackstone_brick_stairs", "north"))
        for z in range(cz - 9, cz + 10):
            a.set(cx - 12, g, z, stair("polished_blackstone_brick_stairs", "east"))
            a.set(cx + 12, g, z, stair("polished_blackstone_brick_stairs", "west"))
        for x in range(cx - 11, cx + 12):
            a.set(x, g + 1, cz - 9, stair("polished_blackstone_brick_stairs", "south"))
            a.set(x, g + 1, cz + 9, stair("polished_blackstone_brick_stairs", "north"))
        for z in range(cz - 8, cz + 9):
            a.set(cx - 11, g + 1, z, stair("polished_blackstone_brick_stairs", "east"))
            a.set(cx + 11, g + 1, z, stair("polished_blackstone_brick_stairs", "west"))
        floor_y = g + 2
        # floor pattern
        for x in range(cx - 10, cx + 11):
            for z in range(cz - 8, cz + 9):
                a.set(x, g + 1, z, B("gilded_blackstone") if (x + z) % 7 == 0 else
                      B("polished_blackstone") if (x // 2 + z // 2) % 2 else pbb)
        # colonnade (ruined: some broken)
        for x in range(cx - 9, cx + 10, 3):
            for z in (cz - 7, cz + 7):
                hgt = rng.choice([8, 8, 8, 5, 3, 8])
                for y in range(floor_y, floor_y + hgt):
                    a.set(x, y, z, nb if (y - floor_y) % 4 else B("chiseled_nether_bricks"))
                if hgt == 8:
                    a.set(x, floor_y + 8, z, rnb)
        # partial roof beams on intact columns
        for z in (cz - 7, cz + 7):
            for x in range(cx - 9, cx + 10):
                if rng.random() < 0.75:
                    a.set(x, floor_y + 8, z, B("nether_brick_slab", half="bottom") if a.get(x, floor_y + 8, z) == AIR else a.get(x, floor_y + 8, z))
        # inner sanctum walls (low, broken) with doorways
        for x in range(cx - 5, cx + 6):
            for z in (cz - 4, cz + 4):
                if abs(x - cx) > 1:
                    for y in range(floor_y, floor_y + rng.choice([1, 2, 3, 3])):
                        a.set(x, y, z, rnb)
        for z in range(cz - 4, cz + 5):
            for x in (cx - 5, cx + 5):
                if abs(z - cz) > 1:
                    for y in range(floor_y, floor_y + rng.choice([1, 2, 3, 3])):
                        a.set(x, y, z, rnb)
        # central brazier
        a.set(cx, floor_y, cz, B("polished_blackstone_bricks"))
        a.set(cx, floor_y + 1, cz, B("soul_campfire"))
        a.add_be(simple_be("Campfire", cx, floor_y + 1, cz))
        for (ox, oz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
            a.set(cx + ox, floor_y, cz + oz, B("cauldron", cauldron_liquid="lava", fill_level=6))
            a.add_be(simple_be("Cauldron", cx + ox, floor_y, cz + oz))
        # soul lanterns on chains from the beams, banners of gilded blackstone
        for x in range(cx - 8, cx + 9, 3):
            for z in (cz - 7, cz + 7):
                if a.get(x, floor_y + 8, z) != AIR and a.get(x, floor_y + 7, z) == AIR:
                    a.set(x, floor_y + 7, z, B("chain"))
                    a.set(x, floor_y + 6, z, B("soul_lantern", hanging=1))
        for (ox, oz) in ((-9, -8), (9, -8), (-9, 8), (9, 8)):
            a.set(cx + ox, floor_y, cz + oz, B("polished_blackstone_wall"))
            a.set(cx + ox, floor_y + 1, cz + oz, B("soul_lantern"))
        # side balcony (second level) reachable by stairs
        bx = cx + 8
        for i in range(5):
            a.set(bx - i, floor_y + i, cz + 5, stair("nether_brick_stairs", "west"))
            for y in range(floor_y, floor_y + i):
                a.set(bx - i, y, cz + 5, nb)
        a.fill(cx - 2, floor_y + 4, cz + 5, cx + 3, floor_y + 4, cz + 6, nb)
        for x in range(cx - 2, cx + 4):
            a.set(x, floor_y + 5, cz + 6, B("nether_brick_fence"))
        a.set(cx - 2, floor_y + 5, cz + 5, B("nether_brick_fence"))
        a.set(cx, g + 2, cz - 12, B("polished_blackstone_bricks"))
        a.set(cx, g + 3, cz - 12, B("polished_blackstone_bricks"))
        wall_sign(a, cx, g + 3, cz - 13, 2, "§l§4불의 신전\n§r§7오래전 버려진\n§7화산의 제단", kind="crimson_wall_sign")
        self.pois["temple"] = (cx, floor_y, cz)

    def pillars(self):
        a = self.a
        rng = random.Random(77)
        # basalt pillar field in the north-west
        pts = self.scatter(80, 3.2, lambda x, z: self.ok_spot(x, z, margin=6) and x < -24 and z < -10
                           and math.hypot(x, z) > CONE_R + 6)
        for (dx, dz) in pts:
            x, z = self.w(dx, dz)
            g = self.gy(x, z)
            h = rng.choice([2, 3, 4, 5, 6, 7, 8, 10])
            for y in range(g + 1, g + 1 + h):
                a.set(x, y, z, B("basalt", axis="y") if rng.random() < 0.8 else B("polished_basalt", axis="y"))
            if rng.random() < 0.35:
                a.set(x + 1, g + 1, z, B("basalt", axis="y"))
                if h > 3:
                    a.set(x + 1, g + 2, z, B("basalt", axis="y"))
            if rng.random() < 0.2:
                a.set(x, g + 1 + h, z, B("magma"))
            self.reserved[x - self.a.x0, z - self.a.z0] = True
        self.pois["pillars"] = self.w(-48, -30)

    def spires(self):
        a = self.a
        rng = random.Random(31)
        pts = self.scatter(9, 11, lambda x, z: self.ok_spot(x, z, margin=8) and x > 18 and z < -20)
        for (dx, dz) in pts:
            x, z = self.w(dx, dz)
            g = self.gy(x, z)
            h = rng.randint(7, 14)
            lean = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15))
            for y in range(g - 1, g + h):
                t = (y - g) / h
                r = 1.9 * (1 - t) + 0.3
                ox, oz = lean[0] * (y - g), lean[1] * (y - g)
                for xx in range(x - 3, x + 4):
                    for zz in range(z - 3, z + 4):
                        if (xx - x - ox) ** 2 + (zz - z - oz) ** 2 <= r * r:
                            a.set(xx, y, zz, B("crying_obsidian") if rng.random() < 0.18 else B("obsidian"))
            self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 9] = True

    def ash_field(self):
        a = self.a
        rng = random.Random(13)
        pts = self.scatter(16, 9, lambda x, z: self.ok_spot(x, z, margin=5) and x < -20 and z > 14)
        for n, (dx, dz) in enumerate(pts):
            x, z = self.w(dx, dz)
            g = self.gy(x, z)
            if n % 3 == 0:
                # smoke vent: campfire in a 1-deep hole ringed by magma
                a.set(x, g, z, B("campfire"))
                a.add_be(simple_be("Campfire", x, g, z))
                for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a.set(x + ox, g, z + oz, B("magma"))
            elif n % 3 == 1:
                dead_tree(a, x, g + 1, z, rng, kind="dark_oak")
            else:
                # half-buried fossil
                for t in range(rng.randint(3, 5)):
                    a.set(x + t, g + (1 if t % 2 else 0), z, B("bone_block", axis="x"))
        self.pois["ash"] = self.w(-44, 44)

    def bridges(self):
        a = self.a
        for pts, fracs in ((self.river1, (0.35, 0.75)), (self.river2, (0.3, 0.68))):
            n = len(pts)
            for f in fracs:
                i = int(n * f)
                (x0, z0), (x1, z1) = pts[i], pts[min(n - 1, i + 3)]
                tx, tz = x1 - x0, z1 - z0
                if abs(tz) > abs(tx):     # river runs along z -> bridge along x
                    p0, p1 = (round(x0) - 6, round(z0)), (round(x0) + 6, round(z0))
                else:
                    p0, p1 = (round(x0), round(z0) - 6), (round(x0), round(z0) + 6)
                w0, w1 = self.w(*p0), self.w(*p1)
                f0, f1 = self.gy(*w0) + 1, self.gy(*w1) + 1
                mid = max(f0, f1) + 1
                pm = ((w0[0] + w1[0]) // 2, (w0[1] + w1[1]) // 2)
                bridge(a, w0, pm, f0, mid, B("polished_blackstone_bricks"), slab("polished_blackstone_brick_slab"),
                       B("polished_blackstone_wall"), lamp=B("soul_lantern"), lamp_every=7)
                bridge(a, pm, w1, mid, f1, B("polished_blackstone_bricks"), slab("polished_blackstone_brick_slab"),
                       B("polished_blackstone_wall"), lamp=B("soul_lantern"), lamp_every=7)

    def decorate(self):
        a = self.a
        rng = random.Random(3)
        for i in range(SIZE):
            for k in range(SIZE):
                if self.water[i, k] or self.road[i, k] or self.reserved[i, k]:
                    continue
                x, z = i + self.a.x0, k + self.a.z0
                y = int(self.H[i, k]) + 1
                if a.get(x, y, z) != AIR:
                    continue
                below = a.get(x, y - 1, z)
                r = rng.random()
                if self.wall[i, k]:
                    if below == B("netherrack") or (r < 0.004):
                        a.set(x, y - 1, z, B("netherrack"))
                        a.set(x, y, z, B("fire", age=0))
                    elif r < 0.02 and below in (B("red_sand"), B("coarse_dirt")):
                        a.set(x, y, z, B("deadbush"))
                    continue
                if below == B("netherrack") and r < 0.08 and self.r[i, k] > CRATER_R:
                    a.set(x, y, z, B("fire", age=0))
                elif below in (B("red_sand"), B("coarse_dirt"), B("orange_terracotta")) and r < 0.05:
                    a.set(x, y, z, B("deadbush"))
                elif r < 0.004:
                    a.set(x, y, z, B("crimson_roots"))
        # dead trees and rocks around the plains
        pts = self.scatter(40, 11, lambda x, z: self.ok_spot(x, z, margin=5) and math.hypot(x, z) > CONE_R + 4)
        for n, (dx, dz) in enumerate(pts):
            x, z = self.w(dx, dz)
            g = self.gy(x, z)
            if n % 2 == 0:
                dead_tree(a, x, g + 1, z, rng, kind="dark_oak")
            else:
                boulder(a, x, g + 0.5, z, rng, rng.uniform(1.3, 2.2), [B("blackstone"), B("basalt"), B("obsidian"),
                                                                     B("magma"), B("tuff")])
        # lamp posts near spawns and bridges
        for (dx, dz) in ((46, -10), (46, 10), (-44, 2), (0, 44), (-20, -40)):
            x, z = self.w(dx, dz)
            lamp_post(a, x, self.gy(x, z) + 1, z, B("polished_blackstone_wall"), B("lantern"), height=2)

    def falls(self):
        a = self.a
        for ang in self.fall_angles:
            cascade(self, ang, 1.2, self.H0 + 16, LL, B("lava"), B("flowing_lava", liquid_depth=8), B("blackstone"),
                    fill_base=True)
