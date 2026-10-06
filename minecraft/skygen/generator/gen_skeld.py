"""Map 5 - The Skeld ("더 스켈드"): the Among Us spaceship.

The floor plan comes from data/skeld_layout.txt (1 char = 1 block) which was traced from the reference
map: the 14 rooms, 7 hallways and the colour-coded doors sit exactly where they are on the map.
The ship is a closed hull (walls, ceilings, windows) floating inside a starfield box, so nobody can leave.
Vents (sneak on a grate) and the emergency button are handled by the behaviour pack script.
"""
import math
import os
import random
from collections import deque

import numpy as np
import amulet_nbt as an

from mcw import B, AIR, Area, simple_be, sign_be
from gen_common import stair, slab, disk, ring, leaf_blob, leaves_of, line_points

HERE = os.path.dirname(os.path.abspath(__file__))
FY = 64           # floor block level
P = 65            # feet level
PAD = 6           # empty blueprint border (hull + exterior details)
HALL_H = 5        # clear height of hallways
DOOR_H = 4        # clear height of doorways

# reference image -> blueprint transform (prop positions are given in reference-image pixels)
PXS, PX0, PY0 = 5.5, 60, 95

ROOMS = {
    # key: name, clear height, floor (main, seam), wall accent stripe, windows
    "C": dict(name="식당", h=9, floor=("light_blue_terracotta", "polished_andesite"), accent="light_blue_concrete", win=True),
    "W": dict(name="무기고", h=7, floor=("gray_concrete", "light_gray_concrete"), accent="red_concrete", win=True),
    "O": dict(name="산소 공급실", h=7, floor=("light_gray_concrete", "white_concrete"), accent="lime_concrete", win=True),
    "N": dict(name="항해실", h=7, floor=("cyan_terracotta", "light_blue_concrete"), accent="light_blue_concrete", win=True),
    "S": dict(name="보호막 제어실", h=7, floor=("light_gray_concrete", "purple_terracotta"), accent="purple_concrete", win=True),
    "M": dict(name="통신실", h=7, floor=("gray_concrete", "cyan_terracotta"), accent="cyan_concrete", win=True),
    "T": dict(name="창고", h=8, floor=("polished_andesite", "andesite"), accent="yellow_concrete", win=True),
    "A": dict(name="관리실", h=7, floor=("light_blue_terracotta", "white_terracotta"), accent="green_concrete", win=False),
    "E": dict(name="전기실", h=7, floor=("gray_concrete", "black_concrete"), accent="yellow_concrete", win=False),
    "L": dict(name="하부 엔진", h=9, floor=("deepslate_tiles", "polished_deepslate"), accent="orange_concrete", win=True),
    "U": dict(name="상부 엔진", h=9, floor=("deepslate_tiles", "polished_deepslate"), accent="orange_concrete", win=True),
    "Y": dict(name="보안실", h=6, floor=("cyan_terracotta", "gray_concrete"), accent="red_concrete", win=False),
    "R": dict(name="원자로", h=9, floor=("polished_deepslate", "deepslate_tiles"), accent="light_blue_concrete", win=True),
    "D": dict(name="의무실", h=7, floor=("white_concrete", "light_blue_concrete"), accent="lime_concrete", win=False),
}
DOOR_COLOUR = {"g": "lime", "r": "red", "b": "light_blue", "o": "orange", "p": "purple", "k": "magenta", "y": "yellow"}

# vents: (group, region, reference x, reference y) - sneaking on a grate moves you to the next vent of its group
VENTS = [
    ("upper", "U", 244, 183), ("upper", "R", 107, 319),
    ("lower", "R", 130, 396), ("lower", "L", 244, 539),
    ("medbay", "D", 356, 339), ("medbay", "Y", 305, 396), ("medbay", "E", 374, 433),
    ("cafe", "C", 673, 260), ("cafe", "A", 644, 461), ("cafe", "3", 787, 373),
    ("nav1", "W", 776, 186), ("nav1", "N", 938, 308),
    ("nav2", "N", 938, 382), ("nav2", "S", 785, 556),
]
VENT_NAME = {"U": "상부 엔진", "R": "원자로", "L": "하부 엔진", "D": "의무실", "Y": "보안실", "E": "전기실",
             "C": "식당", "A": "관리실", "3": "항해실 복도", "W": "무기고", "N": "항해실", "S": "보호막 제어실"}

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
FACE = {(0, -1): 2, (0, 1): 3, (-1, 0): 4, (1, 0): 5}         # direction a wall-attached thing faces
ASC = {(1, 0): "east", (-1, 0): "west", (0, 1): "south", (0, -1): "north"}


def load_layout():
    rows = [l.rstrip("\n") for l in open(os.path.join(HERE, "data", "skeld_layout.txt"), encoding="utf8")
            if not l.startswith(";")]
    nz, nx = len(rows), max(len(r) for r in rows)
    g = np.full((nx + 2 * PAD, nz + 2 * PAD), " ", dtype="<U1")
    for z, r in enumerate(rows):
        for x, c in enumerate(r):
            if c != "#":
                g[x + PAD, z + PAD] = c
    return g, nx, nz


