"""Behaviour pack, level.dat settings, icon, previews and world_info.json for the RPG world."""
import json
import os
import tempfile

import amulet_nbt as an
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import render
import lighting
from worldkit import write_behavior_pack, package as wk_package
from rpg_world import X0, Z0, SX, SZ
from rpg_parts import HUNT_LIGHT

PACK_NAME = "RPG Adventure Road System"
REGION_KO = {"spawn": "스폰 (뽑기장)", "farm": "농장", "cave": "초급 던전: 동굴", "village": "점령된 마을",
             "hq": "보스: 우민 본거지", "beach": "해변", "deepsea": "보스: 심해 신전", "nether": "지옥",
             "castle": "마왕성", "dungeon": "보스: 마왕성 지하감옥", "deepdark": "워든 서식지"}
HUNT_KEY = {"초보자 훈련장": "spawn_training", "들판 사냥터": "farm_field", "동굴 사냥터": "cave",
            "점령지 광장": "village_square", "근위대 훈련장": "hq_barracks", "해안 사냥터": "beach_cove",
            "가라앉은 회랑": "deepsea_gallery", "요새 사냥터": "nether_fortress", "마왕군 연병장": "castle_drill",
            "감방 구역": "dungeon_cells", "고대 도시 사냥터": "deepdark_plaza"}
HUNT_MOBS = {"spawn_training": ["zombie", "zombie", "spider"],
             "farm_field": ["zombie", "spider", "slime", "zombie"],
             "cave": ["zombie", "skeleton", "spider", "cave_spider"],
             "village_square": ["pillager", "vindicator", "pillager", "pillager"],
             "hq_barracks": ["vindicator", "pillager", "vindicator", "witch"],
             "beach_cove": ["drowned", "husk", "drowned"],
             "deepsea_gallery": ["drowned", "drowned", "drowned", "zombie"],
             "nether_fortress": ["blaze", "wither_skeleton", "magma_cube", "zombie_pigman"],
             "castle_drill": ["wither_skeleton", "skeleton", "stray", "witch"],
             "dungeon_cells": ["skeleton", "zombie", "stray", "wither_skeleton"],
             "deepdark_plaza": ["skeleton", "zombie", "silverfish"]}
BOSS_FN = {"hq": [("evocation_illager", "§c§l우민 대장군", 0), ("vindicator", "§c근위병", 2), ("vindicator", "§c근위병", -2)],
           "deepsea": [("elder_guardian", "§b§l심해의 수호자", 0)],
           "dungeon": [("wither_skeleton", "§4§l마왕의 처형인", 0), ("skeleton", "§7옥졸", 3), ("skeleton", "§7옥졸", -3)]}


def rt(text):
    return json.dumps({"rawtext": [{"text": text}]}, ensure_ascii=False)


