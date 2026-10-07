"""Shared machinery for the high-tier realm dungeons: valley terrain with walled boss basins.

Each boss stands in its own basin; paths in and out pass through gate walls that fill the whole path cross-section,
so a gate can never be walked around. Hazard liquids (lava) get a rim with an invisible cap on every floor cell that
touches them. Walk boxes plus a height rule decide what counts as an escape.
"""
import math

import numpy as np
from scipy.ndimage import distance_transform_edt

from mcw import B, AIR, PAL
import nr_castle as C
from nr_dungeon import Dungeon


class Realm(Dungeon):
    ZN = {}
    PATHS = []

    def realm_setup(self):
        self.walk_boxes = []
        self.lava = np.zeros((self.sx, self.sz), bool)
        self.blocked = np.zeros((self.sx, self.sz), bool)
        self.no_rim = set()
        self.gate_spots = []

    def w(self, lx, lz):
        return self.x0 + lx, self.z0 + lz

    def _at(self, lx, lz):
        x, z = self.w(lx, lz)
        return x, int(self.H[lx, lz]) + 1, z

    def free(self, lx, lz):
        return 0 <= lx < self.sx and 0 <= lz < self.sz and self.carved[lx, lz] and self.wall_dist[lx, lz] == 0 \
            and not self.lava[lx, lz] and not self.blocked[lx, lz]

    def zbox(self, key, pad=3, dy=(-4, 10)):
        cx, cz, rx, rz = self.ZN[key][:4]
        x, z = self.w(cx, cz)
        f = int(np.mean(self.H[max(0, cx - 3):cx + 4, max(0, cz - 3):cz + 4]))
        return (x - rx - pad, f + dy[0], z - rz - pad, x + rx + pad, f + dy[1], z + rz + pad)

    def allow(self, lx1, lz1, lx2, lz2, y1, y2):
        x1, z1 = self.w(lx1, lz1)
        x2, z2 = self.w(lx2, lz2)
        self.walk_boxes.append((min(x1, x2), y1, min(z1, z2), max(x1, x2), y2, max(z1, z2)))

    def lava_cells(self, cells, depth=2, rim=True):
        """Lava one block below the floor in the given local cells; a blackstone rim with a barrier cap on every
        floor cell that touches the lava, so nobody walks or jumps in."""
        a = self.a
        S = set(cells)
        for (i, k) in S:
            if not self.carved[i, k]:
                continue
            x, z = self.w(i, k)
            f = int(self.H[i, k])
            for y in range(f - depth, f):
                a.set(x, y, z, B("lava"))
            a.set(x, f - depth - 1, z, B("magma"))
            for y in range(f, f + 4):
                a.set(x, y, z, AIR)
            self.lava[i, k] = True
            self.H[i, k] = f - 1
        if rim:
            for (i, k) in S:
                for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    c = (i + di, k + dk)
                    if c in S or not (0 <= c[0] < self.sx and 0 <= c[1] < self.sz) or not self.carved[c] or self.lava[c]:
                        continue
                    if c in self.no_rim:
                        continue
                    x, z = self.w(*c)
                    f = int(self.H[c])
                    a.set(x, f + 1, z, B("polished_blackstone_wall"))
                    for y in range(f + 2, f + 4):
                        a.set(x, y, z, B("barrier"))
                    self.blocked[c] = True

    def gate_wall(self, lx, lz, axis, half, floor_y, gw=7, gh=7, height=14):
        """A wall across a path (filling every carved cell of the line) with a doorway; returns the doorway cells."""
        a, pal = self.a, self.pal
        cells = [(lx, lz + t) for t in range(-half, half + 1)] if axis == "x" else [(lx + t, lz) for t in range(-half, half + 1)]
        for (i, k) in cells:
            if not self.carved[i, k]:
                continue
            x, z = self.w(i, k)
            f = int(self.H[i, k])
            for y in range(f - 2, floor_y + height):
                a.set(x, y, z, pal.wall() if (y - floor_y) % 6 != 5 else pal.trim)
            a.set(x, floor_y + height, z, pal.top)
            for y in range(floor_y + height + 1, floor_y + height + 4):
                a.set(x, y, z, B("barrier"))
            self.blocked[i, k] = True
        x, z = self.w(lx, lz)
        out = []
        for t in range(-(gw // 2), gw // 2 + 1):
            gx, gz = (x, z + t) if axis == "x" else (x + t, z)
            a.set(gx, floor_y - 1, gz, pal.floor())
            for y in range(floor_y, floor_y + gh):
                a.set(gx, y, gz, AIR)
                out.append((gx, y, gz))
            for y in range(floor_y - 2, floor_y - 1):
                a.set(gx, y, gz, pal.wall())
            li, lk = gx - self.x0, gz - self.z0
            self.blocked[li, lk] = False
        # ramps in front of and behind the doorway (the path floor may be a block off the gate floor)
        for t in range(-(gw // 2), gw // 2 + 1):
            for s in (-1, 1, -2, 2):
                gx, gz = (x + s, z + t) if axis == "x" else (x + t, z + s)
                li, lk = gx - self.x0, gz - self.z0
                if self.carved[li, lk]:
                    f = int(self.H[li, lk])
                    if abs(f - (floor_y - 1)) <= 2:
                        for y in range(min(f, floor_y - 1), max(f, floor_y - 1) + 1):
                            a.set(gx, y, gz, pal.floor())
                        for y in range(floor_y, floor_y + gh):
                            a.set(gx, y, gz, AIR)
                        self.H[li, lk] = floor_y - 1
        for y in (floor_y + gh,):
            for t in range(-(gw // 2) - 1, gw // 2 + 2):
                gx, gz = (x, z + t) if axis == "x" else (x + t, z)
                a.set(gx, y, gz, pal.trim)
        return out

    def fortify(self, key, height=16, towers=6, pal=None, tower_roof="cone"):
        """Dress the rim of a basin as built walls: masonry on the first ring of wall cells up to height above the
        floor, merlons on top, towers at intervals around the ring."""
        a, rng = self.a, self.rng
        pal = pal or self.pal
        m = self.masks[key]
        cx, cz = self.ZN[key][:2]
        f0 = int(np.median(self.H[m]))
        dist = distance_transform_edt(~m)
        ring = (dist > 0) & (dist <= 2.5) & ~self.carved
        for (i, k) in np.argwhere(ring):
            x, z = self.w(i, k)
            for y in range(f0 - 1, f0 + height):
                a.set(x, y, z, pal.wall() if (y - f0) % 7 != 6 else pal.trim)
            if dist[i, k] <= 1.5:
                a.set(x, f0 + height, z, pal.wall())
                if (i + k) % 3 == 0:
                    a.set(x, f0 + height + 1, z, pal.top)
            else:
                a.set(x, f0 + height, z, pal.floor())
        R = self.ZN[key][2] + 3
        for t in range(towers):
            ang = t / towers * 2 * math.pi + 0.4
            tx, tz = int(round(cx + math.cos(ang) * R)), int(round(cz + math.sin(ang) * R))
            if not (8 <= tx < self.sx - 8 and 8 <= tz < self.sz - 8):
                continue
            gates = any(math.hypot(tx - gx, tz - gz) < 12 for (gx, gz) in self.gate_spots)
            if gates:
                continue
            x, z = self.w(tx, tz)
            C.tower(a, x, z, f0, height + 12, 4, pal, roof=tower_roof, windows=False)
        return f0

    def lava_fall(self, i, k, di, dk):
        """A lava fall in a recess of the wall cell (i, k), facing the open direction (di, dk), with a rimmed pool."""
        a = self.a
        lat = (-dk, di)
        f = int(self.near_floor[i, k])
        top = int(self.H[i, k])
        cells = [(i + lat[0] * s, k + lat[1] * s) for s in (-1, 0, 1)]
        for (ci, ck) in cells:
            x, z = self.w(ci, ck)
            for y in range(f - 2, top):
                a.set(x, y, z, B("flowing_lava", liquid_depth=8) if y >= f else B("lava"))
            a.set(x, top, z, B("lava"))
            a.set(x, f - 3, z, B("magma"))
            self.lava[ci, ck] = True
        front = [(ci + di, ck + dk) for (ci, ck) in cells]
        for (ci, ck) in front:
            if not self.carved[ci, ck]:
                continue
            x, z = self.w(ci, ck)
            ff = int(self.H[ci, ck])
            a.set(x, ff + 1, z, B("polished_blackstone_wall"))
            for y in range(ff + 2, ff + 5):
                a.set(x, y, z, B("barrier"))
            self.blocked[ci, ck] = True

    def is_escape(self, x, y, z):
        i, k = x - self.x0, z - self.z0
        for (x1, y1, z1, x2, y2, z2) in self.walk_boxes:
            if x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2:
                return False
        if not (0 <= i < self.sx and 0 <= k < self.sz):
            return True
        near = self.carved[max(0, i - 3):i + 4, max(0, k - 3):k + 4].any()
        if not near:
            return True
        return y > int(self.H[i, k]) + 12

