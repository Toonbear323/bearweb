"""Spawn town 'Bear Town': curtain wall, gatehouses, towers, plaza, spawn rotunda and street grid."""
import math

from . import blocks as bl
from . import kit
from .core import B, Mix
from .kit import Frame
from .layout import G, TOWN_R

AIR = 0
R = TOWN_R


def wall_mix():
    return Mix((bl.block("stone_brick"), 12), (B("stonebrick", stone_brick_type="cracked"), 2),
               (bl.block("mossy_stone_brick"), 2), (bl.block("andesite"), 2), (bl.block("cobblestone"), 2))


def street_mix():
    return Mix((bl.block("stone_brick"), 7), (bl.block("andesite"), 3), (bl.block("cobblestone"), 3),
               (B("stonebrick", stone_brick_type="cracked"), 1), (B("gravel"), 1))


def alley_mix():
    return Mix((bl.block("cobblestone"), 5), (B("gravel"), 3), (B("grass_path"), 3), (bl.block("andesite"), 2),
               (bl.block("mossy_cobblestone"), 1))


def strip_frames(w):
    L = 2 * R + 1
    return {
        "N": Frame.box(w, -R, G, -R, L, 5, "N"),
        "S": Frame.box(w, -R, G, R - 4, L, 5, "S"),
        "E": Frame.box(w, R - 4, G, -R, L, 5, "E"),
        "W": Frame.box(w, -R, G, -R, L, 5, "W"),
    }


def wall_strip(F, L):
    mix = wall_mix()
    rng = F.rng
    F.fill(0, -5, 0, L - 1, 6, 4, mix)
    F.fill(0, 7, -1, L - 1, 24, 6, AIR)
    F.fill(0, 6, 1, L - 1, 6, 3, Mix((bl.block("stone_brick"), 5), (bl.block("polished_andesite"), 2),
                                    (bl.block("andesite"), 1)))
    for x in range(L):
        F.stairs(x, 6, 5, "stone_brick", "N", top=True)
        F.set(x, 7, 5, mix)
        if x % 4 in (0, 1):
            F.set(x, 8, 5, mix)
            F.slab(x, 9, 5, "stone_brick")
        F.set(x, 7, 0, bl.wall("stone_brick"))
        if x % 8 == 4:
            F.set(x, 8, 0, bl.wall("stone_brick"))
            F.lantern(x, 9, 0)
        F.fill(x, -4, 5, x, 0, 5, mix)
        F.stairs(x, 1, 5, "stone_brick", "N")
    for x in range(6, L, 12):
        F.fill(x, 1, 5, x, 4, 5, mix)
        F.stairs(x, 5, 5, "stone_brick", "N")
        F.fill(x, -3, 6, x, 1, 6, mix)
        F.stairs(x, 2, 6, "stone_brick", "N")
    # blind arcade on the town side
    back = Mix((bl.block("cobblestone"), 5), (bl.block("mossy_cobblestone"), 2), (bl.block("stone"), 2))
    for bx in range(3, L - 7, 6):
        F.fill(bx + 1, 1, 0, bx + 4, 4, 0, AIR)
        F.fill(bx + 1, 1, 1, bx + 4, 4, 1, back)
        F.stairs(bx + 1, 4, 0, "stone_brick", "W", top=True)
        F.stairs(bx + 4, 4, 0, "stone_brick", "E", top=True)
        r = rng.random()
        if r < 0.3:
            kit.crate_pile(F, bx + 2, 1, 0, rng, n=3)
        elif r < 0.45:
            F.lantern(bx + 2, 4, 0, hanging=True)
        elif r < 0.55:
            F.set(bx + 2, 1, 0, B("hay_block"))
            F.set(bx + 3, 1, 0, B("hay_block"))
            F.set(bx + 2, 2, 0, B("hay_block"))


