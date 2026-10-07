"""Castle building kit for the mid / high tier dungeons.

Everything is axis-aligned and works in world coordinates on an mcw.Area. A palette `Pal` bundles the materials of
one style (wall mixer, trim, floor, roof stairs/slab/block, pillar, window, light) so the same builders produce a
black basalt shipyard, a giant grey citadel or a dwarven forge hall.

Conventions: `y0` is the feet level of the floor (the floor block is at y0 - 1); heights count blocks above y0.
"""
import math

from mcw import B, AIR, PAL
from gen_common import stair, slab

DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
FACE = {"north": 2, "south": 3, "west": 4, "east": 5}          # facing_direction of wall-mounted blocks


def mixer(rng, items):
    tot = sum(w for _, w in items)

    def f():
        r = rng.random() * tot
        for b, w in items:
            r -= w
            if r <= 0:
                return b
        return items[-1][0]
    return f


class Pal:
    def __init__(self, rng, wall, trim, floor, roof, pillar=None, window="iron_bars", light="lantern", accent=None,
                 top=None, beam="dark_oak_log", plank="dark_oak_planks"):
        """wall/floor: [(block name, weight)]; trim/pillar/accent/top: block name; roof: stairs base name
        (e.g. 'deepslate_tile' -> deepslate_tile_stairs / _slab / deepslate_tiles)."""
        self.rng = rng
        self.wall = mixer(rng, [(B(n), w) for n, w in wall])
        self.floor = mixer(rng, [(B(n), w) for n, w in floor])
        self.trim = B(trim)
        self.trim_name = trim
        self.pillar = B(pillar or trim)
        self.window = B(window)
        self.light = light
        self.accent = B(accent or trim)
        self.top = B(top or trim)
        self.roof_stairs = roof + "_stairs"
        self.roof_slab = B(roof + "_slab")
        self.roof_block = B(ROOF_BLOCK.get(roof, roof))
        self.beam = beam
        self.plank = B(plank)


ROOF_BLOCK = {"deepslate_tile": "deepslate_tiles", "deepslate_brick": "deepslate_bricks", "stone_brick": "stone_bricks",
              "dark_oak": "dark_oak_planks", "spruce": "spruce_planks", "polished_blackstone_brick": "polished_blackstone_bricks",
              "blackstone": "blackstone", "nether_brick": "nether_brick", "mud_brick": "mud_bricks",
              "dark_prismarine": "dark_prismarine", "cut_copper": "cut_copper", "waxed_oxidized_cut_copper": "waxed_oxidized_cut_copper",
              "polished_deepslate": "polished_deepslate", "cobbled_deepslate": "cobbled_deepslate", "tuff_brick": "tuff_bricks",
              "mangrove": "mangrove_planks", "crimson": "crimson_planks", "warped": "warped_planks", "end_stone_brick": "end_stone_bricks",
              "purpur": "purpur_block", "quartz": "quartz_block", "red_nether_brick": "red_nether_brick"}


def put_b(a, x, y, z, b):
    a.set(x, y, z, b() if callable(b) else b)


