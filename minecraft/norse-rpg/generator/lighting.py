"""Approximate block-light simulation, used to check that areas are lit (but moody)."""
import numpy as np

from mcw import PAL, physics

EMIT = {
    "lantern": 15, "soul_lantern": 10, "torch": 14, "soul_torch": 10, "redstone_torch": 7,
    "sea_lantern": 15, "glowstone": 15, "shroomlight": 15, "ochre_froglight": 15, "verdant_froglight": 15,
    "pearlescent_froglight": 15, "beacon": 15, "end_rod": 14, "campfire": 15, "soul_campfire": 10,
    "lava": 15, "flowing_lava": 15, "fire": 15, "soul_fire": 10, "magma": 3, "crying_obsidian": 10,
    "glow_lichen": 7, "amethyst_cluster": 5, "lit_furnace": 13, "lit_blast_furnace": 13, "lit_smoker": 13,
    "lit_redstone_lamp": 15, "lit_pumpkin": 15, "brewing_stand": 1, "enchanting_table": 7, "conduit": 15,
    "cave_vines_body_with_berries": 14, "cave_vines_head_with_berries": 14, "glowingobsidian": 12,
    "underwater_torch": 14, "colored_torch_red": 14, "colored_torch_blue": 14, "colored_torch_green": 14,
    "colored_torch_purple": 14, "light_block_15": 15, "light_block_14": 14, "light_block_13": 13,
    "light_block_12": 12, "light_block_11": 11, "light_block_10": 10, "light_block_9": 9, "light_block_8": 8,
}
for _n in range(16):
    EMIT["light_block_%d" % _n] = _n
TRANSPARENT_FULL = ("glass", "leaves", "ice", "slime", "honey_block", "beacon", "barrier", "scaffolding",
                    "mob_spawner", "light_block", "sea_lantern", "glowstone", "web", "bamboo")


def tables():
    n = len(PAL.entries)
    emit = np.zeros(n, np.int8)
    trans = np.zeros(n, bool)
    for i, (name, st) in enumerate(PAL.entries):
        e = EMIT.get(name, 0)
        if name.endswith("copper_bulb") and st.get("lit", (0, 0))[1]:
            e = 15
        if name == "sea_pickle":
            e = 3 + 3 * (st.get("cluster_count", (0, 0))[1] + 1)
        if name.endswith("candle") and st.get("lit", (0, 0))[1]:
            e = 3 * (st.get("candles", (0, 0))[1] + 1)
        if name == "tinted_glass":
            trans[i] = False
        else:
            h, liq, _ = physics(i)
            trans[i] = h != 2 or any(k in name for k in TRANSPARENT_FULL) or name.endswith(("_slab", "_stairs"))
        emit[i] = e
    return emit, trans


def block_light(blk):
    emit_t, trans_t = tables()
    E = emit_t[blk].astype(np.int8)
    T = trans_t[blk]
    L = E.copy()
    for _ in range(15):
        m = np.zeros_like(L)
        m[1:] = np.maximum(m[1:], L[:-1]); m[:-1] = np.maximum(m[:-1], L[1:])
        m[:, 1:] = np.maximum(m[:, 1:], L[:, :-1]); m[:, :-1] = np.maximum(m[:, :-1], L[:, 1:])
        m[:, :, 1:] = np.maximum(m[:, :, 1:], L[:, :, :-1]); m[:, :, :-1] = np.maximum(m[:, :, :-1], L[:, :, 1:])
        nl = np.where(T, np.maximum(m - 1, 0), 0).astype(np.int8)
        nl = np.maximum(nl, E)
        if np.array_equal(nl, L):
            break
        L = nl
    return L


def floor_light_stats(area, x1, z1, x2, z2, ymin, ymax, mask_fn=None):
    """Light at the feet of every standable spot inside the box."""
    from mcw import physics_tables
    h, liq, _ = physics_tables()
    sl = (slice(x1 - area.x0, x2 - area.x0 + 1), slice(ymin - area.y0 - 1, ymax - area.y0 + 2),
          slice(z1 - area.z0, z2 - area.z0 + 1))
    blk = area.blk[sl]
    L = block_light(blk)
    H = h[blk]
    stand = (H[:, :-2, :] == 2) & (H[:, 1:-1, :] == 0) & (H[:, 2:, :] == 0) & ~liq[blk[:, 1:-1, :]]
    vals = L[:, 1:-1, :][stand]
    pos = np.argwhere(stand)
    return vals, pos, L


def fill_dark(area, box, yrange, threshold=5, level=8, height=4, spacing=5, rounds=4, avoid_col=None, skip=None):
    """Add invisible light blocks above dark standable spots (soft fill light)."""
    from mcw import B
    x1, z1, x2, z2 = box
    lb = B("light_block_%d" % level)
    added = 0
    for _ in range(rounds):
        vals, pos, L = floor_light_stats(area, x1, z1, x2, z2, yrange[0], yrange[1])
        dark = pos[vals < threshold]
        if len(dark) == 0:
            break
        taken = set()
        for (px, py, pz) in dark:
            x, z = px + x1, pz + z1
            y = py + yrange[0]    # feet y of the dark spot
            key = (x // spacing, z // spacing)
            if key in taken:
                continue
            if avoid_col is not None and (x, z) == avoid_col:
                continue
            if skip is not None and skip(x, z):
                continue
            for hy in range(height, 0, -1):
                if area.get(x, y + hy, z) == 0 and all(area.get(x, y + k, z) == 0 for k in range(1, hy)):
                    area.set(x, y + hy, z, lb)
                    taken.add(key)
                    added += 1
                    break
    return added
