"""Lobby: a large, dimly lit hall with a stage (start NPC), an ability shop street and a map gallery."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from mcw import B, AIR, Area, sign_be, simple_be, flowerpot_be, banner_be
from gen_common import (stair, slab, lamp_post, hanging_lamp, wall_sign, standing_sign, disk, ring,
                        leaf_blob, leaves_of, log_of, oak_tree, palm_tree, cherry_tree, spruce_tree,
                        tall_plant, FLOWERS, big_oak, ellipsoid)
from abilities import ABILITIES

FY = 63          # floor block level
P = 64           # feet level
ROOF = 95
SPAWN = (0, P, 41)

# interior extents
NB_Z = (-47, -31)      # north (stage) band
WING_Z = (-30, 47)
STALL_Z = [-21, -3, 15, 33]
GATE_Z = [-24, -11, 2, 15, 28, 41]     # six map gates, 13 apart
PILLARS_Z = [-29, -20, -11, -2, 7, 16, 25, 34, 43]
FOUNTAIN = (0, 6)
DOME_R = 20


def vault_top(x):
    return 76 + int(round(13 * math.sqrt(max(0.0, 1 - (x / 20.0) ** 2))))


class Lobby:
    def __init__(self):
        self.a = Area("lobby", -80, -80, 160, 160, y0=48, sy=80, biome=1)
        self.rng = random.Random(7)
        self.npcs = []          # dicts: name, x, y, z, yaw, tag, scene
        self.markers = []       # blocks that must exist before NPCs are summoned

    # ------------------------------------------------------------------
    def build(self):
        self.shell()
        self.floors()
        self.ceilings()
        self.colonnades()
        self.walls_decor()
        self.stage()
        self.title()
        self.fountain()
        self.chandeliers()
        self.shop()
        self.gallery()
        self.foyer()
        self.a.fix_walls()
        from lighting import fill_dark
        fill_dark(self.a, (-57, -47, 57, 47), (P, 67), threshold=5, level=9, height=3, spacing=4, avoid_col=(0, FOUNTAIN[1]))
        return self.a

    # ------------------------------------------------------------------
    def shell(self):
        a = self.a
        a.fill(-60, 56, -50, 60, ROOF + 1, 50, B("deepslate_bricks"))
        a.fill(-60, 56, -50, 60, 62, 50, B("deepslate"))
        # carve interior
        a.fill(-57, P, NB_Z[0], 57, 92, NB_Z[1], AIR)
        a.fill(-57, P, WING_Z[0], -23, 75, WING_Z[1], AIR)
        a.fill(23, P, WING_Z[0], 57, 75, WING_Z[1], AIR)
        for x in range(-19, 20):
            a.fill(x, P, WING_Z[0], x, vault_top(x), WING_Z[1], AIR)
        # dome over the fountain
        fx, fz = FOUNTAIN
        rib = B("polished_blackstone_bricks")
        glass = B("glass")
        tint = B("purple_stained_glass")
        for x in range(fx - DOME_R - 1, fx + DOME_R + 2):
            for z in range(fz - DOME_R - 1, fz + DOME_R + 2):
                for y in range(76, ROOF + 4):
                    d = math.sqrt((x - fx) ** 2 + (y - 76) ** 2 + (z - fz) ** 2)
                    if abs(x) > 19:
                        continue
                    if d < DOME_R - 0.5:
                        a.set(x, y, z, AIR)
                    elif d < DOME_R + 0.5:
                        ang = math.degrees(math.atan2(z - fz, x - fx)) % 45
                        if ang < 3.5 or ang > 41.5 or y in (84, 90):
                            b = rib
                        else:
                            b = tint if (y < 84) else glass
                        a.set(x, y, z, b)
                # clear roof above the dome
                r2 = (x - fx) ** 2 + (z - fz) ** 2
                if r2 <= (DOME_R + 0.5) ** 2 and abs(x) <= 20:
                    ys = 76 + math.sqrt(max(0.0, (DOME_R + 0.5) ** 2 - r2))
                    a.fill(x, int(ys) + 1, z, x, ROOF + 3, z, AIR)
        a.set(fx, 76 + DOME_R, fz, glass)
        # outer cornice / roof trim (visible from the dome only)
        a.fill(-61, ROOF + 1, -51, 61, ROOF + 1, 51, B("polished_blackstone_bricks"), only_air=True)
        for x in range(-61, 62):
            for z in (-51, 51):
                a.set(x, ROOF + 2, z, B("polished_blackstone_wall"))
        for z in range(-51, 52):
            for x in (-61, 61):
                a.set(x, ROOF + 2, z, B("polished_blackstone_wall"))

    # ------------------------------------------------------------------
    def floor_block(self, x, z):
        # north band: polished blackstone with gold rays towards the stage
        if NB_Z[0] <= z <= NB_Z[1]:
            if (x + z) % 8 == 0 or (x - z) % 8 == 0:
                return B("polished_blackstone_bricks")
            return B("polished_deepslate") if (x // 2 + z // 2) % 2 == 0 else B("deepslate_tiles")
        if abs(x) <= 19:
            fx, fz = FOUNTAIN
            r = math.sqrt((x - fx) ** 2 + (z - fz) ** 2)
            if 8.5 <= r < 13.5:
                k = int(r)
                if k in (10, 12):
                    return B("polished_blackstone_bricks")
                if k == 11:
                    ang = math.degrees(math.atan2(z - fz, x - fx)) % 45
                    return B("crying_obsidian") if ang < 4 else B("chiseled_deepslate")
                return B("polished_deepslate")
            if abs(x) == 2:
                return B("gilded_blackstone") if z % 4 == 0 else B("polished_blackstone_bricks")
            if x % 6 == 0 or z % 6 == 0:
                return B("deepslate_tiles")
            return B("polished_deepslate")
        if x < 0:   # shop street
            if -50 <= x <= -36:
                k = (x * 7 + z * 13) % 11
                if x in (-50, -36):
                    return B("polished_tuff")
                return B("tuff_bricks") if k < 7 else B("chiseled_tuff_bricks") if k == 7 else B("polished_tuff")
            return B("dark_oak_planks") if (x + z) % 2 == 0 else B("spruce_planks")
        # gallery: parquet
        if (x // 3 + z // 3) % 2 == 0:
            return B("dark_oak_planks")
        return B("stripped_dark_oak_wood", axis="x") if (x // 3) % 2 == 0 else B("stripped_dark_oak_wood", axis="z")

    def floors(self):
        a = self.a
        for x in range(-57, 58):
            for z in range(-47, 48):
                if a.get(x, P, z) == AIR:
                    a.set(x, FY, z, self.floor_block(x, z))
        # red runner from the foyer to the stage
        red = B("red_carpet")
        for z in range(-34, 46):
            fx, fz = FOUNTAIN
            if math.sqrt((0 - fx) ** 2 + (z - fz) ** 2) < 13.5:
                continue
            for x in (-1, 0, 1):
                a.set(x, P, z, red)

    # ------------------------------------------------------------------
    def coffered(self, x1, z1, x2, z2, y, step=6):
        a = self.a
        a.fill(x1, y, z1, x2, y, z2, B("dark_oak_planks"))
        beam_x = B("stripped_dark_oak_log", axis="x")
        beam_z = B("stripped_dark_oak_log", axis="z")
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if (x - x1) % step == 0:
                    a.set(x, y - 1, z, beam_z)
                elif (z - z1) % step == 0:
                    a.set(x, y - 1, z, beam_x)
        for x in range(x1, x2 + 1, step):
            for z in range(z1, z2 + 1, step):
                a.set(x, y - 1, z, B("polished_deepslate"))

    def ceilings(self):
        a = self.a
        self.coffered(-57, WING_Z[0], -23, WING_Z[1], 76)
        self.coffered(23, WING_Z[0], 57, WING_Z[1], 76)
        self.coffered(-57, NB_Z[0], 57, NB_Z[1], 93)
        # vault ribs over the nave (outside the dome)
        rib = B("polished_blackstone_bricks")
        tile = B("deepslate_tiles")
        fx, fz = FOUNTAIN
        for z in range(WING_Z[0], WING_Z[1] + 1):
            for x in range(-19, 20):
                yt = vault_top(x) + 1
                if (x - fx) ** 2 + (z - fz) ** 2 <= (DOME_R + 0.5) ** 2:
                    continue
                a.set(x, yt, z, rib if (z - WING_Z[0]) % 9 == 1 else tile)

    # ------------------------------------------------------------------
    def colonnades(self):
        a = self.a
        wall = B("deepslate_bricks")
        pil = B("polished_deepslate")
        cap = B("chiseled_deepslate")
        base = B("polished_blackstone_bricks")
        for side in (-1, 1):
            xs = [side * 20, side * 21, side * 22]
            x_lo, x_hi = min(xs), max(xs)
            # solid colonnade wall, then openings
            a.fill(x_lo, P, WING_Z[0], x_hi, 80, WING_Z[1], wall)
            for zp in PILLARS_Z:
                a.fill(x_lo, P, zp - 1, x_hi, 75, zp + 1, pil)
                a.fill(x_lo, P, zp - 1, x_hi, P, zp + 1, base)
                a.fill(x_lo, 72, zp - 1, x_hi, 72, zp + 1, cap)
            for i in range(len(PILLARS_Z) - 1):
                z1, z2 = PILLARS_Z[i] + 2, PILLARS_Z[i + 1] - 2
                a.fill(x_lo, P, z1, x_hi, 71, z2, AIR)
                # arch: stairs at the corners
                for x in xs:
                    a.set(x, 71, z1, stair("deepslate_brick_stairs", "north", upside=True))
                    a.set(x, 71, z2, stair("deepslate_brick_stairs", "south", upside=True))
                    a.set(x, 71, z1 + 1, slab("deepslate_brick_slab", top=True))
                    a.set(x, 71, z2 - 1, slab("deepslate_brick_slab", top=True))
            # niches with soul lanterns facing the nave on the pillar
            xn = side * 19
            for zp in PILLARS_Z:
                a.set(xn, 69, zp, B("polished_blackstone_wall"))
                a.set(xn, 70, zp, B("soul_lantern"))
                a.set(xn, 66, zp, B("polished_blackstone_wall"))
                # banner over the colonnade wall above every opening
            for i in range(len(PILLARS_Z) - 1):
                zc = (PILLARS_Z[i] + PILLARS_Z[i + 1]) // 2
                xb = side * 19
                a.set(xb, 76, zc, B("wall_banner", facing_direction=5 if side < 0 else 4))
                a.add_be(banner_be(xb, 76, zc, 5, [("bri", 11), ("bo", 0), ("cbo", 11)]))
                a.set(xb, 78, zc, B("gold_block"))
                a.set(xb - side, 78, zc, B("crying_obsidian"))

    # ------------------------------------------------------------------
    def walls_decor(self):
        """Base course, pilasters, sconces and high windows on the outer walls."""
        a = self.a
        base = B("polished_blackstone_bricks")
        trim = B("chiseled_deepslate")
        pil = B("polished_deepslate")
        # base course (two blocks) wherever an outer wall meets the interior
        for x in range(-57, 58):
            for z in range(-47, 48):
                if a.get(x, P, z) != AIR:
                    continue
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, nz = x + dx, z + dz
                    if a.get(nx, P, nz) == B("deepslate_bricks") and (abs(nx) >= 58 or abs(nz) >= 48):
                        a.set(nx, P, nz, base)
                        a.set(nx, P + 1, nz, base)
                        a.set(nx, P + 2, nz, trim)
        # sconces + pilasters on the gallery-side south wall and north band side walls
        sconce_post = B("dark_oak_fence")
        lantern_h = B("lantern", hanging=1)
        soul_h = B("soul_lantern", hanging=1)
        # north band side walls (x = +-58) and its big windows
        for side in (-1, 1):
            xw = side * 58
            for z in range(-45, -32, 4):
                a.fill(xw, 78, z, xw, 89, z + 1, AIR)
                a.fill(xw + side, 78, z, xw + side, 89, z + 1, B("purple_stained_glass_pane"))
                a.set(xw, 77, z, B("polished_blackstone_bricks")); a.set(xw, 77, z + 1, B("polished_blackstone_bricks"))
                a.set(xw, 90, z, B("polished_blackstone_bricks")); a.set(xw, 90, z + 1, B("polished_blackstone_bricks"))
            for z in (-43, -39, -35):
                a.set(xw - side, 70, z, sconce_post)
                a.set(xw - side, 69, z, lantern_h)
        # south wall of the wings: tall windows
        for x in list(range(-54, -24, 6)) + list(range(26, 56, 6)):
            a.fill(x, 67, 48, x + 1, 74, 49, AIR)
            a.fill(x, 67, 49, x + 1, 74, 49, B("blue_stained_glass_pane"))
            a.fill(x, 67, 50, x + 1, 74, 50, B("blue_stained_glass_pane"))
            a.set(x, 66, 48, B("polished_blackstone_bricks")); a.set(x + 1, 66, 48, B("polished_blackstone_bricks"))
            a.set(x - 1, 70, 47, sconce_post); a.set(x - 1, 69, 47, soul_h)
        # wall above the wing openings facing the stage band (z = -30, y 76..92)
        for x in list(range(-54, -22, 8)) + list(range(26, 58, 8)):
            a.set(x, 84, -30, B("wall_banner", facing_direction=2))
            a.add_be(banner_be(x, 84, -30, 0, [("ss", 5), ("cbo", 11), ("flo", 11)]))
            a.set(x, 82, -31, sconce_post)
            a.set(x, 81, -31, soul_h)
        # pilasters along all interior walls every 9 blocks
        for x in range(-57, 58):
            for z in (-48, 48):
                if a.get(x, P + 3, z - (1 if z > 0 else -1)) == AIR and x % 9 == 0:
                    zi = z
                    top = 92 if z < 0 else 75
                    a.fill(x, P + 3, zi, x, top, zi, pil)

    # ------------------------------------------------------------------
    def stage(self):
        a = self.a
        top = B("polished_blackstone_bricks")
        edge = B("gilded_blackstone")
        a.fill(-14, P, -46, 14, P + 1, -37, top)
        for x in range(-14, 15):
            a.set(x, P, -36, stair("polished_blackstone_brick_stairs", "north"))
            # upper step row
            a.set(x, P + 1, -37, stair("polished_blackstone_brick_stairs", "north"))
            a.set(x, P, -37, top)
        for x in range(-14, 15):
            a.set(x, P + 1, -46, edge)
        for z in range(-46, -37):
            a.set(-14, P + 1, z, edge)
            a.set(14, P + 1, z, edge)
        # stage carpet
        for x in range(-11, 12):
            for z in range(-45, -38):
                a.set(x, P + 2, z, B("red_carpet") if abs(x) <= 1 or z in (-45, -39) or abs(x) == 11 else B("black_carpet"))
        # NPC pedestal
        a.set(0, P + 1, -41, B("lodestone"))
        a.set(0, P + 2, -41, AIR)
        self.markers.append((0, P + 1, -41, "lodestone"))
        self.npcs.append(dict(name="§l§e▶ 게임 시작 ◀", x=0.5, y=P + 2, z=-40.5, face=(0.5, P + 2, 0.5),
                              tag="start_npc", scene=None))
        # side braziers
        for x in (-10, 10):
            a.set(x, P + 2, -43, B("polished_blackstone_wall"))
            a.set(x, P + 3, -43, B("polished_blackstone_wall"))
            a.set(x, P + 4, -43, B("soul_campfire", cardinal="south"))
            a.add_be(simple_be("Campfire", x, P + 4, -43))
        # grand pillars + arch behind the NPC
        for x in (-13, 13):
            a.fill(x - 1, P + 2, -47, x + 1, 88, -46, B("polished_deepslate"))
            a.fill(x - 1, P + 2, -47, x + 1, P + 2, -46, B("polished_blackstone_bricks"))
            for y in (72, 80, 88):
                a.fill(x - 1, y, -47, x + 1, y, -46, B("chiseled_deepslate"))
            a.set(x, 76, -45, B("dark_oak_fence"))
            a.set(x, 75, -45, B("lantern", hanging=1))
        # rune circle on the wall behind the NPC (crying obsidian / amethyst)
        cy, cz = 70, -48
        for x in range(-7, 8):
            for y in range(cy - 7, cy + 8):
                d = math.sqrt(x * x + (y - cy) ** 2)
                if 5.5 <= d < 6.5:
                    a.set(x, y, cz, B("amethyst_block"))
                elif 4.5 <= d < 5.5:
                    a.set(x, y, cz, B("purpur_block") if (x + y) % 3 else B("crying_obsidian"))
                elif d < 4.5:
                    a.set(x, y, cz, B("obsidian"))
                elif 6.5 <= d < 7.3 and (abs(x) < 1 or abs(y - cy) < 1):
                    a.set(x, y, cz, B("gold_block"))
        a.set(0, cy, cz, B("crying_obsidian"))
        for (x, y) in ((0, cy + 3), (0, cy - 3), (3, cy), (-3, cy)):
            a.set(x, y, cz + 1, B("end_rod", facing_direction=3))
        # hanging sign above the NPC
        a.set(0, 75, -41, B("chain"))
        a.set(0, 74, -41, B("chain"))
        a.set(0, 73, -41, B("dark_oak_hanging_sign", hanging=1, attached_bit=1, ground_sign_direction=0))
        a.add_be(sign_be(0, 73, -41, "§l§e게임 시작\n§r§f여기를 눌러\n§f게임을 시작하세요", back="§l§e게임 시작", hanging=True))
        # spotlights in the band ceiling
        for x in (-6, 0, 6):
            a.set(x, 92, -40, B("ochre_froglight"))
        # large banners hanging from the band ceiling
        for x in (-30, -20, 20, 30):
            for y in range(86, 92):
                a.set(x, y, -46, B("chain"))
            a.set(x, 85, -46, B("standing_banner", ground_sign_direction=0))
            a.add_be(banner_be(x, 85, -46, 5, [("gra", 0), ("mc", 11), ("bo", 11)]))
        # long chandeliers across the stage band
        for x in (-46, -34, -22, 22, 34, 46):
            self.chandelier(x, 91, -39, 18, big=abs(x) == 34)
        # ability orbs on pedestals left and right of the stage
        for x, (c1, c2) in ((-28, ("purple_stained_glass", "magenta_stained_glass")),
                            (28, ("cyan_stained_glass", "light_blue_stained_glass"))):
            a.fill(x - 1, P, -40, x + 1, P + 1, -38, B("polished_blackstone_bricks"))
            a.set(x, P + 2, -39, B("polished_blackstone_wall"))
            a.set(x, P + 3, -39, B("polished_blackstone_wall"))
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    for dz in range(-2, 3):
                        d = (dx * dx + dy * dy + dz * dz) ** 0.5
                        if 1.2 < d <= 2.3:
                            a.set(x + dx, P + 6 + dy, -39 + dz, B(c1 if (dx + dy + dz) % 2 else c2))
            a.set(x, P + 6, -39, B("pearlescent_froglight", axis="y"))
            for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                a.set(x + dx, P + 2, -39 + dz, B("amethyst_cluster", face="up"))
            for dx in (-1, 1):
                a.set(x + dx, P + 2, -41, B("lantern"))
                a.set(x + dx, P + 2, -37, B("lantern"))
        # stage-corner lamp posts
        for x in (-14, 14):
            for z in (-46,):
                a.set(x, P + 2, z, B("polished_blackstone_wall"))
                a.set(x, P + 3, z, B("polished_blackstone_wall"))
                a.set(x, P + 4, z, B("lantern"))
        # floor light strips in the stage band
        for x in range(-56, 57, 4):
            if abs(x) > 15:
                a.set(x, FY, -32, B("ochre_froglight", axis="y"))

    # ------------------------------------------------------------------
    def title(self):
        """Pixel-art title '능력 술래잡기' on the north wall."""
        a = self.a
        f = ImageFont.truetype("/usr/share/fonts/opentype/unifont/unifont.otf", 16)
        text = "능력 술래잡기"
        l, t, r, b = f.getbbox(text)
        im = Image.new("1", (r + 2, 18), 0)
        ImageDraw.Draw(im).text((0, 0), text, font=f, fill=1)
        px = np.array(im)[2:16, : r]
        # bold: dilate horizontally
        bold = px.copy()
        bold[:, 1:] |= px[:, :-1]
        h, w = bold.shape
        x0 = -(w // 2)
        ytop = 90
        z = -48
        panel = B("polished_blackstone")
        a.fill(x0 - 3, ytop - h - 1, z, x0 + w + 2, ytop + 2, z, panel)
        for x in range(x0 - 3, x0 + w + 3):
            a.set(x, ytop + 2, z, B("gold_block"))
            a.set(x, ytop - h - 1, z, B("gold_block"))
        for y in range(ytop - h - 1, ytop + 3):
            a.set(x0 - 3, y, z, B("gold_block"))
            a.set(x0 + w + 2, y, z, B("gold_block"))
        glow = B("ochre_froglight", axis="y")
        shadow = B("purple_concrete")
        for row in range(h):
            for col in range(w):
                y = ytop - row
                x = x0 + col
                if bold[row, col]:
                    a.set(x, y, z, glow)
                elif row > 0 and col > 0 and bold[row - 1, col - 1]:
                    a.set(x, y, z, shadow)

    # ------------------------------------------------------------------
    def fountain(self):
        a = self.a
        fx, fz = FOUNTAIN
        rim = B("polished_blackstone_bricks")
        water = B("water")
        for x in range(fx - 9, fx + 10):
            for z in range(fz - 9, fz + 10):
                r = math.sqrt((x - fx) ** 2 + (z - fz) ** 2)
                if r < 7.5:
                    a.set(x, FY, z, B("dark_prismarine") if int(r * 1.3) % 2 else B("prismarine_bricks"))
                    a.set(x, P, z, water)
                    if 5.5 <= r < 6.5 and (x + z) % 3 == 0:
                        a.set(x, FY, z, B("sea_lantern"))
                elif r < 8.5:
                    a.set(x, P, z, rim)
                    a.set(x, FY, z, rim)
                    if (x + z) % 2 == 0:
                        a.set(x, P + 1, z, slab("polished_blackstone_brick_slab"))
        # central island: beacon on a gold pyramid
        for x in range(fx - 2, fx + 3):
            for z in range(fz - 2, fz + 3):
                a.set(x, P, z, B("polished_blackstone_bricks"))
        for x in range(fx - 1, fx + 2):
            for z in range(fz - 1, fz + 2):
                a.set(x, P, z, B("gold_block"))
        a.set(fx, P + 1, fz, B("beacon"))
        a.add_be(simple_be("Beacon", fx, P + 1, fz))
        # crystal column (transparent so the beam passes) + amethyst spikes
        for y in range(P + 2, P + 8):
            a.set(fx, y, fz, B("purple_stained_glass"))
        for y in range(P + 3, P + 7):
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if y < P + 6:
                    a.set(fx + dx, y, fz + dz, B("magenta_stained_glass"))
        a.set(fx, P + 8, fz, B("magenta_stained_glass"))
        for k in range(4):
            ang = k * math.pi / 2 + math.pi / 4
            for i in range(1, 4):
                x = fx + round(math.cos(ang) * (1 + i * 0.8))
                z = fz + round(math.sin(ang) * (1 + i * 0.8))
                a.set(x, P + i, z, B("amethyst_block"))
            x = fx + round(math.cos(ang) * 4.2)
            z = fz + round(math.sin(ang) * 4.2)
            a.set(x, P + 4, z, B("amethyst_cluster", face="up"))
        # floating halo ring
        for k in range(16):
            ang = k * math.pi / 8
            x = fx + round(math.cos(ang) * 4)
            z = fz + round(math.sin(ang) * 4)
            if k % 2 == 0:
                a.set(x, P + 9, z, B("end_rod", facing_direction=1))
        # benches + lamps around the plaza
        for k in range(8):
            ang = k * math.pi / 4 + math.pi / 8
            x = fx + round(math.cos(ang) * 12.5)
            z = fz + round(math.sin(ang) * 12.5)
            lamp_post(a, x, P, z, B("polished_blackstone_wall"), B("lantern"), height=3)
        for (bx, bz, d) in ((fx, fz - 11, "north"), (fx, fz + 11, "south"), (fx - 11, fz, "west"), (fx + 11, fz, "east")):
            if abs(bx) <= 1 and d in ("north", "south"):
                continue   # carpet runner
            for o in (-1, 0, 1):
                x = bx + (o if d in ("north", "south") else 0)
                z = bz + (o if d in ("east", "west") else 0)
                a.set(x, P, z, stair("dark_oak_stairs", d))

    # ------------------------------------------------------------------
    def chandelier(self, x, ytop, z, length, big=False):
        a = self.a
        for i in range(length):
            a.set(x, ytop - i, z, B("chain"))
        y = ytop - length
        arm = B("dark_oak_fence")
        a.set(x, y, z, B("polished_blackstone"))
        r = 3 if big else 2
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for i in range(1, r + 1):
                a.set(x + dx * i, y, z + dz * i, arm)
            a.set(x + dx * r, y + 1, z + dz * r, B("lantern"))
            a.set(x + dx * r, y - 1, z + dz * r, B("lantern", hanging=1))
        a.set(x, y - 1, z, B("lantern", hanging=1))
        if big:
            for dx, dz in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
                a.set(x + dx, y, z + dz, arm)
                a.set(x + dx, y - 1, z + dz, B("soul_lantern", hanging=1))

    def chandeliers(self):
        for z in (-24, 37):
            self.chandelier(0, vault_top(0), z, 12, big=True)
        for z in (-24, 37, 44):
            for x in (-12, 12):
                self.chandelier(x, vault_top(x), z, 8)

    # ------------------------------------------------------------------
    def shop(self):
        a = self.a
        # aisle lanterns
        for z in range(-27, 47, 6):
            hanging_lamp(a, -43, 75, z, 6)
        # shop street entrance arches (north and south ends of the aisle)
        for zg, face in ((-29, 2), (46, 3)):
            for x in (-50, -36):
                a.fill(x, P, zg, x, 74, zg, B("dark_oak_log"))
            a.fill(-50, 73, zg, -36, 74, zg, B("stripped_dark_oak_log", axis="x"))
            a.set(-43, 72, zg, B("chain"))
            a.set(-43, 71, zg, B("dark_oak_hanging_sign", hanging=1, attached_bit=1, ground_sign_direction=0 if face == 3 else 8))
            a.add_be(sign_be(-43, 71, zg, "§l§6★ 능력 상점 ★\n§r§f원하는 능력을\n§f구매하세요!", back="§l§6★ 능력 상점 ★\n§r§f원하는 능력을\n§f구매하세요!", hanging=True))
            for x in (-49, -37):
                a.set(x, 72, zg, B("lantern", hanging=1))
        # lamp posts at the aisle edges, between stalls
        for z in (-28, -12, 6, 24, 42):
            for x in (-49, -37):
                lamp_post(a, x, P, z, B("polished_blackstone_wall"), B("lantern"), height=2)
        for i, ab in enumerate(ABILITIES):
            zc = STALL_Z[i % 4]
            if i < 4:
                self.stall(ab, zc, back_x=-57, face=+1)
            else:
                self.stall(ab, zc, back_x=-29, face=-1)
        # strip between freestanding stalls and colonnade: planters + benches
        for zc in STALL_Z:
            for dz in (-4, 4):
                z = zc + dz
                a.set(-25, P, z, B("dark_oak_planks"))
                a.set(-25, P + 1, z, B("azalea_leaves_flowered", persistent_bit=1))
                a.set(-24, P, z, stair("dark_oak_stairs", "west"))
        for z in (-12, 6, 24, 41):
            a.set(-25, P, z, B("polished_blackstone_wall"))
            a.set(-25, P + 1, z, B("polished_blackstone_wall"))
            a.set(-25, P + 2, z, B("lantern"))

    THEMES = {
        "speed": dict(awn=("light_blue_wool", "white_wool"), wall="light_blue_glazed_terracotta",
                      wall2="light_blue_concrete", floor="blue_ice", lamp="soul_lantern", glow="sea_lantern",
                      banner=12),
        "jump": dict(awn=("lime_wool", "white_wool"), wall="lime_concrete", wall2="slime",
                     floor="moss_block", lamp="lantern", glow="verdant_froglight", banner=10),
        "invis": dict(awn=("light_gray_wool", "white_wool"), wall="tinted_glass", wall2="white_stained_glass",
                      floor="smooth_quartz", lamp="soul_lantern", glow="pearlescent_froglight", banner=7),
        "feather": dict(awn=("pink_wool", "white_wool"), wall="white_wool", wall2="pink_stained_glass",
                        floor="white_concrete", lamp="lantern", glow="pearlescent_froglight", banner=9),
        "owl": dict(awn=("blue_wool", "black_wool"), wall="blue_concrete", wall2="amethyst_block",
                    floor="deepslate_tiles", lamp="soul_lantern", glow="sea_lantern", banner=4),
        "mermaid": dict(awn=("cyan_wool", "white_wool"), wall="prismarine_bricks", wall2="dark_prismarine",
                        floor="prismarine", lamp="lantern", glow="sea_lantern", banner=6),
        "berserk": dict(awn=("red_wool", "orange_wool"), wall="red_nether_brick", wall2="magma",
                        floor="red_concrete", lamp="lantern", glow="shroomlight", banner=1),
        "hunter": dict(awn=("brown_wool", "black_wool"), wall="spruce_planks", wall2="target",
                       floor="coarse_dirt", lamp="lantern", glow="shroomlight", banner=3),
    }

    def stall(self, ab, zc, back_x, face):
        """Market stall, 7 deep (x) x 13 long (z). face=+1 opens to +x, -1 opens to -x."""
        a = self.a
        th = self.THEMES[ab["key"]]
        X = lambda d: back_x + face * d           # d = 0 (back) .. 6 (front)
        z1, z2 = zc - 6, zc + 6
        frame = B("dark_oak_log")
        plank = B("dark_oak_planks")
        # back wall (for freestanding stalls build one), side walls
        if face < 0:
            a.fill(X(0), P, z1, X(0), 70, z2, plank)
            a.fill(X(0) + 1, P, z1, X(0) + 1, 70, z2, B("spruce_planks"))   # rear facade
            a.fill(X(0) + 1, P, z1 + 1, X(0) + 1, P + 1, z2 - 1, B("barrel", facing_direction=1))
        a.fill(X(1), 66, z1 + 1, X(1), 69, z2 - 1, B(th["wall"]))
        for z in range(z1 + 2, z2 - 1, 3):
            a.fill(X(1), 66, z, X(1), 69, z, B(th["wall2"]))
        a.fill(X(1), P, z1 + 1, X(1), P + 1, z2 - 1, B("dark_oak_planks"))
        for z in (z1, z2):
            a.fill(X(0), P, z, X(5), 70, z, plank)
            a.fill(X(6), P, z, X(6), 70, z, frame)
            a.fill(X(0), P, z, X(0), 70, z, frame)
        # floor inside
        for d in range(1, 6):
            a.fill(X(d), FY, z1 + 1, X(d), FY, z2 - 1, B(th["floor"]))
        # counter
        cnt = B("stripped_dark_oak_log", axis="z")
        for z in range(z1 + 1, z2):
            a.set(X(4), P, z, cnt)
            a.set(X(4), P + 1, z, slab("dark_oak_slab"))
        a.set(X(4), P + 1, zc - 3, B("brewing_stand"))
        a.add_be(simple_be("BrewingStand", X(4), P + 1, zc - 3))
        a.set(X(4), P + 1, zc + 3, B("flower_pot"))
        a.add_be(flowerpot_be(X(4), P + 1, zc + 3, "allium" if face > 0 else "blue_orchid"))
        a.set(X(4), P + 1, zc + 4, B(th["lamp"]))
        a.set(X(4), P + 1, zc - 4, B(th["lamp"]))
        # NPC behind counter, on a lodestone marker
        a.set(X(3), FY, zc, B("lodestone"))
        self.markers.append((X(3), FY, zc, "lodestone"))
        yaw_face = (X(3) + face * 5 + 0.5, P, zc + 0.5)
        self.npcs.append(dict(name="%s§l%s §r§7상인" % (ab["color"], ab["name"]), x=X(3) + 0.5, y=P, z=zc + 0.5,
                              face=yaw_face, tag="shop_%s" % ab["key"], scene="shop_%s" % ab["key"]))
        # roof / striped awning
        a.fill(X(0), 71, z1, X(6), 71, z2, plank)
        c1, c2 = B(th["awn"][0]), B(th["awn"][1])
        for z in range(z1, z2 + 1):
            c = c1 if (z - z1) % 2 == 0 else c2
            a.set(X(6), 71, z, c)
            a.set(X(7), 70, z, c)
            a.set(X(8), 69, z, c)
        for z in range(z1 + 2, z2 - 1, 4):
            a.set(X(7), 69, z, B(th["lamp"], hanging=1))
        # ceiling light inside the stall
        a.set(X(2), 70, zc, B(th["glow"]) if "froglight" not in th["glow"] else B(th["glow"], axis="y"))
        a.set(X(2), 70, zc - 4, B(th["glow"]) if "froglight" not in th["glow"] else B(th["glow"], axis="y"))
        a.set(X(2), 70, zc + 4, B(th["glow"]) if "froglight" not in th["glow"] else B(th["glow"], axis="y"))
        # name board above the awning
        a.fill(X(5), 72, zc - 3, X(5), 73, zc + 3, B("dark_oak_planks"))
        a.fill(X(5), 74, zc - 3, X(5), 74, zc + 3, slab("dark_oak_slab"))
        fd = 5 if face > 0 else 4
        wall_sign(a, X(6), 73, zc, fd, "%s§l%s\n§r§6가격: §e%d 코인" % (ab["color"], ab["name"], ab["price"]),
                  kind="dark_oak_wall_sign")
        wall_sign(a, X(6), 72, zc, fd, "§f%s" % ab["desc"], kind="dark_oak_wall_sign")
        for dz in (-2, 2):
            a.set(X(6), 72, zc + dz, B("wall_banner", facing_direction=fd))
            a.add_be(banner_be(X(6), 72, zc + dz, th["banner"], [("bo", 15), ("mc", 15)]))
        # theme props
        k = ab["key"]
        if k == "speed":
            for z in (z1 + 1, z2 - 1):
                a.set(X(1), P + 2, z, B("blue_ice"))
                a.set(X(2), P, z, B("packed_ice"))
            for z in range(z1 + 2, z2 - 1, 2):
                a.set(X(1), 70, z, B("end_rod", facing_direction=0))
        elif k == "jump":
            for z in (z1 + 1, z2 - 1):
                a.set(X(2), P, z, B("slime"))
                a.set(X(2), P + 1, z, B("slime"))
                a.set(X(3), P, z, B("slime"))
        elif k == "invis":
            for z in (z1 + 1, z2 - 1):
                a.set(X(2), P, z, B("glass"))
                a.set(X(2), P + 1, z, B("glass"))
                a.set(X(2), P + 2, z, B("tinted_glass"))
            a.set(X(1), 70, z1 + 1, B("web"))
            a.set(X(1), 70, z2 - 1, B("web"))
        elif k == "feather":
            for z in (z1 + 1, z2 - 1):
                a.set(X(2), P, z, B("white_wool"))
                a.set(X(3), P, z, B("white_carpet"))
            for z in range(z1 + 1, z2):
                if self.rng.random() < 0.5:
                    if a.get(X(2), P, z) == AIR:
                        a.set(X(2), P, z, B("pink_petals", growth=3, cardinal=self.rng.choice(["north", "south", "east", "west"])))
        elif k == "owl":
            for z in (z1 + 1, z2 - 1):
                a.set(X(2), P, z, B("amethyst_block"))
                a.set(X(2), P + 1, z, B("amethyst_cluster", face="up"))
            a.set(X(1), 68, zc - 2, B("sea_lantern")); a.set(X(1), 68, zc + 2, B("sea_lantern"))
        elif k == "mermaid":
            # aquarium tanks on both ends
            for z in (z1 + 1, z2 - 1):
                for y in (P, P + 1, P + 2):
                    a.set(X(2), y, z, B("glass"))
                a.set(X(3), P, z, B("glass"))
            a.set(X(1), P + 2, zc, B("water"))
            a.setw(X(1), P + 2, zc, B("sea_pickle", cluster_count=3, dead_bit=0))
            for dz in (-2, 2):
                a.set(X(1), P + 2, zc + dz, B("water"))
                a.setw(X(1), P + 2, zc + dz, B("tube_coral" if dz < 0 else "brain_coral"))
            a.fill(X(1), P + 3, zc - 3, X(1), P + 3, zc + 3, B("glass"))
            a.fill(X(1), P + 2, zc - 3, X(1), P + 2, zc - 3, B("glass"))
            a.fill(X(1), P + 2, zc + 3, X(1), P + 2, zc + 3, B("glass"))
            for z in (zc - 1, zc + 1):
                a.set(X(1), P + 2, z, B("water"))
                a.setw(X(1), P + 2, z, B("seagrass"))
        elif k == "berserk":
            for z in (z1 + 1, z2 - 1):
                a.set(X(2), P, z, B("lit_furnace", cardinal="east" if face > 0 else "west"))
                a.set(X(2), P + 1, z, B("redstone_block"))
            a.set(X(1), P + 2, zc, B("magma"))
        elif k == "hunter":
            for z in (z1 + 1, z2 - 1):
                a.set(X(2), P, z, B("hay_block"))
                a.set(X(2), P + 1, z, B("target"))
            a.set(X(1), P + 3, zc, B("skeleton_skull", facing_direction=5 if face > 0 else 4))
            a.add_be(simple_be("Skull", X(1), P + 3, zc, SkullType=__import__("amulet_nbt").ByteTag(0),
                               Rotation=__import__("amulet_nbt").FloatTag(0.0)))

    # ------------------------------------------------------------------
    def gallery(self):
        a = self.a
        maps = [
            ("forest", "§l§a1. 숲", "§f울창한 숲과 세계수"),
            ("volcano", "§l§c2. 화산", "§f용암이 흐르는 화산지대"),
            ("paradise", "§l§b3. 파라다이스", "§f에메랄드빛 낙원 섬"),
            ("factory", "§l§74. 공장", "§f거대한 산업 단지"),
            ("skeld", "§l§c5. 더 스켈드", "§f어몽어스 우주선"),
            ("library", "§l§66. 대도서관", "§f돔 원형홀 도서관"),
        ]
        for (key, title, sub), zc in zip(maps, GATE_Z):
            self.diorama(key, zc)
            self.gate(key, zc, title, sub)
        # gallery lounge: benches, plants, lamps
        for zc in GATE_Z:
            # sofa (stairs facing the gate) + table
            for dz in (-2, -1, 0, 1, 2):
                a.set(46, P, zc + dz, stair("dark_oak_stairs", "west"))
            a.set(43, P, zc, B("dark_oak_fence"))
            a.set(43, P + 1, zc, B("dark_oak_fence"))
            a.set(43, P + 2, zc, slab("dark_oak_slab"))
            a.set(43, P + 3, zc, B("lantern"))
            for dz in (-4, 4):
                a.set(46, P, zc + dz, B("flower_pot"))
                a.add_be(flowerpot_be(46, P, zc + dz, "fern"))
            # carpet rug
            for x in range(40, 48):
                for dz in range(-3, 4):
                    if a.get(x, P, zc + dz) == AIR:
                        a.set(x, P, zc + dz, B("purple_carpet") if (x in (40, 47) or dz in (-3, 3)) else B("black_carpet"))
        for z in range(-27, 47, 6):
            hanging_lamp(a, 34, 75, z, 6)
            hanging_lamp(a, 26, 75, z + 3, 7)
            hanging_lamp(a, 52, 75, z + 3, 6)
        # notice board on the gallery south wall
        a.fill(36, P + 1, 47, 50, P + 5, 47, B("dark_oak_planks"))
        a.fill(36, P + 6, 47, 50, P + 6, 47, B("stripped_dark_oak_log", axis="x"))
        a.fill(36, P, 47, 50, P, 47, B("stripped_dark_oak_log", axis="x"))
        notes = [
            "§l§e술래잡기 규칙\n§r§f술래에게 잡히지\n§f않고 버티세요!",
            "§l§b능력\n§r§f상점에서 1개를\n§f장착할 수 있어요",
            "§l§a코인\n§r§f처음 입장 시\n§f200 코인 지급",
            "§l§d맵 이동\n§r§f핫바의 이동 아이템을\n§f우클릭하세요",
            "§l§c주의\n§r§f맵 밖으로는\n§f나갈 수 없어요",
        ]
        for i, t in enumerate(notes):
            wall_sign(a, 37 + i * 3, P + 3, 46, 2, t, kind="dark_oak_wall_sign")
        for x in (35, 51):
            lamp_post(a, x, P, 46, B("dark_oak_fence"), B("lantern"), height=3)
        # big planters with mini trees in the gallery centre line
        for z in (-12, 6, 24):
            a.fill(27, P, z - 1, 29, P, z + 1, B("polished_blackstone_bricks"))
            a.fill(28, P, z, 28, P, z, B("moss_block"))
            for i in range(1, 4):
                a.set(28, P + i, z, B("cherry_log", axis="y"))
            leaf_blob(a, 28, P + 4.5, z, 2.4, leaves_of("cherry"), self.rng, flat=0.7)
        # sign board in the gallery
        a.set(31, P, 41, B("dark_oak_planks"))
        standing_sign(a, 31, P + 1, 41, 8, "§l§b맵 갤러리\n§r§f게임 맵 6곳을\n§f미리 구경하세요", kind="dark_oak_standing_sign")

    def gate(self, key, zc, title, sub):
        a = self.a
        styles = {
            "forest": (B("mossy_stone_bricks"), B("oak_log"), B("oak_leaves", persistent_bit=1)),
            "volcano": (B("polished_blackstone_bricks"), B("magma"), B("red_nether_brick")),
            "paradise": (B("prismarine_bricks"), B("smooth_sandstone"), B("sea_lantern")),
            "factory": (B("iron_block"), B("polished_deepslate"), B("copper_block")),
            "skeld": (B("light_gray_concrete"), B("black_concrete"), B("red_concrete")),
            "library": (B("dark_oak_planks"), B("bookshelf"), B("gold_block")),
        }
        main, accent, trim = styles[key]
        x = 57
        # frame on the inner wall face (x=57 column is interior; build frame protruding 1)
        for dz in range(-6, 7):
            for y in range(P, 75):
                inner = abs(dz) <= 4 and y <= 72
                if not inner:
                    a.set(x, y, zc + dz, main if (abs(dz) == 5 or y in (73, 74)) else accent)
        for y in range(P, 74):
            a.set(x, y, zc - 6, accent)
            a.set(x, y, zc + 6, accent)
        for dz in range(-6, 7):
            a.set(x, 74, zc + dz, trim)
        # glass window into the diorama
        a.fill(58, P, zc - 4, 58, 72, zc + 4, B("glass"))
        # arch top
        for dz in (-4, 4):
            a.set(x, 72, zc + dz, main)
        for dz in (-3, 3):
            st_name = {"forest": "mossy_stone_brick_stairs", "volcano": "polished_blackstone_brick_stairs",
                       "paradise": "prismarine_bricks_stairs", "factory": "polished_deepslate_stairs",
                       "skeld": "polished_andesite_stairs", "library": "dark_oak_stairs"}[key]
            a.set(x, 72, zc + dz, stair(st_name, "south" if dz < 0 else "north", upside=True))
        # signs
        a.set(x, P + 3, zc - 5, main)
        wall_sign(a, 56, P + 3, zc - 5, 4, "%s\n%s" % (title, sub), kind="dark_oak_wall_sign")
        wall_sign(a, 56, P + 3, zc + 5, 4, "%s\n§7(맵 미리보기)" % title, kind="dark_oak_wall_sign")
        # floor lights in front
        glow = {"paradise": B("sea_lantern"), "volcano": B("ochre_froglight", axis="y"),
                "forest": B("verdant_froglight", axis="y"), "factory": B("pearlescent_froglight", axis="y"),
                "skeld": B("sea_lantern"), "library": B("ochre_froglight", axis="y")}[key]
        for dz in (-3, 0, 3):
            a.set(56, FY, zc + dz, glow)

    def diorama(self, key, zc):
        a = self.a
        rng = random.Random(zc * 31 + 5)
        x1, x2 = 59, 70
        z1, z2 = zc - 5, zc + 5
        a.fill(58, FY - 2, z1 - 2, 73, 76, z2 + 2, B("deepslate_bricks"))
        a.fill(x1, P, z1, x2, 73, z2, AIR)
        # sky-ish back wall and ceiling light
        sky = {"forest": B("light_blue_concrete"), "volcano": B("orange_terracotta"),
               "paradise": B("light_blue_concrete"), "factory": B("light_gray_concrete"),
               "skeld": B("black_concrete"), "library": B("dark_oak_planks")}[key]
        a.fill(71, P, z1, 71, 73, z2, sky)
        a.fill(x1, 74, z1, x2, 74, z2, B("glowstone") if key not in ("factory", "skeld") else B("sea_lantern"))
        a.fill(x1, 73, z1, x2, 73, z2, AIR)
        if key == "forest":
            a.fill(x1, FY, z1, x2, FY, z2, B("grass_block"))
            a.fill(x1, FY - 1, z1, x2, FY - 1, z2, B("dirt"))
            for z in range(z1, z2 + 1):
                a.set(65, FY, z, B("water"))
            a.set(65, P, zc, B("spruce_slab"))
            for (tx, tz) in ((61, z1 + 2), (68, z2 - 2), (69, z1 + 1)):
                oak_tree(a, tx, P, tz, rng, h=4)
            spruce_tree(a, 62, P, z2 - 1, rng, h=6)
            for _ in range(14):
                x, z = rng.randint(x1, x2), rng.randint(z1, z2)
                if a.get(x, FY, z) == B("grass_block") and a.get(x, P, z) == AIR:
                    a.set(x, P, z, B(rng.choice(FLOWERS + ["short_grass", "fern", "short_grass"])))
            a.set(67, P, zc + 1, B("mossy_cobblestone"))
            lamp_post(a, 63, P, zc, B("spruce_fence"), B("lantern"), height=1)
        elif key == "volcano":
            a.fill(x1, FY, z1, x2, FY, z2, B("blackstone"))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    d = math.sqrt((x - 67) ** 2 + (z - zc) ** 2)
                    h = int(max(0, 6.5 - d * 1.2))
                    for y in range(P, P + h):
                        a.set(x, y, z, B("basalt") if rng.random() < 0.6 else B("blackstone"))
                    if rng.random() < 0.15 and h == 0:
                        a.set(x, FY, z, B("magma"))
            for y in range(P, P + 7):
                a.set(67, y, zc, AIR)
            a.set(67, FY, zc, B("lava"))
            a.set(67, P + 5, zc, B("lava"))
            for z in range(z1, z1 + 3):
                for x in range(x1, x1 + 4):
                    a.set(x, FY, z, B("lava"))
            for (x, z) in ((61, z2 - 1), (62, z2 - 2)):
                a.set(x, P, z, B("netherrack"))
                a.set(x, P + 1, z, B("fire", age=0))
            a.set(60, P, zc, B("campfire", cardinal="east"))
            a.add_be(simple_be("Campfire", 60, P, zc))
        elif key == "paradise":
            a.fill(x1, FY, z1, x2, FY, z2, B("sand"))
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    if x <= 63:
                        a.set(x, FY, z, B("water"))
                        a.set(x, FY - 1, z, B("sand"))
            a.setw(60, FY, zc, B("brain_coral"))
            a.setw(61, FY, zc + 2, B("sea_pickle", cluster_count=3))
            a.setw(62, FY, zc - 2, B("fire_coral"))
            palm_tree(a, 67, P, zc, rng, h=6)
            for (x, z) in ((69, z1 + 1), (69, z2 - 1), (65, z2)):
                a.set(x, P, z, B(rng.choice(["allium", "blue_orchid", "pink_tulip", "oxeye_daisy"])))
            a.set(66, P, z1 + 1, B("red_wool"))
            a.set(66, P + 1, z1 + 1, B("bamboo_fence"))
        elif key == "factory":
            a.fill(x1, FY, z1, x2, FY, z2, B("gray_concrete"))
            for z in range(z1, z2 + 1):
                a.set(64, FY, z, B("yellow_concrete") if z % 2 else B("black_concrete"))
            for y in range(P, P + 8):
                a.set(68, y, zc + 2, B("brick_block"))
            a.set(68, P + 8, zc + 2, B("campfire"))
            a.add_be(simple_be("Campfire", 68, P + 8, zc + 2))
            for x in range(60, 67):
                a.set(x, P + 3, zc - 3, B("copper_block"))
            a.set(60, P, zc - 3, B("copper_block")); a.set(60, P + 1, zc - 3, B("copper_block")); a.set(60, P + 2, zc - 3, B("copper_block"))
            for (x, z, c) in ((61, z2 - 1, "orange_concrete"), (62, z2 - 1, "orange_concrete"), (61, z2 - 2, "blue_concrete")):
                a.set(x, P, z, B(c))
            a.set(66, P, zc, B("iron_block")); a.set(66, P + 1, zc, B("iron_block"))
            a.set(66, P + 2, zc, B("copper_bulb", lit=1))
        elif key == "skeld":
            # deep space with stars, a little spaceship and a crewmate
            a.fill(x1, FY, z1, x2, FY, z2, B("black_concrete"))
            for _ in range(26):
                x, y, z = 71, rng.randint(P, 72), rng.randint(z1, z2)
                a.set(x, y, z, B("glowstone") if rng.random() < 0.5 else B("sea_lantern"))
            for _ in range(10):
                a.set(rng.randint(x1, x2), FY, rng.randint(z1, z2), B("sea_lantern"))
            for x in range(61, 70):
                for z in range(zc - 3, zc + 4):
                    for y in range(P + 1, P + 4):
                        if ((x - 65.5) / 4.6) ** 2 + ((z - zc) / 3.4) ** 2 + ((y - (P + 2)) / 1.6) ** 2 <= 1:
                            a.set(x, y, z, B("light_gray_concrete"))
            for z in (zc - 1, zc + 1):
                a.set(60, P + 2, z, B("orange_stained_glass"))
                a.set(61, P + 2, z, B("ochre_froglight", axis="x"))
            a.set(69, P + 2, zc, B("light_blue_stained_glass"))
            a.set(66, P + 4, zc, B("red_concrete"))
            a.set(66, P + 5, zc, B("red_concrete"))
            a.set(65, P + 5, zc, B("light_blue_stained_glass"))
            a.set(67, P + 4, zc, B("red_concrete"))
            for x in range(62, 70):
                a.set(x, P, zc, B("iron_bars") if x in (65, 66) else AIR)
        elif key == "library":
            # a little library: shelves, a domed reading room and a globe
            for x in range(x1, x2 + 1):
                for z in range(z1, z2 + 1):
                    a.set(x, FY, z, B("dark_oak_planks") if (x + z) % 2 else B("spruce_planks"))
            for x in range(x1, x2 + 1, 2):
                for z in (z1, z2):
                    for y in range(P, P + 3):
                        a.set(x, y, z, B("bookshelf"))
            for x in range(61, 70):
                for z in range(zc - 4, zc + 5):
                    d = math.sqrt((x - 65) ** 2 + (z - zc) ** 2)
                    if 3.5 <= d < 4.5:
                        for y in range(P, P + 3):
                            a.set(x, y, z, B("bookshelf") if (x + z) % 3 else B("stripped_dark_oak_log", axis="y"))
            for x in range(60, 71):
                for z in range(zc - 5, zc + 6):
                    for y in range(P + 3, P + 9):
                        d = math.sqrt((x - 65) ** 2 + (z - zc) ** 2 + (y - (P + 3)) ** 2)
                        if 4.0 <= d < 5.0:
                            a.set(x, y, z, B("waxed_oxidized_cut_copper") if d > 4.5 else B("quartz_bricks"))
            for x in range(63, 68):
                for z in range(zc - 2, zc + 3):
                    if (x - 65) ** 2 + (z - zc) ** 2 <= 4:
                        a.set(x, P + 1, z, B("blue_concrete") if (x + z) % 3 else B("lime_concrete"))
            a.set(65, P, zc, B("gold_block"))
            a.set(65, P + 2, zc, B("green_concrete"))
            for z in (zc - 4, zc + 4):
                a.set(60, P, z, B("dark_oak_fence"))
                a.set(60, P + 1, z, B("lantern"))

    # ------------------------------------------------------------------
    def foyer(self):
        a = self.a
        # spawn compass rose
        sx, _, sz = SPAWN
        for x in range(sx - 4, sx + 5):
            for z in range(sz - 4, sz + 5):
                r = math.sqrt((x - sx) ** 2 + (z - sz) ** 2)
                if r < 4.5:
                    if x == sx or z == sz:
                        a.set(x, FY, z, B("gold_block") if r < 3.5 else B("gilded_blackstone"))
                    elif abs(x - sx) == abs(z - sz):
                        a.set(x, FY, z, B("polished_blackstone_bricks"))
                    else:
                        a.set(x, FY, z, B("polished_deepslate"))
                    if a.get(x, P, z) == B("red_carpet"):
                        a.set(x, P, z, AIR)
        # decorative iron double door in the south wall
        for x in (-1, 0, 1):
            a.fill(x, P, 48, x, P + 4, 48, B("polished_blackstone_bricks"))
        a.set(-1, P, 48, B("iron_door", cardinal="north", upper_block_bit=0, door_hinge_bit=0))
        a.set(-1, P + 1, 48, B("iron_door", cardinal="north", upper_block_bit=1, door_hinge_bit=0))
        a.set(0, P, 48, B("iron_door", cardinal="north", upper_block_bit=0, door_hinge_bit=1))
        a.set(0, P + 1, 48, B("iron_door", cardinal="north", upper_block_bit=1, door_hinge_bit=1))
        a.fill(-3, P + 3, 47, 2, P + 3, 47, B("polished_blackstone_brick_wall"))
        for x in (-3, 2):
            a.set(x, P + 2, 47, B("lantern"))
        # welcome + rules boards
        for (x, rot) in ((-7, 8), (6, 8)):
            a.set(x, P, 44, B("polished_blackstone_bricks"))
        standing_sign(a, -7, P + 1, 44, 8, "§l§d능력 술래잡기\n§r§f에 오신 것을\n§f환영합니다!", kind="dark_oak_standing_sign")
        standing_sign(a, 6, P + 1, 44, 8, "§l§6게임 방법\n§r§f상점에서 능력 구매\n§f→ 무대 NPC에서 시작", kind="dark_oak_standing_sign")
        wall_sign(a, -4, P + 1, 47, 2, "§l§e코인 안내\n§r§f처음 입장 시 200코인\n§f상인을 눌러 구매", kind="dark_oak_wall_sign")
        wall_sign(a, 3, P + 1, 47, 2, "§l§b← 능력 상점\n§l§a맵 갤러리 →\n§l§e↑ 게임 시작", kind="dark_oak_wall_sign")
        # big potted trees flanking the foyer
        for x in (-12, 12):
            a.fill(x - 1, P, 42, x + 1, P, 44, B("polished_blackstone_bricks"))
            a.set(x, P, 43, B("moss_block"))
            for i in range(1, 6):
                a.set(x, P + i, 43, B("dark_oak_log"))
            leaf_blob(a, x, P + 6.5, 43, 3.2, B("azalea_leaves_flowered", persistent_bit=1), self.rng, flat=0.7,
                      extra=B("azalea_leaves", persistent_bit=1), extra_chance=0.5)
        # floor uplights along the runner
        for z in range(16, 46, 5):
            for x in (-3, 3):
                a.set(x, FY, z, B("ochre_froglight", axis="y"))
        for z in range(-33, -12, 5):
            for x in (-3, 3):
                a.set(x, FY, z, B("ochre_froglight", axis="y"))


def build_lobby():
    lb = Lobby()
    area = lb.build()
    return lb, area
