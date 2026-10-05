"""Reusable building parts for the RPG world: signs, lamps, railings, ender chests, shop kits,
hunting grounds (enclosed arenas with fence-gate airlocks), windowed gateway corridors, paths."""
import math

import numpy as np

from mcw import B, AIR, PAL, sign_be, simple_be, banner_be, physics_tables
from gen_common import stair, slab, line_points

FACE = {"north": 2, "south": 3, "west": 4, "east": 5}
DV = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPP = {"north": "south", "south": "north", "west": "east", "east": "west"}
LEFT = {"north": "west", "west": "south", "south": "east", "east": "north"}
RIGHT = {v: k for k, v in LEFT.items()}
DIR4 = {"south": 0, "west": 1, "north": 2, "east": 3}          # bell / pot / grindstone direction
ROT = {"south": 0, "west": 4, "north": 8, "east": 12}          # standing sign / banner rotation

HUNT_LIGHT = 11              # light level used only inside hunting grounds (toggle functions rely on it)


# --------------------------------------------------------------------------- small props
def wall_sign(a, x, y, z, facing, text, kind="oak_wall_sign", color=-16777216, glow=True):
    """facing = direction the text faces (the sign hangs on the block behind it)."""
    a.set(x, y, z, B(kind, facing_direction=FACE[facing]))
    a.add_be(sign_be(x, y, z, text, glow=glow, color=color))


def hang_sign(a, x, y, z, facing, text, kind="spruce_hanging_sign", color=-1, back=None):
    """Hanging sign under a solid block; facing = direction of the front text (north/south/west/east)."""
    a.set(x, y, z, B(kind, hanging=1, attached_bit=0, facing_direction=FACE[facing]))
    a.add_be(sign_be(x, y, z, text, back if back is not None else text, glow=True, hanging=True, color=color))


def stand_sign(a, x, y, z, facing, text, kind="oak_standing_sign"):
    a.set(x, y, z, B(kind, ground_sign_direction=ROT[facing]))
    a.add_be(sign_be(x, y, z, text, glow=True))


def lamp_post(a, x, y, z, post=None, lamp=None, h=3, cap=None):
    post = post or B("dark_oak_fence")
    for i in range(h):
        a.set(x, y + i, z, post)
    a.set(x, y + h, z, lamp or B("lantern"))
    if cap is not None:
        a.set(x, y + h + 1, z, cap)


def crook_lamp(a, x, y, z, d, post=None, lamp=None, h=4):
    post = post or B("dark_oak_fence")
    dx, dz = DV[d]
    for i in range(h):
        a.set(x, y + i, z, post)
    a.set(x + dx, y + h - 1, z + dz, post)
    a.set(x + dx, y + h - 2, z + dz, lamp or B("lantern", hanging=1))


def hanging_lantern(a, x, ytop, z, chain=1, lamp=None):
    for i in range(chain):
        a.set(x, ytop - i, z, B("chain"))
    a.set(x, ytop - chain, z, lamp or B("lantern", hanging=1))


def ender_chest(W, x, y, z, facing):
    W.a.set(x, y, z, B("ender_chest", cardinal=facing))
    W.a.add_be(simple_be("EnderChest", x, y, z))


def chest(a, x, y, z, facing, kind="chest"):
    from amulet_nbt import ListTag
    a.set(x, y, z, B(kind, cardinal=facing))
    a.add_be(simple_be("Chest", x, y, z, Items=ListTag([])))


def barrel(a, x, y, z, up=True):
    a.set(x, y, z, B("barrel", facing_direction=1 if up else 2))


def banner_wall(a, x, y, z, facing, base, patterns=(), ominous=False):
    a.set(x, y, z, B("wall_banner", facing_direction=FACE[facing]))
    be = banner_be(x, y, z, base, patterns)
    if ominous:
        from amulet_nbt import IntTag
        be["Type"] = IntTag(1)
    a.add_be(be)


