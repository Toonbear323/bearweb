"""Behavior pack: first-run setup (NPCs, scoreboards), shop dialogues and helper functions."""
import json
import os

from abilities import ABILITIES, START_COINS

PACK_UUID = "6f1d3c52-2a8e-4c41-9a35-6b7b1f0c4a11"
MODULE_UUID = "a83e1f0e-5c6d-4f2b-8e77-0d9c2b1a5e22"
SCRIPT_UUID = "c5b2e7d4-1f3a-4b6c-9d8e-7a2f4c6b1e33"
SCRIPT_API = "1.11.0"      # @minecraft/server stable version (Minecraft 1.21.0+)

# TP items: (key, vanilla item, display name, title, hotbar slot)
TP_ITEMS = [
    ("lobby", "minecraft:nether_star", "§l§e로비 (스폰)으로 이동", "§l§e로비", 4),
    ("forest", "minecraft:emerald", "§l§a1. 숲으로 이동", "§l§a숲", 5),
    ("volcano", "minecraft:blaze_powder", "§l§c2. 화산으로 이동", "§l§c화산", 6),
    ("paradise", "minecraft:heart_of_the_sea", "§l§b3. 파라다이스로 이동", "§l§b파라다이스", 7),
    ("factory", "minecraft:iron_ingot", "§l§74. 공장으로 이동", "§l§7공장", 8),
]
PACK_NAME = "ability_tag_bp"
VERSION = [1, 0, 0]


def rt(text):
    return {"rawtext": [{"text": text}]}


def tellraw(sel, text):
    return "tellraw %s %s" % (sel, json.dumps(rt(text), ensure_ascii=False))


def effect_cmds(ab, sel="@s"):
    out = []
    for (eff, amp, dur) in ab["effects"]:
        out.append("effect %s %s %s %d true" % (sel, eff, dur, amp))
    return out


