"""Overworld terrain: island heightmap, biomes, rivers, roads, ores and vegetation."""
import math

import numpy as np

from . import blocks as bl
from . import kit
from .core import B, Mix
from .layout import *  # noqa: F401,F403


def value_noise(sx, sz, cell, rng):
    gx, gz = sx // cell + 3, sz // cell + 3
    g = rng.random((gx, gz)).astype(np.float32)
    xs = np.arange(sx) / cell
    zs = np.arange(sz) / cell
    xi, zi = xs.astype(int), zs.astype(int)
    xf, zf = (xs - xi).astype(np.float32), (zs - zi).astype(np.float32)
    xf = xf * xf * (3 - 2 * xf)
    zf = zf * zf * (3 - 2 * zf)
    a = g[xi][:, zi]
    b = g[xi + 1][:, zi]
    c = g[xi][:, zi + 1]
    d = g[xi + 1][:, zi + 1]
    return (a * (1 - xf)[:, None] + b * xf[:, None]) * (1 - zf)[None, :] + (
        c * (1 - xf)[:, None] + d * xf[:, None]) * zf[None, :]


def fbm(sx, sz, cell, rng, octaves=4, gain=0.5):
    total, amp, norm = 0, 1.0, 0.0
    for o in range(octaves):
        total = total + amp * value_noise(sx, sz, max(1, cell >> o), rng)
        norm += amp
        amp *= gain
    return total / norm


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


# coast radius by angle (degrees from +x toward +z)
_COAST = [(0, 415), (40, 400), (70, 250), (84, 172), (90, 160), (96, 172), (110, 250), (140, 410), (180, 420),
          (225, 470), (270, 420), (315, 500), (360, 415)]


def coast_radius(theta_deg):
    t = np.mod(theta_deg, 360.0)
    out = np.zeros_like(t)
    for (a0, r0), (a1, r1) in zip(_COAST[:-1], _COAST[1:]):
        m = (t >= a0) & (t <= a1)
        u = (t[m] - a0) / (a1 - a0)
        u = (1 - np.cos(u * np.pi)) / 2
        out[m] = r0 + (r1 - r0) * u
    return out


def polyline_field(X, Z, pts, maxd):
    """Distance to a polyline and arc-length position of the nearest point (inf / 0 beyond maxd)."""
    dist = np.full(X.shape, np.inf, np.float32)
    pos = np.zeros(X.shape, np.float32)
    acc = 0.0
    x0g, z0g = X[0, 0], Z[0, 0]
    for (xa, za), (xb, zb) in zip(pts[:-1], pts[1:]):
        L = math.hypot(xb - xa, zb - za)
        lo_x = int(max(min(xa, xb) - maxd - x0g, 0))
        hi_x = int(min(max(xa, xb) + maxd - x0g + 1, X.shape[0]))
        lo_z = int(max(min(za, zb) - maxd - z0g, 0))
        hi_z = int(min(max(za, zb) + maxd - z0g + 1, X.shape[1]))
        if lo_x < hi_x and lo_z < hi_z and L > 0:
            xs = X[lo_x:hi_x, lo_z:hi_z]
            zs = Z[lo_x:hi_x, lo_z:hi_z]
            t = np.clip(((xs - xa) * (xb - xa) + (zs - za) * (zb - za)) / (L * L), 0, 1)
            d = np.hypot(xs - (xa + t * (xb - xa)), zs - (za + t * (zb - za)))
            cur = dist[lo_x:hi_x, lo_z:hi_z]
            m = d < cur
            cur[m] = d[m]
            pos[lo_x:hi_x, lo_z:hi_z][m] = (acc + t * L)[m]
        acc += L
    return dist, pos


