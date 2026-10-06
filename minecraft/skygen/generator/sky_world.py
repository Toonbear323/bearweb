"""One global voxel buffer for the whole sky archipelago + tools that turn a map into a floating island.

Coordinates: islands keep the heights of the original maps (ground ~ y 64); the void below is empty down
to the bottom of the world, so falling off an island kills (as in every skygen server).
"""
import math
import random

import numpy as np
from scipy.ndimage import distance_transform_edt, binary_dilation

from mcw import B, AIR, Area, PAL, physics_tables
from gen_common import fbm, superdist

X0, Z0 = -368, -368
SX, SZ = 736, 752
Y0, SY = 16, 128

LIQ_NAMES = {"water", "flowing_water", "lava", "flowing_lava"}


class SkyWorld:
    def __init__(self):
        self.a = Area("sky", X0, Z0, SX, SZ, y0=Y0, sy=SY, biome=1)
        self.islands = {}          # key -> dict(name, center, R, ...)
        self.safe_zones = []       # (name, x1, y1, z1, x2, y2, z2)
        self.generators = []       # dict(x, y, z, block, kind, regen)
        self.portals = []          # dict(key, box, dest, ...)
        self.arrivals = {}         # key -> (x, y, z, yaw)
        self.npcs = []             # dict(name, x, y, z, face, tag, kind)
        self.plots = []
        self.furnace_rooms = []
        self.signs = []            # dynamic signs updated by the script
        self.ender_chests = []
        self.enchant_tables = []
        self.buttons = []          # dict(x, y, z, action, arg)
        self.light_boxes = []
        self.no_walk = []          # boxes excluded from the walk check (plots)
        self.notes = []

    # ------------------------------------------------------------------ copying maps in
    def paste(self, src, dy=0, only_solid=False):
        """Copy a generated Area into the global buffer (same x/z, shifted by dy), clipped to the buffer."""
        a = self.a
        ix, iz = src.x0 - a.x0, src.z0 - a.z0
        iy = src.y0 + dy - a.y0
        x_lo, x_hi = max(0, -ix), min(src.sx, a.sx - ix)
        y_lo, y_hi = max(0, -iy), min(src.sy, a.sy - iy)
        z_lo, z_hi = max(0, -iz), min(src.sz, a.sz - iz)
        dsl = (slice(ix + x_lo, ix + x_hi), slice(iy + y_lo, iy + y_hi), slice(iz + z_lo, iz + z_hi))
        ssl = (slice(x_lo, x_hi), slice(y_lo, y_hi), slice(z_lo, z_hi))
        s, w = src.blk[ssl], src.wet[ssl]
        if only_solid:
            m = s != AIR
            a.blk[dsl][m] = s[m]
            a.wet[dsl][m] = w[m]
        else:
            a.blk[dsl] = s
            a.wet[dsl] = w
        a.bio[dsl[0], dsl[2]] = src.bio[ssl[0], ssl[2]]
        for (x, y, z), be in src.be.items():
            if a.inside(x, y + dy, z):
                a.be[(x, y + dy, z)] = be

    def view(self, x0, z0, sx, sz):
        a = self.a
        return a.blk[x0 - a.x0:x0 - a.x0 + sx, :, z0 - a.z0:z0 - a.z0 + sz]

    def ys(self):
        return np.arange(self.a.sy) + self.a.y0


def coast_mask(DX, DZ, R, p, seed, wobble=4.0, extra=3.0):
    """Irregular island outline around a superellipse of radius R."""
    sx, sz = DX.shape
    n1 = fbm(sx, sz, 22, 3, seed)
    n2 = fbm(sx, sz, 7, 2, seed + 1)
    D = superdist(DX, DZ, p)
    edge = R + extra + (n1 - 0.5) * 2 * wobble + (n2 - 0.5) * 2.0
    return D <= edge


