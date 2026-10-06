"""The Skeld as a mining ship floating in the sky.

reactor  -> iron ore core (3x3x3) + iron veins on the walls
engines  -> coal bunkers along the side walls
storage  -> smeltery with 12 personal furnace rooms (one player at a time; two who enter together can fight)
west airlock (bridge from the hub), south hatch (bridge to the volcano)
"""
import math

import gen_skeld
from gen_skeld import Skeld, P, FY, ROOMS, N4
from mcw import B, AIR, simple_be
from gen_common import stair, slab, wall_sign, standing_sign

ROOMS["T"]["name"] = "제련실 (개인 화로방)"
ROOMS["R"]["name"] = "철광 반응로"
ROOMS["U"]["name"] = "상부 엔진 (석탄)"
ROOMS["L"]["name"] = "하부 엔진 (석탄)"

SPINE_X = 85                          # blueprint column of the back-to-back wall
CELL_Z = [63, 68, 73, 78, 83, 88, 93]  # blueprint rows of the walls between rooms


class SkySkeld(Skeld):
    def __init__(self, cx, cz, gens):
        super().__init__(cx, cz)
        self.gens = gens
        self.furnace_rooms = []
        self.entrance_w = None
        self.entrance_s = None

    def bx(self, x):
        return self.X0 + x

    def bz(self, z):
        return self.Z0 + z

    def space(self):
        pass                     # no starfield box: the ship floats in the open sky

    def build(self):
        a = super().build()
        self.entrances()
        a.fix_walls()
        return a

    # ------------------------------------------------------------------ iron
    def reactor(self):
        a = self.a
        c = "R"
        top = P + ROOMS[c]["h"]
        cx, cz = self.ref(115, 357)
        for y in range(P, top):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    r2 = dx * dx + dz * dz
                    if r2 > 5:
                        continue
                    if y < P + 3:
                        if r2 <= 2:
                            self.gens.add(a, cx + dx, y, cz + dz, "iron_ore", "iron", "skeld")
                        else:
                            a.set(cx + dx, y, cz + dz, AIR)
                    elif y == P + 3:
                        a.set(cx + dx, y, cz + dz, B("iron_block"))
                    elif r2 <= 1:
                        a.set(cx + dx, y, cz + dz, B("sea_lantern"))
                    else:
                        a.set(cx + dx, y, cz + dz, B("light_blue_stained_glass") if (y - P) % 4 else B("iron_block"))
                    self.occ.add((cx + dx, cz + dz))
        for (x, z) in self.cells[c]:
            d = math.hypot(x - cx, z - cz)
            if 3.6 <= d < 4.6 and a.get(x, P, z) == AIR:
                a.set(x, FY, z, B("sea_lantern") if (x + z) % 2 == 0 else B("light_blue_concrete"))
        # iron veins: wall-side floor cells, 2 high, every third cell
        n = 0
        for (x, z) in sorted(self.cells[c]):
            i, k = self.gi(x, z)
            if not any(self.hull[i + di, k + dk] for di, dk in N4):
                continue
            if (x, z) in self.keep or (x, z) in self.occ or (x + 2 * z) % 3:
                continue
            if math.hypot(x - cx, z - cz) < 6:
                continue
            for y in (P, P + 1):
                if a.get(x, y, z) == AIR:
                    self.gens.add(a, x, y, z, "iron_ore", "iron", "skeld")
            self.occ.add((x, z))
            n += 1
        self.panel(c, 120, 268, "hand")
        self.panel(c, 120, 447, "hand")
        self.pois["reactor"] = (cx, P, cz)

    # ------------------------------------------------------------------ coal
    def engine(self, c):
        super().engine(c)
        a = self.a
        cx, cz = self.center[c]
        xw = min(x for x, z in self.cells[c] if z == cz)
        for (x, z) in sorted(self.cells[c]):
            if x < xw + 11:
                continue
            i, k = self.gi(x, z)
            if not any(self.hull[i + di, k + dk] for di, dk in N4):
                continue
            if (x, z) in self.keep or (x, z) in self.occ or x % 2:
                continue
            for y in (P, P + 1):
                if a.get(x, y, z) == AIR:
                    self.gens.add(a, x, y, z, "coal_ore", "coal", "skeld")
            self.occ.add((x, z))

    # ------------------------------------------------------------------ furnace rooms
    def storage(self):
        a = self.a
        c = "T"
        wall = B("light_gray_concrete")
        frame = B("iron_block")
        roof = B("smooth_stone")
        x_w, x_s, x_e = self.bx(80), self.bx(SPINE_X), self.bx(90)
        z_top, z_bot = self.bz(CELL_Z[0]), self.bz(CELL_Z[-1])
        # shell of the block: everything solid, then hollow each room
        for x in range(x_w, x_e + 1):
            for z in range(z_top, z_bot + 1):
                for y in range(P, P + 4):
                    a.set(x, y, z, wall)
                a.set(x, P + 4, z, roof)
                self.occ.add((x, z))
                self.keep.add((x, z))
        for x in (x_w, x_s, x_e):
            for z in range(z_top, z_bot + 1):
                if z in [self.bz(v) for v in CELL_Z]:
                    for y in range(P, P + 5):
                        a.set(x, y, z, frame)
        num = 0
        for side, (ix1, ix2, door_x, out_x, face, back_face) in enumerate((
                (self.bx(81), self.bx(84), x_w, x_w - 2, "west", 4),
                (self.bx(86), self.bx(89), x_e, x_e + 2, "east", 5))):
            for r in range(len(CELL_Z) - 1):
                z1, z2 = self.bz(CELL_Z[r]) + 1, self.bz(CELL_Z[r + 1]) - 1
                num += 1
                for x in range(ix1, ix2 + 1):
                    for z in range(z1, z2 + 1):
                        for y in range(P, P + 4):
                            a.set(x, y, z, AIR)
                        a.set(x, FY, z, B("polished_andesite") if (x + z) % 2 else B("smooth_stone"))
                dz = z1 + 1
                a.set(door_x, P, dz, AIR)
                a.set(door_x, P + 1, dz, AIR)
                a.set(door_x, P + 2, dz, B("lime_concrete"))
                # furnaces on the back wall, facing the doorway
                fx = ix2 if side == 0 else ix1
                for i, z in enumerate(range(z1, z2 + 1)):
                    blk = "blast_furnace" if i == 1 else "furnace"
                    a.set(fx, P, z, B(blk, cardinal=face))
                    a.add_be(simple_be("BlastFurnace" if blk == "blast_furnace" else "Furnace", fx, P, z))
                    a.set(fx, P + 1, z, B("iron_trapdoor", direction=0, open_bit=0, upside_down_bit=0))
                a.set(fx, P + 2, z1 + 1, B("lantern", hanging=0))
                mx = (ix1 + ix2) // 2
                a.set(mx, P + 3, z1 + 2, B("lantern", hanging=1))
                # number sign above the doorway, facing the aisle
                wall_sign(a, door_x + (-1 if side == 0 else 1), P + 3, dz, back_face,
                          "§l§6개인 화로방 %d\n§r§f초록 = 비어 있음\n§c빨강 = 사용 중" % num, kind="birch_wall_sign")
                self.furnace_rooms.append(dict(
                    id=num, box=(ix1, P, z1, ix2, P + 3, z2),
                    lamp=(door_x, P + 2, dz),
                    door=(door_x, P, dz),
                    out=(out_x, P, dz, 90 if side == 0 else 270),
                    furnaces=[(fx, P, z) for z in range(z1, z2 + 1)]))
        # warning board at the north end of the aisle
        for (x, z, rot) in ((self.bx(78), self.bz(62), 8), (self.bx(93), self.bz(62), 8)):
            if a.get(x, P, z) == AIR:
                a.set(x, P, z, B("iron_block"))
                standing_sign(a, x, P + 1, z, rot, "§l§6제련실\n§r§f비어 있는 방에만\n§f들어갈 수 있어요",
                              kind="birch_standing_sign")
        for (x, z) in ((self.bx(77), self.bz(95)), (self.bx(95), self.bz(95))):
            if a.get(x, P, z) == AIR:
                a.set(x, P, z, B("iron_block"))
                standing_sign(a, x, P + 1, z, 0, "§l§c주의\n§r§f화로방은 안전구역이\n§f아닙니다 (밤 PvP)",
                              kind="birch_standing_sign")
        self.pois["storage"] = self.center[c]

    # ------------------------------------------------------------------ doors to the bridges
    def entrances(self):
        a = self.a
        # west airlock into the reactor (bridge from the hub)
        zc = self.bz(50)
        for x in range(self.bx(-3), self.bx(2)):
            for z in range(zc - 1, zc + 2):
                for y in range(P, P + 3):
                    a.set(x, y, z, AIR)
                a.set(x, FY, z, B("iron_block") if z != zc else B("yellow_concrete"))
        for z in (zc - 2, zc + 2):
            for y in range(P, P + 4):
                a.set(self.bx(-1), y, z, B("iron_block"))
                a.set(self.bx(1), y, z, B("iron_block"))
        for x in (self.bx(-1), self.bx(0), self.bx(1)):
            a.set(x, P + 3, zc - 1, B("black_concrete"))
            a.set(x, P + 3, zc, B("yellow_concrete"))
            a.set(x, P + 3, zc + 1, B("black_concrete"))
        self.entrance_w = (self.bx(-3), P, zc)
        # south hatch out of the smeltery (bridge to the volcano)
        xc = self.bx(87)
        for z in range(self.bz(98), self.bz(102)):
            for x in range(xc - 1, xc + 2):
                for y in range(P, P + 3):
                    a.set(x, y, z, AIR)
                a.set(x, FY, z, B("iron_block") if x != xc else B("orange_concrete"))
        for x in (xc - 2, xc + 2):
            for y in range(P, P + 4):
                a.set(x, y, self.bz(98), B("iron_block"))
        self.entrance_s = (xc, P, self.bz(101))
