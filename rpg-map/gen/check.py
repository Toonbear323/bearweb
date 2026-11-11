"""Consistency checks on a built World (block entities, command wiring, doors)."""
from .core import REG, DIRS

_BE_BLOCKS = {
    "Chest": ("chest", "trapped_chest"), "Barrel": ("barrel",), "Sign": ("sign",), "HangingSign": ("hanging_sign",),
    "MobSpawner": ("mob_spawner",), "CommandBlock": ("command_block",), "Banner": ("banner",), "Bed": ("bed",),
    "FlowerPot": ("flower_pot",), "Skull": ("skull",), "Beacon": ("beacon",), "Conduit": ("conduit",),
    "DecoratedPot": ("decorated_pot",),
}


def run(w):
    out = []
    name = lambda x, y, z: REG.name(w.get(x, y, z))
    for (x, y, z), d in w.be.items():
        n = name(x, y, z)
        want = _BE_BLOCKS.get(d["id"])
        if want and not any(k in n for k in want):
            out.append("BE %s at %s sits on block %s" % (d["id"], (x, y, z), n))
        if d["id"] == "CommandBlock" and "command_block" in n and "repeating" not in n:
            ok = False
            # plate two above with a solid block between
            if "pressure_plate" in name(x, y + 2, z) and w.get(x, y + 1, z) != 0:
                ok = True
            # button on a support block next to the command block
            for (dx, dz) in DIRS.values():
                sx, sz = x + dx, z + dz
                if w.get(sx, y, sz) != 0 and "button" in name(sx + dx, y, sz + dz):
                    ok = True
            if not ok:
                out.append("command block at %s has no trigger: %s" % ((x, y, z), d["Command"]))
    # doors need both halves
    door_ids = [i for i, (n, st) in enumerate(REG.entries) if n.endswith("_door")]
    import numpy as np
    pos = np.argwhere(np.isin(w.b, door_ids))
    for (xi, zi, yi) in pos:
        st = REG.states(int(w.b[xi, zi, yi]))
        other = yi - 1 if st["upper_block_bit"] else yi + 1
        if not (0 <= other < w.sy) or REG.name(int(w.b[xi, zi, other])) != REG.name(int(w.b[xi, zi, yi])):
            out.append("door half without partner at %s" % ((xi + w.x0, yi + w.y0, zi + w.z0),))
    return out
