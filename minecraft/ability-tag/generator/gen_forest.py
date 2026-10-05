"""Map 1 - Forest ("세계수의 숲"): rolling woodland around a giant hollow world tree."""
import math
import random

import numpy as np

from mcw import B, AIR, simple_be, sign_be
from gen_common import (fbm, clamp_gradient, smoothstep, leaf_blob, leaves_of, log_of, branch, oak_tree,
                        birch_tree, spruce_tree, dark_oak_tree, big_oak, bush, boulder, lamp_post, stair, slab,
                        tall_plant, FLOWERS, TALL_FLOWERS, disk, ring, line_points, axis_of, wall_sign,
                        standing_sign, hanging_lamp)
from gen_mapbase import MapBase, catmull, bridge, SIZE

WL = 62


class Forest(MapBase):
    def __init__(self, cx, cz):
        super().__init__("forest", cx, cz, seed=1101, biome=4)

    # ------------------------------------------------------------------
    def build(self):
        self.terrain()
        self.paint()
        self.world_tree()
        self.satellites()
        self.watchtower(42, -40)
        self.cabin(-48, -8)
        self.campsite(38, 40)
        self.ruins(-42, -44)
        self.pond_details()
        self.stream_bridges()
        self.trees()
        self.cliff_top_trees()
        self.undergrowth()
        self.lamps()
        self.waterfall_feature()
        self.barrier()
        self.a.fix_walls()
        self.spawns = [self.w(11, 0), self.w(-11, 0), self.w(0, 12)]
        self.spawns = [(x, self.gy(x, z) + 1, z) for (x, z) in self.spawns]
        return self.a

    # ------------------------------------------------------------------
    def terrain(self):
        n = fbm(SIZE, SIZE, 44, 4, self.seed)
        n2 = fbm(SIZE, SIZE, 14, 2, self.seed + 5)
        h = self.H0 + np.round((n - 0.5) * 13 + (n2 - 0.5) * 2).astype(np.int32)
        inside = self.D < self.R + 2
        self.H = np.where(inside, h, self.H0 + 2)
        # gentle bowl towards the centre so the world tree sits proud
        r = np.sqrt(self.DX ** 2 + self.DZ ** 2)
        self.H = self.H + np.round(1.5 * (1 - smoothstep(0, 40, r))).astype(np.int32)
        # stream + pond
        self.stream_pts = catmull([(16, -84), (24, -60), (30, -36), (27, -14), (29, 6), (18, 25), (-4, 33),
                                   (-22, 38), (-34, 41)])
        dist = self.carve_river(self.stream_pts, None, None, WL)
        self.apply_water_body(dist, 2.3, WL, max_depth=2, bank=5)
        pd = np.sqrt(((self.DX + 36) / 1.25) ** 2 + (self.DZ - 42) ** 2)
        self.apply_water_body(pd, 9.5, WL, max_depth=3, bank=6)
        self.water_dist = np.minimum(dist, pd)
        # structure pads
        self.wt_h = self.flatten(0, 0, 10, blend=5)
        self.flatten(42, -40, 7)
        self.flatten(-48, -8, 8, square=True)
        self.flatten(38, 40, 10)
        self.flatten(-42, -44, 10)
        for ang in self.sat_angles():
            self.flatten(round(math.cos(ang) * 25), round(math.sin(ang) * 25), 4)
        self.H = clamp_gradient(self.H, self.D < self.R + 1, 1)
        self.H = np.where(self.water > 0, np.minimum(self.H, WL - 1), self.H)
        # cliffs
        self.make_cliffs(base_jump=10, top=26, width=18, amp=7)
        # materials
        nm = fbm(SIZE, SIZE, 9, 2, self.seed + 77)
        nm2 = fbm(SIZE, SIZE, 13, 2, self.seed + 78)
        self.top[:] = B("grass_block")
        self.top[(nm > 0.68) & (self.DZ < -10)] = B("podzol")
        self.top[(nm2 > 0.72)] = B("coarse_dirt")
        self.top[(self.water_dist < 5.5) & (nm > 0.45)] = B("moss_block")
        self.top[self.water > 0] = B("gravel")
        self.top[(self.water > 0) & (nm2 > 0.55)] = B("clay")
        self.sub[self.water > 0] = B("gravel")

        stone_set = [B("stone"), B("andesite"), B("cobblestone"), B("stone"), B("mossy_cobblestone"),
                     B("andesite"), B("tuff"), B("stone")]
        off = (fbm(SIZE, SIZE, 12, 2, self.seed + 91) * 9).astype(np.int32)
        speck = fbm(SIZE, SIZE, 3, 1, self.seed + 92)
        mossy = fbm(SIZE, SIZE, 7, 2, self.seed + 93)

        def strata(y):
            idx = ((y + off) // 3) % len(stone_set)
            arr = np.array(stone_set)[idx]
            arr = np.where(speck > 0.8, B("mossy_cobblestone"), arr)
            arr = np.where((mossy > 0.7) & (y > self.H0 + 6), B("moss_block"), arr)
            arr = np.where(y >= self.H - 1, np.where(y == self.H, B("grass_block"), B("dirt")), arr)
            return arr
        self.strata = strata
        self.deep[:] = B("stone")

    def sat_angles(self):
        return [math.radians(a) for a in (35, 155, 270)]

    # ------------------------------------------------------------------
    def world_tree(self):
        a = self.a
        rng = random.Random(4242)
        cx, cz = self.w(0, 0)
        h = self.wt_h
        self.reserved[(self.DX ** 2 + self.DZ ** 2) <= 14 ** 2] = True
        bark = B("dark_oak_log", axis="y")
        wood = B("dark_oak_wood", axis="y")
        H_T = 27
        deck_y = h + 14
        up_y = h + 21
        for y in range(h - 1, h + H_T + 1):
            k = y - h
            r = 4.7 - k / H_T * 1.7
            if k <= 3:
                r += (3 - k) * 0.6
            for x in range(cx - 8, cx + 9):
                for z in range(cz - 8, cz + 9):
                    d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                    nr = r + 0.45 * math.sin(math.atan2(z - cz, x - cx) * 5 + k * 0.3)
                    if d <= nr:
                        inner = nr - 1.7
                        if d > inner or y > up_y + 1 or y < h + 1:
                            a.set(x, y, z, wood if k <= 3 else bark)
                        else:
                            a.set(x, y, z, AIR)
        # roots spreading over the ground
        for i in range(10):
            ang = i * 2 * math.pi / 10 + rng.uniform(-0.2, 0.2)
            L = rng.uniform(6, 9)
            for t in np.linspace(3.5, L, 14):
                x = cx + round(math.cos(ang) * t)
                z = cz + round(math.sin(ang) * t)
                y = self.gy(x, z) + (1 if t < L - 2 else 0)
                a.set(x, y, z, wood)
        # floor inside the trunk
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                if (x - cx) ** 2 + (z - cz) ** 2 <= 7 and a.get(x, h + 1, z) == AIR:
                    a.set(x, h, z, B("spruce_planks"))
        # doorways east and west (3 high, 2 wide)
        for sx in (1, -1):
            for t in range(2, 8):
                for o in (0, 1):
                    for y in range(h + 1, h + 4):
                        a.set(cx + sx * t, y, cz - o, AIR)
            for o in (-1, 1):
                a.set(cx + sx * 4, h + 3, cz + o, AIR)
        # lantern lights inside the trunk
        for y in range(h + 3, up_y, 5):
            for (ox, oz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                if a.get(cx + ox, y, cz + oz) == AIR and a.get(cx + ox, y + 1, cz + oz) != AIR:
                    a.set(cx + ox, y, cz + oz, B("lantern", hanging=1))
                    break
        # branches + canopy
        tips = []
        for i in range(9):
            ang = i * 2 * math.pi / 9 + rng.uniform(-0.15, 0.15)
            sy = h + rng.randint(17, 22)
            L = rng.uniform(10, 13)
            ex, ez = cx + math.cos(ang) * L, cz + math.sin(ang) * L
            ey = sy + rng.randint(3, 5)
            for q in line_points((cx + math.cos(ang) * 3.6, sy, cz + math.sin(ang) * 3.6), (ex, ey, ez)):
                ax = axis_of((cx, sy, cz), (ex, ey, ez))
                a.set(q[0], q[1], q[2], B("dark_oak_log", axis=ax))
                if math.dist((q[0], q[2]), (cx, cz)) < 6:
                    a.set(q[0], q[1] + 1, q[2], B("dark_oak_log", axis=ax))
            tips.append((ex, ey, ez))
        leafA = leaves_of("oak")
        leafB = B("azalea_leaves", persistent_bit=1)
        leafC = B("azalea_leaves_flowered", persistent_bit=1)
        glow = B("shroomlight")
        for (ex, ey, ez) in tips:
            leaf_blob(a, ex, ey + 1, ez, rng.uniform(4.6, 5.8), leafA, rng, flat=0.55, extra=glow, extra_chance=0.02)
        leaf_blob(a, cx, h + H_T + 2, cz, 8.5, leafA, rng, flat=0.5, extra=glow, extra_chance=0.015)
        for (ex, ey, ez) in tips[::2]:
            leaf_blob(a, (ex + cx) / 2, ey + 3, (ez + cz) / 2, 4.5, leafC, rng, flat=0.5)
        for (ex, ey, ez) in tips[1::2]:
            leaf_blob(a, (ex * 2 + cx) / 3, ey + 2, (ez * 2 + cz) / 3, 3.8, leafB, rng, flat=0.6)
        # hanging lanterns under the canopy
        for (ex, ey, ez) in tips:
            hx, hz = round(ex * 0.8 + cx * 0.2), round(ez * 0.8 + cz * 0.2)
            yy = int(ey)
            while yy > h + 8 and a.get(hx, yy, hz) != AIR:
                yy -= 1
            if yy > deck_y + 4:
                for d in range(3):
                    if a.get(hx, yy - d, hz) == AIR:
                        a.set(hx, yy - d, hz, B("chain"))
                a.set(hx, yy - 3, hz, B("lantern", hanging=1))
        # clear the hollow interior (branches/leaves may have intruded), then build the spiral
        for y in range(h + 1, up_y + 3):
            k = y - h
            inner = 4.7 - k / H_T * 1.7 - 1.9
            for x in range(cx - 4, cx + 5):
                for z in range(cz - 4, cz + 5):
                    if math.sqrt((x - cx) ** 2 + (z - cz) ** 2) <= max(inner, 1.5):
                        a.set(x, y, z, AIR)
        # central column + spiral stairs
        for y in range(h + 1, up_y + 1):
            a.set(cx, y, cz, B("stripped_dark_oak_log", axis="y"))
        ringc = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
        dirs = []
        for i in range(8):
            (x0, z0), (x1, z1) = ringc[i], ringc[(i + 1) % 8]
            ddx, ddz = x1 - x0, z1 - z0
            dirs.append("east" if ddx > 0 else "west" if ddx < 0 else "south" if ddz > 0 else "north")
        steps = up_y - h - 1
        exits = {}
        for k in range(steps):
            i = k % 8
            ox, oz = ringc[i]
            y = h + 1 + k
            a.set(cx + ox, y, cz + oz, stair("spruce_stairs", dirs[i]))
            exits[y + 1] = (ox, oz)
        # ring deck around the trunk
        plank = B("spruce_planks")
        rail = B("spruce_fence")
        self.deck_ring = []
        for x in range(cx - 10, cx + 11):
            for z in range(cz - 10, cz + 11):
                d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                if 3.6 < d <= 9.2:
                    if a.get(x, deck_y, z) in (AIR,) or a.get(x, deck_y, z) == leafA or a.get(x, deck_y, z) in (leafB, leafC, glow):
                        a.set(x, deck_y, z, plank)
                    for y in range(deck_y + 1, deck_y + 4):
                        if a.get(x, y, z) in (leafA, leafB, leafC, glow):
                            a.set(x, y, z, AIR)
                if 8.6 < d <= 9.6:
                    ang = math.degrees(math.atan2(z - cz, x - cx)) % 360
                    gap = any(abs(((ang - g + 180) % 360) - 180) < 9 for g in (35, 155, 270, 95, 215, 330))
                    if not gap:
                        a.set(x, deck_y + 1, z, rail)
        for k, (ox, oz) in enumerate(((7, 0), (-7, 0), (0, 7), (0, -7))):
            a.set(cx + ox, deck_y + 1, cz + oz, rail)
            a.set(cx + ox, deck_y + 2, cz + oz, B("lantern"))
        # exits from the spiral onto the deck and the upper lookout
        for ty in (deck_y + 1, up_y + 1):
            ox, oz = exits.get(ty, exits.get(ty - 1, (1, 0)))
            sx_, sz_ = (int(math.copysign(1, ox)), 0) if ox != 0 else (0, int(math.copysign(1, oz)))
            for t in range(1, 7):
                x, z = cx + ox + sx_ * t, cz + oz + sz_ * t
                for y in (ty, ty + 1):
                    a.set(x, y, z, AIR)
                if a.get(x, ty - 1, z) == AIR or t <= 4:
                    a.set(x, ty - 1, z, plank)
        # upper lookout platform in the canopy
        for x in range(cx - 7, cx + 8):
            for z in range(cz - 7, cz + 8):
                d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                if 2.5 < d <= 6.5:
                    a.set(x, up_y, z, plank)
                    for y in range(up_y + 1, up_y + 4):
                        if a.get(x, y, z) in (leafA, leafB, leafC, glow, B("dark_oak_log", axis="x"), B("dark_oak_log", axis="z")):
                            a.set(x, y, z, AIR)
                if 6.0 < d <= 7.0:
                    a.set(x, up_y + 1, z, rail)
        a.set(cx - 6, up_y + 1, cz, B("lantern"))
        self.deck_y = deck_y
        self.pois["world_tree"] = (cx, h + 1, cz)
        # signs at the doors
        for sx in (1, -1):
            x = cx + sx * 8
            a.set(x, self.gy(x, cz + 2) + 1, cz + 2, B("spruce_fence"))
            a.set(x, self.gy(x, cz + 2) + 2, cz + 2, B("lantern"))
            a.set(x, self.gy(x, cz - 2) + 1, cz - 2, B("spruce_fence"))
            a.set(x, self.gy(x, cz - 2) + 2, cz - 2, B("lantern"))

    def satellites(self):
        a = self.a
        rng = random.Random(99)
        cx, cz = self.w(0, 0)
        for ang in self.sat_angles():
            sx, sz = self.w(round(math.cos(ang) * 25), round(math.sin(ang) * 25))
            g = self.gy(sx, sz)
            dk = g + 11
            self.reserved[(self.DX - (sx - self.cx)) ** 2 + (self.DZ - (sz - self.cz)) ** 2 <= 36] = True
            lb = log_of("oak")
            for dx in (0, 1):
                for dz in (0, 1):
                    for y in range(g + 1, dk + 7):
                        a.set(sx + dx, y, sz + dz, lb)
            for (dx, dz) in ((-1, 0), (2, 1), (0, 2), (1, -1)):
                a.set(sx + dx, g + 1, sz + dz, B("oak_wood", axis="y"))
            for k in range(4):
                an = k * math.pi / 2 + 0.6
                branch(a, (sx, dk + 4, sz), (round(sx + math.cos(an) * 5), dk + 7, round(sz + math.sin(an) * 5)), "oak")
                leaf_blob(a, sx + math.cos(an) * 5, dk + 8, sz + math.sin(an) * 5, 3.6, leaves_of("oak"), rng, flat=0.6,
                          extra=B("shroomlight"), extra_chance=0.02)
            leaf_blob(a, sx + 0.5, dk + 10, sz + 0.5, 5, leaves_of("oak"), rng, flat=0.55)
            # deck
            for x in range(sx - 5, sx + 7):
                for z in range(sz - 5, sz + 7):
                    d = math.sqrt((x - sx - 0.5) ** 2 + (z - sz - 0.5) ** 2)
                    if 1.4 < d <= 4.8:
                        a.set(x, dk, z, B("spruce_planks"))
                        for y in range(dk + 1, dk + 4):
                            if a.get(x, y, z) != lb:
                                a.set(x, y, z, AIR)
                    if 4.3 < d <= 5.3 and (x + z) % 2 == 0:
                        a.set(x, dk + 1, z, B("spruce_fence"))
            # ladder on the trunk side facing the world tree
            lx = sx - 1 if cx < sx else sx + 2
            fd = 4 if cx < sx else 5
            for y in range(g + 1, dk + 2):
                a.set(lx, y, sz, B("ladder", facing_direction=fd))
            a.set(lx, dk + 2, sz, AIR)
            a.set(sx - 1 if cx >= sx else sx + 2, dk + 1, sz + 1, B("lantern"))
            # bridge to the world tree deck
            ux, uz = math.cos(ang), math.sin(ang)
            p0 = (round(cx + ux * 9.5), round(cz + uz * 9.5))
            p1 = (round(cx + ux * 20.5), round(cz + uz * 20.5))
            bridge(a, p0, p1, self.deck_y + 1, dk + 1, B("spruce_planks"), slab("spruce_slab"),
                   B("spruce_fence"), lamp=B("lantern"), width=3, lamp_every=6)

    # ------------------------------------------------------------------
    def watchtower(self, dx, dz):
        a = self.a
        rng = random.Random(7)
        cx, cz = self.w(dx, dz)
        g = self.gy(cx, cz)
        self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 64] = True
        mats = [B("stone_bricks"), B("stone_bricks"), B("mossy_stone_bricks"), B("cracked_stone_bricks")]
        top = g + 16
        for y in range(g - 1, top + 3):
            for x in range(cx - 5, cx + 6):
                for z in range(cz - 5, cz + 6):
                    d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                    if 3.5 < d <= 4.6:
                        if y <= top or (y in (top + 1, top + 2) and int(math.degrees(math.atan2(z - cz, x - cx)) // 30) % 2 == 0):
                            a.set(x, y, z, rng.choice(mats))
                    elif d <= 3.5 and y < top:
                        a.set(x, y, z, AIR if y > g else B("cobblestone"))
        # top floor
        for x in range(cx - 4, cx + 5):
            for z in range(cz - 4, cz + 5):
                if math.sqrt((x - cx) ** 2 + (z - cz) ** 2) <= 3.6:
                    a.set(x, top, z, B("spruce_planks"))
        # spiral stairs: square ring (4-connected) around the centre
        ring_cells = []
        for t in range(-2, 2):
            ring_cells.append((2, t))
        for t in range(2, -2, -1):
            ring_cells.append((t, 2))
        for t in range(2, -2, -1):
            ring_cells.append((-2, t))
        for t in range(-2, 2):
            ring_cells.append((t, -2))
        start = ring_cells.index((0, 2))
        n = len(ring_cells)
        y = g + 1
        k = 0
        while y < top:
            ox, oz = ring_cells[(start + k) % n]
            nx_, nz_ = ring_cells[(start + k + 1) % n]
            ddx, ddz = nx_ - ox, nz_ - oz
            d = ("east" if ddx > 0 else "west") if ddx else ("south" if ddz > 0 else "north")
            a.set(cx + ox, y, cz + oz, stair("stone_brick_stairs", d))
            if y >= top - 4:
                a.set(cx + ox, top, cz + oz, AIR)
            k += 1
            y += 1
        # door to the south
        for y in (g + 1, g + 2, g + 3):
            for o in (-1, 0):
                for t in (3, 4, 5):
                    a.set(cx + o, y, cz + t, AIR)
        # windows
        for (wy, ang) in ((g + 6, 0), (g + 9, 120), (g + 12, 240)):
            x = cx + round(math.cos(math.radians(ang)) * 4)
            z = cz + round(math.sin(math.radians(ang)) * 4)
            a.set(x, wy, z, AIR)
            a.set(x, wy + 1, z, AIR)
        # lanterns on top
        for (ox, oz) in ((-3, 0), (0, -3), (0, 3), (-2, -2)):
            a.set(cx + ox, top + 1, cz + oz, B("lantern"))
        if a.get(cx, top - 1, cz) == AIR:
            a.set(cx, top - 1, cz, B("lantern", hanging=1))
        # vines on the north face (climbable)
        for x in range(cx - 2, cx + 3):
            z = cz - 5
            for y in range(g + 1, g + rng.randint(6, 11)):
                if a.get(x, y, z + 1) != AIR and a.get(x, y, z) == AIR:
                    a.set(x, y, z, B("vine", vine_direction_bits=1))
        self.pois["tower"] = (cx, g + 1, cz)

    # ------------------------------------------------------------------
    def cabin(self, dx, dz):
        a = self.a
        cx, cz = self.w(dx, dz)
        g = self.gy(cx, cz)
        self.reserved[(np.abs(self.DX - dx) <= 8) & (np.abs(self.DZ - dz) <= 7)] = True
        x1, x2, z1, z2 = cx - 5, cx + 5, cz - 4, cz + 4
        log = B("spruce_log", axis="y")
        plank = B("spruce_planks")
        a.fill(x1, g, z1, x2, g, z2, B("cobblestone"))
        a.fill(x1 + 1, g, z1 + 1, x2 - 1, g, z2 - 1, B("spruce_planks"))
        a.fill(x1, g + 1, z1, x2, g + 4, z2, plank)
        a.fill(x1 + 1, g + 1, z1 + 1, x2 - 1, g + 4, z2 - 1, AIR)
        for x in (x1, x2):
            for z in (z1, z2):
                a.fill(x, g + 1, z, x, g + 4, z, log)
        a.fill(x1, g + 4, z1, x2, g + 4, z1, B("stripped_spruce_log", axis="x"))
        a.fill(x1, g + 4, z2, x2, g + 4, z2, B("stripped_spruce_log", axis="x"))
        # gable roof along x
        for i in range(0, 6):
            y = g + 5 + i
            for x in range(x1 - 1, x2 + 2):
                za, zb = z1 - 1 + i, z2 + 1 - i
                if za > zb:
                    break
                if za == zb:
                    a.set(x, y, za, B("spruce_planks"))
                    continue
                a.set(x, y, za, stair("spruce_stairs", "south"))
                a.set(x, y, zb, stair("spruce_stairs", "north"))
                if x in (x1, x2):
                    a.fill(x, y, za + 1, x, y, zb - 1, plank)
        # windows
        for x in (cx - 3, cx + 3):
            for z in (z1, z2):
                a.set(x, g + 2, z, B("glass_pane"))
                a.set(x, g + 3, z, B("glass_pane"))
        # doors: east 2-wide open doorway with open doors, west back door
        for z in (cz, cz - 1):
            a.set(x2, g + 1, z, AIR)
            a.set(x2, g + 2, z, AIR)
            a.set(x2, g + 3, z, AIR)
        a.set(x2 + 1, g, cz, B("spruce_planks"))
        a.set(x2 + 1, g, cz - 1, B("spruce_planks"))
        a.set(x1, g + 1, cz + 1, B("spruce_door", cardinal="west", upper_block_bit=0, open_bit=1))
        a.set(x1, g + 2, cz + 1, B("spruce_door", cardinal="west", upper_block_bit=1, open_bit=1))
        # porch posts with lanterns
        for z in (cz - 3, cz + 2):
            a.set(x2 + 1, g + 1, z, B("spruce_fence"))
            a.set(x2 + 1, g + 2, z, B("spruce_fence"))
            a.set(x2 + 1, g + 3, z, B("lantern"))
        # chimney + smoke
        a.fill(x1 + 1, g + 1, z2 - 1, x1 + 1, g + 11, z2 - 1, B("cobblestone"))
        a.set(x1 + 1, g + 12, z2 - 1, B("campfire"))
        a.add_be(simple_be("Campfire", x1 + 1, g + 12, z2 - 1))
        a.set(x1 + 1, g + 1, z2 - 1, B("lit_furnace", cardinal="east"))
        # interior
        a.set(cx, g + 1, cz + 1, B("spruce_fence"))
        a.set(cx, g + 2, cz + 1, B("wooden_pressure_plate"))
        a.set(cx - 1, g + 1, cz + 1, stair("spruce_stairs", "west"))
        a.set(cx + 1, g + 1, cz + 1, stair("spruce_stairs", "east"))
        a.set(x1 + 1, g + 1, z1 + 1, B("crafting_table"))
        a.set(x1 + 2, g + 1, z1 + 1, B("barrel", facing_direction=1))
        a.set(x1 + 3, g + 1, z1 + 1, B("bookshelf"))
        a.set(x1 + 3, g + 2, z1 + 1, B("flower_pot"))
        from mcw import flowerpot_be
        a.add_be(flowerpot_be(x1 + 3, g + 2, z1 + 1, "red_tulip"))
        a.set(cx + 2, g + 1, z1 + 1, B("bed", direction=1, head_piece_bit=0))
        a.set(cx + 1, g + 1, z1 + 1, B("bed", direction=1, head_piece_bit=1))
        import amulet_nbt as an
        a.add_be(simple_be("Bed", cx + 2, g + 1, z1 + 1, color=an.ByteTag(14)))
        a.add_be(simple_be("Bed", cx + 1, g + 1, z1 + 1, color=an.ByteTag(14)))
        a.set(cx, g + 4, cz, B("chain") if a.get(cx, g + 5, cz) != AIR else AIR)
        a.set(cx, g + 4, cz - 2, B("lantern", hanging=1))
        a.fill(cx - 2, g + 1, cz - 2, cx + 2, g + 1, cz - 2, B("red_carpet"), only_air=True)
        # woodpile + axe stump outside
        for z in range(z1, z1 + 3):
            a.set(x1 - 1, g + 1, z, B("oak_log", axis="z"))
        a.set(x1 - 1, g + 2, z1 + 1, B("oak_log", axis="z"))
        self.pois["cabin"] = (cx, g + 1, cz)

    # ------------------------------------------------------------------
    def campsite(self, dx, dz):
        a = self.a
        rng = random.Random(3)
        cx, cz = self.w(dx, dz)
        g = self.gy(cx, cz)
        self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 100] = True
        a.set(cx, g + 1, cz, B("campfire"))
        a.add_be(simple_be("Campfire", cx, g + 1, cz))
        for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            a.set(cx + ox, g, cz + oz, B("cobblestone") if (ox + oz) % 2 else B("mossy_cobblestone"))
        for (ox, oz, ax) in ((3, 0, "z"), (-3, 0, "z"), (0, 3, "x"), (0, -3, "x")):
            for t in (-1, 0, 1):
                x = cx + ox + (t if ax == "x" else 0)
                z = cz + oz + (t if ax == "z" else 0)
                a.set(x, g + 1, z, B("stripped_oak_log", axis=ax))
        cols = ["white_wool", "green_wool", "brown_wool"]
        for i, ang in enumerate((30, 150, 270)):
            r = 6.5
            tx = cx + round(math.cos(math.radians(ang)) * r)
            tz = cz + round(math.sin(math.radians(ang)) * r)
            along_x = abs(math.cos(math.radians(ang))) > abs(math.sin(math.radians(ang)))
            wool = B(cols[i])
            outward = math.cos(math.radians(ang)) if along_x else math.sin(math.radians(ang))
            back = 1 if outward > 0 else -2          # the end facing away from the campfire
            for L in range(-2, 2):
                for lvl, o in ((1, 2), (2, 1), (3, 0)):
                    for s in {-o, o}:
                        x = tx + (L if along_x else s)
                        z = tz + (s if along_x else L)
                        a.set(x, g + lvl, z, wool)
                for s in (-1, 0, 1):
                    x = tx + (L if along_x else s)
                    z = tz + (s if along_x else L)
                    a.set(x, g + 1, z, AIR)
            for (lvl, o) in ((1, 1), (1, 0), (1, -1), (2, 0)):
                x = tx + (back if along_x else o)
                z = tz + (o if along_x else back)
                a.set(x, g + lvl, z, wool)
            a.set(tx, g + 1, tz, B(cols[(i + 1) % 3].replace("wool", "carpet")))
        # crates + lantern posts
        for (ox, oz) in ((5, -4), (-5, 4)):
            a.set(cx + ox, g + 1, cz + oz, B("barrel", facing_direction=1))
            a.set(cx + ox + 1, g + 1, cz + oz, B("hay_block"))
            a.set(cx + ox, g + 2, cz + oz, B("barrel", facing_direction=1))
        for ang in (90, 210, 330):
            x = cx + round(math.cos(math.radians(ang)) * 8)
            z = cz + round(math.sin(math.radians(ang)) * 8)
            lamp_post(a, x, self.gy(x, z) + 1, z, B("oak_fence"), B("lantern"), height=2)
        self.pois["camp"] = (cx, g + 1, cz)

    # ------------------------------------------------------------------
    def ruins(self, dx, dz):
        a = self.a
        rng = random.Random(11)
        cx, cz = self.w(dx, dz)
        g = self.gy(cx, cz)
        self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 110] = True
        mats = [B("stone_bricks"), B("mossy_stone_bricks"), B("cracked_stone_bricks"), B("mossy_stone_bricks")]
        for x in range(cx - 9, cx + 10):
            for z in range(cz - 9, cz + 10):
                d = math.sqrt((x - cx) ** 2 + (z - cz) ** 2)
                if d <= 8.5 and rng.random() < 0.8:
                    a.set(x, g, z, rng.choice(mats + [B("stone_bricks")]))
        tops = []
        for i in range(8):
            ang = i * math.pi / 4
            px = cx + round(math.cos(ang) * 7)
            pz = cz + round(math.sin(ang) * 7)
            hgt = rng.choice([2, 3, 6, 6, 6, 4])
            for y in range(g + 1, g + 1 + hgt):
                a.set(px, y, pz, rng.choice(mats))
            if hgt == 6:
                a.set(px, g + 7, pz, B("chiseled_stone_bricks"))
            tops.append((px, pz, hgt))
        # arches between consecutive full-height pillars
        for i in range(8):
            p, q = tops[i], tops[(i + 1) % 8]
            if p[2] == 6 and q[2] == 6:
                for pt in line_points((p[0], g + 7, p[1]), (q[0], g + 7, q[1])):
                    a.set(pt[0], pt[1], pt[2], B("stone_brick_slab", half="top") if pt[:1] != p[:1] else B("stone_bricks"))
        # altar
        a.set(cx, g + 1, cz, B("chiseled_stone_bricks"))
        a.set(cx, g + 2, cz, B("soul_lantern"))
        for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a.set(cx + ox, g + 1, cz + oz, stair("stone_brick_stairs", {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(ox, oz)]))
        for (ox, oz) in ((2, 2), (-2, -2), (2, -2), (-2, 2)):
            a.set(cx + ox, g + 1, cz + oz, B("candle", candles=2, lit=1))
        # fallen pillar pieces
        for k in range(3):
            ang = rng.random() * 6.28
            x0 = cx + round(math.cos(ang) * 10)
            z0 = cz + round(math.sin(ang) * 10)
            ax = rng.choice(["x", "z"])
            for t in range(3):
                x = x0 + (t if ax == "x" else 0)
                z = z0 + (t if ax == "z" else 0)
                a.set(x, self.gy(x, z) + 1, z, rng.choice(mats))
        self.pois["ruins"] = (cx, g + 1, cz)

    # ------------------------------------------------------------------
    def pond_details(self):
        a = self.a
        rng = random.Random(5)
        for i in range(SIZE):
            for k in range(SIZE):
                if self.water[i, k] and not self.wall[i, k]:
                    x, z = i + self.a.x0, k + self.a.z0
                    if rng.random() < 0.05 and self.H[i, k] <= WL - 2 and abs(self.DX[i, k] + 36) < 14:
                        a.set(x, WL + 1, z, B("waterlily"))
                    if rng.random() < 0.12 and self.H[i, k] <= WL - 2:
                        a.setw(x, self.H[i, k] + 1, z, B("seagrass"))
                elif not self.wall[i, k] and self.water_dist[i, k] < 4 and self.H[i, k] == WL and rng.random() < 0.18:
                    x, z = i + self.a.x0, k + self.a.z0
                    adj = any(self.water[min(SIZE - 1, max(0, i + dx)), min(SIZE - 1, max(0, k + dz))] for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if adj and a.get(x, WL + 1, z) == AIR and not self.path[i, k]:
                        a.set(x, WL, z, B("grass_block"))
                        for y in range(WL + 1, WL + 1 + rng.randint(1, 3)):
                            a.set(x, y, z, B("reeds"))
        # little pier into the pond
        px, pz = self.w(-26, 36)
        for t in range(0, 7):
            for o in (0, 1):
                x, z = px - t, pz + o
                a.set(x, WL, z, B("spruce_planks"))
                a.set(x, WL + 1, z, AIR)
        for t in (2, 5):
            for o in (-1, 2):
                a.set(px - t, WL, pz + o, B("spruce_log", axis="y"))
                a.set(px - t, WL - 1, pz + o, B("spruce_log", axis="y"))
                a.set(px - t, WL + 1, pz + o, B("spruce_fence"))
                if t == 5:
                    a.set(px - t, WL + 2, pz + o, B("lantern"))

    def stream_bridges(self):
        a = self.a
        # three bridges across the stream at chosen sample indices
        pts = self.stream_pts
        n = len(pts)
        for f in (0.18, 0.47, 0.7):
            i = int(n * f)
            (x0, z0), (x1, z1) = pts[i], pts[min(n - 1, i + 3)]
            tx, tz = x1 - x0, z1 - z0
            L = math.hypot(tx, tz)
            nx_, nz_ = -tz / L, tx / L
            # snap the bridge direction to an axis
            if abs(nx_) >= abs(nz_):
                p0 = (round(x0) - 6, round(z0))
                p1 = (round(x0) + 6, round(z0))
            else:
                p0 = (round(x0), round(z0) - 6)
                p1 = (round(x0), round(z0) + 6)
            w0 = self.w(*p0)
            w1 = self.w(*p1)
            f0 = self.gy(*w0) + 1
            f1 = self.gy(*w1) + 1
            mid = max(f0, f1, WL + 2)
            pm = ((w0[0] + w1[0]) // 2, (w0[1] + w1[1]) // 2)
            bridge(a, w0, pm, f0, mid + 0.5, B("spruce_planks"), slab("spruce_slab"), B("spruce_fence"), lamp=None)
            bridge(a, pm, w1, mid + 0.5, f1, B("spruce_planks"), slab("spruce_slab"), B("spruce_fence"), lamp=None)
            # paths to the bridge ends
            for (px, pz) in (p0, p1):
                self.raster_path([(px, pz)], width=2.5)

    # ------------------------------------------------------------------
    def trees(self):
        a = self.a
        rng = self.rng
        # big oaks first
        big = self.scatter(40, 15, lambda x, z: self.ok_spot(x, z, margin=6) and math.hypot(x, z) > 18)
        for (dx, dz) in big:
            x, z = self.w(dx, dz)
            big_oak(a, x, self.gy(x, z) + 1, z, rng, glow=B("shroomlight"))
            self.reserved[(self.DX - dx) ** 2 + (self.DZ - dz) ** 2 <= 25] = True
        pts = self.scatter(400, 5.6, lambda x, z: self.ok_spot(x, z, margin=3) and math.hypot(x, z) > 15)
        for (dx, dz) in pts:
            x, z = self.w(dx, dz)
            y = self.gy(x, z) + 1
            r = rng.random()
            if dz < -28:
                if r < 0.6:
                    spruce_tree(a, x, y, z, rng)
                elif r < 0.85:
                    oak_tree(a, x, y, z, rng)
                else:
                    birch_tree(a, x, y, z, rng)
            elif dx < -28:
                if r < 0.45:
                    birch_tree(a, x, y, z, rng)
                elif r < 0.8:
                    oak_tree(a, x, y, z, rng)
                else:
                    dark_oak_tree(a, x, y, z, rng)
            else:
                if r < 0.55:
                    oak_tree(a, x, y, z, rng, glow=B("shroomlight") if rng.random() < 0.08 else None)
                elif r < 0.8:
                    birch_tree(a, x, y, z, rng)
                elif r < 0.9:
                    dark_oak_tree(a, x, y, z, rng)
                else:
                    spruce_tree(a, x, y, z, rng, h=rng.randint(7, 9))
            i, k = x - self.a.x0, z - self.a.z0
            self.reserved[max(0, i - 1):i + 2, max(0, k - 1):k + 2] = True

    def cliff_top_trees(self):
        a = self.a
        rng = random.Random(77)
        t = self.wall_t
        cand = np.argwhere((t > 5) & (t < 17) & (self.D < 105))
        rng.shuffle(cand_list := [tuple(c) for c in cand])
        placed = []
        for (i, k) in cand_list:
            if any((i - p) ** 2 + (k - q) ** 2 < 30 for p, q in placed[-60:]):
                continue
            if rng.random() > 0.35:
                continue
            x, z = i + self.a.x0, k + self.a.z0
            y = int(self.H[i, k]) + 1
            if rng.random() < 0.55:
                spruce_tree(a, x, y, z, rng)
            else:
                oak_tree(a, x, y, z, rng, h=rng.randint(5, 7))
            placed.append((i, k))
            if len(placed) > 420:
                break

    def undergrowth(self):
        a = self.a
        rng = random.Random(21)
        flow = fbm(SIZE, SIZE, 10, 2, self.seed + 300)
        fern = fbm(SIZE, SIZE, 16, 2, self.seed + 301)
        for i in range(SIZE):
            for k in range(SIZE):
                if self.water[i, k]:
                    continue
                x, z = i + self.a.x0, k + self.a.z0
                y = int(self.H[i, k]) + 1
                if a.get(x, y, z) != AIR or a.get(x, y - 1, z) not in (B("grass_block"), B("podzol"), B("moss_block")):
                    continue
                if self.path[i, k]:
                    continue
                r = rng.random()
                if self.wall[i, k]:
                    if r < 0.25:
                        a.set(x, y, z, B("short_grass"))
                    elif r < 0.3:
                        a.set(x, y, z, B("fern"))
                    continue
                if flow[i, k] > 0.68 and r < 0.35:
                    a.set(x, y, z, B(rng.choice(FLOWERS)))
                elif flow[i, k] > 0.74 and r < 0.4:
                    tall_plant(a, x, y, z, rng.choice(TALL_FLOWERS))
                elif fern[i, k] > 0.6 and r < 0.3:
                    if rng.random() < 0.2:
                        tall_plant(a, x, y, z, "large_fern")
                    else:
                        a.set(x, y, z, B("fern"))
                elif r < 0.22:
                    a.set(x, y, z, B("short_grass"))
                elif r < 0.25:
                    tall_plant(a, x, y, z, "tall_grass")
                elif r < 0.257 and not self.reserved[i, k]:
                    bush(a, x, y, z, rng, leaves_of("oak") if rng.random() < 0.6 else B("azalea_leaves", persistent_bit=1))
                elif r < 0.265:
                    a.set(x, y, z, B(rng.choice(["brown_mushroom", "red_mushroom"])))
                elif r < 0.268:
                    a.set(x, y, z, B("glow_lichen", multi_face_direction_bits=1))
                elif r < 0.273:
                    a.set(x, y, z, B("moss_carpet"))
        # boulders and fallen logs
        spots = self.scatter(26, 9, lambda x, z: self.ok_spot(x, z, margin=5))
        for n, (dx, dz) in enumerate(spots):
            x, z = self.w(dx, dz)
            y = self.gy(x, z)
            if n < 15:
                boulder(a, x, y + 0.6, z, rng, rng.uniform(1.4, 2.3),
                        [B("mossy_cobblestone"), B("andesite"), B("stone"), B("cobblestone"), B("moss_block")])
                a.put(x + 1, y + 1, z + 2, B("glow_lichen", multi_face_direction_bits=1))
            else:
                ax = rng.choice(["x", "z"])
                kind = rng.choice(["oak", "birch", "spruce"])
                L = rng.randint(4, 6)
                for t in range(L):
                    xx = x + (t if ax == "x" else 0)
                    zz = z + (t if ax == "z" else 0)
                    if self.ok_spot(xx - self.cx, zz - self.cz, margin=3, allow_path=False):
                        a.set(xx, self.gy(xx, zz) + 1, zz, B(kind + "_log", axis=ax))
                        if rng.random() < 0.4:
                            a.put(xx, self.gy(xx, zz) + 2, zz, B("moss_carpet") if rng.random() < 0.6 else B("red_mushroom"))

    def lamps(self):
        a = self.a
        # dirt paths from the world tree to every point of interest
        targets = [(42, -34), (-40, -8), (34, 34), (-38, -38), (-26, 37)]
        for (tx, tz) in targets:
            ang = math.atan2(tz, tx)
            start = (math.cos(ang) * 9, math.sin(ang) * 9)
            mid = ((start[0] + tx) / 2 + 6 * math.sin(ang * 3), (start[1] + tz) / 2 + 6 * math.cos(ang * 2))
            pts = catmull([start, mid, (tx, tz)], step=0.7)
            cells = self.raster_path(pts, width=2.2)
            for (dx, dz) in cells:
                x, z = self.w(dx, dz)
                y = self.gy(x, z)
                if self.water[dx + self.cx - self.a.x0, dz + self.cz - self.a.z0]:
                    continue
                b = a.get(x, y, z)
                if b in (B("grass_block"), B("podzol"), B("coarse_dirt"), B("moss_block"), B("dirt")):
                    a.set(x, y, z, B("grass_path") if self.rng.random() < 0.85 else B("coarse_dirt"))
                    if a.get(x, y + 1, z) in (B("short_grass"), B("fern"), B("moss_carpet")) or a.get(x, y + 1, z) in [B(f) for f in FLOWERS]:
                        a.set(x, y + 1, z, AIR)
            # lamp posts along the path
            for j in range(6, len(pts) - 3, 14):
                px, pz = pts[j]
                ox, oz = -math.sin(ang) * 2.6, math.cos(ang) * 2.6
                x, z = self.w(round(px + ox), round(pz + oz))
                y = self.gy(x, z) + 1
                if a.get(x, y, z) in (AIR, B("short_grass"), B("fern")) and not self.water[x - self.a.x0, z - self.a.z0]:
                    lamp_post(a, x, y, z, B("spruce_fence"), B("lantern"), height=2)

    def waterfall_feature(self):
        """Spring waterfall where the stream enters from the north cliff."""
        a = self.a
        x0, z0 = self.w(16, 0)
        # find the cliff columns north of the stream start along x = x0..x0+1
        for x in (x0, x0 + 1):
            # walk from the stream start northwards until D > R+1.7
            zs = [z for z in range(self.cz - 95, self.cz - 60) if self.R + 1.7 < self.D[x - self.a.x0, z - self.a.z0] <= self.R + 3.2]
            if not zs:
                continue
            zf = max(zs)
            top = self.H0 + 13
            for z in range(zf + 1, self.cz - 60):
                if self.D[x - self.a.x0, z - self.a.z0] > self.wall_start[x - self.a.x0, z - self.a.z0] - 0.5:
                    for y in range(WL + 1, top + 1):
                        a.set(x, y, z, AIR)
                    a.set(x, WL, z, B("mossy_cobblestone"))
            a.set(x, top, zf, B("water"))
            for y in range(WL + 1, top):
                a.set(x, y, zf, B("flowing_water", liquid_depth=8))
            a.set(x, top + 1, zf, B("mossy_cobblestone"))
            a.set(x, top, zf - 1, B("mossy_cobblestone"))
            a.set(x, WL, zf, B("mossy_cobblestone"))
