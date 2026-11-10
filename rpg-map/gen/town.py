"""Buildings inside Bear Town: shops, warp shrine, guild hall, inn, houses, park."""
import math

from . import blocks as bl
from . import houses, kit
from .catalog import DUNGEONS, SELLS, SHOPS
from .core import B, Mix, DIRS, OPP
from .hub import street_mix, wall_mix
from .kit import Frame
from .layout import G

AIR = 0
_CARD = {"N": "north", "E": "east", "S": "south", "W": "west"}


def card(F, d):
    return _CARD[F.d(d)]


# ---------------------------------------------------------------------------
# shops
# ---------------------------------------------------------------------------

SHOP_STYLE = {
    "weapon": ("dark", "§l무기점", "§c§l⚔ 무기점 ⚔", 14),
    "armor": ("brick", "§l방어구점", "§9§l방어구점", 11),
    "tool": ("spruce", "§l도구점", "§2§l도구 · 잡화", 13),
    "magic": ("purple", "§l마법 상점", "§5§l마법 상점", 10),
    "food": ("red", "§l식료품점", "§6§l식료품점", 1),
}


def sale_slot(F, x, y, z, d, text, command, panel, deco=None):
    """One purchase slot on a display wall block (x,y,z) whose customer side is `d`."""
    dx, dz = DIRS[d]
    F.button_cmd(x, y, z, d, command, support=panel, kind="polished_blackstone_button")
    F.sign(x + dx, y + 1, z + dz, d, text, wood="spruce")
    if deco is not None:
        F.set(x, y - 1, z, deco)


def shop_interior(F, info, kind):
    rng = F.rng
    pal = info["pal"]
    items = SHOPS[kind]
    W, D = info["W"], info["D"]
    panel = bl.planks(pal["accent"] if pal["accent"] in bl.WOODS else "spruce")
    frame = pal["frame"]
    # display walls with a hidden service cavity behind them
    F.fill(1, 2, 2, W - 2, 5, 2, panel)
    F.fill(2, 2, 3, 2, 5, 13, panel)
    F.fill(W - 3, 2, 3, W - 3, 5, 13, panel)
    F.fill(1, 2, 13, 2, 5, 13, panel)
    F.fill(W - 3, 2, 13, W - 2, 5, 13, panel)
    slots = [(x, 2, "S") for x in (4, 6, 8, 10, 12)] + [(2, z, "E") for z in (4, 6, 8, 10, 12)] + [
        (W - 3, z, "W") for z in (4, 6, 8, 10, 12)]
    for x in (3, 5, 7, 9, 11, 13):
        for y in range(2, 6):
            F.log(x, y, 2, frame)
    for z in (3, 5, 7, 9, 11, 13):
        for y in range(2, 6):
            F.log(2, y, z, frame)
            F.log(W - 3, y, z, frame)
    extra = len(items) - len(slots)
    if extra > 0:    # central island with slots on both long sides
        F.fill(7, 2, 6, 9, 4, 10, panel)
        F.fill(7, 5, 6, 9, 5, 10, bl.slab(pal["floor"]))
        for z in (6, 8, 10):
            slots.append((7, z, "W"))
            slots.append((9, z, "E"))
        for z in (7, 9):
            for y in (2, 3, 4):
                F.log(7, y, z, frame)
                F.log(9, y, z, frame)
    decos = {"weapon": [B("smithing_table"), bl.barrel("U"), B("polished_andesite")],
             "armor": [B("iron_block"), bl.barrel("U"), B("smithing_table")],
             "tool": [bl.barrel("U"), B("crafting_table"), B("composter")],
             "magic": [B("bookshelf"), B("amethyst_block"), B("chiseled_bookshelf", books_stored=63, direction=0)],
             "food": [bl.barrel("U"), B("hay_block"), B("melon_block")]}[kind]
    for (sid, label, price, _cmds), (x, z, d) in zip(items, slots):
        text = "§l%s\n§6%d 골드" % (label.replace("\n", "§r\n"), price)
        sale_slot(F, x, 3, z, d, text, "function bear/shop/" + sid, panel, deco=decos[int(rng.integers(0, len(decos)))])
        dx, dz = DIRS[d]
        if (x, z) not in ((7, 6), (7, 8), (7, 10), (9, 6), (9, 8), (9, 10)):
            F.set(x, 5, z, B("glowstone") if kind != "magic" else B("sea_lantern"))
    # floor runner + lights
    col = {"weapon": "red", "armor": "blue", "tool": "green", "magic": "purple", "food": "orange"}[kind]
    for z in range(11, D - 1):
        F.set(info["door_x"], 2, z, B(col + "_carpet"), keep=True)
    for (lx, lz) in ((5, 6), (11, 6), (5, 11), (11, 11), (8, 14)):
        if F.get(lx, 5, lz) == 0:
            F.lantern(lx, 5, lz, hanging=True, soul=(kind == "magic"))
    F.sign(info["door_x"] - 1, 3, D - 2, "N", "§l이용 방법\n§r원하는 물건의\n버튼을 누르면\n골드로 구매!", wood="spruce")
    # themed centre pieces
    if extra <= 0:
        if kind == "weapon":
            F.set(8, 2, 8, bl.anvil(F.d("E")))
            F.set(6, 2, 8, B("grindstone", attachment="standing", direction=0))
            F.set(10, 2, 8, B("cauldron", cauldron_liquid="water", fill_level=6))
            for x in (6, 10):
                F.set(x, 2, 6, bl.fence("dark_oak"))
                F.set(x, 3, 6, bl.fence("dark_oak"))
                F.set(x, 4, 6, B("iron_bars"))
        elif kind == "armor":
            for x in (6, 10):
                F.set(x, 2, 7, B("polished_andesite"))
                F.set(x, 3, 7, B("iron_block"))
                F.set(x, 4, 7, B("carved_pumpkin", cardinal_direction=card(F, "S")))
                F.set(x, 2, 10, B("polished_andesite"))
                F.set(x, 3, 10, B("gold_block") if x == 6 else B("diamond_block"))
                F.set(x, 4, 10, B("carved_pumpkin", cardinal_direction=card(F, "S")))
            F.set(8, 2, 8, B("smithing_table"))
        elif kind == "tool":
            F.set(8, 2, 8, B("crafting_table"))
            F.set(7, 2, 8, B("stonecutter_block", cardinal_direction=card(F, "S")))
            F.set(9, 2, 8, B("cartography_table"))
            F.set(8, 2, 7, bl.barrel("U"))
            F.set(8, 3, 8, bl.lantern())
            kit.crate_pile(F, 5, 2, 9, rng, 4)
            kit.crate_pile(F, 10, 2, 9, rng, 4)
        elif kind == "food":
            for (tx, tz) in ((6, 7), (10, 7), (6, 10), (10, 10)):
                F.set(tx, 2, tz, bl.fence("spruce"))
                F.set(tx, 3, tz, B("spruce_pressure_plate"))
            F.set(8, 2, 8, bl.block("spruce"))
            F.set(8, 3, 8, B("cake"))
            F.set(8, 2, 9, B("hay_block"))
            F.set(7, 2, 8, B("melon_block"))
            F.set(9, 2, 8, B("pumpkin", cardinal_direction=card(F, "S")))
    # stairs + upper floor
    houses.stairwell(F, info, 10, D - 2, 1, 0)
    fy = info["fy"]
    uy = fy[1] + 1
    zf = info["zf"][1] - 1
    F.bed(2, uy, 2, "W", {"weapon": 14, "armor": 11, "tool": 13, "magic": 10, "food": 1}[kind])
    F.chest(1, uy, 4, "E", [])
    F.set(1, uy, 5, B("bookshelf"))
    F.set(1, uy + 1, 5, bl.lantern())
    for x in range(5, W - 2, 2):
        F.set(x, uy, 1, bl.barrel("U") if rng.random() < 0.6 else B("bookshelf"))
        if rng.random() < 0.5:
            F.set(x, uy + 1, 1, bl.barrel("S"))
    kit.table(F, 6, uy, 8, pal["accent"] if pal["accent"] in bl.WOODS else "spruce")
    F.stairs(5, uy, 8, "spruce", "W")
    F.stairs(7, uy, 8, "spruce", "E")
    for x in range(3, 9):
        for z in range(5, 8):
            F.set(x, uy, z, B(col + "_carpet"), keep=True)
    F.lantern(8, fy[2] - 1, 8, hanging=True)
    F.lantern(4, fy[2] - 1, 12, hanging=True)
    kit.crate_pile(F, W - 4, uy, 3, rng, 5)


