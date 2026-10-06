"""Behaviour pack + world packaging for the skygen world."""
import json
import os
import shutil
import tempfile
import time
import uuid

import amulet_nbt as an

from mcw import write_db, write_level_dat, zip_dir
from worldkit import level_changes, TEMPLATE

HERE = os.path.dirname(os.path.abspath(__file__))
PACK_NAME = "skygen_bp"
NS = uuid.uuid5(uuid.NAMESPACE_URL, "bearweb/skygen-sky-archipelago")
PACK_UUID = str(uuid.uuid5(NS, "pack"))
VERSION = [1, 0, 0]
SERVER_API = "2.0.0"
UI_API = "2.0.0"

# sell prices (원): smelting raises the value, nothing the shop sells can be sold back
SELL = {
    "minecraft:oak_log": [2, "참나무 원목"], "minecraft:birch_log": [2, "자작나무 원목"],
    "minecraft:spruce_log": [2, "가문비나무 원목"], "minecraft:dark_oak_log": [2, "짙은 참나무 원목"],
    "minecraft:cobblestone": [1, "조약돌"], "minecraft:stone": [2, "돌 (구운 것)"],
    "minecraft:charcoal": [3, "숯"], "minecraft:coal": [4, "석탄"],
    "minecraft:raw_iron": [6, "철 원석"], "minecraft:iron_ingot": [10, "철 주괴"],
    "minecraft:raw_gold": [12, "금 원석"], "minecraft:gold_ingot": [20, "금 주괴"],
    "minecraft:diamond": [50, "다이아몬드"],
}


def item(id_, name, n, price):
    return dict(id="minecraft:" + id_, name=name, n=n, price=price)


SHOPS = {
    "tools": dict(title="§l도구 상점", items=[
        item("wooden_pickaxe", "나무 곡괭이", 1, 15), item("stone_pickaxe", "돌 곡괭이", 1, 60),
        item("iron_pickaxe", "철 곡괭이", 1, 400), item("diamond_pickaxe", "다이아몬드 곡괭이", 1, 2500),
        item("stone_axe", "돌 도끼", 1, 50), item("iron_axe", "철 도끼", 1, 350), item("diamond_axe", "다이아몬드 도끼", 1, 2200),
        item("stone_shovel", "돌 삽", 1, 30), item("iron_shovel", "철 삽", 1, 250), item("wooden_hoe", "나무 괭이", 1, 10)]),
    "combat": dict(title="§l무기 · 갑옷", items=[
        item("stone_sword", "돌 검", 1, 60), item("iron_sword", "철 검", 1, 450), item("diamond_sword", "다이아몬드 검", 1, 3000),
        item("bow", "활", 1, 300), item("arrow", "화살", 16, 80), item("shield", "방패", 1, 250),
        item("leather_helmet", "가죽 모자", 1, 40), item("leather_chestplate", "가죽 튜닉", 1, 60),
        item("leather_leggings", "가죽 바지", 1, 50), item("leather_boots", "가죽 장화", 1, 30),
        item("iron_helmet", "철 투구", 1, 300), item("iron_chestplate", "철 흉갑", 1, 500),
        item("iron_leggings", "철 각반", 1, 450), item("iron_boots", "철 부츠", 1, 250),
        item("diamond_helmet", "다이아몬드 투구", 1, 2500), item("diamond_chestplate", "다이아몬드 흉갑", 1, 4000),
        item("diamond_leggings", "다이아몬드 각반", 1, 3500), item("diamond_boots", "다이아몬드 부츠", 1, 2000)]),
    "food": dict(title="§l음식 상점", items=[
        item("bread", "빵", 8, 30), item("baked_potato", "구운 감자", 8, 40), item("cooked_beef", "스테이크", 8, 60),
        item("cooked_chicken", "구운 닭고기", 8, 50), item("pumpkin_pie", "호박 파이", 4, 40),
        item("golden_carrot", "황금 당근", 4, 120), item("golden_apple", "황금 사과", 1, 400)]),
    "build": dict(title="§l건축 블록", items=[
        item("oak_planks", "참나무 판자", 32, 30), item("spruce_planks", "가문비나무 판자", 32, 30),
        item("birch_planks", "자작나무 판자", 32, 30), item("stone_bricks", "석재 벽돌", 32, 60),
        item("smooth_stone", "매끄러운 돌", 32, 60), item("bricks", "벽돌", 32, 80), item("sandstone", "사암", 32, 50),
        item("polished_andesite", "윤나는 안산암", 32, 50), item("deepslate_tiles", "심층암 타일", 32, 80),
        item("quartz_block", "석영 블록", 16, 120), item("glass", "유리", 16, 40), item("glass_pane", "유리판", 16, 30),
        item("oak_stairs", "참나무 계단", 16, 30), item("oak_slab", "참나무 반 블록", 16, 20),
        item("oak_fence", "참나무 울타리", 16, 25), item("oak_door", "참나무 문", 2, 20), item("ladder", "사다리", 16, 20)]),
    "deco": dict(title="§l장식 블록", items=[
        item("white_wool", "흰색 양털", 16, 30), item("red_wool", "빨간색 양털", 16, 30), item("blue_wool", "파란색 양털", 16, 30),
        item("yellow_wool", "노란색 양털", 16, 30), item("lime_wool", "연두색 양털", 16, 30), item("black_wool", "검은색 양털", 16, 30),
        item("white_carpet", "흰색 카펫", 16, 20), item("red_carpet", "빨간색 카펫", 16, 20),
        item("terracotta", "테라코타", 16, 40), item("white_concrete", "흰색 콘크리트", 16, 40),
        item("flower_pot", "화분", 4, 20), item("poppy", "양귀비", 8, 10), item("dandelion", "민들레", 8, 10),
        item("lantern", "랜턴", 4, 40), item("painting", "그림", 2, 30), item("bookshelf", "책장", 4, 80)]),
    "living": dict(title="§l생활 용품", items=[
        item("crafting_table", "제작대", 1, 15), item("furnace", "화로", 1, 30), item("chest", "상자", 2, 30),
        item("barrel", "통", 1, 25), item("white_bed", "흰색 침대", 1, 60), item("torch", "횃불", 16, 15),
        item("smoker", "훈연기", 1, 40), item("blast_furnace", "용광로", 1, 120), item("campfire", "모닥불", 1, 40),
        item("ender_chest", "엔더 상자", 1, 800), item("wheat_seeds", "밀 씨앗", 8, 10), item("oak_sapling", "참나무 묘목", 2, 20),
        item("bone_meal", "뼛가루", 8, 20)]),
    "magic": dict(title="§l인첸트 재료", items=[
        item("lapis_lazuli", "청금석", 8, 60), item("experience_bottle", "경험치 병", 8, 120), item("book", "책", 4, 30),
        item("bookshelf", "책장", 4, 80), item("enchanting_table", "마법 부여대", 1, 600), item("anvil", "모루", 1, 500),
        item("grindstone", "숫돌", 1, 100)]),
}


