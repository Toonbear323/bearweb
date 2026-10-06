"""Map 6 - Library ("대도서관"): a grand indoor library.

Layout (seen from above, north = up):

        +-----------+-----------+-----------+
        |  고문서    |   서고     |  어린이    |
        | archives  |  stacks   | kids      |
        +-----------+  (2 lv)   +-----------+
        | 마법 서재  |  ( 원형홀 )  |  열람실    |
        | arcane    |  rotunda  | reading   |
        +-----------+  3 levels +-----------+
        |  실내정원   |  입구 홀    |  북카페    |
        | garden    |  entrance | cafe      |
        +-----------+-----------+-----------+

The rotunda in the middle is three storeys tall (ring balconies at level 2 and 3, a copper dome with an
oculus and a giant globe). Every wing has a level-2 gallery joined to the rotunda balcony, so there are
two connected floors to chase each other on. The building is closed (walls, windows, roof, dome), and a
garden around it is only there to be seen through the windows.
"""
import math
import random

import numpy as np
import amulet_nbt as an

from mcw import B, AIR, Area, simple_be, sign_be, flowerpot_be, banner_be, chiseled_bookshelf_be
from gen_common import (stair, slab, disk, ring, leaf_blob, leaves_of, log_of, oak_tree, big_oak, cherry_tree,
                        birch_tree, spruce_tree, tall_plant, FLOWERS, wall_sign, standing_sign, value_noise)

F1 = 64          # level-1 floor block
P = 65           # level-1 feet
L2 = 71          # level-2 floor block
P2 = 72
L3 = 78          # level-3 floor block (rotunda only)
P3 = 79
CEIL = 80        # ceiling block of wings and corner rooms
BX, BZ = 72, 64  # outer wall (outer face) half sizes
RD = 19.5        # rotunda inner radius
RW = 21.5        # rotunda drum outer radius
DOME_Y = 86

ZONE_NAMES = {
    "rot": "중앙 원형홀", "N": "서고", "S": "입구 홀", "E": "열람실", "W": "마법 서재",
    "NE": "어린이 도서관", "NW": "고문서 보관소", "SE": "북카페", "SW": "실내 정원",
}
IW_ARCHES = [  # interior-wall doorways (axis, wall coordinate, centre along the wall)
    ("x", 19, -41), ("x", 19, 41), ("x", -19, -41), ("x", -19, 41),
    ("z", -19, 45), ("z", -19, -45), ("z", 19, 45), ("z", 19, -45),
]


