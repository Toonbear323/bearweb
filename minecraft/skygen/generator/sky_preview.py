"""World icon, previews and world_info.json for the skygen world."""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import render

FONT = "/usr/share/fonts/opentype/unifont/unifont.otf"
VIEWS = {
    # name: (island key, half size)
    "hub": ("hub", 116), "forest": ("forest", 112), "skeld": ("skeld", 100), "volcano": ("volcano", 112),
    "paradise": ("paradise", 112), "library": ("library", 112),
}


def _font(size):
    return ImageFont.truetype(FONT, size) if os.path.exists(FONT) else None


def overview(W, path, scale=1):
    im = render.topdown(W.a, path, scale=scale)
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    f = _font(16)
    a = W.a
    for k, isl in W.islands.items():
        cx, cz = isl["center"]
        x, y = (cx - a.x0) * scale, (cz - a.z0) * scale
        if f:
            tw = d.textlength(isl["name"], font=f)
            d.rectangle((x - tw / 2 - 4, y - 10, x + tw / 2 + 4, y + 10), fill=(20, 20, 30))
            d.text((x - tw / 2, y - 9), isl["name"], font=f, fill=(255, 230, 120))
    im.save(path)
    return im


def icon(W):
    tmp = "/tmp/skygen_icon_top.png"
    im = overview(W, tmp, scale=1)
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((540, 540))
    out = Image.new("RGB", (960, 540), (16, 18, 40))
    out.paste(im, (210, 0))
    d = ImageDraw.Draw(out)
    f = _font(64)
    if f:
        t = "스카이젠"
        tw = d.textlength(t, font=f)
        d.rectangle((480 - tw / 2 - 20, 210, 480 + tw / 2 + 20, 300), fill=(14, 24, 52))
        d.text((480 - tw / 2 + 4, 222), t, font=f, fill=(40, 90, 160))
        d.text((480 - tw / 2, 218), t, font=f, fill=(150, 225, 255))
    return out


def previews(W, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    overview(W, os.path.join(out_dir, "00_overview.png"), scale=1)
    for i, (name, (key, hw)) in enumerate(VIEWS.items(), 1):
        cx, cz = W.islands[key]["center"]
        render.iso(W.a, os.path.join(out_dir, "%02d_%s.png" % (i, name)),
                   box=(cx - hw, 20, cz - hw, cx + hw - 1, 140, cz + hw - 1), s=2)
    import lighting
    a = W.a
    shots = [
        ("p01_hub_plaza", (0, 66.6, 96), 180, 4),
        ("p02_hub_shops", (-43, 66.6, 44), 180, 4),
        ("p03_hub_gallery", (40.5, 67.2, 9.5), 235, 6),
        ("p04_lumber_camp", (38, 72, -197), 180, 14),
        ("p05_quarry", (-42, 73, -283), 180, 26),
        ("p06_furnace_rooms", (262.5, 67.3, 11.5), 0, 8),
        ("p07_reactor_iron", (190, 66.6, -3), 90, 6),
        ("p08_volcano_crater", (256, 96, 241), 180, 28),
        ("p09_plots", (45, 79, 190), 0, 18),
        ("p10_plot_map", (-9, 70.6, 184), 90, 2),
        ("p11_enchanting", (-301, 74.6, 11.2), 180, 24),
        ("p12_forest_bridge", (6, 71, -96), 180, 4),
        ("p13_ship_bridge", (114, 70, 6), 270, 1),
        ("p14_library_door", (-148, 67.6, -9), 90, 2),
    ]
    for name, cam, yaw, pitch in shots:
        cx, cy, cz = cam
        bx1, by1, bz1 = int(cx) - 80, max(a.y0 + 1, int(cy) - 30), int(cz) - 80
        sl = (slice(max(0, bx1 - a.x0), max(0, bx1 - a.x0) + 160), slice(by1 - a.y0, by1 - a.y0 + 70),
              slice(max(0, bz1 - a.z0), max(0, bz1 - a.z0) + 160))
        L = np.zeros(a.blk.shape, np.int8)
        L[sl] = lighting.block_light(a.blk[sl])
        try:
            render.persp(a, os.path.join(out_dir, name + ".png"), cam, yaw, pitch, W=800, H=450, fov=78,
                         block_light=L, fog_col=(170, 190, 225), fog_dist=220)
        except Exception as e:
            print("preview", name, "failed:", e)


def world_info(W, path):
    gens = {}
    for g in W.generators:
        gens.setdefault(g["island"], {}).setdefault(g["kind"], 0)
        gens[g["island"]][g["kind"]] += 1
    info = dict(
        islands={k: dict(name=v["name"], center=v["center"], arrival=W.arrivals.get(k)) for k, v in W.islands.items()},
        generators=gens,
        generator_count=len(W.generators),
        plots=[dict(id=p["id"], entry=p["btn_out"], price=p["price"], size="15x15") for p in W.plots],
        furnace_rooms=[dict(id=r["id"], door=r["door"]) for r in W.furnace_rooms],
        npcs=[dict(name=n["name"], pos=(n["x"], n["y"], n["z"]), tag=n["tag"]) for n in W.npcs if n.get("kind") != "deco"],
        ender_chests=W.ender_chests,
        enchanting_tables=W.enchant_tables,
        repairs=getattr(W, "repairs", []),
        portals=[dict(kind=p["kind"], dest=p["dest"], box=p["box"]) for p in W.portals],
        safe_zone_boxes=len(W.safe_zones),
        verification=getattr(W, "verification", {}),
    )
    json.dump(info, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1,
              default=lambda o: o.tolist() if hasattr(o, "tolist") else int(o))
