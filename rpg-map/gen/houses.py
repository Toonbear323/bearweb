"""Timber-framed town buildings: parametric shell + interiors."""
from . import blocks as bl
from . import kit
from .core import B, Mix

AIR = 0


def _base_mix():
    return Mix((bl.block("stone_brick"), 6), (bl.block("cobblestone"), 3), (bl.block("andesite"), 2),
               (bl.block("mossy_stone_brick"), 1), (B("stonebrick", stone_brick_type="cracked"), 1))


def palette(name):
    base = _base_mix()
    P = {
        "spruce": dict(base=base, frame="spruce", plaster=B("calcite"), roof="dark_oak", trim="spruce",
                       floor="spruce", door="spruce", accent="spruce", glass=B("glass_pane")),
        "dark": dict(base=base, frame="dark_oak", plaster=B("white_terracotta"), roof="deepslate_tile",
                     trim="cobbled_deepslate", floor="oak", door="dark_oak", accent="dark_oak", glass=B("glass_pane")),
        "brick": dict(base=Mix((bl.block("brick"), 6), (bl.block("granite"), 1), (bl.block("stone_brick"), 1)),
                      frame="dark_oak", plaster=B("calcite"), roof="brick", trim="stone_brick", floor="spruce",
                      door="dark_oak", accent="spruce", glass=B("glass_pane")),
        "oak": dict(base=base, frame="oak", plaster=bl.block("diorite"), roof="spruce", trim="cobblestone",
                    floor="oak", door="oak", accent="oak", glass=B("glass_pane")),
        "red": dict(base=base, frame="spruce", plaster=B("calcite"), roof="mangrove", trim="dark_oak",
                    floor="spruce", door="mangrove", accent="mangrove", glass=B("glass_pane")),
        "moss": dict(base=Mix((bl.block("mossy_cobblestone"), 4), (bl.block("cobblestone"), 4),
                              (bl.block("mossy_stone_brick"), 3), (bl.block("stone_brick"), 2)),
                     frame="oak", plaster=B("white_terracotta"), roof="mud_brick", trim="spruce", floor="oak",
                     door="spruce", accent="spruce", glass=B("glass_pane")),
        "purple": dict(base=Mix((bl.block("polished_deepslate"), 2), (bl.block("deepslate_brick"), 5),
                                (bl.block("cobbled_deepslate"), 2), (bl.block("deepslate_tile"), 1)),
                       frame="dark_oak", plaster=B("calcite"), roof="purpur", trim="deepslate_tile", floor="dark_oak",
                       door="dark_oak", accent="crimson", glass=B("purple_stained_glass_pane")),
        "copper": dict(base=base, frame="dark_oak", plaster=B("calcite"), roof="waxed_oxidized_cut_copper",
                       trim="deepslate_tile", floor="dark_oak", door="dark_oak", accent="dark_oak",
                       glass=B("glass_pane")),
        "cherry": dict(base=base, frame="cherry", plaster=B("calcite"), roof="cherry", trim="spruce", floor="cherry",
                       door="cherry", accent="cherry", glass=B("pink_stained_glass_pane")),
    }
    return dict(P[name])


def _posts(n, bay=4):
    """Post positions 0..n-1 splitting the span into roughly `bay` wide bays."""
    k = max(1, round((n - 1) / bay))
    return sorted(set(int(round(i * (n - 1) / k)) for i in range(k + 1)))


