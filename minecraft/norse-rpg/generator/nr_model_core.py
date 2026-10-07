"""Bedrock entity model toolkit: bones + cubes -> geometry JSON, packed per-face UV atlas, procedural
pixel-art painting (base + glow layer), and an offline software renderer for previews.

Coordinates are Bedrock model units (1/16 block): feet at y=0, +Y up, the model faces -Z,
the character's right side is -X (as in vanilla 'rightarm').
Rotations follow Bedrock: x<0 raises a hanging limb forwards, x>0 bows a torso forwards,
z>0 swings a right (-X) arm outwards.
"""
import colorsys
import json
import math

import numpy as np
from PIL import Image, ImageDraw

FACES = ("north", "south", "east", "west", "up", "down")


# ---------------------------------------------------------------- colours
def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(base, n=7, spread=0.55, hue_shift=0.035):
    """Pixel-art colour ramp dark -> light with hue shifting (shadows cooler, lights warmer)."""
    if isinstance(base, str):
        base = hexrgb(base)
    r, g, b = [c / 255 for c in base]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    for i in range(n):
        t = (i / (n - 1)) * 2 - 1           # -1 .. 1
        ll = min(0.97, max(0.03, l + t * spread * (0.5 if t > 0 else 0.62) * (1.0 if l < 0.7 else 0.6)))
        hh = (h + t * hue_shift) % 1.0
        ss = min(1, max(0, s * (1 - 0.25 * abs(t)) + (0.08 if t < 0 else -0.04)))
        rr, gg, bb = colorsys.hls_to_rgb(hh, ll, ss)
        out.append((int(rr * 255), int(gg * 255), int(bb * 255)))
    return np.array(out, float)


# ---------------------------------------------------------------- model structure
class Cube:
    def __init__(self, origin, size, mat, inflate=0.0, rotation=None, pivot=None, glow=False, mirror=False, faces=None, seed=0):
        self.origin = [float(v) for v in origin]
        self.size = [float(v) for v in size]
        self.mat = mat
        self.inflate = inflate
        self.rotation = rotation
        self.pivot = pivot
        self.glow = glow
        self.mirror = mirror
        self.faces = faces          # optional {face: mat} overrides, or face -> None to skip painting detail
        self.seed = seed
        self.uv = {}


class Bone:
    def __init__(self, name, parent=None, pivot=(0, 0, 0), rotation=(0, 0, 0)):
        self.name = name
        self.parent = parent
        self.pivot = [float(v) for v in pivot]
        self.rotation = [float(v) for v in rotation]
        self.cubes = []


