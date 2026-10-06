"""Sky bridges between the islands and the return pads.

Bridges are straight (axis aligned), 5 wide with rails, gently sloped with slabs, lanterns on the rails
and chains with lanterns hanging under the deck. They are not safe zones: at night you can be knocked off.
"""
import math

from mcw import B, AIR
from gen_common import slab, wall_sign, standing_sign
from gen_mapbase import bridge

STYLES = {
    "forest": ("spruce_planks", "spruce_slab", "spruce_fence", "lantern"),
    "skeld": ("smooth_stone", "smooth_stone_slab", "iron_bars", "lantern"),
    "library": ("dark_oak_planks", "dark_oak_slab", "dark_oak_fence", "lantern"),
    "paradise": ("birch_planks", "birch_slab", "bamboo_fence", "lantern"),
    "volcano": ("polished_blackstone_bricks", "polished_blackstone_brick_slab", "polished_blackstone_wall",
                "soul_lantern"),
}


def sky_bridge(W, p0, p1, f0, f1, style):
    """p0, p1: (x, z) ends (inclusive); f0, f1: feet height at the ends."""
    a = W.a
    deck, sl, rail, lamp = STYLES[style]
    n = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))
    # keep the middle a little higher (arched look) but never steeper than 1 per 4
    rise = min(4, n // 12)
    mid = max(f0, f1) + rise

    def prof(t):
        base = f0 + (f1 - f0) * t
        return base + (mid - max(f0, f1)) * math.sin(math.pi * t)

    pts = []
    steps = 8
    for k in range(steps):
        t0, t1 = k / steps, (k + 1) / steps
        q0 = (round(p0[0] + (p1[0] - p0[0]) * t0), round(p0[1] + (p1[1] - p0[1]) * t0))
        q1 = (round(p0[0] + (p1[0] - p0[0]) * t1), round(p0[1] + (p1[1] - p0[1]) * t1))
        h0 = round(prof(t0) * 2) / 2
        h1 = round(prof(t1) * 2) / 2
        placed = bridge(a, q0, q1, h0, h1, B(deck), slab(sl), B(rail), lamp=B(lamp), width=5, lamp_every=8)
        pts += placed
    # chains + lanterns under the deck, every 8 blocks
    horiz = abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1])
    for i, (x, f, z) in enumerate(pts):
        if i % 8 != 4:
            continue
        under = int(math.floor(f)) - 2
        for d in range(0, 2):
            a.set(x, under - d, z, B("chain"))
        a.set(x, under - 2, z, B(lamp, hanging=1))
    return pts


def return_pad(W, x, y, z, label, glow="pearlescent_froglight"):
    """3x3 glowing floor pad (floor block level y). Standing on it for a moment takes you to the hub."""
    a = W.a
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            a.set(x + dx, y, z + dz, B(glow, axis="y") if "froglight" in glow else B(glow))
            for h in range(1, 4):
                if a.get(x + dx, y + h, z + dz) != AIR:
                    a.set(x + dx, y + h, z + dz, AIR)
    for (dx, dz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        a.set(x + dx, y + 1, z + dz, B("end_rod", facing_direction=1))
    W.portals.append(dict(kind="return", dest="hub", box=(x - 1, y + 1, z - 1, x + 1, y + 3, z + 1), label=label))
    return (x, y + 1, z)
