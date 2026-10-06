"""Residential island (the paradise lagoon map): house plots for sale + the plot office.

Every plot is 17x17: a 15x15 interior over a hidden layer of allow blocks (adventure players may build
there) and a 1-block ring with border blocks 4 deep under it (the invisible border wall nobody passes).
Owners get in and out with the buttons on the entry post; anyone found inside somebody else's plot can only
have got there by cheating and is banned by the script.
"""
import math
import random

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt

from mcw import B, AIR, simple_be, sign_be
from gen_common import (stair, slab, lamp_post, wall_sign, standing_sign, clamp_gradient, cherry_tree, bush,
                        leaves_of, FLOWERS)
from gen_paradise import WL
from gen_mapbase import SIZE
from sky_islands import SkyParadise

PLOT = 17                # footprint incl. ring
PITCH = 21               # 4-wide paths between plots
GP = 68                  # plot ground surface y
DEPTH = 4                # allow / border layer at GP - DEPTH
BUILD_UP = 24            # owners may build up to GP + BUILD_UP
PRICE_VIEW, PRICE_STD = 4000, 2500
PLAZA = (-26, -104, 26, -74)     # local box kept free for the arrival plaza and the office


class ResidentialIsland(SkyParadise):
    """Paradise with a flat plot district around the lagoon."""

    def terrain(self):
        super().terrain()
        land = (self.water == 0) & (self.D < self.R + 6)
        self.district = (self.sea_d >= 8) & (self.D <= self.R - 1) & land
        # flat district; around it the ground ramps down one block per block of distance (no ledges)
        dd = distance_transform_edt(~self.district)
        ramp = np.minimum(np.maximum(self.H, np.round(GP - dd).astype(np.int32)), GP)
        self.H = np.where(self.district, GP, np.where(land, ramp, self.H))
        self.top[self.district] = B("grass_block")
        # nothing grows in the district: plots and paths go there
        self.reserved |= self.district


def plan_plots(m):
    """Grid of 17x17 plots that fit inside the district (local coords of the north-west ring corner)."""
    ok = binary_erosion(m.district, iterations=1)
    plots = []
    for j in range(0, 10):
        for i in range(-5, 5):
            x0 = 2 + PITCH * i
            z0 = -97 + PITCH * j
            if x0 + PLOT - 1 >= PLAZA[0] and x0 <= PLAZA[2] and z0 <= PLAZA[3] and z0 + PLOT - 1 >= PLAZA[1]:
                continue
            ii = x0 + m.cx - m.a.x0
            kk = z0 + m.cz - m.a.z0
            if ii < 0 or kk < 0 or ii + PLOT > SIZE or kk + PLOT > SIZE:
                continue
            if not ok[ii:ii + PLOT, kk:kk + PLOT].all():
                continue
            plots.append(dict(gi=i, gj=j, lx=x0, lz=z0))
    return plots


