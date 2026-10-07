"""Dungeon 6 — 우트가르드 거인 성채 (Utgard Citadel). Mid tier, 272 x 448, castle type, everything giant-sized.

South -> north: the fjord landing and the grey moor; Skrymir's glove lying in the rock pass (Thor took it for a hall,
and its thumb for a side room); the 40-block gate; the outer bailey with a giant's cart, barrels and axe; the eating
contest hall and Logi's fire pit (mid-boss 1); the pillared racecourse; the banquet hall with the drinking horn that
reaches the sea and the grey cat that is really the world serpent; Elli's wrestling ring (mid-boss 2); the hall of
illusions; and Utgarda-Loki's throne room.

Local coordinates: x 0..271 (west -> east), z 0..447 (north -> south). Feet level 64 everywhere inside.
"""
import math

import numpy as np

from mcw import B, AIR, PAL
from gen_common import fbm, stair, slab, standing_sign, line_points, boulder, spruce_tree
import nr_parts as P
import nr_castle as C
from nr_dungeon import mixer
from nr_fortress import Fortress
from nr_spawn import cyl, ell, thick_line

SEA = 62
G = 64
HT = 34                       # hall height (feet 64 .. 97)


class Utgard(Fortress):
    Y0, SY = 48, 128          # 48..175
    MT = 104

    def build(self):
        rng = self.rng
        self.setup()
        self.pal = C.Pal(rng, wall=[("stone_bricks", 6), ("cracked_stone_bricks", 1), ("andesite", 1)], trim="polished_deepslate",
                         floor=[("polished_andesite", 3), ("stone_bricks", 2), ("andesite", 1)], roof="deepslate_tile",
                         pillar="polished_deepslate", window="blue_stained_glass_pane", light="lantern", accent="chiseled_stone_bricks",
                         top="stone_brick_wall", plank="spruce_planks")
        self.body = [B("stone_bricks"), B("andesite"), B("stone"), B("stone_bricks"), B("tuff")]
        self.terrain()
        self.landing()
        self.glove()
        self.citadel()
        self.bailey()
        self.eating_hall()
        self.logi_pit()
        self.racecourse()
        self.banquet()
        self.elli_ring()
        self.illusions()
        self.throne_room()
        self.finish()

    # ------------------------------------------------------------ terrain: fjord, moor, cliffs, the pass
    def terrain(self):
        a, rng = self.a, self.rng
        rock = [B("stone"), B("andesite"), B("stone"), B("tuff"), B("diorite"), B("stone")]
        for j in range(G - self.Y0):
            y = j + self.Y0
            a.blk[:, j, :] = rock[(y // 4) % len(rock)]
        n = fbm(self.sx, self.sz, 16, 4, self.seed + 3)
        self.H = np.full((self.sx, self.sz), G - 1)
        moor = mixer(rng, [(B("coarse_dirt"), 3), (B("gravel"), 1), (B("podzol"), 1), (B("grass_block"), 2), (B("stone"), 1)])
        snow = mixer(rng, [(B("snow"), 3), (B("grass_block"), 1)])
        self.water = np.zeros((self.sx, self.sz), bool)
        for i in range(self.sx):
            for k in range(290, self.sz):
                col = a.blk[i, :, k]
                fj = math.hypot((i - 136) / 108.0, (k - 452) / 34.0) < 1 or (abs(i - 136) < 18 + (k - 432) and k > 432)
                cliff = i < 20 or i > 250 or (k >= 420 and not fj)
                if fj:
                    depth = 8 + int(6 * n[i, k])
                    for y in range(SEA - depth + 1, SEA + 1):
                        col[y - self.Y0] = B("water")
                    col[SEA - depth - self.Y0] = B("gravel")
                    self.H[i, k] = SEA - depth
                    self.water[i, k] = True
                elif cliff:
                    h = int(100 + n[i, k] * 30)
                    for y in range(G, h + 1):
                        col[y - self.Y0] = rock[(y // 3 + i // 9) % len(rock)]
                    if h > 112:
                        col[h - self.Y0] = B("snow")
                    self.H[i, k] = h
                elif k >= 364:
                    col[G - 1 - self.Y0] = snow() if n[i, k] > 0.62 else moor()
                    if n[i, k] > 0.66 and rng.random() < 0.7:
                        col[G - self.Y0] = B("snow_layer", height=rng.randint(0, 1))
        # the rock pass the glove lies in (filled up to 76 with sheer faces) and the plaza in front of the gate
        self.pass_top = 76
        for i in range(20, 251):
            for k in range(290, 360):
                col = a.blk[i, :, k]
                for y in range(G, self.pass_top + 1):
                    col[y - self.Y0] = rock[(y // 3 + i // 7 + k // 11) % len(rock)]
                col[self.pass_top + 1 - self.Y0] = B("snow") if rng.random() < 0.6 else B("stone")
                for y in range(self.pass_top + 2, self.pass_top + 6):
                    col[y - self.Y0] = B("barrier")
        for i in range(112, 161):
            for k in range(290, 298):
                col = a.blk[i, :, k]
                col[G - self.Y0:] = AIR
                col[G - 1 - self.Y0] = self.pal.floor()
        self.allow(0, 290, 271, 447, 40, 72)
        a.bio[:, :] = 3
        a.bio[:, :300] = 5

    def landing(self):
        a, rng = self.a, self.rng
        for lz in range(410, 436):
            for lx in (135, 136, 137):
                x, z = self.w(lx, lz)
                a.set(x, SEA + 1, z, B("spruce_planks"))
                for y in range(SEA + 2, SEA + 6):
                    a.set(x, y, z, AIR)
                if lx != 136 and lz % 4 == 0:
                    for y in range(SEA - 12, SEA + 1):
                        if a.get(x, y, z) in (B("water"), AIR, B("gravel")):
                            a.set(x, y, z, B("spruce_log", axis="y"))
                    a.set(x, SEA + 2, z, B("spruce_fence"))
                    if lz % 8 == 0:
                        a.set(x, SEA + 3, z, B("lantern"))
        sx, sz = self.w(142, 444)
        info = P.longship(a, sx, SEA, sz, "north", rng, length=29, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        ax, az = self.w(136, 412)
        self.data["start"] = [ax + 0.5, SEA + 2, az + 0.5, 180]
        self.walk_seeds = [(ax, SEA + 2, az)]
        standing_sign(a, ax - 2, G, az - 4, 8, "§l§9우트가르드 거인 성채\n§r§f환영의 거인왕이\n§f사는 곳\n§7장갑 안으로 들어가세요", kind="spruce_standing_sign")
        # the road north to the glove, boulders, dead spruces, a cairn
        for lz in range(364, 412):
            for dx in range(-3, 4):
                x, z = self.w(136 + dx + int(3 * math.sin(lz / 9.0)), lz)
                a.set(x, G - 1, z, B("gravel") if rng.random() < 0.7 else B("coarse_dirt"))
                a.set(x, G, z, AIR)
        for _ in range(70):
            lx, lz = rng.randint(24, 246), rng.randint(366, 418)
            if abs(lx - 136) < 9:
                continue
            x, z = self.w(lx, lz)
            if self.water[lx, lz] or a.get(x, G, z) not in (AIR, B("snow_layer", height=0), B("snow_layer", height=1)):
                continue
            r = rng.random()
            if r < 0.25:
                boulder(a, x, G, z, rng, rng.uniform(1.4, 3.4), [B("stone"), B("andesite"), B("cobblestone"), B("diorite")])
            elif r < 0.4:
                spruce_tree(a, x, G, z, rng, h=rng.randint(7, 12))
            elif r < 0.55:
                a.set(x, G, z, B("deadbush"))
            else:
                a.set(x, G, z, B(rng.choice(["short_grass", "fern", "short_grass"])))
        cx, cz = self.w(118, 392)
        for k in range(6):
            for dx in range(-(3 - k // 2), 4 - k // 2):
                for dz in range(-(3 - k // 2), 4 - k // 2):
                    a.set(cx + dx, G + k, cz + dz, B("cobblestone") if (dx + dz + k) % 3 else B("mossy_cobblestone"))
        a.set(cx, G + 6, cz, B("lantern"))

    # ------------------------------------------------------------ c1: Skrymir's glove
    def glove(self):
        """A leather glove ~70 long lying palm-down in the pass: cuff open to the south, four finger tunnels to the
        north (the middle one torn open at the tip), the thumb a side room to the east."""
        a, rng = self.a, self.rng
        leather = mixer(rng, [(B("brown_terracotta"), 5), (B("brown_concrete"), 1), (B("mud_bricks"), 1)])
        lining = mixer(rng, [(B("brown_wool"), 3), (B("red_terracotta"), 1)])
        seam = B("light_gray_terracotta")
        cx = 136

        def palm_hx(lz):
            if lz >= 350:
                return 24.0
            return 27.0
        # palm + cuff: elliptical tube along z
        for lz in range(316, 364):
            hx = palm_hx(lz)
            hy = 18.0 if lz < 350 else 16.0
            yc = 70
            for lx in range(cx - 30, cx + 31):
                for y in range(G - 2, yc + 20):
                    d = math.hypot((lx - cx) / hx, (y - yc) / hy)
                    if d > 1:
                        continue
                    x, z = self.w(lx, lz)
                    inner = math.hypot((lx - cx) / (hx - 2.2), (y - yc) / (hy - 2.2)) < 1
                    if inner and y >= G:
                        a.set(x, y, z, AIR)
                    elif inner:
                        a.set(x, y, z, lining() if y == G - 1 else B("dirt"))
                    else:
                        a.set(x, y, z, seam if (lx - cx) % 9 == 0 and d > 0.93 else leather())
        # fingers: tubes from the palm front (z 318) to their tips; centre y 66, outer r 5.5, inner r 3.5
        fingers = [(-19, 304), (-6, 296), (7, 299), (20, 308)]
        self.finger_tips = []
        for (ox, tip) in fingers:
            fx = cx + ox
            for lz in range(tip, 322):
                taper = 1.0 if lz > tip + 4 else 0.75 + 0.06 * (lz - tip)
                ro, ri = 5.5 * taper, 3.5 * taper
                for lx in range(fx - 7, fx + 8):
                    for y in range(G - 2, G + 9):
                        d = math.hypot(lx - fx, (y - 66) * 1.0)
                        if d > ro:
                            continue
                        x, z = self.w(lx, lz)
                        if d < ri and y >= G:
                            a.set(x, y, z, AIR)
                        elif d < ri:
                            a.set(x, y, z, lining() if y == G - 1 else B("dirt"))
                        elif lz > 316 and math.hypot((lx - cx) / 27.0, (y - 70) / 18.0) < 0.92:
                            continue                    # inside the palm already
                        else:
                            a.set(x, y, z, seam if lz % 7 == 0 else leather())
            # fingertip cap (rounded) except the torn middle finger
            if ox != -6:
                for lx in range(fx - 6, fx + 7):
                    for y in range(G - 1, G + 8):
                        for lz in range(tip - 3, tip + 1):
                            if math.hypot(lx - fx, y - 66, (lz - tip) * 1.4) < 4.6:
                                x, z = self.w(lx, lz)
                                a.set(x, y, z, leather())
            self.finger_tips.append((fx, tip))
        # the torn tip of the middle finger opens onto the plaza in front of the gate
        fx = cx - 6
        for lz in range(290, 300):
            for lx in range(fx - 3, fx + 4):
                x, z = self.w(lx, lz)
                for y in range(G, G + 4):
                    a.set(x, y, z, AIR)
                a.set(x, G - 1, z, self.pal.floor())
        for lz in range(296, 300):
            for lx in (fx - 4, fx + 4):
                x, z = self.w(lx, lz)
                for y in range(G, G + 5):
                    if rng.random() < 0.6:
                        a.set(x, y, z, B("brown_terracotta"))
                a.set(x, G + 5, z, B("web") if rng.random() < 0.3 else B("brown_terracotta"))
        # the thumb: a side room to the east, angled
        tx0, tz0 = cx + 24, 342
        tx1, tz1 = cx + 40, 326
        L = math.dist((tx0, tz0), (tx1, tz1))
        for t in range(int(L) + 1):
            u = t / L
            px, pz = tx0 + (tx1 - tx0) * u, tz0 + (tz1 - tz0) * u
            ro, ri = 7.5, 5.2
            for lx in range(int(px) - 9, int(px) + 10):
                for lz in range(int(pz) - 9, int(pz) + 10):
                    dd = math.hypot(lx - px, lz - pz)
                    if dd > ro:
                        continue
                    for y in range(G - 2, G + 12):
                        d = math.hypot(dd, (y - 68) * 1.1)
                        if d > ro:
                            continue
                        x, z = self.w(lx, lz)
                        if d < ri and y >= G:
                            a.set(x, y, z, AIR)
                        elif d < ri:
                            a.set(x, y, z, lining() if y == G - 1 else B("dirt"))
                        elif math.hypot((lx - cx) / 24.7, (y - 70) / 15.8) < 1 and lz > 316:
                            continue
                        else:
                            a.set(x, y, z, leather())
        for lx in range(int(tx1) - 6, int(tx1) + 7):
            for lz in range(int(tz1) - 6, int(tz1) + 7):
                for y in range(G - 1, G + 10):
                    if math.hypot(lx - tx1, lz - tz1, (y - 68) * 1.1) < 6.0 and math.hypot(lx - tx1, lz - tz1, (y - 68) * 1.1) > 4.2:
                        x, z = self.w(lx, lz)
                        a.set(x, y, z, leather())
        # inside: the travellers' camp Thor's companions made, a few lanterns
        px, pz = self.w(cx, 338)
        a.set(px, G - 1, pz, B("cobblestone"))
        a.set(px, G, pz, B("campfire"))
        for (dx, dz) in ((-4, 2), (4, -2), (-3, -4)):
            a.set(px + dx, G, pz + dz, B("barrel"))
        for (lx, lz) in ((cx - 14, 330), (cx + 14, 330), (cx, 352), (cx - 10, 346), (cx + 10, 322)):
            x, z = self.w(lx, lz)
            y = G
            while a.get(x, y, z) == AIR and y < 100:
                y += 1
            if y < 100:
                for k in range(1, 4):
                    a.set(x, y - k, z, B("chain"))
                a.set(x, y - 4, z, B("lantern", hanging=1))
        self.allow(100, 290, 182, 364, G - 2, 88)
        self.add_zone("c1", (self.x0 + 108, G - 2, self.z0 + 298, self.x0 + 172, G + 3, self.z0 + 360), floor_mask=None, n=10)

    # ------------------------------------------------------------ the citadel: outer wall, gate, towers
    def citadel(self):
        a, rng, pal = self.a, self.rng, self.pal
        self.mass(14, 14, 257, 289, G - 1, self.MT, self.body)
        # outer face: trim courses and a crenellated top along the south front
        for lx in range(14, 258):
            x, z = self.w(lx, 289)
            for y in range(G, self.MT + 1):
                if (y - G) % 10 == 9:
                    a.set(x, y, z, pal.trim)
                elif lx % 12 == 0:
                    a.set(x, y, z, pal.pillar)
            a.set(x, self.MT + 1, z, pal.wall())
            if (lx // 2) % 2 == 0:
                a.set(x, self.MT + 2, z, pal.wall())
                a.set(x, self.MT + 3, z, pal.top)
        # the 40-block gate with a raised portcullis and the doors swung open against the passage walls
        gx, gz = self.w(136, 285)
        self.carve(128, 280, 144, 290, G, G + 39, floor_b=pal.floor)
        for lz in range(280, 291):
            for k in range(1, 7):
                for lx in (128 + k - 1, 144 - k + 1):
                    x, z = self.w(lx, lz)
                    a.set(x, G + 33 + k, z, pal.wall())
        for lx in range(129, 144):
            x, z = self.w(lx, 288)
            for y in range(G + 30, G + 34):
                a.set(x, y, z, B("iron_bars"))
            a.set(x, G + 34, z, pal.trim)
        for lx0 in (129, 143):
            for lz in range(281, 288):
                x, z = self.w(lx0, lz)
                for y in range(G, G + 34):
                    a.set(x, y, z, B("dark_oak_planks") if (y - G) % 9 not in (2, 7) else B("iron_block"))
        # gatehouse towers and corner towers rising above the wall
        for lx in (114, 158):
            x, z = self.w(lx, 290)
            C.tower(a, x, z, G, 66, 10, pal, roof="cone", windows=True)
        for lx in (22, 250):
            x, z = self.w(lx, 286)
            C.tower(a, x, z, G, 58, 8, pal, roof="cone", windows=True)
        # braziers in the plaza
        for lx in (126, 146):
            x, z = self.w(lx, 294)
            P.brazier(a, x, G, z, soul=False, base="cobblestone")
        self.allow(112, 290, 160, 297, 60, 72)

    def giant_barrel(self, x, y, z, r=5, h=12):
        a = self.a
        for dy in range(h):
            bulge = r + 0.8 * math.sin(math.pi * dy / (h - 1))
            band = dy in (1, 2, h - 3, h - 2)
            for dx in range(-r - 2, r + 3):
                for dz in range(-r - 2, r + 3):
                    d = math.hypot(dx, dz)
                    if d <= bulge:
                        a.set(x + dx, y + dy, z + dz, B("iron_block") if band and d > bulge - 1.2 else
                              B("spruce_planks") if d > bulge - 1.2 or dy in (0, h - 1) else B("barrel"))

    def ring(self, cx, cy, cz, r, plane, block, spokes=0, th=1.0):
        """Vertical ring (a wheel). plane: 'xy' (axle along z) or 'zy' (axle along x)."""
        a = self.a
        for t in range(int(2 * math.pi * r * 3)):
            ang = t / (r * 3.0)
            for dr in np.arange(0, th, 0.5):
                u, v = math.cos(ang) * (r - dr), math.sin(ang) * (r - dr)
                if plane == "xy":
                    a.set(int(round(cx + u)), int(round(cy + v)), cz, block)
                else:
                    a.set(cx, int(round(cy + v)), int(round(cz + u)), block)
        for s in range(spokes):
            ang = s / spokes * 2 * math.pi
            for q in line_points((0, 0, 0), (math.cos(ang) * r, math.sin(ang) * r, 0), step=0.5):
                u, v = q[0], q[1]
                if plane == "xy":
                    a.set(int(round(cx + u)), int(round(cy + v)), cz, block)
                else:
                    a.set(cx, int(round(cy + v)), int(round(cz + u)), block)

    # ------------------------------------------------------------ c2: the outer bailey
    def bailey(self):
        a, rng, pal = self.a, self.rng, self.pal
        ground = mixer(rng, [(B("polished_andesite"), 3), (B("stone_bricks"), 2), (B("gravel"), 1), (B("snow"), 1)])
        self.carve(30, 200, 240, 279, G, self.Y0 + self.SY - 2, floor_b=ground)
        for side in ("north", "west", "east"):
            self.facade(30, 200, 240, 279, side, G, self.MT - G + 1, pal, every=12, win=tuple(range(6, 15)) + tuple(range(20, 29)),
                        win_cols=(4, 5, 6, 7, 8), band=10, door_every=0, lamp="lantern")
        for lx in range(30, 241):
            x, z = self.w(lx, 279)
            a.put(x, G, z, B("snow_layer", height=1) if rng.random() < 0.3 else AIR)
        # the giant's cart: a plank bed you can walk under, four spoked wheels
        bx1, bz1, bx2, bz2 = 160, 222, 204, 238
        for lx in range(bx1, bx2 + 1):
            for lz in range(bz1, bz2 + 1):
                x, z = self.w(lx, lz)
                for y in (G + 12, G + 13):
                    a.set(x, y, z, B("spruce_planks") if (lx // 3) % 2 else B("dark_oak_planks"))
                if lx in (bx1, bx2) or lz in (bz1, bz2):
                    for y in range(G + 14, G + 18):
                        a.set(x, y, z, B("dark_oak_log", axis="y") if (lx + lz) % 6 == 0 else B("spruce_planks"))
        for (lx, lz) in ((166, 220), (198, 220), (166, 240), (198, 240)):
            x, z = self.w(lx, lz)
            self.ring(x, G + 8, z, 8, "xy", B("dark_oak_log", axis="z"), spokes=8)
            a.set(x, G + 8, z, B("iron_block"))
        for lz in range(220, 241):
            for lx in (166, 198):
                x, z = self.w(lx, lz)
                a.set(x, G + 8, z, B("dark_oak_log", axis="z"))
        # sacks on the cart, a wheel leaning against the east wall
        for (lx, lz) in ((170, 228), (182, 232), (194, 226)):
            x, z = self.w(lx, lz)
            ell(a, x, G + 18, z, 5, 4, 4, B("brown_wool"))
        x, z = self.w(237, 252)
        self.ring(x, G + 13, z, 13, "zy", B("dark_oak_log", axis="x"), spokes=10)
        # barrels, the axe in its chopping block, bones
        for (lx, lz) in ((54, 222), (70, 230), (50, 240), (226, 214)):
            x, z = self.w(lx, lz)
            self.giant_barrel(x, G, z, r=5, h=12)
        sx, sz = self.w(110, 254)
        cyl(a, sx, G, sz, 6.5, 6.5, 6, B("spruce_log", axis="y"))
        for dx in range(-6, 7):
            for dz in range(-6, 7):
                if math.hypot(dx, dz) <= 6.5:
                    a.set(sx + dx, G + 5, sz + dz, B("stripped_spruce_wood"))
        for k in range(10):
            for dz in range(-1, 2):
                a.set(sx - 4 + k, G + 5 - (k % 3 == 0), sz + dz, B("iron_block"))
            a.set(sx - 4 + k, G + 6, sz, B("iron_block") if k > 2 else AIR)
        thick_line(a, (sx + 2, G + 7, sz), (sx + 16, G + 34, sz + 10), 1.2, B("stripped_spruce_log", axis="y"))
        for _ in range(10):
            lx, lz = rng.randint(40, 230), rng.randint(206, 274)
            x, z = self.w(lx, lz)
            if a.get(x, G, z) == AIR and not (150 <= lx <= 210 and 214 <= lz <= 246):
                axis = rng.choice(["x", "z"])
                for k in range(rng.randint(5, 9)):
                    a.put(x + (k if axis == "x" else 0), G, z + (k if axis == "z" else 0), B("bone_block", axis=axis))
        for (lx, lz) in ((90, 270), (180, 270), (40, 206), (232, 206)):
            x, z = self.w(lx, lz)
            P.brazier(a, x, G, z, soul=False, base="cobblestone")
        # door into the eating hall
        self.carve(76, 196, 84, 199, G, G + 13, floor_b=pal.floor)
        x, z = self.w(80, 199)
        C.gate(a, x, z, G, "z", 9, 14, 4, pal, frame=True)
        self.allow(14, 14, 257, 289, 60, 100)
        self.add_zone("c2", (self.x0 + 34, G - 2, self.z0 + 204, self.x0 + 236, G + 3, self.z0 + 276), floor_mask=None, n=12)

    # ------------------------------------------------------------ c3: the eating contest hall
    def eating_hall(self):
        a, rng, pal = self.a, self.rng, self.pal
        wood = mixer(rng, [(B("spruce_planks"), 4), (B("dark_oak_planks"), 2), (B("stripped_spruce_log", axis="x"), 1)])
        lx1, lz1, lx2, lz2 = 30, 140, 136, 195
        self.carve(lx1, lz1, lx2, lz2, G, G + HT - 1, floor_b=wood)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, G, HT, pal, every=8, win=(), door_every=0, lamp="lantern", band=11)
        self.ceiling_beams(lx1, lz1, lx2, lz2, G + HT - 1, axis="z", every=8)
        # the trough of meat
        meat = mixer(rng, [(B("red_terracotta"), 3), (B("pink_terracotta"), 2), (B("bone_block", axis="x"), 1), (B("brown_mushroom_block", huge_mushroom_bits=14), 1)])
        for lx in range(40, 127):
            for lz in range(164, 173):
                x, z = self.w(lx, lz)
                edge = lx in (40, 126) or lz in (164, 172)
                for y in range(G, G + 6):
                    a.set(x, y, z, B("spruce_log", axis="x") if edge else (meat() if y < G + 4 + (lx * 7 + lz) % 3 else AIR))
        # giant benches you walk under
        for (za, zb) in ((154, 159), (177, 182)):
            for lx in range(42, 125):
                for lz in range(za, zb + 1):
                    x, z = self.w(lx, lz)
                    a.set(x, G + 8, z, B("spruce_planks"))
                    a.set(x, G + 9, z, B("spruce_slab"))
                    if (lx - 42) % 14 < 2 and lz in (za, za + 1, zb - 1, zb):
                        for y in range(G, G + 8):
                            a.set(x, y, z, B("spruce_log", axis="y"))
        # the great hearth in the west wall
        hx, hz = self.w(30, 168)
        for dz in range(-10, 11):
            for y in range(G, G + 20):
                for dx in range(0, 4):
                    inner = abs(dz) < 7 and y < G + 12 and dx < 3
                    a.set(hx + dx, y, hz + dz, AIR if inner else pal.trim if (y - G) in (12, 19) else pal.wall())
            for dx in range(-3, 0):
                if abs(dz) < 7:
                    for y in range(G - 1, G + 12):
                        a.set(hx + dx, y, hz + dz, B("netherrack") if y == G - 1 else AIR)
                    a.set(hx + dx, G, hz + dz, B("fire"))
                    for y in range(G + 12, self.MT):
                        a.set(hx + dx, y, hz + dz, pal.wall())
        for dz in range(-6, 7, 3):
            a.set(hx + 1, G, hz + dz, B("campfire"))
        for lx in range(46, 127, 16):
            x, z = self.w(lx, 168)
            C.chandelier(a, x, G + HT - 2, z, 6, "lantern")
        # door to Logi's pit (entry gate inside it)
        self.carve(137, 164, 141, 172, G, G + 11, floor_b=pal.floor)
        self.add_zone("c3", (self.x0 + 34, G - 2, self.z0 + 142, self.x0 + 134, G + 3, self.z0 + 194), floor_mask=None, n=12)

    # ------------------------------------------------------------ mid-boss 1: Logi's fire pit
    def logi_pit(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 142, 146, 190, 190
        char = mixer(rng, [(B("blackstone"), 3), (B("basalt", pillar_axis="y"), 1), (B("polished_blackstone"), 1)])
        self.carve(lx1, lz1, lx2, lz2, G, G + HT - 1, floor_b=char)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, G, HT, pal, every=6, win=(), door_every=0, lamp="lantern", band=8)
        self.ceiling_beams(lx1, lz1, lx2, lz2, G + HT - 1, axis="x", every=6, beam="basalt")
        cx, cz = self.w(166, 168)
        R = 16

        def floor_fn(x, z, d):
            ang = math.atan2(z - cz, x - cx)
            crack = abs(math.sin(ang * 5 + d * 0.35)) < 0.08 and d > 3
            if d > R - 1.2:
                return B("polished_blackstone_bricks")
            if crack:
                return B("magma")
            if d < 3:
                return B("crying_obsidian") if d < 1.5 else B("polished_blackstone")
            return B("blackstone") if (int(d) + (x + z) % 3) % 4 else B("basalt", pillar_axis="y")
        ex, ez = self.w(141, 168)
        entry = self.doorway(ex, G, ez, 9, 12, "z")
        self.carve(191, 164, 195, 172, G, G + 11, floor_b=pal.floor)
        xx, zz = self.w(191, 168)
        exitg = self.doorway(xx, G, zz, 9, 12, "z")
        self.arena("c3_mid", cx, G, cz, R, "logi", "mid1", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # fire troughs in the four corners, out of the fight
        for (dx, dz) in ((-21, -19), (21, -19), (-21, 19), (21, 19)):
            for ox in range(-2, 3):
                for oz in range(-2, 3):
                    x, z = cx + dx + ox, cz + dz + oz
                    a.set(x, G - 1, z, B("netherrack"))
                    a.set(x, G, z, B("fire") if abs(ox) < 2 and abs(oz) < 2 else B("polished_blackstone_wall"))
        self.allow(140, 144, 198, 192, 60, 100)

    # ------------------------------------------------------------ c4: the racecourse
    def racecourse(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 196, 26, 244, 192
        self.carve(lx1, lz1, lx2, lz2, G, G + HT - 1, floor_b=pal.floor)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, G, HT, pal, every=7, win=(), door_every=0, lamp="lantern", band=11)
        track = mixer(rng, [(B("coarse_dirt"), 4), (B("gravel"), 1), (B("packed_mud"), 1)])
        for lx in range(206, 235):
            for lz in range(lz1, lz2 + 1):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, B("calcite") if (lx - 206) % 7 == 0 else track())
        for lz in (36, 37, 180, 181):
            for lx in range(206, 235):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, B("black_concrete") if (lx + lz) % 2 else B("white_concrete"))
        # colonnades down both sides
        for lz in range(32, 190, 14):
            for lx0 in (200, 238):
                for dx in range(0, 4):
                    for dz in range(0, 4):
                        x, z = self.w(lx0 + dx, lz + dz)
                        for y in range(G, G + HT):
                            cap = y in (G, G + 1, G + HT - 2, G + HT - 1)
                            a.set(x, y, z, pal.accent if cap else B("polished_andesite") if (y - G) % 8 else pal.trim)
                x, z = self.w(lx0 + (4 if lx0 == 200 else -1), lz + 1)
                a.put(x, G + 6, z, B("lantern"))
        # the finish posts and banners
        for lx in (205, 235):
            for lz in (36, 180):
                x, z = self.w(lx, lz)
                for y in range(G, G + 10):
                    a.set(x, y, z, B("spruce_log", axis="y"))
                a.set(x, G + 10, z, B("lantern"))
        for lz in range(40, 180, 20):
            x, z = self.w(221, lz)
            C.chandelier(a, x, G + HT - 2, z, 8, "lantern")
        # door into the banquet hall
        self.carve(191, 46, 195, 54, G, G + 13, floor_b=pal.floor)
        self.add_zone("c4", (self.x0 + 198, G - 2, self.z0 + 28, self.x0 + 242, G + 3, self.z0 + 190), floor_mask=None, n=12)

    # ------------------------------------------------------------ c5: the banquet hall
    def banquet(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 92, 20, 190, 88
        wood = mixer(rng, [(B("spruce_planks"), 4), (B("dark_oak_planks"), 2)])
        self.carve(lx1, lz1, lx2, lz2, G, G + HT - 1, floor_b=wood)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, G, HT, pal, every=8, win=(), door_every=0, lamp="lantern", band=11)
        self.ceiling_beams(lx1, lz1, lx2, lz2, G + HT - 1, axis="z", every=8)
        for lx in range(lx1 + 4, lx2 - 3):
            for lz in range(52, 57):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, B("blue_wool") if lz in (52, 56) else B("light_blue_wool"))
        # two giant tables (walk under them)
        for (za, zb) in ((30, 42), (64, 76)):
            for lx in range(126, 186):
                for lz in range(za, zb + 1):
                    x, z = self.w(lx, lz)
                    a.set(x, G + 15, z, B("dark_oak_planks"))
                    a.set(x, G + 16, z, B("spruce_planks"))
            for lx in (127, 147, 167, 184):
                for lz in (za + 1, zb - 2):
                    for dx in range(2):
                        for dz in range(2):
                            x, z = self.w(lx + dx, lz + dz)
                            for y in range(G, G + 15):
                                a.set(x, y, z, B("dark_oak_log", axis="y"))
        top = G + 17
        # the drinking horn lying on the north table; its tip runs into the wall towards the sea
        mx, mz = 132, 36
        tip = (189, 22)
        L = math.dist((mx, mz), tip)
        for t in range(int(L * 2) + 1):
            u = t / (L * 2)
            px, pz = mx + (tip[0] - mx) * u, mz + (tip[1] - mz) * u
            r = 6.0 * (1 - u) + 1.0
            py = top + r - 0.5 + u * 3
            for dx in range(-8, 9):
                for dy in range(-8, 9):
                    for dz in range(-8, 9):
                        d = math.sqrt(dx * dx + dy * dy + dz * dz)
                        if d > r:
                            continue
                        x, y, z = int(round(self.x0 + px + dx)), int(round(py + dy)), int(round(self.z0 + pz + dz))
                        if d > r - 1.1:
                            band = u < 0.05 or abs(u - 0.4) < 0.02 or abs(u - 0.7) < 0.02
                            a.set(x, y, z, B("gold_block") if band else B("bone_block", axis="x") if (t // 3) % 2 else B("calcite"))
                        elif dy < -r * 0.35:
                            a.set(x, y, z, B("light_blue_stained_glass"))
                        else:
                            a.set(x, y, z, AIR)
        # the grey cat (the world serpent in disguise) sitting at the west end
        cx, cz = self.w(110, 56)
        grey = mixer(rng, [(B("light_gray_concrete"), 4), (B("smooth_stone"), 2), (B("andesite"), 1)])
        for dx in range(-12, 13):
            for dy in range(0, 26):
                for dz in range(-11, 12):
                    body = ((dx + 1) / 9.5) ** 2 + ((dy - 10) / 11.0) ** 2 + (dz / 8.0) ** 2 <= 1
                    haunch = (dx / 11.0) ** 2 + ((dy - 4) / 6.0) ** 2 + (dz / 10.5) ** 2 <= 1
                    if body or haunch:
                        stripe = (dy + abs(dz)) % 6 == 0 and dx < 2
                        a.set(cx + dx, G + dy, cz + dz, B("gray_concrete") if stripe else grey())
        hx, hy = cx + 4, G + 25
        for dx in range(-7, 8):
            for dy in range(-6, 7):
                for dz in range(-7, 8):
                    if (dx / 6.5) ** 2 + (dy / 5.5) ** 2 + (dz / 6.5) ** 2 <= 1:
                        a.set(hx + dx, hy + dy, cz + dz, grey())
        for s_ in (-1, 1):
            for k in range(4):
                for w_ in range(-(3 - k), 4 - k):
                    a.set(hx - 1 + w_ // 2, hy + 5 + k, cz + s_ * 4 + w_ % 2 * s_, B("gray_concrete") if k < 3 else B("pink_concrete"))
            a.set(hx + 6, hy + 1, cz + s_ * 3, B("gold_block"))
            a.set(hx + 7, hy + 1, cz + s_ * 3, B("black_concrete"))
            for k in range(4):
                a.set(hx + 6 + (k > 1), hy - 1 - k // 2, cz + s_ * (2 + k), B("white_concrete"))
        a.set(hx + 7, hy - 1, cz, B("pink_concrete"))
        for s_ in (-1, 1):
            for y in range(G, G + 12):
                for dx in range(0, 3):
                    for dz in range(0, 3):
                        a.set(cx + 8 + dx, y, cz + s_ * 3 + dz - 1, grey())
        for t in range(40):
            ang = t / 40 * 1.6 * math.pi
            x, z = int(round(cx - 2 + math.cos(ang) * 13)), int(round(cz + math.sin(ang) * 12))
            for dy in range(0, 3):
                for dd in range(-1, 2):
                    a.set(x + dd, G + dy, z, B("gray_concrete") if t % 5 == 0 else grey())
        # giant goblets and plates on the tables, candle-lanterns
        for (lx, lz) in ((150, 66), (170, 72), (140, 74), (176, 34)):
            x, z = self.w(lx, lz)
            cyl(a, x, top, z, 3.5, 3.5, 1, B("gold_block"))
            if lz > 50:
                cyl(a, x, top + 1, z, 1, 1, 4, B("gold_block"))
                cyl(a, x, top + 5, z, 2.5, 3.5, 4, B("gold_block"), hollow=True)
        for lx in range(100, 190, 14):
            for lz in (48, 60):
                x, z = self.w(lx, lz)
                C.chandelier(a, x, G + HT - 2, z, 7, "lantern")
        # door into Elli's ring
        self.carve(87, 42, 91, 50, G, G + 11, floor_b=pal.floor)
        self.add_zone("c5", (self.x0 + 124, G - 2, self.z0 + 22, self.x0 + 188, G + 3, self.z0 + 86), floor_mask=None, n=12)

    # ------------------------------------------------------------ mid-boss 2: Elli's wrestling ring
    def elli_ring(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 36, 22, 86, 70
        self.carve(lx1, lz1, lx2, lz2, G, G + 29, floor_b=pal.floor)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, G, 30, pal, every=6, win=(), door_every=0, lamp="lantern", band=10)
        self.ceiling_beams(lx1, lz1, lx2, lz2, G + 29, axis="x", every=6)
        cx, cz = self.w(61, 46)
        R = 16

        def floor_fn(x, z, d):
            if abs(d - R + 0.6) < 0.7 or abs(d - 8) < 0.5:
                return B("deepslate_tiles")
            if d < 2:
                return B("chiseled_stone_bricks")
            return B("polished_andesite") if (int(d) // 2) % 2 else B("smooth_stone")
        ex, ez = self.w(87, 46)
        entry = self.doorway(ex, G, ez, 9, 12, "z")
        self.carve(57, 71, 65, 75, G, G + 11, floor_b=pal.floor)
        xx, zz = self.w(61, 71)
        exitg = self.doorway(xx, G, zz, 9, 12, "x")
        self.arena("c5_mid", cx, G, cz, R, "elli", "mid2", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # the hourglass of age and a spinning wheel in the corners
        hx, hz = self.w(40, 26)
        for dy in range(0, 18):
            r = 1 + abs(dy - 9) * 0.35
            for dx in range(-4, 5):
                for dz in range(-4, 5):
                    d = math.hypot(dx, dz)
                    if d <= r:
                        a.set(hx + dx + 1, G + dy, hz + dz + 1, B("sand") if dy < 6 or (11 <= dy <= 12 and d < r - 1) else B("glass"))
        for dx in range(-4, 6):
            for dz in range(-4, 6):
                for y in (G, G + 18):
                    if abs(dx - 1) <= 4 and abs(dz - 1) <= 4:
                        a.set(hx + dx, y, hz + dz, B("dark_oak_planks"))
        wx, wz = self.w(82, 66)
        self.ring(wx, G + 6, wz, 5, "xy", B("spruce_planks"), spokes=6)
        for y in range(G, G + 6):
            a.set(wx, y, wz + 1, B("spruce_fence"))
        self.allow(34, 20, 92, 76, 60, 100)

    # ------------------------------------------------------------ c6: the hall of illusions
    def illusions(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 30, 76, 86, 134
        H = 24
        self.carve(lx1, lz1, lx2, lz2, G, G + H - 1)
        for lx in range(lx1, lx2 + 1):
            for lz in range(lz1, lz2 + 1):
                x, z = self.w(lx, lz)
                a.set(x, G - 1, z, B("black_concrete") if (lx // 3 + lz // 3) % 2 else B("white_concrete"))
                a.set(x, G + H, z, B("tinted_glass") if (lx + lz) % 9 else B("sea_lantern"))
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, G, H, pal, every=4, win=(), door_every=0, lamp="", band=6)
        # glass partitions on an 8-block grid; every partition has a 3-wide gap somewhere, so every cell connects
        cols = ["white_stained_glass", "light_blue_stained_glass", "purple_stained_glass", "magenta_stained_glass",
                "cyan_stained_glass", "light_gray_stained_glass", "tinted_glass"]
        S = 8
        for gx in range(lx1 + S, lx2 - 2, S):
            for gz0 in range(lz1, lz2 + 1, S):
                gap = rng.randint(1, S - 4)
                col = B(rng.choice(cols))
                for lz in range(gz0, min(gz0 + S, lz2 + 1)):
                    if gap <= lz - gz0 < gap + 3:
                        continue
                    x, z = self.w(gx, lz)
                    for y in range(G, G + 12):
                        a.set(x, y, z, col)
        for gz in range(lz1 + S, lz2 - 2, S):
            for gx0 in range(lx1, lx2 + 1, S):
                gap = rng.randint(1, S - 4)
                col = B(rng.choice(cols))
                for lx in range(gx0, min(gx0 + S, lx2 + 1)):
                    if gap <= lx - gx0 < gap + 3:
                        continue
                    x, z = self.w(lx, gz)
                    if a.get(x, G, z) != AIR:
                        continue
                    for y in range(G, G + 12):
                        a.set(x, y, z, col)
        # glass giants: illusions standing among the panes
        for (lx, lz) in ((46, 92), (70, 118), (42, 124)):
            x, z = self.w(lx, lz)
            ell(a, x, G + 9, z, 2.2, 6, 2.2, B("light_blue_stained_glass"))
            ell(a, x, G + 17, z, 2.0, 2.0, 2.0, B("white_stained_glass"))
            a.set(x, G + 17, z, B("sea_lantern"))
        # door to the throne room (the boss entry gate stands in it)
        self.carve(87, 112, 91, 120, G, G + 11, floor_b=pal.floor)
        self.add_zone("c6", (self.x0 + 32, G - 2, self.z0 + 78, self.x0 + 84, G + 3, self.z0 + 132), floor_mask=None, n=12)

    # ------------------------------------------------------------ the throne room
    def throne_room(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 92, 94, 176, 136
        H = 38
        self.carve(lx1, lz1, lx2, lz2, G, G + H - 1, floor_b=pal.floor)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, G, H, pal, every=10, win=(), door_every=0, lamp="lantern", band=12)
        self.ceiling_beams(lx1, lz1, lx2, lz2, G + H - 1, axis="z", every=10)
        # engaged pillars with gold capitals, blue banners between them
        for lx in range(lx1 + 4, lx2 - 2, 10):
            for (lz, dzs) in ((lz1, 1), (lz2, -1)):
                for k in range(0, 2):
                    for dx in range(0, 3):
                        x, z = self.w(lx + dx, lz + dzs * k)
                        for y in range(G, G + H):
                            a.set(x, y, z, B("gold_block") if y in (G + H - 3, G + H - 2) else B("polished_deepslate"))
                x, z = self.w(lx + 6, lz)
                for y in range(G + 8, G + 26):
                    a.set(x, y, z, B("blue_wool") if y > G + 9 else B("yellow_wool"))
        cx, cz = self.w(128, 115)
        R = 20

        def floor_fn(x, z, d):
            ang = math.atan2(z - cz, x - cx)
            spiral = abs(((ang + d * 0.18) % (math.pi / 2)) - math.pi / 4) < 0.12 and 3 < d < R - 2
            if d > R - 1.2:
                return B("polished_deepslate")
            if spiral:
                return B("purple_glazed_terracotta") if int(d) % 2 else B("purple_concrete")
            if d < 3:
                return B("crying_obsidian") if d < 1.5 else B("gold_block")
            return B("polished_andesite") if int(d) % 4 else B("polished_deepslate")
        ex, ez = self.w(91, 116)
        entry = self.doorway(ex, G, ez, 9, 12, "z")
        ar = self.arena("boss", cx, G, cz, R, "utgardaloki", "final", floor_fn=floor_fn, entry=entry)
        # the throne on its dais
        tx, tz = self.w(166, 115)
        for k, (w, dz) in enumerate(((14, 12), (12, 10), (10, 8))):
            for dx in range(-w // 2, w // 2 + 1):
                for d_z in range(-dz, dz + 1):
                    a.set(tx + dx, G + k, tz + d_z, B("polished_deepslate") if k < 2 else B("blue_wool"))
        for dx in range(-5, 6):
            for d_z in range(-6, 7):
                for y in range(G + 3, G + 13):
                    a.set(tx + 2 + dx // 2, y, tz + d_z, B("polished_deepslate"))
        for d_z in range(-7, 8):
            for y in range(G + 3, G + 34):
                if abs(d_z) <= 7 - max(0, y - (G + 28)):
                    a.set(tx + 6, y, tz + d_z, B("gold_block") if abs(d_z) == 7 - max(0, y - (G + 28)) or y == G + 20 else B("polished_deepslate"))
        for s_ in (-1, 1):
            for y in range(G + 3, G + 17):
                a.set(tx, y, tz + s_ * 7, B("polished_deepslate"))
                a.set(tx + 1, y, tz + s_ * 7, B("polished_deepslate"))
            a.set(tx - 1, G + 17, tz + s_ * 7, B("gold_block"))
        a.set(tx + 6, G + 30, tz, B("sea_lantern"))
        for s_ in (-1, 1):
            P.brazier(a, tx - 8, G, tz + s_ * 10, soul=True, base="polished_blackstone")
        for lx in range(100, 160, 14):
            x, z = self.w(lx, 115)
            C.chandelier(a, x, G + H - 2, z, 10, "lantern")
        # exit: a corridor behind the throne's south side, gated, to the portal room
        self.carve(177, 129, 181, 133, G, G + 5, floor_b=pal.floor)
        self.carve(182, 118, 190, 136, G, G + 11, floor_b=pal.floor)
        xx, zz = self.w(177, 131)
        exitg = self.doorway(xx, G, zz, 5, 6, "z")
        ar["exit"] = [list(p) for p in exitg]
        self.close(exitg)
        px, pz = self.w(186, 127)
        self.exit_portal(px, G, pz)
        self.allow(90, 92, 192, 138, 60, 104)

    # ------------------------------------------------------------ finishing
    def finish(self):
        a = self.a
        self.roofscape(self.pal, 14, 14, 257, 199, T=16, chimney=0.4, snow=True)
        for (lx1, lz1, lx2, lz2) in ((30, 140, 136, 195), (142, 146, 190, 190), (196, 26, 244, 192), (92, 20, 190, 88),
                                     (36, 22, 86, 70), (30, 76, 86, 134), (92, 94, 190, 136), (100, 300, 176, 362)):
            x1, z1 = self.w(lx1, lz1)
            x2, z2 = self.w(lx2, lz2)
            self.light_fill((x1, z1, x2, z2), (G, G + 3), level=8, threshold=5, spacing=7)
        self.ambient = [dict(box=self.zones["c2"]["box"], particle="minecraft:snowflake_particle", rate=3),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:enchanting_table_particle", rate=1),
                        dict(box=self.zones["c3"]["box"], particle="minecraft:campfire_smoke_particle", rate=1)]
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        a.fix_walls()


def build(seed=1):
    d = Utgard("d06", seed)
    d.build()
    return d
