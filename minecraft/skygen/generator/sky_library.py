"""Library island changes: an east entrance, four more enchanting tables, a repair corner and a magic NPC."""
from mcw import B, AIR, simple_be
from gen_library import P, F1, BX, BZ, L2
from gen_common import wall_sign, standing_sign, stair
from sky_features import enchant_dais

DOOR_Z = -9


def library_features(lib, W):
    enchants = []
    # the original dais in the arcane study
    enchants.append((lib.cx - 45, P + 1, lib.cz))
    for (x, z) in ((-30, -7), (-30, 7), (-58, -8), (-58, 8)):
        enchant_dais(lib, x, z, enchants)
    # east entrance next to the fireplace
    for x in range(BX - 7, BX + 1):
        for z in range(DOOR_Z - 1, DOOR_Z + 2):
            for y in range(P, P + 4):
                lib.set(x, y, z, AIR)
            lib.set(x, F1, z, B("dark_oak_planks") if z != DOOR_Z else B("red_wool"))
    for z in (DOOR_Z - 2, DOOR_Z + 2):
        for y in range(P, P + 5):
            lib.set(BX, y, z, B("stripped_dark_oak_log", axis="y"))
            lib.set(BX + 1, y, z, B("stripped_dark_oak_log", axis="y"))
    for z in range(DOOR_Z - 2, DOOR_Z + 3):
        lib.set(BX + 1, P + 4, z, B("dark_oak_planks"))
        lib.set(BX, P + 4, z, B("dark_oak_planks"))
    lib.set(BX + 2, P + 3, DOOR_Z - 2, B("lantern"))
    lib.set(BX + 2, P + 3, DOOR_Z + 2, B("lantern"))
    lib.set(BX + 2, P + 2, DOOR_Z - 2, B("dark_oak_fence"))
    lib.set(BX + 2, P + 2, DOOR_Z + 2, B("dark_oak_fence"))
    wall_sign(lib.a, lib.cx + BX + 2, P + 1, lib.cz + DOOR_Z + 2, 5,
              "§l§d마법 도서관\n§r§a안전구역\n§f인첸트는 서쪽 서재", kind="dark_oak_wall_sign")
    # path from the door through the garden to the coast
    for x in range(BX + 1, BX + 30):
        for z in range(DOOR_Z - 1, DOOR_Z + 2):
            lib.set(x, F1, z, B("stone_bricks") if z != DOOR_Z else B("polished_andesite"))
            for y in range(P, P + 8):
                lib.set(x, y, z, AIR)
    for z in range(DOOR_Z + 2, 2):
        for x in range(BX + 26, BX + 29):
            lib.set(x, F1, z, B("stone_bricks"))
            for y in range(P, P + 8):
                lib.set(x, y, z, AIR)
    # repair corner by the east wall (anvils, grindstones, smithing table)
    xi = BX - 1
    spots = [((xi, 5), "anvil"), ((xi, 6), "anvil"), ((xi, 8), "grindstone"), ((xi, 10), "smithing_table"),
             ((xi, -15), "anvil"), ((xi, -16), "anvil"), ((xi, -13), "grindstone")]
    repairs = []
    for (x, z), kind in spots:
        for y in range(P, P + 3):
            lib.set(x, y, z, AIR)
        lib.set(x - 1, P, z, AIR)
        if kind == "anvil":
            lib.set(x, P, z, B("anvil", cardinal="north"))
        elif kind == "grindstone":
            lib.set(x, P, z, B("grindstone", attachment="standing", direction=1))
        else:
            lib.set(x, P, z, B("smithing_table"))
        repairs.append((lib.cx + x, P, lib.cz + z, kind))
    wall_sign(lib.a, lib.cx + xi - 1, P + 2, lib.cz + 7, 4, "§l§6수리 공방\n§r§f모루 · 숫돌\n§f대장장이 작업대",
              kind="dark_oak_wall_sign")
    # magic merchant NPC in the arcane study, next to the big dais
    W.npcs.append(dict(name="§l§9마법 상인", x=lib.cx - 45 + 0.5, y=P, z=lib.cz - 9 + 0.5,
                       face=(lib.cx - 45 + 0.5, P, lib.cz + 0.5), tag="sky_shop_magic2", kind="shop", shop="magic"))
    lib.set(-45, F1, -9, B("lodestone"))
    for y in range(P, P + 3):
        lib.set(-45, y, -9, AIR)
    W.enchant_tables += enchants
    return dict(door=(lib.cx + BX + 2, P, lib.cz + DOOR_Z), repairs=repairs,
                arrival=(lib.cx - 45 + 0.5, P, lib.cz + 5.5, 180), pad=(lib.cx - 45, F1, lib.cz + 9))