class Model:
    def __init__(self, ident, visible=(4, 4)):
        self.ident = ident
        self.bones = []
        self.by = {}
        self.visible = visible
        self.tex_w = self.tex_h = 0
        self._seed = 1

    def bone(self, name, parent=None, pivot=(0, 0, 0), rotation=(0, 0, 0)):
        b = Bone(name, parent, pivot, rotation)
        self.bones.append(b)
        self.by[name] = b
        return b

    def box(self, bone, origin, size, mat, **kw):
        self._seed += 1
        kw.setdefault("seed", self._seed * 7919)
        c = Cube(origin, size, mat, **kw)
        (self.by[bone] if isinstance(bone, str) else bone).cubes.append(c)
        return c

    def has(self, name):
        return name in self.by

    # ------------------------------------------------------------ UV atlas
    def face_dims(self, c):
        w, h, d = c.size
        dims = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}
        return {f: (max(1, int(math.ceil(a - 1e-6))), max(1, int(math.ceil(b - 1e-6)))) for f, (a, b) in dims.items()}

    def pack(self, width=None):
        rects = []
        for b in self.bones:
            for c in b.cubes:
                for f, (w, h) in self.face_dims(c).items():
                    rects.append((h, w, c, f))
        rects.sort(key=lambda r: (-r[0], -r[1]))
        area = sum(r[0] * r[1] for r in rects)
        W = width or 64
        while W * W < area * 1.25:
            W *= 2
        W = max(W, max(r[1] for r in rects))
        while True:
            ok, H = self._shelf(rects, W)
            if ok:
                break
            W *= 2
        Hp = 16
        while Hp < H:
            Hp *= 2
        self.tex_w, self.tex_h = W, Hp
        return W, Hp

    def _shelf(self, rects, W):
        x = y = shelf_h = 0
        place = []
        for h, w, c, f in rects:
            if x + w > W:
                y += shelf_h
                x = 0
                shelf_h = 0
            place.append((x, y, w, h, c, f))
            x += w
            shelf_h = max(shelf_h, h)
        H = y + shelf_h
        if H > W * 4:
            return False, H
        for x, y, w, h, c, f in place:
            c.uv[f] = (x, y, w, h)
        return True, H

    # ------------------------------------------------------------ export
    def geometry_json(self):
        bones = []
        for b in self.bones:
            jb = {"name": b.name, "pivot": [round(v, 4) for v in b.pivot]}
            if b.parent:
                jb["parent"] = b.parent
            if any(b.rotation):
                jb["rotation"] = [round(v, 3) for v in b.rotation]
            cubes = []
            for c in b.cubes:
                jc = {"origin": [round(v, 4) for v in c.origin], "size": [round(v, 4) for v in c.size]}
                if c.inflate:
                    jc["inflate"] = c.inflate
                if c.rotation:
                    jc["rotation"] = [round(v, 3) for v in c.rotation]
                    jc["pivot"] = [round(v, 4) for v in (c.pivot or c.origin)]
                uv = {}
                for f in FACES:
                    x, y, w, h = c.uv[f]
                    uv[f] = {"uv": [x, y], "uv_size": [w, h]}
                jc["uv"] = uv
                cubes.append(jc)
            if cubes:
                jb["cubes"] = cubes
            bones.append(jb)
        vw, vh = self.visible
        return {"format_version": "1.12.0", "minecraft:geometry": [{
            "description": {"identifier": self.ident, "texture_width": self.tex_w, "texture_height": self.tex_h,
                            "visible_bounds_width": vw, "visible_bounds_height": vh, "visible_bounds_offset": [0, vh / 2, 0]},
            "bones": bones}]}

    def paint(self):
        base = np.zeros((self.tex_h, self.tex_w, 4), np.uint8)
        glow = np.zeros((self.tex_h, self.tex_w, 4), np.uint8)
        for b in self.bones:
            for c in b.cubes:
                for f in FACES:
                    x, y, w, h = c.uv[f]
                    mat = (c.faces or {}).get(f, c.mat)
                    rgba, grgba = paint_face(mat, f, w, h, c, np.random.default_rng(c.seed + FACES.index(f) * 101))
                    base[y:y + h, x:x + w] = rgba
                    if grgba is not None:
                        glow[y:y + h, x:x + w] = grgba
        return Image.fromarray(base, "RGBA"), Image.fromarray(glow, "RGBA")


# ---------------------------------------------------------------- painting
def _shade_idx(h, w, face, top=4.4, bottom=2.6):
    """Base ramp index per pixel: lighter at the top of side faces."""
    if face in ("up",):
        return np.full((h, w), top + 0.4)
    if face == "down":
        return np.full((h, w), bottom - 0.6)
    t = np.linspace(0, 1, h)[:, None] if h > 1 else np.zeros((1, 1))
    return np.repeat(top + (bottom - top) * t, w, axis=1)


def _edge_dark(idx, amount=0.7, sides=True):
    h, w = idx.shape
    if h > 2:
        idx[-1, :] -= amount
    if sides and w > 2:
        idx[:, 0] -= amount * 0.45
        idx[:, -1] -= amount * 0.45
    return idx


def _lookup(r, idx):
    i = np.clip(np.round(idx).astype(int), 0, len(r) - 1)
    return r[i]


def _to_rgba(rgb, alpha=None):
    h, w = rgb.shape[:2]
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = 255 if alpha is None else alpha
    return out


def paint_face(mat, face, w, h, cube, rng):
    """mat: dict(kind=..., c=base, c2=..., trim=..., glow=colour, ...). Returns (rgba, glow_rgba or None)."""
    k = mat.get("kind", "skin")
    fn = PAINTERS.get(k, p_skin)
    rgb, alpha, glow = fn(mat, face, w, h, cube, rng)
    g = None
    if glow is not None:
        g = glow
    return _to_rgba(rgb, alpha), g


