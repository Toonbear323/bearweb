"""Personal housing district: 12 large fenced plots on a paved street grid west of the town."""
from . import blocks as bl
from . import kit
from .core import B, Mix
from .hub import street_mix
from .kit import Frame
from .layout import G, PLOT_COLS, PLOT_ROAD, PLOT_ROWS, PLOT_SIZE, PLOT_X0, PLOT_Z0

AIR = 0


def plot_origin(c, r):
    return (PLOT_X0 + PLOT_ROAD + c * (PLOT_SIZE + PLOT_ROAD), PLOT_Z0 + PLOT_ROAD + r * (PLOT_SIZE + PLOT_ROAD))


def district_bounds():
    x1 = PLOT_X0 + PLOT_COLS * PLOT_SIZE + (PLOT_COLS + 1) * PLOT_ROAD - 1
    z1 = PLOT_Z0 + PLOT_ROWS * PLOT_SIZE + (PLOT_ROWS + 1) * PLOT_ROAD - 1
    return PLOT_X0, PLOT_Z0, x1, z1


def build_plots(w, T, log=print):
    rng = w.rng
    x0, z0, x1, z1 = district_bounds()
    F = Frame(w, 0, G, 0, 0)
    sm = street_mix()
    curb = bl.block("polished_andesite")
    # level the whole district
    w.fill(x0 - 2, G + 1, z0 - 2, x1 + 2, G + 40, z1 + 2, AIR)
    w.fill(x0 - 2, G, z0 - 2, x1 + 2, G, z1 + 2, B("grass_block"))
    w.fill(x0 - 2, G - 3, z0 - 2, x1 + 2, G - 1, z1 + 2, B("dirt"))
    T.reserved[x0 - 4 - w.x0:x1 + 5 - w.x0, z0 - 4 - w.z0:z1 + 5 - w.z0] = True
    # streets
    w.fill(x0, G, z0, x1, G, z1, sm)
    for c in range(PLOT_COLS + 1):
        xa = PLOT_X0 + c * (PLOT_SIZE + PLOT_ROAD)
        w.fill(xa, G, z0, xa, G, z1, curb)
        w.fill(xa + PLOT_ROAD - 1, G, z0, xa + PLOT_ROAD - 1, G, z1, curb)
    for r in range(PLOT_ROWS + 1):
        za = PLOT_Z0 + r * (PLOT_SIZE + PLOT_ROAD)
        w.fill(x0, G, za, x1, G, za, curb)
        w.fill(x0, G, za + PLOT_ROAD - 1, x1, G, za + PLOT_ROAD - 1, curb)
    for c in range(PLOT_COLS + 1):
        for r in range(PLOT_ROWS + 1):
            xa = PLOT_X0 + c * (PLOT_SIZE + PLOT_ROAD)
            za = PLOT_Z0 + r * (PLOT_SIZE + PLOT_ROAD)
            w.fill(xa + 1, G, za + 1, xa + PLOT_ROAD - 2, G, za + PLOT_ROAD - 2, bl.block("polished_andesite"))
            w.set(xa + PLOT_ROAD // 2, G, za + PLOT_ROAD // 2, B("glowstone"))
            w.set(xa + PLOT_ROAD // 2, G + 1, za + PLOT_ROAD // 2, B("light_gray_carpet"))
    # plots
    n = 0
    post = bl.wall("stone_brick")
    for r in range(PLOT_ROWS):
        for c in range(PLOT_COLS):
            n += 1
            px, pz = plot_origin(c, r)
            qx, qz = px + PLOT_SIZE - 1, pz + PLOT_SIZE - 1
            w.fill(px, G, pz, qx, G, qz, B("grass_block"))
            # border: stone base course, posts every 5, fences between
            for i in range(PLOT_SIZE):
                for (bx, bz) in ((px + i, pz), (px + i, qz), (px, pz + i), (qx, pz + i)):
                    w.set(bx, G, bz, bl.block("stone_brick"))
                    if i % 5 == 0:
                        w.set(bx, G + 1, bz, post)
                        w.set(bx, G + 2, bz, post)
                        if i % 10 == 0:
                            w.set(bx, G + 3, bz, bl.lantern())
                    else:
                        w.set(bx, G + 1, bz, bl.fence("spruce"))
            # gate in the middle of the south side
            gx = px + PLOT_SIZE // 2
            for dx in (-1, 0, 1):
                w.set(gx + dx, G + 1, qz, bl.gate("spruce", "S"))
                w.set(gx + dx, G, qz, bl.block("polished_andesite"))
            for dx in (-2, 2):
                w.set(gx + dx, G + 1, qz, bl.log("spruce"))
                w.set(gx + dx, G + 2, qz, bl.log("spruce"))
                w.set(gx + dx, G + 3, qz, bl.log("spruce"))
                w.set(gx + dx, G + 4, qz, bl.slab("spruce"))
            for dx in (-1, 0, 1):
                w.set(gx + dx, G + 4, qz, bl.slab("spruce", top=True))
            w.set(gx, G + 3, qz, bl.lantern(True))
            # name plate + mailbox
            sign = bl.be_sign("§l%d번 집터\n§r주인:\n(이름을 적으세요)" % n)
            sign["IsWaxed"] = bl.Byte(0)
            w.put(gx - 2, G + 2, qz + 1, bl.wall_sign("S", "spruce"), sign)
            w.put(gx + 3, G + 1, qz + 1, bl.barrel("U"), bl.be_chest([], "Barrel"))
            # a little path stub + corner trees inside the plot
            for i in range(1, 4):
                w.set(gx, G, qz - i, B("grass_path"))
            for (tx, tz) in ((px + 4, pz + 4), (qx - 4, pz + 4)):
                if rng.random() < 0.6:
                    kit.tree_oak(w, tx, G + 1, tz, rng) if rng.random() < 0.6 else kit.tree_birch(w, tx, G + 1, tz, rng)
            for _ in range(40):
                fx, fz = int(rng.integers(px + 2, qx - 1)), int(rng.integers(pz + 2, qz - 1))
                if w.get(fx, G + 1, fz) == 0 and w.get(fx, G, fz) == B("grass_block"):
                    w.set(fx, G + 1, fz, B("short_grass") if rng.random() < 0.6 else kit.flowers(rng))
    # street lamps at mid-block
    for c in range(PLOT_COLS + 1):
        xa = PLOT_X0 + c * (PLOT_SIZE + PLOT_ROAD)
        for r in range(PLOT_ROWS):
            zc = PLOT_Z0 + PLOT_ROAD + r * (PLOT_SIZE + PLOT_ROAD) + PLOT_SIZE // 2
            if not (c == PLOT_COLS and abs(zc) < 6):
                kit.lamp_arm(F, xa, 1, zc + 8, "E", h=4)
                kit.lamp_arm(F, xa + PLOT_ROAD - 1, 1, zc - 8, "W", h=4)
    # entrance arch on the east side (road from the town's west gate)
    ex = x1 + 1
    for dz in (-4, 4):
        w.fill(ex, G + 1, dz, ex, G + 1, dz, bl.block("stone_brick"))
        for y in range(G + 2, G + 7):
            w.set(ex, y, dz, bl.log("spruce"))
        w.set(ex, G + 7, dz, bl.block("stone_brick"))
        w.set(ex, G + 8, dz, bl.lantern())
    for dz in range(-5, 6):
        w.set(ex, G + 6, dz, bl.log("spruce", "z"))
        if abs(dz) < 4:
            w.set(ex, G + 7, dz, bl.slab("dark_oak"))
    for dz in (-2, 2):
        w.set(ex, G + 5, dz, bl.lantern(True))
    w.put(ex + 1, G + 6, 0, bl.wall_sign("E", "dark_oak"), bl.be_sign("§d§l베어 주택단지\n§r개인 집터 12필지\n§2자유 건축 구역", glow=True))
    w.put(ex - 1, G + 6, 0, bl.wall_sign("W", "dark_oak"), bl.be_sign("§l베어 타운 방면\n§r→ 동쪽", glow=True))
    w.fill(ex, G, -3, ex + 4, G, 3, sm)
    # notice board near the entrance
    w.set(ex + 2, G + 1, 5, bl.fence("spruce"))
    w.set(ex + 2, G + 2, 5, bl.planks("spruce"))
    w.put(ex + 2, G + 2, 4, bl.wall_sign("N", "spruce"),
          bl.be_sign("§l집터 이용 안내\n§r빈 집터의 표지판에\n이름을 적고\n집을 지으세요!"))
    w.put(ex + 3, G + 2, 5, bl.wall_sign("E", "spruce"),
          bl.be_sign("§l이곳은\n§2서바이벌 구역\n§r블록 설치·파괴\n가능"))
    return (x0, z0, x1, z1)
