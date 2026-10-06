"""World-wide walk from the hub spawn over every island and bridge.

* trapped : positions you can reach but never leave (falling into the void is not a way you can walk, so a
            pit with no way up counts as a trap even on an island edge) -> must be 0
* falls   : walking off an edge that drops >= 4 blocks onto solid ground (fall damage is on)
* missing : arrivals, shop NPCs, plot entries, furnace rooms, enchanting tables, ender chests, return pads
            and generators the walk does not reach
Plot interiors are closed by the ring wall + border blocks and are not part of the walk.
"""
import collections
import contextlib
import math

import numpy as np

import mcw
import trapcheck
from sky_world import X0, Z0, SX, SZ


@contextlib.contextmanager
def physics_patch():
    """Fence gates count as open; cave vines / hanging roots under islands are not climbable here
    (a player dropping off an island is dead anyway)."""
    orig = mcw.physics

    def patched(idx):
        name = mcw.PAL.entries[idx][0]
        if name.endswith("fence_gate") or name == "fence_gate":
            return 0, False, False
        if name.startswith("cave_vines") or name in ("hanging_roots", "glow_lichen"):
            return 0, False, False
        return orig(idx)

    mcw.physics = patched
    try:
        yield
    finally:
        mcw.physics = orig


def walk(W, y_range=(50, 124)):
    a = W.a
    sx, sy, sz, _ = W.arrivals["hub"]
    seeds = [(int(math.floor(sx)), int(sy), int(math.floor(sz)))]
    with physics_patch():
        rep = trapcheck.analyze(a, (X0 + 1, Z0 + 1, X0 + SX - 2, Z0 + SZ - 2), y_range, seeds, inside=None,
                                track_falls=True)
    ox, oy, oz = rep["offset"]
    rep["positions"] = [(p[0] + ox, p[1] + oy, p[2] + oz) for p in rep["fwd"]]
    rep["_set"] = set(rep["positions"])
    return rep


def reached(rep, target, r=2, dy=2):
    S = rep["_set"]
    x, y, z = (int(math.floor(v)) for v in target[:3])
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            for yy in range(y - dy, y + dy + 1):
                if (x + dx, yy, z + dz) in S:
                    return True
    return False


def can_mine(rep, g, reach=4.5):
    S = rep["_set"]
    x, y, z = g
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            for dy in range(-5, 3):
                p = (x + dx, y + dy, z + dz)
                if p in S:
                    ex, ey, ez = p[0] + 0.5, p[1] + 1.62, p[2] + 0.5
                    if math.dist((ex, ey, ez), (x + 0.5, y + 0.5, z + 0.5)) <= reach:
                        return True
    return False


def coverage(W, rep):
    missing = []
    for k, v in W.arrivals.items():
        if not reached(rep, v, r=1, dy=1):
            missing.append(("arrival", k, v))
    for n in W.npcs:
        if n.get("kind") in ("shop", "guide", "plots") and not reached(rep, (n["x"], n["y"], n["z"]), r=3, dy=2):
            missing.append(("npc", n["name"], (n["x"], n["y"], n["z"])))
    for p in W.plots:
        if not reached(rep, p["outside"], r=1, dy=1):
            missing.append(("plot entry", p["id"], p["outside"]))
    for r in W.furnace_rooms:
        x1, y1, z1, x2, y2, z2 = r["box"]
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        if not reached(rep, (cx, y1, cz), r=2, dy=0):
            missing.append(("furnace room", r["id"], (cx, y1, cz)))
        if not reached(rep, r["out"], r=1, dy=0):
            missing.append(("furnace room door", r["id"], r["out"]))
    for e in W.enchant_tables:
        if not reached(rep, e, r=3, dy=1):
            missing.append(("enchanting table", e))
    for e in W.ender_chests:
        if not reached(rep, e, r=2, dy=1):
            missing.append(("ender chest", e))
    for p in W.portals:
        x1, y1, z1, x2, y2, z2 = p["box"]
        if not reached(rep, ((x1 + x2) // 2, y1, (z1 + z2) // 2), r=1, dy=0):
            missing.append(("portal", p["dest"], p["box"]))
    bad = [g for g in W.generators if not can_mine(rep, (g["x"], g["y"], g["z"]))]
    for g in bad[:20]:
        missing.append(("generator", g["kind"], (g["x"], g["y"], g["z"])))
    return missing, len(bad)


def summarize_falls(falls):
    land = collections.Counter()
    ex = {}
    for p, q, d in falls:
        key = (q[0] // 4 * 4, q[2] // 4 * 4)
        land[key] += 1
        ex.setdefault(key, (p, q, d))
    return land, ex


def liquid_leaks(W):
    a = W.a
    liq = np.array([i for i, (n, _s) in enumerate(mcw.PAL.entries) if n in ("water", "flowing_water", "lava", "flowing_lava")])
    L = np.isin(a.blk, liq) | a.wet
    air = a.blk == 0
    n = 0
    n += int((L[1:, :, :] & air[:-1, :, :]).sum() + (L[:-1, :, :] & air[1:, :, :]).sum())
    n += int((L[:, :, 1:] & air[:, :, :-1]).sum() + (L[:, :, :-1] & air[:, :, 1:]).sum())
    n += int((L[:, 1:, :] & air[:, :-1, :]).sum())
    return n