def shell(F, W, D, floors=2, pal=None, jetty=True, roof_axis="x", door_x=None, chimney=None, dormer=False,
          ground_stone=True, sign=None, lantern=True, side_windows=True, back_windows=True, front_windows=True,
          flower_box=True, no_window=(), ground_side_windows=True, ground_back_windows=True):
    """Build a timber-frame building shell in frame F.

    Local box x:[0,W-1] z:[0,D-1]; the front is z=D-1 (local south); y=0 is the ground surface.
    Returns a dict describing the interior (floor levels, extents).
    chimney = ('W'|'E', z) external chimney breast on a side wall."""
    rng = F.rng
    pal = pal or palette("spruce")
    base, frame, plaster, roof = pal["base"], pal["frame"], pal["plaster"], pal["roof"]
    H = 4
    fy = [1 + k * (H + 1) for k in range(floors + 1)]      # floor block level of each storey; last = top plate
    top = fy[floors]

    def zf(k):
        return D if (jetty and k >= 1) else D - 1

    # foundation + plinth
    F.fill(0, -3, 0, W - 1, 0, D - 1, base)
    F.fill(0, 1, 0, W - 1, 1, D - 1, base)
    F.fill(1, 1, 1, W - 2, 1, D - 2, bl.planks(pal["floor"]))
    px = _posts(W)
    for k in range(floors):
        z1 = zf(k)
        y0, y1 = fy[k] + 1, fy[k] + H
        wallm = base if (k == 0 and ground_stone) else plaster
        F.fill(0, y0, 0, W - 1, y1, z1, AIR)
        F.walls(0, y0, 0, W - 1, y1, z1, wallm)
        # beam course on top of this storey (also the next floor)
        by = fy[k + 1]
        zb = zf(k + 1) if k + 1 < floors else z1
        F.fill(1, by, 1, W - 2, by, zb - 1, bl.planks(pal["floor"]))
        for x in range(0, W):
            F.log(x, by, 0, frame, "x")
            F.log(x, by, zb, frame, "x")
        for z in range(0, zb + 1):
            F.log(0, by, z, frame, "z")
            F.log(W - 1, by, z, frame, "z")
        if zb > z1:   # jetty brackets + soffit
            for x in px:
                F.stairs(x, by - 1, zb, pal["trim"] if pal["trim"] in bl.WOODS else frame, "N", top=True)
        # posts
        pz = _posts(z1 + 1)
        for x in px:
            for y in range(y0, y1 + 1):
                F.log(x, y, 0, frame)
                F.log(x, y, z1, frame)
        for z in pz:
            for y in range(y0, y1 + 1):
                F.log(0, y, z, frame)
                F.log(W - 1, y, z, frame)
        if k == 0 and ground_stone:
            # stone ground floor: keep only the corner posts as quoins
            for x in px[1:-1]:
                F.fill(x, y0, 0, x, y1, 0, base)
                F.fill(x, y0, z1, x, y1, z1, base)
            for z in pz[1:-1]:
                F.fill(0, y0, z, 0, y1, z, base)
                F.fill(W - 1, y0, z, W - 1, y1, z, base)
        # windows
        wy = fy[k] + 2
        glass = pal["glass"]

        def window(a0, a1, fixed, side, k=k, wy=wy, z1=z1):
            """Window in the bay between posts a0 and a1 on wall `side`."""
            bw = a1 - a0 - 1
            if bw < 1:
                return
            if bw == 1:
                cells = [a0 + 1]
            elif bw == 2:
                cells = [a0 + 1, a0 + 2]
            elif bw == 3:
                cells = [a0 + 2]
            else:
                mid = a0 + 1 + (bw - 2) // 2
                cells = [mid, mid + 1]
            out = {"S": (0, 1), "N": (0, -1), "E": (1, 0), "W": (-1, 0)}[side]
            for c in cells:
                x, z = (c, fixed) if side in "NS" else (fixed, c)
                for y in (wy, wy + 1):
                    F.set(x, y, z, glass)
            if bw == 3 and not (k == 0 and ground_stone):
                for c, att_lo in ((cells[0] - 1, True), (cells[-1] + 1, False)):
                    x, z = (c, fixed) if side in "NS" else (fixed, c)
                    for y in (wy, wy + 1):
                        if F.get(x + out[0], y, z + out[1]) == 0:
                            F.trap(x + out[0], y, z + out[1], pal["accent"], {"S": "N", "N": "S", "E": "W",
                                                                              "W": "E"}[side], open=True)
            if flower_box and k >= 1 and side == "S" and rng.random() < 0.8:
                for c in cells:
                    F.set(c, wy - 1, fixed + 1, B("azalea_leaves_flowered", persistent_bit=True), keep=True)
            if k == 0 and ground_stone:
                # stone lintel + sill accents
                for c in cells:
                    x, z = (c, fixed) if side in "NS" else (fixed, c)
                    F.stairs(x + out[0], wy - 1, z + out[1], "stone_brick", {"S": "N", "N": "S", "E": "W",
                                                                             "W": "E"}[side], top=True, keep=True)

        dx_door = door_x if door_x is not None else (px[len(px) // 2 - 1] + px[len(px) // 2]) // 2 if len(px) > 1 else W // 2
        if front_windows:
            for a0, a1 in zip(px[:-1], px[1:]):
                if k == 0 and a0 < dx_door < a1:
                    continue
                if ("S", k, a0) in no_window:
                    continue
                window(a0, a1, z1, "S")
        if back_windows and (k > 0 or ground_back_windows):
            for a0, a1 in zip(px[:-1], px[1:]):
                if ("N", k, a0) in no_window:
                    continue
                window(a0, a1, 0, "N")
        if side_windows and (k > 0 or ground_side_windows):
            for a0, a1 in zip(pz[:-1], pz[1:]):
                for side, fx in (("W", 0), ("E", W - 1)):
                    if chimney and chimney[0] == side and a0 <= chimney[1] <= a1:
                        continue
                    if (side, k, a0) in no_window:
                        continue
                    window(a0, a1, fx, side)
    # door ----------------------------------------------------------------
    dz = D - 1
    F.set(dx_door, 2, dz, AIR)
    F.set(dx_door, 3, dz, AIR)
    F.door(dx_door, 2, dz, pal["door"], "N")
    F.set(dx_door, 4, dz, bl.block("stone_brick") if ground_stone else bl.log(frame, F.ax("x")))
    F.stairs(dx_door, 1, D, "stone_brick", "N")
    F.set(dx_door - 1, 1, D, bl.slab("stone_brick"), keep=True)
    F.set(dx_door + 1, 1, D, bl.slab("stone_brick"), keep=True)
    if lantern:
        if jetty and floors > 1:
            F.lantern(dx_door + 1, 5, D, hanging=True)
            F.lantern(dx_door - 1, 5, D, hanging=True)
        else:
            F.torch(dx_door + 1, 4, D, attach="N")
            F.torch(dx_door - 1, 4, D, attach="N")
    if sign:
        sx_ = dx_door + (2 if dx_door + 2 < W - 1 else -2)
        if jetty and floors > 1:
            F.set(sx_, 5, D + 1, bl.fence(frame))
            F.hsign(sx_, 4, D + 1, "S", sign, wood="spruce")
        else:
            F.sign(sx_, 3, D, "S", sign)
    # roof ----------------------------------------------------------------
    zt = zf(floors - 1)
    ry = top + 1
    gable_fill = plaster
    top_y = kit.gable_roof(F, 0, 0, W - 1, zt, ry, roof, axis=roof_axis, overhang=1, trim=pal["trim"],
                           gable=gable_fill)
    # gable timbering + attic window
    if roof_axis == "x":
        mid = zt // 2
        for xg in (0, W - 1):
            for y in range(ry, top_y):
                if F.get(xg, y, mid) == gable_fill:
                    F.log(xg, y, mid, frame)
            if top_y - ry >= 3:
                for zz in (mid - 1, mid + 1):
                    if F.get(xg, ry + 1, zz) == gable_fill:
                        F.set(xg, ry + 1, zz, pal["glass"])
    else:
        mid = (W - 1) // 2
        for zg in (0, zt):
            for y in range(ry, top_y):
                if F.get(mid, y, zg) == gable_fill:
                    F.log(mid, y, zg, frame)
            if top_y - ry >= 3:
                for xx in (mid - 1, mid + 1):
                    if F.get(xx, ry + 1, zg) == gable_fill:
                        F.set(xx, ry + 1, zg, pal["glass"])
    # dormer --------------------------------------------------------------
    if dormer and roof_axis == "x":
        for cx in ([W // 2] if W < 17 else [W // 4 + 1, W - 1 - W // 4 - 1]):
            for dzz in range(0, 4):
                z = zt - dzz
                for sx_, face in ((-2, "E"), (2, "W")):
                    F.stairs(cx + sx_, ry + 1, z + 1, roof, face, keep=(dzz > 0))
                    F.stairs(cx + sx_ // 2, ry + 2, z + 1, roof, face, keep=(dzz > 0))
                F.set(cx, ry + 3, z + 1, bl.slab(roof), keep=(dzz > 0))
                for sx_ in (-1, 1):
                    F.set(cx + sx_, ry, z, bl.log(frame), keep=(dzz > 0))
                    F.set(cx + sx_, ry + 1, z, bl.log(frame), keep=(dzz > 0))
                if dzz > 0:
                    F.set(cx, ry, z, AIR)
                    F.set(cx, ry + 1, z, AIR)
            F.set(cx, ry, zt, plaster)
            F.set(cx, ry + 1, zt, pal["glass"])
            F.set(cx, ry + 2, zt, plaster)
    # chimney -------------------------------------------------------------
    if chimney:
        side, cz = chimney
        cxo = -1 if side == "W" else W
        cxi = 0 if side == "W" else W - 1
        cm = Mix((bl.block("brick"), 5), (bl.block("granite"), 1), (bl.block("cobblestone"), 2),
                 (bl.block("stone_brick"), 1))
        ctop = top_y + 2
        for z in (cz, cz + 1):
            for y in range(-1, ctop + 1):
                F.set(cxo, y, z, cm)
            for y in range(top + 1, ctop + 1):
                if F.get(cxi, y, z) in (0,):
                    pass
        # widen the base, taper with stairs
        for z in (cz - 1, cz + 2):
            for y in range(-1, 4):
                F.set(cxo, y, z, cm)
            F.stairs(cxo, 4, z, "brick", "S" if z < cz else "N")
        F.set(cxo, ctop + 1, cz, bl.campfire())
        F.set(cxo, ctop + 1, cz + 1, bl.wall("brick"))
        F.stairs(cxo, ctop, cz - 1, "brick", "S", top=True, keep=True)
        F.stairs(cxo, ctop, cz + 2, "brick", "N", top=True, keep=True)
        # fireplace opening inside
        for z in (cz, cz + 1):
            F.set(cxi, 2, z, AIR)
            F.set(cxi, 3, z, bl.block("brick"))
            F.set(cxo, 2, z, AIR)
            F.set(cxo, 1, z, B("netherrack"))
            F.set(cxo, 2, z, bl.campfire())
        outx = -2 if side == "W" else W + 1
        for z in (cz, cz + 1):
            for y in range(-1, 4):
                F.set(outx, y, z, cm)
        F.stairs(outx, 4, cz, "brick", "E" if side == "W" else "W")
        F.stairs(outx, 4, cz + 1, "brick", "E" if side == "W" else "W")
        inx = 1 if side == "W" else W - 2
        F.set(inx, 2, cz - 1, bl.block("brick"), keep=True)
        F.set(inx, 2, cz + 2, bl.block("brick"), keep=True)
        F.set(inx, 3, cz - 1, bl.slab("brick"), keep=True)
        F.set(inx, 3, cz + 2, bl.slab("brick"), keep=True)
    return dict(W=W, D=D, fy=fy, floors=floors, zf=[zf(k) for k in range(floors)], door_x=dx_door, pal=pal,
                top=top, roof_top=top_y, H=H)


def stairwell(F, info, x0, z, direction=1, storey=0):
    """Straight flight along local x at row z from storey -> storey+1.  Returns the cells used."""
    fy = info["fy"]
    pal = info["pal"]
    y = fy[storey] + 1
    for i in range(info["H"] + 1):
        x = x0 + i * direction
        F.stairs(x, y + i, z, pal["floor"], "E" if direction > 0 else "W")
        for yy in range(y + i + 1, fy[storey + 1] + 3):
            F.set(x, yy, z, AIR)
        if i > 0:
            F.set(x, y + i - 1, z, bl.planks(pal["floor"]))
    # railing on the upper floor around the opening
    uy = fy[storey + 1] + 1
    for i in range(0, info["H"]):
        F.set(x0 + i * direction, uy, z + 1, bl.fence(pal["accent"]), keep=True)
    F.set(x0 - direction, uy, z, bl.fence(pal["accent"]), keep=True)
    F.set(x0 - direction, uy, z + 1, bl.fence(pal["accent"]), keep=True)


def furnish_home(F, info, seed=0):
    """Cosy generic interior: kitchen + table downstairs, bedroom upstairs."""
    rng = F.rng
    W, D, fy, pal = info["W"], info["D"], info["fy"], info["pal"]
    wood = pal["accent"]
    y = fy[0] + 1
    # stairs along the back wall
    if info["floors"] > 1 and W >= 9:
        stairwell(F, info, 2, 1, 1, 0)
        F.barrel(2, y, 2, "U")
    # kitchen corner
    kx = W - 2
    F.set(kx, y, 1, B("lit_smoker", cardinal_direction=bl._CARD[F.d("S")]) if rng.random() < 0.5 else bl.furnace(
        F.d("S")))
    F.set(kx, y, 2, B("crafting_table"))
    F.barrel(kx, y, 3, "W")
    F.set(kx, y + 1, 3, B("flower_pot", update_bit=True)) if False else None
    F.set(kx - 1, y, 1, B("cauldron", cauldron_liquid="water", fill_level=6))
    # table and chairs
    tx, tz = W // 2, D // 2
    kit.table(F, tx, y, tz, wood)
    F.stairs(tx - 1, y, tz, wood, "W")
    F.stairs(tx + 1, y, tz, wood, "E")
    # rug + light
    col = ["red", "blue", "green", "yellow", "cyan", "orange", "purple", "light_blue"][int(rng.integers(0, 8))]
    for dx in range(-1, 2):
        for dz_ in (1, 2):
            if F.get(tx + dx, y, tz + dz_) == 0:
                F.set(tx + dx, y, tz + dz_, B(col + "_carpet"))
    F.lantern(tx, fy[1] - 1, tz, hanging=True)
    F.set(1, y, D - 2, bl.block(wood))
    F.potted(1, y + 1, D - 2, kit.flowers(rng))
    # upstairs
    if info["floors"] > 1:
        uy = fy[1] + 1
        zfront = info["zf"][1] - 1
        F.bed(W - 3, uy, zfront, "E", int(rng.integers(0, 16)))
        F.chest(W - 2, uy, zfront - 2, "W", [])
        F.set(W - 2, uy, zfront - 1, B("bookshelf"))
        F.set(W - 2, uy + 1, zfront - 1, bl.lantern())
        if W >= 11:
            F.bed(2, uy, zfront, "W", int(rng.integers(0, 16)))
        for dx in range(3, W - 3):
            for dz_ in range(zfront - 2, zfront):
                if F.get(dx, uy, dz_) == 0 and rng.random() < 0.9:
                    F.set(dx, uy, dz_, B(col + "_carpet"))
        F.lantern(W // 2, fy[2] - 1, D // 2, hanging=True)
        F.set(W - 2, uy, 2, B("loom", direction=0)) if rng.random() < 0.4 else F.set(W - 2, uy, 2, B("bookshelf"))
