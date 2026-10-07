"""Dungeon 5 — 나글파르 조선 요새 (Naglfar Shipyard). Mid tier, 272 x 448, castle type.

South -> north: the black-sand cove with the landing jetty; the outer gatehouse; the outer docks around a walled
harbour basin; the great curtain wall, walked along its top; the nail smelter yard and Naglfari's furnace court
(mid-boss 1); the chain-hung scaffolds down into the dry dock; the dock floor beside the hull and Hraesvelgr's pen
(mid-boss 2); the deck of Naglfar, the ship of dead men's nails; and the raised stern where Hrym holds the tiller.

Local coordinates: x 0..271 (west -> east), z 0..447 (north -> south). Feet levels: ground 64, dock floor 44,
deck 64, stern deck 70, wall walk 84.
"""
import math

import numpy as np

from mcw import B, AIR, PAL
from gen_common import fbm, stair, slab, standing_sign, line_points, boulder
import nr_parts as P
import nr_castle as C
from nr_dungeon import Dungeon, mixer
from nr_spawn import cyl, ell, thick_line

SEA = 62
G, DF, DK, DS, WT = 64, 44, 64, 70, 84


class Naglfar(Dungeon):
    Y0, SY = 32, 128                # 32..159

    def build(self):
        rng = self.rng
        self.pal = C.Pal(rng, wall=[("polished_blackstone_bricks", 7), ("cracked_polished_blackstone_bricks", 2), ("blackstone", 1)],
                         trim="polished_basalt", floor=[("polished_blackstone_bricks", 4), ("polished_blackstone", 2), ("blackstone", 1)],
                         roof="waxed_oxidized_cut_copper", pillar="basalt", window="purple_stained_glass_pane", light="soul_lantern",
                         accent="gilded_blackstone", top="polished_blackstone_wall", plank="dark_oak_planks")
        self.tim = C.Pal(rng, wall=[("dark_oak_planks", 5), ("spruce_planks", 2)], trim="stripped_dark_oak_log", floor=[("spruce_planks", 3), ("dark_oak_planks", 2)],
                         roof="waxed_oxidized_cut_copper", pillar="dark_oak_log", window="spruce_trapdoor", light="soul_lantern",
                         accent="polished_basalt", top="dark_oak_fence")
        self.walk_boxes = []
        self.base()
        self.cove()
        self.outer_wall()
        self.docks()
        self.inner_mass()
        self.smelter()
        self.furnace_court()
        self.curtain()
        self.dry_dock()
        self.scaffolds()
        self.dock_floor_zone()
        self.ship()
        self.boarding()
        self.finish()

    # ------------------------------------------------------------ helpers
    def w(self, lx, lz):
        return self.x0 + lx, self.z0 + lz

    def allow(self, lx1, lz1, lx2, lz2, y1, y2):
        x1, z1 = self.w(lx1, lz1)
        x2, z2 = self.w(lx2, lz2)
        self.walk_boxes.append((min(x1, x2), y1, min(z1, z2), max(x1, x2), y2, max(z1, z2)))

    def fillL(self, lx1, y1, lz1, lx2, y2, lz2, b):
        x1, z1 = self.w(lx1, lz1)
        x2, z2 = self.w(lx2, lz2)
        C.fill(self.a, x1, y1, z1, x2, y2, z2, b)

    # ------------------------------------------------------------ terrain
    def base(self):
        a = self.a
        rock = [B("blackstone"), B("basalt", pillar_axis="y"), B("tuff"), B("blackstone"), B("deepslate"), B("smooth_basalt")]
        for j in range(G - self.Y0):
            y = j + self.Y0
            a.blk[:, j, :] = rock[(y // 4) % len(rock)]
        n1 = fbm(self.sx, self.sz, 18, 4, self.seed + 1)
        self.n1 = n1
        # the fortress grounds are paved; outside the fortress walls: basalt crags up to ~100
        X, Z = np.meshgrid(np.arange(self.sx), np.arange(self.sz), indexing="ij")
        self.crag = (X < 8) | (X > 263) | (Z < 8)
        H = np.full((self.sx, self.sz), G - 1)
        cragH = (96 + (n1 - 0.5) * 30).astype(int)
        H = np.where(self.crag, cragH, H)
        self.H = H
        for (i, k) in np.argwhere(self.crag):
            col = a.blk[i, :, k]
            for y in range(G, int(H[i, k]) + 1):
                col[y - self.Y0] = rock[(y // 3 + i // 7) % len(rock)]

    def cove(self):
        """The black-sand cove south of the outer wall, closed by crags except for a narrow sea mouth."""
        a, rng = self.a, self.rng
        n = fbm(self.sx, self.sz, 12, 3, self.seed + 5)
        sand = mixer(rng, [(B("black_concrete_powder"), 6), (B("gravel"), 2), (B("blackstone"), 1), (B("basalt", pillar_axis="y"), 1)])
        rock = [B("blackstone"), B("basalt", pillar_axis="y"), B("tuff"), B("smooth_basalt")]
        self.sea = np.zeros((self.sx, self.sz), bool)
        for i in range(self.sx):
            for k in range(394, self.sz):
                col = self.a.blk[i, :, k]
                # open water: an ellipse reaching the south edge only through a narrow mouth
                dsea = math.hypot((i - 136) / 92.0, (k - 450) / 34.0)
                dbeach = math.hypot((i - 136) / 98.0, (k - 418) / 22.0)
                mouth = abs(i - 136) < 22 + (k - 430) * 0.6 and k > 430
                if dsea < 1 or mouth:
                    depth = int(3 + 12 * min(1.0, (1 - min(dsea, 1)) * 2.5)) if not mouth else 12
                    floor_y = SEA - depth
                    for y in range(floor_y + 1, SEA + 1):
                        col[y - self.Y0] = B("water")
                    for y in range(SEA + 1, 130):
                        col[y - self.Y0] = AIR
                    col[floor_y - self.Y0] = B("gravel") if rng.random() < 0.5 else B("black_concrete_powder")
                    self.H[i, k] = floor_y
                    self.sea[i, k] = True
                elif dbeach < 1 and k >= 394:
                    # beach: 63 at the wall, sloping into the water
                    t = max(0.0, (k - 404) / 14.0)
                    top = int(round(63 - 3 * t * t))
                    for y in range(top + 1, 130):
                        col[y - self.Y0] = AIR
                    for y in range(top + 1, SEA + 1):
                        col[y - self.Y0] = B("water")
                    col[top - self.Y0] = sand()
                    self.H[i, k] = top
                else:
                    h = int(84 + n[i, k] * 30 + max(0, 20 - abs(i - 136) * 0.0))
                    for y in range(G, h + 1):
                        col[y - self.Y0] = rock[(y // 3 + i // 9) % len(rock)]
                    self.H[i, k] = h
                    self.crag[i, k] = True
        # sea stacks at the mouth break the horizon
        for (sx_, sz_, r, h) in ((104, 438, 5, 94), (170, 440, 6, 100), (150, 446, 4, 86)):
            x, z = self.w(sx_, sz_)
            for dx in range(-r - 1, r + 2):
                for dz in range(-r - 1, r + 2):
                    d = math.hypot(dx, dz)
                    if d <= r:
                        top = int(h - d * 2.2)
                        for y in range(44, top):
                            a.set(x + dx, y, z + dz, rock[(y // 3) % len(rock)])
        # landing jetty and return ship
        for lz in range(398, 432):
            for lx in (128, 129, 130):
                x, z = self.w(lx, lz)
                a.set(x, SEA + 1, z, B("dark_oak_planks"))
                for y in range(SEA + 2, SEA + 6):
                    a.set(x, y, z, AIR)
                if lx != 129 and lz % 4 == 0:
                    for y in range(SEA - 10, SEA + 1):
                        if a.get(x, y, z) in (B("water"), AIR, B("gravel"), B("black_concrete_powder")):
                            a.set(x, y, z, B("dark_oak_log", axis="y"))
                    a.set(x, SEA + 2, z, B("dark_oak_fence"))
                    if lz % 8 == 0:
                        a.set(x, SEA + 3, z, B("soul_lantern"))
        sx_, sz_ = self.w(134, 440)
        info = P.longship(a, sx_, SEA, sz_, "north", rng, length=29, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        ax, az = self.w(129, 404)
        self.data["start"] = [ax + 0.5, SEA + 2, az + 0.5, 180]
        self.walk_seeds = [(ax, SEA + 2, az)]
        standing_sign(a, ax + 2, SEA + 2, az - 2, 8, "§l§5나글파르 조선 요새\n§r§f망자의 손톱으로\n§f배를 짓는 곳\n§7성문으로 들어가세요", kind="dark_oak_standing_sign")
        # driftwood, bones and soul fires on the beach
        for _ in range(40):
            lx, lz = rng.randint(50, 222), rng.randint(395, 412)
            x, z = self.w(lx, lz)
            t = P.surface_y(a, x, z)
            if t is None or t < 62 or a.get(x, t + 1, z) != AIR or abs(lx - 129) < 4:
                continue
            r = rng.random()
            if r < 0.3:
                axis = rng.choice(["x", "z"])
                for k in range(rng.randint(3, 6)):
                    a.put(x + (k if axis == "x" else 0), t + 1, z + (k if axis == "z" else 0), B("stripped_dark_oak_log", axis=axis))
            elif r < 0.45:
                a.set(x, t + 1, z, B("bone_block", axis=rng.choice(["x", "z"])))
            elif r < 0.55:
                a.set(x, t, z, B("soul_soil"))
                a.set(x, t + 1, z, B("soul_fire"))
            else:
                boulder(a, x, t + 1, z, rng, rng.uniform(1.0, 1.8), [B("basalt"), B("blackstone"), B("tuff")])
        self.allow(30, 386, 242, 447, 40, 74)

    # ------------------------------------------------------------ outer wall + gatehouse
    def outer_wall(self):
        a, pal = self.a, self.pal
        x1, z1 = self.w(8, 388)
        x2, z2 = self.w(263, 393)
        C.wall(a, x1, z1, x2, z2, G, 22, pal, walk=False, cren="both", outer="south", buttress=9, foot=20)
        # side walls and the north wall (the fortress perimeter)
        for (lx1, lz1, lx2, lz2, outer) in ((8, 8, 13, 393, "west"), (258, 8, 263, 393, "east"), (8, 8, 263, 13, "north")):
            xa, za = self.w(lx1, lz1)
            xb, zb = self.w(lx2, lz2)
            C.wall(a, xa, za, xb, zb, G, 22, pal, walk=False, cren="both", outer=outer, buttress=0, foot=30, slits=False)
        # main gatehouse: two round towers and an arched gate with a raised portcullis
        gx, gz = self.w(136, 390)
        C.gate(a, gx, gz, G, "z", 7, 11, 8, pal, portcullis=True)
        for dx in (-11, 11):
            C.tower(a, gx + dx, gz, G, 32, 6, pal, roof="cone")
        # the beach in front of the gate is paved
        for dx in range(-5, 6):
            for z in range(gz + 4, gz + 9):
                a.set(gx + dx, G - 1, z, pal.floor())
                for y in range(G, G + 6):
                    if a.get(gx + dx, y, z) != AIR and PAL.names[a.get(gx + dx, y, z)] not in ("water",):
                        a.set(gx + dx, y, z, AIR)
        for dx in (-5, 5):
            P.brazier(a, gx + dx, G, gz + 5, soul=True)
        # a sea gate (barred) where the harbour basin meets the sea
        sx_, sz_ = self.w(84, 390)
        for dx in range(-4, 5):
            for z in range(sz_ - 3, sz_ + 4):
                for y in range(52, SEA + 1):
                    a.set(sx_ + dx, y, z, B("water"))
                for y in range(SEA + 1, SEA + 7):
                    a.set(sx_ + dx, y, z, AIR if abs(dx) < 4 else pal.trim)
            a.set(sx_ + dx, SEA + 7, sz_, pal.accent)
        for dx in range(-3, 4):
            for y in range(52, SEA + 7):
                a.set(sx_ + dx, y, sz_, B("iron_bars"))
        # channel from the sea gate to the beach water
        for lz in range(394, 412):
            for lx in range(80, 89):
                x, z = self.w(lx, lz)
                for y in range(54, SEA + 1):
                    a.set(x, y, z, B("water"))
                for y in range(SEA + 1, SEA + 8):
                    if a.get(x, y, z) != AIR and lx in (80, 88):
                        continue
                    a.set(x, y, z, AIR)
                a.set(x, 53, z, B("gravel"))

    # ------------------------------------------------------------ c1: outer docks around the harbour basin
    def docks(self):
        a, rng, pal, tim = self.a, self.rng, self.pal, self.tim
        # paving
        quay = mixer(rng, [(B("polished_blackstone_bricks"), 4), (B("blackstone"), 2), (B("polished_basalt", pillar_axis="y"), 1), (B("gravel"), 1)])
        for lx in range(14, 258):
            for lz in range(305, 388):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, quay())
        # basin: water 10 deep, quay walls with a trim edge (one step out of the water everywhere)
        bx1, bz1, bx2, bz2 = 70, 322, 200, 372
        for lx in range(bx1, bx2 + 1):
            for lz in range(bz1, bz2 + 1):
                x, z = self.w(lx, lz)
                edge = lx in (bx1, bx2) or lz in (bz1, bz2)
                for y in range(52, SEA + 1):
                    a.set(x, y, z, B("water"))
                a.set(x, 51, z, B("gravel"))
                a.set(x, G - 1, z, B("water") if not edge else B("water"))
        for lx in range(bx1 - 1, bx2 + 2):
            for lz in (bz1 - 1, bz2 + 1):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, pal.trim)
        for lz in range(bz1 - 1, bz2 + 2):
            for lx in (bx1 - 1, bx2 + 1):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, pal.trim)
        # the basin opens south towards the sea gate
        for lz in range(bz2 + 1, 390):
            for lx in range(80, 89):
                x, z = self.w(lx, lz)
                for y in range(52, SEA + 1):
                    a.set(x, y, z, B("water"))
                a.set(x, G - 1, z, B("water") if lx not in (80, 88) else pal.trim)
        # a footbridge over the channel
        for lz in range(376, 381):
            for lx in range(78, 91):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, B("dark_oak_planks") if 79 <= lx <= 89 else pal.trim)
                if lz in (376, 380):
                    a.set(x, G, z, B("dark_oak_fence"))
        # mooring posts and moored black longships
        for (lx, lz, facing) in ((96, 330, "east"), (150, 364, "west"), (180, 332, "west")):
            x, z = self.w(lx, lz)
            P.longship(a, x, SEA, z, facing, rng, length=27, beam=8, sail="high", sail_up=rng.random() < 0.5)
        for lx in range(bx1, bx2 + 1, 8):
            for lz in (bz1 - 2, bz2 + 2):
                x, z = self.w(lx, lz)
                a.set(x, G, z, B("polished_blackstone_wall"))
                a.set(x, G + 1, z, B("chain"))
        # warehouses along the west and east quays
        for (lx1, lz1, lx2, lz2, door) in ((18, 310, 50, 334, "east"), (18, 344, 50, 378, "east"),
                                           (222, 310, 254, 334, "west"), (222, 344, 254, 378, "west")):
            x1, z1 = self.w(lx1, lz1)
            x2, z2 = self.w(lx2, lz2)
            C.hall(a, x1, z1, x2, z2, G, 9, tim, roof="gable", axis="z", doors=[(door, 0, 5, 6)], pillars=0, lights=True)
            # make the interiors solid storage stacks except the doorway alcove (nobody goes inside)
            cx = (x1 + x2) // 2
            for x in range(x1 + 1, x2):
                for z in range(z1 + 1, z2):
                    inner = abs(x - (x2 if door == "east" else x1)) > 3
                    if inner:
                        for y in range(G, G + 9):
                            a.set(x, y, z, B("barrel") if (x + y + z) % 5 == 0 else B("dark_oak_planks"))
            # loading door crates
            dxo = 3 if door == "east" else -3
            dz0 = (z1 + z2) // 2
            ex = (x2 if door == "east" else x1) + dxo
            for k in range(-6, 7, 3):
                C.crate_stack(a, ex, G, dz0 + k + (8 if k == 0 else 0), rng, 3)
        # cranes on the quays
        for (lx, lz, facing) in ((76, 316, "south"), (130, 316, "south"), (194, 316, "south"), (110, 378, "north"), (170, 378, "north")):
            x, z = self.w(lx, lz)
            C.crane(a, x, G, z, facing, h=15, arm=9)
        # cargo: nail barrels, chains coiled, nets
        for _ in range(60):
            lx, lz = rng.randint(56, 214), rng.randint(308, 386)
            if bx1 - 3 <= lx <= bx2 + 3 and bz1 - 3 <= lz <= bz2 + 3:
                continue
            if 126 <= lx <= 146 and lz > 380:
                continue
            x, z = self.w(lx, lz)
            if a.get(x, G, z) != AIR or a.get(x, G - 1, z) == B("water"):
                continue
            r = rng.random()
            if r < 0.35:
                C.crate_stack(a, x, G, z, rng, rng.randint(2, 5))
            elif r < 0.5:
                a.set(x, G, z, B("bone_block", axis="y"))
                a.set(x, G + 1, z, B("bone_block", axis="y") if rng.random() < 0.5 else AIR)
            elif r < 0.6:
                a.set(x, G, z, B("chain", axis="x"))
            elif r < 0.7:
                a.set(x, G, z, B("web"))
        # lamp posts along the quays
        for lx in range(60, 216, 12):
            for lz in (312, 384):
                x, z = self.w(lx, lz)
                if a.get(x, G, z) == AIR:
                    for y in range(G, G + 4):
                        a.set(x, y, z, B("polished_blackstone_wall"))
                    a.set(x, G + 4, z, B("soul_lantern"))
        self.allow(14, 304, 257, 388, 40, 74)
        self.add_zone("c1", (self.x0 + 14, G - 2, self.z0 + 306, self.x0 + 257, G + 6, self.z0 + 386), floor_mask=None, n=12)

    # ------------------------------------------------------------ c2: the great curtain wall and its wall walk
    def curtain(self):
        a, rng, pal = self.a, self.rng, self.pal
        x1, z1 = self.w(14, 296)
        x2, z2 = self.w(257, 304)
        top = C.wall(a, x1, z1, x2, z2, G, WT - G, pal, walk=True, cren="both", buttress=0, foot=4, slits=True)
        assert top == WT
        # invisible guard above both parapets (no jumping off the wall walk)
        C.barrier_line(a, [(x, z1) for x in range(x1, x2 + 1)] + [(x, z2) for x in range(x1, x2 + 1)], WT, WT + 4)
        # towers astride the wall: the wall walk passes through arched doorways
        for lx in (60, 136, 210):
            tx, tz = self.w(lx, 300)
            C.tower(a, tx, tz, G, 44, 8, pal, shape="square", roof="pyramid", windows=True)
            for y in range(WT - 1, WT):
                for dx in range(-8, 9):
                    for dz in range(-6, 7):
                        a.set(tx + dx, y, tz + dz, pal.floor())
            for dx in range(-8, 9):
                for dz in range(-3, 4):
                    for y in range(WT, WT + 6):
                        a.set(tx + dx, y, tz + dz, AIR)
            C.gate(a, tx - 8, tz, WT, "x", 7, 6, 2, pal)
            C.gate(a, tx + 8, tz, WT, "x", 7, 6, 2, pal)
            C.chandelier(a, tx, WT + 7, tz, 2, "soul_lantern")
            # the tower rooms widen the walk: barrels of nails, racks of spears
            for dz in (-5, 5):
                for dx in range(-5, 6, 2):
                    a.set(tx + dx, WT, tz + dz, B("barrel") if dx % 4 else B("dark_oak_fence"))
        # catapults on the wall walk
        for lx in (96, 172, 236):
            cx, cz = self.w(lx, 300)
            self.catapult(cx, WT, cz)
        # banners hanging on the south face
        for lx in range(30, 250, 16):
            x, z = self.w(lx, 305)
            for y in range(WT - 9, WT - 2):
                a.set(x, y, z, B("purple_wool") if y > WT - 8 else B("black_wool"))
        # stairs: up the south face from the docks (west), down the north face into the smelter yard (east)
        n = WT - G
        bx, bz = self.w(100, 307)                      # flight runs west along z 307..305 (south of the wall face)
        C.flight(a, bx, G, bz, "west", n, 3, "polished_blackstone_brick_stairs", support=pal.wall, centre=False)
        for x in range(bx - n - 3, bx - n + 2):
            for w in range(0, 3):
                a.set(x, WT - 1, bz - w, pal.floor())
                for y in range(WT, WT + 4):
                    a.set(x, y, bz - w, AIR)
            for y in range(WT, WT + 5):
                a.set(x, y, z2, AIR)
            a.set(x, WT - 1, z2, pal.floor())
        C.barrier_line(a, [(x, bz + 1) for x in range(bx - n - 4, bx + 1)], G, WT + 4)
        C.barrier_line(a, [(bx - n - 4, z) for z in range(bz - 2, bz + 2)], WT, WT + 4)
        ex, ez = self.w(224, 293)                      # flight runs east along z 293..295 (north of the wall face)
        C.flight(a, ex, G, ez, "east", n, 3, "polished_blackstone_brick_stairs", support=pal.wall, centre=False)
        hx = ex + n
        for x in range(hx - 1, hx + 4):
            for w in range(0, 3):
                a.set(x, WT - 1, ez + w, pal.floor())
                for y in range(WT, WT + 4):
                    a.set(x, y, ez + w, AIR)
            for y in range(WT, WT + 5):
                a.set(x, y, z1, AIR)
            a.set(x, WT - 1, z1, pal.floor())
        C.barrier_line(a, [(x, ez - 1) for x in range(ex, hx + 5)], G, WT + 4)
        C.barrier_line(a, [(hx + 4, z) for z in range(ez - 1, ez + 3)], WT, WT + 4)
        self.allow(70, 300, 104, 312, 60, 92)
        self.allow(218, 286, 254, 300, 60, 92)
        self.allow(14, 290, 257, 310, 60, 92)
        self.add_zone("c2", (x1, WT - 2, z1, x2, WT + 3, z2), floor_mask=None, n=12)

    def catapult(self, x, y, z):
        a = self.a
        for dx in (-2, 2):
            for dz in (-2, 2):
                a.set(x + dx, y, z + dz, B("dark_oak_log", axis="y"))
            for k in range(1, 4):
                a.set(x + dx, y + k, z, B("dark_oak_log", axis="y"))
        for dz in range(-2, 3):
            a.set(x - 2, y, z + dz, B("dark_oak_log", axis="z"))
            a.set(x + 2, y, z + dz, B("dark_oak_log", axis="z"))
        for dx in range(-2, 3):
            a.set(x + dx, y + 4, z, B("dark_oak_log", axis="x"))
        for k in range(6):
            a.set(x, y + 4 + k, z - k // 2, B("stripped_dark_oak_log", axis="y"))
        a.set(x, y + 10, z - 3, B("chain"))
        a.set(x, y + 9, z - 3, B("bone_block"))
        a.set(x, y + 1, z + 1, B("blackstone"))
        a.set(x, y + 1, z - 1, B("cobblestone"))

    # ------------------------------------------------------------ the inner fortress: solid blocks of buildings
    def inner_mass(self):
        """Everything north of the curtain wall starts as solid masonry up to y 79; courtyards, rooms, corridors and
        the dry dock are carved out of it. Whatever is not carved can never be walked into."""
        a = self.a
        self.MT = 79
        body = [B("polished_blackstone_bricks"), B("blackstone"), B("polished_blackstone_bricks"), B("basalt", pillar_axis="y")]
        for i in range(14, 258):
            for k in range(14, 296):
                col = a.blk[i, :, k]
                for y in range(G, self.MT + 1):
                    col[y - self.Y0] = body[(y // 6 + i // 11 + k // 13) % len(body)]
        self.carved = np.zeros((self.sx, self.sz), bool)

    def carve(self, lx1, lz1, lx2, lz2, y1, y2, floor_b=None, mark=True):
        a = self.a
        for lx in range(min(lx1, lx2), max(lx1, lx2) + 1):
            for lz in range(min(lz1, lz2), max(lz1, lz2) + 1):
                x, z = self.w(lx, lz)
                for y in range(y1, y2 + 1):
                    a.set(x, y, z, AIR)
                if floor_b is not None:
                    a.set(x, y1 - 1, z, floor_b() if callable(floor_b) else floor_b)
                if mark:
                    self.carved[lx, lz] = True

    def facade(self, lx1, lz1, lx2, lz2, side, y0, h, rng):
        """Dress a carved wall face (the cells just outside the carved rectangle on `side`) as building fronts."""
        a, pal = self.a, self.pal
        if side in ("north", "south"):
            lz = lz1 - 1 if side == "north" else lz2 + 1
            cells = [(lx, lz) for lx in range(lx1, lx2 + 1)]
        else:
            lx = lx1 - 1 if side == "west" else lx2 + 1
            cells = [(lx, lz) for lz in range(lz1, lz2 + 1)]
        face = {"north": "south", "south": "north", "west": "east", "east": "west"}[side]
        for i, (lx, lz) in enumerate(cells):
            x, z = self.w(lx, lz)
            if a.get(x, y0, z) == AIR:
                continue
            for y in range(y0, y0 + h):
                b = pal.wall()
                if i % 8 == 0:
                    b = pal.pillar
                elif (y - y0) in (6, h - 1):
                    b = pal.trim
                elif i % 8 in (3, 5) and (y - y0) in (2, 3, 8, 9, 10):
                    b = pal.window
                a.set(x, y, z, b)
            if i % 16 == 4:
                # a door (shut) with a lamp above it
                for y in (y0, y0 + 1):
                    a.set(x, y, z, B("dark_oak_planks"))
                a.set(x, y0 + 2, z, pal.trim)
                dx, dz = C.DIRS[face]
                a.put(x + dx, y0 + 3, z + dz, B("soul_lantern", hanging=0))
            elif i % 8 == 0 and h > 8:
                dx, dz = C.DIRS[face]
                a.put(x + dx, y0 + 4, z + dz, B("soul_lantern"))

    def roofscape(self):
        """Gabled copper roofs and chimneys on top of the solid blocks so the fortress reads as a crowded town."""
        a, rng, pal = self.a, self.rng, self.pal
        T = 16
        for tx in range(14, 258 - T + 1, T):
            for tz in range(14, 296 - T + 1, T):
                sub = self.carved[tx:tx + T, tz:tz + T]
                if sub.any():
                    continue
                x1, z1 = self.w(tx + 1, tz + 1)
                x2, z2 = self.w(tx + T - 2, tz + T - 2)
                axis = "x" if (tx // T + tz // T) % 2 else "z"
                C.gable_roof(a, x1, z1, x2, z2, self.MT + 1, axis, pal, overhang=1, end_fill=pal.wall)
                if rng.random() < 0.5:
                    cx, cz = x1 + rng.randint(2, T - 5), z1 + rng.randint(2, T - 5)
                    for y in range(self.MT + 1, self.MT + 12):
                        for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                            a.set(cx + dx, y, cz + dz, B("polished_blackstone_bricks"))
                    a.set(cx, self.MT + 12, cz, B("soul_campfire"))
                    a.set(cx + 1, self.MT + 12, cz + 1, B("campfire"))

    # ------------------------------------------------------------ c3: the nail smelter yard
    def smelter(self):
        a, rng, pal = self.a, self.rng, self.pal
        yard = mixer(rng, [(B("polished_blackstone_bricks"), 3), (B("blackstone"), 2), (B("gravel"), 1), (B("soul_soil"), 1)])
        self.carve(120, 212, 250, 294, G, 158, floor_b=yard)
        for (side, args) in (("north", (120, 212, 250, 294)), ("west", (120, 212, 250, 294)), ("east", (120, 212, 250, 294))):
            self.facade(*args, side, G, self.MT - G + 1, rng)
        # three soul smelters: round furnaces with blast-furnace mouths and soul-fire chimneys
        for (lx, lz) in ((150, 236), (196, 228), (226, 262)):
            x, z = self.w(lx, lz)
            r = 4
            for dx in range(-r - 1, r + 2):
                for dz in range(-r - 1, r + 2):
                    d = math.hypot(dx, dz)
                    if d <= r + 0.4:
                        for y in range(G, G + 14):
                            if d > r - 1.1 or y < G + 1:
                                band = (y - G) % 5 == 4
                                a.set(x + dx, y, z + dz, B("crying_obsidian") if band and (dx + dz) % 2 == 0 else
                                      B("polished_blackstone") if band else B("polished_blackstone_bricks"))
                            else:
                                a.set(x + dx, y, z + dz, B("soul_soil") if y == G + 1 else AIR)
                        if d <= r - 1.1:
                            a.set(x + dx, G + 2, z + dz, B("soul_fire"))
            for (dx, dz, f) in ((r, 0, "east"), (-r, 0, "west"), (0, r, "south"), (0, -r, "north")):
                a.set(x + dx, G, z + dz, B("blast_furnace", cardinal=f))
                a.set(x + dx, G + 1, z + dz, B("iron_bars"))
            for y in range(G + 14, G + 20):
                for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    a.set(x + dx, y, z + dz, B("polished_blackstone_bricks"))
            a.set(x, G + 20, z, B("soul_campfire"))
            a.set(x + 1, G + 20, z + 1, B("soul_campfire"))
        # heaps of nails
        for _ in range(16):
            lx, lz = rng.randint(126, 244), rng.randint(216, 290)
            x, z = self.w(lx, lz)
            if a.get(x, G, z) != AIR:
                continue
            r = rng.uniform(1.4, 2.8)
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    dd = math.hypot(dx, dz)
                    if dd <= r:
                        for t in range(int((r - dd) * 0.9) + 1):
                            a.put(x + dx, G + t, z + dz, B("bone_block", axis=rng.choice(["x", "z"])) if rng.random() < 0.6 else B("calcite"))
        # chain conveyors on posts across the yard
        for (lz, lxa, lxb) in ((248, 132, 240), (274, 132, 240)):
            for lx in range(lxa, lxb + 1, 12):
                x, z = self.w(lx, lz)
                for y in range(G, G + 7):
                    a.set(x, y, z, B("polished_blackstone_wall"))
                a.set(x, G + 7, z, B("polished_blackstone"))
                a.set(x, G + 8, z, B("soul_lantern"))
            for lx in range(lxa, lxb + 1):
                x, z = self.w(lx, lz)
                if a.get(x, G + 6, z) == AIR:
                    a.set(x, G + 6, z, B("chain", axis="x"))
                    if lx % 6 == 3:
                        a.set(x, G + 5, z, B("chain"))
                        a.set(x, G + 4, z, B("bone_block"))
        # crucibles and minecart rails
        for (lx, lz) in ((170, 262), (210, 286), (136, 270)):
            x, z = self.w(lx, lz)
            a.set(x, G, z, B("cauldron", cauldron_liquid="lava", fill_level=6))
            a.set(x + 1, G, z, B("polished_blackstone_wall"))
            a.set(x - 1, G, z, B("polished_blackstone_wall"))
        for lx in range(124, 248):
            x, z = self.w(lx, 222)
            if a.get(x, G, z) == AIR:
                a.set(x, G, z, B("rail", rail_direction=1))
        self.allow(118, 204, 252, 296, 60, 74)
        self.add_zone("c3", (self.x0 + 122, G - 2, self.z0 + 214, self.x0 + 248, G + 4, self.z0 + 292), floor_mask=None, n=12)

    # ------------------------------------------------------------ mid-boss 1: Naglfari's furnace court
    def furnace_court(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 60, 222, 100, 262
        self.carve(lx1, lz1, lx2, lz2, G, 158, floor_b=pal.floor)
        self.facade(lx1, lz1, lx2, lz2, "north", G, 16, rng)
        self.facade(lx1, lz1, lx2, lz2, "south", G, 16, rng)
        self.facade(lx1, lz1, lx2, lz2, "west", G, 16, rng)
        self.facade(lx1, lz1, lx2, lz2, "east", G, 16, rng)
        cx, cz = self.w(80, 242)
        R = 15

        def floor_fn(x, z, d):
            if abs(d - R + 0.5) < 0.7:
                return B("crying_obsidian") if int(math.degrees(math.atan2(z - cz, x - cx))) % 30 < 15 else B("polished_blackstone")
            if d < 3:
                return B("chiseled_polished_blackstone")
            if abs(d - 8) < 0.6:
                return B("gilded_blackstone")
            return B("polished_blackstone_bricks") if (int(d) + (x + z) % 2) % 3 else B("cracked_polished_blackstone_bricks")
        # corridors: yard -> court (entry gate) and court -> dock rim (exit gate)
        self.carve(101, 239, 119, 245, G, G + 5, floor_b=pal.floor)
        self.carve(77, 202, 83, 221, G, G + 5, floor_b=pal.floor)
        for lz in range(203, 221, 5):
            x, z = self.w(80, lz)
            C.chandelier(a, x, G + 5, z, 1, "soul_lantern", ring=False)
        for lx in range(103, 119, 5):
            x, z = self.w(lx, 242)
            C.chandelier(a, x, G + 5, z, 1, "soul_lantern", ring=False)
        ex, ez = self.w(100, 242)
        entry = self.doorway(ex, G, ez, 7, 6, "z")
        xx, zz = self.w(80, 221)
        exitg = self.doorway(xx, G, zz, 7, 6, "x")
        self.arena("c3_mid", cx, G, cz, R, "naglfari", "mid1", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # soul furnaces in the four corners, nail heaps, chains hanging from the walls
        for (dx, dz) in ((-17, -17), (17, -17), (-17, 17), (17, 17)):
            x, z = cx + dx, cz + dz
            for y in range(G, G + 4):
                for (ox, oz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    a.set(x + ox - (1 if dx > 0 else 0), y, z + oz - (1 if dz > 0 else 0), B("polished_blackstone_bricks") if y < G + 3 else B("soul_campfire"))
        for k in range(12):
            ang = k / 12 * 2 * math.pi
            x, z = int(round(cx + math.cos(ang) * 19)), int(round(cz + math.sin(ang) * 19))
            if a.get(x, G, z) == AIR:
                a.set(x, G, z, B("bone_block", axis="y"))
                a.put(x, G + 1, z, B("calcite") if k % 2 else B("bone_block", axis="x"))
        for (lx, lz) in ((60, 232), (60, 252), (100, 232), (100, 252), (70, 222), (90, 222), (70, 262), (90, 262)):
            x, z = self.w(lx, lz)
            ix = 1 if lx == 60 else -1 if lx == 100 else 0
            iz = 1 if lz == 222 else -1 if lz == 262 else 0
            for y in range(G + 6, G + 15):
                a.put(x + ix, y, z + iz, B("chain"))
            a.put(x + ix, G + 5, z + iz, B("soul_lantern", hanging=1))
        self.allow(58, 200, 122, 264, 60, 74)

    # ------------------------------------------------------------ the dry dock
    def dry_dock(self):
        a, rng, pal = self.a, self.rng, self.pal
        WL = DF - 1                                     # water surface level (flush with the dock floor)
        floor_b = mixer(rng, [(B("polished_blackstone_bricks"), 3), (B("blackstone"), 2), (B("smooth_basalt"), 1)])
        # main basin (flooded) and the west floor
        self.carve(108, 14, 240, 200, DF, 158)
        self.carve(40, 68, 126, 200, DF, 158)
        self.carve(64, 24, 108, 68, DF, 158)
        self.carve(74, 14, 100, 23, DF, 158)
        self.dock_floor = np.zeros((self.sx, self.sz), bool)
        self.dock_floor[40:127, 68:201] = True
        self.dock_floor[64:109, 24:69] = True
        self.dock_floor[74:101, 14:24] = True
        for lx in range(40, 241):
            for lz in range(14, 201):
                if not self.carved[lx, lz]:
                    continue
                x, z = self.w(lx, lz)
                if self.dock_floor[lx, lz]:
                    a.set(x, DF - 1, z, floor_b())
                    for y in range(DF - 6, DF - 1):
                        a.set(x, y, z, B("blackstone"))
                else:
                    for y in range(DF - 6, WL + 1):
                        a.set(x, y, z, B("water"))
                    a.set(x, DF - 7, z, B("gravel"))
        # basin walls: pilasters, trim courses, soul lanterns, barred culverts at the waterline
        for lx in range(40, 241):
            for lz in range(14, 201):
                if not self.carved[lx, lz]:
                    continue
                for (di, dk, face) in ((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south")):
                    ii, kk = lx + di, lz + dk
                    if self.carved[ii, kk]:
                        continue
                    x, z = self.w(ii, kk)
                    t = (ii + kk) % 10
                    for y in range(DF, self.MT + 1):
                        if a.get(x, y, z) == AIR:
                            continue
                        if t == 0:
                            a.set(x, y, z, B("basalt", pillar_axis="y"))
                        elif (y - DF) % 9 == 8:
                            a.set(x, y, z, pal.trim)
                    if t == 5:
                        fx, fz = self.w(lx, lz)
                        a.put(fx, DF + 6, fz, B("soul_lantern"))
                        a.put(fx, DF + 18, fz, B("soul_lantern"))
        # the stone pier carrying the exit portal (south of the stern), rising out of the water
        for lx in range(150, 171):
            for lz in range(192, 209):
                x, z = self.w(lx, lz)
                edge = lx in (150, 170) or lz in (192, 208)
                for y in range(DF - 7, DS - 1):
                    a.set(x, y, z, pal.wall())
                a.set(x, DS - 1, z, pal.floor())
                for y in range(DS, DS + 10):
                    a.set(x, y, z, pal.wall() if edge else AIR)
                self.carved[lx, lz] = True
        self.allow(148, 182, 172, 210, DS - 2, DS + 6)
        self.allow(40, 14, 240, 200, DF - 8, DF + 3)          # the flooded basin and dock floor

    # ------------------------------------------------------------ c4: chain-hung scaffolds down into the dock
    def scaffolds(self):
        a, rng, tim = self.a, self.rng, self.tim
        PY = 53                                        # platform deck block (feet 54)
        plank = mixer(rng, [(B("spruce_planks"), 4), (B("dark_oak_planks"), 2), (B("spruce_slab", half="top"), 1)])
        # head platform at the corridor mouth
        for lx in range(76, 101):
            for lz in range(194, 201):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, B("dark_oak_planks"))
                for y in range(G, G + 5):
                    a.set(x, y, z, AIR)
        for lz in range(201, 203):
            for lx in range(77, 84):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, B("dark_oak_planks"))
                for y in range(G, G + 6):
                    a.set(x, y, z, AIR)
        # the big hanging platform (c4)
        for lx in range(40, 127):
            for lz in range(172, 194):
                x, z = self.w(lx, lz)
                a.set(x, PY, z, plank())
        # flight 1: head platform (64) -> hanging platform (54), running east along z 194..196
        sx, sz = self.w(66, 194)
        C.flight(a, sx, PY + 1, sz, "east", G - PY - 1, 3, "spruce_stairs", support=None, centre=False)
        # flight 2: hanging platform -> dock floor, running north along x 42..44
        fx, fz = self.w(42, 181)
        C.flight(a, fx, DF, fz, "south", PY + 1 - DF, 3, "spruce_stairs", support=None, centre=False)
        # posts, braces, chains to the rim; railings on open edges
        for lx in range(40, 127, 8):
            for lz in (172, 182, 193):
                x, z = self.w(lx, lz)
                for y in range(DF, PY):
                    a.set(x, y, z, B("dark_oak_log", axis="y"))
                for y in range(PY + 1, self.MT + 1, 1):
                    if lz == 172:
                        a.set(x, y, z, B("chain"))
        # landing under flight 1, railings with barriers on every open edge
        for lx in range(56, 66):
            for lz in range(194, 197):
                x, z = self.w(lx, lz)
                a.set(x, PY, z, plank())
        low = [(lx, 171) for lx in range(40, 127)] + [(lx, 194) for lx in list(range(40, 56)) + list(range(76, 127))]
        low += [(lx, 197) for lx in range(55, 66)] + [(55, lz) for lz in range(194, 197)]
        low = [self.w(lx, lz) for (lx, lz) in low]
        C.rail(a, low, PY + 1, "dark_oak_fence")
        C.barrier_line(a, low, PY + 2, PY + 4)
        high = [(lx, 193) for lx in range(76, 101)] + [(101, lz) for lz in range(194, 201)] + [(75, lz) for lz in range(197, 201)]
        high = [self.w(lx, lz) for (lx, lz) in high]
        C.rail(a, high, G, "dark_oak_fence")
        C.barrier_line(a, high, G + 1, G + 3)
        # chain lift cages hanging beside the platform
        for lx in (60, 96, 118):
            x, z = self.w(lx, 168)
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    a.set(x + dx, PY, z + dz, B("dark_oak_planks"))
                    if abs(dx) == 1 or abs(dz) == 1:
                        for y in range(PY + 1, PY + 4):
                            a.set(x + dx, y, z + dz, B("iron_bars"))
                    a.set(x + dx, PY + 4, z + dz, B("dark_oak_slab"))
            for y in range(PY + 5, self.MT + 1):
                a.set(x, y, z, B("chain"))
            a.set(x, PY + 3, z, B("soul_lantern", hanging=1))
        # windlass on the head platform
        wx, wz = self.w(94, 197)
        for dz in range(-2, 3):
            a.set(wx, G + 1, wz + dz, B("dark_oak_log", axis="z"))
        a.set(wx, G, wz - 2, B("dark_oak_fence"))
        a.set(wx, G, wz + 2, B("dark_oak_fence"))
        for y in range(G + 2, self.MT + 1):
            a.set(wx, y, wz, B("chain"))
        self.allow(38, 166, 128, 204, DF - 2, G + 6)
        self.add_zone("c4", (self.x0 + 46, PY, self.z0 + 172, self.x0 + 124, PY + 4, self.z0 + 193), floor_mask=None, n=10)

    # ------------------------------------------------------------ c5: the dock floor and Hraesvelgr's pen
    def dock_floor_zone(self):
        a, rng, pal = self.a, self.rng, self.pal
        # timber stacks, nail heaps, braziers, half-built ribs
        for _ in range(24):
            lx, lz = rng.randint(44, 122), rng.randint(72, 168)
            x, z = self.w(lx, lz)
            if a.get(x, DF, z) != AIR:
                continue
            r = rng.random()
            if r < 0.3:
                axis = rng.choice(["x", "z"])
                for k in range(5):
                    for h in range(rng.randint(1, 3)):
                        a.put(x + (k if axis == "x" else 0), DF + h, z + (k if axis == "z" else 0), B("dark_oak_log", axis=axis))
            elif r < 0.6:
                rr = rng.uniform(1.4, 2.6)
                for dx in range(-3, 4):
                    for dz in range(-3, 4):
                        dd = math.hypot(dx, dz)
                        if dd <= rr:
                            for t in range(int((rr - dd) * 0.9) + 1):
                                a.put(x + dx, DF + t, z + dz, B("bone_block", axis="y") if rng.random() < 0.5 else B("calcite"))
            elif r < 0.75:
                P.brazier(a, x, DF, z, soul=True)
            else:
                # a rib of a new ship: a white arc
                for t in range(9):
                    ang = math.pi * t / 8
                    a.put(x + int(round(math.cos(ang) * 4)), DF + int(round(math.sin(ang) * 5)), z, B("bone_block", axis="y"))
        self.add_zone("c5", (self.x0 + 42, DF - 2, self.z0 + 72, self.x0 + 124, DF + 3, self.z0 + 168), floor_mask=None, n=12)
        # the pen
        lx1, lz1, lx2, lz2 = 64, 24, 108, 68
        for lx in range(lx1, lx2 + 1):
            for lz in range(lz1, lz2 + 1):
                edge = lx in (lx1, lx1 + 1, lx2 - 1, lx2) or lz in (lz1, lz1 + 1, lz2 - 1, lz2)
                if edge:
                    x, z = self.w(lx, lz)
                    for y in range(DF, DF + 16):
                        a.set(x, y, z, pal.trim if (y - DF) % 5 == 4 else pal.wall())
                    a.set(x, DF + 16, z, pal.top)
        cx, cz = self.w(86, 46)
        R = 17

        def floor_fn(x, z, d):
            ang = math.atan2(z - cz, x - cx)
            feather = (int(ang * 9 / math.pi) % 2 == 0) and 4 < d < R - 1
            if d > R - 1:
                return B("polished_basalt", pillar_axis="y")
            return B("white_concrete") if feather and int(d) % 4 == 0 else B("light_gray_concrete") if feather else B("polished_blackstone")
        ex, ez = self.w(86, 67)
        entry = self.doorway(ex, DF, ez, 5, 6, "x")
        for p in self.doorway(ex, DF, ez + 1, 5, 6, "x"):
            a.set(*p, AIR)
        for p in entry:
            a.set(*p, AIR)
        xx, zz = self.w(86, 25)
        exitg = self.doorway(xx, DF, zz, 5, 6, "x")
        for p in self.doorway(xx, DF, zz - 1, 5, 6, "x"):
            a.set(*p, AIR)
        self.arena("c5_mid", cx, DF, cz, R, "hraesvelgr", "mid2", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # the cage roof: chains strung across the top, feathers and bones on the floor
        for k in range(-18, 19, 6):
            for t in range(-20, 21):
                a.put(cx + t, DF + 15, cz + k, B("chain", axis="x"))
        for _ in range(26):
            ang, r = rng.uniform(0, 6.28), rng.uniform(R + 0.5, R + 3)
            x, z = int(cx + math.cos(ang) * r), int(cz + math.sin(ang) * r)
            if a.get(x, DF, z) == AIR:
                a.set(x, DF, z, B(rng.choice(["white_carpet", "light_gray_carpet", "bone_block"])))
        self.allow(62, 12, 110, 70, DF - 2, DF + 6)

    # ------------------------------------------------------------ the boarding tower and gangway
    def boarding(self):
        a, rng, tim = self.a, self.rng, self.tim
        # tower shell (timber), interior x 76..100, z 15..22
        for lx in range(74, 103):
            for lz in range(14, 24):
                x, z = self.w(lx, lz)
                edge = lx in (74, 75, 101, 102) or lz in (14, 23)
                for y in range(DF, G + 6):
                    if edge:
                        a.set(x, y, z, B("dark_oak_log", axis="y") if (lx + lz) % 6 == 0 else B("spruce_planks"))
        # opening from the pen exit
        px, pz = self.w(86, 23)
        for dx in range(-2, 3):
            for y in range(DF, DF + 6):
                a.set(px + dx, y, pz, AIR)
        # flight A: west along z 21..19 from x 98 (44 -> 54); flight B: east along z 15..17 from x 89 (54 -> 64)
        fa = self.w(98, 21)
        C.flight(a, fa[0], DF, fa[1], "west", 10, 3, "spruce_stairs", support=None, centre=False)
        for lx in range(84, 89):
            for lz in range(15, 22):
                x, z = self.w(lx, lz)
                a.set(x, DF + 9, z, B("spruce_planks"))
        fb = self.w(89, 15)
        C.flight(a, fb[0], DF + 10, fb[1], "east", 10, 3, "spruce_stairs", support=None, centre=False)
        # gangway: east along z 15..17, south along x 140..142, then east onto the foredeck at z 49..51
        edge_x = min(lx for (lx, lz) in self.deck_cells if lz == 50)
        cells = [(lx, lz) for lx in range(99, 143) for lz in range(15, 18)]
        cells += [(lx, lz) for lx in range(140, 143) for lz in range(18, 52)]
        cells += [(lx, lz) for lx in range(143, edge_x) for lz in range(49, 52)]
        self.walkway(cells, G - 1, open_cells={(lx, lz) for lx in range(84, 99) for lz in range(14, 19)})
        for lz in range(49, 52):
            for lx in range(edge_x, edge_x + 2):
                x, z = self.w(lx, lz)
                for y in range(DK, DK + 3):
                    a.set(x, y, z, AIR)
        self.allow(72, 12, 164, 44, DF - 2, G + 6)

    # ------------------------------------------------------------ walkways (bridges with rails)
    def walkway(self, cells, y, posts=8, plank="dark_oak_planks", fence="dark_oak_fence", open_cells=()):
        """Plank walk at block level y over the given local cells; fences on every neighbouring cell that is open
        at y (so nobody falls off), timber posts down to the water every `posts` cells."""
        a = self.a
        S = set(cells)
        for (lx, lz) in S:
            x, z = self.w(lx, lz)
            a.set(x, y, z, B(plank))
            for yy in range(y + 1, y + 5):
                a.set(x, yy, z, AIR)
            if (lx + lz) % posts == 0:
                for yy in range(DF - 7, y):
                    if a.get(x, yy, z) in (AIR, B("water")):
                        a.set(x, yy, z, B("dark_oak_log", axis="y"))
        ring = set()
        for (lx, lz) in S:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    c = (lx + dx, lz + dz)
                    if c not in S and c not in open_cells:
                        ring.add(c)
        for (lx, lz) in ring:
            x, z = self.w(lx, lz)
            if a.get(x, y, z) == AIR and a.get(x, y + 1, z) == AIR:
                a.set(x, y + 1, z, B(fence))

    # ------------------------------------------------------------ Naglfar
    ZB, ZE, CXS = 30, 182, 160

    def hw(self, lz):
        t = (lz - self.ZB) / float(self.ZE - self.ZB)
        if t < 0 or t > 1:
            return 0.0
        bow = math.sin(min(1.0, t / 0.42) * math.pi / 2) ** 0.7
        stern = 1 - 0.2 * max(0.0, (t - 0.72) / 0.28) ** 2
        return 26.0 * bow * stern

    def deck_y(self, lz):
        return DS - 1 if lz >= 136 else DK - 1

    def ship(self):
        a, rng = self.a, self.rng
        KY = DF + 1
        nails = [B("bone_block", axis="x"), B("calcite"), B("white_terracotta"), B("bone_block", axis="z"), B("dripstone_block")]
        deck_mix = mixer(rng, [(B("dark_oak_planks"), 5), (B("spruce_planks"), 2), (B("stripped_dark_oak_log", axis="z"), 1)])
        D = {}
        for lz in range(self.ZB, self.ZE + 1):
            hwz = self.hw(lz)
            if hwz < 0.8:
                continue
            dy = self.deck_y(lz)
            for y in range(KY, dy + 1):
                frac = min(1.0, (y - KY + 1) / float(DK - KY))
                half = hwz * frac ** 0.45
                r = int(math.ceil(half))
                for dx in range(-r, r + 1):
                    if abs(dx) > half + 0.3:
                        continue
                    x, z = self.w(self.CXS + dx, lz)
                    shell = abs(dx) > half - 1.6 or y == KY
                    if y == dy:
                        a.set(x, y, z, deck_mix())
                        D[(self.CXS + dx, lz)] = dy
                    elif shell:
                        a.set(x, y, z, nails[((y - KY) // 2 + lz // 9) % len(nails)])
                    else:
                        a.set(x, y, z, B("dark_oak_planks"))
                for yy in range(dy + 1, dy + 6):
                    for dx in range(-r, r + 1):
                        if abs(dx) <= half + 0.3:
                            x, z = self.w(self.CXS + dx, lz)
                            a.set(x, yy, z, AIR)
        self.deck_cells = D
        # gunwale: a nail rail with a fence on every deck cell that touches the outside
        edges = [c for c in D if any((c[0] + dx, c[1] + dz) not in D for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        self.deck_edges = set(edges)
        for (lx, lz) in edges:
            x, z = self.w(lx, lz)
            dy = D[(lx, lz)]
            a.set(x, dy + 1, z, B("polished_basalt", pillar_axis="y"))
            a.set(x, dy + 2, z, B("dark_oak_fence"))
        # shields hung outside the rail amidships
        cols = ["black_wool", "purple_wool", "gray_wool", "white_wool"]
        for (lx, lz) in edges:
            if lz % 2 or not (40 <= lz <= 178):
                continue
            side = 1 if lx > self.CXS else -1
            x, z = self.w(lx + side, lz)
            if a.get(x, D[(lx, lz)], z) == AIR:
                a.set(x, D[(lx, lz)], z, B(cols[(lz // 2) % 4]))
        # cradles and keel blocks in the water
        for lz in range(self.ZB + 6, self.ZE - 2, 12):
            for dx in (-6, -5, 5, 6):
                x, z = self.w(self.CXS + dx, lz)
                for y in range(DF - 7, KY):
                    a.set(x, y, z, B("polished_blackstone_bricks"))
        for lz in range(self.ZB + 2, self.ZE):
            x, z = self.w(self.CXS, lz)
            a.set(x, KY - 1, z, B("dark_oak_log", axis="z"))
        self.bow_head()
        self.deck_dressing()
        self.stern()

    def bow_head(self):
        """The prow: a serpent of bone rising from the stem, soul fire in its eyes."""
        a = self.a
        cx = self.x0 + self.CXS
        z0 = self.z0
        bone = B("bone_block", axis="y")
        pts = [(cx, 50, z0 + 31), (cx, 66, z0 + 29), (cx, 76, z0 + 25), (cx, 84, z0 + 21), (cx, 88, z0 + 17)]
        for p0, p1 in zip(pts[:-1], pts[1:]):
            thick_line(a, p0, p1, 1.4, bone)
        ell(a, cx, 89, z0 + 14, 2.6, 2.2, 3.8, bone)
        ell(a, cx, 86.5, z0 + 13, 2.0, 1.0, 3.0, B("calcite"))
        for s in (-1, 1):
            a.set(cx + 2 * s, 90, z0 + 12, B("soul_lantern"))
            thick_line(a, (cx + s, 91, z0 + 16), (cx + 3 * s, 95, z0 + 19), 0.5, B("dripstone_block"))
        for k in range(4):
            a.set(cx - 1 + (k % 2) * 2, 85, z0 + 11 + k, B("pointed_dripstone", dripstone_thickness="tip", hanging=1))

    def deck_dressing(self):
        a, rng = self.a, self.rng
        D = self.deck_cells
        cx = self.CXS
        # hatches
        for lz0 in (48, 74, 102):
            for dx in range(-3, 4):
                for dz in range(0, 6):
                    x, z = self.w(cx + dx, lz0 + dz)
                    edge = abs(dx) == 3 or dz in (0, 5)
                    a.set(x, DK - 1, z, B("stripped_dark_oak_log", axis="x") if edge else B("spruce_trapdoor", direction=0))
        # masts with yards and grey sails, chains for rigging
        for mz in (60, 90, 120):
            for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                x, z = self.w(cx + dx, mz + dz)
                for y in range(DK, 114):
                    a.set(x, y, z, B("dark_oak_log", axis="y"))
            yard_y = 106
            for dx in range(-24, 26):
                x, z = self.w(cx + dx, mz - 1)
                a.set(x, yard_y, z, B("stripped_dark_oak_log", axis="x"))
            for dx in range(-21, 23):
                stripe = (dx + 21) // 3 % 2
                for y in range(84, yard_y):
                    x, z = self.w(cx + dx, mz - 2)
                    belly = int(1.5 * math.sin(math.pi * (y - 84) / 22.0))
                    a.set(x, y, z - belly, B("gray_wool") if stripe else B("light_gray_wool"))
            # the emblem: a pale hand of nails on the main sail
            if mz == 90:
                for (dx, dy) in [(0, 0), (0, 1), (0, 2), (0, 3), (-1, 0), (1, 0), (-1, 1), (1, 1), (-2, 4), (-1, 4), (0, 5), (1, 4), (2, 4),
                                 (-2, 5), (2, 5), (-3, 6), (3, 6), (0, 6), (0, 7), (-1, 7), (1, 7)]:
                    x, z = self.w(cx + dx, mz - 2)
                    y = 90 + dy
                    belly = int(1.5 * math.sin(math.pi * (y - 84) / 22.0))
                    a.set(x, y, z - belly, B("white_wool"))
            x0, z0 = self.w(cx, mz)
            for side in (-1, 1):
                for dzr in (-8, 8):
                    tgt_lz = mz + dzr
                    hwz = int(round(self.hw(tgt_lz))) - 1
                    for q in line_points((x0 + side, 112, z0), (x0 + side * hwz, DK + 1, z0 + dzr), step=0.6):
                        xx, yy, zz = (int(round(c)) for c in q)
                        if a.get(xx, yy, zz) == AIR:
                            a.set(xx, yy, zz, B("chain"))
        # rowing benches and oars along both sides
        for lz in range(40, 132, 4):
            hwz = int(round(self.hw(lz)))
            for side in (-1, 1):
                for k in range(2, 6):
                    x, z = self.w(cx + side * (hwz - k), lz)
                    if a.get(x, DK, z) == AIR:
                        a.set(x, DK, z, B("spruce_slab"))
                for q in line_points((self.x0 + cx + side * (hwz + 1), DK - 2, self.z0 + lz), (self.x0 + cx + side * (hwz + 9), DF + 2, self.z0 + lz), step=0.5):
                    xx, yy, zz = (int(round(c)) for c in q)
                    if a.get(xx, yy, zz) == AIR:
                        a.set(xx, yy, zz, B("dark_oak_fence"))
        # cargo, coiled chains, lanterns
        for _ in range(40):
            lz = rng.randint(40, 130)
            hwz = int(self.hw(lz)) - 7
            if hwz < 2:
                continue
            dx = rng.randint(-hwz, hwz)
            x, z = self.w(cx + dx, lz)
            if a.get(x, DK, z) != AIR or a.get(x, DK - 1, z) == B("spruce_trapdoor", direction=0):
                continue
            r = rng.random()
            if r < 0.4:
                a.set(x, DK, z, B("barrel"))
            elif r < 0.6:
                a.set(x, DK, z, B("bone_block", axis="y"))
            elif r < 0.75:
                a.set(x, DK, z, B("chain", axis="x"))
        for lz in range(44, 132, 16):
            for side in (-1, 1):
                hwz = int(round(self.hw(lz))) - 2
                x, z = self.w(cx + side * hwz, lz)
                for y in range(DK, DK + 3):
                    a.set(x, y, z, B("dark_oak_fence"))
                a.set(x, DK + 3, z, B("soul_lantern"))
        self.add_zone("c6", (self.x0 + 138, DK - 1, self.z0 + 40, self.x0 + 182, DK + 4, self.z0 + 130), floor_mask=None, n=12)
        self.allow(130, 26, 190, 136, DK - 2, DK + 6)

    def stern(self):
        a, rng = self.a, self.rng
        cx, cz = self.w(self.CXS, 158)
        R = 19
        D = self.deck_cells
        # front breastwork across the stern deck with the entry gate, stairs up from the main deck
        for (lx, lz), dy in D.items():
            if lz == 136:
                x, z = self.w(lx, lz)
                for y in range(DS, DS + 4):
                    a.set(x, y, z, B("polished_basalt", pillar_axis="y") if (lx % 4) else B("chiseled_polished_blackstone"))
                C.barrier_line(a, [(x, z)], DS + 4, DS + 7)
        fx, fz = self.w(self.CXS, 130)
        C.flight(a, fx, DK, fz, "south", DS - DK, 5, "dark_oak_stairs", support=B("dark_oak_planks"))
        for lz in range(130, 136):
            for lx in (self.CXS - 3, self.CXS + 3):
                x, z = self.w(lx, lz)
                for y in range(DK, DK + (lz - 130) + 2):
                    a.set(x, y, z, B("dark_oak_planks"))
                a.set(x, DK + (lz - 130) + 2, z, B("dark_oak_fence"))
        entry = self.doorway(cx, DS, self.z0 + 136, 5, 4, "x")
        for p in entry:
            a.set(*p, AIR)

        def floor_fn(x, z, d):
            lz = z - self.z0
            if d < 2.5:
                return B("chiseled_polished_blackstone")
            if abs(d - 6) < 0.6 or (d < 6 and (x - cx == 0 or z - cz == 0)):
                return B("gilded_blackstone")
            if abs(d - R + 0.5) < 0.7:
                return B("polished_basalt", pillar_axis="y")
            frost = ((x * 13 + z * 7) % 17 == 0) or (abs(d - 13) < 0.5 and (x + z) % 3 == 0)
            if frost:
                return B("light_blue_terracotta")
            return B("dark_oak_planks") if (lz // 2) % 2 else B("spruce_planks")
        ar = self.arena("boss", cx, DS, cz, R, "hrym", "final", floor_fn=floor_fn, entry=entry)
        # rear breastwork (transom) with the exit gate, gangway to the portal pier
        for (lx, lz), dy in D.items():
            if lz == self.ZE:
                x, z = self.w(lx, lz)
                for y in range(DS, DS + 4):
                    a.set(x, y, z, B("polished_basalt", pillar_axis="y"))
                C.barrier_line(a, [(x, z)], DS + 4, DS + 7)
        exitg = self.doorway(cx, DS, self.z0 + self.ZE, 3, 3, "x")
        for p in exitg:
            a.set(*p, AIR)
        self.walkway([(lx, lz) for lx in range(self.CXS - 1, self.CXS + 2) for lz in range(self.ZE + 1, 193)], DS - 1,
                     open_cells={(lx, self.ZE) for lx in range(self.CXS - 1, self.CXS + 2)} | {(lx, 193) for lx in range(self.CXS - 1, self.CXS + 2)})
        for lx in range(self.CXS - 1, self.CXS + 2):
            x, z = self.w(lx, 192)
            for y in range(DS, DS + 4):
                a.set(x, y, z, AIR)
        ar["exit"] = [list(p) for p in exitg]
        self.close(exitg)
        self.exit_portal(cx, DS, self.z0 + 200)
        # the great steering oar on the starboard quarter and the tiller
        hwz = int(round(self.hw(172)))
        sx = self.x0 + self.CXS + hwz
        thick_line(a, (sx + 1, DS + 4, self.z0 + 170), (sx + 4, DF + 1, self.z0 + 178), 1.1, B("dark_oak_log", axis="y"))
        for dz in range(-1, 6):
            for y in range(DF - 2, DF + 6):
                a.put(sx + 4, y, self.z0 + 176 + dz, B("dark_oak_planks"))
        for k in range(0, 7):
            a.set(sx - k, DS + 2, self.z0 + 171, B("stripped_dark_oak_log", axis="x"))
        # stern lanterns on tall posts at the corners
        for side in (-1, 1):
            hz = int(round(self.hw(self.ZE - 1))) - 1
            x, z = self.w(self.CXS + side * hz, self.ZE - 1)
            for y in range(DS, DS + 8):
                a.set(x, y, z, B("dark_oak_log", axis="y"))
            a.set(x, DS + 8, z, B("polished_blackstone"))
            a.set(x, DS + 9, z, B("soul_lantern"))
        self.allow(130, 134, 190, 210, DS - 8, DS + 6)

    # ------------------------------------------------------------ finishing
    def finish(self):
        a = self.a
        self.roofscape()
        for (lx1, lz1, lx2, lz2, y1, y2) in ((40, 14, 240, 200, DF, DF + 4), (40, 166, 128, 204, DF + 9, DF + 12),
                                            (120, 212, 250, 294, G, G + 3), (60, 200, 120, 262, G, G + 3)):
            x1, z1 = self.w(lx1, lz1)
            x2, z2 = self.w(lx2, lz2)
            self.light_fill((x1, z1, x2, z2), (y1, y2), level=7, threshold=4, spacing=7)
        self.ambient = [dict(box=self.zones["c3"]["box"], particle="minecraft:soul_particle", rate=2),
                        dict(box=self.zones["c5"]["box"], particle="minecraft:basic_smoke_particle", rate=1),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:soul_particle", rate=1)]
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        a.fix_walls()

    def is_escape(self, x, y, z):
        for (x1, y1, z1, x2, y2, z2) in self.walk_boxes:
            if x1 <= x <= x2 and y1 <= y <= y2 and z1 <= z <= z2:
                return False
        return True


def build(seed=1):
    d = Naglfar("d05", seed)
    d.build()
    return d