def write_pack(root, lobby, maps, spawn):
    """root: behavior_packs/<name> directory."""
    os.makedirs(root, exist_ok=True)
    fdir = os.path.join(root, "functions", "at")
    os.makedirs(os.path.join(fdir, "shop"), exist_ok=True)
    os.makedirs(os.path.join(fdir, "tp"), exist_ok=True)
    os.makedirs(os.path.join(fdir, "ability"), exist_ok=True)
    os.makedirs(os.path.join(root, "dialogue"), exist_ok=True)

    manifest = {
        "format_version": 2,
        "header": {
            "name": "능력 술래잡기 시스템",
            "description": "로비 NPC / 능력 상점 / 코인 / 맵 이동 함수",
            "uuid": PACK_UUID,
            "version": VERSION,
            "min_engine_version": [1, 21, 60],
        },
        "modules": [
            {"type": "data", "uuid": MODULE_UUID, "version": VERSION},
            {"type": "script", "language": "javascript", "uuid": SCRIPT_UUID, "version": VERSION,
             "entry": "scripts/main.js"},
        ],
        "dependencies": [{"module_name": "@minecraft/server", "version": SCRIPT_API}],
    }
    json.dump(manifest, open(os.path.join(root, "manifest.json"), "w", encoding="utf8"), ensure_ascii=False, indent=2)
    json.dump({"values": ["at/tick"]}, open(os.path.join(root, "functions", "tick.json"), "w"), indent=2)

    def fn(name, lines):
        with open(os.path.join(fdir, name + ".mcfunction"), "w", encoding="utf8") as f:
            f.write("\n".join(lines) + "\n")

    sx, sy, sz = spawn
    marker_tests = " ".join("if block %d %d %d %s" % m for m in lobby.markers)

    # ---- tick ---------------------------------------------------------------------------
    fn("tick", [
        "# runs every tick",
        "scoreboard objectives add at_sys dummy",
        "scoreboard players add setup_done at_sys 0",
        "# keep the lobby loaded so the NPC setup can always run (fails harmlessly once it exists)",
        "execute if score setup_done at_sys matches 0 run tickingarea add -64 0 -64 79 0 63 at_lobby true",
        "execute if score setup_done at_sys matches 0 %s run function at/setup" % marker_tests,
        "execute as @a[tag=!at_joined] run function at/first_join",
        "scoreboard players add timer at_sys 1",
        "execute if score timer at_sys matches 40.. run function at/refresh",
    ])
    vol = maps["volcano"]
    fn("refresh", [
        "# every 2 seconds",
        "scoreboard players set timer at_sys 0",
        "scoreboard players add @a coin 0",
        "scoreboard players add @a ability 0",
        "# lava is everywhere in the volcano map: keep players fire resistant there",
        "effect @a[x=%d,y=0,z=%d,dx=224,dy=255,dz=224] fire_resistance 30 0 true" % (vol.a.x0, vol.a.z0),
    ] + ["execute as @e[type=npc,tag=%s] run dialogue change @s %s" % (n["tag"], n["scene"])
         for n in lobby.npcs if n["scene"]])

    # ---- setup (first run) -------------------------------------------------------------
    setup = [
        "# first run: scoreboards, rules and lobby NPCs",
        "scoreboard objectives add coin dummy \"§6코인\"",
        "scoreboard objectives add ability dummy \"능력\"",
        "scoreboard objectives setdisplay sidebar coin",
        "setworldspawn %d %d %d" % (sx, sy, sz),
        "gamerule domobspawning false",
        "gamerule dodaylightcycle false",
        "gamerule doweathercycle false",
        "gamerule falldamage false",
        "gamerule firedamage false",
        "gamerule drowningdamage false",
        "gamerule dofiretick false",
        "gamerule mobgriefing false",
        "gamerule keepinventory true",
        "gamerule randomtickspeed 0",
        "gamerule doimmediaterespawn true",
        "gamerule spawnradius 0",
        "gamerule showtags false",
        "time set 12000",
        "weather clear",
    ]
    for n in lobby.npcs:
        setup.append("summon npc \"%s\" %.1f %d %.1f" % (n["name"], n["x"], n["y"], n["z"]))
        sel = "@e[type=npc,x=%.1f,y=%d,z=%.1f,r=1.5,tag=!at_npc]" % (n["x"], n["y"], n["z"])
        setup.append("tag %s add %s" % (sel, n["tag"]))
        fx, fy, fz = n["face"]
        setup.append("tp @e[type=npc,tag=%s,tag=!at_npc] %.1f %d %.1f facing %.1f %d %.1f" % (
            n["tag"], n["x"], n["y"], n["z"], fx, fy, fz))
        setup.append("tag @e[type=npc,tag=%s] add at_npc" % n["tag"])
        if n["scene"]:
            setup.append("execute as @e[type=npc,tag=%s] run dialogue change @s %s" % (n["tag"], n["scene"]))
    setup += [
        "scoreboard players set setup_done at_sys 1",
        tellraw("@a", "§d[능력 술래잡기] §f로비 설정이 완료되었습니다."),
    ]
    fn("setup", setup)

    fn("first_join", [
        "# runs once for every new player (as the player)",
        "scoreboard players set @s coin %d" % START_COINS,
        "scoreboard players set @s ability 0",
        "gamemode adventure @s",
        "tp @s %d %d %d facing %d %d %d" % (sx, sy, sz, sx, sy, sz - 20),
        tellraw("@s", "§d§l능력 술래잡기§r§f에 오신 것을 환영합니다!"),
        tellraw("@s", "§e%d 코인§f이 지급되었습니다. §7왼쪽 상점가에서 능력을 구매하세요." % START_COINS),
        "tag @s add at_joined",
    ])

    # ---- shop ---------------------------------------------------------------------------
    scenes = []
    for ab in ABILITIES:
        k = ab["key"]
        p = ab["price"]
        nm = ab["color"] + ab["name"]
        fn("shop/buy_" + k, [
            "scoreboard players add @s coin 0",
            "scoreboard players add @s ability 0",
            "execute if score @s ability matches %d run %s" % (ab["id"], tellraw("@s", "§e이미 %s§e 능력을 장착하고 있습니다." % nm)),
            "execute unless score @s ability matches %d if score @s coin matches ..%d run %s" % (
                ab["id"], p - 1, tellraw("@s", "§c코인이 부족합니다! §7(필요: %d 코인)" % p)),
            "execute unless score @s ability matches %d if score @s coin matches %d.. run function at/shop/grant_%s" % (
                ab["id"], p, k),
        ])
        fn("shop/grant_" + k, [
            "scoreboard players remove @s coin %d" % p,
            "scoreboard players set @s ability %d" % ab["id"],
            tellraw("@s", "§a구매 완료! %s§a 능력이 장착되었습니다. §7(게임 시작 시 적용)" % nm),
            "playsound random.levelup @s",
        ])
        scenes.append({
            "scene_tag": "shop_" + k,
            "npc_name": rt("%s§l%s 상인" % (ab["color"], ab["name"])),
            "text": rt("%s§l[%s]§r\n§f%s\n§7효과: %s\n\n§6가격: §e%d 코인\n§7(능력은 1개만 장착됩니다. 새로 사면 교체돼요)" % (
                ab["color"], ab["name"], ab["desc"], ab["detail"], p)),
            "buttons": [
                {"name": rt("구매하기 (%d 코인)" % p),
                 "commands": ["/execute as @initiator run function at/shop/buy_%s" % k]},
                {"name": rt("내 코인 확인"),
                 "commands": ["/execute as @initiator run function at/shop/balance"]},
            ],
        })
    fn("shop/balance", [
        "scoreboard players add @s coin 0",
        "tellraw @s " + json.dumps({"rawtext": [{"text": "§6보유 코인: §e"},
                                                 {"score": {"name": "@s", "objective": "coin"}},
                                                 {"text": "§6 코인"}]}, ensure_ascii=False),
    ])
    dialogue = {"format_version": "1.17", "minecraft:npc_dialogue": {"scenes": scenes}}
    json.dump(dialogue, open(os.path.join(root, "dialogue", "shop.diag.json"), "w", encoding="utf8"),
              ensure_ascii=False, indent=2)

    # ---- ability helpers (for the game logic) ------------------------------------------
    apply = ["# run as players when a round starts: function at/ability/apply"]
    for ab in ABILITIES:
        for c in effect_cmds(ab, "@s[scores={ability=%d}]" % ab["id"]):
            apply.append(c)
    fn("ability/apply", apply)
    fn("ability/clear", ["# remove all effects (fire resistance in the volcano is re-applied automatically)",
                         "effect @s clear"])
    fn("ability/reset", ["scoreboard players set @s ability 0"])
    os.makedirs(os.path.join(fdir, "coin"), exist_ok=True)
    for amt in (10, 50, 100):
        fn("coin/add%d" % amt, ["scoreboard players add @s coin %d" % amt])

    # ---- TP items (right-click to teleport; handled by scripts/main.js) ---------------------
    write_tp_script(root, maps, spawn)
    os.makedirs(os.path.join(fdir, "items"), exist_ok=True)
    fn("items/give", ["# give the missing TP items to @s (or everyone when run from the console)",
                      "scriptevent at:tpitems give"])
    fn("items/clear", ["scriptevent at:tpitems clear"])
    fn("items/auto_on", ["# hand out TP items automatically whenever a player spawns (default)",
                         "scriptevent at:tpitems auto_on"])
    fn("items/auto_off", ["scriptevent at:tpitems auto_off"])

    # ---- teleports ------------------------------------------------------------------------
    fn("tp/lobby", ["tp @s %d %d %d facing %d %d %d" % (sx, sy, sz, sx, sy, sz - 20)])
    for key, m in maps.items():
        x, y, z = m.spawns[0]
        fn("tp/" + key, ["tp @s %d %d %d" % (x, y, z)])
        for i, (x, y, z) in enumerate(m.spawns):
            fn("tp/%s_%d" % (key, i + 1), ["tp @s %d %d %d" % (x, y, z)])
    return manifest