def p_skin(m, face, w, h, cube, rng):
    r = ramp(m["c"])
    idx = _shade_idx(h, w, face) + rng.normal(0, 0.22, (h, w))
    idx = _edge_dark(idx, 0.8)
    return _lookup(r, idx), None, None


def p_cloth(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.5)
    idx = _shade_idx(h, w, face, 4.2, 2.4)
    if face not in ("up", "down"):
        xs = np.arange(w)
        period = m.get("fold", 4)
        fold = (np.sin((xs + rng.integers(0, 4)) * 2 * math.pi / period) * 0.7)[None, :]
        idx = idx + fold + rng.normal(0, 0.25, (h, w))
        if h > 4:
            idx[-2:, :] -= 0.9
    else:
        idx = idx + rng.normal(0, 0.3, (h, w))
    idx = _edge_dark(idx, 0.6)
    rgb = _lookup(r, idx)
    if m.get("trim") and face not in ("up", "down") and h > 4:
        tr = ramp(m["trim"])
        rgb[-2, :] = tr[4]
        rgb[-1, :] = tr[2]
        if m.get("trim_top"):
            rgb[0, :] = tr[4]
    if m.get("pattern") == "stripes" and face not in ("up", "down"):
        sr = ramp(m.get("c2", m["c"]))
        for yy in range(1, h, 4):
            rgb[yy, :] = sr[3]
    return rgb, None, None


