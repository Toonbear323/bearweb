"""Builds the RPG world (11 connected regions) and packages it as RPGWorld.mcworld.

usage: python build.py [output_dir] [--no-previews]
"""
import json
import os
import sys
import time

import numpy as np

from mcw import B, PAL
from rpg_world import World, X0, Z0, SX, SZ
import layout
import area_spawn, area_farm, area_cave, area_village, area_hq, area_beach, area_deepsea
import area_nether, area_castle, area_dungeon, area_deepdark
import rpg_verify
import rpg_light

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = [area_spawn, area_farm, area_cave, area_village, area_hq, area_beach, area_deepsea,
           area_nether, area_castle, area_dungeon, area_deepdark]
WORLD_NAME = "RPG 모험의 길"
FILE_NAME = "RPGWorld.mcworld"


def build_world():
    t0 = time.time()
    W = World()
    layout.define_regions(W)
    W.terrain()
    layout.post_terrain(W)
    for m in MODULES:
        m.shape(W)
    W.paint()
    for m in MODULES:
        m.build(W)
        print("built %-14s %.1fs" % (m.__name__, time.time() - t0))
    for sl in getattr(W, "extra_surface", []):
        W.surface_ok[sl] = True
    W.a.fix_walls()
    return W


def verify(W, label=""):
    t0 = time.time()
    rep = rpg_verify.walk(W)
    missing = rpg_verify.coverage(W, rep)
    land, ex = rpg_verify.summarize_falls(rep["falls"])
    print("verify%s: reachable=%d trapped=%d escaped=%d fall-spots=%d missing=%d (%.0fs)" % (
        label, rep["reachable"], len(rep["trapped"]), len(rep["escaped"]), len(land), len(missing),
        time.time() - t0))
    if rep["trapped"]:
        print("   trapped e.g.", rep["trapped"][:10])
    if rep["escaped"]:
        print("   escaped e.g.", rep["escaped"][:10])
    for key, n in land.most_common(15):
        print("   fall", key, n, ex[key])
    for m in missing:
        print("   missing", m)
    return rep, missing, land


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_dir = args[0] if args else os.path.join(HERE, "..")
    W = build_world()
    if "--quick" in sys.argv:          # packaging test only: no walk, no light fill
        import pack_rpg
        rep = dict(reachable=0, trapped=[], escaped=[], falls=[])
        pack_rpg.package(W, out_dir, WORLD_NAME, FILE_NAME, rep, {}, previews=False)
        return W, rep
    rep, missing, land = verify(W)
    if "--check" in sys.argv:
        return W, rep
    added = rpg_light.light_world(W, rep)
    print("light blocks added:", added)
    stats = rpg_light.stats(W, rep)
    for k, v in stats.items():
        print("   light %-12s %s" % (k, v))
    import pack_rpg
    pack_rpg.package(W, out_dir, WORLD_NAME, FILE_NAME, rep, stats, previews="--no-previews" not in sys.argv)
    dump = os.environ.get("RPG_DUMP")
    if dump:                       # keep the voxels for a later diff against what BDS saved
        import pickle
        os.makedirs(dump, exist_ok=True)
        np.save(os.path.join(dump, "blk.npy"), W.a.blk)
        pickle.dump(dict(entries=PAL.entries, x0=W.a.x0, z0=W.a.z0, y0=W.a.y0),
                    open(os.path.join(dump, "meta.pkl"), "wb"))
    return W, rep


if __name__ == "__main__":
    main()