def banner_stand(a, x, y, z, facing, base, patterns=(), ominous=False):
    a.set(x, y, z, B("standing_banner", ground_sign_direction=ROT[facing]))
    be = banner_be(x, y, z, base, patterns)
    if ominous:
        from amulet_nbt import IntTag
        be["Type"] = IntTag(1)
    a.add_be(be)


def campfire(a, x, y, z, soul=False, facing="south"):
    a.set(x, y, z, B("soul_campfire" if soul else "campfire", cardinal=facing))
    a.add_be(simple_be("Campfire", x, y, z))


def pot(a, x, y, z, plant=None, **st):
    from mcw import flowerpot_be
    a.set(x, y, z, B("flower_pot"))
    if plant:
        a.add_be(flowerpot_be(x, y, z, plant, **st))
    else:
        a.add_be(simple_be("FlowerPot", x, y, z))


def bell(a, x, y, z, attach="standing", d="south"):
    a.set(x, y, z, B("bell", attachment=attach, direction=DIR4[d]))
    a.add_be(simple_be("Bell", x, y, z))


def fence_line(a, x1, z1, x2, z2, y, block, h=1):
    for (x, _, z) in line_points((x1, 0, z1), (x2, 0, z2), 0.5):
        for i in range(h):
            a.set(x, y + i, z, block)


def railing_auto(W, box, y1, y2, block, drop=3, only_air=True, skip=None):
    """Put a railing block on every standable edge cell that overlooks a drop deeper than `drop`.
    The railing goes on the floor cell itself (feet level) so nothing floats."""
    a = W.a
    htab, liq, _ = physics_tables()
    x1, z1, x2, z2 = box
    sl = (slice(x1 - a.x0 - 1, x2 - a.x0 + 2), slice(y1 - a.y0 - 1, y2 - a.y0 + 3), slice(z1 - a.z0 - 1, z2 - a.z0 + 2))
    blk = a.blk[sl]
    Hh = htab[blk]
    L = liq[blk]
    nx, ny, nz = blk.shape
    placed = 0
    for i in range(1, nx - 1):
        for k in range(1, nz - 1):
            for j in range(1, ny - 2):
                if not (Hh[i, j - 1, k] == 2 and Hh[i, j, k] == 0 and Hh[i, j + 1, k] == 0 and not L[i, j, k]):
                    continue
                edge = False
                for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ii, kk = i + di, k + dk
                    if Hh[ii, j, kk] != 0 or Hh[ii, j + 1, kk] != 0:
                        continue
                    # how far down is the next floor in the neighbour column?
                    t = j - 1
                    while t >= 0 and Hh[ii, t, kk] == 0 and not L[ii, t, kk]:
                        t -= 1
                    if t < 0 or (j - 1 - t) > drop:
                        if t >= 0 and L[ii, t, kk]:
                            continue
                        edge = True
                        break
                if edge:
                    x, y, z = i + x1 - 1, j + y1 - 1, k + z1 - 1
                    if skip is not None and skip(x, y, z):
                        continue
                    if not only_air or a.get(x, y, z) == AIR:
                        a.set(x, y, z, block)
                        placed += 1
    return placed


def light_grid(W, x1, z1, x2, z2, y, level=HUNT_LIGHT, spacing=5, offset=2):
    """Invisible light blocks on a grid at height y (only into air). Returns positions."""
    lb = B("light_block_%d" % level)
    out = []
    for x in range(x1 + offset, x2 + 1, spacing):
        for z in range(z1 + offset, z2 + 1, spacing):
            if W.a.get(x, y, z) == AIR:
                W.a.set(x, y, z, lb)
                out.append((x, y, z))
    return out