def _num(o):
    if hasattr(o, "tolist"):
        return o.tolist()
    return int(o) if float(o) == int(o) else float(o)


def data_of(W):
    gens = [[g["x"], g["y"], g["z"], "minecraft:" + g["block"], g["kind"], g["regen"]] for g in W.generators]
    safe = [list(b[1:]) + [b[0]] for b in W.safe_zones]
    plots = []
    for p in W.plots:
        x1, z1, x2, z2 = p["ring"]
        plots.append(dict(id=p["id"], interior=list(p["interior"]), zone=[x1 + 1, p["floor"] - 6, z1 + 1, x2 - 1, 320, z2 - 1],
                          floor=p["floor"], btnOut=list(p["btn_out"]), btnIn=list(p["btn_in"]),
                          btnFace=[p["btn_out_face"], p["btn_in_face"]], sign=list(p["sign"]),
                          inside=list(p["inside"]), outside=list(p["outside"]), price=p["price"],
                          map=list(W.plot_board.get(p["id"], ())) or None))
    furnace = [dict(id=r["id"], box=list(r["box"]), lamp=list(r["lamp"]), out=list(r["out"]),
                    furnaces=[list(f) for f in r["furnaces"]]) for r in W.furnace_rooms]
    portals = [dict(kind=p["kind"], dest=p["dest"], box=list(p["box"]), label=p.get("label", "")) for p in W.portals]
    npcs = [dict(name=n["name"], x=n["x"], y=n["y"], z=n["z"], face=list(n["face"]), tag=n["tag"])
            for n in W.npcs if n.get("kind") in ("shop", "guide", "plots")]
    arrivals = {k: list(v) for k, v in W.arrivals.items()}
    return dict(gens=gens, safe=safe, plots=plots, furnace=furnace, portals=portals, npcs=npcs, arrivals=arrivals)