def gatehouse(F, cx, label, banner=1):
    """Twin-tower gatehouse centred on local x=cx of a wall strip frame (outside = local south)."""
    mix = wall_mix()
    x0, x1, z0, z1 = cx - 9, cx + 9, -2, 6
    F.fill(x0, -5, z0, x1, 12, z1, mix)
    F.fill(x0, 13, z0 - 1, x1, 30, z1 + 1, AIR)
    # passage with arched head
    F.fill(cx - 2, 1, z0, cx + 2, 5, z1, AIR)
    F.fill(cx - 3, 0, z0 - 1, cx + 3, 0, z1 + 1, street_mix())
    for z in range(z0, z1 + 1):
        F.stairs(cx - 2, 5, z, "stone_brick", "W", top=True)
        F.stairs(cx + 2, 5, z, "stone_brick", "E", top=True)
    for z in (z0, z1):       # deeper outer arch ring
        F.set(cx - 2, 4, z, bl.block("stone_brick"))
        F.set(cx + 2, 4, z, bl.block("stone_brick"))
        F.stairs(cx - 2, 3, z, "stone_brick", "W", top=True)
        F.stairs(cx + 2, 3, z, "stone_brick", "E", top=True)
        F.stairs(cx - 1, 5, z, "stone_brick", "W", top=True)
        F.stairs(cx + 1, 5, z, "stone_brick", "E", top=True)
    for x in range(cx - 1, cx + 2):      # raised portcullis
        F.set(x, 5, 5, B("iron_bars"))
        F.set(x, 4, 5, B("iron_bars"))
    F.set(cx - 2, 4, 5, B("iron_bars"))
    F.set(cx + 2, 4, 5, B("iron_bars"))
    F.lantern(cx, 5, 2, hanging=True)
    F.lantern(cx, 5, -1, hanging=True)
    # gate room over the passage
    F.fill(x0 + 1, 7, z0 + 1, x1 - 1, 11, z1 - 1, AIR)
    F.fill(x0 + 1, 6, z0 + 1, x1 - 1, 6, z1 - 1, bl.planks("spruce"))
    for xx in (x0, x1):
        F.fill(xx, 7, 2, xx, 8, 3, AIR)
        F.stairs(xx, 9, 2, "stone_brick", "S", top=True)
        F.stairs(xx, 9, 3, "stone_brick", "N", top=True)
    for x in (cx - 6, cx - 3, cx, cx + 3, cx + 6):
        F.set(x, 8, z1, B("iron_bars"))
        F.set(x, 9, z1, B("iron_bars"))
        F.set(x, 8, z0, B("glass_pane"))
        F.set(x, 9, z0, B("glass_pane"))
    kit.chandelier(F, cx, 11, 2, drop=1)
    F.set(cx - 7, 7, 4, bl.barrel("U"))
    F.set(cx - 6, 7, 4, bl.barrel("U"))
    F.set(cx - 7, 8, 4, bl.barrel("N"))
    F.chest(cx + 7, 7, 4, "N", [bl.item("arrow", 32), bl.item("bread", 6), bl.item("torch", 16)])
    F.set(cx + 6, 7, 4, B("crafting_table"))
    F.set(cx + 7, 7, -1, B("grindstone", attachment="standing", direction=0))
    for x in (cx - 5, cx + 5):
        kit.table(F, x, 7, 0, "spruce")
    # crenellated curtain between the towers
    F.fill(cx - 3, 12, z0, cx + 3, 12, z1, Mix((bl.block("stone_brick"), 4), (bl.block("polished_andesite"), 1)))
    for x in range(cx - 3, cx + 4):
        for z, f in ((z1 + 1, "N"), (z0 - 1, "S")):
            F.stairs(x, 12, z, "stone_brick", f, top=True)
            F.set(x, 13, z, mix)
            if (x - cx) % 2 == 0:
                F.set(x, 14, z, mix)
                F.slab(x, 15, z, "stone_brick")
    # towers
    for tx0, tx1 in ((x0, x0 + 5), (x1 - 5, x1)):
        F.fill(tx0, 13, z0, tx1, 17, z1, mix)
        F.fill(tx0 + 1, 13, z0 + 1, tx1 - 1, 16, z1 - 1, AIR)
        F.fill(tx0 + 1, 12, z0 + 1, tx1 - 1, 12, z1 - 1, bl.planks("spruce"))
        # corbelled eave
        for x in range(tx0 - 1, tx1 + 2):
            F.stairs(x, 17, z0 - 1, "stone_brick", "S", top=True)
            F.stairs(x, 17, z1 + 1, "stone_brick", "N", top=True)
        for z in range(z0, z1 + 1):
            F.stairs(tx0 - 1, 17, z, "stone_brick", "E", top=True)
            F.stairs(tx1 + 1, 17, z, "stone_brick", "W", top=True)
        top = kit.hip_roof(F, tx0 - 1, z0 - 1, tx1 + 1, z1 + 1, 18, "deepslate_tile", overhang=0,
                           cap="deepslate_tile")
        mx = (tx0 + tx1) // 2
        F.fill(mx, top, 1, mx + 1, top, 3, bl.block("deepslate_tile"))
        for i in range(1, 4):
            F.set(mx, top + i, 2, bl.fence("spruce"))
        F.banner(mx, top + 4, 2, "S", banner, standing=True)
        for yb in (9, 14):
            for x in (mx, mx + 1):
                F.set(x, yb, z1, B("iron_bars"))
                F.set(x, yb + 1, z1, B("iron_bars"))
                F.set(x, yb, z0, B("glass_pane"))
                F.set(x, yb + 1, z0, B("glass_pane"))
        # hanging banners + torches on the outer face
        F.banner(mx, 7, z1 + 1, "S", banner)
        F.banner(mx + 1, 7, z1 + 1, "S", banner)
        F.torch(mx - 1, 4, z1 + 1, attach="N")
        F.torch(mx + 2, 4, z1 + 1, attach="N")
        F.torch(mx, 4, z0 - 1, attach="S")
        F.lantern(mx, 16, 2, hanging=True)
        # ladder inside the tower from the gate room up
        for y in range(7, 13):
            F.set(tx0 + 1 if tx0 == x0 else tx1 - 1, y, z0 + 1, bl.ladder(F.d("S")))
        F.set(tx0 + 1 if tx0 == x0 else tx1 - 1, 12, z0 + 1, bl.ladder(F.d("S")))
    # base batter outside + name plate
    for x in range(x0, x1 + 1):
        if abs(x - cx) > 2:
            F.stairs(x, 1, z1 + 1, "stone_brick", "N")
            F.stairs(x, 1, z0 - 1, "stone_brick", "S")
    F.sign(cx, 7, z1 + 1, "S", label, wood="dark_oak", glow=True)
    F.sign(cx, 7, z0 - 1, "N", label, wood="dark_oak", glow=True)
    # stairs from the town up to the wall walk on both sides
    for sgn in (1, -1):
        for i in range(6):
            x = cx + sgn * (16 - i)
            F.fill(x, -3, -1, x, i, -1, mix)
            F.stairs(x, 1 + i, -1, "stone_brick", "W" if sgn > 0 else "E")
            F.fill(x, 2 + i, -1, x, 9, -1, AIR)
            F.fill(x, 1, 0, x, 6, 0, mix)
        lx = cx + sgn * 10
        F.fill(lx, -3, -1, lx, 6, -1, mix)
        F.fill(lx, 1, 0, lx, 6, 0, mix)
        F.set(lx, 7, 0, AIR)
        F.set(lx, 8, 0, AIR)
        F.set(cx + sgn * 11, 7, 0, AIR)
        F.set(cx + sgn * 11, 8, 0, AIR)
        F.set(cx + sgn * 11, 9, 0, AIR)


