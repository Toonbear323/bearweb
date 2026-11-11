"""Walkability checker: breadth-first search of player movement through a World.

Used as a stand-in for play-testing: verifies that dungeon routes are actually traversable."""
from collections import deque

import numpy as np

from .core import REG

_PASS_KEYS = ("door", "torch", "sign", "carpet", "pressure_plate", "button", "rail", "ladder", "vine", "web", "banner",
              "lever", "short_grass", "tall_grass", "fern", "tulip", "poppy", "flower", "orchid", "allium", "bluet",
              "daisy", "cornflower", "lily_of_the_valley", "lilac", "peony", "rose_bush", "sunflower", "roots",
              "sprouts", "sapling", "deadbush", "reeds", "petals", "snow_layer", "wire", "candle", "lichen",
              "sculk_vein", "spore_blossom", "seagrass", "kelp", "sea_pickle", "coral_fan", "dripleaf", "wheat",
              "nether_wart", "fence_gate", "frame", "sweet_berry")
_PASS_EXACT = {"air", "light_block", "crimson_fungus", "warped_fungus", "brown_mushroom", "red_mushroom",
               "tube_coral", "brain_coral", "bubble_coral", "fire_coral", "horn_coral", "waterlily", "sculk_sensor"}
_BARRIER_KEYS = ("fence", "_wall", "pane", "iron_bars", "lantern", "chain", "end_rod", "pointed_dripstone", "skull",
                 "flower_pot", "amethyst_cluster", "amethyst_bud", "bell", "azalea", "brewing_stand", "lightning_rod",
                 "decorated_pot", "cactus", "fire", "portal", "magma")


def tables():
    n = len(REG.entries)
    passable = np.zeros(n, bool)
    barrier = np.zeros(n, bool)
    water = np.zeros(n, bool)
    lava = np.zeros(n, bool)
    ladder = np.zeros(n, bool)
    for i, (name, st) in enumerate(REG.entries):
        std = {k: v for k, t, v in st}
        if name in ("water", "flowing_water"):
            water[i] = True
            continue
        if name in ("lava", "flowing_lava"):
            lava[i] = True
            continue
        if name == "ladder":
            ladder[i] = True
            passable[i] = True
            continue
        if "trapdoor" in name:
            passable[i] = bool(std.get("open_bit"))
            continue
        if name in _PASS_EXACT or (any(k in name for k in _PASS_KEYS) and not name.endswith("_block")
                                   and "nether_wart_block" != name):
            if "fence_gate" in name or not any(k in name for k in ("fence", "_wall")):
                passable[i] = True
                continue
        if any(k in name for k in _BARRIER_KEYS) and name not in ("magma",):
            barrier[i] = True
    return passable, barrier, water, lava, ladder


def reach(w, start, goals, box, max_fall=None, tol=2):
    import os
    max_fall = max_fall or int(os.environ.get("BEAR_MAX_FALL", "6"))
    """BFS from start (x,y,z feet) inside box; returns {goal: bool}."""
    xa, ya, za, xb, yb, zb = box
    xa, xb = max(xa, w.x0), min(xb, w.x1 - 1)
    za, zb = max(za, w.z0), min(zb, w.z1 - 1)
    ya, yb = max(ya, w.y0), min(yb, w.y1 - 2)
    A = w.b[xa - w.x0:xb + 1 - w.x0, za - w.z0:zb + 1 - w.z0, ya - w.y0:yb + 2 - w.y0]
    WL = w.wl[xa - w.x0:xb + 1 - w.x0, za - w.z0:zb + 1 - w.z0, ya - w.y0:yb + 2 - w.y0]
    passable, barrier, water, lava, ladder = tables()
    P = passable[A]
    Wt = water[A] | (WL & P)
    Lv = lava[A]
    Ld = ladder[A]
    free = P | Wt
    solid = ~free & ~Lv
    stand_ok = solid & ~barrier[A]
    nx, nz, ny = A.shape
    seen = np.zeros(A.shape, bool)

    def ok_cell(x, y, z):
        if not (0 <= x < nx and 0 <= z < nz and 1 <= y < ny - 1):
            return False
        if not (free[x, z, y] and free[x, z, y + 1]):
            return False
        return bool(stand_ok[x, z, y - 1] or Wt[x, z, y] or Wt[x, z, y - 1] or Ld[x, z, y] or Ld[x, z, y - 1])

    sx, sy, sz = start[0] - xa, start[1] - ya, start[2] - za
    # snap the start to the nearest valid cell
    best = None
    for dy in range(0, 5):
        for d in (dy, -dy):
            if ok_cell(sx, sy + d, sz):
                best = (sx, sy + d, sz)
                break
        if best:
            break
    if best is None:
        return {g: False for g in goals}, 0
    q = deque([best])
    seen[best[0], best[2], best[1]] = True
    cnt = 0
    while q:
        x, y, z = q.popleft()
        cnt += 1
        inw = Wt[x, z, y]
        onl = Ld[x, z, y] or Ld[x, z, y - 1]
        cand = []
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Z = x + dx, z + dz
            if not (0 <= X < nx and 0 <= Z < nz):
                continue
            # same level, step up one (needs head room above current position)
            cand.append((X, y, Z))
            if y + 2 < ny and free[x, z, y + 2]:
                cand.append((X, y + 1, Z))
            # drop down
            for d in range(1, max_fall + 1):
                if y - d < 1:
                    break
                if not free[X, Z, y - d + 1]:
                    break
                cand.append((X, y - d, Z))
                if not free[X, Z, y - d]:
                    break
        if inw or onl or (y + 1 < ny and (Wt[x, z, y + 1] or Ld[x, z, y + 1])):
            cand.append((x, y + 1, z))
        if inw or onl or Wt[x, z, y - 1] or Ld[x, z, y - 1]:
            cand.append((x, y - 1, z))
        for (X, Y, Z) in cand:
            if 0 <= X < nx and 0 <= Z < nz and 1 <= Y < ny - 1 and not seen[X, Z, Y] and ok_cell(X, Y, Z):
                seen[X, Z, Y] = True
                q.append((X, Y, Z))
    res = {}
    for g in goals:
        gx, gy, gz = g[0] - xa, g[1] - ya, g[2] - za
        s = seen[max(0, gx - tol):gx + tol + 1, max(0, gz - tol):gz + tol + 1, max(0, gy - tol):gy + tol + 1]
        res[g] = bool(s.any())
    return res, cnt