class Library:
    def __init__(self, cx, cz):
        self.name = "library"
        self.cx, self.cz = cx, cz
        self.H0 = F1
        self.R = 80
        self.a = Area("library", cx - 112, cz - 112, 224, 224, y0=32, sy=112, biome=1)
        self.rng = random.Random(6606)
        self.spawns = []
        self.pois = {}
        self.zone = {}
        self.l2 = set()          # level-2 floor cells (local)
        self.signs = []

    # ------------------------------------------------------------------ local helpers
    def set(self, x, y, z, b):
        self.a.set(self.cx + x, y, self.cz + z, b)

    def put(self, x, y, z, b):
        self.a.put(self.cx + x, y, self.cz + z, b)

    def get(self, x, y, z):
        return self.a.get(self.cx + x, y, self.cz + z)

    def fill(self, x1, y1, z1, x2, y2, z2, b, only_air=False):
        self.a.fill(self.cx + x1, y1, self.cz + z1, self.cx + x2, y2, self.cz + z2, b, only_air=only_air)

    def chisel(self, x, y, z, direction, mask=None):
        mask = mask if mask is not None else self.rng.randrange(1, 64)
        self.set(x, y, z, B("chiseled_bookshelf", books_stored=mask, direction=direction))
        self.a.add_be(chiseled_bookshelf_be(self.cx + x, y, self.cz + z, mask))

    def be(self, kind, x, y, z, **extra):
        self.a.add_be(simple_be(kind, self.cx + x, y, self.cz + z, **extra))

    def inside(self, x, z):
        return abs(x - self.cx) <= BX and abs(z - self.cz) <= BZ

    def zone_of(self, x, z):
        """Zone of a local cell."""
        if abs(x) > BX or abs(z) > BZ:
            return "out"
        if abs(x) >= BX - 1 or abs(z) >= BZ - 1:
            return "ow"
        r = math.hypot(x, z)
        if r <= RD:
            return "rot"
        if r <= RW:
            if (abs(x) <= 5 and abs(z) > 15) or (abs(z) <= 5 and abs(x) > 15):
                return "arch"
            return "drum"
        if abs(x) <= 19 and abs(z) <= 19:
            return "pocket"
        if (abs(x) == 19 and abs(z) >= 19) or (abs(z) == 19 and abs(x) >= 19):
            return "iw"
        if abs(x) <= 18:
            return "N" if z < 0 else "S"
        if abs(z) <= 18:
            return "E" if x > 0 else "W"
        if x > 0:
            return "NE" if z < 0 else "SE"
        return "NW" if z < 0 else "SW"

    def cells(self, zone):
        return [(x, z) for (x, z), zz in self.zone.items() if zz == zone]

    # ------------------------------------------------------------------ build
    def build(self):
        for x in range(-BX, BX + 1):
            for z in range(-BZ, BZ + 1):
                self.zone[(x, z)] = self.zone_of(x, z)
        self.garden_outside()
        self.shell()
        self.iw_arches()
        self.windows()
        self.rotunda()
        self.hall()
        self.stacks()
        self.reading()
        self.arcane()
        self.kids()
        self.archives()
        self.cafe()
        self.garden_room()
        self.labels()
        self.lighting()
        self.a.fix_walls()
        self.a.prune_be()
        return self.a

    # ------------------------------------------------------------------ shell
    def floor_block(self, zone, x, z):
        if zone == "rot":
            r = math.hypot(x, z)
            ang = math.degrees(math.atan2(z, x)) % 30
            if r < 1.5:
                return B("chiseled_quartz_block")
            if int(r) in (6, 12, 18):
                return B("polished_blackstone")
            if 2 <= r < 12 and (ang < 2.5 or ang > 27.5):
                return B("gold_block") if r < 6 else B("polished_blackstone")
            return B("smooth_quartz") if int(r) % 2 == 0 else B("polished_diorite")
        if zone in ("arch",):
            return B("polished_blackstone")
        if zone == "S":
            return B("polished_blackstone") if (x + z) % 2 == 0 else B("smooth_quartz")
        if zone == "N":
            return B("dark_oak_planks") if z % 5 not in (0,) else B("spruce_planks")
        if zone == "E":
            if abs(z) <= 1:
                return B("red_wool") if abs(z) == 0 else B("spruce_planks")
            return B("spruce_planks") if (x // 2 + z) % 2 == 0 else B("dark_oak_planks")
        if zone == "W":
            return B("deepslate_tiles") if (x + z) % 2 == 0 else B("polished_deepslate")
        if zone == "NE":
            return B("birch_planks")
        if zone == "NW":
            return B("spruce_planks") if (x * 3 + z) % 7 else B("stripped_spruce_log", axis="x")
        if zone == "SE":
            return B("white_terracotta") if (x + z) % 2 == 0 else B("black_terracotta")
        if zone == "SW":
            return B("grass_block")
        return B("stone_bricks")

    def shell(self):
        a = self.a
        wain = B("dark_oak_planks")
        trim = B("stripped_dark_oak_log", axis="y")
        plaster = B("smooth_sandstone")
        cornice = B("dark_oak_planks")
        ext = B("stone_bricks")
        base = B("polished_deepslate")
        for (x, z), zn in self.zone.items():
            self.fill(x, 58, z, x, F1 - 1, z, B("stone"))
            if zn in ("rot", "arch", "N", "S", "E", "W", "NE", "NW", "SE", "SW"):
                self.set(x, F1, z, self.floor_block(zn, x, z))
                top = CEIL if zn not in ("rot", "arch") else DOME_Y
                self.fill(x, P, z, x, top - 1 if zn != "arch" else CEIL - 1, z, AIR)
                if zn not in ("rot", "arch"):
                    if zn == "SW":
                        self.set(x, CEIL, z, B("glass") if (x % 6 and z % 6) else B("dark_oak_planks"))
                    else:
                        beam = x % 6 == 0 or z % 6 == 0
                        self.set(x, CEIL, z, B("dark_oak_planks") if beam else B("spruce_planks"))
                    self.set(x, CEIL + 1, z, B("deepslate_tiles"))
                elif zn == "arch":
                    self.fill(x, 76, z, x, CEIL + 1, z, B("stone_bricks"))
                continue
            # walls
            if zn == "ow":
                top = CEIL + 3
                outer = abs(x) == BX or abs(z) == BZ
                for y in range(F1, top + 1):
                    if outer:
                        if y <= F1 + 2:
                            b = base
                        elif y == top:
                            b = B("stone_brick_wall")
                        elif y == top - 1 or y == 75:
                            b = B("polished_andesite")
                        elif (x if abs(z) == BZ else z) % 9 == 0:
                            b = B("chiseled_stone_bricks") if y == 74 else B("polished_andesite")
                        else:
                            b = ext
                    else:
                        b = self.style(x, z, y)
                    self.set(x, y, z, b)
            elif zn in ("iw", "pocket", "drum"):
                top = CEIL + 1 if zn != "drum" else DOME_Y
                for y in range(F1, top + 1):
                    self.set(x, y, z, self.style(x, z, y) if zn == "iw" else B("stone_bricks"))

    def style(self, x, z, y):
        """Interior wall face: dark oak wainscot, log trim, sandstone plaster, pilasters."""
        along = z if abs(x) in (BX - 1, 19) else x
        if along % 8 == 0:
            return B("stripped_dark_oak_log", axis="y")
        if y <= F1:
            return B("stone_bricks")
        if y <= P + 2:
            return B("dark_oak_planks")
        if y == P + 3:
            return B("stripped_dark_oak_log", axis="x" if abs(z) in (BZ - 1, 19) else "z")
        if y >= CEIL - 1:
            return B("dark_oak_planks")
        return B("smooth_sandstone")

    def iw_arches(self):
        """Arched doorways through the interior walls (wing <-> corner room), level 1."""
        for axis, w, c in IW_ARCHES:
            for t in range(c - 2, c + 3):
                x, z = (w, t) if axis == "x" else (t, w)
                for y in range(P, P + 5):
                    self.set(x, y, z, AIR)
                self.set(x, P + 5, z, B("stripped_dark_oak_log", axis="z" if axis == "x" else "x"))
            for t in (c - 2, c + 2):
                x, z = (w, t) if axis == "x" else (t, w)
                self.set(x, P + 4, z, B("dark_oak_planks"))
            for t in (c - 3, c + 3):
                x, z = (w, t) if axis == "x" else (t, w)
                for y in range(P, P + 6):
                    self.set(x, y, z, B("stripped_dark_oak_log", axis="y"))

    def windows(self):
        """Tall arched windows in the outer walls with a warm stained-glass top."""
        pane = B("glass_pane")
        top_pane = B("orange_stained_glass_pane")
        for side in ("n", "s", "e", "w"):
            if side in ("n", "s"):
                z_in = -(BZ - 1) if side == "n" else BZ - 1
                z_out = -BZ if side == "n" else BZ
                coords = [(t, z_in, z_out) for t in range(-BX + 4, BX - 3)]
            else:
                x_in = BX - 1 if side == "e" else -(BX - 1)
                x_out = BX if side == "e" else -BX
                coords = [(t, x_in, x_out) for t in range(-BZ + 4, BZ - 3)]
            for t, a_in, a_out in coords:
                m = (t + 4) % 9
                if m not in (3, 4, 5):
                    continue
                if abs(abs(t) - 19) <= 1:
                    continue        # interior wall joins here
                if side == "s" and abs(t) <= 4:
                    continue        # main entrance
                if side == "e" and abs(t) <= 4:
                    continue        # fireplace
                for y in range(P + 2, P + 12):
                    if m != 4 and y == P + 11:
                        continue
                    b = top_pane if y >= P + 10 else pane
                    for aa in (a_in, a_out):
                        x, z = (t, aa) if side in ("n", "s") else (aa, t)
                        self.set(x, y, z, b)
                for aa in (a_in,):
                    x, z = (t, aa) if side in ("n", "s") else (aa, t)
                    self.set(x, P + 1, z, B("dark_oak_planks"))

    # ------------------------------------------------------------------ level-2 helpers
    def l2_floor(self, cells, b=None):
        b = b or B("dark_oak_planks")
        for (x, z) in cells:
            if self.zone.get((x, z)) in ("rot", "arch", "N", "S", "E", "W"):
                self.set(x, L2, z, b)
                self.l2.add((x, z))

    def railing(self, cells, y=P2, gap=()):
        """Fence on every level-2 cell that borders a drop."""
        fence = B("dark_oak_fence")
        for (x, z) in cells:
            if (x, z) in gap:
                continue
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, z + dz)
                if n not in self.l2 and self.zone.get(n) in ("rot", "arch", "N", "S", "E", "W"):
                    if self.get(x, y, z) == AIR:
                        self.set(x, y, z, fence)
                    break

    def flight(self, x0, z0, d, width_dir, width=2, block="dark_oak_stairs", y0=P, steps=7, fill=B("dark_oak_planks")):
        """Straight stair flight. Step t sits at (x0 + d*t, z0 + d*t) with its block at y0 + t;
        d = (dx, dz) rising direction, width_dir = sideways unit vector."""
        dx, dz = d
        wx, wz = width_dir
        asc = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}[(dx, dz)]
        cells = []
        for t in range(steps):
            for w in range(width):
                x, z = x0 + dx * t + wx * w, z0 + dz * t + wz * w
                for y in range(y0, y0 + t):
                    self.set(x, y, z, fill)
                self.set(x, y0 + t, z, stair(block, asc))
                for y in range(y0 + t + 1, y0 + t + 4):
                    if self.get(x, y, z) not in (AIR,):
                        self.set(x, y, z, AIR)
                cells.append((x, z))
        return cells

    def chandelier(self, x, ytop, z, length, r=2, lamp=None, soul=False):
        lamp = lamp or B("soul_lantern" if soul else "lantern", hanging=1)
        for i in range(length):
            self.set(x, ytop - i, z, B("chain"))
        yb = ytop - length
        self.set(x, yb, z, B("dark_oak_fence"))
        for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
            for t in range(1, r + 1):
                self.set(x + dx * t // r, yb, z + dz * t // r, B("dark_oak_fence"))
            self.set(x + dx, yb - 1, z + dz, lamp)
        self.set(x, yb - 1, z, lamp)

    def sconce(self, x, y, z):
        self.set(x, y, z, B("dark_oak_fence"))
        self.set(x, y - 1, z, B("lantern", hanging=1))

    def bookshelf_wall(self, cells, y1, y2, chisel=0.12, face=None):
        rng = self.rng
        for (x, z) in cells:
            if self.get(x, P, z) == AIR or self.get(x, P + 1, z) == AIR:
                continue            # doorway
            for y in range(y1, y2 + 1):
                if face is not None and rng.random() < chisel:
                    self.chisel(x, y, z, face)
                else:
                    self.set(x, y, z, B("bookshelf"))

    def table(self, x1, z1, x2, z2, top="dark_oak_slab"):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                self.set(x, P, z, B(top, half="top"))

    def chair(self, x, z, face):
        back = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[face]
        self.set(x, P, z, stair("spruce_stairs", back))

    # ------------------------------------------------------------------ rotunda
    def rotunda(self):
        a = self.a
        rng = self.rng
        rot = self.cells("rot")
        # drum inner face: bookshelves on every level, clerestory windows above the roof
        for (x, z) in self.cells("drum"):
            r = math.hypot(x, z)
            inner = r <= RD + 1.05
            for y in range(P, DOME_Y + 1):
                if inner:
                    if y in (L2, L3):
                        b = B("dark_oak_planks")
                    elif y in (P + 5, P2 + 5):
                        b = B("stripped_dark_oak_log", axis="y")
                    elif y <= L3 + 3:
                        b = B("bookshelf")
                    elif 82 <= y <= 85:
                        ang = math.degrees(math.atan2(z, x)) % 20
                        b = B("yellow_stained_glass") if 4 < ang < 16 else B("dark_oak_planks")
                    else:
                        b = B("dark_oak_planks")
                else:
                    if 82 <= y <= 85:
                        ang = math.degrees(math.atan2(z, x)) % 20
                        b = B("yellow_stained_glass") if 4 < ang < 16 else B("stone_bricks")
                    elif y == DOME_Y:
                        b = B("polished_andesite")
                    else:
                        b = B("stone_bricks")
                self.set(x, y, z, b)
        # arches: level-1 passage and level-2 passage stacked, keystone above
        for (x, z) in self.cells("arch"):
            self.set(x, F1, z, B("polished_blackstone"))
            self.fill(x, P, z, x, 75, z, AIR)
            self.set(x, L2, z, B("dark_oak_planks"))
            self.l2.add((x, z))
            self.set(x, 76, z, B("chiseled_stone_bricks") if (x == 0 or z == 0) else B("stone_bricks"))
            for y in range(77, DOME_Y + 1):
                if 82 <= y <= 85:
                    b = B("yellow_stained_glass") if (abs(x) + abs(z)) % 4 == 1 else B("stone_bricks")
                elif y == DOME_Y:
                    b = B("polished_andesite")
                else:
                    b = B("stone_bricks")
                self.set(x, y, z, b)
        # level-2 and level-3 rings
        l2 = [(x, z) for (x, z) in rot if math.hypot(x, z) >= 14.5]
        self.l2_floor(l2)
        for (x, z) in rot:
            r = math.hypot(x, z)
            if r >= 16.5:
                self.set(x, L3, z, B("spruce_planks"))
        # ladders from level 2 to level 3 at the four diagonals (in the gap of the level-3 ring)
        self.ladders = []
        for sx, sz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            x, z = 13 * sx, 14 * sz
            # wall cell behind (outwards in z)
            for y in range(P2, L3 + 1):
                self.set(x, y, z, B("ladder", facing_direction=2 if sz > 0 else 3))
            # solid backing for the ladder
            for y in range(P2, L3 + 2):
                if self.get(x, y, z + sz) == AIR:
                    self.set(x, y, z + sz, B("bookshelf"))
            self.ladders.append((x, z))
        # railings
        fence = B("dark_oak_fence")
        for (x, z) in rot:
            r = math.hypot(x, z)
            if 14.5 <= r < 15.5:
                self.set(x, P2, z, fence)
            if 16.5 <= r < 17.5 and (x, z) not in self.ladders:
                self.set(x, P3, z, fence)
        for (x, z) in self.ladders:
            self.set(x, P3, z, AIR)
            self.set(x, P2, z, B("ladder", facing_direction=2 if z > 0 else 3))
        # lanterns under the level-2 ring
        for (x, z) in rot:
            r = math.hypot(x, z)
            if 16 <= r < 17 and (x + z) % 5 == 0:
                self.set(x, L2 - 1, z, B("lantern", hanging=1))
            if 18 <= r < 19 and (x * 3 + z) % 7 == 0:
                self.set(x, L3 - 1, z, B("lantern", hanging=1))
        # dome: coffered quartz with dark ribs, oculus at the top, copper outside
        for x in range(-23, 24):
            for z in range(-23, 24):
                for y in range(DOME_Y, DOME_Y + 24):
                    d = math.sqrt(x * x + z * z + (y - DOME_Y) ** 2)
                    rh = math.hypot(x, z)
                    if RD + 0.5 < d <= RD + 1.5:
                        ang = math.degrees(math.atan2(z, x)) % 30
                        if rh < 4.5:
                            b = B("glass")
                        elif ang < 3 or ang > 27 or (y - DOME_Y) % 5 == 0:
                            b = B("dark_oak_planks")
                        else:
                            b = B("quartz_bricks")
                        self.set(x, y, z, b)
                    elif RD + 1.5 < d <= RD + 2.6:
                        self.set(x, y, z, B("glass") if rh < 4.5 else B("waxed_oxidized_cut_copper"))
                    elif d <= RD + 0.5 and y > DOME_Y:
                        self.set(x, y, z, AIR)
        # giant globe on a pedestal in the middle
        self.fill(-2, P, -2, 2, P, 2, B("polished_blackstone_bricks"))
        self.fill(-1, P + 1, -1, 1, P + 1, 1, B("gold_block"))
        n = value_noise(40, 40, 5, 9)
        gy = 71.5
        for x in range(-5, 6):
            for y in range(66, 78):
                for z in range(-5, 6):
                    d = math.sqrt(x * x + (y - gy) ** 2 + z * z)
                    if d <= 4.6:
                        v = n[(x * 2 + y + 20) % 40, (z * 2 - y + 20) % 40]
                        b = "blue_concrete" if v < 0.46 else ("lime_concrete" if v < 0.62 else "green_concrete")
                        if abs(y - gy) > 3.6:
                            b = "white_concrete"
                        self.set(x, y, z, B(b))
        for t in range(0, 360, 4):
            x = round(math.cos(math.radians(t)) * 6)
            y = round(gy + math.sin(math.radians(t)) * 6)
            if y >= P + 1:
                self.set(x, y, 0, B("gold_block"))
        # librarian desk ring with four openings
        for (x, z) in rot:
            r = math.hypot(x, z)
            ang = math.degrees(math.atan2(z, x)) % 90
            if 8.5 <= r < 9.6 and 12 < ang < 78:
                self.set(x, P, z, B("dark_oak_slab", half="top"))
        for (x, z) in ((7, 0), (-7, 0), (0, 7), (0, -7)):
            self.set(x, P, z, B("lectern", cardinal="south" if z < 0 else "north" if z > 0 else "east" if x < 0 else "west"))
        # chandelier from the oculus
        for ang in range(0, 360, 30):
            x, z = round(math.cos(math.radians(ang)) * 4), round(math.sin(math.radians(ang)) * 4)
            self.set(x, DOME_Y + 3, z, B("lantern", hanging=1))
            self.set(x, DOME_Y + 4, z, B("chain"))
        ring(a, self.cx, DOME_Y + 5, self.cz, 3.5, 4.6, B("dark_oak_fence"))
        for t in range(1, 4):
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                self.set(dx * t, DOME_Y + 5, dz * t, B("dark_oak_fence"))
        self.set(0, DOME_Y + 5, 0, B("dark_oak_fence"))
        self.set(0, DOME_Y + 4, 0, B("lantern", hanging=1))
        for y in range(DOME_Y + 6, DOME_Y + 21):
            self.set(0, y, 0, B("chain"))
        # banners between the level-2 bookshelves
        self.pois["rotunda"] = (self.cx, P, self.cz)
        self.pois["globe"] = (self.cx, 77, self.cz)

    # ------------------------------------------------------------------ south: entrance hall
    def hall(self):
        cells = self.cells("S")
        l2 = [(x, z) for (x, z) in cells if abs(x) >= 13 or z >= 57 or z <= 27]
        self.l2_floor(l2)
        # pillars under the balcony edge
        for z in range(30, 57, 6):
            for x in (-13, 13):
                self.fill(x, P, z, x, L2 - 1, z, B("stripped_dark_oak_log", axis="y"))
                self.set(x, L2 - 1, z, B("dark_oak_planks"))
        # double staircase up to the south balcony
        s1 = self.flight(-12, 50, (0, 1), (1, 0))
        s2 = self.flight(11, 50, (0, 1), (1, 0))
        self.railing(l2, gap=set((x, 57) for x in (-12, -11, 11, 12)))
        # circulation desk (U shape) with a bell
        for x in range(-6, 7):
            for z in range(36, 43):
                edge = x in (-6, 6) or z == 42
                if edge and not (z == 36):
                    self.set(x, P, z, B("dark_oak_planks"))
                    self.set(x, P + 1, z, B("dark_oak_slab"))
        self.set(0, P + 1, 42, B("bell", attachment="standing", direction=0))
        self.be("Bell", 0, P + 1, 42)
        self.set(-4, P + 1, 42, B("lantern"))
        self.set(4, P + 1, 42, B("lantern"))
        self.set(-5, P, 38, B("lectern", cardinal="east"))
        self.set(5, P, 38, B("lectern", cardinal="west"))
        # card catalogues under the side balconies
        for z in range(28, 56):
            if z % 6 == 0 or abs(z - 41) <= 3:
                continue
            for x in (-18, 18):
                for y in range(P, P + 3):
                    self.chisel(x, y, z, 1 if x > 0 else 3, self.rng.randrange(8, 64))
        # benches facing the desk
        for x in range(-8, 9):
            if abs(x) <= 1:
                continue
            self.set(x, P, 46, stair("spruce_stairs", "south"))
        # main entrance (closed doors) on the south wall
        zi = BZ - 1
        for x in range(-4, 5):
            for y in range(P, P + 8):
                self.set(x, y, zi, B("polished_blackstone_bricks"))
        for x in (-1, 0, 1):
            for y in range(P, P + 4):
                self.set(x, y, zi, B("dark_oak_planks"))
        self.set(-1, P, zi, B("dark_oak_door", cardinal="north", upper_block_bit=0, door_hinge_bit=0))
        self.set(-1, P + 1, zi, B("dark_oak_door", cardinal="north", upper_block_bit=1, door_hinge_bit=0))
        self.set(0, P, zi, B("dark_oak_door", cardinal="north", upper_block_bit=0, door_hinge_bit=1))
        self.set(0, P + 1, zi, B("dark_oak_door", cardinal="north", upper_block_bit=1, door_hinge_bit=1))
        self.set(1, P, zi, B("dark_oak_planks"))
        for x in (-3, 3):
            self.set(x, P + 2, zi - 1, B("lantern"))
            self.set(x, P + 1, zi - 1, B("dark_oak_fence"))
            self.set(x, P, zi - 1, B("dark_oak_fence"))
        self.a.add_be(sign_be(self.cx + 1, P + 2, self.cz + zi - 1, "§l§6대도서관\n§r§f정문 (닫힘)", glow=True))
        self.set(1, P + 2, zi - 1, B("dark_oak_wall_sign", facing_direction=2))
        # big chandeliers
        for z in (34, 48):
            self.chandelier(0, CEIL - 1, z, 4, r=3)
        # potted plants by the pillars
        for z in range(33, 57, 6):
            for x in (-12, 12):
                if self.get(x, P, z) == AIR:
                    self.set(x, P, z, B("flower_pot"))
                    self.a.add_be(flowerpot_be(self.cx + x, P, self.cz + z, "azalea"))
        # spawn points
        for x in (0, -4, 4):
            self.spawns.append((self.cx + x, P, self.cz + 53))
        self.pois["entrance"] = (self.cx, P, self.cz + 53)

    # ------------------------------------------------------------------ north: book stacks (two levels)
    def stacks(self):
        rng = self.rng
        cells = self.cells("N")
        rows = [(-60, -59), (-55, -54), (-50, -49), (-45, -44), (-40, -39), (-35, -34), (-30, -29)]
        # level 1 shelves (support the level-2 floor)
        for z1, z2 in rows:
            for z in (z1, z2):
                for x in range(-18, 19):
                    if abs(x) <= 2 or abs(x) in (9, 10):
                        continue
                    if (x, z) not in self.zone or self.zone[(x, z)] != "N":
                        continue
                    face = 2 if z == z1 else 0
                    for y in range(P, L2):
                        if rng.random() < 0.08:
                            self.chisel(x, y, z, face)
                        else:
                            self.set(x, y, z, B("bookshelf"))
        # level-2 floor except the central light well and the stairwell landing
        l2 = [(x, z) for (x, z) in cells if (z <= -28 and not (abs(x) <= 3 and -57 <= z <= -28)) or
              (z > -28 and abs(x) <= 5)]
        l2 = [(x, z) for (x, z) in l2 if not (abs(x) in (17, 18) and z > -29)]
        self.l2_floor(l2)
        # stairs up along both side walls
        self.flight(-18, -22, (0, -1), (1, 0))
        self.flight(17, -22, (0, -1), (1, 0))
        # the flight top steps sit at z=-28; landing cells beyond
        self.railing(l2, gap=set((x, -29) for x in (-18, -17, 17, 18)))
        # level 2 shelves (the first row stays open as a landing corridor)
        for z1, z2 in rows[:-1]:
            for z in (z1, z2):
                for x in range(-18, 19):
                    if abs(x) <= 6 or abs(x) in (9, 10):
                        continue
                    if (x, z) not in self.l2:
                        continue
                    for y in range(P2, P2 + 6):
                        self.set(x, y, z, B("bookshelf"))
        # lanterns in the level-1 aisles (hanging from the level-2 floor) and over level 2
        for (x, z) in cells:
            aisle = all(not (z1 <= z <= z2) for z1, z2 in rows)
            if aisle and (x, z) in self.l2 and x % 6 == 3 and z % 5 == 2:
                if self.get(x, L2 - 1, z) == AIR:
                    self.set(x, L2 - 1, z, B("lantern", hanging=1))
        for z in range(-56, -28, 8):
            self.chandelier(0, CEIL - 1, z, 3, r=2)
        for z in range(-58, -30, 8):
            for x in (-13, 13):
                if self.get(x, CEIL - 1, z) == AIR:
                    self.set(x, CEIL - 1, z, B("chain"))
                    self.set(x, CEIL - 2, z, B("lantern", hanging=1))
        # library ladders leaning on a few shelves (level 1)
        for (x, z, f) in ((5, -58, 3), (-7, -53, 3), (13, -48, 3), (-14, -43, 3), (6, -38, 3), (-5, -33, 3)):
            if self.zone.get((x, z)) == "N" and self.get(x, P, z) == AIR and self.get(x, P, z - 1) != AIR:
                for y in range(P, P + 4):
                    self.set(x, y, z, B("ladder", facing_direction=f))
        self.pois["stacks"] = (self.cx, P, self.cz - 45)

    # ------------------------------------------------------------------ east: reading room
    def side_wing(self, zone, sx):
        """Shared frame of the east/west wings: U-shaped level-2 gallery with stairs at the far end."""
        cells = self.cells(zone)
        near = min(abs(x) for x, z in cells)
        l2 = [(x, z) for (x, z) in cells if abs(z) >= 12 or abs(x) <= 27]
        self.l2_floor(l2)
        far = 64
        s1 = self.flight(sx * far, 5, (0, 1), (sx, 0))
        s2 = self.flight(sx * far, -5, (0, -1), (sx, 0))
        gaps = set([(sx * far, 12), (sx * (far + 1), 12), (sx * far, -12), (sx * (far + 1), -12)])
        self.railing(l2, gap=gaps)
        # bookshelves on the walls of both levels (gallery side)
        for (x, z) in cells:
            if abs(z) == 18:
                face = 2 if z > 0 else 0
                self.bookshelf_wall([(x, z + (1 if z > 0 else -1))], P, L2 - 1)
        # columns under the gallery edges
        for x in range(28, 64, 6):
            for z in (-12, 12):
                self.fill(sx * x, P, z, sx * x, L2 - 1, z, B("stripped_dark_oak_log", axis="y"))
        return l2

    def reading(self):
        l2 = self.side_wing("E", 1)
        # gallery bookshelves (level 2) against the interior walls
        for x in range(22, 71):
            for z in (-18, 18):
                if (x, z) in self.l2 and self.get(x, P2, z) in (AIR, B("dark_oak_fence")):
                    for y in range(P2, P2 + 6):
                        self.set(x, y, z, B("bookshelf"))
        # long reading tables with lamps and chairs
        for zc in (-6, 0, 6):
            for x in range(31, 60):
                if 44 <= x <= 46:
                    continue
                self.set(x, P, zc, B("dark_oak_slab", half="top"))
                if x % 4 == 1:
                    self.set(x, P + 1, zc, B("lantern"))
                for dz in (-1, 1):
                    if x % 2 == 0:
                        self.chair(x, zc + dz, (0, -dz))
        # fireplace on the east wall
        xi = BX - 1
        self.fill(xi - 3, P, -3, xi, P + 8, 3, B("stone_bricks"))
        self.fill(xi - 3, P, -1, xi - 2, P + 1, 1, AIR)
        for z in (-1, 0, 1):
            self.set(xi - 2, P, z, B("campfire", cardinal="west"))
            self.be("Campfire", xi - 2, P, z)
            self.set(xi - 3, P, z, B("iron_bars"))
            self.set(xi - 3, P + 1, z, B("iron_bars"))
        self.fill(xi - 4, P + 3, -3, xi - 4, P + 3, 3, B("dark_oak_slab", half="top"))
        self.set(xi - 4, P + 4, -2, B("lantern"))
        self.set(xi - 4, P + 4, 2, B("lantern"))
        self.fill(xi - 3, P + 4, -1, xi - 3, P + 6, 1, B("bookshelf"))
        # armchairs in front of the fire
        for z in (-3, 3):
            self.chair(xi - 8, z, (1, 0))
            self.set(xi - 8, P, z + (1 if z > 0 else -1), B("spruce_slab"))
        self.set(xi - 8, P, 0, B("spruce_slab"))
        self.set(xi - 8, P + 1, 0, B("flower_pot"))
        self.a.add_be(flowerpot_be(self.cx + xi - 8, P + 1, self.cz, "fern"))
        for x in (36, 52):
            self.chandelier(x, CEIL - 1, 0, 4, r=2)
        self.pois["reading"] = (self.cx + 45, P, self.cz)

    # ------------------------------------------------------------------ west: arcane study
    def arcane(self):
        a = self.a
        rng = random.Random(44)
        l2 = self.side_wing("W", -1)
        for x in range(-70, -21):
            for z in (-18, 18):
                if (x, z) in self.l2 and self.get(x, P2, z) in (AIR, B("dark_oak_fence")):
                    for y in range(P2, P2 + 6):
                        self.set(x, y, z, B("bookshelf"))
        # starry ceiling
        for (x, z) in self.cells("W"):
            self.set(x, CEIL, z, B("black_concrete") if (x + z) % 5 else B("blue_concrete"))
            if rng.random() < 0.05:
                self.set(x, CEIL, z, B("glowstone") if rng.random() < 0.4 else B("sea_lantern"))
        # enchanting dais with the classic bookshelf ring
        cx, cz = -45, 0
        self.fill(cx - 3, P, cz - 3, cx + 3, P, cz + 3, B("polished_deepslate"))
        for x in range(cx - 2, cx + 3):
            for z in range(cz - 2, cz + 3):
                ring_c = max(abs(x - cx), abs(z - cz)) == 2
                if ring_c and not (z == cz + 2 and abs(x - cx) <= 0) and not (z == cz - 2 and abs(x - cx) <= 0):
                    self.set(x, P + 1, z, B("bookshelf"))
                    self.set(x, P + 2, z, B("bookshelf"))
        self.set(cx, P + 1, cz, B("enchanting_table"))
        self.be("EnchantTable", cx, P + 1, cz)
        for (x, z) in self.cells("W"):
            d = math.hypot(x - cx, z - cz)
            if 5.5 <= d < 6.5 and self.get(x, P, z) == AIR:
                self.set(x, F1, z, B("amethyst_block"))
            elif 4.5 <= d < 5.5 and self.get(x, P, z) == AIR:
                self.set(x, P, z, B("purple_carpet"))
        # lecterns and candles around
        for (dx, dz, c) in ((-7, -4, "east"), (7, -4, "west"), (-7, 4, "east"), (7, 4, "west")):
            self.set(cx + dx, P, cz + dz, B("lectern", cardinal=c))
        # alchemy benches by the far wall
        for z in range(-8, 9):
            x = -66
            if abs(z) <= 1:
                continue
            self.set(x, P, z, B("polished_deepslate"))
            if z % 3 == 0:
                self.set(x, P + 1, z, B("brewing_stand"))
                self.be("BrewingStand", x, P + 1, z)
            elif z % 3 == 1:
                self.set(x, P + 1, z, B("purple_candle", candles=2, lit=1))
            else:
                self.set(x, P + 1, z, B("amethyst_cluster", face="up"))
        for z in (-1, 0, 1):
            self.set(-66, P, z, B("cauldron", cauldron_liquid="water", fill_level=6))
            self.be("Cauldron", -66, P, z)
        # floating orrery: sun and planets hanging from the starry ceiling
        planets = [(-45, 0, 75, 2.2, "glowstone"), (-38, -5, 76, 1.2, "blue_concrete"),
                   (-53, 4, 74, 1.0, "orange_terracotta"), (-50, -6, 77, 0.8, "light_gray_concrete"),
                   (-36, 6, 75, 1.4, "red_terracotta")]
        for (px, pz, py, r, mat) in planets:
            for x in range(int(px - r - 1), int(px + r + 2)):
                for y in range(int(py - r - 1), int(py + r + 2)):
                    for z in range(int(pz - r - 1), int(pz + r + 2)):
                        if (x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2 <= r * r:
                            self.set(x, y, z, B(mat))
            for y in range(int(py + r) + 1, CEIL):
                self.set(px, y, pz, B("chain"))
        self.pois["arcane"] = (self.cx - 45, P, self.cz)

    # ------------------------------------------------------------------ corner rooms
    def kids(self):
        cells = self.cells("NE")
        cols = ["red", "orange", "yellow", "lime", "light_blue", "purple", "pink"]
        for (x, z) in cells:
            self.set(x, P, z, B(cols[(x // 3) % len(cols)] + "_carpet") if (z % 7 in (0, 1)) else AIR)
        # low colourful shelves
        for (x1, z1) in ((26, -58), (40, -58), (54, -58), (26, -26), (54, -26)):
            for x in range(x1, x1 + 8):
                self.set(x, P, z1, B("bookshelf"))
                self.set(x, P + 1, z1, B("bookshelf"))
                self.set(x, P + 2, z1, B(cols[x % len(cols)] + "_concrete"))
        # beanbags
        rng = random.Random(3)
        for (x, z) in ((30, -48), (33, -47), (58, -50), (61, -46), (48, -32), (52, -33)):
            self.set(x, P, z, B(rng.choice(cols) + "_wool"))
        # reading tree with a platform (stairs up, railing)
        tx, tz = 45, -42
        for dx in (0, 1):
            for dz in (0, 1):
                self.fill(tx + dx, P, tz + dz, tx + dx, 77, tz + dz, B("oak_log"))
        plat = [(x, z) for x in range(tx - 3, tx + 5) for z in range(tz - 3, tz + 5)
                if not (tx <= x <= tx + 1 and tz <= z <= tz + 1)]
        for (x, z) in plat:
            self.set(x, P + 5, z, B("oak_planks"))
        for (x, z) in plat:
            if x in (tx - 3, tx + 4) or z in (tz - 3, tz + 4):
                self.set(x, P + 6, z, B("oak_fence"))
        # stairs: west side, rising east into the platform
        for t in range(6):
            x = tx - 9 + t
            for z in (tz, tz + 1):
                for y in range(P, P + t):
                    self.set(x, y, z, B("oak_planks"))
                self.set(x, P + t, z, stair("oak_stairs", "east"))
        for z in (tz, tz + 1):
            self.set(tx - 3, P + 6, z, AIR)
        leaf_blob(self.a, self.cx + tx + 0.5, 77.5, self.cz + tz + 0.5, 6.0, B("oak_leaves", persistent_bit=1),
                  self.rng, flat=0.35)
        self.set(tx - 3, P + 7, tz - 3, B("lantern"))
        self.set(tx + 4, P + 7, tz + 4, B("lantern"))
        # giant crayons
        for (x, z, c) in ((64, -58, "red"), (66, -58, "blue"), (64, -56, "yellow"), (24, -38, "lime")):
            self.fill(x, P, z, x, P + 4, z, B(c + "_concrete"))
            self.set(x, P + 5, z, B(c + "_terracotta"))
        for x in range(30, 66, 9):
            for z in range(-56, -24, 9):
                self.chandelier(x, CEIL - 1, z, 3, r=1)
        self.pois["kids"] = (self.cx + 45, P, self.cz - 42)

    def archives(self):
        rng = random.Random(8)
        cells = self.cells("NW")
        for x in range(-66, -23, 4):
            for z in range(-60, -22):
                if z in (-42, -41, -40) or z in (-23,):
                    continue
                if self.zone.get((x, z)) != "NW":
                    continue
                for y in range(P, P + 7):
                    self.set(x, y, z, B("bookshelf") if rng.random() > 0.1 else B("barrel", facing_direction=rng.choice([2, 3])))
        # map table and old desks in the cross aisle
        for (x, z) in ((-60, -41), (-48, -41), (-36, -41)):
            self.set(x, P, z, B("cartography_table"))
        for (x, z) in ((-54, -41), (-30, -41)):
            self.set(x, P, z, B("spruce_slab", half="top"))
            self.set(x, P + 1, z, B("candle", candles=3, lit=1))
        # cobwebs high in the corners and soul lanterns
        for (x, z) in cells:
            if rng.random() < 0.02 and self.get(x, CEIL - 1, z) == AIR:
                self.set(x, CEIL - 1, z, B("web"))
        for x in range(-64, -22, 8):
            for z in range(-58, -22, 8):
                if self.get(x, CEIL - 1, z) == AIR:
                    self.set(x, CEIL - 1, z, B("chain"))
                    self.set(x, CEIL - 2, z, B("chain"))
                    self.set(x, CEIL - 3, z, B("soul_lantern", hanging=1))
        self.pois["archives"] = (self.cx - 45, P, self.cz - 41)

    def cafe(self):
        # counter along the east wall
        xi = BX - 2
        for z in range(26, 58):
            self.set(xi - 2, P, z, B("dark_oak_planks"))
            self.set(xi - 2, P + 1, z, B("dark_oak_slab"))
            if z % 5 == 0:
                self.set(xi - 2, P + 1, z, B("brewing_stand"))
                self.be("BrewingStand", xi - 2, P + 1, z)
            elif z % 7 == 0:
                self.set(xi - 2, P + 1, z, B("cake"))
        for z in range(26, 58):
            self.set(xi, P + 3, z, B("dark_oak_slab", half="top"))
        # round cafe tables with chairs
        for (x, z) in ((30, 28), (40, 28), (50, 28), (30, 40), (40, 40), (50, 40), (30, 52), (40, 52), (50, 52)):
            self.set(x, P, z, B("dark_oak_fence"))
            self.set(x, P + 1, z, B("dark_oak_slab"))
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                self.set(x + dx, P + 1, z + dz, B("dark_oak_slab"))
            for dx, dz in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                self.chair(x + dx, z + dz, (-dx // 2, -dz // 2))
            self.set(x + 1, P + 1, z + 1, B("flower_pot"))
            self.a.add_be(flowerpot_be(self.cx + x + 1, P + 1, self.cz + z + 1, "red_tulip"))
        # plants and lights
        for (x, z) in ((23, 23), (23, 59), (60, 23)):
            self.set(x, P, z, B("flower_pot"))
            self.a.add_be(flowerpot_be(self.cx + x, P, self.cz + z, "azalea"))
        for x in range(30, 61, 10):
            for z in range(28, 61, 12):
                self.chandelier(x, CEIL - 1, z, 5, r=1)
        # menu board
        self.fill(xi, P + 4, 38, xi, P + 6, 44, B("black_concrete"))
        self.a.add_be(sign_be(self.cx + xi - 1, P + 5, self.cz + 41, "§l§e북카페 메뉴\n§r§f아메리카노\n§f책 한 잔 라떼", glow=True))
        self.set(xi - 1, P + 5, 41, B("dark_oak_wall_sign", facing_direction=4))
        self.pois["cafe"] = (self.cx + 40, P, self.cz + 40)

    def garden_room(self):
        rng = random.Random(12)
        cells = self.cells("SW")
        for (x, z) in cells:
            r = math.hypot(x + 45, z - 41)
            if abs(x + 45) <= 1 or abs(z - 41) <= 1:
                self.set(x, F1, z, B("grass_path"))
            elif rng.random() < 0.18:
                self.set(x, P, z, B(rng.choice(FLOWERS + ["short_grass", "short_grass", "fern"])))
        # fountain
        fx, fz = -45, 41
        for (x, z) in cells:
            d = math.hypot(x - fx, z - fz)
            if d < 3.6:
                self.set(x, F1, z, B("water"))
                self.set(x, F1 - 1, z, B("stone_bricks"))
                self.set(x, P, z, AIR)
            elif d < 4.6:
                self.set(x, F1, z, B("stone_bricks"))
                self.set(x, P, z, B("stone_brick_slab"))
        self.fill(fx, F1, fz, fx, P + 1, fz, B("chiseled_stone_bricks"))
        self.set(fx, P + 2, fz, B("sea_lantern"))
        for (dx, dz) in ((2, 1), (-1, -2), (1, -2)):
            self.a.set(self.cx + fx + dx, P, self.cz + fz + dz, B("waterlily"))
        # trees
        for (x, z, kind) in ((-60, 28, "cherry"), (-30, 28, "oak"), (-60, 55, "oak"), (-30, 55, "cherry"),
                             (-62, 36, "azalea"), (-28, 46, "azalea")):
            if kind == "cherry":
                from gen_common import cherry_tree
                cherry_tree(self.a, self.cx + x, P, self.cz + z, rng, h=6)
            elif kind == "oak":
                oak_tree(self.a, self.cx + x, P, self.cz + z, rng, h=7)
            else:
                self.set(x, P, z, B("flowering_azalea"))
        # benches
        for (x, z, f) in ((-45, 33, "south"), (-45, 49, "north"), (-53, 41, "east"), (-37, 41, "west")):
            for t in (-1, 0, 1):
                xx, zz = (x + t, z) if f in ("north", "south") else (x, z + t)
                self.set(xx, P, zz, stair("spruce_stairs", {"south": "north", "north": "south", "east": "west", "west": "east"}[f]))
        for (x, z) in ((-52, 33), (-38, 49), (-52, 49), (-38, 33)):
            self.fill(x, P, z, x, P + 2, z, B("dark_oak_fence"))
            self.set(x, P + 3, z, B("lantern"))
        self.pois["garden"] = (self.cx - 45, P, self.cz + 41)

    # ------------------------------------------------------------------ outside (seen through windows)
    def garden_outside(self):
        a = self.a
        rng = random.Random(21)
        n = value_noise(224, 224, 9, 5)
        x0, z0 = self.cx - 112, self.cz - 112
        for i in range(224):
            for k in range(224):
                x, z = i - 112, k - 112
                if abs(x) <= BX and abs(z) <= BZ:
                    continue
                a.set(x0 + i, F1 - 1, z0 + k, B("dirt"))
                d = max(abs(x) - BX, abs(z) - BZ)
                if 1 <= d <= 4:
                    b = B("stone_bricks") if d in (1, 4) else B("gravel")
                else:
                    b = B("grass_block")
                a.set(x0 + i, F1, z0 + k, b)
                if d > 5 and n[i, k] > 0.62 and rng.random() < 0.3:
                    a.set(x0 + i, P, z0 + k, B(rng.choice(FLOWERS + ["short_grass", "fern"])))
        # trees around the building and a tall hedge at the edge
        for _ in range(140):
            x, z = rng.randint(-104, 104), rng.randint(-104, 104)
            d = max(abs(x) - BX, abs(z) - BZ)
            if d < 9:
                continue
            kind = rng.random()
            if kind < 0.4:
                oak_tree(a, self.cx + x, P, self.cz + z, rng)
            elif kind < 0.65:
                birch_tree(a, self.cx + x, P, self.cz + z, rng)
            elif kind < 0.85:
                spruce_tree(a, self.cx + x, P, self.cz + z, rng, h=rng.randint(8, 11))
            else:
                cherry_tree(a, self.cx + x, P, self.cz + z, rng)
        for i in range(224):
            for k in range(224):
                x, z = i - 112, k - 112
                if max(abs(x), abs(z)) >= 107:
                    for y in range(P, P + 6):
                        a.set(x0 + i, y, z0 + k, B("oak_leaves", persistent_bit=1) if (x + z + y) % 7 else B("azalea_leaves", persistent_bit=1))
        # lamp posts along the path ring
        for t in range(-BX, BX + 1, 12):
            for z in (-BZ - 6, BZ + 6):
                self.fill(t, P, z, t, P + 2, z, B("dark_oak_fence"))
                self.set(t, P + 3, z, B("lantern"))
        for t in range(-BZ, BZ + 1, 12):
            for x in (-BX - 6, BX + 6):
                self.fill(x, P, t, x, P + 2, t, B("dark_oak_fence"))
                self.set(x, P + 3, t, B("lantern"))

    # ------------------------------------------------------------------ signs & light
    def labels(self):
        """Hanging name signs at the doorways of every room."""
        spots = [
            ((0, -22), "N", 3), ((0, 22), "S", 2), ((22, 0), "E", 4), ((-22, 0), "W", 5),
            ((19, -41), "NE", 4), ((-19, -41), "NW", 5), ((19, 41), "SE", 4), ((-19, 41), "SW", 5),
        ]
        for (x, z), zone, face in spots:
            y = P + 4 if zone in ("NE", "NW", "SE", "SW") else L2 - 1
            self.set(x, y, z, B("spruce_hanging_sign", hanging=1, attached_bit=0, facing_direction=face))
            txt = "§l%s" % ZONE_NAMES[zone]
            self.a.add_be(sign_be(self.cx + x, y, self.cz + z, txt, txt, glow=True, hanging=True, color=-1))
        # directory board in the entrance hall
        self.set(0, P, 56, B("dark_oak_planks"))
        self.set(0, P + 1, 56, B("dark_oak_standing_sign", ground_sign_direction=8))
        self.a.add_be(sign_be(self.cx, P + 1, self.cz + 56,
                              "§l§6대도서관 안내\n§r§f↑ 원형홀 · 서고\n§f← 마법 서재  열람실 →\n§72층 회랑은 계단으로", glow=True))

    def lighting(self):
        """Warm, readable light: an even grid of invisible light blocks on both levels (dimmer in the
        archives), topped up wherever a spot is still dark."""
        from lighting import fill_dark
        a = self.a
        walk = ("rot", "arch", "N", "S", "E", "W", "NE", "SE", "SW", "NW")
        for (x, z), zn in self.zone.items():
            if zn not in walk or x % 5 != 2 or z % 5 != 2:
                continue
            lb = B("light_block_9") if zn == "NW" else B("light_block_13")
            for y in (P + 2, P + 3):
                if self.get(x, y, z) == AIR and self.get(x, y - 1, z) == AIR:
                    self.set(x, y, z, lb)
                    break
            if (x, z) in self.l2:
                for y in (P2 + 2, P2 + 3):
                    if self.get(x, y, z) == AIR and self.get(x, y - 1, z) == AIR:
                        self.set(x, y, z, lb)
                        break
        box = (self.cx - BX, self.cz - BZ, self.cx + BX, self.cz + BZ)
        fill_dark(a, box, (P, P + 16), threshold=7, level=12, height=3, spacing=3,
                  skip=lambda x, z: self.zone.get((x - self.cx, z - self.cz)) in (None, "out", "ow", "iw", "pocket", "drum")
                  or self.zone.get((x - self.cx, z - self.cz)) == "NW")
        fill_dark(a, (self.cx - 70, self.cz - 62, self.cx - 20, self.cz - 20), (P, P + 16), threshold=5, level=10,
                  height=3, spacing=3, skip=lambda x, z: self.zone.get((x - self.cx, z - self.cz)) != "NW")


def build_library(cx, cz):
    lib = Library(cx, cz)
    lib.build()
    return lib