# --------------------------------------------------------------------------- shop kit
def shop_kit(W, region, name, x, y, z, facing, counter=None, top=None, chests=2, chest_side="right",
             ender_wall=None, deco=None, sign_kind="oak_wall_sign"):
    """Counter facing `facing` (customers stand on that side), merchant spot behind it, ender chests.
    (x, y, z) = centre of the counter at feet level y. Returns the record stored in W.shops."""
    a = W.a
    dx, dz = DV[facing]
    lx, lz = DV[LEFT[facing]]
    counter = counter or B("spruce_planks")
    top = top or B("spruce_slab", half="top")
    for t in (-2, -1, 0, 1, 2):
        cx, cz = x + lx * t, z + lz * t
        a.set(cx, y, cz, counter)
    # counter top display: a few props on the slab-topped ends
    a.set(x + lx * -2, y + 1, z + lz * -2, B("lantern"))
    npc = (x - dx * 2, y, z - dz * 2)
    a.set(npc[0], y - 1, npc[2], B("lodestone"))       # marker under the merchant spot
    # ender chests in a row on the customer side, to the right of the counter
    side = RIGHT[facing] if chest_side == "right" else LEFT[facing]
    sx, sz = DV[side]
    ends = []
    if ender_wall is None:
        base = (x + sx * 4 + dx * 1, z + sz * 4 + dz * 1)
        for i in range(chests):
            ex, ez = base[0] + sx * i, base[1] + sz * i
            ender_chest(W, ex, y, ez, facing)
            ends.append((ex, y, ez))
    else:
        for (ex, ey, ez, f) in ender_wall:
            ender_chest(W, ex, ey, ez, f)
            ends.append((ex, ey, ez))
    rec = dict(region=region, name=name, npc=npc, counter=(x, y, z), facing=facing, ender_chests=ends)
    W.shops.append(rec)
    return rec


# --------------------------------------------------------------------------- hunting grounds
def gate_airlock(W, x, y, z, facing, gate, frame, depth=3, width=2, roof=None, sign=None, sign_kind="oak_wall_sign"):
    """2-wide vestibule leaving the arena wall toward `facing` with a fence gate at both ends.
    (x, z) = left inner corner cell of the opening in the wall line; y = floor (top block) level."""
    a = W.a
    dx, dz = DV[facing]
    lx, lz = DV[RIGHT[facing]]
    for d in range(0, depth + 1):
        for w in range(-1, width + 1):
            cx, cz = x + dx * d + lx * w, z + dz * d + lz * w
            side = w in (-1, width)
            for yy in range(y + 1, y + 5):
                if side:
                    a.set(cx, yy, cz, frame)
                else:
                    a.set(cx, yy, cz, AIR)
            a.set(cx, y + 4, cz, roof or frame)
            if not side:
                a.set(cx, y, cz, frame if a.get(cx, y, cz) == AIR else a.get(cx, y, cz))
        if d in (0, depth):
            for w in range(width):
                cx, cz = x + dx * d + lx * w, z + dz * d + lz * w
                a.set(cx, y + 1, cz, B(gate, cardinal=facing if facing in ("north", "south") else facing))
                a.set(cx, y + 2, cz, AIR)
                a.set(cx, y + 3, cz, frame)
    if sign:
        # sign on the outer face above the gate
        cx, cz = x + dx * (depth + 1), z + dz * (depth + 1)
        mx, mz = cx + lx * 0, cz + lz * 0
        a.set(x + dx * depth, y + 3, z + dz * depth, frame)
        wall_sign(a, mx, y + 3, mz, facing, sign, kind=sign_kind)
        wall_sign(a, mx + lx, y + 3, mz + lz, facing, sign, kind=sign_kind)
    return (x + dx * (depth + 1), y + 1, z + dz * (depth + 1))


