"""Behaviour pack V1 generator: mcfunctions, loot tables and manifest for the Bear RPG systems."""
import json
import os
import shutil

from . import dkit as dk
from .catalog import DUNGEONS, GEAR, SELLS, SHOPS
import re

from .layout import G, NOFF, NX0, NX1, NZ0, NZ1, PLOT_COLS, PLOT_ROAD, PLOT_SIZE, PLOT_X0, TOWN_R

PACK_NAME = "BearRPG_BP_V1"
PACK_UUID = "6f2a1c5e-8b1d-4c7a-9e21-be4201000001"
MODULE_UUID = "6f2a1c5e-8b1d-4c7a-9e21-be4201000002"
PACK_VERSION = [1, 0, 0]
DIM = {0: "overworld", 1: "nether"}
SPAWN = (0.5, G + 3, 4.5)
REWARD_GEAR = {"plains": "sword_plains", "cave": "pick_miner", "desert": "helm_pharaoh", "ocean": "trident_tide",
               "hell": "sword_flame", "fortress": "bow_storm", "bastion": "axe_war"}
WARP_TITLE = {
    "town": ("§6베어 타운", "§7스폰 광장"), "plots": ("§d개인 집터", "§7서바이벌 구역 · 자유 건축"),
    "plains": ("§a초원 던전", "§7폐허의 성채"), "cave": ("§8동굴 던전", "§7수정 동굴"),
    "desert": ("§e사막 던전", "§7태양왕의 피라미드"), "ocean": ("§3바다 던전", "§7가라앉은 신전"),
    "hell": ("§c지옥 허브", "§7세 갈래 길"), "fortress": ("§4네더 요새", "§7위더의 성채"),
    "bastion": ("§6피글린 요새", "§7황금 보루"), "hell_dungeon": ("§c지옥 던전", "§7불타는 협곡"),
    "hellgate": ("§c지옥문", "§7화산 분화구"),
}


NETHER_IDS = ("hell", "fortress", "bastion")


def shift_cmd(c):
    """Move the x coordinates of a nether boss command by the export offset."""
    c = re.sub(r'^(summon \S+ (?:"[^"]*" )?)(-?\d+)( -?\d+ -?\d+)$', lambda m: m.group(1) + str(int(m.group(2)) + NOFF) + m.group(3), c)
    c = re.sub(r'\[([^\]]*?)x=(-?\d+)', lambda m: "[" + m.group(1) + "x=" + str(int(m.group(2)) + NOFF), c)
    return c


def raw(text):
    return json.dumps({"rawtext": [{"text": text}]}, ensure_ascii=False)


def fnum(v):
    return ("%.1f" % v) if isinstance(v, float) and v != int(v) else str(int(v))


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def loot_table(item, name, lore, enchants):
    fns = []
    if name:
        fns.append({"function": "set_name", "name": name})
    if lore:
        fns.append({"function": "set_lore", "lore": lore})
    if enchants:
        fns.append({"function": "specific_enchants", "enchants": [{"id": e, "level": l} for e, l in enchants]})
    if item == "enchanted_book":
        item = "book"
    return {"pools": [{"rolls": 1, "entries": [{"type": "item", "name": "minecraft:" + item, "weight": 1,
                                                 "functions": fns}]}]}


