"""Map 4 - Factory ("폐공장 단지"): an industrial complex - warehouse with racks, smelter and chimney,
tank farm with catwalks, container yard with a gantry crane, offices, pipes and a concrete wall."""
import math
import random

import numpy as np

from mcw import B, AIR, simple_be
from gen_common import (fbm, lamp_post, stair, slab, disk, ring, cylinder, wall_sign, standing_sign, hanging_lamp,
                        line_points)
from gen_mapbase import MapBase, SIZE

Y = 64   # ground block level


class Factory(MapBase):
    def __init__(self, cx, cz):
        super().__init__("factory", cx, cz, seed=4404, biome=1, p=14.0)

    def w3(self, dx, y, dz):
        return self.cx + dx, y, self.cz + dz

    def box(self, x1, y1, z1, x2, y2, z2, b, only_air=False):
        self.a.fill(self.cx + x1, y1, self.cz + z1, self.cx + x2, y2, self.cz + z2, b, only_air=only_air)

    def put(self, dx, y, dz, b):
        self.a.set(self.cx + dx, y, self.cz + dz, b)

    def get(self, dx, y, dz):
        return self.a.get(self.cx + dx, y, self.cz + dz)

    def build(self):
        self.ground()
        self.perimeter()
        self.skyline()
        self.warehouse(-40, -64, 6, -38)
        self.smelter(28, -56, 60, -22)
        self.tanks()
        self.containers()
        self.offices(-64, -24, -46, 2)
        self.control_plaza()
        self.loading_dock()
        self.scrap_yard()
        self.substation()
        self.pipes()
        self.props()
        self.street_lights()
        self.barrier()
        self.a.fix_walls()
        sp = [(0, 8), (8, 0), (-8, 0)]
        self.spawns = [(self.cx + dx, Y + 1, self.cz + dz) for dx, dz in sp]
        return self.a

    # ------------------------------------------------------------------
    def ground(self):
        self.H[:] = Y
        n = fbm(SIZE, SIZE, 6, 2, self.seed)
        n2 = fbm(SIZE, SIZE, 18, 2, self.seed + 1)
        top = np.full((SIZE, SIZE), B("light_gray_concrete"), np.int32)
        top[n > 0.6] = B("gray_concrete")
        top[n < 0.3] = B("smooth_stone")
        top[(n2 > 0.7)] = B("polished_andesite")
        top[(n2 < 0.2) & (n > 0.5)] = B("gravel")
        top[(n2 < 0.15) & (n < 0.35)] = B("cracked_stone_bricks")
        # roads: asphalt grid with markings
        ax = np.abs(self.DX)
        az = np.abs(self.DZ)
        road = (ax <= 3) | (az <= 3) | ((np.abs(self.DZ - 8) <= 2) & (self.DX > 6)) | (np.abs(self.DX + 20) <= 2)
        top[road] = B("gray_concrete")
        top[road & (n > 0.7)] = B("black_concrete")
        mark = ((ax == 0) & (self.DZ % 6 < 3)) | ((az == 0) & (self.DX % 6 < 3))
        top[mark & ((ax <= 3) | (az <= 3))] = B("yellow_concrete")
        edge = ((ax == 4) & (az > 4)) | ((az == 4) & (ax > 4))
        top[edge] = B("white_concrete")
        self.top = top
        self.sub[:] = B("stone")
        self.deep[:] = B("stone")
        # wall footprint
        self.wall = self.D > self.R - 1.5
        self.wall_start = np.full((SIZE, SIZE), self.R - 1.5)
        self.wall_t = self.D - (self.R - 1.5)
        self.H = np.where(self.wall, Y, self.H)
        self.paint(ybase=50)

    def perimeter(self):
        a = self.a
        top_y = Y + 14
        gray = B("gray_concrete")
        lgray = B("light_gray_concrete")
        stripe = (B("yellow_concrete"), B("black_concrete"))
        A = np.arctan2(self.DZ, self.DX)
        for (i, k) in np.argwhere((self.D > self.R - 1.5) & (self.D <= self.R + 3)):
            x, z = i + a.x0, k + a.z0
            dx, dz = x - self.cx, z - self.cz
            along = (dx if abs(dz) > abs(dx) else dz)
            pil = along % 10 == 0
            for y in range(Y + 1, top_y + 1):
                b = lgray if pil else gray
                if y <= Y + 2 and not pil:
                    b = stripe[(along // 2 + y) % 2]
                if y == top_y:
                    b = B("polished_andesite")
                a.set(x, y, z, b)
            self.H[i, k] = top_y
            if self.D[i, k] <= self.R - 0.5:
                # inner face details: lamps on pilasters, iron bars on top
                a.set(x, top_y + 1, z, B("iron_bars"))
                a.set(x, top_y + 2, z, B("iron_bars") if along % 2 == 0 else AIR)
                if pil:
                    a.set(x, top_y + 1, z, lgray)
                    a.set(x, top_y + 2, z, B("sea_lantern"))
        # pilaster bumps on the inner face
        for (i, k) in np.argwhere((self.D > self.R - 2.5) & (self.D <= self.R - 1.5)):
            x, z = i + a.x0, k + a.z0
            dx, dz = x - self.cx, z - self.cz
            along = (dx if abs(dz) > abs(dx) else dz)
            if along % 10 == 0:
                for y in range(Y + 1, top_y):
                    a.set(x, y, z, lgray)
                a.set(x, Y + 9, z, B("sea_lantern"))
        # corner watchtowers
        for sx in (-1, 1):
            for sz in (-1, 1):
                tx, tz = self.cx + sx * 72, self.cz + sz * 72
                a.fill(tx - 3, Y + 1, tz - 3, tx + 3, Y + 22, tz + 3, B("gray_concrete"))
                a.fill(tx - 3, Y + 18, tz - 3, tx + 3, Y + 21, tz + 3, B("glass"))
                a.fill(tx - 2, Y + 18, tz - 2, tx + 2, Y + 21, tz + 2, AIR)
                a.fill(tx - 4, Y + 22, tz - 4, tx + 4, Y + 22, tz + 4, B("smooth_stone_slab"))
                a.set(tx, Y + 19, tz, B("lantern"))
                a.set(tx - sx * 4, Y + 17, tz - sz * 4, B("sea_lantern"))
                a.set(tx - sx * 4, Y + 16, tz - sz * 4, B("iron_bars"))

    def skyline(self):
        """Background industrial buildings beyond the wall (not reachable)."""
        a = self.a
        rng = random.Random(9)
        cols = ["light_gray_concrete", "gray_concrete", "white_concrete", "brick_block", "cyan_terracotta",
                "light_gray_terracotta", "stone_bricks"]
        placed = []
        for _ in range(400):
            ang = rng.random() * 2 * math.pi
            dist = rng.uniform(self.R + 9, self.R + 30)
            dx, dz = math.cos(ang) * dist, math.sin(ang) * dist
            dx = max(-106, min(100, dx))
            dz = max(-106, min(100, dz))
            w, d = rng.randint(6, 14), rng.randint(6, 14)
            if any(abs(dx - px) < (w + pw) / 2 + 2 and abs(dz - pz) < (d + pd) / 2 + 2 for px, pz, pw, pd in placed):
                continue
            placed.append((dx, dz, w, d))
            h = rng.randint(10, 42)
            x1, z1 = int(dx - w / 2), int(dz - d / 2)
            col = B(rng.choice(cols))
            self.box(x1, Y + 1, z1, x1 + w, Y + h, z1 + d, col)
            # window bands
            for y in range(Y + 4, Y + h - 1, 4):
                for x in range(x1 + 1, x1 + w, 2):
                    for z in (z1, z1 + d):
                        self.put(x, y, z, B("glass") if rng.random() < 0.7 else B("yellow_stained_glass"))
                for z in range(z1 + 1, z1 + d, 2):
                    for x in (x1, x1 + w):
                        self.put(x, y, z, B("glass") if rng.random() < 0.7 else B("yellow_stained_glass"))
            self.box(x1, Y + h + 1, z1, x1 + w, Y + h + 1, z1 + d, B("smooth_stone_slab"))
            if rng.random() < 0.35:
                # rooftop chimney with smoke
                cxh, czh = x1 + w // 2, z1 + d // 2
                ch = rng.randint(8, 20)
                self.box(cxh - 1, Y + h + 1, czh - 1, cxh + 1, Y + h + ch, czh + 1, B("brick_block"))
                self.box(cxh, Y + h + 1, czh, cxh, Y + h + ch, czh, AIR)
                self.put(cxh, Y + h + ch - 1, czh, B("campfire"))
                a.add_be(simple_be("Campfire", self.cx + cxh, Y + h + ch - 1, self.cz + czh))
                self.put(cxh, Y + h + 2, czh, B("brick_block"))
            if rng.random() < 0.5:
                self.put(x1 + 1, Y + h + 2, z1 + 1, B("sea_lantern"))
        # cooling tower in the far corner
        tx, tz = 92, 92
        for y in range(0, 44):
            t = (y - 26) / 26
            r = 9 + 6 * t * t
            ring(a, self.cx + tx, Y + 1 + y, self.cz + tz, r - 1.2, r, B("light_gray_concrete"))
        self.put(tx, Y + 44, tz, B("campfire"))
        a.add_be(simple_be("Campfire", self.cx + tx, Y + 44, self.cz + tz))

    # ------------------------------------------------------------------
    def warehouse(self, x1, z1, x2, z2):
        a = self.a
        rng = random.Random(21)
        top = Y + 13
        self.reserved[(self.DX >= x1 - 1) & (self.DX <= x2 + 1) & (self.DZ >= z1 - 1) & (self.DZ <= z2 + 1)] = True
        self.box(x1, Y, z1, x2, Y, z2, B("polished_andesite"))
        self.box(x1, Y + 1, z1, x2, top, z2, B("white_concrete"))
        self.box(x1, Y + 1, z1, x2, Y + 4, z2, B("light_gray_concrete"))
        self.box(x1 + 1, Y + 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
        # steel frame
        for x in range(x1, x2 + 1, 6):
            for z in (z1, z2):
                self.box(x, Y + 1, z, x, top, z, B("iron_block"))
        for z in range(z1, z2 + 1, 6):
            for x in (x1, x2):
                self.box(x, Y + 1, z, x, top, z, B("iron_block"))
        # window band
        for x in range(x1 + 1, x2):
            for z in (z1, z2):
                if self.get(x, Y + 7, z) == B("white_concrete"):
                    self.box(x, Y + 7, z, x, Y + 9, z, B("glass_pane"))
        for z in range(z1 + 1, z2):
            for x in (x1, x2):
                if self.get(x, Y + 7, z) == B("white_concrete"):
                    self.box(x, Y + 7, z, x, Y + 9, z, B("glass_pane"))
        # roof with skylights
        self.box(x1 - 1, top, z1 - 1, x2 + 1, top, z2 + 1, B("smooth_stone"))
        for x in range(x1 + 4, x2 - 3, 8):
            self.box(x, top, z1 + 3, x + 2, top, z2 - 3, B("glass"))
        # big doorways (south side) and side doors
        for dx in (x1 + 7, x1 + 19, x1 + 31):
            self.box(dx, Y + 1, z2, dx + 4, Y + 5, z2, AIR)
            self.box(dx - 1, Y + 6, z2, dx + 5, Y + 6, z2, B("yellow_concrete"))
            for t in range(dx, dx + 5):
                self.put(t, Y + 6, z2 + 1, B("iron_trapdoor", direction=2, open_bit=0, upside_down_bit=1))
        for z in (z1 + 8,):
            self.box(x1, Y + 1, z, x1, Y + 4, z + 3, AIR)
            self.box(x2, Y + 1, z, x2, Y + 4, z + 3, AIR)
        self.box(x1 + 20, Y + 1, z1, x1 + 23, Y + 4, z1, AIR)
        # storage racks (rows along x)
        rack_up = B("stripped_spruce_log", axis="y")
        shelf = B("spruce_slab", half="top")
        goods = [B("barrel", facing_direction=1), B("composter"), B("hay_block"), B("spruce_planks"),
                 B("brown_wool"), B("chest", cardinal="south"), B("smithing_table"), B("iron_block")]
        for rz in range(z1 + 4, z2 - 6, 5):
            for rx in range(x1 + 3, x2 - 12, 1):
                if (rx - x1) % 18 in (16, 17):
                    continue      # cross aisles
                for zz in (rz, rz + 1):
                    if (rx - x1) % 4 == 3:
                        self.box(rx, Y + 1, zz, rx, Y + 7, zz, rack_up)
                    else:
                        for lvl in (Y + 3, Y + 6):
                            self.put(rx, lvl, zz, shelf)
                        for lvl in (Y + 1, Y + 4):
                            if rng.random() < 0.55:
                                g = rng.choice(goods)
                                self.put(rx, lvl, zz, g)
                                if g == B("chest", cardinal="south"):
                                    a.add_be(simple_be("Chest", self.cx + rx, lvl, self.cz + zz))
        # mezzanine along the east wall with stairs and railing
        mx1 = x2 - 10
        self.box(mx1, Y + 6, z1 + 1, x2 - 1, Y + 6, z2 - 1, B("smooth_stone_slab", half="top"))
        for z in range(z1 + 1, z2):
            if (z - z1) % 7 != 3:
                self.put(mx1 - 1, Y + 7, z, B("iron_bars"))
        for z in range(z1 + 4, z2, 6):
            self.box(mx1, Y + 1, z, mx1, Y + 5, z, B("iron_block"))
        for i in range(6):
            self.put(mx1 - 1 - i, Y + 6 - i, z2 - 2, stair("polished_andesite_stairs", "east"))
            self.put(mx1 - 1 - i, Y + 6 - i, z2 - 3, stair("polished_andesite_stairs", "east"))
            for y in range(Y + 1, Y + 6 - i):
                self.put(mx1 - 1 - i, y, z2 - 2, AIR)
                self.put(mx1 - 1 - i, y, z2 - 3, AIR)
        for z in (z2 - 2, z2 - 3):
            self.put(mx1 - 1, Y + 7, z, AIR)
        # office box on the mezzanine
        self.box(x2 - 7, Y + 7, z1 + 2, x2 - 1, Y + 10, z1 + 8, B("white_concrete"))
        self.box(x2 - 6, Y + 7, z1 + 3, x2 - 1, Y + 9, z1 + 7, AIR)
        self.box(x2 - 7, Y + 8, z1 + 3, x2 - 7, Y + 9, z1 + 7, B("glass_pane"))
        self.box(x2 - 7, Y + 7, z1 + 5, x2 - 7, Y + 8, z1 + 5, AIR)
        self.put(x2 - 3, Y + 7, z1 + 5, B("dark_oak_stairs", weirdo_direction=1))
        self.put(x2 - 4, Y + 7, z1 + 5, B("dark_oak_slab", half="top"))
        self.put(x2 - 4, Y + 9, z1 + 5, B("lantern", hanging=1))
        # ceiling lights
        for x in range(x1 + 3, x2 - 1, 6):
            for z in range(z1 + 3, z2 - 1, 6):
                self.put(x, top - 1, z, B("chain"))
                self.put(x, top - 2, z, B("lantern", hanging=1))
        # forklift
        fx, fz = x1 + 12, z2 - 3
        self.box(fx, Y + 1, fz, fx + 1, Y + 2, fz + 1, B("yellow_concrete"))
        self.put(fx + 2, Y + 1, fz, B("iron_bars"))
        self.put(fx + 2, Y + 1, fz + 1, B("iron_bars"))
        self.put(fx, Y + 3, fz, B("black_carpet"))
        wall_sign(a, self.cx + x1 + 9, Y + 7, self.cz + z2 + 1, 3, "§l§7A동 창고\n§r§8WAREHOUSE A", kind="wall_sign")
        self.pois["warehouse"] = self.w3((x1 + x2) // 2, Y + 1, (z1 + z2) // 2)

    def smelter(self, x1, z1, x2, z2):
        a = self.a
        top = Y + 12
        self.reserved[(self.DX >= x1 - 1) & (self.DX <= x2 + 1) & (self.DZ >= z1 - 1) & (self.DZ <= z2 + 1)] = True
        self.box(x1, Y, z1, x2, Y, z2, B("polished_deepslate"))
        # open shed: columns + roof
        for x in range(x1, x2 + 1, 8):
            for z in range(z1, z2 + 1, 8):
                self.box(x, Y + 1, z, x, top - 1, z, B("polished_blackstone"))
        self.box(x1, top, z1, x2, top, z2, B("weathered_cut_copper"))
        for x in range(x1 + 2, x2, 6):
            self.box(x, top, z1 + 2, x + 1, top, z2 - 2, B("cut_copper"))
        # big furnace block with lava viewport
        fx1, fz1 = x1 + 10, z1 + 9
        self.box(fx1, Y + 1, fz1, fx1 + 9, Y + 10, fz1 + 9, B("brick_block"))
        self.box(fx1 + 1, Y + 1, fz1 + 1, fx1 + 8, Y + 9, fz1 + 8, B("brick_block"))
        self.box(fx1 + 3, Y + 2, fz1 - 0, fx1 + 6, Y + 4, fz1, B("iron_bars"))
        self.box(fx1 + 3, Y + 2, fz1 + 1, fx1 + 6, Y + 2, fz1 + 3, B("lava"))
        self.box(fx1 + 3, Y + 1, fz1 + 1, fx1 + 6, Y + 1, fz1 + 3, B("magma"))
        self.box(fx1 + 3, Y + 3, fz1 + 1, fx1 + 6, Y + 4, fz1 + 3, AIR)
        for x in range(fx1, fx1 + 10, 3):
            self.put(x, Y + 1, fz1 - 1, B("lit_blast_furnace", cardinal="north"))
        # chimney stack through the roof
        sx, sz = fx1 + 4, fz1 + 4
        self.box(sx - 2, Y + 11, sz - 2, sx + 2, Y + 40, sz + 2, B("brick_block"))
        self.box(sx - 1, Y + 11, sz - 1, sx + 1, Y + 40, sz + 1, AIR)
        for y in range(Y + 14, Y + 40, 6):
            self.box(sx - 2, y, sz - 2, sx + 2, y, sz + 2, B("red_nether_brick"))
        self.box(sx - 1, Y + 38, sz - 1, sx + 1, Y + 38, sz + 1, B("brick_block"))
        for (ox, oz) in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            self.put(sx + ox, Y + 39, sz + oz, B("campfire"))
            a.add_be(simple_be("Campfire", self.cx + sx + ox, Y + 39, self.cz + sz + oz))
        self.put(sx + 2, Y + 41, sz + 2, B("redstone_torch", torch_facing_direction="top"))
        # cauldrons of molten metal, anvils, hoppers
        for (ox, oz) in ((3, 4), (5, 4), (3, 26), (6, 26), (20, 4), (22, 4)):
            self.put(x1 + ox, Y + 1, z1 + oz, B("cauldron", cauldron_liquid="lava", fill_level=6))
            a.add_be(simple_be("Cauldron", self.cx + x1 + ox, Y + 1, self.cz + z1 + oz))
        for (ox, oz) in ((26, 10), (26, 14)):
            self.put(x1 + ox, Y + 1, z1 + oz, B("anvil", cardinal="north"))
        for x in range(x1 + 2, x1 + 9):
            self.put(x, Y + 3, z1 + 14, B("hopper", facing_direction=5))
            self.put(x, Y + 1, z1 + 14, B("iron_bars"))
            if x % 3 == 0:
                self.put(x, Y + 2, z1 + 14, B("iron_bars"))
        # conveyor belt toward the furnace
        for x in range(x1 - 14, fx1):
            self.put(x, Y + 1, fz1 + 4, B("black_concrete"))
            self.put(x, Y + 1, fz1 + 5, B("black_concrete"))
            self.put(x, Y + 2, fz1 + 4, B("rail", rail_direction=1))
            self.put(x, Y + 2, fz1 + 5, B("rail", rail_direction=1))
            if x % 4 == 0:
                self.put(x, Y + 3, fz1 + 4, B("raw_iron_block") if x % 8 == 0 else AIR)
        for (ox, oz) in ((2, 2), (x2 - x1 - 2, 2), (2, z2 - z1 - 2), (x2 - x1 - 2, z2 - z1 - 2)):
            self.put(x1 + ox, top - 1, z1 + oz, B("chain"))
            self.put(x1 + ox, top - 2, z1 + oz, B("lantern", hanging=1))
        for x in range(x1 + 4, x2, 8):
            for z in range(z1 + 4, z2, 8):
                self.put(x, top - 1, z, B("copper_bulb", lit=1))
        self.pois["smelter"] = self.w3(x1 + 4, Y + 1, z1 + 4)

    def tanks(self):
        a = self.a
        specs = [(-50, 34, 6, 12), (-30, 26, 5, 10), (-48, 56, 5, 14), (-28, 50, 6, 11)]
        tops = []
        for (dx, dz, r, h) in specs:
            x, z = self.cx + dx, self.cz + dz
            self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= (r + 2) ** 2] = True
            for y in range(Y + 1, Y + h + 1):
                b = B("iron_block") if (y - Y) % 4 == 0 else B("white_concrete")
                disk(a, x, y, z, r, b)
            disk(a, x, Y + h + 1, z, r, B("smooth_stone_slab"))
            disk(a, x, Y + h + 1, z, r - 1.5, B("light_gray_concrete"))
            disk(a, x, Y + h + 1, z, 1, B("iron_block"))
            a.set(x, Y + h + 2, z, B("lantern"))
            # ladder up the south side
            lz = z + r + 1
            for y in range(Y + 1, Y + h + 2):
                a.set(x, y, lz, B("ladder", facing_direction=3))
            a.set(x, Y + h + 1, lz - 1, B("smooth_stone_slab"))
            # railing on the rim
            for xx in range(x - r - 1, x + r + 2):
                for zz in range(z - r - 1, z + r + 2):
                    d = math.sqrt((xx - x) ** 2 + (zz - z) ** 2)
                    if r - 0.6 < d <= r + 0.4 and (xx + zz) % 3 == 0 and a.get(xx, Y + h + 2, zz) == AIR:
                        a.set(xx, Y + h + 2, zz, B("iron_bars"))
            tops.append((x, Y + h + 2, z, r))
            for side in (-1, 1):
                a.set(x + side * (r + 1), Y + 3, z, B("copper_block"))
                a.set(x + side * (r + 2), Y + 3, z, B("copper_block"))
        # catwalks between tank tops
        for (p, q) in ((0, 1), (0, 2), (1, 3), (2, 3)):
            (x1, y1, z1, r1), (x2, y2, z2, r2) = tops[p], tops[q]
            pts = line_points((x1, y1 - 1, z1), (x2, y2 - 1, z2), step=0.3)
            for (x, y, z) in pts:
                d1 = math.dist((x, z), (x1, z1))
                d2 = math.dist((x, z), (x2, z2))
                if d1 <= r1 - 0.5 or d2 <= r2 - 0.5:
                    continue
                yy = round(y1 - 1 + (y2 - y1) * (d1 / (d1 + d2)))
                for o in (0,):
                    a.set(x, yy, z, B("iron_block"))
                    a.set(x, yy + 1, z, AIR)
                    a.set(x, yy + 2, z, AIR)
        self.pois["tanks"] = (self.cx - 40, Y + 1, self.cz + 40)

    def containers(self):
        a = self.a
        rng = random.Random(33)
        cols = ["red", "blue", "green", "orange", "cyan", "gray", "brown", "lime"]
        x1, x2, z1, z2 = 14, 62, 18, 62
        self.reserved[(self.DX >= x1) & (self.DX <= x2) & (self.DZ >= z1) & (self.DZ <= z2)] = True
        rows = list(range(z1 + 2, z2 - 3, 7))
        for ri, rz in enumerate(rows):
            x = x1 + 1 + (ri % 2) * 3
            while x + 7 < x2:
                c = B(rng.choice(cols) + "_concrete")
                stack = rng.choice([1, 1, 2, 2, 1])
                opened = rng.random() < 0.3
                for s in range(stack):
                    y0 = Y + 1 + s * 3
                    self.box(x, y0, rz, x + 7, y0 + 2, rz + 2, c)
                    if s == 0 and opened:
                        self.box(x, y0, rz + 1, x + 7, y0 + 1, rz + 1, AIR)
                    # corrugation
                    self.put(x + 7, y0 + 1, rz + 1, B("iron_trapdoor", direction=0, open_bit=1) if not (s == 0 and opened) else AIR)
                x += 8 + rng.choice([3, 3, 4])
        # gantry crane spanning the yard
        gx1, gx2 = x1 + 2, x2 - 2
        gz = (z1 + z2) // 2 - 1
        for gx in (gx1, gx2):
            for o in (-6, 6):
                self.box(gx, Y + 1, gz + o, gx, Y + 16, gz + o, B("yellow_concrete"))
            self.box(gx, Y + 16, gz - 6, gx, Y + 17, gz + 6, B("yellow_concrete"))
        self.box(gx1, Y + 17, gz - 1, gx2, Y + 17, gz + 1, B("yellow_concrete"))
        self.box(gx1, Y + 18, gz - 1, gx2, Y + 18, gz - 1, B("iron_bars"))
        self.box(gx1, Y + 18, gz + 1, gx2, Y + 18, gz + 1, B("iron_bars"))
        hx = (gx1 + gx2) // 2
        self.box(hx - 1, Y + 16, gz - 1, hx + 1, Y + 16, gz + 1, B("black_concrete"))
        for y in range(Y + 9, Y + 16):
            self.put(hx, y, gz, B("chain"))
        self.put(hx, Y + 8, gz, B("anvil", cardinal="north"))
        for y in range(Y + 1, Y + 17):
            self.put(gx1 + 1, y, gz + 6, B("ladder", facing_direction=5))
        self.put(gx1 + 1, Y + 17, gz + 6, AIR)
        for (gx, o) in ((gx1, -6), (gx2, 6)):
            self.put(gx, Y + 18, gz + o, B("sea_lantern"))
        self.pois["yard"] = self.w3((x1 + x2) // 2, Y + 1, (z1 + z2) // 2)

    def offices(self, x1, z1, x2, z2):
        a = self.a
        self.reserved[(self.DX >= x1 - 2) & (self.DX <= x2 + 3) & (self.DZ >= z1 - 1) & (self.DZ <= z2 + 1)] = True
        f1 = Y + 5
        self.box(x1, Y + 1, z1, x2, Y + 10, z2, B("smooth_stone"))
        self.box(x1 + 1, Y + 1, z1 + 1, x2 - 1, Y + 4, z2 - 1, AIR)
        self.box(x1 + 1, f1 + 1, z1 + 1, x2 - 1, Y + 9, z2 - 1, AIR)
        self.box(x1, Y + 11, z1, x2, Y + 11, z2, B("smooth_stone_slab"))
        for y in (Y + 2, Y + 3, f1 + 2, f1 + 3):
            for x in range(x1 + 1, x2, 2):
                for z in (z1, z2):
                    self.put(x, y, z, B("light_blue_stained_glass_pane"))
            for z in range(z1 + 1, z2, 2):
                self.put(x1, y, z, B("light_blue_stained_glass_pane"))
        # doors (east side) and internal stairs
        for z in (z1 + 4, z2 - 5):
            self.box(x2, Y + 1, z, x2, Y + 3, z + 1, AIR)
        for i in range(5):
            self.put(x1 + 2 + i, Y + 1 + i, z2 - 2, stair("stone_brick_stairs", "east"))
            self.put(x1 + 2 + i, f1, z2 - 2, AIR)
        for i in range(5):
            self.put(x1 + 2 + i, f1, z2 - 2, AIR)
        self.put(x1 + 7, f1, z2 - 2, B("smooth_stone"))
        # desks
        for z in range(z1 + 3, z2 - 4, 4):
            for x in (x1 + 4, x1 + 10):
                for y0 in (Y + 1, f1 + 1):
                    self.put(x, y0, z, B("dark_oak_slab", half="top"))
                    self.put(x + 1, y0, z, B("dark_oak_slab", half="top"))
                    self.put(x, y0, z + 1, stair("dark_oak_stairs", "south"))
        for x in range(x1 + 3, x2, 5):
            for z in range(z1 + 3, z2, 6):
                self.put(x, Y + 4, z, B("sea_lantern"))
                self.put(x, Y + 9, z, B("sea_lantern"))
        # external stair to the roof terrace (east face)
        for i in range(11):
            self.put(x2 + 1, Y + 1 + i, z1 + 1 + i, stair("polished_andesite_stairs", "south"))
            self.put(x2 + 2, Y + 1 + i, z1 + 1 + i, stair("polished_andesite_stairs", "south"))
            for y in range(Y + 1, Y + 1 + i):
                self.put(x2 + 1, y, z1 + 1 + i, B("iron_bars") if (y - Y) % 3 == 0 else AIR)
        self.box(x2 + 1, Y + 11, z1 + 12, x2 + 2, Y + 11, z1 + 13, B("smooth_stone_slab", half="top"))
        for x in range(x1, x2 + 1):
            for z in (z1, z2):
                self.put(x, Y + 12, z, B("iron_bars"))
        for z in range(z1, z2 + 1):
            self.put(x1, Y + 12, z, B("iron_bars"))
            if not (z1 + 11 <= z <= z1 + 14):
                self.put(x2, Y + 12, z, B("iron_bars"))
        self.put(x1 + 4, Y + 12, z1 + 4, B("lantern"))
        wall_sign(a, self.cx + x2 + 1, Y + 4, self.cz + z1 + 3, 5, "§l§7관리동\n§r§8OFFICE", kind="wall_sign")
        self.pois["office"] = self.w3((x1 + x2) // 2, Y + 1, (z1 + z2) // 2)

    def control_plaza(self):
        a = self.a
        # water tower NW of centre
        tx, tz = -12, -14
        for (ox, oz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            self.box(tx + ox, Y + 1, tz + oz, tx + ox, Y + 12, tz + oz, B("iron_block"))
        for y in range(Y + 13, Y + 19):
            disk(a, self.cx + tx, y, self.cz + tz, 4.5, B("cyan_terracotta") if y < Y + 18 else B("light_gray_concrete"))
        disk(a, self.cx + tx, Y + 12, self.cz + tz, 4.5, B("iron_block"))
        disk(a, self.cx + tx, Y + 13, self.cz + tz, 5.6, B("smooth_stone_slab"))
        for y in range(Y + 1, Y + 13):
            self.put(tx + 4, y, tz + 3, B("ladder", facing_direction=5))
        self.put(tx + 4, Y + 13, tz + 3, B("ladder", facing_direction=5))
        for xx in range(tx - 6, tx + 7):
            for zz in range(tz - 6, tz + 7):
                d = math.sqrt((xx - tx) ** 2 + (zz - tz) ** 2)
                if 5.0 < d <= 5.8 and (xx + zz) % 2 == 0 and not (xx == tx + 4 or xx == tx + 5):
                    self.put(xx, Y + 14, zz, B("iron_bars"))
        self.put(tx, Y + 19, tz, B("lightning_rod", facing_direction=1))
        self.reserved[(self.DX - tx) ** 2 + (self.DZ - tz) ** 2 <= 49] = True
        # control tower SE of centre
        cx, cz = 12, 14
        self.box(cx - 2, Y + 1, cz - 2, cx + 2, Y + 14, cz + 2, B("gray_concrete"))
        self.box(cx - 1, Y + 1, cz - 1, cx + 1, Y + 13, cz + 1, AIR)
        self.box(cx - 3, Y + 11, cz - 3, cx + 3, Y + 14, cz + 3, B("glass"))
        self.box(cx - 2, Y + 11, cz - 2, cx + 2, Y + 13, cz + 2, AIR)
        self.box(cx - 3, Y + 10, cz - 3, cx + 3, Y + 10, cz + 3, B("smooth_stone"))
        self.box(cx - 3, Y + 15, cz - 3, cx + 3, Y + 15, cz + 3, B("smooth_stone_slab"))
        self.put(cx, Y + 16, cz, B("copper_bulb", lit=1))
        self.box(cx, Y + 1, cz - 2, cx, Y + 3, cz - 2, AIR)
        for y in range(Y + 1, Y + 11):
            self.put(cx + 1, y, cz + 1, B("ladder", facing_direction=4))
        self.put(cx + 1, Y + 10, cz + 1, B("ladder", facing_direction=4))
        self.put(cx, Y + 13, cz, B("lantern", hanging=1))
        self.reserved[(np.abs(self.DX - cx) <= 4) & (np.abs(self.DZ - cz) <= 4)] = True
        standing_sign(a, self.cx + 4, Y + 1, self.cz + 4, 6, "§l§e폐공장 단지\n§r§7FACTORY ZONE\n§c출입 주의", kind="standing_sign")

    def truck(self, x, z, along_x, color):
        """Box truck: cab + cargo box, wheels."""
        L = 8
        for t in range(L):
            for o in (0, 1, 2):
                dx, dz = (x + t, z + o) if along_x else (x + o, z + t)
                if t < 2:      # cab
                    self.put(dx, Y + 1, dz, B("black_concrete") if o in (0, 2) and t == 1 else B(color))
                    self.put(dx, Y + 2, dz, B("light_blue_stained_glass") if t == 0 else B(color))
                else:
                    for y in (Y + 1, Y + 2, Y + 3):
                        self.put(dx, y, dz, B("white_concrete") if y > Y + 1 else (B("black_concrete") if t in (3, 6) and o != 1 else B("gray_concrete")))

    def loading_dock(self):
        x1, x2, z1, z2 = 22, 62, -16, 12
        self.reserved[(self.DX >= x1) & (self.DX <= x2) & (self.DZ >= z1) & (self.DZ <= z2)] = True
        # dock platform (1 high) with ramps
        self.box(48, Y + 1, z1, 60, Y + 1, z2, B("smooth_stone"))
        for z in range(z1, z2 + 1):
            self.put(47, Y + 1, z, slab("smooth_stone_slab"))
        for z in range(z1, z2 + 1, 4):
            self.put(48, Y + 2, z, B("yellow_concrete"))
        # parked trucks backed to the dock
        colors = ["red_concrete", "blue_concrete", "orange_concrete", "green_concrete"]
        for i, z in enumerate(range(z1 + 1, z2 - 2, 7)):
            self.truck(37, z, True, colors[i % 4])
        # pallet stacks on the dock
        rng = random.Random(4)
        for (x, z) in ((51, z1 + 2), (54, z1 + 9), (51, z1 + 17), (55, z2 - 3)):
            for (ox, oz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                self.put(x + ox, Y + 2, z + oz, rng.choice([B("barrel", facing_direction=1), B("hay_block"), B("spruce_planks")]))
            self.put(x, Y + 3, z, B("barrel", facing_direction=1))
        for z in range(z1, z2 + 1, 6):
            self.put(60, Y + 5, z, B("sea_lantern"))
            self.box(60, Y + 2, z, 60, Y + 4, z, B("iron_bars"))
        wall_sign(self.a, self.cx + 46, Y + 3, self.cz + z2 + 1, 3, "§l§7하역장\n§r§8LOADING DOCK", kind="wall_sign")

    def scrap_yard(self):
        rng = random.Random(8)
        x1, x2, z1, z2 = -16, 10, 34, 62
        self.reserved[(self.DX >= x1) & (self.DX <= x2) & (self.DZ >= z1) & (self.DZ <= z2)] = True
        scrap = [B("iron_block"), B("raw_iron_block"), B("copper_block"), B("exposed_copper"), B("weathered_copper"),
                 B("anvil", cardinal="north"), B("observer", mfacing="up"), B("piston", facing_direction=1),
                 B("hopper", facing_direction=0), B("iron_trapdoor", direction=1), B("rail", rail_direction=0)]
        for (cx_, cz_, r) in ((-8, 44, 3.5), (4, 52, 3.0), (-6, 57, 2.5)):
            for dx in range(-4, 5):
                for dz in range(-4, 5):
                    d = math.hypot(dx, dz)
                    h = int(max(0, r - d) * 1.1)
                    for y in range(Y + 1, Y + 1 + h):
                        self.put(cx_ + dx, y, cz_ + dz, rng.choice(scrap))
        # scaffolding towers (climbable)
        for (x, z, h) in ((6, 38, 9), (-14, 50, 7)):
            for y in range(Y + 1, Y + 1 + h):
                for (ox, oz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    self.put(x + ox, y, z + oz, B("scaffolding", stability=0))
            self.put(x, Y + 1 + h, z, B("lantern"))
        # chain-link fence around (iron bars) with gaps
        for x in range(x1, x2 + 1):
            for z in (z1,):
                if (x - x1) % 9 not in (4, 5, 6):
                    self.put(x, Y + 1, z, B("iron_bars"))
                    self.put(x, Y + 2, z, B("iron_bars"))
        self.put(x1 + 2, Y + 1, z1 - 1, B("andesite_wall"))
        self.put(x1 + 2, Y + 2, z1 - 1, B("andesite_wall"))
        self.put(x1 + 2, Y + 3, z1 - 1, B("lantern"))

    def substation(self):
        x1, x2, z1, z2 = 10, 24, -64, -46
        self.reserved[(self.DX >= x1 - 1) & (self.DX <= x2 + 1) & (self.DZ >= z1 - 1) & (self.DZ <= z2 + 1)] = True
        self.box(x1, Y + 1, z1, x1 + 6, Y + 6, z1 + 8, B("brick_block"))
        self.box(x1 + 1, Y + 1, z1 + 1, x1 + 5, Y + 5, z1 + 7, AIR)
        self.box(x1 + 6, Y + 1, z1 + 3, x1 + 6, Y + 3, z1 + 4, AIR)
        self.box(x1, Y + 7, z1, x1 + 6, Y + 7, z1 + 8, B("smooth_stone_slab"))
        self.put(x1 + 3, Y + 5, z1 + 4, B("copper_bulb", lit=1))
        # transformers
        for (x, z) in ((x1 + 10, z1 + 2), (x1 + 10, z1 + 8), (x1 + 13, z1 + 5)):
            self.box(x, Y + 1, z, x + 1, Y + 3, z + 1, B("iron_block"))
            self.put(x, Y + 4, z, B("lightning_rod", facing_direction=1))
            self.put(x + 1, Y + 4, z + 1, B("lightning_rod", facing_direction=1))
        # fence
        for x in range(x1 + 8, x2 + 1):
            for z in (z1, z2):
                self.put(x, Y + 1, z, B("iron_bars"))
                self.put(x, Y + 2, z, B("iron_bars"))
        for z in range(z1, z2 + 1):
            if not (z1 + 7 <= z <= z1 + 9):
                self.put(x2, Y + 1, z, B("iron_bars"))
                self.put(x2, Y + 2, z, B("iron_bars"))
        self.put(x2, Y + 3, z1, B("sea_lantern"))
        self.put(x2, Y + 3, z2, B("sea_lantern"))

    def pipes(self):
        a = self.a
        rng = random.Random(5)
        mats = [B("copper_block"), B("exposed_copper"), B("weathered_copper"), B("cut_copper")]
        routes = [((-38, -36), (-38, 20), 7), ((-38, 20), (-24, 20), 7), ((6, -46), (28, -46), 8),
                  ((40, -22), (40, 14), 6), ((-24, 20), (-24, 40), 9), ((-46, -10), (-30, -10), 6)]
        for (p0, p1, h) in routes:
            pts = line_points((p0[0], Y + h, p0[1]), (p1[0], Y + h, p1[1]), step=0.5)
            for n, (x, y, z) in enumerate(pts):
                if self.get(x, y, z) == AIR:
                    self.put(x, y, z, rng.choice(mats))
                if n % 7 == 0:
                    for yy in range(Y + 1, y):
                        if self.get(x, yy, z) == AIR:
                            self.put(x, yy, z, B("polished_blackstone_wall") if yy < y - 1 else B("iron_block"))

    def props(self):
        a = self.a
        rng = random.Random(77)
        pal = [B("barrel", facing_direction=1), B("composter"), B("hay_block"), B("iron_block"),
               B("cauldron", cauldron_liquid="water", fill_level=0), B("spruce_planks"), B("scaffolding")]
        spots = self.scatter(60, 6, lambda x, z: self.ok_spot(x, z, margin=4))
        for (dx, dz) in spots:
            k = rng.random()
            if k < 0.35:
                # crate pile
                for (ox, oz, oy) in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)):
                    if rng.random() < 0.8:
                        self.put(dx + ox, Y + 1 + oy, dz + oz, rng.choice(pal[:4]))
            elif k < 0.55:
                # oil drums
                for (ox, oz) in ((0, 0), (1, 0), (0, 1)):
                    self.put(dx + ox, Y + 1, dz + oz, B("cauldron", cauldron_liquid="water", fill_level=0))
            elif k < 0.7:
                # pallets
                self.box(dx, Y + 1, dz, dx + 1, Y + 1, dz + 1, B("spruce_slab"))
            elif k < 0.8:
                # puddle (1 deep)
                for (ox, oz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    self.put(dx + ox, Y, dz + oz, B("water"))
            elif k < 0.9:
                # stack of iron/copper
                self.put(dx, Y + 1, dz, B("iron_block"))
                self.put(dx + 1, Y + 1, dz, B("raw_copper_block"))
            else:
                # traffic barrier
                for t in range(3):
                    self.put(dx + t, Y + 1, dz, B("andesite_wall") if t % 2 else B("yellow_concrete"))
        # rail track along the south road
        for x in range(-60, 60):
            if self.get(x, Y + 1, 30) == AIR and not self.reserved[x + self.cx - self.a.x0, 30 + self.cz - self.a.z0]:
                self.put(x, Y + 1, 30, B("rail", rail_direction=1))

    def street_lights(self):
        a = self.a
        for t in range(-64, 65, 12):
            for (dx, dz) in ((t, 5), (5, t), (t, -5), (-5, t)):
                if abs(dx) < 6 and abs(dz) < 6:
                    continue
                i, k = dx + self.cx - self.a.x0, dz + self.cz - self.a.z0
                if self.wall[i, k] or self.reserved[i, k] or self.get(dx, Y + 1, dz) != AIR:
                    continue
                self.box(dx, Y + 1, dz, dx, Y + 5, dz, B("andesite_wall"))
                self.put(dx, Y + 6, dz, B("sea_lantern"))
                self.put(dx, Y + 7, dz, B("smooth_stone_slab"))
