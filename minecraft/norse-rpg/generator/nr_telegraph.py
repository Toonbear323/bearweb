"""Ground telegraph decal: one entity (nrpg:telegraph) that draws every warning shape flat on the floor.

The script sets entity properties; the client model shows the matching bones only:
    nrpg:shape  0 circle   1 ring   2 line   3 cone   4 dot (summon point)
    nrpg:a      radius / ring outer radius / line length / cone radius            (blocks)
    nrpg:b      line width                                                        (blocks)
    nrpg:v      variant: ring inner ratio index (RING_RATIOS) or cone angle index (CONE_ANGLES)
    nrpg:dur    seconds until it hits: the inner fill grows from 0 to the full shape over this time
    nrpg:col    colour index (COLORS)
Lines start at the entity and run along its facing direction (model -Z = facing); the impact marker
(double ring + cross) sits at the far end, so a laser shows its whole path and where it lands.
Everything is drawn 0.04 blocks above the entity's feet and ignores lighting so it reads in dark arenas.
"""
import json
import math
import os

import numpy as np
from PIL import Image

COLORS = ["red", "orange", "purple", "cyan", "gold", "green"]
RGB = {"red": (255, 46, 36), "orange": (255, 140, 26), "purple": (190, 90, 255), "cyan": (60, 225, 255),
       "gold": (255, 214, 60), "green": (110, 255, 80)}
RING_RATIOS = [0.2, 0.35, 0.5, 0.65, 0.8]
CONE_ANGLES = [60, 90, 120, 180]
TW, TH = 512, 768
Y = 0.6          # plane height in model units (1/16 block)