ROADS = {
    # name: (points, half width)
    "north": ([(0, -TOWN_R - 2), (0, -118), (0, -150), (0, -214)], 2.6),
    "east": ([(TOWN_R + 2, 0), (120, 2), (165, 20), (205, 50), (238, 72)], 2.6),
    "south": ([(0, TOWN_R + 2), (0, 112), (0, 146)], 2.6),
    "west": ([(-TOWN_R - 2, 0), (-97, 0), (-117, 0)], 2.6),
    "mine": ([(112, 2), (135, -50), (160, -110), (182, -158), (192, -176)], 2.0),
    "hell": ([(0, 100), (-40, 118), (-95, 140), (-150, 185), (-190, 214), (-214, 228)], 2.0),
    "forest": ([(0, -106), (-60, -112), (-110, -140), (-150, -165)], 1.6),
}
RIVER = [(170, -236), (128, -205), (84, -178), (40, -156), (0, -140), (-45, -146), (-95, -172), (-150, -196),
         (-205, -215), (-262, -252), (-330, -300), (-420, -360)]
LAKE = (-168, -196, 30)


class Terrain:
    pass


def build_heightmap(seed=7):
    rng = np.random.default_rng(seed)
    sx, sz = OX1 - OX0, OZ1 - OZ0
    X, Z = np.meshgrid(np.arange(OX0, OX1, dtype=np.float32), np.arange(OZ0, OZ1, dtype=np.float32), indexing="ij")
    n_low = fbm(sx, sz, 128, rng, 3) * 2 - 1
    n_mid = fbm(sx, sz, 48, rng, 4) * 2 - 1
    n_hi = fbm(sx, sz, 12, rng, 3) * 2 - 1
    n_det = fbm(sx, sz, 5, rng, 2) * 2 - 1
    n_b1 = fbm(sx, sz, 80, rng, 3) * 2 - 1
    n_b2 = fbm(sx, sz, 80, rng, 3) * 2 - 1

    r = np.hypot(X, Z)
    theta = np.degrees(np.arctan2(Z, X))
    R = coast_radius(theta) + n_low * 22 + n_mid * 9
    land = (R - r) / 60.0                      # >0 inland, 1 = 60 blocks from the shore

    # --- base elevations ----------------------------------------------------
    base = 67.5 + n_mid * 2.6 + n_hi * 1.1 + n_low * 1.5
    # mountains (north east)
    mx, mz = MOUNTAIN
    md = np.hypot((X - mx) / 150.0, (Z - mz) / 135.0)
    mmask = smooth(1.22 - (md + n_b2 * 0.16) * 1.22)
    ridge = 1 - np.abs(fbm(sx, sz, 56, rng, 4) * 2 - 1)
    ridge2 = 1 - np.abs(fbm(sx, sz, 24, rng, 3) * 2 - 1)
    peaks = mmask ** 2.1 * (34 + ridge * 44 + ridge2 * 12 + n_hi * 5) + mmask * 9
    base = base + peaks
    # desert dunes (east)
    dd = np.hypot((X - 330) / 185.0, (Z - 75) / 215.0)
    desert = smooth((1.0 - dd + n_b1 * 0.2 + n_mid * 0.08) * 4.0) * (1 - smooth(mmask * 3.0))
    dune = np.abs(np.sin((X * 0.045 + Z * 0.02) + n_mid * 2.2)) * 5.0 + n_hi * 1.0
    base = base + desert * (dune - 1.5)
    # forest hills (north west)
    fd = np.hypot((X + 285) / 215.0, (Z + 285) / 200.0)
    forest = smooth((1.0 - fd + n_b1 * 0.22 + n_mid * 0.06) * 4.0)
    base = base + forest * (n_mid * 4.0 + 2.0)
    # volcano (south west)
    hx, hz = HELLGATE
    vd = np.hypot(X - hx, Z - hz) + n_hi * 3
    cone = 30 * np.exp(-((vd - 40) / 22.0) ** 2) + 9 * np.exp(-(vd / 85.0) ** 2)
    crater = smooth((34 - vd) / 10.0)
    volcano = smooth((95 - vd) / 30.0)
    # notch in the rim toward the town (north east) for the road
    ang = np.degrees(np.arctan2(Z - hz, X - hx))
    notch = np.exp(-(((ang + 32 + 180) % 360 - 180) / 13.0) ** 2)
    base = base + cone * (1 - 0.93 * notch)
    base = base * (1 - crater) + (HELL_G + 0.3) * crater
    base = np.where((notch > 0.5) & (vd < 62), np.minimum(base, HELL_G + 0.3 + np.maximum(vd - 46, 0) * -0.25), base)

    # --- coast + ocean floor --------------------------------------------------
    shore = smooth(land * 1.6)                 # 0 at shoreline -> 1 inland
    beach_h = SEA + 0.4 + shore * 3.0
    h = np.where(land > 0, beach_h + (base - beach_h) * smooth(land * 1.2 - 0.05), 0)
    depth = np.clip(-land, 0, None)
    sea_floor = SEA - 2 - smooth(depth * 0.9) * 18 + n_hi * 1.2 * smooth(depth * 3)
    h = np.where(land > 0, h, sea_floor)

    def flatten(mask_dist, target, inner, blend):
        nonlocal h
        t = smooth((mask_dist - inner) / blend)   # 0 inside, 1 outside
        h = h * t + target * (1 - t)

    # --- flatten build sites --------------------------------------------------
    d_town = np.maximum(np.abs(X), np.abs(Z))
    flatten(d_town, G + 0.3, TOWN_R + 8, 26)
    px0, pz0 = PLOT_X0, PLOT_Z0
    px1 = px0 + PLOT_COLS * PLOT_SIZE + (PLOT_COLS + 1) * PLOT_ROAD
    pz1 = pz0 + PLOT_ROWS * PLOT_SIZE + (PLOT_ROWS + 1) * PLOT_ROAD
    d_plot = np.maximum(np.maximum(px0 - X, X - px1), np.maximum(pz0 - Z, Z - pz1))
    flatten(d_plot, G + 0.3, 6, 22)
    flatten(np.hypot(X - KEEP[0], Z - KEEP[1]), KEEP_G + 0.3, 52, 26)
    d_pyr = np.maximum(np.abs(X - PYRAMID[0]), np.abs(Z - PYRAMID[1]))
    flatten(d_pyr, PYR_G + 0.3, 56, 28)
    flatten(np.hypot(X - MINE[0], Z - MINE[1]), MINE_G + 0.3, 11, 12)
    flatten(np.hypot(X - HARBOR[0], Z - HARBOR[1] + 14), SEA + 2.3, 16, 18)

    # deep basin for the sunken temple
    td = np.hypot((X - TEMPLE[0]) / 1.25, Z - TEMPLE[1])
    basin = smooth((112 - td) / 55.0)
    h = np.where(land <= 0, h * (1 - basin) + (24 + n_hi * 1.5) * basin, h)
    # sea floor must meet the surrounding flat ocean (sand top y=42) at the region border
    edge = np.minimum(np.minimum(X - OX0, OX1 - 1 - X), np.minimum(Z - OZ0, OZ1 - 1 - Z))
    e = smooth(edge / 20.0)
    h = np.where(land <= 0, h * e + 42.0 * (1 - e), h)

    # --- river + lake ---------------------------------------------------------
    rd, _ = polyline_field(X, Z, RIVER, 40)
    rd = rd + n_det * 1.5
    lake_d = np.hypot(X - LAKE[0], Z - LAKE[1]) - LAKE[2] - n_hi * 4
    wd = np.minimum(rd - 4.5, lake_d)          # <0 inside water
    inland = land > 0.05
    bank = smooth(wd / 16.0)
    hb = np.minimum(h, 63.2 + bank * 60)
    h = np.where(inland & (wd < 16), h * bank + np.minimum(h, 63.3) * (1 - bank), h)
    h = np.where(inland & (wd < 16), np.minimum(h, hb), h)
    bed = 56.0 + np.clip(wd + 4.5, 0, 4.5) * 1.1 + n_det * 0.6
    lake_bed = 52.0 + np.clip(-lake_d, 0, 12) * -0.25 + n_det
    is_river = inland & (rd < 4.5) & (h > 30)
    is_lake = inland & (lake_d < 0)
    h = np.where(is_river, np.minimum(h, bed), h)
    h = np.where(is_lake, np.minimum(h, np.where(lake_d > -5, 60.5 + lake_d * 1.5, lake_bed)), h)

    # --- roads ----------------------------------------------------------------
    road = np.zeros((sx, sz), bool)
    road_edge = np.zeros((sx, sz), bool)
    for name, (pts, hw) in ROADS.items():
        d, pos = polyline_field(X, Z, pts, hw + 9)
        # smoothed height profile along the road
        total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts[:-1], pts[1:]))
        ns = int(total) + 1
        prof = np.zeros(ns, np.float32)
        acc = 0.0
        k = 0
        for (xa, za), (xb, zb) in zip(pts[:-1], pts[1:]):
            L = math.hypot(xb - xa, zb - za)
            while k < ns and k <= acc + L:
                t = (k - acc) / L
                xi = int(round(xa + (xb - xa) * t)) - OX0
                zi = int(round(za + (zb - za) * t)) - OZ0
                prof[k] = max(h[xi, zi], SEA + 1.4)
                k += 1
            acc += L
        ker = np.ones(21, np.float32) / 21
        prof = np.convolve(np.pad(prof, 10, mode="edge"), ker, mode="valid")
        target = prof[np.clip(pos.astype(int), 0, ns - 1)]
        over_water = (wd < 2) & inland
        core = (d <= hw) & ~over_water & (land > 0.02)
        t = smooth((d - hw) / 7.0)
        blend = (d < hw + 7) & ~over_water & (land > 0.02)
        h = np.where(blend, h * t + target * (1 - t), h)
        road |= core
        road_edge |= (d <= hw + 1.2) & ~core & ~over_water & (land > 0.02)

    T = Terrain()
    T.X, T.Z = X, Z
    T.h = np.round(h).astype(np.int32)
    T.land, T.desert, T.forest, T.mmask, T.volcano, T.vd = land, desert, forest, mmask, volcano, vd
    T.road, T.road_edge = road, road_edge
    T.river = is_river | is_lake
    T.wd = wd
    T.n_hi, T.n_mid, T.n_det, T.n_low = n_hi, n_mid, n_det, n_low
    T.rng = rng
    T.reserved = np.zeros((sx, sz), bool)
    return T


