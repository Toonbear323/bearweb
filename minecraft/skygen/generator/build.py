"""Builds the skygen world (hub + 5 islands + bridges) and packages SkyGen.mcworld.

usage: python build.py [output_dir] [--no-pack] [--no-previews] [--check]
"""
import json
import math
import os
import sys
import time

import numpy as np

from mcw import B, AIR, PAL
from sky_world import SkyWorld, seal_liquids, persist_leaves, fix_plants
from sky_features import Gens, volcano_mines, GEN_KINDS
import sky_islands as si
import sky_hub
import sky_skeld
import sky_plots
import sky_library
from sky_bridges import sky_bridge, return_pad
from gen_library import Library

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD_NAME = "스카이젠 - 하늘섬 군도"
FILE_NAME = "SkyGen.mcworld"
ISL = dict(hub=(0, 0), forest=(0, -256), skeld=(256, 0), library=(-256, 0), paradise=(0, 272), volcano=(256, 224))
NAMES = dict(hub="허브", forest="숲 섬", skeld="우주 광산선", library="마법 도서관", paradise="주거 섬", volcano="화산 섬")


def landing(area, x1, z1, x2, z2, h, rng_top=("coarse_dirt", "gravel", "grass_path")):
    """Level a pad where a bridge meets an island (top block at y = h)."""
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            for y in range(h + 1, h + 16):
                area.set(x, y, z, AIR)
            for y in range(h - 8, h):
                if area.get(x, y, z) == AIR:
                    area.set(x, y, z, B("stone") if y < h - 2 else B("dirt"))
            area.set(x, h, z, B(rng_top[(x * 7 + z * 3) % len(rng_top)]))


def free_spot(W, x, y, z, r=12, need=1):
    """Nearest (x, z) with a (2*need+1)^2 square of floor at y-1 and two air blocks above it."""
    a = W.a
    best = None
    for d in range(0, r + 1):
        for dx in range(-d, d + 1):
            for dz in range(-d, d + 1):
                if max(abs(dx), abs(dz)) != d:
                    continue
                ok = True
                for ox in range(-need, need + 1):
                    for oz in range(-need, need + 1):
                        X, Z = x + dx + ox, z + dz + oz
                        if a.get(X, y - 1, Z) == AIR or a.get(X, y, Z) != AIR or a.get(X, y + 1, Z) != AIR:
                            ok = False
                if ok:
                    return (x + dx, z + dz)
    return best


def safe_boxes(mask, x0, z0, y1=40, y2=150):
    """Cover a 2D mask with rectangles (merge equal row runs)."""
    boxes = []
    sx, sz = mask.shape
    runs_prev = {}
    out = []
    for i in range(sx):
        runs = []
        k = 0
        while k < sz:
            if mask[i, k]:
                s = k
                while k < sz and mask[i, k]:
                    k += 1
                runs.append((s, k - 1))
            else:
                k += 1
        nxt = {}
        for r in runs:
            if r in runs_prev:
                nxt[r] = runs_prev[r]
            else:
                nxt[r] = i
        for r, start in runs_prev.items():
            if r not in nxt:
                out.append((start, r[0], i - 1, r[1]))
        runs_prev = nxt
    for r, start in runs_prev.items():
        out.append((start, r[0], sx - 1, r[1]))
    for (i1, k1, i2, k2) in out:
        boxes.append((x0 + i1, y1, z0 + k1, x0 + i2, y2, z0 + k2))
    return boxes


