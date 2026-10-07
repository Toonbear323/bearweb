"""Dungeon 10 — 비프로스트와 신들의 황혼 (Bifrost & Ragnarok). High tier, 272 x 448, islands in the sky over the world sea.

The way: from the foot of Bifrost (the flying ship Skidbladnir is moored there) along the rainbow bridge to Heimdall's
Himinbjorg and the Gjallarhorn over its gate; down onto the sea wall where Jormungandr rises beside the bastion
(mid-boss 1); across to Valhalla's hall roofed with golden shields; west to the plain of Idavoll and its golden game
boards; over to Loki's isle (mid-boss 2); south to burning Vigrid; and at last the shattered island under the burning
branch of Yggdrasil, where Fenrir has broken his chain.

Only islands and bridges can be walked; every edge is closed by an invisible wall, and the gates stand on bridges, so
nothing can be walked around. Local coordinates: x 0..271 (west -> east), z 0..447 (north -> south).
"""
import math

import numpy as np

from mcw import B, AIR, PAL
from gen_common import fbm, stair, slab, standing_sign, line_points, leaf_blob, leaves_of
import nr_parts as P
import nr_castle as C
from nr_dungeon import Dungeon, mixer
from nr_spawn import cyl, ell, thick_line

SEA = 62

ISL = {
    "start": (136, 414, 54, 22, 100),
    "c2": (136, 250, 60, 32, 110),
    "c3": (170, 176, 70, 16, 108),
    "a1": (236, 114, 22, 22, 108),
    "c4": (156, 62, 50, 22, 112),
    "c5": (48, 62, 34, 28, 112),
    "a2": (46, 150, 22, 22, 112),
    "c6": (34, 246, 26, 38, 110),
    "boss": (40, 340, 30, 30, 108),
    "frag": (40, 398, 11, 9, 108),
}


