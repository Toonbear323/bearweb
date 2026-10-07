"""Dungeon 9 — 헬헤임 걀라르 다리 (Helheim). High tier, 272 x 448, the realm of the dead.

South -> north: the grey Hel-way with its dark river landing; the thorn forest of dead trees and sculk; the bank of
the Gjoll where ice floes carry blades; the gold-roofed bridge Gjallarbru over the abyss, its round middle pier the
ring where Modgud keeps the way (mid-boss 1); Helgrind, the gate of bones; the cave of Gnipa and Garm's chained den
(mid-boss 2); Nastrond, the corpse shore under arches of serpent spines with the bones of Nidhogg; and Eljudnir, Hel's
hall, half alive and half dead.

Local coordinates: x 0..271 (west -> east), z 0..447 (north -> south).
"""
import math

import numpy as np
from scipy.ndimage import distance_transform_edt

from mcw import B, AIR, PAL
from gen_common import fbm, stair, slab, standing_sign, line_points, boulder
import nr_parts as P
import nr_castle as C
from nr_dungeon import mixer
from nr_realm import Realm
from nr_spawn import cyl, ell, thick_line

SEA = 62
RIM = 66                     # feet level on the gorge rims and the bridge
GZ1, GZ2 = 196, 270          # the abyss of the Gjoll, z range
RIVER = 45                   # water surface in the abyss
BX = 154                     # bridge centre line x
PZ = 232                     # the round pier (Modgud's ring) centre z


