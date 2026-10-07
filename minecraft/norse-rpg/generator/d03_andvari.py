"""Dungeon 3 — 안드바리의 황금 동굴 (Andvari's Falls). Beginner, 176 x 288, underground.

An open gorge with a waterfall lake (the ship lands here); behind the falls the caves go ever deeper:
spray cave, lush moss vein, crystal mine, underground lake with stone bridges, the cursed gold vault,
Andvari's forge, and the golden hoard cavern.
"""
import math

import numpy as np

from mcw import B, AIR, PAL, banner_be
from gen_common import fbm, stair, slab, wall_sign, standing_sign, hanging_lamp, lamp_post, line_points, leaves_of, \
    leaf_blob, boulder, disk
import nr_parts as P
from nr_dungeon import Dungeon, mixer
from nr_spawn import cyl, ell, thick_line

SEA = 62


class Andvari(Dungeon):
    Y0, SY = 16, 96          # 16..111

    ZN = {
        "start": (88, 257, 50, 22, 63, 80, 0.25),
        "c1": (88, 214, 30, 20, 63, 12),
        "c2": (50, 178, 34, 26, 60, 16),
        "c3": (120, 150, 34, 24, 56, 14),
        "c4": (70, 110, 42, 28, 52, 22),
        "c5": (126, 74, 30, 22, 48, 12),
        "c6": (58, 48, 30, 22, 44, 14),
        "boss": (116, 30, 20, 19, 40, 20, 0.08),
    }

    def build(self):
        self.terrain()
        self.gorge()
        self.spray_cave()
        self.lush_vein()
        self.crystal_mine()
        self.cave_lake()
        self.gold_vault()
        self.forge()
        self.hoard()
        self.finish()

    def terrain(self):
        zones = dict(self.ZN)
        paths = [([(88, 240), (88, 226)], 7, 7), ([(70, 210), (58, 196)], 7, 7), ([(80, 168), (100, 158)], 7, 7),
                 ([(104, 136), (90, 124)], 7, 8), ([(104, 98), (114, 88)], 7, 7), ([(104, 66), (80, 56)], 7, 7),
                 ([(82, 38), (100, 32)], 7, 8)]
        rock = [B("stone"), B("andesite"), B("stone"), B("tuff"), B("deepslate"), B("stone"), B("diorite")]
        self.caverns(zones, paths, rock)
        self.keep_margin(6, rock)
        a = self.a
        # deeper layers become deepslate
        for j in range(0, 40 - self.Y0):
            layer = a.blk[:, j, :]
            layer[layer != AIR] = B("deepslate")
        # the gorge is open to the sky
        m = self.masks["start"]
        for (i, k) in np.argwhere(m):
            col = a.blk[i, :, k]
            for j in range(int(self.F[i, k]) + 1 - self.Y0, self.SY):
                col[j] = AIR
        self.a.bio[:, :] = 187
        self.a.bio[:, 230:] = 7
        self.a.bio[:, :95] = 188

    def fy(self, lx, lz):
        return int(self.F[lx, lz])

    def at(self, lx, lz):
        x, z = self.L(lx, lz)
        return x, int(self.F[lx, lz]) + 1, z

    def zbox(self, key, pad=3):
        cx, cz, rx, rz, f, h = self.ZN[key][:6]
        x, z = self.L(cx, cz)
        return (x - rx - pad, f - 6, z - rz - pad, x + rx + pad, f + h + 2, z + rz + pad)

    def floor_paint(self, mask, mix, depth=1):
        a = self.a
        water = B("water")
        for (i, k) in np.argwhere(mask):
            f = int(self.F[i, k]) - self.Y0
            if a.blk[i, f, k] == water:
                continue
            for d in range(depth):
                if f - d >= 0:
                    a.blk[i, f - d, k] = mix()

    # ------------------------------------------------------------ start: waterfall gorge
    def gorge(self):
        a, rng = self.a, self.rng
        L = self.L
        m = self.masks["start"]
        top = mixer(rng, [(B("grass_block"), 4), (B("moss_block"), 3), (B("gravel"), 1), (B("coarse_dirt"), 1)])
        # lake in the middle of the gorge: water up to SEA, flush banks one block higher
        lake = np.zeros_like(m)
        for (i, k) in np.argwhere(m):
            if math.hypot((i - 90) / 32.0, (k - 260) / 12.0) < 1:
                lake[i, k] = True
        from scipy.ndimage import distance_transform_edt
        dist = distance_transform_edt(~lake)
        for (i, k) in np.argwhere(m & ~lake & (dist < 5)):
            self.lower_floor(i, k, SEA + 1 + int(dist[i, k] // 3))
        self.floor_paint(m, top)
        sand = mixer(rng, [(B("gravel"), 3), (B("sand"), 1), (B("clay"), 1)])
        for (i, k) in np.argwhere(m & ~lake & (dist < 2.5)):
            a.blk[i, int(self.F[i, k]) - self.Y0, k] = sand()
        for (i, k) in np.argwhere(lake):
            d = math.hypot((i - 90) / 32.0, (k - 260) / 12.0)
            x, z = self.x0 + i, self.z0 + k
            depth = int(2 + 5 * (1 - d))
            for y in range(SEA + 1, int(self.F[i, k]) + 1):
                a.set(x, y, z, AIR)
            for y in range(SEA - depth + 1, SEA + 1):
                a.set(x, y, z, B("water"))
            a.set(x, SEA - depth, z, B("gravel") if rng.random() < 0.5 else B("clay"))
            self.F[i, k] = SEA - depth
            if rng.random() < 0.05 and depth >= 3:
                a.set(x, SEA - depth + 1, z, B("seagrass"))
        # return ship moored in the lake, jetty from the north shore to its side
        info = P.longship(a, self.x0 + 112, SEA, self.z0 + 261, "west", rng, length=27, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        for lz in range(244, 258):
            for lx in (99, 100, 101):
                x, z = L(lx, lz)
                if not m[lx, lz]:
                    continue
                a.set(x, SEA + 1, z, B("spruce_planks"))
                for y in range(SEA + 2, SEA + 6):
                    a.set(x, y, z, AIR)
                if lx != 100 and lz % 4 == 0:
                    for y in range(SEA - 4, SEA + 1):
                        if a.get(x, y, z) in (B("water"), AIR):
                            a.set(x, y, z, B("spruce_log", axis="y"))
                    if lz < 256:
                        a.set(x, SEA + 2, z, B("spruce_fence"))
                        if lz % 8 == 0:
                            a.set(x, SEA + 3, z, B("lantern"))
        ax, az = L(100, 247)
        ay = SEA + 2
        self.data["start"] = [ax + 0.5, ay, az + 0.5, 180]
        self.walk_seeds = [(ax, ay, az)]
        # the waterfall: a curtain down the north wall in front of the cave mouth
        zm = min(k for k in range(self.sz) if m[88, k])
        wx, wz = L(88, zm)
        top_y = self.Y0 + self.SY - 3
        for dx in range(-4, 5):
            for y in range(SEA + 1, top_y):
                if a.get(wx + dx, y, wz) == AIR and (abs(dx) < 4 or y > SEA + 9):
                    a.set(wx + dx, y, wz, B("flowing_water", liquid_depth=8))
            # stream cut into the rim feeding the falls
            for dz in range(1, 9):
                a.set(wx + dx, top_y - 1, wz - dz, B("stone"))
                a.set(wx + dx, top_y, wz - dz, B("water") if abs(dx) < 4 else B("mossy_cobblestone"))
                for y in range(top_y + 1, self.Y0 + self.SY):
                    a.set(wx + dx, y, wz - dz, AIR)
            a.set(wx + dx, top_y, wz, B("flowing_water", liquid_depth=8) if abs(dx) < 4 else B("mossy_cobblestone"))
        # plunge pool: 3 deep under the curtain (anyone dropping off the falls lands in water), flush with the floor
        for dx in range(-8, 9):
            for dz in range(-3, 8):
                if (dx / 8.5) ** 2 + (dz / 7.5) ** 2 > 1:
                    continue
                x, z = wx + dx, wz + dz
                i, k = x - self.x0, z - self.z0
                if self.cave[i, k] and not lake[i, k]:
                    f = int(self.F[i, k])
                    deep = 3 if abs(dx) <= 6 and dz <= 5 else 1
                    for y in range(f - deep + 1, f + 1):
                        a.set(x, y, z, B("water"))
                    a.set(x, f - deep, z, B("gravel") if (dx + dz) % 3 else B("mossy_cobblestone"))
        # mossy rocks and glow lichen on the wet wall around the falls
        for dx in range(-9, 10):
            for y in range(SEA + 1, top_y):
                x, z = wx + dx, wz - 1
                if a.get(x, y, z) != AIR and a.get(x, y, z + 1) == AIR and rng.random() < 0.35:
                    a.set(x, y, z, B("mossy_cobblestone") if rng.random() < 0.6 else B("moss_block"))
        # trees and ferns on the gorge floor
        from gen_common import birch_tree
        for _ in range(80):
            lx, lz = rng.randint(36, 140), rng.randint(236, 282)
            if not m[lx, lz] or lake[lx, lz] or dist[lx, lz] < 3:
                continue
            if 96 <= lx <= 104 and lz < 252:
                continue
            x, y, z = self.at(lx, lz)
            if a.get(x, y - 1, z) in (B("grass_block"), B("moss_block")) and a.get(x, y, z) == AIR:
                r = rng.random()
                if r < 0.18:
                    birch_tree(a, x, y, z, rng)
                elif r < 0.25:
                    boulder(a, x, y - 1, z, rng, rng.uniform(1.2, 2.2), [B("mossy_cobblestone"), B("stone"), B("andesite")])
                else:
                    a.set(x, y, z, B(rng.choice(["fern", "short_grass", "azalea", "flowering_azalea", "short_grass", "blue_orchid"])))
        # vines and glow lichen down the gorge walls
        for (i, k) in np.argwhere(m):
            if rng.random() < 0.82:
                continue
            for (di, dk, bit) in ((1, 0, 8), (-1, 0, 2), (0, 1, 1), (0, -1, 4)):
                ii, kk = i + di, k + dk
                if 0 <= ii < self.sx and 0 <= kk < self.sz and not m[ii, kk]:
                    x, z = self.x0 + i, self.z0 + k
                    y0 = int(self.F[i, k]) + rng.randint(10, 32)
                    n = rng.randint(3, 14)
                    for t in range(min(n, y0 - int(self.F[i, k]) - 5)):
                        if a.get(x, y0 - t, z) == AIR:
                            a.set(x, y0 - t, z, B("vine", vine_direction_bits=bit))
                    break
        standing_sign(a, ax - 2, ay, az - 2, 8, "§l§6안드바리의 황금 동굴\n§r§f폭포 뒤 동굴로\n§7황금을 탐내지 마라", kind="spruce_standing_sign")

    def lower_floor(self, i, k, f):
        if self.F[i, k] > f:
            col = self.a.blk[i, :, k]
            for y in range(f + 1, int(self.F[i, k]) + 1):
                col[y - self.Y0] = AIR
            self.F[i, k] = f

    # ------------------------------------------------------------ c1: spray cave
    def spray_cave(self):
        a, rng = self.a, self.rng
        m = self.masks["c1"]
        self.floor_paint(m, mixer(rng, [(B("moss_block"), 3), (B("stone"), 2), (B("gravel"), 1), (B("clay"), 1)]))
        # shallow channels (1 deep) across the floor
        for (i, k) in np.argwhere(m):
            if abs(math.sin(i / 6.0) * 5 + 214 - k) < 1.2 and rng.random() < 0.9:
                x, z = self.x0 + i, self.z0 + k
                f = int(self.F[i, k])
                a.set(x, f, z, B("water"))
        self.dripstones("c1", 0.05)
        self.cave_lights("c1", "lantern", spacing=10)
        self.add_zone("c1", self.zbox("c1"), floor_mask=self.cave)

    def dripstones(self, key, chance, lichen=0.03):
        a, rng = self.a, self.rng
        for (i, k) in np.argwhere(self.masks[key]):
            r = rng.random()
            x, z = self.x0 + i, self.z0 + k
            c = int(self.C[i, k])
            if r < chance and c - int(self.F[i, k]) > 7:
                n = rng.randint(1, 4)
                for t in range(n):
                    yy = c - t
                    if a.get(x, yy, z) == AIR:
                        thick = "tip" if t == n - 1 else "frustum" if t == n - 2 else "middle"
                        a.set(x, yy, z, B("pointed_dripstone", dripstone_thickness=thick, hanging=1))
            elif r < chance + lichen:
                if a.get(x, c, z) == AIR and a.get(x, c + 1, z) != AIR:
                    a.set(x, c, z, B("glow_lichen", multi_face_direction_bits=2))

    def cave_lights(self, key, block="lantern", spacing=9):
        a = self.a
        for (i, k) in np.argwhere(self.masks[key]):
            if i % spacing or k % spacing:
                continue
            x, z = self.x0 + i, self.z0 + k
            c = int(self.C[i, k])
            if c - int(self.F[i, k]) >= 6 and a.get(x, c + 1, z) != AIR:
                hanging_lamp(a, x, c, z, 2, B(block, hanging=1))

    # ------------------------------------------------------------ c2: lush moss vein
    def lush_vein(self):
        a, rng = self.a, self.rng
        m = self.masks["c2"]
        self.floor_paint(m, mixer(rng, [(B("moss_block"), 6), (B("clay"), 1), (B("dirt_with_roots"), 1)]))
        for (i, k) in np.argwhere(m):
            x, z = self.x0 + i, self.z0 + k
            f, c = int(self.F[i, k]), int(self.C[i, k])
            r = rng.random()
            if r < 0.06:
                a.set(x, f + 1, z, B(rng.choice(["azalea", "flowering_azalea"])))
            elif r < 0.25:
                a.set(x, f + 1, z, B("moss_carpet"))
            elif r < 0.31:
                a.set(x, f + 1, z, B(rng.choice(["short_grass", "fern"])))
            # glow berries hanging from the ceiling
            if rng.random() < 0.05 and a.get(x, c + 1, z) != AIR:
                n = rng.randint(2, 6)
                for t in range(n):
                    if a.get(x, c - t, z) == AIR and c - t > f + 3:
                        a.set(x, c - t, z, B("cave_vines_body_with_berries") if t % 2 else B("cave_vines"))
            if rng.random() < 0.004 and a.get(x, c + 1, z) != AIR:
                a.set(x, c, z, B("spore_blossom"))
        # a few clay pools
        for _ in range(5):
            lx, lz = rng.randint(24, 76), rng.randint(160, 196)
            if m[lx, lz]:
                for dx in range(-2, 3):
                    for dz in range(-2, 3):
                        if m[lx + dx, lz + dz] and dx * dx + dz * dz <= 5:
                            x, z = self.x0 + lx + dx, self.z0 + lz + dz
                            f = int(self.F[lx + dx, lz + dz])
                            a.set(x, f, z, B("water"))
                            a.set(x, f - 1, z, B("clay"))
        self.add_zone("c2", self.zbox("c2"), floor_mask=self.cave)

    # ------------------------------------------------------------ c3: crystal mine
    def crystal_mine(self):
        a, rng = self.a, self.rng
        m = self.masks["c3"]
        self.floor_paint(m, mixer(rng, [(B("stone"), 3), (B("gravel"), 2), (B("andesite"), 1), (B("cobblestone"), 1)]))
        # amethyst geode pockets in the walls
        geodes = [(96, 140), (140, 138), (124, 166), (106, 160)]
        for (lx, lz) in geodes:
            x, z = self.L(lx, lz)
            f = int(self.F[min(lx, self.sx - 1), lz])
            cy = f + 4
            for dx in range(-5, 6):
                for dy in range(-4, 5):
                    for dz in range(-5, 6):
                        d = math.sqrt(dx * dx + dy * dy * 1.3 + dz * dz)
                        if d > 5.5:
                            continue
                        b = a.get(x + dx, cy + dy, z + dz)
                        if b == AIR:
                            continue
                        if d > 4.6:
                            a.set(x + dx, cy + dy, z + dz, B("smooth_basalt"))
                        elif d > 3.8:
                            a.set(x + dx, cy + dy, z + dz, B("calcite"))
                        else:
                            a.set(x + dx, cy + dy, z + dz, B("budding_amethyst") if rng.random() < 0.15 else B("amethyst_block"))
            # clusters on exposed amethyst
            for _ in range(30):
                px, py, pz = x + rng.randint(-4, 4), cy + rng.randint(-3, 3), z + rng.randint(-4, 4)
                if a.get(px, py, pz) == AIR and a.get(px, py - 1, pz) in (B("amethyst_block"), B("budding_amethyst"), B("calcite")):
                    a.set(px, py, pz, B("amethyst_cluster", block_face="up"))
        # mine rails with timber frames along the passage
        pts = [(96, 160), (110, 152), (140, 146)]
        for (p0, p1) in zip(pts[:-1], pts[1:]):
            for q in line_points((p0[0], 0, p0[1]), (p1[0], 0, p1[1]), step=1.0):
                lx, lz = int(q[0]), int(q[2])
                if not self.cave[lx, lz]:
                    continue
                x, z = self.L(lx, lz)
                f = int(self.F[lx, lz])
                a.set(x, f, z, B("gravel"))
                a.set(x, f + 1, z, B("rail", rail_direction=1) if abs(p1[0] - p0[0]) > abs(p1[1] - p0[1]) else B("rail", rail_direction=0))
        for (lx, lz) in ((100, 150), (116, 150), (130, 148), (110, 160)):
            x, z = self.L(lx, lz)
            f = int(self.F[lx, lz])
            for side in (-2, 2):
                for yy in range(f + 1, f + 5):
                    a.set(x, yy, z + side, B("spruce_log", axis="y"))
            for dz in range(-2, 3):
                a.set(x, f + 5, z + dz, B("spruce_planks"))
            a.set(x, f + 4, z, B("lantern", hanging=1))
        self.dripstones("c3", 0.03)
        self.add_zone("c3", self.zbox("c3"), floor_mask=self.cave)

    # ------------------------------------------------------------ c4: the underground lake
    def cave_lake(self):
        a, rng = self.a, self.rng
        m = self.masks["c4"]
        f0 = self.ZN["c4"][4]
        # stone bridges (5 wide: 3 walkable + parapets) cross the lake between the two passages
        route = [(92, 124), (66, 110), (94, 98)]
        deck, rail, along = set(), set(), {}
        n = 0
        for (p0, p1) in zip(route[:-1], route[1:]):
            for q in line_points((p0[0], 0, p0[1]), (p1[0], 0, p1[1]), step=0.5):
                n += 1
                for dx in range(-2, 3):
                    for dz in range(-2, 3):
                        c = (int(q[0]) + dx, int(q[2]) + dz)
                        if max(abs(dx), abs(dz)) <= 1:
                            deck.add(c)
                        else:
                            rail.add(c)
                        along.setdefault(c, n)
        rail -= deck
        lake = np.zeros_like(m)
        for (i, k) in np.argwhere(m):
            d = math.hypot((i - 66) / 27.0, (k - 110) / 16.0)
            isl = math.hypot(i - 66, k - 110) < 5.5
            if d < 1 and not isl:
                lake[i, k] = True
        for (i, k) in np.argwhere(lake):
            d = math.hypot((i - 66) / 27.0, (k - 110) / 16.0)
            x, z = self.x0 + i, self.z0 + k
            f = int(self.F[i, k])
            depth = 2 + int(5 * (1 - d))
            wtop = min(f, f0) - 1                   # water one below the surrounding floor: banks are a single step
            for y in range(wtop + 1, f + 1):
                a.set(x, y, z, AIR)
            for y in range(wtop - depth + 1, wtop + 1):
                a.set(x, y, z, B("water"))
            a.set(x, wtop - depth, z, B("gravel") if rng.random() < 0.6 else B("clay"))
            self.F[i, k] = wtop - depth
            if rng.random() < 0.04:
                a.set(x, wtop - depth + 1, z, B("seagrass"))
        # bridges: deck at the cavern floor level, arches every 7 blocks along the run
        for c in deck | rail:
            i, k = c
            if not (0 <= i < self.sx and 0 <= k < self.sz) or not self.cave[i, k]:
                continue
            x, z = self.x0 + i, self.z0 + k
            pier = along[c] % 14 < 3
            if c in deck:
                a.set(x, f0, z, B("stone_bricks") if (i * 7 + k) % 5 else B("mossy_stone_bricks"))
                for y in range(f0 + 1, f0 + 4):
                    if a.get(x, y, z) != AIR and lake[i, k]:
                        a.set(x, y, z, AIR)
            elif lake[i, k]:
                a.set(x, f0, z, B("stone_bricks"))
                a.set(x, f0 + 1, z, B("stone_brick_wall") if not pier else B("chiseled_stone_bricks"))
                if pier and along[c] % 14 == 1:
                    a.set(x, f0 + 2, z, B("lantern"))
            if lake[i, k]:
                bottom = int(self.F[i, k])
                for y in range(bottom + 1, f0):
                    if pier:
                        a.set(x, y, z, B("stone_bricks") if y < f0 - 2 else B("mossy_stone_bricks"))
                    elif y == f0 - 1:
                        a.set(x, y, z, slab("stone_brick_slab", top=True))
                if c in deck:
                    self.F[i, k] = f0
        # glowing ceiling and drips
        for (i, k) in np.argwhere(m):
            if rng.random() < 0.08:
                x, z = self.x0 + i, self.z0 + k
                c = int(self.C[i, k])
                if a.get(x, c, z) == AIR and a.get(x, c + 1, z) != AIR:
                    a.set(x, c, z, B("glow_lichen", multi_face_direction_bits=2))
        self.dripstones("c4", 0.03, lichen=0.04)
        self.lake4 = lake
        self.add_zone("c4", self.zbox("c4"), floor_mask=self.cave & ~lake)

    # ------------------------------------------------------------ c5: the cursed gold vault (dwarven halls)
    def gold_vault(self):
        a, rng = self.a, self.rng
        m = self.masks["c5"]
        cx, cy, cz = self.at(126, 74)
        f = cy - 1
        tiles = mixer(rng, [(B("deepslate_tiles"), 4), (B("polished_deepslate"), 3), (B("cracked_deepslate_tiles"), 1)])
        self.floor_paint(m, tiles)
        # a built hall inside the cavern: pillars with gold capitals, gold heaps
        for dx in range(-22, 23, 6):
            for dz in (-12, 12):
                x, z = cx + dx, cz + dz
                if not self.inside(x, z) or not self.cave[x - self.x0, z - self.z0]:
                    continue
                c = int(self.C[x - self.x0, z - self.z0])
                for yy in range(f + 1, c + 1):
                    a.set(x, yy, z, B("deepslate_bricks") if yy < c - 1 else B("gold_block"))
                a.set(x, f + 3, z + (1 if dz < 0 else -1), B("lantern"))
        for _ in range(26):
            lx, lz = rng.randint(100, 152), rng.randint(56, 92)
            if not m[lx, lz]:
                continue
            x, y, z = self.at(lx, lz)
            r = rng.uniform(1.2, 2.6)
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    dd = math.hypot(dx, dz)
                    if dd <= r:
                        hh = int((r - dd) * 0.8) + 1
                        for t in range(hh):
                            a.put(x + dx, y + t, z + dz, B("gold_block") if rng.random() < 0.6 else B("raw_gold_block"))
        for _ in range(10):
            lx, lz = rng.randint(100, 152), rng.randint(56, 92)
            if m[lx, lz]:
                x, y, z = self.at(lx, lz)
                if a.get(x, y, z) == AIR:
                    a.set(x, y, z, B("chest") if rng.random() < 0.4 else B("candle"))
        self.add_zone("c5", self.zbox("c5"), floor_mask=self.cave)

    # ------------------------------------------------------------ c6: Andvari's forge
    def forge(self):
        a, rng = self.a, self.rng
        m = self.masks["c6"]
        self.floor_paint(m, mixer(rng, [(B("blackstone"), 3), (B("polished_blackstone"), 2), (B("basalt"), 1), (B("cobbled_deepslate"), 1)]))
        cx, cy, cz = self.at(58, 48)
        f = cy - 1
        # lava pools set into the floor, rimmed with stone
        for (lx, lz) in ((44, 40), (70, 58), (64, 36), (40, 56)):
            x, z = self.L(lx, lz)
            if not self.cave[lx, lz]:
                continue
            ff = int(self.F[lx, lz])
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if dx * dx + dz * dz <= 4:
                        a.set(x + dx, ff, z + dz, B("lava"))
                        a.set(x + dx, ff - 1, z + dz, B("magma"))
                    elif dx * dx + dz * dz <= 8:
                        a.set(x + dx, ff, z + dz, B("polished_blackstone_bricks"))
                        a.set(x + dx, ff + 1, z + dz, B("polished_blackstone_wall") if (dx + dz) % 2 == 0 else AIR)
        # anvils, blast furnaces, chains
        for k, (dx, dz) in enumerate(((-6, -4), (6, -3), (-4, 6), (5, 5))):
            a.set(cx + dx, cy, cz + dz, B("anvil", cardinal=["north", "east", "south", "west"][k]))
        for dz in range(-2, 3):
            a.set(cx - 12, cy, cz + dz, B("blast_furnace", cardinal="east"))
            a.set(cx - 12, cy + 1, cz + dz, B("polished_blackstone_bricks"))
        for (dx, dz) in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            x, z = cx + dx, cz + dz
            c = int(self.C[x - self.x0, z - self.z0])
            for yy in range(cy + 4, c + 1):
                a.set(x, yy, z, B("chain", axis="y"))
            a.set(x, cy + 3, z, B("lantern", hanging=1))
        self.add_zone("c6", self.zbox("c6"), floor_mask=self.cave)

    # ------------------------------------------------------------ boss: the golden hoard
    def hoard(self):
        a, rng = self.a, self.rng
        cx, cz = self.L(116, 30)
        y = self.ZN["boss"][4] + 1
        R = 15

        def floor_fn(x, z, d):
            if int(d) % 5 == 0:
                return B("gold_block")
            return B("polished_deepslate") if (x + z) % 2 else B("deepslate_tiles")
        ar = self.arena("boss", cx, y, cz, R, "andvari", "final", floor_fn=floor_fn)
        # gold mounds around the arena edge
        for k in range(18):
            ang = k / 18 * 2 * math.pi
            r = R + 3
            x, z = int(round(cx + math.cos(ang) * r)), int(round(cz + math.sin(ang) * r))
            if not self.inside(x, z) or not self.cave[x - self.x0, z - self.z0]:
                continue
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    dd = math.hypot(dx, dz)
                    if dd < 3.2:
                        for t in range(int((3.2 - dd) * 1.2) + 1):
                            a.put(x + dx, y + t, z + dz, B("gold_block") if rng.random() < 0.6 else B("raw_gold_block"))
        # the cursed ring on a pedestal at the back
        px, pz = cx, cz - R + 2
        a.set(px, y, pz, B("chiseled_deepslate"))
        a.set(px, y + 1, pz, B("gold_block"))
        a.set(px, y + 2, pz, B("glowstone"))
        for k in range(8):
            ang = k / 8 * 2 * math.pi
            x, z = int(round(cx + math.cos(ang) * (R - 1.5))), int(round(cz + math.sin(ang) * (R - 1.5)))
            a.set(x, y, z, B("lantern"))
        # exit: a tunnel east through the rock, gated, to the rune circle
        ex, ez = cx + R + 16, cz
        for x in range(ex - 4, ex + 5):
            for z in range(ez - 4, ez + 5):
                a.set(x, y - 1, z, B("polished_deepslate"))
                for yy in range(y, y + 6):
                    a.set(x, yy, z, AIR if max(abs(x - ex), abs(z - ez)) < 4 else B("deepslate_tiles"))
        for x in range(cx + R - 2, ex - 3):
            for w in range(-2, 3):
                edge = abs(w) == 2
                a.set(x, y - 1, ez + w, B("polished_deepslate"))
                for yy in range(y, y + 4):
                    if edge and yy < y + 3:
                        if a.get(x, yy, ez + w) == AIR and x > cx + R + 2:
                            a.set(x, yy, ez + w, B("deepslate_bricks"))
                    elif not edge and yy < y + 3:
                        a.set(x, yy, ez + w, AIR)
                    else:
                        if x > cx + R + 2:
                            a.set(x, yy, ez + w, B("deepslate_bricks"))
            if (x - cx) % 4 == 0 and x > cx + R + 2:
                a.set(x, y + 2, ez - 1, B("lantern", hanging=1))
        self.exit_portal(ex, y, ez)
        gx = cx + R + 9
        ar["exit"] = [list(p) for p in self.doorway(gx, y, ez, 3, 3, "z")]
        for yy in range(y, y + 3):
            for w in (-2, 2):
                a.set(gx, yy, ez + w, B("chiseled_deepslate"))
        for w in range(-2, 3):
            a.set(gx, y + 3, ez + w, B("chiseled_deepslate"))
        self.close([tuple(p) for p in ar["exit"]])

    def finish(self):
        # light the dark parts softly, ambient particles, boundary
        for key in ("c1", "c2", "c3", "c4", "c5", "c6"):
            x1, y1, z1, x2, y2, z2 = self.zones[key]["box"]
            self.light_fill((x1, z1, x2, z2), (y1, y2), level=6, threshold=3, spacing=7)
        ar = self.arenas[0]
        self.light_fill((int(ar["x"]) - 16, int(ar["z"]) - 16, int(ar["x"]) + 16, int(ar["z"]) + 16), (ar["y"] - 1, ar["y"] + 2), level=8, threshold=5, spacing=6)
        self.ambient = [dict(box=self.zones["c2"]["box"], particle="minecraft:spore_blossom_ambient_particle", rate=2),
                        dict(box=self.zones["c4"]["box"], particle="minecraft:water_drip_particle", rate=2),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:lava_particle", rate=1)]
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        self.a.fix_walls()

    def is_escape(self, x, y, z):
        # the only open sky is the gorge; anything with sky above elsewhere would be outside the caves
        i, k = x - self.x0, z - self.z0
        if self.masks["start"][i, k]:
            return False
        return all(self.a.get(x, yy, z) == AIR for yy in range(y + 2, min(y + 30, self.Y0 + self.SY - 1)))


def build(seed=1):
    d = Andvari("d03", seed)
    d.build()
    return d


if __name__ == "__main__":
    import sys, time
    import render
    t0 = time.time()
    d = build()
    print("built %.1fs" % (time.time() - t0))
