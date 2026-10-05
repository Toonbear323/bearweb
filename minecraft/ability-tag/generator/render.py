"""Preview renderer (top-down + isometric) used for design review and the world icon."""
import math

import numpy as np
from PIL import Image

from mcw import PAL

KEYWORDS = [
    ("barrier", None), ("light_block", None), ("structure_void", None), ("air", None),
    ("grass_block", (95, 159, 53)), ("short_grass", (110, 170, 60)), ("tall_grass", (110, 170, 60)),
    ("fern", (90, 150, 55)), ("moss", (89, 125, 48)), ("podzol", (106, 77, 40)),
    ("grass_path", (148, 122, 65)), ("coarse_dirt", (119, 85, 59)), ("dirt", (134, 96, 67)),
    ("mud", (60, 57, 60)), ("cherry_leaves", (229, 172, 194)), ("azalea_leaves", (90, 120, 50)),
    ("spruce_leaves", (52, 88, 52)), ("birch_leaves", (110, 150, 70)), ("dark_oak_leaves", (50, 100, 30)),
    ("jungle_leaves", (60, 150, 40)), ("leaves", (70, 125, 40)), ("pale_oak", (220, 215, 210)),
    ("birch_log", (216, 215, 210)), ("cherry_log", (60, 34, 44)), ("spruce_log", (58, 37, 16)),
    ("dark_oak_log", (60, 46, 26)), ("jungle_log", (85, 67, 25)), ("log", (109, 85, 50)), ("_wood", (100, 78, 46)),
    ("stem", (90, 50, 60)), ("cherry_planks", (226, 178, 172)), ("spruce", (114, 84, 48)),
    ("dark_oak", (66, 43, 20)), ("birch", (192, 175, 121)), ("jungle", (160, 115, 80)),
    ("acacia", (168, 90, 50)), ("mangrove", (117, 54, 48)), ("bamboo", (190, 170, 80)), ("crimson", (101, 48, 70)),
    ("warped", (43, 104, 99)), ("oak", (162, 130, 78)), ("planks", (162, 130, 78)),
    ("water", (40, 110, 210)), ("lava", (230, 100, 20)), ("magma", (180, 70, 20)),
    ("deepslate", (70, 70, 75)), ("blackstone", (42, 36, 41)), ("basalt", (80, 80, 85)),
    ("tuff", (108, 109, 102)), ("calcite", (223, 224, 220)), ("andesite", (136, 136, 137)),
    ("diorite", (188, 188, 188)), ("granite", (149, 103, 85)), ("mossy", (100, 120, 90)),
    ("cobble", (122, 122, 122)), ("stone_brick", (122, 121, 122)), ("smooth_stone", (160, 160, 160)),
    ("stone", (125, 125, 125)), ("gravel", (131, 127, 126)), ("red_sand", (190, 102, 33)),
    ("sandstone", (216, 203, 155)), ("sand", (219, 207, 163)), ("clay", (160, 166, 179)),
    ("netherrack", (97, 38, 38)), ("nether_brick", (44, 21, 26)), ("obsidian", (20, 18, 30)),
    ("gold", (246, 208, 61)), ("iron", (220, 220, 220)), ("copper", (192, 107, 79)),
    ("amethyst", (133, 97, 191)), ("purpur", (169, 125, 169)), ("quartz", (235, 229, 222)),
    ("prismarine", (99, 156, 151)), ("sea_lantern", (172, 199, 190)), ("glowstone", (171, 131, 84)),
    ("shroomlight", (240, 146, 70)), ("froglight", (240, 220, 170)), ("lantern", (250, 200, 90)),
    ("torch", (250, 200, 90)), ("campfire", (220, 120, 40)), ("glass", (200, 220, 230)),
    ("bars", (150, 150, 150)), ("chain", (60, 60, 70)),
    ("white", (233, 236, 236)), ("orange", (240, 118, 19)), ("magenta", (189, 68, 179)),
    ("light_blue", (58, 175, 217)), ("yellow", (248, 197, 39)), ("lime", (112, 185, 25)),
    ("pink", (237, 141, 172)), ("light_gray", (142, 142, 134)), ("gray", (62, 68, 71)),
    ("cyan", (21, 137, 145)), ("purple", (121, 42, 172)), ("blue", (53, 57, 157)),
    ("brown", (114, 71, 40)), ("green", (84, 109, 27)), ("red", (160, 39, 34)), ("black", (20, 21, 25)),
    ("terracotta", (152, 94, 67)), ("hay", (166, 139, 12)), ("bookshelf", (117, 94, 60)),
    ("coral", (220, 100, 160)), ("snow", (250, 250, 250)), ("brick", (150, 97, 83)),
    ("poppy", (200, 30, 30)), ("dandelion", (240, 220, 40)), ("tulip", (230, 120, 120)),
    ("orchid", (40, 160, 220)), ("allium", (180, 110, 220)), ("bluet", (220, 230, 240)),
    ("daisy", (230, 230, 200)), ("cornflower", (70, 100, 220)), ("valley", (240, 240, 240)),
    ("sunflower", (240, 200, 40)), ("lilac", (200, 150, 210)), ("rose", (190, 40, 40)), ("peony", (230, 170, 220)),
    ("petals", (240, 170, 200)), ("lily", (40, 120, 40)), ("vine", (60, 110, 30)), ("lichen", (110, 140, 110)),
    ("reeds", (140, 190, 90)), ("cactus", (80, 130, 40)), ("pickle", (100, 120, 50)),
    ("slime", (110, 190, 90)), ("honey", (230, 160, 40)), ("target", (230, 200, 190)),
    ("mushroom", (180, 60, 50)), ("wool", (220, 220, 220)), ("concrete", (130, 130, 130)),
]