def forge(F, W):
    """Open smithy lean-to on the local west side of the weapon shop."""
    stone = wall_mix()
    x0, x1, z0, z1 = -6, -1, 3, 13
    F.fill(x0, 1, z0, x1, 1, z1, Mix((bl.block("cobblestone"), 3), (bl.block("stone_brick"), 3),
                                     (bl.block("andesite"), 2)))
    F.fill(x0, 2, z0, x1, 9, z1, AIR)
    for (px, pz) in ((x0, z0), (x0, z1), (x0, (z0 + z1) // 2)):
        F.set(px, 2, pz, bl.block("stone_brick"))
        for y in range(3, 6):
            F.log(px, y, pz, "dark_oak")
    for z in range(z0 - 1, z1 + 2):
        for x in range(x0, x1 + 1):
            F.slab(x, 6, z, "deepslate_tile")
        F.stairs(x0 - 1, 5, z, "deepslate_tile", "E")
        F.set(x0, 5, z, bl.log("dark_oak", F.ax("z")), keep=True) if z0 <= z <= z1 else None
    # furnace block with chimney
    F.fill(x1 - 1, 2, z0, x1, 4, z0 + 2, stone)
    F.set(x1 - 1, 2, z0 + 1, B("lit_blast_furnace", cardinal_direction=card(F, "W")))
    F.set(x1 - 1, 3, z0 + 1, B("magma"))
    for y in range(5, 12):
        F.set(x1, y, z0 + 1, stone)
    F.set(x1, 12, z0 + 1, bl.campfire())
    F.set(x1 - 2, 2, z0 + 1, B("cauldron", cauldron_liquid="lava", fill_level=6))
    F.set(x0 + 2, 2, 7, bl.anvil(F.d("N")))
    F.set(x0 + 2, 2, 10, B("grindstone", attachment="standing", direction=1))
    F.set(x1, 2, 9, B("smithing_table"))
    F.set(x1, 2, 10, B("cauldron", cauldron_liquid="water", fill_level=6))
    F.set(x1, 2, 12, bl.barrel("U"))
    F.set(x1, 3, 12, bl.barrel("W"))
    F.set(x1 - 1, 2, 12, B("coal_block"))
    F.set(x0 + 1, 2, z1, B("iron_block"))
    F.set(x0 + 1, 3, z1, B("iron_bars"))
    F.lantern(x0 + 2, 5, 8, hanging=True)
    F.lantern(x1 - 1, 5, 11, hanging=True)
    F.sign(x0 - 1, 4, (z0 + z1) // 2, "W", "§l대장간", wood="dark_oak")


def magic_tower(F, cx, cz):
    """Round wizard tower fused to the corner of the magic shop."""
    r = 4.0
    wallm = Mix((bl.block("deepslate_brick"), 5), (bl.block("polished_deepslate"), 2),
                (bl.block("cobbled_deepslate"), 2), (B("cracked_deepslate_bricks"), 1))
    h = 19
    for y in range(-3, 1):
        for (dx, dz) in kit.disc_cells(r):
            F.set(cx + dx, y, cz + dz, wallm)
    for y in range(1, 1 + h):
        for (dx, dz) in kit.disc_cells(r):
            d = math.hypot(dx, dz)
            F.set(cx + dx, y, cz + dz, wallm if d > r - 1.0 else AIR)
    for fyy in (1, 6, 11, 16):
        for (dx, dz) in kit.disc_cells(r - 1.0):
            F.set(cx + dx, fyy, cz + dz, bl.planks("dark_oak"))
    for y in (8, 9, 13, 14, 18):
        for (dx, dz) in ((4, 0), (0, 4), (0, -4)):
            F.set(cx + dx, y, cz + dz, B("purple_stained_glass_pane"))
    for (dx, dz) in kit._ring(r + 1.0):
        F.stairs(cx + dx, h, cz + dz, "deepslate_tile", kit._inward(dx, dz), top=True)
    kit.cone_roof(F, cx, cz, h + 1, r, "purpur", steep=2,
                  spire=[B("amethyst_block"), B("amethyst_cluster", block_face="up")])
    # ladder shaft + rooms
    for y in range(2, 17):
        F.set(cx, y, cz + 2, bl.ladder(F.d("N")))
    for fyy in (6, 11, 16):
        F.set(cx, fyy, cz + 2, bl.ladder(F.d("N")))
    F.set(cx, 17, cz, B("enchanting_table"))
    for (dx, dz) in ((-2, -1), (-2, 0), (-2, 1), (2, -1), (2, 0), (2, 1), (-1, -2), (0, -2), (1, -2)):
        F.set(cx + dx, 17, cz + dz, B("bookshelf"))
        F.set(cx + dx, 18, cz + dz, B("bookshelf"))
    F.lantern(cx, 19, cz, hanging=True, soul=True)
    F.set(cx - 1, 12, cz - 1, B("brewing_stand"))
    F.set(cx + 1, 12, cz - 1, B("cauldron", cauldron_liquid="water", fill_level=4))
    F.set(cx - 2, 12, cz, B("amethyst_block"))
    F.set(cx - 2, 13, cz, B("amethyst_cluster", block_face="up"))
    F.lantern(cx, 15, cz, hanging=True, soul=True)
    F.set(cx + 1, 7, cz - 1, B("lectern", cardinal_direction=card(F, "S")))
    F.set(cx - 1, 7, cz - 2, B("bookshelf"))
    F.lantern(cx, 10, cz, hanging=True, soul=True)
    F.lantern(cx, 5, cz, hanging=True, soul=True)
    F.set(cx - 2, 2, cz, B("cauldron", cauldron_liquid="water", fill_level=6))
    F.set(cx + 1, 2, cz - 2, B("brewing_stand"))


def shop(w, x, z, face, kind):
    palname, sign, board, bcol = SHOP_STYLE[kind]
    W = D = 17
    F = Frame.box(w, x, G, z, W, D, face)
    pal = houses.palette(palname)
    info = houses.shell(F, W, D, floors=2, pal=pal, jetty=True, roof_axis="x", door_x=8, dormer=True, sign=sign,
                        ground_side_windows=False, ground_back_windows=False,
                        chimney=("E", 6) if kind == "food" else None)
    shop_interior(F, info, kind)
    # sign board over the door and banners
    F.sign(8, 6, D + 1, "S", board, wood="dark_oak", glow=True)
    F.banner(3, 9, D + 1, "S", bcol)
    F.banner(13, 9, D + 1, "S", bcol)
    if kind == "weapon":
        forge(F, W)
        F.set(-1, 2, 8, AIR)
        F.set(-1, 3, 8, AIR)
    elif kind == "magic":
        magic_tower(F, W + 1, 3)
        for y in (2, 3):
            F.set(W - 1, y, 3, AIR)
            F.set(W - 2, y, 3, AIR)
            F.set(W - 3, y, 3, AIR)
            F.set(W, y, 3, AIR)
        F.set(W - 3, 4, 3, bl.planks("crimson"))
    elif kind == "food":
        # striped awning + street tables
        for xx in range(1, W - 1):
            c = "red" if xx % 2 else "white"
            F.set(xx, 5, D + 1, B(c + "_wool"))
            F.set(xx, 5, D + 2, B(c + "_carpet")) if False else None
            F.slab(xx, 4, D + 2, "spruce", top=True) if False else None
        for xx in (3, 13):
            F.set(xx, 2, D + 3, bl.fence("spruce"))
            F.set(xx, 3, D + 3, B("white_carpet"))
            F.stairs(xx - 1, 2, D + 3, "spruce", "W")
            F.stairs(xx + 1, 2, D + 3, "spruce", "E")
        F.fill(1, 1, D + 1, W - 2, 1, D + 3, Mix((bl.block("stone_brick"), 3), (bl.block("andesite"), 1)))
        F.stairs(8, 1, D, "stone_brick", "N")
    elif kind == "tool":
        kit.crate_pile(F, 2, 2, D + 1, F.rng, 5)
        kit.crate_pile(F, 13, 2, D + 1, F.rng, 5)
        F.fill(1, 1, D + 1, 3, 1, D + 2, bl.block("spruce"))
        F.fill(12, 1, D + 1, 14, 1, D + 2, bl.block("spruce"))
    elif kind == "armor":
        for xx in (5, 11):
            F.set(xx, 2, D + 1, bl.block("stone_brick"))
            F.set(xx, 3, D + 1, B("iron_block"))
            F.set(xx, 4, D + 1, B("carved_pumpkin", cardinal_direction=card(F, "S")))
        F.fill(4, 1, D + 1, 12, 1, D + 1, bl.block("stone_brick"))
        F.stairs(8, 1, D, "stone_brick", "N")
    return info


# ---------------------------------------------------------------------------
# warp shrine
# ---------------------------------------------------------------------------

WARPS = [
    # id, title line, theme frame block, floor block, glass colour
    ("plains", "§2§l초원 던전", "mossy_stone_brick", "moss_block", "lime"),
    ("cave", "§8§l동굴 던전", "deepslate_brick", "amethyst_block", "purple"),
    ("desert", "§6§l사막 던전", "cut_sandstone", "chiseled_sandstone", "yellow"),
    ("ocean", "§3§l바다 던전", "prismarine_brick", "dark_prismarine", "cyan"),
    ("hell", "§c§l지옥 던전", "red_nether_brick", "netherrack", "red"),
    ("fortress", "§4§l네더 요새", "nether_brick", "chiseled_nether_bricks", "orange"),
    ("bastion", "§6§l피글린 요새", "polished_blackstone_brick", "gilded_blackstone", "black"),
    ("plots", "§d§l개인 집터", "cherry", "cherry_planks", "pink"),
]
_WARP_SUB = {"plains": "폐허의 성채", "cave": "수정 동굴", "desert": "태양왕의 피라미드", "ocean": "가라앉은 신전",
             "hell": "불타는 협곡", "fortress": "위더의 성채", "bastion": "황금 보루", "plots": "주택 단지"}


def _theme_block(name):
    if name == "chiseled_sandstone":
        return B("sandstone", sand_stone_type="heiroglyphs")
    try:
        return bl.block(name)
    except KeyError:
        return B(name)


def warp_shrine(w, x, z, face):
    W, D = 23, 33
    F = Frame.box(w, x, G, z, W, D, face)
    rng = F.rng
    white = Mix((B("calcite"), 5), (bl.block("quartz"), 3), (bl.block("polished_diorite"), 2))
    stone = Mix((bl.block("stone_brick"), 8), (bl.block("polished_andesite"), 2), (bl.block("andesite"), 1))
    qb = B("quartz_bricks")
    pillar = B("quartz_block", chisel_type="lines", pillar_axis="y")
    chis = B("quartz_block", chisel_type="chiseled")
    # podium and floor
    F.fill(-1, -3, -1, W, 0, D, stone)
    F.fill(0, 1, 0, W - 1, 2, D - 1, stone)
    F.fill(0, 3, 0, W - 1, 30, D - 1, AIR)
    for xx in range(-1, W + 1):
        F.stairs(xx, 1, -1, "stone_brick", "S")
        F.stairs(xx, 1, D, "stone_brick", "N")
    for zz in range(0, D):
        F.stairs(-1, 1, zz, "stone_brick", "E")
        F.stairs(W, 1, zz, "stone_brick", "W")
    for xx in range(0, W):
        for zz in range(0, D):
            F.set(xx, 2, zz, bl.block("polished_andesite") if (xx + zz) % 2 == 0 else bl.block("polished_diorite"))
    for xx in range(5, 18):
        F.set(xx, 1, D, bl.block("stone_brick"))
        F.stairs(xx, 2, D, "quartz", "N")
        F.stairs(xx, 1, D + 1, "quartz", "N")
        F.set(xx, 0, D + 1, bl.block("stone_brick"))
    # cella walls
    zc = 26
    F.walls(0, 3, 0, W - 1, 11, zc, white)
    F.walls(0, 3, 0, W - 1, 3, zc, stone)
    F.walls(0, 11, 0, W - 1, 11, zc, qb)
    for zz in range(2, zc, 6):
        for y in range(4, 11):
            F.set(-1, y, zz, pillar)
            F.set(W, y, zz, pillar)
        F.set(-1, 3, zz, chis)
        F.set(W, 3, zz, chis)
        F.set(-1, 2, zz, bl.block("stone_brick"))
        F.set(W, 2, zz, bl.block("stone_brick"))
        F.set(-1, 1, zz, bl.block("stone_brick"))
        F.set(W, 1, zz, bl.block("stone_brick"))
        F.stairs(-1, 11, zz, "quartz", "E", top=True)
        F.stairs(W, 11, zz, "quartz", "W", top=True)
    # doorway (3 wide, arched)
    F.fill(10, 3, zc, 12, 7, zc, AIR)
    F.stairs(10, 7, zc, "quartz", "W", top=True)
    F.stairs(12, 7, zc, "quartz", "E", top=True)
    F.set(9, 3, zc, chis)
    F.set(13, 3, zc, chis)
    for y in range(4, 8):
        F.set(9, y, zc, pillar)
        F.set(13, y, zc, pillar)
    F.fill(9, 8, zc, 13, 8, zc, B("gold_block"))
    # portico
    for cx in (0, 4, 9, 13, 18, 22):
        F.set(cx, 3, D - 1, chis)
        for y in range(4, 10):
            F.set(cx, y, D - 1, pillar)
        F.set(cx, 10, D - 1, chis)
        for d_, (ddx, ddz) in (("E", (-1, 0)), ("W", (1, 0)), ("S", (0, -1))):
            F.stairs(cx + ddx, 10, D - 1 + ddz, "quartz", d_, top=True, keep=True)
    F.fill(0, 11, D - 1, W - 1, 11, D - 1, qb)
    F.fill(0, 11, zc + 1, 0, 11, D - 1, qb)
    F.fill(W - 1, 11, zc + 1, W - 1, 11, D - 1, qb)
    F.fill(1, 11, zc + 1, W - 2, 11, D - 2, bl.slab("smooth_quartz", top=True))
    for cx in (6, 11, 16):
        F.lantern(cx, 10, D - 3, hanging=True)
    # roof with pediments
    top = kit.gable_roof(F, 0, 0, W - 1, D - 1, 12, "dark_prismarine", axis="z", overhang=1, trim="prismarine_brick",
                         gable=white)
    cxm = W // 2
    for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1), (2, 0), (-2, 0),
                     (0, 2), (0, -2)):
        for zz in (0, D - 1):
            if F.get(cxm + dx, 16 + dy, zz) != 0:
                F.set(cxm + dx, 16 + dy, zz, B("gold_block") if (dx, dy) == (0, 0) else B(
                    "magenta_stained_glass") if abs(dx) + abs(dy) == 1 else B("purple_stained_glass"))
    F.set(cxm, top + 1, D, B("gold_block"))
    F.set(cxm, top + 2, D, B("end_rod", facing_direction=1))
    F.set(cxm, top + 1, -1, B("gold_block"))
    # interior: tie beams + chandeliers
    for zz in (4, 10, 16, 22):
        for xx in range(1, W - 1):
            F.set(xx, 12, zz, bl.log("dark_oak", F.ax("x")))
        if zz > 4:
            kit.chandelier(F, cxm, 11, zz, drop=2, arms=1, soul=True)
    # piers and warp alcoves
    pier = Mix((bl.block("quartz"), 4), (qb, 3), (B("calcite"), 2))
    for side in (0, 1):
        xw = 0 if side == 0 else W - 1
        dr = 1 if side == 0 else -1
        face_in = "E" if side == 0 else "W"
        F.fill(xw + dr, 3, 1, xw + dr * 3, 9, zc - 1, pier)
        for k in range(4):
            wid, title, frame_b, floor_b, colr = WARPS[side * 4 + k]
            z0 = 3 + 6 * k
            fb = _theme_block(frame_b)
            flb = _theme_block(floor_b)
            F.fill(xw + dr * 2, 3, z0, xw + dr * 3, 8, z0 + 2, AIR)
            F.fill(xw + dr * 2, 9, z0, xw + dr * 3, 9, z0 + 2, pier)
            # glowing portal panel
            for zz in range(z0, z0 + 3):
                F.set(xw + dr, 2, zz, B("sea_lantern"))
                F.set(xw + dr, 7, zz, B("sea_lantern"))
                for y in range(3, 7):
                    F.set(xw + dr, y, zz, B(colr + "_stained_glass"))
                F.set(xw + dr, 8, zz, fb)
                F.set(xw + dr * 2, 2, zz, flb)
                F.set(xw + dr * 3, 2, zz, flb)
            for zz in (z0 - 1, z0 + 3):
                for y in range(3, 8):
                    F.set(xw + dr * 2, y, zz, fb)
                    F.set(xw + dr * 3, y, zz, fb)
            F.stairs(xw + dr * 3, 8, z0, "quartz", "N", top=True)
            F.stairs(xw + dr * 3, 8, z0 + 2, "quartz", "S", top=True)
            F.stairs(xw + dr * 2, 8, z0, "quartz", "N", top=True)
            F.stairs(xw + dr * 2, 8, z0 + 2, "quartz", "S", top=True)
            if wid == "bastion":
                F.set(xw + dr * 3, 7, z0 - 1, B("gold_block"))
                F.set(xw + dr * 3, 7, z0 + 3, B("gold_block"))
            if wid == "cave":
                F.set(xw + dr * 3, 3, z0, B("amethyst_cluster", block_face="up"))
            F.plate_cmd(xw + dr * 2, 3, z0 + 1, "function bear/warp/" + wid,
                        plate="light_weighted_pressure_plate", floor=flb)
            F.sign(xw + dr * 4, 9, z0 + 1, face_in, "%s\n§r%s" % (title, _WARP_SUB[wid]), wood="dark_oak", glow=True)
            info_txt = "§l발판을 밟으면\n이동합니다"
            if wid in DUNGEONS:
                info_txt = "§l보상 %d 골드§r\n%s" % (DUNGEONS[wid][1], DUNGEONS[wid][2])
            F.sign(xw + dr * 4, 5, z0 - 1, face_in, info_txt, wood="dark_oak")
            F.set(xw + dr * 4, 6, z0 + 3, B("end_rod", facing_direction={"E": 5, "W": 4, "N": 2, "S": 3}[
                F.d(face_in)]))
    # carpet runner and altar
    for zz in range(6, zc + 1):
        for xx in (10, 11, 12):
            F.set(xx, 3, zz, B("purple_carpet") if xx == 11 else B("magenta_carpet"))
    F.fill(8, 3, 1, 14, 3, 4, qb)
    for xx in range(8, 15):
        F.stairs(xx, 3, 5, "quartz", "N")
    F.set(11, 4, 2, B("lodestone"))
    F.set(11, 5, 2, B("amethyst_cluster", block_face="up"))
    for xx in (9, 13):
        F.set(xx, 4, 2, pillar)
        F.set(xx, 5, 2, pillar)
        F.set(xx, 6, 2, B("end_rod", facing_direction=1))
        F.set(xx, 4, 4, B("amethyst_block"))
        F.set(xx, 5, 4, B("amethyst_cluster", block_face="up"))
    F.put(11, 4, 4, B("lectern", cardinal_direction=card(F, "S")), None)
    # great stained window behind the altar
    cols = ["purple", "magenta", "cyan", "light_blue", "cyan", "magenta", "purple"]
    for i, xx in enumerate(range(8, 15)):
        for y in range(5, 11):
            if y == 10 and i in (0, 6):
                continue
            F.set(xx, y, 0, B(cols[i] + "_stained_glass"))
    F.sign(11, 9, zc + 1, "S", "§5§l차원문 신전\n§r발판을 밟아\n던전으로 이동", wood="dark_oak", glow=True)
    return F


# ---------------------------------------------------------------------------
# guild hall + inn
# ---------------------------------------------------------------------------

def guild_hall(w, x, z, face):
    W, D = 33, 19
    F = Frame.box(w, x, G, z, W, D, face)
    rng = F.rng
    pal = houses.palette("copper")
    info = houses.shell(F, W, D, floors=2, pal=pal, jetty=True, roof_axis="x", door_x=16, dormer=True,
                        chimney=("W", 8), sign="§l모험가 길드", ground_back_windows=False,
                        no_window=(("E", 0, 0), ("E", 1, 0)))
    fy = info["fy"]
    panel = bl.planks("dark_oak")
    # sell counter along the back wall
    F.fill(1, 2, 2, W - 9, 5, 2, panel)
    xs = list(range(3, W - 10, 2))
    for xx in range(2, W - 8, 2):
        for y in range(2, 6):
            F.log(xx, y, 2, "dark_oak")
    F.fill(W - 9, 2, 1, W - 9, 5, 2, panel)
    for (sid, label, item, cnt, gold), xx in zip(SELLS, xs):
        text = "§l%s\n§r판매 → §6%d 골드" % (label, gold)
        sale_slot(F, xx, 3, 2, "S", text, "function bear/sell/" + sid, panel, deco=bl.barrel("S"))
        F.set(xx, 5, 2, B("glowstone"))
    left = SELLS[len(xs):]
    for i, (sid, label, item, cnt, gold) in enumerate(left):
        zz = 5 + 2 * i
        F.fill(W - 3, 2, zz - 1, W - 3, 5, zz + 1, panel)
        sale_slot(F, W - 3, 3, zz, "W", "§l%s\n§r판매 → §6%d 골드" % (label, gold), "function bear/sell/" + sid,
                  panel, deco=bl.barrel("W"))
    F.sign(16, 5, 3, "S", "§6§l전리품 매입소\n§r버튼을 누르면\n판매됩니다", wood="dark_oak", glow=True)
    # quest board on the west wall
    board = [("§l§n의뢰 게시판", "§r던전을 정복하고\n보상을 받으세요")]
    for did, (nm, gold, rec, colr) in DUNGEONS.items():
        a, b_ = nm.split(" · ")
        board.append(("%s§l%s" % (colr, a), "§r%s\n§6보상 %d 골드\n§8%s" % (b_, gold, rec)))
    for i, (t1, t2) in enumerate(board):
        zz = 4 + i + (1 if i >= 4 else 0)
        if zz in (8, 9):
            zz += 3
        F.set(1, 3 + (i % 2), zz, bl.planks("spruce")) if False else None
    bz = [12, 13, 14, 15, 16]
    k = 0
    for row in (4, 3):
        for zz in bz:
            if k < len(board):
                F.sign(1, row, zz, "E", board[k][0] + "\n" + board[k][1], wood="birch")
                k += 1
    # lounge
    for (tx, tz) in ((7, 9), (13, 9), (19, 9), (7, 14), (13, 14)):
        kit.table(F, tx, 2, tz, "dark_oak")
        F.stairs(tx - 1, 2, tz, "spruce", "W")
        F.stairs(tx + 1, 2, tz, "spruce", "E")
    for xx in range(4, W - 4):
        for zz in (5, 6):
            F.set(xx, 2, zz, B("cyan_carpet"), keep=True)
    for (lx, lz) in ((6, 7), (16, 7), (26, 7), (6, 13), (16, 13), (26, 13)):
        kit.chandelier(F, lx, 5, lz, drop=1) if False else F.lantern(lx, 5, lz, hanging=True)
    houses.stairwell(F, info, 20, D - 2, 1, 0)
    # upper floor: library + map room
    uy = fy[1] + 1
    zf = info["zf"][1] - 1
    for xx in range(2, 14, 3):
        for zz in range(3, 9):
            F.set(xx, uy, zz, B("bookshelf"))
            F.set(xx, uy + 1, zz, B("bookshelf"))
            F.set(xx, uy + 2, zz, B("bookshelf") if rng.random() < 0.6 else AIR)
    F.set(8, uy, 12, B("enchanting_table"))
    for xx in (20, 21, 22, 23):
        F.set(xx, uy, 6, bl.block("dark_oak"))
        F.set(xx, uy + 1, 6, B("green_carpet"))
    F.set(21, uy, 5, bl.stairs("spruce", F.d("S")))
    F.set(22, uy, 7, bl.stairs("spruce", F.d("N")))
    F.set(W - 2, uy, 3, B("cartography_table"))
    F.set(W - 2, uy, 4, B("lectern", cardinal_direction=card(F, "W")))
    F.chest(W - 2, uy, 6, "W", [bl.item("map", 1), bl.item("compass", 1), bl.item("book", 3)])
    for (lx, lz) in ((8, 10), (22, 10), (15, 4)):
        F.lantern(lx, fy[2] - 1, lz, hanging=True)
    for xx in range(15, 28):
        for zz in range(9, 13):
            F.set(xx, uy, zz, B("red_carpet"), keep=True)
    # porch with balcony
    dx_ = info["door_x"]
    for px in (dx_ - 3, dx_ + 3):
        F.set(px, 1, D + 2, bl.block("stone_brick"))
        for y in range(2, 6):
            F.log(px, y, D + 2, "dark_oak")
    for xx in range(dx_ - 3, dx_ + 4):
        F.set(xx, 6, D + 1, bl.planks("dark_oak"))
        F.set(xx, 6, D + 2, bl.planks("dark_oak"))
        F.set(xx, 7, D + 2, bl.fence("dark_oak"))
        F.set(xx, 1, D + 1, bl.block("stone_brick"), keep=True)
        F.set(xx, 1, D + 2, bl.block("stone_brick"), keep=True)
        F.stairs(xx, 1, D + 3, "stone_brick", "N")
    F.set(dx_ - 3, 7, D + 1, bl.fence("dark_oak"))
    F.set(dx_ + 3, 7, D + 1, bl.fence("dark_oak"))
    F.stairs(dx_, 1, D, "stone_brick", "N") if False else F.set(dx_, 1, D, bl.block("stone_brick"))
    F.set(dx_ - 1, 1, D, bl.block("stone_brick"))
    F.set(dx_ + 1, 1, D, bl.block("stone_brick"))
    for px in (dx_ - 2, dx_ + 2):
        F.banner(px, 9, D + 1, "S", 6) if False else None
    F.banner(dx_ - 5, 9, D + 1, "S", 6)
    F.banner(dx_ + 5, 9, D + 1, "S", 6)
    F.banner(dx_ - 9, 9, D + 1, "S", 11)
    F.banner(dx_ + 9, 9, D + 1, "S", 11)
    F.sign(dx_, 5, D + 3, "S", "§3§l모험가 길드\n§r전리품 매입\n의뢰 게시판", wood="dark_oak", glow=True)
    F.set(dx_, 6, D + 3, bl.slab("dark_oak", top=True)) if False else None
    # bell tower at the east end rising through the roof
    tx0, tz0 = W - 7, 0
    tm = wall_mix()
    F.fill(tx0, 1, tz0, W - 1, 24, tz0 + 6, tm)
    F.fill(tx0 + 1, 2, tz0 + 1, W - 2, 23, tz0 + 5, AIR)
    for fyy in (6, 11, 16, 20):
        F.fill(tx0 + 1, fyy, tz0 + 1, W - 2, fyy, tz0 + 5, bl.planks("spruce"))
        F.set(tx0 + 1, fyy, tz0 + 1, bl.ladder(F.d("E")))
    for y in range(2, 21):
        F.set(tx0 + 1, y, tz0 + 1, bl.ladder(F.d("E")))
    for y in (2, 3):
        F.set(tx0, y, tz0 + 3, AIR)
    for y in (7, 8):
        F.set(tx0, y, tz0 + 3, AIR)
    # belfry openings
    for y in (21, 22, 23):
        for k in (2, 3, 4):
            F.set(tx0 + k, y, tz0, AIR)
            F.set(tx0 + k, y, tz0 + 6, AIR)
            F.set(tx0, y, tz0 + k, AIR)
            F.set(W - 1, y, tz0 + k, AIR)
    for k, (a, b_) in enumerate((("W", "E"), ("N", "S"))):
        pass
    for (xx, zz, da, db) in ((tx0 + 2, tz0, "W", "E"), (tx0 + 2, tz0 + 6, "W", "E")):
        F.stairs(xx, 23, zz, "stone_brick", "W", top=True)
        F.stairs(xx + 2, 23, zz, "stone_brick", "E", top=True)
    for (xx, zz) in ((tx0, tz0 + 2), (W - 1, tz0 + 2)):
        F.stairs(xx, 23, zz, "stone_brick", "N", top=True)
        F.stairs(xx, 23, zz + 2, "stone_brick", "S", top=True)
    F.set(tx0 + 3, 23, tz0 + 3, B("bell", attachment="hanging", direction=0))
    F.set(tx0 + 3, 24, tz0 + 3, bl.block("dark_oak"))
    for xx in range(tx0 - 1, W + 1):
        F.stairs(xx, 24, tz0 - 1, "stone_brick", "S", top=True)
        F.stairs(xx, 24, tz0 + 7, "stone_brick", "N", top=True)
    for zz in range(tz0, tz0 + 7):
        F.stairs(tx0 - 1, 24, zz, "stone_brick", "E", top=True)
        F.stairs(W, 24, zz, "stone_brick", "W", top=True)
    t = kit.hip_roof(F, tx0 - 1, tz0 - 1, W, tz0 + 7, 25, "waxed_oxidized_cut_copper", overhang=0,
                     cap="waxed_oxidized_cut_copper")
    F.set(tx0 + 3, t, tz0 + 3, B("waxed_oxidized_copper"))
    F.set(tx0 + 3, t + 1, tz0 + 3, B("lightning_rod", facing_direction=1))
    for y in (13, 14):
        F.set(tx0 + 3, y, tz0 + 6, B("glass_pane"))
        F.set(W - 1, y, tz0 + 3, B("glass_pane"))
    return info


def inn(w, x, z, face):
    W, D = 31, 15
    F = Frame.box(w, x, G, z, W, D, face)
    rng = F.rng
    pal = houses.palette("spruce")
    pal["roof"] = "dark_oak"
    info = houses.shell(F, W, D, floors=3, pal=pal, jetty=True, roof_axis="x", door_x=15, dormer=True,
                        chimney=("E", 5), sign="§l곰발바닥 여관")
    fy = info["fy"]
    # bar
    for xx in range(2, 11):
        F.set(xx, 2, 4, bl.planks("dark_oak"))
        F.set(xx, 3, 4, bl.slab("spruce")) if False else None
    for zz in (2, 3):
        F.set(10, 2, zz, bl.planks("dark_oak"))
    for xx in range(2, 10, 2):
        F.set(xx, 2, 1, bl.barrel("S"))
        F.set(xx, 3, 1, bl.barrel("S"))
        F.set(xx + 1, 2, 1, B("bookshelf"))
        F.set(xx + 1, 3, 1, bl.barrel("U"))
    F.set(3, 3, 4, B("brewing_stand"))
    F.set(6, 3, 4, B("cake"))
    F.set(9, 3, 4, bl.lantern())
    for xx in (3, 5, 7, 9):
        F.stairs(xx, 2, 5, "spruce", "N")
    # tables
    for (tx, tz) in ((5, 9), (11, 9), (19, 5), (24, 5), (19, 10), (24, 10)):
        kit.table(F, tx, 2, tz, "spruce")
        F.stairs(tx - 1, 2, tz, "spruce", "W")
        F.stairs(tx + 1, 2, tz, "spruce", "E")
        if rng.random() < 0.5:
            F.stairs(tx, 2, tz - 1, "spruce", "N")
    for (lx, lz) in ((5, 7), (13, 7), (21, 7), (26, 11)):
        F.lantern(lx, 5, lz, hanging=True)
    for xx in range(13, 18):
        for zz in range(8, D - 1):
            F.set(xx, 2, zz, B("red_carpet"), keep=True)
    F.sign(14, 3, D - 2, "N", "§l곰발바닥 여관\n§r2·3층 객실에서\n쉬어 가세요", wood="spruce")
    houses.stairwell(F, info, 22, 1, 1, 0)
    houses.stairwell(F, info, 8, 1, 1, 1)
    # guest rooms on floors 1 and 2
    for k in (1, 2):
        uy = fy[k] + 1
        zf = info["zf"][k]
        wallb = bl.planks("spruce")
        F.fill(1, uy, 6, W - 2, uy + 3, 6, wallb)
        xs = [2, 8, 14, 20, 26] if k == 1 else [14, 20, 26]
        for i, x0 in enumerate(xs):
            if x0 + 5 < W - 1:
                F.fill(x0 + 5, uy, 7, x0 + 5, uy + 3, zf - 1, wallb)
            F.set(x0 + 2, uy, 6, AIR)
            F.set(x0 + 2, uy + 1, 6, AIR)
            F.door(x0 + 2, uy, 6, "spruce", "S")
            F.bed(x0 + 1, uy, zf - 2, "S", int(rng.integers(0, 16)))
            F.chest(x0 + 3, uy, zf - 1, "N", [])
            F.set(x0 + 4, uy, zf - 1, B("bookshelf")) if x0 + 4 < W - 1 else None
            F.lantern(x0 + 2, fy[k + 1] - 1, 9, hanging=True)
            for xx in range(x0, min(x0 + 5, W - 1)):
                for zz in range(8, zf - 2):
                    F.set(xx, uy, zz, B(["green", "blue", "purple", "cyan", "orange"][i % 5] + "_carpet"), keep=True)
        for xx in range(2, W - 2, 6):
            F.lantern(xx, fy[k + 1] - 1, 3, hanging=True)
    return info


def stable(w, x, z, face):
    """Open timber stable 19x10."""
    W, D = 19, 10
    F = Frame.box(w, x, G, z, W, D, face)
    F.fill(0, 0, 0, W - 1, 0, D - 1, Mix((B("dirt", dirt_type="coarse"), 3), (B("grass_path"), 3), (B("hay_block"), 1)))
    F.fill(0, 1, 0, W - 1, 12, D - 1, AIR)
    for xx in range(0, W, 6):
        for zz in (0, D - 1):
            F.set(xx, 1, zz, bl.block("stone_brick"))
            for y in range(2, 5):
                F.log(xx, y, zz, "spruce")
        for zz in range(0, D):
            F.log(xx, 5, zz, "spruce", "z")
    for xx in range(0, W):
        F.log(xx, 5, 0, "spruce", "x")
        F.log(xx, 5, D - 1, "spruce", "x")
        for y in range(1, 5):
            F.set(xx, y, 0, bl.planks("spruce") if y < 3 else (bl.fence("spruce") if xx % 6 else bl.log("spruce")),
                  keep=True)
    for xx in range(0, W, 6):
        for zz in range(1, 6):
            F.set(xx, 1, zz, bl.fence("spruce"))
            F.set(xx, 2, zz, bl.fence("spruce")) if zz < 3 else None
    for xx in (3, 9, 15):
        F.set(xx, 1, 1, B("hay_block"))
        F.set(xx - 1, 1, 1, B("hay_block"))
        F.set(xx, 2, 1, B("hay_block")) if xx != 9 else None
        F.set(xx + 1, 1, 2, B("cauldron", cauldron_liquid="water", fill_level=6))
        F.set(xx, 1, 6, bl.gate("spruce", F.d("S")))
        F.set(xx - 1, 1, 6, bl.fence("spruce"))
        F.set(xx - 2, 1, 6, bl.fence("spruce"))
        F.set(xx + 1, 1, 6, bl.fence("spruce"))
        F.set(xx + 2, 1, 6, bl.fence("spruce"))
        F.lantern(xx, 4, 3, hanging=True)
    kit.gable_roof(F, 0, 0, W - 1, D - 1, 6, "spruce", axis="x", overhang=1, trim="dark_oak", gable=bl.planks("spruce"))
    F.sign(9, 4, D, "S", "§l마구간", wood="spruce")


# ---------------------------------------------------------------------------
# park
# ---------------------------------------------------------------------------

def _ell(F, cx, cy, cz, rx, ry, rz, b):
    wx, wy, wz = F.p(cx, cy, cz)
    if F.rot % 2:
        rx, rz = rz, rx
    F.w.ellipsoid(wx, wy, wz, rx, ry, rz, b)


def bear_statue(F, x, y, z):
    """Seated bear mascot facing local south, ~11 blocks tall on a plinth."""
    fur = Mix((B("brown_terracotta"), 5), (B("brown_concrete_powder"), 2), (B("brown_wool"), 1))
    tan = B("yellow_terracotta") if False else B("hardened_clay")
    cream = B("white_terracotta")
    black = B("black_concrete")
    S = F.sub(x, y, z)
    S.fill(-5, 0, -4, 5, 0, 6, bl.block("stone_brick"))
    S.fill(-4, 1, -3, 4, 1, 5, bl.block("polished_andesite"))
    for xx in range(-5, 6):
        S.stairs(xx, 1, -4, "stone_brick", "S")
        S.stairs(xx, 1, 6, "stone_brick", "N")
    for zz in range(-3, 6):
        S.stairs(-5, 1, zz, "stone_brick", "E")
        S.stairs(5, 1, zz, "stone_brick", "W")
    by = 2
    _ell(S, 0, by + 3.2, 0, 3.4, 3.6, 3.0, fur)            # body
    _ell(S, 0, by + 2.8, 1.6, 2.2, 2.6, 1.9, tan)          # belly
    _ell(S, 0, by + 8.0, 0.4, 2.7, 2.5, 2.6, fur)          # head
    _ell(S, -2.2, by + 10.3, 0.2, 1.1, 1.1, 0.9, fur)      # ears
    _ell(S, 2.2, by + 10.3, 0.2, 1.1, 1.1, 0.9, fur)
    _ell(S, 0, by + 7.3, 2.7, 1.4, 1.1, 1.1, cream)        # muzzle
    S.set(0, by + 8, 4, black)                             # nose
    S.set(-1, by + 9, 3, black)                            # eyes
    S.set(1, by + 9, 3, black)
    _ell(S, -3.3, by + 4.4, 1.2, 1.1, 2.0, 1.4, fur)       # arms
    _ell(S, 3.3, by + 4.4, 1.2, 1.1, 2.0, 1.4, fur)
    _ell(S, -2.3, by + 0.8, 2.8, 1.4, 1.2, 2.2, fur)       # legs
    _ell(S, 2.3, by + 0.8, 2.8, 1.4, 1.2, 2.2, fur)
    for sx in (-2, 2):
        S.set(sx, by + 1, 5, B("pink_terracotta"))
        S.set(sx + (1 if sx < 0 else -1), by + 1, 5, B("pink_terracotta")) if False else None
    S.set(-2, by, 5, cream)
    S.set(2, by, 5, cream)
    S.sign(0, 1, 7, "S", "§6§l베어 타운\n§r마을의 수호신\n곰돌이 동상", wood="dark_oak", standing=True)


def park(w, x0, z0, x1, z1):
    rng = w.rng
    F = Frame(w, 0, G, 0, 0)
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    w.fill(x0, G, z0, x1, G, z1, B("grass_block"))
    # hedge border with openings in the middle of each side
    for xx in range(x0, x1 + 1):
        for zz in (z0, z1):
            if abs(xx - cx) > 2:
                w.set(xx, G + 1, zz, bl.leaves("oak"))
    for zz in range(z0, z1 + 1):
        for xx in (x0, x1):
            if abs(zz - cz) > 2:
                w.set(xx, G + 1, zz, bl.leaves("oak"))
    # paths (cross) + ring around the statue
    pm = Mix((B("gravel"), 4), (B("grass_path"), 4), (bl.block("cobblestone"), 1))
    w.fill(cx - 1, G, z0, cx + 1, G, z1, pm)
    w.fill(x0, G, cz - 1, x1, G, cz + 1, pm)
    for (dx, dz) in kit.disc_cells(8.5):
        w.set(cx + dx, G, cz + dz, pm if math.hypot(dx, dz) > 6.2 else bl.block("stone_brick"))
    bear_statue(F, cx, 1, cz - 1)
    # pond in the south-west corner
    px, pz = x0 + 8, z1 - 8
    for (dx, dz) in kit.disc_cells(5.5):
        d = math.hypot(dx * 0.85, dz)
        if d <= 4.6:
            w.set(px + dx, G, pz + dz, bl.WATER)
            w.set(px + dx, G - 1, pz + dz, bl.WATER if d < 3.2 else B("clay"))
            w.set(px + dx, G - 2, pz + dz, B("clay"))
            if rng.random() < 0.12:
                w.set(px + dx, G + 1, pz + dz, B("waterlily"))
        elif d <= 5.5:
            w.set(px + dx, G, pz + dz, Mix((bl.block("mossy_cobblestone"), 2), (B("stone"), 1), (B("grass_block"), 2)))
            if rng.random() < 0.3:
                w.set(px + dx, G + 1, pz + dz, B("reeds", age=0))
    # trees, flower beds, benches, lamps
    for (tx, tz, kind) in ((x0 + 6, z0 + 6, "cherry"), (x1 - 6, z0 + 6, "big"), (x1 - 6, z1 - 6, "cherry"),
                           (x0 + 5, cz + 6, "birch"), (x1 - 5, cz - 6, "oak")):
        if kind == "cherry":
            kit.tree_cherry(w, tx, G + 1, tz, rng)
        elif kind == "big":
            kit.tree_big(w, tx, G + 1, tz, rng, h=9)
        elif kind == "birch":
            kit.tree_birch(w, tx, G + 1, tz, rng)
        else:
            kit.tree_oak(w, tx, G + 1, tz, rng)
    for (bx, bz) in ((cx - 10, z0 + 3), (cx + 6, z0 + 3), (cx - 10, z1 - 3), (cx + 6, z1 - 3)):
        for xx in range(bx, bx + 5):
            for zz in (bz - 1, bz, bz + 1):
                if w.get(xx, G + 1, zz) == 0 and w.get(xx, G, zz) == B("grass_block"):
                    w.set(xx, G + 1, zz, kit.flowers(rng))
    kit.bench(F, cx + 4, 1, cz - 11, 3, "S", "spruce")
    kit.bench(F, cx - 7, 1, cz - 11, 3, "S", "spruce")
    kit.bench(F, cx + 4, 1, cz + 10, 3, "N", "spruce")
    kit.bench(F, cx - 7, 1, cz + 10, 3, "N", "spruce")
    for (lx, lz) in ((cx - 3, z0 + 1), (cx + 3, z0 + 1), (cx - 3, z1 - 1), (cx + 3, z1 - 1), (x0 + 1, cz - 3),
                     (x0 + 1, cz + 3), (x1 - 1, cz - 3), (x1 - 1, cz + 3)):
        kit.lamp_post(F, lx, 1, lz, h=4, wall_mat="stone_brick", wood="dark_oak")


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

HOUSES = [
    # x, z, W, D, face, palette, floors, kwargs
    (-68, -17, 13, 11, "S", "moss", 2, dict(chimney=("W", 3))),
    (-44, -63, 13, 11, "S", "red", 2, dict(dormer=True)),
    (-64, -65, 13, 13, "S", "oak", 2, dict(chimney=("W", 4), roof_axis="z")),
    (-68, -41, 15, 11, "E", "spruce", 2, dict(dormer=True)),
    (32, -63, 13, 11, "S", "brick", 2, dict(chimney=("E", 3))),
    (50, -65, 13, 13, "S", "cherry", 2, dict(roof_axis="z")),
    (6, 52, 17, 15, "W", "dark", 3, dict(chimney=("W", 5), dormer=True)),
    (32, 52, 13, 11, "N", "oak", 2, dict(dormer=True)),
    (50, 52, 13, 13, "N", "red", 2, dict(chimney=("E", 4), roof_axis="z")),
    (-22, 30, 17, 15, "E", "brick", 2, dict(chimney=("E", 5), dormer=True)),
    (-20, 52, 15, 13, "E", "spruce", 2, dict(dormer=True)),
    (-44, 52, 13, 11, "N", "moss", 2, dict(chimney=("W", 3))),
    (-64, 52, 13, 13, "N", "cherry", 2, dict(roof_axis="z")),
    (-68, 7, 11, 11, "N", "dark", 2, dict(roof_axis="z")),
    (64, -41, 9, 11, "W", "moss", 2, dict(roof_axis="z")),
]


def build_town(w, T, log=print):
    rng = w.rng
    shops_at = {
        "weapon": (-22, -45, "E"), "armor": (-22, -70, "E"), "tool": (6, -45, "W"), "magic": (6, -70, "W"),
        "food": (6, 30, "W"),
    }
    for kind, (x, z, f) in shops_at.items():
        shop(w, x, z, f, kind)
    log("  shops done")
    warp_shrine(w, -52, -40, "S")
    guild_hall(w, 30, -27, "S")
    inn(w, 30, 8, "N")
    stable(w, 34, 28, "N")
    log("  landmarks done")
    for (x, z, W, D, f, palname, floors, kw) in HOUSES:
        bw, bd = (W, D)
        F = Frame.box(w, x, G, z, bw, bd, f)
        info = houses.shell(F, W, D, floors=floors, pal=houses.palette(palname), **kw)
        houses.furnish_home(F, info)
    park(w, -56, 9, -29, 45)
    greenery(w)


def greenery(w):
    """Street lamps, trees and gardens in the leftover town space."""
    rng = w.rng
    F = Frame(w, 0, G, 0, 0)
    grass = B("grass_block")
    # avenue lamps
    for s in range(34, 70, 12):
        for sgn in (-1, 1):
            kit.lamp_arm(F, 5, 1, sgn * s, "W", h=4)
            kit.lamp_arm(F, -5, 1, sgn * s, "E", h=4)
            kit.lamp_arm(F, sgn * s, 1, 5, "N", h=4)
            kit.lamp_arm(F, sgn * s, 1, -5, "S", h=4)
    # scatter trees / bushes / flowers on free grass
    def free(x, z, r):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if w.get(x + dx, G, z + dz) != grass or w.get(x + dx, G + 1, z + dz) != 0:
                    return False
                if w.get(x + dx, G + 4, z + dz) != 0 or w.get(x + dx, G + 8, z + dz) != 0:
                    return False
        return True
    placed = []
    for _ in range(900):
        x, z = int(rng.integers(-70, 71)), int(rng.integers(-70, 71))
        if not free(x, z, 3):
            continue
        if any(abs(x - px) < 7 and abs(z - pz) < 7 for px, pz in placed):
            continue
        r = rng.random()
        if r < 0.35:
            kit.tree_oak(w, x, G + 1, z, rng, h=int(rng.integers(5, 7)))
        elif r < 0.6:
            kit.tree_birch(w, x, G + 1, z, rng)
        elif r < 0.8:
            kit.tree_cherry(w, x, G + 1, z, rng)
        else:
            kit.tree_big(w, x, G + 1, z, rng, h=int(rng.integers(8, 10)), spread=4)
        placed.append((x, z))
    for _ in range(2600):
        x, z = int(rng.integers(-72, 73)), int(rng.integers(-72, 73))
        if w.get(x, G, z) == grass and w.get(x, G + 1, z) == 0:
            r = rng.random()
            if r < 0.5:
                w.set(x, G + 1, z, B("short_grass"))
            elif r < 0.85:
                w.set(x, G + 1, z, kit.flowers(rng))
            elif r < 0.93:
                kit.bush(w, x, G + 1, z, rng, "azalea" if rng.random() < 0.5 else "oak")
            else:
                w.set(x, G + 1, z, B("fern"))
