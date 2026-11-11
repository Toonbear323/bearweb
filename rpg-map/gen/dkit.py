"""Dungeon toolkit: room carving, loot, spawners, boss/zone registry shared by all dungeons."""
from . import blocks as bl
from .core import B, Mix, Byte, Float
from .catalog import ENCH_ID

AIR = 0

# ---------------------------------------------------------------------------
# registry consumed by systems.py (functions / zones / warps)
# ---------------------------------------------------------------------------
REG = {"warps": {}, "zones": {0: [], 1: []}, "boss": {}, "notes": [], "survival": []}


def warp(wid, dim, x, y, z, face_to=None):
    """Arrival point of a warp; face_to = (x,y,z) the player looks at."""
    REG["warps"][wid] = (dim, x, y, z, face_to)


def zone(dim, x0, y0, z0, x1, y1, z1):
    """Adventure-mode protection box."""
    REG["zones"][dim].append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1)))


def boss(bid, commands):
    REG["boss"][bid] = commands


# ---------------------------------------------------------------------------
# carving
# ---------------------------------------------------------------------------

class Plan:
    """Collects rooms then carves shells first and interiors second so they never clip each other."""

    def __init__(self, w, wall, floor=None, ceil=None):
        self.w, self.wall, self.floor, self.ceil = w, wall, floor or wall, ceil or wall
        self.items = []

    def room(self, x0, y0, z0, x1, y1, z1, wall=None, floor=None, ceil=None):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        self.items.append((x0, y0, z0, x1, y1, z1, wall or self.wall, floor or self.floor, ceil or self.ceil))
        return (x0, y0, z0, x1, y1, z1)

    def carve(self):
        w = self.w
        for (x0, y0, z0, x1, y1, z1, wall, floor, ceil) in self.items:
            w.fill(x0 - 1, y0, z0 - 1, x1 + 1, y1, z1 + 1, wall)
            w.fill(x0 - 1, y0 - 1, z0 - 1, x1 + 1, y0 - 1, z1 + 1, floor)
            w.fill(x0 - 1, y1 + 1, z0 - 1, x1 + 1, y1 + 1, z1 + 1, ceil)
        for (x0, y0, z0, x1, y1, z1, *_r) in self.items:
            w.fill(x0, y0, z0, x1, y1, z1, AIR)


def spawner(w, x, y, z, entity, **kw):
    w.put(x, y, z, B("mob_spawner"), bl.be_spawner(entity, **kw))


def skull(w, x, y, z, kind=0, rot=0.0):
    w.put(x, y, z, B("skull", facing_direction=1),
          {"id": "Skull", "SkullType": Byte(kind), "Rotation": Float(rot), "Rot": Byte(0), "MouthMoving": Byte(0),
           "MouthTickCount": 0})


def pillar(w, x, y0, y1, z, mat="stone_brick", cap=True, body=None):
    body = body or bl.block(mat)
    for y in range(y0, y1 + 1):
        w.set(x, y, z, body)
    if cap:
        for d, (dx, dz) in (("E", (-1, 0)), ("W", (1, 0)), ("S", (0, -1)), ("N", (0, 1))):
            w.set(x + dx, y1, z + dz, bl.stairs(mat, d, top=True), keep=True)
            w.set(x + dx, y0, z + dz, bl.stairs(mat, d), keep=True)


def brazier(w, x, y, z, soul=False, base="polished_blackstone"):
    w.set(x, y, z, bl.wall(base) if base in ("polished_blackstone", "blackstone") else bl.wall("stone_brick"))
    w.set(x, y + 1, z, bl.campfire(soul=soul))


def cobwebs(w, box, n, rng):
    x0, y0, z0, x1, y1, z1 = box
    for _ in range(n):
        x, z = int(rng.integers(x0, x1 + 1)), int(rng.integers(z0, z1 + 1))
        if w.get(x, y1, z) == 0 and (x in (x0, x1) or z in (z0, z1)):
            w.set(x, y1, z, B("web"))


def scatter(w, box, blocks_, n, rng, on=None):
    """Drop decoration blocks on the floor of a box."""
    x0, y0, z0, x1, y1, z1 = box
    for _ in range(n):
        x, z = int(rng.integers(x0, x1 + 1)), int(rng.integers(z0, z1 + 1))
        if w.get(x, y0, z) == 0 and w.get(x, y0 - 1, z) != 0:
            b = blocks_[int(rng.integers(0, len(blocks_)))]
            w.set(x, y0, z, b)