def corner_tower(w, sx, sz):
    cx, cz = sx * (R - 2), sz * (R - 2)
    F = Frame(w, 0, 0, 0, 0)
    r = 7.5
    y0 = G + 1
    h = 18
    w.cyl(cx, cz, r + 1.0, G - 5, G, wall_mix())
    top = kit.round_tower(F, cx, cz, y0, h, r, wall_mix(), floor=bl.planks("spruce"), roof="deepslate_tile",
                          floors_every=6)
    # doors onto the wall walks
    for y in (G + 7, G + 8):
        for k in (6, 7, 8):
            w.set(cx - sx * k, y, cz, AIR)
            w.set(cx, y, cz - sz * k, AIR)
    w.fill(cx - sx * 8, G + 6, cz - 1, cx - sx * 6, G + 6, cz + 1, bl.block("stone_brick"))
    w.fill(cx - 1, G + 6, cz - sz * 8, cx + 1, G + 6, cz - sz * 6, bl.block("stone_brick"))
    # ladder on the far side
    lz = cz + sz * 6
    face = "N" if sz > 0 else "S"
    for y in range(y0, top + 1):
        w.set(cx, y, lz, bl.ladder(face))
    w.set(cx, y0 + 5, cz, bl.planks("spruce"))
    w.set(cx, y0 + 11, cz, bl.planks("spruce"))
    # furnishing: armoury / lookout
    rng = w.rng
    for (dx, dz) in ((3, 2), (-3, 2), (2, -3), (-2, -3)):
        w.set(cx + dx, y0, cz + dz * (1 if sz < 0 else -1), bl.barrel("U"))
    w.put(cx - sx * 3, y0, cz + sz * 3, bl.chest("N" if sz > 0 else "S"),
          bl.be_chest([bl.item("bread", 4), bl.item("arrow", 16), bl.item("iron_ingot", 2)]))
    w.set(cx + sx * 2, G + 7, cz + sz * 2, B("crafting_table"))
    for fy in (y0 + 3, G + 10, G + 16):
        w.set(cx, fy + 1, cz, AIR)
    kit.chandelier(F, cx, G + 11, cz, drop=1)
    kit.chandelier(F, cx, G + 17, cz, drop=1)
    w.set(cx, G + 5, cz, bl.lantern(True))


