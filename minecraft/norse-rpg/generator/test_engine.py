"""Engine test world: one flat walled arena per boss, behaviour + resource pack attached.

usage: python test_engine.py <out.mcworld>   then run the BDS scenario written next to it.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import nr_design as D
import nr_pack
from mcw import Area, B
import nr_package as NP
import amulet_nbt as an


class NoModels:
    @staticmethod
    def write(rp, bp):
        return {}


def build(out):
    ids = list(D.BOSSES)
    cols = 6
    pitch = 64
    sx = cols * pitch
    sz = math.ceil(len(ids) / cols) * pitch
    a = Area("test", 0, 0, sx, sz, y0=48, sy=48)
    a.fill(0, 48, 0, sx - 1, 62, sz - 1, B("stone"))
    arenas = []
    for i, bid in enumerate(ids):
        b = D.BOSSES[bid]
        cx = (i % cols) * pitch + pitch // 2
        cz = (i // cols) * pitch + pitch // 2
        r = b["arena"]
        for x in range(cx - r - 3, cx + r + 4):
            for z in range(cz - r - 3, cz + r + 4):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.5:
                    a.set(x, 63, z, B("polished_andesite") if int(d) % 4 else B("polished_deepslate"))
                elif d <= r + 2.5:
                    for y in range(63, 70):
                        a.set(x, y, z, B("stone_bricks"))
        y = 64
        arenas.append(dict(id="t_" + bid, dungeon=b["dungeon"], boss=bid, role=b["role"], x=cx + 0.5, y=y, z=cz + 0.5, r=r,
                           trigger=[cx - 2, 64, cz - 2, cx + 2, 66, cz + 2], entry=[], exit=[], gateBlock="minecraft:iron_bars",
                           respawn=600))
    world_data = dict(ARENAS=arenas, ZONES=[], SHIPS=[], RETURNS=[], STATIONS={}, POINTS={})
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "test_packs")
    packs = nr_pack.build(tmp, world_data, NoModels)
    wdir = NP.new_world_dir(os.path.join(os.path.dirname(os.path.abspath(out)), "test_world"))
    db = NP.DB(os.path.join(wdir, "db"))
    db.put_area(a)
    I, By = an.IntTag, an.ByteTag
    NP.finish(wdir, out, "nrpg engine test", (pitch // 2, 64, pitch // 2), packs=packs, db=db,
              overrides={"Difficulty": I(2), "GameType": I(2), "domobspawning": By(0), "dodaylightcycle": By(0),
                         "Time": an.LongTag(13000), "lastOpenedWithVersion": an.ListTag([I(v) for v in (1, 21, 90, 0, 0)]),
                         "MinimumCompatibleClientVersion": an.ListTag([I(v) for v in (1, 21, 90, 0, 0)])})
    return arenas, packs


if __name__ == "__main__":
    out = sys.argv[1]
    arenas, packs = build(out)
    print(len(arenas), "arenas;", packs["bp"])