# atlas regions (u, v, w, h)
R_CIRCLE = (0, 0, 128, 128)
R_CFILL = (128, 0, 128, 128)
R_IMPACT = (256, 0, 128, 128)
R_DOT = (384, 0, 128, 128)
R_RING = [(i * 128 % 512, 128 + (i * 128 // 512) * 128, 128, 128) for i in range(5)]            # 128..383
R_RFILL = [((i + 5) * 128 % 512, 128 + ((i + 5) * 128 // 512) * 128, 128, 128) for i in range(5)]
R_LFILL = (256, 384, 64, 128)
R_LEDGE = (320, 384, 16, 128)
R_LPROG = (336, 384, 64, 128)
R_LCAP = (400, 384, 112, 16)
R_CONE = [(i * 128, 512, 128, 64) for i in range(4)]
R_CONEF = [(i * 128, 576, 128, 64) for i in range(4)]
R_CHEV = (0, 640, 128, 128)       # chevrons travelling along a charge path (unused by bones, spare)


def _alpha_img(w, h, fn, aa=3):
    """fn(x, y) on [0,1]^2 returns alpha 0..1 (supersampled)."""
    ys, xs = np.mgrid[0:h * aa, 0:w * aa]
    u = (xs + 0.5) / (w * aa)
    v = (ys + 0.5) / (h * aa)
    a = fn(u, v)
    a = a.reshape(h, aa, w, aa).mean(axis=(1, 3))
    return np.clip(a, 0, 1)


def _disc(r_in, r_out, cx=0.5, cy=0.5):
    def f(u, v):
        d = np.hypot(u - cx, v - cy) * 2
        return ((d >= r_in) & (d <= r_out)).astype(float)
    return f


def atlas(color):
    """RGBA atlas for one colour. Alpha carries the shape; edges are near-white hot so they read on any floor."""
    base = np.array(RGB[color], float)
    hot = base * 0.45 + 255 * 0.55
    img = np.zeros((TH, TW, 4), float)

    def put(region, a_fill, a_edge, fill_a=0.30, edge_a=1.0):
        u0, v0, w, h = region
        a = np.clip(a_fill * fill_a + a_edge * edge_a, 0, 1)
        col = base[None, None, :] * (1 - a_edge[..., None]) + hot[None, None, :] * a_edge[..., None]
        img[v0:v0 + h, u0:u0 + w, :3] = col
        img[v0:v0 + h, u0:u0 + w, 3] = a

    e = 0.045      # edge thickness (fraction of diameter)
    # circle outline: soft inner fill, faint inner ring, bright rim
    fill = _alpha_img(128, 128, _disc(0, 1))
    rim = _alpha_img(128, 128, _disc(1 - e, 1))
    inner = _alpha_img(128, 128, _disc(0.62, 0.62 + e * 0.5))
    put(R_CIRCLE, fill, np.clip(rim + inner * 0.45, 0, 1), fill_a=0.22)
    # circle progress fill
    put(R_CFILL, _alpha_img(128, 128, _disc(0, 1)), _alpha_img(128, 128, _disc(1 - e * 0.7, 1)), fill_a=0.42, edge_a=0.8)

    # impact marker: double ring + cross hair
    def impact(u, v):
        d = np.hypot(u - 0.5, v - 0.5) * 2
        r1 = (d > 0.92) & (d < 1.0)
        r2 = (d > 0.48) & (d < 0.56)
        cross = ((np.abs(u - 0.5) < 0.025) | (np.abs(v - 0.5) < 0.025)) & (d < 0.8) & (d > 0.18)
        return (r1 | r2 | cross).astype(float)
    put(R_IMPACT, _alpha_img(128, 128, _disc(0, 1)) * 0.6, _alpha_img(128, 128, impact), fill_a=0.18)

    # summon dot: rune circle (ring + 6 ticks)
    def dot(u, v):
        d = np.hypot(u - 0.5, v - 0.5) * 2
        ang = np.arctan2(v - 0.5, u - 0.5)
        ticks = (np.abs(((ang / (2 * math.pi / 6)) % 1) - 0.5) > 0.44) & (d > 0.55) & (d < 0.95)
        return (((d > 0.86) & (d < 0.98)) | ticks | (d < 0.16)).astype(float)
    put(R_DOT, _alpha_img(128, 128, _disc(0, 0.98)), _alpha_img(128, 128, dot), fill_a=0.2)

    for i, ratio in enumerate(RING_RATIOS):
        f = _alpha_img(128, 128, _disc(ratio, 1))
        edge = np.clip(_alpha_img(128, 128, _disc(1 - e, 1)) + _alpha_img(128, 128, _disc(ratio, ratio + e)), 0, 1)
        put(R_RING[i], f, edge, fill_a=0.24)
        put(R_RFILL[i], f, _alpha_img(128, 128, _disc(1 - e * 0.7, 1)), fill_a=0.42, edge_a=0.8)

    # line pieces: fill brighter in the middle across the width, constant along the length
    u = (np.arange(64) + 0.5) / 64
    prof = 0.75 + 0.25 * np.cos((u - 0.5) * math.pi)
    lf = np.tile(prof[None, :], (128, 1))
    put(R_LFILL, lf, np.zeros_like(lf), fill_a=0.26)
    put(R_LEDGE, np.zeros((128, 16)), np.ones((128, 16)))
    put(R_LPROG, lf, np.zeros_like(lf), fill_a=0.45)
    put(R_LCAP, np.zeros((16, 112)), np.ones((16, 112)))

    for i, ang in enumerate(CONE_ANGLES):
        half = math.radians(ang) / 2

        def sector(uu, vv, edge=False):
            # apex at (0.5, 1.0) (bottom centre, v grows towards the apex); radius 1 = full height
            dx = (uu - 0.5) * 2          # width 2R
            dz = (1.0 - vv)              # depth R
            d = np.hypot(dx, dz)
            th = np.arctan2(np.abs(dx), dz)
            inside = (d <= 1.0) & (th <= half + 1e-9)
            if not edge:
                return inside.astype(float)
            ee = 0.05
            rim = inside & (d >= 1 - ee)
            side = inside & ((half - th) * d <= ee * 0.9)
            return (rim | side).astype(float)
        f = _alpha_img(128, 64, lambda a, b: sector(a, b))
        ed = _alpha_img(128, 64, lambda a, b: sector(a, b, True))
        put(R_CONE[i], f, ed, fill_a=0.24)
        put(R_CONEF[i], f, np.zeros_like(f), fill_a=0.42)

    # chevrons (spare)
    def chev(uu, vv):
        return ((np.abs(((vv * 4 + np.abs(uu - 0.5) * 2) % 1) - 0.5) < 0.12) & (np.abs(uu - 0.5) < 0.4)).astype(float)
    put(R_CHEV, np.zeros((128, 128)), _alpha_img(128, 128, chev), edge_a=0.9)
    out = np.zeros((TH, TW, 4), np.uint8)
    out[..., :3] = np.clip(img[..., :3], 0, 255)
    out[..., 3] = np.clip(img[..., 3] * 255, 0, 255)
    out[out[..., 3] == 0, :3] = 0
    return Image.fromarray(out, "RGBA")


# ---------------------------------------------------------------- geometry
def _plane(origin, size, region, flip=False):
    u, v, w, h = region
    face = {"uv": [u, v], "uv_size": [w, h]}
    # 'down' face mirrored so it reads the same from below (never seen, but keeps both faces valid)
    return {"origin": origin, "size": size, "uv": {"up": face, "down": {"uv": [u, v + h], "uv_size": [w, -h]}}}


def geometry():
    bones = [{"name": "root", "pivot": [0, 0, 0]}]

    def bone(name, cubes):
        bones.append({"name": name, "parent": "root", "pivot": [0, 0, 0], "cubes": cubes})

    c = lambda reg, y: [_plane([-8, y, -8], [16, 0, 16], reg)]
    bone("c_out", c(R_CIRCLE, Y))
    bone("c_fill", c(R_CFILL, Y + 0.02))
    bone("impact", c(R_IMPACT, Y + 0.06))
    bone("dot", c(R_DOT, Y + 0.02))
    for i in range(len(RING_RATIOS)):
        bone("r%d_out" % i, c(R_RING[i], Y))
        bone("r%d_fill" % i, c(R_RFILL[i], Y + 0.02))
    bone("l_fill", [_plane([-8, Y, -16], [16, 0, 16], R_LFILL)])
    bone("l_prog", [_plane([-8, Y + 0.02, -16], [16, 0, 16], R_LPROG)])
    bone("l_edge_l", [_plane([-1.5, Y + 0.04, -16], [3, 0, 16], R_LEDGE)])
    bone("l_edge_r", [_plane([-1.5, Y + 0.04, -16], [3, 0, 16], R_LEDGE)])
    bone("l_cap", [_plane([-8, Y + 0.04, -1.5], [16, 0, 3], R_LCAP)])
    for i in range(len(CONE_ANGLES)):
        bone("k%d_out" % i, [_plane([-16, Y, -16], [32, 0, 16], R_CONE[i])])
        bone("k%d_fill" % i, [_plane([-16, Y + 0.02, -16], [32, 0, 16], R_CONEF[i])])
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.nrpg.telegraph", "texture_width": TW, "texture_height": TH,
                        "visible_bounds_width": 96, "visible_bounds_height": 6, "visible_bounds_offset": [0, 1, 0]},
        "bones": bones}]}


def animation():
    """Scale/position every bone from the synced properties. v.* are set in the client entity pre_animation."""
    S = "v.shape"
    sc = lambda cond, val: "(%s) ? (%s) : 0" % (cond, val)
    bones = {
        "c_out": {"scale": [sc(S + " == 0", "v.a * 2"), 1, sc(S + " == 0", "v.a * 2")]},
        "c_fill": {"scale": [sc(S + " == 0", "v.a * 2 * v.p"), 1, sc(S + " == 0", "v.a * 2 * v.p")]},
        # impact marker: at the end of a line, inside a circle (0.7 r) for circles
        "impact": {"position": [0, 0, "(" + S + " == 2) ? -v.a * 16 : 0"],
                   "scale": [sc("%s == 2 || %s == 0" % (S, S), "(%s == 2) ? math.max(v.b * 1.6, 2.0) : v.a * 1.4" % S), 1,
                             sc("%s == 2 || %s == 0" % (S, S), "(%s == 2) ? math.max(v.b * 1.6, 2.0) : v.a * 1.4" % S)]},
        "dot": {"scale": [sc(S + " == 4", "v.a * 2"), 1, sc(S + " == 4", "v.a * 2")],
                "rotation": [0, "q.life_time * 90", 0]},
        "l_fill": {"scale": [sc(S + " == 2", "v.b"), 1, sc(S + " == 2", "v.a")]},
        "l_prog": {"scale": [sc(S + " == 2", "v.b"), 1, sc(S + " == 2", "v.a * v.p")]},
        "l_edge_l": {"position": ["v.b * 8 - 1.5", 0, 0], "scale": [sc(S + " == 2", "1"), 1, sc(S + " == 2", "v.a")]},
        "l_edge_r": {"position": ["-v.b * 8 + 1.5", 0, 0], "scale": [sc(S + " == 2", "1"), 1, sc(S + " == 2", "v.a")]},
        "l_cap": {"position": [0, 0, "-v.a * 16 + 1.5"], "scale": [sc(S + " == 2", "v.b"), 1, sc(S + " == 2", "1")]},
    }
    for i in range(len(RING_RATIOS)):
        cond = "%s == 1 && v.vr == %d" % (S, i)
        bones["r%d_out" % i] = {"scale": [sc(cond, "v.a * 2"), 1, sc(cond, "v.a * 2")]}
        bones["r%d_fill" % i] = {"scale": [sc(cond, "v.a * 2 * v.p"), 1, sc(cond, "v.a * 2 * v.p")]}
    for i in range(len(CONE_ANGLES)):
        cond = "%s == 3 && v.vr == %d" % (S, i)
        bones["k%d_out" % i] = {"scale": [sc(cond, "v.a"), 1, sc(cond, "v.a")]}
        bones["k%d_fill" % i] = {"scale": [sc(cond, "v.a * v.p"), 1, sc(cond, "v.a * v.p")]}
    return {"format_version": "1.8.0", "animations": {
        "animation.nrpg.telegraph.shape": {"loop": True, "bones": bones}}}


def client_entity():
    tex = {c: "textures/nrpg/telegraph/%s" % c for c in COLORS}
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": "nrpg:telegraph",
        "materials": {"default": "entity_alphablend"},
        "textures": tex,
        "geometry": {"default": "geometry.nrpg.telegraph"},
        "animations": {"shape": "animation.nrpg.telegraph.shape"},
        "scripts": {
            "pre_animation": [
                "v.shape = q.property('nrpg:shape');",
                "v.a = q.property('nrpg:a');",
                "v.b = q.property('nrpg:b');",
                "v.vr = q.property('nrpg:v');",
                "v.p = math.clamp(q.life_time / math.max(q.property('nrpg:dur'), 0.05), 0, 1);",
            ],
            "animate": ["shape"],
            "should_update_bones_and_effects_offscreen": True,
        },
        "render_controllers": ["controller.render.nrpg.telegraph"],
    }}}


