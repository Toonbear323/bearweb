"""Hub island: the ability-tag lobby rebuilt as the skygen spawn (whole island = safe zone).

Inside the hall: 8 shop stalls (one category each, an NPC opens the shop window), the gallery gates now
teleport to the islands, the stage NPC explains the rules, ender chests in the foyer.
Outside: a floating garden island with a plaza in front of the opened south entrance, a ring path around
the hall and four bridgeheads (north forest, east space ship, west library, south residential island).
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt

import gen_lobby
from gen_lobby import Lobby, P, FY, ROOF, SPAWN, STALL_Z, GATE_Z, FOUNTAIN
from mcw import B, AIR, simple_be, sign_be, flowerpot_be, banner_be
from gen_common import (stair, slab, lamp_post, hanging_lamp, wall_sign, standing_sign, leaf_blob, leaves_of,
                        oak_tree, cherry_tree, birch_tree, big_oak, bush, fbm, superdist, FLOWERS, TALL_FLOWERS,
                        tall_plant)
from sky_world import shape_island
from sky_islands import solidify_below, under_rock

# the eight stalls keep their ability themes (colours, props); each becomes one shop category
SHOPS = [
    dict(key="speed", shop="sell", name="광물 판매소", color="§b", sub="채굴한 광물을 팔아요", desc="§f모두 팔기 지원"),
    dict(key="jump", shop="living", name="생활 용품", color="§a", sub="화로 · 상자 · 침대", desc="§f집 꾸미기 필수품"),
    dict(key="invis", shop="build", name="건축 블록", color="§7", sub="돌 · 나무 · 유리", desc="§f집터에 쓸 블록"),
    dict(key="feather", shop="deco", name="장식 블록", color="§d", sub="양털 · 테라코타 · 꽃", desc="§f알록달록 장식"),
    dict(key="owl", shop="magic", name="인첸트 재료", color="§9", sub="청금석 · 경험치 병", desc="§f마법 도서관에서 사용"),
    dict(key="mermaid", shop="tools", name="도구 상점", color="§3", sub="곡괭이 · 도끼 · 삽", desc="§f좋은 도구로 빨리 캐기"),
    dict(key="berserk", shop="combat", name="무기 · 갑옷", color="§c", sub="검 · 활 · 갑옷", desc="§f밤의 PvP 대비"),
    dict(key="hunter", shop="food", name="음식 상점", color="§6", sub="빵 · 스테이크 · 황금사과", desc="§f배고프면 체력이 안 차요"),
]
for s in SHOPS:
    s.update(price=0)
gen_lobby.ABILITIES[:] = SHOPS

# gallery gates (same order and slots as the tag-map gallery; the factory slot becomes "my plot")
GATES = [
    ("forest", "forest", "§l§a1. 숲 섬", "§f나무 · 돌 채집"),
    ("volcano", "volcano", "§l§c2. 화산 섬", "§f금 · 다이아몬드"),
    ("paradise", "paradise", "§l§b3. 주거 섬", "§f집터 · 집터 사무소"),
    ("home", "factory", "§l§e4. 내 집터", "§f내 집으로 바로 이동"),
    ("skeld", "skeld", "§l§75. 우주 광산선", "§f석탄 · 철 · 화로방"),
    ("library", "library", "§l§d6. 마법 도서관", "§f인첸트 · 수리"),
]

HUB_C = (6, 8)
HUB_RX, HUB_RZ = 104, 100
BRIDGEHEADS = {"forest": (0, -92, "N"), "skeld": (110, 0, "E"), "library": (-98, 0, "W"), "paradise": (0, 108, "S")}
G = 63                     # outdoor ground surface (= hall floor block level)


def hall_mask(X, Z):
    return ((np.abs(X) <= 60) & (np.abs(Z) <= 50)) | ((X >= 58) & (X <= 73) & (Z >= -31) & (Z <= 48))


class SkyLobby(Lobby):
    def __init__(self):
        super().__init__()
        self.gates = []          # dict(key, box)
        self.ender = []

    # ------------------------------------------------------------------ title
    def title(self):
        a = self.a
        f = ImageFont.truetype("/usr/share/fonts/opentype/unifont/unifont.otf", 16)
        text = "스카이젠"
        l, t, r, b = f.getbbox(text)
        im = Image.new("1", (r + 2, 18), 0)
        ImageDraw.Draw(im).text((0, 0), text, font=f, fill=1)
        px = np.array(im)[2:16, :r]
        bold = px.copy()
        bold[:, 1:] |= px[:, :-1]
        h, w = bold.shape
        x0 = -(w // 2)
        ytop, z = 90, -48
        a.fill(x0 - 3, ytop - h - 1, z, x0 + w + 2, ytop + 2, z, B("polished_blackstone"))
        for x in range(x0 - 3, x0 + w + 3):
            a.set(x, ytop + 2, z, B("gold_block"))
            a.set(x, ytop - h - 1, z, B("gold_block"))
        for y in range(ytop - h - 1, ytop + 3):
            a.set(x0 - 3, y, z, B("gold_block"))
            a.set(x0 + w + 2, y, z, B("gold_block"))
        glow, shadow = B("sea_lantern"), B("blue_concrete")
        for row in range(h):
            for col in range(w):
                y, x = ytop - row, x0 + col
                if bold[row, col]:
                    a.set(x, y, z, glow)
                elif row > 0 and col > 0 and bold[row - 1, col - 1]:
                    a.set(x, y, z, shadow)

    # ------------------------------------------------------------------ stage: the guide NPC
    def stage(self):
        super().stage()
        a = self.a
        for n in self.npcs:
            if n["tag"] == "start_npc":
                n.update(name="§l§b스카이젠 안내원", tag="sky_guide", kind="guide")
        a.add_be(sign_be(0, 73, -41, "§l§b스카이젠 안내\n§r§f안내원을 누르면\n§f규칙과 메뉴가 나와요",
                         back="§l§b스카이젠 안내", hanging=True))

    # ------------------------------------------------------------------ shops
    def shop(self):
        super().shop()
        a = self.a
        for zg in (-29, 46):
            a.add_be(sign_be(-43, 71, zg, "§l§6★ 스카이젠 상점가 ★\n§r§f상인을 눌러\n§f사고 팔 수 있어요",
                             back="§l§6★ 스카이젠 상점가 ★", hanging=True))
        for i, s in enumerate(SHOPS):
            zc = STALL_Z[i % 4]
            back_x, face = (-57, 1) if i < 4 else (-29, -1)
            fx = back_x + face * 6
            fd = 5 if face > 0 else 4
            wall_sign(a, fx, 73, zc, fd, "%s§l%s\n§r§f%s" % (s["color"], s["name"], s["sub"]), kind="dark_oak_wall_sign")
            wall_sign(a, fx, 72, zc, fd, "%s\n§7상인을 눌러 주세요" % s["desc"], kind="dark_oak_wall_sign")
        for n in self.npcs:
            if n["tag"].startswith("shop_"):
                key = n["tag"][5:]
                s = next(s for s in SHOPS if s["key"] == key)
                n.update(name="%s§l%s" % (s["color"], s["name"]), tag="sky_shop_" + s["shop"], kind="shop",
                         shop=s["shop"])

    # ------------------------------------------------------------------ gallery: teleport gates
    def gallery(self):
        a = self.a
        for (dest, style, title, sub), zc in zip(GATES, GATE_Z):
            if style == "factory":
                self.home_diorama(zc)
            else:
                self.diorama(style, zc)
            self.gate2(dest, style, zc, title, sub)
        for zc in GATE_Z:
            for dz in (-2, -1, 0, 1, 2):
                a.set(46, P, zc + dz, stair("dark_oak_stairs", "west"))
            a.set(43, P, zc, B("dark_oak_fence"))
            a.set(43, P + 1, zc, B("dark_oak_fence"))
            a.set(43, P + 2, zc, slab("dark_oak_slab"))
            a.set(43, P + 3, zc, B("lantern"))
            for dz in (-4, 4):
                a.set(46, P, zc + dz, B("flower_pot"))
                a.add_be(flowerpot_be(46, P, zc + dz, "fern"))
            for x in range(40, 48):
                for dz in range(-3, 4):
                    if a.get(x, P, zc + dz) == AIR:
                        a.set(x, P, zc + dz, B("purple_carpet") if (x in (40, 47) or dz in (-3, 3)) else B("black_carpet"))
        for z in range(-27, 47, 6):
            hanging_lamp(a, 34, 75, z, 6)
            hanging_lamp(a, 26, 75, z + 3, 7)
            hanging_lamp(a, 52, 75, z + 3, 6)
        a.fill(36, P + 1, 47, 50, P + 5, 47, B("dark_oak_planks"))
        a.fill(36, P + 6, 47, 50, P + 6, 47, B("stripped_dark_oak_log", axis="x"))
        a.fill(36, P, 47, 50, P, 47, B("stripped_dark_oak_log", axis="x"))
        notes = [
            "§l§e낮 (05~19시)\n§r§fPvP 불가\n§f인벤토리 보호",
            "§l§c밤 (19~05시)\n§r§fPvP 가능\n§f죽으면 아이템 드롭",
            "§l§a안전구역\n§r§f허브 · 주거 섬\n§f마법 도서관",
            "§l§b섬 이동\n§r§f문 앞 빛나는 바닥에\n§f서면 이동해요",
            "§l§4보안\n§r§f남의 집터 침입 핵\n§f= 자동 영구밴",
        ]
        for i, t in enumerate(notes):
            wall_sign(a, 37 + i * 3, P + 3, 46, 2, t, kind="dark_oak_wall_sign")
        for x in (35, 51):
            lamp_post(a, x, P, 46, B("dark_oak_fence"), B("lantern"), height=3)
        for z in (-12, 6, 24):
            a.fill(27, P, z - 1, 29, P, z + 1, B("polished_blackstone_bricks"))
            a.fill(28, P, z, 28, P, z, B("moss_block"))
            for i in range(1, 4):
                a.set(28, P + i, z, B("cherry_log", axis="y"))
            leaf_blob(a, 28, P + 4.5, z, 2.4, leaves_of("cherry"), self.rng, flat=0.7)
        a.set(31, P, 41, B("dark_oak_planks"))
        standing_sign(a, 31, P + 1, 41, 8, "§l§b섬 이동 갤러리\n§r§f문 앞 빛나는 바닥에\n§f서면 바로 이동",
                      kind="dark_oak_standing_sign")

    def gate2(self, dest, key, zc, title, sub):
        a = self.a
        styles = {
            "forest": (B("mossy_stone_bricks"), B("oak_log"), B("oak_leaves", persistent_bit=1), "mossy_stone_brick_stairs"),
            "volcano": (B("polished_blackstone_bricks"), B("magma"), B("red_nether_brick"), "polished_blackstone_brick_stairs"),
            "paradise": (B("prismarine_bricks"), B("smooth_sandstone"), B("sea_lantern"), "prismarine_bricks_stairs"),
            "factory": (B("bricks"), B("stripped_oak_log", axis="y"), B("gold_block"), "brick_stairs"),
            "skeld": (B("light_gray_concrete"), B("black_concrete"), B("red_concrete"), "polished_andesite_stairs"),
            "library": (B("dark_oak_planks"), B("bookshelf"), B("gold_block"), "dark_oak_stairs"),
        }
        main, accent, trim, st_name = styles[key]
        x = 57
        for dz in range(-6, 7):
            for y in range(P, 75):
                inner = abs(dz) <= 4 and y <= 72
                if not inner:
                    a.set(x, y, zc + dz, main if (abs(dz) == 5 or y in (73, 74)) else accent)
        for y in range(P, 74):
            a.set(x, y, zc - 6, accent)
            a.set(x, y, zc + 6, accent)
        for dz in range(-6, 7):
            a.set(x, 74, zc + dz, trim)
        # the window is now a shimmering portal pane
        pane = {"forest": "lime", "volcano": "orange", "paradise": "light_blue", "factory": "yellow",
                "skeld": "white", "library": "purple"}[key]
        a.fill(58, P, zc - 4, 58, 72, zc + 4, B("%s_stained_glass" % pane))
        for dz in (-4, 4):
            a.set(x, 72, zc + dz, main)
        for dz in (-3, 3):
            a.set(x, 72, zc + dz, stair(st_name, "south" if dz < 0 else "north", upside=True))
        a.set(x, P + 3, zc - 5, main)
        wall_sign(a, 56, P + 3, zc - 5, 4, "%s\n%s" % (title, sub), kind="dark_oak_wall_sign")
        wall_sign(a, 56, P + 3, zc + 5, 4, "%s\n§7빛나는 바닥에 서세요" % title, kind="dark_oak_wall_sign")
        glow = {"paradise": B("sea_lantern"), "volcano": B("ochre_froglight", axis="y"),
                "forest": B("verdant_froglight", axis="y"), "factory": B("ochre_froglight", axis="y"),
                "skeld": B("sea_lantern"), "library": B("pearlescent_froglight", axis="y")}[key]
        for dz in range(-3, 4):
            a.set(56, FY, zc + dz, glow)
            a.set(55, FY, zc + dz, glow if abs(dz) <= 2 else a.get(55, FY, zc + dz))
        self.gates.append(dict(dest=dest, box=(55, P, zc - 3, 56, P + 2, zc + 3), title=title))

    def home_diorama(self, zc):
        """Miniature of the residential island: little houses on bordered plots."""
        a = self.a
        rng = random.Random(zc * 17 + 3)
        x1, x2 = 59, 70
        z1, z2 = zc - 5, zc + 5
        a.fill(58, FY - 2, z1 - 2, 73, 76, z2 + 2, B("deepslate_bricks"))
        a.fill(x1, P, z1, x2, 73, z2, AIR)
        a.fill(71, P, z1, 71, 73, z2, B("light_blue_concrete"))
        a.fill(x1, 74, z1, x2, 74, z2, B("glowstone"))
        a.fill(x1, FY, z1, x2, FY, z2, B("grass_block"))
        a.fill(x1, FY - 1, z1, x2, FY - 1, z2, B("dirt"))
        for z in range(z1, z2 + 1):
            a.set(64, FY, z, B("gravel"))
        for (px, pz) in ((60, z1), (60, zc + 1), (66, z1), (66, zc + 1)):
            for i in range(5):
                for k in range(4):
                    edge = i in (0, 4) or k in (0, 3)
                    if edge:
                        a.set(px + i, FY, pz + k, B("stone_bricks"))
            roof = rng.choice(["red", "blue", "green", "orange"])
            a.fill(px + 1, P, pz + 1, px + 3, P + 1, pz + 2, B(rng.choice(["oak_planks", "birch_planks", "spruce_planks"])))
            a.fill(px + 1, P + 2, pz + 1, px + 3, P + 2, pz + 2, B("%s_terracotta" % roof))
            a.set(px + 2, P, pz + 2 if pz < zc else pz + 1, B("oak_door", cardinal="south", upper_block_bit=0))
        a.set(64, P, zc, B("lantern"))

    # ------------------------------------------------------------------ foyer: open entrance + ender chests
    def foyer(self):
        super().foyer()
        a = self.a
        # open a grand 7-wide entrance through the south wall
        a.fill(-3, P, 48, 3, P + 5, 50, AIR)
        for x in (-4, 4):
            a.fill(x, P, 48, x, P + 6, 50, B("polished_blackstone_bricks"))
        a.fill(-4, P + 6, 48, 4, P + 6, 50, B("chiseled_polished_blackstone"))
        for x in (-3, 3):
            a.set(x, P + 5, 48, stair("polished_blackstone_brick_stairs", "west" if x < 0 else "east", upside=True))
            a.set(x, P + 5, 50, stair("polished_blackstone_brick_stairs", "west" if x < 0 else "east", upside=True))
        for x in range(-3, 4):
            for z in (48, 49, 50):
                a.set(x, FY, z, B("polished_blackstone_bricks") if abs(x) == 3 else B("gilded_blackstone") if x == 0 else B("polished_deepslate"))
        a.fill(-3, P + 3, 47, 2, P + 3, 47, AIR)
        for x in (-3, 2):
            a.set(x, P + 2, 47, AIR)
        # replace the tag-game boards
        standing_sign(a, -7, P + 1, 44, 8, "§l§b스카이젠\n§r§f에 오신 것을\n§f환영합니다!", kind="dark_oak_standing_sign")
        standing_sign(a, 6, P + 1, 44, 8, "§l§6시작하기\n§r§f숲 섬에서 나무를 캐고\n§f상점에 팔아 보세요",
                      kind="dark_oak_standing_sign")
        wall_sign(a, -4, P + 1, 47, 2, "§l§e돈 안내\n§r§f처음 입장 시 100원\n§f+ 기본 도구 지급", kind="dark_oak_wall_sign")
        wall_sign(a, 3, P + 1, 47, 2, "§l§b← 상점가\n§l§a섬 이동 갤러리 →\n§l§e↑ 안내원", kind="dark_oak_wall_sign")
        # ender chests along the foyer side walls
        for x in (-10, -9, 9, 10):
            a.set(x, P, 46, B("ender_chest", cardinal="north"))
            a.add_be(simple_be("EnderChest", x, P, 46))
            self.ender.append((x, P, 46))
        for x in (-11, 11):
            a.set(x, P, 46, B("polished_blackstone_bricks"))
            a.set(x, P + 1, 46, B("lantern"))
        wall_sign(a, -10, P + 2, 47, 2, "§l§5엔더 상자\n§r§f나만의 보관함", kind="dark_oak_wall_sign")
        wall_sign(a, 9, P + 2, 47, 2, "§l§5엔더 상자\n§r§f나만의 보관함", kind="dark_oak_wall_sign")


# ============================================================================ outdoor island

def build_hub(W):
    lb = SkyLobby()
    area = lb.build()
    W.paste(area)
    a = W.a
    rng = random.Random(9090)
    x0, z0, sx, sz = -112, -112, 240, 240
    lx = np.arange(sx) + x0
    lz = np.arange(sz) + z0
    X, Z = np.meshgrid(lx, lz, indexing="ij")
    n1 = fbm(sx, sz, 20, 3, 501)
    n2 = fbm(sx, sz, 6, 2, 502)
    D = superdist((X - HUB_C[0]) / HUB_RX, (Z - HUB_C[1]) / HUB_RZ, 5.0)
    foot = D <= 1.0 + (n1 - 0.5) * 0.06 + (n2 - 0.5) * 0.02
    hall = hall_mask(X, Z)
    # bridgehead tongues reach the coast exactly
    for key, (bx, bz, d) in BRIDGEHEADS.items():
        if d in "NS":
            foot |= (np.abs(X - bx) <= 5) & (Z >= min(0, bz)) & (Z <= max(0, bz))
        else:
            foot |= (np.abs(Z - bz) <= 5) & (X >= min(0, bx)) & (X <= max(0, bx))
    dh = distance_transform_edt(~hall)
    H = np.full((sx, sz), G, np.int32)
    H += np.round((n1 - 0.5) * 4 * np.clip((dh - 12) / 18, 0, 1)).astype(np.int32)
    paths = path_mask(X, Z)
    H[paths] = G
    plaza = (X ** 2 + (Z - 76) ** 2) <= 19 ** 2
    H[plaza] = G
    from gen_common import clamp_gradient
    H = clamp_gradient(H, foot & ~hall, 1)
    H[hall] = G
    # ground columns
    V = W.view(x0, z0, sx, sz)
    ys = W.ys()
    stone = [B("stone"), B("andesite"), B("stone"), B("tuff"), B("diorite")]
    for (i, k) in np.argwhere(foot & ~hall):
        h = int(H[i, k])
        for y in range(32, h - 3):
            V[i, y - a.y0, k] = stone[(y // 3 + (i + k) % 2) % len(stone)]
        for y in range(h - 3, h):
            V[i, y - a.y0, k] = B("dirt")
        V[i, h - a.y0, k] = B("grass_block")
    solidify_below(W, x0, z0, foot & hall)
    under = under_rock([B("stone"), B("andesite"), B("tuff"), B("stone")], accent=B("moss_block"), accent_chance=0.05)
    shape_island(W, x0, z0, foot, H, 777, under, max_depth=36, spikes=16, keep_leaves=False)
    hub = dict(x0=x0, z0=z0, foot=foot, H=H, X=X, Z=Z, hall=hall, paths=paths, plaza=plaza)
    surface(W, hub, rng)
    exterior(W)
    plaza_build(W, rng)
    gardens(W, hub, rng)
    for key in BRIDGEHEADS:
        bridgehead(W, key)
    W.light_boxes.append(("hub_out", -100, -96, 112, 110, 60, 80, 1, 12))
    return lb, hub


def path_mask(X, Z):
    m = np.zeros(X.shape, bool)
    # ring path around the hall (4 wide)
    ring_outer = (X >= -70) & (X <= 82) & (Z >= -60) & (Z <= 60)
    ring_inner = (X >= -65) & (X <= 77) & (Z >= -55) & (Z <= 55)
    m |= ring_outer & ~ring_inner
    m &= ~((X >= -65) & (X <= 77) & (Z >= -55) & (Z <= 55))
    # spokes to the bridgeheads
    m |= (np.abs(X) <= 2) & (Z <= -55) & (Z >= -92)
    m |= (np.abs(Z) <= 2) & (X >= 77) & (X <= 110)
    m |= (np.abs(Z) <= 2) & (X <= -65) & (X >= -98)
    m |= (np.abs(X) <= 2) & (Z >= 50) & (Z <= 108)
    return m


def surface(W, hub, rng):
    """Path and plaza paving on top of the grass."""
    a = W.a
    X, Z, H = hub["X"], hub["Z"], hub["H"]
    for (i, k) in np.argwhere(hub["paths"] & hub["foot"] & ~hub["hall"]):
        x, z = int(X[i, k]), int(Z[i, k])
        r = rng.random()
        b = B("stone_bricks") if r < 0.55 else B("mossy_stone_bricks") if r < 0.7 else B("cracked_stone_bricks") if r < 0.8 else B("polished_andesite")
        a.set(x, int(H[i, k]), z, b)
    for (i, k) in np.argwhere(hub["plaza"] & ~hub["hall"]):
        x, z = int(X[i, k]), int(Z[i, k])
        r = math.hypot(x, z - 76)
        ang = math.degrees(math.atan2(z - 76, x)) % 30
        if r < 6.5:
            b = B("polished_diorite")
        elif int(r) in (8, 14):
            b = B("polished_blackstone_bricks")
        elif ang < 2.5:
            b = B("gilded_blackstone") if int(r) % 3 == 0 else B("polished_blackstone_bricks")
        else:
            b = B("smooth_quartz") if (int(r) % 2 == 0) else B("polished_andesite")
        a.set(x, G, z, b)


def exterior(W):
    """Buttresses, lanterns and banners on the plain deepslate walls of the hall."""
    a = W.a
    pil, cap = B("polished_blackstone_bricks"), B("chiseled_polished_blackstone")
    for z in range(-45, 49, 10):
        for x in (-61, 61):
            if x > 0 and -31 <= z <= 48:
                continue
            a.fill(x, P, z, x, 92, z, pil)
            a.set(x, 93, z, cap)
            a.set(x + (1 if x > 0 else -1), 72, z, B("lantern"))
            a.set(x + (1 if x > 0 else -1), 71, z, B("polished_blackstone_wall"))
    for x in range(-55, 56, 10):
        for z in (-51, 51):
            if z > 0 and abs(x) <= 6:
                continue
            a.fill(x, P, z, x, 92, z, pil)
            a.set(x, 93, z, cap)
            a.set(x, 72, z + (1 if z > 0 else -1), B("polished_blackstone_wall"))
            a.set(x, 73, z + (1 if z > 0 else -1), B("lantern"))
    # diorama bulge corners
    for (x, z) in ((74, -32), (74, 49)):
        a.fill(x, P, z, x, 78, z, pil)
        a.set(x, 79, z, cap)
    # banners over the entrance
    for x in (-8, 8):
        for y in range(76, 86):
            a.set(x, y, 51, B("polished_blackstone_bricks"))
        a.set(x, 76, 52, B("wall_banner", facing_direction=3))
        a.add_be(banner_be(x, 76, 52, 11, [("gra", 3), ("mc", 0), ("bo", 15)]))
    a.fill(-6, 74, 51, 6, 76, 51, B("polished_blackstone"))
    wall_sign(a, -2, 75, 52, 3, "§l§b스카이젠", kind="dark_oak_wall_sign")
    wall_sign(a, 1, 75, 52, 3, "§l§f허브", kind="dark_oak_wall_sign")
    wall_sign(a, -1, 75, 52, 3, "§l§a안전구역", kind="dark_oak_wall_sign")
    wall_sign(a, 0, 75, 52, 3, "§l§e환영합니다", kind="dark_oak_wall_sign")


def plaza_build(W, rng):
    """Spawn plaza in front of the entrance: a sky-crystal fountain, benches, lamps."""
    a = W.a
    cx, cz = 0, 76
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            r = math.hypot(x - cx, z - cz)
            if r <= 4.5:
                a.set(x, G, z, B("water") if r < 3.6 else B("polished_diorite"))
                a.set(x, G - 1, z, B("polished_diorite"))
                if 3.6 <= r <= 4.5:
                    a.set(x, G + 1, z, B("quartz_slab", half="bottom") if r > 4.0 else AIR)
    for y in range(G, G + 6):
        a.set(cx, y, cz, B("quartz_pillar", axis="y"))
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a.set(cx + dx, G + 6, cz + dz, B("amethyst_block"))
        a.set(cx + dx, G + 7, cz + dz, B("amethyst_cluster", block_face="up"))
    a.set(cx, G + 6, cz, B("sea_lantern"))
    a.set(cx, G + 7, cz, B("amethyst_block"))
    a.set(cx, G + 8, cz, B("end_rod", facing_direction=1))
    a.set(cx, G + 9, cz, B("end_rod", facing_direction=1))
    # benches on the four diagonals
    for ang in (45, 135, 225, 315):
        bx = cx + round(math.cos(math.radians(ang)) * 11)
        bz = cz + round(math.sin(math.radians(ang)) * 11)
        horiz = ang in (45, 225)
        for t in (-1, 0, 1):
            x, z = (bx + t, bz) if horiz else (bx, bz + t)
            face = "north" if math.sin(math.radians(ang)) > 0 else "south"
            a.set(x, G + 1, z, stair("spruce_stairs", face))
    for ang in range(0, 360, 45):
        lx = cx + round(math.cos(math.radians(ang + 22.5)) * 16)
        lz = cz + round(math.sin(math.radians(ang + 22.5)) * 16)
        lamp_post(a, lx, G + 1, lz, B("polished_blackstone_wall"), B("lantern"), height=3)
    # welcome boards at the plaza edge
    for (x, rot, text) in ((-7, 8, "§l§b스카이젠 허브\n§r§f안전구역입니다\n§f(낮·밤 모두 PvP 불가)"),
                           (7, 8, "§l§e섬 가는 길\n§r§f↑ 홀 갤러리: 순간이동\n§f↓ 다리: 주거 섬")):
        a.set(x, G + 1, 66, B("polished_blackstone_bricks"))
        standing_sign(a, x, G + 2, 66, rot, text, kind="dark_oak_standing_sign")


def gardens(W, hub, rng):
    a = W.a
    X, Z, H, foot = hub["X"], hub["Z"], hub["H"], hub["foot"]
    hall, paths, plaza = hub["hall"], hub["paths"], hub["plaza"]
    free = foot & ~hall & ~paths & ~plaza
    near_hall = distance_transform_edt(~hall) < 3
    free &= ~near_hall
    edge = distance_transform_edt(foot)
    free &= edge > 3
    # keep clear corridors around bridgeheads
    for key, (bx, bz, d) in BRIDGEHEADS.items():
        free &= ~((np.abs(X - bx) <= 8) & (np.abs(Z - bz) <= 8))
    taken = np.zeros_like(free)
    cand = np.argwhere(free)
    rng.shuffle(cand_l := [tuple(c) for c in cand])
    trees = 0
    for (i, k) in cand_l:
        if taken[max(0, i - 6):i + 7, max(0, k - 6):k + 7].any():
            continue
        if rng.random() > 0.35:
            continue
        x, z, y = int(X[i, k]), int(Z[i, k]), int(H[i, k]) + 1
        r = rng.random()
        if r < 0.35:
            oak_tree(a, x, y, z, rng)
        elif r < 0.6:
            cherry_tree(a, x, y, z, rng)
        elif r < 0.75:
            birch_tree(a, x, y, z, rng)
        elif r < 0.85 and edge[i, k] > 8:
            big_oak(a, x, y, z, rng, lantern_ok=False)
        else:
            bush(a, x, y, z, rng, B("azalea_leaves_flowered", persistent_bit=1))
        taken[max(0, i - 3):i + 4, max(0, k - 3):k + 4] = True
        trees += 1
    for (i, k) in cand_l:
        if taken[i, k] or rng.random() > 0.10:
            continue
        x, z, y = int(X[i, k]), int(Z[i, k]), int(H[i, k]) + 1
        if a.get(x, y, z) == AIR and a.get(x, y - 1, z) == B("grass_block"):
            if rng.random() < 0.15:
                tall_plant(a, x, y, z, rng.choice(TALL_FLOWERS))
            else:
                a.set(x, y, z, B(rng.choice(FLOWERS + ["short_grass", "short_grass", "fern"])))
    # lamp posts along the paths
    for (i, k) in np.argwhere(paths & foot & ~hall):
        x, z = int(X[i, k]), int(Z[i, k])
        if (x + z) % 11 == 0 and (x % 2 == 0):
            for (dx, dz) in ((3, 0), (-3, 0), (0, 3), (0, -3)):
                ii, kk = i + dx, k + dz
                if 0 <= ii < X.shape[0] and 0 <= kk < X.shape[1] and free[ii, kk] and not taken[ii, kk]:
                    lamp_post(a, x + dx, int(H[ii, kk]) + 1, z + dz, B("spruce_fence"), B("lantern"), height=3)
                    taken[ii, kk] = True
                    break
    return trees


BRIDGE_STYLE = {
    "forest": ("mossy_stone_bricks", "oak_log", "§l§a숲 섬", "§f나무 · 돌"),
    "skeld": ("smooth_stone", "iron_block", "§l§7우주 광산선", "§f석탄 · 철 · 화로방"),
    "library": ("dark_oak_planks", "bookshelf", "§l§d마법 도서관", "§f인첸트 (안전구역)"),
    "paradise": ("smooth_sandstone", "prismarine_bricks", "§l§b주거 섬", "§f집터 (안전구역)"),
}


def bridgehead(W, key):
    """Arch at the coast where a bridge starts, with the safe-zone warning line."""
    a = W.a
    bx, bz, d = BRIDGEHEADS[key]
    mat, accent, title, sub = BRIDGE_STYLE[key]
    along = (0, -1) if d == "N" else (0, 1) if d == "S" else (1, 0) if d == "E" else (-1, 0)
    side = (1, 0) if d in "NS" else (0, 1)
    # arch 3 blocks inland from the coast end
    cx, cz = bx - along[0] * 4, bz - along[1] * 4
    for s in (-3, 3):
        px, pz = cx + side[0] * s, cz + side[1] * s
        a.fill(px, G + 1, pz, px, G + 6, pz, B(accent) if accent != "oak_log" else B("oak_log", axis="y"))
        a.set(px, G + 7, pz, B("lantern"))
    for s in range(-3, 4):
        px, pz = cx + side[0] * s, cz + side[1] * s
        a.set(px, G + 6, pz, B(mat) if abs(s) < 3 else a.get(px, G + 6, pz))
    # warning line (red) and signs facing inland
    for s in range(-2, 3):
        px, pz = cx + side[0] * s + along[0], cz + side[1] * s + along[1]
        a.set(px, G, pz, B("red_concrete"))
    facing = {"N": 3, "S": 2, "E": 4, "W": 5}[d]
    px, pz = cx + side[0] * 2 - along[0], cz + side[1] * 2 - along[1]
    sp = cx + side[0] * -2 - along[0], cz + side[1] * -2 - along[1]
    a.set(px, G + 1, pz, B("polished_andesite"))
    rot = {"N": 0, "S": 8, "E": 4, "W": 12}[d]
    standing_sign(a, px, G + 2, pz, rot, "%s\n%s\n§7(다리 →)" % (title, sub),
                  kind="dark_oak_standing_sign")
    a.set(sp[0], G + 1, sp[1], B("polished_andesite"))
    standing_sign(a, sp[0], G + 2, sp[1], rot,
                  "§l§c안전구역 끝\n§r§f이 선 밖은\n§f밤에 PvP 가능", kind="dark_oak_standing_sign")
