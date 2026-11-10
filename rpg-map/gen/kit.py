"""Architecture toolkit: rotated frames, roofs, towers and reusable props."""
import math

import numpy as np

from . import blocks as bl
from .core import B, CW, DIRS, OPP, Mix, REG

AIR = 0


class Frame:
    """Local coordinate frame rotated in 90 degree steps.  Local +z is 'S' (the front of a building)."""

    def __init__(self, w, ox, oy, oz, rot=0):
        self.w, self.o, self.rot = w, (ox, oy, oz), rot % 4
        self.rng = w.rng

    @staticmethod
    def box(w, x, y, z, bw, bd, face="S"):
        """Frame whose local box [0,bw)x[0,bd) covers the world box with min corner (x,z).
        The local front (south) points to `face`; for E/W the world box is (bd x bw)."""
        rot = {"S": 0, "W": 1, "N": 2, "E": 3}[face]
        ox, oz = {0: (x, z), 1: (x + bd - 1, z), 2: (x + bw - 1, z + bd - 1), 3: (x, z + bw - 1)}[rot]
        return Frame(w, ox, y, oz, rot)

    def sub(self, x, y, z, rot=0):
        """Child frame at a local position (optionally rotated relative to this one)."""
        wx, wy, wz = self.p(x, y, z)
        return Frame(self.w, wx, wy, wz, self.rot + rot)

    def p(self, x, y, z):
        r = self.rot
        if r == 0:
            dx, dz = x, z
        elif r == 1:
            dx, dz = -z, x
        elif r == 2:
            dx, dz = -x, -z
        else:
            dx, dz = z, -x
        return self.o[0] + dx, self.o[1] + y, self.o[2] + dz

    def d(self, direction):
        if direction in "UD":
            return direction
        for _ in range(self.rot):
            direction = CW[direction]
        return direction

    def ax(self, axis):
        if axis == "y" or self.rot % 2 == 0:
            return axis
        return "z" if axis == "x" else "x"

    def set(self, x, y, z, b, keep=False):
        self.w.set(*self.p(x, y, z), b, keep=keep)

    def get(self, x, y, z):
        return self.w.get(*self.p(x, y, z))

    def put(self, x, y, z, b, be=None):
        self.w.put(*self.p(x, y, z), b, be)

    def fill(self, xa, ya, za, xb, yb, zb, b, keep=False, only=None):
        ax_, ay_, az_ = self.p(xa, ya, za)
        bx_, by_, bz_ = self.p(xb, yb, zb)
        self.w.fill(ax_, ay_, az_, bx_, by_, bz_, b, keep=keep, only=only)

    def walls(self, xa, ya, za, xb, yb, zb, b):
        self.fill(xa, ya, za, xb, yb, za, b)
        self.fill(xa, ya, zb, xb, yb, zb, b)
        self.fill(xa, ya, za, xa, yb, zb, b)
        self.fill(xb, ya, za, xb, yb, zb, b)

    def water(self, x, y, z, on=True):
        self.w.water(*self.p(x, y, z), on)

    # directional shortcuts -------------------------------------------------
    def stairs(self, x, y, z, mat, facing, top=False, keep=False):
        self.set(x, y, z, bl.stairs(mat, self.d(facing), top), keep=keep)

    def slab(self, x, y, z, mat, top=False, keep=False):
        self.set(x, y, z, bl.slab(mat, top), keep=keep)

    def log(self, x, y, z, wood, axis="y", stripped=False):
        self.set(x, y, z, bl.log(wood, self.ax(axis), stripped))

    def door(self, x, y, z, wood, into, hinge_right=False):
        self.set(x, y, z, bl.door(wood, self.d(into), False, hinge_right))
        self.set(x, y + 1, z, bl.door(wood, self.d(into), True, hinge_right))

    def trap(self, x, y, z, wood, attach, open=True, top=False):
        self.set(x, y, z, bl.trapdoor(wood, self.d(attach), open, top))

    def torch(self, x, y, z, attach="top", kind="torch"):
        self.set(x, y, z, bl.torch(attach if attach == "top" else self.d(attach), kind))

    def lantern(self, x, y, z, hanging=False, soul=False):
        self.set(x, y, z, bl.lantern(hanging, soul))

    def chest(self, x, y, z, facing, items, trapped=False):
        self.put(x, y, z, bl.chest(self.d(facing), trapped), bl.be_chest(items))

    def barrel(self, x, y, z, facing="U", items=()):
        self.put(x, y, z, bl.barrel(self.d(facing)), bl.be_chest(list(items), "Barrel"))

    def sign(self, x, y, z, facing, text, wood="spruce", standing=False, glow=False):
        b = bl.standing_sign(self.d(facing), wood) if standing else bl.wall_sign(self.d(facing), wood)
        self.put(x, y, z, b, bl.be_sign(text, glow=glow))

    def hsign(self, x, y, z, facing, text, wood="spruce"):
        self.put(x, y, z, bl.hanging_sign(self.d(facing), wood), bl.be_sign(text, kind="HangingSign"))

    def banner(self, x, y, z, facing, color, standing=False):
        b = bl.standing_banner(self.d(facing)) if standing else bl.wall_banner(self.d(facing))
        self.put(x, y, z, b, bl.be_banner(color))

    def bed(self, x, y, z, facing, color=14):
        """(x,z) = foot position; head is one block toward `facing`."""
        f = self.d(facing)
        self.put(x, y, z, bl.bed(f, False), bl.be_bed(color))
        hx, hz = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}[facing]
        self.put(x + hx, y, z + hz, bl.bed(f, True), bl.be_bed(color))

    def spawner(self, x, y, z, entity, **kw):
        self.put(x, y, z, B("mob_spawner"), bl.be_spawner(entity, **kw))

    def potted(self, x, y, z, plant):
        self.put(x, y, z, B("flower_pot", update_bit=True), bl.be_pot(plant))

    def button_cmd(self, x, y, z, facing, command, support=None, kind="stone_button"):
        """Button on the `facing` side of a support block at (x,y,z); command block hidden behind it."""
        dx, dz = DIRS[facing]
        if support is not None:
            self.set(x, y, z, support)
        self.set(x + dx, y, z + dz, bl.button(self.d(facing), kind))
        self.put(x - dx, y, z - dz, bl.cmd("impulse", "U"), bl.be_cmd(command))

    def plate_cmd(self, x, y, z, command, plate="stone_pressure_plate", floor=None):
        """Pressure plate at (x,y,z) standing on a floor block with the command block beneath."""
        if floor is not None:
            self.set(x, y - 1, z, floor)
        self.set(x, y, z, B(plate))
        self.put(x, y - 2, z, bl.cmd("impulse", "U"), bl.be_cmd(command))