def build_plots(m, plots):
    a = m.a
    rng = random.Random(77)
    lag = (0, 14)
    out = []
    for n, p in enumerate(plots, 1):
        x0, z0 = m.cx + p["lx"], m.cz + p["lz"]
        x1, z1 = x0 + PLOT - 1, z0 + PLOT - 1
        # front side: the one facing the lagoon centre
        pcx, pcz = p["lx"] + PLOT // 2, p["lz"] + PLOT // 2
        vx, vz = lag[0] - pcx, lag[1] - pcz
        if abs(vx) > abs(vz):
            front = "E" if vx > 0 else "W"
        else:
            front = "S" if vz > 0 else "N"
        for x in range(x0 - 2, x1 + 3):
            for z in range(z0 - 2, z1 + 3):
                for y in range(GP + 1, GP + 30):
                    if a.get(x, y, z) != AIR:
                        a.set(x, y, z, AIR)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                ring = x in (x0, x1) or z in (z0, z1)
                for y in range(GP - 12, GP - DEPTH):
                    a.set(x, y, z, B("stone"))
                if ring:
                    a.set(x, GP - DEPTH, z, B("border_block"))
                    for y in range(GP - DEPTH + 1, GP):
                        a.set(x, y, z, B("stone_bricks"))
                    a.set(x, GP, z, B("polished_andesite"))
                    a.set(x, GP + 1, z, B("mossy_stone_brick_wall") if (x + z) % 5 == 0 else B("stone_brick_wall"))
                else:
                    a.set(x, GP - DEPTH, z, B("allow"))
                    for y in range(GP - DEPTH + 1, GP):
                        a.set(x, y, z, B("dirt"))
                    a.set(x, GP, z, B("grass_block"))
        for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            a.set(x, GP + 1, z, B("stone_bricks"))
            a.set(x, GP + 2, z, B("lantern"))
        # entry post in the middle of the front side
        mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
        if front == "N":
            px, pz, ox, oz = mx, z0, 0, -1
        elif front == "S":
            px, pz, ox, oz = mx, z1, 0, 1
        elif front == "W":
            px, pz, ox, oz = x0, mz, -1, 0
        else:
            px, pz, ox, oz = x1, mz, 1, 0
        face_out = {(0, -1): 2, (0, 1): 3, (-1, 0): 4, (1, 0): 5}[(ox, oz)]
        face_in = {(0, -1): 3, (0, 1): 2, (-1, 0): 5, (1, 0): 4}[(ox, oz)]
        a.set(px, GP + 1, pz, B("chiseled_stone_bricks"))
        a.set(px, GP + 2, pz, B("chiseled_stone_bricks"))
        a.set(px, GP + 3, pz, B("lantern"))
        a.set(px + ox, GP + 1, pz + oz, B("stone_button", facing_direction=face_out))
        a.set(px - ox, GP + 1, pz - oz, B("stone_button", facing_direction=face_in))
        price = PRICE_VIEW if math.hypot(pcx - lag[0], (pcz - lag[1]) * 60 / 44) < 95 else PRICE_STD
        txt = "§l§e집터 #%d\n§r§a판매 중\n§f%d원" % (n, price)
        a.set(px + ox, GP + 2, pz + oz, B("spruce_wall_sign", facing_direction=face_out))
        a.add_be(sign_be(px + ox, GP + 2, pz + oz, txt))
        inside = (px - 3 * ox, GP + 1, pz - 3 * oz, {(0, -1): 0, (0, 1): 180, (-1, 0): 270, (1, 0): 90}[(ox, oz)])
        outside = (px + 3 * ox, GP + 1, pz + 3 * oz, {(0, -1): 180, (0, 1): 0, (-1, 0): 90, (1, 0): 270}[(ox, oz)])
        out.append(dict(id=n, ring=(x0, z0, x1, z1), interior=(x0 + 1, GP - DEPTH + 1, z0 + 1, x1 - 1, GP + BUILD_UP, z1 - 1),
                        floor=GP, front=front, post=(px, GP + 1, pz), btn_out=(px + ox, GP + 1, pz + oz),
                        btn_in=(px - ox, GP + 1, pz - oz), btn_out_face=face_out, btn_in_face=face_in,
                        sign=(px + ox, GP + 2, pz + oz),
                        inside=inside, outside=outside, price=price, grid=(p["gi"], p["gj"])))
    return out