def shape_island(W, x0, z0, foot, H, seed, under, max_depth=30, spikes=10, keep_box=None, deco=True,
                 old_bottom=32, keep_leaves=True):
    """Cut the buffer around one island.

    foot: bool (sx, sz) footprint in local coords starting at (x0, z0); everything outside is cleared.
    H: ground surface y per column (local); the underside hangs below it like an upside-down cone.
    under(rng, x, y, z, depth_below_ground) -> block for the new rock under the old map bottom.
    """
    a = W.a
    sx, sz = foot.shape
    rng = random.Random(seed)
    V = W.view(x0, z0, sx, sz)                       # (sx, sy, sz) view
    WET = a.wet[x0 - a.x0:x0 - a.x0 + sx, :, z0 - a.z0:z0 - a.z0 + sz]
    ys = W.ys()
    # 1. clear everything outside the footprint
    outside = ~foot
    if keep_leaves:                                  # tree crowns may overhang the coast
        leaf_ids = [i for i, (n, _s) in enumerate(PAL.entries) if "leaves" in n]
        near = binary_dilation(foot, iterations=5)
        lv = np.isin(V, leaf_ids) & near[:, None, :]
    if keep_box is not None:
        kx1, kz1, kx2, kz2 = keep_box
        lx = np.arange(sx)[:, None] + x0
        lz = np.arange(sz)[None, :] + z0
        outside &= ~((lx >= kx1) & (lx <= kx2) & (lz >= kz1) & (lz <= kz2))
    clear = outside[:, None, :].repeat(a.sy, axis=1)
    if keep_leaves:
        clear &= ~lv
    V[clear] = AIR
    WET[clear] = False
    # 2. underside profile
    edge = distance_transform_edt(foot)
    n1 = fbm(sx, sz, 16, 3, seed + 7)
    n2 = fbm(sx, sz, 5, 2, seed + 8)
    depth = 3.0 + np.minimum(edge * 0.85, max_depth) * (0.7 + 0.6 * n1) + (n2 - 0.5) * 3.0
    bottom = np.floor(H - depth).astype(np.int32)
    # never cut into caves, tunnels or liquid floors of the old map
    liq_ids = [i for i, (n, _s) in enumerate(PAL.entries) if n in LIQ_NAMES]
    open_cell = (V == AIR) | np.isin(V, liq_ids)
    yy = ys[None, :, None]
    probe = open_cell & (yy >= old_bottom) & (yy <= H[:, None, :])
    has = probe.any(axis=1)
    lowest_open = np.where(has, ys[np.argmax(probe, axis=1)], 10 ** 6)
    bottom = np.minimum(bottom, lowest_open - 2)
    bottom = np.maximum(bottom, a.y0 + 1)
    # spikes: narrow stalactites under the thick middle
    pts = np.argwhere(foot & (edge > 9))
    for _ in range(spikes if len(pts) else 0):
        i, k = pts[rng.randrange(len(pts))]
        r0 = rng.uniform(2.0, 4.5)
        L = rng.uniform(8, 18)
        for di in range(-6, 7):
            for dk in range(-6, 7):
                ii, kk = i + di, k + dk
                if not (0 <= ii < sx and 0 <= kk < sz) or not foot[ii, kk]:
                    continue
                d = math.hypot(di, dk)
                if d > r0:
                    continue
                extra = L * (1 - d / r0) ** 1.6
                bottom[ii, kk] = min(bottom[ii, kk], int(bottom[ii, kk] - extra))
    bottom = np.maximum(bottom, a.y0 + 1)
    # 3. carve below the profile, fill new rock between the profile and the old map bottom
    below = foot[:, None, :] & (yy < bottom[:, None, :])
    V[below] = AIR
    WET[below] = False
    fill = foot[:, None, :] & (yy >= bottom[:, None, :]) & (yy < old_bottom) & (V == AIR)
    idx = np.argwhere(fill)
    for (i, j, k) in idx:
        y = int(ys[j])
        V[i, j, k] = under(rng, x0 + i, y, z0 + k, int(H[i, k]) - y)
    # 4. underside decoration: hanging roots / glow berries / lichen along the rim
    if deco:
        for (i, k) in np.argwhere(foot & (edge <= 3.5)):
            if rng.random() < 0.10:
                b = int(bottom[i, k]) - 1
                if b - a.y0 < 2:
                    continue
                j = b - a.y0
                if V[i, j + 1, k] == AIR:
                    continue
                r = rng.random()
                if r < 0.45:
                    V[i, j, k] = B("hanging_roots")
                elif r < 0.75:
                    n = rng.randint(2, 6)
                    for t in range(n):
                        if j - t < 0:
                            break
                        last = t == n - 1
                        berries = rng.random() < 0.35
                        name = ("cave_vines_head_with_berries" if berries else "cave_vines") if last else \
                            ("cave_vines_body_with_berries" if berries else "cave_vines")
                        V[i, j - t, k] = B(name)
                else:
                    V[i, j, k] = B("glow_lichen", multi_face_direction_bits=2)
    return bottom


