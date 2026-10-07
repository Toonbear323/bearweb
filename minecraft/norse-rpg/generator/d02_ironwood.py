"""Dungeon 2 — 철의 숲 야른비드 (the Iron Wood). Beginner, 176 x 288.

South -> north: river-mouth camp, rusted giant-tree path, wolf dens, bone clearing, vine ravine with rope bridges,
Angrboda's stilt hut over a bog, the moonlit ancient tree, and Hati's rock hill under a pale moon.
"""
import math

import numpy as np
from scipy.ndimage import binary_dilation

from mcw import B, AIR, PAL, banner_be
from gen_common import fbm, stair, slab, wall_sign, standing_sign, hanging_lamp, lamp_post, line_points, leaves_of, \
    leaf_blob, boulder, disk, spruce_tree
import nr_parts as P
from nr_dungeon import Dungeon, mixer
from nr_spawn import cyl, ell, thick_line

SEA = 62


def iron_tree(a, x, y, z, rng, h=None, big=True):
    """Giant 'iron' tree: dark trunk with rust-red bands, buttress roots, a dark crown."""
    h = h or rng.randint(14, 22)
    r0 = 1.8 if big else 1.0
    bark = B("dark_oak_log", axis="y")
    rust = B("stripped_mangrove_log", axis="y")
    cyl(a, x, y, z, r0, r0 * 0.6, h, bark)
    for k in range(0, h, 5):
        if rng.random() < 0.7:
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if a.get(x + dx, y + k, z + dz) == bark and rng.random() < 0.5:
                        a.set(x + dx, y + k, z + dz, rust)
    for k in range(5 if big else 3):
        ang = k / 5 * 2 * math.pi + rng.uniform(-0.3, 0.3)
        thick_line(a, (x + math.cos(ang) * r0, y + 3, z + math.sin(ang) * r0),
                   (x + math.cos(ang) * (r0 + 4), y - 1, z + math.sin(ang) * (r0 + 4)), 0.6, B("dark_oak_wood"))
    leaf = leaves_of("dark_oak")
    alt = leaves_of("mangrove")
    for k in range(4):
        ang = rng.uniform(0, 6.28)
        hb = y + h - rng.randint(2, 7)
        L = rng.uniform(3, 6)
        tx, tz = x + math.cos(ang) * L, z + math.sin(ang) * L
        thick_line(a, (x, hb, z), (tx, hb + 3, tz), 0.5, bark)
        leaf_blob(a, tx, hb + 4, tz, rng.uniform(3.5, 5), leaf, rng, flat=0.55, extra=alt, extra_chance=0.25)
    leaf_blob(a, x, y + h + 1, z, rng.uniform(4.5, 6.5), leaf, rng, flat=0.5, extra=alt, extra_chance=0.2)