def tp_destinations(maps, spawn):
    sx, sy, sz = spawn
    dests = []
    for key, item, name, title, slot in TP_ITEMS:
        if key == "lobby":
            pos = (sx + 0.5, sy, sz + 0.5)
            face = (sx + 0.5, sy + 1.6, sz - 20)
            where = "로비 스폰"
        else:
            m = maps[key]
            x, y, z = m.spawns[0]
            pos = (x + 0.5, y, z + 0.5)
            face = (m.cx + 0.5, y + 1.6, m.cz + 0.5)
            where = title.replace("§l", "")[2:] + " 맵 스폰"
        dests.append({
            "key": key, "item": item, "name": name, "slot": slot,
            "lore": ["§7우클릭하면 바로 이동합니다", "§8%s (%d, %d, %d)" % (where, pos[0], pos[1], pos[2])],
            "pos": {"x": pos[0], "y": pos[1], "z": pos[2]},
            "face": {"x": face[0], "y": face[1], "z": face[2]},
            "title": title, "subtitle": "§f이동 완료!",
        })
    return dests


def write_tp_script(root, maps, spawn):
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "tp_items.js"), encoding="utf8").read()
    dests = json.dumps(tp_destinations(maps, spawn), ensure_ascii=False, indent=2)
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    with open(os.path.join(root, "scripts", "main.js"), "w", encoding="utf8") as f:
        f.write(src.replace("__DESTS__", dests))
