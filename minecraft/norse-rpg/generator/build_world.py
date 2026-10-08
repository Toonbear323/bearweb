"""Build the whole Norse RPG world: the harbour spawn, ten dungeons, both packs, the .mcworld and the .mcpack files.

usage: python build_world.py <out_dir> [--only d01,d02] [--keep <work dir>]
       python build_world.py <out_dir> --repack --keep <work dir>

Every region is generated, walk-verified (traps are filled, escapes and gate bypasses reported), encoded into the
world's LevelDB and dropped before the next one is built, so memory stays at one region at a time.
--repack reuses the world kept by an earlier build (--keep) and only rebuilds the packs and the files: use it after
changing scripts, models or pack data without touching the terrain.
"""
import argparse
import importlib
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import amulet_nbt as an
import nr_design as D
import nr_pack
import nr_package as NP
import nr_spawn
import nr_verify

MODULES = {"d01": "d01_barrow", "d02": "d02_ironwood", "d03": "d03_andvari", "d04": "d04_hrungnir", "d05": "d05_naglfar",
           "d06": "d06_utgard", "d07": "d07_nidavellir", "d08": "d08_muspelheim", "d09": "d09_helheim", "d10": "d10_ragnarok"}
WORLD_NAME = "아홉 세계의 항해 - 노르드 RPG"

# client fog per biome used by the dungeons (the spawn keeps vanilla plains)
FOGS = {
    "stone_beach": ("misty_coast", "#8a9298", 18, 90), "swampland": ("misty_coast", "#8a9298", 18, 90),
    "roofed_forest": ("ironwood", "#3c4a3a", 12, 64), "mega_taiga": ("ironwood", "#3c4a3a", 12, 64),
    "lush_caves": ("caves", "#3d4a36", 10, 70), "river": ("caves", "#6f8a8a", 20, 110), "dripstone_caves": ("forge", "#4a3a2c", 10, 70),
    "stony_peaks": ("giants", "#a9b2ba", 24, 120), "extreme_hills": ("giants", "#a9b2ba", 24, 120), "taiga": ("giants", "#a9b2ba", 24, 120),
    "deep_ocean": ("naglfar", "#3a2f48", 14, 72),
    "basalt_deltas": ("muspel", "#6e2a1c", 12, 72), "crimson_forest": ("muspel", "#6e2a1c", 12, 72),
    "soulsand_valley": ("hel", "#2f3a44", 8, 52), "deep_dark": ("hel_deep", "#151a20", 6, 40),
    "meadow": ("asgard", "#f2dcae", 60, 220), "cherry_grove": ("asgard", "#f2dcae", 60, 220),
}
WATER = {"deep_ocean": "#2a2338", "soulsand_valley": "#1c2630", "deep_dark": "#141a20", "swampland": "#4c5a50", "stone_beach": "#3d5560"}
PRECIP = {"basalt_deltas": {"ash": 0.12}, "crimson_forest": {"red_spores": 0.1}, "soulsand_valley": {"blue_spores": 0.04},
          "deep_dark": {"blue_spores": 0.02}}


def client_biomes(rp):
    """Fog definitions and client biome overrides (atmosphere per dungeon)."""
    os.makedirs(os.path.join(rp, "fogs"), exist_ok=True)
    os.makedirs(os.path.join(rp, "biomes"), exist_ok=True)
    done = set()
    for biome, (fog, col, start, end) in FOGS.items():
        if fog not in done:
            done.add(fog)
            json.dump({"format_version": "1.16.100", "minecraft:fog_settings": {
                "description": {"identifier": "nrpg:fog_" + fog},
                "distance": {
                    "air": {"fog_start": start, "fog_end": end, "fog_color": col, "render_distance_type": "fixed"},
                    "weather": {"fog_start": start * 0.6, "fog_end": end * 0.7, "fog_color": col, "render_distance_type": "fixed"},
                    "water": {"fog_start": 0, "fog_end": 30, "fog_color": WATER.get(biome, "#2a3a4a"), "render_distance_type": "fixed"},
                }}}, open(os.path.join(rp, "fogs", fog + ".json"), "w"), indent=1)
        comps = {"minecraft:fog_appearance": {"fog_identifier": "nrpg:fog_" + fog}}
        if biome in WATER:
            comps["minecraft:water_appearance"] = {"surface_color": WATER[biome], "surface_opacity": 0.85}
        if biome in PRECIP:
            comps["minecraft:precipitation"] = PRECIP[biome]
        json.dump({"format_version": "1.21.120", "minecraft:client_biome": {"description": {"identifier": biome}, "components": comps}},
                  open(os.path.join(rp, "biomes", biome + ".client_biome.json"), "w"), indent=1)


