"""Block-state helpers (Bedrock 1.21.0 naming) with compass based orientation.

Directions are the strings 'N','E','S','W' (north = -Z, east = +X).
"""
from .core import B, REG, Mix, OPP, Byte, Short, Float, Long  # noqa: F401

# ---------------------------------------------------------------------------
# material families
# ---------------------------------------------------------------------------

_STONE = {
    # name: (block, stairs, slab(name, states), wall(name, states))
    "stone": (("stone", {}), "normal_stone_stairs", ("stone_block_slab4", {"stone_slab_type_4": "stone"}), None),
    "smooth_stone": (("smooth_stone", {}), None, ("smooth_stone_slab", {}), None),
    "cobblestone": (("cobblestone", {}), "stone_stairs", ("cobblestone_slab", {}),
                    ("cobblestone_wall", {"wall_block_type": "cobblestone"})),
    "mossy_cobblestone": (("mossy_cobblestone", {}), "mossy_cobblestone_stairs",
                          ("stone_block_slab2", {"stone_slab_type_2": "mossy_cobblestone"}),
                          ("cobblestone_wall", {"wall_block_type": "mossy_cobblestone"})),
    "stone_brick": (("stonebrick", {"stone_brick_type": "default"}), "stone_brick_stairs", ("stone_brick_slab", {}),
                    ("cobblestone_wall", {"wall_block_type": "stone_brick"})),
    "mossy_stone_brick": (("stonebrick", {"stone_brick_type": "mossy"}), "mossy_stone_brick_stairs",
                          ("stone_block_slab4", {"stone_slab_type_4": "mossy_stone_brick"}),
                          ("cobblestone_wall", {"wall_block_type": "mossy_stone_brick"})),
    "andesite": (("andesite", {}), "andesite_stairs", ("stone_block_slab3", {"stone_slab_type_3": "andesite"}),
                 ("cobblestone_wall", {"wall_block_type": "andesite"})),
    "polished_andesite": (("polished_andesite", {}), "polished_andesite_stairs",
                          ("stone_block_slab3", {"stone_slab_type_3": "polished_andesite"}), None),
    "diorite": (("diorite", {}), "diorite_stairs", ("stone_block_slab3", {"stone_slab_type_3": "diorite"}),
                ("cobblestone_wall", {"wall_block_type": "diorite"})),
    "polished_diorite": (("polished_diorite", {}), "polished_diorite_stairs",
                         ("stone_block_slab3", {"stone_slab_type_3": "polished_diorite"}), None),
    "granite": (("granite", {}), "granite_stairs", ("stone_block_slab3", {"stone_slab_type_3": "granite"}),
                ("cobblestone_wall", {"wall_block_type": "granite"})),
    "polished_granite": (("polished_granite", {}), "polished_granite_stairs",
                         ("stone_block_slab3", {"stone_slab_type_3": "polished_granite"}), None),
    "sandstone": (("sandstone", {"sand_stone_type": "default"}), "sandstone_stairs", ("sandstone_slab", {}),
                  ("cobblestone_wall", {"wall_block_type": "sandstone"})),
    "smooth_sandstone": (("sandstone", {"sand_stone_type": "smooth"}), "smooth_sandstone_stairs",
                         ("stone_block_slab2", {"stone_slab_type_2": "smooth_sandstone"}), None),
    "cut_sandstone": (("sandstone", {"sand_stone_type": "cut"}), None,
                      ("stone_block_slab4", {"stone_slab_type_4": "cut_sandstone"}), None),
    "red_sandstone": (("red_sandstone", {"sand_stone_type": "default"}), "red_sandstone_stairs",
                      ("stone_block_slab2", {"stone_slab_type_2": "red_sandstone"}),
                      ("cobblestone_wall", {"wall_block_type": "red_sandstone"})),
    "smooth_red_sandstone": (("red_sandstone", {"sand_stone_type": "smooth"}), "smooth_red_sandstone_stairs",
                             ("stone_block_slab3", {"stone_slab_type_3": "smooth_red_sandstone"}), None),
    "brick": (("brick_block", {}), "brick_stairs", ("brick_slab", {}),
              ("cobblestone_wall", {"wall_block_type": "brick"})),
    "nether_brick": (("nether_brick", {}), "nether_brick_stairs", ("nether_brick_slab", {}),
                     ("cobblestone_wall", {"wall_block_type": "nether_brick"})),
    "red_nether_brick": (("red_nether_brick", {}), "red_nether_brick_stairs",
                         ("stone_block_slab2", {"stone_slab_type_2": "red_nether_brick"}),
                         ("cobblestone_wall", {"wall_block_type": "red_nether_brick"})),
    "quartz": (("quartz_block", {"chisel_type": "default"}), "quartz_stairs", ("quartz_slab", {}), None),
    "smooth_quartz": (("quartz_block", {"chisel_type": "smooth"}), "smooth_quartz_stairs",
                      ("stone_block_slab4", {"stone_slab_type_4": "smooth_quartz"}), None),
    "prismarine": (("prismarine", {"prismarine_block_type": "default"}), "prismarine_stairs",
                   ("stone_block_slab2", {"stone_slab_type_2": "prismarine_rough"}),
                   ("cobblestone_wall", {"wall_block_type": "prismarine"})),
    "prismarine_brick": (("prismarine", {"prismarine_block_type": "bricks"}), "prismarine_bricks_stairs",
                         ("stone_block_slab2", {"stone_slab_type_2": "prismarine_brick"}), None),
    "dark_prismarine": (("prismarine", {"prismarine_block_type": "dark"}), "dark_prismarine_stairs",
                        ("stone_block_slab2", {"stone_slab_type_2": "prismarine_dark"}), None),
    "purpur": (("purpur_block", {}), "purpur_stairs", ("stone_block_slab2", {"stone_slab_type_2": "purpur"}), None),
    "end_brick": (("end_bricks", {}), "end_brick_stairs",
                  ("stone_block_slab3", {"stone_slab_type_3": "end_stone_brick"}),
                  ("cobblestone_wall", {"wall_block_type": "end_brick"})),
}
# regular "<n>", "<n>_stairs", "<n>_slab", "<n>_wall" families
_REGULAR = {
    "blackstone": "blackstone", "polished_blackstone": "polished_blackstone",
    "polished_blackstone_brick": "polished_blackstone_bricks",
    "cobbled_deepslate": "cobbled_deepslate", "polished_deepslate": "polished_deepslate",
    "deepslate_brick": "deepslate_bricks", "deepslate_tile": "deepslate_tiles",
    "mud_brick": "mud_bricks", "tuff": "tuff", "polished_tuff": "polished_tuff", "tuff_brick": "tuff_bricks",
    "cut_copper": "cut_copper", "exposed_cut_copper": "exposed_cut_copper",
    "weathered_cut_copper": "weathered_cut_copper", "oxidized_cut_copper": "oxidized_cut_copper",
    "waxed_cut_copper": "waxed_cut_copper", "waxed_exposed_cut_copper": "waxed_exposed_cut_copper",
    "waxed_weathered_cut_copper": "waxed_weathered_cut_copper",
    "waxed_oxidized_cut_copper": "waxed_oxidized_cut_copper",
    "bamboo_mosaic": "bamboo_mosaic",
}
WOODS = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "bamboo", "crimson", "warped"]