def hunting_ground(W, region, name, x1, z1, x2, z2, y, floor, wall, gates, wall_h=6, overhang=True,
                   roof=None, roof_h=None, pillar=None, cap=None, gate_block="spruce_fence_gate",
                   frame=None, spawn_n=6, light_y=None, props=None, sign_kind="oak_wall_sign", inner=None):
    """Enclosed arena.  floor(x, z) -> block id;  wall = block id (or fn(x, y, z));
    gates = [(side, offset)] 2-wide airlocks in the wall (side north/south/west/east, offset along wall from x1/z1).
    The interior (x1..x2, z1..z2) is flat at top-block level y.  Returns the record stored in W.hunts."""
    a = W.a
    wf = wall if callable(wall) else (lambda xx, yy, zz: wall)
    roof_h = roof_h or wall_h
    for x in range(x1 - 1, x2 + 2):
        for z in range(z1 - 1, z2 + 2):
            ring = x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)
            for yy in range(y - 3, y + 1):
                a.set(x, yy, z, floor(x, z) if not ring else wf(x, yy, z))
            top = y + (roof_h if roof is not None else wall_h)
            for yy in range(y + 1, top + 1):
                a.set(x, yy, z, wf(x, yy, z) if ring else AIR)
            if roof is not None:
                a.set(x, y + roof_h + 1, z, roof)
            elif ring and cap is not None:
                a.set(x, y + wall_h + 1, z, cap)
    if pillar is not None:
        for (px, pz) in ((x1 - 1, z1 - 1), (x2 + 1, z1 - 1), (x1 - 1, z2 + 1), (x2 + 1, z2 + 1)):
            for yy in range(y + 1, y + wall_h + 2):
                a.set(px, yy, pz, pillar)
    if overhang and roof is None:
        # inward lip so spiders cannot climb out
        lip = cap if cap is not None else (wall if not callable(wall) else wf(x1, y + wall_h, z1))
        for x in range(x1, x2 + 1):
            a.set(x, y + wall_h, z1, lip); a.set(x, y + wall_h, z2, lip)
        for z in range(z1, z2 + 1):
            a.set(x1, y + wall_h, z, lip); a.set(x2, y + wall_h, z, lip)
    entries = []
    frame = frame or (wall if not callable(wall) else wf(x1 - 1, y + 1, z1 - 1))
    for side, off in gates:
        if side == "north":
            gx, gz, f = x1 + off, z1 - 1, "north"
        elif side == "south":
            gx, gz, f = x1 + off, z2 + 1, "south"
        elif side == "west":
            gx, gz, f = x1 - 1, z1 + off, "west"
        else:
            gx, gz, f = x2 + 1, z1 + off, "east"
        # left-inner corner for the airlock: walk so the 2-wide opening spans off, off+1
        lx, lz = DV[RIGHT[f]]
        if lx < 0 or lz < 0:
            gx, gz = gx + 1 if lx < 0 else gx, gz + 1 if lz < 0 else gz
        out = gate_airlock(W, gx, y, gz, f, gate_block, frame, sign="§l§c⚔ 사냥터 ⚔\n§r" + name,
                           sign_kind=sign_kind)
        entries.append(out)
    inner_box = (x1, z1, x2, z2)
    if props:
        props(inner_box)
    # spawn points: spread on a grid, kept clear of props
    pts = []
    cols = max(2, int(round(math.sqrt(spawn_n * (x2 - x1) / max(1, (z2 - z1))))))
    rows = max(2, int(math.ceil(spawn_n / cols)))
    for r in range(rows):
        for c in range(cols):
            if len(pts) >= spawn_n:
                break
            px = int(round(x1 + 3 + (x2 - x1 - 6) * (c + 0.5) / cols))
            pz = int(round(z1 + 3 + (z2 - z1 - 6) * (r + 0.5) / rows))
            for dd in range(0, 4):
                if a.get(px + dd, y + 1, pz) == AIR and a.get(px + dd, y + 2, pz) == AIR:
                    px += dd
                    break
            pts.append((px, y + 1, pz))
    ly = light_y if light_y is not None else y + 4
    lights = light_grid(W, x1, z1, x2, z2, ly, spacing=5, offset=2)
    rec = dict(region=region, name=name, box=(x1, y + 1, z1, x2, y + (roof_h if roof is not None else wall_h), z2),
               floor_y=y, entrances=entries, spawn_points=pts, lights=lights, roofed=roof is not None)
    W.hunts.append(rec)
    W.allow("hunt:" + name, x1 - 6, y - 2, z1 - 6, x2 + 6, y + wall_h + 2, z2 + 6)
    return rec