def build_world():
    t0 = time.time()
    W = SkyWorld()
    gens = Gens()

    def log(msg):
        print("%-34s %6.1fs" % (msg, time.time() - t0))

    # ---------------------------------------------------------------- hub
    lb, hub = sky_hub.build_hub(W)
    for n in lb.npcs:
        n.setdefault("kind", "deco")
        W.npcs.append(n)
    W.ender_chests += lb.ender
    for g in lb.gates:
        W.portals.append(dict(kind="gate", dest=g["dest"], box=g["box"], label=g["title"]))
    W.arrivals["hub"] = (0.5, 64, 41.5, 180)
    X, Z = hub["X"], hub["Z"]
    tongues = ((np.abs(X) <= 6) & ((Z < -88) | (Z > 104))) | ((np.abs(Z) <= 6) & ((X < -94) | (X > 106)))
    hub_safe = hub["foot"] & ~tongues
    W.safe_zones += [("hub",) + b for b in safe_boxes(hub_safe, hub["x0"], hub["z0"])]
    log("hub")

    # ---------------------------------------------------------------- forest
    fo = si.SkyForest(*ISL["forest"], gens=gens)
    fo.build()
    fz = ISL["forest"][1]
    fh = max(fo.gy(0, fz + 80), fo.gy(0, fz + 86))
    landing(fo.a, -6, fz + 78, 6, fz + 96, fh)
    under = si.under_rock([B("stone"), B("andesite"), B("tuff"), B("stone")], accent=B("moss_block"), accent_chance=0.04)
    si.place_mapbase(W, fo, 11, under, force=[(-6, fz + 78, 6, fz + 98)])
    W.arrivals["forest"] = (0.5, fh + 1, fz + 88.5, 180)
    return_pad(W, 4, fh, fz + 84, "숲 섬")
    log("forest")

    # ---------------------------------------------------------------- skeld (ship)
    sk = sky_skeld.SkySkeld(*ISL["skeld"], gens)
    sk.build()
    W.paste(sk.a)
    W.furnace_rooms = sk.furnace_rooms
    ccx, ccz = sk.center["C"]
    p = free_spot(W, ccx - 12, sky_skeld.P, ccz, r=14)
    return_pad(W, p[0], sky_skeld.FY, p[1], "우주 광산선", glow="sea_lantern")
    a2 = free_spot(W, ccx - 12, sky_skeld.P, ccz + 6, r=14, need=0)
    W.arrivals["skeld"] = (a2[0] + 0.5, sky_skeld.P, a2[1] + 0.5, 90)
    log("skeld")

    # ---------------------------------------------------------------- volcano
    vo = si.SkyVolcano(*ISL["volcano"])
    vo.build()
    volcano_mines(vo, gens)
    vx, vz = ISL["volcano"]
    hx = sk.entrance_s[0]
    vh = vo.gy(hx, vz - 82)
    landing(vo.a, hx - 7, vz - 96, hx + 7, vz - 78, vh, rng_top=("polished_blackstone_bricks", "blackstone", "basalt"))
    under = si.under_rock([B("blackstone"), B("basalt"), B("deepslate"), B("blackstone")], accent=B("magma"), accent_chance=0.03)
    si.place_mapbase(W, vo, 12, under, force=[(hx - 7, vz - 98, hx + 7, vz - 78)])
    W.arrivals["volcano"] = (hx + 0.5, vh + 1, vz - 86.5, 0)
    return_pad(W, hx + 5, vh, vz - 84, "화산 섬", glow="ochre_froglight")
    log("volcano")

    # ---------------------------------------------------------------- residential island
    pa = sky_plots.ResidentialIsland(*ISL["paradise"])
    pa.build()
    plans = sky_plots.plan_plots(pa)
    plots = sky_plots.build_plots(pa, plans)
    sky_plots.paths_and_garden(pa, plots)
    board = sky_plots.plot_office(pa, W)
    px_, pz_ = ISL["paradise"]
    landing(pa.a, -6, pz_ - 112, 6, pz_ - 104, sky_plots.GP, rng_top=("smooth_sandstone", "cut_sandstone"))
    under = si.under_rock([B("calcite"), B("diorite"), B("stone"), B("sandstone")], accent=B("moss_block"), accent_chance=0.03)
    pfoot, _ = si.place_mapbase(W, pa, 13, under, force=[(-6, pz_ - 114, 6, pz_ - 100)])
    W.plots = plots
    W.plot_board = sky_plots.board_pixels(W, pa, plots, board)
    W.arrivals["paradise"] = (0.5, sky_plots.GP + 1, pz_ - 99.5, 0)
    return_pad(W, 12, sky_plots.GP, pz_ - 96, "주거 섬", glow="sea_lantern")
    W.safe_zones += [("paradise",) + b for b in safe_boxes(pfoot, pa.a.x0, pa.a.z0)]
    W.no_walk += [p["ring"] for p in plots]
    log("paradise (%d plots)" % len(plots))

    # ---------------------------------------------------------------- library
    lib = Library(*ISL["library"])
    lib.build()
    feats = sky_library.library_features(lib, W)
    lx, lz = ISL["library"]
    lfoot, _, _, _ = si.library_island(W, lib, 15, force=[(lx + 72, lz - 4, lx + 104, lz + 4)])
    W.arrivals["library"] = feats["arrival"]
    return_pad(W, feats["pad"][0], feats["pad"][1], feats["pad"][2], "마법 도서관", glow="pearlescent_froglight")
    W.repairs = feats["repairs"]
    W.safe_zones += [("library",) + b for b in safe_boxes(lfoot, lib.a.x0, lib.a.z0)]
    log("library")

    # ---------------------------------------------------------------- bridges
    W.bridges = []
    W.bridges.append(("hub-forest", sky_bridge(W, (0, -93), (0, fz + 96), 64, fh + 1, "forest")))
    W.bridges.append(("hub-skeld", sky_bridge(W, (111, 0), (sk.entrance_w[0] - 1, 0), 64, sky_skeld.P, "skeld")))
    W.bridges.append(("hub-library", sky_bridge(W, (-99, 0), (lx + 101, 0), 64, 65, "library")))
    W.bridges.append(("hub-paradise", sky_bridge(W, (0, 109), (0, pz_ - 105), 64, sky_plots.GP + 1, "paradise")))
    W.bridges.append(("skeld-volcano", sky_bridge(W, (hx, sk.entrance_s[2] + 1), (hx, vz - 95), sky_skeld.P, vh + 1, "volcano")))
    log("bridges")

    # ---------------------------------------------------------------- finishing
    ncols = gens.finalize(W.a)
    W.generators = gens.export()
    n_seal = seal_liquids(W, B("stone"))
    n_leaf = persist_leaves(W)
    W.a.fix_walls()
    n_plant = fix_plants(W)
    log("finish: %d gens (%d cols), sealed %d, leaves %d, plants %d" % (len(W.generators), ncols, n_seal, n_leaf, n_plant))
    W.islands = {k: dict(name=NAMES[k], center=v) for k, v in ISL.items()}
    return W