def render_controller():
    return {"format_version": "1.8.0", "render_controllers": {"controller.render.nrpg.telegraph": {
        "arrays": {"textures": {"Array.col": ["Texture.%s" % c for c in COLORS]}},
        "geometry": "Geometry.default",
        "materials": [{"*": "Material.default"}],
        "textures": ["Array.col[q.property('nrpg:col')]"],
        "ignore_lighting": True,
        "is_hurt_color": {},
        "on_fire_color": {},
    }}}


def behavior_entity():
    return {"format_version": "1.21.50", "minecraft:entity": {
        "description": {
            "identifier": "nrpg:telegraph", "is_spawnable": False, "is_summonable": True,
            "properties": {
                "nrpg:shape": {"type": "int", "range": [0, 4], "default": 0, "client_sync": True},
                "nrpg:a": {"type": "float", "range": [0.0, 96.0], "default": 0.0, "client_sync": True},
                "nrpg:b": {"type": "float", "range": [0.0, 32.0], "default": 0.0, "client_sync": True},
                "nrpg:v": {"type": "int", "range": [0, 7], "default": 0, "client_sync": True},
                "nrpg:dur": {"type": "float", "range": [0.0, 30.0], "default": 1.0, "client_sync": True},
                "nrpg:col": {"type": "int", "range": [0, len(COLORS) - 1], "default": 0, "client_sync": True},
            },
        },
        "component_groups": {"nrpg:despawn": {"minecraft:instant_despawn": {}}},
        "components": {
            "minecraft:type_family": {"family": ["nrpg_telegraph", "inanimate"]},
            "minecraft:collision_box": {"width": 0.1, "height": 0.1},
            "minecraft:custom_hit_test": {"hitboxes": [{"width": 0.0, "height": 0.0, "pivot": [0, -8, 0]}]},
            "minecraft:physics": {"has_gravity": False, "has_collision": False},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": "no"}]},
            "minecraft:health": {"value": 1, "max": 1},
            "minecraft:knockback_resistance": {"value": 1.0},
            "minecraft:fire_immune": {},
            "minecraft:breathable": {"breathes_water": True, "breathes_air": True, "suffocate_time": 0},
            "minecraft:body_rotation_always_follows_head": {},
            "minecraft:conditional_bandwidth_optimization": {},
            # safety net: a telegraph never outlives 20 s even if the script that owns it stops
            "minecraft:timer": {"looping": False, "time": 20, "time_down_event": {"event": "nrpg:despawn"}},
        },
        "events": {"nrpg:despawn": {"add": {"component_groups": ["nrpg:despawn"]}}},
    }}


