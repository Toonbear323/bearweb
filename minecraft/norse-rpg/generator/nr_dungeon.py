"""Dungeon framework: area, zones, arenas, gates, spawn points, start camp, exit portal, boundary walls.

A dungeon module subclasses Dungeon, fills `self.layout` (zone centres) and implements one builder per zone.
Everything the behaviour pack needs (zones, arenas, gates, arrival/return points) is collected in self.data.
"""
import math
import random

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, binary_dilation

from mcw import Area, B, AIR, PAL, banner_be
from gen_common import fbm, smoothstep, stair, slab, wall_sign, standing_sign, hanging_lamp, lamp_post, line_points, leaves_of
import nr_design as D
import nr_parts as P

# world placement: dungeon n (1..10) starts at x = 1024 + (n-1) * 512
BASE_X = 1024
PITCH = 512
BASE_Z = -224


def origin_of(no):
    return BASE_X + (no - 1) * PITCH, BASE_Z


def mixer(rng, items):
    tot = float(sum(w for _, w in items))

    def f():
        r = rng.random() * tot
        for b, w in items:
            r -= w
            if r <= 0:
                return b
        return items[-1][0]
    return f


class Dungeon:
    """Subclasses set: Y0, SY (vertical range), and implement build()."""
    Y0, SY = 32, 128

    def __init__(self, did, seed=1):
        self.d = D.BY_ID[did]
        self.did = did
        self.tier = self.d["tier"]
        sx, sz = D.TIERS[self.tier]["size"]
        self.x0, self.z0 = origin_of(self.d["no"])
        self.sx, self.sz = sx, sz
        self.a = Area(did, self.x0, self.z0, sx, sz, y0=self.Y0, sy=self.SY, biome=1)
        self.rng = random.Random(seed * 1000 + self.d["no"])
        self.seed = seed * 1000 + self.d["no"]
        self.zones = {}           # key -> dict(box, points, mobs, cap, floor)
        self.arenas = []
        self.data = dict(start=None, ret=None, exit=None)
        self.no_walk = []
        self.walk_seeds = []
        xs = np.arange(self.x0, self.x0 + sx)
        zs = np.arange(self.z0, self.z0 + sz)
        self.X, self.Z = np.meshgrid(xs, zs, indexing="ij")

    # ------------------------------------------------------------ coordinates
    def L(self, lx, lz):
        """local (0..sx, 0..sz) -> world."""
        return self.x0 + lx, self.z0 + lz

    def inside(self, x, z):
        return self.x0 <= x < self.x0 + self.sx and self.z0 <= z < self.z0 + self.sz

    # ------------------------------------------------------------ generic carving
    def noisy_ellipse(self, cx, cz, rx, rz, rough=0.25, seed=0):
        n = fbm(self.sx, self.sz, max(8, min(rx, rz) * 0.7), 3, self.seed + seed)
        d = np.hypot((self.X - cx) / rx, (self.Z - cz) / rz)
        return d < 1.0 - rough * (n - 0.5) * 2

    def path_mask(self, pts, width):
        m = np.zeros((self.sx, self.sz), bool)
        for (p0, p1) in zip(pts[:-1], pts[1:]):
            for q in line_points((p0[0], 0, p0[1]), (p1[0], 0, p1[1]), step=0.5):
                x, _, z = q
                i, k = int(x) - self.x0, int(z) - self.z0
                r = int(math.ceil(width / 2))
                m[max(0, i - r):i + r + 1, max(0, k - r):k + r + 1] = True
        return m

    def column_fill(self, i, k, top_y, top_block, under, depth=4, base=None):
        a = self.a
        col = a.blk[i, :, k]
        ty = top_y - self.Y0
        if ty < 0:
            return
        for y in range(0, ty + 1):
            col[y] = base if base is not None and y < ty - depth else under
        col[ty] = top_block

    # ------------------------------------------------------------ zones and spawn points
    def add_zone(self, key, box, floor_mask=None, spacing=5, n=10, y_hint=None, extra_points=None):
        """box = (x1, y1, z1, x2, y2, z2) world. Spawn points are sampled on walkable floor inside the box."""
        z = self.d["zones"][[q["key"] for q in self.d["zones"]].index(key)]
        pts = list(extra_points or [])
        if len(pts) < n:
            pts += self.sample_floor(box, n - len(pts), spacing, floor_mask)
        self.zones[key] = dict(key=key, ko=z["ko"], box=list(box), points=[list(p) for p in pts], mobs=z["mobs"], cap=z["cap"])
        return self.zones[key]

    def sample_floor(self, box, n, spacing, mask=None):
        a = self.a
        x1, y1, z1, x2, y2, z2 = box
        out = []
        tries = 0
        htab = None
        from mcw import physics_tables
        htab, liq, _ = physics_tables()
        while len(out) < n and tries < n * 80:
            tries += 1
            x, z = self.rng.randint(x1, x2), self.rng.randint(z1, z2)
            if not self.inside(x, z):
                continue
            if mask is not None and not mask[x - self.x0, z - self.z0]:
                continue
            for y in range(y2, y1 - 1, -1):
                b = a.get(x, y, z)
                if b == AIR:
                    continue
                if htab[b] >= 2 and not liq[b] and a.get(x, y + 1, z) == AIR and a.get(x, y + 2, z) == AIR:
                    if all(math.hypot(x - p[0], z - p[2]) >= spacing for p in out):
                        out.append((x + 0.5, y + 1, z + 0.5))
                    break
        return out

    # ------------------------------------------------------------ arenas
    def arena(self, key, cx, y, cz, r, boss, role, floor_fn=None, rim_fn=None, entry=(), exit=(), gate_block="minecraft:iron_bars",
              respawn=6000):
        """Flat circular arena (top block at y-1, players stand at y). entry/exit = lists of block positions for the gates."""
        a = self.a
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.5:
                    b = floor_fn(x, z, d) if floor_fn else B("polished_andesite")
                    a.set(x, y - 1, z, b)
                    for yy in range(y, y + 14):
                        if a.get(x, yy, z) != AIR and not (rim_fn and d > r - 0.5):
                            a.set(x, yy, z, AIR)
        tb = [int(cx - r + 3), y, int(cz - r + 3), int(cx + r - 3), y + 3, int(cz + r - 3)]
        ar = dict(id="%s_%s" % (self.did, key), dungeon=self.did, boss=boss, role=role, x=cx + 0.5, y=y, z=cz + 0.5, r=r,
                  trigger=tb, entry=[list(p) for p in entry], exit=[list(p) for p in exit], gateBlock=gate_block, respawn=respawn)
        self.arenas.append(ar)
        return ar

    def doorway(self, x, y, z, width, height, axis):
        """Gate block positions of a doorway centred on (x, z), spanning `width` along axis ('x' or 'z')."""
        out = []
        for w in range(-(width // 2), width // 2 + 1):
            for h in range(height):
                if axis == "x":
                    out.append((x + w, y + h, z))
                else:
                    out.append((x, y + h, z + w))
        return out

    def stair_run(self, x, y, z, direction, steps, width=3, name="deepslate_brick_stairs", head=5, wall=None):
        """Walkable stairs going DOWN `steps` blocks while travelling `direction` from feet level y at (x, z).
        Returns the (x, y, z) feet position after the last step (on flat floor, already carved)."""
        a = self.a
        dx, dz = P.DIRS[direction]
        nx, nz = -dz, dx
        up = P.OPP[direction]
        half = width // 2
        for k in range(steps + 2):
            fy = y - min(k, steps)                     # feet level on this column
            cx, cz = x + dx * k, z + dz * k
            for w in range(-half, half + 1):
                xx, zz = cx + nx * w, cz + nz * w
                if k < steps:
                    a.set(xx, fy - 1, zz, stair(name, up))
                else:
                    a.set(xx, fy - 1, zz, B(name.replace("_stairs", "s") if name.endswith("brick_stairs") else "polished_deepslate"))
                for yy in range(fy, fy + head):
                    a.set(xx, yy, zz, AIR)
                if wall is not None:
                    a.set(xx, fy + head, zz, wall)
            if wall is not None:
                for w in (-half - 1, half + 1):
                    xx, zz = cx + nx * w, cz + nz * w
                    for yy in range(fy - 1, fy + head + 1):
                        if a.get(xx, yy, zz) != AIR:
                            a.set(xx, yy, zz, wall)
        return (x + dx * (steps + 1), y - steps, z + dz * (steps + 1))

    def close(self, cells, block=None):
        for (x, y, z) in cells:
            self.a.set(x, y, z, block or B("iron_bars"))

    # ------------------------------------------------------------ start camp / exit portal
    def start_camp(self, ax, ay, az, facing_yaw, ship=None, rng=None):
        """Arrival point (players appear here) + return ship (stand on its deck to sail home)."""
        rng = rng or self.rng
        self.data["start"] = [ax + 0.5, ay, az + 0.5, facing_yaw]
        if ship:
            x, y, z, facing, sail = ship
            info = P.longship(self.a, x, y, z, facing, rng, sail=sail)
            self.data["ret"] = dict(deck=list(info["deck"]))
            self.no_walk.append(info["deck"])
        self.walk_seeds.append((ax, ay, az))

    def exit_portal(self, cx, y, cz, style="stone"):
        """Rune circle behind the final boss: stand in it to return to the harbour."""
        a = self.a
        for x in range(cx - 3, cx + 4):
            for z in range(cz - 3, cz + 4):
                d = math.hypot(x - cx, z - cz)
                if d <= 3.4:
                    a.set(x, y - 1, z, B("gold_block") if 2.4 < d <= 3.4 and (x + z) % 2 == 0 else B("chiseled_stone_bricks") if d > 2.4 else B("crying_obsidian") if d < 1 else B("polished_blackstone"))
        for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
            for k in range(4):
                a.set(cx + dx, y + k, cz + dz, B("chiseled_stone_bricks") if k < 3 else B("soul_lantern"))
        self.data["exit"] = [cx - 1, y, cz - 1, cx + 1, y + 2, cz + 1]

    # ------------------------------------------------------------ valley terrain (outdoor dungeons)
    def valleys(self, zones, paths, high=(86, 14), wall_extra=12, wall_rise=4.5, rough=0.3, smooth=2.0, margin=0):
        """zones: key -> (lcx, lcz, rx, rz, floor) where floor is a number or fn(Xl, Zl, n) -> array.
        paths: list of (local points, width). Builds self.H (int), self.carved, self.near_floor, self.masks."""
        X, Z = self.X - self.x0, self.Z - self.z0
        n1 = fbm(self.sx, self.sz, 40, 4, self.seed + 1)
        n2 = fbm(self.sx, self.sz, 14, 3, self.seed + 2)
        self.n1, self.n2 = n1, n2
        H = high[0] + (n1 - 0.5) * high[1] + (n2 - 0.5) * 3
        floor = np.full(H.shape, np.nan)
        masks = {}
        fields = {}
        for idx, (k, (cx, cz, rx, rz, f)) in enumerate(zones.items()):
            m = self.noisy_ellipse(self.x0 + cx, self.z0 + cz, rx, rz, rough=rough, seed=idx * 7 + 3)
            masks[k] = m
            fld = f(X, Z, n2) if callable(f) else np.full(H.shape, float(f)) + (n2 - 0.5) * 1.2
            fields[k] = fld
            floor = np.where(m & np.isnan(floor), fld, floor)
        for pts, w in paths:
            pts_w = [(self.x0 + x, self.z0 + z) for x, z in pts]
            pm = self.path_mask(pts_w, w)
            # floor at both ends from the carved floor, linear along the path
            def fl_at(p):
                i, k = int(p[0]), int(p[1])
                i, k = min(max(i, 0), self.sx - 1), min(max(k, 0), self.sz - 1)
                win = floor[max(0, i - 3):i + 4, max(0, k - 3):k + 4]
                v = win[~np.isnan(win)]
                return float(v.mean()) if len(v) else float(H[i, k] - wall_extra)
            f0, f1 = fl_at(pts[0]), fl_at(pts[-1])
            seglen = [math.dist(a_, b_) for a_, b_ in zip(pts[:-1], pts[1:])]
            total = sum(seglen) or 1
            # parameter t of each cell = nearest point along the polyline
            cells = np.argwhere(pm & np.isnan(floor))
            for (i, k) in cells:
                best, bt = 1e9, 0.0
                acc = 0.0
                for (p0, p1), L in zip(zip(pts[:-1], pts[1:]), seglen):
                    vx, vz = p1[0] - p0[0], p1[1] - p0[1]
                    t = ((i - p0[0]) * vx + (k - p0[1]) * vz) / max(L * L, 1e-6)
                    t = min(max(t, 0), 1)
                    d = math.hypot(i - (p0[0] + vx * t), k - (p0[1] + vz * t))
                    if d < best:
                        best, bt = d, (acc + t * L) / total
                    acc += L
                floor[i, k] = f0 + (f1 - f0) * bt
        if margin:
            edge = np.zeros(floor.shape, bool)
            edge[:margin, :] = edge[-margin:, :] = edge[:, :margin] = edge[:, -margin:] = True
            floor[edge] = np.nan
            for k in masks:
                masks[k] = masks[k] & ~edge
        carved = ~np.isnan(floor)
        fl = np.where(carved, floor, 0)
        fl = gaussian_filter(fl, smooth) / np.maximum(gaussian_filter(carved.astype(float), smooth), 1e-3)
        dist, (ii, kk) = distance_transform_edt(~carved, return_indices=True)
        near_floor = fl[ii, kk]
        wall_top = np.maximum(H, near_floor + wall_extra + n1 * 8)
        Hf = np.where(carved, fl, np.minimum(near_floor + 1 + dist * wall_rise, wall_top))
        self.H = np.round(Hf).astype(int)
        self.carved, self.near_floor, self.masks, self.fields = carved, near_floor, masks, fields
        self.wall_dist = dist
        return self.H

    def caverns(self, zones, paths, rock, smooth=1.6):
        """Underground: zones key -> (lcx, lcz, rx, rz, floor, height[, rough]); paths (points, width, height).
        Solid rock everywhere, then air between a walkable floor field and a domed, noisy ceiling.
        Sets self.F (floor top y), self.C (ceiling y), self.cave (bool mask), self.masks."""
        a = self.a
        X, Z = self.X - self.x0, self.Z - self.z0
        n1 = fbm(self.sx, self.sz, 30, 4, self.seed + 1)
        n2 = fbm(self.sx, self.sz, 11, 3, self.seed + 2)
        n3 = fbm(self.sx, self.sz, 6, 2, self.seed + 3)
        self.n1, self.n2, self.n3 = n1, n2, n3
        F = np.full(X.shape, np.nan)
        Hh = np.zeros(X.shape)
        masks = {}
        for idx, (k, spec) in enumerate(zones.items()):
            cx, cz, rx, rz, fl, hh = spec[:6]
            rough = spec[6] if len(spec) > 6 else 0.3
            m = self.noisy_ellipse(self.x0 + cx, self.z0 + cz, rx, rz, rough=rough, seed=idx * 11 + 5)
            masks[k] = m & np.isnan(F)          # zones never share cells (earlier zones win)
            fld = fl(X, Z, n2) if callable(fl) else np.full(X.shape, float(fl)) + (n2 - 0.5) * 2.5
            d = np.clip(np.hypot((X - cx) / rx, (Z - cz) / rz), 0, 1)
            dome = np.sqrt(np.clip(1 - d * d, 0, 1))
            hgt = 5 + (hh - 5) * dome * (0.75 + 0.5 * n1)
            sel = m & np.isnan(F)
            F = np.where(sel, fld, F)
            Hh = np.where(sel, hgt, Hh)
        for pts, w, hh in paths:
            pts_w = [(self.x0 + x, self.z0 + z) for x, z in pts]
            pm = self.path_mask(pts_w, w)

            def fl_at(p):
                i, k = int(p[0]), int(p[1])
                win = F[max(0, i - 3):i + 4, max(0, k - 3):k + 4]
                v = win[~np.isnan(win)]
                return float(v.mean()) if len(v) else 60.0
            f0, f1 = fl_at(pts[0]), fl_at(pts[-1])
            seglen = [math.dist(a_, b_) for a_, b_ in zip(pts[:-1], pts[1:])]
            total = sum(seglen) or 1
            for (i, k) in np.argwhere(pm & np.isnan(F)):
                best, bt, acc = 1e9, 0.0, 0.0
                for (p0, p1), Lg in zip(zip(pts[:-1], pts[1:]), seglen):
                    vx, vz = p1[0] - p0[0], p1[1] - p0[1]
                    t = ((i - p0[0]) * vx + (k - p0[1]) * vz) / max(Lg * Lg, 1e-6)
                    t = min(max(t, 0), 1)
                    dd = math.hypot(i - (p0[0] + vx * t), k - (p0[1] + vz * t))
                    if dd < best:
                        best, bt = dd, (acc + t * Lg) / total
                    acc += Lg
                F[i, k] = f0 + (f1 - f0) * bt
                Hh[i, k] = hh + n2[i, k] * 2
        cave = ~np.isnan(F)
        fl = np.where(cave, F, 0)
        fl = gaussian_filter(fl, smooth) / np.maximum(gaussian_filter(cave.astype(float), smooth), 1e-3)
        Fi = np.round(fl).astype(int)
        Ci = np.round(fl + gaussian_filter(Hh, 1.2) + (n3 - 0.5) * 3).astype(int)
        Ci = np.maximum(Ci, Fi + 4)
        # rock body
        blk = a.blk
        for i in range(self.sx):
            for k in range(self.sz):
                col = blk[i, :, k]
                for j in range(self.SY):
                    y = j + self.Y0
                    col[j] = rock[(y // 5 + (i // 17) + (k // 13)) % len(rock)]
                if cave[i, k]:
                    f, c = Fi[i, k], Ci[i, k]
                    for y in range(f + 1, min(c, self.Y0 + self.SY - 2) + 1):
                        col[y - self.Y0] = AIR
        self.F, self.C, self.cave, self.masks = Fi, Ci, cave, masks
        return Fi, Ci

    def patch_paint(self, mask, layers, scale=7.0, speckle=0.1, seed=91, floor=None):
        """Repaint the top block of `mask` columns in coherent patches instead of per-block noise.
        layers: [(upper_threshold, mixer)] in increasing order, chosen by an fbm value in 0..1."""
        a, rng = self.a, self.rng
        n = fbm(self.sx, self.sz, scale, 3, self.seed + seed)
        F = floor if floor is not None else self.H
        water = B("water")
        for (i, k) in np.argwhere(mask):
            j = int(F[i, k]) - self.Y0
            if j < 0 or j >= self.SY or a.blk[i, j, k] == water:
                continue
            v = n[i, k]
            if rng.random() < speckle:
                v = rng.random()
            for thr, mix in layers:
                if v <= thr:
                    a.blk[i, j, k] = mix()
                    break

    def keep_margin(self, margin, rock):
        """Refill cavern cells closer than `margin` to the area edge with rock (nothing opens onto the void)."""
        edge = np.zeros(self.cave.shape, bool)
        edge[:margin, :] = edge[-margin:, :] = edge[:, :margin] = edge[:, -margin:] = True
        for (i, k) in np.argwhere(self.cave & edge):
            col = self.a.blk[i, :, k]
            for j in range(self.SY):
                col[j] = rock[((j + self.Y0) // 5 + (i // 17) + (k // 13)) % len(rock)]
            self.cave[i, k] = False
            for m in self.masks.values():
                m[i, k] = False

    def paint_valley(self, top, sub, rock, deep=None, slope_rock=1.5, beach=None):
        """Fill columns: rock body (palette by height bands), floor top/sub mixers on carved and gentle ground."""
        a = self.a
        gy, gx = np.gradient(self.H.astype(float))
        slope = np.hypot(gx, gy)
        deep = deep or B("deepslate")
        for i in range(self.sx):
            for k in range(self.sz):
                h = int(self.H[i, k])
                col = a.blk[i, :, k]
                tj = h - self.Y0
                if tj < 0:
                    continue
                col[:min(tj + 1, self.SY)] = deep
                for j in range(max(0, tj - 40), min(tj + 1, self.SY)):
                    col[j] = rock[((j + self.Y0) // 4 + i // 19 + k // 23) % len(rock)]
                if tj >= self.SY:
                    continue
                if slope[i, k] > slope_rock and not self.carved[i, k]:
                    continue
                if beach is not None and beach(i, k, h):
                    col[tj] = beach.block()
                    continue
                col[tj] = top()
                for d in range(1, 3):
                    if tj - d >= 0:
                        col[tj - d] = sub()

    # ------------------------------------------------------------ dressing
    def dress_walls(self, carved, palette, moss=0.18, vines=0.25, rim=None, rim_trees=0.04, lichen=0.02, top_y=None):
        """Texture valley walls next to `carved`: palette stone by noise, moss patches, hanging vines from the rim,
        and grass / bushes / trees along the rim so the skyline is not a flat line."""
        a, rng = self.a, self.rng
        dist = distance_transform_edt(~carved)
        ring = (dist > 0) & (dist <= 5)
        n = fbm(self.sx, self.sz, 9, 3, self.seed + 77)
        pal = palette
        vine_bits = {(0, 1): 4, (0, -1): 1, (1, 0): 2, (-1, 0): 8}     # neighbour direction -> bit of the face it hangs on
        mossb = B("moss_block")
        for (i, k) in np.argwhere(ring):
            x, z = self.x0 + i, self.z0 + k
            h = self.H[i, k] if hasattr(self, "H") else None
            if h is None:
                continue
            v = n[i, k]
            col = a.blk[i, :, k]
            for y in range(int(self.near_floor[i, k]) if hasattr(self, "near_floor") else h - 20, h + 1):
                j = y - self.Y0
                if j < 0 or j >= self.SY or col[j] == AIR:
                    continue
                exposed = False
                for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if a.get(x + dx, y, z + dz) == AIR:
                        exposed = True
                        break
                if not exposed:
                    continue
                r = rng.random()
                if r < moss * (1.3 - (y - self.near_floor[i, k]) / 20.0 if hasattr(self, "near_floor") else 1):
                    col[j] = mossb
                else:
                    col[j] = pal[int((v * 3 + y / 6.0 + rng.random() * 0.6)) % len(pal)]
            # vines hanging from the rim towards the valley
            if rng.random() < vines:
                for (dx, dz), bit in vine_bits.items():
                    ii, kk = i + dx, k + dz
                    if 0 <= ii < self.sx and 0 <= kk < self.sz and carved[ii, kk]:
                        vx, vz = x + dx, z + dz
                        for t in range(rng.randint(3, 9)):
                            yy = h - t
                            if a.get(vx, yy, vz) == AIR and a.get(x, yy, z) != AIR:
                                a.set(vx, yy, vz, B("vine", vine_direction_bits={(0, 1): 1, (0, -1): 4, (1, 0): 8, (-1, 0): 2}[(-dx, -dz)]))
                            else:
                                break
                        break
        # the rim on top of the walls
        if rim:
            top = (dist > 1) & (dist <= 9)
            for (i, k) in np.argwhere(top):
                if rng.random() > 0.55:
                    continue
                x, z = self.x0 + i, self.z0 + k
                h = self.H[i, k]
                if a.get(x, h + 1, z) != AIR or h >= self.Y0 + self.SY - 12:
                    continue
                r = rng.random()
                if r < rim_trees:
                    rim["tree"](a, x, h + 1, z, rng)
                elif r < 0.45:
                    a.set(x, h + 1, z, B(rng.choice(rim["plants"])))
                elif r < 0.55 and rim.get("bush"):
                    a.set(x, h + 1, z, rim["bush"])

    def light_fill(self, box, yr, level=7, threshold=4, spacing=6):
        import lighting
        return lighting.fill_dark(self.a, box, yr, threshold=threshold, level=level, height=4, spacing=spacing, rounds=3)

    # ------------------------------------------------------------ boundary
    def boundary(self, top=None):
        """Barrier walls on the four edges up to the top of the area, border blocks under them."""
        a = self.a
        bar, bb = B("barrier"), B("border_block")
        sy = self.SY
        for (i_range, k_range) in ((range(self.sx), (0, self.sz - 1)), ((0, self.sx - 1), range(self.sz))):
            for i in (i_range if isinstance(i_range, range) else i_range):
                for k in (k_range if isinstance(k_range, range) else k_range):
                    col = a.blk[i, :, k]
                    col[0] = bb
                    for y in range(1, sy):
                        if col[y] == 0 or PAL.names[col[y]] in ("water", "flowing_water", "lava", "flowing_lava"):
                            col[y] = bar
                            a.wet[i, y, k] = False

    def ceiling(self, y):
        """Barrier ceiling (for dungeons whose walls are lower than the area top)."""
        a = self.a
        j = y - self.Y0
        if 0 <= j < self.SY:
            m = a.blk[:, j, :] == 0
            a.blk[:, j, :][m] = B("barrier")

    # ------------------------------------------------------------ export
    def export(self):
        zones = []
        for key in ["c1", "c2", "c3", "c4", "c5", "c6"]:
            if key in self.zones:
                z = self.zones[key]
                zones.append(dict(id="%s_%s" % (self.did, key), dungeon=self.did, key=key, ko=z["ko"], box=z["box"],
                                  points=z["points"], mobs=z["mobs"], cap=z["cap"]))
        region = [self.x0, self.Y0, self.z0, self.x0 + self.sx - 1, self.Y0 + self.SY - 1, self.z0 + self.sz - 1]
        return dict(id=self.did, region=region, start=self.data["start"], ret=self.data["ret"], exit=self.data["exit"],
                    zones=zones, arenas=self.arenas, biome=self.d["biome"], ambient=getattr(self, "ambient", []))