def build_walls(w, T):
    frames = strip_frames(w)
    L = 2 * R + 1
    for f in "NESW":
        wall_strip(frames[f], L)
    labels = {"N": ("§l북문\n§r초원 던전 방면", 1), "E": ("§l동문\n§r사막 · 광산 방면", 11),
              "S": ("§l남문\n§r항구 · 지옥문 방면", 4), "W": ("§l서문\n§r개인 집터 방면", 10)}
    for f in "NESW":
        gatehouse(frames[f], R, labels[f][0], labels[f][1])
    for sx in (-1, 1):
        for sz in (-1, 1):
            corner_tower(w, sx, sz)
    xi0, zi0 = -R - 3 - w.x0, -R - 3 - w.z0
    T.reserved[xi0:xi0 + 2 * R + 7, zi0:zi0 + 2 * R + 7] = True


# ---------------------------------------------------------------------------
# plaza + rotunda
# ---------------------------------------------------------------------------

def build_streets(w):
    sm, am = street_mix(), alley_mix()
    curb = bl.block("polished_andesite")
    inner = R - 5
    # ground inside the walls: clean grass
    w.fill(-inner, G + 1, -inner, inner, G + 40, inner, AIR)
    w.fill(-inner, G, -inner, inner, G, inner, B("grass_block"))
    w.fill(-inner, G - 3, -inner, inner, G - 1, inner, B("dirt"))
    # avenues
    w.fill(-3, G, -inner, 3, G, inner, sm)
    w.fill(-inner, G, -3, inner, G, 3, sm)
    for s in (-3, 3):
        w.fill(s, G, -inner, s, G, inner, curb)
        w.fill(-inner, G, s, inner, G, s, curb)
    w.fill(-2, G, -2, 2, G, 2, sm)
    # lanes behind the avenue frontages
    for s_ in (-49, 47):
        w.fill(-inner, G, s_, inner, G, s_ + 2, am)
    for s_ in (-27, 25):
        w.fill(s_, G, -inner, s_ + 2, G, -8, am)
        w.fill(s_, G, 8, s_ + 2, G, inner, am)
    # sidewalks along the avenues
    side = Mix((bl.block("cobblestone"), 4), (bl.block("andesite"), 3), (B("gravel"), 1), (bl.block("stone_brick"), 2))
    for s_ in (-5, -4, 4, 5):
        w.fill(s_, G, -inner, s_, G, inner, side)
        w.fill(-inner, G, s_, inner, G, s_, side)
    # plaza
    for (dx, dz) in kit.disc_cells(27.5):
        r = math.hypot(dx, dz)
        ang = math.degrees(math.atan2(dz, dx)) % 45.0
        spoke = min(ang, 45 - ang) * math.pi / 180 * r < 0.75
        if r > 26.5:
            b = bl.block("polished_deepslate")
        elif r > 25.5:
            b = bl.block("polished_andesite")
        elif 19.5 < r <= 20.5:
            b = bl.block("polished_andesite")
        elif r <= 14.5:
            b = bl.block("polished_andesite")
        elif spoke:
            b = B("smooth_stone")
        else:
            b = sm
        w.set(dx, G, dz, b)