# ---------------------------------------------------------------------------
# loot
# ---------------------------------------------------------------------------

def ench(*pairs):
    return [(ENCH_ID[n], l) for n, l in pairs]


def book(*pairs):
    return bl.item("enchanted_book", ench=ench(*pairs))


_TIERS = {
    1: [("bread", 2, 5, 8), ("apple", 1, 4, 5), ("iron_ingot", 1, 4, 8), ("arrow", 4, 12, 7), ("coal", 2, 6, 5),
        ("gold_nugget", 3, 9, 5), ("emerald", 1, 2, 3), ("stone_sword", 1, 1, 2), ("leather_chestplate", 1, 1, 2),
        ("iron_helmet", 1, 1, 1), ("torch", 4, 10, 6), ("bone", 2, 5, 4), ("string", 1, 4, 3),
        ("potion:21", 1, 1, 2), ("iron_sword", 1, 1, 1), ("shield", 1, 1, 1), ("cooked_beef", 2, 4, 4)],
    2: [("iron_ingot", 2, 6, 8), ("gold_ingot", 1, 4, 7), ("diamond", 1, 1, 2), ("emerald", 1, 3, 4),
        ("golden_apple", 1, 1, 2), ("arrow", 6, 16, 6), ("cooked_beef", 3, 6, 5), ("iron_sword", 1, 1, 2),
        ("iron_chestplate", 1, 1, 1), ("iron_leggings", 1, 1, 1), ("iron_boots", 1, 1, 1), ("bow", 1, 1, 2),
        ("potion:22", 1, 1, 3), ("potion:28", 1, 1, 2), ("ender_pearl", 1, 2, 2), ("experience_bottle", 2, 6, 3),
        ("redstone", 3, 8, 3), ("lapis_lazuli", 2, 6, 3), ("torch", 6, 12, 4), ("golden_carrot", 2, 5, 3)],
    3: [("diamond", 1, 3, 5), ("gold_ingot", 3, 8, 7), ("emerald", 2, 5, 5), ("golden_apple", 1, 2, 4),
        ("iron_ingot", 4, 10, 5), ("diamond_sword", 1, 1, 1), ("diamond_helmet", 1, 1, 1),
        ("diamond_boots", 1, 1, 1), ("potion:22", 1, 2, 4), ("potion:13", 1, 1, 3), ("potion:32", 1, 1, 2),
        ("ender_pearl", 1, 3, 3), ("experience_bottle", 4, 10, 5), ("golden_carrot", 3, 8, 4), ("arrow", 8, 24, 4),
        ("obsidian", 2, 5, 2), ("crossbow", 1, 1, 1), ("totem_of_undying", 1, 1, 0.4)],
    4: [("diamond", 2, 5, 6), ("gold_ingot", 5, 14, 6), ("gold_block", 1, 2, 3), ("emerald", 3, 8, 4),
        ("netherite_scrap", 1, 2, 2), ("ancient_debris", 1, 1, 1), ("golden_apple", 1, 3, 4),
        ("enchanted_golden_apple", 1, 1, 0.5), ("diamond_chestplate", 1, 1, 1), ("diamond_leggings", 1, 1, 1),
        ("diamond_sword", 1, 1, 1), ("potion:22", 2, 3, 4), ("potion:33", 1, 1, 2), ("potion:13", 1, 2, 3),
        ("experience_bottle", 6, 16, 5), ("blaze_rod", 1, 4, 3), ("ender_pearl", 2, 4, 3), ("quartz", 4, 12, 3),
        ("totem_of_undying", 1, 1, 0.6), ("netherite_ingot", 1, 1, 0.5)],
}
_BOOKS = {
    1: [("unbreaking", 1), ("protection", 1), ("sharpness", 1), ("efficiency", 1)],
    2: [("unbreaking", 2), ("protection", 2), ("sharpness", 2), ("power", 2), ("efficiency", 2), ("looting", 1)],
    3: [("unbreaking", 3), ("protection", 3), ("sharpness", 3), ("power", 3), ("fire_aspect", 1), ("fortune", 2),
        ("feather_falling", 3), ("respiration", 3), ("depth_strider", 2)],
    4: [("protection", 4), ("sharpness", 4), ("power", 4), ("mending", 1), ("looting", 3), ("fortune", 3),
        ("efficiency", 4), ("fire_aspect", 2), ("unbreaking", 3)],
}


