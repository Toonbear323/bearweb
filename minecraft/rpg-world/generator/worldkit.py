"""Turn generated Areas into a finished .mcworld: LevelDB + level.dat + behaviour pack + icon + zip.

    from worldkit import package, write_behavior_pack
    pack = write_behavior_pack(tmp + "/bp", "My Map System", functions={...}, tick=["at/tick"],
                               scripts={"main.js": source})
    package([area1, area2], "out/MyMap.mcworld", "My Map", spawn=(0, 65, 0), pack=pack, icon=img)

Defaults suit minigame / adventure maps: adventure mode, peaceful, cheats on (functions, NPCs),
fixed time and weather, no mob spawning, no fall/fire/drowning damage, keep inventory,
instant respawn, random tick speed 0 (grass, leaves, coral, crops never change).
Override anything through `level_overrides` (NBT tags from amulet_nbt).
"""
import json
import os
import shutil
import tempfile
import time
import uuid

import amulet_nbt as an

from mcw import write_db, write_level_dat, zip_dir

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "data", "level_template.dat")
VOID_LAYERS = ('{"biome_id":1,"block_layers":[{"block_name":"minecraft:air","count":1}],'
               '"encoding_version":6,"structure_options":null,"world_version":"version.post_1_18"}\n')
SCRIPT_API = "1.11.0"        # @minecraft/server stable, Minecraft 1.21.0+, no experiments needed


def level_changes(name, spawn, game_type=2, time_of_day=6000, seed=1):
    I, By = an.IntTag, an.ByteTag
    sx, sy, sz = spawn
    return {
        "LevelName": an.StringTag(name),
        "GameType": I(game_type), "ForceGameType": By(0),
        "Generator": I(2), "FlatWorldLayers": an.StringTag(VOID_LAYERS),     # void world outside your areas
        "Difficulty": I(0),
        "SpawnX": I(sx), "SpawnY": I(sy), "SpawnZ": I(sz),
        "Time": an.LongTag(time_of_day), "currentTick": an.LongTag(0),
        "LastPlayed": an.LongTag(int(time.time())), "RandomSeed": an.LongTag(seed),
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


def write_behavior_pack(root, name, description="", functions=None, tick=None, scripts=None, extra_files=None,
                        version=(1, 0, 0)):
    """functions: {"at/tick": ["say hi", ...]} -> functions/at/tick.mcfunction
    tick: list of function names run every tick (functions/tick.json)
    scripts: {"main.js": source, "other.js": source} -> scripts/; main.js is the entry point
    extra_files: {"dialogue/shop.diag.json": dict_or_str, ...}
    UUIDs are derived from the pack name, so rebuilding keeps the same pack identity."""
    os.makedirs(root, exist_ok=True)
    ns = uuid.uuid5(uuid.NAMESPACE_URL, "bedrock-world-builder/" + name)
    pack_uuid = str(uuid.uuid5(ns, "pack"))
    modules = [{"type": "data", "uuid": str(uuid.uuid5(ns, "data")), "version": list(version)}]
    deps = []
    if scripts:
        modules.append({"type": "script", "language": "javascript", "uuid": str(uuid.uuid5(ns, "script")),
                        "version": list(version), "entry": "scripts/main.js"})
        deps.append({"module_name": "@minecraft/server", "version": SCRIPT_API})
    manifest = {"format_version": 2,
                "header": {"name": name, "description": description, "uuid": pack_uuid, "version": list(version),
                           "min_engine_version": [1, 21, 60]},
                "modules": modules}
    if deps:
        manifest["dependencies"] = deps
    json.dump(manifest, open(os.path.join(root, "manifest.json"), "w", encoding="utf8"), ensure_ascii=False, indent=2)
    for fname, lines in (functions or {}).items():
        path = os.path.join(root, "functions", fname + ".mcfunction")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf8").write("\n".join(lines) + "\n")
    if tick:
        os.makedirs(os.path.join(root, "functions"), exist_ok=True)
        json.dump({"values": list(tick)}, open(os.path.join(root, "functions", "tick.json"), "w"), indent=2)
    for fname, src in (scripts or {}).items():
        path = os.path.join(root, "scripts", fname)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf8").write(src)
    for fname, data in (extra_files or {}).items():
        path = os.path.join(root, fname)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(data, (dict, list)):
            json.dump(data, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=2)
        else:
            open(path, "w", encoding="utf8").write(data)
    return {"root": root, "uuid": pack_uuid, "version": list(version)}


def package(areas, out_file, name, spawn, pack=None, icon=None, level_overrides=None, keep_dir=None):
    """Write every Area into one world and zip it. Returns the world folder (for BDS tests)."""
    work = keep_dir or tempfile.mkdtemp(prefix="bwb_")
    wdir = os.path.join(work, "world")
    shutil.rmtree(wdir, ignore_errors=True)
    os.makedirs(wdir)
    nkeys = write_db(areas, os.path.join(wdir, "db"))
    changes = level_changes(name, spawn)
    changes.update(level_overrides or {})
    write_level_dat(os.path.join(wdir, "level.dat"), TEMPLATE, changes)
    open(os.path.join(wdir, "levelname.txt"), "w", encoding="utf8").write(name)
    if pack:
        dst = os.path.join(wdir, "behavior_packs", os.path.basename(pack["root"].rstrip("/")))
        shutil.copytree(pack["root"], dst)
        json.dump([{"pack_id": pack["uuid"], "version": pack["version"]}],
                  open(os.path.join(wdir, "world_behavior_packs.json"), "w"), indent=2)
        if icon is not None:
            icon.resize((256, 256)).save(os.path.join(dst, "pack_icon.png"))
    if icon is not None:
        icon.convert("RGB").save(os.path.join(wdir, "world_icon.jpeg"), quality=92)
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
    if os.path.exists(out_file):
        os.remove(out_file)
    zip_dir(wdir, out_file)
    print("wrote %s (%.2f MB, %d leveldb keys)" % (out_file, os.path.getsize(out_file) / 1e6, nkeys))
    return wdir