def box6(b):
    return [int(v) for v in b]


def world_info(world_data):
    """Coordinates for server owners: harbour stations, ships, every dungeon's start, zones, boss arenas and exits."""
    S, W = world_data["SPAWN"], world_data["WORLDS"]
    ROLE = {"final": "최종 보스", "mid1": "중간 보스 1", "mid2": "중간 보스 2"}
    info = dict(world_spawn=S["arrival"][:3], spawn=dict(
        name="미드가르드 항구 빅", region=S["region"], enhance_anvil=S["stations"].get("enhance", []),
        norn_well=S["stations"].get("daily", []), training_dummies=S.get("dummies", []),
        ships=[dict(dungeon=s["dungeon"], deck=s["deck"], sign=s["sign"]) for s in S["ships"]]), dungeons={})
    for d in D.DUNGEONS:
        did = d["id"]
        if did not in W:
            continue
        w = W[did]
        info["dungeons"][did] = dict(
            name=d["ko"], en=d["en"], tier=D.TIERS[d["tier"]]["ko"], level=D.TIERS[d["tier"]]["lv"], realm=d["realm"],
            region=w["region"], start=w["start"][:3], return_ship_deck=w["ret"]["deck"], exit_portal=w["exit"],
            zones=[dict(id=z["key"], name=z["ko"], box=z["box"], mobs=z["mobs"]) for z in world_data["ZONES"] if z["dungeon"] == did],
            bosses=[dict(id=a["boss"], name=D.BOSSES[a["boss"]]["ko"], role=ROLE[a["role"]], hp=D.BOSSES[a["boss"]]["hp"],
                         center=[a["x"], a["y"], a["z"]], radius=a["r"]) for a in world_data["ARENAS"] if a["dungeon"] == did])
    info["scriptevents"] = {
        "nrpg:sail <d01..d10>": "실행한 플레이어를 그 던전 시작 지점으로 보냄",
        "nrpg:home": "항구로 귀환", "nrpg:clearall": "모든 항로 개방", "nrpg:enh <0-10>": "손에 든 장비의 강화 단계를 지정",
        "nrpg:test <arena> [skill ...]": "허수아비를 상대로 보스 소환(스킬 시험)", "nrpg:status": "보스 전투 상태를 콘솔에 출력",
        "nrpg:reset": "모든 보스 방 초기화", "nrpg:kill <arena>": "그 방의 보스 처치", "nrpg:hurt <arena> <0-1>": "보스 체력을 비율만큼 깎음",
        "nrpg:zones": "사냥터 몹 수", "nrpg:zonetest [dungeon]": "사냥터 몹 소환 시험", "nrpg:mobtest <x y z>": "모든 몹 종류 소환 시험"}
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only", default="")
    ap.add_argument("--keep", default=None)
    ap.add_argument("--repack", action="store_true")
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    if args.repack:
        if not args.keep or not os.path.isdir(os.path.join(args.keep, "world", "db")):
            sys.exit("--repack needs --keep <work dir> of an earlier full build")
        world_data = json.load(open(os.path.join(out, "world_data.json"), encoding="utf8"))
        report = json.load(open(os.path.join(out, "build_report.json"), encoding="utf8"))
        finish_world(out, os.path.join(args.keep, "world"), world_data, report, None, t0)
        return
    only = [s for s in args.only.split(",") if s] or list(MODULES)
    report = {}

    wdir = NP.new_world_dir(args.keep)
    db = NP.DB(os.path.join(wdir, "db"))

    # ---- the harbour
    signs = {d["id"]: dict(d, tier_ko=D.TIERS[d["tier"]]["ko"], lv=D.TIERS[d["tier"]]["lv"]) for d in D.DUNGEONS}
    S = nr_spawn.build(dungeons=signs)
    sp = S.S if hasattr(S, "S") else S
    arrival = list(sp.points["arrival"])
    SPAWN = dict(
        arrival=[round(v, 2) for v in arrival],
        region=[nr_spawn.X0, nr_spawn.Y0, nr_spawn.Z0, nr_spawn.X0 + nr_spawn.SX - 1, nr_spawn.Y0 + nr_spawn.SY - 1, nr_spawn.Z0 + nr_spawn.SZ - 1],
        ships=[dict(dungeon=s["dungeon"], deck=box6(s["deck"]), sign=list(s["sign"])) for s in sp.ships],
        stations={k: [list(map(int, p)) for p in v] for k, v in sp.stations.items()},
        dummies=[list(p) for p in sp.points.get("dummies", [])],
    )
    db.put_area(sp.a)
    report["spawn"] = dict(ships=len(sp.ships), seconds=round(time.time() - t0, 1))
    print("spawn done %.1fs" % (time.time() - t0))
    del S, sp

    # ---- the dungeons
    ARENAS, ZONES, WORLDS = [], [], {}
    for did in only:
        t1 = time.time()
        mod = importlib.import_module(MODULES[did])
        d = mod.build()
        if did == "d05":
            d.a.bio[:, :] = 24                    # the world's-end coast: its own dark fog
        out_v, rep = nr_verify.verify_dungeon(d, fix_traps=True, rounds=3)
        gates = nr_verify.gate_check(d)
        bypass = [not st["exit"] for st in gates[:-1]]
        ex = d.export()
        ARENAS += ex["arenas"]
        ZONES += ex["zones"]
        WORLDS[did] = dict(region=ex["region"], start=[round(v, 2) for v in ex["start"]],
                           ret=ex["ret"], exit=ex["exit"], ambient=ex.get("ambient", []))
        db.put_area(d.a)
        report[did] = dict(reachable=out_v["reachable"], trapped=out_v["trapped"], filled=out_v["auto_filled"], escape=out_v.get("escape"),
                           missing=out_v["missing"], gates_hold=all(bypass), stages=[(len(s["zones"]), s["exit"]) for s in gates],
                           seconds=round(time.time() - t1, 1))
        print(did, json.dumps(report[did], ensure_ascii=False))
        del d, mod

    world_data = dict(ARENAS=ARENAS, ZONES=ZONES, SPAWN=SPAWN, WORLDS=WORLDS)
    json.dump(world_data, open(os.path.join(out, "world_data.json"), "w"), ensure_ascii=False)
    finish_world(out, wdir, world_data, report, db, t0)


