"""Generic buildings: timber houses with gable roofs, towers, tents, palisades."""
import math

from mcw import B, AIR
from gen_common import stair, slab
from rpg_parts import DV, LEFT, RIGHT, OPP, FACE, hanging_lantern


def gable_roof(a, x1, z1, x2, z2, y, stairs, ridge, gable, axis=None, overhang=1, holes=None, rng=None):
    """Gable roof over the box x1..x2, z1..z2 starting at height y (first stair row).
    axis = direction of the ridge ('x' or 'z'); default = longer side."""
    if axis is None:
        axis = "x" if (x2 - x1) >= (z2 - z1) else "z"
    if axis == "x":
        lo, hi = z1 - overhang, z2 + overhang
        i = 0
        while lo <= hi:
            yy = y + i
            for x in range(x1 - overhang, x2 + overhang + 1):
                if holes and rng and rng.random() < holes:
                    continue
                if lo == hi:
                    a.set(x, yy, lo, ridge)
                else:
                    a.set(x, yy, lo, stair(stairs, "south"))
                    a.set(x, yy, hi, stair(stairs, "north"))
            for x in (x1, x2):
                for z in range(lo + 1, hi):
                    a.set(x, yy, z, gable)
            lo += 1
            hi -= 1
            i += 1
        return y + i - 1
    else:
        lo, hi = x1 - overhang, x2 + overhang
        i = 0
        while lo <= hi:
            yy = y + i
            for z in range(z1 - overhang, z2 + overhang + 1):
                if holes and rng and rng.random() < holes:
                    continue
                if lo == hi:
                    a.set(lo, yy, z, ridge)
                else:
                    a.set(lo, yy, z, stair(stairs, "east"))
                    a.set(hi, yy, z, stair(stairs, "west"))
            for z in (z1, z2):
                for x in range(lo + 1, hi):
                    a.set(x, yy, z, gable)
            lo += 1
            hi -= 1
            i += 1
        return y + i - 1


def house(W, x1, z1, x2, z2, y, h=4, post=None, wall=None, floor=None, roof_stairs="dark_oak_stairs",
          roof_ridge=None, gable=None, window=None, doors=(), axis=None, lamp=True, base=None,
          burnt=0.0, rng=None, roof_holes=0.0, interior_air=True):
    """Box house: corner posts, walls, windows every 3rd cell, doorways (side, offset) 2 high.
    y = floor top block; walls y+1..y+h; roof starts at y+h+1."""
    a = W.a
    post = post or B("spruce_log")
    wall = wall or B("spruce_planks")
    floor = floor or B("spruce_planks")
    gable = gable or wall
    roof_ridge = roof_ridge or B("dark_oak_slab")
    window = window if window is not None else B("glass_pane")
    base = base or B("cobblestone")
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            corner = x in (x1, x2) and z in (z1, z2)
            # foundation down to the ground
            yy = y - 1
            while yy > y - 12 and a.get(x, yy, z) in (AIR, B("short_grass")):
                a.set(x, yy, z, base)
                yy -= 1
            a.set(x, y, z, base if edge else floor)
            for k in range(1, h + 1):
                if corner:
                    b = post
                elif edge:
                    b = base if k == 1 and burnt == 0 else wall
                    along = (x - x1) if z in (z1, z2) else (z - z1)
                    if k in (2, 3) and along % 3 == 2 and window != AIR:
                        b = window
                    if burnt and rng and rng.random() < burnt:
                        b = rng.choice([B("coal_block"), B("blackstone"), AIR, B("black_concrete_powder")])
                else:
                    b = AIR if interior_air else None
                if b is not None:
                    a.set(x, y + k, z, b)
    # doorways
    for side, off in doors:
        if side == "north":
            cells = [(x1 + off, z1)]
        elif side == "south":
            cells = [(x1 + off, z2)]
        elif side == "west":
            cells = [(x1, z1 + off)]
        else:
            cells = [(x2, z1 + off)]
        for (cx, cz) in cells:
            a.set(cx, y + 1, cz, AIR)
            a.set(cx, y + 2, cz, AIR)
            a.set(cx, y, cz, floor)
    top = gable_roof(a, x1, z1, x2, z2, y + h + 1, roof_stairs, roof_ridge, gable, axis=axis,
                     holes=roof_holes, rng=rng)
    if lamp:
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        if a.get(cx, y + h + 1, cz) != AIR:
            hanging_lantern(a, cx, y + h, cz, chain=0)
        else:
            a.set(cx, y + h, cz, B("lantern", hanging=0))
    return top


def round_tower(W, cx, cz, y, r, h, wall, floor=None, roof=None, roof_h=None, windows=None, door=None,
                inner=AIR, cap_block=None):
    """Round tower; roof is a cone of `roof` blocks (None = flat battlement with merlons)."""
    a = W.a
    floor = floor or wall
    for x in range(cx - r - 1, cx + r + 2):
        for z in range(cz - r - 1, cz + r + 2):
            d = math.hypot(x - cx, z - cz)
            if d <= r + 0.5:
                a.set(x, y, z, floor)
                for k in range(1, h + 1):
                    if d > r - 0.5:
                        a.set(x, y + k, z, wall)
                    else:
                        a.set(x, y + k, z, inner)
                a.set(x, y + h + 1, z, wall if d > r - 0.5 else floor)
    if roof is not None:
        rh = roof_h or (r * 2 + 2)
        for k in range(rh):
            rr = (r + 1) * (1 - k / rh)
            for x in range(cx - r - 2, cx + r + 3):
                for z in range(cz - r - 2, cz + r + 3):
                    if math.hypot(x - cx, z - cz) <= rr + 0.3:
                        a.set(x, y + h + 2 + k, z, roof)
        if cap_block is not None:
            a.set(cx, y + h + 2 + rh, cz, cap_block)
    else:
        for x in range(cx - r - 1, cx + r + 2):
            for z in range(cz - r - 1, cz + r + 2):
                d = math.hypot(x - cx, z - cz)
                if r - 0.5 < d <= r + 0.5 and (x + z) % 2 == 0:
                    a.set(x, y + h + 2, z, wall)
    if windows:
        for k in windows:
            for ang in range(0, 360, 90):
                wx = cx + int(round(math.cos(math.radians(ang)) * r))
                wz = cz + int(round(math.sin(math.radians(ang)) * r))
                a.set(wx, y + k, wz, B("glass_pane") if not isinstance(windows, dict) else windows[k])
    if door:
        dx, dz = DV[door]
        for t in range(r + 1):
            for k in (1, 2):
                a.set(cx + dx * t, y + k, cz + dz * t, AIR)


def tent(W, x, z, y, length, color, axis="x", pole=None):
    """A-frame wool tent (open at both ends)."""
    a = W.a
    wool = B(color + "_wool")
    pole = pole or B("oak_fence")
    for t in range(length):
        for k in range(3):
            for s in (-1, 1):
                off = (2 - k) * s
                if axis == "x":
                    a.set(x + t, y + 1 + k, z + off, wool)
                else:
                    a.set(x + off, y + 1 + k, z + t, wool)
        if axis == "x":
            a.set(x + t, y + 4, z, wool)
        else:
            a.set(x, y + 4, z + t, wool)
    # ridge poles at both ends (above head height, so the ends stay open)
    for t in (0, length - 1):
        if axis == "x":
            a.set(x + t, y + 4, z, pole)
        else:
            a.set(x, y + 4, z + t, pole)


def palisade_post(a, x, y, z, h, log, tip=None):
    for k in range(1, h + 1):
        a.set(x, y + k, z, log)
    if tip is not None:
        a.set(x, y + h + 1, z, tip)