def register_hunt(W, region, name, box, floor_y, entrances, spawn_points, lights, roofed=True):
    rec = dict(region=region, name=name, box=box, floor_y=floor_y, entrances=entries_list(entrances),
               spawn_points=spawn_points, lights=lights, roofed=roofed)
    W.hunts.append(rec)
    return rec


def entries_list(e):
    return [tuple(int(v) for v in p) for p in e]


# --------------------------------------------------------------------------- gateway corridors
def corridor(W, cells, floor_y, width=5, height=5, wall=None, floor=None, roof=None, window=None,
             window_side=None, window_every=3, window_rows=(2, 3), pillar=None, lamp=None, lamp_every=6,
             carve=True, foundation=None, carpet=None):
    """Straight corridor along a list of centre cells [(x, z), ...] with direction changes allowed.
    floor_y: int or list (per cell); window_side: 'left'/'right'/'both' relative to the walking direction.
    Builds floor, walls, roof; stained-glass windows let you see out (the next region)."""
    a = W.a
    wall = wall or B("stone_bricks")
    floor = floor or B("polished_andesite")
    roof = roof or wall
    hw = width // 2
    n = len(cells)
    fys = floor_y if isinstance(floor_y, (list, tuple)) else [floor_y] * n
    for idx, (x, z) in enumerate(cells):
        nx_, nz_ = cells[min(idx + 1, n - 1)]
        px_, pz_ = cells[max(idx - 1, 0)]
        dx, dz = (nx_ - px_), (nz_ - pz_)
        if abs(dx) >= abs(dz):
            d = "east" if dx > 0 else "west"
        else:
            d = "south" if dz > 0 else "north"
        lx, lz = DV[LEFT[d]]
        fy = fys[idx]
        for w in range(-hw - 1, hw + 2):
            cx, cz = x + lx * w, z + lz * w
            side = abs(w) == hw + 1
            if foundation is not None:
                yy = fy - 1
                while yy > fy - 40 and a.get(cx, yy, cz) == AIR:
                    a.set(cx, yy, cz, foundation)
                    yy -= 1
            a.set(cx, fy, cz, wall if side else floor)
            for yy in range(fy + 1, fy + height + 1):
                if side:
                    win = False
                    if window is not None and (yy - fy) in window_rows and idx % window_every != 0:
                        # positive w lies on the LEFT of the walking direction
                        if window_side == "both" or (window_side == "left" and w > 0) or (window_side == "right" and w < 0):
                            win = True
                    a.set(cx, yy, cz, window if win else (pillar if (pillar is not None and idx % window_every == 0) else wall))
                else:
                    a.set(cx, yy, cz, AIR)
            a.set(cx, fy + height + 1, cz, roof)
            if carpet is not None and not side and abs(w) <= hw - 1:
                a.set(cx, fy + 1, cz, carpet)
        if lamp is not None and idx % lamp_every == lamp_every // 2:
            a.set(x, fy + height, z, lamp)


def run_cells(x, z, d, n):
    dx, dz = DV[d]
    return [(x + dx * i, z + dz * i) for i in range(n)]


