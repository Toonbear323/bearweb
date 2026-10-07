"""Boss models for the 22 bosses (+ wolves, illusion, training dummy): procedural geometry, painted textures,
animations, animation controller, client entities, render controllers.

Archetypes: humanoid (normal / hunch / slim / dwarf / giant), winged (eagle giant), beast (wolf),
dragon, serpent, spirit (living flame).
"""
import json
import math
import os

import nr_design as D
from nr_model_core import Model, render, hexrgb

# ---------------------------------------------------------------- helpers
def M(kind, c=None, **kw):
    d = dict(kind=kind)
    if c is not None:
        d["c"] = c
    d.update(kw)
    return d


def darker(h, f=0.7):
    r, g, b = hexrgb(h)
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))


def lighter(h, f=1.25):
    r, g, b = hexrgb(h)
    return "#%02x%02x%02x" % (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))


def mix(a, b, t):
    ra, rb = hexrgb(a), hexrgb(b)
    return "#%02x%02x%02x" % tuple(int(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


# ---------------------------------------------------------------- humanoid
BUILDS = {
    #          head  legs  chest_w arm_t leg_t depth
    "normal": (0.20, 0.42, 0.36, 0.10, 0.115, 0.20),
    "slim":   (0.19, 0.45, 0.30, 0.085, 0.10, 0.17),
    "hunch":  (0.20, 0.40, 0.38, 0.10, 0.11, 0.21),
    "dwarf":  (0.27, 0.27, 0.50, 0.14, 0.15, 0.30),
    "giant":  (0.16, 0.40, 0.42, 0.12, 0.13, 0.22),
}


def ev(x, lo=2):
    """round to an even integer (pixel art reads cleaner on even sizes)."""
    return max(lo, int(round(x / 2.0)) * 2)


def humanoid(ident, H, pal, kit, build="normal"):
    m = Model(ident, visible=(max(4, H / 16 * 2.8), H / 16 * 1.5))
    hsr, legr, cwr, armr, legtr, depr = BUILDS[build]
    hs = ev(H * hsr, 8)
    legH = round(H * legr)
    torsoH = H - legH - hs
    cw = ev(H * cwr, 8)                       # chest width
    ww = ev(cw * 0.74, 6)                     # waist width
    at = ev(H * armr, 4)                      # arm thickness
    lt = ev(H * legtr, 4)                     # leg thickness
    dep = ev(H * depr, 5)                     # torso depth
    skin = pal.get("skin", "#c99a78")
    cloth = pal.get("cloth", "#3b4a3f")
    metal = pal.get("metal", "#7b7466")
    trim = pal.get("trim", "#a8873e")
    glow = pal.get("glow", "#7fe0ff")
    skinmat = M("skin", skin)
    if kit.get("stone"):
        skinmat = M("stone", skin, moss=pal.get("moss") if kit.get("moss") else None, cracks_glow=glow)
    if kit.get("cracks"):
        skinmat = M("stone", skin, cracks_glow=trim)
    armor = M("metal", metal, trim=trim, rivets=True, seam=max(4, at // 2 + 2))
    plain_armor = M("metal", metal, seam=99)
    clothm = M("cloth", cloth, trim=trim, fold=4 if H < 60 else 5)
    dark_cloth = M("cloth", darker(cloth, 0.78), fold=3)
    leather = M("leather", "#4a3424" if build != "dwarf" else "#5a3a24")
    gloves = M("leather", "#2e2018") if not kit.get("claws") else M("bone", "#cfc6b0")
    robe = kit.get("robe")

    m.bone("root", pivot=(0, 0, 0))
    hy = legH
    m.bone("waist", "root", pivot=(0, hy, 0))
    hunch = 22 if (build == "hunch" or kit.get("hunch")) else 0
    m.bone("chest", "waist", pivot=(0, hy + torsoH * 0.35, 0), rotation=(hunch, 0, 0))
    top = hy + torsoH
    belly = round(torsoH * 0.38)
    # hips + belt
    m.box("waist", (-ww / 2, hy - 2, -dep / 2 + 0.5), (ww, belly + 2, dep - 1), dark_cloth if not robe else clothm)
    m.box("waist", (-ww / 2 - 0.5, hy - 1, -dep / 2), (ww + 1, 2.5, dep), leather)
    m.box("waist", (-2, hy - 1.5, -dep / 2 - 0.8), (4, 3.5, 1), M("gold", trim))
    # chest: tapered torso (chest wider than waist)
    ch = torsoH - belly
    m.box("chest", (-cw / 2, hy + belly, -dep / 2), (cw, ch, dep), clothm)
    if kit.get("decay"):
        m.box("chest", (-cw / 2 + 1.5, hy + belly + 1, -dep / 2 - 0.6), (cw - 3, ch * 0.55, 0.6), M("chain", darker(metal, 0.9)))
        m.box("chest", (-cw / 4, hy + belly + ch * 0.25, -dep / 2 - 0.9), (cw / 2, ch * 0.3, 0.5), M("bone", "#cfc6aa"))
        m.box("chest", (-1, hy + belly + ch * 0.32, -dep / 2 - 1.1), (2, 2, 0.4), M("glow", g=glow))
    elif build == "dwarf" or kit.get("apron"):
        m.box("chest", (-cw / 2 + 1.5, hy - 4, -dep / 2 - 1), (cw - 3, torsoH - 1, 1), M("leather", "#6b4a2b"))
    elif not robe:
        # breastplate with a central ridge
        m.box("chest", (-cw / 2 - 0.5, hy + belly + ch * 0.35, -dep / 2 - 0.6), (cw + 1, ch * 0.62, dep + 1.2), armor)
        m.box("chest", (-1, hy + belly + ch * 0.35, -dep / 2 - 1.1), (2, ch * 0.62, 0.6), M("gold", trim))
    if robe:
        m.box("chest", (-cw / 2 - 0.5, top - 3, -dep / 2 - 0.6), (cw + 1, 3, dep + 1.2), M("gold", trim))
        m.box("chest", (-1.5, hy + belly, -dep / 2 - 0.7), (3, ch - 3, 0.6), M("gold", trim))
    # collar (fur or metal gorget)
    m.box("chest", (-cw / 2 + 1, top - 2, -dep / 2 - 1), (cw - 2, 3.5, dep + 2), M("fur", pal.get("fur", "#4a3a2c")) if not kit.get("ghost") else M("glow", g=glow, ga=120))
    # head
    m.bone("head", "chest", pivot=(0, top, 0), rotation=(-hunch * 0.9, 0, 0))
    facemat = M("face", skin, eye=pal.get("eye", "#e8e2d0"), eye_glow=glow if kit.get("glow_eyes", True) else None,
                hair=pal.get("hair") if kit.get("hair") else None, half=pal.get("skin2") if kit.get("half") else None,
                decay="#4a5a40" if kit.get("decay") else None, mouth="#2a1414")
    m.box("head", (-hs / 2, top, -hs / 2), (hs, hs, hs), facemat)
    m.box("head", (-hs / 2 - 0.3, top + hs * 0.56, -hs / 2 - 0.4), (hs + 0.6, 1, 0.6), M("skin", darker(skin, 0.7)))   # brow ridge
    helm(m, kit.get("helm", "none"), hs, top, armor, pal, kit)
    if kit.get("beard"):
        bc = pal.get("beard", mix(skin, "#d8d8d8", 0.55) if build != "dwarf" else "#c3c8cc")
        bmat = M("flame", "#ff8a1f", core="#fff2a8", c2="#c02a0a") if kit.get("fire") else M("hair", bc)
        bl = round(hs * (0.95 if build == "dwarf" else 0.6))
        bz = min(-hs / 2 - 1.2, -dep / 2 - 2.4)          # in front of the chest armour
        m.box("head", (-hs / 2 + 0.5, top - bl + hs * 0.32, bz), (hs - 1, bl, 1.6), bmat)
        m.box("head", (-hs / 2 + 0.5, top + hs * 0.05, -hs / 2 - 1.2), (hs - 1, hs * 0.3, bz + 1.6 + hs / 2 + 1.2 if bz < -hs / 2 - 1.2 else 1.6), bmat)
        m.box("head", (-hs / 2 + 2, top - bl - 2 + hs * 0.32, bz + 0.2), (2, 3, 1.4), bmat)
        m.box("head", (hs / 2 - 4, top - bl - 2 + hs * 0.32, bz + 0.2), (2, 3, 1.4), bmat)
        m.box("head", (-hs / 2 - 0.4, top + hs * 0.2, -hs / 2 + 0.5), (1, hs * 0.4, hs * 0.5), bmat)
        m.box("head", (hs / 2 - 0.6, top + hs * 0.2, -hs / 2 + 0.5), (1, hs * 0.4, hs * 0.5), bmat)
    if kit.get("hair"):
        hl = round(hs * (1.5 if build == "slim" else 1.0))
        hm = M("flame", "#ff6a1a", core="#ffd27a", c2="#a01a08") if kit.get("fire") else M("hair", pal.get("hair", "#2a1a12"))
        m.box("head", (-hs / 2 - 0.5, top + hs - hl, hs / 2 - 1.5), (hs + 1, hl + 0.5, 2.2), hm)
    # arms (upper + fore), big layered pauldrons
    au = round(torsoH * (0.55 if build != "dwarf" else 0.48))
    af = round(torsoH * (0.52 if build != "dwarf" else 0.46))
    sx = cw / 2 + at / 2 - 0.5
    bare = kit.get("bare_arms", build == "giant")
    for side, sgn in (("r", -1), ("l", 1)):
        px = sgn * sx
        m.bone("arm_" + side, "chest", pivot=(px, top - 2, 0), rotation=(4, 0, -sgn * 6))
        m.box("arm_" + side, (px - at / 2, top - au - 1, -at / 2), (at, au + 1, at), skinmat if bare else clothm)
        if not robe or kit.get("cape"):
            pw = at + 4
            m.box("arm_" + side, (px - pw / 2 + sgn * 1, top - 5, -pw / 2), (pw, 5, pw), armor, rotation=(0, 0, -sgn * 12), pivot=(px, top - 2, 0))
            m.box("arm_" + side, (px - (pw - 2) / 2 + sgn * 1.5, top - 1, -(pw - 2) / 2), (pw - 2, 2, pw - 2), plain_armor, rotation=(0, 0, -sgn * 12), pivot=(px, top - 2, 0))
        else:
            m.box("arm_" + side, (px - at / 2 - 1, top - 4, -at / 2 - 1), (at + 2, 4, at + 2), clothm)
        if kit.get("frost"):
            for k in range(2):
                m.box("arm_" + side, (px - 1 + sgn * (1 + k * 2), top + 1, -1.5 + k * 2), (2, 3 + k * 2, 2), M("ice"), rotation=(0, 0, sgn * (15 + k * 10)), pivot=(px, top, 0))
        if kit.get("fire"):
            m.box("arm_" + side, (px - 2, top, -2), (4, 5, 4), M("flame", "#ff8a1f", core="#fff2a8", c2="#c02a0a"))
        ey = top - au
        m.bone("fore_" + side, "arm_" + side, pivot=(px, ey, 0), rotation=(-14, 0, 0))
        m.box("fore_" + side, (px - at / 2 + 0.25, ey - af, -at / 2 + 0.25), (at - 0.5, af, at - 0.5), skinmat if bare else clothm)
        m.box("fore_" + side, (px - at / 2 - 0.5, ey - af * 0.75, -at / 2 - 0.5), (at + 1, af * 0.5, at + 1), armor if not robe else leather)
        m.box("fore_" + side, (px - at / 2, ey - af - 3, -at / 2), (at, 3.5, at), gloves)
        if kit.get("claws"):
            for k in range(3):
                m.box("fore_" + side, (px - at / 2 + 0.3 + k * (at - 0.6) / 3, ey - af - 6, -at / 2 - 0.4), (0.8, 3.5, 0.8), M("bone", "#e8e0c8"))
        if side == "l" and kit.get("ring"):
            m.box("fore_l", (px - at / 2, ey - af - 1.5, -at / 2), (at, 1, at), M("glow", g="#ffd84a"), inflate=0.3)
    hand_y = top - au - af - 1.5
    m.bone("weapon", "fore_r", pivot=(-sx, hand_y, -0.5), rotation=(55, 0, 0))
    weapon(m, kit.get("weapon", "none"), H, at, pal, kit, origin=(-sx, hand_y, -0.5))
    if kit.get("weapon") == "daggers":
        m.bone("weapon_l", "fore_l", pivot=(sx, hand_y, -0.5), rotation=(55, 0, 0))
        dagger(m, "weapon_l", (sx, hand_y, -0.5), H, pal)
    # legs: thigh + shin with boots
    for side, sgn in (("r", -1), ("l", 1)):
        px = sgn * (ww / 2 - lt / 2)
        thigh = round(legH * 0.5)
        m.bone("leg_" + side, "root", pivot=(px, legH, 0))
        m.box("leg_" + side, (px - lt / 2, legH - thigh, -lt / 2), (lt, thigh + 1, lt),
              M("cloth", darker(cloth, 0.7), fold=3) if not kit.get("bare_legs") else skinmat)
        m.bone("shin_" + side, "leg_" + side, pivot=(px, legH - thigh, 0))
        shin = legH - thigh
        if kit.get("talons"):
            m.box("shin_" + side, (px - lt / 2 + 0.5, 2, -lt / 2 + 0.5), (lt - 1, shin - 2, lt - 1), M("skin", "#c9a85a"))
            for k in range(3):
                m.box("shin_" + side, (px - lt / 2 + 0.2 + k * (lt - 0.4) / 3, 0, -lt / 2 - 2.5), (1, 2, 3.5), M("bone", "#2a2420"))
        else:
            m.box("shin_" + side, (px - lt / 2 + 0.25, 0, -lt / 2 + 0.25), (lt - 0.5, shin, lt - 0.5), leather)
            m.box("shin_" + side, (px - lt / 2 - 0.5, shin * 0.35, -lt / 2 - 0.7), (lt + 1, shin * 0.5, lt + 1), M("metal", darker(metal, 0.85), seam=99, trim=trim))
            m.box("shin_" + side, (px - lt / 2 - 0.5, 0, -lt / 2 - 2), (lt + 1, max(2.5, round(shin * 0.22)), lt + 2.5), M("leather", "#2a1e16"))
    # skirt panels / robe
    if robe:
        rl = legH + 1
        m.bone("skirt_f", "waist", pivot=(0, hy, -dep / 2))
        m.box("skirt_f", (-ww / 2 - 2, hy - rl + 1, -dep / 2 - 1.5), (ww + 4, rl, 2), M("cloth", cloth, trim=trim, trim_top=True))
        m.bone("skirt_b", "waist", pivot=(0, hy, dep / 2))
        m.box("skirt_b", (-ww / 2 - 2, hy - rl + 1, dep / 2 - 0.5), (ww + 4, rl, 2), M("cloth", cloth, trim=trim))
        m.box("waist", (-ww / 2 - 2, hy - rl + 2, -dep / 2 - 0.5), (2, rl - 1, dep + 1), M("cloth", darker(cloth, 0.88), trim=trim))
        m.box("waist", (ww / 2, hy - rl + 2, -dep / 2 - 0.5), (2, rl - 1, dep + 1), M("cloth", darker(cloth, 0.88), trim=trim))
    else:
        tl = round(legH * 0.5)
        m.bone("skirt_f", "waist", pivot=(0, hy, -dep / 2))
        m.box("skirt_f", (-ww / 2 + 1, hy - tl, -dep / 2 - 1), (ww - 2, tl, 1), M("cloth", cloth, trim=trim, pattern="stripes", c2=trim))
        m.bone("skirt_b", "waist", pivot=(0, hy, dep / 2))
        m.box("skirt_b", (-ww / 2 + 1, hy - tl, dep / 2), (ww - 2, tl, 1), M("cloth", cloth, trim=trim))
        if kit.get("decay") or build == "giant":
            for sgn in (-1, 1):
                m.box("waist", (sgn * (ww / 2) - (1 if sgn > 0 else 0), hy - tl * 0.8, -dep / 2 + 1), (1, tl * 0.8, dep - 2), M("chain", metal))
    # cape (two segments, torn hem)
    if kit.get("cape"):
        capw = cw - 1
        c1 = round((top - 2) * 0.48)
        capec = pal.get("cape", darker(cloth, 0.72) if not kit.get("half") else "#120e18")
        m.bone("cape1", "chest", pivot=(0, top - 1, dep / 2 + 0.6), rotation=(5, 0, 0))
        m.box("cape1", (-capw / 2, top - 1 - c1, dep / 2 + 0.6), (capw, c1, 1), M("cloth", capec, trim=trim, fold=3))
        m.bone("cape2", "cape1", pivot=(0, top - 1 - c1, dep / 2 + 1.1))
        m.box("cape2", (-capw / 2, max(1, top - 1 - 2 * c1 + 1), dep / 2 + 0.6), (capw, c1 - 1, 1),
              M("fur", capec, shaggy=True) if kit.get("decay") else M("cloth", capec, trim=trim, fold=3))
    if kit.get("sack"):
        m.box("waist", (ww / 2, hy - 7, -2.5), (5, 7, 5), M("leather", "#7a5a30"))
        m.box("waist", (ww / 2 + 1, hy - 1, -1.5), (3, 2, 3), M("gold", "#ffd84a"))
    if kit.get("wings"):
        wings_feather(m, H, top, dep, pal)
    if kit.get("head") == "eagle":
        eagle_head(m, hs, top, pal)
    if kit.get("half"):
        # the dead half: a bony shoulder and ribs on the left side
        m.box("chest", (cw / 2 - 3, hy + belly + 2, -dep / 2 - 0.7), (3, ch - 4, 0.6), M("bone", "#9fb1b8"))
    return m


def helm(m, kind, hs, top, armor, pal, kit):
    trim = pal.get("trim", "#a8873e")
    metal = pal.get("metal", "#7b7466")
    h0 = top + hs
    if kind in ("horned", "winged", "spiked", "cap"):
        m.box("head", (-hs / 2 - 0.5, top + hs * 0.45, -hs / 2 - 0.5), (hs + 1, hs * 0.55 + 1, hs + 1), armor)
        m.box("head", (-0.75, top + hs * 0.1, -hs / 2 - 1.2), (1.5, hs * 0.5, 1), M("metal", metal, trim=trim))   # nose guard
    if kind == "horned":
        for sgn in (-1, 1):
            m.bone("horn_%d" % sgn, "head", pivot=(sgn * hs / 2, h0 - 2, 0), rotation=(0, 0, -sgn * 35))
            m.box("horn_%d" % sgn, (sgn * hs / 2 - (0 if sgn > 0 else 2), h0 - 3, -1), (2, 2, 2), M("bone", "#ded3b6"))
            m.box("horn_%d" % sgn, (sgn * hs / 2 + (1.5 if sgn > 0 else -3.5), h0 - 2, -0.75), (2, hs * 0.55, 1.5), M("bone", "#e8dcc0"),
                  rotation=(0, 0, -sgn * 25), pivot=(sgn * hs / 2, h0 - 2, 0))
    elif kind == "winged":
        for sgn in (-1, 1):
            m.box("head", (sgn * (hs / 2 + 0.3) - (0 if sgn > 0 else 1), top + hs * 0.55, -1), (1, hs * 0.6, hs * 0.55),
                  M("feather", "#e8e4dc", c2="#b8b0a0"), rotation=(sgn * 0, 0, -sgn * 20), pivot=(sgn * hs / 2, top + hs * 0.6, 0))
    elif kind == "spiked":
        for k in range(5):
            x = -hs / 2 + 1 + k * (hs - 2) / 4
            m.box("head", (x - 0.5, h0, -0.5), (1, 2 + (k % 2) * 2, 1), M("metal", darker(metal, 0.7)))
    elif kind == "hood":
        # open cowl: top, sides and back; the face stays visible in shadow
        hc = pal.get("cloth")
        cm = M("cloth", hc, fold=3)
        m.box("head", (-hs / 2 - 1, top + hs - 0.5, -hs / 2 - 2), (hs + 2, 2, hs + 3), cm)
        m.box("head", (-hs / 2 - 1, top - 1, -hs / 2 - 2), (1.2, hs + 0.5, hs + 3), cm)
        m.box("head", (hs / 2 - 0.2, top - 1, -hs / 2 - 2), (1.2, hs + 0.5, hs + 3), cm)
        m.box("head", (-hs / 2 - 1, top - 1, hs / 2 - 0.2), (hs + 2, hs + 0.5, 1.2), cm)
        m.box("head", (-hs / 2 - 1, top + hs - 3, hs / 2 + 0.8), (hs + 2, 3, 3), cm)          # point of the hood
        m.box("head", (-hs / 2 + 0.2, top + hs - 1.5, -hs / 2 - 1.6), (hs - 0.4, 1, 0.4), M("dark", "#0c0a10"))
    elif kind == "crown":
        m.box("head", (-hs / 2 - 0.5, h0 - 1, -hs / 2 - 0.5), (hs + 1, 2, hs + 1), M("gold", trim))
        for k in range(5):
            x = -hs / 2 + k * hs / 4
            m.box("head", (x - 0.5, h0 + 1, -hs / 2 - 0.5), (1, 2 + (k % 2) * 1.5, 1), M("gold", trim))
            m.box("head", (x - 0.5, h0 + 1, hs / 2 - 0.5), (1, 2 + (k % 2) * 1.5, 1), M("gold", trim))
        m.box("head", (-0.75, h0 + 0.5, -hs / 2 - 1), (1.5, 1.5, 0.6), M("glow", g=pal.get("glow", "#fff")))
    elif kind == "circlet":
        m.box("head", (-hs / 2 - 0.3, top + hs * 0.7, -hs / 2 - 0.3), (hs + 0.6, 1, hs + 0.6), M("gold", trim))
        m.box("head", (-0.75, top + hs * 0.68, -hs / 2 - 0.8), (1.5, 1.5, 0.6), M("glow", g=pal.get("glow", "#fff")))
    elif kind == "horns":
        for sgn in (-1, 1):
            m.box("head", (sgn * hs * 0.25 - 0.75, h0 - 1, -hs / 4), (1.5, hs * 0.6, 1.5), M("gold", "#c8a02a"),
                  rotation=(-25, 0, -sgn * 30), pivot=(sgn * hs * 0.25, h0, 0))
            m.box("head", (sgn * hs * 0.25 - 0.75 + sgn * 2.5, h0 + hs * 0.45, -hs / 4 + 2), (1.2, hs * 0.4, 1.2), M("gold", "#e0b83a"),
                  rotation=(-60, 0, -sgn * 10), pivot=(sgn * hs * 0.25 + sgn * 2.5, h0 + hs * 0.45, -hs / 4 + 2))
    elif kind == "cap":
        m.box("head", (-hs / 2 - 1, top + hs * 0.45, -hs / 2 - 1), (hs + 2, 1.5, hs + 2), M("leather", "#5a3a24"))


def weapon(m, kind, H, t, pal, kit, origin):
    ox, oy, oz = origin
    trim = pal.get("trim", "#a8873e")
    metal = pal.get("metal", "#8a8a90")
    glow = pal.get("glow", "#ffffff")
    L = H * 0.55
    W = "weapon"
    grip = M("leather", "#3a2414")
    if kind == "greatsword":
        m.box(W, (ox - 1, oy - 1, oz - 4), (2, 2, 6), grip)
        m.box(W, (ox - 3.5, oy - 1.5, oz - 5), (7, 3, 1.5), M("gold", trim))
        m.box(W, (ox - 1.5, oy - 0.5, oz - 5 - L), (3, 1, L), M("metal", "#9aa2a8", trim="#d8dde0", seam=99))
        m.box(W, (ox - 0.4, oy - 0.7, oz - 5 - L * 0.95), (0.8, 1.4, L * 0.9), M("glow", g=glow, ga=150))
    elif kind == "pick":
        m.box(W, (ox - 0.75, oy - 0.75, oz - L * 0.7), (1.5, 1.5, L * 0.8), M("wood", "#6b4a2b"))
        m.box(W, (ox - 0.75, oy - 6, oz - L * 0.7), (1.5, 12, 2), M("gold", "#e0b02c"))
    elif kind == "whetstone":
        m.box(W, (ox - 3, oy - 3, oz - L * 0.75), (6, 6, L * 0.85), M("stone", "#7c7a74", cracks_glow=glow))
    elif kind == "hook":
        m.box(W, (ox - 0.6, oy - 0.6, oz - L * 0.8), (1.2, 1.2, L * 0.9), M("wood", "#3a2a22"))
        m.box(W, (ox - 0.6, oy - 7, oz - L * 0.8), (1.2, 7, 1.2), M("metal", "#6a6470"))
        m.box(W, (ox - 0.6, oy - 7, oz - L * 0.8 + 1), (1.2, 1.2, 4), M("metal", "#6a6470"))
        m.box(W, (ox - 0.4, oy - 5, oz - L * 0.8 + 4), (0.8, 3, 0.8), M("glow", g=glow))
    elif kind == "anchor":
        m.box(W, (ox - 1.5, oy - 1.5, oz - L), (3, 3, L), M("metal", "#4b5563", rivets=True))
        m.box(W, (ox - 8, oy - 1.5, oz - L), (16, 3, 3), M("metal", "#4b5563"))
        m.box(W, (ox - 8, oy - 1.5, oz - L + 3), (3, 3, 4), M("metal", "#4b5563"))
        m.box(W, (ox + 5, oy - 1.5, oz - L + 3), (3, 3, 4), M("metal", "#4b5563"))
        m.box(W, (ox - 4, oy - 2, oz - 2), (8, 4, 2), M("metal", "#6b7280"))
        m.box(W, (ox - 1, oy - 0.5, oz - L + 1), (2, 1, L - 3), M("ice"), inflate=0.2)
    elif kind == "staff":
        m.box(W, (ox - 0.75, oy - 0.75, oz - L * 0.9), (1.5, 1.5, L * 1.1), M("wood", "#4a3424"))
        m.box(W, (ox - 2.5, oy - 2.5, oz - L * 0.9 - 4), (5, 5, 5), M("glow", g=glow))
        m.box(W, (ox - 3, oy - 1, oz - L * 0.9 - 2), (6, 2, 1), M("gold", trim))
    elif kind == "bellows":
        m.box(W, (ox - 4, oy - 3, oz - 10), (8, 6, 9), M("leather", "#7a4a24"))
        m.box(W, (ox - 1, oy - 1, oz - 16), (2, 2, 6), M("metal", "#8a8a90"))
        m.box(W, (ox - 0.6, oy - 0.6, oz - 17), (1.2, 1.2, 1.2), M("glow", g=glow))
    elif kind == "hammer":
        m.box(W, (ox - 0.8, oy - 0.8, oz - L * 0.6), (1.6, 1.6, L * 0.7), M("wood", "#5a3a24"))
        m.box(W, (ox - 3.5, oy - 3.5, oz - L * 0.6 - 4), (7, 7, 5), M("metal", "#9aa0a8", rivets=True, trim=trim))
        m.box(W, (ox - 3.6, oy - 0.6, oz - L * 0.6 - 3.5), (7.2, 1.2, 4), M("glow", g=glow, ga=170))
    elif kind == "spear":
        m.box(W, (ox - 0.6, oy - 0.6, oz - L * 1.0), (1.2, 1.2, L * 1.3), M("wood", "#4a3424"))
        m.box(W, (ox - 1.5, oy - 0.5, oz - L * 1.0 - 6), (3, 1, 6), M("metal", "#c8ccd2"))
        m.box(W, (ox - 0.3, oy - 0.7, oz - L * 1.0 - 5), (0.6, 1.4, 4.5), M("glow", g=glow))
    elif kind == "flamesword":
        m.box(W, (ox - 1, oy - 1, oz - 4), (2, 2, 6), grip)
        m.box(W, (ox - 4, oy - 1.5, oz - 5), (8, 3, 1.5), M("metal", "#2a2424", trim=trim))
        m.box(W, (ox - 2, oy - 0.75, oz - 5 - L * 1.1), (4, 1.5, L * 1.1), M("flame", "#ff8a1f", core="#fff2a8", c2="#d63a12"))
    elif kind == "daggers":
        dagger(m, W, origin, H, pal)


def dagger(m, bone, origin, H, pal):
    ox, oy, oz = origin
    m.box(bone, (ox - 0.6, oy - 0.6, oz - 3), (1.2, 1.2, 4), M("leather", "#2a1a12"))
    m.box(bone, (ox - 0.8, oy - 0.4, oz - 9), (1.6, 0.8, 6), M("metal", "#b8c0c8"))
    m.box(bone, (ox - 0.2, oy - 0.5, oz - 8.5), (0.4, 1.0, 5), M("glow", g=pal.get("glow", "#7dff6a")))


def wings_feather(m, H, top, depth, pal):
    f1, f2 = pal.get("feather", "#4e4236"), pal.get("feather2", "#e9e1cf")
    span = H * 0.75
    for side, sgn in (("r", -1), ("l", 1)):
        m.bone("wing_" + side, "chest", pivot=(sgn * 4, top - 3, depth / 2), rotation=(0, sgn * 25, -sgn * 15))
        m.box("wing_" + side, (sgn * 4 - (0 if sgn > 0 else span * 0.5), top - 6, depth / 2), (span * 0.5, 6, 2), M("feather", f1, c2=f2))
        m.bone("wing2_" + side, "wing_" + side, pivot=(sgn * (4 + span * 0.5), top - 3, depth / 2), rotation=(0, 0, -sgn * 20))
        m.box("wing2_" + side, (sgn * (4 + span * 0.5) - (0 if sgn > 0 else span * 0.5), top - 14, depth / 2 + 0.5), (span * 0.5, 14, 1.5), M("feather", f1, c2=f2))
        for k in range(4):
            x = sgn * (4 + span * (0.55 + k * 0.11))
            m.box("wing2_" + side, (x - 1.5, top - 22 - k, depth / 2 + 0.6), (3, 10, 1.2), M("feather", f1, c2=f2))


def eagle_head(m, hs, top, pal):
    # replace the face with an eagle head: beak and feather crest (the head cube stays as skull)
    m.box("head", (-hs / 2 - 0.5, top - 0.5, -hs / 2 - 0.5), (hs + 1, hs + 1, hs + 1), M("feather", pal.get("feather2", "#e9e1cf"), c2="#ffffff"),
          faces={"north": M("face", pal.get("feather2", "#e9e1cf"), eye="#ffcc33", eye_glow=pal.get("glow"))})
    m.box("head", (-1.5, top + hs * 0.3, -hs / 2 - 4), (3, 3, 4), M("gold", "#e2b04a"))
    m.box("head", (-1.2, top + hs * 0.15, -hs / 2 - 4.5), (2.4, 1.5, 1.5), M("gold", "#c08a2a"))
    for k in range(3):
        m.box("head", (-0.5 + (k - 1) * 2, top + hs, -1 + k), (1, 3 + k, 3), M("feather", pal.get("feather", "#4e4236")))


# ---------------------------------------------------------------- beast (wolf)
def beast(ident, scale, pal, kit):
    """Wolf built on vanilla wolf proportions (body 6x6x9, mane 8x8x7, head 6x6x4, snout 3x3x4, legs 2x8x2)
    scaled up, with thicker legs, fur tufts, glowing eyes and optional runes / chains."""
    s = scale * 2.6
    m = Model(ident, visible=(5 * scale, 3.5 * scale))
    fur = M("fur", pal["fur"], c2=pal.get("belly"), shaggy=True, runes=pal.get("rune") if kit.get("runes") else None)
    fur2 = M("fur", pal.get("fur2", darker(pal["fur"])), c2=pal.get("belly"), shaggy=True)
    legH = 8 * s
    m.bone("root")
    by = legH + 3 * s                          # body centre height
    m.bone("body", "root", pivot=(0, by, 0))
    # hips (rear body) and mane (chest), slightly tapered
    m.box("body", (-3 * s, by - 3 * s, -1 * s), (6 * s, 6 * s, 9 * s), fur2)
    m.box("body", (-4 * s, by - 4 * s, -7 * s), (8 * s, 8 * s, 7 * s), fur)
    if kit.get("mane"):
        m.box("body", (-4.6 * s, by - 2.5 * s, -7.6 * s), (9.2 * s, 7.4 * s, 4 * s), M("fur", pal.get("fur", "#777"), shaggy=True))
        for k in range(4):
            m.box("body", (-1 * s + (k - 1.5) * 1.6 * s, by + 4 * s, -6.5 * s + k * 1.2 * s), (1.2 * s, 1.6 * s, 2 * s), fur)
    # head
    hy = by + 1.5 * s
    m.bone("head", "body", pivot=(0, hy, -7 * s))
    m.box("head", (-3 * s, hy - 3 * s, -11 * s), (6 * s, 6 * s, 4 * s),
          M("face", pal["fur"], eye="#ffffff", eye_glow=pal["glow"], eyes4=kit.get("eyes4"), mouth=darker(pal["fur"], 0.5)))
    m.box("head", (-1.5 * s, hy - 3 * s, -15 * s), (3 * s, 2 * s, 4 * s), fur2)              # muzzle (upper)
    m.box("head", (-0.6 * s, hy - 1.2 * s, -15.2 * s), (1.2 * s, 0.6 * s, 0.6 * s), M("dark", "#100c0e"))   # nose
    m.bone("jaw", "head", pivot=(0, hy - 3 * s, -11 * s))
    m.box("jaw", (-1.4 * s, hy - 4 * s, -14.6 * s), (2.8 * s, 1 * s, 3.6 * s), fur2)
    for k in range(3):
        m.box("jaw", (-1.1 * s + k * 1 * s, hy - 3.1 * s, -14.4 * s), (0.35 * s, 0.5 * s, 0.35 * s), M("bone", "#f2ead8"))
    for sgn in (-1, 1):
        m.box("head", (sgn * 2 * s - 1 * s, hy + 3 * s, -9.5 * s), (2 * s, 2.2 * s, 1 * s), fur, rotation=(10, 0, -sgn * 8),
              pivot=(sgn * 2 * s, hy + 3 * s, -9 * s))
        m.box("head", (sgn * 3 * s - 0.5 * s, hy - 2.5 * s, -10 * s), (1 * s, 3.5 * s, 3 * s), fur)          # cheek fur
    # legs: upper + lower with paws
    for name, x, z in (("leg_fr", -1, -1), ("leg_fl", 1, -1), ("leg_br", -1, 1), ("leg_bl", 1, 1)):
        lx = x * (2.4 if z < 0 else 2.0) * s
        lz = -4.5 * s if z < 0 else 6.5 * s
        lw = 2.4 * s
        m.bone(name, "body", pivot=(lx, legH + 1 * s, lz))
        m.box(name, (lx - lw / 2, legH * 0.5, lz - lw / 2), (lw, legH * 0.5 + 1.5 * s, lw), fur)
        m.bone(name + "_low", name, pivot=(lx, legH * 0.5, lz))
        m.box(name + "_low", (lx - lw / 2 + 0.2 * s, 0.6 * s, lz - lw / 2 + 0.2 * s), (lw - 0.4 * s, legH * 0.5, lw - 0.4 * s), fur2)
        m.box(name + "_low", (lx - lw / 2 - 0.1 * s, 0, lz - lw / 2 - 0.6 * s), (lw + 0.2 * s, 0.8 * s, lw + 0.8 * s), M("dark", "#2a2224"))
        if kit.get("chains") and z < 0:
            m.box(name + "_low", (lx - lw / 2 - 0.2 * s, legH * 0.25, lz - lw / 2 - 0.2 * s), (lw + 0.4 * s, 0.6 * s, lw + 0.4 * s), M("metal", "#8a8a90", seam=99))
    # tail: raised, two segments
    m.bone("tail", "body", pivot=(0, by + 1.5 * s, 8 * s), rotation=(-50, 0, 0))
    m.box("tail", (-1 * s, by + 0.5 * s, 8 * s), (2 * s, 2 * s, 5 * s), fur)
    m.bone("tail2", "tail", pivot=(0, by + 1.5 * s, 13 * s), rotation=(25, 0, 0))
    m.box("tail2", (-1.2 * s, by + 0.3 * s, 13 * s), (2.4 * s, 2.4 * s, 4 * s), M("fur", pal.get("belly", pal["fur"]), shaggy=True))
    if kit.get("chains"):
        # the broken fetter Gleipnir round the neck: a glowing ribbon
        m.box("body", (-4.8 * s, by + 0.5 * s, -7.8 * s), (9.6 * s, 0.8 * s, 1.2 * s), M("glow", g=pal["rune"], ga=200))
        m.box("body", (-5.0 * s, by - 3.5 * s, -7.4 * s), (0.6 * s, 4 * s, 0.6 * s), M("metal", "#9aa0a8", seam=99))
    return m


# ---------------------------------------------------------------- dragon
def dragon(ident, pal, kit):
    s = 1.0
    m = Model(ident, visible=(8, 5))
    sc = M("scales", pal["scale"], c2=pal["belly"])
    sc2 = M("scales", pal["scale2"], c2=pal["belly"])
    legH = 18
    m.bone("root")
    m.bone("body", "root", pivot=(0, legH + 10, 0))
    m.box("body", (-12, legH, -16), (24, 20, 34), sc)
    for k in range(6):
        m.box("body", (-1, legH + 20, -14 + k * 6), (2, 4 - (k % 2), 3), M("bone", pal["horn"]))
    # neck segments
    m.bone("neck1", "body", pivot=(0, legH + 14, -16), rotation=(-30, 0, 0))
    m.box("neck1", (-6, legH + 9, -28), (12, 11, 13), sc)
    m.bone("neck2", "neck1", pivot=(0, legH + 14, -28), rotation=(-15, 0, 0))
    m.box("neck2", (-5, legH + 10, -38), (10, 9, 11), sc)
    m.bone("head", "neck2", pivot=(0, legH + 14, -38), rotation=(40, 0, 0))
    m.box("head", (-7, legH + 9, -50), (14, 11, 13), M("face", pal["scale"], eye="#fff6a0", eye_glow=pal["glow"]))
    m.box("head", (-5, legH + 9, -60), (10, 6, 10), sc2)
    m.bone("jaw", "head", pivot=(0, legH + 9, -48))
    m.box("jaw", (-4.5, legH + 5, -59), (9, 4, 11), sc2)
    for k in range(4):
        m.box("jaw", (-4 + k * 2.6, legH + 9, -58.5), (0.8, 1.2, 0.8), M("bone", "#f2ead8"))
    for sgn in (-1, 1):
        m.box("head", (sgn * 5 - 1.5, legH + 18, -44), (3, 3, 10), M("bone", pal["horn"]), rotation=(-25, sgn * 12, 0), pivot=(sgn * 5, legH + 19, -44))
    # legs
    for name, x, z in (("leg_fr", -1, -1), ("leg_fl", 1, -1), ("leg_br", -1, 1), ("leg_bl", 1, 1)):
        lx, lz = x * 11, (-10 if z < 0 else 12)
        m.bone(name, "body", pivot=(lx, legH + 4, lz))
        m.box(name, (lx - 3.5, legH * 0.45, lz - 3.5), (7, legH * 0.55 + 4, 7), sc)
        m.bone(name + "_low", name, pivot=(lx, legH * 0.45, lz))
        m.box(name + "_low", (lx - 3, 0, lz - 3), (6, legH * 0.45, 6), sc2)
        m.box(name + "_low", (lx - 3.5, 0, lz - 6), (7, 2, 4), M("bone", pal["horn"]))
    # wings
    for side, sgn in (("r", -1), ("l", 1)):
        m.bone("wing_" + side, "body", pivot=(sgn * 10, legH + 19, -8), rotation=(0, 0, -sgn * 20))
        m.box("wing_" + side, (sgn * 10 - (0 if sgn > 0 else 26), legH + 18, -10), (26, 3, 3), M("scales", pal["scale2"]))
        m.box("wing_" + side, (sgn * 10 - (0 if sgn > 0 else 26), legH + 18.5, -8), (26, 1, 20), M("membrane", pal["wing"]))
        m.bone("wing2_" + side, "wing_" + side, pivot=(sgn * 36, legH + 19, -8), rotation=(0, 0, -sgn * 25))
        m.box("wing2_" + side, (sgn * 36 - (0 if sgn > 0 else 24), legH + 18, -10), (24, 2.5, 2.5), M("scales", pal["scale2"]))
        m.box("wing2_" + side, (sgn * 36 - (0 if sgn > 0 else 24), legH + 18.5, -8), (24, 1, 24), M("membrane", pal["wing"]))
    # tail
    prev, z0, y0 = "body", 18, legH + 12
    for k in range(5):
        n = "tail%d" % (k + 1)
        m.bone(n, prev, pivot=(0, y0, z0), rotation=(8 if k == 0 else 4, 0, 0))
        w = 9 - k * 1.5
        m.box(n, (-w / 2, y0 - w / 2, z0), (w, w, 10), sc if k % 2 == 0 else sc2)
        m.box(n, (-0.6, y0 + w / 2, z0 + 3), (1.2, 2.5, 3), M("bone", pal["horn"]))
        prev, z0 = n, z0 + 10
    return m


# ---------------------------------------------------------------- serpent
def serpent(ident, pal, kit):
    m = Model(ident, visible=(10, 7))
    sc = M("scales", pal["scale"], c2=pal["belly"])
    sc2 = M("scales", pal["scale2"], c2=pal["belly"])
    n = kit.get("segments", 7)
    m.bone("root")
    # body rises from the ground in an S; segment 0 lies on the ground at the back
    m.bone("seg0", "root", pivot=(0, 6, 30))
    m.box("seg0", (-9, 0, 22), (18, 16, 20), sc)
    prev = "seg0"
    y, z = 8, 22
    pitch = [-10, -25, -30, -20, 10, 25, 30]
    for k in range(1, n):
        name = "seg%d" % k
        m.bone(name, prev, pivot=(0, y, z), rotation=(pitch[k % len(pitch)] * 0.6, 0, 0))
        w = 17 - k * 0.8
        m.box(name, (-w / 2, y - w / 2, z - 12), (w, w, 13), sc if k % 2 else sc2)
        m.box(name, (-0.8, y + w / 2, z - 9), (1.6, 3.5, 5), M("membrane", pal["fin"]))
        prev = name
        z -= 12
        y += 6
    m.bone("head", prev, pivot=(0, y, z), rotation=(25, 0, 0))
    m.box("head", (-10, y - 6, z - 18), (20, 13, 18), M("face", pal["scale"], eye="#e8ffd0", eye_glow=pal["glow"]))
    m.box("head", (-7, y - 5, z - 28), (14, 8, 11), sc2)
    m.bone("jaw", "head", pivot=(0, y - 6, z - 16))
    m.box("jaw", (-6.5, y - 11, z - 27), (13, 5, 12), sc2)
    for k in range(4):
        m.box("jaw", (-5.5 + k * 3.4, y - 6, z - 26.5), (1, 2, 1), M("bone", "#f4f0dc"))
    for sgn in (-1, 1):
        m.box("head", (sgn * 9 - 1.5, y + 6, z - 8), (3, 3, 12), M("bone", pal["horn"]), rotation=(-30, sgn * 15, 0), pivot=(sgn * 9, y + 6, z - 8))
        m.box("head", (sgn * 10 - (0 if sgn > 0 else 6), y - 2, z - 12), (6, 8, 1), M("membrane", pal["fin"]), rotation=(0, sgn * 25, 0), pivot=(sgn * 10, y, z - 12))
    return m


# ---------------------------------------------------------------- spirit (Logi)
def spirit(ident, H, pal, kit):
    m = Model(ident, visible=(4, 4))
    core, f1, f2 = pal["core"], pal["flame"], pal["flame2"]
    fl = lambda: M("flame", f1, core=core, c2=f2)
    m.bone("root")
    m.bone("waist", "root", pivot=(0, 14, 0))
    m.box("waist", (-4, 2, -3), (8, 14, 6), fl())
    m.box("waist", (-2.5, 0, -2), (5, 6, 4), fl())
    m.bone("chest", "waist", pivot=(0, 22, 0))
    m.box("chest", (-7, 16, -4), (14, 16, 8), M("stone", pal["ember"], cracks_glow=core))
    m.box("chest", (-5, 20, -4.6), (10, 9, 0.6), M("glow", g=core))
    m.bone("head", "chest", pivot=(0, 32, 0))
    m.box("head", (-5, 32, -5), (10, 10, 10), M("face", pal["ember"], eye="#ffffff", eye_glow="#ffffff"))
    for k in range(5):
        m.box("head", (-5 + k * 2.2, 41, -3 + (k % 2) * 2), (2, 4 + (k % 3) * 3, 2), fl())
    for side, sgn in (("r", -1), ("l", 1)):
        m.bone("arm_" + side, "chest", pivot=(sgn * 8, 30, 0), rotation=(0, 0, -sgn * 15))
        m.box("arm_" + side, (sgn * 8 - 2.5, 18, -2.5), (5, 13, 5), M("stone", pal["ember"], cracks_glow=core))
        m.bone("fore_" + side, "arm_" + side, pivot=(sgn * 8, 18, 0), rotation=(-15, 0, 0))
        m.box("fore_" + side, (sgn * 8 - 2.5, 6, -2.5), (5, 12, 5), fl())
        m.box("fore_" + side, (sgn * 8 - 1.5, 2, -1.5), (3, 4, 3), M("glow", g=core))
    return m


# ---------------------------------------------------------------- per boss
def build_boss(bid, b):
    pal, kit = b["palette"], b["kit"]
    H = round(b["size"][1] * 16 * 0.97)
    ident = "geometry.nrpg." + bid
    arch = b["model"]
    if arch == "humanoid":
        build = "slim" if kit.get("hair") and not kit.get("beard") and bid in ("sinmara", "modgudr", "hel", "loki") else "normal"
        if kit.get("hunch"):
            build = "hunch"
        return humanoid(ident, H, pal, kit, build)
    if arch == "dwarf":
        return humanoid(ident, H, pal, dict(kit, glow_eyes=bid != "eitri"), "dwarf")
    if arch == "giant":
        return humanoid(ident, H, pal, kit, "giant")
    if arch == "winged":
        return humanoid(ident, H, dict(pal, skin=pal.get("feather2"), cloth=pal.get("cloth")), dict(kit, cape=False, talons=True, bare_legs=True), "normal")
    if arch == "beast":
        return beast(ident, kit.get("scale", 1.0), pal, kit)
    if arch == "dragon":
        return dragon(ident, pal, kit)
    if arch == "serpent":
        return serpent(ident, pal, kit)
    if arch == "spirit":
        return spirit(ident, H, pal, kit)
    raise ValueError(arch)


EXTRA = {
    "iron_wolf": lambda: beast("geometry.nrpg.iron_wolf", 0.55, dict(fur="#5a5f66", fur2="#3e4248", belly="#8a9098", glow="#ff4a2a", rune="#ff4a2a"), dict(mane=True)),
    "fenrir_pup": lambda: beast("geometry.nrpg.fenrir_pup", 0.7, dict(fur="#24242a", fur2="#121216", belly="#3a3a44", glow="#ff3a1a", rune="#ff7a2a"), dict(mane=True, runes=True)),
    "dummy": lambda: dummy_model(),
}


def dummy_model():
    m = Model("geometry.nrpg.dummy", visible=(2, 3))
    m.bone("root")
    m.bone("post", "root", pivot=(0, 0, 0))
    m.box("post", (-1, 0, -1), (2, 30, 2), M("wood", "#6b4a2b"))
    m.box("post", (-5, 10, -3), (10, 13, 6), M("cloth", "#c9b07a", fold=3))
    m.box("post", (-4, 23, -4), (8, 8, 8), M("face", "#d8c08a", eye="#3a2a1a", mouth="#3a2a1a"))
    m.box("post", (-11, 20, -1.5), (22, 3, 3), M("wood", "#5a3a22"))
    return m


# ---------------------------------------------------------------- animations
def bone_names(m):
    return set(m.by)


def anims(key, m, arch):
    """Animation set for one model. Looping poses read q.anim_time; walk uses q.modified_move_speed."""
    B = bone_names(m)
    A = {}
    ns = "animation.nrpg.%s." % key

    def put(name, bones, loop=True):
        A[ns + name] = {"loop": loop, "bones": {k: v for k, v in bones.items() if k in B}}

    s = "math.sin(q.life_time * %s)"
    if arch in ("humanoid", "dwarf", "giant", "winged", "spirit"):
        put("idle", {
            "chest": {"rotation": [s % 90 + " * 1.5", 0, 0], "position": [0, s % 90 + " * 0.35", 0]},
            "head": {"rotation": [s % 70 + " * 2", s % 35 + " * 4", 0]},
            "arm_r": {"rotation": [s % 80 + " * 3", 0, "3 + " + s % 80 + " * 2"]},
            "arm_l": {"rotation": ["-" + s % 80 + " * 3", 0, "-3 - " + s % 80 + " * 2"]},
            "cape1": {"rotation": [s % 100 + " * 4 + 4", 0, 0]},
            "cape2": {"rotation": [s % 110 + " * 6 + 6", 0, 0]},
            "skirt_f": {"rotation": [s % 90 + " * 2", 0, 0]},
            "skirt_b": {"rotation": ["-" + s % 90 + " * 2", 0, 0]},
            "wing_r": {"rotation": [0, s % 60 + " * 6", s % 60 + " * 5"]},
            "wing_l": {"rotation": [0, "-" + s % 60 + " * 6", "-" + s % 60 + " * 5"]},
            "waist": {"position": [0, (s % 120 + " * 1.2") if arch == "spirit" else "0", 0]},
        })
        w = "math.sin(q.life_time * 400) * 32 * q.modified_move_speed"
        put("walk", {
            "leg_r": {"rotation": [w, 0, 0]},
            "leg_l": {"rotation": ["-" + w, 0, 0]},
            "shin_r": {"rotation": ["math.max(0, -math.sin(q.life_time * 400 - 60)) * 30 * q.modified_move_speed", 0, 0]},
            "shin_l": {"rotation": ["math.max(0, math.sin(q.life_time * 400 - 60)) * 30 * q.modified_move_speed", 0, 0]},
            "arm_r": {"rotation": ["-" + w + " * 0.6", 0, 0]},
            "arm_l": {"rotation": [w + " * 0.6", 0, 0]},
            "waist": {"position": [0, "math.abs(math.sin(q.life_time * 400)) * 0.8 * q.modified_move_speed", 0]},
            "cape1": {"rotation": ["14 * q.modified_move_speed", 0, 0]},
        })
        put("attack", {
            "arm_r": {"rotation": ["-150 * math.sin(v.attack_time * 180) + 40 * math.sin(v.attack_time * 360)", 0, 0]},
            "fore_r": {"rotation": ["-25 * math.sin(v.attack_time * 180)", 0, 0]},
            "chest": {"rotation": ["12 * math.sin(v.attack_time * 180)", "-20 * math.sin(v.attack_time * 180)", 0]},
        })
        put("cast", {   # channel: both arms raised forward-up, trembling
            "arm_r": {"rotation": ["-150 + math.sin(q.life_time * 900) * 4", 0, 25]},
            "arm_l": {"rotation": ["-150 - math.sin(q.life_time * 900) * 4", 0, -25]},
            "fore_r": {"rotation": [-10, 0, 0]}, "fore_l": {"rotation": [-10, 0, 0]},
            "head": {"rotation": [-15, 0, 0]}, "chest": {"rotation": [-8, 0, 0]},
        })
        put("slam", {   # raise overhead, then smash down every 1.6 s
            "arm_r": {"rotation": ["-170 + math.clamp(math.mod(q.anim_time, 1.6) - 1.1, 0, 0.3) * 520", 0, 10]},
            "arm_l": {"rotation": ["-170 + math.clamp(math.mod(q.anim_time, 1.6) - 1.1, 0, 0.3) * 520", 0, -10]},
            "chest": {"rotation": ["-14 + math.clamp(math.mod(q.anim_time, 1.6) - 1.1, 0, 0.3) * 120", 0, 0]},
        })
        put("beam", {   # weapon / arm pointed straight along the gaze
            "arm_r": {"rotation": [-90, -8, 0]}, "fore_r": {"rotation": [0, 0, 0]},
            "weapon": {"rotation": [-40, 0, 0]},
            "arm_l": {"rotation": [-30, 0, -20]},
            "head": {"rotation": [5, 0, 0]}, "chest": {"rotation": [6, -10, 0]},
        })
        put("roar", {
            "head": {"rotation": [-30, 0, 0]}, "chest": {"rotation": [-12, 0, 0]},
            "arm_r": {"rotation": [-20, 0, "70 + math.sin(q.life_time * 1200) * 3"]},
            "arm_l": {"rotation": [-20, 0, "-70 - math.sin(q.life_time * 1200) * 3"]},
            "jaw": {"rotation": [25, 0, 0]},
        })
        put("sweep", {
            "chest": {"rotation": [8, "math.sin(q.anim_time * 260) * 40", 0]},
            "arm_r": {"rotation": [-85, 0, 30]}, "arm_l": {"rotation": [-60, 0, -40]},
        })
        put("charge", {
            "chest": {"rotation": [25, 0, 0]}, "head": {"rotation": [-20, 0, 0]},
            "arm_r": {"rotation": [-60, 0, 10]}, "arm_l": {"rotation": [40, 0, -10]},
            "leg_r": {"rotation": [-30, 0, 0]}, "leg_l": {"rotation": [25, 0, 0]},
        })
        put("leap", {
            "chest": {"rotation": [20, 0, 0]},
            "leg_r": {"rotation": [-50, 0, 0]}, "leg_l": {"rotation": [-50, 0, 0]},
            "shin_r": {"rotation": [70, 0, 0]}, "shin_l": {"rotation": [70, 0, 0]},
            "arm_r": {"rotation": [-160, 0, 20]}, "arm_l": {"rotation": [-160, 0, -20]},
            "root": {"position": [0, -3, 0]},
        })
        put("summon", {
            "arm_r": {"rotation": [-60, 0, "100 + math.sin(q.life_time * 500) * 6"]},
            "arm_l": {"rotation": [-60, 0, "-100 - math.sin(q.life_time * 500) * 6"]},
            "head": {"rotation": [-25, 0, 0]}, "chest": {"rotation": [-10, 0, 0]},
        })
    else:
        # quadrupeds / dragon / serpent
        seg = sorted([b for b in B if b.startswith("seg")], key=lambda x: int(x[3:]))
        tails = sorted([b for b in B if b.startswith("tail")])
        idle = {
            "body": {"position": [0, s % 80 + " * 0.4", 0]},
            "head": {"rotation": [s % 60 + " * 3", s % 30 + " * 6", 0]},
            "jaw": {"rotation": ["math.max(0, " + s % 50 + ") * 6", 0, 0]},
            "wing_r": {"rotation": [0, 0, s % 50 + " * 6"]}, "wing_l": {"rotation": [0, 0, "-" + s % 50 + " * 6"]},
        }
        for i, t in enumerate(tails):
            idle[t] = {"rotation": [0, "math.sin(q.life_time * 120 - %d) * 12" % (i * 40), 0]}
        for i, sg in enumerate(seg):
            idle[sg] = {"rotation": [0, "math.sin(q.life_time * 90 - %d) * 7" % (i * 45), 0]}
        put("idle", idle)
        w = "math.sin(q.life_time * 450) * 30 * q.modified_move_speed"
        walk = {
            "leg_fr": {"rotation": [w, 0, 0]}, "leg_bl": {"rotation": [w, 0, 0]},
            "leg_fl": {"rotation": ["-" + w, 0, 0]}, "leg_br": {"rotation": ["-" + w, 0, 0]},
            "body": {"position": [0, "math.abs(math.sin(q.life_time * 450)) * 1.2 * q.modified_move_speed", 0]},
        }
        for i, sg in enumerate(seg):
            walk[sg] = {"rotation": [0, "math.sin(q.life_time * 300 - %d) * 14 * q.modified_move_speed" % (i * 50), 0]}
        put("walk", walk)
        put("attack", {"head": {"rotation": ["30 * math.sin(v.attack_time * 180)", 0, 0]},
                       "jaw": {"rotation": ["35 * math.sin(v.attack_time * 180)", 0, 0]},
                       "body": {"rotation": ["-8 * math.sin(v.attack_time * 180)", 0, 0]}})
        put("cast", {"head": {"rotation": [-25, 0, 0]}, "jaw": {"rotation": ["20 + math.sin(q.life_time * 800) * 5", 0, 0]},
                     "body": {"rotation": [-6, 0, 0]}, "wing_r": {"rotation": [0, 0, 30]}, "wing_l": {"rotation": [0, 0, -30]}})
        put("slam", {"body": {"rotation": ["-18 + math.clamp(math.mod(q.anim_time, 1.6) - 1.1, 0, 0.3) * 140", 0, 0]},
                     "leg_fr": {"rotation": ["-50 + math.clamp(math.mod(q.anim_time, 1.6) - 1.1, 0, 0.3) * 160", 0, 0]},
                     "leg_fl": {"rotation": ["-50 + math.clamp(math.mod(q.anim_time, 1.6) - 1.1, 0, 0.3) * 160", 0, 0]}})
        put("beam", {"head": {"rotation": [10, 0, 0]}, "jaw": {"rotation": [35, 0, 0]}, "body": {"rotation": [6, 0, 0]}})
        put("roar", {"head": {"rotation": [-35, 0, 0]}, "jaw": {"rotation": [40, 0, 0]}, "body": {"rotation": [-10, 0, 0]},
                     "wing_r": {"rotation": [0, 0, 45]}, "wing_l": {"rotation": [0, 0, -45]}})
        put("sweep", {"body": {"rotation": [0, "math.sin(q.anim_time * 300) * 25", 0]},
                      "wing_r": {"rotation": [0, 0, "math.sin(q.anim_time * 600) * 40"]}, "wing_l": {"rotation": [0, 0, "-math.sin(q.anim_time * 600) * 40"]}})
        put("charge", {"body": {"rotation": [12, 0, 0]}, "head": {"rotation": [8, 0, 0]},
                       "leg_fr": {"rotation": [-40, 0, 0]}, "leg_fl": {"rotation": [-40, 0, 0]}, "leg_br": {"rotation": [35, 0, 0]}, "leg_bl": {"rotation": [35, 0, 0]}})
        put("leap", {"body": {"rotation": [-15, 0, 0], "position": [0, -2, 0]},
                     "leg_fr": {"rotation": [-60, 0, 0]}, "leg_fl": {"rotation": [-60, 0, 0]}, "leg_br": {"rotation": [40, 0, 0]}, "leg_bl": {"rotation": [40, 0, 0]}})
        put("summon", {"head": {"rotation": [-40, 0, 0]}, "jaw": {"rotation": [40, 0, 0]}})
    put("look", {"head": {"rotation": ["math.clamp(q.target_x_rotation, -30, 30)", "math.clamp(q.target_y_rotation, -45, 45)", 0]}})
    return A


POSES = ["cast", "slam", "beam", "roar", "sweep", "charge", "leap", "summon"]
# property nrpg:anim -> pose (see bosses.js ANIM): 1 cast, 2 slam, 3 beam, 4 roar, 5 sweep/cone, 6 charge, 7 leap, 8 summon


def controller():
    states = {"default": {
        "animations": ["idle", {"walk": "q.modified_move_speed > 0.05"}, {"attack": "v.attack_time > 0"}, "look"],
        "transitions": [{p: "v.anim == %d" % (i + 1)} for i, p in enumerate(POSES)],
        "blend_transition": 0.2}}
    for i, p in enumerate(POSES):
        states[p] = {"animations": ["idle", p],
                     "transitions": [{"default": "v.anim == 0"}] + [{q: "v.anim == %d" % (j + 1)} for j, q in enumerate(POSES) if q != p],
                     "blend_transition": 0.18}
    return {"format_version": "1.10.0", "animation_controllers": {"controller.animation.nrpg.boss": {"initial_state": "default", "states": states}}}


def render_controllers():
    return {"format_version": "1.8.0", "render_controllers": {
        "controller.render.nrpg.base": {
            "geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]},
        "controller.render.nrpg.glow": {
            "geometry": "Geometry.default", "materials": [{"*": "Material.glow"}], "textures": ["Texture.glow"],
            "ignore_lighting": True, "is_hurt_color": {}, "on_fire_color": {}},
        "controller.render.nrpg.illusion": {
            "arrays": {"geometries": {"Array.geo": ["Geometry.%s" % k for k in D.BOSSES]},
                       "textures": {"Array.tex": ["Texture.%s" % k for k in D.BOSSES]}},
            "geometry": "Array.geo[q.property('nrpg:skin')]", "materials": [{"*": "Material.default"}],
            "textures": ["Array.tex[q.property('nrpg:skin')]"], "ignore_lighting": True,
            "color": {"r": 0.75, "g": 0.6, "b": 1.0, "a": 0.55}},
    }}


SPAWN_EGG = {"arnarr": ("#5c6b5a", "#a8873e"), "hati": ("#9aa3ad", "#7fd6ff"), "andvari": ("#4b3a6b", "#ffd84a")}


def client_entity(key, ident, has_glow, anim_names, egg=None, scale=1.0):
    tex = {"default": "textures/nrpg/bosses/" + key}
    mats = {"default": "entity_alphatest"}
    rcs = ["controller.render.nrpg.base"]
    if has_glow:
        tex["glow"] = "textures/nrpg/bosses/%s_glow" % key
        mats["glow"] = "entity_alphablend"
        rcs.append("controller.render.nrpg.glow")
    anims = {n: "animation.nrpg.%s.%s" % (key, n) for n in anim_names}
    anims["ctrl"] = "controller.animation.nrpg.boss"
    desc = {"identifier": ident, "materials": mats, "textures": tex, "geometry": {"default": "geometry.nrpg." + key},
            "animations": anims,
            "scripts": {"pre_animation": ["v.anim = q.has_property('nrpg:anim') ? q.property('nrpg:anim') : 0;"],
                        "animate": ["ctrl"], "scale": str(scale)},
            "render_controllers": rcs}
    if egg:
        desc["spawn_egg"] = {"base_color": egg[0], "overlay_color": egg[1]}
    return {"format_version": "1.10.0", "minecraft:client_entity": {"description": desc}}


def models():
    out = {}
    for bid, b in D.BOSSES.items():
        out[bid] = (build_boss(bid, b), b["model"])
    for k, fn in EXTRA.items():
        out[k] = (fn(), "beast" if k != "dummy" else "humanoid")
    return out


def write(rp, bp=None, preview_dir=None):
    tex_dir = os.path.join(rp, "textures", "nrpg", "bosses")
    os.makedirs(tex_dir, exist_ok=True)
    allm = models()
    geo_all, anim_all = [], {}
    info = {}
    for key, (m, arch) in allm.items():
        m.pack()
        base, glow = m.paint()
        base.save(os.path.join(tex_dir, key + ".png"))
        has_glow = glow.getextrema()[3][1] > 0
        if has_glow:
            glow.save(os.path.join(tex_dir, key + "_glow.png"))
        geo_all.append(m.geometry_json()["minecraft:geometry"][0])
        A = anims(key, m, arch) if key != "dummy" else {}
        anim_all.update(A)
        names = sorted(set(n.split(".")[-1] for n in A))
        ident = "nrpg:" + key
        b = D.BOSSES.get(key)
        egg = None
        if b:
            pal = b["palette"]
            c1 = next(iter(pal.values()))
            egg = (c1, pal.get("glow", "#ffffff"))
        ce = client_entity(key, ident, has_glow, names, egg)
        if key == "dummy":
            ce["minecraft:client_entity"]["description"]["animations"] = {}
            ce["minecraft:client_entity"]["description"]["scripts"] = {}
        path = os.path.join(rp, "entity", "nrpg_%s.entity.json" % key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(ce, open(path, "w", encoding="utf8"), indent=1)
        info[key] = dict(tex=(m.tex_w, m.tex_h), bones=len(m.bones), cubes=sum(len(b.cubes) for b in m.bones), glow=has_glow)
        if preview_dir:
            os.makedirs(preview_dir, exist_ok=True)
            render(m, base, glow, os.path.join(preview_dir, key + ".png"), size=(360, 360))
    # illusion: every boss geometry/texture, picked by property
    il = {"format_version": "1.10.0", "minecraft:client_entity": {"description": {
        "identifier": "nrpg:illusion", "materials": {"default": "entity_alphablend"},
        "textures": {k: "textures/nrpg/bosses/" + k for k in D.BOSSES},
        "geometry": {k: "geometry.nrpg." + k for k in D.BOSSES},
        "render_controllers": ["controller.render.nrpg.illusion"]}}}
    json.dump(il, open(os.path.join(rp, "entity", "nrpg_illusion.entity.json"), "w"), indent=1)
    os.makedirs(os.path.join(rp, "models", "entity"), exist_ok=True)
    json.dump({"format_version": "1.12.0", "minecraft:geometry": geo_all},
              open(os.path.join(rp, "models", "entity", "nrpg_bosses.geo.json"), "w"), separators=(",", ":"))
    os.makedirs(os.path.join(rp, "animations"), exist_ok=True)
    json.dump({"format_version": "1.8.0", "animations": anim_all},
              open(os.path.join(rp, "animations", "nrpg_bosses.animation.json"), "w"), separators=(",", ":"))
    os.makedirs(os.path.join(rp, "animation_controllers"), exist_ok=True)
    json.dump(controller(), open(os.path.join(rp, "animation_controllers", "nrpg_boss.animation_controllers.json"), "w"), indent=1)
    os.makedirs(os.path.join(rp, "render_controllers"), exist_ok=True)
    json.dump(render_controllers(), open(os.path.join(rp, "render_controllers", "nrpg_bosses.render_controllers.json"), "w"), indent=1)
    return info


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    info = write(os.path.join(out, "rp"), None, os.path.join(out, "preview"))
    for k, v in info.items():
        print(k, v)