def verify(W, fix_rounds=4):
    """Walk from the hub spawn; fill the floor of trapped spots and walk again until nothing is trapped."""
    import sky_verify as sv
    t0 = time.time()
    fixed = 0
    for r in range(fix_rounds + 1):
        rep = sv.walk(W)
        if not rep["trapped"] or r == fix_rounds:
            break
        for (x, y, z) in rep["trapped"]:
            below = W.a.get(x, y - 1, z)
            W.a.set(x, y, z, below if below else B("stone"))
            fixed += 1
    land, ex = sv.summarize_falls(rep["falls"])
    missing, nbad = sv.coverage(W, rep)
    leaks = sv.liquid_leaks(W)
    W.verification = dict(reachable=rep["reachable"], trapped=len(rep["trapped"]), auto_filled=fixed,
                          fall_spots=len(land), missing=len(missing), unminable_generators=nbad, liquid_leaks=leaks)
    print("verify: reachable=%d trapped=%d (auto-filled %d) fall-spots=%d missing=%d unminable=%d leaks=%d (%.0fs)" % (
        rep["reachable"], len(rep["trapped"]), fixed, len(land), len(missing), nbad, leaks, time.time() - t0))
    for t in rep["trapped"][:10]:
        print("   trapped", t)
    for m in missing[:20]:
        print("   missing", m)
    return rep


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_dir = args[0] if args else os.path.join(HERE, "..")
    W = build_world()
    verify(W)
    if "--no-pack" in sys.argv:
        return W
    import sky_pack
    sky_pack.package(W, out_dir, WORLD_NAME, FILE_NAME, previews="--no-previews" not in sys.argv)
    return W


if __name__ == "__main__":
    main()
