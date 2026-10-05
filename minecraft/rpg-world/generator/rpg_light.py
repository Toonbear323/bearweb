"""Invisible light blocks where players can actually walk.

Every region box has a target: block light >= threshold at the feet of every reachable (dry) spot.
Threshold 1 is enough to stop natural hostile spawns in Bedrock (they need block light 0), so even
with mob spawning switched on, monsters only appear where the server owner spawns them
(or in a hunting ground whose lights were switched off with its function).
Hunting grounds are skipped here; they carry their own toggleable light grids (level 11).
"""
import numpy as np

from mcw import B, AIR, PAL
import lighting


def _in_hunt(W):
    boxes = [h["box"] for h in W.hunts]

    def f(x, y, z):
        for (x1, y1, z1, x2, y2, z2) in boxes:
            if x1 - 1 <= x <= x2 + 1 and z1 - 1 <= z <= z2 + 1 and y1 - 2 <= y <= y2 + 1:
                return True
        return False
    return f


def _box_light(W, x1, z1, x2, z2, y1, y2):
    a = W.a
    sl = (slice(x1 - a.x0, x2 - a.x0 + 1), slice(y1 - a.y0, y2 - a.y0 + 1), slice(z1 - a.z0, z2 - a.z0 + 1))
    return lighting.block_light(a.blk[sl])


def _points(W, rep, box, in_hunt):
    a = W.a
    name, x1, z1, x2, z2, y1, y2, thr, lvl = box
    water = {B("water"), B("lava"), B("flowing_water"), B("flowing_lava")}
    pts = []
    for (x, y, z) in rep["positions"]:
        if x1 <= x <= x2 and z1 <= z <= z2 and y1 <= y <= y2 and not in_hunt(x, y, z):
            if a.get(x, y, z) in water or a.get(x, y - 1, z) in water or a.wet[x - a.x0, y - a.y0, z - a.z0]:
                continue
            pts.append((x, y, z))
    return pts


def light_world(W, rep, spacing=4, rounds=5):
    a = W.a
    in_hunt = _in_hunt(W)
    total = 0
    for box in W.light_boxes:
        name, x1, z1, x2, z2, y1, y2, thr, lvl = box
        assert lvl != 11, "level 11 is reserved for hunting grounds"
        pts = _points(W, rep, box, in_hunt)
        if not pts:
            continue
        lb = B("light_block_%d" % lvl)
        ya, yb = y1 - 2, y2 + 4
        for r in range(rounds + 2):
            L = _box_light(W, x1, z1, x2, z2, ya, yb)
            dark = [p for p in pts if L[p[0] - x1, p[1] - ya, p[2] - z1] < thr]
            if not dark:
                break
            sp = spacing if r < rounds else 1          # last rounds: every remaining dark spot
            taken = set()
            for (x, y, z) in dark:
                key = (x // sp, y // 3, z // sp)
                if key in taken:
                    continue
                cand = [(0, 0, hy) for hy in (2, 1, 0)]
                if sp == 1:            # last resort: a neighbouring cell at head or feet height
                    cand += [(dx, dz, hy) for hy in (1, 0) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                for (dx, dz, hy) in cand:
                    if a.get(x + dx, y + hy, z + dz) == AIR:
                        a.set(x + dx, y + hy, z + dz, lb)
                        taken.add(key)
                        total += 1
                        break
    return total


def stats(W, rep):
    in_hunt = _in_hunt(W)
    out = {}
    for box in W.light_boxes:
        name, x1, z1, x2, z2, y1, y2, thr, lvl = box
        pts = _points(W, rep, box, in_hunt)
        if not pts:
            out[name] = "no reachable points"
            continue
        ya = y1 - 2
        L = _box_light(W, x1, z1, x2, z2, ya, y2 + 4)
        v = np.array([L[p[0] - x1, p[1] - ya, p[2] - z1] for p in pts])
        out[name] = "spots=%d min=%d median=%d target>=%d dark=%d" % (len(v), v.min(), int(np.median(v)), thr,
                                                                     int((v < thr).sum()))
    return out
