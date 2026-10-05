"""Builds the complete '능력 술래잡기' Bedrock world and packages it as a .mcworld file.

usage: python build.py [output_dir]
"""
import json
import os
import shutil
import sys
import tempfile
import time

import amulet_nbt as an
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from mcw import write_db, write_level_dat, zip_dir, PAL
from gen_lobby import build_lobby, SPAWN
from gen_forest import Forest
from gen_volcano import Volcano
from gen_paradise import Paradise
from gen_factory import Factory
import trapcheck
import render
import pack

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD_NAME = "능력 술래잡기"
FILE_NAME = "AbilityTag.mcworld"
TIME_OF_DAY = 12000      # sunset

VOID_LAYERS = ('{"biome_id":1,"block_layers":[{"block_name":"minecraft:air","count":1}],'
               '"encoding_version":6,"structure_options":null,"world_version":"version.post_1_18"}\n')


def build_all():
    t0 = time.time()
    lb, lobby = build_lobby()
    maps = {
        "forest": Forest(1024, 0),
        "volcano": Volcano(0, 1024),
        "paradise": Paradise(-1024, 0),
        "factory": Factory(0, -1024),
    }
    for k, m in maps.items():
        m.build()
        print("built %-9s %.1fs" % (k, time.time() - t0))
    return lb, lobby, maps


def verify(lobby, maps):
    """No position reachable from a spawn may be a trap, and nobody may leave a map."""
    ok = True
    rep = trapcheck.analyze(lobby, (-59, -49, 59, 49), (63, 96), [SPAWN],
                            inside=lambda x, z: -57 <= x <= 57 and -47 <= z <= 47)
    print("verify lobby   : reachable=%6d trapped=%d escaped=%d" % (rep["reachable"], len(rep["trapped"]), len(rep["escaped"])))
    ok &= not rep["trapped"] and not rep["escaped"]
    for k, m in maps.items():
        R = m.R
        rep, fixed = trapcheck.check_and_fix(m.a, (m.cx - R - 4, m.cz - R - 4, m.cx + R + 4, m.cz + R + 4),
                                             (m.H0 - 8, m.H0 + 62), m.spawns, inside=m.inside, label=k,
                                             verbose=False)
        print("verify %-9s: reachable=%6d trapped=%d escaped=%d (auto-fixed %d)" % (
            k, rep["reachable"], len(rep["trapped"]), len(rep["escaped"]), fixed))
        ok &= not rep["trapped"] and not rep["escaped"]
    return ok