def paths_and_garden(m, plots):
    """Pave the gaps between plots, lamp posts at crossings, flowers and cherry trees in spare corners."""
    a = m.a
    rng = random.Random(78)
    taken = np.zeros((SIZE, SIZE), bool)
    for p in plots:
        x0, z0, x1, z1 = p["ring"]
        taken[x0 - a.x0:x1 - a.x0 + 1, z0 - a.z0:z1 - a.z0 + 1] = True
    dist = m.district
    keep = set()
    for p in plots:
        for key in ("btn_out", "sign"):
            keep.add(tuple(p[key]))
    for i in range(SIZE):
        for k in range(SIZE):
            if not dist[i, k] or taken[i, k]:
                continue
            x, z = i + a.x0, k + a.z0
            for y in range(GP + 1, GP + 20):
                if a.get(x, y, z) != AIR and (x, y, z) not in keep:
                    a.set(x, y, z, AIR)
            r = rng.random()
            a.set(x, GP, z, B("grass_path") if r < 0.75 else B("coarse_dirt") if r < 0.9 else B("gravel"))
    # crossings: the 4x4 squares between four plot corners
    plot_set = {(p["grid"][0], p["grid"][1]) for p in plots}
    done = set()
    for (gi, gj) in plot_set:
        for (di, dj) in ((1, 1), (0, 1), (1, 0), (0, 0)):
            ci, cj = gi + di, gj + dj
            if (ci, cj) in done:
                continue
            done.add((ci, cj))
            cx = m.cx + 2 + PITCH * ci - 3
            cz = m.cz - 97 + PITCH * cj - 3
            ii, kk = cx - a.x0, cz - a.z0
            if 0 <= ii < SIZE and 0 <= kk < SIZE and dist[ii, kk] and not taken[ii, kk]:
                if a.get(cx, GP + 1, cz) == AIR:
                    lamp_post(a, cx, GP + 1, cz, B("dark_oak_fence"), B("lantern"), height=3)
    return taken


def plot_office(m, W):
    """Office at the arrival plaza: plot clerk NPC, live plot map, ender chests."""
    a = m.a
    cx, cz = m.cx, m.cz - 88
    g = GP
    for x in range(cx - 25, cx + 26):
        for z in range(cz - 16, cz + 15):
            for y in range(g + 1, g + 22):
                a.set(x, y, z, AIR)
            for y in range(g - 6, g):
                if a.get(x, y, z) == AIR:
                    a.set(x, y, z, B("stone"))
            a.set(x, g, z, B("smooth_sandstone") if (x + z) % 4 else B("cut_sandstone"))
            m.H[x - a.x0, z - a.z0] = g
    # building: x cx-9..cx+9, z cz-6..cz+6, door on the north (bridge) and south (district)
    x1, x2, z1, z2 = cx - 9, cx + 9, cz - 6, cz + 6
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            edge = x in (x1, x2) or z in (z1, z2)
            a.set(x, g, z, B("birch_planks") if (x + z) % 2 else B("stripped_birch_wood", axis="x"))
            for y in range(g + 1, g + 6):
                if edge:
                    corner = x in (x1, x2) and z in (z1, z2)
                    a.set(x, y, z, B("stripped_birch_log", axis="y") if corner or x % 4 == 0 else
                          (B("light_blue_stained_glass_pane") if y in (g + 2, g + 3) and not corner else B("smooth_sandstone")))
                else:
                    a.set(x, y, z, AIR)
            a.set(x, g + 6, z, B("smooth_sandstone"))
    for x in range(x1 - 1, x2 + 2):
        for z in range(z1 - 1, z2 + 2):
            a.set(x, g + 7, z, B("prismarine_brick_slab", half="bottom") if x in (x1 - 1, x2 + 1) or z in (z1 - 1, z2 + 1)
                  else B("prismarine_bricks"))
    for x in range(x1 + 1, x2):
        for z in range(z1 + 1, z2):
            if (x - cx) % 4 == 0 and (z - cz) % 4 == 0:
                a.set(x, g + 6, z, B("sea_lantern"))
    for zd in (z1, z2):
        for x in (cx - 1, cx, cx + 1):
            for y in (g + 1, g + 2, g + 3):
                a.set(x, y, zd, AIR)
    # counter + clerk on a lodestone marker
    for x in range(cx - 4, cx + 5):
        a.set(x, g + 1, cz - 1, B("stripped_birch_log", axis="x"))
    a.set(cx - 4, g + 1, cz - 1, B("birch_planks"))
    a.set(cx, g, cz - 3, B("lodestone"))
    W.npcs.append(dict(name="§l§e집터 관리인", x=cx + 0.5, y=g + 1, z=cz - 2.5, face=(cx + 0.5, g + 1, cz + 3.5),
                       tag="sky_plot_clerk", kind="plots"))
    # ender chests
    for x in (x1 + 1, x2 - 1):
        a.set(x, g + 1, z2 - 1, B("ender_chest", cardinal="north"))
        a.add_be(simple_be("EnderChest", x, g + 1, z2 - 1))
        W.ender_chests.append((x, g + 1, z2 - 1))
    board = dict(x=cx - 21, cz=cz, g=g)
    wall_sign(a, x2 - 1, g + 3, cz, 4, "§l§e집터 구매\n§r§f관리인을 눌러\n§f사고 · 관리하세요", kind="birch_wall_sign")
    wall_sign(a, cx + 2, g + 3, z2 - 1, 2, "§l§6집터 규칙\n§r§f1인 1집터\n§f허용 블록 위만 건축", kind="birch_wall_sign")
    wall_sign(a, cx - 2, g + 3, z2 - 1, 2, "§l§4경고\n§r§f남의 집터에 핵으로\n§f들어가면 영구밴", kind="birch_wall_sign")
    # plaza lamps and benches
    for (x, z) in ((cx - 14, cz - 10), (cx + 14, cz - 10), (cx - 14, cz + 10), (cx + 14, cz + 10),
                   (cx - 22, cz), (cx + 22, cz)):
        lamp_post(a, x, g + 1, z, B("bamboo_fence"), B("lantern"), height=3)
    for x in (cx - 18, cx + 18):
        for z in (cz - 3, cz - 2, cz - 1):
            a.set(x, g + 1, z, stair("birch_stairs", "west" if x < cx else "east"))
    a.set(cx, g + 1, cz - 12, B("smooth_sandstone"))
    standing_sign(a, cx, g + 2, cz - 12, 8, "§l§b주거 섬\n§r§f안전구역 (PvP 불가)\n§f집터 사무소 →", kind="birch_standing_sign")
    return board