def block_colors():
    n = len(PAL.entries)
    col = np.zeros((n, 3), np.float32)
    vis = np.zeros(n, bool)
    for i, (name, _) in enumerate(PAL.entries):
        c = (150, 150, 150)
        found = False
        for kw, rgb in KEYWORDS:
            if kw in name:
                found = True
                if rgb is None:
                    c = None
                break
            if found:
                break
        if c is None:
            continue
        if found:
            for kw, rgb in KEYWORDS:
                if kw in name and rgb is not None:
                    c = rgb
                    break
        col[i] = c
        vis[i] = True
    return col, vis


def topdown(area, path, scale=2, y_max=None):
    col, vis = block_colors()
    blk = area.blk if y_max is None else area.blk[:, : y_max - area.y0, :]
    v = vis[blk]
    any_v = v.any(axis=1)
    top = blk.shape[1] - 1 - np.argmax(v[:, ::-1, :], axis=1)
    ids = np.take_along_axis(blk, top[:, None, :], axis=1)[:, 0, :]
    rgb = col[ids]
    h = top.astype(float)
    shade = np.ones_like(h)
    shade[1:, :] += (h[1:, :] - h[:-1, :]) * 0.08
    shade[:, 1:] += (h[:, 1:] - h[:, :-1]) * 0.05
    shade = np.clip(shade, 0.55, 1.35)
    rgb = rgb * shade[:, :, None] * (0.75 + 0.25 * (h[:, :, None] - h.min()) / max(1, h.max() - h.min()))
    rgb[~any_v] = (10, 10, 18)
    img = np.clip(rgb, 0, 255).astype(np.uint8).transpose(1, 0, 2)   # rows = z
    im = Image.fromarray(img).resize((area.sx * scale, area.sz * scale), Image.NEAREST)
    im.save(path)
    return im


