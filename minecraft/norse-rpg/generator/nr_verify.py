"""Walk checks for dungeons and the harbour.

From the arrival point an adventure-mode player must be able to reach every zone's spawn points, every arena,
the return ship and (with the exit gates open) the exit portal; nothing reachable may be a trap; and nobody may
climb out onto ground the dungeon does not use (escape check against an allowed-area mask).
"""
import math

import numpy as np

import trapcheck
from mcw import B, AIR


def near(S, p, r=2, dy=2):
    x, y, z = (int(math.floor(v)) for v in p[:3])
    for dx in range(-r, r + 1):
        for dz in range(-r, r + 1):
            for yy in range(y - dy, y + dy + 1):
                if (x + dx, yy, z + dz) in S:
                    return True
    return False


def walk(area, box, yr, seeds):
    rep = trapcheck.analyze(area, box, yr, seeds, inside=None, track_falls=True)
    ox, oy, oz = rep["offset"]
    pos = [(p[0] + ox, p[1] + oy, p[2] + oz) for p in rep["fwd"]]
    rep["positions"] = pos
    rep["_set"] = set(pos)
    return rep


def verify_dungeon(d, allowed=None, fix_traps=True, rounds=4):
    """allowed: bool mask (sx, sz) of columns players may stand on; None = anywhere."""
    a = d.a
    # open exit gates for the check, restore afterwards
    saved = []
    for ar in d.arenas:
        for (x, y, z) in ar["exit"]:
            saved.append((x, y, z, a.get(x, y, z)))
            a.set(x, y, z, AIR)
    box = (d.x0 + 1, d.z0 + 1, d.x0 + d.sx - 2, d.z0 + d.sz - 2)
    yr = (d.Y0 + 1, d.Y0 + d.SY - 4)
    seeds = [tuple(int(math.floor(v)) for v in d.data["start"][:3])]
    fixed = 0
    for r in range(rounds + 1):
        rep = walk(a, box, yr, seeds)
        if not rep["trapped"] or not fix_traps or r == rounds:
            break
        for (x, y, z) in rep["trapped"]:
            below = a.get(x, y - 1, z)
            a.set(x, y, z, below if below else B("stone"))
            fixed += 1
    S = rep["_set"]
    out = dict(reachable=rep["reachable"], trapped=len(rep["trapped"]), auto_filled=fixed, missing=[])
    for key, z in d.zones.items():
        ok = sum(1 for p in z["points"] if near(S, p, 1, 1))
        if ok < len(z["points"]):
            out["missing"].append(("zone points", key, "%d/%d" % (ok, len(z["points"]))))
        z["points"] = [p for p in z["points"] if near(S, p, 1, 1)]
    for ar in d.arenas:
        if not near(S, (ar["x"], ar["y"], ar["z"]), 2, 1):
            out["missing"].append(("arena", ar["id"]))
    if d.data.get("ret"):
        x1, y1, z1, x2, y2, z2 = d.data["ret"]["deck"]
        if not any(x1 <= p[0] <= x2 and z1 <= p[2] <= z2 and y1 - 1 <= p[1] <= y2 for p in S):
            out["missing"].append(("return ship", d.data["ret"]["deck"]))
    if d.data.get("exit"):
        x1, y1, z1, x2, y2, z2 = d.data["exit"]
        if not near(S, ((x1 + x2) / 2, y1, (z1 + z2) / 2), 1, 1):
            out["missing"].append(("exit portal", d.data["exit"]))
    if hasattr(d, "is_escape"):
        esc = [p for p in rep["positions"] if d.is_escape(*p)]
        out["escape"] = len(esc)
        out["escape_sample"] = esc[:8]
    elif allowed is not None:
        esc = [p for p in rep["positions"] if not allowed[p[0] - d.x0, p[2] - d.z0]]
        out["escape"] = len(esc)
        out["escape_sample"] = esc[:8]
    for (x, y, z, b) in saved:
        a.set(x, y, z, b)
    out["falls"] = len(rep.get("falls", []))
    d.verification = out
    return out, rep


def gate_check(d):
    """With every arena's exit gate shut (as built), open them one by one in arena order and report what becomes
    reachable at each stage. A zone or exit that is reachable before its gate opens means the gate can be bypassed."""
    a = d.a
    box = (d.x0 + 1, d.z0 + 1, d.x0 + d.sx - 2, d.z0 + d.sz - 2)
    yr = (d.Y0 + 1, d.Y0 + d.SY - 4)
    seeds = [tuple(int(math.floor(v)) for v in d.data["start"][:3])]
    order = sorted(d.arenas, key=lambda ar: {"mid1": 0, "mid2": 1, "final": 2}.get(ar["role"], 3))
    saved = []
    stages = []
    for stage in range(len(order) + 1):
        S = walk(a, box, yr, seeds)["_set"]
        got = [k for k, z in d.zones.items() if z["points"] and any(near(S, p, 1, 1) for p in z["points"])]
        ars = [ar["id"] for ar in d.arenas if near(S, (ar["x"], ar["y"], ar["z"]), 2, 1)]
        ex = False
        if d.data.get("exit"):
            x1, y1, z1, x2, y2, z2 = d.data["exit"]
            ex = near(S, ((x1 + x2) / 2, y1, (z1 + z2) / 2), 1, 1)
        stages.append(dict(opened=[o["id"] for o in order[:stage]], zones=got, arenas=ars, exit=ex))
        if stage < len(order):
            for (x, y, z) in order[stage]["exit"]:
                saved.append((x, y, z, a.get(x, y, z)))
                a.set(x, y, z, AIR)
    for (x, y, z, b) in saved:
        a.set(x, y, z, b)
    return stages
