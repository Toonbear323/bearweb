"""Dungeon 7 — 니다벨리르 대장간 성채 (Nidavellir Forge Citadel). Mid tier, 272 x 448, a dwarven fortress inside a mountain.

South -> north and ever deeper: the mountain lake and the gate in the beard of a great carved dwarf face (64); the ore
haulage tunnels (64); the furnace cavern where lava runs under glass floors (56); the workshop and Brokkr's bellows
tower (56, mid-boss 1); the gallery of the gods' treasures (48); the quenching channels and Eitri's forge (40,
mid-boss 2); the chamber of glowing runes (40); and Fafnir's hoard cavern (32).

Local coordinates: x 0..271 (west -> east), z 0..447 (north -> south).
"""
import math

import numpy as np

from mcw import B, AIR, PAL
from gen_common import fbm, stair, slab, standing_sign, line_points, boulder
import nr_parts as P
import nr_castle as C
from nr_dungeon import mixer
from nr_fortress import Fortress
from nr_spawn import cyl, ell, thick_line

SEA = 62
F1, F2, F3, F4, F5 = 64, 56, 48, 40, 32


class Nidavellir(Fortress):
    Y0, SY = 16, 128            # 16..143
    MT = 112

    def build(self):
        rng = self.rng
        self.setup()
        self.post = []                  # stair flights, built after every room is carved so no carve erases them
        self.pal = C.Pal(rng, wall=[("deepslate_bricks", 6), ("cracked_deepslate_bricks", 1), ("deepslate_tiles", 2)], trim="polished_deepslate",
                         floor=[("polished_deepslate", 3), ("deepslate_tiles", 2), ("deepslate_bricks", 1)], roof="deepslate_tile",
                         pillar="chiseled_deepslate", window="orange_stained_glass_pane", light="lantern", accent="gold_block",
                         top="deepslate_brick_wall", plank="spruce_planks")
        self.ores = [B("coal_ore"), B("deepslate_iron_ore"), B("deepslate_gold_ore"), B("deepslate_copper_ore"), B("deepslate_coal_ore")]
        self.terrain()
        self.lake()
        self.dwarf_face()
        self.haulage()
        self.furnace_cavern()
        self.workshop()
        self.bellows_tower()
        self.treasury()
        self.quench()
        self.eitri_forge()
        self.rune_chamber()
        self.hoard()
        for fn in self.post:
            fn()
        self.finish()

    # ------------------------------------------------------------ the mountain and the crater lake
    def terrain(self):
        a, rng = self.a, self.rng
        rock = [B("deepslate"), B("tuff"), B("deepslate"), B("blackstone"), B("deepslate"), B("smooth_basalt")]
        n = fbm(self.sx, self.sz, 14, 4, self.seed + 7)
        for i in range(self.sx):
            for k in range(self.sz):
                col = a.blk[i, :, k]
                top = self.MT + int((n[i, k] - 0.5) * 16)
                for y in range(self.Y0, min(top, self.Y0 + self.SY - 2) + 1):
                    col[y - self.Y0] = rock[(y // 5 + i // 17 + k // 13) % len(rock)]
                if top > 118:
                    col[top - self.Y0] = B("snow")
        self.mtn = n

    def lake(self):
        a, rng = self.a, self.rng
        shore = mixer(rng, [(B("gravel"), 3), (B("stone"), 2), (B("moss_block"), 2), (B("coarse_dirt"), 1)])
        self.water = np.zeros((self.sx, self.sz), bool)
        for i in range(self.sx):
            for k in range(361, self.sz):
                crater = math.hypot((i - 136) / 110.0, (k - 412) / 50.0) < 1 or (56 <= i <= 216 and k <= 384)
                if not crater:
                    continue
                col = a.blk[i, :, k]
                col[F1 - self.Y0:] = AIR
                water = math.hypot((i - 136) / 98.0, (k - 420) / 32.0) < 1
                if water:
                    d = math.hypot((i - 136) / 98.0, (k - 420) / 32.0)
                    depth = int(3 + 10 * (1 - d))
                    for y in range(SEA - depth + 1, SEA + 1):
                        col[y - self.Y0] = B("water")
                    for y in range(SEA + 1, F1):
                        col[y - self.Y0] = AIR
                    col[SEA - depth - self.Y0] = B("gravel")
                    self.water[i, k] = True
                else:
                    col[F1 - 1 - self.Y0] = shore()
        # jetty and return ship
        for lz in range(376, 402):
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
        sx, sz = self.w(142, 412)
        info = P.longship(a, sx, SEA, sz, "north", rng, length=29, beam=8, sail="return")
        self.data["ret"] = dict(deck=list(info["deck"]))
        ax, az = self.w(136, 378)
        self.data["start"] = [ax + 0.5, SEA + 2, az + 0.5, 180]
        self.walk_seeds = [(ax, SEA + 2, az)]
        standing_sign(a, ax + 3, F1, az - 3, 8, "§l§6니다벨리르 대장간 성채\n§r§f신들의 보물을\n§f벼린 난쟁이들의 산\n§7수염 속 대문으로", kind="spruce_standing_sign")
        for _ in range(50):
            lx, lz = rng.randint(30, 242), rng.randint(362, 440)
            x, z = self.w(lx, lz)
            if self.water[lx, lz] or a.get(x, F1, z) != AIR or a.get(x, F1 - 1, z) == AIR or abs(lx - 136) < 5:
                continue
            r = rng.random()
            if r < 0.3:
                boulder(a, x, F1, z, rng, rng.uniform(1.2, 2.6), [B("deepslate"), B("tuff"), B("cobbled_deepslate")])
            elif r < 0.5:
                a.set(x, F1, z, B("lantern") if rng.random() < 0.2 else B("fern"))
            else:
                a.set(x, F1, z, B(rng.choice(["short_grass", "fern", "moss_carpet"])))
        self.allow(0, 356, 271, 447, 40, 72)
        a.bio[:, :] = 188

    # ------------------------------------------------------------ the dwarf face on the mountain
    def dwarf_face(self):
        """A relief carved into the cliff (plane z = 360, protruding south): helmet, brows, glowing eyes, nose,
        a sweeping moustache and a braided beard with the gate opening in it."""
        a, rng = self.a, self.rng
        cx, zf = 136, 360
        face = B("polished_deepslate")
        beard = mixer(rng, [(B("deepslate_tiles"), 3), (B("cobbled_deepslate"), 1)])
        gold = B("gold_block")
        for lx in range(cx - 40, cx + 41):
            for y in range(F1, F1 + 76):
                dx, dy = lx - cx, y - F1
                d, mat = 0, None
                # helmet dome with a gold band and two horns
                if dy >= 50:
                    hr = math.hypot(dx / 30.0, (dy - 50) / 26.0)
                    if hr <= 1:
                        d = int(3 + 4 * (1 - hr))
                        mat = gold if 50 <= dy <= 52 else B("deepslate_tiles") if (dx + dy) % 7 else B("chiseled_deepslate")
                # forehead and brows
                if 38 <= dy < 50 and abs(dx) <= 28:
                    d, mat = 3, face
                    if 40 <= dy <= 43 and 4 <= abs(dx) <= 20:
                        d = 6
                # eyes
                if 32 <= dy < 38 and abs(dx) <= 26:
                    d, mat = 3, face
                    if 6 <= abs(dx) <= 16:
                        d, mat = 1, B("ochre_froglight") if 33 <= dy <= 36 and 9 <= abs(dx) <= 13 else B("blackstone")
                # nose
                if 20 <= dy < 40 and abs(dx) <= 5 - (40 - dy) // 8:
                    d = max(d, 4 + (40 - dy) // 4)
                    mat = face
                # cheeks
                if 20 <= dy < 32 and 6 <= abs(dx) <= 26:
                    d, mat = 3, face
                # moustache sweeping out and down
                if 14 <= dy < 22 and abs(dx) <= 30:
                    t = abs(dx) / 30.0
                    if dy >= 16 + int(5 * t * t) - 2 and dy <= 21 - int(4 * t):
                        d, mat = 6 - int(2 * t), beard()
                # beard: wide at the top, narrowing in braids to the ground
                if dy < 16:
                    wdt = 26 - (16 - dy) * 0.4
                    if abs(dx) <= wdt:
                        d = 5 + int(3 * (1 - abs(dx) / max(wdt, 1)))
                        mat = beard()
                        if abs(dx) % 9 in (0, 1):
                            mat = B("polished_deepslate")
                        if abs(dx) % 9 in (0, 1) and dy % 5 == 0:
                            mat = gold
                if mat is None or d <= 0:
                    continue
                for t in range(1, d + 1):
                    x, z = self.w(lx, zf + t)
                    a.set(x, y, z, mat)
        # horns on the helmet
        for s in (-1, 1):
            thick_line(a, (self.x0 + cx + s * 26, F1 + 62, self.z0 + zf + 4), (self.x0 + cx + s * 40, F1 + 78, self.z0 + zf + 6), 1.6, B("bone_block", axis="y"))
            thick_line(a, (self.x0 + cx + s * 40, F1 + 78, self.z0 + zf + 6), (self.x0 + cx + s * 42, F1 + 88, self.z0 + zf + 4), 0.9, B("bone_block", axis="y"))
        # the gate in the beard: 15 wide, 20 high, gold framed
        self.carve(129, 300, 143, 370, F1, F1 + 19, floor_b=self.pal.floor)
        for lz in range(361, 371):
            for lx in (128, 144):
                x, z = self.w(lx, lz)
                for y in range(F1, F1 + 21):
                    a.set(x, y, z, B("gold_block") if lz == 368 else B("polished_deepslate"))
            for lx in range(128, 145):
                x, z = self.w(lx, lz)
                a.set(x, F1 + 20, z, B("gold_block") if lz == 368 else B("polished_deepslate"))
        for k in range(1, 5):
            for lz in range(300, 371):
                for lx in (128 + k, 144 - k):
                    x, z = self.w(lx, lz)
                    a.set(x, F1 + 20 - k, z, self.pal.wall())
        for lx in (124, 148):
            x, z = self.w(lx, 372)
            P.brazier(a, x, F1, z, soul=False, base="polished_blackstone")

    # ------------------------------------------------------------ dressing helpers
    def ore_speckle(self, lx1, lz1, lx2, lz2, y1, y2, chance=0.04):
        """Scatter ore blocks on the exposed rock faces around a carved room."""
        a, rng = self.a, self.rng
        for lx in range(lx1 - 1, lx2 + 2):
            for lz in range(lz1 - 1, lz2 + 2):
                for y in range(y1, y2 + 1):
                    x, z = self.w(lx, lz)
                    b = a.get(x, y, z)
                    if b == AIR or rng.random() > chance:
                        continue
                    if any(a.get(x + dx, y, z + dz) == AIR for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        if PAL.names[b] in ("deepslate", "tuff", "blackstone", "smooth_basalt", "stone"):
                            a.set(x, y, z, rng.choice(self.ores))

    def arch_ribs(self, lx1, lz1, lx2, lz2, y0, h, axis, every=8):
        """Stone arch ribs across a tunnel every few blocks (dwarven masonry against the raw rock)."""
        a, pal = self.a, self.pal
        if axis == "z":
            for lz in range(lz1 + 2, lz2, every):
                for lx in range(lx1, lx2 + 1):
                    x, z = self.w(lx, lz)
                    edge = lx in (lx1, lx2)
                    a.set(x, y0 + h - 1, z, pal.trim)
                    if edge:
                        for y in range(y0, y0 + h):
                            a.set(x, y, z, pal.pillar if y in (y0, y0 + h - 2) else pal.wall())
                x, z = self.w((lx1 + lx2) // 2, lz)
                a.set(x, y0 + h - 2, z, B("lantern", hanging=1))
        else:
            for lx in range(lx1 + 2, lx2, every):
                for lz in range(lz1, lz2 + 1):
                    x, z = self.w(lx, lz)
                    edge = lz in (lz1, lz2)
                    a.set(x, y0 + h - 1, z, pal.trim)
                    if edge:
                        for y in range(y0, y0 + h):
                            a.set(x, y, z, pal.pillar if y in (y0, y0 + h - 2) else pal.wall())
                x, z = self.w(lx, (lz1 + lz2) // 2)
                a.set(x, y0 + h - 2, z, B("lantern", hanging=1))

    def gear(self, x, y, z, r, plane, mat=None):
        """A big cog on a wall: ring with teeth and spokes. plane 'xy' (wall facing z) or 'zy' (wall facing x)."""
        a = self.a
        mat = mat or B("waxed_cut_copper")
        for dy in range(-r - 2, r + 3):
            for du in range(-r - 2, r + 3):
                d = math.hypot(du, dy)
                ang = math.atan2(dy, du)
                tooth = d <= r + 1.5 and d > r - 0.5 and (int(ang / (2 * math.pi) * 16 + 16) % 2 == 0)
                ringc = r - 1.5 < d <= r + 0.5
                spoke = d < r - 1 and (abs(du) < 0.6 or abs(dy) < 0.6 or abs(abs(du) - abs(dy)) < 0.6)
                hub = d < 1.6
                if tooth or ringc or spoke or hub:
                    b = B("polished_blackstone") if hub else mat
                    if plane == "xy":
                        a.set(x + du, y + dy, z, b)
                    else:
                        a.set(x, y + dy, z + du, b)

    def rails(self, cells, y):
        a = self.a
        for (lx, lz, d) in cells:
            x, z = self.w(lx, lz)
            if a.get(x, y, z) == AIR:
                a.set(x, y, z, B("rail", rail_direction=d))

    # ------------------------------------------------------------ c1: ore haulage tunnels
    def haulage(self):
        a, rng, pal = self.a, self.rng, self.pal
        H = 11
        tunnels = [(129, 300, 143, 360, "z"), (74, 300, 86, 350, "z"), (186, 300, 198, 350, "z"),
                   (74, 344, 198, 350, "x"), (74, 320, 198, 326, "x"), (74, 300, 198, 306, "x")]
        for (x1, z1, x2, z2, axis) in tunnels:
            self.carve(x1, z1, x2, z2, F1, F1 + H - 1, floor_b=pal.floor)
        for (x1, z1, x2, z2, axis) in tunnels:
            self.arch_ribs(x1, z1, x2, z2, F1, H, axis, every=8)
            self.ore_speckle(x1, z1, x2, z2, F1, F1 + H, chance=0.05)
        # rails down the middle of each tunnel
        cells = [(136, lz, 0) for lz in range(300, 368)] + [(80, lz, 0) for lz in range(300, 351)] + [(192, lz, 0) for lz in range(300, 351)]
        cells += [(lx, lz, 1) for lz in (323, 347) for lx in range(74, 199)]
        self.rails(cells, F1)
        # ore heaps, mine carts (chests on rails), cogs on the walls
        heap_mix = mixer(rng, [(B("raw_iron_block"), 2), (B("raw_copper_block"), 2), (B("raw_gold_block"), 1), (B("cobbled_deepslate"), 3), (B("coal_block"), 1)])
        for (lx, lz) in ((77, 312), (195, 314), (140, 336), (90, 302), (182, 348), (130, 310), (76, 338)):
            x, z = self.w(lx, lz)
            self.heap(x, F1, z, rng.uniform(1.6, 2.6), heap_mix)
        for (lx, lz) in ((136, 330), (80, 316), (192, 334), (110, 323), (160, 347)):
            x, z = self.w(lx, lz)
            if a.get(x, F1, z) == B("rail", rail_direction=0) or a.get(x, F1, z) == B("rail", rail_direction=1):
                a.set(x, F1, z, B("chest", cardinal="south"))
        for (lx, lz, plane) in ((128, 340, "zy"), (144, 316, "zy"), (100, 319, "xy"), (170, 327, "xy"), (73, 330, "zy"), (199, 320, "zy")):
            x, z = self.w(lx, lz)
            self.gear(x, F1 + 5, z, 4, plane)
        self.allow(70, 288, 202, 372, F2 - 2, F1 + 8)
        self.add_zone("c1", (self.x0 + 72, F1 - 2, self.z0 + 300, self.x0 + 200, F1 + 3, self.z0 + 360), floor_mask=None, n=12)

    # ------------------------------------------------------------ c2: the furnace cavern
    def furnace_cavern(self):
        a, rng, pal = self.a, self.rng, self.pal
        cx, cz, rx, rz = 136, 250, 112, 45
        n = fbm(self.sx, self.sz, 9, 3, self.seed + 21)
        floor_mix = mixer(rng, [(B("polished_deepslate"), 3), (B("deepslate_tiles"), 2), (B("cobbled_deepslate"), 1)])
        self.cav2 = {}
        for lx in range(cx - rx, cx + rx + 1):
            for lz in range(cz - rz, cz + rz + 1):
                d = math.hypot((lx - cx) / rx, (lz - cz) / rz)
                if d > 1 - (n[lx, lz] - 0.5) * 0.12:
                    continue
                top = F2 + int(16 + 24 * math.sqrt(max(0.0, 1 - d * d)) + (n[lx, lz] - 0.5) * 6)
                x, z = self.w(lx, lz)
                col = a.blk[lx, :, lz]
                col[F2 - self.Y0:top - self.Y0 + 1] = AIR
                a.set(x, F2 - 1, z, floor_mix())
                self.carved[lx, lz] = True
                self.cav2[(lx, lz)] = top
        self.ore_speckle(cx - rx, cz - rz, cx + rx, cz + rz, F2, F2 + 44, chance=0.03)
        # stalactites and hanging lanterns from the cavern roof
        for (lx, lz), top in self.cav2.items():
            x, z = self.w(lx, lz)
            r = rng.random()
            if r < 0.02:
                for t in range(rng.randint(1, 4)):
                    a.set(x, top - t, z, B("pointed_dripstone", dripstone_thickness="tip" if t == 0 else "middle", hanging=1))
            elif r < 0.024 and top - F2 > 20:
                for t in range(rng.randint(4, 12)):
                    a.set(x, top - t, z, B("chain"))
                a.set(x, top - 12, z, B("lantern", hanging=1))
        # the great blast furnace in the middle, a lava band behind bars, chimney up to the roof
        fx, fz = self.w(cx, 244)
        R = 12
        for dx in range(-R - 1, R + 2):
            for dz in range(-R - 1, R + 2):
                d = math.hypot(dx, dz)
                if d > R + 0.4:
                    continue
                for y in range(F2, F2 + 36):
                    shell = d > R - 2
                    band = (y - F2) % 9 == 8
                    if shell:
                        a.set(fx + dx, y, fz + dz, B("gold_block") if band and (dx + dz) % 3 == 0 else pal.trim if band else B("polished_blackstone_bricks"))
                    else:
                        a.set(fx + dx, y, fz + dz, B("lava") if y < F2 + 6 else AIR)
                if R - 2 < d <= R + 0.4:
                    for y in range(F2 + 10, F2 + 14):
                        a.set(fx + dx, y, fz + dz, B("iron_bars") if (dx + dz) % 2 else B("orange_stained_glass"))
        top = self.cav2.get((cx, 244), F2 + 44)
        for y in range(F2 + 36, top + 1):
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    if math.hypot(dx, dz) <= 3.4:
                        a.set(fx + dx, y, fz + dz, B("polished_blackstone_bricks") if math.hypot(dx, dz) > 2 else AIR)
        # lava channels under glass running east and west from the furnace
        for lz in range(242, 247):
            for lx in list(range(cx - 100, cx - R - 1)) + list(range(cx + R + 2, cx + 101)):
                if (lx, lz) not in self.cav2:
                    continue
                x, z = self.w(lx, lz)
                a.set(x, F2 - 3, z, B("magma"))
                a.set(x, F2 - 2, z, B("lava"))
                a.set(x, F2 - 1, z, B("orange_stained_glass") if lz in (243, 244, 245) else B("gold_block"))
        # dwarf houses around the cavern: small stone halls with lit windows, forges outside
        houses = [(44, 222, 68, 238, "south"), (44, 258, 68, 274, "north"), (204, 222, 228, 238, "south"), (204, 258, 228, 274, "north"),
                  (92, 270, 112, 284, "north"), (160, 270, 180, 284, "north")]
        for (x1, z1, x2, z2, door) in houses:
            if not all((lx, lz) in self.cav2 for lx in (x1, x2) for lz in (z1, z2)):
                continue
            wx1, wz1 = self.w(x1, z1)
            wx2, wz2 = self.w(x2, z2)
            C.hall(a, wx1, wz1, wx2, wz2, F2, 7, pal, roof="gable", axis="x", doors=[(door, 0, 3, 4)], lights=True)
            ox, oz = (wx1 + wx2) // 2, (wz2 + 3) if door == "south" else (wz1 - 3)
            a.set(ox - 3, F2, oz, B("anvil"))
            a.set(ox + 3, F2, oz, B("blast_furnace", cardinal=door))
            a.set(ox + 4, F2, oz, B("smithing_table"))
            a.set(ox - 4, F2, oz, B("grindstone"))
            ch_x = wx1 + 2
            ch_z = (wz1 + wz2) // 2
            for y in range(F2 + 8, self.cav2.get((x1 + 2, (z1 + z2) // 2), F2 + 30)):
                a.set(ch_x, y, ch_z, B("polished_blackstone_bricks"))
        self.rails([(136, lz, 0) for lz in range(252, 292)] + [(lx, 250, 1) for lx in range(40, 232) if abs(lx - 136) > 14], F2)
        self.allow(20, 200, 252, 298, F2 - 2, F2 + 14)
        self.add_zone("c2", (self.x0 + 34, F2 - 2, self.z0 + 210, self.x0 + 238, F2 + 3, self.z0 + 290), floor_mask=None, n=12)
        # passage to the workshop; grand stairs up to the haulage tunnels (built after the cavern so it stays)
        self.carve(60, 196, 70, 212, F2, F2 + 11, floor_b=pal.floor)
        sx, sz = self.w(136, 291)
        C.flight(a, sx, F2, sz, "south", F1 - F2, 9, "deepslate_brick_stairs", support=pal.wall)
        for lz in range(291, 300):
            for lx in (131, 141):
                x, z = self.w(lx, lz)
                for y in range(F2, F2 + (lz - 291) + 2):
                    if a.get(x, y, z) == AIR:
                        a.set(x, y, z, pal.wall())
                a.set(x, F2 + (lz - 291) + 2, z, B("deepslate_brick_wall"))

    # ------------------------------------------------------------ c3: the workshop
    def workshop(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 24, 140, 130, 198
        H = 24
        self.carve(lx1, lz1, lx2, lz2, F2, F2 + H - 1, floor_b=pal.floor)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, F2, H, pal, every=12, win=(), door_every=0, lamp="lantern", band=8)
        self.ceiling_beams(lx1, lz1, lx2, lz2, F2 + H - 1, axis="z", every=12, beam="polished_basalt")
        # pillar rows with gold capitals
        for lx in range(36, 126, 12):
            for lz in (156, 182):
                for dx in range(2):
                    for dz in range(2):
                        x, z = self.w(lx + dx, lz + dz)
                        for y in range(F2, F2 + H):
                            a.set(x, y, z, B("gold_block") if y in (F2 + H - 3, F2 + 1) else pal.pillar)
        # workbenches: anvils, smithing tables, grindstones, forges with lava behind bars
        stations = ["anvil", "smithing_table", "grindstone", "crafting_table", "blast_furnace", "barrel", "cauldron", "fletching_table"]
        for lx in range(34, 124, 6):
            for lz in (146, 192):
                x, z = self.w(lx, lz)
                st = rng.choice(stations)
                if st == "blast_furnace":
                    a.set(x, F2, z, B("blast_furnace", cardinal="south" if lz == 146 else "north"))
                elif st == "cauldron":
                    a.set(x, F2, z, B("cauldron", cauldron_liquid="lava", fill_level=6))
                else:
                    a.set(x, F2, z, B(st))
        for (lx, lz) in ((50, 168), (80, 170), (110, 168)):
            x, z = self.w(lx, lz)
            for dx in range(-2, 3):
                for dz in range(-1, 2):
                    a.set(x + dx, F2, z + dz, B("polished_blackstone_bricks"))
            a.set(x, F2 + 1, z, B("anvil"))
            a.set(x - 2, F2 + 1, z, B("iron_block"))
            a.set(x + 2, F2 + 1, z, B("gold_block"))
        hx, hz = self.w(24, 169)
        for dz in range(-6, 7):
            for y in range(F2, F2 + 10):
                inner = abs(dz) < 4 and y < F2 + 6
                a.set(hx, y, hz + dz, B("iron_bars") if inner and y > F2 else pal.trim if y == F2 + 6 else pal.wall())
                if inner:
                    a.set(hx - 1, y, hz + dz, B("lava") if y < F2 + 3 else AIR)
                    a.set(hx - 2, y, hz + dz, pal.wall())
        for (lx, lz) in ((60, 140), (100, 140), (44, 198), (116, 198)):
            x, z = self.w(lx, lz - 1 if lz == 140 else lz + 1)
            self.gear(x, F2 + 12, z, 5, "xy")
        for lx in range(40, 126, 16):
            x, z = self.w(lx, 169)
            C.chandelier(a, x, F2 + H - 2, z, 5, "lantern")
        self.carve(131, 166, 141, 174, F2, F2 + 11, floor_b=pal.floor)
        self.allow(20, 136, 206, 214, F2 - 2, F2 + 16)
        self.add_zone("c3", (self.x0 + 26, F2 - 2, self.z0 + 142, self.x0 + 128, F2 + 3, self.z0 + 196), floor_mask=None, n=12)

    # ------------------------------------------------------------ mid-boss 1: Brokkr's bellows tower
    def bellows_tower(self):
        a, rng, pal = self.a, self.rng, self.pal
        cx_l, cz_l, RR, H = 168, 170, 26, 42
        for lx in range(cx_l - RR, cx_l + RR + 1):
            for lz in range(cz_l - RR, cz_l + RR + 1):
                if math.hypot(lx - cx_l, lz - cz_l) <= RR:
                    self.carve(lx, lz, lx, lz, F2, F2 + H - 1, floor_b=pal.floor)
        cx, cz = self.w(cx_l, cz_l)
        # wall shell: bands, copper pipes, balconies (decoration, out of reach)
        for t in range(int(2 * math.pi * (RR + 1) * 2)):
            ang = t / ((RR + 1) * 2.0)
            x, z = int(round(cx + math.cos(ang) * (RR + 1))), int(round(cz + math.sin(ang) * (RR + 1)))
            for y in range(F2, F2 + H):
                if (y - F2) % 10 == 9:
                    a.set(x, y, z, B("gold_block") if t % 3 == 0 else pal.trim)
                elif t % 14 == 0:
                    a.set(x, y, z, B("waxed_cut_copper"))
        for (by, w) in ((F2 + 16, 2), (F2 + 30, 2)):
            for lx in range(cx_l - RR, cx_l + RR + 1):
                for lz in range(cz_l - RR, cz_l + RR + 1):
                    d = math.hypot(lx - cx_l, lz - cz_l)
                    if RR - w < d <= RR:
                        x, z = self.w(lx, lz)
                        a.set(x, by, z, B("spruce_planks"))
                    elif RR - w - 1 < d <= RR - w:
                        x, z = self.w(lx, lz)
                        a.set(x, by + 1, z, B("spruce_fence"))
        R = 16

        def floor_fn(x, z, d):
            if abs(d - R + 0.6) < 0.7:
                return B("waxed_cut_copper")
            if abs(d - 10) < 0.5 or abs(d - 5) < 0.5:
                return B("gold_block") if int(math.degrees(math.atan2(z - cz, x - cx))) % 20 < 10 else B("polished_deepslate")
            return B("polished_deepslate") if (int(d) + (x + z) % 2) % 3 else B("deepslate_tiles")
        ex, ez = self.w(141, 170)
        entry = self.doorway(ex, F2, ez, 9, 12, "z")
        self.carve(195, 167, 205, 173, F3, F2 + 11)
        xx, zz = self.w(195, 170)
        exitg = self.doorway(xx, F2, zz, 7, 12, "z")
        for lx in range(195, 198):
            for lz in range(167, 174):
                x, z = self.w(lx, lz)
                for y in range(F3 - 1, F2 - 1):
                    a.set(x, y, z, pal.wall())
                a.set(x, F2 - 1, z, pal.floor())
        sx, sz = self.w(205, 170)
        self.post.append(lambda: C.flight(a, sx, F3, sz, "west", F2 - F3, 7, "deepslate_brick_stairs", support=pal.wall))
        self.arena("c3_mid", cx, F2, cz, R, "brokkr", "mid1", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # the great hearth on the north wall, bellows on both sides pointing at it
        hx, hz = cx, cz - RR + 1
        for dx in range(-6, 7):
            for y in range(F2, F2 + 12):
                inner = abs(dx) < 4 and y < F2 + 7
                a.set(hx + dx, y, hz, (B("lava") if y < F2 + 2 else AIR) if inner else pal.trim if y == F2 + 7 else B("polished_blackstone_bricks"))
                if inner:
                    a.set(hx + dx, y, hz - 1, B("polished_blackstone_bricks"))
            a.set(hx + dx, F2 - 1, hz + 1, B("magma"))
        for s in (-1, 1):
            bx = hx + s * 12
            for k in range(9):
                spread = int(k * 0.5)
                for dz in range(0, 9):
                    for y in (F2 + 2 + 4 - spread, F2 + 2 + 4 + spread):
                        a.set(bx - s * k, y, hz + 2 + dz, B("spruce_planks"))
                    for y in range(F2 + 6 - spread + 1, F2 + 6 + spread):
                        if dz in (0, 8):
                            a.set(bx - s * k, y, hz + 2 + dz, B("brown_terracotta"))
            thick_line(a, (bx - s * 9, F2 + 6, hz + 6), (hx + s * 4, F2 + 4, hz + 2), 0.8, B("waxed_cut_copper"))
        for (dx, dz) in ((-12, 8), (12, 8), (-16, -6), (16, -6)):
            for y in range(F2 + 8, F2 + H):
                a.set(cx + dx, y, cz + dz + RR // 2, B("chain"))
        self.allow(138, 142, 210, 198, F3 - 2, F2 + 14)

    # ------------------------------------------------------------ c4: the gallery of the gods' treasures
    def treasury(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 206, 60, 246, 196
        H = 20
        self.carve(lx1, lz1, lx2, lz2, F3, F3 + H - 1, floor_b=pal.floor)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, F3, H, pal, every=10, win=(), door_every=0, lamp="lantern", band=7)
        self.arch_ribs(lx1, lz1, lx2, lz2, F3, H, "z", every=10)
        for lz in range(lz1, lz2 + 1):
            for lx in range(223, 230):
                x, z = self.w(lx, lz)
                a.set(x, F3 - 1, z, B("gold_block") if lx in (223, 229) else B("red_wool"))
        # pedestals with glass cases along both sides
        slots = [(212, lz) for lz in range(76, 196, 20)] + [(240, lz) for lz in range(76, 196, 20)]
        builders = [self.mjolnir, self.gungnir, self.draupnir, self.gullinbursti, self.skidbladnir, self.sif_hair,
                    self.helm, self.mjolnir_small, self.shield, self.sword, self.cup, self.anvil_gold]
        for (lx, lz), fn in zip(slots, builders):
            x, z = self.w(lx, lz)
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    edge = abs(dx) == 3 or abs(dz) == 3
                    a.set(x + dx, F3, z + dz, B("chiseled_deepslate") if edge else B("polished_deepslate"))
                    a.set(x + dx, F3 + 1, z + dz, B("gold_block") if edge and (dx + dz) % 2 == 0 else B("polished_deepslate") if edge else AIR)
            fn(x, F3 + 1, z)
            for (dx, dz) in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
                a.set(x + dx, F3 + 2, z + dz, B("lantern"))
        for lz in range(70, 196, 16):
            x, z = self.w(226, lz)
            C.chandelier(a, x, F3 + H - 2, z, 4, "lantern")
        # stairs down to the quenching channels at the north end
        qx, qz = self.w(226, 52)
        self.post.append(lambda: C.flight(a, qx, F4, qz, "south", F3 - F4, 7, "deepslate_brick_stairs", support=pal.wall))
        self.allow(190, 46, 250, 200, F4 - 2, F2 + 14)
        self.add_zone("c4", (self.x0 + 208, F3 - 2, self.z0 + 62, self.x0 + 244, F3 + 3, self.z0 + 194), floor_mask=None, n=12)

    # the treasures (each stands on a pedestal; y = first block above the pedestal top)
    def mjolnir(self, x, y, z):
        a = self.a
        for dx in range(-2, 3):
            for dz in range(-1, 2):
                for dy in range(4, 7):
                    a.set(x + dx, y + dy, z + dz, B("iron_block") if abs(dx) < 2 else B("polished_deepslate"))
        for dy in range(0, 4):
            a.set(x, y + dy, z, B("stripped_dark_oak_log", axis="y"))
        a.set(x, y + 5, z + 2, B("chiseled_deepslate"))
        a.set(x, y + 5, z - 2, B("chiseled_deepslate"))

    def mjolnir_small(self, x, y, z):
        a = self.a
        for dx in (-1, 0, 1):
            a.set(x + dx, y + 2, z, B("iron_block"))
        a.set(x, y + 1, z, B("dark_oak_fence"))
        a.set(x, y, z, B("dark_oak_fence"))

    def gungnir(self, x, y, z):
        a = self.a
        for dy in range(0, 13):
            a.set(x, y + dy, z, B("stripped_birch_log", axis="y") if dy % 4 else B("gold_block"))
        for dy, w in ((13, 1), (14, 1), (15, 0)):
            for dx in range(-w, w + 1):
                a.set(x + dx, y + dy, z, B("gold_block"))
        a.set(x, y + 16, z, B("end_rod"))

    def draupnir(self, x, y, z):
        a = self.a
        for t in range(24):
            ang = t / 24 * 2 * math.pi
            a.set(x + int(round(math.cos(ang) * 2.6)), y + 3 + int(round(math.sin(ang) * 2.6)), z, B("gold_block"))
        a.set(x, y, z, B("gold_block"))
        for dx in (-2, -1, 1, 2):
            a.set(x + dx, y, z + 1, B("gold_block"))

    def gullinbursti(self, x, y, z):
        a = self.a
        ell(a, x, y + 2, z, 2.6, 1.6, 1.6, B("gold_block"))
        ell(a, x + 3, y + 2, z, 1.2, 1.1, 1.1, B("gold_block"))
        a.set(x + 4, y + 2, z, B("raw_gold_block"))
        for (dx, dz) in ((-2, -1), (-2, 1), (2, -1), (2, 1)):
            a.set(x + dx, y, z + dz, B("gold_block"))
        for dx in range(-2, 3):
            a.set(x + dx, y + 4, z, B("yellow_stained_glass_pane"))

    def skidbladnir(self, x, y, z):
        a = self.a
        for dx in range(-3, 4):
            w = 1 if abs(dx) < 3 else 0
            for dz in range(-w, w + 1):
                a.set(x + dx, y, z + dz, B("spruce_planks"))
            a.set(x + dx, y + 1, z - w, B("spruce_slab"))
        for dy in range(1, 5):
            a.set(x, y + dy, z, B("spruce_fence"))
        for dz in (-1, 0, 1):
            for dy in (2, 3, 4):
                a.set(x + 1, y + dy, z + dz, B("white_wool"))

    def sif_hair(self, x, y, z):
        a = self.a
        for dz in range(-2, 3):
            for dy in range(0, 6):
                a.set(x, y + dy, z + dz, B("chain") if (dz + dy) % 2 else B("gold_block") if dy == 5 else B("yellow_stained_glass_pane"))

    def helm(self, x, y, z):
        a = self.a
        ell(a, x, y + 1, z, 1.6, 1.6, 1.6, B("gold_block"))
        a.set(x, y, z, AIR)
        for s in (-1, 1):
            a.set(x + s * 2, y + 2, z, B("bone_block", axis="x"))
            a.set(x + s * 3, y + 3, z, B("bone_block", axis="y"))

    def shield(self, x, y, z):
        a = self.a
        for dz in range(-2, 3):
            for dy in range(0, 5):
                if math.hypot(dz, dy - 2) <= 2.4:
                    a.set(x, y + dy, z + dz, B("gold_block") if math.hypot(dz, dy - 2) < 0.8 else B("red_wool") if (dz + dy) % 2 else B("spruce_planks"))

    def sword(self, x, y, z):
        a = self.a
        for dy in range(0, 3):
            a.set(x, y + dy, z, B("stripped_dark_oak_log", axis="y"))
        for dz in (-1, 0, 1):
            a.set(x, y + 3, z + dz, B("gold_block"))
        for dy in range(4, 10):
            a.set(x, y + dy, z, B("iron_block"))

    def cup(self, x, y, z):
        cyl(self.a, x, y, z, 1.5, 1.5, 1, B("gold_block"))
        cyl(self.a, x, y + 1, z, 0.6, 0.6, 2, B("gold_block"))
        cyl(self.a, x, y + 3, z, 1.6, 2.2, 3, B("gold_block"), hollow=True)

    def anvil_gold(self, x, y, z):
        a = self.a
        a.set(x, y, z, B("anvil"))
        a.set(x - 1, y, z, B("gold_block"))
        a.set(x + 1, y, z, B("raw_gold_block"))

    # ------------------------------------------------------------ c5: quenching channels
    def quench(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 120, 16, 248, 56
        H = 20
        self.carve(lx1, lz1, lx2, lz2, F4, F4 + H - 1, floor_b=pal.floor)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, F4, H, pal, every=8, win=(), door_every=0, lamp="lantern", band=7)
        self.arch_ribs(lx1, lz1, lx2, lz2, F4, H, "x", every=12)
        for lx in range(lx1, lx2 + 1):
            for lz in range(lz1, lz2 + 1):
                x, z = self.w(lx, lz)
                if lz in (24, 25, 26, 46, 47, 48):
                    a.set(x, F4 - 1, z, B("water"))
                    a.set(x, F4 - 2, z, B("magma") if lx % 13 == 0 else B("polished_blackstone"))
                elif lz in (35, 36, 37):
                    a.set(x, F4 - 3, z, B("magma"))
                    a.set(x, F4 - 2, z, B("lava"))
                    a.set(x, F4 - 1, z, B("orange_stained_glass") if lz == 36 else B("gold_block"))
        # where water meets lava: obsidian and basalt crusts
        for lx in range(126, 246, 14):
            for lz in (30, 42):
                x, z = self.w(lx, lz)
                self.heap(x, F4, z, rng.uniform(1.2, 2.0), mixer(rng, [(B("obsidian"), 2), (B("basalt", pillar_axis="y"), 2), (B("crying_obsidian"), 1)]))
        # quench tanks and anvils
        for lx in range(132, 244, 24):
            for lz in (19, 53):
                x, z = self.w(lx, lz)
                for dx in range(-2, 3):
                    for dz in range(-1, 2):
                        edge = abs(dx) == 2 or abs(dz) == 1
                        a.set(x + dx, F4, z + dz, B("polished_blackstone_bricks") if edge else B("water"))
                a.set(x + 4, F4, z, B("anvil"))
        self.carve(114, 33, 119, 41, F4, F4 + 11, floor_b=pal.floor)
        self.allow(110, 12, 250, 62, F4 - 2, F4 + 14)
        self.add_zone("c5", (self.x0 + 122, F4 - 2, self.z0 + 18, self.x0 + 246, F4 + 3, self.z0 + 54), floor_mask=None, n=12)

    # ------------------------------------------------------------ mid-boss 2: Eitri's forge
    def eitri_forge(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 60, 14, 113, 58
        H = 30
        self.carve(lx1, lz1, lx2, lz2, F4, F4 + H - 1, floor_b=pal.floor)
        for side in ("north", "south", "east", "west"):
            self.facade(lx1, lz1, lx2, lz2, side, F4, H, pal, every=6, win=(), door_every=0, lamp="lantern", band=9)
        self.ceiling_beams(lx1, lz1, lx2, lz2, F4 + H - 1, axis="x", every=6, beam="polished_basalt")
        cx, cz = self.w(86, 36)
        R = 16

        def floor_fn(x, z, d):
            if abs(d - R + 0.6) < 0.7:
                return B("gold_block")
            if abs(d - 7) < 0.6:
                return B("iron_block")
            if d < 2.5:
                return B("chiseled_deepslate")
            ang = math.degrees(math.atan2(z - cz, x - cx)) % 45
            return B("polished_deepslate") if ang < 22.5 else B("deepslate_tiles")
        ex, ez = self.w(114, 37)
        entry = self.doorway(ex, F4, ez, 9, 12, "z")
        self.carve(82, 59, 90, 65, F4, F4 + 11, floor_b=pal.floor)
        xx, zz = self.w(86, 59)
        exitg = self.doorway(xx, F4, zz, 9, 12, "x")
        self.arena("c5_mid", cx, F4, cz, R, "eitri", "mid2", floor_fn=floor_fn, entry=entry, exit=exitg)
        self.close(exitg)
        # the great anvil and forge on the west wall
        ax_, az_ = self.w(64, 36)
        for dz in range(-5, 6):
            for dy in range(0, 6):
                w = 1 if dy < 2 else 2 if dy < 4 else 3
                for dx in range(-w + 1, w + 1):
                    a.set(ax_ + dx, F4 + dy, az_ + dz, B("polished_blackstone") if dy < 4 else B("iron_block"))
        for dz in range(-3, 4):
            for y in range(F4, F4 + 8):
                a.set(ax_ - 3, y, az_ + dz, B("lava") if abs(dz) < 2 and y < F4 + 3 else B("polished_blackstone_bricks"))
        self.allow(56, 10, 122, 68, F4 - 2, F4 + 14)

    # ------------------------------------------------------------ c6: the rune chamber
    RUNES = {
        "fehu": ["X.X.X", "XXX..", "X.XX.", "XX...", "X....", "X....", "X...."],
        "uruz": ["XXX..", "X..X.", "X...X", "X...X", "X...X", "X...X", "X...X"],
        "thurisaz": ["X....", "XX...", "X.X..", "X..X.", "X.X..", "XX...", "X...."],
        "ansuz": ["X....", "XX...", "X.X..", "XX...", "X.X..", "X....", "X...."],
        "raido": ["XXX..", "X..X.", "X..X.", "XXX..", "X.X..", "X..X.", "X...X"],
        "kenaz": ["...X.", "..X..", ".X...", "X....", ".X...", "..X..", "...X."],
        "gebo": ["X...X", ".X.X.", "..X..", "..X..", "..X..", ".X.X.", "X...X"],
        "hagalaz": ["X...X", "X...X", "XX..X", "X.X.X", "X..XX", "X...X", "X...X"],
        "algiz": ["X.X.X", "X.X.X", ".XXX.", "..X..", "..X..", "..X..", "..X.."],
        "tiwaz": ["..X..", ".XXX.", "X.X.X", "..X..", "..X..", "..X..", "..X.."],
        "othala": ["..X..", ".X.X.", "X...X", ".X.X.", "..X..", ".X.X.", "X...X"],
    }

    def stamp_rune(self, cells, y0, glyph, glow):
        """cells: 5 wall cells left->right (local (lx, lz)), glyph drawn upward from y0 (top row first)."""
        a = self.a
        rows = self.RUNES[glyph]
        for r, row in enumerate(rows):
            y = y0 + (len(rows) - 1 - r)
            for c, ch in enumerate(row):
                x, z = self.w(*cells[c])
                if a.get(x, y, z) == AIR:
                    continue
                a.set(x, y, z, glow if ch == "X" else B("chiseled_deepslate"))

    def rune_chamber(self):
        a, rng, pal = self.a, self.rng, self.pal
        lx1, lz1, lx2, lz2 = 24, 66, 110, 136
        H = 25
        self.carve(lx1, lz1, lx2, lz2, F4, F4 + H - 1, floor_b=pal.floor)
        self.ceiling_beams(lx1, lz1, lx2, lz2, F4 + H - 1, axis="z", every=8, beam="polished_basalt")
        glows = [B("verdant_froglight"), B("sea_lantern"), B("pearlescent_froglight"), B("amethyst_block")]
        names = list(self.RUNES)
        k = 0
        for side, cells in self.faces(lx1, lz1, lx2, lz2):
            for i in range(2, len(cells) - 6, 9):
                self.stamp_rune(cells[i:i + 5], F4 + 5, names[k % len(names)], glows[(k // 3) % len(glows)])
                k += 1
        # rune pillars in two rows, glyphs on their faces
        for lx in range(40, 100, 15):
            for lz in (86, 116):
                for dx in range(5):
                    for dz in range(5):
                        x, z = self.w(lx + dx, lz + dz)
                        for y in range(F4, F4 + H):
                            a.set(x, y, z, pal.pillar if dx in (0, 4) or dz in (0, 4) else pal.wall())
                self.stamp_rune([(lx + d, lz - 0) for d in range(5)], F4 + 6, names[(lx + lz) % len(names)], rng.choice(glows))
                self.stamp_rune([(lx + d, lz + 4) for d in range(5)], F4 + 6, names[(lx + lz + 3) % len(names)], rng.choice(glows))
        # a great rune circle inlaid in the floor
        cx, cz = self.w(67, 101)
        for dx in range(-12, 13):
            for dz in range(-12, 13):
                d = math.hypot(dx, dz)
                if abs(d - 11) < 0.6 or abs(d - 7) < 0.5:
                    a.set(cx + dx, F4 - 1, cz + dz, B("gold_block"))
                elif d < 7 and (abs(dx) < 1 or abs(dz) < 1 or abs(abs(dx) - abs(dz)) < 1):
                    a.set(cx + dx, F4 - 1, cz + dz, B("waxed_cut_copper"))
        self.carve(111, 96, 121, 104, F5, F4 + 11)
        for lx in range(111, 114):
            for lz in range(96, 105):
                x, z = self.w(lx, lz)
                for y in range(F5 - 1, F4 - 1):
                    a.set(x, y, z, pal.wall())
                a.set(x, F4 - 1, z, pal.floor())
        rx_, rz_ = self.w(121, 100)
        self.post.append(lambda: C.flight(a, rx_, F5, rz_, "west", F4 - F5, 9, "deepslate_brick_stairs", support=pal.wall))
        self.allow(20, 62, 124, 140, F5 - 2, F4 + 14)
        self.add_zone("c6", (self.x0 + 26, F4 - 2, self.z0 + 68, self.x0 + 108, F4 + 3, self.z0 + 134), floor_mask=None, n=12)

    # ------------------------------------------------------------ boss: Fafnir's hoard cavern
    def hoard(self):
        a, rng, pal = self.a, self.rng, self.pal
        ccx, ccz, rx, rz = 156, 100, 36, 32
        n = fbm(self.sx, self.sz, 8, 2, self.seed + 33)
        floor_mix = mixer(rng, [(B("deepslate_tiles"), 3), (B("polished_deepslate"), 2), (B("raw_gold_block"), 1)])
        self.cav7 = {}
        for lx in range(ccx - rx, ccx + rx + 1):
            for lz in range(ccz - rz, ccz + rz + 1):
                d = math.hypot((lx - ccx) / rx, (lz - ccz) / rz)
                if d > 1:
                    continue
                top = F5 + int(14 + 26 * math.sqrt(max(0.0, 1 - d * d)) + (n[lx, lz] - 0.5) * 6)
                x, z = self.w(lx, lz)
                col = a.blk[lx, :, lz]
                col[F5 - self.Y0:top - self.Y0 + 1] = AIR
                a.set(x, F5 - 1, z, floor_mix())
                self.carved[lx, lz] = True
                self.cav7[(lx, lz)] = top
        self.ore_speckle(ccx - rx, ccz - rz, ccx + rx, ccz + rz, F5, F5 + 40, chance=0.06)
        cx, cz = self.w(ccx, ccz)
        R = 21

        def floor_fn(x, z, d):
            if abs(d - R + 0.6) < 0.7:
                return B("gold_block")
            ang = math.atan2(z - cz, x - cx)
            scale = abs(math.sin(ang * 6 + d * 0.5)) < 0.2 and 4 < d < R - 2
            if scale:
                return B("raw_gold_block")
            if d < 3:
                return B("gold_block")
            return B("deepslate_tiles") if (int(d) + (x + z) % 2) % 3 else B("polished_deepslate")
        ex, ez = self.w(111, 100)
        entry = self.doorway(ex, F4, ez, 9, 12, "z")
        ar = self.arena("boss", cx, F5, cz, R, "fafnir", "final", floor_fn=floor_fn, entry=entry)
        # the hoard: gold heaps all around the ring, chests, a few jewels; stalactites from the dome
        gold_mix = mixer(rng, [(B("gold_block"), 5), (B("raw_gold_block"), 3), (B("gold_ore"), 1), (B("emerald_block"), 0.2), (B("diamond_block"), 0.1)])
        for k in range(30):
            ang = k / 30 * 2 * math.pi + rng.uniform(-0.1, 0.1)
            r = rng.uniform(R + 3, R + 9)
            lx, lz = int(round(ccx + math.cos(ang) * r)), int(round(ccz + math.sin(ang) * r))
            if (lx, lz) not in self.cav7:
                continue
            if 180 <= lx <= 196 and lz < 92:
                continue
            x, z = self.w(lx, lz)
            self.heap(x, F5, z, rng.uniform(2.0, 3.6), gold_mix)
            if rng.random() < 0.4:
                a.put(x + 2, F5, z, B("chest", cardinal="south"))
        for (lx, lz), top in self.cav7.items():
            if rng.random() < 0.025:
                x, z = self.w(lx, lz)
                for t in range(rng.randint(1, 5)):
                    a.set(x, top - t, z, B("pointed_dripstone", dripstone_thickness="tip" if t == 0 else "middle", hanging=1))
        # exit: a corridor north from the cavern's east side to the portal alcove, gated
        self.carve(188, 72, 192, 92, F5, F5 + 5, floor_b=pal.floor)
        self.carve(182, 60, 198, 71, F5, F5 + 11, floor_b=pal.floor)
        xx, zz = self.w(190, 72)
        exitg = self.doorway(xx, F5, zz, 5, 6, "x")
        ar["exit"] = [list(p) for p in exitg]
        self.close(exitg)
        px, pz = self.w(190, 65)
        self.exit_portal(px, F5, pz)
        self.allow(116, 56, 202, 136, F5 - 2, F5 + 14)

    # ------------------------------------------------------------ finishing
    def finish(self):
        a = self.a
        rooms = [(70, 300, 202, 370, F1), (24, 205, 248, 295, F2), (24, 140, 130, 198, F2), (142, 144, 194, 196, F2), (206, 60, 246, 196, F3),
                 (120, 16, 248, 56, F4), (60, 14, 113, 58, F4), (24, 66, 110, 136, F4), (120, 60, 198, 132, F5)]
        for (lx1, lz1, lx2, lz2, fy) in rooms:
            x1, z1 = self.w(lx1, lz1)
            x2, z2 = self.w(lx2, lz2)
            self.light_fill((x1, z1, x2, z2), (fy, fy + 3), level=8, threshold=5, spacing=7)
        self.ambient = [dict(box=self.zones["c2"]["box"], particle="minecraft:lava_particle", rate=2),
                        dict(box=self.zones["c5"]["box"], particle="minecraft:basic_smoke_particle", rate=2),
                        dict(box=self.zones["c6"]["box"], particle="minecraft:enchanting_table_particle", rate=2)]
        self.boundary()
        self.ceiling(self.Y0 + self.SY - 1)
        a.fix_walls()


def build(seed=1):
    d = Nidavellir("d07", seed)
    d.build()
    return d