def p_metal(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.75, hue_shift=0.02)
    idx = _shade_idx(h, w, face, 4.6, 2.3) + rng.normal(0, 0.16, (h, w))
    seam = m.get("seam", 5)
    if face not in ("up", "down") and h >= seam + 2:
        for yy in range(seam, h - 1, seam):
            idx[yy, :] -= 1.6
            if yy + 1 < h:
                idx[yy + 1, :] += 0.9
    # highlight streak
    if w > 3 and face not in ("down",):
        sx = int(rng.integers(1, max(2, w - 1)))
        idx[: max(1, h // 2), sx] += 1.2
    idx = _edge_dark(idx, 1.0)
    rgb = _lookup(r, idx)
    if m.get("rivets") and w >= 4 and h >= 4 and face not in ("up", "down"):
        hi = r[6]
        for (yy, xx) in ((1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2)):
            rgb[yy, xx] = hi
    if m.get("trim") and face not in ("up", "down") and h > 3:
        tr = ramp(m["trim"])
        rgb[0, :] = tr[5]
        rgb[-1, :] = tr[2]
    return rgb, None, None


def p_chain(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.7)
    yy, xx = np.mgrid[0:h, 0:w]
    pat = ((xx + (yy // 2) % 2) % 2 == 0).astype(float) * 1.4 - 0.7
    idx = _shade_idx(h, w, face, 4.2, 2.6) + pat + rng.normal(0, 0.2, (h, w))
    idx = _edge_dark(idx, 0.8)
    return _lookup(r, idx), None, None


def p_leather(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.5)
    idx = _shade_idx(h, w, face, 4.0, 2.5) + rng.normal(0, 0.4, (h, w))
    idx = _edge_dark(idx, 0.7)
    rgb = _lookup(r, idx)
    if face not in ("up", "down") and w > 4 and h > 3:
        for xx in range(1, w - 1, 2):
            rgb[1, xx] = r[5]
    return rgb, None, None


def p_fur(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.6)
    idx = _shade_idx(h, w, face, 4.3, 2.4)
    streak = rng.normal(0, 0.9, (1, w)).repeat(h, axis=0)
    idx = idx + streak * 0.8 + rng.normal(0, 0.35, (h, w))
    if face == "down" and m.get("c2"):
        r = ramp(m["c2"], spread=0.5)
        idx = np.full((h, w), 3.2) + rng.normal(0, 0.4, (h, w))
    idx = _edge_dark(idx, 0.6)
    rgb = _lookup(r, idx)
    alpha = None
    if m.get("shaggy") and face not in ("up", "down") and h > 3:
        alpha = np.full((h, w), 255, np.uint8)
        cut = rng.integers(0, 3, w)
        for xx in range(w):
            for k in range(cut[xx]):
                alpha[h - 1 - k, xx] = 0
    glow = None
    if m.get("runes") and face in ("east", "west", "up") and w >= 6 and h >= 4:
        glow = np.zeros((h, w, 4), np.uint8)
        gc = hexrgb(m["runes"])
        _rune_marks(glow, gc, rng, density=0.6)
        mask = glow[..., 3] > 0
        rgb[mask] = np.array(gc) * 0.8
    return rgb, alpha, glow


def p_stone(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.55, hue_shift=0.01)
    yy, xx = np.mgrid[0:h, 0:w]
    blot = np.sin(xx * 0.9 + rng.uniform(0, 6)) * np.cos(yy * 0.7 + rng.uniform(0, 6))
    idx = _shade_idx(h, w, face, 4.2, 2.5) + blot * 0.6 + rng.normal(0, 0.45, (h, w))
    idx = _edge_dark(idx, 0.9)
    rgb = _lookup(r, idx)
    # cracks
    for _ in range(max(1, (w * h) // 60)):
        x0, y0 = int(rng.integers(0, w)), int(rng.integers(0, h))
        for _s in range(int(rng.integers(2, 6))):
            if 0 <= x0 < w and 0 <= y0 < h:
                rgb[y0, x0] = r[0]
            x0 += int(rng.integers(-1, 2))
            y0 += 1
    glow = None
    if m.get("moss"):
        mr = ramp(m["moss"])
        if face == "up":
            mask = rng.random((h, w)) < 0.75
            rgb[mask] = mr[np.clip(rng.integers(2, 6, mask.sum()), 0, 6)]
        elif face != "down" and h > 3:
            depth = rng.integers(0, 3, w)
            for x0 in range(w):
                for k in range(depth[x0]):
                    rgb[k, x0] = mr[3 + (k == 0)]
    if m.get("cracks_glow"):
        glow = np.zeros((h, w, 4), np.uint8)
        gc = hexrgb(m["cracks_glow"])
        _crack_glow(glow, rgb, gc, rng, n=max(1, (w * h) // 40))
    return rgb, None, glow


def p_scales(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.6)
    if face == "down" and m.get("c2"):
        r2 = ramp(m["c2"], spread=0.45)
        yy, xx = np.mgrid[0:h, 0:w]
        idx = np.full((h, w), 3.4) - ((yy % 3) == 2) * 1.2 + rng.normal(0, 0.25, (h, w))
        return _lookup(r2, idx), None, None
    yy, xx = np.mgrid[0:h, 0:w]
    cw, ch = 4, 3
    row = yy // ch
    lx = (xx + (row % 2) * 2) % cw
    ly = yy % ch
    arc = ((ly == ch - 1) | ((lx == 0) & (ly > 0))).astype(float)
    idx = _shade_idx(h, w, face, 4.4, 2.6) - arc * 1.5 + (ly == 0) * 0.6 + rng.normal(0, 0.25, (h, w))
    idx = _edge_dark(idx, 0.6)
    return _lookup(r, idx), None, None


def p_bone(m, face, w, h, cube, rng):
    r = ramp(m.get("c", "#d8cfb8"), spread=0.45)
    idx = _shade_idx(h, w, face, 4.6, 3.0) + rng.normal(0, 0.3, (h, w))
    idx = _edge_dark(idx, 1.0)
    rgb = _lookup(r, idx)
    for _ in range(max(1, (w * h) // 50)):
        x0, y0 = int(rng.integers(0, w)), int(rng.integers(0, h))
        rgb[y0, x0] = r[1]
    return rgb, None, None


def p_wood(m, face, w, h, cube, rng):
    r = ramp(m.get("c", "#6b4a2b"), spread=0.5)
    yy, xx = np.mgrid[0:h, 0:w]
    long_axis_x = w > h
    grain = np.sin((yy if long_axis_x else xx) * 1.7 + rng.uniform(0, 6)) * 0.8
    idx = _shade_idx(h, w, face, 4.0, 2.6) + grain + rng.normal(0, 0.25, (h, w))
    idx = _edge_dark(idx, 0.8)
    return _lookup(r, idx), None, None


def p_gold(m, face, w, h, cube, rng):
    r = ramp(m.get("c", "#d9a92c"), spread=0.8, hue_shift=0.05)
    idx = _shade_idx(h, w, face, 4.7, 2.5) + rng.normal(0, 0.3, (h, w))
    idx = _edge_dark(idx, 1.1)
    rgb = _lookup(r, idx)
    sp = rng.random((h, w)) < 0.06
    rgb[sp] = r[6]
    return rgb, None, None


def p_glow(m, face, w, h, cube, rng):
    gc = np.array(hexrgb(m.get("g", m.get("c"))), float)
    t = np.linspace(1.0, 0.75, h)[:, None].repeat(w, axis=1) if face not in ("up", "down") else np.ones((h, w))
    rgb = gc[None, None, :] * (0.85 + 0.15 * t[..., None]) + rng.normal(0, 6, (h, w, 1))
    glow = np.zeros((h, w, 4), np.uint8)
    glow[..., :3] = np.clip(rgb * 1.05 + 25, 0, 255)
    glow[..., 3] = int(m.get("ga", 230))
    return rgb, None, glow


def p_flame(m, face, w, h, cube, rng):
    core = np.array(hexrgb(m.get("core", "#fff2a8")), float)
    mid = np.array(hexrgb(m.get("c", "#ff8a1f")), float)
    tip = np.array(hexrgb(m.get("c2", "#d63a12")), float)
    t = np.linspace(1, 0, h)[:, None].repeat(w, axis=1) if face not in ("up", "down") else np.full((h, w), 0.5 if face == "up" else 1.0)
    t = np.clip(t + rng.normal(0, 0.12, (h, w)) + np.sin(np.arange(w) * 1.3 + rng.uniform(0, 6))[None, :] * 0.08, 0, 1)
    rgb = np.where(t[..., None] > 0.6, mid + (core - mid) * ((t[..., None] - 0.6) / 0.4), tip + (mid - tip) * (t[..., None] / 0.6))
    glow = np.zeros((h, w, 4), np.uint8)
    glow[..., :3] = np.clip(rgb + 20, 0, 255)
    glow[..., 3] = np.clip(150 + t * 100, 0, 255).astype(np.uint8)
    return rgb, None, glow


def p_hair(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.55)
    streak = rng.normal(0, 1.0, (1, w)).repeat(h, axis=0)
    idx = _shade_idx(h, w, face, 4.4, 2.6) + streak * 0.7 + rng.normal(0, 0.2, (h, w))
    if face not in ("up", "down") and h > 4:
        band = h // 4
        idx[band:band + 1, :] += 1.2
    return _lookup(r, idx), None, None


def p_membrane(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.45)
    yy, xx = np.mgrid[0:h, 0:w]
    vein = ((xx * 3 + yy) % 9 == 0) | ((xx * 2 - yy) % 11 == 0)
    idx = np.full((h, w), 2.8) + rng.normal(0, 0.25, (h, w)) - vein * 1.4
    return _lookup(r, idx), None, None


def p_feather(m, face, w, h, cube, rng):
    r = ramp(m["c"], spread=0.6)
    r2 = ramp(m.get("c2", m["c"]), spread=0.5)
    yy, xx = np.mgrid[0:h, 0:w]
    v = ((yy + np.abs((xx % 6) - 3)) % 4)
    idx = _shade_idx(h, w, face, 4.2, 2.4) + (v == 0) * -1.3 + rng.normal(0, 0.25, (h, w))
    rgb = _lookup(r, idx)
    if face not in ("up", "down") and h > 4:
        tips = yy >= h - 2
        rgb[tips] = _lookup(r2, idx)[tips]
    return rgb, None, None


def p_dark(m, face, w, h, cube, rng):
    r = ramp(m.get("c", "#14121a"), spread=0.3)
    idx = np.full((h, w), 3.0) + rng.normal(0, 0.3, (h, w))
    return _lookup(r, idx), None, None


def p_ice(m, face, w, h, cube, rng):
    r = ramp(m.get("c", "#a9dcf2"), spread=0.5)
    yy, xx = np.mgrid[0:h, 0:w]
    facet = ((xx + yy) % 5 == 0) * 1.4
    idx = _shade_idx(h, w, face, 4.8, 3.2) + facet + rng.normal(0, 0.2, (h, w))
    glow = np.zeros((h, w, 4), np.uint8)
    hi = (idx > 5.2)
    glow[hi, :3] = (220, 245, 255)
    glow[hi, 3] = 120
    return _lookup(r, idx), None, glow


def _rune_marks(glow, gc, rng, density=0.5):
    h, w = glow.shape[:2]
    x = 1
    while x < w - 2:
        if rng.random() < density:
            hgt = int(rng.integers(2, max(3, min(5, h - 1))))
            y0 = int(rng.integers(0, max(1, h - hgt)))
            for yy in range(y0, y0 + hgt):
                glow[yy, x, :3] = gc
                glow[yy, x, 3] = 235
            side = 1 if rng.random() < 0.5 else -1
            ty = y0 + int(rng.integers(0, hgt))
            if 0 <= x + side < w:
                glow[ty, x + side, :3] = gc
                glow[ty, x + side, 3] = 235
        x += int(rng.integers(2, 4))


def _crack_glow(glow, rgb, gc, rng, n=3):
    h, w = glow.shape[:2]
    for _ in range(n):
        x0, y0 = float(rng.integers(0, w)), float(rng.integers(0, h))
        ang = rng.uniform(0, 2 * math.pi)
        for _s in range(int(rng.integers(3, 9))):
            xi, yi = int(x0), int(y0)
            if 0 <= xi < w and 0 <= yi < h:
                glow[yi, xi, :3] = gc
                glow[yi, xi, 3] = 240
                rgb[yi, xi] = np.array(gc) * 0.9
            ang += rng.uniform(-0.8, 0.8)
            x0 += math.cos(ang)
            y0 += math.sin(ang)


def p_face(m, face, w, h, cube, rng):
    """Head cube: skin everywhere, a face on the north side."""
    rgb, _, _ = p_skin(m, face, w, h, cube, rng)
    glow = None
    if face != "north":
        if face == "up" and m.get("hair"):
            hr = ramp(m["hair"])
            rgb[:, :] = _lookup(hr, np.full((h, w), 3.4) + rng.normal(0, 0.5, (h, w)))
        elif face in ("south", "east", "west") and m.get("hair"):
            hr = ramp(m["hair"])
            cut = h if face == "south" else max(2, h * 2 // 3)
            band = _lookup(hr, _shade_idx(cut, w, face, 4.0, 2.6) + rng.normal(0, 0.5, (cut, w)))
            rgb[:cut, :] = band
        return rgb, None, None
    r = ramp(m["c"])
    eh = 2 if h >= 10 else 1
    ey = max(1, int(round(h * 0.40)))
    ew = max(1, int(round(w / 5.0)))
    lx = max(1, int(round(w * 0.2)))
    rx = w - lx - ew
    # cheek shading and brow shadow
    rgb[:, 0] = r[2]
    rgb[:, -1] = r[2]
    rgb[ey - 1, max(0, lx - 1):lx + ew + 1] = r[1]
    rgb[ey - 1, rx - 1:min(w, rx + ew + 1)] = r[1]
    eye_col = np.array(hexrgb(m.get("eye", "#f2f2f2")), float)
    for k in range(eh):
        rgb[ey + k, lx:lx + ew] = eye_col
        rgb[ey + k, rx:rx + ew] = eye_col
    if m.get("eye_glow"):
        glow = np.zeros((h, w, 4), np.uint8)
        gc = hexrgb(m["eye_glow"])
        for k in range(eh):
            for xx in list(range(lx, lx + ew)) + list(range(rx, rx + ew)):
                glow[ey + k, xx, :3] = gc
                glow[ey + k, xx, 3] = 255
        if m.get("eyes4") and ey > 2:
            for xx in (lx + ew // 2, rx + ew // 2):
                glow[ey - 2, xx, :3] = gc
                glow[ey - 2, xx, 3] = 255
    else:
        pupil = np.array(hexrgb(m.get("pupil", "#1a1a22")), float)
        for k in range(eh):
            rgb[ey + k, lx + ew - 1] = pupil
            rgb[ey + k, rx] = pupil
    ey = ey + eh - 1
    # nose
    nx = w // 2
    if h > 6:
        rgb[ey + 1:ey + 3, nx - (1 if w % 2 == 0 else 0):nx + 1] = r[5]
        rgb[ey + 3, nx - 1:nx + 1] = r[1]
    # mouth
    my = min(h - 2, ey + 4)
    if my > ey + 2:
        rgb[my, w // 2 - max(1, w // 6):w // 2 + max(1, w // 6)] = np.array(hexrgb(m.get("mouth", "#3a1f1f")), float)
    if m.get("half"):
        # Hel: right half (viewer's left on the north face = +X side) is the dead half
        dr = ramp(m["half"])
        dead = _lookup(dr, _shade_idx(h, w // 2, face, 3.6, 2.2) + rng.normal(0, 0.4, (h, w // 2)))
        rgb[:, : w // 2] = dead
        rgb[ey, lx:lx + ew] = eye_col
    if m.get("decay"):
        dr = ramp(m["decay"])
        mask = rng.random((h, w)) < 0.12
        rgb[mask] = dr[2]
    return rgb, None, glow


PAINTERS = {
    "skin": p_skin, "cloth": p_cloth, "metal": p_metal, "chain": p_chain, "leather": p_leather, "fur": p_fur,
    "stone": p_stone, "scales": p_scales, "bone": p_bone, "wood": p_wood, "gold": p_gold, "glow": p_glow,
    "flame": p_flame, "hair": p_hair, "membrane": p_membrane, "feather": p_feather, "dark": p_dark, "ice": p_ice,
    "face": p_face,
}


# ---------------------------------------------------------------- preview renderer
def _rot(deg):
    """Bedrock rotation (x, y, z degrees) -> 3x3 matrix. Bedrock angles act as right-handed rotations by -angle,
    applied z first, then y, then x."""
    x, y, z = [-math.radians(v) for v in deg]
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rx @ Ry @ Rz


def world_transforms(model, pose=None):
    """Bone -> (R, t): world = R @ local + t (local = model space at rest)."""
    pose = pose or {}
    T = {}
    for b in model.bones:
        rot = np.array(b.rotation) + np.array(pose.get(b.name, {}).get("rot", (0, 0, 0)))
        off = np.array(pose.get(b.name, {}).get("pos", (0, 0, 0)), float)
        p = np.array(b.pivot)
        R = _rot(rot)
        # rotate around own pivot (in parent space), then apply parent's transform
        Rl, tl = R, p - R @ p + off
        if b.parent and b.parent in T:
            PR, Pt = T[b.parent]
            T[b.name] = (PR @ Rl, PR @ tl + Pt)
        else:
            T[b.name] = (Rl, tl)
    return T


SHADE = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.62, "west": 0.62}


def render(model, base, glow, path=None, size=(512, 512), views=((-35, 22), (145, 22)), pose=None, bg=(26, 28, 36)):
    """Orthographic 3/4 views. Returns a PIL image with the views side by side."""
    B = np.asarray(base.convert("RGBA"), float)
    G = np.asarray(glow.convert("RGBA"), float)
    T = world_transforms(model, pose)
    quads = []
    for b in model.bones:
        R, t = T[b.name]
        for c in b.cubes:
            x0, y0, z0 = [v - c.inflate for v in c.origin]
            sx, sy, sz = [v + 2 * c.inflate for v in c.size]
            corners = {}
            for ix in (0, 1):
                for iy in (0, 1):
                    for iz in (0, 1):
                        p = np.array([x0 + ix * sx, y0 + iy * sy, z0 + iz * sz])
                        if c.rotation:
                            cp = np.array(c.pivot or c.origin)
                            p = _rot(c.rotation) @ (p - cp) + cp
                        corners[(ix, iy, iz)] = R @ p + t
            # face: (corner at uv(0,0), corner at u+, corner at v+), outward normal
            F = {
                "north": ((1, 1, 0), (0, 1, 0), (1, 0, 0)),
                "south": ((0, 1, 1), (1, 1, 1), (0, 0, 1)),
                "east": ((1, 1, 1), (1, 1, 0), (1, 0, 1)),
                "west": ((0, 1, 0), (0, 1, 1), (0, 0, 0)),
                "up": ((0, 1, 0), (1, 1, 0), (0, 1, 1)),
                "down": ((0, 0, 1), (1, 0, 1), (0, 0, 0)),
            }
            for f, (o, u, v) in F.items():
                quads.append((corners[o], corners[u], corners[v], c.uv[f], SHADE[f]))
    W, H = size
    out = Image.new("RGB", (W * len(views), H), bg)
    allp = np.array([q[0] for q in quads] + [q[1] for q in quads] + [q[2] for q in quads])
    for vi, (yaw, pitch) in enumerate(views):
        ya, pa = math.radians(yaw), math.radians(pitch)
        # camera looks at the model from direction (yaw around Y from -Z, pitch down)
        Ry = np.array([[math.cos(ya), 0, -math.sin(ya)], [0, 1, 0], [math.sin(ya), 0, math.cos(ya)]])
        Rx = np.array([[1, 0, 0], [0, math.cos(pa), -math.sin(pa)], [0, math.sin(pa), math.cos(pa)]])
        V = Rx @ Ry
        pts = allp @ V.T
        span = max(pts[:, 0].max() - pts[:, 0].min(), pts[:, 1].max() - pts[:, 1].min()) * 1.12 + 1e-6
        sc = min(W, H) / span
        cx = (pts[:, 0].max() + pts[:, 0].min()) / 2
        cy = (pts[:, 1].max() + pts[:, 1].min()) / 2
        img = np.zeros((H, W, 3), float)
        img[:] = bg
        zb = np.full((H, W), np.inf)
        for (o, u, v, uvr, shade) in quads:
            P = np.array([o, u, v]) @ V.T
            # camera looks along +z: world +x appears on the left of the picture
            S = np.stack([-(P[:, 0] - cx) * sc + W / 2, -(P[:, 1] - cy) * sc + H / 2, P[:, 2]], axis=1)
            e1, e2 = S[1] - S[0], S[2] - S[0]
            det = e1[0] * e2[1] - e1[1] * e2[0]
            if abs(det) < 1e-6:
                continue
            # back-face cull: cross(u, v) of the face corners points inwards; keep faces whose outward normal faces the camera
            n = np.cross(P[1] - P[0], P[2] - P[0])
            if n[2] <= 0:
                continue
            q = S[0] + e1 + e2
            xs = [S[0][0], S[1][0], S[2][0], q[0]]
            ys = [S[0][1], S[1][1], S[2][1], q[1]]
            x0, x1 = max(0, int(min(xs))), min(W - 1, int(max(xs)) + 1)
            y0, y1 = max(0, int(min(ys))), min(H - 1, int(max(ys)) + 1)
            if x1 < x0 or y1 < y0:
                continue
            gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            dx, dy = gx + 0.5 - S[0][0], gy + 0.5 - S[0][1]
            a = (dx * e2[1] - dy * e2[0]) / det
            bb = (e1[0] * dy - e1[1] * dx) / det
            m = (a >= 0) & (a <= 1) & (bb >= 0) & (bb <= 1)
            if not m.any():
                continue
            z = S[0][2] + a * e1[2] + bb * e2[2]
            ux, uy, uw, uh = uvr
            tx = np.clip((ux + a * uw).astype(int), ux, ux + uw - 1)
            ty = np.clip((uy + bb * uh).astype(int), uy, uy + uh - 1)
            col = B[ty, tx]
            gl = G[ty, tx]
            m &= col[..., 3] > 10
            m &= z < zb[gy, gx]
            if not m.any():
                continue
            rgb = col[..., :3] * shade
            ga = gl[..., 3:4] / 255.0
            rgb = rgb * (1 - ga) + gl[..., :3] * ga
            zb[gy[m], gx[m]] = z[m]
            img[gy[m], gx[m]] = rgb[m]
        out.paste(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), (vi * W, 0))
    if path:
        out.save(path)
    return out