def loot(tier, rng, n=None, extra=()):
    """Random chest contents for a tier (list with random slots)."""
    table = _TIERS[tier]
    n = n or int(rng.integers(5, 9))
    weights = [t[3] for t in table]
    tot = sum(weights)
    slots = list(rng.permutation(27)[: n + len(extra) + 1])
    out = []
    for _ in range(n):
        r = rng.random() * tot
        for name, lo, hi, wgt in table:
            r -= wgt
            if r <= 0:
                break
        cnt = int(rng.integers(lo, hi + 1))
        if ":" in name:
            nm, dmg = name.split(":")
            it = bl.item(nm, cnt, int(dmg))
        else:
            it = bl.item(name, cnt)
        it["Slot"] = Byte(int(slots.pop()))
        out.append(it)
    if rng.random() < 0.35 + 0.1 * tier:
        e = _BOOKS[tier][int(rng.integers(0, len(_BOOKS[tier])))]
        it = book(e)
        it["Slot"] = Byte(int(slots.pop()))
        out.append(it)
    for it in extra:
        it = dict(it)
        it["Slot"] = Byte(int(slots.pop()))
        out.append(it)
    return out


def chest(w, x, y, z, facing, tier, rng, extra=(), n=None):
    w.put(x, y, z, bl.chest(facing), bl.be_chest(loot(tier, rng, n=n, extra=extra)))


def sign(w, x, y, z, facing, text, wood="dark_oak", standing=False, glow=False):
    b = bl.standing_sign(facing, wood) if standing else bl.wall_sign(facing, wood)
    w.put(x, y, z, b, bl.be_sign(text, glow=glow))


def plate(w, x, y, z, command, kind="stone_pressure_plate", floor=None):
    """Pressure plate at (x,y,z); command block two below."""
    if floor is not None:
        w.set(x, y - 1, z, floor)
    w.set(x, y, z, B(kind))
    w.put(x, y - 2, z, bl.cmd("impulse", "U"), bl.be_cmd(command))


def button(w, x, y, z, facing, command, support, kind="polished_blackstone_button"):
    """Button on the `facing` side of the support block at (x,y,z); command block behind."""
    from .core import DIRS
    dx, dz = DIRS[facing]
    w.set(x, y, z, support)
    w.set(x + dx, y, z + dz, bl.button(facing, kind))
    w.put(x - dx, y, z - dz, bl.cmd("impulse", "U"), bl.be_cmd(command))


def reward_altar(w, x, y, z, facing, did, title):
    """Reward pedestal: button + sign, plus an exit warp plate beside it."""
    from .core import DIRS
    dx, dz = DIRS[facing]
    w.set(x, y, z, B("gold_block"))
    button(w, x, y + 1, z, facing, "function bear/clear/" + did, B("chiseled_polished_blackstone"))
    w.set(x, y + 2, z, B("lodestone"))
    w.set(x, y + 3, z, B("end_rod", facing_direction=1))
    sign(w, x + dx, y + 2, z + dz, facing, "§6§l%s\n§r보스 처치 후\n버튼을 눌러\n§6보상 수령" % title, glow=True)


def exit_pad(w, x, y, z, facing_sign=None, text="§b§l마을로 귀환\n§r발판을 밟으세요"):
    for ddx in (-1, 0, 1):
        for ddz in (-1, 0, 1):
            w.set(x + ddx, y - 1, z + ddz, B("lapis_block") if (ddx or ddz) else B("sea_lantern"))
    plate(w, x, y, z, "function bear/warp/town", kind="light_weighted_pressure_plate", floor=B("sea_lantern"))
    if facing_sign:
        from .core import DIRS
        dx, dz = DIRS[facing_sign]
        w.set(x - dx * 2, y, z - dz * 2, B("lapis_block"))
        w.set(x - dx * 2, y + 1, z - dz * 2, B("lapis_block"))
        sign(w, x - dx, y + 1, z - dz, facing_sign, text, glow=True)