def write(bp, rp):
    os.makedirs(os.path.join(rp, "textures", "nrpg", "telegraph"), exist_ok=True)
    for c in COLORS:
        atlas(c).save(os.path.join(rp, "textures", "nrpg", "telegraph", c + ".png"))
    files = {
        os.path.join(rp, "models", "entity", "nrpg_telegraph.geo.json"): geometry(),
        os.path.join(rp, "animations", "nrpg_telegraph.animation.json"): animation(),
        os.path.join(rp, "entity", "nrpg_telegraph.entity.json"): client_entity(),
        os.path.join(rp, "render_controllers", "nrpg_telegraph.render_controllers.json"): render_controller(),
        os.path.join(bp, "entities", "nrpg_telegraph.json"): behavior_entity(),
    }
    for path, data in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(data, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return list(files)


def ratio_index(inner, outer):
    r = inner / max(outer, 0.01)
    return min(range(len(RING_RATIOS)), key=lambda i: abs(RING_RATIOS[i] - r))


if __name__ == "__main__":
    im = atlas("red")
    bg = Image.new("RGBA", im.size, (40, 40, 44, 255))
    bg.alpha_composite(im)
    bg.save("/tmp/claude-0/-home-user-bearweb/f4f7b110-48b0-5375-ae4d-67c55b2d90dd/scratchpad/tg_atlas.png")
    print("ok")
