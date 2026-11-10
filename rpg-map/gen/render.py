"""Preview renderers (isometric + top-down) used to review builds without opening the game."""
import numpy as np
from PIL import Image

from .core import REG

_EXACT = {
    "grass_block": (104, 164, 72), "dirt": (134, 96, 67), "grass_path": (170, 148, 90), "podzol": (106, 76, 40),
    "farmland": (98, 62, 36), "mud": (60, 57, 61), "packed_mud": (142, 106, 79), "mud_bricks": (137, 103, 79),
    "stone": (125, 125, 125), "cobblestone": (122, 122, 122), "mossy_cobblestone": (106, 124, 98),
    "stonebrick": (120, 119, 120), "andesite": (136, 136, 137), "polished_andesite": (132, 135, 134),
    "diorite": (189, 188, 189), "polished_diorite": (193, 193, 195), "granite": (149, 103, 86),
    "polished_granite": (154, 107, 89), "smooth_stone": (159, 159, 159), "gravel": (132, 127, 127),
    "deepslate": (80, 80, 83), "cobbled_deepslate": (77, 77, 81), "polished_deepslate": (72, 73, 73),
    "deepslate_bricks": (70, 70, 71), "deepslate_tiles": (55, 55, 56), "chiseled_deepslate": (54, 54, 55),
    "tuff": (108, 109, 103), "tuff_bricks": (98, 103, 95), "polished_tuff": (98, 104, 100),
    "chiseled_tuff": (89, 94, 87), "chiseled_tuff_bricks": (99, 103, 96), "calcite": (223, 224, 221),
    "dripstone_block": (134, 108, 93), "pointed_dripstone": (130, 102, 88), "bedrock": (60, 60, 60),
    "sand": (219, 207, 163), "sandstone": (216, 203, 156), "red_sandstone": (187, 99, 29),
    "suspicious_sand": (217, 204, 159),
    "water": (56, 98, 190), "lava": (222, 99, 20), "flowing_water": (56, 98, 190), "flowing_lava": (222, 99, 20),
    "ice": (146, 184, 254), "packed_ice": (142, 180, 250), "blue_ice": (116, 168, 253), "snow": (249, 254, 254),
    "snow_layer": (249, 254, 254), "powder_snow": (248, 253, 253),
    "glass": (190, 222, 230), "glass_pane": (190, 222, 230), "tinted_glass": (45, 40, 48),
    "brick_block": (151, 98, 83), "bookshelf": (130, 100, 60), "hay_block": (166, 139, 12),
    "obsidian": (16, 11, 26), "crying_obsidian": (40, 12, 72), "netherrack": (98, 38, 38),
    "nether_brick": (45, 22, 27), "red_nether_brick": (70, 7, 9), "cracked_nether_bricks": (41, 20, 24),
    "chiseled_nether_bricks": (47, 23, 28), "soul_sand": (81, 62, 51), "soul_soil": (76, 58, 47),
    "magma": (143, 63, 32), "glowstone": (250, 215, 120), "shroomlight": (241, 147, 71),
    "basalt": (74, 73, 78), "polished_basalt": (88, 88, 92), "smooth_basalt": (72, 72, 78),
    "blackstone": (42, 36, 41), "polished_blackstone": (53, 49, 57), "polished_blackstone_bricks": (48, 43, 50),
    "cracked_polished_blackstone_bricks": (44, 38, 44), "chiseled_polished_blackstone": (54, 49, 57),
    "gilded_blackstone": (86, 63, 38), "gold_block": (247, 210, 62), "iron_block": (220, 220, 220),
    "diamond_block": (98, 237, 228), "emerald_block": (42, 203, 88), "lapis_block": (31, 67, 140),
    "redstone_block": (176, 25, 5), "coal_block": (16, 16, 16), "copper_block": (192, 107, 79),
    "netherite_block": (67, 61, 64), "amethyst_block": (134, 98, 191), "budding_amethyst": (132, 96, 186),
    "amethyst_cluster": (164, 126, 207), "raw_gold_block": (222, 169, 47), "raw_iron_block": (166, 136, 107),
    "crimson_nylium": (131, 31, 31), "warped_nylium": (43, 115, 101), "nether_wart_block": (115, 3, 2),
    "warped_wart_block": (23, 120, 121), "crimson_stem": (93, 26, 30), "warped_stem": (58, 59, 78),
    "crimson_planks": (101, 49, 71), "warped_planks": (43, 105, 99), "ancient_debris": (95, 64, 56),
    "nether_gold_ore": (115, 55, 42), "quartz_ore": (118, 66, 62), "quartz_block": (236, 230, 223),
    "quartz_bricks": (235, 229, 222), "purpur_block": (170, 126, 170), "end_stone": (220, 223, 158),
    "end_bricks": (218, 224, 162), "prismarine": (99, 156, 151), "sea_lantern": (172, 200, 190),
    "sponge": (196, 192, 75), "clay": (161, 166, 179), "moss_block": (89, 110, 45), "moss_carpet": (89, 110, 45),
    "mycelium": (111, 99, 105), "sculk": (13, 30, 36), "sculk_vein": (8, 48, 57), "sculk_catalyst": (15, 32, 38),
    "sculk_shrieker": (199, 205, 170), "sculk_sensor": (7, 70, 84), "reinforced_deepslate": (80, 83, 79),
    "lantern": (255, 200, 110), "soul_lantern": (90, 230, 235), "torch": (255, 215, 90),
    "soul_torch": (90, 230, 235), "campfire": (255, 150, 40), "soul_campfire": (80, 210, 220),
    "fire": (255, 140, 20), "soul_fire": (60, 200, 220), "redstone_torch": (230, 50, 30),
    "ochre_froglight": (250, 245, 206), "verdant_froglight": (229, 244, 228),
    "pearlescent_froglight": (245, 240, 240), "lit_redstone_lamp": (240, 180, 100), "end_rod": (240, 235, 225),
    "beacon": (117, 220, 215), "conduit": (160, 140, 113), "lit_pumpkin": (240, 150, 30), "pumpkin": (198, 118, 24),
    "melon_block": (111, 145, 30), "cactus": (85, 127, 43), "reeds": (148, 192, 101), "bamboo": (93, 144, 19),
    "web": (228, 233, 234), "chest": (162, 114, 37), "trapped_chest": (162, 114, 37), "barrel": (135, 100, 58),
    "crafting_table": (160, 105, 60), "furnace": (110, 110, 110), "anvil": (68, 68, 68),
    "command_block": (190, 130, 90), "chain_command_block": (130, 165, 150),
    "repeating_command_block": (130, 110, 175), "mob_spawner": (36, 46, 62), "portal": (120, 30, 200),
    "iron_bars": (140, 140, 140), "chain": (60, 66, 80), "ladder": (125, 97, 55), "vine": (60, 110, 30),
    "glow_lichen": (112, 131, 121), "kelp": (87, 140, 44), "seagrass": (50, 126, 8), "waterlily": (32, 128, 48),
    "short_grass": (112, 160, 72), "tall_grass": (112, 160, 72), "fern": (100, 150, 70),
    "large_fern": (100, 150, 70), "deadbush": (107, 79, 41), "poppy": (200, 40, 40), "yellow_flower": (240, 220, 50),
    "blue_orchid": (47, 162, 232), "allium": (181, 122, 233), "azure_bluet": (220, 230, 220),
    "red_tulip": (200, 50, 40), "orange_tulip": (230, 120, 40), "white_tulip": (230, 230, 230),
    "pink_tulip": (235, 170, 200), "oxeye_daisy": (230, 230, 210), "cornflower": (70, 110, 230),
    "lily_of_the_valley": (240, 240, 240), "sunflower": (240, 200, 40), "lilac": (190, 140, 200),
    "rose_bush": (190, 40, 40), "peony": (230, 170, 220), "pink_petals": (246, 181, 220),
    "torchflower": (230, 140, 50), "sweet_berry_bush": (60, 100, 60), "wheat": (200, 180, 80),
    "carrots": (80, 150, 50), "potatoes": (80, 160, 60), "beetroot": (90, 140, 60),
    "brown_mushroom": (150, 110, 85), "red_mushroom": (220, 50, 45), "brown_mushroom_block": (149, 111, 81),
    "red_mushroom_block": (200, 46, 45), "crimson_fungus": (160, 40, 30), "warped_fungus": (20, 150, 130),
    "crimson_roots": (150, 20, 40), "warped_roots": (20, 140, 120), "nether_sprouts": (20, 150, 130),
    "weeping_vines": (130, 20, 20), "twisting_vines": (20, 140, 120), "nether_wart": (120, 20, 25),
    "bone_block": (210, 206, 180), "skull": (200, 200, 190), "tnt": (200, 60, 50), "slime": (112, 192, 91),
    "honey_block": (251, 185, 52), "honeycomb_block": (229, 148, 29), "dried_kelp_block": (50, 60, 40),
    "bell": (250, 210, 70), "lodestone": (147, 149, 152), "respawn_anchor": (60, 20, 100),
    "enchanting_table": (130, 40, 50), "brewing_stand": (150, 130, 90), "cauldron": (75, 75, 75),
    "lectern": (170, 135, 80), "loom": (150, 120, 90), "smithing_table": (60, 60, 70),
    "grindstone": (140, 140, 140), "stonecutter_block": (120, 120, 120), "blast_furnace": (80, 80, 85),
    "smoker": (100, 90, 80), "cartography_table": (100, 85, 65), "fletching_table": (190, 165, 130),
    "composter": (110, 70, 30), "jukebox": (110, 70, 55), "noteblock": (110, 70, 55), "bed": (160, 40, 40),
    "light_block": (255, 255, 200), "barrier": (255, 0, 0), "hardened_clay": (152, 94, 68),
    "decorated_pot": (150, 85, 60), "flower_pot": (124, 68, 53), "target": (230, 180, 170),
    "cherry_leaves": (240, 170, 205), "azalea_leaves": (90, 115, 44), "azalea_leaves_flowered": (120, 110, 90),
    "mangrove_leaves": (70, 110, 40), "spore_blossom": (220, 100, 160), "big_dripleaf": (110, 140, 50),
    "small_dripleaf_block": (100, 130, 50), "cave_vines": (90, 110, 40),
    "cave_vines_body_with_berries": (200, 150, 50), "cave_vines_head_with_berries": (200, 150, 50),
    "hanging_roots": (160, 115, 90), "dirt_with_roots": (144, 103, 76), "azalea": (100, 125, 47),
    "flowering_azalea": (130, 120, 110), "sea_pickle": (90, 97, 39), "turtle_egg": (228, 226, 191),
    "wither_rose": (40, 40, 30), "frame": (150, 110, 60), "standing_banner": (230, 230, 230),
    "wall_banner": (230, 230, 230), "tripwire_hook": (130, 110, 80), "lever": (110, 100, 90),
    "redstone_wire": (200, 20, 10), "lightning_rod": (200, 110, 80), "heavy_core": (80, 85, 95),
}
_WOOD = {"oak": (162, 131, 79), "spruce": (115, 85, 49), "birch": (192, 175, 121), "jungle": (160, 115, 81),
         "acacia": (168, 90, 50), "dark_oak": (67, 43, 20), "mangrove": (118, 54, 49), "cherry": (227, 179, 173),
         "bamboo": (194, 173, 80), "crimson": (101, 49, 71), "warped": (43, 105, 99)}