def seal_liquids(W, rim, box=None, rounds=6):
    """Any water/lava cell that touches air sideways or below gets that air replaced by rim."""
    a = W.a
    liq_ids = np.array([i for i, (n, _s) in enumerate(PAL.entries) if n in LIQ_NAMES])
    if box:
        x1, z1, x2, z2 = box
        sl = (slice(x1 - a.x0, x2 - a.x0 + 1), slice(None), slice(z1 - a.z0, z2 - a.z0 + 1))
    else:
        sl = (slice(None), slice(None), slice(None))
    total = 0
    for _ in range(rounds):
        V = a.blk[sl]
        WT = a.wet[sl]
        liq = np.isin(V, liq_ids) | WT
        airm = V == AIR
        need = np.zeros_like(airm)
        need[1:, :, :] |= liq[:-1, :, :] & airm[1:, :, :]
        need[:-1, :, :] |= liq[1:, :, :] & airm[:-1, :, :]
        need[:, :, 1:] |= liq[:, :, :-1] & airm[:, :, 1:]
        need[:, :, :-1] |= liq[:, :, 1:] & airm[:, :, :-1]
        need[:, :-1, :] |= liq[:, 1:, :] & airm[:, :-1, :]
        n = int(need.sum())
        if not n:
            break
        V[need] = rim
        total += n
    return total


def persist_leaves(W):
    """Leaves never decay (players cut generator logs next to decorative trees)."""
    a = W.a
    remap = {}
    for i, (name, st) in enumerate(list(PAL.entries)):
        if name.endswith("leaves") or name.endswith("leaves_flowered") or name == "azalea_leaves_flowered":
            if "persistent_bit" in st and st["persistent_bit"][1] == 0:
                states = {k: v[1] for k, v in st.items()}
                states["persistent_bit"] = 1
                remap[i] = PAL.get(name, states)
    for old, new in remap.items():
        a.blk[a.blk == old] = new
    return len(remap)


def fix_plants(W):
    """Remove plants the game would pop on the first block update: half double-plants, sugar cane without
    water or on a block it cannot stand on (a dirt path under it becomes grass), mushrooms in bright light on
    grass (they get podzol under them)."""
    a = W.a
    names = PAL.names
    n = 0
    dbl = [i for i, (nm, st) in enumerate(PAL.entries) if "upper_block_bit" in st and not nm.endswith("door")]
    for i in dbl:
        nm, st = PAL.entries[i]
        upper = st["upper_block_bit"][1]
        for (x, j, z) in np.argwhere(a.blk == i):
            jj = j - 1 if upper else j + 1
            if not (0 <= jj < a.sy) or names[a.blk[x, jj, z]] != nm:
                a.blk[x, j, z] = AIR
                n += 1
    reeds = PAL.lookup and [i for i, (nm, st) in enumerate(PAL.entries) if nm == "reeds"]
    water = {i for i, (nm, st) in enumerate(PAL.entries) if nm in ("water", "flowing_water")}
    reed_base = ("grass_block", "dirt", "coarse_dirt", "podzol", "mycelium", "dirt_with_roots", "moss_block", "mud",
                 "muddy_mangrove_roots", "sand", "red_sand", "suspicious_sand")
    for i in reeds:
        for (x, j, z) in np.argwhere(a.blk == i):
            if j > 0 and names[a.blk[x, j - 1, z]] == "reeds":
                continue
            base = names[a.blk[x, j - 1, z]] if j > 0 else "air"
            if base in ("grass_path", "farmland"):
                # a path laid up to the cane: sugar cane does not stand on dirt path
                a.blk[x, j - 1, z] = B("grass_block")
                n += 1
            ok = False
            if base in reed_base or base in ("grass_path", "farmland"):
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, zz = x + dx, z + dz
                    if 0 <= xx < a.sx and 0 <= zz < a.sz and (a.blk[xx, j - 1, zz] in water or a.wet[xx, j - 1, zz]):
                        ok = True
            if not ok:
                t = j
                while t < a.sy and names[a.blk[x, t, z]] == "reeds":
                    a.blk[x, t, z] = AIR
                    t += 1
                    n += 1
    shrooms = [i for i, (nm, st) in enumerate(PAL.entries) if nm in ("brown_mushroom", "red_mushroom")]
    pod = B("podzol")
    for i in shrooms:
        for (x, j, z) in np.argwhere(a.blk == i):
            if j > 0 and names[a.blk[x, j - 1, z]] in ("grass_block", "dirt", "coarse_dirt", "moss_block", "dirt_with_roots"):
                a.blk[x, j - 1, z] = pod
                n += 1
    return n