def world_frame(w):
    return Frame(w, 0, 0, 0, 0)


# ---------------------------------------------------------------------------
# roofs
# ---------------------------------------------------------------------------

def gable_roof(F, x0, z0, x1, z1, y, mat, axis="x", overhang=1, trim=None, gable=None, ridge=None, flare=False,
               end_overhang=None):
    """Gable roof over the local rect.  y = height of the wall top + 1.
    axis: direction of the ridge.  trim: stair material for the two gable-end rows.
    gable: block filling the triangular end walls.  flare: slab kick at the eaves."""
    trim = trim or mat
    eo = overhang if end_overhang is None else end_overhang
    if axis == "x":
        a0, a1, b0, b1 = x0, x1, z0, z1
    else:
        a0, a1, b0, b1 = z0, z1, x0, x1
    lo, hi = b0 - overhang, b1 + overhang

    def put(a, yy, b, blk_fn):
        if axis == "x":
            blk_fn(a, yy, b)
        else:
            blk_fn(b, yy, a)

    up_lo = "S" if axis == "x" else "E"   # ascent direction for the low-coordinate slope
    up_hi = "N" if axis == "x" else "W"
    n = (hi - lo) // 2 + 1
    top_y = y
    for i in range(n):
        bA, bB = lo + i, hi - i
        yy = y - overhang + i
        top_y = yy
        for a in range(a0 - eo, a1 + eo + 1):
            m = trim if (a == a0 - eo or a == a1 + eo) else mat
            if bA < bB:
                if flare and i == 0:
                    put(a, yy, bA, lambda X, Y, Z: F.slab(X, Y, Z, m, top=True))
                    put(a, yy, bB, lambda X, Y, Z: F.slab(X, Y, Z, m, top=True))
                else:
                    put(a, yy, bA, lambda X, Y, Z: F.stairs(X, Y, Z, m, up_lo))
                    put(a, yy, bB, lambda X, Y, Z: F.stairs(X, Y, Z, m, up_hi))
            elif bA == bB:
                rm = ridge or m
                put(a, yy, bA, lambda X, Y, Z: F.slab(X, Y, Z, rm))
        # gable end walls
        if gable is not None and bA < bB and yy >= y:
            for a in (a0, a1):
                for b in range(bA + 1, bB):
                    put(a, yy, b, lambda X, Y, Z: F.set(X, Y, Z, gable))
        # underside lining at the gable overhang for a thicker edge
        if eo > 0 and bA < bB and i > 0:
            for a in (a0 - eo, a1 + eo):
                put(a, yy - 1, bA, lambda X, Y, Z: F.stairs(X, Y, Z, trim, OPP[up_lo], top=True, keep=True))
                put(a, yy - 1, bB, lambda X, Y, Z: F.stairs(X, Y, Z, trim, OPP[up_hi], top=True, keep=True))
    return top_y


