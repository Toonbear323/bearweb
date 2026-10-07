"""Dungeon 4 — 흐룽그니르의 돌산 (Hrungnir's Mountain). Beginner, 176 x 288, climbs ~55 blocks.

South -> north, ever higher: a mountain tarn with the landing jetty and giant footprints, the stone-arch path,
the valley of trolls turned to stone, the chasm crossed on rope bridges, the ruined hunters' camp, the giant
mushroom cave inside the mountain, the troll den full of bones, and Griotunagard - the stone duelling ring on the
summit where the clay giant Mokkurkalfi still lies where he fell.
"""
import math

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

from mcw import B, AIR, PAL
from gen_common import fbm, stair, slab, standing_sign, hanging_lamp, line_points, leaves_of, leaf_blob, boulder, \
    spruce_tree
import nr_parts as P
from nr_dungeon import Dungeon, mixer
from nr_spawn import cyl, ell, thick_line

SEA = 62


def troll_statue(a, x, y, z, rng, h=14, yaw=0.0, pose="crouch"):
    """A troll turned to stone by the sunrise: hunched body, huge head and nose, long arms with knuckles on the ground.
    Mossy on top. (x, y, z) = ground under the middle, yaw = facing angle (radians, 0 = +z)."""
    fx, fz = math.sin(yaw), math.cos(yaw)          # forward
    rx, rz = fz, -fx                                # right
    mats = [B("stone"), B("andesite"), B("cobblestone"), B("stone"), B("stone")]
    moss = [B("mossy_cobblestone"), B("moss_block")]

    def W(u, v, w):                                 # local (right, up, forward) -> world
        return (x + rx * u + fx * w, y + v, z + rz * u + fz * w)

    def blob(c, r, ry=None, mat=None):
        cx, cy, cz = c
        ry = ry or r
        for xx in range(int(cx - r - 1), int(cx + r + 2)):
            for yy in range(int(cy - ry - 1), int(cy + ry + 2)):
                for zz in range(int(cz - r - 1), int(cz + r + 2)):
                    d = math.sqrt(((xx - cx) / r) ** 2 + ((yy - cy) / ry) ** 2 + ((zz - cz) / r) ** 2)
                    if d <= 1.0 - rng.random() * 0.12:
                        top = d > 0.6 and yy > cy + ry * 0.35
                        a.set(xx, yy, zz, (rng.choice(moss) if top and rng.random() < 0.7 else mat or rng.choice(mats)))

    s = h / 14.0
    sit = pose == "sit"
    eye, tusk = B("blackstone"), B("calcite")
    # legs: short and thick; knees up and feet forward when sitting
    for side in (-1, 1):
        hip = W(side * 2.4 * s, 4.0 * s, -0.8 * s)
        knee = W(side * 3.0 * s, (4.2 if sit else 2.4) * s, (4.0 if sit else 0.8) * s)
        foot = W(side * 3.0 * s, 0.6 * s, (6.0 if sit else 1.8) * s)
        thick_line(a, hip, knee, 1.6 * s, mats[0])
        thick_line(a, knee, foot, 1.4 * s, mats[1])
        blob(W(side * 3.0 * s, 0.7 * s, (6.8 if sit else 2.6) * s), 1.6 * s, 0.9 * s)
    # round belly, chest, and the great mossy hump that rises above the head
    blob(W(0, 5.2 * s, 0.4 * s), 3.6 * s, 3.0 * s)
    blob(W(0, 8.0 * s, 1.2 * s), 3.8 * s, 3.0 * s)
    blob(W(0, 10.4 * s, -0.6 * s), 3.2 * s, 2.4 * s, mat=B("mossy_cobblestone"))
    # neck and the head hanging forward, lower than the hump
    thick_line(a, W(0, 9.6 * s, 2.6 * s), W(0, 9.4 * s, 5.6 * s), 1.6 * s, mats[0])
    blob(W(0, 9.6 * s, 6.4 * s), 2.6 * s, 2.4 * s, mat=B("stone"))
    blob(W(0, 10.9 * s, 8.0 * s), 1.7 * s, 0.6 * s, mat=B("cobblestone"))                 # heavy brow
    thick_line(a, W(0, 9.8 * s, 8.6 * s), W(0, 8.0 * s, 10.8 * s), 0.9 * s, B("andesite"))   # long drooping nose
    for side in (-1, 1):
        blob(W(side * 2.8 * s, 10.4 * s, 6.0 * s), 0.9 * s, 1.2 * s, mat=B("stone"))       # ears
        a.set(*[int(round(v)) for v in W(side * 1.1 * s, 10.1 * s, 8.6 * s)], eye)       # eyes
        a.set(*[int(round(v)) for v in W(side * 1.2 * s, 7.9 * s, 8.4 * s)], tusk)       # tusks
        a.set(*[int(round(v)) for v in W(side * 1.2 * s, 8.7 * s, 8.6 * s)], tusk)
    # long arms: knuckles on the ground, or hands on the knees when sitting
    for side in (-1, 1):
        sh = W(side * 4.2 * s, 9.8 * s, 1.4 * s)
        el = W(side * 5.8 * s, 6.2 * s, 3.6 * s)
        hand = W(side * 5.2 * s, 0.8 * s, 6.2 * s) if not sit else W(side * 3.4 * s, 5.4 * s, 5.0 * s)
        blob(sh, 1.9 * s, 1.7 * s)
        thick_line(a, sh, el, 1.5 * s, mats[2])
        thick_line(a, el, hand, 1.3 * s, mats[0])
        blob(hand, 1.7 * s, 1.1 * s)
    # moss and small plants growing on his back and shoulders
    for _ in range(int(30 * s)):
        u, v, w = rng.uniform(-4, 4) * s, rng.uniform(6, 13) * s, rng.uniform(-3, 4) * s
        px, py, pz = (int(round(c)) for c in W(u, v, w))
        if a.get(px, py, pz) != AIR and a.get(px, py + 1, pz) == AIR and rng.random() < 0.5:
            a.set(px, py + 1, pz, B(rng.choice(["short_grass", "fern", "moss_carpet", "moss_carpet"])))