def rotunda(w):
    """White marble spawn rotunda with a copper dome, an oculus and a beacon at the centre."""
    q = bl.block("quartz")
    sq = bl.block("smooth_quartz")
    pd = bl.block("polished_diorite")
    chis = B("quartz_block", chisel_type="chiseled")
    pillar = B("quartz_block", chisel_type="lines", pillar_axis="y")
    for (dx, dz) in kit.disc_cells(12.5):
        r = math.hypot(dx, dz)
        if r <= 9.5:
            w.set(dx, G + 1, dz, pd)
            ang = math.degrees(math.atan2(dz, dx)) % 45.0
            spoke = min(ang, 45 - ang) * math.pi / 180 * r < 0.6
            if r < 2.3:
                b = B("gold_block")
            elif 4.5 <= r < 5.5:
                b = B("lapis_block")
            elif 8.5 <= r:
                b = sq
            elif spoke:
                b = chis
            else:
                b = q if (dx + dz) % 2 == 0 else pd
            w.set(dx, G + 2, dz, b)
        elif r <= 10.5:
            w.set(dx, G + 1, dz, pd)
            w.set(dx, G + 2, dz, bl.slab("polished_diorite"))
        elif r <= 11.5:
            w.set(dx, G + 1, dz, pd)
        else:
            w.set(dx, G + 1, dz, bl.slab("polished_diorite"))
    # beacon on an iron base
    w.fill(-1, G + 1, -1, 1, G + 1, 1, B("iron_block"))
    w.put(0, G + 2, 0, B("beacon"), {"id": "Beacon", "primary": 0, "secondary": 0})
    # columns
    cols = []
    for k in range(8):
        a = math.radians(k * 45)
        cx, cz = int(round(8 * math.cos(a))), int(round(8 * math.sin(a)))
        cols.append((cx, cz))
        w.set(cx, G + 3, cz, chis)
        for y in range(G + 4, G + 9):
            w.set(cx, y, cz, pillar)
        w.set(cx, G + 9, cz, chis)
        for d, (ddx, ddz) in (("E", (-1, 0)), ("W", (1, 0)), ("S", (0, -1)), ("N", (0, 1))):
            w.set(cx + ddx, G + 9, cz + ddz, bl.stairs("quartz", d, top=True), keep=True)
            w.set(cx + ddx, G + 3, cz + ddz, bl.stairs("quartz", d), keep=True)
    # entablature
    for (dx, dz) in kit.disc_cells(10.5):
        r = math.hypot(dx, dz)
        if 6.8 < r <= 9.5:
            w.set(dx, G + 10, dz, sq)
            w.set(dx, G + 11, dz, B("quartz_bricks") if r > 7.6 else AIR)
        elif 9.5 < r <= 10.5:
            w.set(dx, G + 11, dz, bl.stairs("quartz", kit._inward(dx, dz), top=True))
    # dome with ribs and a gilded oculus
    F = Frame(w, 0, 0, 0, 0)
    dome_b = B("waxed_oxidized_cut_copper")
    rib = B("waxed_oxidized_copper")
    Rr = 9.5
    for dx in range(-10, 11):
        for dz in range(-10, 11):
            rr = math.hypot(dx, dz)
            for dy in range(0, 11):
                d = math.sqrt((dx / Rr) ** 2 + (dz / Rr) ** 2 + (dy / 9.0) ** 2)
                d_in = math.sqrt((dx / (Rr - 1.2)) ** 2 + (dz / (Rr - 1.2)) ** 2 + (dy / 7.8) ** 2)
                if d <= 1.0 and d_in > 1.0:
                    if rr <= 2.5:
                        continue
                    ang = math.degrees(math.atan2(dz, dx)) % 45.0
                    is_rib = min(ang, 45 - ang) * math.pi / 180 * rr < 0.55
                    b = B("gold_block") if rr <= 3.6 else (rib if is_rib else dome_b)
                    w.set(dx, G + 12 + dy, dz, b)
    # lanterns between the columns, hanging from the entablature
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        lx, lz = int(round(8 * math.cos(a))), int(round(8 * math.sin(a)))
        w.set(lx, G + 9, lz, B("chain", pillar_axis="y"))
        w.set(lx, G + 8, lz, bl.lantern(True))
    # welcome boards
    msgs = [
        ((-3, -5), "S", "§l§6베어 RPG§r\n환영합니다!\n§8북쪽: 상점가"),
        ((3, -5), "S", "§l던전 7곳§r\n초원·동굴·사막\n바다·지옥·요새"),
        ((-5, -3), "E", "§l차원문 신전§r\n서쪽 대로 북편\n모든 던전으로 이동"),
        ((5, -3), "W", "§l모험가 길드§r\n동쪽 대로 북편\n전리품 판매 · 안내"),
        ((-5, 3), "E", "§l개인 집터§r\n서문 밖 주택단지\n자유롭게 건축!"),
        ((5, 3), "W", "§l골드§r\n던전 클리어와\n전리품 판매로 획득"),
    ]
    for (sx_, sz_), f, text in msgs:
        w.put(sx_, G + 3, sz_, bl.standing_sign(f, "cherry"), bl.be_sign(text, glow=False))
    return cols