class Ragnarok(Dungeon):
    Y0, SY = 48, 128            # 48..175

    def build(self):
        rng = self.rng
        self.walk = np.zeros((self.sx, self.sz), bool)
        self.F = np.full((self.sx, self.sz), -1, np.int32)
        self.H = np.zeros((self.sx, self.sz), np.int32)
        self.pal = C.Pal(rng, wall=[("quartz_bricks", 4), ("calcite", 2), ("smooth_quartz", 1)], trim="gold_block",
                         floor=[("polished_diorite", 3), ("quartz_bricks", 2), ("smooth_stone", 1)], roof="quartz",
                         pillar="quartz_pillar", window="yellow_stained_glass_pane", light="lantern", accent="gold_block",
                         top="diorite_wall", plank="birch_planks")
        self.sea()
        self.top_mix = mixer(rng, [(B("grass_block"), 8), (B("moss_block"), 1), (B("coarse_dirt"), 1)])
        for key in ISL:
            self.island(key)
        self.bridges()
        self.foot_of_bifrost()
        self.rainbow()
        self.himinbjorg()
        self.sea_wall()
        self.bastion()
        self.valhalla()
        self.idavoll()
        self.loki_isle()
        self.vigrid()
        self.shattered()
        self.finish()

    # ------------------------------------------------------------ helpers
    def w(self, lx, lz):
        return self.x0 + lx, self.z0 + lz

    def at(self, lx, lz):
        x, z = self.w(lx, lz)
        return x, int(self.F[lx, lz]) + 1, z

    def free(self, lx, lz):
        if not (0 <= lx < self.sx and 0 <= lz < self.sz) or not self.walk[lx, lz]:
            return False
        x, y, z = self.at(lx, lz)
        return self.a.get(x, y, z) == AIR and self.a.get(x, y + 1, z) == AIR

    def zbox(self, key, pad=0, dy=(-2, 6)):
        cx, cz, rx, rz, f = ISL[key]
        x, z = self.w(cx, cz)
        return (x - rx - pad, f + dy[0], z - rz - pad, x + rx + pad, f + dy[1], z + rz + pad)

    def mask_of(self, key, shrink=0.0):
        cx, cz, rx, rz, f = ISL[key]
        X, Z = self.X - self.x0, self.Z - self.z0
        return (np.hypot((X - cx) / rx, (Z - cz) / rz) < 1 - shrink) & self.walk

    # ------------------------------------------------------------ the world sea far below
    def sea(self):
        a = self.a
        a.blk[:, 0, :] = B("sand")
        a.blk[:, 1:SEA - self.Y0 + 1, :] = B("water")
        a.bio[:, :] = 186                 # meadow
        a.bio[:, 300:] = 192              # cherry grove at the foot of Bifrost

    # ------------------------------------------------------------ islands and bridges
    def island(self, key):
        a, rng = self.a, self.rng
        cx, cz, rx, rz, f = ISL[key]
        n = fbm(self.sx, self.sz, 9, 3, self.seed + sum(map(ord, key)))
        n2 = fbm(self.sx, self.sz, 5, 2, self.seed + 7 + sum(map(ord, key)))
        rock = [B("stone"), B("andesite"), B("diorite"), B("stone"), B("calcite"), B("tuff")]
        for i in range(max(1, cx - rx - 4), min(self.sx - 1, cx + rx + 5)):
            for k in range(max(1, cz - rz - 4), min(self.sz - 1, cz + rz + 5)):
                d = math.hypot((i - cx) / rx, (k - cz) / rz) * (1 + (n[i, k] - 0.5) * 0.18)
                if d > 1:
                    continue
                depth = int(6 + 30 * (1 - d) ** 0.7 + n2[i, k] * 8)
                bottom = max(f - 1 - depth, SEA + 8)
                col = a.blk[i, :, k]
                for y in range(bottom, f - 1):
                    col[y - self.Y0] = B("dirt") if y >= f - 4 else rock[(y // 4 + i // 9) % len(rock)]
                col[f - 1 - self.Y0] = self.top_mix()
                if rng.random() < 0.05 and d > 0.75:
                    for t in range(1, rng.randint(3, 9)):
                        col[bottom - t - self.Y0] = B("hanging_roots") if t > 1 else B("dirt_with_roots")
                self.walk[i, k] = True
                self.F[i, k] = f - 1
                self.H[i, k] = f - 1

    BRIDGES = [
        # (points, width, kind, from-floor, to-floor, arch)
        ([(150, 220), (150, 192)], 9, "stone", 110, 108, 0),
        ([(230, 168), (230, 134)], 9, "stone", 108, 108, 0),
        ([(236, 94), (236, 62), (204, 62)], 9, "stone", 108, 112, 0),
        ([(108, 62), (80, 62)], 9, "stone", 112, 112, 0),
        ([(46, 88), (46, 130)], 9, "stone", 112, 112, 0),
        ([(42, 170), (38, 210)], 9, "stone", 112, 110, 0),
        ([(36, 282), (38, 312)], 9, "stone", 110, 108, 0),
        ([(40, 368), (40, 391)], 7, "stone", 108, 108, 0),
    ]

    def bridge_cells(self, pts, width):
        cells = {}
        total = sum(math.dist(p, q) for p, q in zip(pts[:-1], pts[1:]))
        acc = 0.0
        r = width / 2.0
        for p, q in zip(pts[:-1], pts[1:]):
            L = math.dist(p, q)
            for s in np.arange(0, L + 0.01, 0.4):
                u = (acc + s) / total
                x = p[0] + (q[0] - p[0]) * s / max(L, 1e-6)
                z = p[1] + (q[1] - p[1]) * s / max(L, 1e-6)
                for dx in range(-int(r) - 1, int(r) + 2):
                    for dz in range(-int(r) - 1, int(r) + 2):
                        if max(abs(dx), abs(dz)) <= r - 0.5:
                            c = (int(round(x + dx)), int(round(z + dz)))
                            cells.setdefault(c, u)
            acc += L
        return cells

    def bridges(self):
        a = self.a
        stone = mixer(self.rng, [(B("polished_diorite"), 3), (B("quartz_bricks"), 2), (B("smooth_stone"), 1)])
        for (pts, width, kind, f0, f1, arch) in self.BRIDGES:
            cells = self.bridge_cells(pts, width)
            for (i, k), u in cells.items():
                if self.walk[i, k] and self.F[i, k] >= 0 and not self.is_bridge_cell(i, k):
                    continue
                f = int(round(f0 + (f1 - f0) * u + arch * math.sin(math.pi * u))) - 1
                x, z = self.w(i, k)
                a.set(x, f, z, stone())
                a.set(x, f - 1, z, B("quartz_bricks"))
                if (i + k) % 7 == 0:
                    for t in range(2, 5):
                        a.set(x, f - t, z, B("chain"))
                self.walk[i, k] = True
                self.F[i, k] = f
                self.H[i, k] = f
                self.bridge_mask[i, k] = True

    def is_bridge_cell(self, i, k):
        return bool(self.bridge_mask[i, k])

    @property
    def bridge_mask(self):
        if not hasattr(self, "_bm"):
            self._bm = np.zeros((self.sx, self.sz), bool)
        return self._bm

    def gate_bridge(self, lx, lz, axis, half, gw=7, gh=7, height=11):
        """A wall across a bridge with a doorway; returns the doorway cells (the gate)."""
        a, pal = self.a, self.pal
        f = int(self.F[lx, lz]) + 1
        cells = [(lx, lz + t) for t in range(-half, half + 1)] if axis == "x" else [(lx + t, lz) for t in range(-half, half + 1)]
        for (i, k) in cells:
            x, z = self.w(i, k)
            for y in range(f, f + height):
                a.set(x, y, z, pal.wall() if (y - f) % 5 != 4 else pal.trim)
            a.set(x, f + height, z, pal.top)
            for y in range(f + height + 1, f + height + 4):
                a.set(x, y, z, B("barrier"))
        x, z = self.w(lx, lz)
        door = self.doorway(x, f, z, gw, gh, "z" if axis == "x" else "x")
        for p in door:
            a.set(*p, AIR)
        for t in range(-(gw // 2) - 1, gw // 2 + 2):
            gx, gz = (x, z + t) if axis == "x" else (x + t, z)
            a.set(gx, f + gh, gz, pal.trim)
        return door

    # ------------------------------------------------------------ start: the foot of Bifrost
    def foot_of_bifrost(self):
        a, rng = self.a, self.rng
        cx, cz, rx, rz, f = ISL["start"]
        # Skidbladnir, the ship that sails the sky, moored at a pier off the east edge
        for lx in range(184, 196):
            for lz in range(410, 415):
                x, z = self.w(lx, lz)
                a.set(x, f - 1, z, B("birch_planks"))
                a.set(x, f - 2, z, B("stripped_birch_log", axis="x"))
                self.walk[lx, lz] = True
                self.F[lx, lz] = f - 1
        sx, sz = self.w(194, 426)
        info = P.longship(a, sx, f - 2, sz, "north", rng, length=27, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        dx1, dy1, dz1, dx2, dy2, dz2 = info["deck"]
        for x in range(dx1 - 6, dx2 + 7):
            for z in range(dz1 - 6, dz2 + 7):
                li, lk = x - self.x0, z - self.z0
                if not (0 <= li < self.sx and 0 <= lk < self.sz) or self.walk[li, lk]:
                    continue
                # a hull column is walkable when it has a block at deck level; everything else gets the barriers
                if a.get(x, dy1 - 1, z) != AIR:
                    self.walk[li, lk] = True
                    self.F[li, lk] = dy1 - 1
        ax, ay, az = self.at(136, 404)
        self.data["start"] = [ax + 0.5, ay, az + 0.5, 180]
        self.walk_seeds = [(ax, ay, az)]
        standing_sign(a, ax + 3, ay, az, 8, "§l§e비프로스트와 신들의 황혼\n§r§f무지개 다리를 건너\n§f아스가르드로\n§7펜리르가 사슬을 끊었다", kind="birch_standing_sign")
        # Heimdall's watch post at the bridge foot, cherry trees and flowers
        for s in (-1, 1):
            tx, ty, tz = self.at(136 + s * 10, 394)
            C.tower(a, tx, tz, ty, 14, 3, self.pal, roof="cone", windows=False, foot=2)
        from gen_common import cherry_tree
        for _ in range(60):
            lx, lz = rng.randint(cx - rx + 4, cx + rx - 4), rng.randint(cz - rz + 3, cz + rz - 3)
            if not self.free(lx, lz) or abs(lx - 136) < 8:
                continue
            x, y, z = self.at(lx, lz)
            r = rng.random()
            if r < 0.12:
                cherry_tree(a, x, y, z, rng)
            elif r < 0.6:
                a.set(x, y, z, B(rng.choice(["short_grass", "pink_petals", "dandelion", "poppy", "allium", "cornflower"])))

    # ------------------------------------------------------------ c1: the rainbow bridge
    def rainbow(self):
        a, rng = self.a, self.rng
        colors = ["red", "orange", "yellow", "lime", "light_blue", "blue", "purple"]
        x0b, x1b = 131, 141
        z_from, z_to = 393, 281
        f0, f1 = 100, 110
        L = z_from - z_to
        for lz in range(z_to, z_from + 1):
            u = (z_from - lz) / float(L)
            f = int(round(f0 + (f1 - f0) * u + 6 * math.sin(math.pi * u))) - 1
            wide = abs(lz - 352) < 7 or abs(lz - 318) < 7
            xa, xb = (x0b - 5, x1b + 5) if wide else (x0b, x1b)
            for lx in range(xa, xb + 1):
                x, z = self.w(lx, lz)
                c = colors[min(6, max(0, (lx - x0b) * 7 // (x1b - x0b + 1)))] if x0b <= lx <= x1b else "white"
                a.set(x, f, z, B(c + "_stained_glass"))
                if not self.walk[lx, lz] or self.F[lx, lz] < 0:
                    self.walk[lx, lz] = True
                    self.F[lx, lz] = f
                    self.H[lx, lz] = f
                for y in range(f + 1, f + 6):
                    if a.get(x, y, z) != AIR and not (self.walk[lx, lz] and y <= self.F[lx, lz]):
                        a.set(x, y, z, AIR)
            for lx in (xa - 1, xb + 1):
                x, z = self.w(lx, lz)
                a.set(x, f + 1, z, B("white_stained_glass_pane"))
            if lz % 10 == 0:
                for lx in (xa, xb):
                    x, z = self.w(lx, lz)
                    a.set(x, f + 1, z, B("gold_block"))
                    a.set(x, f + 2, z, B("campfire"))
        self.add_zone("c1", (self.x0 + x0b - 5, 96, self.z0 + 286, self.x0 + x1b + 5, 120, self.z0 + 388), floor_mask=None, n=10)

    # ------------------------------------------------------------ c2: Himinbjorg and the Gjallarhorn
    def himinbjorg(self):
        a, rng, pal = self.a, self.rng, self.pal
        cx, cz, rx, rz, f = ISL["c2"]
        # a ring wall around the north part of the island with the great gate where the bridge to the sea wall leaves
        for t in range(240):
            ang = math.pi + t / 239.0 * math.pi
            lx, lz = int(round(cx + math.cos(ang) * (rx - 6))), int(round(cz + math.sin(ang) * (rz - 5)))
            if abs(lx - 150) < 7 and lz < cz:
                continue
            x, z = self.w(lx, lz)
            for y in range(f, f + 12):
                a.set(x, y, z, pal.wall() if (y - f) % 5 != 4 else pal.trim)
            a.set(x, f + 12, z, pal.top if t % 2 else pal.wall())
            self.walk[lx, lz] = False
        gx, gz = self.w(150, cz - rz + 5)
        for s in (-1, 1):
            C.tower(a, gx + s * 9, gz, f, 22, 4, pal, roof="cone", windows=True, foot=4)
        for dx in range(-6, 7):
            for y in range(f + 9, f + 13):
                a.set(gx + dx, y, gz, pal.wall() if y > f + 9 else pal.trim)
        # the Gjallarhorn hung over the gate on golden chains
        hx, hy, hz = gx, f + 18, gz + 2
        for t in range(0, 40):
            u = t / 39.0
            px = hx - 14 + 28 * u
            py = hy + 3 * math.sin(math.pi * u) - 2 * u
            r = 0.6 + 2.6 * u
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    for dz in range(-4, 5):
                        d = math.sqrt(dx * dx + dy * dy + dz * dz)
                        if r - 1.0 < d <= r:
                            b = B("gold_block") if t % 9 == 0 or t > 36 else B("bone_block", axis="x") if t % 2 else B("calcite")
                            a.set(int(round(px + dx)), int(round(py + dy)), int(round(hz + dz)), b)
        for s in (-10, 10):
            for y in range(hy + 3, f + 22):
                a.set(hx + s, y, hz, B("chain"))
        # Heimdall's hall in the south-west of the island, watch braziers, banners
        hx1, hz1 = self.w(cx - 40, cz + 6)
        C.hall(a, hx1, hz1, hx1 + 22, hz1 + 14, f, 8, pal, roof="gable", axis="x", doors=[("north", 0, 3, 4)], lights=True, foot=2)
        for lx in range(cx - 40, cx - 17):
            for lz in range(cz + 6, cz + 21):
                self.walk[lx, lz] = self.walk[lx, lz] and not (cx - 40 <= lx <= cx - 18 and cz + 6 <= lz <= cz + 20)
        for _ in range(40):
            lx, lz = rng.randint(cx - rx + 6, cx + rx - 6), rng.randint(cz - rz + 6, cz + rz - 4)
            if not self.free(lx, lz):
                continue
            x, y, z = self.at(lx, lz)
            r = rng.random()
            if r < 0.15:
                P.brazier(a, x, y, z, soul=False, base="cobblestone")
            elif r < 0.25:
                for k in range(5):
                    a.set(x, y + k, z, B("birch_fence"))
                for k in range(1, 5):
                    a.set(x + 1, y + k, z, B("blue_wool") if k > 1 else B("white_wool"))
                a.set(x, y + 5, z, B("lantern"))
            else:
                a.set(x, y, z, B(rng.choice(["short_grass", "dandelion", "cornflower", "oxeye_daisy"])))
        self.add_zone("c2", self.zbox("c2"), floor_mask=None, n=10)

    # ------------------------------------------------------------ c3: the sea wall and the rising serpent
    def sea_wall(self):
        a, rng, pal = self.a, self.rng, self.pal
        cx, cz, rx, rz, f = ISL["c3"]
        # the rampart: a paved walk with crenellations along the sea (north) side, towers at intervals
        for (i, k) in np.argwhere(self.mask_of("c3")):
            x, z = self.w(i, k)
            a.set(x, f - 1, z, pal.floor())
            a.set(x, f - 2, z, pal.wall())
        for lx in range(cx - rx + 8, cx + rx - 7, 22):
            if abs(lx - 230) < 8:
                continue
            k = cz - int(rz * math.sqrt(max(0.0, 1 - ((lx - cx) / float(rx)) ** 2))) + 3
            x, z = self.w(lx, k)
            C.tower(a, x, z, f, 18, 3, pal, roof="cone", windows=False, foot=8)
        # Jormungandr's coils breaking the sea north of the wall
        body = mixer(rng, [(B("dark_prismarine"), 4), (B("prismarine_bricks"), 2), (B("warped_wart_block"), 1)])
        for (ccx, ccz, r) in ((120, 140, 9), (160, 132, 11), (200, 150, 8)):
            for t in range(0, 31):
                ang = math.pi * t / 30
                x = self.x0 + ccx + math.cos(ang) * r
                y = SEA + math.sin(ang) * r * 1.6
                z = self.z0 + ccz
                ell(a, x, y, z, 2.6, 2.6, 2.6, body())
        self.add_zone("c3", self.zbox("c3"), floor_mask=None, n=12)

    def bastion(self):
        a, rng, pal = self.a, self.rng, self.pal
        cx, cz, rx, rz, f = ISL["a1"]
        entry = self.gate_bridge(230, 140, "z", 6)
        exitg = self.gate_bridge(236, 88, "z", 6)
        x, z = self.w(cx, cz)
        R = 19

        def floor_fn(xx, zz, d):
            ang = math.atan2(zz - z, xx - x)
            coil = abs(math.sin(ang * 3 + d * 0.4)) < 0.15 and 4 < d < R - 2
            if d > R - 1.2:
                return B("gold_block") if (xx + zz) % 3 == 0 else B("quartz_bricks")
            if coil:
                return B("dark_prismarine")
            return B("polished_diorite") if (int(d) + (xx + zz) % 2) % 3 else B("smooth_quartz")
        self.arena("c3_mid", x, f, z, R, "jormungandr", "mid1", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # the serpent's head rising out of the sea beside the bastion, jaws open
        hx, hz = self.x0 + cx + 30, self.z0 + cz - 6
        body = mixer(rng, [(B("dark_prismarine"), 4), (B("prismarine_bricks"), 2)])
        for t in range(0, 40):
            u = t / 39.0
            px = hx - 6 * math.sin(u * 3)
            py = SEA - 4 + u * (f + 18 - SEA)
            pz = hz + 8 * math.cos(u * 2.5)
            ell(a, px, py, pz, 3.2, 3.2, 3.2, body())
        top = (hx - 6 * math.sin(3), f + 18, hz + 8 * math.cos(2.5))
        ell(a, top[0] - 4, top[1] + 2, top[2], 5, 3.5, 4, B("dark_prismarine"))
        ell(a, top[0] - 8, top[1] - 1, top[2], 4, 1.5, 3.4, B("prismarine_bricks"))
        for s in (-1, 1):
            a.set(int(top[0] - 6), int(top[1] + 3), int(top[2] + s * 3), B("verdant_froglight"))
            for k in range(3):
                a.set(int(top[0] - 9 + k), int(top[1]), int(top[2] + s * 2), B("pointed_dripstone", dripstone_thickness="tip", hanging=1))
        for t in range(10):
            ang = t / 10 * 2 * math.pi
            bx, bz = int(round(cx + math.cos(ang) * (R + 1.5))), int(round(cz + math.sin(ang) * (R + 1.5)))
            if self.free(bx, bz):
                xx, yy, zz = self.at(bx, bz)
                P.brazier(a, xx, yy, zz, soul=False, base="cobblestone")

    # ------------------------------------------------------------ c4: Valhalla's hall of golden shields
    def shield_disc(self, x, y, z, plane="xz"):
        a = self.a
        for du in range(-3, 4):
            for dv in range(-3, 4):
                d = math.hypot(du, dv)
                if d <= 3.2:
                    b = B("iron_block") if d < 0.8 else B("gold_block") if d > 2.2 or abs(du) == abs(dv) else B("raw_gold_block")
                    if plane == "xz":
                        a.set(x + du, y, z + dv, b)
                    else:
                        a.set(x + du, y + dv, z, b)

    def valhalla(self):
        a, rng, pal = self.a, self.rng, self.pal
        cx, cz, rx, rz, f = ISL["c4"]
        hx1, hx2, hz1, hz2 = cx - 38, cx + 38, cz - 12, cz + 12
        H = 18
        # colonnade of golden pillars down both long sides, the floor of the hall
        for lx in range(hx1, hx2 + 1):
            for lz in range(hz1, hz2 + 1):
                x, z = self.w(lx, lz)
                a.set(x, f - 1, z, B("polished_diorite") if (lx + lz) % 2 else B("quartz_bricks"))
                if abs(lz - cz) <= 2:
                    a.set(x, f - 1, z, B("red_wool"))
        for lx in range(hx1, hx2 + 1, 6):
            for lz in (hz1, hz2):
                x, z = self.w(lx, lz)
                for y in range(f, f + H):
                    a.set(x, y, z, B("gold_block") if y in (f, f + H - 1) else B("quartz_pillar"))
                self.walk[lx, lz] = False
        # the roof of shields, stepped up to a ridge, with spear rafters beneath
        for step in range(0, 7):
            y = f + H + step
            for lx in range(hx1 - 2, hx2 + 3, 6):
                for lz in (hz1 - 2 + step * 2, hz2 + 2 - step * 2):
                    self.shield_disc(self.x0 + lx, y, self.z0 + lz)
        for lx in range(hx1, hx2 + 1, 6):
            for q in line_points((self.x0 + lx, f + H - 2, self.z0 + hz1), (self.x0 + lx, f + H + 5, self.z0 + cz), step=0.5):
                a.set(int(q[0]), int(q[1]), int(q[2]), B("stripped_spruce_log", axis="z"))
            for q in line_points((self.x0 + lx, f + H - 2, self.z0 + hz2), (self.x0 + lx, f + H + 5, self.z0 + cz), step=0.5):
                a.set(int(q[0]), int(q[1]), int(q[2]), B("stripped_spruce_log", axis="z"))
            a.set(self.x0 + lx, f + H + 6, self.z0 + cz, B("end_rod"))
        # long tables of the einherjar, braziers, Heidrun's mead basin
        for side in (-7, 7):
            for lx in range(hx1 + 4, hx2 - 3):
                x, z = self.w(lx, cz + side)
                a.set(x, f, z, B("dark_oak_planks") if lx % 8 else B("dark_oak_log", axis="y"))
                a.set(x, f + 1, z, B("dark_oak_slab", half="top") if lx % 8 else B("dark_oak_log", axis="y"))
        for lx in range(hx1 + 2, hx2, 12):
            x, z = self.w(lx, cz)
            C.chandelier(a, x, f + H - 1, z, 4, "lantern")
        bx, by, bz = self.at(hx2 + 6, cz)
        cyl(a, bx, by, bz, 3, 3, 2, B("gold_block"), hollow=True)
        a.set(bx, by, bz, B("honey_block"))
        a.set(bx, by + 1, bz, B("honey_block"))
        self.add_zone("c4", self.zbox("c4"), floor_mask=None, n=12)

    # ------------------------------------------------------------ c5: the plain of Idavoll
    def idavoll(self):
        a, rng = self.a, self.rng
        cx, cz, rx, rz, f = ISL["c5"]
        for (bx, bz) in ((cx - 14, cz - 10), (cx + 12, cz + 8), (cx - 8, cz + 14)):
            for dx in range(-4, 5):
                for dz in range(-4, 5):
                    x, z = self.w(bx + dx, bz + dz)
                    a.set(x, f - 1, z, B("gold_block") if (dx + dz) % 2 else B("white_concrete"))
            for (dx, dz) in ((0, 0), (2, -2), (-2, 2), (3, 1), (-3, -1), (1, 3)):
                x, z = self.w(bx + dx, bz + dz)
                a.set(x, f, z, B("gold_block") if (dx + dz) % 2 else B("polished_blackstone"))
                if (dx, dz) == (0, 0):
                    a.set(x, f + 1, z, B("lightning_rod"))
        # Idun's apple tree with golden apples
        tx, ty, tz = self.at(cx + 18, cz - 14)
        thick_line(a, (tx, ty - 1, tz), (tx, ty + 8, tz), 0.9, B("oak_log", axis="y"))
        leaf_blob(a, tx, ty + 10, tz, 5.5, leaves_of("azalea"), rng, flat=0.6, extra=leaves_of("oak"), extra_chance=0.3)
        for _ in range(16):
            x, y, z = tx + rng.randint(-5, 5), ty + rng.randint(7, 13), tz + rng.randint(-5, 5)
            if a.get(x, y, z) == AIR and a.get(x, y + 1, z) != AIR:
                a.set(x, y, z, B("gold_block") if rng.random() < 0.5 else B("orange_concrete"))
        for _ in range(500):
            lx, lz = rng.randint(cx - rx + 2, cx + rx - 2), rng.randint(cz - rz + 2, cz + rz - 2)
            if self.free(lx, lz) and rng.random() < 0.5:
                x, y, z = self.at(lx, lz)
                a.set(x, y, z, B(rng.choice(["short_grass", "short_grass", "dandelion", "poppy", "cornflower", "oxeye_daisy", "allium", "azure_bluet"])))
        self.add_zone("c5", self.zbox("c5"), floor_mask=None, n=12)

    # ------------------------------------------------------------ mid-boss 2: Loki's isle
    def loki_isle(self):
        a, rng = self.a, self.rng
        cx, cz, rx, rz, f = ISL["a2"]
        entry = self.gate_bridge(46, 124, "z", 6)
        exitg = self.gate_bridge(41, 176, "z", 6)
        x, z = self.w(cx, cz)
        R = 18

        def floor_fn(xx, zz, d):
            ang = math.atan2(zz - z, xx - x)
            snake = abs(math.sin(ang * 2 + d * 0.5)) < 0.18 and 3 < d < R - 2
            if d > R - 1.2:
                return B("green_concrete")
            if snake:
                return B("lime_concrete")
            return B("black_concrete") if (int(d) + (xx + zz) % 2) % 3 == 0 else B("polished_blackstone")
        self.arena("c5_mid", x, f, z, R, "loki", "mid2", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # the binding rocks, the serpent above, Sigyn's bowl; broken chains around the rim
        bx, by, bz = self.at(cx - 19, cz)
        for dz in (-3, 0, 3):
            for y in range(by, by + 2):
                a.set(bx, y, bz + dz, B("cobblestone"))
        a.set(bx, by + 6, bz, B("green_concrete"))
        for k in range(5):
            a.set(bx, by + 6, bz - 2 + k, B("green_concrete") if k % 2 else B("lime_concrete"))
        a.set(bx, by + 5, bz, B("green_stained_glass_pane"))
        a.set(bx + 1, by + 2, bz, B("cauldron"))
        for t in range(16):
            ang = t / 16 * 2 * math.pi
            px, pz = int(round(cx + math.cos(ang) * 20)), int(round(cz + math.sin(ang) * 20))
            if self.free(px, pz):
                xx, yy, zz = self.at(px, pz)
                a.set(xx, yy, zz, B("chain", axis="x" if t % 2 else "z"))

    # ------------------------------------------------------------ c6: burning Vigrid
    def vigrid(self):
        a, rng = self.a, self.rng
        cx, cz, rx, rz, f = ISL["c6"]
        scorch = mixer(rng, [(B("coarse_dirt"), 3), (B("blackstone"), 2), (B("magma"), 1), (B("gravel"), 1)])
        for (i, k) in np.argwhere(self.mask_of("c6")):
            if rng.random() < 0.7:
                x, z = self.w(i, k)
                a.set(x, f - 1, z, scorch())
        # broken giant swords stuck in the field, shields, spears
        for _ in range(9):
            lx, lz = rng.randint(cx - rx + 4, cx + rx - 4), rng.randint(cz - rz + 6, cz + rz - 6)
            if not self.free(lx, lz):
                continue
            x, y, z = self.at(lx, lz)
            h = rng.randint(6, 12)
            for k in range(h):
                a.set(x, y + k, z, B("iron_block"))
            for dz in (-2, -1, 1, 2):
                a.set(x, y + h, z + dz, B("gold_block"))
            for k in range(h + 1, h + 4):
                a.set(x, y + k, z, B("stripped_dark_oak_log", axis="y"))
        for _ in range(12):
            lx, lz = rng.randint(cx - rx + 3, cx + rx - 3), rng.randint(cz - rz + 4, cz + rz - 4)
            if self.free(lx, lz):
                x, y, z = self.at(lx, lz)
                a.set(x, y, z, B(rng.choice(["red_wool", "blue_wool", "yellow_wool"])))
                a.set(x + 1, y, z, B("gold_block"))
            if self.free(lx + 3, lz):
                x, y, z = self.at(lx + 3, lz)
                a.set(x, y - 1, z, B("netherrack"))
                a.set(x, y, z, B("fire"))
        # the burning golden hall
        gpal = C.Pal(rng, wall=[("gold_block", 3), ("raw_gold_block", 1), ("yellow_terracotta", 2)], trim="gilded_blackstone",
                     floor=[("polished_blackstone", 2), ("blackstone", 1)], roof="nether_brick", pillar="polished_blackstone",
                     window="iron_bars", light="lantern", accent="magma", top="polished_blackstone_wall")
        hx1, hz1 = self.w(cx - 12, cz - 24)
        C.hall(a, hx1, hz1, hx1 + 22, hz1 + 14, f, 8, gpal, roof="gable", axis="x", doors=[("south", 0, 3, 5)], lights=True, foot=2)
        for lx in range(cx - 12, cx + 11):
            for lz in range(cz - 24, cz - 9):
                self.walk[lx, lz] = False
        for lx in range(cx - 13, cx + 12):
            x, z = self.w(lx, cz - 17)
            for y in range(f + 9, f + 20):
                if a.get(x, y, z) != AIR and a.get(x, y + 1, z) == AIR:
                    a.set(x, y, z, B("netherrack"))
                    a.set(x, y + 1, z, B("fire"))
                    break
        self.add_zone("c6", self.zbox("c6"), floor_mask=None, n=12)

    # ------------------------------------------------------------ boss: the shattered island under Yggdrasil's burning branch
    def shattered(self):
        a, rng = self.a, self.rng
        cx, cz, rx, rz, f = ISL["boss"]
        entry = self.gate_bridge(37, 300, "z", 6)
        x, z = self.w(cx, cz)
        R = 24

        def floor_fn(xx, zz, d):
            ang = math.atan2(zz - z, xx - x)
            crack = abs(math.sin(ang * 5 + d * 0.25)) < 0.06 and d > 5
            if d > R - 1.2:
                return B("gold_block") if (xx + zz) % 4 == 0 else B("polished_diorite")
            if crack:
                return B("magma")
            if d < 3:
                return B("crying_obsidian")
            return B("smooth_stone") if (int(d) + (xx + zz) % 2) % 4 else B("cracked_stone_bricks")
        ar = self.arena("boss", x, f, z, R, "fenrir", "final", floor_fn=floor_fn, entry=entry)
        # Gleipnir lies broken on the rim
        for t in range(30):
            ang = t / 30 * 2 * math.pi
            px, pz = int(round(cx + math.cos(ang) * (R + 2))), int(round(cz + math.sin(ang) * (R + 2)))
            if self.free(px, pz) and t % 3:
                xx, yy, zz = self.at(px, pz)
                a.set(xx, yy, zz, B("chain", axis="x" if t % 2 else "z"))
        # fragments of the island drifting in the air
        for _ in range(14):
            ang = rng.uniform(0, 6.28)
            r = rng.uniform(rx + 6, rx + 18)
            px, pz = cx + math.cos(ang) * r, cz + math.sin(ang) * r
            if not (4 <= px < self.sx - 4 and 4 <= pz < self.sz - 4):
                continue
            py = f + rng.uniform(-14, 10)
            rr = rng.uniform(1.5, 3.5)
            ell(a, self.x0 + px, py, self.z0 + pz, rr, rr * 0.8, rr, B("stone"))
            ell(a, self.x0 + px, py + rr * 0.6, self.z0 + pz, rr, 0.6, rr, B("grass_block"))
        # the burning branch of Yggdrasil arching over the island from the west
        pts = [(2, f + 50, cz + 18), (14, f + 46, cz + 6), (cx - 4, f + 40, cz - 4), (cx + 18, f + 36, cz - 2), (cx + 34, f + 30, cz + 8)]
        for p0, p1 in zip(pts[:-1], pts[1:]):
            thick_line(a, (self.x0 + p0[0], p0[1], self.z0 + p0[2]), (self.x0 + p1[0], p1[1], self.z0 + p1[2]), 3.0, B("oak_wood"))
        for (bx, by, bz) in pts[1:]:
            for _ in range(3):
                tx, ty, tz = bx + rng.uniform(-10, 10), by + rng.uniform(-2, 6), bz + rng.uniform(-10, 10)
                thick_line(a, (self.x0 + bx, by, self.z0 + bz), (self.x0 + tx, ty, self.z0 + tz), 1.0, B("oak_log", axis="y"))
                leaf_blob(a, self.x0 + tx, ty + 2, self.z0 + tz, rng.uniform(3.5, 5.0), leaves_of("oak"), rng, flat=0.6,
                          extra=leaves_of("azalea"), extra_chance=0.2)
                for _ in range(10):
                    lx_, ly_, lz_ = int(self.x0 + tx + rng.randint(-4, 4)), int(ty + rng.randint(1, 6)), int(self.z0 + tz + rng.randint(-4, 4))
                    if a.get(lx_, ly_, lz_) != AIR and a.get(lx_, ly_ + 1, lz_) == AIR:
                        a.set(lx_, ly_, lz_, B("netherrack"))
                        a.set(lx_, ly_ + 1, lz_, B("fire"))
                    elif a.get(lx_, ly_, lz_) == AIR and rng.random() < 0.3:
                        a.set(lx_, ly_, lz_, B("shroomlight"))
        for (bx, by, bz) in pts[2:]:
            for k in range(1, rng.randint(6, 14)):
                a.put(self.x0 + bx + 2, by - 3 - k, self.z0 + bz, B("hanging_roots") if k > 2 else B("dirt_with_roots"))
        # exit: the gate on the bridge to the portal fragment
        exitg = self.gate_bridge(40, 378, "z", 5, gw=5, gh=6)
        ar["exit"] = [list(p) for p in exitg]
        self.close(exitg)
        fx, fy, fz = self.at(40, 398)
        self.exit_portal(fx, fy, fz)

    # ------------------------------------------------------------ finishing
    def finish(self):
        a = self.a
        # invisible walls on every edge: barriers on the open air beside each walkable cell
        for (i, k) in np.argwhere(self.walk):
            f = int(self.F[i, k])
            for di in (-1, 0, 1):
                for dk in (-1, 0, 1):
                    ii, kk = i + di, k + dk
                    if not (0 <= ii < self.sx and 0 <= kk < self.sz) or self.walk[ii, kk]:
                        continue
                    x, z = self.w(ii, kk)
                    for y in range(f + 1, f + 15):
                        if a.get(x, y, z) == AIR:
                            a.set(x, y, z, B("barrier"))
        self.ambient = [dict(box=self.zones["c1"]["box"], particle="minecraft:villager_happy", rate=1),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:basic_flame_particle", rate=2),
                        dict(box=self.zones["c4"]["box"], particle="minecraft:totem_particle", rate=1)]
        for key in ("c2", "c3", "c4", "c5", "c6"):
            bx1, by1, bz1, bx2, by2, bz2 = self.zones[key]["box"]
            self.light_fill((bx1, bz1, bx2, bz2), (by1, by2), level=9, threshold=5, spacing=8)
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        a.fix_walls()

    def is_escape(self, x, y, z):
        i, k = x - self.x0, z - self.z0
        if not (0 <= i < self.sx and 0 <= k < self.sz):
            return True
        win = self.walk[max(0, i - 1):i + 2, max(0, k - 1):k + 2]
        if not win.any():
            return True
        f = int(self.F[max(0, i - 1):i + 2, max(0, k - 1):k + 2].max())
        return y > f + 14


def build(seed=1):
    d = Ragnarok("d10", seed)
    d.build()
    return d