_DIR_STAIRS = {"E": 0, "W": 1, "S": 2, "N": 3}
_DIR_DOOR = {"E": 0, "S": 1, "W": 2, "N": 3}
_DIR_TRAP = {"E": 0, "W": 1, "S": 2, "N": 3}
_DIR_GATE = {"S": 0, "W": 1, "N": 2, "E": 3}
_DIR_BED = {"S": 0, "W": 1, "N": 2, "E": 3}
_DIR6 = {"D": 0, "U": 1, "N": 2, "S": 3, "W": 4, "E": 5}
_CARD = {"N": "north", "E": "east", "S": "south", "W": "west"}
_ROT16 = {"S": 0, "W": 4, "N": 8, "E": 12}
_VINE = {"S": 1, "W": 2, "N": 4, "E": 8}
_POT = {"N": 0, "E": 1, "S": 2, "W": 3}


def block(mat):
    """Full block of a material family (stone family, wood planks, or raw block name)."""
    if mat in _STONE:
        n, st = _STONE[mat][0]
        return B(n, **st)
    if mat in _REGULAR:
        return B(_REGULAR[mat])
    if mat in WOODS:
        return B(mat + "_planks")
    return B(mat)


def stairs(mat, facing, top=False):
    """facing = direction of ascent (the tall side)."""
    if mat in _STONE:
        n = _STONE[mat][1]
        if n is None:
            raise KeyError("no stairs for " + mat)
    else:
        n = mat + "_stairs"
    return B(n, weirdo_direction=_DIR_STAIRS[facing], upside_down_bit=top)


def slab(mat, top=False):
    half = "top" if top else "bottom"
    if mat in _STONE:
        n, st = _STONE[mat][2]
        return B(n, vertical_half=half, **st)
    return B(mat + "_slab", vertical_half=half)