def functions(W):
    fn = {}
    fn["rpg/tick"] = [
        "scoreboard objectives add rpg_sys dummy",
        "scoreboard players add setup_done rpg_sys 0",
        "scoreboard players add animals_done rpg_sys 0",
        "execute if score setup_done rpg_sys matches 0 run function rpg/setup",
    ]
    if W.markers:
        cond = " ".join("if block %d %d %d lodestone" % m for m in W.markers)
        fn["rpg/tick"].append("execute if score animals_done rpg_sys matches 0 %s run function rpg/setup_animals"
                              % cond)
    fn["rpg/setup"] = [
        "gamerule domobspawning false", "gamerule mobgriefing false", "gamerule dofiretick false",
        "gamerule respawnblocksexplode false", "gamerule tntexplodes false",
        "gamerule projectilescanbreakblocks false", "gamerule spawnradius 0",
        "scoreboard players set setup_done rpg_sys 1",
    ]
    fn["rpg/setup_animals"] = ["summon %s %d %d %d" % (e, x, y, z) for (e, x, y, z) in W.animals] + \
        ["scoreboard players set animals_done rpg_sys 1"]
    # admin teleports
    for k, (x, y, z) in W.spawns.items():
        fn["rpg/tp/" + k] = ["tp @s %d %d %d" % (x, y, z),
                             "tellraw @s " + rt("§e[RPG] §f%s 으로 이동했습니다" % REGION_KO.get(k, k))]
    # hunting grounds: sample waves and light switches
    for h in W.hunts:
        key = HUNT_KEY[h["name"]]
        mobs = HUNT_MOBS[key]
        lines = []
        for i, (x, y, z) in enumerate(h["spawn_points"]):
            lines.append("summon %s %d %d %d" % (mobs[i % len(mobs)], x, y, z))
        lines.append("tellraw @s " + rt("§c[사냥터] §f%s 에 예시 몬스터를 소환했습니다 (함수 rpg/hunt/%s 를 고쳐 쓰세요)"
                                       % (h["name"], key)))
        fn["rpg/hunt/" + key] = lines
        x1, y1, z1, x2, y2, z2 = h["box"]
        fn["rpg/arena/%s_off" % key] = [
            "fill %d %d %d %d %d %d air replace light_block_%d" % (x1, y1, z1, x2, y2 + 2, z2, HUNT_LIGHT),
            "tellraw @s " + rt("§c[사냥터] §f%s 조명을 껐습니다 (자연 스폰 가능)" % h["name"])]
        fn["rpg/arena/%s_on" % key] = ["setblock %d %d %d light_block_%d" % (x, y, z, HUNT_LIGHT)
                                       for (x, y, z) in h["lights"]] + [
            "tellraw @s " + rt("§a[사냥터] §f%s 조명을 켰습니다" % h["name"])]
    # sample bosses
    for b in W.bosses:
        x, y, z = b["boss_spawn"]
        lines = []
        for (e, name, dz) in BOSS_FN[b["region"]]:
            lines.append('summon %s "%s" %d %d %d' % (e, name, x, y, z + dz))
        lines.append("tellraw @s " + rt("§4[보스] §f%s 에 예시 보스를 소환했습니다 (함수 rpg/boss/%s 를 고쳐 쓰세요)"
                                       % (b["name"], b["region"])))
        fn["rpg/boss/" + b["region"]] = lines
    # gacha hooks (called by the script when a machine button is pressed)
    for g in W.gacha:
        fn[g["function"]] = [
            "tellraw @s " + rt("§6[뽑기] §f%s§r§f 기계를 돌렸습니다! §7(이 함수 %s 에 보상 명령을 넣으세요)"
                               % (g["label"], g["function"])),
            "playsound random.levelup @s",
        ]
    fn["rpg/help"] = ["tellraw @s " + rt(t) for t in [
        "§6==== RPG 월드 관리자 함수 ====",
        "§e/function rpg/tp/<지역>§f : " + ", ".join(W.spawns),
        "§e/function rpg/hunt/<사냥터>§f : 예시 몬스터 소환",
        "§e/function rpg/arena/<사냥터>_off | _on§f : 사냥터 조명 끄기/켜기",
        "§e/function rpg/boss/<hq|deepsea|dungeon>§f : 예시 보스 소환",
        "§e뽑기 함수§f : rpg/gacha/common | rare | epic | legend",
    ]]
    return fn


def script(W):
    g = ",\n  ".join('{x: %d, y: %d, z: %d, fn: "%s"}' % (b["button"][0], b["button"][1], b["button"][2],
                                                           b["function"]) for b in W.gacha)
    return '''import { world, system } from "@minecraft/server";

// gacha machine buttons -> function rpg/gacha/<tier> (run as the player who pressed it)
const GACHA = [
  %s
];

world.afterEvents.buttonPush.subscribe((ev) => {
  const b = ev.block;
  const g = GACHA.find((q) => q.x === b.x && q.y === b.y && q.z === b.z);
  if (!g) return;
  const p = ev.source;
  if (p && p.typeId === "minecraft:player") p.runCommandAsync("function " + g.fn);
});

// /scriptevent rpg:diag   (checks that the script is running)
system.afterEvents.scriptEventReceive.subscribe(
  (ev) => {
    if (ev.id === "rpg:diag") {
      console.warn("[rpg] ok gacha=" + GACHA.length + " buttonPush=" + typeof world.afterEvents.buttonPush);
    }
  },
  { namespaces: ["rpg"] }
);
''' % g


def level_overrides(time_of_day=1000):
    I, By = an.IntTag, an.ByteTag
    return {
        "GameType": I(2), "Difficulty": I(2), "Time": an.LongTag(time_of_day),
        "dodaylightcycle": By(1), "doweathercycle": By(1), "domobspawning": By(0), "spawnMobs": By(0),
        "falldamage": By(1), "firedamage": By(1), "drowningdamage": By(1), "freezedamage": By(1),
        "keepinventory": By(0), "doimmediaterespawn": By(0), "randomtickspeed": I(1),
        "doentitydrops": By(1), "naturalregeneration": By(1), "mobgriefing": By(0), "dofiretick": By(0),
        "respawnblocksexplode": By(0), "tntexplodes": By(0), "projectilescanbreakblocks": By(0),
        "rainTime": I(24000), "lightningTime": I(36000),
    }