class IronWood(Dungeon):
    Y0, SY = 32, 112

    def build(self):
        self.terrain()
        self.camp()
        self.forest_path()
        self.wolf_dens()
        self.bone_clearing()
        self.ravine()
        self.hag_bog()
        self.ancient_tree()
        self.moon_hill()
        self.finish()

    def terrain(self):
        rng = self.rng
        hill = lambda X, Z, n: 70 + np.clip((X - 112) / 30.0, 0, 1) * 6 + (n - 0.5) * 2
        zones = {
            "start": (88, 262, 54, 26, lambda X, Z, n: 63 + np.clip((270 - Z) * 0.08, 0, 2.5)),
            "c1": (60, 222, 36, 28, 66),
            "c2": (124, 190, 36, 28, hill),
            "c3": (60, 154, 32, 26, 72),
            "c4": (114, 118, 34, 24, 72),
            "c5": (56, 80, 34, 26, 70),
            "c6": (120, 48, 36, 30, 74),
            "boss": (54, 22, 26, 20, 82),
        }
        paths = [([(86, 250), (66, 236)], 9), ([(84, 214), (104, 204)], 9), ([(110, 172), (80, 162)], 9),
                 ([(80, 140), (96, 128)], 9), ([(96, 104), (74, 92)], 9), ([(80, 66), (100, 58)], 9),
                 ([(98, 30), (74, 24)], 9)]
        self.valleys(zones, paths, high=(94, 14), wall_extra=13)
        X, Z = self.X - self.x0, self.Z - self.z0
        self.river = (Z > 276 + (self.n2 - 0.5) * 6)
        self.H = np.where(self.river, 57, self.H)
        # banks next to the river are low (one step out of the water), and walls there are trimmed
        from scipy.ndimage import distance_transform_edt as _edt
        dr = _edt(~self.river)
        bank = (dr > 0) & (dr <= 3) & (self.H > 63)
        self.H = np.where(bank & (Z > 266), 63, self.H)
        self.carved = self.carved | (bank & (Z > 266))
        top = mixer(rng, [(B("podzol"), 4), (B("grass_block"), 3), (B("coarse_dirt"), 2), (B("dirt_with_roots"), 1), (B("moss_block"), 1)])
        sub = mixer(rng, [(B("dirt"), 5), (B("dirt_with_roots"), 1)])
        rock = [B("stone"), B("andesite"), B("tuff"), B("deepslate"), B("cobbled_deepslate"), B("stone")]
        self.paint_valley(top, sub, rock)
        a = self.a
        for (i, k) in np.argwhere(self.river):
            for y in range(int(self.H[i, k]) + 1, SEA + 1):
                a.blk[i, y - self.Y0, k] = B("water")
            a.blk[i, int(self.H[i, k]) - self.Y0, k] = B("mud") if rng.random() < 0.5 else B("gravel")
        a.bio[:, :] = 29                    # dark forest
        a.bio[:, :70] = 32                  # old-growth taiga around the moon hill

    def zbox(self, key, pad=4, dy=(-6, 18)):
        cx, cz, rx, rz = self._z[key]
        x, z = self.L(cx, cz)
        f = int(np.nanmean(self.H[max(0, cx - 4):cx + 5, max(0, cz - 4):cz + 5]))
        return (x - rx - pad, f + dy[0], z - rz - pad, x + rx + pad, f + dy[1], z + rz + pad)

    _z = {"c1": (60, 222, 36, 28), "c2": (124, 190, 36, 28), "c3": (60, 154, 32, 26), "c4": (114, 118, 34, 24),
          "c5": (56, 80, 34, 26), "c6": (120, 48, 36, 30)}

    def _at(self, lx, lz):
        x, z = self.L(lx, lz)
        return x, int(self.H[lx, lz]) + 1, z

    # ------------------------------------------------------------ S
    def camp(self):
        a, rng = self.a, self.rng
        L = self.L
        # jetty into the river and the return ship
        for lz in range(266, 284):
            for lx in range(84, 89):
                x, z = L(lx, lz)
                a.set(x, 64, z, B("spruce_planks"))
                for y in range(65, 70):
                    a.set(x, y, z, AIR)
                if lx in (84, 88) and lz % 4 == 0:
                    for y in range(55, 64):
                        if a.get(x, y, z) in (B("water"), AIR):
                            a.set(x, y, z, B("spruce_log", axis="y"))
                    a.set(x, 65, z, B("spruce_fence"))
        sx, sz = L(58, 282)
        info = P.longship(a, sx, SEA, sz, "east", rng, sail="beginner")
        self.data["ret"] = dict(deck=list(info["deck"]))
        ax, az = L(86, 266)
        self.data["start"] = [ax + 0.5, 65, az + 0.5, 180]
        self.walk_seeds = [(ax, 65, az)]
        # palisade ring around the camp
        cx, cz = L(100, 258)
        for k in range(48):
            ang = k / 48 * 2 * math.pi
            if 1.2 < ang < 2.0:
                continue                    # gap towards the forest (north-west)
            x, z = int(round(cx + math.cos(ang) * 13)), int(round(cz + math.sin(ang) * 9))
            t = P.surface_y(a, x, z)
            if t is None:
                continue
            for y in range(t + 1, t + 4 + (k % 2)):
                a.set(x, y, z, B("spruce_log", axis="y"))
        y = self._at(100, 258)[1]
        a.set(cx, y - 1, cz, B("cobblestone"))
        a.set(cx, y, cz, B("campfire"))
        for (dx, dz, c) in ((-6, -3, "brown"), (5, -4, "green"), (0, 4, "brown")):
            self._tent(cx + dx, y, cz + dz, c)
        P.barrels(a, cx + 8, y, cz + 2, rng, 3)
        standing_sign(a, *self._at(92, 262), 10, "§l§8철의 숲 야른비드\n§r§f늑대 거인들의 숲\n§7길을 벗어나지 마세요", kind="spruce_standing_sign")

    def _tent(self, x, y, z, color):
        a = self.a
        for dz in range(-2, 3):
            for k in range(3):
                a.set(x - 2 + k, y + k, z + dz, B(color + "_wool"))
                a.set(x + 2 - k, y + k, z + dz, B(color + "_wool"))
            a.set(x, y + 3, z + dz, B("spruce_slab"))

    # ------------------------------------------------------------ C1
    def forest_path(self):
        a, rng = self.a, self.rng
        L = self.L
        m = self.masks["c1"] | self.masks["start"]
        placed = []
        for _ in range(400):
            lx, lz = rng.randint(30, 96), rng.randint(196, 250)
            if not m[lx, lz] or self.wall_dist[lx, lz] > 0:
                continue
            if any(math.hypot(lx - p[0], lz - p[1]) < 11 for p in placed):
                continue
            # keep a winding path free
            if abs((lx - 60) - math.sin(lz / 9.0) * 8) < 5:
                continue
            x, y, z = self._at(lx, lz)
            iron_tree(a, x, y, z, rng, big=rng.random() < 0.6)
            placed.append((lx, lz))
            if len(placed) > 9:
                break
        # mushrooms and fallen logs
        for _ in range(60):
            lx, lz = rng.randint(28, 96), rng.randint(196, 250)
            if not m[lx, lz]:
                continue
            x, y, z = self._at(lx, lz)
            if a.get(x, y, z) != AIR:
                continue
            r = rng.random()
            if r < 0.5:
                a.set(x, y, z, B(rng.choice(["red_mushroom", "brown_mushroom"])))
                a.set(x, y - 1, z, B("podzol"))
            elif r < 0.65:
                axis = rng.choice(["x", "z"])
                for k in range(rng.randint(4, 7)):
                    a.put(x + (k if axis == "x" else 0), y, z + (k if axis == "z" else 0), B("dark_oak_log", axis=axis))
            else:
                a.set(x, y, z, B("fern") if rng.random() < 0.6 else B("short_grass"))
        self.add_zone("c1", self.zbox("c1"), floor_mask=self.carved)

    # ------------------------------------------------------------ C2
    def wolf_dens(self):
        a, rng = self.a, self.rng
        L = self.L
        # den caves dug into the east wall
        for (lz, depth) in ((176, 9), (192, 11), (206, 8)):
            lx = 124
            while self.carved[lx, lz] and lx < self.sx - 2:
                lx += 1
            x, z = L(lx, lz)
            y = int(self.H[lx - 1, lz]) + 1
            for t in range(depth):
                r = 2.2 - t * 0.05
                for dy in range(0, 4):
                    for dz in range(-2, 3):
                        if dy * dy * 0.5 + dz * dz <= r * r + 1:
                            a.set(x + t, y + dy, z + dz, AIR)
                a.set(x + t, y - 1, z, B("coarse_dirt"))
            for k in range(6):
                a.set(x + rng.randint(2, depth - 1), y, z + rng.randint(-1, 1), B("bone_block", axis=rng.choice(["x", "y", "z"])))
        for _ in range(16):
            lx, lz = rng.randint(96, 160), rng.randint(168, 214)
            if not self.carved[lx, lz]:
                continue
            x, y, z = self._at(lx, lz)
            boulder(a, x, y, z, rng, rng.uniform(1.4, 2.8), [B("stone"), B("andesite"), B("tuff"), B("mossy_cobblestone")])
        for _ in range(12):
            lx, lz = rng.randint(96, 160), rng.randint(168, 214)
            if self.carved[lx, lz]:
                x, y, z = self._at(lx, lz)
                spruce_tree(a, x, y, z, rng, h=rng.randint(8, 13))
        self.add_zone("c2", self.zbox("c2"), floor_mask=self.carved)

    # ------------------------------------------------------------ C3
    def bone_clearing(self):
        a, rng = self.a, self.rng
        cx, cy, cz = self._at(60, 154)
        # a giant beast skeleton: spine, ribs, skull
        spine = [(cx - 14 + k, cy + 4 + int(2 * math.sin(k / 5.0)), cz) for k in range(28)]
        for (x, y, z) in spine:
            a.set(x, y, z, B("bone_block", axis="x"))
        for k in range(4, 22, 3):
            x, y, z = spine[k]
            for side in (-1, 1):
                pts = [(x, y, z), (x, y + 2, z + side * 4), (x, y - 1, z + side * 7), (x, cy, z + side * 7)]
                for p0, p1 in zip(pts[:-1], pts[1:]):
                    for q in line_points(p0, p1, step=0.5):
                        a.set(q[0], q[1], q[2], B("bone_block", axis="y"))
        sx, sy, sz = spine[-1]
        ell(a, sx + 3, sy, sz, 3, 2.2, 2.5, B("bone_block", axis="y"))
        for (dx, dz) in ((4, -1), (4, 1)):
            a.set(sx + dx, sy + 1, sz + dz, B("air"))
        a.set(sx + 4, sy + 1, sz - 1, B("shroomlight"))
        a.set(sx + 4, sy + 1, sz + 1, B("shroomlight"))
        for k in range(4):
            a.set(sx + 6 + k, sy - 1, sz - 1, B("bone_block", axis="x"))
            a.set(sx + 6 + k, sy - 1, sz + 1, B("bone_block", axis="x"))
        # ritual stones with red banners around the clearing
        for k in range(8):
            ang = k / 8 * 2 * math.pi
            x, z = int(round(cx + math.cos(ang) * 17)), int(round(cz + math.sin(ang) * 14))
            t = P.surface_y(a, x, z)
            if t is None:
                continue
            P.runestone(a, x, t + 1, z, rng, h=rng.randint(4, 6), mat="dark")
            if k % 2 == 0:
                P.banner_pole(a, x + 2, t + 1, z, 1, [("sku", 0), ("bo", 0)], height=4, facing="south")
        self.add_zone("c3", self.zbox("c3"), floor_mask=self.carved)

    # ------------------------------------------------------------ C4: the ravine and rope bridges
    def ravine(self):
        a, rng = self.a, self.rng
        L = self.L
        cx, cy, cz = self._at(114, 118)
        floor_y = cy - 1
        bottom = floor_y - 18
        # a ravine running east-west through the zone, the path crosses it north-south on bridges
        n = fbm(self.sx, self.sz, 10, 2, self.seed + 40)
        for lx in range(76, 154):
            for lz in range(108, 130):
                if not self.carved[lx, lz]:
                    continue
                w = 6 + n[lx, lz] * 3
                if abs(lz - 118 - math.sin(lx / 8.0) * 2) > w:
                    continue
                x, z = L(lx, lz)
                for y in range(bottom, floor_y + 6):
                    a.set(x, y, z, AIR)
                a.set(x, bottom - 1, z, B("gravel"))
                for y in range(bottom, bottom + 4):          # deep enough to break a fall
                    a.set(x, y, z, B("water"))
                self.H[lx, lz] = bottom
        # ravine walls: moss + vines
        # rope bridge (planks with chain/fence rails) along the passage line x = 96..100
        for lx in (95, 96, 97):
            for lz in range(104, 133):
                x, z = L(lx, lz)
                if a.get(x, floor_y, z) == AIR:
                    sag = int(round(1.5 * math.sin(math.pi * (lz - 104) / 28.0)))
                    a.set(x, floor_y - sag, z, B("spruce_slab", half="top") if lx != 96 or lz % 3 else B("spruce_planks"))
                    if lx in (95, 97):
                        a.set(x, floor_y - sag + 1, z, B("spruce_fence"))
        # second bridge further east (an alternate route)
        for lx in (132, 133, 134):
            for lz in range(104, 133):
                x, z = L(lx, lz)
                if a.get(x, floor_y, z) == AIR:
                    sag = int(round(2 * math.sin(math.pi * (lz - 104) / 28.0)))
                    a.set(x, floor_y - sag, z, B("spruce_slab", half="top"))
                    if lx in (132, 134):
                        a.set(x, floor_y - sag + 1, z, B("spruce_fence"))
        # ladders up both ravine walls at three places, so a fall is never a trap
        for lx in (86, 112, 142):
            for sgn, face in ((1, 2), (-1, 3)):          # south wall: ladder faces north (2); north wall: faces south (3)
                lz = 118
                x, _z = L(lx, lz)
                zz = _z
                while a.get(x, floor_y - 2, zz) == AIR and abs(zz - _z) < 14:
                    zz += sgn
                if a.get(x, floor_y - 2, zz) == AIR:
                    continue
                lad = zz - sgn
                for yy in range(bottom + 1, floor_y + 1):
                    a.set(x, yy, lad, B("ladder", facing_direction=face))
                    a.wet[x - self.x0, yy - self.Y0, lad - self.z0] = yy < bottom + 4
                for yy in range(floor_y + 1, floor_y + 4):
                    a.set(x, yy, zz, AIR)
        self.add_zone("c4", self.zbox("c4", dy=(-24, 16)), floor_mask=self.carved)
        self.ravine_box = (L(76, 104), L(154, 132), bottom, floor_y)

    # ------------------------------------------------------------ C5: Angrboda's hut over the bog
    def hag_bog(self):
        a, rng = self.a, self.rng
        L = self.L
        cx, cy, cz = self._at(56, 80)
        n = fbm(self.sx, self.sz, 8, 2, self.seed + 50)
        for lx in range(30, 84):
            for lz in range(60, 102):
                if not self.carved[lx, lz] or self.wall_dist[lx, lz] > 0:
                    continue
                if n[lx, lz] > 0.58 and abs(lx - 56) + abs(lz - 80) > 9:
                    x, z = L(lx, lz)
                    h = int(self.H[lx, lz])
                    a.set(x, h, z, B("water"))
                    a.set(x, h - 1, z, B("mud"))
                    if rng.random() < 0.15:
                        a.set(x, h + 1, z, B("waterlily"))
        # stilt hut
        y0 = cy + 4
        for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4), (0, -4), (0, 4)):
            for y in range(cy - 1, y0):
                a.set(cx + dx, y, cz + dz, B("mangrove_log", axis="y"))
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                a.set(cx + dx, y0, cz + dz, B("mangrove_planks"))
                edge = abs(dx) == 5 or abs(dz) == 5
                if edge:
                    for y in range(y0 + 1, y0 + 5):
                        a.set(cx + dx, y, cz + dz, B("stripped_mangrove_log", axis="y") if abs(dx) == abs(dz) else B("mangrove_planks"))
        for k in range(6):
            for dz in range(-6, 7):
                a.set(cx - 6 + k, y0 + 5 + k, cz + dz, stair("dark_oak_stairs", "east"))
                a.set(cx + 6 - k, y0 + 5 + k, cz + dz, stair("dark_oak_stairs", "west"))
            if k == 5:
                for dz in range(-6, 7):
                    a.set(cx, y0 + 11, cz + dz, B("dark_oak_slab"))
        for k in range(6):
            for dx in range(-5 + k, 6 - k):
                for dz in (-5, 5):
                    a.set(cx + dx, y0 + 5 + k, cz + dz, B("mangrove_planks"))
        a.set(cx, y0 + 1, cz + 5, AIR)
        a.set(cx, y0 + 2, cz + 5, AIR)
        a.set(cx - 2, y0 + 1, cz, B("cauldron", cauldron_liquid="water", fill_level=6))
        a.set(cx + 2, y0 + 1, cz - 2, B("brewing_stand"))
        a.set(cx + 3, y0 + 1, cz + 2, B("barrel", facing_direction=1))
        hanging_lamp(a, cx, y0 + 4, cz, 1, B("soul_lantern", hanging=1))
        # stairs up to the door from the south
        for k in range(5):
            for dx in (-1, 0, 1):
                a.set(cx + dx, cy - 1 + k, cz + 6 + (4 - k), stair("mangrove_stairs", "north"))
        # mushrooms and hanging roots around
        for _ in range(40):
            lx, lz = rng.randint(30, 84), rng.randint(60, 102)
            if self.carved[lx, lz]:
                x, y, z = self._at(lx, lz)
                if a.get(x, y, z) == AIR and a.get(x, y - 1, z) not in (B("water"),):
                    a.set(x, y, z, B(rng.choice(["red_mushroom", "brown_mushroom", "fern", "short_grass"])))
        self.add_zone("c5", self.zbox("c5"), floor_mask=self.carved)

    # ------------------------------------------------------------ C6: the moonlit ancient tree
    def ancient_tree(self):
        a, rng = self.a, self.rng
        cx, cy, cz = self._at(120, 48)
        cyl(a, cx, cy, cz, 4.5, 2.6, 34, B("dark_oak_wood"))
        for k in range(8):
            ang = k / 8 * 2 * math.pi
            thick_line(a, (cx + math.cos(ang) * 3.5, cy + 6, cz + math.sin(ang) * 3.5),
                       (cx + math.cos(ang) * 11, cy - 1, cz + math.sin(ang) * 11), 1.1, B("dark_oak_wood"))
        # root arches: keep the ground passable between the roots
        leaf, alt = leaves_of("dark_oak"), leaves_of("azalea")
        tops = []
        for k in range(7):
            ang = k / 7 * 2 * math.pi + 0.3
            p1 = (cx + math.cos(ang) * 13, cy + 30 + rng.uniform(-3, 3), cz + math.sin(ang) * 13)
            thick_line(a, (cx, cy + 24, cz), p1, 1.0, B("dark_oak_wood"))
            tops.append(p1)
        for (tx, ty, tz) in tops + [(cx, cy + 38, cz)]:
            leaf_blob(a, tx, ty + 2, tz, rng.uniform(6, 8), leaf, rng, flat=0.5, extra=alt, extra_chance=0.15)
        # glowing mushrooms and lichen around the base
        for _ in range(50):
            ang, r = rng.uniform(0, 6.28), rng.uniform(5, 20)
            x, z = int(cx + math.cos(ang) * r), int(cz + math.sin(ang) * r)
            t = P.surface_y(a, x, z)
            if t is None or a.get(x, t + 1, z) != AIR:
                continue
            q = rng.random()
            if q < 0.25:
                a.set(x, t + 1, z, B("shroomlight"))
            elif q < 0.7:
                a.set(x, t + 1, z, B(rng.choice(["red_mushroom", "brown_mushroom"])))
            else:
                a.set(x, t, z, B("moss_block"))
        for (tx, ty, tz) in tops:
            for yy in range(int(ty) - 1, int(cy) + 6, -1):
                if a.get(int(tx), yy, int(tz)) == AIR:
                    hanging_lamp(a, int(tx), yy, int(tz), 3, B("soul_lantern", hanging=1))
                    break
        self.add_zone("c6", self.zbox("c6"), floor_mask=self.carved)

    # ------------------------------------------------------------ boss: Hati's hill under the moon
    def moon_hill(self):
        a, rng = self.a, self.rng
        L = self.L
        cx, cz = L(54, 22)
        y = int(self.H[54, 22]) + 1
        R = 16

        def floor_fn(x, z, d):
            if d > R - 1.2:
                return B("polished_andesite")
            n = (x * 7 + z * 13) % 11
            return B("stone") if n < 5 else B("andesite") if n < 8 else B("cobblestone") if n < 10 else B("mossy_cobblestone")
        ar = self.arena("boss", cx, y, cz, R, "hati", "final", floor_fn=floor_fn)
        # ring of standing stones (leave the north-east open for the path)
        for k in range(14):
            ang = k / 14 * 2 * math.pi
            x, z = int(round(cx + math.cos(ang) * (R + 2))), int(round(cz + math.sin(ang) * (R + 2)))
            if self.carved[x - self.x0, z - self.z0] and math.cos(ang) > 0.3 and math.sin(ang) > -0.2:
                continue
            P.runestone(a, x, y, z, rng, h=rng.randint(5, 8), mat="dark", glow=True)
        # the moon: a pale disc hanging in the northern sky
        mx, my, mz = cx, y + 44, cz - 46
        Rm = 15
        for dx in range(-Rm, Rm + 1):
            for dy in range(-Rm, Rm + 1):
                d = math.hypot(dx, dy)
                if d <= Rm:
                    crater = ((dx * 3 + dy * 7) % 13 == 0) or (math.hypot(dx - 5, dy - 3) < 3) or (math.hypot(dx + 6, dy + 5) < 2.5)
                    a.set(mx + dx, my + dy, mz, B("light_gray_concrete") if crater else B("white_concrete"))
                    if d > Rm - 1.2:
                        a.set(mx + dx, my + dy, mz + 1, B("pearlescent_froglight"))
        # exit portal in an alcove cut into the valley wall west of the arena; the gate stands in its mouth
        lz_ex = 22
        mx = 54 - R - 1
        while mx > 16 and self.carved[mx, lz_ex - 6:lz_ex + 7].any():
            mx -= 1
        ey = y
        # a short corridor from the valley to the gate, then the gate in solid rock, then the alcove
        for lx in range(mx + 1, 54 - R + 1):
            for lz in range(lz_ex - 1, lz_ex + 2):
                xx, zz = L(lx, lz)
                a.set(xx, ey - 1, zz, B("stone"))
                for yy in range(ey, ey + 4):
                    a.set(xx, yy, zz, AIR)
        mx_w, ez = L(mx, lz_ex)
        for xx in range(mx_w - 11, mx_w + 1):
            for zz in range(ez - 4, ez + 5):
                inner = xx < mx_w - 1 or abs(zz - ez) <= 1
                if not inner:
                    continue
                a.set(xx, ey - 1, zz, B("stone"))
                for yy in range(ey, ey + 6):
                    a.set(xx, yy, zz, AIR)
        for yy in range(ey - 1, ey + 1):
            for zz in range(ez - 1, ez + 2):
                a.set(mx_w + 1, yy, zz, B("stone") if yy < ey else AIR)
        self.exit_portal(mx_w - 6, ey, ez)
        ar["exit"] = [list(p) for p in self.doorway(mx_w, ey, ez, 3, 3, "z")]
        for yy in range(ey + 3, ey + 6):
            for zz in range(ez - 1, ez + 2):
                a.set(mx_w, yy, zz, B("cobbled_deepslate"))
        self.close([tuple(p) for p in ar["exit"]])

    def finish(self):
        a, rng = self.a, self.rng

        def tree(a_, x, y, z, r):
            if r.random() < 0.5:
                iron_tree(a_, x, y, z, r, h=r.randint(10, 16), big=False)
            else:
                spruce_tree(a_, x, y, z, r, h=r.randint(9, 14))
        self.dress_walls(self.carved, [B("stone"), B("andesite"), B("tuff"), B("cobbled_deepslate"), B("mossy_cobblestone"), B("deepslate")],
                         rim=dict(tree=tree, plants=["fern", "short_grass", "fern", "brown_mushroom"], bush=B("dark_oak_leaves", persistent_bit=1)),
                         rim_trees=0.09, moss=0.25)
        # trees across the open floors outside the paths (sparse)
        for _ in range(500):
            lx, lz = rng.randint(4, self.sx - 5), rng.randint(30, 250)
            if not self.carved[lx, lz] or self.wall_dist[lx, lz] > 0:
                continue
            x, y, z = self._at(lx, lz)
            if a.get(x, y, z) != AIR:
                continue
            q = rng.random()
            if q < 0.05:
                spruce_tree(a, x, y, z, rng, h=rng.randint(8, 12))
            elif q < 0.4:
                a.set(x, y, z, B(rng.choice(["fern", "short_grass", "fern"])))
        self.ambient = [dict(box=self.zones["c5"]["box"], particle="minecraft:white_smoke_particle", rate=2),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:spore_blossom_ambient_particle", rate=2)]
        x, y, z = self.arenas[0]["x"], self.arenas[0]["y"], self.arenas[0]["z"]
        self.light_fill((int(x) - 18, int(z) - 18, int(x) + 18, int(z) + 18), (y - 1, y + 2), level=8, threshold=5, spacing=6)
        self.boundary()
        a.fix_walls()

    def is_escape(self, x, y, z):
        i, k = x - self.x0, z - self.z0
        if self._allowed is None:
            self._allowed = binary_dilation(self.carved | self.river, iterations=4)
        if self._allowed[i, k]:
            return False
        return all(self.a.get(x, yy, z) == AIR for yy in range(y + 2, y + 10))

    _allowed = None


def build(seed=1):
    d = IronWood("d02", seed)
    d.build()
    return d


if __name__ == "__main__":
    import sys, time
    import render
    t0 = time.time()
    d = build()
    print("built %.1fs" % (time.time() - t0))
    render.topdown(d.a, sys.argv[1], scale=2)