def hip_roof(F, x0, z0, x1, z1, y, mat, overhang=1, cap=None, steep=1):
    """Hipped / pyramid roof.  Returns top y."""
    xa, xb, za, zb = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
    yy = y - overhang
    while xa <= xb and za <= zb:
        if xa == xb or za == zb:
            for x in range(xa, xb + 1):
                for z in range(za, zb + 1):
                    F.slab(x, yy, z, cap or mat)
            return yy
        for x in range(xa, xb + 1):
            F.stairs(x, yy, za, mat, "S")
            F.stairs(x, yy, zb, mat, "N")
        for z in range(za + 1, zb):
            F.stairs(xa, yy, z, mat, "E")
            F.stairs(xb, yy, z, mat, "W")
        for s in range(1, steep):
            # steeper pitch: solid course under the next ring
            pass
        xa, xb, za, zb, yy = xa + 1, xb - 1, za + 1, zb - 1, yy + 1
    return yy - 1


def _ring(r):
    """Cells of a one-thick circle ring of radius r (r may be x.5)."""
    out = []
    R = int(math.ceil(r)) + 1
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            d = math.hypot(dx, dz)
            if r - 1.0 < d <= r:
                out.append((dx, dz))
    return out


def disc_cells(r):
    out = []
    R = int(math.ceil(r)) + 1
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            if math.hypot(dx, dz) <= r:
                out.append((dx, dz))
    return out


def _inward(dx, dz):
    if abs(dx) >= abs(dz):
        return "W" if dx > 0 else "E"
    return "N" if dz > 0 else "S"


def cone_roof(F, cx, cz, y, r, mat, steep=2, spire=None, cap=None, flare=True):
    """Conical roof for round towers.  steep = vertical layers per radius step."""
    yy = y
    rr = r + (1.0 if flare else 0.0)
    first = True
    while rr > 0.6:
        cells = _ring(rr)
        for (dx, dz) in cells:
            F.stairs(cx + dx, yy, cz + dz, mat, _inward(dx, dz)) if (first and flare) or steep == 1 else F.set(
                cx + dx, yy, cz + dz, bl.block(mat))
        if not ((first and flare) or steep == 1):
            for (dx, dz) in cells:
                for s in range(1, steep):
                    F.set(cx + dx, yy + s, cz + dz, bl.block(mat)) if s < steep - 1 else F.stairs(
                        cx + dx, yy + s, cz + dz, mat, _inward(dx, dz))
            yy += steep
        else:
            yy += 1
        first = False
        rr -= 1.0
    F.set(cx, yy - 1, cz, bl.block(mat))
    F.set(cx, yy, cz, cap or bl.block(mat))
    if spire is not None:
        for i, b in enumerate(spire):
            F.set(cx, yy + 1 + i, cz, b)
    return yy


def dome(F, cx, cy, cz, r, mat, thick=1.0, oculus=0.0, ry=None):
    """Hemispherical shell (upper half) centred at (cx,cy,cz)."""
    ry = ry or r
    R = int(math.ceil(r)) + 1
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            if oculus and math.hypot(dx, dz) <= oculus:
                continue
            for dy in range(0, int(math.ceil(ry)) + 1):
                d = math.sqrt((dx / r) ** 2 + (dz / r) ** 2 + (dy / ry) ** 2)
                d_in = math.sqrt((dx / (r - thick)) ** 2 + (dz / (r - thick)) ** 2 + (dy / (ry - thick)) ** 2)
                if d <= 1.0 and d_in > 1.0:
                    F.set(cx + dx, cy + dy, cz + dz, mat)


# ---------------------------------------------------------------------------
# towers & walls
# ---------------------------------------------------------------------------