def write_pack(root, W):
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    manifest = {
        "format_version": 2,
        "header": {"name": "스카이젠 시스템", "description": "낮/밤 PvP · 안전구역 · 생성기 · 상점 · 집터 · 화로방",
                   "uuid": PACK_UUID, "version": VERSION, "min_engine_version": [1, 21, 90]},
        "modules": [
            {"type": "data", "uuid": str(uuid.uuid5(NS, "data")), "version": VERSION},
            {"type": "script", "language": "javascript", "uuid": str(uuid.uuid5(NS, "script")), "version": VERSION,
             "entry": "scripts/main.js"},
        ],
        "dependencies": [{"module_name": "@minecraft/server", "version": SERVER_API},
                         {"module_name": "@minecraft/server-ui", "version": UI_API}],
    }
    json.dump(manifest, open(os.path.join(root, "manifest.json"), "w", encoding="utf8"), ensure_ascii=False, indent=2)
    src = open(os.path.join(HERE, "sky_main.js"), encoding="utf8").read()
    src = src.replace("__DATA__", json.dumps(data_of(W), ensure_ascii=False, separators=(",", ":"), default=_num))
    src = src.replace("__SHOPS__", json.dumps(SHOPS, ensure_ascii=False))
    src = src.replace("__SELL__", json.dumps(SELL, ensure_ascii=False))
    open(os.path.join(root, "scripts", "main.js"), "w", encoding="utf8").write(src)
    fns = {
        "sky/help": ["tellraw @s {\"rawtext\":[{\"text\":\"§b[스카이젠 관리자 함수]\\n"
                     "§f/function sky/admin_on §7- 나를 관리자로 (보호·밴 예외)\\n"
                     "§f/function sky/admin_off §7- 관리자 해제\\n"
                     "§f/function sky/day · sky/night §7- 시간 바꾸기\\n"
                     "§f/function sky/tp/hub · forest · skeld · volcano · paradise · library\\n"
                     "§f/scriptevent sky:unban 이름 §7- 밴 해제\\n"
                     "§f/scriptevent sky:money 이름 금액 §7- 돈 지급\\n"
                     "§f/scriptevent sky:plotfree 번호 §7- 집터 회수\"}]}"],
        "sky/admin_on": ["tag @s add sky_admin", "gamemode creative @s"],
        "sky/admin_off": ["tag @s remove sky_admin", "gamemode adventure @s"],
        "sky/day": ["time set 1000"],
        "sky/night": ["time set 14000"],
    }
    for k, v in W.arrivals.items():
        x, y, z, yaw = v
        fns["sky/tp/" + k] = ["tp @s %.1f %.1f %.1f %d 0" % (x, y, z, yaw)]
    for name, lines in fns.items():
        path = os.path.join(root, "functions", name + ".mcfunction")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf8").write("\n".join(lines) + "\n")
    return {"root": root, "uuid": PACK_UUID, "version": VERSION}


def level_overrides():
    By, I = an.ByteTag, an.IntTag
    return {
        "GameType": I(2), "Difficulty": I(2),
        "Time": an.LongTag(1000),
        "dodaylightcycle": By(1), "doweathercycle": By(0), "domobspawning": By(0), "spawnMobs": By(0),
        "keepinventory": By(1), "pvp": By(0),
        "falldamage": By(1), "firedamage": By(1), "drowningdamage": By(1), "freezedamage": By(1),
        "dotiledrops": By(1), "doentitydrops": By(1), "domobloot": By(1),
        "mobgriefing": By(0), "tntexplodes": By(0), "dofiretick": By(0), "respawnblocksexplode": By(0),
        "randomtickspeed": I(1), "naturalregeneration": By(1), "doimmediaterespawn": By(1),
        "showcoordinates": By(0), "showdeathmessages": By(1), "sendcommandfeedback": By(0),
        "commandblockoutput": By(0), "showtags": By(0), "spawnradius": I(0),
        "lastOpenedWithVersion": an.ListTag([I(v) for v in (1, 21, 90, 0, 0)]),
        "MinimumCompatibleClientVersion": an.ListTag([I(v) for v in (1, 21, 90, 0, 0)]),
    }


def package(W, out_dir, name, file_name, previews=True, keep_dir=None):
    work = keep_dir or tempfile.mkdtemp(prefix="skygen_")
    wdir = os.path.join(work, "world")
    shutil.rmtree(wdir, ignore_errors=True)
    os.makedirs(wdir)
    nkeys = write_db([W.a], os.path.join(wdir, "db"))
    spawn = (0, 64, 41)
    changes = level_changes(name, spawn)
    changes.update(level_overrides())
    write_level_dat(os.path.join(wdir, "level.dat"), TEMPLATE, changes)
    open(os.path.join(wdir, "levelname.txt"), "w", encoding="utf8").write(name)
    pack = write_pack(os.path.join(wdir, "behavior_packs", PACK_NAME), W)
    json.dump([{"pack_id": pack["uuid"], "version": pack["version"]}],
              open(os.path.join(wdir, "world_behavior_packs.json"), "w"), indent=2)
    import sky_preview
    icon = sky_preview.icon(W)
    icon.resize((256, 256)).save(os.path.join(pack["root"], "pack_icon.png"))
    icon.convert("RGB").save(os.path.join(wdir, "world_icon.jpeg"), quality=92)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, file_name)
    if os.path.exists(dst):
        os.remove(dst)
    zip_dir(wdir, dst)
    print("wrote %s (%.2f MB, %d leveldb keys)" % (dst, os.path.getsize(dst) / 1e6, nkeys))
    sky_preview.world_info(W, os.path.join(out_dir, "world_info.json"))
    if previews:
        sky_preview.previews(W, os.path.join(out_dir, "previews"))
    return wdir