def iso(area, path, box=None, s=2, cut_y=None, bg=(18, 16, 28)):
    """Isometric view looking from +x,+z (south-east), top-lit."""
    col, vis = block_colors()
    blk = area.blk
    if box is not None:
        x1, y1, z1, x2, y2, z2 = box
        blk = blk[x1 - area.x0:x2 - area.x0 + 1, y1 - area.y0:y2 - area.y0 + 1, z1 - area.z0:z2 - area.z0 + 1]
    if cut_y is not None:
        blk = blk[:, : cut_y, :]
    v = vis[blk]
    pad = np.pad(v, 1, constant_values=False)
    exposed = v & (~pad[1:-1, 2:, 1:-1] | ~pad[2:, 1:-1, 1:-1] | ~pad[1:-1, 1:-1, 2:])
    xs, ys, zs = np.nonzero(exposed)
    ids = blk[xs, ys, zs]
    c = col[ids]
    sx, sy, sz = blk.shape
    u = (xs - zs) * 2 * s
    vv = (xs + zs) * s - ys * 2 * s
    u = u - u.min() + 2
    vv = vv - vv.min() + 2
    W = int(u.max() + 4 * s + 4)
    H = int(vv.max() + 4 * s + 4)
    depth = (xs + zs + ys).astype(np.float32)
    img = np.zeros((H, W, 3), np.float32)
    img[:] = bg
    zbuf = np.full(H * W, -1e9, np.float32)
    offs = []
    for dy in range(4 * s):
        for dx in range(4 * s):
            if dy < 2 * s:
                mid = 2 * s
                half = (dy + 1) if dy < s else (2 * s - dy)
                if abs(dx + 0.5 - mid) > half * 2:
                    continue
                offs.append((dy, dx, 1.0))
            else:
                offs.append((dy, dx, 0.78 if dx < 2 * s else 0.62))
    base = vv * W + u
    for dy, dx, sh in offs:
        np.maximum.at(zbuf, base + dy * W + dx, depth)
    flat = img.reshape(-1, 3)
    for dy, dx, sh in offs:
        idx = base + dy * W + dx
        m = depth >= zbuf[idx]
        flat[idx[m]] = c[m] * sh
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    im.save(path)
    return im


