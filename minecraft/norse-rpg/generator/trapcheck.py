"""Walkability analysis: verifies that an adventure-mode player can never get stuck.

A position is a feet cell where a player (1.8 tall) can stand, swim or climb.
Moves: walk / step up at most 1 block (jump), fall any distance (fall damage is off),
swim in water, climb ladders/vines. Every position reachable from the spawn must be able
to get back to the spawn - otherwise it is a trap ("2칸 이상 갇히는 공간").
"""
from collections import deque

import numpy as np

from mcw import physics_tables, B


def analyze(area, box, yr, seeds, inside=None, max_report=20, track_falls=False, fall_min=4):
    x1, z1, x2, z2 = box
    y1, y2 = yr
    htab, liq, clb = physics_tables()
    ox, oy, oz = x1 - area.x0, y1 - 1 - area.y0, z1 - area.z0
    sub = area.blk[ox:x2 - area.x0 + 1, oy:y2 - area.y0 + 3, oz:z2 - area.z0 + 1]
    Hs = htab[sub]
    Ls = liq[sub] | area.wet[ox:x2 - area.x0 + 1, oy:y2 - area.y0 + 3, oz:z2 - area.z0 + 1]
    Cs = clb[sub]
    from mcw import PAL
    stair_t = np.array([n.endswith("_stairs") for n in PAL.names] + [False] * (len(htab) - len(PAL.names)))
    Ss = stair_t[sub]
    pas = Hs == 0
    nx, ny, nz = sub.shape
    # feet index j (1..ny-3) -> world y = y1 - 1 + j
    valid = np.zeros(sub.shape, bool)
    F2 = np.full(sub.shape, -999, np.int32)
    kind = np.zeros(sub.shape, np.int8)    # 1 stand, 2 swim, 3 surface, 4 climb
    J = np.arange(ny)
    wy = y1 - 1 + J
    for j in range(1, ny - 2):
        below, feet, head, head2 = Hs[:, j - 1], Hs[:, j], Hs[:, j + 1], Hs[:, j + 2] if j + 2 < ny else Hs[:, j + 1]
        lf = Ls[:, j]
        lb = Ls[:, j - 1]
        a = (below == 2) & (feet == 0) & ~lf & (head == 0)
        b = (below == 3) & (feet == 0) & ~lf & (head == 0) & (head2 == 0)
        c = (feet == 1) & (head == 0) & (head2 == 0)
        s = lf & (head == 0)
        u = (feet == 0) & ~lf & lb & (head == 0)
        k = Cs[:, j] & (head == 0)
        v = a | b | c | s | u | k
        valid[:, j] = v
        f = np.full((nx, nz), -999, np.int32)
        f[a | u | k | s] = 2 * wy[j]
        f[b | c] = 2 * wy[j] + 1
        F2[:, j] = f
        kd = np.zeros((nx, nz), np.int8)
        kd[a | b | c] = 1
        kd[u] = 3
        kd[k & ~(a | b | c)] = 4
        kd[s] = 2
        kind[:, j] = kd
    # column lists
    cols = {}
    vi = np.argwhere(valid)
    for (x, j, z) in vi:
        cols.setdefault((x, z), []).append(j)
    for key in cols:
        cols[key].sort()

    def neighbors(x, j, z):
        out = []
        kd = kind[x, j, z]
        f = F2[x, j, z]
        # vertical moves
        if kd == 2:      # swimming
            if j + 1 < ny - 2 and valid[x, j + 1, z]:
                out.append((x, j + 1, z))
            if j - 1 >= 1 and valid[x, j - 1, z] and kind[x, j - 1, z] == 2:
                out.append((x, j - 1, z))
        if kd == 3 and j - 1 >= 1 and valid[x, j - 1, z] and kind[x, j - 1, z] == 2:
            out.append((x, j - 1, z))
        if Cs[x, j, z] or (kd == 4):
            if j + 1 < ny - 2 and valid[x, j + 1, z]:
                out.append((x, j + 1, z))
            if j - 1 >= 1 and valid[x, j - 1, z]:
                out.append((x, j - 1, z))
        # falling straight down from a non-standing spot (e.g. top of a climbable)
        reach = f + 2 if kd != 2 else 2 * (y1 - 1 + j) + 2
        head_clear = (j + 2 < ny) and Hs[x, j + 2, z] == 0
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            qx, qz = x + dx, z + dz
            if not (0 <= qx < nx and 0 <= qz < nz):
                continue
            lst = cols.get((qx, qz))
            if not lst:
                continue
            # step up / same level
            for qj in lst:
                g = F2[qx, qj, qz]
                if g < f - 1 or g > reach:
                    continue
                if g > f + 1 and kd != 2 and not head_clear and not Ss[qx, qj - 1, qz]:
                    continue
                if g > f + 1 and kd == 2 and not (Hs[x, j + 1, z] == 0):
                    continue
                out.append((qx, qj, qz))
            # walking off an edge / swimming sideways then falling
            if pas[qx, j, qz] and (j + 1 < ny and pas[qx, j + 1, qz]):
                for qj in reversed(lst):
                    if qj <= j and F2[qx, qj, qz] < f - 1:
                        # nothing solid between landing and feet level
                        if all(pas[qx, t, qz] for t in range(qj + 1, j + 1)) and (pas[qx, qj, qz] or Hs[qx, qj, qz] == 1):
                            out.append((qx, qj, qz))
                        break
        return out

    seed_idx = []
    for (sx, sy, sz) in seeds:
        x, j, z = sx - x1, sy - (y1 - 1), sz - z1
        if 0 <= x < nx and 0 <= z < nz and 0 <= j < ny and valid[x, j, z]:
            seed_idx.append((x, j, z))
    if not seed_idx:
        raise RuntimeError("no valid seed position")
    # forward BFS (build reverse edges along the way)
    fwd = {s: None for s in seed_idx}
    rev = {}
    dq = deque(seed_idx)
    falls = []
    while dq:
        p = dq.popleft()
        for q in neighbors(*p):
            rev.setdefault(q, []).append(p)
            if track_falls and F2[p] - F2[q] >= 2 * fall_min and kind[q] not in (2, 3) and kind[p] != 4:
                falls.append((p, q))
            if q not in fwd:
                fwd[q] = p
                dq.append(q)
    back = set(seed_idx)
    dq = deque(seed_idx)
    while dq:
        p = dq.popleft()
        for q in rev.get(p, ()):
            if q not in back:
                back.add(q)
                dq.append(q)
    trapped = [p for p in fwd if p not in back]
    to_world = lambda p: (p[0] + x1, p[1] + y1 - 1, p[2] + z1)
    escaped = []
    if inside is not None:
        escaped = [to_world(p) for p in fwd if not inside(p[0] + x1, p[2] + z1)]
    def entry(p):
        """Walk parents back to the first position that is NOT trapped (how the player got in)."""
        path = [p]
        while fwd.get(path[-1]) is not None and path[-1] not in back:
            path.append(fwd[path[-1]])
        return [to_world(q) for q in path[-3:]]
    fall_list = [(to_world(p), to_world(q), (int(F2[p]) - int(F2[q])) / 2.0) for p, q in falls]
    return dict(reachable=len(fwd), trapped=[to_world(p) for p in trapped], escaped=escaped, falls=fall_list,
                fwd=fwd, offset=(x1, y1 - 1, z1), entry=lambda w: entry((w[0] - x1, w[1] - y1 + 1, w[2] - z1)))


def fix_traps(area, report, filler=None, max_iter=1):
    """Raise the floor under trapped positions (fills the feet cell with the block below)."""
    n = 0
    for (x, y, z) in report["trapped"]:
        b = area.get(x, y, z)
        below = area.get(x, y - 1, z)
        fill = filler if filler is not None else below
        if b == 0 or True:
            area.set(x, y, z, fill if fill != 0 else B("stone"))
            n += 1
    return n


def check_and_fix(area, box, yr, seeds, inside=None, label="", filler=None, rounds=8, verbose=True):
    total_fixed = 0
    rep = None
    for r in range(rounds):
        rep = analyze(area, box, yr, seeds, inside)
        tr = rep["trapped"]
        if verbose:
            print("  [%s] round %d: reachable=%d trapped=%d escaped=%d" % (label, r, rep["reachable"], len(tr), len(rep["escaped"])))
            if tr:
                print("     e.g.", tr[:8])
            if rep["escaped"]:
                print("     escaped e.g.", rep["escaped"][:8])
        if not tr:
            break
        total_fixed += fix_traps(area, rep, filler)
    return rep, total_fixed