def wall(mat):
    if mat in _STONE:
        w = _STONE[mat][3]
        if w is None:
            raise KeyError("no wall for " + mat)
        return B(w[0], wall_post_bit=True, **w[1])
    return B(mat + "_wall", wall_post_bit=True)


def planks(w):
    return B(w + "_planks")


def log(w, axis="y", stripped=False):
    n = w + ("_stem" if w in ("crimson", "warped") else "_log")
    if w == "bamboo":
        n = "bamboo_block"
    if stripped:
        n = "stripped_" + n
    return B(n, pillar_axis=axis)


def wood(w, axis="y", stripped=False):
    n = w + ("_hyphae" if w in ("crimson", "warped") else "_wood")
    if stripped:
        n = "stripped_" + n
    return B(n, pillar_axis=axis)


def fence(w):
    return B("nether_brick_fence") if w == "nether_brick" else B(w + "_fence")


def gate(w, facing, open=False, in_wall=False):
    """facing N/S => gate spans east-west."""
    n = "fence_gate" if w == "oak" else w + "_fence_gate"
    return B(n, direction=_DIR_GATE[facing], open_bit=open, in_wall_bit=in_wall)


def door(w, into, upper=False, hinge_right=False, open=False):
    """into = direction pointing into the building (door panel sits on the outer edge)."""
    n = {"oak": "wooden_door", "iron": "iron_door"}.get(w, w + "_door")
    return B(n, direction=_DIR_DOOR[into], upper_block_bit=upper, door_hinge_bit=hinge_right, open_bit=open)


def trapdoor(w, attach, open=False, top=False):
    """attach = side of the cell the hinge is on (an open trapdoor stands against that side)."""
    n = {"oak": "trapdoor", "iron": "iron_trapdoor"}.get(w, w + "_trapdoor")
    return B(n, direction=_DIR_TRAP[OPP[attach]], open_bit=open, upside_down_bit=top)


def leaves(w):
    n = {"azalea": "azalea_leaves", "flowering_azalea": "azalea_leaves_flowered"}.get(w, w + "_leaves")
    return B(n, persistent_bit=True)


def torch(attach="top", kind="torch"):
    """attach = 'top' (standing) or the side where the supporting block is."""
    return B(kind, torch_facing_direction="top" if attach == "top" else _CARD[attach])


def lantern(hanging=False, soul=False):
    return B("soul_lantern" if soul else "lantern", hanging=hanging)


def ladder(facing):
    """facing = direction the ladder faces (support block is on the opposite side)."""
    return B("ladder", facing_direction=_DIR6[facing])


def button(facing, kind="stone_button"):
    """facing = direction the button points to ('U' on a floor, 'D' on a ceiling)."""
    return B(kind, facing_direction=_DIR6[facing])


def chest(facing, trapped=False):
    return B("trapped_chest" if trapped else "chest", cardinal_direction=_CARD[facing])


def barrel(facing="U"):
    return B("barrel", facing_direction=_DIR6[facing])


def furnace(facing, kind="furnace"):
    return B(kind, cardinal_direction=_CARD[facing])


def wall_sign(facing, w="oak"):
    n = {"oak": "wall_sign", "dark_oak": "darkoak_wall_sign"}.get(w, w + "_wall_sign")
    return B(n, facing_direction=_DIR6[facing])


def standing_sign(facing, w="oak"):
    n = {"oak": "standing_sign", "dark_oak": "darkoak_standing_sign"}.get(w, w + "_standing_sign")
    return B(n, ground_sign_direction=_ROT16[facing])


def hanging_sign(facing, w="oak"):
    """Ceiling-hung sign whose face looks toward `facing`."""
    return B(w + "_hanging_sign", hanging=True, attached_bit=False, ground_sign_direction=_ROT16[facing],
             facing_direction=_DIR6[facing])


def wall_banner(facing):
    return B("wall_banner", facing_direction=_DIR6[facing])


def standing_banner(facing):
    return B("standing_banner", ground_sign_direction=_ROT16[facing])


def vine(*sides):
    bits = 0
    for s in sides:
        bits |= _VINE[s]
    return B("vine", vine_direction_bits=bits)


def bed(facing, head):
    """facing = direction from foot to head."""
    return B("bed", direction=_DIR_BED[facing], head_piece_bit=head)


def campfire(soul=False, lit=True):
    return B("soul_campfire" if soul else "campfire", extinguished=not lit)


def cmd(kind="impulse", facing="U", conditional=False):
    n = {"impulse": "command_block", "chain": "chain_command_block", "repeat": "repeating_command_block"}[kind]
    return B(n, facing_direction=_DIR6[facing], conditional_bit=conditional)