def persp(area, path, cam, yaw, pitch, W=640, H=360, fov=75, max_steps=420, sky_strength=0.85,
          block_light=None, fog_col=(200, 140, 120), fog_dist=160.0):
    """Simple voxel ray caster. cam=(x,y,z) world coords (eye), yaw: 0 = looking +z (south), 90 = -x (west),
    180 = -z (north), 270 = +x (east); pitch: positive looks down."""
    col, vis = block_colors()
    from mcw import PAL
    names = PAL.names
    n = len(names)
    passthru = np.zeros(n, bool)
    water = np.zeros(n, bool)
    for i, nm in enumerate(names):
        if not vis[i]:
            passthru[i] = True
        if nm in ("water", "flowing_water"):
            water[i] = True
        if "glass" in nm and "pane" not in nm:
            passthru[i] = True
    # sky exposure: highest non-passthrough block per column
    solid = ~passthru[area.blk] & ~water[area.blk]
    anyb = solid.any(axis=1)
    topi = np.where(anyb, area.sy - 1 - np.argmax(solid[:, ::-1, :], axis=1), -1)
    ys, xs = np.mgrid[0:H, 0:W]
    f = 1.0 / math.tan(math.radians(fov) / 2)
    u = (xs + 0.5 - W / 2) / (W / 2)
    v = -(ys + 0.5 - H / 2) / (W / 2)
    d_cam = np.stack([u, v, np.full_like(u, f)], -1)
    d_cam /= np.linalg.norm(d_cam, axis=-1, keepdims=True)
    cy, sy_ = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    # pitch around x
    dx = d_cam[..., 0]
    dy = d_cam[..., 1] * cy - d_cam[..., 2] * sy_
    dz = d_cam[..., 1] * sy_ + d_cam[..., 2] * cy
    a = math.radians(yaw)
    rx = dx * math.cos(a) - dz * math.sin(a)
    rz = dx * math.sin(a) + dz * math.cos(a)
    D = np.stack([rx, dy, rz], -1).reshape(-1, 3)
    N = D.shape[0]
    O = np.array(cam, float) - np.array([area.x0, area.y0, area.z0], float)
    pos = np.tile(O, (N, 1))
    ivox = np.floor(pos).astype(np.int64)
    step = np.where(D > 0, 1, -1)
    with np.errstate(divide="ignore"):
        tdelta = np.where(D != 0, np.abs(1.0 / D), 1e30)
        nxt = np.where(D > 0, ivox + 1 - pos, pos - ivox)
        tmax = np.where(D != 0, nxt * tdelta, 1e30)
    hit = np.zeros(N, bool)
    hit_id = np.zeros(N, np.int64)
    axis = np.zeros(N, np.int64)
    tint = np.ones((N, 3))
    t_hit = np.zeros(N)
    prev = ivox.copy()
    active = np.ones(N, bool)
    shape = np.array(area.blk.shape)
    for _ in range(max_steps):
        idx = np.nonzero(active)[0]
        if len(idx) == 0:
            break
        tm = tmax[idx]
        ax = np.argmin(tm, axis=1)
        prev[idx] = ivox[idx]
        ivox[idx, ax] += step[idx, ax]
        t_hit[idx] = tm[np.arange(len(idx)), ax]
        tmax[idx, ax] += tdelta[idx, ax]
        axis[idx] = ax
        iv = ivox[idx]
        inside = np.all((iv >= 0) & (iv < shape), axis=1)
        out = idx[~inside]
        active[out] = False
        idx = idx[inside]
        iv = iv[inside]
        b = area.blk[iv[:, 0], iv[:, 1], iv[:, 2]]
        w = water[b]
        if w.any():
            tint[idx[w]] *= np.array([0.86, 0.95, 0.98])
        stop = ~passthru[b] & ~w
        hidx = idx[stop]
        hit[hidx] = True
        hit_id[hidx] = b[stop]
        active[hidx] = False
    # colours
    img = np.zeros((N, 3))
    # sky gradient (sunset)
    el = D[:, 1]
    skyc = np.where(el[:, None] < 0.05,
                    np.array([250, 170, 110]) * (1 - np.clip(el, -0.2, 0.05)[:, None] * 0) ,
                    np.array([250, 170, 110]) * (1 - np.clip(el * 2.2, 0, 1))[:, None]
                    + np.array([70, 80, 150]) * np.clip(el * 2.2, 0, 1)[:, None])
    img[:] = skyc
    h = np.nonzero(hit)[0]
    base = col[hit_id[h]].astype(float)
    vx = ivox[h]
    hsh = ((vx[:, 0] * 73856093) ^ (vx[:, 1] * 19349663) ^ (vx[:, 2] * 83492791)) & 255
    base *= (0.92 + 0.16 * hsh[:, None] / 255.0)
    ax = axis[h]
    face = np.where(ax == 1, np.where(D[h, 1] < 0, 1.0, 0.55), np.where(ax == 0, 0.8, 0.68))
    pv = prev[h]
    pv = np.clip(pv, 0, shape - 1)
    skyv = (pv[:, 1] > topi[pv[:, 0], pv[:, 2]]).astype(float)
    if block_light is not None:
        bl = block_light[pv[:, 0], pv[:, 1], pv[:, 2]] / 15.0
    else:
        bl = np.zeros(len(h))
    bright = np.maximum(skyv * sky_strength, bl)
    bright = 0.12 + 0.88 * bright ** 1.15
    fog = np.clip(t_hit[h] / fog_dist, 0, 1)[:, None]
    shade = base * (face * bright)[:, None]
    shade = shade * (1 - fog * 0.6) + np.array(fog_col) * fog * 0.6
    img[h] = shade
    img *= tint
    out = np.clip(img.reshape(H, W, 3), 0, 255).astype(np.uint8)
    im = Image.fromarray(out)
    im.save(path)
    return im