_LOG = {"oak": (109, 85, 51), "spruce": (59, 38, 17), "birch": (216, 215, 210), "jungle": (85, 68, 25),
        "acacia": (103, 96, 87), "dark_oak": (60, 46, 26), "mangrove": (84, 67, 41), "cherry": (55, 33, 45),
        "bamboo": (127, 144, 58)}
_LEAF = {"oak": (72, 122, 40), "spruce": (58, 95, 58), "birch": (100, 140, 70), "jungle": (60, 130, 35),
         "acacia": (90, 125, 40), "dark_oak": (55, 105, 30)}
_DYE = {"white": (234, 236, 237), "orange": (240, 118, 19), "magenta": (189, 68, 179), "light_blue": (58, 175, 217),
        "yellow": (248, 198, 39), "lime": (112, 185, 25), "pink": (237, 141, 172), "gray": (62, 68, 71),
        "light_gray": (142, 142, 135), "silver": (142, 142, 135), "cyan": (21, 137, 145), "purple": (121, 42, 172),
        "blue": (53, 57, 157), "brown": (114, 71, 40), "green": (84, 109, 27), "red": (160, 39, 34),
        "black": (20, 21, 25)}
_COPPER = {"oxidized": (82, 162, 132), "weathered": (108, 153, 110), "exposed": (161, 125, 103)}
EMISSIVE = {"lantern", "soul_lantern", "torch", "soul_torch", "glowstone", "sea_lantern", "shroomlight", "lava",
            "fire", "soul_fire", "campfire", "soul_campfire", "ochre_froglight", "verdant_froglight",
            "pearlescent_froglight", "lit_redstone_lamp", "end_rod", "beacon", "lit_pumpkin", "magma", "portal",
            "flowing_lava", "candle"}