def build_pack(out_dir, icon=None):
    root = os.path.join(out_dir, PACK_NAME)
    if os.path.exists(root):
        shutil.rmtree(root)
    fn = os.path.join(root, "functions", "bear")
    os.makedirs(fn)
    manifest = {
        "format_version": 2,
        "header": {"name": "베어 RPG 행동 팩 V1", "description": "베어 RPG 맵 전용: 상점 · 워프 · 보스 · 보상 시스템 (V1)",
                   "uuid": PACK_UUID, "version": PACK_VERSION, "min_engine_version": [1, 19, 50]},
        "modules": [{"type": "data", "uuid": MODULE_UUID, "version": PACK_VERSION}],
    }
    json.dump(manifest, open(os.path.join(root, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"values": ["bear/tick"]}, open(os.path.join(root, "functions", "tick.json"), "w"))
    if icon and os.path.exists(icon):
        shutil.copy(icon, os.path.join(root, "pack_icon.png"))
    # ---- loot tables ---------------------------------------------------------------
    lt = os.path.join(root, "loot_tables", "bear")
    os.makedirs(lt)
    for gid, (item, name, lore, ench) in GEAR.items():
        json.dump(loot_table(item, name, lore, ench), open(os.path.join(lt, gid + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    # ---- tick ------------------------------------------------------------------------
    ids = list(DUNGEONS)
    tick = [
        'scoreboard objectives add gold dummy "§6§l골드"',
        "scoreboard objectives add bear_state dummy",
        "scoreboard objectives setdisplay sidebar gold",
        "scoreboard players add @a gold 0",
        "scoreboard players add st_zones_off bear_state 0",
    ]
    tick += ["scoreboard players add st_%s bear_state 0" % d for d in ids]
    tick += [
        "execute as @a[tag=!bear_joined] run function bear/init_player",
        "execute unless score st_zones_off bear_state matches 1 run function bear/zones",
        "tag @a[%s,tag=!bear_hero] add bear_hero_new" % ",".join("tag=clr_" + d for d in ids),
        "execute as @a[tag=bear_hero_new] run function bear/hero",
    ]
    write(os.path.join(fn, "tick.mcfunction"), tick)
    sx, sy, sz = SPAWN
    write(os.path.join(fn, "init_player.mcfunction"), [
        "tp @s %s %d %s facing %s %d %s" % (fnum(sx), sy, fnum(sz), fnum(sx), sy + 1, fnum(sz - 30)),
        "spawnpoint @s %d %d %d" % (int(sx), sy, int(sz)),
        "scoreboard players add @s gold 50",
        "give @s stone_sword 1",
        "give @s bread 16",
        "give @s torch 16",
        "give @s leather_chestplate 1",
        "title @s title §6§l베어 RPG",
        "title @s subtitle §f모험을 시작하세요!",
        "tellraw @s " + raw("§6[베어 RPG] §f환영합니다! 시작 지원금 §650 골드§f와 기본 장비를 지급했습니다."),
        "tellraw @s " + raw("§7· 북쪽 대로: 상점가  · 서쪽 대로: 차원문 신전(던전 이동)  · 동쪽 대로: 모험가 길드(전리품 판매)"),
        "tellraw @s " + raw("§7· 서문 밖 주택단지에서는 자유롭게 집을 지을 수 있습니다."),
        "playsound random.levelup @s",
        "tag @s add bear_joined",
    ])
    write(os.path.join(fn, "hero.mcfunction"), [
        "tag @s add bear_hero",
        "tag @s remove bear_hero_new",
        "scoreboard players add @s gold 3000",
        'loot give @s loot "bear/sword_hero"',
        "title @s title §6§l전설의 용사",
        "title @s subtitle §f모든 던전을 정복했습니다!",
        "tellraw @a " + json.dumps({"rawtext": [{"text": "§6§l[베어 RPG] §r§e"}, {"selector": "@s"},
                                                 {"text": " §f님이 모든 던전을 정복하고 §6전설의 용사§f가 되었습니다!"}]},
                                   ensure_ascii=False),
        "playsound random.levelup @a",
    ])
    # ---- zones -------------------------------------------------------------------------------
    zl = ["tag @a remove bear_in"]
    t = TOWN_R + 6
    zones = [(-t, 40, -t, t, 150, t)] + list(dk.REG["zones"][0])
    for (x0, y0, z0, x1, y1, z1) in zones:
        zl.append("tag @a[x=%d,y=%d,z=%d,dx=%d,dy=%d,dz=%d] add bear_in" % (x0, y0, z0, x1 - x0, y1 - y0, z1 - z0))
    zl += [
        "execute in nether run tag @a[x=%d,y=-64,z=%d,dx=%d,dy=400,dz=%d] add bear_in" % (NX0 + NOFF, NZ0, NX1 - NX0, NZ1 - NZ0),
        "gamemode adventure @a[tag=bear_in,m=survival,tag=!bear_admin]",
        "gamemode survival @a[tag=!bear_in,m=adventure,tag=!bear_admin]",
    ]
    write(os.path.join(fn, "zones.mcfunction"), zl)
    write(os.path.join(fn, "admin", "zones_off.mcfunction"), [
        "scoreboard players set st_zones_off bear_state 1",
        "tellraw @s " + raw("§e[관리] 구역별 게임 모드 전환을 껐습니다."),
    ])
    write(os.path.join(fn, "admin", "zones_on.mcfunction"), [
        "scoreboard players set st_zones_off bear_state 0",
        "tellraw @s " + raw("§e[관리] 구역별 게임 모드 전환을 켰습니다."),
    ])
    write(os.path.join(fn, "admin", "gold.mcfunction"), [
        "scoreboard players add @s gold 1000",
        "tellraw @s " + raw("§e[관리] 1000 골드를 지급했습니다."),
    ])
    write(os.path.join(fn, "admin", "reset_bosses.mcfunction"),
          ["scoreboard players set st_%s bear_state 0" % d for d in ids] +
          ["kill @e[tag=boss_%s]" % d for d in ids] +
          ["tellraw @s " + raw("§e[관리] 모든 보스 상태를 초기화했습니다.")])
    # ---- warps ----------------------------------------------------------------------------------
    warps = dict(dk.REG["warps"])
    warps["town"] = (0, sx, sy, sz, (sx, sy + 1, sz - 30))
    px = PLOT_X0 + PLOT_COLS * PLOT_SIZE + (PLOT_COLS + 1) * PLOT_ROAD + 4
    warps["plots"] = (0, px + 0.5, G + 1, 0.5, (px - 20, G + 2, 0))
    for wid, (dim, x, y, z, face) in warps.items():
        title, sub = WARP_TITLE.get(wid, (wid, ""))
        if dim == 1:
            x += NOFF
            face = (face[0] + NOFF, face[1], face[2]) if face else None
        tp = "execute as @a[tag=bear_w] in %s run tp @s %s %s %s" % (DIM[dim], fnum(x), fnum(y), fnum(z))
        if face:
            tp += " facing %s %s %s" % (fnum(face[0]), fnum(face[1]), fnum(face[2]))
        write(os.path.join(fn, "warp", wid + ".mcfunction"), [
            "tag @p[r=5] add bear_w",
            tp,
            "effect @a[tag=bear_w] resistance 4 4 true",
            "execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~",
            "title @a[tag=bear_w] title " + title,
            "title @a[tag=bear_w] subtitle " + sub,
            "tag @a remove bear_w",
        ])
    # ---- shops -------------------------------------------------------------------------------------
    for shop, items in SHOPS.items():
        for (sid, label, price, cmds) in items:
            name = label.split("\n")[0]
            lines = [
                "tag @p[r=7] add bear_c",
                "tag @a[tag=bear_c,scores={gold=%d..}] add bear_b" % price,
            ]
            lines += ["execute as @a[tag=bear_b] run " + c for c in cmds]
            lines += [
                "scoreboard players remove @a[tag=bear_b] gold %d" % price,
                "execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~",
                "tellraw @a[tag=bear_b] " + raw("§a[상점] §f%s 구매 완료! §7(-%d 골드)" % (name, price)),
                "tellraw @a[tag=bear_c,tag=!bear_b] " + raw("§c[상점] 골드가 부족합니다. §7(%s: %d 골드)" % (name, price)),
                "execute as @a[tag=bear_c,tag=!bear_b] at @s run playsound note.bass @s ~ ~ ~",
                "tag @a remove bear_b",
                "tag @a remove bear_c",
            ]
            write(os.path.join(fn, "shop", sid + ".mcfunction"), lines)
    for (sid, label, item, cnt, gold) in SELLS:
        write(os.path.join(fn, "sell", sid + ".mcfunction"), [
            "tag @p[r=7] add bear_c",
            "tag @a[tag=bear_c,hasitem={item=%s,quantity=%d..}] add bear_b" % (item, cnt),
            "clear @a[tag=bear_b] %s -1 %d" % (item, cnt),
            "scoreboard players add @a[tag=bear_b] gold %d" % gold,
            "execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~",
            "tellraw @a[tag=bear_b] " + raw("§a[길드] §f%s 판매! §6(+%d 골드)" % (label, gold)),
            "tellraw @a[tag=bear_c,tag=!bear_b] " + raw("§c[길드] 판매할 물건이 부족합니다. §7(%s)" % label),
            "tag @a remove bear_b",
            "tag @a remove bear_c",
        ])
    # ---- dungeons -------------------------------------------------------------------------------------
    for did, (nm, gold, rec, colr) in DUNGEONS.items():
        a, b_ = nm.split(" · ")
        write(os.path.join(fn, "enter", did + ".mcfunction"), [
            "title @p[r=5] title %s%s" % (colr, a),
            "title @p[r=5] subtitle §7%s" % b_,
            "tellraw @p[r=5] " + raw("%s[%s] §f%s §8(권장: %s)" % (colr, a, b_, rec)),
        ])
        boss = dk.REG["boss"].get(did)
        if boss:
            spawn = [shift_cmd(c) for c in boss["spawn"]] if did in NETHER_IDS else list(boss["spawn"])
            write(os.path.join(fn, "boss", did + ".mcfunction"), [
                "execute if score st_%s bear_state matches 0 run function bear/boss/%s_spawn" % (did, did),
            ])
            write(os.path.join(fn, "boss", did + "_spawn.mcfunction"),
                  ["scoreboard players set st_%s bear_state 1" % did] + spawn + [
                      "title @a[r=48] title " + boss["title"],
                      "title @a[r=48] subtitle " + boss["sub"],
                      "playsound mob.wither.spawn @a[r=48]",
                  ])
        repeat = max(20, gold // 4)
        write(os.path.join(fn, "clear", did + ".mcfunction"), [
            "execute if entity @e[tag=boss_%s] run tellraw @a[r=12] %s" % (did, raw("§c보스가 아직 살아 있습니다!")),
            "execute unless entity @e[tag=boss_%s] if score st_%s bear_state matches 0 run tellraw @a[r=12] %s" % (
                did, did, raw("§7보스를 처치한 뒤에 보상을 받을 수 있습니다.")),
            "execute unless entity @e[tag=boss_%s] if score st_%s bear_state matches 1 run function bear/clear/%s_ok" % (
                did, did, did),
        ])
        write(os.path.join(fn, "clear", did + "_ok.mcfunction"), [
            "scoreboard players set st_%s bear_state 0" % did,
            "tag @a[r=30,tag=!clr_%s] add bear_first" % did,
            "scoreboard players add @a[r=30,tag=bear_first] gold %d" % gold,
            "scoreboard players add @a[r=30,tag=!bear_first] gold %d" % repeat,
            'execute as @a[tag=bear_first] run loot give @s loot "bear/%s"' % REWARD_GEAR[did],
            "tellraw @a[r=30,tag=bear_first] " + raw("§6[보상] §f%s 최초 클리어! §6+%d 골드 §f와 특별 장비를 받았습니다." % (a, gold)),
            "tellraw @a[r=30,tag=!bear_first] " + raw("§6[보상] §f%s 클리어! §6+%d 골드" % (a, repeat)),
            "tellraw @a " + json.dumps({"rawtext": [{"text": "§6[베어 RPG] §e"}, {"selector": "@a[r=30]"},
                                                     {"text": " §f님이 %s%s§f을(를) 클리어했습니다!" % (colr, a)}]},
                                       ensure_ascii=False),
            "tag @a[tag=bear_first] add clr_%s" % did,
            "tag @a remove bear_first",
            "playsound random.levelup @a[r=30]",
            "summon fireworks_rocket ~ ~3 ~",
        ])
    wp = dk.REG.get("wither_pos")
    if wp:
        write(os.path.join(fn, "boss", "wither.mcfunction"), [
            "execute if entity @e[type=wither] run tellraw @a[r=16] " + raw("§c위더가 이미 소환되어 있습니다!"),
            "execute unless entity @e[type=wither] run tellraw @a[r=48] " + raw("§4§l최종 도전: 위더가 전당에 나타났습니다!"),
            "execute unless entity @e[type=wither] run summon wither %d %d %d" % (wp[0] + NOFF, wp[1], wp[2]),
        ])
    return root


def pack_icon(path):
    """Simple bear-face icon."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (128, 128), (46, 110, 78))
    d = ImageDraw.Draw(im)
    brown, tan, dark = (124, 82, 48), (214, 178, 132), (30, 22, 18)
    d.ellipse((14, 14, 50, 50), fill=brown)
    d.ellipse((78, 14, 114, 50), fill=brown)
    d.ellipse((22, 22, 42, 42), fill=tan)
    d.ellipse((86, 22, 106, 42), fill=tan)
    d.ellipse((18, 26, 110, 116), fill=brown)
    d.ellipse((44, 66, 84, 104), fill=tan)
    d.ellipse((40, 50, 50, 62), fill=dark)
    d.ellipse((78, 50, 88, 62), fill=dark)
    d.ellipse((56, 70, 72, 82), fill=dark)
    d.line((64, 82, 64, 92), fill=dark, width=3)
    d.arc((52, 84, 64, 98), 0, 180, fill=dark, width=3)
    d.arc((64, 84, 76, 98), 0, 180, fill=dark, width=3)
    im.save(path)