class Helheim(Realm):
    Y0, SY = 16, 128            # 16..143

    ZN = {
        "start": (136, 404, 100, 28, 64),
        "c1": (96, 344, 66, 20, 65),
        "c2": (176, 292, 72, 18, 66),
        "c4": (136, 168, 88, 18, 65),
        "c5": (66, 114, 48, 18, 62),
        "a2": (46, 46, 22, 22, 60),
        "c6": (172, 40, 70, 22, 60),
        "boss": (212, 112, 27, 27, 62),
    }
    PATHS = [([(112, 380), (100, 360)], 9), ([(146, 340), (166, 304)], 9), ([(154, 286), (154, 266)], 11),
             ([(154, 200), (150, 178)], 11), ([(80, 160), (70, 124)], 9), ([(50, 104), (46, 60)], 9),
             ([(58, 40), (116, 36)], 9), ([(206, 54), (210, 96)], 9)]

    def build(self):
        rng = self.rng
        self.realm_setup()
        self.dead = C.Pal(rng, wall=[("deepslate_bricks", 5), ("cracked_deepslate_bricks", 2), ("deepslate_tiles", 1)], trim="bone_block",
                          floor=[("deepslate_tiles", 3), ("polished_deepslate", 2), ("sculk", 1)], roof="deepslate_tile",
                          pillar="bone_block", window="iron_bars", light="soul_lantern", accent="chiseled_deepslate",
                          top="deepslate_brick_wall", plank="dark_oak_planks")
        self.live = C.Pal(rng, wall=[("stone_bricks", 4), ("mossy_stone_bricks", 3), ("moss_block", 1)], trim="gold_block",
                          floor=[("moss_block", 3), ("grass_block", 2), ("mossy_cobblestone", 1)], roof="stone_brick",
                          pillar="stripped_birch_log", window="glass_pane", light="lantern", accent="azalea_leaves_flowered",
                          top="mossy_stone_brick_wall")
        self.pal = self.dead
        self.gate_spots = [(BX, 249), (BX, 215), (48, 82), (84, 38), (208, 74)]
        self.terrain()
        self.helveg()
        self.thorn_forest()
        self.riverbank()
        self.abyss()
        self.gjallarbru()
        self.helgrind()
        self.gnipa()
        self.garm_den()
        self.nastrond()
        self.eljudnir()
        self.finish()

    # ------------------------------------------------------------ terrain
    def terrain(self):
        rng = self.rng
        zones = {k: v[:5] for k, v in self.ZN.items()}
        self.valleys(zones, self.PATHS, high=(98, 12), wall_extra=14, rough=0.1, margin=6)
        self.H = np.minimum(self.H, self.Y0 + self.SY - 8)
        top = mixer(rng, [(B("soul_soil"), 3), (B("gravel"), 2), (B("coarse_dirt"), 2), (B("mud"), 1), (B("podzol"), 1)])
        sub = mixer(rng, [(B("dirt"), 3), (B("soul_soil"), 1)])
        rock = [B("deepslate"), B("tuff"), B("deepslate"), B("cobbled_deepslate"), B("andesite"), B("deepslate")]
        self.paint_valley(top, sub, rock, deep=B("deepslate"), slope_rock=1.0)
        grey = mixer(rng, [(B("soul_soil"), 3), (B("gravel"), 2), (B("light_gray_concrete_powder"), 1)])
        dirt = mixer(rng, [(B("coarse_dirt"), 3), (B("mud"), 1), (B("podzol"), 1)])
        stone = mixer(rng, [(B("cobbled_deepslate"), 2), (B("tuff"), 2), (B("deepslate_tiles"), 1)])
        a = self.a
        # the bridge heads: the paths to the abyss lie at rim height
        for (x1, z1, x2, z2, f) in ((143, 262, 165, 292, RIM - 1), (141, 174, 165, 206, RIM - 2)):
            for i in range(x1, x2 + 1):
                for k in range(z1, z2 + 1):
                    if not self.carved[i, k] or self.H[i, k] <= f:
                        continue
                    col = a.blk[i, :, k]
                    col[f + 1 - self.Y0:int(self.H[i, k]) + 1] = AIR
                    col[f - self.Y0] = B("gravel")
                    self.H[i, k] = f
        self.patch_paint(self.carved, [(0.4, grey), (0.62, dirt), (0.8, stone), (1.0, grey)], scale=7, speckle=0.06)
        a.bio[:, :] = 178                 # soul sand valley
        a.bio[:, :200] = 190              # deep dark beyond the abyss

    # ------------------------------------------------------------ start: the Hel-way
    def helveg(self):
        a, rng = self.a, self.rng
        m = self.masks["start"]
        # a dark river along the south of the landing, the return ship on it
        river = [(i, k) for (i, k) in np.argwhere(m) if math.hypot((i - 136) / 96.0, (k - 430) / 14.0) < 1]
        for (i, k) in river:
            x, z = self.w(i, k)
            f = int(self.H[i, k])
            depth = 5
            for y in range(SEA - depth + 1, SEA + 1):
                a.set(x, y, z, B("water"))
            for y in range(SEA + 1, f + 3):
                a.set(x, y, z, AIR)
            a.set(x, SEA - depth, z, B("black_concrete") if (i + k) % 3 else B("mud"))
            self.H[i, k] = SEA - depth
        for lz in range(406, 424):
            for lx in (135, 136, 137):
                x, z = self.w(lx, lz)
                a.set(x, SEA + 1, z, B("dark_oak_planks"))
                for y in range(SEA + 2, SEA + 6):
                    a.set(x, y, z, AIR)
                if lx != 136 and lz % 4 == 0:
                    for y in range(SEA - 6, SEA + 1):
                        if a.get(x, y, z) in (B("water"), AIR):
                            a.set(x, y, z, B("dark_oak_log", axis="y"))
                    a.set(x, SEA + 2, z, B("dark_oak_fence"))
                    if lz % 8 == 0:
                        a.set(x, SEA + 3, z, B("soul_lantern"))
        sx, sz = self.w(118, 428)
        info = P.longship(a, sx, SEA, sz, "east", rng, length=29, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        ax, az = self.w(136, 404)
        ay = int(self.H[136, 404]) + 1
        self.data["start"] = [ax + 0.5, ay, az + 0.5, 180]
        self.walk_seeds = [(ax, ay, az)]
        standing_sign(a, ax + 3, ay, az - 2, 8, "§l§3헬헤임 걀라르 다리\n§r§f죽은 자들의 길\n§7안개 속 등불을 따라가세요", kind="dark_oak_standing_sign")
        # the road north lined with soul lanterns, gravestones in the grey grass
        for t in range(60):
            lz = 404 - t * 0.5
            lx = 136 - (136 - 112) * min(1.0, t / 50.0)
            for dx in range(-2, 3):
                i, k = int(lx + dx), int(lz)
                if self.free(i, k):
                    x, z = self.w(i, k)
                    a.set(x, int(self.H[i, k]), z, B("gravel") if rng.random() < 0.7 else B("packed_mud"))
        for t in range(0, 60, 8):
            for side in (-4, 4):
                lz = int(404 - t * 0.5)
                lx = int(136 - (136 - 112) * min(1.0, t / 50.0)) + side
                if self.free(lx, lz):
                    x, y, z = self._at(lx, lz)
                    for k in range(3):
                        a.set(x, y + k, z, B("deepslate_brick_wall"))
                    a.set(x, y + 3, z, B("soul_lantern"))
        self.graves(m, 40, 380, 230, 418)
        self.allow(30, 372, 242, 440, 54, 74)

    def graves(self, m, lx1, lz1, lx2, lz2, n=30):
        a, rng = self.a, self.rng
        for _ in range(n * 4):
            lx, lz = rng.randint(lx1, lx2), rng.randint(lz1, lz2)
            if not self.free(lx, lz) or not m[lx, lz]:
                continue
            x, y, z = self._at(lx, lz)
            if a.get(x, y, z) != AIR:
                continue
            r = rng.random()
            if r < 0.4:
                a.set(x, y, z, B("andesite_wall") if rng.random() < 0.5 else B("cobbled_deepslate_wall"))
                a.set(x, y + 1, z, B("polished_andesite_slab") if rng.random() < 0.5 else AIR)
            elif r < 0.6:
                a.set(x, y, z, B("deadbush"))
            elif r < 0.7:
                a.set(x, y, z, B("bone_block", axis=rng.choice(["x", "z"])))
            elif r < 0.8:
                a.set(x, y, z, B("web"))
            n -= 1
            if n <= 0:
                break

    # ------------------------------------------------------------ c1: the thorn forest
    def dead_tree(self, x, y, z, h, rng):
        a = self.a
        log = rng.choice([B("stripped_dark_oak_log", axis="y"), B("stripped_mangrove_log", axis="y"), B("dark_oak_log", axis="y")])
        top = (x + rng.uniform(-2, 2), y + h, z + rng.uniform(-2, 2))
        thick_line(a, (x, y - 1, z), top, 0.7 if h < 12 else 1.1, log)
        for _ in range(rng.randint(3, 6)):
            t = rng.uniform(0.4, 0.95)
            base = (x + (top[0] - x) * t, y + h * t, z + (top[2] - z) * t)
            ang = rng.uniform(0, 6.28)
            L = rng.uniform(3, 7)
            tip = (base[0] + math.cos(ang) * L, base[1] + rng.uniform(1, 4), base[2] + math.sin(ang) * L)
            thick_line(a, base, tip, 0.5, log)
            if rng.random() < 0.4:
                for k in range(1, rng.randint(3, 6)):
                    a.put(int(tip[0]), int(tip[1]) - k, int(tip[2]), B("chain") if k < 4 else B("soul_lantern", hanging=1))

    def thorns(self, x, y, z, rng):
        a = self.a
        for _ in range(rng.randint(3, 7)):
            dx, dz = rng.randint(-2, 2), rng.randint(-2, 2)
            n = rng.randint(1, 4)
            a.put(x + dx, y - 1, z + dz, B("dripstone_block"))
            for t in range(n):
                th = "tip" if t == n - 1 else "frustum" if t == n - 2 else "middle"
                a.put(x + dx, y + t, z + dz, B("pointed_dripstone", dripstone_thickness=th, hanging=0))

    def thorn_forest(self):
        a, rng = self.a, self.rng
        m = self.masks["c1"]
        sculk = [c for c in np.argwhere(m) if rng.random() < 0.08]
        for (i, k) in sculk:
            x, z = self.w(i, k)
            a.set(x, int(self.H[i, k]), z, B("sculk"))
        placed = []
        for _ in range(600):
            lx, lz = rng.randint(30, 162), rng.randint(326, 364)
            if not self.free(lx, lz) or any(math.hypot(lx - p[0], lz - p[1]) < 7 for p in placed):
                continue
            if abs(lz - (344 + math.sin(lx / 11.0) * 6)) < 3:
                continue
            x, y, z = self._at(lx, lz)
            if rng.random() < 0.6:
                self.dead_tree(x, y, z, rng.randint(7, 16), rng)
            else:
                self.thorns(x, y, z, rng)
            placed.append((lx, lz))
            if len(placed) > 60:
                break
        for _ in range(60):
            lx, lz = rng.randint(30, 162), rng.randint(326, 364)
            if self.free(lx, lz):
                x, y, z = self._at(lx, lz)
                if a.get(x, y, z) == AIR:
                    a.set(x, y, z, B(rng.choice(["sculk_vein", "deadbush", "web", "sculk_sensor"])) if rng.random() < 0.5 else B("deadbush"))
        self.add_zone("c1", self.zbox("c1"), floor_mask=self.carved & ~self.blocked)

    # ------------------------------------------------------------ c2: the bank of the Gjoll
    def riverbank(self):
        a, rng = self.a, self.rng
        m = self.masks["c2"]
        for _ in range(26):
            lx, lz = rng.randint(110, 244), rng.randint(276, 308)
            if not self.free(lx, lz) or abs(lx - BX) < 10:
                continue
            x, y, z = self._at(lx, lz)
            r = rng.random()
            if r < 0.5:
                # a block of blade ice: packed ice with swords frozen in it
                for dx in range(-1, 2):
                    for dz in range(-1, 2):
                        for dy in range(rng.randint(1, 3)):
                            a.put(x + dx, y + dy, z + dz, B("packed_ice") if rng.random() < 0.7 else B("blue_ice"))
                for _ in range(3):
                    a.put(x + rng.randint(-1, 1), y + 3, z + rng.randint(-1, 1), B("iron_bars"))
            elif r < 0.75:
                # a frozen warrior
                for k in range(3):
                    a.set(x, y + k, z, B("light_gray_terracotta") if k < 2 else B("packed_ice"))
                a.set(x + 1, y + 1, z, B("iron_bars"))
            else:
                self.thorns(x, y, z, rng)
        self.add_zone("c2", self.zbox("c2"), floor_mask=self.carved & ~self.blocked)

    # ------------------------------------------------------------ the abyss of the Gjoll
    def abyss(self):
        a, rng = self.a, self.rng
        for i in range(6, self.sx - 6):
            for k in range(GZ1, GZ2 + 1):
                col = a.blk[i, :, k]
                col[RIVER - 10 - self.Y0 + 1:] = AIR
                for y in range(RIVER - 9, RIVER + 1):
                    col[y - self.Y0] = B("water")
                col[RIVER - 10 - self.Y0] = B("gravel") if (i + k) % 3 else B("mud")
                self.carved[i, k] = False
                self.H[i, k] = RIVER - 10
        # the abyss walls: deepslate with bone and sculk streaks, soul lanterns low down
        for i in range(6, self.sx - 6):
            for k in (GZ1 - 1, GZ2 + 1):
                x, z = self.w(i, k)
                for y in range(RIVER - 9, RIM + 30):
                    b = a.get(x, y, z)
                    if b == AIR:
                        continue
                    r = rng.random()
                    if r < 0.08:
                        a.set(x, y, z, B("sculk"))
                    elif r < 0.12:
                        a.set(x, y, z, B("bone_block", axis="y"))
        # ice floes carrying blades on the river
        for _ in range(40):
            lx, lz = rng.randint(10, self.sx - 11), rng.randint(GZ1 + 3, GZ2 - 3)
            if abs(lx - BX) < 26:
                continue
            x, z = self.w(lx, lz)
            w, d = rng.randint(1, 3), rng.randint(1, 2)
            for dx in range(-w, w + 1):
                for dz in range(-d, d + 1):
                    a.set(x + dx, RIVER, z + dz, B("packed_ice") if rng.random() < 0.7 else B("blue_ice"))
            for _ in range(rng.randint(1, 3)):
                for k in range(1, rng.randint(2, 4)):
                    a.set(x + rng.randint(-w, w), RIVER + k, z + rng.randint(-d, d), B("iron_bars"))
        # ladders up the south wall into the riverbank (the only way out of the river)
        for lx in (124, 182, 222):
            x, z = self.w(lx, GZ2)
            for y in range(RIVER - 2, RIM):
                a.set(x, y, z, B("ladder", facing_direction=2))
                a.wet[x - self.x0, y - self.Y0, z - self.z0] = y <= RIVER
            for lz in range(GZ2 + 1, GZ2 + 5):
                xx, zz = self.w(lx, lz)
                for dx in (-1, 0, 1):
                    a.set(xx + dx, RIM - 1, zz, B("deepslate_tiles"))
                    for y in range(RIM, RIM + 3):
                        a.set(xx + dx, y, zz, AIR)
                    self.carved[lx + dx, lz] = True
                    self.H[lx + dx, lz] = RIM - 1
        self.allow(6, GZ1 - 2, self.sx - 6, GZ2 + 6, RIVER - 12, RIM + 8)

    # ------------------------------------------------------------ c3 and mid-boss 1: Gjallarbru
    def gjallarbru(self):
        a, rng, pal = self.a, self.rng, self.dead
        deck = RIM - 1
        # Modgud's ring: a round pier rising out of the river
        PR = 19
        for lx in range(BX - PR - 1, BX + PR + 2):
            for lz in range(PZ - PR - 1, PZ + PR + 2):
                d = math.hypot(lx - BX, lz - PZ)
                if d > PR + 0.4:
                    continue
                x, z = self.w(lx, lz)
                for y in range(RIVER - 10, deck + 1):
                    band = (y - RIVER) % 7 == 0
                    a.set(x, y, z, B("gold_block") if band and d > PR - 1 else pal.wall())
                self.carved[lx, lz] = True
                self.H[lx, lz] = deck
        # bridge decks north and south of the ring, piers into the river, rails with invisible caps
        segs = [(GZ1 - 4, PZ - PR + 1), (PZ + PR - 1, GZ2 + 4)]
        for (z1, z2) in segs:
            for lz in range(z1, z2 + 1):
                for lx in range(BX - 7, BX + 8):
                    x, z = self.w(lx, lz)
                    a.set(x, deck, z, B("polished_deepslate") if abs(lx - BX) < 6 else pal.wall())
                    a.set(x, deck - 1, z, pal.wall())
                    for y in range(deck + 1, deck + 6):
                        a.set(x, y, z, AIR)
                    self.carved[lx, lz] = True
                    self.H[lx, lz] = deck
                    if abs(lx - BX) == 7:
                        a.set(x, deck + 1, z, B("deepslate_brick_wall"))
                        for y in range(deck + 2, deck + 5):
                            a.set(x, y, z, B("barrier"))
                if lz % 12 == 0 and GZ1 <= lz <= GZ2:
                    for lx in range(BX - 6, BX + 7):
                        x, z = self.w(lx, lz)
                        for y in range(RIVER - 10, deck - 1):
                            arch = abs(lx - BX) < 4 and y < deck - 4 - int(abs(lx - BX) * 0.6) and y > RIVER
                            if not arch:
                                a.set(x, y, z, pal.wall())
        # rails around the ring's edge
        for lx in range(BX - PR - 1, BX + PR + 2):
            for lz in range(PZ - PR - 1, PZ + PR + 2):
                d = math.hypot(lx - BX, lz - PZ)
                if PR - 0.6 < d <= PR + 0.4 and abs(lx - BX) > 6:
                    x, z = self.w(lx, lz)
                    a.set(x, RIM, z, B("deepslate_brick_wall"))
                    for y in range(RIM + 1, RIM + 4):
                        a.set(x, y, z, B("barrier"))
        # the golden roof over both bridge spans
        for (z1, z2) in ((GZ1 - 2, PZ - PR - 1), (PZ + PR + 1, GZ2 + 2)):
            for lz in range(z1, z2 + 1):
                for lx in (BX - 6, BX + 6):
                    if lz % 4 == 0:
                        x, z = self.w(lx, lz)
                        for y in range(RIM, RIM + 6):
                            a.set(x, y, z, B("polished_deepslate"))
                for t in range(0, 9):
                    for s in (-1, 1):
                        lx = BX + s * (8 - t)
                        x, z = self.w(lx, lz)
                        a.set(x, RIM + 6 + t // 2 + (t % 2), z, B("gold_block") if (lz + t) % 5 else B("raw_gold_block"))
                x, z = self.w(BX, lz)
                a.set(x, RIM + 10, z, B("gold_block"))
                if lz % 8 == 0:
                    C.chandelier(a, x, RIM + 9, z, 2, "soul_lantern", ring=False)
        # gates: the ring's south (entry) and north (exit) mouths
        gates = {}
        for name, lz in (("entry", PZ + PR - 1), ("exit", PZ - PR + 1)):
            for lx in range(BX - 7, BX + 8):
                x, z = self.w(lx, lz)
                for y in range(RIM, RIM + 14):
                    a.set(x, y, z, pal.wall() if (y - RIM) % 6 != 5 else pal.trim)
                for y in range(RIM + 14, RIM + 17):
                    a.set(x, y, z, B("barrier"))
            x, z = self.w(BX, lz)
            cells = self.doorway(x, RIM, z, 7, 8, "x")
            for p in cells:
                a.set(*p, AIR)
            gates[name] = cells
        cx, cz = self.w(BX, PZ)
        R = 16

        def floor_fn(x, z, d):
            if abs(d - R + 0.6) < 0.7:
                return B("gold_block")
            if abs(d - 8) < 0.5:
                return B("bone_block", axis="y")
            if d < 2.5:
                return B("chiseled_deepslate")
            return B("polished_deepslate") if (int(d) + (x + z) % 2) % 3 else B("deepslate_tiles")
        self.arena("c3_mid", cx, RIM, cz, R, "modgudr", "mid1", floor_fn=floor_fn, entry=gates["entry"], exit=gates["exit"])
        self.close(gates["exit"])
        # Modgud's chair of bones at the ring's west edge
        sx, sz = self.w(BX - 17, PZ)
        for dz in range(-2, 3):
            for y in range(RIM, RIM + 6):
                if abs(dz) == 2 or y < RIM + 2 or y == RIM + 5:
                    a.set(sx, y, sz + dz, B("bone_block", axis="y"))
        self.add_zone("c3", (cx - 6, RIM - 2, self.z0 + PZ + PR + 1, cx + 6, RIM + 3, self.z0 + GZ2 + 3), floor_mask=None, n=9)
        self.allow(BX - 22, GZ1 - 8, BX + 22, GZ2 + 8, RIM - 3, RIM + 6)

    # ------------------------------------------------------------ c4: Helgrind, the gate of bones
    def helgrind(self):
        a, rng = self.a, self.rng
        gx, gy, gz = self._at(76, 146)
        bone = mixer(rng, [(B("bone_block", axis="y"), 5), (B("calcite"), 1), (B("bone_block", axis="x"), 2)])
        for s in (-1, 1):
            tx = gx + s * 11
            for dx in range(-5, 6):
                for dz in range(-5, 6):
                    for y in range(gy - 1, gy + 30):
                        r = 5 - max(0, (y - gy - 22)) * 0.6
                        if abs(dx) <= r and abs(dz) <= r:
                            a.set(tx + dx, y, gz + dz, bone())
            for y in range(gy + 3, gy + 27, 4):
                for d in range(-4, 5, 2):
                    a.put(tx + d, y, gz + 6, B("skeleton_skull", facing_direction=3))
                    a.put(tx + d, y, gz - 6, B("skeleton_skull", facing_direction=2))
        # the arch: ribs curving over the way
        for t in range(0, 31):
            ang = math.pi * t / 30
            ax_ = gx + int(round(math.cos(ang) * 11))
            ay_ = gy + 22 + int(round(math.sin(ang) * 8))
            for dz in range(-4, 5):
                a.set(ax_, ay_, gz + dz, B("bone_block", axis="z"))
        for dx in range(-5, 6):
            for y in range(gy + 18, gy + 22):
                if a.get(gx + dx, y, gz) == AIR and y == gy + 21:
                    a.set(gx + dx, y, gz, B("iron_bars"))
        # bone heaps, black banners, soul fire, iron spikes about the field
        for _ in range(50):
            lx, lz = rng.randint(44, 228), rng.randint(152, 186)
            if not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            r = rng.random()
            if r < 0.3:
                self.heap(x, y, z, rng.uniform(1.2, 2.4), bone)
            elif r < 0.45:
                for k in range(5):
                    a.set(x, y + k, z, B("deepslate_brick_wall"))
                for k in range(1, 5):
                    a.set(x + 1, y + k, z, B("black_wool"))
                a.set(x, y + 5, z, B("soul_lantern"))
            elif r < 0.55:
                P.brazier(a, x, y, z, soul=True, base="polished_blackstone")
            elif r < 0.7:
                for k in range(rng.randint(1, 3)):
                    a.set(x, y + k, z, B("iron_bars"))
        self.add_zone("c4", self.zbox("c4"), floor_mask=self.carved & ~self.blocked)

    def heap(self, x, y, z, r, mix):
        a = self.a
        for dx in range(-int(r) - 1, int(r) + 2):
            for dz in range(-int(r) - 1, int(r) + 2):
                dd = math.hypot(dx, dz)
                if dd <= r:
                    for t in range(int((r - dd) * 0.9) + 1):
                        a.put(x + dx, y + t, z + dz, mix())

    # ------------------------------------------------------------ caves: roof over c5 and Garm's den
    def roof(self, keys, low=9, high=20, extra=()):
        a = self.a
        others = np.zeros(self.carved.shape, bool)
        for k, m in self.masks.items():
            if k not in keys:
                others |= m
        target = np.zeros(self.carved.shape, bool)
        for k in keys:
            target |= self.masks[k]
        d = distance_transform_edt(~target)
        region = self.carved & (d <= 8) & ~others
        for (i, k) in extra:
            region[i, k] = True
        self.roofed = getattr(self, "roofed", np.zeros(self.carved.shape, bool)) | region
        n = fbm(self.sx, self.sz, 7, 2, self.seed + 61)
        dt = distance_transform_edt(target)
        for (i, k) in np.argwhere(region):
            f = int(self.H[i, k])
            h = low + int(min(high - low, dt[i, k] * 0.9)) + int((n[i, k] - 0.5) * 3)
            c = f + max(low, h)
            top = max(c + 6, int(np.max(self.H[max(0, i - 9):i + 10, max(0, k - 9):k + 10])))
            top = min(top, self.Y0 + self.SY - 6)
            x, z = self.w(i, k)
            col = a.blk[i, :, k]
            for y in range(c + 1, top + 1):
                col[y - self.Y0] = B("deepslate") if (y + i // 5) % 6 else B("tuff")
            if self.rng.random() < 0.03 and c - f > 8:
                for t in range(1, self.rng.randint(4, 10)):
                    a.set(x, c - t + 1, z, B("chain"))
            elif self.rng.random() < 0.02:
                a.set(x, c, z, B("sculk"))

    def gnipa(self):
        a, rng = self.a, self.rng
        self.roof(["c5"], low=9, high=18)
        m = self.masks["c5"]
        for _ in range(40):
            lx, lz = rng.randint(22, 112), rng.randint(98, 132)
            if not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            r = rng.random()
            if r < 0.3:
                self.heap(x, y, z, rng.uniform(1.0, 2.0), mixer(rng, [(B("bone_block", axis="x"), 3), (B("bone_block", axis="y"), 1)]))
            elif r < 0.45:
                a.set(x, y - 1, z, B("nether_wart_block") if rng.random() < 0.5 else B("red_terracotta"))
            elif r < 0.55:
                a.set(x, y, z, B("soul_lantern"))
        self.add_zone("c5", self.zbox("c5"), floor_mask=self.carved & ~self.blocked)

    # ------------------------------------------------------------ mid-boss 2: Garm's den
    def garm_den(self):
        a, rng = self.a, self.rng
        f0 = int(np.median(self.H[self.masks["a2"]]))
        entry = self.gate_wall(48, 82, "z", 9, int(self.H[48, 82]) + 1, gw=7, gh=8, height=14)
        exitg = self.gate_wall(84, 38, "x", 9, int(self.H[84, 38]) + 1, gw=7, gh=8, height=14)
        self.roof(["a2"], low=10, high=24)
        cx, cz = self.w(46, 46)
        R = 17

        def floor_fn(x, z, d):
            if abs(d - R + 0.6) < 0.7 or abs(d - 9) < 0.5:
                return B("iron_block")
            if d < 2:
                return B("chiseled_deepslate")
            return B("deepslate_tiles") if (int(d) + (x + z) % 2) % 3 else B("polished_deepslate")
        self.arena("c5_mid", cx, f0 + 1, cz, R, "garm", "mid2", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # the broken chain Gleipnir-like links lying around the rim, chains hanging from the roof
        for t in range(24):
            ang = t / 24 * 2 * math.pi
            x, z = int(round(cx + math.cos(ang) * 19)), int(round(cz + math.sin(ang) * 19))
            if a.get(x, f0 + 1, z) == AIR:
                a.set(x, f0 + 1, z, B("chain", axis="x" if t % 2 else "z"))
        self.allow(20, 20, 92, 86, f0 - 4, f0 + 8)

    # ------------------------------------------------------------ c6: Nastrond, the corpse shore
    def nastrond(self):
        a, rng = self.a, self.rng
        m = self.masks["c6"]
        # the black lake along the north of the shore
        lake = [(i, k) for (i, k) in np.argwhere(m) if k < 30 + int(6 * math.sin(i / 13.0))]
        for (i, k) in lake:
            x, z = self.w(i, k)
            f = int(self.H[i, k])
            for y in range(f - 2, f + 1):
                a.set(x, y, z, B("water"))
            a.set(x, f - 3, z, B("black_concrete"))
            self.H[i, k] = f - 3
        # arches of serpent spines over the shore path
        for lx in range(118, 228, 6):
            x, y, z = self._at(lx, 46)
            for t in range(0, 21):
                ang = math.pi * t / 20
                ax_ = int(round(math.cos(ang) * 7))
                ay_ = int(round(math.sin(ang) * 9))
                a.set(x, y + ay_, z + ax_, B("bone_block", axis="y"))
                if t % 4 == 0:
                    a.set(x - 1, y + ay_, z + ax_, B("bone_block", axis="x"))
                    a.set(x + 1, y + ay_, z + ax_, B("bone_block", axis="x"))
            a.set(x, y + 9, z, B("verdant_froglight"))
        # Nidhogg's bones on the shore
        sx, sy, sz = self._at(150, 34)
        spine = [(sx - 34 + k, sy + 3 + int(3 * math.sin(k / 9.0)), sz + int(4 * math.sin(k / 14.0))) for k in range(68)]
        for (x, y, z) in spine:
            a.set(x, y, z, B("bone_block", axis="x"))
        for k in range(8, 50, 4):
            x, y, z = spine[k]
            for s in (-1, 1):
                pts = [(x, y, z), (x, y + 3, z + s * 5), (x, y, z + s * 8), (x, sy, z + s * 8)]
                for p0, p1 in zip(pts[:-1], pts[1:]):
                    for q in line_points(p0, p1, step=0.5):
                        a.set(int(q[0]), int(q[1]), int(q[2]), B("bone_block", axis="y"))
        hx, hy, hz = spine[-1]
        ell(a, hx + 4, hy + 1, hz, 4, 3, 3, B("bone_block", axis="y"))
        ell(a, hx + 8, hy - 1, hz, 3, 1.4, 2.4, B("bone_block", axis="x"))
        for s in (-1, 1):
            a.set(hx + 5, hy + 2, hz + s * 2, B("verdant_froglight"))
            thick_line(a, (hx + 2, hy + 3, hz + s * 2), (hx - 4, hy + 9, hz + s * 5), 0.6, B("bone_block", axis="y"))
        for s in (-1, 1):
            wx, wy, wz = spine[30]
            thick_line(a, (wx, wy, wz), (wx + 6, wy + 14, wz + s * 18), 0.6, B("bone_block", axis="y"))
            thick_line(a, (wx + 6, wy + 14, wz + s * 18), (wx + 20, wy + 6, wz + s * 26), 0.5, B("bone_block", axis="y"))
        self.graves(m, 110, 30, 240, 60, n=30)
        self.add_zone("c6", self.zbox("c6"), floor_mask=self.carved & ~self.blocked)

    # ------------------------------------------------------------ boss: Eljudnir, half alive and half dead
    def eljudnir(self):
        a, rng = self.a, self.rng
        lcx, lcz = 212, 112
        f0 = self.fortify("boss", height=20, towers=6, pal=self.dead, tower_roof="pyramid")
        # the east half of the walls belongs to the living
        m = self.masks["boss"]
        dist = distance_transform_edt(~m)
        ring = (dist > 0) & (dist <= 3.5) & ~self.carved
        for (i, k) in np.argwhere(ring):
            if i < lcx:
                continue
            x, z = self.w(i, k)
            for y in range(f0 - 1, f0 + 22):
                b = a.get(x, y, z)
                if b == AIR:
                    continue
                n = PAL.names[b]
                if n in ("deepslate_bricks", "cracked_deepslate_bricks", "deepslate_tiles"):
                    a.set(x, y, z, self.live.wall())
                elif n == "bone_block":
                    a.set(x, y, z, self.live.trim)
                elif n == "deepslate_brick_wall":
                    a.set(x, y, z, self.live.top)
        entry = self.gate_wall(208, 74, "z", 9, int(self.H[208, 74]) + 1, gw=7, gh=8, height=16)
        cx, cz = self.w(lcx, lcz)
        R = 22

        def floor_fn(x, z, d):
            east = x >= cx
            if abs(x - cx) < 1:
                return B("gold_block")
            if abs(d - R + 0.6) < 0.7:
                return B("gold_block") if east else B("bone_block", axis="y")
            if east:
                return B("moss_block") if (x + z) % 4 else B("mossy_stone_bricks")
            return B("sculk") if (x * 3 + z) % 5 == 0 else B("deepslate_tiles")
        ar = self.arena("boss", cx, f0, cz, R, "hel", "final", floor_fn=floor_fn, entry=entry)
        # flowers on the living side, sculk veins and bones on the dead side (outside the ring)
        for _ in range(200):
            lx, lz = rng.randint(lcx - 29, lcx + 29), rng.randint(lcz - 29, lcz + 29)
            d = math.hypot(lx - lcx, lz - lcz)
            if d < R + 1 or not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            if a.get(x, y, z) != AIR:
                continue
            if lx >= lcx:
                a.set(x, y - 1, z, B("moss_block"))
                a.set(x, y, z, B(rng.choice(["azalea", "flowering_azalea", "poppy", "cornflower", "lily_of_the_valley", "fern"])))
            else:
                a.set(x, y - 1, z, B("sculk"))
                a.set(x, y, z, B(rng.choice(["bone_block", "sculk_vein", "deadbush", "web"])) if rng.random() < 0.6 else B("soul_lantern"))
        # the split throne on the north rim
        tx, tz = self.w(lcx, lcz - R - 3)
        for dx in range(-4, 5):
            for y in range(f0, f0 + 12):
                if abs(dx) == 4 or y < f0 + 3 or y > f0 + 9:
                    a.set(tx + dx, y, tz, B("gold_block") if dx > 0 else B("bone_block", axis="y") if dx < 0 else B("crying_obsidian"))
        # exit: a corridor east through the wall to the portal alcove, gated
        for lx in range(lcx + 26, lcx + 47):
            for lz in range(lcz - 3, lcz + 4):
                x, z = self.w(lx, lz)
                a.set(x, f0 - 1, z, self.dead.floor())
                for y in range(f0, f0 + 7):
                    a.set(x, y, z, AIR)
                self.carved[lx, lz] = True
                self.H[lx, lz] = f0 - 1
        for lx in range(lcx + 34, lcx + 47):
            for lz in range(lcz - 7, lcz + 8):
                x, z = self.w(lx, lz)
                a.set(x, f0 - 1, z, self.dead.floor())
                for y in range(f0, f0 + 9):
                    a.set(x, y, z, AIR)
                self.carved[lx, lz] = True
                self.H[lx, lz] = f0 - 1
        gx, gz = self.w(lcx + 31, lcz)
        exitg = self.doorway(gx, f0, gz, 7, 7, "z")
        for dz in range(-4, 5):
            for y in range(f0, f0 + 10):
                if abs(dz) > 3 or y >= f0 + 7:
                    a.set(gx, y, gz + dz, self.dead.wall())
        ar["exit"] = [list(p) for p in exitg]
        self.close(exitg)
        px, pz = self.w(lcx + 41, lcz)
        self.exit_portal(px, f0, pz)
        self.allow(176, 76, 262, 146, f0 - 4, f0 + 8)

    # ------------------------------------------------------------ finishing
    def finish(self):
        a, rng = self.a, self.rng
        carved = self.carved & ~getattr(self, "roofed", np.zeros(self.carved.shape, bool))
        self.dress_walls(carved, [B("deepslate"), B("tuff"), B("cobbled_deepslate"), B("deepslate"), B("sculk"), B("deepslate_tiles")],
                         moss=0.0, vines=0.0, rim=None, lichen=0.0)
        self.ambient = [dict(box=self.zones["c1"]["box"], particle="minecraft:sculk_soul_particle", rate=2),
                        dict(box=self.zones["c2"]["box"], particle="minecraft:snowflake_particle", rate=2),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:soul_particle", rate=2),
                        dict(box=self.zones["c4"]["box"], particle="minecraft:soul_particle", rate=1)]
        for key in ("c1", "c2", "c4", "c5", "c6"):
            bx1, by1, bz1, bx2, by2, bz2 = self.zones[key]["box"]
            self.light_fill((bx1, bz1, bx2, bz2), (by1, by2), level=7, threshold=4, spacing=8)
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        a.fix_walls()


def build(seed=1):
    d = Helheim("d09", seed)
    d.build()
    return d