class Skeld:
    def __init__(self, cx, cz):
        self.name = "skeld"
        self.cx, self.cz = cx, cz
        self.H0 = FY
        self.R = 100
        self.a = Area("skeld", cx - 128, cz - 128, 256, 256, y0=32, sy=112, biome=1)
        self.g, nx, nz = load_layout()
        self.GX, self.GZ = self.g.shape
        # world coordinate of blueprint cell (0, 0)
        self.X0 = cx - nx // 2
        self.Z0 = cz - nz // 2
        self.rng = random.Random(5505)
        self.spawns = []
        self.pois = {}
        self.vents = []
        self.button = None
        self.keep = set()       # cells props must stay off (entrances, vents)
        self.occ = set()        # cells taken by floor props

    # ------------------------------------------------------------------ coordinates
    def wx(self, i):
        return self.X0 - PAD + i

    def wz(self, k):
        return self.Z0 - PAD + k

    def gi(self, x, z):
        return x - self.X0 + PAD, z - self.Z0 + PAD

    def ref(self, xp, yp):
        """Reference-image pixel -> world (x, z)."""
        return self.X0 + int((xp - PX0) / PXS), self.Z0 + int((yp - PY0) / PXS)

    def ch(self, x, z):
        i, k = self.gi(x, z)
        if 0 <= i < self.GX and 0 <= k < self.GZ:
            return self.g[i, k]
        return " "

    def inside(self, x, z):
        i, k = self.gi(x, z)
        return 0 <= i < self.GX and 0 <= k < self.GZ and bool(self.foot[i, k])

    def room_cells(self, c):
        return self.cells[c]

    def foot_cells(self):
        return [(int(self.wx(i)), int(self.wz(k))) for i, k in np.argwhere(self.foot)]

    # ------------------------------------------------------------------ build
    def build(self):
        self.analyse()
        self.space()
        self.shell()
        self.doors()
        self.windows()
        self.lights()
        self.place_vents()
        self.cafeteria()
        self.weapons()
        self.o2()
        self.navigation()
        self.shields()
        self.comms()
        self.storage()
        self.admin()
        self.electrical()
        self.engine("U")
        self.engine("L")
        self.security()
        self.reactor()
        self.medbay()
        self.hallways()
        self.crewmates()
        self.exterior()
        self.roof_details()
        self.labels()
        self.fill_light()
        self.a.fix_walls()
        self.a.prune_be()
        return self.a

    # ------------------------------------------------------------------ analysis
    def analyse(self):
        g = self.g
        self.interior = (g != " ")
        GX, GZ = self.GX, self.GZ
        d = np.full((GX, GZ), 99, np.int32)
        dq = deque()
        for i, k in np.argwhere(self.interior):
            d[i, k] = 0
            dq.append((i, k))
        while dq:
            i, k = dq.popleft()
            if d[i, k] >= 4:
                continue
            for di, dk in N8:
                ii, kk = i + di, k + dk
                if 0 <= ii < GX and 0 <= kk < GZ and d[ii, kk] > d[i, k] + 1:
                    d[ii, kk] = d[i, k] + 1
                    dq.append((ii, kk))
        self.d = d
        hull = (d == 1) | (d == 2)
        # enclosed gaps between rooms become solid hull too
        openm = ~hull & ~self.interior
        reach = np.zeros_like(openm)
        dq = deque([(i, k) for i in range(GX) for k in (0, GZ - 1)] + [(i, k) for k in range(GZ) for i in (0, GX - 1)])
        while dq:
            i, k = dq.popleft()
            if not (0 <= i < GX and 0 <= k < GZ) or reach[i, k] or not openm[i, k]:
                continue
            reach[i, k] = True
            dq.extend([(i + 1, k), (i - 1, k), (i, k + 1), (i, k - 1)])
        self.pocket = openm & ~reach
        self.hull = hull | self.pocket
        self.foot = self.hull | self.interior
        self.space_open = reach
        # clear heights
        ceil = np.zeros((GX, GZ), np.int32)
        for (i, k) in np.argwhere(self.interior):
            c = g[i, k]
            if c.isupper():
                ceil[i, k] = P + ROOMS[c]["h"]
            elif c.isdigit():
                ceil[i, k] = P + HALL_H
            else:
                ceil[i, k] = P + DOOR_H
        self.ceil = ceil
        roof = np.zeros((GX, GZ), np.int32)
        for (i, k) in np.argwhere(self.hull):
            best = 0
            for di in range(-2, 3):
                for dk in range(-2, 3):
                    ii, kk = i + di, k + dk
                    if 0 <= ii < GX and 0 <= kk < GZ:
                        best = max(best, ceil[ii, kk])
            roof[i, k] = (best or P + 6) + 1
        for (i, k) in np.argwhere(self.interior):
            roof[i, k] = ceil[i, k] + 1
        self.roof = roof
        # rooms
        self.cells = {}
        for (i, k) in np.argwhere(self.interior):
            self.cells.setdefault(g[i, k], []).append((self.wx(i), self.wz(k)))
        self.center = {c: (int(round(np.mean([p[0] for p in v]))), int(round(np.mean([p[1] for p in v]))))
                       for c, v in self.cells.items()}
        # entrances: cells within 2 of a boundary between different interior kinds stay clear
        for (i, k) in np.argwhere(self.interior):
            c = g[i, k]
            for di, dk in N4:
                c2 = g[i + di, k + dk]
                if c2 != " " and c2 != c:
                    for a in range(-2, 3):
                        for b in range(-2, 3):
                            self.keep.add((self.wx(i + a), self.wz(k + b)))

    def owner(self, i, k):
        """Interior char a hull cell faces (4-neighbours first, rooms preferred)."""
        best = None
        for di, dk in N4 + N8[4:]:
            ii, kk = i + di, k + dk
            if 0 <= ii < self.GX and 0 <= kk < self.GZ:
                c = self.g[ii, kk]
                if c != " ":
                    if c.isupper():
                        return c, (di, dk)
                    if best is None:
                        best = (c, (di, dk))
        return best if best else (None, None)

    # ------------------------------------------------------------------ space backdrop
    def space(self):
        a = self.a
        rng = random.Random(77)
        x1, x2 = self.cx - 126, self.cx + 125
        z1, z2 = self.cz - 126, self.cz + 125
        y1, y2 = 36, 140
        black = B("black_concrete")
        a.fill(x1, y1, z1, x2, y2, z2, black)
        a.fill(x1 + 1, y1 + 1, z1 + 1, x2 - 1, y2 - 1, z2 - 1, AIR)
        stars = [B("sea_lantern"), B("glowstone"), B("pearlescent_froglight", axis="y"), B("ochre_froglight", axis="y"),
                 B("verdant_froglight", axis="y"), B("sea_lantern"), B("end_rod", facing_direction=1)]
        n = 0
        for _ in range(9000):
            face = rng.randrange(6)
            if face == 0:
                x, y, z = rng.randint(x1, x2), y1, rng.randint(z1, z2)
            elif face == 1:
                x, y, z = rng.randint(x1, x2), y2, rng.randint(z1, z2)
            elif face == 2:
                x, y, z = x1, rng.randint(y1, y2), rng.randint(z1, z2)
            elif face == 3:
                x, y, z = x2, rng.randint(y1, y2), rng.randint(z1, z2)
            elif face == 4:
                x, y, z = rng.randint(x1, x2), rng.randint(y1, y2), z1
            else:
                x, y, z = rng.randint(x1, x2), rng.randint(y1, y2), z2
            if rng.random() < 0.62:
                a.set(x, y, z, stars[rng.randrange(len(stars) - 1)])
                n += 1
        # a few stars floating in front of the walls, so the field has depth
        for _ in range(500):
            x, y, z = rng.randint(x1 + 2, x2 - 2), rng.randint(y1 + 2, y2 - 2), rng.randint(z1 + 2, z2 - 2)
            if abs(x - self.cx) < 100 and abs(z - self.cz) < 64 and 52 < y < 86:
                continue
            a.set(x, y, z, B("end_rod", facing_direction=rng.choice([0, 1])))
        # ringed gas giant beyond the navigation nose
        self.planet(self.cx + 108, 80, self.cz - 30, 11,
                    ["orange_terracotta", "yellow_terracotta", "white_terracotta", "brown_terracotta", "orange_terracotta",
                     "yellow_terracotta", "red_terracotta", "white_terracotta"], ring=(15, 19, "white_stained_glass"))
        # blue planet ahead of the cafeteria windows
        self.blue_planet(self.cx + 18, 84, self.cz - 104, 10)
        # small purple moon behind the engines
        self.planet(self.cx - 112, 100, self.cz + 70, 6, ["purple_terracotta", "magenta_terracotta", "purple_terracotta"])
        # asteroids around the weapons room (they shoot at those!)
        for _ in range(26):
            ang = rng.uniform(-1.6, 0.4)
            dist = rng.uniform(80, 116)
            ax, az = self.cx + math.cos(ang) * dist, self.cz + math.sin(ang) * dist - 10
            ay = rng.uniform(56, 112)
            if abs(ax - self.cx) > 118 or abs(az - self.cz) > 118:
                continue
            if abs(ax - self.cx) < 98 and abs(az - self.cz) < 62 and ay < 86:
                continue
            r = rng.uniform(1.2, 3.6)
            mats = [B("stone"), B("tuff"), B("cobbled_deepslate"), B("andesite"), B("gravel")]
            for x in range(int(ax - r - 1), int(ax + r + 2)):
                for y in range(int(ay - r - 1), int(ay + r + 2)):
                    for z in range(int(az - r - 1), int(az + r + 2)):
                        if (x - ax) ** 2 + ((y - ay) * 1.2) ** 2 + (z - az) ** 2 <= r * r - rng.random() * 1.5:
                            a.set(x, y, z, rng.choice(mats))

    def planet(self, px, py, pz, r, bands, ring=None):
        a = self.a
        for x in range(int(px - r - 1), int(px + r + 2)):
            for y in range(int(py - r - 1), int(py + r + 2)):
                for z in range(int(pz - r - 1), int(pz + r + 2)):
                    d = math.sqrt((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2)
                    if d <= r:
                        wob = math.sin((x - px) * 0.45 + (z - pz) * 0.3) * 0.8
                        idx = int((y - py + r + wob) / (2 * r + 1) * len(bands))
                        a.set(x, y, z, B(bands[max(0, min(len(bands) - 1, idx))]))
        if ring:
            r1, r2, mat = ring
            for x in range(int(px - r2 - 1), int(px + r2 + 2)):
                for z in range(int(pz - r2 - 1), int(pz + r2 + 2)):
                    d = math.hypot(x - px, z - pz)
                    if r1 <= d <= r2:
                        y = int(round(py + (x - px) * 0.28))
                        if a.get(x, y, z) == AIR and abs(x - self.cx) < 124 and abs(z - self.cz) < 124:
                            a.set(x, y, z, B(mat if d < r2 - 1 else "light_gray_stained_glass"))

    def blue_planet(self, px, py, pz, r):
        a = self.a
        from gen_common import value_noise
        n = value_noise(64, 64, 6, 31)
        for x in range(int(px - r - 1), int(px + r + 2)):
            for y in range(int(py - r - 1), int(py + r + 2)):
                for z in range(int(pz - r - 1), int(pz + r + 2)):
                    d = math.sqrt((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2)
                    if d <= r:
                        v = n[(x * 3 + y) % 64, (z * 3 - y) % 64]
                        b = "blue_concrete" if v < 0.55 else ("lime_concrete" if v < 0.7 else "green_concrete")
                        if v > 0.8 or abs(y - py) > r - 2:
                            b = "white_concrete"
                        a.set(x, y, z, B(b))

    # ------------------------------------------------------------------ shell
    def floor_block(self, c, x, z):
        if c.isupper():
            main, seam = ROOMS[c]["floor"]
            if c == "C":
                return B(seam) if (x % 4 == 0 or z % 4 == 0) else B(main)
            if c in "LUR":
                return B(seam) if (x + z) % 2 == 0 else B(main)
            if c == "D":
                return B(seam) if ((x // 2) + (z // 2)) % 2 == 0 else B(main)
            if c == "T":
                return B(seam) if (x * 7 + z * 3) % 5 == 0 else B(main)
            if c == "E":
                return B(seam) if (x % 3 == 0 and z % 3 == 0) else B(main)
            return B(seam) if (x % 5 == 0 or z % 5 == 0) else B(main)
        if c.isdigit():
            if x % 4 == 0 or z % 4 == 0:
                return B("polished_andesite")
            return B("smooth_stone")
        return B(DOOR_COLOUR[c] + "_concrete")

    def shell(self):
        a = self.a
        g = self.g
        ext = B("light_gray_concrete")
        ext2 = B("smooth_stone")
        under = B("gray_concrete")
        roofb = B("smooth_stone")
        for (i, k) in np.argwhere(self.foot):
            x, z = self.wx(i), self.wz(k)
            a.set(x, FY - 2, z, under)
            if self.interior[i, k]:
                c = g[i, k]
                top = self.ceil[i, k]
                a.set(x, FY - 1, z, B("gray_concrete"))
                a.set(x, FY, z, self.floor_block(c, x, z))
                a.fill(x, P, z, x, top - 1, z, AIR)
                if c.isupper():
                    cb = B("light_gray_concrete")
                elif c.isdigit():
                    cb = B("smooth_stone")
                else:
                    cb = B("yellow_concrete") if (x + z) % 2 == 0 else B("black_concrete")
                a.set(x, top, z, cb)
                rt = top + 1
                for di, dk in N4:
                    if self.hull[i + di, k + dk]:
                        rt = max(rt, self.roof[i + di, k + dk])
                a.fill(x, top + 1, z, x, rt - 1, z, ext)
                a.set(x, rt, z, roofb)
                continue
            top = self.roof[i, k]
            a.fill(x, FY - 1, z, x, top - 1, z, ext)
            a.set(x, top, z, roofb)
            if self.d[i, k] == 1:
                c, v = self.owner(i, k)
                if c is None:
                    continue
                ci, ck = i + v[0], k + v[1]
                ctop = self.ceil[ci, ck]
                along_x = v[1] != 0 and v[0] == 0
                coord = x if along_x else z
                if c.isupper():
                    acc = B(ROOMS[c]["accent"])
                    for y in range(P, ctop):
                        if y == P:
                            b = B("gray_concrete")
                        elif y == ctop - 1:
                            b = B("smooth_stone")
                        elif y == P + 3:
                            b = acc
                        elif coord % 5 == 0:
                            b = B("white_concrete")
                        else:
                            b = B("light_gray_concrete")
                        a.set(x, y, z, b)
                else:
                    for y in range(P, ctop):
                        if y == P:
                            b = B("gray_concrete")
                        elif y == ctop - 1:
                            b = B("smooth_stone")
                        elif coord % 6 == 0:
                            b = B("white_concrete")
                        else:
                            b = B("light_gray_concrete")
                        a.set(x, y, z, b)
            elif self.space_open[min(self.GX - 1, i + 1), k] or self.space_open[max(0, i - 1), k] or \
                    self.space_open[i, min(self.GZ - 1, k + 1)] or self.space_open[i, max(0, k - 1)]:
                # outer hull plating: panel seams and a dark band
                for y in range(FY - 1, top):
                    if y == FY - 1 or y == top - 1:
                        b = ext2
                    elif y == FY + 2:
                        b = B("gray_concrete")
                    elif (x + z) % 7 == 0:
                        b = ext2
                    else:
                        b = ext
                    a.set(x, y, z, b)

    # ------------------------------------------------------------------ doors
    def doors(self):
        """Iron jambs and a hazard-striped lintel around every colour-coded doorway."""
        a = self.a
        g = self.g
        for (i, k) in np.argwhere(np.char.islower(g)):
            x, z = self.wx(i), self.wz(k)
            for di, dk in N4:
                ii, kk = i + di, k + dk
                if self.hull[ii, kk]:
                    for y in range(P, P + DOOR_H):
                        a.set(self.wx(ii), y, self.wz(kk), B("iron_block"))
                    a.set(self.wx(ii), P + DOOR_H, self.wz(kk), B(DOOR_COLOUR[g[i, k]] + "_concrete"))

    # ------------------------------------------------------------------ windows
    def windows(self):
        a = self.a
        g = self.g
        glass = B("glass")
        for (i, k) in np.argwhere((self.d == 1) & ~self.pocket):
            for di, dk in N4:
                c = g[i + di, k + dk]
                if not c.isupper() or not ROOMS[c]["win"]:
                    continue
                vi, vk = -di, -dk          # outward
                if not self.hull[i + vi, k + vk]:
                    continue
                ok = True
                for s in range(2, 10):
                    ii, kk = i + vi * s, k + vk * s
                    if not (0 <= ii < self.GX and 0 <= kk < self.GZ):
                        break
                    if not self.space_open[ii, kk]:
                        ok = False
                        break
                if not ok:
                    continue
                x, z = self.wx(i), self.wz(k)
                along = x if vk != 0 else z
                if along % 4 == 0:
                    break           # mullion
                top = self.ceil[i + di, k + dk]
                yt = top - 1 if c == "N" else top - 2
                for y in range(P + 1, yt):
                    a.set(x, y, z, glass)
                    a.set(x + vi, y, z + vk, glass)
                break

    # ------------------------------------------------------------------ lights
    def lights(self):
        a = self.a
        g = self.g
        for (i, k) in np.argwhere(self.interior):
            c = g[i, k]
            x, z = self.wx(i), self.wz(k)
            if not all(self.interior[i + di, k + dk] for di, dk in N4):
                continue
            top = self.ceil[i, k]
            if c.isupper():
                sp = 7 if c == "E" else 5
                if x % sp == 2 and z % sp == 2:
                    a.set(x, top, z, B("ochre_froglight", axis="y") if c in "ELU" else B("sea_lantern"))
            elif c.isdigit():
                if x % 4 == 1 and z % 4 == 1:
                    a.set(x, top, z, B("sea_lantern"))

    def fill_light(self):
        """Among Us rooms are brightly lit: an even grid of invisible light blocks at head height
        (dimmer in electrical), then a top-up pass for any spot that is still dark."""
        from lighting import fill_dark
        a = self.a
        g = self.g
        for (i, k) in np.argwhere(self.interior):
            x, z = self.wx(i), self.wz(k)
            c = g[i, k]
            if c == "E":
                if x % 5 == 1 and z % 5 == 1:
                    a.put(x, P + 2, z, B("light_block_11"))
            elif x % 4 == 2 and z % 4 == 2:
                if a.get(x, P + 2, z) == AIR:
                    a.set(x, P + 2, z, B("light_block_15"))
                elif a.get(x, P + 3, z) == AIR:
                    a.set(x, P + 3, z, B("light_block_15"))
        x1, z1 = self.wx(0), self.wz(0)
        x2, z2 = self.wx(self.GX - 1), self.wz(self.GZ - 1)
        elec = set(self.cells["E"])
        fill_dark(a, (x1, z1, x2, z2), (P, P + 10), threshold=9, level=15, height=2, spacing=3,
                  skip=lambda x, z: (x, z) in elec or not self.inside(x, z))
        ex = [p[0] for p in elec]
        ez = [p[1] for p in elec]
        fill_dark(a, (min(ex), min(ez), max(ex), max(ez)), (P, P + 10), threshold=5, level=11, height=2, spacing=3,
                  skip=lambda x, z: (x, z) not in elec)

    # ------------------------------------------------------------------ helpers for props
    def free(self, x, z, c=None, keep_ok=False):
        ch = self.ch(x, z)
        if ch == " " or (c is not None and ch != c):
            return False
        if (x, z) in self.occ or (not keep_ok and (x, z) in self.keep):
            return False
        return True

    def take(self, cells):
        for p in cells:
            self.occ.add(p)

    def wall_spot(self, c, x, z, avoid=()):
        """Nearest inner wall cell of room c to (x, z). Returns (wall_x, wall_z, (dx, dz) into the room)."""
        best = None
        for (rx, rz) in self.cells[c]:
            for dx, dz in N4:
                wx, wz = rx - dx, rz - dz
                i, k = self.gi(wx, wz)
                if not self.hull[i, k] or self.d[i, k] != 1 or (wx, wz) in avoid:
                    continue
                dd = (wx - x) ** 2 + (wz - z) ** 2
                if best is None or dd < best[0]:
                    best = (dd, wx, wz, (dx, dz))
        return best[1:]

    def screen(self, wx, wz, v, y, colour="light_blue", w=2, h=2):
        """Glowing wall screen: stained glass in the wall with a sea lantern behind it."""
        a = self.a
        dx, dz = v
        ax, az = (abs(dz), abs(dx))     # along the wall
        for s in range(w):
            x, z = wx + ax * s, wz + az * s
            i, k = self.gi(x, z)
            if not self.hull[i, k] or self.d[i, k] != 1:
                continue
            bi, bk = i - dx, k - dz
            backlit = self.hull[bi, bk] and self.d[bi, bk] >= 2
            for yy in range(y, y + h):
                a.set(x, yy, z, B(colour + "_stained_glass"))
                if backlit:
                    a.set(x - dx, yy, z - dz, B("sea_lantern"))
                else:
                    a.set(x, yy, z, B(colour + "_concrete") if colour != "black" else B("black_concrete"))
            a.set(x, y - 1, z, B("black_concrete"))
            a.set(x, y + h, z, B("black_concrete"))

    def panel(self, c, xp, yp, kind, y=None):
        """Task panel on the wall nearest to a reference-image position."""
        x, z = self.ref(xp, yp)
        wx, wz, v = self.wall_spot(c, x, z)
        a = self.a
        dx, dz = v
        ax, az = abs(dz), abs(dx)
        y = y or P + 1
        if kind == "screen":
            self.screen(wx, wz, v, y, "light_blue")
        elif kind == "green":
            self.screen(wx, wz, v, y, "lime")
        elif kind == "wires":
            cols = ["red", "blue", "yellow", "magenta"]
            for s in range(2):
                for t in range(2):
                    a.set(wx + ax * s, y + t, wz + az * s, B(cols[s * 2 + t] + "_concrete"))
            for s in (-1, 2):
                for t in range(2):
                    a.set(wx + ax * s, y + t, wz + az * s, B("black_concrete"))
        elif kind == "switches":
            for s in range(3):
                a.set(wx + ax * s, y, wz + az * s, B("iron_block"))
                a.set(wx + ax * s, y + 1, wz + az * s, B("black_concrete"))
                fx, fz = wx + ax * s + dx, wz + az * s + dz
                if self.ch(fx, fz) != " ":
                    a.set(fx, y + 1, fz, B("lever", lever_direction={2: "north", 3: "south", 4: "west", 5: "east"}[FACE[v]],
                                           open_bit=s % 2))
        elif kind == "chute":
            for s in range(2):
                a.set(wx + ax * s, y, wz + az * s, B("iron_block"))
                a.set(wx + ax * s, y + 1, wz + az * s, B("iron_bars"))
                i, k = self.gi(wx + ax * s - dx, wz + az * s - dz)
                if self.hull[i, k] and self.d[i, k] >= 2:
                    a.set(wx + ax * s - dx, y + 1, wz + az * s - dz, B("black_concrete"))
                a.set(wx + ax * s, y + 2, wz + az * s, B("yellow_concrete"))
        elif kind == "hand":
            self.screen(wx, wz, v, y, "lime", w=2, h=2)
            a.set(wx, y + 2, wz, B("lime_concrete"))
        elif kind == "keypad":
            self.screen(wx, wz, v, y + 1, "black", w=1, h=1)
            a.set(wx, y, wz, B("polished_andesite"))
            fx, fz = wx + dx, wz + dz
            if self.ch(fx, fz) != " ":
                a.set(fx, y, fz, B("stone_button", facing_direction=FACE[v]))
        elif kind == "orange":
            self.screen(wx, wz, v, y, "orange")

    def chair(self, x, z, face):
        """Stair seat; face = direction the sitter looks."""
        back = {(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[face]
        self.a.set(x, P, z, stair("polished_andesite_stairs", back))
        self.take([(x, z)])

    def round_table(self, cx, cz, r=2.5, top="smooth_stone_slab", benches=True, centre=None, c="C"):
        a = self.a
        cells = [(x, z) for x in range(int(cx - r - 1), int(cx + r + 2)) for z in range(int(cz - r - 1), int(cz + r + 2))
                 if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + 0.3]
        if not all(self.free(x, z, c) for x, z in cells):
            print("  [skeld] table skipped at", cx, cz)
            return False
        for x, z in cells:
            a.set(x, P + 1, z, B(top, half="top"))
        a.set(cx, P, cz, B("iron_block"))
        if centre is not None:
            a.set(cx, P + 1, cz, centre)
        self.take(cells)
        if benches:
            for ang in range(0, 360, 30):
                rb = r + 1.6
                bx, bz = int(round(cx + math.cos(math.radians(ang)) * rb)), int(round(cz + math.sin(math.radians(ang)) * rb))
                if not self.free(bx, bz, c) or (bx, bz) in self.occ:
                    continue
                dx, dz = cx - bx, cz - bz
                face = (int(math.copysign(1, dx)), 0) if abs(dx) >= abs(dz) else (0, int(math.copysign(1, dz)))
                self.chair(bx, bz, face)
        return True

    def box(self, x1, y1, z1, x2, y2, z2, b, c=None, mark=True):
        cells = [(x, z) for x in range(min(x1, x2), max(x1, x2) + 1) for z in range(min(z1, z2), max(z1, z2) + 1)]
        self.a.fill(x1, y1, z1, x2, y2, z2, b)
        if mark:
            self.take(cells)

    def region_ok(self, x1, z1, x2, z2, c, keep_ok=False):
        return all(self.free(x, z, c, keep_ok) for x in range(min(x1, x2), max(x1, x2) + 1)
                   for z in range(min(z1, z2), max(z1, z2) + 1))

    # ------------------------------------------------------------------ vents
    def place_vents(self):
        a = self.a
        grate = B("iron_trapdoor", direction=0, open_bit=0, upside_down_bit=1)
        for group, c, xp, yp in VENTS:
            x0, z0 = self.ref(xp, yp)
            best = None
            for r in range(0, 6):
                for dx in range(-r, r + 1):
                    for dz in range(-r, r + 1):
                        if max(abs(dx), abs(dz)) != r:
                            continue
                        x, z = x0 + dx, z0 + dz
                        cells = [(x, z), (x + 1, z), (x, z + 1), (x + 1, z + 1)]
                        ring_ok = all(self.ch(px, pz) == c for px in range(x - 1, x + 3) for pz in range(z - 1, z + 3))
                        if all(self.ch(px, pz) == c and (px, pz) not in self.keep for px, pz in cells) and ring_ok:
                            best = (x, z)
                            break
                    if best:
                        break
                if best:
                    break
            if best is None:
                raise RuntimeError("no spot for vent %s %s" % (group, c))
            x, z = best
            for px, pz in ((x, z), (x + 1, z), (x, z + 1), (x + 1, z + 1)):
                a.set(px, FY, pz, grate)
                a.set(px, FY - 1, pz, B("black_concrete"))
            for px in range(x - 1, x + 3):
                for pz in range(z - 1, z + 3):
                    self.keep.add((px, pz))
            self.vents.append(dict(group=group, name=VENT_NAME[c], x=int(x), y=P, z=int(z)))

    # ------------------------------------------------------------------ rooms
    def cafeteria(self):
        a = self.a
        tx, tz = self.ref(555, 243)
        # emergency meeting table: red button in the middle
        self.round_table(tx, tz, r=3.2, top="smooth_quartz_slab", centre=B("red_concrete"))
        a.set(tx, P + 2, tz, B("crimson_button", facing_direction=1))
        self.button = (tx, P + 2, tz)
        self.face = (tx, tz)
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a.set(tx + dx, P + 1, tz + dz, B("yellow_concrete") if (dx + dz) % 2 else B("black_concrete"))
        self.pois["emergency_button"] = (tx, P + 2, tz)
        # four dining tables around it
        for ox, oz in ((-13, -11), (12, -11), (-13, 10), (12, 10)):
            self.round_table(tx + ox, tz + oz, r=2.5)
        # spawn points around the emergency table
        for (ox, oz) in ((0, 7), (-7, 0), (7, 0)):
            x, z = tx + ox, tz + oz
            assert self.ch(x, z) == "C", (x, z)
            self.spawns.append((x, P, z))
        # wall tasks
        self.panel("C", 468, 135, "wires")
        self.panel("C", 652, 125, "screen")
        self.panel("C", 682, 145, "chute")
        # vending machines / counters along the north wall
        cx, cz = self.center["C"]
        zn = min(z for x, z in self.cells["C"] if x == cx)
        for x in range(cx - 6, cx + 7, 3):
            zz = min(z for xx, z in self.cells["C"] if xx == x)
            if self.free(x, zz, "C") and self.free(x + 1, zz, "C"):
                self.box(x, P, zz, x + 1, P + 1, zz, B("white_concrete"))
                a.set(x, P + 1, zz, B("light_blue_stained_glass"))
                a.set(x + 1, P + 1, zz, B("red_stained_glass") if x % 2 else B("lime_stained_glass"))
                a.set(x, P + 2, zz, B("smooth_quartz_slab"))
                a.set(x + 1, P + 2, zz, B("smooth_quartz_slab"))

    def weapons(self):
        a = self.a
        c = "W"
        cx, cz = self.center[c]
        # gunner seat on a pedestal facing the east window
        xe = max(x for x, z in self.cells[c] if z == cz)
        sx = xe - 4
        if self.region_ok(sx - 1, cz - 1, sx + 1, cz + 1, c):
            self.box(sx - 1, P, cz - 1, sx + 1, P, cz + 1, B("polished_andesite"))
            a.set(sx, P + 1, cz, stair("polished_andesite_stairs", "west"))
            a.set(sx + 1, P + 1, cz, B("iron_bars"))
            a.set(sx + 1, P + 2, cz, B("black_stained_glass"))
        # targeting screens on the east wall
        for zz in (cz - 3, cz + 2):
            wx, wz, v = self.wall_spot(c, xe + 1, zz)
            self.screen(wx, wz, v, P + 1, "lime", w=2, h=2)
        self.panel(c, 782, 166, "screen")
        self.panel(c, 826, 200, "screen")
        # ammo crates
        for (x, z) in ((cx - 5, cz + 5), (cx - 4, cz + 5), (cx - 5, cz + 4)):
            if self.free(x, z, c):
                self.box(x, P, z, x, P, z, B("barrel", facing_direction=1))
        self.pois["weapons"] = (cx, P, cz)

    def o2(self):
        a = self.a
        c = "O"
        cx, cz = self.center[c]
        # planter with an oxygen tree
        if self.region_ok(cx - 1, cz - 1, cx + 1, cz + 1, c):
            self.box(cx - 1, P, cz - 1, cx + 1, P, cz + 1, B("polished_andesite"))
            a.set(cx, P, cz, B("moss_block"))
            for y in range(P + 1, P + 4):
                a.set(cx, y, cz, B("oak_log"))
            leaf_blob(a, cx, P + 4.5, cz, 2.2, B("azalea_leaves_flowered", persistent_bit=1), self.rng, flat=0.7,
                      extra=B("azalea_leaves", persistent_bit=1), extra_chance=0.5)
        # oxygen tanks along the walls
        for (xp, yp) in ((735, 345), (690, 345)):
            x, z = self.ref(xp, yp)
            for dx in (0, 1):
                if self.free(x + dx, z, c):
                    self.box(x + dx, P, z, x + dx, P + 2, z, B("light_blue_concrete"))
                    a.set(x + dx, P + 1, z, B("white_concrete"))
                    a.set(x + dx, P + 3, z, B("iron_trapdoor", direction=0, upside_down_bit=0))
        self.panel(c, 690, 305, "chute")
        self.panel(c, 718, 296, "screen")
        self.panel(c, 745, 300, "keypad")
        self.pois["o2"] = (cx, P, cz)

    def navigation(self):
        a = self.a
        c = "N"
        cx, cz = self.center[c]
        xe = max(x for x, z in self.cells[c] if z == cz)
        # helm console in front of the windshield + two pilot seats
        for dz in range(-3, 4):
            x = xe - 2
            if self.free(x, cz + dz, c):
                a.set(x, P, cz + dz, B("smooth_stone_slab", half="top"))
                a.set(x, P + 1, cz + dz, B("light_blue_carpet") if dz % 2 else B("black_carpet"))
                self.take([(x, cz + dz)])
        for dz in (-2, 2):
            if self.free(xe - 4, cz + dz, c):
                self.chair(xe - 4, cz + dz, (1, 0))
        # star chart table
        if self.region_ok(cx - 3, cz - 1, cx - 2, cz + 1, c):
            self.box(cx - 3, P, cz - 1, cx - 2, P, cz + 1, B("cyan_terracotta"))
            for dz in (-1, 0, 1):
                a.set(cx - 3, P + 1, cz + dz, B("light_blue_carpet"))
                a.set(cx - 2, P + 1, cz + dz, B("white_carpet") if dz == 0 else B("light_blue_carpet"))
        self.panel(c, 950, 292, "screen")
        self.panel(c, 1000, 330, "screen")
        self.panel(c, 905, 330, "green")
        self.pois["navigation"] = (cx, P, cz)

    def shields(self):
        a = self.a
        c = "S"
        cx, cz = self.center[c]
        # shield generator: glowing core inside a glass column, floor to ceiling
        top = P + ROOMS[c]["h"]
        if self.region_ok(cx - 1, cz - 1, cx + 1, cz + 1, c):
            for y in range(P, top):
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        b = B("purple_stained_glass") if (dx or dz) else B("sea_lantern")
                        if abs(dx) + abs(dz) == 2:
                            b = B("iron_block")
                        a.set(cx + dx, y, cz + dz, b)
            self.take([(cx + dx, cz + dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)])
        # hexagon shield panel on the east wall (red / white like the prime shields task)
        xe = max(x for x, z in self.cells[c] if z == cz)
        wx, wz, v = self.wall_spot(c, xe + 1, cz)
        for s in range(-3, 4):
            for t in range(4):
                x, z = wx, wz + s
                i, k = self.gi(x, z)
                if self.hull[i, k] and self.d[i, k] == 1:
                    a.set(x, P + 1 + t, z, B("red_concrete") if (s + t) % 3 == 0 else B("white_concrete"))
        self.panel(c, 750, 555, "screen")
        self.panel(c, 830, 520, "screen")
        self.pois["shields"] = (cx, P, cz)

    def comms(self):
        a = self.a
        c = "M"
        cx, cz = self.center[c]
        # radio desk along the north wall with screens above
        zn = min(z for x, z in self.cells[c] if x == cx)
        for x in range(cx - 5, cx + 6):
            if self.free(x, zn, c, keep_ok=False):
                a.set(x, P, zn, B("smooth_stone_slab", half="top"))
                self.take([(x, zn)])
                if x % 3 == 0:
                    a.set(x, P + 1, zn, B("daylight_detector"))
        for x in (cx - 4, cx - 1, cx + 2):
            wx, wz, v = self.wall_spot(c, x, zn - 1)
            self.screen(wx, wz, v, P + 2, "cyan", w=2, h=2)
        for x in (cx - 3, cx + 1):
            if self.free(x, zn + 2, c):
                self.chair(x, zn + 2, (0, -1))
        # antenna / transmitter rack
        for (x, z) in ((cx + 6, cz + 4), (cx - 7, cz + 4)):
            if self.free(x, z, c):
                self.box(x, P, z, x, P + 3, z, B("iron_block"))
                a.set(x, P + 4, z, B("lightning_rod", facing_direction=1))
                a.set(x, P + 2, z, B("redstone_lamp"))
        self.panel(c, 655, 570, "screen")
        self.panel(c, 707, 570, "screen")
        self.pois["comms"] = (cx, P, cz)

    def storage(self):
        a = self.a
        c = "T"
        cx, cz = self.center[c]
        rng = random.Random(81)
        # big fuel tanks (refuel task)
        fx, fz = self.ref(510, 560)
        for (dx, dz) in ((0, 0), (2, 0), (0, 2)):
            x, z = fx + dx, fz + dz
            if self.region_ok(x, z, x + 1, z + 1, c):
                self.box(x, P, z, x + 1, P + 2, z + 1, B("orange_concrete"))
                self.box(x, P + 1, z, x + 1, P + 1, z + 1, B("white_concrete"))
                for (ox, oz) in ((0, 0), (1, 1)):
                    a.set(x + ox, P + 3, z + oz, B("iron_trapdoor", direction=0))
        # crate stacks on pallets
        for (xp, yp, h) in ((560, 470, 2), (585, 470, 1), (480, 620, 1), (585, 560, 2), (500, 470, 1), (560, 610, 1)):
            x, z = self.ref(xp, yp)
            if self.region_ok(x, z, x + 1, z + 1, c):
                self.box(x, P, z, x + 1, P, z + 1, B("spruce_slab", half="top") if h == 1 else B("barrel", facing_direction=1))
                if h == 2:
                    self.box(x, P + 1, z, x + 1, P + 1, z + 1, B("spruce_planks"))
                    a.set(x, P + 2, z, B("barrel", facing_direction=1))
        # hazard stripes around the middle of the room
        for (x, z) in self.cells[c]:
            if abs(x - cx) == 4 and abs(z - cz) <= 4 or abs(z - cz) == 4 and abs(x - cx) <= 4:
                if a.get(x, P, z) == AIR:
                    a.set(x, FY, z, B("yellow_concrete") if (x + z) % 2 else B("black_concrete"))
        # garbage chute hatch on the south wall
        self.panel(c, 575, 630, "chute")
        self.panel(c, 510, 450, "green")
        self.panel(c, 595, 600, "orange")
        self.pois["storage"] = (cx, P, cz)

    def admin(self):
        """Admin: the holographic map table shows a tiny Skeld (rooms in blue, hallways in white)."""
        a = self.a
        c = "A"
        cx, cz = self.center[c]
        W, H = 11, 7
        x1, z1 = cx - W // 2, cz - H // 2 - 1
        if not self.region_ok(x1 - 1, z1 - 1, x1 + W, z1 + H, c):
            print("  [skeld] admin table does not fit")
            return
        self.box(x1, P, z1, x1 + W - 1, P, z1 + H - 1, B("polished_deepslate"))
        nx, nz = self.GX - 2 * PAD, self.GZ - 2 * PAD
        for u in range(W):
            for v in range(H):
                i0 = PAD + int(u * nx / W)
                i1 = PAD + int((u + 1) * nx / W)
                k0 = PAD + int(v * nz / H)
                k1 = PAD + int((v + 1) * nz / H)
                blk = self.g[i0:i1, k0:k1].ravel()
                rooms = sum(1 for q in blk if q.isupper())
                halls = sum(1 for q in blk if q.isdigit() or q.islower())
                if rooms >= halls and rooms > len(blk) * 0.2:
                    col = "light_blue_carpet"
                elif halls > len(blk) * 0.1:
                    col = "white_carpet"
                else:
                    col = "black_carpet"
                a.set(x1 + u, P + 1, z1 + v, B(col))
        # the card swipe slot at the table edge
        a.set(cx, P + 1, z1 + H - 1, B("lime_carpet"))
        self.panel(c, 642, 395, "screen")
        self.panel(c, 722, 395, "keypad")
        self.pois["admin"] = (cx, P, cz)

    def electrical(self):
        a = self.a
        c = "E"
        cx, cz = self.center[c]
        self.panel(c, 371, 410, "screen")
        self.panel(c, 400, 410, "wires")
        self.panel(c, 430, 410, "green")
        self.panel(c, 457, 412, "switches")
        # the big electrical cabinet with a hazard sign
        x, z = self.ref(372, 470)
        wx, wz, v = self.wall_spot(c, x - 2, z)
        dx, dz = v
        bx, bz = wx + dx, wz + dz
        ax, az = abs(dz), abs(dx)
        cells = [(bx + ax * s, bz + az * s) for s in range(3)]
        if all(self.free(px, pz, c) for px, pz in cells):
            for (px, pz) in cells:
                self.box(px, P, pz, px, P + 3, pz, B("iron_block"))
            mx, mz = cells[1]
            a.set(mx, P + 2, mz, B("yellow_glazed_terracotta"))
        # breaker rows and cable trays
        for (xp, yp) in ((440, 470), (440, 500)):
            x, z = self.ref(xp, yp)
            wx, wz, v = self.wall_spot(c, x + 3, z)
            self.screen(wx, wz, v, P + 1, "red", w=1, h=1)
        for (x, z) in self.cells[c]:
            if (x + z) % 9 == 0 and self.free(x, z, c) and a.get(x, P + 5, z) == AIR:
                a.set(x, P + 5, z, B("iron_bars"))
        self.pois["electrical"] = (cx, P, cz)

    def engine(self, c):
        """Upper / lower engine: a huge engine body against the back (west) wall with glowing vents."""
        a = self.a
        cx, cz = self.center[c]
        top = P + ROOMS[c]["h"]
        xw = min(x for x, z in self.cells[c] if z == cz)
        x1, x2 = xw, xw + 9
        z1, z2 = cz - 5, cz + 5
        if not self.region_ok(x1, z1, x2 + 1, z2, c, keep_ok=True):
            print("  [skeld] engine %s does not fit" % c)
        # base block (2 high, not climbable) and the cylinder lying on it
        x1 = min([x for x, z in self.cells[c] if z1 <= z <= z2] + [x1])
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if self.ch(x, z) != c:
                    continue
                a.set(x, P, z, B("gray_concrete"))
                a.set(x, P + 1, z, B("gray_concrete") if x < x2 else B("iron_block"))
                self.occ.add((x, z))
        ry = (top - 1 + P + 2) / 2.0
        rr = (top - 1 - (P + 2)) / 2.0 + 0.5
        for x in range(x1, x2 + 2):
            for z in range(z1, z2 + 1):
                for y in range(P + 2, top):
                    if (z - cz) ** 2 + (y - ry) ** 2 <= rr * rr:
                        if self.ch(x, z) != c:
                            continue
                        ring_i = (x - x1) % 3 == 0
                        b = B("light_gray_concrete") if not ring_i else B("orange_concrete")
                        if x == x2 + 1:
                            d2 = (z - cz) ** 2 + (y - ry) ** 2
                            b = B("orange_stained_glass") if d2 <= (rr - 1.2) ** 2 else B("iron_block")
                        a.set(x, y, z, b)
                        self.occ.add((x, z))
        # glowing core seen through the front cap
        for z in range(cz - 1, cz + 2):
            for y in range(int(ry) - 1, int(ry) + 2):
                a.set(x2, y, z, B("ochre_froglight", axis="x"))
        # under the overhang of the front cap: fill so nothing is a 1-high cave
        for z in range(z1, z2 + 1):
            if self.ch(x2 + 1, z) == c and a.get(x2 + 1, P + 2, z) != AIR:
                a.set(x2 + 1, P, z, B("iron_block"))
                a.set(x2 + 1, P + 1, z, B("iron_block"))
        # fuel can + control console in front
        fx = x2 + 4
        for dz in (-4, 4):
            if self.free(fx, cz + dz, c):
                self.box(fx, P, cz + dz, fx, P + 1, cz + dz, B("orange_concrete"))
                a.set(fx, P + 2, cz + dz, B("iron_trapdoor", direction=0))
        # panels
        if c == "U":
            self.panel(c, 201, 180, "screen")
            self.panel(c, 171, 257, "screen")
        else:
            self.panel(c, 179, 450, "screen")
            self.panel(c, 171, 516, "screen")
        self.pois["upper_engine" if c == "U" else "lower_engine"] = (cx, P, cz)

    def security(self):
        a = self.a
        c = "Y"
        cx, cz = self.center[c]
        # camera monitors on the east wall
        xe = max(x for x, z in self.cells[c] if z == cz)
        for zz in (cz - 4, cz - 1, cz + 2):
            wx, wz, v = self.wall_spot(c, xe + 1, zz)
            self.screen(wx, wz, v, P + 1, "light_blue", w=2, h=2)
        # desk with the camera console
        for dz in range(-4, 4):
            x = xe
            if self.free(x, cz + dz, c):
                a.set(x, P, cz + dz, B("dark_oak_slab", half="top"))
                self.take([(x, cz + dz)])
        for dz in (-3, 1):
            if self.free(xe - 2, cz + dz, c):
                self.chair(xe - 2, cz + dz, (1, 0))
        self.panel(c, 322, 320, "screen")
        self.pois["security"] = (cx, P, cz)

    def reactor(self):
        a = self.a
        c = "R"
        top = P + ROOMS[c]["h"]
        cx, cz = self.ref(115, 357)
        # reactor core: glowing column in a glass sleeve, floor to ceiling
        for y in range(P, top):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    r2 = dx * dx + dz * dz
                    if r2 > 5:
                        continue
                    if r2 <= 1:
                        b = B("sea_lantern")
                    elif y in (P, top - 1) or (y - P) % 4 == 0:
                        b = B("iron_block")
                    else:
                        b = B("light_blue_stained_glass")
                    a.set(cx + dx, y, cz + dz, b)
                    self.occ.add((cx + dx, cz + dz))
        # glowing floor ring
        for (x, z) in self.cells[c]:
            d = math.hypot(x - cx, z - cz)
            if 3.6 <= d < 4.6 and a.get(x, P, z) == AIR:
                a.set(x, FY, z, B("sea_lantern") if (x + z) % 2 == 0 else B("light_blue_concrete"))
        # coolant pipes under the ceiling to the walls
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for s in range(3, 16):
                x, z = cx + dx * s, cz + dz * s
                if self.ch(x, z) != c:
                    break
                a.set(x, top - 1, z, B("iron_bars"))
        # handprint scanners at the two tabs, start-reactor keypad, manifolds
        self.panel(c, 120, 268, "hand")
        self.panel(c, 120, 447, "hand")
        self.panel(c, 75, 310, "keypad")
        self.panel(c, 70, 410, "orange")
        self.pois["reactor"] = (cx, P, cz)

    def medbay(self):
        a = self.a
        c = "D"
        # body scanner platform (green glowing disk)
        sx, sz = self.ref(421, 357)
        for (x, z) in self.cells[c]:
            d = math.hypot(x - sx, z - sz)
            if d <= 2.2 and self.free(x, z, c, keep_ok=True):
                a.set(x, FY, z, B("lime_stained_glass"))
                a.set(x, FY - 1, z, B("sea_lantern"))
        for (x, z) in self.cells[c]:
            d = math.hypot(x - sx, z - sz)
            if 1.6 <= d <= 2.6:
                a.set(x, P + ROOMS[c]["h"] - 1, z, B("lime_stained_glass"))
        # beds along the west wall
        xw = min(x for x, z in self.cells[c])
        zs = sorted(set(z for x, z in self.cells[c] if x == xw))
        for z in zs[1:-1:3]:
            bx = xw
            if self.free(bx, z, c) and self.free(bx + 1, z, c):
                a.set(bx, P, z, B("bed", direction=1, head_piece_bit=1))
                a.set(bx + 1, P, z, B("bed", direction=1, head_piece_bit=0))
                a.add_be(simple_be("Bed", bx, P, z, color=an.ByteTag(0)))
                a.add_be(simple_be("Bed", bx + 1, P, z, color=an.ByteTag(0)))
                self.take([(bx, z), (bx + 1, z)])
        # sample analyser bench
        x, z = self.ref(456, 330)
        wx, wz, v = self.wall_spot(c, x + 2, z)
        dx, dz = v
        ax, az = abs(dz), abs(dx)
        for s in range(-1, 2):
            px, pz = wx + dx + ax * s, wz + dz + az * s
            if self.free(px, pz, c):
                a.set(px, P, pz, B("smooth_quartz_slab", half="top"))
                self.take([(px, pz)])
                if s == 0:
                    a.set(px, P + 1, pz, B("brewing_stand"))
                    a.add_be(simple_be("BrewingStand", px, P + 1, pz))
        self.screen(wx + ax * -1, wz + az * -1, v, P + 2, "lime", w=3, h=1)
        self.pois["medbay"] = (sx, P, sz)

    def hallways(self):
        """Pipes under the hallway ceilings and hazard stripes at the junctions."""
        a = self.a
        g = self.g
        for (i, k) in np.argwhere(np.char.isdigit(g)):
            x, z = self.wx(i), self.wz(k)
            top = self.ceil[i, k]
            for di, dk in N4:
                if self.hull[i + di, k + dk] and self.d[i + di, k + dk] == 1:
                    face = 2 if di != 0 else 4      # pipe runs along the wall
                    if a.get(x, top - 1, z) == AIR:
                        a.set(x, top - 1, z, B("lightning_rod", facing_direction=face))
                    break
            # stripe where a hallway meets a room without a door
            for di, dk in N4:
                c2 = g[i + di, k + dk]
                if c2.isupper():
                    a.set(x, FY, z, B("yellow_concrete") if (x + z) % 2 else B("black_concrete"))

    # ------------------------------------------------------------------ crewmates
    def crewmate(self, x0, z0, colour, face=(0, 1), c=None):
        """Crewmate statue (2 wide, 3.5 tall) with visor and backpack; face = direction it looks."""
        a = self.a
        fx, fz = face
        sx, sz = abs(fz), abs(fx)                  # sideways axis
        body = [(x0 + sx * u - fx * w, z0 + sz * u - fz * w) for u in (0, 1) for w in (0, 1)]
        visor = [(x0 + sx * u + fx, z0 + sz * u + fz) for u in (0, 1)]
        pack = [(x0 + sx * u - fx * 2, z0 + sz * u - fz * 2) for u in (0, 1)]
        need = body + visor + pack
        if not all(self.free(x, z, c) for x, z in need):
            print("  [skeld] crewmate skipped at", x0, z0)
            return False
        col = B(colour + "_concrete")
        for (x, z) in body:
            for y in range(P, P + 4):
                a.set(x, y, z, col)
        for (x, z) in visor:
            a.set(x, P + 2, z, B("light_blue_stained_glass"))
        for (x, z) in pack:
            a.set(x, P + 1, z, col)
            a.set(x, P + 2, z, col)
        # under the backpack: no 1-high cave
        for (x, z) in pack:
            a.set(x, P, z, col)
        self.take(body + pack)
        return True

    def near_crewmate(self, x, z, colour, face, c):
        """Crewmate at (x, z) or the nearest spot around it that fits."""
        for r in range(0, 5):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if max(abs(dx), abs(dz)) == r and self.fits_crewmate(x + dx, z + dz, face, c):
                        return self.crewmate(x + dx, z + dz, colour, face, c)
        print("  [skeld] no room for the %s crewmate" % colour)
        return False

    def fits_crewmate(self, x0, z0, face, c):
        fx, fz = face
        sx, sz = abs(fz), abs(fx)
        need = [(x0 + sx * u - fx * w, z0 + sz * u - fz * w) for u in (0, 1) for w in (-1, 0, 1, 2)]
        return all(self.free(x, z, c) for x, z in need)

    def crewmates(self):
        cx, cz = self.center["C"]
        self.near_crewmate(cx - 3, cz - 16, "red", (0, 1), "C")
        self.near_crewmate(cx + 8, cz - 16, "lime", (0, 1), "C")
        x, z = self.center["T"]
        self.near_crewmate(x + 6, z + 8, "yellow", (-1, 0), "T")
        x, z = self.center["A"]
        self.near_crewmate(x + 7, z + 5, "pink", (-1, 0), "A")
        x, z = self.center["N"]
        self.near_crewmate(x - 4, z + 5, "cyan", (1, 0), "N")
        x, z = self.center["W"]
        self.near_crewmate(x - 5, z + 4, "black", (1, 0), "W")
        # ...and the famous one lying in electrical
        x, z = self.center["E"]
        for dx, dz in ((3, 2), (4, 2), (3, 3), (4, 3)):
            if self.free(x + dx, z + dz, "E"):
                self.a.set(x + dx, P, z + dz, B("cyan_concrete"))
                self.take([(x + dx, z + dz)])
        if (x + 4, z + 2) in self.occ:
            self.a.set(x + 4, P + 1, z + 2, B("bone_block", axis="y"))

    # ------------------------------------------------------------------ outside details
    def exterior(self):
        a = self.a
        # engine thrusters behind the two engine rooms (pointing west)
        for c in ("U", "L"):
            cx, cz = self.center[c]
            xw = min(x for x, z in self.cells[c] if z == cz) - 3
            cy = P + 4
            for s in range(0, 14):
                x = xw - s
                r = 4.2 + s * 0.22
                for z in range(int(cz - r - 1), int(cz + r + 2)):
                    for y in range(int(cy - r - 1), int(cy + r + 2)):
                        d = math.hypot(z - cz, y - cy)
                        i, k = self.gi(x, z)
                        if self.foot[i, k]:
                            continue
                        if r - 1.1 < d <= r:
                            a.set(x, y, z, B("light_gray_concrete") if s % 4 else B("iron_block"))
                        elif d <= r - 1.1 and s == 2:
                            a.set(x, y, z, B("shroomlight") if d < r - 2.5 else B("ochre_froglight", axis="x"))
            # exhaust glow
            for s in range(14, 20):
                x = xw - s
                r = 3.0 - (s - 14) * 0.4
                for z in range(int(cz - r - 1), int(cz + r + 2)):
                    for y in range(int(cy - r - 1), int(cy + r + 2)):
                        if math.hypot(z - cz, y - cy) <= r:
                            a.set(x, y, z, B("orange_stained_glass") if s % 2 else B("yellow_stained_glass"))
        # twin cannons outside the weapons room
        c = "W"
        cx, cz = self.center[c]
        xe = max(x for x, z in self.cells[c] if z == cz) + 3
        for dz in (-2, 2):
            for s in range(0, 12):
                x = xe + s
                b = B("purple_concrete") if s >= 9 else B("gray_concrete")
                a.set(x, P + 3, cz + dz, b)
                if s < 3:
                    a.set(x, P + 2, cz + dz, B("gray_concrete"))
                    a.set(x, P + 4, cz + dz, B("gray_concrete"))
        # shield emitters below the shields room
        c = "S"
        sx, sz = self.ref(818, 595)
        for dx in (-3, 3):
            for s in range(0, 6):
                for y in (P + 1, P + 2):
                    i, k = self.gi(sx + dx, sz + s)
                    if not self.foot[i, k]:
                        a.set(sx + dx, y, sz + s, B("iron_block") if s < 5 else B("light_blue_stained_glass"))
        # comms antenna dish on the roof
        cx, cz = self.center["M"]
        ry = P + ROOMS["M"]["h"] + 2
        for y in range(ry, ry + 6):
            a.set(cx, y, cz, B("iron_bars"))
        disk(a, cx, ry + 6, cz, 3.2, B("white_concrete"))
        a.set(cx, ry + 7, cz, B("lightning_rod", facing_direction=1))
        # storage garbage hatch outside the south hull
        x, z = self.ref(575, 650)
        for dx in range(-2, 3):
            i, k = self.gi(x + dx, z + 2)
            if not self.foot[i, k]:
                a.set(x + dx, P - 1, z + 2, B("iron_block"))
                a.set(x + dx, P, z + 2, B("yellow_concrete") if dx % 2 else B("black_concrete"))

    def roof_details(self):
        """Roof panel lines, rooftop vents and running lights along the hull edge."""
        a = self.a
        rng = random.Random(12)
        for (i, k) in np.argwhere(self.foot):
            x, z = self.wx(i), self.wz(k)
            top = self.roof[i, k] if self.hull[i, k] else None
            if top is None:
                y = self.ceil[i, k] + 1
                for di, dk in N4:
                    if self.hull[i + di, k + dk]:
                        y = max(y, self.roof[i + di, k + dk])
                top = y
            if x % 8 == 0 or z % 8 == 0:
                a.set(x, top, z, B("light_gray_concrete"))
            edge = any(self.space_open[i + di, k + dk] for di, dk in N4)
            if edge and (x + z) % 9 == 0:
                a.set(x, top + 1, z, B("sea_lantern"))
            elif not edge and rng.random() < 0.012:
                a.set(x, top + 1, z, B("iron_trapdoor", direction=0))
            elif not edge and rng.random() < 0.004:
                for y in range(top + 1, top + 4):
                    a.set(x, y, z, B("iron_bars"))
                a.set(x, top + 4, z, B("redstone_lamp"))

    # ------------------------------------------------------------------ signs
    def labels(self):
        """A hanging name sign above every way into a room."""
        a = self.a
        g = self.g
        done = set()
        for c in ROOMS:
            ent = []
            for (x, z) in self.cells[c]:
                i, k = self.gi(x, z)
                for di, dk in N4:
                    c2 = g[i + di, k + dk]
                    if c2 != " " and c2 != c:
                        ent.append((x, z, (di, dk)))
                        break
            # group entrance cells into runs
            seen = set()
            for (x, z, v) in ent:
                if (x, z) in seen:
                    continue
                run = []
                dq = deque([(x, z)])
                pts = {(p[0], p[1]): p[2] for p in ent}
                while dq:
                    p = dq.popleft()
                    if p in seen or p not in pts:
                        continue
                    seen.add(p)
                    run.append(p)
                    for dx, dz in N8:
                        dq.append((p[0] + dx, p[1] + dz))
                run.sort()
                mx, mz = run[len(run) // 2]
                v = pts[(mx, mz)]
                # sign one block inside the room, hanging from the ceiling, text facing the doorway
                sx, sz = mx - v[0], mz - v[1]
                if self.ch(sx, sz) != c or (sx, sz) in done:
                    sx, sz = mx, mz
                top = P + ROOMS[c]["h"]
                y = top - 1
                face = FACE[v]
                a.set(sx, y, sz, B("spruce_hanging_sign", hanging=1, attached_bit=0, facing_direction=face))
                txt = "§l%s" % ROOMS[c]["name"]
                a.add_be(sign_be(sx, y, sz, txt, txt, glow=True, hanging=True, color=-1))
                done.add((sx, sz))


def build_skeld(cx, cz):
    s = Skeld(cx, cz)
    s.build()
    return s
