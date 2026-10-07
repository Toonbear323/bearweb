"""Dungeon 8 — 무스펠헤임 불꽃의 문 (Muspelheim). High tier, 272 x 448, the realm of fire.

South -> north, climbing the volcano: the ash shore of the lava sea (the return ship rides in a cooled harbour pool);
lava rivers crossed on chain bridges; the basalt forest with crimson fungi; the war camp of the Muspel host and the
obsidian keep where Muspellsson waits (mid-boss 1); the crater stairs beside lava falls; the precinct of the obsidian
temple and its sanctum, where Sinmara guards Laevateinn (mid-boss 2); the forge of the colossal burning sword; and
the crater heart, an island in a lava moat, where Surtr sits.

Every boss stands in its own walled basin; the paths in and out of a basin pass through gate walls, so a gate can
never be walked around. Local coordinates: x 0..271 (west -> east), z 0..447 (north -> south).
"""
import math

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

from mcw import B, AIR, PAL
from gen_common import fbm, stair, slab, standing_sign, line_points, boulder
import nr_parts as P
import nr_castle as C
from nr_dungeon import mixer
from nr_realm import Realm
from nr_spawn import cyl, ell, thick_line

SEA = 62


class Muspelheim(Realm):
    Y0, SY = 32, 128            # 32..159

    ZN = {
        "start": (136, 402, 102, 28, 64),
        "c1": (92, 344, 68, 22, 66),
        "c2": (182, 282, 72, 26, 70),
        "c3": (72, 226, 56, 22, 76),
        "a1": (176, 222, 22, 22, 76),
        "c4": (212, 152, 40, 38, lambda X, Z, n: 78 + np.clip((192 - Z) / 80.0, 0, 1) * 22 + (n - 0.5) * 0.8),
        "c5": (162, 92, 48, 20, 100),
        "a2": (56, 104, 22, 22, 100),
        "c6": (164, 30, 62, 16, 104),
        "boss": (42, 40, 27, 27, 98),
    }
    PATHS = [([(112, 378), (100, 362)], 9), ([(148, 338), (166, 306)], 9), ([(136, 272), (100, 236)], 9),
             ([(126, 224), (156, 222)], 9), ([(184, 206), (204, 186)], 9), ([(190, 122), (176, 104)], 9),
             ([(120, 96), (72, 103)], 9), ([(64, 88), (112, 36)], 9), ([(110, 34), (66, 38)], 9)]

    def build(self):
        rng = self.rng
        self.pal = C.Pal(rng, wall=[("polished_blackstone_bricks", 5), ("obsidian", 2), ("cracked_polished_blackstone_bricks", 1)],
                         trim="gilded_blackstone", floor=[("polished_blackstone", 3), ("blackstone", 2), ("basalt", 1)],
                         roof="red_nether_brick", pillar="crying_obsidian", window="iron_bars", light="lantern",
                         accent="magma", top="polished_blackstone_wall", plank="crimson_planks")
        self.realm_setup()
        self.terrain()
        self.shore()
        self.lava_rivers()
        self.basalt_forest()
        self.war_camp()
        self.keep()
        self.crater_stairs()
        self.temple_precinct()
        self.sanctum()
        self.sword_forge()
        self.crater_heart()
        self.finish()

    # ------------------------------------------------------------ helpers







    # ------------------------------------------------------------ terrain
    def terrain(self):
        rng = self.rng
        zones = {k: v[:5] for k, v in self.ZN.items()}
        self.valleys(zones, self.PATHS, high=(104, 12), wall_extra=14, rough=0.15, margin=6)
        self.H = np.minimum(self.H, self.Y0 + self.SY - 8)
        top = mixer(rng, [(B("blackstone"), 4), (B("basalt", pillar_axis="y"), 2), (B("smooth_basalt"), 1), (B("netherrack"), 1)])
        sub = mixer(rng, [(B("blackstone"), 3), (B("basalt", pillar_axis="y"), 1)])
        rock = [B("basalt", pillar_axis="y"), B("blackstone"), B("smooth_basalt"), B("basalt", pillar_axis="y"), B("tuff"), B("blackstone")]
        self.paint_valley(top, sub, rock, deep=B("blackstone"), slope_rock=1.0)
        a = self.a
        X, Z = self.X - self.x0, self.Z - self.z0
        self.gate_spots = [(148, 223), (194, 196), (90, 100), (84, 66), (80, 37)]
        # magma veins down the cliff faces
        n = fbm(self.sx, self.sz, 6, 2, self.seed + 9)
        for (i, k) in np.argwhere(~self.carved & (self.wall_dist < 4)):
            if n[i, k] > 0.68:
                h = int(self.H[i, k])
                for y in range(int(self.near_floor[i, k]) + 2, h - 1):
                    j = y - self.Y0
                    if a.blk[i, j, k] != AIR and rng.random() < 0.7:
                        a.blk[i, j, k] = B("magma")
        a.bio[:, :] = 181
        a.bio[:, 250:320] = 179

    # ------------------------------------------------------------ start: the ash shore
    def shore(self):
        a, rng = self.a, self.rng
        m = self.masks["start"]
        sea = [(i, k) for (i, k) in np.argwhere(m) if math.hypot((i - 136) / 96.0, (k - 432) / 18.0) < 1]
        self.lava_cells(sea, depth=3)
        # the cooled harbour: a water pool walled in basalt where the return ship rides
        hx1, hz1, hx2, hz2 = 150, 392, 186, 408
        for lx in range(hx1, hx2 + 1):
            for lz in range(hz1, hz2 + 1):
                x, z = self.w(lx, lz)
                edge = lx in (hx1, hx2) or lz in (hz1, hz2)
                if edge:
                    for y in range(SEA - 6, SEA + 2):
                        a.set(x, y, z, B("polished_basalt", pillar_axis="y"))
                    a.set(x, SEA + 2, z, B("polished_blackstone_wall"))
                else:
                    for y in range(SEA - 6, SEA + 1):
                        a.set(x, y, z, B("water"))
                    a.set(x, SEA - 7, z, B("obsidian"))
                    for y in range(SEA + 1, SEA + 6):
                        a.set(x, y, z, AIR)
                self.blocked[lx, lz] = True
        sx, sz = self.w(182, 400)
        info = P.longship(a, sx, SEA, sz, "west", rng, length=29, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        # jetty on the pool's north side
        for lx in range(156, 160):
            for lz in range(386, 397):
                x, z = self.w(lx, lz)
                a.set(x, SEA + 1, z, B("crimson_planks"))
                for y in range(SEA + 2, SEA + 6):
                    a.set(x, y, z, AIR)
                self.blocked[lx, lz] = False
        for lz in range(386, 392):
            for lx in range(156, 160):
                x, z = self.w(lx, lz)
                for y in range(SEA - 2, SEA + 1):
                    a.set(x, y, z, B("blackstone"))
        for lx in (156, 159):
            x, z = self.w(lx, 392)
            a.set(x, SEA + 2, z, AIR)
        ax, az = self.w(158, 386)
        self.data["start"] = [ax + 0.5, SEA + 2, az + 0.5, 180]
        self.walk_seeds = [(ax, SEA + 2, az)]
        standing_sign(a, ax - 3, SEA + 2, az - 1, 8, "§l§c무스펠헤임 불꽃의 문\n§r§f세계를 태울\n§f불의 나라\n§7용암에 빠지지 마세요", kind="crimson_standing_sign")
        # obsidian spires and ash heaps on the shore
        for _ in range(30):
            lx, lz = rng.randint(40, 232), rng.randint(378, 420)
            if not self.free(lx, lz) or (140 <= lx <= 196 and 380 <= lz <= 412):
                continue
            x, y, z = self._at(lx, lz)
            r = rng.random()
            if r < 0.3:
                h = rng.randint(5, 14)
                for k in range(h):
                    rr = max(0, 1.6 - k * 0.15)
                    for dx in range(-2, 3):
                        for dz in range(-2, 3):
                            if math.hypot(dx, dz) <= rr:
                                a.set(x + dx, y + k, z + dz, B("obsidian") if k % 4 else B("crying_obsidian"))
            elif r < 0.6:
                boulder(a, x, y, z, rng, rng.uniform(1.2, 2.4), [B("basalt"), B("blackstone"), B("magma")])
            else:
                a.set(x, y - 1, z, B("netherrack"))
                a.set(x, y, z, B("fire"))
        self.allow(30, 370, 242, 440, 54, 72)


    # ------------------------------------------------------------ c1: lava rivers and chain bridges
    def lava_rivers(self):
        a, rng = self.a, self.rng
        m = self.masks["c1"]
        bridges = []
        for (zc, amp, xs) in ((334, 3, (60, 120)), (354, 2, (44, 136))):
            cells = []
            for (i, k) in np.argwhere(m):
                if abs(k - (zc + math.sin(i / 9.0) * amp)) <= 2.5:
                    cells.append((i, k))
            for bx in xs:
                for (i, k) in list(cells):
                    if abs(i - bx) <= 2:
                        cells.remove((i, k))
                        bridges.append((i, k))
            for bx in xs:
                for (i, k) in cells:
                    if abs(i - bx) == 3:
                        self.no_rim.add((i, k))
            self.lava_cells(cells, depth=2)
            # bridge decks: blackstone slabs on chains, rails each side
            for bx in xs:
                for (i, k) in bridges:
                    if abs(i - bx) > 2:
                        continue
                    x, z = self.w(i, k)
                    f = int(self.H[i, k])
                    if abs(i - bx) == 2:
                        a.set(x, f + 1, z, B("polished_blackstone_wall"))
                        a.set(x, f + 2, z, B("chain"))
                        for y in range(f + 3, f + 5):
                            a.set(x, y, z, B("barrier"))
                        self.blocked[i, k] = True
                    else:
                        a.set(x, f, z, B("polished_blackstone_bricks") if (k % 3) else B("gilded_blackstone"))
                        for y in range(f - 2, f):
                            a.set(x, y, z, B("lava"))
        # chain posts at the bridge ends with braziers
        for (zc, xs) in ((334, (60, 120)), (354, (44, 136))):
            for bx in xs:
                for dz in (-4, 4):
                    lx, lz = bx - 3, int(zc + dz)
                    if self.free(lx, lz):
                        x, y, z = self._at(lx, lz)
                        P.brazier(a, x, y, z, soul=False, base="polished_blackstone")
        self.add_zone("c1", self.zbox("c1"), floor_mask=self.carved & ~self.lava & ~self.blocked)

    # ------------------------------------------------------------ c2: the basalt forest
    def huge_fungus(self, x, y, z, h, rng):
        a = self.a
        for k in range(h):
            for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)) if h > 9 else ((0, 0),):
                a.set(x + dx, y + k, z + dz, B("crimson_stem", axis="y"))
        r = 4.5 if h > 9 else 3.2
        for dy in range(0, 4):
            rr = r * (1 - dy / 5.0)
            for dx in range(-6, 7):
                for dz in range(-6, 7):
                    d = math.hypot(dx - 0.5, dz - 0.5)
                    if d <= rr and (dy > 0 or d > rr - 1.5):
                        a.set(x + dx, y + h - 1 + dy, z + dz, B("shroomlight") if rng.random() < 0.08 else B("nether_wart_block"))
        for _ in range(6):
            dx, dz = rng.randint(-4, 4), rng.randint(-4, 4)
            if math.hypot(dx, dz) < r - 0.5:
                for t in range(1, rng.randint(2, 5)):
                    a.put(x + dx, y + h - 1 - t, z + dz, B("weeping_vines"))

    def basalt_forest(self):
        a, rng = self.a, self.rng
        m = self.masks["c2"]
        nyl = mixer(rng, [(B("crimson_nylium"), 5), (B("netherrack"), 2), (B("blackstone"), 1)])
        self.patch_paint(m & ~self.lava, [(0.5, nyl), (0.7, mixer(rng, [(B("blackstone"), 2), (B("basalt", pillar_axis="y"), 1)])), (1.0, nyl)], scale=7, speckle=0.05)
        placed = []
        for _ in range(500):
            lx, lz = rng.randint(110, 254), rng.randint(258, 308)
            if not self.free(lx, lz) or any(math.hypot(lx - p[0], lz - p[1]) < 6 for p in placed):
                continue
            # keep a winding way open through the forest
            if abs(lz - (282 + math.sin(lx / 13.0) * 10)) < 4:
                continue
            x, y, z = self._at(lx, lz)
            r = rng.random()
            if r < 0.55:
                h = rng.randint(4, 22)
                rr = rng.choice([1.0, 1.5, 2.2])
                for k in range(h):
                    for dx in range(-3, 4):
                        for dz in range(-3, 4):
                            if math.hypot(dx, dz) <= rr:
                                a.set(x + dx, y + k, z + dz, B("polished_basalt", pillar_axis="y") if k < h - 1 else B("basalt", pillar_axis="y"))
                if rng.random() < 0.3:
                    a.set(x, y + h, z, B("magma"))
            else:
                self.huge_fungus(x, y, z, rng.randint(7, 14), rng)
            placed.append((lx, lz))
            if len(placed) > 70:
                break
        for _ in range(80):
            lx, lz = rng.randint(110, 254), rng.randint(258, 308)
            if self.free(lx, lz):
                x, y, z = self._at(lx, lz)
                if a.get(x, y, z) == AIR:
                    a.set(x, y, z, B(rng.choice(["crimson_roots", "crimson_fungus", "crimson_roots"])))
        self.add_zone("c2", self.zbox("c2"), floor_mask=self.carved & ~self.lava & ~self.blocked)

    # ------------------------------------------------------------ c3: the war camp of the Muspel host
    def war_camp(self):
        a, rng = self.a, self.rng
        m = self.masks["c3"]
        for _ in range(300):
            lx, lz = rng.randint(20, 128), rng.randint(206, 248)
            if not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            r = rng.random()
            if r < 0.06:
                # a war tent of red and black hides
                col = rng.choice(["red_wool", "black_wool", "orange_wool"])
                for dz in range(-2, 3):
                    for k in range(3):
                        a.put(x - 2 + k, y + k, z + dz, B(col))
                        a.put(x + 2 - k, y + k, z + dz, B(col))
                    a.put(x, y + 3, z + dz, B("crimson_slab"))
            elif r < 0.1:
                # a war banner on a blackstone pole
                for k in range(6):
                    a.set(x, y + k, z, B("polished_blackstone_wall"))
                for k in range(2, 6):
                    a.set(x + 1, y + k, z, B("red_wool") if k > 2 else B("black_wool"))
                a.set(x, y + 6, z, B("lantern"))
            elif r < 0.13:
                P.brazier(a, x, y, z, soul=False, base="polished_blackstone")
            elif r < 0.16:
                # weapon rack with skulls
                for k in range(3):
                    a.set(x + k, y, z, B("crimson_fence"))
                a.set(x + 1, y + 1, z, B("skeleton_skull", facing_direction=1))
            elif r < 0.2:
                a.set(x, y - 1, z, B("netherrack"))
                a.set(x, y, z, B("fire"))
        # a catapult pointed at the keep
        x, y, z = self._at(96, 232)
        for dx in (-2, 2):
            for dz in (-2, 2):
                a.set(x + dx, y, z + dz, B("crimson_stem", axis="y"))
            for k in range(1, 4):
                a.set(x + dx, y + k, z, B("crimson_stem", axis="y"))
        for dx in range(-2, 3):
            a.set(x + dx, y + 4, z, B("crimson_stem", axis="x"))
        for k in range(6):
            a.set(x, y + 4 + k, z - k // 2, B("stripped_crimson_stem", axis="y"))
        a.set(x, y + 9, z - 3, B("magma"))
        self.add_zone("c3", self.zbox("c3"), floor_mask=self.carved & ~self.lava & ~self.blocked)

    # ------------------------------------------------------------ mid-boss 1: the obsidian keep
    def keep(self):
        a, rng, pal = self.a, self.rng, self.pal
        f0 = self.fortify("a1", height=18, towers=6)
        entry = self.gate_wall(148, 223, "x", 9, f0, gw=7, gh=8, height=16)
        exitg = self.gate_wall(194, 196, "z", 9, int(self.H[194, 196]) + 1, gw=7, gh=8, height=16)
        cx, cz = self.w(176, 222)
        R = 17

        def floor_fn(x, z, d):
            ang = math.degrees(math.atan2(z - cz, x - cx))
            if abs(d - R + 0.6) < 0.7:
                return B("gilded_blackstone") if int(ang) % 24 < 12 else B("obsidian")
            if abs(d - 9) < 0.6:
                return B("crying_obsidian")
            if d < 2.5:
                return B("magma")
            return B("polished_blackstone_bricks") if (int(d) + (x + z) % 2) % 3 else B("obsidian")
        self.arena("c3_mid", cx, f0, cz, R, "muspellsson", "mid1", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        for t in range(8):
            ang = t / 8 * 2 * math.pi + 0.2
            lx, lz = int(round(176 + math.cos(ang) * 20)), int(round(222 + math.sin(ang) * 20))
            if self.free(lx, lz):
                x, y, z = self._at(lx, lz)
                P.brazier(a, x, y, z, soul=False, base="polished_blackstone")
        self.allow(140, 180, 210, 250, f0 - 4, f0 + 8)

    # ------------------------------------------------------------ c4: the crater stairs and lava falls

    def crater_stairs(self):
        a, rng = self.a, self.rng
        m = self.masks["c4"]
        dist = distance_transform_edt(~m)
        cand = [(i, k) for (i, k) in np.argwhere((dist > 0.5) & (dist <= 1.5) & ~self.carved)
                if self.H[i, k] - self.near_floor[i, k] >= 14]
        rng.shuffle(cand)
        falls = []
        for (i, k) in cand:
            if any(math.hypot(i - p[0], k - p[1]) < 22 for p in falls):
                continue
            for (di, dk) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= i + di < self.sx and 0 <= k + dk < self.sz and m[i + di, k + dk]:
                    self.lava_fall(i, k, di, dk)
                    falls.append((i, k))
                    break
            if len(falls) >= 5:
                break
        # steaming vents and basalt steps along the climb
        for _ in range(30):
            lx, lz = rng.randint(176, 250), rng.randint(116, 190)
            if not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            r = rng.random()
            if r < 0.3:
                a.set(x, y - 1, z, B("magma"))
                a.set(x, y - 2, z, B("soul_soil"))
            elif r < 0.5:
                boulder(a, x, y, z, rng, rng.uniform(1.0, 1.8), [B("basalt"), B("blackstone")])
        self.add_zone("c4", self.zbox("c4", dy=(-6, 26)), floor_mask=self.carved & ~self.lava & ~self.blocked)

    # ------------------------------------------------------------ c5: the temple precinct
    def temple_precinct(self):
        a, rng = self.a, self.rng
        tpal = C.Pal(rng, wall=[("crying_obsidian", 2), ("obsidian", 5), ("polished_blackstone_bricks", 2)], trim="gilded_blackstone",
                     floor=[("polished_blackstone", 3), ("obsidian", 1)], roof="red_nether_brick", pillar="crying_obsidian",
                     window="iron_bars", light="lantern", accent="magma", top="polished_blackstone_wall")
        self.tpal = tpal
        # the ziggurat on the north side of the precinct (solid; a stair climbs its face to a shrine of fire)
        cx, cy, cz = self._at(162, 76)
        for tier, (w, d, h) in enumerate(((30, 12, 6), (24, 10, 6), (18, 8, 6), (12, 6, 6))):
            y0 = cy + tier * 6
            for dx in range(-w // 2, w // 2 + 1):
                for dz in range(-d, d // 2):
                    x, z = cx + dx, cz + dz
                    for y in range(y0 - 1, y0 + h):
                        edge = abs(dx) == w // 2 or dz in (-d, d // 2 - 1)
                        a.set(x, y, z, tpal.trim if (y == y0 + h - 1 and edge) else tpal.wall())
        for k in range(4):
            a.set(cx + k - 1, cy + 24, cz - 3, B("magma"))
        ell(a, cx, cy + 27, cz - 3, 2, 3, 2, B("shroomlight"))
        a.set(cx, cy + 30, cz - 3, B("fire"))
        # obelisks with fire on top, statues of fire giants
        for lx in (124, 140, 184, 200):
            for lz in (96, 104):
                if not self.free(lx, lz):
                    continue
                x, y, z = self._at(lx, lz)
                for k in range(10):
                    for dx in range(2):
                        for dz in range(2):
                            a.set(x + dx, y + k, z + dz, B("crying_obsidian") if k % 4 == 3 else B("obsidian"))
                a.set(x, y + 10, z, B("netherrack"))
                a.set(x, y + 11, z, B("fire"))
        for lx in (132, 192):
            x, y, z = self._at(lx, 86)
            thick_line(a, (x, y, z), (x, y + 7, z), 1.4, B("blackstone"))
            ell(a, x, y + 10, z, 2.4, 2.8, 2.4, B("polished_blackstone"))
            a.set(x, y + 10, z + 2, B("shroomlight"))
            thick_line(a, (x + 2, y + 9, z), (x + 5, y + 14, z + 1), 0.8, B("magma"))
        self.add_zone("c5", self.zbox("c5"), floor_mask=self.carved & ~self.lava & ~self.blocked)

    # ------------------------------------------------------------ mid-boss 2: the sanctum of Laevateinn
    def sanctum(self):
        a, rng = self.a, self.rng
        tpal = self.tpal
        f0 = self.fortify("a2", height=18, towers=5, pal=tpal, tower_roof="pyramid")
        entry = self.gate_wall(90, 100, "x", 9, int(self.H[90, 100]) + 1, gw=7, gh=8, height=16)
        exitg = self.gate_wall(84, 66, "z", 9, int(self.H[84, 66]) + 1, gw=7, gh=8, height=16)
        cx, cz = self.w(56, 104)
        R = 17

        def floor_fn(x, z, d):
            if abs(d - R + 0.6) < 0.7:
                return B("crying_obsidian")
            if abs(d - 6) < 0.6 or abs(d - 12) < 0.5:
                return B("gilded_blackstone")
            return B("obsidian") if (x + z) % 3 else B("polished_blackstone")
        self.arena("c5_mid", cx, f0, cz, R, "sinmara", "mid2", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # Laevateinn on its altar at the west rim, out of the fight
        ax_, az_ = self.w(36, 104)
        for dx in range(-2, 3):
            for dz in range(-3, 4):
                a.set(ax_ + dx, f0 - 1, az_ + dz, B("gilded_blackstone"))
                a.set(ax_ + dx, f0, az_ + dz, B("crying_obsidian") if abs(dx) == 2 or abs(dz) == 3 else B("obsidian"))
        for k in range(1, 9):
            a.set(ax_, f0 + k, az_, B("red_nether_brick") if k < 7 else B("shroomlight"))
        for dz in (-1, 1):
            a.set(ax_, f0 + 3, az_ + dz, B("gold_block"))
        a.set(ax_, f0 + 9, az_, B("end_rod"))
        self.allow(26, 76, 92, 132, f0 - 4, f0 + 8)

    # ------------------------------------------------------------ c6: the forge of the burning sword
    def sword_forge(self):
        a, rng = self.a, self.rng
        cx, cy, cz = self._at(164, 30)
        base = cy
        # the anvil
        for dx in range(-9, 10):
            for dz in range(-4, 5):
                for dy in range(0, 8):
                    w = 2 if dy < 3 else 3 if dy < 5 else 4
                    if abs(dz) <= w and (dy >= 5 or abs(dx) <= 6):
                        a.set(cx + dx, base + dy, cz + dz, B("polished_blackstone") if dy < 5 else B("iron_block"))
        # the colossal sword lying across it: a broad blade with a glowing fuller and flames along both edges,
        # a gilded guard with upswept quillons, a wrapped grip and a burning pommel
        y = base + 8
        tip, guard = 116, 194
        for lx in range(tip, guard):
            x = self.x0 + lx
            t = (lx - tip) / float(guard - tip)
            half = 4 if t > 0.16 else max(0, int(round(4 * t / 0.16)))
            for dz in range(-half, half + 1):
                z = cz + dz
                edge = abs(dz) == half
                a.set(x, y, z, B("magma") if edge else B("red_nether_brick"))
                a.set(x, y + 1, z, B("magma") if edge else (B("orange_stained_glass") if dz == 0 else B("shroomlight")))
                if edge and half >= 2 and lx % 3 == 0:
                    a.set(x, y + 1, z, B("netherrack"))
                    a.set(x, y + 2, z, B("fire"))
            if half >= 2 and lx % 4 == 0:
                a.set(x, y + 2, cz, B("magma"))
        for lx in range(guard, guard + 3):
            x = self.x0 + lx
            for dz in range(-9, 10):
                curl = 1 if abs(dz) >= 8 else 0
                for yy in range(y - 1, y + 3 + curl):
                    a.set(x, yy, cz + dz, B("gold_block") if abs(dz) in (0, 9) else B("gilded_blackstone"))
        for lx in range(guard + 3, guard + 15):
            x = self.x0 + lx
            for dz in (-1, 0, 1):
                for yy in (y, y + 1):
                    a.set(x, yy, cz + dz, B("red_wool") if (lx + yy) % 3 == 0 else B("polished_blackstone"))
        px = self.x0 + guard + 17
        ell(a, px, y + 0.5, cz, 2.5, 2.2, 2.5, B("gold_block"))
        a.set(px, y + 1, cz, B("shroomlight"))
        a.set(px + 2, y + 1, cz, B("magma"))
        # supports under the blade, lava troughs, a giant hammer
        for lx in (128, 148, 182, 202):
            x = self.x0 + lx
            for dz in (-2, 2):
                for yy in range(base, y):
                    a.set(x, yy, cz + dz, B("polished_blackstone_wall"))
        trough = []
        for lx in range(128, 200):
            for lz in (22, 23, 37, 38):
                if self.carved[lx, lz]:
                    trough.append((lx, lz))
        self.lava_cells(trough, depth=1)
        hx, hy, hz = self._at(140, 40)
        thick_line(a, (hx, hy, hz), (hx + 12, hy + 2, hz - 1), 0.9, B("stripped_crimson_stem", axis="x"))
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for dy in range(0, 4):
                    a.set(hx - 3 + dx, hy + dy, hz + dz, B("iron_block") if abs(dx) < 2 else B("polished_blackstone"))
        self.add_zone("c6", self.zbox("c6"), floor_mask=self.carved & ~self.lava & ~self.blocked)

    # ------------------------------------------------------------ boss: the crater heart
    def crater_heart(self):
        a, rng, pal = self.a, self.rng, self.pal
        lcx, lcz = 42, 40
        R = 23
        f0 = int(np.median(self.H[self.masks["boss"]]))
        y = f0 + 1
        cx, cz = self.w(lcx, lcz)
        entry = self.gate_wall(80, 37, "x", 9, int(self.H[80, 37]) + 1, gw=7, gh=8, height=16)

        def floor_fn(x, z, d):
            ang = math.atan2(z - cz, x - cx)
            crack = abs(math.sin(ang * 7 + d * 0.3)) < 0.07 and 4 < d < R - 2
            if d > R - 1.3:
                return B("obsidian")
            if crack:
                return B("magma")
            if d < 4:
                return B("crying_obsidian") if d < 2 else B("gilded_blackstone")
            return B("blackstone") if (int(d) + (x + z) % 3) % 4 else B("basalt", pillar_axis="y")
        ar = self.arena("boss", cx, y, cz, R, "surtr", "final", floor_fn=floor_fn, entry=entry)
        for (i, k) in np.argwhere(self.masks["boss"]):
            if math.hypot(i - lcx, k - lcz) <= R + 0.5:
                self.H[i, k] = y - 1
        # bridges: entry from the east, exit to the north
        bridge_e = [(i, k) for i in range(lcx + R - 1, lcx + R + 12) for k in range(lcz - 3, lcz + 4)]
        bridge_n = [(i, k) for i in range(lcx - 3, lcx + 4) for k in range(10, lcz - R + 2)]
        for (i, k) in bridge_e + bridge_n:
            if 0 <= i < self.sx and 0 <= k < self.sz:
                self.carved[i, k] = True
                x, z = self.w(i, k)
                a.set(x, y - 1, z, pal.floor())
                for yy in range(y, y + 8):
                    a.set(x, yy, z, AIR)
                self.H[i, k] = y - 1
        walk_e = {(i, k) for (i, k) in bridge_e if abs(k - lcz) <= 2}
        walk_n = {(i, k) for (i, k) in bridge_n if abs(i - lcx) <= 2}
        self.no_rim |= walk_e | walk_n
        # the alcove with the portal beyond the north bridge
        alcove = [(i, k) for i in range(lcx - 8, lcx + 9) for k in range(6, 13)]
        for (i, k) in alcove:
            self.carved[i, k] = True
            x, z = self.w(i, k)
            a.set(x, y - 1, z, pal.floor())
            for yy in range(y, y + 9):
                a.set(x, yy, z, AIR)
            self.H[i, k] = y - 1
        self.no_rim |= set(alcove)
        moat = [(i, k) for (i, k) in np.argwhere(self.masks["boss"]) if math.hypot(i - lcx, k - lcz) > R + 0.5
                and (i, k) not in set(bridge_e) | set(bridge_n) | set(alcove)]
        self.lava_cells(moat, depth=3)
        # the arena edge next to the moat gets a rim too (lava_cells rims every floor cell touching lava)
        exitg = self.doorway(cx, y, self.z0 + 13, 5, 6, "x")
        for t in range(-4, 5):
            x, z = self.w(lcx + t, 13)
            for yy in range(y, y + 10):
                if abs(t) > 2 or yy >= y + 6:
                    a.set(x, yy, z, pal.wall() if yy < y + 9 else pal.trim)
        ar["exit"] = [list(p) for p in exitg]
        self.close(exitg)
        self.exit_portal(cx, y, self.z0 + 9)
        # Surtr's seat of basalt on the west rim, looking over the lava
        sx_, sz_ = self.w(lcx - R - 1, lcz)
        for dz in range(-4, 5):
            for yy in range(y, y + 14):
                a.set(sx_, yy, sz_ + dz, B("basalt", pillar_axis="y") if abs(dz) == 4 or yy > y + 10 else B("blackstone"))
        self.allow(4, 4, 96, 76, y - 4, y + 8)

    # ------------------------------------------------------------ finishing
    def finish(self):
        a, rng = self.a, self.rng
        self.dress_walls(self.carved, [B("blackstone"), B("basalt", pillar_axis="y"), B("blackstone"), B("smooth_basalt"),
                                       B("netherrack"), B("blackstone"), B("magma")],
                         moss=0.0, vines=0.0, rim=None, lichen=0.0)
        for key, n in (("c1", 3), ("c2", 2), ("c3", 3), ("c5", 2), ("c6", 4)):
            m = self.masks[key]
            dist = distance_transform_edt(~m)
            cand = [(i, k) for (i, k) in np.argwhere((dist > 0.5) & (dist <= 1.5) & ~self.carved)
                    if self.H[i, k] - self.near_floor[i, k] >= 14]
            rng.shuffle(cand)
            done = []
            for (i, k) in cand:
                if any(math.hypot(i - p[0], k - p[1]) < 26 for p in done):
                    continue
                if any(math.hypot(i - gx, k - gz) < 14 for (gx, gz) in self.gate_spots):
                    continue
                for (di, dk) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ii, kk = i + di, k + dk
                    if 0 <= ii < self.sx and 0 <= kk < self.sz and m[ii, kk] and not self.lava[ii, kk] and not self.blocked[ii, kk]:
                        self.lava_fall(i, k, di, dk)
                        done.append((i, k))
                        break
                if len(done) >= n:
                    break
        self.ambient = [dict(box=self.zones["c2"]["box"], particle="minecraft:crimson_spore_particle", rate=3),
                        dict(box=self.zones["c4"]["box"], particle="minecraft:lava_particle", rate=2),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:basic_flame_particle", rate=3),
                        dict(box=self.zones["c1"]["box"], particle="minecraft:lava_particle", rate=2)]
        for key in ("c1", "c2", "c3", "c4", "c5", "c6"):
            bx1, by1, bz1, bx2, by2, bz2 = self.zones[key]["box"]
            self.light_fill((bx1, bz1, bx2, bz2), (by1, by2), level=8, threshold=4, spacing=8)
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        a.fix_walls()


def build(seed=1):
    d = Muspelheim("d08", seed)
    d.build()
    return d