def stone_arch(a, p0, p1, height, r, rng, mats):
    """Natural rock arch between two ground points, rough and slightly twisted."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    n = int(math.dist(p0, p1) * 2) + 2
    for t in range(n + 1):
        u = t / n
        x = x0 + (x1 - x0) * u
        z = z0 + (z1 - z0) * u
        yb = y0 + (y1 - y0) * u
        y = yb + height * math.sin(math.pi * u) ** 0.8
        rr = r * (1.25 - 0.45 * math.sin(math.pi * u))
        ell(a, x, y, z, rr + rng.uniform(-0.3, 0.3), rr * 0.8, rr + rng.uniform(-0.3, 0.3), rng.choice(mats))


class Hrungnir(Dungeon):
    Y0, SY = 48, 128          # 48..175

    ZN = {
        "start": (88, 258, 56, 22, lambda X, Z, n: 63 + np.clip((262 - Z) * 0.07, 0, 3) + (n - 0.5) * 1.2, 0.15),
        "c1": (58, 220, 34, 24, 68),
        "c2": (118, 186, 36, 26, 75),
        "c3": (62, 148, 38, 24, 84),
        "c4": (116, 110, 36, 24, 92),
        "c5": (60, 74, 34, 24, 97),
        "c6": (118, 46, 34, 22, 105),
        "boss": (56, 26, 19, 19, 116, 0.06),
    }

    def build(self):
        self.terrain()
        self.tarn()
        self.arch_path()
        self.troll_valley()
        self.chasm()
        self.hunters_ruin()
        self.mushroom_cave()
        self.troll_den()
        self.summit()
        self.finish()

    # ------------------------------------------------------------ terrain
    def terrain(self):
        rng = self.rng
        zones = {}
        for k, spec in self.ZN.items():
            zones[k] = spec[:5]
        paths = [([(84, 248), (66, 234)], 9), ([(84, 214), (100, 200)], 9), ([(100, 172), (84, 162)], 9),
                 ([(84, 132), (98, 122)], 9), ([(96, 96), (78, 86)], 9), ([(84, 62), (100, 54)], 9),
                 ([(100, 34), (76, 26)], 9)]
        self.valleys(zones, paths, high=(96, 10), wall_extra=13, rough=0.22, margin=6)
        X, Z = self.X - self.x0, self.Z - self.z0
        # the mountain mass: highest in the middle of the climb, crags around the summit
        M = 96 + 54 * np.exp(-((Z - 135) / 95.0) ** 2) + (self.n1 - 0.5) * 26 + (self.n2 - 0.5) * 8
        rise = self.near_floor + 1 + self.wall_dist * 4.5
        H = np.where(self.carved, self.H, np.maximum(self.H, np.minimum(rise, M)))
        self.H = np.minimum(np.round(H).astype(int), self.Y0 + self.SY - 6)
        # the tarn at the foot of the mountain
        self.lake = np.zeros(self.carved.shape, bool)
        d = np.hypot((X - 90) / 48.0, (Z - 270) / 8.5 * (1 + 0.25 * (self.n2 - 0.5)))
        self.lake = (d < 1) & self.masks["start"]
        dl = distance_transform_edt(~self.lake)
        bank = self.masks["start"] & ~self.lake & (dl < 6)
        self.H = np.where(bank, np.minimum(self.H, 63 + (dl // 3).astype(int)), self.H)
        self.H = np.where(self.lake, (SEA - 2 - 5 * (1 - d)).astype(int), self.H)
        top = mixer(rng, [(B("grass_block"), 5), (B("coarse_dirt"), 2), (B("gravel"), 1), (B("stone"), 1), (B("moss_block"), 1)])
        sub = mixer(rng, [(B("dirt"), 4), (B("stone"), 1)])
        rock = [B("stone"), B("andesite"), B("stone"), B("stone"), B("tuff"), B("andesite"), B("stone"), B("cobblestone")]
        self.paint_valley(top, sub, rock, slope_rock=1.2)
        a = self.a
        grass = mixer(rng, [(B("grass_block"), 8), (B("moss_block"), 1)])
        dirt = mixer(rng, [(B("coarse_dirt"), 3), (B("grass_block"), 1), (B("gravel"), 1)])
        scree = mixer(rng, [(B("gravel"), 3), (B("stone"), 2), (B("andesite"), 2), (B("cobblestone"), 1)])
        stone = mixer(rng, [(B("stone"), 4), (B("andesite"), 2), (B("tuff"), 1)])
        low = self.carved & (Z >= 170) & ~self.lake
        high = self.carved & (Z < 170)
        self.patch_paint(low, [(0.55, grass), (0.68, dirt), (0.8, scree), (1.0, grass)], scale=8, speckle=0.06)
        self.patch_paint(high, [(0.38, grass), (0.52, dirt), (0.72, scree), (1.0, stone)], scale=7, speckle=0.06)
        for (i, k) in np.argwhere(self.lake):
            h = int(self.H[i, k])
            for y in range(h + 1, SEA + 1):
                a.blk[i, y - self.Y0, k] = B("water")
            a.blk[i, h - self.Y0, k] = B("gravel") if rng.random() < 0.6 else B("clay")
        sand = mixer(rng, [(B("gravel"), 3), (B("stone"), 1), (B("sand"), 1)])
        for (i, k) in np.argwhere(bank & (dl < 2.5)):
            a.blk[i, int(self.H[i, k]) - self.Y0, k] = sand()
        # snow on the high crags
        for (i, k) in np.argwhere(~self.carved & (self.H > 134)):
            h = int(self.H[i, k])
            j = h - self.Y0
            if rng.random() < min(1.0, (h - 134) / 8.0):
                a.blk[i, j, k] = B("snow")
                if j + 1 < self.SY and rng.random() < 0.6:
                    a.blk[i, j + 1, k] = B("snow_layer", height=rng.randint(0, 2))
        a.bio[:, :] = 189                   # stony peaks
        a.bio[:, 200:] = 3                  # windswept hills at the foot

    def zbox(self, key, pad=4, dy=(-6, 18)):
        cx, cz, rx, rz = self.ZN[key][:4]
        x, z = self.L(cx, cz)
        win = self.H[max(0, cx - 4):cx + 5, max(0, cz - 4):cz + 5]
        f = int(np.mean(win))
        return (x - rx - pad, f + dy[0], z - rz - pad, x + rx + pad, f + dy[1], z + rz + pad)

    def _at(self, lx, lz):
        x, z = self.L(lx, lz)
        return x, int(self.H[lx, lz]) + 1, z

    def free(self, lx, lz):
        return self.carved[lx, lz] and not self.lake[lx, lz] and self.wall_dist[lx, lz] == 0

    # ------------------------------------------------------------ start: the tarn
    def tarn(self):
        a, rng = self.a, self.rng
        L = self.L
        # return ship on the tarn, jetty from the north shore
        info = P.longship(a, self.x0 + 116, SEA, self.z0 + 272, "west", rng, length=29, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        for lz in range(254, 268):
            for lx in (99, 100, 101):
                x, z = L(lx, lz)
                if not self.carved[lx, lz]:
                    continue
                a.set(x, SEA + 1, z, B("spruce_planks"))
                for y in range(SEA + 2, SEA + 6):
                    a.set(x, y, z, AIR)
                if lx != 100 and lz % 4 == 2:
                    for y in range(SEA - 6, SEA + 1):
                        if a.get(x, y, z) in (B("water"), AIR):
                            a.set(x, y, z, B("spruce_log", axis="y"))
                    a.set(x, SEA + 2, z, B("spruce_fence"))
                    if lz % 8 == 2:
                        a.set(x, SEA + 3, z, B("lantern"))
        ax, az = L(100, 256)
        self.data["start"] = [ax + 0.5, SEA + 2, az + 0.5, 180]
        self.walk_seeds = [(ax, SEA + 2, az)]
        # giant footprints pressed into the meadow, filled with rain water
        for (fx, fz, ang) in ((70, 248, 0.3), (122, 244, -0.2)):
            self.footprint(fx, fz, ang)
        # a small camp: tent, fire, runestone telling the story
        cx, cy, cz = self._at(122, 258)
        a.set(cx, cy - 1, cz, B("cobblestone"))
        a.set(cx, cy, cz, B("campfire"))
        for k in range(6):
            ang = k / 6 * 2 * math.pi
            x, z = int(round(cx + math.cos(ang) * 2.5)), int(round(cz + math.sin(ang) * 2.5))
            t = P.surface_y(a, x, z)
            if t is not None and a.get(x, t + 1, z) == AIR:
                a.set(x, t + 1, z, B("spruce_log", axis="x" if k % 2 else "z"))
        tx, ty, tz = self._at(132, 254)
        for dz in range(-2, 3):
            for k in range(3):
                a.set(tx - 2 + k, ty + k, tz + dz, B("brown_wool"))
                a.set(tx + 2 - k, ty + k, tz + dz, B("brown_wool"))
            a.set(tx, ty + 3, tz + dz, B("spruce_slab"))
        P.barrels(a, tx - 4, ty, tz + 3, rng, 3)
        rx, ry, rz = self._at(94, 250)
        P.runestone(a, rx, ry, rz, rng, h=6, mat="stone")
        standing_sign(a, ax + 2, SEA + 2, az - 3, 8, "§l§7흐룽그니르의 돌산\n§r§f정상의 결투장까지\n§7석상을 깨우지 마라", kind="spruce_standing_sign")
        # a few spruces and boulders along the shore meadows
        for _ in range(60):
            lx, lz = rng.randint(30, 150), rng.randint(238, 268)
            if not self.free(lx, lz) or 94 <= lx <= 106:
                continue
            x, y, z = self._at(lx, lz)
            if a.get(x, y, z) != AIR or a.get(x, y - 1, z) == B("water"):
                continue
            r = rng.random()
            if r < 0.12:
                spruce_tree(a, x, y, z, rng, h=rng.randint(7, 11))
            elif r < 0.2:
                boulder(a, x, y - 1, z, rng, rng.uniform(1.2, 2.4), [B("stone"), B("andesite"), B("mossy_cobblestone")])
            else:
                a.set(x, y, z, B(rng.choice(["short_grass", "short_grass", "fern", "cornflower", "dandelion"])))

    def footprint(self, lx, lz, ang):
        """A footprint ~16 long sunk two blocks into the ground, water flush with the floor (a step to get out)."""
        a = self.a
        ca, sa = math.cos(ang), math.sin(ang)
        cells = set()
        for du in range(-10, 11):
            for dw in range(-6, 7):
                # heel + sole ellipse
                inside = (du / 8.0) ** 2 + (dw / (4.0 + 0.6 * du / 8.0)) ** 2 <= 1
                # four toes in front
                for t, off in enumerate((-3.4, -1.1, 1.2, 3.3)):
                    if math.hypot(du - (9.4 - abs(off) * 0.25), dw - off) < (1.5 if t else 1.8):
                        inside = True
                if inside:
                    x = int(round(lx + du * sa + dw * ca))
                    z = int(round(lz - du * ca + dw * sa))
                    cells.add((x, z))
        for (i, k) in cells:
            if not (0 <= i < self.sx and 0 <= k < self.sz) or not self.free(i, k):
                continue
            x, z = self.L(i, k)
            h = int(self.H[i, k])
            a.set(x, h, z, B("water"))
            a.set(x, h - 1, z, B("water"))
            a.set(x, h - 2, z, B("mud") if (i + k) % 3 else B("gravel"))

    # ------------------------------------------------------------ c1: path of stone arches
    def arch_path(self):
        a, rng = self.a, self.rng
        mats = [B("stone"), B("andesite"), B("tuff"), B("stone"), B("mossy_cobblestone")]
        spans = [((40, 236), (52, 226), 9), ((62, 222), (76, 212), 11), ((34, 214), (46, 202), 8), ((74, 236), (84, 224), 7)]
        for (p0, p1, hgt) in spans:
            if not (self.carved[p0] and self.carved[p1]):
                continue
            q0 = self._at(*p0)
            q1 = self._at(*p1)
            stone_arch(a, (q0[0], q0[1] - 1, q0[2]), (q1[0], q1[1] - 1, q1[2]), hgt, 1.8, rng, mats)
        # a gravel track winding through, boulders and spruces beside it
        for t in range(140):
            lz = 250 - t * 0.4
            lx = 60 + math.sin(lz / 9.0) * 10
            for dx in range(-1, 2):
                i, k = int(lx + dx), int(lz)
                if self.free(i, k):
                    x, z = self.L(i, k)
                    a.set(x, int(self.H[i, k]), z, B("gravel") if rng.random() < 0.7 else B("coarse_dirt"))
        for _ in range(26):
            lx, lz = rng.randint(28, 92), rng.randint(198, 244)
            if not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            if rng.random() < 0.6:
                boulder(a, x, y - 1, z, rng, rng.uniform(1.4, 3.0), mats)
            else:
                spruce_tree(a, x, y, z, rng, h=rng.randint(8, 12))
        self.add_zone("c1", self.zbox("c1"), floor_mask=self.carved)

    # ------------------------------------------------------------ c2: valley of petrified trolls
    def troll_valley(self):
        a, rng = self.a, self.rng
        trolls = [(100, 196, 0.8, 15, "crouch"), (134, 206, 2.6, 13, "sit"), (140, 172, -2.2, 16, "crouch"),
                  (112, 168, 1.6, 12, "sit"), (126, 188, 3.4, 18, "crouch")]
        for (lx, lz, yaw, h, pose) in trolls:
            if not self.carved[lx, lz]:
                continue
            x, y, z = self._at(lx, lz)
            troll_statue(a, x, y - 1, z, rng, h=h, yaw=yaw, pose=pose)
        # the morning sun that turned them: a ring of pale stones and scattered rubble
        for _ in range(40):
            lx, lz = rng.randint(86, 154), rng.randint(162, 212)
            if not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            if a.get(x, y, z) != AIR:
                continue
            r = rng.random()
            if r < 0.3:
                a.set(x, y, z, B(rng.choice(["cobblestone", "mossy_cobblestone", "andesite"])))
            elif r < 0.45:
                a.set(x, y, z, B("cobblestone_wall"))
            else:
                a.set(x, y, z, B(rng.choice(["short_grass", "fern", "moss_carpet"])))
        self.add_zone("c2", self.zbox("c2"), floor_mask=self.carved)

    # ------------------------------------------------------------ c3: the chasm and rope bridges
    def chasm(self):
        a, rng = self.a, self.rng
        L = self.L
        floor_y = self.ZN["c3"][4]
        bottom = floor_y - 26
        n = fbm(self.sx, self.sz, 10, 2, self.seed + 40)
        self.chasm_cells = set()
        for lx in range(20, 108):
            for lz in range(126, 172):
                if not self.carved[lx, lz]:
                    continue
                w = 5.5 + n[lx, lz] * 3
                zc = 148 + math.sin(lx / 11.0) * 4
                if abs(lz - zc) > w:
                    continue
                pillar = math.hypot(lx - 60, lz - zc) < 4.6
                if pillar:
                    continue
                x, z = L(lx, lz)
                h = int(self.H[lx, lz])
                for y in range(bottom, h + 8):
                    a.set(x, y, z, AIR)
                a.set(x, bottom - 1, z, B("gravel"))
                for y in range(bottom, bottom + 4):
                    a.set(x, y, z, B("water"))
                self.H[lx, lz] = bottom
                self.chasm_cells.add((lx, lz))
        # the rock pillar in the middle: flat top at the ledge height
        zc60 = 148 + math.sin(60 / 11.0) * 4
        px, pz = L(60, int(round(zc60)))
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                d = math.hypot(dx, dz)
                if d < 4.6:
                    for y in range(bottom - 1, floor_y + 1):
                        a.set(px + dx, y, pz + dz, B("stone") if y < floor_y else B("coarse_dirt"))
                    for y in range(floor_y + 1, floor_y + 8):
                        a.set(px + dx, y, pz + dz, AIR)
                    self.H[60 + dx, int(round(zc60)) + dz] = floor_y
        a.set(px, floor_y + 1, pz, B("spruce_fence"))
        a.set(px, floor_y + 2, pz, B("lantern"))
        # rope bridges: south ledge -> pillar -> north ledge (west route), and a long east span
        self.rope_bridge((60, int(round(zc60)) + 4), (60, 166), floor_y)
        self.rope_bridge((60, int(round(zc60)) - 4), (60, 130), floor_y)
        self.rope_bridge((84, 166), (84, 130), floor_y, sag=2.5)
        # ladders up both walls so a fall into the water is never a dead end
        for lx in (34, 50, 76, 100):
            zc = 148 + math.sin(lx / 11.0) * 4
            for sgn, face in ((1, 2), (-1, 3)):
                x, z0 = L(lx, int(round(zc)))
                zz = z0
                while a.get(x, floor_y - 2, zz) == AIR and abs(zz - z0) < 14:
                    zz += sgn
                if a.get(x, floor_y - 2, zz) == AIR:
                    continue
                lad = zz - sgn
                for yy in range(bottom + 1, floor_y + 1):
                    a.set(x, yy, lad, B("ladder", facing_direction=face))
                    a.wet[x - self.x0, yy - self.Y0, lad - self.z0] = yy < bottom + 4
                for yy in range(floor_y + 1, floor_y + 4):
                    a.set(x, yy, zz, AIR)
        # cliff dressing: moss, glow lichen and hanging vines down the chasm walls
        for (lx, lz) in list(self.chasm_cells):
            if rng.random() < 0.25:
                for (di, dk, bit) in ((1, 0, 8), (-1, 0, 2), (0, 1, 1), (0, -1, 4)):
                    if (lx + di, lz + dk) not in self.chasm_cells:
                        x, z = L(lx, lz)
                        y0 = floor_y - rng.randint(0, 4)
                        for t in range(rng.randint(4, 14)):
                            if a.get(x, y0 - t, z) == AIR and a.get(x + di, y0 - t, z + dk) != AIR:
                                a.set(x, y0 - t, z, B("vine", vine_direction_bits=bit))
                        break
        self.add_zone("c3", self.zbox("c3", dy=(-30, 16)), floor_mask=self.carved & ~self.cells_mask(self.chasm_cells))

    def cells_mask(self, cells):
        m = np.zeros(self.carved.shape, bool)
        for (i, k) in cells:
            m[i, k] = True
        return m

    def rope_bridge(self, p0, p1, y, sag=1.5):
        """3-wide plank bridge with fence rails and chain posts, sagging in the middle. p = local (x, z)."""
        a = self.a
        (x0, z0), (x1, z1) = p0, p1
        n = max(abs(x1 - x0), abs(z1 - z0))
        along_z = abs(z1 - z0) >= abs(x1 - x0)
        for t in range(n + 1):
            u = t / max(1, n)
            lx = int(round(x0 + (x1 - x0) * u))
            lz = int(round(z0 + (z1 - z0) * u))
            s = int(round(sag * math.sin(math.pi * u)))
            for w in (-1, 0, 1):
                i, k = (lx + w, lz) if along_z else (lx, lz + w)
                x, z = self.L(i, k)
                if a.get(x, y, z) != AIR and t not in (0, n):
                    continue
                if a.get(x, y, z) == AIR or a.get(x, y, z) in (B("water"),):
                    a.set(x, y - s, z, B("spruce_slab", half="top") if w or t % 3 else B("spruce_planks"))
                    if w:
                        a.set(x, y - s + 1, z, B("spruce_fence") if t % 6 else B("dark_oak_log", axis="y"))
                        if t % 6 == 0:
                            a.set(x, y - s + 2, z, B("chain"))

    # ------------------------------------------------------------ c4: ruined hunters' camp
    def hunters_ruin(self):
        a, rng = self.a, self.rng
        cx, cy, cz = self._at(116, 110)
        # broken palisade ring
        for k in range(90):
            ang = k / 90 * 2 * math.pi
            if rng.random() < 0.35:
                continue
            x, z = int(round(cx + math.cos(ang) * 18)), int(round(cz + math.sin(ang) * 13))
            if not self.inside(x, z) or not self.carved[x - self.x0, z - self.z0]:
                continue
            t = P.surface_y(a, x, z)
            if t is None:
                continue
            hh = rng.randint(1, 5)
            for y in range(t + 1, t + 1 + hh):
                a.set(x, y, z, B("spruce_log", axis="y") if rng.random() < 0.8 else B("stripped_spruce_log", axis="y"))
            if hh >= 4 and rng.random() < 0.5:
                a.set(x, t + 1 + hh, z, B("skeleton_skull", facing_direction=1))
        # a watchtower (still standing) on the east side
        tx, ty, tz = self._at(132, 104)
        for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            for y in range(ty, ty + 9):
                a.set(tx + dx, y, tz + dz, B("spruce_log", axis="y"))
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                a.set(tx + dx, ty + 8, tz + dz, B("spruce_planks"))
                if abs(dx) == 3 or abs(dz) == 3:
                    a.set(tx + dx, ty + 9, tz + dz, B("spruce_fence"))
        for k in range(4):
            for dx in range(-3 + k, 4 - k):
                for dz in range(-3 + k, 4 - k):
                    if abs(dx) == 3 - k or abs(dz) == 3 - k:
                        a.set(tx + dx, ty + 12 + k, tz + dz, B("spruce_planks") if k < 3 else B("spruce_slab"))
        for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            for y in range(ty + 10, ty + 12):
                a.set(tx + dx, y, tz + dz, B("spruce_fence"))
        for y in range(ty, ty + 9):
            a.set(tx, y, tz - 3, B("ladder", facing_direction=2))
        a.set(tx, ty + 8, tz - 3, AIR)
        a.set(tx, ty + 9, tz, B("lantern"))
        # broken carts: plank beds, a wheel of dark oak trapdoor discs, spilled barrels
        for (lx, lz, along) in ((104, 116, "x"), (122, 100, "z"), (98, 102, "z")):
            x, y, z = self._at(lx, lz)
            for k in range(4):
                for w in range(2):
                    xx, zz = (x + k, z + w) if along == "x" else (x + w, z + k)
                    if rng.random() < 0.8:
                        a.set(xx, y, zz, B("spruce_slab"))
            wx, wz = (x + 1, z - 1) if along == "x" else (x - 1, z + 1)
            a.set(wx, y, wz, B("dark_oak_trapdoor", direction=0, open_bit=True))
            P.barrels(a, x + (5 if along == "x" else 2), y, z + (0 if along == "x" else 5), rng, 2)
        # trophy poles with skulls, hide racks, the cold fire
        for (lx, lz) in ((110, 104), (120, 118), (106, 112), (126, 112)):
            x, y, z = self._at(lx, lz)
            for k in range(3):
                a.set(x, y + k, z, B("spruce_fence"))
            a.set(x, y + 3, z, B(rng.choice(["skeleton_skull", "skeleton_skull", "creeper_head"]), facing_direction=1))
        x, y, z = self._at(116, 110)
        a.set(x, y - 1, z, B("cobblestone"))
        a.set(x, y, z, B("campfire", extinguished=True))
        for k in range(6):
            ang = k / 6 * 2 * math.pi
            a.put(int(round(x + math.cos(ang) * 3)), y, int(round(z + math.sin(ang) * 3)), B("soul_lantern"))
        for (lx, lz) in ((102, 120), (130, 120)):
            x, y, z = self._at(lx, lz)
            for k in range(5):
                a.set(x + k, y + 2, z, B("spruce_fence"))
            a.set(x, y, z, B("spruce_fence"))
            a.set(x, y + 1, z, B("spruce_fence"))
            a.set(x + 4, y, z, B("spruce_fence"))
            a.set(x + 4, y + 1, z, B("spruce_fence"))
            for k in range(1, 4):
                a.set(x + k, y + 1, z, B("brown_wool") if k != 2 else B("white_wool"))
        self.add_zone("c4", self.zbox("c4"), floor_mask=self.carved)

    # ------------------------------------------------------------ c5: the giant mushroom cave
    def mushroom_cave(self):
        a, rng = self.a, self.rng
        m5 = self.masks["c5"]
        d5 = distance_transform_edt(~m5)
        others = np.zeros_like(m5)
        for k, m in self.masks.items():
            if k != "c5":
                others |= m
        roof = self.carved & (d5 <= 9) & ~others
        cx, cz = 60, 74
        rx, rz = self.ZN["c5"][2], self.ZN["c5"][3]
        n = fbm(self.sx, self.sz, 7, 2, self.seed + 55)
        self.c5_ceiling = {}
        for (i, k) in np.argwhere(roof):
            f = int(self.H[i, k])
            dd = math.hypot((i - cx) / (rx * 1.15), (k - cz) / (rz * 1.15))
            dome = math.sqrt(max(0.0, 1 - dd * dd))
            hgt = int(7 + 15 * dome + (n[i, k] - 0.5) * 4) if m5[i, k] else 7
            c = f + hgt
            top = max(c + 6, int(np.max(self.H[max(0, i - 8):i + 9, max(0, k - 8):k + 9])))
            top = min(top, self.Y0 + self.SY - 6)
            x, z = self.x0 + i, self.z0 + k
            col = a.blk[i, :, k]
            for y in range(c + 1, top + 1):
                col[y - self.Y0] = B("stone") if (y + i // 5) % 7 else B("tuff")
            col[top - self.Y0] = B("stone")
            self.c5_ceiling[(i, k)] = c
        # mycelium and moss floor
        floor = mixer(rng, [(B("mycelium"), 5), (B("podzol"), 2), (B("moss_block"), 1), (B("coarse_dirt"), 1)])
        for (i, k) in np.argwhere(roof):
            a.blk[i, int(self.H[i, k]) - self.Y0, k] = floor()
        # giant mushrooms (red and brown), keep a winding lane free
        placed = []
        for _ in range(400):
            lx, lz = rng.randint(30, 92), rng.randint(52, 98)
            if not m5[lx, lz] or self.wall_dist[lx, lz] > 0:
                continue
            if any(math.hypot(lx - p[0], lz - p[1]) < 9 for p in placed):
                continue
            c = self.c5_ceiling.get((lx, lz))
            f = int(self.H[lx, lz])
            if c is None or c - f < 12:
                continue
            x, y, z = self._at(lx, lz)
            self.giant_mushroom(x, y, z, min(c - f - 3, rng.randint(9, 15)), rng.random() < 0.5)
            placed.append((lx, lz))
            if len(placed) >= 9:
                break
        # small mushrooms, shroomlights in the floor, glow lichen on the ceiling
        for (i, k) in np.argwhere(roof):
            x, z = self.x0 + i, self.z0 + k
            f = int(self.H[i, k])
            r = rng.random()
            if a.get(x, f + 1, z) != AIR:
                continue
            if r < 0.06:
                a.set(x, f + 1, z, B(rng.choice(["red_mushroom", "brown_mushroom"])))
            elif r < 0.075:
                a.set(x, f, z, B("shroomlight"))
            c = self.c5_ceiling[(i, k)]
            if rng.random() < 0.06 and a.get(x, c + 1, z) != AIR and a.get(x, c, z) == AIR:
                a.set(x, c, z, B("glow_lichen", multi_face_direction_bits=2))
            elif rng.random() < 0.01 and a.get(x, c + 1, z) != AIR:
                hanging_lamp(a, x, c, z, 2)
        self.roof5 = roof
        self.add_zone("c5", self.zbox("c5", dy=(-4, 14)), floor_mask=self.carved)

    def giant_mushroom(self, x, y, z, h, red):
        a = self.a
        stem = B("mushroom_stem", huge_mushroom_bits=15)
        for k in range(h):
            for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)) if h > 11 else ((0, 0),):
                a.set(x + dx, y + k, z + dz, stem)
        cap = B("red_mushroom_block", huge_mushroom_bits=14) if red else B("brown_mushroom_block", huge_mushroom_bits=14)
        r = 4.5 if red else 6.0
        ox, oz = (0.5, 0.5) if h > 11 else (0, 0)
        if red:
            for dy in range(0, 4):
                rr = r * math.sqrt(max(0, 1 - (dy / 4.0) ** 2))
                for dx in range(-6, 8):
                    for dz in range(-6, 8):
                        d = math.hypot(dx - ox, dz - oz)
                        if rr - 1.2 < d <= rr or (dy == 3 and d <= rr):
                            a.set(x + dx, y + h - 2 + dy, z + dz, cap)
            for k in range(3):
                a.put(x + k * 2 - 2, y + h - 3, z + 3, B("shroomlight"))
        else:
            for dx in range(-7, 9):
                for dz in range(-7, 9):
                    d = math.hypot(dx - ox, dz - oz)
                    if d <= r:
                        a.set(x + dx, y + h, z + dz, cap)
                        if r - 1 < d:
                            a.set(x + dx, y + h - 1, z + dz, cap)
            a.set(x, y + h - 1, z, B("shroomlight"))

    # ------------------------------------------------------------ c6: troll den
    def troll_den(self):
        a, rng = self.a, self.rng
        cx, cy, cz = self._at(118, 46)
        # bone heaps
        for _ in range(14):
            lx, lz = rng.randint(92, 148), rng.randint(30, 64)
            if not self.free(lx, lz):
                continue
            x, y, z = self._at(lx, lz)
            r = rng.uniform(1.3, 2.6)
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    dd = math.hypot(dx, dz)
                    if dd <= r:
                        for t in range(int((r - dd) * 0.9) + 1):
                            a.put(x + dx, y + t, z + dz, B("bone_block", axis=rng.choice(["x", "y", "z"])))
            if rng.random() < 0.5:
                a.put(x, y + int(r), z, B("skeleton_skull", facing_direction=1))
        # the hearth: a big firepit with a cauldron on stones, spits of meat
        a.set(cx, cy - 1, cz, B("magma"))
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                d = math.hypot(dx, dz)
                if 2.2 < d <= 3.4:
                    a.set(cx + dx, cy, cz + dz, B("cobblestone") if (dx + dz) % 2 else B("blackstone"))
                elif d <= 2.2:
                    a.set(cx + dx, cy - 1, cz + dz, B("netherrack"))
                    a.set(cx + dx, cy, cz + dz, B("fire") if d < 1.6 else AIR)
        for (dx, dz) in ((-3, 0), (3, 0)):
            for y in range(cy + 1, cy + 5):
                a.set(cx + dx, y, cz + dz, B("spruce_log", axis="y"))
        for dx in range(-3, 4):
            a.set(cx + dx, cy + 5, cz, B("spruce_log", axis="x"))
        a.set(cx, cy + 4, cz, B("chain"))
        a.set(cx, cy + 3, cz, B("cauldron", cauldron_liquid="lava", fill_level=6))
        # troll-sized stone table and seats
        tx, ty, tz = self._at(132, 38)
        for dx in range(-3, 4):
            for dz in range(-2, 3):
                a.set(tx + dx, ty + 2, tz + dz, B("smooth_stone"))
        for (dx, dz) in ((-3, -2), (3, -2), (-3, 2), (3, 2)):
            for y in range(ty, ty + 2):
                a.set(tx + dx, y, tz + dz, B("stone_bricks"))
        for (dx, dz) in ((-6, 0), (6, 0)):
            for y in range(ty, ty + 2):
                for w in range(-1, 2):
                    a.set(tx + dx, y, tz + dz + w, B("cobblestone"))
        a.set(tx - 1, ty + 3, tz, B("cauldron", cauldron_liquid="water", fill_level=3))
        a.set(tx + 1, ty + 3, tz, B("skeleton_skull", facing_direction=1))
        # loot piles: chests, barrels, raw iron and copper, hide tents
        for (lx, lz) in ((102, 36), (140, 54), (108, 58)):
            x, y, z = self._at(lx, lz)
            P.barrels(a, x, y, z, rng, 3)
            a.put(x + 2, y, z + 1, B("chest", cardinal="south"))
            a.put(x - 2, y, z, B("raw_iron_block"))
            a.put(x - 2, y, z + 1, B("raw_copper_block"))
        for (lx, lz) in ((96, 48), (140, 40)):
            x, y, z = self._at(lx, lz)
            for dz in range(-3, 4):
                for k in range(4):
                    a.set(x - 3 + k, y + k, z + dz, B("brown_wool") if (dz + k) % 3 else B("light_gray_wool"))
                    a.set(x + 3 - k, y + k, z + dz, B("brown_wool") if (dz + k) % 3 else B("light_gray_wool"))
            for k in range(1, 3):
                a.set(x, y + k, z - 3, AIR)
        self.add_zone("c6", self.zbox("c6"), floor_mask=self.carved)

    # ------------------------------------------------------------ boss: Griotunagard, the summit duelling ring
    def summit(self):
        a, rng = self.a, self.rng
        L = self.L
        cx, cz = L(56, 26)
        y = self.ZN["boss"][4] + 1
        R = 16

        def floor_fn(x, z, d):
            dx, dz = x - cx, z - cz
            # Hrungnir's three-horned stone heart in the middle
            ang = math.atan2(dz, dx)
            tri = d * math.cos((ang + math.pi / 2) % (2 * math.pi / 3) - math.pi / 3)
            if tri < 4.2 and tri > 3.0:
                return B("red_nether_brick")
            if tri <= 3.0:
                return B("polished_granite") if d > 1.2 else B("magma")
            if d > R - 1.2:
                return B("polished_andesite")
            if abs(d - 9) < 0.6:
                return B("chiseled_stone_bricks") if int(ang * 8) % 2 else B("stone_bricks")
            n = (x * 7 + z * 13) % 11
            return B("stone") if n < 4 else B("andesite") if n < 7 else B("cobblestone") if n < 9 else B("cracked_stone_bricks")
        ar = self.arena("boss", cx, y, cz, R, "hrungnir", "final", floor_fn=floor_fn)
        # lightning scorch marks
        for _ in range(9):
            ang, r = rng.uniform(0, 6.28), rng.uniform(5, R - 2)
            x, z = int(cx + math.cos(ang) * r), int(cz + math.sin(ang) * r)
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    if rng.random() < 0.7:
                        a.set(x + dx, y - 1, z + dz, B("blackstone") if rng.random() < 0.6 else B("basalt", pillar_axis="y"))
        # standing stones around the ring, open towards the path (east)
        for k in range(16):
            ang = k / 16 * 2 * math.pi
            if math.cos(ang) > 0.75:
                continue
            x, z = int(round(cx + math.cos(ang) * (R + 2))), int(round(cz + math.sin(ang) * (R + 2)))
            t = P.surface_y(a, x, z)
            if t is None:
                continue
            P.runestone(a, x, y, z, rng, h=rng.randint(5, 8), mat="stone")
        # shattered whetstone fragments on the ring edge
        for k in range(5):
            ang = rng.uniform(0, 6.28)
            r = rng.uniform(R - 5, R - 2)
            x, z = int(cx + math.cos(ang) * r), int(cz + math.sin(ang) * r)
            for dx in range(-1, 2):
                for dz in range(-1, 1):
                    for dy in range(rng.randint(1, 2)):
                        a.set(x + dx, y + dy, z + dz, B("smooth_stone") if (dx + dy) % 2 else B("polished_diorite"))
        # Mokkurkalfi, the clay giant, lying broken on the north rim
        mx, mz = cx - 2, cz - R - 1
        body = [(mx - 10, y + 1, mz - 1), (mx - 3, y + 2, mz - 2), (mx + 4, y + 2, mz - 1)]
        for (bx, by, bz) in body:
            ell(a, bx, by, bz, 3.6, 2.2, 2.8, B("packed_mud"))
        ell(a, mx + 9, y + 2, mz - 2, 2.6, 2.4, 2.6, B("mud_bricks"))
        a.set(mx + 10, y + 3, mz, B("magma"))
        for (p0, p1) in (((mx - 3, y + 2, mz), (mx - 6, y + 1, mz + 5)), ((mx + 2, y + 2, mz - 4), (mx + 8, y + 1, mz - 7))):
            thick_line(a, p0, p1, 1.2, B("packed_mud"))
        for _ in range(30):
            px, pz = mx + rng.randint(-14, 12), mz + rng.randint(-6, 6)
            t = P.surface_y(a, px, pz)
            if t is not None and a.get(px, t + 1, pz) == AIR and rng.random() < 0.5:
                a.set(px, t + 1, pz, B(rng.choice(["mud_brick_slab", "packed_mud", "brown_terracotta"])))
        # exit: a tunnel west through the crag, gated, to the rune circle
        ex, ez = cx - R - 13, cz + 2
        for x in range(ex - 4, ex + 5):
            for z in range(ez - 4, ez + 5):
                a.set(x, y - 1, z, B("stone_bricks"))
                for yy in range(y, y + 6):
                    a.set(x, yy, z, AIR if max(abs(x - ex), abs(z - ez)) < 4 else B("stone_bricks"))
        for x in range(ex + 4, cx - R + 3):
            for w in range(-2, 3):
                edge = abs(w) == 2
                a.set(x, y - 1, ez + w, B("stone_bricks"))
                for yy in range(y, y + 4):
                    inner = not edge and yy < y + 3
                    if inner:
                        a.set(x, yy, ez + w, AIR)
                    elif x < cx - R - 2 and a.get(x, yy, ez + w) == AIR:
                        a.set(x, yy, ez + w, B("stone_bricks"))
        gx = cx - R - 6
        ar["exit"] = [list(p) for p in self.doorway(gx, y, ez, 3, 3, "z")]
        for yy in range(y, y + 4):
            for w in (-2, 2):
                a.set(gx, yy, ez + w, B("chiseled_stone_bricks"))
        for w in range(-2, 3):
            a.set(gx, y + 3, ez + w, B("chiseled_stone_bricks"))
        self.exit_portal(ex, y, ez)
        self.close([tuple(p) for p in ar["exit"]])

    # ------------------------------------------------------------ finishing
    def finish(self):
        a, rng = self.a, self.rng

        def tree(a_, x, y, z, r):
            if y < 110:
                spruce_tree(a_, x, y, z, r, h=r.randint(7, 12))
            else:
                a_.set(x, y, z, B("short_grass"))
        carved = self.carved & ~getattr(self, "roof5", np.zeros_like(self.carved))
        self.dress_walls(carved, [B("stone"), B("stone"), B("andesite"), B("stone"), B("tuff"), B("andesite")],
                         rim=dict(tree=tree, plants=["short_grass", "fern", "short_grass"], bush=B("spruce_leaves", persistent_bit=1)),
                         rim_trees=0.012, moss=0.07, vines=0.08)
        # sparse alpine flowers on the higher meadows
        for _ in range(500):
            lx, lz = rng.randint(6, self.sx - 7), rng.randint(6, 236)
            if not self.free(lx, lz) or self.roof5[lx, lz]:
                continue
            x, y, z = self._at(lx, lz)
            if a.get(x, y, z) != AIR or a.get(x, y - 1, z) not in (B("grass_block"), B("coarse_dirt")):
                continue
            q = rng.random()
            if q < 0.3:
                a.set(x, y, z, B(rng.choice(["short_grass", "short_grass", "fern", "azure_bluet", "oxeye_daisy", "cornflower"])))
            elif q < 0.33 and y < 100:
                spruce_tree(a, x, y, z, rng, h=rng.randint(7, 10))
        for key in ("c5",):
            x1, y1, z1, x2, y2, z2 = self.zones[key]["box"]
            self.light_fill((x1, z1, x2, z2), (y1, y2), level=7, threshold=4, spacing=7)
        ar = self.arenas[0]
        self.light_fill((int(ar["x"]) - 18, int(ar["z"]) - 18, int(ar["x"]) + 18, int(ar["z"]) + 18), (ar["y"] - 1, ar["y"] + 2), level=8, threshold=5, spacing=6)
        self.ambient = [dict(box=self.zones["c3"]["box"], particle="minecraft:water_splash_particle_manual", rate=1),
                        dict(box=self.zones["c5"]["box"], particle="minecraft:spore_blossom_ambient_particle", rate=3),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:campfire_smoke_particle", rate=1)]
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        a.fix_walls()

    def is_escape(self, x, y, z):
        i, k = x - self.x0, z - self.z0
        if self._allowed is None:
            self._allowed = binary_dilation(self.carved | self.lake, iterations=4)
        if self._allowed[i, k]:
            # inside the dungeon's footprint, but standing on the mushroom-cave roof would be outside
            if self.roof5[i, k] and y > self.c5_ceiling.get((i, k), 999) + 1:
                return True
            return False
        return all(self.a.get(x, yy, z) == AIR for yy in range(y + 2, y + 10))

    _allowed = None


def build(seed=1):
    d = Hrungnir("d04", seed)
    d.build()
    return d


if __name__ == "__main__":
    import time
    t0 = time.time()
    d = build()
    print("built %.1fs" % (time.time() - t0))