def board_pixels(W, m, plots, board):
    """Plot map billboard on the west side of the office plaza: one block per grid cell, facing east.
    Lime = for sale, red = owned (the script recolours it); blue = lagoon, yellow = you are here."""
    a = W.a
    bx, cz, g = board["x"], board["cz"], board["g"]
    for z in range(cz - 7, cz + 7):
        for y in range(g + 1, g + 15):
            a.set(bx - 1, y, z, B("stripped_birch_log", axis="y") if z in (cz - 7, cz + 6) else B("birch_planks"))
            frame = z in (cz - 6, cz + 5) or y in (g + 2, g + 13)
            if frame or z in (cz - 7, cz + 6) or y == g + 1 or y == g + 14:
                a.set(bx, y, z, B("stripped_birch_log", axis="y") if z in (cz - 7, cz + 6) else B("birch_planks"))
    by_grid = {p["grid"]: p for p in plots}
    pix = {}
    for gi in range(-5, 5):
        for gj in range(0, 10):
            z = cz - 5 + (gi + 5)
            y = g + 12 - gj
            lx = 2 + 21 * gi + 8
            lz = -97 + 21 * gj + 8
            if (gi, gj) in by_grid:
                b = B("lime_concrete")
                pix[by_grid[(gi, gj)]["id"]] = (bx, y, z)
            else:
                ii, kk = lx + m.cx - m.a.x0, lz + m.cz - m.a.z0
                inside = 0 <= ii < SIZE and 0 <= kk < SIZE
                if PLAZA[0] <= lx <= PLAZA[2] and PLAZA[1] <= lz <= PLAZA[3]:
                    b = B("yellow_concrete")
                elif inside and m.water[ii, kk] > 0:
                    b = B("light_blue_concrete")
                elif inside and m.D[ii, kk] <= m.R:
                    b = B("white_terracotta")
                else:
                    b = B("cyan_terracotta")
            a.set(bx, y, z, b)
    wall_sign(a, bx + 1, g + 1, cz - 2, 5, "§l§b집터 지도\n§r§a초록§f = 판매 중\n§c빨강§f = 주인 있음", kind="birch_wall_sign")
    wall_sign(a, bx + 1, g + 1, cz + 1, 5, "§l§e노랑§r§f = 지금 위치\n§b파랑§f = 라군\n§7북쪽이 위", kind="birch_wall_sign")
    return pix