def plaza_decor(w):
    rng = w.rng
    F = Frame(w, 0, 0, 0, 0)
    # lamp posts
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        x, z = int(round(23.5 * math.cos(a))), int(round(23.5 * math.sin(a)))
        kit.lamp_post(F, x, G + 1, z, h=5, wall_mat="stone_brick", wood="dark_oak")
    # cherry planters on the diagonals with benches
    for k in range(4):
        a = math.radians(k * 90 + 45)
        px, pz = int(round(19 * math.cos(a))), int(round(19 * math.sin(a)))
        for (dx, dz) in kit.disc_cells(3.6):
            r = math.hypot(dx, dz)
            if r > 2.6:
                w.set(px + dx, G + 1, pz + dz, bl.stairs("stone_brick", kit._inward(dx, dz)))
            else:
                w.set(px + dx, G + 1, pz + dz, B("grass_block"))
                if (dx, dz) != (0, 0) and rng.random() < 0.7:
                    w.set(px + dx, G + 2, pz + dz, Mix(B("pink_tulip"), B("allium"), B("azure_bluet"),
                                                       B("pink_petals", growth=3, cardinal_direction="south"),
                                                       B("white_tulip"), B("peony", upper_block_bit=False)))
        for (dx, dz) in kit.disc_cells(3.0):
            b = w.get(px + dx, G + 2, pz + dz)
            if b == B("peony", upper_block_bit=False):
                w.set(px + dx, G + 3, pz + dz, B("peony", upper_block_bit=True))
        kit.tree_cherry(w, px, G + 2, pz, rng, h=5)
    # benches facing the rotunda on the cardinal sides of each planter
    for (bx, bz, f) in ((-2, 17, "N"), (-2, -17, "S")):
        kit.bench(F, bx + 6, G + 1, bz, 3, f, "spruce")
        kit.bench(F, bx - 7, G + 1, bz, 3, f, "spruce")
