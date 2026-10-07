"""Behaviour pack + resource pack for 'Norse RPG' (bosses, telegraphs, items, RPG systems).

Both packs are written as folders (copied into the world) and as stand-alone .mcpack files.
The behaviour pack depends on the resource pack, so adding the BP to a world pulls the RP in.
"""
import json
import os
import shutil
import uuid

from PIL import Image, ImageDraw

import nr_design as D
import nr_telegraph as TG

HERE = os.path.dirname(os.path.abspath(__file__))
NS = uuid.uuid5(uuid.NAMESPACE_URL, "bearweb/norse-rpg-nine-worlds")
BP_UUID = str(uuid.uuid5(NS, "bp"))
RP_UUID = str(uuid.uuid5(NS, "rp"))
VERSION = [1, 0, 0]
MIN_ENGINE = [1, 21, 90]
SERVER_API = "2.0.0"
UI_API = "2.0.0"
BP_NAME = "아홉 세계 보스 행동팩"
RP_NAME = "아홉 세계 보스 리소스팩"


def dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(data, (dict, list)):
        json.dump(data, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    else:
        open(path, "w", encoding="utf8").write(data)


# ---------------------------------------------------------------- boss entities
def boss_bp(bid, b):
    w, h = b["size"]
    fire = True
    comps = {
        "minecraft:type_family": {"family": ["nrpg_boss", "monster", "mob"]},
        "minecraft:health": {"value": b["hp"], "max": b["hp"]},
        "minecraft:boss": {"hud_range": 48, "name": b["ko"], "should_darken_sky": False},
        "minecraft:collision_box": {"width": w, "height": h},
        "minecraft:movement.basic": {},
        "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_water": True, "avoid_damage_blocks": True},
        "minecraft:jump.static": {},
        "minecraft:physics": {},
        "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
        "minecraft:knockback_resistance": {"value": 1.0},
        "minecraft:attack": {"damage": b["melee"]},
        "minecraft:behavior.float": {"priority": 0},
        "minecraft:behavior.hurt_by_target": {"priority": 1},
        "minecraft:behavior.nearest_attackable_target": {
            "priority": 2, "must_see": False, "reselect_targets": True, "within_radius": 36.0,
            "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 36}]},
        "minecraft:behavior.look_at_player": {"priority": 8, "look_distance": 16},
        "minecraft:behavior.random_look_around": {"priority": 9},
        "minecraft:follow_range": {"value": 40, "max": 40},
        "minecraft:persistent": {},
        "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0, "breathes_water": True, "breathes_air": True},
        "minecraft:damage_sensor": {"triggers": [
            {"cause": c, "deals_damage": "no"} for c in ("fall", "suffocation", "drowning", "lava", "fire", "fire_tick",
                                                         "magma", "block_explosion", "entity_explosion", "fly_into_wall")]},
        "minecraft:loot": {"table": "loot_tables/nrpg/bosses/%s.json" % bid},
        "minecraft:experience_reward": {"on_death": "query.last_hit_by_player ? %d : 0" % (50 if b["role"] != "final" else 120)},
        "minecraft:nameable": {},
        "minecraft:is_hidden_when_invisible": {},
        "minecraft:conditional_bandwidth_optimization": {},
    }
    if fire:
        comps["minecraft:fire_immune"] = {}
    groups = {
        "nrpg:mobile": {
            "minecraft:movement": {"value": b["speed"]},
            "minecraft:behavior.melee_box_attack": {"priority": 3, "speed_multiplier": 1.15, "track_target": True,
                                                    "melee_fov": 120, "horizontal_reach": max(0.8, w * 0.6)},
        },
        "nrpg:casting": {"minecraft:movement": {"value": 0.0}},
    }
    return {"format_version": "1.21.50", "minecraft:entity": {
        "description": {
            "identifier": "nrpg:" + bid, "is_spawnable": True, "is_summonable": True,
            "properties": {
                "nrpg:anim": {"type": "int", "range": [0, 9], "default": 0, "client_sync": True},
                "nrpg:phase": {"type": "int", "range": [0, 3], "default": 0, "client_sync": True},
            },
        },
        "component_groups": groups,
        "components": comps,
        "events": {
            "minecraft:entity_spawned": {"add": {"component_groups": ["nrpg:mobile"]}},
            "nrpg:cast_start": {"remove": {"component_groups": ["nrpg:mobile"]}, "add": {"component_groups": ["nrpg:casting"]}},
            "nrpg:cast_end": {"remove": {"component_groups": ["nrpg:casting"]}, "add": {"component_groups": ["nrpg:mobile"]}},
        },
    }}


def illusion_bp():
    return {"format_version": "1.21.50", "minecraft:entity": {
        "description": {"identifier": "nrpg:illusion", "is_spawnable": False, "is_summonable": True,
                        "properties": {"nrpg:skin": {"type": "int", "range": [0, 31], "default": 0, "client_sync": True}}},
        "component_groups": {"nrpg:despawn": {"minecraft:instant_despawn": {}}},
        "components": {
            "minecraft:type_family": {"family": ["nrpg_illusion", "monster", "mob"]},
            "minecraft:health": {"value": 1, "max": 1},
            "minecraft:collision_box": {"width": 1.0, "height": 2.6},
            "minecraft:physics": {},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:knockback_resistance": {"value": 1.0},
            "minecraft:movement": {"value": 0.0},
            "minecraft:behavior.look_at_player": {"priority": 1, "look_distance": 32},
            "minecraft:damage_sensor": {"triggers": [{"cause": "fall", "deals_damage": "no"}]},
            "minecraft:breathable": {"suffocate_time": 0, "breathes_water": True},
            "minecraft:loot": {"table": "loot_tables/empty.json"},
            "minecraft:timer": {"looping": False, "time": 15, "time_down_event": {"event": "nrpg:despawn"}},
        },
        "events": {"nrpg:despawn": {"add": {"component_groups": ["nrpg:despawn"]}}},
    }}


def dummy_bp():
    return {"format_version": "1.21.50", "minecraft:entity": {
        "description": {"identifier": "nrpg:dummy", "is_spawnable": True, "is_summonable": True},
        "components": {
            "minecraft:type_family": {"family": ["nrpg_dummy", "inanimate"]},
            "minecraft:health": {"value": 1000, "max": 1000},
            "minecraft:collision_box": {"width": 0.6, "height": 1.8},
            "minecraft:physics": {},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:knockback_resistance": {"value": 1.0},
            "minecraft:persistent": {},
            "minecraft:breathable": {"suffocate_time": 0, "breathes_water": True},
            "minecraft:nameable": {"always_show": True},
            "minecraft:loot": {"table": "loot_tables/empty.json"},
        },
    }}


def wolf_bp(ident, name, hp, dmg, speed, size=(0.9, 1.0)):
    return {"format_version": "1.21.50", "minecraft:entity": {
        "description": {"identifier": ident, "is_spawnable": True, "is_summonable": True},
        "components": {
            "minecraft:type_family": {"family": ["nrpg_wolf", "monster", "mob"]},
            "minecraft:health": {"value": hp, "max": hp},
            "minecraft:collision_box": {"width": size[0], "height": size[1]},
            "minecraft:movement": {"value": speed},
            "minecraft:movement.basic": {},
            "minecraft:navigation.walk": {"avoid_water": True, "avoid_damage_blocks": True},
            "minecraft:jump.static": {},
            "minecraft:physics": {},
            "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
            "minecraft:attack": {"damage": dmg},
            "minecraft:behavior.float": {"priority": 0},
            "minecraft:behavior.leap_at_target": {"priority": 3, "yd": 0.4, "must_be_on_ground": True},
            "minecraft:behavior.melee_box_attack": {"priority": 4, "speed_multiplier": 1.25, "track_target": True},
            "minecraft:behavior.hurt_by_target": {"priority": 1},
            "minecraft:behavior.nearest_attackable_target": {
                "priority": 2, "must_see": True, "reselect_targets": True, "within_radius": 20.0,
                "entity_types": [{"filters": {"test": "is_family", "subject": "other", "value": "player"}, "max_dist": 20}]},
            "minecraft:behavior.random_stroll": {"priority": 7, "speed_multiplier": 0.8},
            "minecraft:behavior.look_at_player": {"priority": 8, "look_distance": 8},
            "minecraft:behavior.random_look_around": {"priority": 9},
            "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
            "minecraft:nameable": {},
            "minecraft:loot": {"table": "loot_tables/nrpg/wolf.json"},
            "minecraft:experience_reward": {"on_death": "query.last_hit_by_player ? 5 : 0"},
        },
    }}


# ---------------------------------------------------------------- items
ITEMS = {
    "rune_shard": dict(ko="§b룬 조각", stack=64, lore="강화에 쓰는 룬 조각"),
    "rune_core": dict(ko="§d룬 정수", stack=64, lore="+6 이상 강화에 필요한 정수"),
    "ward_scroll": dict(ko="§e보호 주문서", stack=16, lore="강화 실패 시 장비 파괴를 막습니다"),
    "return_scroll": dict(ko="§a귀환 주문서", stack=16, lore="5초 뒤 항구로 돌아갑니다"),
    "journal": dict(ko="§6모험가의 수첩", stack=1, lore="메뉴: 진행도, 귀환, 안내"),
}


def item_bp(key, it):
    comps = {
        "minecraft:icon": "nrpg_" + key,
        "minecraft:display_name": {"value": it["ko"]},
        "minecraft:max_stack_size": it["stack"],
    }
    if key in ("return_scroll", "journal"):
        comps["minecraft:cooldown"] = {"category": "nrpg_" + key, "duration": 1.0}
        comps["minecraft:use_modifiers"] = {"use_duration": 0.05, "movement_modifier": 1.0}
    if key in ("rune_core", "ward_scroll"):
        comps["minecraft:glint"] = True
    return {"format_version": "1.21.40", "minecraft:item": {
        "description": {"identifier": "nrpg:" + key, "menu_category": {"category": "items"}},
        "components": comps}}


def item_icon(key):
    """16x16 pixel-art icons drawn in code."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if key == "rune_shard":
        pts = [(8, 1), (13, 6), (10, 15), (5, 14), (3, 6)]
        d.polygon(pts, fill=(70, 150, 200, 255), outline=(20, 50, 80, 255))
        d.polygon([(8, 2), (11, 6), (8, 8), (5, 6)], fill=(150, 220, 250, 255))
        d.line([(7, 9), (7, 13)], fill=(220, 250, 255, 255))
        d.line([(7, 10), (9, 9)], fill=(220, 250, 255, 255))
    elif key == "rune_core":
        d.ellipse((2, 2, 13, 13), fill=(110, 50, 160, 255), outline=(40, 10, 70, 255))
        d.ellipse((4, 4, 11, 11), fill=(190, 110, 255, 255))
        d.ellipse((6, 6, 9, 9), fill=(250, 220, 255, 255))
        d.line([(7, 1), (7, 3)], fill=(240, 200, 255, 255))
    elif key == "ward_scroll":
        d.rectangle((3, 2, 12, 13), fill=(232, 214, 160, 255), outline=(120, 90, 40, 255))
        d.rectangle((2, 1, 13, 3), fill=(160, 110, 50, 255))
        d.rectangle((2, 12, 13, 14), fill=(160, 110, 50, 255))
        d.polygon([(7, 5), (10, 6), (9, 10), (7, 11), (5, 10), (5, 6)], fill=(230, 180, 40, 255), outline=(120, 80, 10, 255))
    elif key == "return_scroll":
        d.rectangle((3, 2, 12, 13), fill=(220, 236, 200, 255), outline=(60, 110, 50, 255))
        d.rectangle((2, 1, 13, 3), fill=(80, 130, 60, 255))
        d.rectangle((2, 12, 13, 14), fill=(80, 130, 60, 255))
        d.polygon([(5, 9), (8, 5), (11, 9)], fill=(40, 120, 200, 255))
        d.rectangle((7, 8, 8, 11), fill=(40, 120, 200, 255))
    elif key == "journal":
        d.rectangle((3, 1, 13, 14), fill=(120, 70, 35, 255), outline=(50, 25, 10, 255))
        d.rectangle((4, 2, 12, 13), fill=(150, 90, 45, 255))
        d.rectangle((3, 1, 4, 14), fill=(80, 45, 20, 255))
        d.polygon([(8, 4), (11, 7), (8, 11), (5, 7)], outline=(240, 200, 80, 255))
        d.point((8, 7), fill=(240, 200, 80, 255))
    return im


# ---------------------------------------------------------------- particles
def particles(rp):
    tex = os.path.join(rp, "textures", "nrpg", "particle")
    os.makedirs(tex, exist_ok=True)
    glow = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            r = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5 / 7.5
            a = max(0.0, 1 - r) ** 1.6
            glow.putpixel((x, y), (255, 255, 255, int(a * 255)))
    glow.save(os.path.join(tex, "glow.png"))
    color = ["variable.color.r", "variable.color.g", "variable.color.b", 1.0]

    def eff(ident, comps):
        return {"format_version": "1.10.0", "particle_effect": {
            "description": {"identifier": ident, "basic_render_parameters": {"material": "particles_add", "texture": "textures/nrpg/particle/glow"}},
            "components": comps}}
    beam = eff("nrpg:beam", {
        "minecraft:emitter_rate_instant": {"num_particles": 2},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_sphere": {"radius": 0.25, "direction": "outwards"},
        "minecraft:particle_lifetime_expression": {"max_lifetime": "math.random(0.35, 0.6)"},
        "minecraft:particle_initial_speed": 0.4,
        "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.6, 0], "linear_drag_coefficient": 2},
        "minecraft:particle_appearance_billboard": {
            "size": ["0.45 * (1 - variable.particle_age / variable.particle_lifetime)", "0.45 * (1 - variable.particle_age / variable.particle_lifetime)"],
            "facing_camera_mode": "lookat_xyz", "uv": {"texture_width": 16, "texture_height": 16, "uv": [0, 0], "uv_size": [16, 16]}},
        "minecraft:particle_appearance_tinting": {"color": color},
    })
    burst = eff("nrpg:burst", {
        "minecraft:emitter_rate_instant": {"num_particles": 28},
        "minecraft:emitter_lifetime_once": {"active_time": 0.05},
        "minecraft:emitter_shape_disc": {"radius": 0.6, "direction": "outwards", "plane_normal": [0, 1, 0]},
        "minecraft:particle_lifetime_expression": {"max_lifetime": "math.random(0.4, 0.9)"},
        "minecraft:particle_initial_speed": "math.random(3, 7)",
        "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 2.5, 0], "linear_drag_coefficient": 3},
        "minecraft:particle_appearance_billboard": {
            "size": ["0.35 * (1 - variable.particle_age / variable.particle_lifetime)", "0.35 * (1 - variable.particle_age / variable.particle_lifetime)"],
            "facing_camera_mode": "lookat_xyz", "uv": {"texture_width": 16, "texture_height": 16, "uv": [0, 0], "uv_size": [16, 16]}},
        "minecraft:particle_appearance_tinting": {"color": color},
    })
    dump(os.path.join(rp, "particles", "nrpg_beam.particle.json"), beam)
    dump(os.path.join(rp, "particles", "nrpg_burst.particle.json"), burst)


# ---------------------------------------------------------------- loot
def loot(bp):
    dump(os.path.join(bp, "loot_tables", "empty.json"), {"pools": []})
    dump(os.path.join(bp, "loot_tables", "nrpg", "wolf.json"), {"pools": [{"rolls": 1, "entries": [
        {"type": "item", "name": "minecraft:bone", "weight": 3, "functions": [{"function": "set_count", "count": {"min": 0, "max": 2}}]},
        {"type": "item", "name": "nrpg:rune_shard", "weight": 1}]}]})
    for bid, b in D.BOSSES.items():
        tier = D.BY_ID[b["dungeon"]]["tier"]
        mul = {"beginner": 1, "mid": 2, "high": 3}[tier]
        entries = [
            {"type": "item", "name": "minecraft:golden_apple", "weight": 2, "functions": [{"function": "set_count", "count": {"min": 1, "max": mul}}]},
            {"type": "item", "name": "minecraft:iron_ingot" if mul == 1 else "minecraft:diamond", "weight": 3,
             "functions": [{"function": "set_count", "count": {"min": 2, "max": 2 + mul * 2}}]},
            {"type": "item", "name": "minecraft:emerald", "weight": 2, "functions": [{"function": "set_count", "count": {"min": 3, "max": 6 * mul}}]},
        ]
        pools = [{"rolls": 2, "entries": entries},
                 {"rolls": 1, "entries": [{"type": "item", "name": "minecraft:experience_bottle", "weight": 1,
                                           "functions": [{"function": "set_count", "count": {"min": 2 * mul, "max": 5 * mul}}]}]}]
        dump(os.path.join(bp, "loot_tables", "nrpg", "bosses", bid + ".json"), {"pools": pools})


# ---------------------------------------------------------------- script data
def js_data(world_data):
    bosses = {}
    for bid, b in D.BOSSES.items():
        bosses[bid] = dict(ko=b["ko"], title=b["title"], dungeon=b["dungeon"], role=b["role"], color=b["color"],
                           skills=b["skills"], phases=[[p, pool] for p, pool in b["phases"]])
    dungeons = {}
    for d in D.DUNGEONS:
        dungeons[d["id"]] = dict(id=d["id"], no=d["no"], tier=d["tier"], ko=d["ko"], realm=d["realm"], color=d["color"],
                                 lv=D.TIERS[d["tier"]]["lv"], blurb=d["blurb"], zones=[z["ko"] for z in d["zones"]])
    mobs = {k: [v[0], v[1], v[2], v[3]] for k, v in D.MOBS.items()}
    data = dict(BOSSES=bosses, DUNGEONS=dungeons, ORDER=D.ORDER, MOBS=mobs)
    data.update(world_data)
    lines = ["// generated by nr_pack.py - world coordinates and design data"]
    for k, v in data.items():
        lines.append("export const %s = %s;" % (k, json.dumps(v, ensure_ascii=False, separators=(",", ":"))))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- manifests
def manifests(bp, rp):
    dump(os.path.join(bp, "manifest.json"), {
        "format_version": 2,
        "header": {"name": BP_NAME, "description": "아홉 세계의 항해 — 보스 22종, 바닥 경고 스킬, 강화, 일일보상, 항해",
                   "uuid": BP_UUID, "version": VERSION, "min_engine_version": MIN_ENGINE},
        "modules": [
            {"type": "data", "uuid": str(uuid.uuid5(NS, "bp-data")), "version": VERSION},
            {"type": "script", "language": "javascript", "uuid": str(uuid.uuid5(NS, "bp-script")), "version": VERSION,
             "entry": "scripts/main.js"},
        ],
        "dependencies": [
            {"uuid": RP_UUID, "version": VERSION},
            {"module_name": "@minecraft/server", "version": SERVER_API},
            {"module_name": "@minecraft/server-ui", "version": UI_API},
        ],
    })
    dump(os.path.join(rp, "manifest.json"), {
        "format_version": 2,
        "header": {"name": RP_NAME, "description": "아홉 세계의 항해 — 보스 모델, 바닥 경고 표시, 아이템",
                   "uuid": RP_UUID, "version": VERSION, "min_engine_version": MIN_ENGINE},
        "modules": [{"type": "resources", "uuid": str(uuid.uuid5(NS, "rp-res")), "version": VERSION}],
    })


def lang(rp):
    lines = ["pack.name=" + RP_NAME, "pack.description=보스 모델, 바닥 경고 표시, 아이템"]
    for bid, b in D.BOSSES.items():
        lines.append("entity.nrpg:%s.name=%s" % (bid, b["ko"]))
        lines.append("item.spawn_egg.entity.nrpg:%s.name=%s 소환" % (bid, b["ko"]))
    lines += ["entity.nrpg:telegraph.name=경고 표시", "entity.nrpg:illusion.name=환영", "entity.nrpg:dummy.name=훈련용 허수아비",
              "entity.nrpg:iron_wolf.name=철숲 늑대", "entity.nrpg:fenrir_pup.name=펜리르의 새끼"]
    for key, it in ITEMS.items():
        lines.append("item.nrpg:%s=%s" % (key, it["ko"]))
    txt = "\n".join(lines) + "\n"
    for code in ("ko_KR", "en_US"):
        dump(os.path.join(rp, "texts", code + ".lang"), txt)
    dump(os.path.join(rp, "texts", "languages.json"), ["ko_KR", "en_US"])


# ---------------------------------------------------------------- build
def build(out_root, world_data, models):
    """models: nr_models.write(rp) result -> {entity id: client info}."""
    bp = os.path.join(out_root, "norse_rpg_bp")
    rp = os.path.join(out_root, "norse_rpg_rp")
    for p in (bp, rp):
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p)
    manifests(bp, rp)
    TG.write(bp, rp)
    for bid, b in D.BOSSES.items():
        dump(os.path.join(bp, "entities", "nrpg_%s.json" % bid), boss_bp(bid, b))
    dump(os.path.join(bp, "entities", "nrpg_illusion.json"), illusion_bp())
    dump(os.path.join(bp, "entities", "nrpg_dummy.json"), dummy_bp())
    dump(os.path.join(bp, "entities", "nrpg_iron_wolf.json"), wolf_bp("nrpg:iron_wolf", "철숲 늑대", 16, 4, 0.32))
    dump(os.path.join(bp, "entities", "nrpg_fenrir_pup.json"), wolf_bp("nrpg:fenrir_pup", "펜리르의 새끼", 34, 8, 0.34, (1.1, 1.2)))
    item_tex = {}
    for key, it in ITEMS.items():
        dump(os.path.join(bp, "items", "nrpg_%s.json" % key), item_bp(key, it))
        p = os.path.join(rp, "textures", "nrpg", "items", key + ".png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        item_icon(key).save(p)
        item_tex["nrpg_" + key] = {"textures": "textures/nrpg/items/" + key}
    dump(os.path.join(rp, "textures", "item_texture.json"),
         {"resource_pack_name": "norse_rpg", "texture_name": "atlas.items", "texture_data": item_tex})
    particles(rp)
    loot(bp)
    lang(rp)
    models.write(rp, bp)
    # scripts
    sdir = os.path.join(bp, "scripts")
    os.makedirs(sdir, exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "js")):
        if f.endswith(".js"):
            shutil.copy(os.path.join(HERE, "js", f), os.path.join(sdir, f))
    dump(os.path.join(sdir, "data.js"), js_data(world_data))
    return dict(bp=bp, rp=rp, bp_uuid=BP_UUID, rp_uuid=RP_UUID, version=VERSION)


def mcpack(folder, out_file):
    from mcw import zip_dir
    if os.path.exists(out_file):
        os.remove(out_file)
    zip_dir(folder, out_file)
    return out_file
