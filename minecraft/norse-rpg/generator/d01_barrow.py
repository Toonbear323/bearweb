"""Dungeon 1 — 안개 해안의 고분 (Barrow Coast). Beginner, 176 x 288.

South -> north: landing beach, wrecked longship shore, runestone hill, barrow field, gorge to the great barrow,
then underground: tomb corridors, the ship-burial hall and the barrow-king's domed throne room.
"""
import math
import random

import numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt

from mcw import B, AIR, PAL, banner_be
from gen_common import fbm, smoothstep, stair, slab, wall_sign, standing_sign, hanging_lamp, lamp_post, line_points, leaves_of, \
    big_oak, boulder, disk
import nr_parts as P
from nr_dungeon import Dungeon, mixer
from nr_spawn import cyl, ell, thick_line

SEA = 62


class Barrow(Dungeon):
    Y0, SY = 32, 96

    def build(self):
        a, rng = self.a, self.rng
        L = self.L
        self.terrain()
        self.beach_start()
        self.wreck_shore()
        self.rune_hill()
        self.barrow_field()
        self.gorge()
        self.tombs()
        self.ship_hall()
        self.throne_room()
        self.details()
        self.boundary()
        a.fix_walls()

    # ------------------------------------------------------------------ terrain
    def terrain(self):
        a, rng = self.a, self.rng
        X, Z = self.X - self.x0, self.Z - self.z0        # local
        n1 = fbm(self.sx, self.sz, 40, 4, self.seed + 1)
        n2 = fbm(self.sx, self.sz, 14, 3, self.seed + 2)
        H = 84 + (n1 - 0.5) * 16 + (n2 - 0.5) * 4          # highland walls
        zones = {
            "start": (88, 262, 52, 30),
            "c1": (136, 222, 36, 26),
            "c2": (52, 186, 38, 30),
            "c3": (112, 140, 46, 30),
            "c4": (46, 100, 24, 26),
            "mound": (70, 62, 26, 22),
        }
        masks = {}
        for k, (cx, cz, rx, rz) in zones.items():
            masks[k] = self.noisy_ellipse(self.x0 + cx, self.z0 + cz, rx, rz, rough=0.3, seed=len(masks) * 7)
        F = {}
        F["start"] = 63 + np.clip((262 - Z) * 0.06, 0, 3) + (n2 - 0.5) * 1.5
        F["c1"] = 65 + (n2 - 0.5) * 3 + (n1 - 0.5) * 2
        d2 = np.hypot((X - 52) / 30.0, (Z - 186) / 24.0)
        F["c2"] = 67 + np.clip(1 - d2, 0, 1) ** 1.3 * 10 + (n2 - 0.5) * 1.5
        F["c3"] = 71 + (n2 - 0.5) * 2
        F["c4"] = 72 - np.clip((100 - Z) / 40.0, 0, 1) * 4 + (n2 - 0.5) * 1.2
        F["mound"] = 68 + (n2 - 0.5)
        floor = np.full_like(H, np.nan)
        for k, m in masks.items():
            floor = np.where(m & np.isnan(floor), F[k], floor)
        # passages (path, width, z_from_floor, z_to_floor)
        paths = [([(110, 252), (128, 236)], 9), ([(118, 206), (90, 196), (70, 192)], 9), ([(66, 166), (88, 156), (96, 150)], 9),
                 ([(84, 124), (62, 116), (52, 110)], 8), ([(46, 78), (58, 70), (64, 66)], 7)]
        self.passages = paths
        for pts, w in paths:
            pm = self.path_mask([(self.x0 + x, self.z0 + z) for x, z in pts], w)
            # interpolate the floor along the passage from neighbouring zone floors
            blurred = np.where(np.isnan(floor), np.nan, floor)
            fill = np.nanmean(blurred[pm]) if np.any(~np.isnan(blurred[pm])) else 70
            floor = np.where(pm & np.isnan(floor), fill, floor)
        carved = ~np.isnan(floor)
        fl = np.where(carved, floor, 0)
        fl = gaussian_filter(fl, 2.0) / np.maximum(gaussian_filter(carved.astype(float), 2.0), 1e-3)
        # walls: never climbable - at least 12 above the nearest floor, rising 4.5 blocks per block
        dist, (ii, kk) = distance_transform_edt(~carved, return_indices=True)
        near_floor = fl[ii, kk]
        wall_top = np.maximum(H, near_floor + 12 + n1 * 8)
        Hf = np.where(carved, fl, np.minimum(near_floor + 1 + dist * 4.5, wall_top))
        self.near_floor = near_floor
        # sea along the south edge
        sea = (Z > 274 + (n2 - 0.5) * 6)
        Hf = np.where(sea, 56 + (n1 - 0.5) * 3, Hf)
        self.H = np.round(Hf).astype(int)
        self.carved = carved
        self.masks = masks
        self.sea = sea
        # paint
        stone = [B("stone"), B("andesite"), B("tuff"), B("stone"), B("cobblestone"), B("andesite")]
        grassy = mixer(rng, [(B("grass_block"), 6), (B("coarse_dirt"), 2), (B("podzol"), 1), (B("moss_block"), 1)])
        beachy = mixer(rng, [(B("gravel"), 5), (B("sand"), 2), (B("tuff"), 1)])
        gy, gx = np.gradient(self.H.astype(float))
        slope = np.hypot(gx, gy)
        for i in range(self.sx):
            for k in range(self.sz):
                h = self.H[i, k]
                col = a.blk[i, :, k]
                top = h - self.Y0
                for y in range(0, top + 1):
                    col[y] = B("deepslate") if y + self.Y0 < 50 else stone[((y + self.Y0) // 4 + i // 23) % len(stone)]
                if sea[i, k]:
                    col[top] = B("gravel")
                    for y in range(top + 1, SEA - self.Y0 + 1):
                        col[y] = B("water")
                    continue
                if slope[i, k] > 1.5:
                    continue
                lz = k
                if lz > 240 or (masks["start"][i, k] and h < 66):
                    col[top] = beachy()
                    col[top - 1] = B("gravel")
                else:
                    col[top] = grassy()
                    col[top - 1] = B("dirt")
                    col[top - 2] = B("dirt")
        self.a.bio[:, :] = 25                 # stone shore: grey skies and water
        self.a.bio[:, : int(self.sz * 0.55)] = 6     # swamp: murky, misty barrow fields further north

    def is_escape(self, x, y, z):
        """Standing on the highland above the valley walls (open sky, outside the carved valley)."""
        i, k = x - self.x0, z - self.z0
        if self._allowed is None:
            from scipy.ndimage import binary_dilation
            self._allowed = binary_dilation(self.carved | self.masks["mound"], iterations=4)
        if self._allowed[i, k]:
            return False
        return y >= 70 and all(self.a.get(x, yy, z) == AIR for yy in range(y + 2, y + 12))

    _allowed = None

    def g(self, lx, lz):
        return int(self.H[lx, lz])

    def top(self, lx, lz):
        x, z = self.L(lx, lz)
        return P.surface_y(self.a, x, z)

    # ------------------------------------------------------------------ S: landing beach
    def beach_start(self):
        a, rng = self.a, self.rng
        L = self.L
        # pier from the beach into the sea and the return ship
        px1, px2 = 70, 74
        for lz in range(262, 286):
            for lx in range(px1, px2 + 1):
                x, z = L(lx, lz)
                a.set(x, 64, z, B("spruce_planks"))
                for y in range(65, 70):
                    a.set(x, y, z, AIR)
                if lx in (px1, px2) and lz % 4 == 0:
                    for y in range(self.Y0 + 22, 64):
                        if a.get(x, y, z) in (B("water"), AIR):
                            a.set(x, y, z, B("spruce_log", axis="y"))
                    a.set(x, 65, z, B("spruce_fence"))
                    if lz % 8 == 0:
                        a.set(x, 66, z, B("lantern"))
        sx, sz = L(66, 286)
        self.start_camp(*L(72, 258), 64, 180, ship=(sx, SEA, sz - 1, "north", "beginner"))
        # fix start: arrival on the pier root
        ax, az = L(72, 262)
        self.data["start"] = [ax + 0.5, 65, az + 0.5, 180]
        self.walk_seeds = [(ax, 65, az)]
        # camp: tents, fire, barrels, runestone welcome
        cx, cz = L(96, 254)
        y = self.top(96, 254) + 1
        for (dx, dz, c) in ((-6, -2, "white"), (6, -3, "red"), (0, -8, "white")):
            self.tent(cx + dx, y, cz + dz, c)
        a.set(cx, y - 1, cz, B("cobblestone"))
        a.set(cx, y, cz, B("campfire"))
        for (dx, dz) in ((-2, 1), (2, 1), (0, 2)):
            a.set(cx + dx, y, cz + dz, stair("spruce_stairs", "north"))
        P.barrels(a, cx + 9, y, cz + 3, rng, 4)
        rx, rz = L(84, 246)
        P.runestone(a, rx, self.top(84, 246) + 1, rz, rng, h=6)
        standing_sign(a, *self._at(80, 258), 8, "§l§7안개 해안의 고분\n§r§f드라우그가 잠든\n§f무덤 언덕\n§8북쪽으로 가세요", kind="spruce_standing_sign")
        # driftwood and boulders
        for _ in range(14):
            lx, lz = rng.randint(30, 150), rng.randint(244, 272)
            x, z = L(lx, lz)
            t = P.surface_y(a, x, z)
            if t and t < 67:
                if rng.random() < 0.5:
                    ax_ = rng.choice(["x", "z"])
                    for k in range(rng.randint(3, 6)):
                        a.put(x + (k if ax_ == "x" else 0), t + 1, z + (k if ax_ == "z" else 0), B("stripped_oak_log", axis=ax_))
                else:
                    boulder(a, x, t + 1, z, rng, rng.uniform(1.2, 2.2), [B("tuff"), B("stone"), B("andesite"), B("mossy_cobblestone")])
        sx_, sy_, sz_ = self._at(80, 250)
        self.add_zone_start = (sx_, sy_, sz_)

    def _at(self, lx, lz):
        x, z = self.L(lx, lz)
        return x, (self.top(lx, lz) or 64) + 1, z

    def tent(self, x, y, z, color):
        a = self.a
        for dz in range(-2, 3):
            for k in range(3):
                a.set(x - 2 + k, y + k, z + dz, B(color + "_wool"))
                a.set(x + 2 - k, y + k, z + dz, B(color + "_wool"))
            a.set(x, y + 3, z + dz, B("spruce_slab"))
        for k in range(1, 3):
            a.set(x, y + k - 1, z - 2, B("spruce_fence") if k == 1 else AIR)

    # ------------------------------------------------------------------ C1: wrecked longship shore
    def wreck_shore(self):
        a, rng = self.a, self.rng
        L = self.L
        x, z = L(118, 226)
        y = self.top(118, 226)
        info = P.longship(a, x, y - 1, z, "east", rng, sail="beginner", sail_up=False)
        # break it: remove chunks, tilt the mast, bury the stern
        F = info["frame"]
        for u in range(0, 31):
            for v in range(-1, 9):
                for w in range(-6, 7):
                    if (u > 18 and rng.random() < 0.55) or (v > 3 and rng.random() < 0.35) or (w > 2 and u % 5 == 0):
                        nm = PAL.names[F.get(u, v, w)]
                        if v <= 0 or not any(t in nm for t in ("planks", "log", "wool", "fence", "stairs", "slab", "lantern", "shroomlight")):
                            continue
                        if v == 1:
                            F.set(u, v, w, B("gravel") if rng.random() < 0.6 else B("sand"))       # sand-filled hull, no pits
                        else:
                            F.set(u, v, w, AIR if rng.random() < 0.8 else B("gravel"))
        for k in range(10):
            xx, yy, zz = F.w(14 + k, 2 + k // 2, 3 + k // 3)
            a.set(xx, yy, zz, B("spruce_log", axis="y"))
        # scattered shields and tide pools
        for _ in range(16):
            lx, lz = rng.randint(108, 166), rng.randint(206, 244)
            xx, zz = L(lx, lz)
            t = P.surface_y(a, xx, zz)
            if t is None:
                continue
            r = rng.random()
            if r < 0.4:
                a.set(xx, t + 1, zz, B(rng.choice(["red_wool", "yellow_wool", "white_wool", "blue_wool"])))
            elif r < 0.75:
                for dx in range(-1, 2):
                    for dz in range(-1, 2):
                        if rng.random() < 0.8:
                            a.set(xx + dx, t, zz + dz, B("water"))
                            a.set(xx + dx, t - 1, zz + dz, B("gravel"))
                a.setw(xx, t, zz, B("seagrass"))
            else:
                boulder(a, xx, t + 1, zz, rng, rng.uniform(1.0, 2.0), [B("tuff"), B("stone"), B("mossy_cobblestone")])
        box = self._zone_box("c1", 124, 222, 44, 34)
        self.add_zone("c1", box, floor_mask=self.carved)

    def _zone_box(self, key, lcx, lcz, rx, rz, y1=58, y2=96):
        x, z = self.L(lcx, lcz)
        return (x - rx, y1, z - rz, x + rx, y2, z + rz)

    # ------------------------------------------------------------------ C2: runestone hill
    def rune_hill(self):
        a, rng = self.a, self.rng
        L = self.L
        cx, cz = L(52, 186)
        top = self.top(52, 186)
        for k in range(12):
            ang = k / 12 * 2 * math.pi
            x, z = int(round(cx + math.cos(ang) * 11)), int(round(cz + math.sin(ang) * 11))
            t = P.surface_y(a, x, z)
            P.runestone(a, x, t + 1, z, rng, h=rng.randint(4, 7))
        # the old oak in the middle, half dead
        big_oak(a, cx, top + 1, cz, rng, h=11)
        for _ in range(140):
            x, y, z = cx + rng.randint(-8, 8), top + rng.randint(8, 16), cz + rng.randint(-8, 8)
            if PAL.names[a.get(x, y, z)].endswith("leaves") and rng.random() < 0.55:
                a.set(x, y, z, AIR)
        # cairns
        for _ in range(9):
            lx, lz = 52 + rng.randint(-26, 26), 186 + rng.randint(-20, 20)
            x, z = L(lx, lz)
            t = P.surface_y(a, x, z)
            if t is None or self.H[lx, lz] > 82:
                continue
            for dy, r in ((1, 1.6), (2, 1.0), (3, 0.5)):
                disk(a, x, t + dy, z, r, B("cobblestone") if dy < 3 else B("mossy_cobblestone"))
        box = self._zone_box("c2", 52, 186, 40, 32)
        self.add_zone("c2", box, floor_mask=self.carved)

    # ------------------------------------------------------------------ C3: barrow field
    def barrow_field(self):
        a, rng = self.a, self.rng
        L = self.L
        mounds = [(92, 128, 7), (118, 122, 8), (140, 140, 6), (104, 156, 6), (130, 160, 7), (78, 146, 5)]
        for (lx, lz, r) in mounds:
            x, z = L(lx, lz)
            t = self.top(lx, lz)
            for xx in range(x - r - 1, x + r + 2):
                for zz in range(z - r - 1, z + r + 2):
                    d = math.hypot(xx - x, zz - z) / r
                    if d <= 1:
                        hh = int(round((1 - d * d) * r * 0.6))
                        for yy in range(t, t + hh + 1):
                            a.set(xx, yy, zz, B("dirt"))
                        a.set(xx, t + hh, zz, B("grass_block") if rng.random() < 0.85 else B("moss_block"))
            # stone entrance on the south side
            ex, ez = x, z + r - 1
            for yy in range(t + 1, t + 4):
                a.set(ex - 1, yy, ez, B("chiseled_stone_bricks"))
                a.set(ex + 1, yy, ez, B("chiseled_stone_bricks"))
                a.set(ex, yy, ez, AIR if yy < t + 3 else B("stone_bricks"))
            a.set(ex, t + 1, ez - 1, B("cobweb"))
        # ship-shaped stone settings (stone ships)
        for (lx, lz, L2, ang) in ((116, 140, 18, 0.3), (88, 158, 12, -0.6)):
            x, z = L(lx, lz)
            for k in range(28):
                tt = k / 28 * 2 * math.pi
                px = x + math.cos(tt) * L2 / 2 * math.cos(ang) - math.sin(tt) * 3 * math.sin(ang)
                pz = z + math.cos(tt) * L2 / 2 * math.sin(ang) + math.sin(tt) * 3 * math.cos(ang)
                px, pz = int(round(px)), int(round(pz))
                t = P.surface_y(a, px, pz)
                h = 2 if abs(math.cos(tt)) > 0.9 else 1
                for yy in range(t + 1, t + 1 + h):
                    a.set(px, yy, pz, B("mossy_cobblestone") if rng.random() < 0.4 else B("cobblestone"))
        # dead grass, ferns, soul lanterns on posts
        for _ in range(500):
            lx, lz = rng.randint(64, 168), rng.randint(110, 172)
            x, z = L(lx, lz)
            t = P.surface_y(a, x, z)
            if t and a.get(x, t, z) == B("grass_block") and a.get(x, t + 1, z) == AIR:
                a.set(x, t + 1, z, B(rng.choice(["short_grass", "fern", "deadbush", "short_grass"])))
        for (lx, lz) in ((96, 140), (124, 140), (110, 166), (82, 130)):
            x, y, z = self._at(lx, lz)
            P.torch_post(a, x, y, z, height=3, soul=True)
        box = self._zone_box("c3", 112, 140, 50, 32)
        self.add_zone("c3", box, floor_mask=self.carved)

    # ------------------------------------------------------------------ C4: the gorge to the great barrow
    def gorge(self):
        a, rng = self.a, self.rng
        L = self.L
        # dead trees
        for _ in range(16):
            lx, lz = rng.randint(28, 66), rng.randint(80, 124)
            x, z = L(lx, lz)
            t = P.surface_y(a, x, z)
            if t is None or not self.carved[lx, lz]:
                continue
            h = rng.randint(5, 9)
            for k in range(h):
                a.set(x, t + 1 + k, z, B("dark_oak_log", axis="y"))
            for _b in range(3):
                ang = rng.uniform(0, 6.28)
                thick_line(a, (x, t + h - 1, z), (x + math.cos(ang) * 3, t + h + 2, z + math.sin(ang) * 3), 0.4, B("dark_oak_log", axis="y"))
        # chains with lanterns hung across the gorge
        for lz in (92, 104, 116):
            x1, z1 = L(30, lz)
            x2, z2 = L(62, lz)
            yy = 80
            for q in line_points((x1, yy, z1), (x2, yy - 3, z2), step=0.5):
                if a.get(q[0], q[1], q[2]) == AIR:
                    a.set(q[0], q[1], q[2], B("chain", axis="x"))
            mx = (x1 + x2) // 2
            hanging_lamp(a, mx, yy - 3, z1, 3, B("soul_lantern", hanging=1))
        # the great barrow: huge mound with a monumental portal
        cx, cz = L(70, 52)
        t0 = self.top(70, 62)
        R = 24
        for x in range(cx - R, cx + R + 1):
            for z in range(cz - R, cz + R + 1):
                d = math.hypot((x - cx) / R, (z - cz) / (R * 0.9))
                if d <= 1:
                    hh = int(round((1 - d ** 2) * 16))
                    base = P.surface_y(a, x, z) or t0
                    for yy in range(min(base, t0), t0 + hh + 1):
                        a.set(x, yy, z, B("dirt") if yy < t0 + hh else (B("grass_block") if rng.random() < 0.8 else B("moss_block")))
        # portal on the south face of the mound
        px, pz = L(70, 72)
        for dz in range(-12, 3):
            for dx in range(-3, 4):
                for yy in range(t0, t0 + 6):
                    a.set(px + dx, yy, pz + dz, AIR if abs(dx) <= 1 and yy < t0 + 5 else B("deepslate_bricks"))
                a.set(px + dx, t0 - 1, pz + dz, B("cobbled_deepslate"))
        for dx in (-2, 2):
            for yy in range(t0, t0 + 6):
                a.set(px + dx, yy, pz + 2, B("chiseled_deepslate"))
        for dx in range(-3, 4):
            a.set(px + dx, t0 + 6, pz + 2, B("polished_deepslate"))
        for dx in (-2, 2):
            a.set(px + dx, t0 + 7, pz + 2, B("soul_lantern"))
        wall_sign(a, px - 2, t0 + 4, pz + 3, 3, "§l§8고분왕의 무덤\n§r§7산 자는 돌아가라", kind="darkoak_wall_sign")
        self.portal_entry = (px, t0, pz - 12)
        box = self._zone_box("c4", 46, 100, 30, 32)
        self.add_zone("c4", box, floor_mask=self.carved)

    # ------------------------------------------------------------------ underground
    def room(self, x1, y1, z1, x2, y2, z2, wall=None, floor=None):
        a, rng = self.a, self.rng
        wall = wall or mixer(rng, [(B("deepslate_bricks"), 5), (B("cracked_deepslate_bricks"), 2), (B("deepslate_tiles"), 2), (B("cobbled_deepslate"), 1)])
        floor = floor or mixer(rng, [(B("polished_deepslate"), 4), (B("deepslate_tiles"), 3), (B("cobbled_deepslate"), 1)])
        for x in range(x1 - 1, x2 + 2):
            for z in range(z1 - 1, z2 + 2):
                for y in range(y1 - 1, y2 + 2):
                    edge = x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1) or y in (y1 - 1, y2 + 1)
                    if edge:
                        if a.get(x, y, z) != AIR or y == y1 - 1:
                            a.set(x, y, z, floor() if y == y1 - 1 else wall())
                    else:
                        a.set(x, y, z, AIR)

    def corridor(self, pts, y, w=5, h=5):
        """Corridor through solid rock along (x, z) points; y = floor (stand) level."""
        a, rng = self.a, self.rng
        wall = mixer(rng, [(B("deepslate_bricks"), 5), (B("cracked_deepslate_bricks"), 2), (B("deepslate_tiles"), 1), (B("cobbled_deepslate"), 2)])
        cells = set()
        for (p0, p1) in zip(pts[:-1], pts[1:]):
            for q in line_points((p0[0], 0, p0[1]), (p1[0], 0, p1[1]), step=0.5):
                for dx in range(-(w // 2), w // 2 + 1):
                    for dz in range(-(w // 2), w // 2 + 1):
                        cells.add((q[0] + dx, q[2] + dz))
        for (x, z) in cells:
            for yy in range(y, y + h):
                a.set(x, yy, z, AIR)
            a.set(x, y - 1, z, B("polished_deepslate") if (x + z) % 3 else B("cobbled_deepslate"))
            a.set(x, y + h, z, wall())
            for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, z + dz) not in cells:
                    for yy in range(y, y + h):
                        # line natural rock with bricks; never wall off an existing open space
                        if a.get(x + dx, yy, z + dz) != AIR:
                            a.set(x + dx, yy, z + dz, wall())
        return cells

    def tombs(self):
        a, rng = self.a, self.rng
        L = self.L
        px, t0, pz = self.portal_entry
        y = 52
        # descending stair from the portal down to the corridors
        sx, sz = px, pz
        cur_y = t0
        k = 0
        while cur_y > y:
            for dx in (-1, 0, 1):
                a.set(sx + dx, cur_y - 1, sz - k, stair("deepslate_brick_stairs", "south"))
                for yy in range(cur_y, cur_y + 5):
                    a.set(sx + dx, yy, sz - k, AIR)
                for side in (-2, 2):
                    for yy in range(cur_y - 1, cur_y + 6):
                        if a.get(sx + side, yy, sz - k) == AIR:
                            a.set(sx + side, yy, sz - k, B("deepslate_bricks"))
                a.set(sx + dx, cur_y + 5, sz - k, B("deepslate_bricks"))
            if k % 4 == 2:
                a.set(sx, cur_y + 4, sz - k, B("soul_lantern", hanging=1))
            k += 1
            cur_y -= 1
        # flat landing at the stair foot, then the corridor starts clear of the stairs
        for kk in range(k, k + 3):
            for dx in (-1, 0, 1):
                a.set(sx + dx, y - 1, sz - kk, B("polished_deepslate"))
                for yy in range(y, y + 5):
                    a.set(sx + dx, yy, sz - kk, AIR)
        start = (sx, sz - k - 4)
        # the corridor network: main hall with burial niches, two side tombs
        mainpts = [start, (start[0], start[1] - 4), L(92, 34), L(112, 34)]
        cells = self.corridor(mainpts, y, w=5, h=6)
        side1 = self.corridor([L(80, 44), L(80, 60)], y, w=5, h=5)
        side2 = self.corridor([L(100, 34), L(100, 16)], y, w=5, h=5)
        # niches with bones and skulls along the walls, soul lanterns
        for (x, z) in list(cells)[::9]:
            for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
                if a.get(x + dx, y + 1, z + dz) not in (AIR,) and PAL.names[a.get(x + dx, y + 1, z + dz)].startswith(("deepslate", "cracked", "cobbled")):
                    a.set(x + dx, y + 1, z + dz, B("bone_block", axis="y") if rng.random() < 0.5 else B("cobweb"))
                    a.set(x + dx, y + 2, z + dz, AIR if rng.random() < 0.5 else B("cobweb"))
                    break
        for (x, z) in list(cells)[::23]:
            if a.get(x, y + 5, z) == AIR and a.get(x, y + 6, z) != AIR:
                a.set(x, y + 5, z, B("soul_lantern", hanging=1))
        for (x, z) in list(side1 | side2)[::7]:
            if a.get(x, y, z) == AIR and rng.random() < 0.4:
                a.set(x, y, z, B("cobweb"))
        x1, z1 = L(70, 10)
        x2, z2 = L(118, 66)
        self.add_zone("c5", (x1, y - 1, z1, x2, y + 6, z2))
        self.tomb_y = y
        self.c5_end = L(112, 34)

    def ship_hall(self):
        a, rng = self.a, self.rng
        L = self.L
        y = 50
        x1, z1 = L(122, 14)
        x2, z2 = L(170, 54)
        self.room(x1, y, z1, x2, y + 12, z2)
        # corridor (feet 52) east to the hall, then two steps down into the hall (feet 50)
        ex, ez = self.c5_end
        self.corridor([(ex, ez), (x1 - 3, ez)], y + 2, w=5, h=6)
        self.stair_run(x1 - 2, y + 2, ez, "east", 2, width=5, wall=B("deepslate_bricks"))
        # pillars with braziers
        for x in range(x1 + 4, x2 - 2, 8):
            for z in (z1 + 3, z2 - 3):
                for yy in range(y, y + 12):
                    a.set(x, yy, z, B("chiseled_deepslate") if yy % 4 == 0 else B("polished_deepslate"))
                a.set(x, y + 4, z + (1 if z == z1 + 3 else -1), B("soul_lantern"))
        # the burial ship (on the floor, sail furled), grave goods around it
        sx, sz = L(130, 34)
        info = P.longship(a, sx, y - 1, sz, "east", rng, length=31, sail="beginner", sail_up=False)
        for _ in range(40):
            gx, gz = rng.randint(x1 + 1, x2 - 1), rng.randint(z1 + 1, z2 - 1)
            if a.get(gx, y, gz) == AIR:
                r = rng.random()
                a.set(gx, y, gz, B("gold_block") if r < 0.15 else B("chest") if r < 0.25 else B("candle") if r < 0.6 else B("bone_block", axis="y") if r < 0.8 else B("raw_gold_block"))
        for x in range(x1 + 2, x2 - 1, 6):
            hanging_lamp(a, x, y + 11, (z1 + z2) // 2, 3, B("soul_lantern", hanging=1))
        self.add_zone("c6", (x1, y - 1, z1, x2, y + 8, z2))
        self.hall = (x1, z1, x2, z2, y)

    def throne_room(self):
        a, rng = self.a, self.rng
        L = self.L
        x1, z1, x2, z2, hy = self.hall
        y = 46
        cx, cz = L(40, 30)
        R = 15
        # dome
        for x in range(cx - R - 2, cx + R + 3):
            for z in range(cz - R - 2, cz + R + 3):
                d = math.hypot(x - cx, z - cz)
                for yy in range(y - 1, y + 16):
                    dd = math.sqrt(d * d + ((yy - y) * 1.1) ** 2)
                    if d <= R + 1.5 and yy == y - 1:
                        continue
                    if dd <= R:
                        a.set(x, yy, z, AIR)
                    elif dd <= R + 1.5:
                        a.set(x, yy, z, B("deepslate_tiles") if (yy // 3) % 2 else B("deepslate_bricks"))
        # corridor from the ship hall (feet 50) along the north edge, then 4 steps down to the arena (feet 46)
        door_x = cx + R + 6
        cells = self.corridor([(x1 + 3, z1 + 3), (x1 + 3, z1 - 3), L(110, 8), (door_x + 6, cz - 8), (door_x, cz - 8)], hy, w=5, h=6)
        foot = self.stair_run(door_x, hy, cz - 8, "west", hy - y, width=5, wall=B("deepslate_bricks"))
        for xx in range(foot[0], cx + R - 3, -1):
            for w in range(-2, 3):
                a.set(xx, y - 1, cz - 8 + w, B("polished_deepslate"))
                for yy in range(y, y + 5):
                    a.set(xx, yy, cz - 8 + w, AIR)
        def floor_fn(x, z, d):
            if 10.6 < d <= 11.4:
                return B("gold_block") if int(math.degrees(math.atan2(z - cz, x - cx))) % 30 < 15 else B("polished_blackstone")
            if int(d) % 4 == 0:
                return B("polished_deepslate")
            return B("deepslate_tiles") if (x + z) % 2 else B("polished_deepslate")
        entry = self.doorway(cx + R, y, cz - 8, 5, 5, "z")
        ar = self.arena("boss", cx, y, cz, R - 1, "arnarr", "final", floor_fn=floor_fn, entry=entry)
        # rune pillars with soul fire
        for k in range(8):
            ang = k / 8 * 2 * math.pi + 0.2
            px, pz = int(round(cx + math.cos(ang) * (R - 2))), int(round(cz + math.sin(ang) * (R - 2)))
            for yy in range(y, y + 7):
                a.set(px, yy, pz, B("chiseled_deepslate") if yy % 3 == 0 else B("polished_deepslate"))
            a.set(px, y + 7, pz, B("soul_campfire"))
        # throne dais on the west side, banners
        tx = cx - R + 3
        for dz in range(-3, 4):
            for dx in range(0, 3):
                a.set(tx + dx, y, cz + dz, B("polished_blackstone_bricks"))
        a.set(tx, y + 1, cz, stair("blackstone_stairs", "west"))
        for k in range(1, 5):
            a.set(tx - 1, y + k, cz, B("polished_blackstone_bricks"))
        a.set(tx - 1, y + 5, cz, B("gold_block"))
        for dz in (-2, 2):
            a.set(tx, y + 1, cz + dz, B("polished_blackstone_wall"))
            a.set(tx, y + 2, cz + dz, B("soul_lantern"))
        for dz in (-5, 5):
            a.set(tx - 1, y + 4, cz + dz, B("wall_banner", facing_direction=5))
            a.add_be(banner_be(tx - 1, y + 4, cz + dz, 0, [("sku", 7), ("bo", 15)]))
        # exit portal behind the throne
        ex, ez = cx - R - 6, cz
        self.room(ex - 4, y, ez - 4, ex + 4, y + 5, ez + 4)
        for w in range(-1, 2):
            for xx in range(cx - R - 2, cx - R + 3):
                a.set(xx, y - 1, cz + w, B("polished_deepslate"))
                for yy in range(y, y + 3):
                    a.set(xx, yy, cz + w, AIR)
        self.exit_portal(ex, y, ez)
        ar["exit"] = [list(p) for p in self.doorway(cx - R - 1, y, cz, 3, 3, "z")]
        self.close([tuple(p) for p in ar["exit"]])

    def details(self):
        from gen_common import spruce_tree
        a, rng = self.a, self.rng

        def dead_tree(a_, x, y, z, r):
            h = r.randint(4, 8)
            for k in range(h):
                a_.set(x, y + k, z, B("dark_oak_log", axis="y"))
            for _b in range(2):
                ang = r.uniform(0, 6.28)
                thick_line(a_, (x, y + h - 1, z), (x + math.cos(ang) * 2.5, y + h + 1, z + math.sin(ang) * 2.5), 0.4, B("dark_oak_log", axis="y"))

        def tree(a_, x, y, z, r):
            if r.random() < 0.6:
                spruce_tree(a_, x, y, z, r, h=r.randint(7, 11))
            else:
                dead_tree(a_, x, y, z, r)
        self.dress_walls(self.carved, [B("stone"), B("andesite"), B("tuff"), B("cobblestone"), B("stone"), B("mossy_cobblestone")],
                         rim=dict(tree=tree, plants=["short_grass", "fern", "short_grass", "deadbush"], bush=B("spruce_leaves", persistent_bit=1)),
                         rim_trees=0.05)
        for key in ("c5", "c6"):
            x1, y1, z1, x2, y2, z2 = self.zones[key]["box"]
            self.light_fill((x1, z1, x2, z2), (y1, y2), level=6, threshold=3, spacing=7)
        x, y, z = self.arenas[0]["x"], self.arenas[0]["y"], self.arenas[0]["z"]
        self.light_fill((int(x) - 16, int(z) - 16, int(x) + 16, int(z) + 16), (y - 1, y + 2), level=7, threshold=4, spacing=6)
        # zone boxes for the start (no mobs) are not exported; ambient particles per zone
        self.ambient = [dict(box=self.zones["c3"]["box"], particle="minecraft:white_smoke_particle", rate=2),
                        dict(box=self.zones["c5"]["box"], particle="minecraft:soul_particle", rate=1),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:soul_particle", rate=1)]


def build(seed=1):
    d = Barrow("d01", seed)
    d.build()
    L = d.L
    def w(lx, y, lz):
        x, z = L(lx, lz)
        return (x, y, z)
    d.shots = [
        ("start", w(88, 74, 284), w(88, 66, 236)),
        ("c1", w(150, 76, 250), w(120, 66, 222)),
        ("c2", w(82, 84, 214), w(52, 76, 186)),
        ("c3", w(150, 82, 170), w(110, 72, 136)),
        ("c4", w(50, 86, 128), w(66, 72, 70)),
        ("c5", w(78, 55, 46), w(96, 54, 34)),
        ("c6", w(166, 58, 50), w(140, 52, 30)),
        ("boss", w(52, 54, 30), w(28, 48, 30)),
    ]
    return d


if __name__ == "__main__":
    import sys, time
    import render
    t0 = time.time()
    d = build()
    print("built %.1fs" % (time.time() - t0), d.export()["start"])
    render.topdown(d.a, sys.argv[1], scale=2)
