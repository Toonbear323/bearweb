"""Build the Bear RPG world and package it as a .mcworld.

usage: python build.py [--no-export]
"""
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gen import bedrock, blocks as bl, d_cave, d_desert, d_ocean, d_plains, dkit, extras, hub, kit  # noqa: E402
from gen import n_bast, n_fort, nether, plots, render, systems, terrain, town  # noqa: E402
from gen.core import REG, World  # noqa: E402
from gen.layout import *  # noqa: E402,F401,F403

NAME = "베어 RPG V1"
OUT = os.path.join(HERE, "out")
MCWORLD = os.path.join(HERE, "BearRPG_V1.mcworld")
SEEDS = {}        # per-area RNG seed overrides (each area draws from its own stream)


def log(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


def build():
    log("heightmap")
    T = terrain.build_heightmap()
    w = World(OX0, OZ0, OX1, OZ1, OY0, OY1, dim=0, biome=BIO_PLAINS, seed=11)
    terrain.voxelize(w, T, log=log)
    terrain.ores(w, T, log=log)
    log("town")
    w.rng = np.random.default_rng(SEEDS.get("town", 101))
    hub.build_streets(w)
    hub.build_walls(w, T)
    hub.rotunda(w)
    hub.plaza_decor(w)
    town.build_town(w, T, log=log)
    log("plots")
    w.rng = np.random.default_rng(SEEDS.get("plots", 102))
    plots.build_plots(w, T, log=log)
    log("dungeon: plains")
    w.rng = np.random.default_rng(SEEDS.get("plains", 103))
    d_plains.build(w, T, log=log)
    log("dungeon: desert")
    w.rng = np.random.default_rng(SEEDS.get("desert", 104))
    d_desert.build(w, T, log=log)
    log("dungeon: cave")
    w.rng = np.random.default_rng(SEEDS.get("cave", 105))
    d_cave.build(w, T, log=log)
    log("dungeon: ocean")
    w.rng = np.random.default_rng(SEEDS.get("ocean", 106))
    d_ocean.build(w, T, log=log)
    log("hell gate + roads")
    w.rng = np.random.default_rng(SEEDS.get("gate", 107))
    nether.hell_gate_overworld(w, T, log=log)
    extras.build(w, T, log=log)
    log("vegetation")
    w.rng = np.random.default_rng(SEEDS.get("veg", 108))
    terrain.vegetation(w, T, log=log)
    log("walls connected: %d" % kit.connect_walls(w))
    # the outermost ring must match the surrounding flat ocean (sand top at y=42, water above)
    edge_ok = all(int(T.h[i, j]) == 42 for i in (0, w.sx - 1) for j in range(w.sz)) and all(
        int(T.h[i, j]) == 42 for j in (0, w.sz - 1) for i in range(w.sx))
    log("region border matches flat ocean: %s" % edge_ok)
    log("nether")
    n = nether.make_world(log=log)
    n.rng = np.random.default_rng(SEEDS.get("nether", 109))
    nether.hub(n, log=log)
    nether.canyon(n, log=log)
    n.rng = np.random.default_rng(SEEDS.get("fort", 110))
    n_fort.build(n, log=log)
    n.rng = np.random.default_rng(SEEDS.get("bast", 111))
    n_bast.build(n, log=log)
    log("nether walls connected: %d" % kit.connect_walls(n))
    n.shift(NOFF, 0)
    return w, n, T


def main():
    os.makedirs(OUT, exist_ok=True)
    w, n, T = build()
    log("registry: %d block states, %d + %d block entities" % (len(REG.entries), len(w.be), len(n.be)))
    from gen import check
    problems = check.run(w) + check.run(n)
    for pr in problems[:40]:
        log("  CHECK:", pr)
    log("consistency problems: %d" % len(problems))
    missing = check.coverage([w, n])
    log("unwired functions: %s" % (missing or "none"))
    for wd in (w, n):       # never export a block entity whose block was replaced
        for k in [k for k, d in wd.be.items() if wd.get(*k) == 0]:
            del wd.be[k]
    # previews
    render.topdown(w, out=os.path.join(OUT, "map_overworld.png"))
    render.topdown(n, ymax=60, scale=2, out=os.path.join(OUT, "map_nether.png"))
    im = render.iso(w, (-92, G - 2, -92, 92, G + 48, 92), view=0, S=4)
    bw, bh = im.size
    tw = min(bw, int(bh * 16 / 9))
    th = int(tw * 9 / 16)
    icon = im.crop(((bw - tw) // 2, max(0, (bh - th) // 2 + 20), (bw - tw) // 2 + tw, max(0, (bh - th) // 2 + 20) + th))
    icon = icon.resize((800, 450))
    icon_path = os.path.join(OUT, "world_icon.jpeg")
    icon.convert("RGB").save(icon_path, quality=88)
    log("previews written")
    if "--no-export" in sys.argv:
        return
    pack_icon = os.path.join(OUT, "pack_icon.png")
    systems.pack_icon(pack_icon)
    pack_dir = systems.build_pack(os.path.join(HERE, "pack"), icon=pack_icon)
    log("behaviour pack: %s" % pack_dir)
    folder = os.path.join(OUT, "world")
    bedrock.write_world(folder, NAME, (0, G + 3, 0), [w, n], bl.WATER,
                        packs=[(pack_dir, systems.PACK_UUID, systems.PACK_VERSION)], icon=icon_path, log=log)
    size = bedrock.pack_mcworld(folder, MCWORLD)
    log("mcworld: %s (%.1f MB)" % (MCWORLD, size / 1e6))


if __name__ == "__main__":
    T0 = time.time()
    main()