def voxelize(w, T, log=print):
    """Fill the world volume from the heightmap."""
    rng = w.rng
    sx, sz = w.sx, w.sz
    h = T.h
    hi = h - w.y0                                # top index
    stone, deep = B("stone"), B("deepslate")
    Yidx = np.arange(w.sy, dtype=np.int32)[None, None, :]
    yy = Yidx + w.y0
    log("  stone fill")
    for xa in range(0, sx, 64):
        sl = slice(xa, xa + 64)
        H = hi[sl][:, :, None]
        blk = np.where(Yidx <= H, np.where(yy < 0, deep, stone), 0).astype(np.uint16)
        blk[:, :, 0] = B("bedrock")
        blk[(Yidx > H) & (yy <= SEA)] = bl.WATER
        w.b[sl] = blk
    # --- surface classification ---------------------------------------------------
    slope = np.zeros_like(h)
    slope[1:-1, 1:-1] = np.maximum(np.abs(h[2:, 1:-1] - h[:-2, 1:-1]), np.abs(h[1:-1, 2:] - h[1:-1, :-2]))
    under = h < SEA
    beach = (~under) & (h <= SEA + 2) & (T.land < 0.22) & (T.volcano < 0.3)
    desert = (T.desert > 0.5) & ~under
    mount = (T.mmask > 0.16) & ~under & (h > 78)
    rock = mount & ((slope >= 3) | (h > 100 + T.n_mid * 10) | (T.n_hi > 0.4))
    snow = mount & (h > 132 + T.n_hi * 9 - slope * 1.5)
    volc = (T.volcano > 0.45) & ~under
    kind = np.zeros((sx, sz), np.uint8)          # 0 sea floor
    kind[~under] = 1                             # grass
    kind[(T.forest > 0.5) & ~under] = 8
    kind[desert] = 2
    kind[mount & ~rock] = 1
    kind[rock] = 3
    kind[snow] = 4
    kind[beach] = 5
    kind[volc] = 6
    kind[T.river & under] = 9
    kind[T.road] = 7
    T.kind = kind
    ix_all, iz_all = np.meshgrid(np.arange(sx), np.arange(sz), indexing="ij")

    def layers(mask, specs):
        ix, iz = ix_all[mask], iz_all[mask]
        if len(ix) == 0:
            return
        top = hi[ix, iz]
        for k, blk in enumerate(specs):
            if blk is None:
                continue
            yk = top - k
            ok = yk >= 1
            v = blk.sample(rng, int(ok.sum())) if isinstance(blk, Mix) else blk
            w.b[ix[ok], iz[ok], yk[ok]] = v

    dirt = B("dirt")
    grass = B("grass_block")
    sand = B("sand")
    sandstone = bl.block("sandstone")
    log("  surface layers")
    layers(kind == 1, [grass, dirt, dirt, dirt])
    layers(kind == 8, [Mix((grass, 8), (B("podzol"), 2), (B("dirt", dirt_type="coarse"), 1), (B("moss_block"), 1)),
                       dirt, dirt, dirt])
    layers(kind == 2, [sand, sand, sand, sand, sandstone, sandstone, sandstone])
    layers(kind == 5, [sand, sand, sand, sandstone, sandstone])
    layers(kind == 3, [Mix((stone, 10), (B("andesite"), 5), (B("cobblestone"), 2), (B("gravel"), 2), (B("tuff"), 2)),
                       Mix((stone, 6), (B("andesite"), 2))])
    layers(kind == 4, [B("snow"), B("snow"), Mix((stone, 5), (B("packed_ice"), 1))])
    layers(kind == 6, [Mix((B("basalt"), 5), (B("smooth_basalt"), 6), (B("blackstone"), 6), (B("tuff"), 3),
                           (B("magma"), 1), (B("cobbled_deepslate"), 2)),
                       Mix((B("blackstone"), 3), (B("basalt"), 2)), B("blackstone"), B("blackstone")])
    deepsea = under & (h < 46)
    layers(under & ~deepsea & (kind == 0), [Mix((sand, 9), (B("gravel"), 2), (B("clay"), 1)), sand, sand, sandstone])
    layers(deepsea & (kind == 0), [Mix((B("gravel"), 6), (sand, 4), (stone, 1), (B("clay"), 1)), B("gravel"), stone])
    layers(kind == 9, [Mix((B("gravel"), 4), (sand, 3), (B("clay"), 2), (dirt, 2)), dirt, dirt])
    # mossy / rocky transition bands on mountain meadows
    alp = (kind == 1) & (T.mmask > 0.16) & (T.n_det > 0.25)
    layers(alp, [Mix((grass, 3), (stone, 2), (B("gravel"), 1), (B("moss_block"), 1), (B("cobblestone"), 1))])
    # roads
    plain_road = Mix((B("grass_path"), 8), (B("gravel"), 3), (B("cobblestone"), 3), (B("dirt", dirt_type="coarse"), 2),
                     (bl.block("mossy_cobblestone"), 1), (B("andesite"), 1))
    desert_road = Mix((bl.block("smooth_sandstone"), 5), (sandstone, 4), (bl.block("cut_sandstone"), 3), (sand, 1))
    rock_road = Mix((B("cobblestone"), 5), (B("gravel"), 4), (B("andesite"), 3), (B("grass_path"), 1))
    volc_road = Mix((B("polished_blackstone_bricks"), 5), (B("blackstone"), 3), (B("cracked_polished_blackstone_bricks"), 2),
                    (B("gilded_blackstone"), 0.3))
    layers((kind == 7) & (T.desert <= 0.5) & (T.volcano <= 0.45) & (T.mmask <= 0.3), [plain_road, dirt, dirt])
    layers((kind == 7) & (T.desert > 0.5), [desert_road, sandstone, sandstone])
    layers((kind == 7) & (T.mmask > 0.3), [rock_road, stone])
    layers((kind == 7) & (T.volcano > 0.45), [volc_road, B("blackstone")])
    # road shoulders
    sh = T.road_edge & (kind == 1) & (rng.random((sx, sz)) < 0.45)
    layers(sh, [Mix((B("dirt", dirt_type="coarse"), 3), (B("gravel"), 2), (B("grass_path"), 1), (B("cobblestone"), 1))])
    # lava in the crater floor cracks + volcano glow
    crack = (kind == 6) & (T.vd < 30) & (T.n_det > 0.42)
    layers(crack, [B("magma")])

    # --- biomes ---------------------------------------------------------------
    bio = np.full((sx, sz), BIO_PLAINS, np.uint8)
    bio[(T.forest > 0.5)] = BIO_FOREST
    bio[T.desert > 0.5] = BIO_DESERT
    bio[T.mmask > 0.2] = BIO_HILLS
    bio[T.volcano > 0.45] = BIO_STONY
    bio[beach] = BIO_BEACH
    bio[T.land <= 0] = BIO_OCEAN
    bio[(T.land <= 0) & (h < 44)] = BIO_DEEP
    bio[T.river] = BIO_RIVER
    w.biome[:, :] = bio
    return kind


