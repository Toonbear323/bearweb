"""World-wide checks for the RPG map: one walk from the spawn over every connected region.

* trapped  : positions you can reach but never leave again (must be 0)
* escaped  : positions outside the playable volumes - climbing a mountain, leaving a building (must be 0)
* falls    : walking off an edge that drops >= 4 blocks onto solid ground (fall damage is on in an RPG)
* missing  : region arrival points, shop counters, hunting grounds or boss arenas the walk did not reach
Fence gates count as open (players open them, mobs cannot).
"""
import collections
import contextlib

import numpy as np

import mcw
import trapcheck
from rpg_world import X0, Z0, SX, SZ


@contextlib.contextmanager
def gates_open():
    orig = mcw.physics

    def patched(idx):
        name = mcw.PAL.entries[idx][0]
        if name.endswith("fence_gate") or name == "fence_gate":
            return 0, False, False
        return orig(idx)

    mcw.physics = patched
    try:
        yield
    finally:
        mcw.physics = orig


def allowed_fn(W):
    vols = W.volumes
    H = np.maximum(W.H, W.water)
    surf = W.surface_ok

    def ok(x, y, z):
        i, k = x - X0, z - Z0
        if 0 <= i < SX and 0 <= k < SZ and surf[i, k] and y <= H[i, k] + 16:
            return True
        for (_, x1, y1, z1, x2, y2, z2) in vols:
            if x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2:
                return True
        return False
    return ok


def walk(W, y_range=(22, 104)):
    a = W.a
    seeds = [W.spawns["spawn"]]
    with gates_open():
        rep = trapcheck.analyze(a, (X0 + 1, Z0 + 1, X0 + SX - 2, Z0 + SZ - 2), y_range, seeds, inside=None,
                                track_falls=True)
    ox, oy, oz = rep["offset"]
    pos = [(p[0] + ox, p[1] + oy, p[2] + oz) for p in rep["fwd"]]
    ok = allowed_fn(W)
    escaped = [p for p in pos if not ok(*p)]
    rep["escaped"] = escaped
    rep["positions"] = pos
    return rep


def reached(rep, target, r=2, dy=2):
    """Is any reachable feet position within r (horizontal) and dy (vertical) of target?"""
    S = rep.setdefault("_set", set(rep["positions"]))
    x, y, z = target
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            for yy in range(y - dy, y + dy + 1):
                if (x + dx, yy, z + dz) in S:
                    return True
    return False


def coverage(W, rep):
    missing = []
    for k, p in W.spawns.items():
        if not reached(rep, p):
            missing.append(("arrival", k, p))
    for s in W.shops:
        x, y, z = s["counter"]
        dx, dz = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}[s["facing"]]
        if not reached(rep, (x + dx, y, z + dz), r=2):
            missing.append(("shop", s["name"], s["counter"]))
        for e in s["ender_chests"]:
            if not reached(rep, (e[0] + dx, e[1], e[2] + dz), r=1, dy=1):
                missing.append(("ender_chest", s["name"], e))
    for h in W.hunts:
        hit = [p for p in h["spawn_points"] if reached(rep, p, r=1, dy=1)]
        if len(hit) < max(1, len(h["spawn_points"]) // 2):
            missing.append(("hunt", h["name"], h["spawn_points"][:2]))
    for b in W.bosses:
        x, y, z = b.get("boss_spawn_floor", b["boss_spawn"])
        if not reached(rep, (x, max(y, b["box"][1]), z), r=3, dy=3):
            missing.append(("boss", b["name"], (x, y, z)))
    return missing


def summarize_falls(falls, limit=12):
    """Group fall edges by landing column."""
    land = collections.Counter()
    ex = {}
    for p, q, d in falls:
        key = (q[0] // 4 * 4, q[2] // 4 * 4)
        land[key] += 1
        ex.setdefault(key, (p, q, d))
    return land, ex