def pot(facing="N"):
    return B("decorated_pot", direction=_POT[facing])


def anvil(facing="N"):
    return B("anvil", cardinal_direction=_CARD[facing])


def candle(n=1, lit=True, color=None):
    return B((color + "_" if color else "") + "candle", candles=n - 1, lit=lit)


WATER = B("water")
LAVA = B("lava")
AIR = 0

# ---------------------------------------------------------------------------
# block-entity payloads
# ---------------------------------------------------------------------------


def item(name, count=1, damage=0, slot=None, display=None, lore=None, ench=None):
    """Item compound.  ench = [(id, lvl), ...] using Bedrock numeric enchant ids."""
    d = {"Name": name if ":" in name else "minecraft:" + name, "Count": Byte(count), "Damage": Short(damage),
         "WasPickedUp": Byte(0)}
    if slot is not None:
        d["Slot"] = Byte(slot)
    tag = {}
    if display or lore:
        disp = {}
        if display:
            disp["Name"] = display
        if lore:
            disp["Lore"] = list(lore)
        tag["display"] = disp
    if ench:
        tag["ench"] = [{"id": Short(i), "lvl": Short(l)} for i, l in ench]
    if tag:
        d["tag"] = tag
    return d


def be_chest(items, kind="Chest"):
    its = []
    for i, it in enumerate(items):
        if it is None:
            continue
        it = dict(it)
        if "Slot" not in it:
            it["Slot"] = Byte(i)
        its.append(it)
    return {"id": kind, "Items": its, "Findable": Byte(0)}


def _sign_side(text, color=-16777216, glow=False):
    return {"Text": text, "TextOwner": "", "IgnoreLighting": Byte(1 if glow else 0), "HideGlowOutline": Byte(0),
            "PersistFormatting": Byte(1), "SignTextColor": color}


def be_sign(text, back=None, glow=False, kind="Sign", color=-16777216):
    return {"id": kind, "FrontText": _sign_side(text, color, glow),
            "BackText": _sign_side(text if back is None else back, color, glow), "IsWaxed": Byte(1)}


def be_spawner(entity, delay_min=200, delay_max=600, count=3, max_nearby=6, player_range=16, spawn_range=4):
    return {"id": "MobSpawner", "EntityIdentifier": entity if ":" in entity else "minecraft:" + entity,
            "Delay": Short(20), "MinSpawnDelay": Short(delay_min), "MaxSpawnDelay": Short(delay_max),
            "SpawnCount": Short(count), "MaxNearbyEntities": Short(max_nearby),
            "RequiredPlayerRange": Short(player_range), "SpawnRange": Short(spawn_range),
            "DisplayEntityHeight": Float(1.8), "DisplayEntityWidth": Float(0.8), "DisplayEntityScale": Float(1.0)}


def be_cmd(command, name="", auto=False, tick_delay=0, repeat=False, chain=False):
    mode = 1 if repeat else (2 if chain else 0)
    return {"id": "CommandBlock", "Command": command, "CustomName": name, "ExecuteOnFirstTick": Byte(0),
            "LPCommandMode": mode, "LPCondionalMode": Byte(0), "LPRedstoneMode": Byte(1 if auto else 0),
            "LastExecution": Long(0), "LastOutput": "", "LastOutputParams": [], "SuccessCount": 0,
            "TickDelay": tick_delay, "TrackOutput": Byte(0), "Version": 39, "auto": Byte(1 if auto else 0),
            "conditionMet": Byte(0), "conditionalMode": Byte(0), "powered": Byte(0)}


def be_banner(base):
    """base colour: 0 black,1 red,2 green,3 brown,4 blue,5 purple,6 cyan,7 light gray,8 gray,9 pink,10 lime,
    11 yellow,12 light blue,13 magenta,14 orange,15 white"""
    return {"id": "Banner", "Base": base, "Type": 0}


def be_bed(color):
    """bed colour: 0 white,1 orange,2 magenta,3 light blue,4 yellow,5 lime,6 pink,7 gray,8 light gray,9 cyan,
    10 purple,11 blue,12 brown,13 green,14 red,15 black"""
    return {"id": "Bed", "color": Byte(color)}


def be_pot(plant_block_id):
    name, st = REG.entries[plant_block_id]
    states = {}
    for k, t, v in st:
        states[k] = Byte(v) if t == "b" else (int(v) if t == "i" else str(v))
    from .core import BLOCK_VERSION
    return {"id": "FlowerPot", "PlantBlock": {"name": "minecraft:" + name, "states": states, "version": BLOCK_VERSION}}