def stair_cells(start_y, n, rise_every=1, up=True):
    """floor heights for a ramp of n cells rising/falling by one every `rise_every` cells."""
    return [start_y + (i // rise_every) * (1 if up else -1) for i in range(n)]


def place_stairs(W, cells, fys, block_name, width=5):
    """Put stair blocks on cells where the floor rises by one compared to the previous cell."""
    a = W.a
    hw = width // 2
    for i in range(1, len(cells)):
        if fys[i] == fys[i - 1]:
            continue
        x, z = cells[i]
        px, pz = cells[i - 1]
        dx, dz = x - px, z - pz
        if dx > 0: d = "east"
        elif dx < 0: d = "west"
        elif dz > 0: d = "south"
        else: d = "north"
        lx, lz = DV[LEFT[d]]
        if fys[i] > fys[i - 1]:
            # rising toward d: stair on the lower cell? place at the new cell's lower level
            for w in range(-hw, hw + 1):
                a.set(px + lx * w, fys[i - 1] + 1, pz + lz * w, stair(block_name, d))
        else:
            back = OPP[d]
            for w in range(-hw, hw + 1):
                a.set(x + lx * w, fys[i] + 1, z + lz * w, stair(block_name, back))


# --------------------------------------------------------------------------- surface paths
def paint_path(W, pts, width, blocks, rng, lamp_every=0, lamp=None, edge=None):
    """Repaint the top block along a polyline of (x, z) (terrain must already be painted)."""
    a = W.a
    cells = set()
    for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
        for (x, _, z) in line_points((ax, 0, az), (bx, 0, bz), 0.5):
            for ox in range(-width, width + 1):
                for oz in range(-width, width + 1):
                    if ox * ox + oz * oz <= (width + 0.3) ** 2:
                        cells.add((x + ox, z + oz))
    for (x, z) in cells:
        y = W.gy(x, z)
        if a.get(x, y, z) in (B("grass_block"), B("dirt"), B("sand"), B("coarse_dirt"), B("podzol"), B("blackstone")):
            a.set(x, y, z, rng.choice(blocks))
            for k in (1, 2):
                if a.get(x, y + k, z) in (B("short_grass"), B("tall_grass", upper_block_bit=0),
                                         B("tall_grass", upper_block_bit=1)):
                    a.set(x, y + k, z, AIR)
        W.reserved[x - W.a.x0, z - W.a.z0] = True
    return cells


def gatehouse(W, cx, cz, facing, fy, glass, wall=None, pillar=None, roof_stairs="spruce_stairs", roof_ridge=None,
              floor=None, next_name="", prev_name="", width=11, depth=9, h=6, sign_kind="spruce_wall_sign",
              foundation=None, gable=None, door_w=3):
    """Gate building on a road running along `facing` (toward the next region), centred on (cx, cz).
    The far wall is a stained-glass window wall around the doorway: walking through the gate you see
    the next region through coloured glass.  Side walls get coloured windows too."""
    a = W.a
    wall = wall or B("stone_bricks")
    pillar = pillar or B("spruce_log")
    floor = floor or B("polished_andesite")
    gable = gable or wall
    roof_ridge = roof_ridge or B("spruce_slab")
    foundation = foundation or wall
    pane = B(glass + "_stained_glass_pane")
    dx, dz = DV[facing]
    lx, lz = DV[LEFT[facing]]
    hw, hd = width // 2, depth // 2
    dh = door_w // 2

    def P(t, w):
        return cx + dx * t + lx * w, cz + dz * t + lz * w

    for t in range(-hd, hd + 1):
        for w in range(-hw, hw + 1):
            x, z = P(t, w)
            yy = fy - 1
            while yy > fy - 30 and a.get(x, yy, z) == AIR:
                a.set(x, yy, z, foundation)
                yy -= 1
            a.set(x, fy, z, floor)
            side = abs(w) == hw
            end = abs(t) == hd
            for k in range(1, h + 1):
                y = fy + k
                b = AIR
                if side and end:
                    b = pillar
                elif end and t == hd:                       # window wall toward the next region
                    if abs(w) <= dh:
                        b = AIR if k <= 4 else wall
                    else:
                        b = pane if k <= h - 1 else wall
                elif end:                                   # entrance wall
                    if abs(w) <= dh:
                        b = AIR if k <= 4 else wall
                    else:
                        b = pane if 2 <= k <= 4 else wall
                elif side:
                    if t == 0:
                        b = pillar
                    else:
                        b = pane if 2 <= k <= 4 else wall
                a.set(x, y, z, b)
    # roof (ridge along the road)
    x1, z1 = P(-hd, -hw)
    x2, z2 = P(hd, hw)
    xa, xb = sorted((x1, x2)); za, zb = sorted((z1, z2))
    from rpg_build import gable_roof
    gable_roof(a, xa, za, xb, zb, fy + h + 1, roof_stairs, roof_ridge, gable,
               axis="x" if facing in ("east", "west") else "z")
    # signs
    sx, sz = P(hd - 1, 0)
    wall_sign(a, sx, fy + 5, sz, OPP[facing], "§l다음 지역\n§r" + next_name, kind=sign_kind)
    ox, oz = P(-hd - 1, 0)
    wall_sign(a, ox, fy + 5, oz, OPP[facing], "§l" + next_name + "\n§r↑ 이쪽으로", kind=sign_kind)
    if prev_name:
        bx, bz = P(hd + 1, 0)
        wall_sign(a, bx, fy + 5, bz, facing, "§l" + prev_name + "\n§r↑ 돌아가기", kind=sign_kind)
    mx, mz = P(0, 0)
    hanging_lantern(a, mx, fy + h, mz, chain=1)
    W.gates.append(dict(next=next_name, prev=prev_name, pos=(cx, fy + 1, cz), facing=facing, glass=glass))
    W.reserved[W.rect(min(x1, x2) - 1, min(z1, z2) - 1, max(x1, x2) + 1, max(z1, z2) + 1)] = True


def path_steps(W, cells, stairs_name):
    """Smooth the 1-block terrain steps of a painted path with stair blocks."""
    a = W.a
    for (x, z) in cells:
        y = W.gy(x, z)
        if a.get(x, y + 1, z) != AIR:
            continue
        for d, (ddx, ddz) in DV.items():
            if (x + ddx, z + ddz) not in cells:
                continue
            ny = W.gy(x + ddx, z + ddz)
            back = W.gy(x - ddx, z - ddz)
            if ny == y + 1 and back <= y and a.get(x + ddx, ny + 1, z + ddz) == AIR:
                a.set(x, y + 1, z, stair(stairs_name, d))
                break


def tube(W, waypoints, width=3, height=3, shell=None, floor=None, accent=None, accent_every=3, ring=None,
         ring_every=9, lamp=None, lamp_every=5, stairs="prismarine_stairs", pillar=None, ends_open=(True, False),
         flat_ends=None):
    """Watertight corridor along axis-aligned waypoints [(x, z, floor_y), ...].
    Floors slope linearly between waypoints (kept flat near both ends of each leg so corners line up).
    All shells are placed before any interior is carved, so corners and joints are sealed."""
    a = W.a
    shell = shell or B("glass")
    floor = floor or B("prismarine_bricks")
    hw = width // 2
    flat_ends = hw + 2 if flat_ends is None else flat_ends
    legs = []
    nleg = len(waypoints) - 1
    for li, ((x0, z0, f0), (x1, z1, f1)) in enumerate(zip(waypoints[:-1], waypoints[1:])):
        assert x0 == x1 or z0 == z1, "tube legs must be axis aligned"
        if x1 > x0: d = "east"
        elif x1 < x0: d = "west"
        elif z1 > z0: d = "south"
        else: d = "north"
        n = abs(x1 - x0) + abs(z1 - z0)
        dx, dz = DV[d]
        cells = []
        span = max(1, n - 2 * flat_ends)
        # interiors reach hw past a corner, shells hw+1 (they cap the other leg); free ends stop at the waypoint
        lo_s = 0 if li == 0 else -hw - 1
        hi_s = n if li == nleg - 1 else n + hw + 1
        lo_i = 0 if li == 0 else -hw
        hi_i = n if li == nleg - 1 else n + hw
        for i in range(lo_s, hi_s + 1):
            t = min(max(i - flat_ends, 0), span) / span
            fy = int(round(f0 + (f1 - f0) * t))
            cells.append((x0 + dx * i, z0 + dz * i, fy, d, i, lo_i <= i <= hi_i))
        legs.append(cells)
    allc = [c for leg in legs for c in leg]
    # pass 1: shells
    for (x, z, fy, d, i, inner) in allc:
        lx, lz = DV[LEFT[d]]
        ringed = ring is not None and i % ring_every == 0
        acc = accent is not None and i % accent_every == 0
        for w in range(-hw - 1, hw + 2):
            cx, cz = x + lx * w, z + lz * w
            for y in range(fy, fy + height + 2):
                side = abs(w) == hw + 1 or y in (fy, fy + height + 1)
                if not side:
                    continue
                b = ring if ringed else (accent if acc and y > fy else shell)
                if y == fy:
                    b = ring if ringed else floor
                a.set(cx, y, cz, b)
            if pillar is not None and abs(w) == hw + 1 and i % 6 == 0:
                yy = fy - 1
                while yy > 1 and a.get(cx, yy, cz) in (AIR, B("water")):
                    a.set(cx, yy, cz, pillar)
                    yy -= 1
    # pass 2: interiors
    for (x, z, fy, d, i, inner) in allc:
        if not inner:
            continue
        lx, lz = DV[LEFT[d]]
        for w in range(-hw, hw + 1):
            cx, cz = x + lx * w, z + lz * w
            for y in range(fy + 1, fy + height + 1):
                if a.get(cx, y, cz) != AIR or a.wet[cx - a.x0, y - a.y0, cz - a.z0]:
                    a.set(cx, y, cz, AIR)
            if lamp is not None and w == 0 and i % lamp_every == 0:
                a.set(cx, fy, cz, lamp)
    # pass 3: stairs where the floor drops along a leg
    for leg in legs:
        for (p, q) in zip(leg[:-1], leg[1:]):
            if not (p[5] and q[5]):
                continue
            if q[2] < p[2]:
                x, z, fy, d, i, _ = q
                lx, lz = DV[LEFT[d]]
                for w in range(-hw, hw + 1):
                    a.set(x + lx * w, fy + 1, z + lz * w, stair(stairs, OPP[d]))
            elif q[2] > p[2]:
                x, z, fy, d, i, _ = p
                lx, lz = DV[LEFT[d]]
                for w in range(-hw, hw + 1):
                    a.set(x + lx * w, fy + 1, z + lz * w, stair(stairs, d))
    return legs


def leak_check(W, box, liquids=("water", "lava")):
    """Liquid source blocks that could flow: a horizontal neighbour or the block below is air
    (or another non-solid, non-liquid block).  Returns a list of positions."""
    from mcw import PAL, physics_tables
    a = W.a
    htab, liq, _ = physics_tables()
    x1, y1, z1, x2, y2, z2 = box
    sl = (slice(x1 - a.x0, x2 - a.x0 + 1), slice(y1 - a.y0, y2 - a.y0 + 1), slice(z1 - a.z0, z2 - a.z0 + 1))
    blk = a.blk[sl]
    wet = a.wet[sl]
    lid = np.array([PAL.names[i] in liquids for i in range(len(PAL.names))] + [False] * (len(htab) - len(PAL.names)))
    L = lid[blk]
    open_ = (htab[blk] < 2) & ~liq[blk] & ~wet
    # waterloggable-ish things (stairs, slabs, fences ...) count as solid enough here
    out = []
    pos = np.argwhere(L)
    nx, ny, nz = blk.shape
    for (i, j, k) in pos:
        for (di, dj, dk) in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0)):
            ii, jj, kk = i + di, j + dj, k + dk
            if 0 <= ii < nx and 0 <= jj < ny and 0 <= kk < nz and open_[ii, jj, kk]:
                out.append((i + x1, j + y1, k + z1))
                break
    return out