def _color(name, states):
    st = states
    if name == "stonebrick" and st.get("stone_brick_type") == "mossy":
        return (112, 122, 100)
    if name == "prismarine":
        t = st.get("prismarine_block_type")
        return {"dark": (51, 91, 75), "bricks": (99, 171, 158)}.get(t, (99, 156, 151))
    if name == "sand" and st.get("sand_type") == "red":
        return (190, 102, 33)
    if name == "dirt" and st.get("dirt_type") == "coarse":
        return (119, 85, 59)
    if name == "cobblestone_wall":
        t = st.get("wall_block_type", "cobblestone")
        return _color({"stone_brick": "stonebrick", "brick": "brick_block", "end_brick": "end_bricks",
                       "mossy_stone_brick": "mossy_cobblestone"}.get(t, t), {})
    if name in _EXACT:
        return _EXACT[name]
    for k, c in _COPPER.items():
        if k in name and "copper" in name:
            return c
    if "copper" in name:
        return (192, 107, 79)
    if name.endswith("_ore"):
        base = (80, 80, 83) if "deepslate" in name else (125, 125, 125)
        tint = {"coal": (40, 40, 40), "iron": (175, 142, 119), "gold": (240, 210, 70), "diamond": (90, 220, 215),
                "emerald": (40, 200, 90), "lapis": (40, 80, 180), "redstone": (200, 30, 20),
                "copper": (190, 110, 80)}
        for k, c in tint.items():
            if k in name:
                return tuple((b + c2) // 2 for b, c2 in zip(base, c))
        return base
    if "candle" in name:
        return (240, 220, 160)
    for dye, c in _DYE.items():
        if name.startswith(dye + "_"):
            rest = name[len(dye) + 1:]
            if "terracotta" in rest and "glazed" not in rest:
                g = sum(c) // 3
                return tuple(int(v * 0.55 + g * 0.15 + 60 * 0.3) for v in c)
            if "stained_glass" in rest:
                return tuple(int(v * 0.6 + 255 * 0.4) for v in c)
            if "concrete_powder" in rest:
                return tuple(min(255, int(v * 0.9 + 25)) for v in c)
            return c
    if "coral" in name:
        if name.startswith("dead"):
            return (130, 123, 119)
        for k, c in {"tube": (49, 87, 207), "brain": (207, 91, 159), "bubble": (165, 26, 162),
                     "fire": (163, 35, 46), "horn": (216, 199, 66)}.items():
            if k in name:
                return c
    if name.endswith("_leaves"):
        for w, c in _LEAF.items():
            if name.startswith(w):
                return c
        return (72, 122, 40)
    if "log" in name or name.endswith("_wood"):
        stripped = name.startswith("stripped_")
        for w in sorted(_LOG, key=len, reverse=True):
            if w in name:
                return _WOOD[w] if stripped else _LOG[w]
    if "stem" in name or "hyphae" in name:
        return (93, 26, 30) if "crimson" in name else (58, 59, 78)
    for w in sorted(_WOOD, key=len, reverse=True):
        if name.startswith(w + "_") or name.startswith(w.replace("_", "") + "_"):
            return _WOOD[w]
    if name in ("wooden_door", "trapdoor", "fence_gate", "wooden_button", "wooden_pressure_plate", "standing_sign",
                "wall_sign", "fence", "wooden_slab", "planks"):
        return _WOOD["oak"]
    # derived blocks (stairs / slabs / walls)
    for suf in ("_stairs", "_slab", "_wall", "_double_slab", "_bricks", "_brick"):
        if name.endswith(suf):
            base = name[: -len(suf)]
            for cand in (base, base + "s", base + "_block", base + "_bricks", base.replace("_brick", "_bricks")):
                if cand in _EXACT:
                    return _EXACT[cand]
    if name.startswith("stone_block_slab") or name.startswith("double_stone_block_slab"):
        for k, v in st.items():
            if "slab_type" in k:
                m = {"smooth_sandstone": "sandstone", "cut_sandstone": "sandstone", "stone": "stone",
                     "mossy_stone_brick": "mossy_cobblestone", "smooth_quartz": "quartz_block",
                     "prismarine_rough": "prismarine", "prismarine_dark": (51, 91, 75),
                     "prismarine_brick": (99, 171, 158), "mossy_cobblestone": "mossy_cobblestone",
                     "red_nether_brick": "red_nether_brick", "purpur": "purpur_block",
                     "end_stone_brick": "end_bricks", "smooth_red_sandstone": "red_sandstone",
                     "red_sandstone": "red_sandstone", "cut_red_sandstone": "red_sandstone"}.get(v, v)
                if isinstance(m, tuple):
                    return m
                return _EXACT.get(m, (125, 125, 125))
    table = [("sandstone", (216, 203, 156)), ("quartz", (236, 230, 223)), ("prismarine", (99, 156, 151)),
             ("nether_brick", (45, 22, 27)), ("stone_brick", (120, 119, 120)), ("mossy", (106, 124, 98)),
             ("brick", (151, 98, 83)), ("stone", (125, 125, 125)), ("purpur", (170, 126, 170)),
             ("end_", (220, 223, 158)), ("iron", (200, 200, 200)), ("rail", (120, 110, 90)),
             ("piston", (150, 130, 100)), ("shulker", (150, 105, 150)), ("glass", (190, 222, 230)),
             ("pressure_plate", (130, 130, 130)), ("button", (130, 130, 130)), ("sign", (162, 131, 79)),
             ("amethyst", (164, 126, 207)), ("dripleaf", (110, 140, 50)), ("sapling", (60, 130, 40))]
    for k, c in table:
        if k in name:
            return c
    return (200, 0, 200)


_cache_cols = None


def color_table():
    """RGB per registered block id (recomputed when the registry has grown)."""
    global _cache_cols
    n = len(REG.entries)
    if _cache_cols is None or len(_cache_cols) != n:
        cols = np.zeros((n, 3), np.uint8)
        for i, (name, st) in enumerate(REG.entries):
            cols[i] = _color(name, {k: v for k, t, v in st})
        _cache_cols = cols
    return _cache_cols


def _flags():
    n = len(REG.entries)
    thin = np.zeros(n, bool)   # small decorations drawn narrower
    emis = np.zeros(n, bool)
    clear = np.zeros(n, bool)  # does not hide neighbours
    for i, (name, st) in enumerate(REG.entries):
        if name in EMISSIVE or "candle" in name:
            emis[i] = True
        if name in ("air", "light_block", "barrier", "structure_void"):
            clear[i] = True
        if any(k in name for k in ("glass", "pane", "bars", "fence", "torch", "lantern", "flower", "tulip", "grass",
                                   "fern", "vine", "sign", "banner", "chain", "door", "ladder", "button", "lever",
                                   "pressure_plate", "carpet", "petals", "candle", "rod", "web", "roots", "sprouts",
                                   "bush", "sapling", "mushroom", "fungus", "lichen", "rail", "wall", "poppy",
                                   "orchid", "allium", "bluet", "daisy", "cornflower", "lily", "lilac", "peony",
                                   "kelp", "seagrass", "coral", "pickle", "dripstone", "amethyst_cluster", "bud",
                                   "cactus", "reeds", "bamboo", "wheat", "carrots", "potatoes", "beetroot",
                                   "snow_layer", "slab", "stairs", "skull", "pot", "bell", "campfire", "fire",
                                   "leaves", "hook", "wire", "dripleaf", "blossom", "frame", "egg")):
            if name not in ("grass_block", "grass_path", "bookshelf", "chiseled_bookshelf", "brown_mushroom_block",
                            "red_mushroom_block", "dripstone_block", "amethyst_block", "budding_amethyst"):
                clear[i] = True
        if name in ("water", "flowing_water"):
            clear[i] = True
        if any(k in name for k in ("torch", "lantern", "flower", "tulip", "short_grass", "tall_grass", "fern", "sign",
                                   "chain", "ladder", "button", "lever", "candle", "rod", "roots", "sprouts",
                                   "sapling", "poppy", "orchid", "allium", "bluet", "daisy", "cornflower", "lily",
                                   "kelp", "seagrass", "pickle", "pointed_dripstone", "bud", "reeds", "wheat",
                                   "carrots", "potatoes", "beetroot", "deadbush", "fence", "bars", "pane", "banner",
                                   "hook", "petals", "lichen", "vine", "carpet", "pressure_plate", "snow_layer",
                                   "rail", "wire")) and "block" not in name:
            thin[i] = True
    panel = np.zeros(n, bool)
    for i, (name, st) in enumerate(REG.entries):
        if any(k in name for k in ("trapdoor", "door", "wall_sign", "wall_banner", "ladder", "button", "lever",
                                   "vine", "lichen", "hanging_sign", "tripwire")):
            panel[i] = True
    return thin, emis, clear, panel


def _rot(a, view):
    # a[x,z,y]; view k rotates the scene so different sides face the camera
    return np.rot90(a, k=view, axes=(0, 1))


def iso(world, box, view=0, S=4, cut_y=None, bg=(24, 26, 34), out=None, water_alpha=True):
    """Isometric render of box=(x0,y0,z0,x1,y1,z1) inclusive.  view 0: camera in the south-east."""
    xa, ya, za, xb, yb, zb = box
    xa, xb = max(xa, world.x0), min(xb, world.x1 - 1)
    za, zb = max(za, world.z0), min(zb, world.z1 - 1)
    ya, yb = max(ya, world.y0), min(yb, world.y1 - 1)
    if cut_y is not None:
        yb = min(yb, cut_y)
    A = world.b[xa - world.x0:xb + 1 - world.x0, za - world.z0:zb + 1 - world.z0, ya - world.y0:yb + 1 - world.y0]
    A = _rot(A, view)
    nx, nz, ny = A.shape
    cols = color_table()
    thin, emis, clear, panel = _flags()
    H = S + S // 4
    W_img = (nx + nz) * S + 2
    H_img = (nx + nz) * S // 2 + ny * H + 4
    solid = ~clear[A]
    nonair = A != 0
    pad = np.zeros((nx + 1, nz + 1, ny + 1), bool)
    pad[:nx, :nz, :ny] = solid
    vis_top = nonair & ~pad[:nx, :nz, 1:]
    vis_e = nonair & ~pad[1:, :nz, :ny]
    vis_s = nonair & ~pad[:nx, 1:, :ny]
    # same-liquid neighbours don't draw internal faces
    wid = [i for i, (n, _) in enumerate(REG.entries) if n in ("water", "flowing_water")]
    isw = np.isin(A, wid)
    wp = np.zeros((nx + 1, nz + 1, ny + 1), bool)
    wp[:nx, :nz, :ny] = isw
    vis_top &= ~(isw & wp[:nx, :nz, 1:])
    vis_e &= ~(isw & wp[1:, :nz, :ny])
    vis_s &= ~(isw & wp[:nx, 1:, :ny])
    # rasterise the three face footprints once
    def raster(poly):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        pts = []
        for py in range(int(np.floor(min(ys))), int(np.ceil(max(ys))) + 1):
            for px in range(int(np.floor(min(xs))), int(np.ceil(max(xs))) + 1):
                cx_, cy_ = px + 0.5, py + 0.5
                inside = True
                n = len(poly)
                for i in range(n):
                    x1, y1 = poly[i]
                    x2, y2 = poly[(i + 1) % n]
                    if (x2 - x1) * (cy_ - y1) - (y2 - y1) * (cx_ - x1) < -1e-6:
                        inside = False
                        break
                if inside:
                    pts.append((px, py))
        return pts
    top_fp = raster([(0, 0), (S, S / 2), (0, S), (-S, S / 2)])
    s_fp = raster([(-S, S / 2), (0, S), (0, S + H), (-S, S / 2 + H)])
    e_fp = raster([(0, S), (S, S / 2), (S, S / 2 + H), (0, S + H)])
    pix_all, dep_all, col_all = [], [], []
    ox = nz * S + 1
    oy = ny * H + 1
    for mask, fp, shade, fbias in ((vis_top, top_fp, 1.0, 2), (vis_s, s_fp, 0.62, 0), (vis_e, e_fp, 0.8, 1)):
        xs, zs, ys = np.nonzero(mask)
        if len(xs) == 0:
            continue
        ids = A[xs, zs, ys]
        c = cols[ids].astype(np.float32)
        sh = np.where(emis[ids], 1.0, shade)
        # gentle height light + water translucency tint
        c = c * sh[:, None] * (0.86 + 0.14 * (ys / max(ny - 1, 1)))[:, None]
        c = np.clip(c, 0, 255).astype(np.uint8)
        bx = (xs - zs) * S + ox
        by = (xs + zs) * S // 2 - (ys + 1) * H + oy
        depth = ((xs + zs + ys).astype(np.int32) * 4 + fbias)
        t = thin[ids]
        pn = panel[ids]
        for (dx, dy) in fp:
            keep = ~t | (abs(dx) <= S // 2)
            if fp is top_fp:
                keep = keep & ~pn
            else:
                keep = keep & (~pn | ((abs(dx) <= max(1, S // 4)) & (dy > S // 2 + 1)))
            px = bx + dx
            py = by + dy
            ok = keep & (px >= 0) & (px < W_img) & (py >= 0) & (py < H_img)
            pix_all.append((py[ok] * W_img + px[ok]).astype(np.int64))
            dep_all.append(depth[ok])
            col_all.append(c[ok])
    img = np.zeros((H_img * W_img, 3), np.uint8)
    img[:] = bg
    if pix_all:
        pix = np.concatenate(pix_all)
        dep = np.concatenate(dep_all)
        col = np.concatenate(col_all)
        order = np.argsort(dep, kind="stable")
        img[pix[order]] = col[order]
    im = Image.fromarray(img.reshape(H_img, W_img, 3))
    if out:
        im.save(out)
    return im


def topdown(world, box=None, scale=1, out=None, ymax=None):
    """Top-down colour map with hill shading."""
    if box is None:
        box = (world.x0, world.z0, world.x1 - 1, world.z1 - 1)
    xa, za, xb, zb = box
    A = world.b[xa - world.x0:xb + 1 - world.x0, za - world.z0:zb + 1 - world.z0, :]
    if ymax is not None:
        A = A[:, :, :ymax - world.y0 + 1]
    cols = color_table()
    nz_ = A != 0
    ny = A.shape[2]
    top = ny - 1 - nz_[:, :, ::-1].argmax(axis=2)
    has = nz_.any(axis=2)
    ids = np.take_along_axis(A, top[:, :, None], axis=2)[:, :, 0]
    c = cols[ids].astype(np.float32)
    h = top.astype(np.float32)
    # water depth shading
    wid = [i for i, (n, _) in enumerate(REG.entries) if n in ("water", "flowing_water")]
    isw = np.isin(ids, wid)
    if isw.any():
        notw = nz_ & ~np.isin(A, wid)
        floor = ny - 1 - notw[:, :, ::-1].argmax(axis=2)
        depth = np.clip((top - floor) / 24.0, 0, 1)
        c[isw] = c[isw] * (1.0 - 0.55 * depth[isw])[:, None]
        h = np.where(isw, top.max() * 0 + top, h)
    gx = np.zeros_like(h)
    gz = np.zeros_like(h)
    gx[1:, :] = h[1:, :] - h[:-1, :]
    gz[:, 1:] = h[:, 1:] - h[:, :-1]
    shade = np.clip(1.0 + 0.09 * (-gx - gz), 0.55, 1.35)
    shade = np.where(isw, 1.0, shade)
    c = np.clip(c * shade[:, :, None] * (0.8 + 0.2 * (h / max(ny - 1, 1)))[:, :, None] * 1.1, 0, 255)
    c[~has] = (10, 10, 20)
    im = Image.fromarray(np.transpose(c.astype(np.uint8), (1, 0, 2)))
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    if out:
        im.save(out)
    return im