def finish_world(out, wdir, world_data, report, db, t0):
    """Packs, level.dat, icon, .mcworld, .mcpack files and the reports."""
    arrival = world_data["SPAWN"]["arrival"]
    import nr_models
    packs = nr_pack.build(os.path.join(out, "packs"), world_data, nr_models)
    client_biomes(packs["rp"])

    # ---- world
    I, By = an.IntTag, an.ByteTag
    v = (1, 21, 90, 0, 0)
    overrides = {
        "Difficulty": I(2), "GameType": I(2), "dodaylightcycle": By(1), "falldamage": By(1), "firedamage": By(1),
        "drowningdamage": By(1), "freezedamage": By(1), "pvp": By(0), "showcoordinates": By(1), "randomtickspeed": I(1),
        "doentitydrops": By(1),                   # boss loot tables (the other defaults stay: no natural spawns, keep inventory)
        "lastOpenedWithVersion": an.ListTag([I(x) for x in v]), "MinimumCompatibleClientVersion": an.ListTag([I(x) for x in v]),
    }
    icon = None
    try:
        from PIL import Image
        icon = Image.open(os.path.join(out, "previews", "spawn_harbour.png")) if os.path.exists(os.path.join(out, "previews", "spawn_harbour.png")) else None
    except Exception:
        icon = None
    mcworld = os.path.join(out, "NorseRPG.mcworld")
    NP.finish(wdir, mcworld, WORLD_NAME, (int(arrival[0]), int(arrival[1]), int(arrival[2])), packs=packs, icon=icon,
              overrides=overrides, db=db)
    nr_pack.mcpack(packs["bp"], os.path.join(out, "NorseRPG_behavior.mcpack"))
    nr_pack.mcpack(packs["rp"], os.path.join(out, "NorseRPG_resources.mcpack"))
    if db is not None:                            # a repack keeps the full build's timings
        report["total_seconds"] = round(time.time() - t0, 1)
    json.dump(report, open(os.path.join(out, "build_report.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(world_info(world_data), open(os.path.join(out, "world_info.json"), "w"), ensure_ascii=False, indent=1)
    print("all done %.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