def round_tower(F, cx, cz, y0, h, r, wall, floor=None, crenel=None, trim=None, windows=True, roof=None,
                floors_every=6, light=True, base_flare=True):
    """Round stone tower: hollow shaft, machicolated parapet, optional cone roof.  Returns parapet y."""
    w = F
    crenel = crenel or wall
    trim = trim or "stone_brick"
    for y in range(y0, y0 + h):
        for (dx, dz) in disc_cells(r):
            d = math.hypot(dx, dz)
            if d > r - 1.0:
                w.set(cx + dx, y, cz + dz, wall)
            else:
                w.set(cx + dx, y, cz + dz, AIR)
    if base_flare:
        for (dx, dz) in _ring(r + 1.0):
            w.stairs(cx + dx, y0, cz + dz, trim, _inward(dx, dz), keep=True)
    # floors
    if floor is not None:
        for fy in range(y0 + floors_every - 1, y0 + h - 2, floors_every):
            for (dx, dz) in disc_cells(r - 1.0):
                w.set(cx + dx, fy, cz + dz, floor)
            w.set(cx, fy, cz, AIR)
    # arrow slits
    if windows:
        for wy in range(y0 + 3, y0 + h - 3, floors_every):
            for (dx, dz, f) in ((r, 0, "E"), (-r, 0, "W"), (0, r, "S"), (0, -r, "N")):
                ix, iz = int(round(dx)), int(round(dz))
                if abs(dx) != int(abs(dx)):
                    ix = int(math.floor(abs(dx))) * (1 if dx > 0 else -1)
                    iz = int(math.floor(abs(dz))) * (1 if dz > 0 else -1)
                w.set(cx + ix, wy, cz + iz, AIR)
                w.set(cx + ix, wy + 1, cz + iz, AIR)
                w.set(cx + ix, wy, cz + iz, B("iron_bars"))
                w.set(cx + ix, wy + 1, cz + iz, B("iron_bars"))
    top = y0 + h
    # machicolation ring + parapet
    for (dx, dz) in _ring(r + 1.0):
        w.stairs(cx + dx, top - 1, cz + dz, trim, _inward(dx, dz), top=True)
    for (dx, dz) in disc_cells(r + 1.0):
        w.set(cx + dx, top, cz + dz, bl.block(trim) if math.hypot(dx, dz) > r - 1 else (floor or bl.block(trim)))
    ring = _ring(r + 1.0)
    ring.sort(key=lambda c: math.atan2(c[1], c[0]))
    for i, (dx, dz) in enumerate(ring):
        w.set(cx + dx, top + 1, cz + dz, crenel)
        if i % 2 == 0:
            w.set(cx + dx, top + 2, cz + dz, bl.slab(trim))
    if roof is not None:
        # timber posts carrying a conical roof above the parapet
        for (dx, dz) in ring[::max(1, len(ring) // 8)]:
            for yy in range(top + 2, top + 4):
                w.set(cx + dx, yy, cz + dz, bl.fence("spruce"))
        cone_roof(F, cx, cz, top + 4, r + 1.0, roof, steep=2, spire=[bl.fence("spruce"), B("lightning_rod",
                                                                                         facing_direction=1)])
        if light:
            w.lantern(cx, top + 1, cz)
    return top


# ---------------------------------------------------------------------------
# small props
# ---------------------------------------------------------------------------

def lamp_post(F, x, y, z, h=4, wall_mat="cobblestone", wood="spruce", soul=False):
    F.set(x, y, z, bl.wall(wall_mat))
    for i in range(1, h):
        F.set(x, y + i, z, bl.fence(wood))
    F.set(x, y + h, z, bl.block(wood))
    for dx, dz, a in ((1, 0, "W"), (-1, 0, "E"), (0, 1, "N"), (0, -1, "S")):
        F.trap(x + dx, y + h, z + dz, wood, a, open=True)
    F.set(x, y + h + 1, z, bl.slab(wood))
    F.set(x, y + h - 1, z, bl.fence(wood))
    # lantern cluster hanging under the cap arms
    F.set(x, y + h, z, B("glowstone") if not soul else B("sea_lantern"))


def lamp_arm(F, x, y, z, side, h=4, wood="dark_oak", soul=False):
    """Street lamp with a single arm and a hanging lantern on `side`."""
    dx, dz = DIRS[side]
    F.set(x, y, z, bl.wall("stone_brick"))
    for i in range(1, h + 1):
        F.set(x, y + i, z, bl.fence(wood))
    F.set(x + dx, y + h, z + dz, bl.fence(wood))
    F.lantern(x + dx, y + h - 1, z + dz, hanging=True, soul=soul)
    F.set(x, y + h + 1, z, bl.slab("stone_brick"))


def bench(F, x, y, z, length, facing, wood="spruce"):
    """Bench along local x starting at x, seat facing `facing` (N or S)."""
    back = OPP[facing]
    for i in range(length):
        F.stairs(x + i, y, z, wood, back)
    F.trap(x - 1, y, z, wood, "E", open=True)
    F.trap(x + length, y, z, wood, "W", open=True)


def crate_pile(F, x, y, z, rng, n=4):
    opts = [bl.barrel("U"), bl.barrel("N"), bl.barrel("E"), B("hay_block"), B("composter"), bl.block("spruce"),
            B("melon_block"), B("pumpkin", cardinal_direction="south")]
    for i in range(n):
        dx, dz = int(rng.integers(0, 2)), int(rng.integers(0, 2))
        hh = 0
        while F.get(x + dx, y + hh, z + dz) != 0 and hh < 3:
            hh += 1
        if hh < 2:
            F.set(x + dx, y + hh, z + dz, opts[int(rng.integers(0, len(opts)))])


def flowers(rng, kinds=None):
    kinds = kinds or ["poppy", "yellow_flower", "azure_bluet", "oxeye_daisy", "cornflower", "red_tulip",
                      "orange_tulip", "white_tulip", "pink_tulip", "allium", "lily_of_the_valley", "blue_orchid"]
    return B(kinds[int(rng.integers(0, len(kinds)))])


def well(F, x, y, z, stone="stone_brick", wood="spruce", roof="dark_oak"):
    """5x5 well centred on (x,z); y = ground surface block level."""
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            edge = max(abs(dx), abs(dz))
            if edge == 2:
                if abs(dx) == 2 and abs(dz) == 2:
                    F.set(x + dx, y + 1, z + dz, bl.slab(stone))
                else:
                    F.set(x + dx, y + 1, z + dz, bl.block("mossy_stone_brick" if (dx + dz) % 2 else stone))
                F.set(x + dx, y, z + dz, bl.block(stone))
            elif edge == 1:
                F.set(x + dx, y + 1, z + dz, bl.block(stone) if abs(dx) + abs(dz) == 2 else AIR)
                for d in range(0, 5):
                    F.set(x + dx, y - d, z + dz, bl.block("mossy_cobblestone"))
    for d in range(0, 5):
        F.set(x, y - d, z, bl.WATER)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        F.set(x + dx, y + 1, z + dz, bl.block(stone))
        F.set(x + dx, y, z + dz, bl.block(stone))
    F.set(x, y + 1, z, AIR)
    F.set(x, y, z, bl.WATER)
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        F.set(x + dx, y + 1, z + dz, bl.block(stone))
        for i in range(2, 4):
            F.set(x + dx, y + i, z + dz, bl.fence(wood))
    hip_roof(F, x - 1, z - 1, x + 1, z + 1, y + 4, roof, overhang=1, cap=roof)
    F.set(x, y + 4, z, bl.block(wood))
    F.set(x, y + 3, z, B("chain", pillar_axis="y"))
    F.set(x, y + 2, z, B("cauldron", cauldron_liquid="water", fill_level=6))


def hedge(F, xa, za, xb, zb, y, leaf="oak", h=1):
    for hh in range(h):
        F.fill(xa, y + hh, za, xb, y + hh, zb, bl.leaves(leaf))


def market_stall(F, x, y, z, color, goods, wood="spruce"):
    """5x3 stall, front facing local south.  (x,z) = back-left corner."""
    wool = B(color + "_wool")
    white = B("white_wool")
    for dx in (0, 4):
        for dz in (0, 2):
            for i in range(0, 3):
                F.set(x + dx, y + i, z + dz, bl.fence(wood))
    for dx in range(0, 5):
        F.set(x + dx, y, z, bl.block(wood)) if dx in (1, 2, 3) else None
        F.stairs(x + dx, y, z + 2, wood, "N", top=True) if dx in (1, 2, 3) else None
    for i, g in enumerate(goods[:3]):
        F.set(x + 1 + i, y + 1, z, g)
    # striped awning sloping to the front
    for dx in range(-1, 6):
        c = wool if dx % 2 == 0 else white
        F.set(x + dx, y + 3, z, c)
        F.set(x + dx, y + 3, z + 1, c)
        F.set(x + dx, y + 3, z + 2, B((color if dx % 2 == 0 else "white") + "_carpet"))
        F.set(x + dx, y + 4, z, B((color if dx % 2 == 0 else "white") + "_carpet"))
        F.set(x + dx, y + 3, z + 3, AIR)
    for dx in range(-1, 6):
        F.set(x + dx, y + 2, z + 3, AIR)
    F.lantern(x + 2, y + 2, z + 1, hanging=True)


def chandelier(F, x, y, z, drop=2, arms=1, soul=False):
    """Hangs from the block above (x,y+1,z); y is the top chain position."""
    for i in range(drop):
        F.set(x, y - i, z, B("chain", pillar_axis="y"))
    cy = y - drop
    F.set(x, cy, z, bl.fence("dark_oak"))
    for dx, dz in ((arms, 0), (-arms, 0), (0, arms), (0, -arms)):
        for k in range(1, arms + 1):
            sx, sz = (dx // arms) * k, (dz // arms) * k
            F.set(x + sx, cy, z + sz, bl.fence("dark_oak"))
        F.lantern(x + dx, cy - 1, z + dz, hanging=True, soul=soul)


def table(F, x, y, z, wood="spruce", cloth=None):
    F.set(x, y, z, bl.fence(wood))
    F.set(x, y + 1, z, B((cloth + "_carpet")) if cloth else B(
        {"oak": "wooden_pressure_plate"}.get(wood, wood + "_pressure_plate")))


def bookshelf_wall(F, xa, y, z, xb, h, rng):
    for x in range(min(xa, xb), max(xa, xb) + 1):
        for i in range(h):
            F.set(x, y + i, z, B("bookshelf") if rng.random() < 0.85 else B("chiseled_bookshelf"))


# ---------------------------------------------------------------------------
# trees
# ---------------------------------------------------------------------------

def _blob(w, x, y, z, r, leaf, rng, squash=0.8):
    R = int(math.ceil(r))
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            for dy in range(-R, R + 1):
                d = math.sqrt(dx * dx + dz * dz + (dy / squash) ** 2)
                if d <= r - 0.25 + rng.random() * 0.6:
                    w.set(x + dx, y + dy, z + dz, leaf, keep=True)


def tree_oak(w, x, y, z, rng, h=None, wood="oak", leaf=None):
    h = h or int(rng.integers(5, 8))
    leaf = bl.leaves(leaf or wood)
    for i in range(h):
        w.set(x, y + i, z, bl.log(wood))
    _blob(w, x, y + h, z, 2.6 + rng.random() * 0.8, leaf, rng, 0.75)
    for _ in range(3):
        _blob(w, x + int(rng.integers(-2, 3)), y + h - 1 + int(rng.integers(-1, 2)), z + int(rng.integers(-2, 3)),
              1.8 + rng.random(), leaf, rng)


def tree_big(w, x, y, z, rng, h=None, wood="oak", leaf=None, spread=5):
    """Large branching tree with several canopy clusters."""
    h = h or int(rng.integers(9, 14))
    leafb = bl.leaves(leaf or wood)
    logy = bl.log(wood)
    for i in range(h):
        w.set(x, y + i, z, logy)
        if i < 2:
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if rng.random() < 0.75 - i * 0.3:
                    w.set(x + dx, y + i, z + dz, bl.wood(wood))
    nb = int(rng.integers(4, 7))
    for k in range(nb):
        ang = 2 * math.pi * k / nb + rng.random() * 0.6
        ln = spread * (0.6 + rng.random() * 0.5)
        by = y + h - int(rng.integers(2, 5))
        ex, ez, ey = x + math.cos(ang) * ln, z + math.sin(ang) * ln, by + ln * 0.5
        steps = int(ln) + 1
        for s in range(steps + 1):
            t = s / steps
            px, py, pz = x + (ex - x) * t, by + (ey - by) * t, z + (ez - z) * t
            w.set(int(round(px)), int(round(py)), int(round(pz)), bl.wood(wood))
        _blob(w, int(round(ex)), int(round(ey)) + 1, int(round(ez)), 2.6 + rng.random() * 1.2, leafb, rng, 0.7)
    _blob(w, x, y + h + 1, z, 3.2 + rng.random(), leafb, rng, 0.7)


def tree_birch(w, x, y, z, rng):
    h = int(rng.integers(6, 9))
    for i in range(h):
        w.set(x, y + i, z, bl.log("birch"))
    lf = bl.leaves("birch")
    for dy, r in ((h - 3, 2.2), (h - 2, 2.4), (h - 1, 1.8), (h, 1.3), (h + 1, 0.8)):
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if math.hypot(dx, dz) <= r + rng.random() * 0.4:
                    w.set(x + dx, y + dy, z + dz, lf, keep=True)


def tree_spruce(w, x, y, z, rng, h=None):
    h = h or int(rng.integers(8, 14))
    for i in range(h):
        w.set(x, y + i, z, bl.log("spruce"))
    lf = bl.leaves("spruce")
    r = 0.6
    yy = y + h + 1
    w.set(x, yy, z, lf, keep=True)
    w.set(x, yy - 1, z, lf, keep=True)
    layer = 0
    for yy in range(y + h, y + 2, -1):
        layer += 1
        rr = 1.0 + (layer // 2) * 0.9 if layer % 2 == 0 else 0.9 + (layer // 2) * 0.55
        rr = min(rr, 4.5)
        R = int(math.ceil(rr))
        for dx in range(-R, R + 1):
            for dz in range(-R, R + 1):
                if math.hypot(dx, dz) <= rr + 0.3:
                    w.set(x + dx, yy, z + dz, lf, keep=True)


def tree_cherry(w, x, y, z, rng, h=None):
    h = h or int(rng.integers(4, 6))
    lf = bl.leaves("cherry")
    for i in range(h):
        w.set(x, y + i, z, bl.log("cherry"))
    for k in range(int(rng.integers(3, 5))):
        ang = 2 * math.pi * k / 4 + rng.random()
        ln = 3 + rng.random() * 2.5
        ex, ez = x + math.cos(ang) * ln, z + math.sin(ang) * ln
        steps = int(ln) + 1
        for s in range(steps + 1):
            t = s / steps
            w.set(int(round(x + (ex - x) * t)), y + h - 1 + int(round(t * 2)), int(round(z + (ez - z) * t)),
                  bl.wood("cherry"))
        _blob(w, int(round(ex)), y + h + 2, int(round(ez)), 2.8 + rng.random(), lf, rng, 0.55)
    _blob(w, x, y + h + 2, z, 3.3, lf, rng, 0.6)


def tree_palm(w, x, y, z, rng, h=None):
    h = h or int(rng.integers(6, 10))
    ang = rng.random() * 2 * math.pi
    lean = 0.25 + rng.random() * 0.25
    px, pz = float(x), float(z)
    for i in range(h):
        w.set(int(round(px)), y + i, int(round(pz)), bl.log("jungle"))
        px += math.cos(ang) * lean * (i / h)
        pz += math.sin(ang) * lean * (i / h)
    tx, tz, ty = int(round(px)), int(round(pz)), y + h
    lf = bl.leaves("jungle")
    w.set(tx, ty, tz, lf)
    for k in range(8):
        a = 2 * math.pi * k / 8
        ln = 4 if k % 2 == 0 else 3
        for s in range(1, ln + 1):
            fx, fz = tx + int(round(math.cos(a) * s)), tz + int(round(math.sin(a) * s))
            fy = ty + (1 if s <= 1 else (0 if s <= 2 else -(s - 2)))
            w.set(fx, fy, fz, lf, keep=True)
    for dx, dz in ((1, 0), (-1, 0), (0, 1)):
        if rng.random() < 0.5:
            w.set(tx + dx, ty - 1, tz + dz, B("cocoa", age=2, direction={(1, 0): 1, (-1, 0): 3, (0, 1): 2}[(dx, dz)]),
                  keep=True)


def tree_dead(w, x, y, z, rng, wood="spruce"):
    h = int(rng.integers(3, 7))
    for i in range(h):
        w.set(x, y + i, z, bl.log(wood, stripped=rng.random() < 0.3))
    for _ in range(int(rng.integers(1, 4))):
        a = rng.random() * 2 * math.pi
        by = y + int(rng.integers(2, max(3, h)))
        for s in range(1, int(rng.integers(2, 4))):
            w.set(x + int(round(math.cos(a) * s)), by + s // 2, z + int(round(math.sin(a) * s)), bl.fence(wood),
                  keep=True)


def bush(w, x, y, z, rng, leaf="oak"):
    lf = bl.leaves(leaf)
    w.set(x, y, z, lf, keep=True)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if rng.random() < 0.5:
            w.set(x + dx, y, z + dz, lf, keep=True)
    if rng.random() < 0.5:
        w.set(x, y + 1, z, lf, keep=True)


# ---------------------------------------------------------------------------
# post processing
# ---------------------------------------------------------------------------

def _wall_ids():
    return [i for i, (n, _) in enumerate(REG.entries) if n.endswith("_wall")]


_SOLID_HINT = ("stairs", "slab", "fence", "pane", "bars", "door", "torch", "lantern", "sign", "banner", "carpet",
               "button", "plate", "lever", "flower", "grass", "leaves", "chain", "ladder", "vine", "candle",
               "water", "lava", "air", "rail", "pot", "bed", "chest", "campfire", "tulip", "fern", "roots",
               "glass", "light_block", "web", "petals", "poppy", "allium", "orchid", "bluet", "daisy", "cornflower",
               "lily", "bush", "sapling", "mushroom", "fungus", "kelp", "seagrass", "coral", "pickle", "dripstone",
               "bud", "cluster", "rod", "hook", "wire", "snow_layer", "cactus", "reeds", "bamboo", "skull", "bell",
               "anvil", "cauldron", "hopper", "brewing", "enchanting", "lectern", "grindstone", "stonecutter",
               "composter", "scaffolding", "frame", "egg", "portal", "fire", "wheat", "carrots", "potatoes",
               "beetroot", "deadbush", "lichen", "sprouts", "azalea", "dripleaf", "blossom", "conduit", "beacon",
               "spawner", "cocoa", "wart", "barrier")


def full_solid_table():
    n = len(REG.entries)
    t = np.ones(n, bool)
    for i, (name, _) in enumerate(REG.entries):
        if name in ("nether_wart_block", "warped_wart_block", "grass_block", "grass_path", "brown_mushroom_block",
                    "red_mushroom_block", "dripstone_block", "glass", "tinted_glass", "sea_lantern", "glowstone",
                    "bone_block", "hay_block", "bookshelf", "chiseled_bookshelf", "flowering_azalea_none"):
            t[i] = name not in ("grass_path",)
            continue
        if any(k in name for k in _SOLID_HINT):
            t[i] = False
    return t


def connect_walls(w):
    """Compute wall connection states (Bedrock stores them explicitly)."""
    ids = _wall_ids()
    if not ids:
        return 0
    solid = full_solid_table()
    pos = np.argwhere(np.isin(w.b, ids))
    is_wall = np.zeros(len(REG.entries) + 4096, bool)
    is_wall[ids] = True
    connect_names = ("iron_bars", "glass_pane", "_stained_glass_pane")
    conn_tbl = np.zeros(len(REG.entries) + 4096, bool)
    gate_tbl = {}
    for i, (name, st) in enumerate(REG.entries):
        if name.endswith("_wall") or name == "iron_bars" or name.endswith("glass_pane"):
            conn_tbl[i] = True
        elif i < len(solid) and solid[i]:
            conn_tbl[i] = True
        if name.endswith("fence_gate"):
            dd = dict((k, v) for k, t, v in st)["direction"]
            gate_tbl[i] = "x" if dd in (0, 2) else "z"   # axis the gate spans
    sx, sz, sy = w.b.shape
    out = {}
    cnt = 0
    for (x, z, y) in pos:
        cur = int(w.b[x, z, y])
        st = {}
        above = int(w.b[x, z, y + 1]) if y + 1 < sy else 0
        above_solid = above < len(solid) and solid[above] and above != 0
        con = {}
        for dname, (dx, dz) in DIRS.items():
            nx_, nz_ = x + dx, z + dz
            c = False
            if 0 <= nx_ < sx and 0 <= nz_ < sz:
                nb = int(w.b[nx_, nz_, y])
                c = bool(conn_tbl[nb]) and nb != 0
                if nb in gate_tbl:
                    c = gate_tbl[nb] == ("x" if dname in ("E", "W") else "z")
            con[dname] = c
        for dname, (dx, dz) in DIRS.items():
            key = "wall_connection_type_" + {"N": "north", "E": "east", "S": "south", "W": "west"}[dname]
            if not con[dname]:
                st[key] = "none"
            else:
                tall = above_solid
                if not tall and is_wall[above]:
                    nx_, nz_ = x + dx, z + dz
                    nb2 = int(w.b[nx_, nz_, y + 1]) if (0 <= nx_ < sx and 0 <= nz_ < sz and y + 1 < sy) else 0
                    tall = bool(conn_tbl[nb2]) and nb2 != 0
                st[key] = "tall" if tall else "short"
        straight = (con["N"] and con["S"] and not con["E"] and not con["W"]) or (
            con["E"] and con["W"] and not con["N"] and not con["S"])
        post = not straight
        if straight and above != 0 and not above_solid:
            post = True
        if straight and is_wall[above]:
            post = False
        st["wall_post_bit"] = post
        new = REG.with_state(cur, **st)
        if new != cur:
            out[(x, z, y)] = new
            cnt += 1
    for (x, z, y), v in out.items():
        w.b[x, z, y] = v
    return cnt


def waterlog_region(w, xa, ya, za, xb, yb, zb):
    """Fill air with water and waterlog partial blocks inside a box (for submerged builds)."""
    s = w._clip(xa, ya, za, xb, yb, zb)
    if s is None:
        return
    v = w.b[s]
    solid = full_solid_table()
    tbl = np.zeros(max(len(REG.entries), int(v.max()) + 1), bool)
    tbl[:len(solid)] = ~solid
    tbl[0] = False
    part = tbl[v]
    w.wl[s] |= part
    v[v == 0] = bl.WATER