def font(size):
    for f in ("/usr/share/fonts/opentype/unifont/unifont.otf", "/usr/share/fonts/truetype/unifont/unifont.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return None


LABELS = [("spawn", 0, -2), ("farm", -132, -8), ("cave", 4, 92), ("village", 0, 222), ("hq", -146, 226),
          ("beach", 40, 326), ("deepsea", -122, 404), ("nether", 196, 356), ("castle", 194, 516),
          ("dungeon", 194, 540), ("deepdark", 46, 522)]


def overview(W, path, scale=2):
    im = render.topdown(W.a, path, scale=1)
    im = im.resize((SX * scale, SZ * scale), Image.NEAREST)
    d = ImageDraw.Draw(im)
    f = font(28)
    # route between regions
    route = [(0, -2), (-60, -9), (-132, -8), None, (0, -2), (0, 50), (4, 92), (20, 160), (0, 222), (-78, 229),
             (-146, 226), None, (0, 222), (22, 289), (22, 316), (-30, 354), (-62, 380), (-122, 404), None,
             (22, 316), (126, 325), (196, 356), (196, 444), (194, 516), (210, 540), None, (194, 516), (130, 526),
             (113, 500), (46, 522)]
    seg = []
    for p in route + [None]:
        if p is None:
            if len(seg) > 1:
                d.line([((x - X0) * scale, (z - Z0) * scale) for x, z in seg], fill=(255, 240, 120), width=4)
            seg = []
        else:
            seg.append(p)
    for key, x, z in LABELS:
        t = REGION_KO[key]
        px, py = (x - X0) * scale, (z - Z0) * scale
        if f:
            bb = d.textbbox((0, 0), t, font=f)
            w, h = bb[2] - bb[0], bb[3] - bb[1]
            d.rectangle((px - w // 2 - 6, py - h // 2 - 6, px + w // 2 + 6, py + h // 2 + 8), fill=(20, 16, 30))
            d.text((px - w // 2, py - h // 2), t, font=f, fill=(255, 225, 140))
    im.save(path)
    return im


ICONS = {"spawn": (-58, 55, -56, 58, 100, 50), "village": (-64, 55, 160, 64, 100, 290),
         "hq": (-200, 58, 168, -94, 100, 286), "beach": (-70, 40, 290, 132, 95, 372),
         "nether": (118, 50, 280, 262, 110, 460), "castle": (126, 60, 444, 260, 130, 586)}


def icon(W, path):
    tiles = []
    for k, box in ICONS.items():
        tiles.append(render.iso(W.a, os.path.join(tempfile.gettempdir(), "rpg_icon_%s.png" % k), box=box, s=1))
    Wd, Ht = 960, 540
    out = Image.new("RGB", (Wd, Ht), (16, 14, 26))
    tw, th = Wd // 3, Ht // 2
    for i, im in enumerate(tiles):
        im = im.copy()
        im.thumbnail((tw, th))
        out.paste(im, ((i % 3) * tw + (tw - im.width) // 2, (i // 3) * th + (th - im.height) // 2))
    d = ImageDraw.Draw(out)
    f = font(64)
    if f:
        t = "RPG 모험의 길"
        bb = d.textbbox((0, 0), t, font=f)
        tx, ty = (Wd - (bb[2] - bb[0])) // 2, (Ht - (bb[3] - bb[1])) // 2 - 10
        d.rectangle((tx - 24, ty - 8, tx + bb[2] - bb[0] + 24, ty + bb[3] - bb[1] + 24), fill=(22, 14, 34))
        d.text((tx + 4, ty + 4), t, font=f, fill=(90, 40, 150))
        d.text((tx, ty), t, font=f, fill=(255, 214, 120))
    out.save(path, quality=92)
    return out.crop(((Wd - Ht) // 2, 0, (Wd + Ht) // 2, Ht)).resize((256, 256))


def world_info(W, rep, stats):
    def ints(o):
        if isinstance(o, dict):
            return {k: ints(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [ints(v) for v in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        return o
    hunts = []
    for h in W.hunts:
        key = HUNT_KEY[h["name"]]
        hunts.append(dict(region=h["region"], name=h["name"], key=key, box=h["box"], entrances=h["entrances"],
                          spawn_points=h["spawn_points"], roofed=h["roofed"],
                          functions=["rpg/hunt/" + key, "rpg/arena/%s_off" % key, "rpg/arena/%s_on" % key]))
    info = dict(world_spawn=W.spawns["spawn"],
                regions={k: dict(name=REGION_KO.get(k, k), arrival=v, tp="rpg/tp/" + k) for k, v in W.spawns.items()},
                shops=[dict(region=s["region"], name=s["name"], npc_spot=s["npc"], counter=s["counter"],
                            customers_face=s["facing"], ender_chests=s["ender_chests"]) for s in W.shops],
                hunting_grounds=hunts,
                bosses=[dict(region=b["region"], name=b["name"], boss_spawn=b["boss_spawn"], box=b["box"],
                             entrance=b["entrance"], function="rpg/boss/" + b["region"]) for b in W.bosses],
                gacha=[dict(tier=g["tier"], button=g["button"], function=g["function"]) for g in W.gacha],
                gates=W.gates,
                verification=dict(reachable=rep["reachable"], trapped=len(rep["trapped"]),
                                  escaped=len(rep["escaped"]), fall_edges=len(rep["falls"]), light=stats))
    return ints(info)


def make_previews(W, out):
    os.makedirs(out, exist_ok=True)
    a = W.a
    shots = []
    overview(W, os.path.join(out, "00_overview.png"))
    isos = [("01_spawn", (-58, 55, -56, 58, 100, 50), 2), ("02_farm", (-182, 55, -56, -40, 95, 40), 2),
            ("03_cave", (-60, 48, 44, 50, 56, 170), 3), ("04_village", (-66, 55, 160, 66, 100, 292), 2),
            ("05_hq", (-200, 58, 168, -94, 100, 286), 2), ("05b_hq_inside", (-188, 60, 200, -98, 70, 254), 3),
            ("06_beach", (-70, 40, 290, 132, 95, 372), 2), ("08_nether", (120, 50, 286, 256, 72, 426), 2),
            ("09_castle", (126, 60, 444, 260, 130, 586), 2), ("10_dungeon", (136, 20, 494, 232, 34, 548), 3),
            ("11_deepdark", (-16, 28, 454, 136, 44, 592), 2)]
    for name, box, s in isos:
        render.iso(a, os.path.join(out, name + ".png"), box=box, s=s)
    # deep sea temple with the water hidden
    from mcw import Area, B
    x1, y1, z1, x2, y2, z2 = (-150, 20, 340, -30, 45, 430)
    T = Area("tmp", (x1 // 16) * 16, (z1 // 16) * 16, ((x2 - (x1 // 16) * 16) // 16 + 1) * 16,
             ((z2 - (z1 // 16) * 16) // 16 + 1) * 16, 0, a.sy)
    T.blk[:] = a.blk[T.x0 - a.x0:T.x0 - a.x0 + T.sx, :, T.z0 - a.z0:T.z0 - a.z0 + T.sz]
    T.blk[T.blk == B("water")] = 0
    render.iso(T, os.path.join(out, "07_deepsea.png"), box=(x1, y1, z1, x2, y2, z2), s=3)
    persp = [("p01_gacha_hall", (0, 67.6, -12), 180, 6), ("p02_farm_gate", (-66, 71.6, -9), 90, 4),
             ("p03_cave_window", (10, 66.6, 63), 0, 12), ("p04_village", (24, 68.6, 172), 0, 6),
             ("p05_hq_gate", (-70, 71.6, 229), 90, 4), ("p06_beach_gate", (22, 72.6, 283), 0, 6),
             ("p07_glass_tunnel", (-62, 44, 380), 0, 3), ("p08_nether_window", (142, 67.6, 334), 270, 4),
             ("p09_nether_bridge", (200, 65.6, 385), 180, 4), ("p10_castle", (196, 68.6, 456), 0, -4),
             ("p11_deepdark_window", (112.5, 50.8, 500), 90, 10)]
    for name, cam, yaw, pitch in persp:
        cx, cy, cz = cam
        bx1, by1, bz1 = int(cx) - 80, max(1, int(cy) - 30), int(cz) - 80
        sl = (slice(bx1 - a.x0, bx1 - a.x0 + 160), slice(by1 - a.y0, by1 - a.y0 + 70), slice(bz1 - a.z0, bz1 - a.z0 + 160))
        L = np.zeros(a.blk.shape, np.int8)
        L[sl] = lighting.block_light(a.blk[sl])
        dark = cy < 60
        render.persp(a, os.path.join(out, name + ".png"), cam, yaw, pitch, block_light=L,
                     fog_col=(40, 36, 50) if dark else (150, 160, 190), fog_dist=200 if not dark else 120)


def package(W, out_dir, world_name, file_name, rep, stats, previews=True):
    work = tempfile.mkdtemp(prefix="rpgworld_")
    pack = write_behavior_pack(os.path.join(work, "bp_" + "rpg"), PACK_NAME,
                               description="RPG 모험의 길: 관리자 함수, 뽑기 버튼, 사냥터 조명 스위치",
                               functions=functions(W), tick=["rpg/tick"], scripts={"main.js": script(W)})
    W.a.prune_be()
    ic = icon(W, os.path.join(work, "icon.jpg"))
    wdir = wk_package([W.a], os.path.join(out_dir, file_name), world_name, W.spawns["spawn"], pack=pack, icon=ic,
                      level_overrides=level_overrides(), keep_dir=os.path.join(work, "keep"))
    info = world_info(W, rep, stats)
    json.dump(info, open(os.path.join(out_dir, "world_info.json"), "w", encoding="utf8"), ensure_ascii=False,
              indent=1)
    if previews:
        make_previews(W, os.path.join(out_dir, "previews"))
    print("world folder:", wdir)
    return wdir