def fill(a, x1, y1, z1, x2, y2, z2, b):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for z in range(min(z1, z2), max(z1, z2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                a.set(x, y, z, b() if callable(b) else b)


def clear(a, x1, y1, z1, x2, y2, z2):
    fill(a, x1, y1, z1, x2, y2, z2, AIR)


def floor(a, x1, z1, x2, z2, y0, b, depth=1, clear_h=0):
    fill(a, x1, y0 - depth, z1, x2, y0 - 1, z2, b)
    if clear_h:
        clear(a, x1, y0, z1, x2, y0 + clear_h - 1, z2)


# ---------------------------------------------------------------------------- walls
def wall(a, x1, z1, x2, z2, y0, h, pal, walk=False, cren="both", outer=None, slits=True, buttress=0, base=None,
         bar_h=3, foot=0):
    """Solid wall on the footprint x1..x2, z1..z2 (inclusive), from y0 - 1 - foot up to y0 + h - 1.
    walk: the top is a walkway (floor material, feet level y0 + h) with parapets on the long edges.
    cren: 'both' / 'outer' / 'inner' / None - which long edges get merlons. outer: 'north'/'south'/'east'/'west' -
    the outside face; an invisible barrier rises above its parapet so nobody jumps off the outside.
    buttress: spacing of buttresses on the outer face (0 = none)."""
    x1, x2 = min(x1, x2), max(x1, x2)
    z1, z2 = min(z1, z2), max(z1, z2)
    along_x = (x2 - x1) >= (z2 - z1)
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(y0 - 1 - foot, y0 + h):
                a.set(x, y, z, (base or pal.wall)() if callable(base or pal.wall) else (base or pal.wall))
    top = y0 + h - 1
    # trim course every 6 blocks of height and at the top
    for y in list(range(y0 + 5, top, 6)) + [top]:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                edge = x in (x1, x2) or z in (z1, z2)
                if edge:
                    a.set(x, y, z, pal.trim)
    if walk:
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                a.set(x, top, z, pal.floor())
                for y in range(top + 1, top + 4):
                    a.set(x, y, z, AIR)
    if cren:
        edges = []
        if along_x:
            edges = [("north", [(x, z1) for x in range(x1, x2 + 1)]), ("south", [(x, z2) for x in range(x1, x2 + 1)])]
        else:
            edges = [("west", [(x1, z) for z in range(z1, z2 + 1)]), ("east", [(x2, z) for z in range(z1, z2 + 1)])]
        for side, cells in edges:
            if cren == "outer" and side != outer:
                continue
            if cren == "inner" and side == outer:
                continue
            for i, (x, z) in enumerate(cells):
                a.set(x, top + 1, z, pal.wall())
                if (i // 2) % 2 == 0:
                    a.set(x, top + 2, z, pal.wall())
                    a.set(x, top + 3, z, pal.top)
    if outer:
        dx, dz = DIRS[outer]
        cells = []
        if outer in ("north", "south"):
            zz = z1 if outer == "north" else z2
            cells = [(x, zz) for x in range(x1, x2 + 1)]
        else:
            xx = x1 if outer == "west" else x2
            cells = [(xx, z) for z in range(z1, z2 + 1)]
        for (x, z) in cells:
            for y in range(top + 1, top + 1 + bar_h + 2):
                if a.get(x, y, z) == AIR:
                    a.set(x, y, z, B("barrier"))
        # buttresses on the outer face
        if buttress:
            n = len(cells)
            for i in range(2, n - 2, buttress):
                x, z = cells[i]
                for k in range(1, 3):
                    for y in range(y0 - 1, top - 2 * k):
                        for w in (-1, 0, 1):
                            bx, bz = (x + w, z + dz * k) if outer in ("north", "south") else (x + dx * k, z + w)
                            if a.get(bx, y, bz) == AIR:
                                a.set(bx, y, bz, pal.wall())
    if slits:
        cells = [(x, z1) for x in range(x1, x2 + 1)] + [(x, z2) for x in range(x1, x2 + 1)] if along_x else \
            [(x1, z) for z in range(z1, z2 + 1)] + [(x2, z) for z in range(z1, z2 + 1)]
        for i, (x, z) in enumerate(cells):
            if i % 7 == 3 and h > 9:
                for y in range(y0 + 4, y0 + 6):
                    a.set(x, y, z, B("polished_blackstone") if pal.trim_name.startswith("polished_black") else B("deepslate_tiles"))
    return top + 1                                              # feet level on the walkway


def gate(a, cx, cz, y0, axis, w, h, depth, pal, arch=True, portcullis=False, frame=True):
    """Opening of width w (odd) and height h through a wall; axis = direction the passage runs ('x' or 'z').
    depth: number of blocks of wall to cut through, centred on (cx, cz)."""
    half = w // 2
    d0 = -(depth // 2)
    for t in range(d0, d0 + depth):
        for s in range(-half, half + 1):
            x, z = (cx + t, cz + s) if axis == "x" else (cx + s, cz + t)
            a.set(x, y0 - 1, z, pal.floor())
            for y in range(y0, y0 + h):
                a.set(x, y, z, AIR)
            if arch:
                # rounded top: lower the corners with upside-down stairs
                if abs(s) == half:
                    sd = ("south" if s > 0 else "north") if axis == "x" else ("east" if s > 0 else "west")
                    a.set(x, y0 + h - 1, z, stair(pal.roof_stairs, OPP[sd], upside=True))
        if frame:
            for s in (-half - 1, half + 1):
                x, z = (cx + t, cz + s) if axis == "x" else (cx + s, cz + t)
                for y in range(y0, y0 + h):
                    if a.get(x, y, z) != AIR:
                        a.set(x, y, z, pal.trim)
    if frame:
        for t in (d0, d0 + depth - 1):
            for s in range(-half - 1, half + 2):
                x, z = (cx + t, cz + s) if axis == "x" else (cx + s, cz + t)
                if a.get(x, y0 + h, z) != AIR:
                    a.set(x, y0 + h, z, pal.accent)
    if portcullis:
        t = d0 + depth // 2
        for s in range(-half, half + 1):
            x, z = (cx + t, cz + s) if axis == "x" else (cx + s, cz + t)
            a.set(x, y0 + h - 1, z, B("iron_bars"))
            a.set(x, y0 + h - 2, z, B("iron_bars") if s % 2 == 0 else AIR)


# ---------------------------------------------------------------------------- towers
def tower(a, cx, cz, y0, h, r, pal, shape="round", roof="cone", roof_h=None, foot=6, windows=True, cren=True, flag=None):
    """Closed tower shell with a pointed roof (cone / pyramid) or a crenellated flat top. Interior is empty."""
    rr = r + 0.45
    top = y0 + h

    def inside(dx, dz, rad):
        return math.hypot(dx, dz) <= rad if shape == "round" else max(abs(dx), abs(dz)) <= rad

    R = int(r) + 2
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            if not inside(dx, dz, rr):
                continue
            shell = not inside(dx, dz, rr - 2)
            for y in range(y0 - 1 - foot, top):
                if shell or y < y0:
                    a.set(cx + dx, y, cz + dz, pal.wall())
                else:
                    a.set(cx + dx, y, cz + dz, AIR)
            # corbelled ring under the top
            if not inside(dx, dz, rr - 1):
                a.set(cx + dx, top - 1, cz + dz, pal.trim)
    for y in range(y0 + 6, top - 2, 7):
        for dx in range(-R, R + 1):
            for dz in range(-R, R + 1):
                if inside(dx, dz, rr) and not inside(dx, dz, rr - 1):
                    a.set(cx + dx, y, cz + dz, pal.trim)
    if windows:
        for y in range(y0 + 8, top - 4, 8):
            for (dx, dz) in ((r, 0), (-r, 0), (0, r), (0, -r)):
                ix, iz = int(round(dx)), int(round(dz))
                for yy in (y, y + 1):
                    a.set(cx + ix, yy, cz + iz, pal.window)
                a.set(cx + ix, y + 2, cz + iz, pal.trim)
    if roof in ("cone", "pyramid"):
        rh = roof_h or int(r * 2.2) + 3
        rb = r + 1.4
        for k in range(rh):
            rad = rb * (1 - k / rh)
            for dx in range(-R - 1, R + 2):
                for dz in range(-R - 1, R + 2):
                    if shape == "round":
                        d = math.hypot(dx, dz)
                        ok = d <= rad + 0.3 and d > rad - 1.4
                    else:
                        d = max(abs(dx), abs(dz))
                        ok = d <= rad + 0.3 and d > rad - 1.2
                    if ok or (k == rh - 1 and d <= rad + 0.3):
                        a.set(cx + dx, top + k, cz + dz, pal.roof_block)
            if rad < 0.8:
                break
        a.set(cx, top + rh, cz, B("lightning_rod") if flag is None else B(flag))
        a.set(cx, top + rh + 1, cz, B("chain"))
    elif cren:
        for dx in range(-R, R + 1):
            for dz in range(-R, R + 1):
                if inside(dx, dz, rr) and not inside(dx, dz, rr - 1):
                    a.set(cx + dx, top, cz + dz, pal.wall())
                    if (dx + dz) % 2 == 0:
                        a.set(cx + dx, top + 1, cz + dz, pal.top)
                elif inside(dx, dz, rr - 1):
                    a.set(cx + dx, top - 1, cz + dz, pal.floor())
    return top


# ---------------------------------------------------------------------------- halls and roofs
def gable_roof(a, x1, z1, x2, z2, y, axis, pal, overhang=1, end_fill=None):
    """Pitched roof over the rectangle; ridge runs along `axis`. y = height of the eaves (first roof row)."""
    if axis == "z":
        lo, hi = x1 - overhang, x2 + overhang
        span = hi - lo
        for i in range(span + 1):
            x = lo + i
            k = min(i, span - i)
            yy = y + k
            for z in range(z1 - overhang, z2 + overhang + 1):
                if i * 2 == span:
                    a.set(x, yy, z, pal.roof_block)
                else:
                    a.set(x, yy, z, stair(pal.roof_stairs, "east" if i < span - i else "west"))
            # gable ends
            for z in (z1, z2):
                for t in range(y, yy):
                    if x1 <= x <= x2:
                        a.set(x, t, z, (end_fill or pal.wall)())
    else:
        lo, hi = z1 - overhang, z2 + overhang
        span = hi - lo
        for i in range(span + 1):
            z = lo + i
            k = min(i, span - i)
            yy = y + k
            for x in range(x1 - overhang, x2 + overhang + 1):
                if i * 2 == span:
                    a.set(x, yy, z, pal.roof_block)
                else:
                    a.set(x, yy, z, stair(pal.roof_stairs, "south" if i < span - i else "north"))
            for x in (x1, x2):
                for t in range(y, yy):
                    if z1 <= z <= z2:
                        a.set(x, t, z, (end_fill or pal.wall)())


def hall(a, x1, z1, x2, z2, y0, h, pal, roof="gable", axis=None, doors=(), windows=True, pillars=0, lights=True,
         floor_mix=None, roof_y=None, foot=4, flat_ceiling=False):
    """Rectangular building: walls 1 thick with pilasters, floor, optional interior pillar rows, gable or flat roof.
    doors: [(side, offset_from_centre, width, height)]; side = 'north'/'south'/'east'/'west'."""
    x1, x2 = min(x1, x2), max(x1, x2)
    z1, z2 = min(z1, z2), max(z1, z2)
    axis = axis or ("z" if (z2 - z1) >= (x2 - x1) else "x")
    top = y0 + h
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            for y in range(y0 - 1 - foot, y0):
                a.set(x, y, z, pal.wall())
            a.set(x, y0 - 1, z, (floor_mix or pal.floor)())
            for y in range(y0, top):
                a.set(x, y, z, pal.wall() if edge else AIR)
            a.set(x, top, z, pal.trim if edge else (pal.plank if flat_ceiling else AIR))
    # pilasters every 4 along the long walls, trim band
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if (x in (x1, x2) and (z - z1) % 4 == 0) or (z in (z1, z2) and (x - x1) % 4 == 0):
                for y in range(y0, top):
                    a.set(x, y, z, pal.pillar)
    if windows:
        for (xa, za, xb, zb) in ((x1, z1, x2, z1), (x1, z2, x2, z2), (x1, z1, x1, z2), (x2, z1, x2, z2)):
            cells = [(x, za) for x in range(xa, xb + 1)] if za == zb else [(xa, z) for z in range(za, zb + 1)]
            for i, (x, z) in enumerate(cells):
                if i % 4 == 2 and 2 <= i <= len(cells) - 3:
                    for y in range(y0 + 3, min(top - 1, y0 + 3 + max(2, h - 6))):
                        a.set(x, y, z, pal.window)
    for (side, off, w, dh) in doors:
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        if side in ("north", "south"):
            z = z1 if side == "north" else z2
            gate(a, cx + off, z, y0, "z", w, dh, 1, pal, frame=True)
        else:
            x = x1 if side == "west" else x2
            gate(a, x, cz + off, y0, "x", w, dh, 1, pal, frame=True)
    if pillars:
        if axis == "z":
            for z in range(z1 + 4, z2 - 2, pillars):
                for x in (x1 + 3, x2 - 3):
                    for y in range(y0, top):
                        a.set(x, y, z, pal.pillar)
        else:
            for x in range(x1 + 4, x2 - 2, pillars):
                for z in (z1 + 3, z2 - 3):
                    for y in range(y0, top):
                        a.set(x, y, z, pal.pillar)
    if roof == "gable":
        gable_roof(a, x1, z1, x2, z2, roof_y or top + 1, axis, pal)
    elif roof == "flat":
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                a.set(x, top, z, pal.roof_block)
                edge = x in (x1, x2) or z in (z1, z2)
                if edge:
                    a.set(x, top + 1, z, pal.wall())
                    if (x + z) % 2 == 0:
                        a.set(x, top + 2, z, pal.top)
    if lights:
        cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
        L = (z2 - z1) if axis == "z" else (x2 - x1)
        for t in range(-(L // 2) + 4, L // 2 - 3, 8):
            x, z = (cx, cz + t) if axis == "z" else (cx + t, cz)
            chandelier(a, x, top - 1, z, 3 if h > 8 else 1, pal.light)
    return top


def chandelier(a, x, ytop, z, length, light="lantern", ring=True):
    for i in range(length):
        a.set(x, ytop - i, z, B("chain"))
    y = ytop - length
    a.set(x, y, z, B(light, hanging=1) if "lantern" in light else B(light))
    if ring:
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a.set(x + dx, y, z + dz, B("dark_oak_fence"))
        for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            a.set(x + dx, y, z + dz, B(light, hanging=1) if "lantern" in light else B(light))
            a.set(x + dx, y + 1, z + dz, B("dark_oak_fence"))


def wall_lamp(a, x, y, z, facing, light="lantern"):
    """Lantern on a short bracket sticking out of a wall towards `facing`."""
    dx, dz = DIRS[facing]
    a.set(x + dx, y + 1, z + dz, B("dark_oak_fence"))
    a.set(x + dx, y, z + dz, B(light, hanging=1))


# ---------------------------------------------------------------------------- stairs
def flight(a, x, y0, z, direction, n, width, name, support=None, head=4, side_wall=None, centre=True):
    """Stairs going UP n steps towards `direction` from feet level y0 at (x, z) (the first step is in the cell (x, z)).
    Returns (x, y, z) feet position on the landing after the top step."""
    dx, dz = DIRS[direction]
    nx, nz = -dz, dx
    half = width // 2
    rng = range(-half, width - half) if centre else range(0, width)
    for k in range(n + 1):
        cx, cz = x + dx * k, z + dz * k
        for w in rng:
            xx, zz = cx + nx * w, cz + nz * w
            if k < n:
                a.set(xx, y0 + k, zz, stair(name, direction))
                if support is not None:
                    for y in range(y0 - 1, y0 + k):
                        a.set(xx, y, zz, support() if callable(support) else support)
                for y in range(y0 + k + 1, y0 + k + 1 + head):
                    a.set(xx, y, zz, AIR)
            else:
                for y in range(y0 + n, y0 + n + head):
                    a.set(xx, y, zz, AIR)
        if side_wall is not None:
            for w in (min(rng) - 1, max(rng) + 1):
                xx, zz = cx + nx * w, cz + nz * w
                for y in range(y0 - 1, y0 + min(k, n) + 2):
                    if a.get(xx, y, zz) == AIR:
                        a.set(xx, y, zz, side_wall() if callable(side_wall) else side_wall)
    return (x + dx * n, y0 + n, z + dz * n)


def rail(a, cells, y, block="dark_oak_fence"):
    for (x, z) in cells:
        if a.get(x, y, z) == AIR:
            a.set(x, y, z, B(block))


def barrier_line(a, cells, y1, y2):
    for (x, z) in cells:
        for y in range(y1, y2 + 1):
            if a.get(x, y, z) == AIR:
                a.set(x, y, z, B("barrier"))


# ---------------------------------------------------------------------------- props
def crane(a, x, y, z, facing, h=14, arm=9):
    """Treadwheel dock crane: a timber mast, a jib reaching over the water, a hook on a chain."""
    dx, dz = DIRS[facing]
    for k in range(h):
        a.set(x, y + k, z, B("dark_oak_log", axis="y"))
    for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in range(3):
            a.set(x + ox * (2 - k), y + k, z + oz * (2 - k), B("dark_oak_log", axis="y"))
    ax = "x" if dx else "z"
    for k in range(1, arm + 1):
        a.set(x + dx * k, y + h - 1 + (1 if k > arm // 2 else 0), z + dz * k, B("dark_oak_log", axis=ax))
    for k in range(1, 4):
        a.set(x + dx * k, y + h - 1 - k, z + dz * k, B("dark_oak_fence"))
    hx, hz = x + dx * arm, z + dz * arm
    for k in range(1, 6):
        a.set(hx, y + h - k, hz, B("chain"))
    a.set(hx, y + h - 6, hz, B("anvil"))
    # the wheel beside the mast
    wx, wz = x - dx * 2, z - dz * 2
    for t in range(16):
        ang = t / 16 * 2 * math.pi
        u, v = math.cos(ang) * 3, math.sin(ang) * 3
        px, pz = (wx, wz + int(round(u))) if dx else (wx + int(round(u)), wz)
        a.set(px, y + 3 + int(round(v)), pz, B("spruce_planks"))
    a.set(wx, y + 3, wz, B("dark_oak_log", axis="x" if dx else "z"))


def crate_stack(a, x, y, z, rng, n=4):
    for k in range(n):
        dx, dz = rng.randint(-1, 1), rng.randint(-1, 1)
        yy = y
        while a.get(x + dx, yy, z + dz) != AIR and yy < y + 3:
            yy += 1
        a.set(x + dx, yy, z + dz, B(rng.choice(["barrel", "spruce_planks", "dark_oak_planks"])))
