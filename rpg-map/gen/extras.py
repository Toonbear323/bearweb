"""Wayside details: river bridge, signposts and lamps along the country roads."""
import math

from . import blocks as bl
from . import kit
from .core import B, Mix
from .kit import Frame
from .layout import SEA
from .terrain import ROADS


def river_bridge(w, T, x=0):
    """Stone arch bridge where the north road crosses the river."""
    col = T.river[x - w.x0, :]
    zs = [z + w.z0 for z in range(len(col)) if col[z] and -220 < z + w.z0 < -90]
    if not zs:
        return
    z0, z1 = min(zs) - 6, max(zs) + 6
    y0 = w.top(x, z0 - 1) or SEA + 3
    y1 = w.top(x, z1 + 1) or SEA + 3
    mix = Mix((bl.block("stone_brick"), 8), (bl.block("mossy_stone_brick"), 2), (B("stonebrick", stone_brick_type="cracked"), 1),
              (bl.block("andesite"), 1))
    n = z1 - z0
    for i in range(n + 1):
        z = z0 + i
        t = i / n
        y = int(round(y0 + (y1 - y0) * t + 3.2 * math.sin(math.pi * t)))
        for dx in range(-3, 4):
            w.fill(x + dx, y + 1, z, x + dx, y + 9, z, 0)
            w.set(x + dx, y, z, mix)
            # arch: solid abutments near the banks, open span in the middle
            depth = int(round(6 * (abs(t - 0.5) * 2) ** 2.2)) + 1
            for yy in range(y - depth, y):
                if w.get(x + dx, yy, z) in (0, bl.WATER):
                    w.set(x + dx, yy, z, mix)
        for dx in (-3, 3):
            w.set(x + dx, y + 1, z, bl.wall("stone_brick"))
            if i % 6 == 3:
                w.set(x + dx, y + 2, z, bl.wall("stone_brick"))
                w.set(x + dx, y + 3, z, bl.lantern())
    for zc in (z0 + n // 3, z0 + 2 * n // 3):
        for dx in (-3, 3):
            for yy in range(SEA - 8, SEA + 4):
                if w.get(x + dx, yy, zc) in (0, bl.WATER):
                    w.set(x + dx, yy, zc, mix)
    xi = x - 5 - w.x0
    T.reserved[xi:xi + 11, z0 - 2 - w.z0:z1 + 3 - w.z0] = True
    kit.auto_waterlog(w, x - 4, SEA - 9, z0 - 1, x + 4, SEA, z1 + 1)


def signpost(w, T, x, z, texts):
    """Post with up to four wall signs: texts = {direction: text}."""
    y = w.top(x, z)
    if y is None:
        return
    w.set(x, y, z, bl.block("cobblestone"))
    for i in range(1, 4):
        w.set(x, y + i, z, bl.log("spruce") if i < 3 else bl.block("spruce"))
    w.set(x, y + 4, z, bl.lantern())
    from .core import DIRS
    for d, text in texts.items():
        dx, dz = DIRS[d]
        w.fill(x + dx, y + 1, z + dz, x + dx, y + 4, z + dz, 0)
        w.put(x + dx, y + 3, z + dz, bl.wall_sign(d, "spruce"), bl.be_sign(text))
    T.reserved[x - 2 - w.x0:x + 3 - w.x0, z - 2 - w.z0:z + 3 - w.z0] = True


def road_lamps(w, T, spacing=30):
    F = Frame(w, 0, 0, 0, 0)
    for name, (pts, hw) in ROADS.items():
        acc = 0.0
        nxt = spacing * 0.6
        side = 1
        for (xa, za), (xb, zb) in zip(pts[:-1], pts[1:]):
            L = math.hypot(xb - xa, zb - za)
            ux, uz = (xb - xa) / L, (zb - za) / L
            while nxt <= acc + L:
                t = nxt - acc
                px = xa + ux * t - uz * (hw + 2) * side
                pz = za + uz * t + ux * (hw + 2) * side
                x, z = int(round(px)), int(round(pz))
                nxt += spacing
                side = -side
                if not (w.x0 + 4 <= x < w.x1 - 4 and w.z0 + 4 <= z < w.z1 - 4):
                    continue
                xi, zi = x - w.x0, z - w.z0
                if T.reserved[xi, zi] or T.road[xi, zi] or T.river[xi, zi]:
                    continue
                y = int(T.h[xi, zi])
                if y <= SEA or w.get(x, y + 1, z) != 0:
                    continue
                arm = "W" if (-uz * side) > 0.5 else "E" if (-uz * side) < -0.5 else ("N" if (ux * side) > 0 else "S")
                wood = "spruce" if T.desert[xi, zi] < 0.5 else "acacia"
                kit.lamp_arm(F, x, y + 1, z, arm, h=4, wood=wood, soul=(T.volcano[xi, zi] > 0.45))
                T.reserved[xi - 1:xi + 2, zi - 1:zi + 2] = True
            acc += L


def build(w, T, log=print):
    river_bridge(w, T)
    signpost(w, T, 5, -104, {"S": "§l↑ 북쪽\n§r초원 던전\n폐허의 성채", "W": "§l← 서쪽\n§r숲 호수", "N": "§l↓ 남쪽\n§r베어 타운"})
    signpost(w, T, 110, 7, {"W": "§l↑ 북동\n§r광산 · 동굴 던전", "S": "§l→ 동쪽\n§r사막 던전\n태양왕의 피라미드", "E": "§l← 서쪽\n§r베어 타운"})
    signpost(w, T, 5, 100, {"N": "§l↓ 남쪽\n§r항구 · 바다 던전", "E": "§l← 남서\n§r지옥문", "S": "§l↑ 북쪽\n§r베어 타운"})
    signpost(w, T, -100, 5, {"E": "§l← 서쪽\n§r개인 집터\n주택단지", "W": "§l→ 동쪽\n§r베어 타운"})
    road_lamps(w, T)