def world_icon(path, lobby, maps):
    tiles = []
    for k in ("forest", "volcano", "paradise", "factory"):
        m = maps[k]
        im = render.iso(m.a, os.path.join(tempfile.gettempdir(), "icon_%s.png" % k),
                        box=(m.cx - 92, 44, m.cz - 92, m.cx + 92, 140, m.cz + 92), s=1)
        tiles.append(im)
    W, H = 960, 540
    out = Image.new("RGB", (W, H), (18, 14, 30))
    tw, th = W // 2, H // 2
    for i, im in enumerate(tiles):
        im = im.copy()
        im.thumbnail((tw, th))
        x = (i % 2) * tw + (tw - im.width) // 2
        y = (i // 2) * th + (th - im.height) // 2
        out.paste(im, (x, y))
    d = ImageDraw.Draw(out)
    font = None
    for f in ("/usr/share/fonts/opentype/unifont/unifont.otf",):
        if os.path.exists(f):
            font = ImageFont.truetype(f, 64)
    if font:
        text = "능력 술래잡기"
        bb = d.textbbox((0, 0), text, font=font)
        tx, ty = (W - (bb[2] - bb[0])) // 2, (H - (bb[3] - bb[1])) // 2 - 10
        d.rectangle((tx - 24, ty - 8, tx + bb[2] - bb[0] + 24, ty + bb[3] - bb[1] + 24), fill=(20, 12, 34))
        for ox, oy in ((4, 4),):
            d.text((tx + ox, ty + oy), text, font=font, fill=(110, 40, 160))
        d.text((tx, ty), text, font=font, fill=(255, 214, 120))
    out.save(path, quality=92)
    sq = out.crop(((W - H) // 2, 0, (W + H) // 2, H)).resize((256, 256))
    return sq


def write_world(lobby_obj, lobby, maps, out_dir):
    work = tempfile.mkdtemp(prefix="abilitytag_")
    wdir = os.path.join(work, "world")
    os.makedirs(wdir)
    nkeys = write_db([lobby] + [m.a for m in maps.values()], os.path.join(wdir, "db"))
    print("leveldb keys:", nkeys, "palette size:", len(PAL.entries))
    sx, sy, sz = SPAWN
    I = an.IntTag
    By = an.ByteTag
    changes = {
        "LevelName": an.StringTag(WORLD_NAME),
        "GameType": I(2), "ForceGameType": By(0),
        "Generator": I(2), "FlatWorldLayers": an.StringTag(VOID_LAYERS),
        "Difficulty": I(0),
        "SpawnX": I(sx), "SpawnY": I(sy), "SpawnZ": I(sz),
        "Time": an.LongTag(TIME_OF_DAY), "currentTick": an.LongTag(0),
        "LastPlayed": an.LongTag(int(time.time())),
        "RandomSeed": an.LongTag(20261005),
        "lastOpenedWithVersion": an.ListTag([I(v) for v in (1, 21, 60, 0, 0)]),
        "MinimumCompatibleClientVersion": an.ListTag([I(v) for v in (1, 21, 60, 0, 0)]),
        "NetworkVersion": I(776), "InventoryVersion": an.StringTag("1.21.60"),
        "commandsEnabled": By(1), "cheatsEnabled": By(1), "commandblocksenabled": By(1),
        "commandblockoutput": By(0), "sendcommandfeedback": By(1),
        "dodaylightcycle": By(0), "doweathercycle": By(0), "domobspawning": By(0), "spawnMobs": By(0),
        "dofiretick": By(0), "mobgriefing": By(0), "tntexplodes": By(0), "doinsomnia": By(0),
        "falldamage": By(0), "firedamage": By(0), "drowningdamage": By(0), "freezedamage": By(0),
        "keepinventory": By(1), "doimmediaterespawn": By(1), "randomtickspeed": I(0),
        "spawnradius": I(0), "showtags": By(0), "showcoordinates": By(0), "showdaysplayed": By(0),
        "recipesunlock": By(0), "showrecipemessages": By(0), "projectilescanbreakblocks": By(0),
        "respawnblocksexplode": By(0), "doentitydrops": By(0), "dotiledrops": By(0),
        "naturalregeneration": By(1), "pvp": By(1), "rainLevel": an.FloatTag(0.0), "rainTime": I(999999999),
        "lightningLevel": an.FloatTag(0.0), "lightningTime": I(999999999),
        "hasBeenLoadedInCreative": By(0), "MultiplayerGameIntent": By(1),
        "XBLBroadcastIntent": I(3), "PlatformBroadcastIntent": I(3),
    }
    write_level_dat(os.path.join(wdir, "level.dat"), os.path.join(HERE, "data", "level_template.dat"), changes)
    open(os.path.join(wdir, "levelname.txt"), "w", encoding="utf8").write(WORLD_NAME)
    # behavior pack
    pdir = os.path.join(wdir, "behavior_packs", pack.PACK_NAME)
    pack.write_pack(pdir, lobby_obj, maps, SPAWN)
    json.dump([{"pack_id": pack.PACK_UUID, "version": pack.VERSION}],
              open(os.path.join(wdir, "world_behavior_packs.json"), "w"), indent=2)
    icon = world_icon(os.path.join(wdir, "world_icon.jpeg"), lobby, maps)
    icon.save(os.path.join(pdir, "pack_icon.png"))
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, FILE_NAME)
    if os.path.exists(dst):
        os.remove(dst)
    zip_dir(wdir, dst)
    print("wrote", dst, "%.1f MB" % (os.path.getsize(dst) / 1e6))
    return wdir, dst


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..")
    lb, lobby, maps = build_all()
    if not verify(lobby, maps):
        print("!! verification failed")
        sys.exit(1)
    wdir, dst = write_world(lb, lobby, maps, out_dir)
    info = {"spawn_lobby": SPAWN, "maps": {k: {"center": (m.cx, m.H0 + 1, m.cz), "spawns": m.spawns,
                                               "pois": {p: v for p, v in m.pois.items()}}
                                           for k, m in maps.items()},
            "npcs": [{k: v for k, v in n.items()} for n in lb.npcs]}
    json.dump(info, open(os.path.join(os.path.dirname(dst), "world_info.json"), "w", encoding="utf8"),
              ensure_ascii=False, indent=2, default=lambda o: [int(v) for v in o] if hasattr(o, "__len__") else int(o))
    print("world folder:", wdir)


if __name__ == "__main__":
    main()
