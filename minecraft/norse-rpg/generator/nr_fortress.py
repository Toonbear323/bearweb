"""Shared machinery for the castle-type dungeons (mid and high tiers).

A fortress dungeon starts as solid masonry; rooms, courtyards and corridors are carved out of it, so anything not
carved can never be walked into. Walk boxes list every volume a player may legitimately stand in; standing anywhere
else (a roof, a crag top) counts as an escape in the verifier.
"""
import math

import numpy as np

from mcw import B, AIR
import nr_castle as C
from nr_dungeon import Dungeon


class Fortress(Dungeon):
    MT = 100                      # top of the solid masonry

    def setup(self):
        self.walk_boxes = []
        self.carved = np.zeros((self.sx, self.sz), bool)

    # ------------------------------------------------------------ coordinates
    def w(self, lx, lz):
        return self.x0 + lx, self.z0 + lz

    def allow(self, lx1, lz1, lx2, lz2, y1, y2):
        x1, z1 = self.w(lx1, lz1)
        x2, z2 = self.w(lx2, lz2)
        self.walk_boxes.append((min(x1, x2), y1, min(z1, z2), max(x1, x2), y2, max(z1, z2)))

    def is_escape(self, x, y, z):
        for (x1, y1, z1, x2, y2, z2) in self.walk_boxes:
            if x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2:
                return False
        return True

    # ------------------------------------------------------------ masonry and carving
    def mass(self, lx1, lz1, lx2, lz2, y1, y2, body):
        """Fill the box with masonry; body: list of block ids, banded by height and position."""
        a = self.a
        for i in range(lx1, lx2 + 1):
            for k in range(lz1, lz2 + 1):
                col = a.blk[i, :, k]
                for y in range(y1, y2 + 1):
                    col[y - self.Y0] = body[(y // 6 + i // 11 + k // 13) % len(body)]

    def carve(self, lx1, lz1, lx2, lz2, y1, y2, floor_b=None, mark=True):
        a = self.a
        for lx in range(min(lx1, lx2), max(lx1, lx2) + 1):
            for lz in range(min(lz1, lz2), max(lz1, lz2) + 1):
                x, z = self.w(lx, lz)
                col = a.blk[lx, :, lz]
                col[y1 - self.Y0:y2 - self.Y0 + 1] = AIR
                if floor_b is not None:
                    a.set(x, y1 - 1, z, floor_b() if callable(floor_b) else floor_b)
                if mark:
                    self.carved[lx, lz] = True

    def faces(self, lx1, lz1, lx2, lz2, sides=("north", "south", "east", "west")):
        """Cells just outside a carved rectangle, per side: [(side, [(lx, lz), ...])]."""
        out = []
        for side in sides:
            if side in ("north", "south"):
                lz = lz1 - 1 if side == "north" else lz2 + 1
                out.append((side, [(lx, lz) for lx in range(lx1, lx2 + 1)]))
            else:
                lx = lx1 - 1 if side == "west" else lx2 + 1
                out.append((side, [(lx, lz) for lz in range(lz1, lz2 + 1)]))
        return out

    def facade(self, lx1, lz1, lx2, lz2, side, y0, h, pal, every=8, win=(2, 3, 8, 9, 10), door_every=16, lamp="soul_lantern",
               win_cols=(3, 5), band=6):
        """Dress a carved wall face as building fronts: pilasters, trim bands, windows, shut doors with lamps."""
        a = self.a
        (side, cells), = self.faces(lx1, lz1, lx2, lz2, (side,))
        face = {"north": "south", "south": "north", "west": "east", "east": "west"}[side]
        dx, dz = C.DIRS[face]
        for i, (lx, lz) in enumerate(cells):
            x, z = self.w(lx, lz)
            if a.get(x, y0, z) == AIR:
                continue
            for y in range(y0, y0 + h):
                if a.get(x, y, z) == AIR:
                    continue
                b = pal.wall()
                if i % every == 0:
                    b = pal.pillar
                elif (y - y0) % band == band - 1 or y == y0 + h - 1:
                    b = pal.trim
                elif i % every in win_cols and (y - y0) in win:
                    b = pal.window
                a.set(x, y, z, b)
            if door_every and i % door_every == door_every // 4:
                for y in (y0, y0 + 1):
                    a.set(x, y, z, B("dark_oak_planks"))
                a.set(x, y0 + 2, z, pal.trim)
                a.put(x + dx, y0 + 3, z + dz, B(lamp))
            elif i % every == 0 and h > 8 and lamp:
                a.put(x + dx, y0 + 4, z + dz, B(lamp))

    def ceiling_beams(self, lx1, lz1, lx2, lz2, ytop, axis="x", every=8, beam="dark_oak_log"):
        a = self.a
        if axis == "x":
            for lz in range(lz1 + every // 2, lz2, every):
                for lx in range(lx1, lx2 + 1):
                    x, z = self.w(lx, lz)
                    a.set(x, ytop, z, B(beam, axis="x"))
        else:
            for lx in range(lx1 + every // 2, lx2, every):
                for lz in range(lz1, lz2 + 1):
                    x, z = self.w(lx, lz)
                    a.set(x, ytop, z, B(beam, axis="z"))

    def roofscape(self, pal, lx1, lz1, lx2, lz2, T=16, chimney=0.5, snow=False, rng=None):
        """Gable roofs and chimneys on top of uncarved masonry tiles so the fortress reads as a crowded town."""
        a, rng = self.a, rng or self.rng
        for tx in range(lx1, lx2 - T + 2, T):
            for tz in range(lz1, lz2 - T + 2, T):
                if self.carved[tx:tx + T, tz:tz + T].any():
                    continue
                x1, z1 = self.w(tx + 1, tz + 1)
                x2, z2 = self.w(tx + T - 2, tz + T - 2)
                axis = "x" if (tx // T + tz // T) % 2 else "z"
                C.gable_roof(a, x1, z1, x2, z2, self.MT + 1, axis, pal, overhang=1, end_fill=pal.wall)
                if snow:
                    for x in range(x1 - 1, x2 + 2):
                        for z in range(z1 - 1, z2 + 2):
                            for y in range(self.MT + 1, self.MT + T):
                                if a.get(x, y, z) != AIR and a.get(x, y + 1, z) == AIR and rng.random() < 0.55:
                                    a.set(x, y + 1, z, B("snow_layer", height=0))
                                    break
                if rng.random() < chimney:
                    cx, cz = x1 + rng.randint(2, T - 5), z1 + rng.randint(2, T - 5)
                    for y in range(self.MT + 1, self.MT + 12):
                        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                            a.set(cx + dx, y, cz + dz, pal.trim)
                    a.set(cx, self.MT + 12, cz, B("campfire"))

    # ------------------------------------------------------------ walkways
    def walkway(self, cells, y, posts=8, plank="dark_oak_planks", fence="dark_oak_fence", open_cells=(), post_bottom=None):
        a = self.a
        S = set(cells)
        for (lx, lz) in S:
            x, z = self.w(lx, lz)
            a.set(x, y, z, B(plank))
            for yy in range(y + 1, y + 5):
                a.set(x, yy, z, AIR)
            if post_bottom is not None and (lx + lz) % posts == 0:
                for yy in range(post_bottom, y):
                    if a.get(x, yy, z) in (AIR, B("water")):
                        a.set(x, yy, z, B("dark_oak_log", axis="y"))
        ring = set()
        for (lx, lz) in S:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    c = (lx + dx, lz + dz)
                    if c not in S and c not in open_cells:
                        ring.add(c)
        for (lx, lz) in ring:
            x, z = self.w(lx, lz)
            if a.get(x, y, z) == AIR and a.get(x, y + 1, z) == AIR:
                a.set(x, y + 1, z, B(fence))

    # ------------------------------------------------------------ props
    def heap(self, x, y, z, r, mix, rng=None):
        a, rng = self.a, rng or self.rng
        for dx in range(-int(r) - 1, int(r) + 2):
            for dz in range(-int(r) - 1, int(r) + 2):
                dd = math.hypot(dx, dz)
                if dd <= r:
                    for t in range(int((r - dd) * 0.9) + 1):
                        a.put(x + dx, y + t, z + dz, mix())