def ores(w, T, log=print):
    """Scatter ore veins under the land so the plots district supports real mining."""
    rng = w.rng
    stone, deep = B("stone"), B("deepslate")
    land_ix = np.argwhere(T.land > 0.05)
    spec = [  # name, deepslate name, veins, ymin, ymax, size
        ("coal_ore", "deepslate_coal_ore", 26000, 5, 110, 6),
        ("iron_ore", "deepslate_iron_ore", 20000, -24, 70, 5),
        ("copper_ore", "deepslate_copper_ore", 12000, 0, 80, 6),
        ("gold_ore", "deepslate_gold_ore", 5000, -30, 30, 5),
        ("redstone_ore", "deepslate_redstone_ore", 5000, -32, 12, 5),
        ("lapis_ore", "deepslate_lapis_ore", 3000, -30, 30, 4),
        ("diamond_ore", "deepslate_diamond_ore", 2600, -32, 8, 4),
        ("emerald_ore", "deepslate_emerald_ore", 1500, 20, 120, 2),
    ]
    for name, dname, n, ymin, ymax, size in spec:
        idx = land_ix[rng.integers(0, len(land_ix), n)]
        x = idx[:, 0].copy()
        z = idx[:, 1].copy()
        y = rng.integers(ymin, ymax + 1, n) - w.y0
        o1, o2 = B(name), B(dname)
        for _ in range(size):
            ok = (x >= 0) & (x < w.sx) & (z >= 0) & (z < w.sz) & (y > 0) & (y < w.sy)
            xs, zs, ys = x[ok], z[ok], y[ok]
            cur = w.b[xs, zs, ys]
            m1 = cur == stone
            m2 = cur == deep
            w.b[xs[m1], zs[m1], ys[m1]] = o1
            w.b[xs[m2], zs[m2], ys[m2]] = o2
            x = x + rng.integers(-1, 2, n)
            z = z + rng.integers(-1, 2, n)
            y = y + rng.integers(-1, 2, n)
    # deepslate / stone blending and a few mineral pockets
    for name, n in (("andesite", 5000), ("diorite", 4000), ("granite", 4000), ("gravel", 2500), ("tuff", 3000)):
        idx = land_ix[rng.integers(0, len(land_ix), n)]
        blk = B(name)
        for (x, z) in idx[: n // 4]:
            y = int(rng.integers(-20, 60))
            w.ellipsoid(x + w.x0, y, z + w.z0, rng.integers(2, 5), rng.integers(1, 4), rng.integers(2, 5), blk,
                        only=(stone, deep))


def vegetation(w, T, log=print):
    """Trees, grass, flowers, cacti, kelp ... everywhere outside reserved build sites."""
    rng = w.rng
    h, kind = T.h, T.kind
    sx, sz = w.sx, w.sz
    res = T.reserved | T.road
    # keep a margin around reserved areas free of trees
    from numpy.lib.stride_tricks import sliding_window_view  # noqa: F401
    near = res.copy()
    for s in (1, 2, 3):
        near[s:, :] |= res[:-s, :]
        near[:-s, :] |= res[s:, :]
        near[:, s:] |= res[:, :-s]
        near[:, :-s] |= res[:, s:]
    grass_b = B("grass_block")

    def top_is(x, z, ids):
        return w.b[x, z, h[x, z] - w.y0] in ids and w.b[x, z, h[x, z] + 1 - w.y0] == 0

    log("  trees")
    n_try = 26000
    xs = rng.integers(6, sx - 6, n_try)
    zs = rng.integers(6, sz - 6, n_try)
    placed = np.zeros((sx, sz), bool)
    soil = {grass_b, B("podzol"), B("moss_block"), B("dirt", dirt_type="coarse")}
    for x, z in zip(xs, zs):
        if near[x, z] or kind[x, z] not in (1, 8):
            continue
        dens = 0.05 + 0.9 * (T.forest[x, z] > 0.5) + 0.25 * (T.mmask[x, z] > 0.16) + 0.06 * (T.n_mid[x, z] > 0.3)
        if rng.random() > dens:
            continue
        if placed[max(0, x - 3):x + 4, max(0, z - 3):z + 4].any():
            continue
        if not top_is(x, z, soil):
            continue
        wx, wz, y = x + w.x0, z + w.z0, int(h[x, z]) + 1
        r = rng.random()
        if T.mmask[x, z] > 0.16:
            kit.tree_spruce(w, wx, y, wz, rng)
        elif T.forest[x, z] > 0.5:
            if r < 0.45:
                kit.tree_oak(w, wx, y, wz, rng)
            elif r < 0.7:
                kit.tree_birch(w, wx, y, wz, rng)
            elif r < 0.85:
                kit.tree_big(w, wx, y, wz, rng)
            elif r < 0.95:
                kit.tree_spruce(w, wx, y, wz, rng)
            else:
                kit.tree_big(w, wx, y, wz, rng, wood="dark_oak", spread=4)
        else:
            if r < 0.6:
                kit.tree_oak(w, wx, y, wz, rng)
            elif r < 0.85:
                kit.tree_birch(w, wx, y, wz, rng)
            else:
                kit.tree_big(w, wx, y, wz, rng, h=int(rng.integers(8, 11)))
        placed[x, z] = True
    # desert: cacti, dead bushes, palms near the oasis handled by the desert module
    log("  ground cover")
    rnd = rng.random((sx, sz))
    air_above = np.take_along_axis(w.b, np.clip(h - w.y0 + 1, 0, w.sy - 1)[:, :, None], axis=2)[:, :, 0] == 0
    topb = np.take_along_axis(w.b, np.clip(h - w.y0, 0, w.sy - 1)[:, :, None], axis=2)[:, :, 0]
    ok = air_above & ~res
    ix_all, iz_all = np.meshgrid(np.arange(sx), np.arange(sz), indexing="ij")

    def place(mask, blk, dy=1):
        ix, iz = ix_all[mask], iz_all[mask]
        if len(ix):
            v = blk.sample(rng, len(ix)) if isinstance(blk, Mix) else blk
            w.b[ix, iz, h[ix, iz] - w.y0 + dy] = v

    is_grass = (topb == grass_b) & ok
    place(is_grass & (rnd < 0.22), B("short_grass"))
    place(is_grass & (rnd >= 0.22) & (rnd < 0.245), B("fern"))
    fl = Mix(B("poppy"), B("yellow_flower"), B("azure_bluet"), B("oxeye_daisy"), B("cornflower"), B("allium"),
             B("red_tulip"), B("white_tulip"), B("pink_tulip"), B("orange_tulip"), B("lily_of_the_valley"))
    meadow = is_grass & (T.n_hi > 0.2) & (rnd >= 0.25) & (rnd < 0.33)
    place(meadow, fl)
    place(is_grass & (rnd >= 0.33) & (rnd < 0.337), fl)
    tall = is_grass & (rnd >= 0.34) & (rnd < 0.365) & (h < w.y1 - 4)
    place(tall, B("tall_grass", upper_block_bit=False))
    place(tall, B("tall_grass", upper_block_bit=True), dy=2)
    # desert
    is_sand = (topb == B("sand")) & ok & (kind == 2)
    place(is_sand & (rnd < 0.006), B("deadbush"))
    cact = is_sand & (rnd >= 0.006) & (rnd < 0.0095)
    for x, z in zip(ix_all[cact], iz_all[cact]):
        if all(w.b[x + dx, z + dz, h[x, z] - w.y0 + 1] == 0 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if 0 <= x + dx < sx and 0 <= z + dz < sz):
            for i in range(int(rng.integers(1, 4))):
                w.b[x, z, h[x, z] - w.y0 + 1 + i] = B("cactus")
    # snow line + rocks
    is_rock = (kind == 3) & ok
    place(is_rock & (h > 112) & (rnd < 0.25), B("snow_layer", height=0, covered_bit=False))
    # volcanic
    is_volc = (kind == 6) & ok
    place(is_volc & (rnd < 0.004), B("deadbush"))
    # beach
    is_beach = (kind == 5) & ok
    place(is_beach & (rnd < 0.004), B("deadbush"))
    # underwater: seagrass, kelp, corals handled by the ocean module
    log("  seabed plants")
    sea = (kind == 0) & (h < SEA - 2) & (h > 30) & ~res
    sg = sea & (rnd < 0.10)
    ix, iz = ix_all[sg], iz_all[sg]
    w.b[ix, iz, h[ix, iz] - w.y0 + 1] = B("seagrass", sea_grass_type="default")
    w.wl[ix, iz, h[ix, iz] - w.y0 + 1] = True
    kp = sea & (rnd >= 0.10) & (rnd < 0.125) & (h < SEA - 6)
    for x, z in zip(ix_all[kp], iz_all[kp]):
        top = h[x, z] - w.y0
        n = int(rng.integers(2, max(3, min(12, SEA - h[x, z] - 2))))
        for i in range(1, n + 1):
            w.b[x, z, top + i] = B("kelp", kelp_age=int(rng.integers(0, 15)) if i < n else 15)
            w.wl[x, z, top + i] = True
    # river reeds + lily pads
    rv = T.river & (h < SEA) & ~res
    lily = rv & (rnd < 0.02)
    ix, iz = ix_all[lily], iz_all[lily]
    w.b[ix, iz, SEA + 1 - w.y0] = B("waterlily")
    bank = (topb == grass_b) & ok & (T.wd < 3) & (T.wd > 0) & (rnd < 0.25) & (h <= SEA + 1)
    for x, z in zip(ix_all[bank], iz_all[bank]):
        for i in range(1, int(rng.integers(2, 4))):
            w.b[x, z, h[x, z] - w.y0 + i] = B("reeds", age=0)
