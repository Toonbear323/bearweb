"""Minimal Minecraft Bedrock world writer.

Blocks are validated against the canonical Bedrock block-state list
(pmmp/BedrockData) so every palette entry is a real block state.
World data is written straight into LevelDB (Mojang's fork via amulet-leveldb).
"""
import json
import os
import struct
import zipfile

import numpy as np
import amulet_nbt as an

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKDB = json.load(open(os.path.join(HERE, "data", "blockdb.json")))

# Block-state version tag (1.21.60.33 - Mojang has not bumped it since).
BLOCK_VERSION = 18168865
CHUNK_VERSION = 42

# Blocks newer than 1.21.60 - avoided so the world opens on slightly older clients too.
DENY = {
    "iron_chain", "copper_chain", "copper_bars", "copper_lantern", "copper_torch", "copper_chest",
    "copper_golem_statue", "dried_ghast", "leaf_litter", "wildflowers", "bush", "firefly_bush",
    "cactus_flower", "short_dry_grass", "tall_dry_grass", "golden_dandelion",
}
DENY_PREFIX = ("sulfur", "potent_sulfur", "cinnabar", "polished_sulfur", "polished_cinnabar",
               "chiseled_sulfur", "chiseled_cinnabar")
DENY_SUFFIX = ("_shelf", "_copper_bars", "_copper_chain", "_copper_lantern", "_copper_chest",
               "_golem_statue")

# Java-style convenience names -> Bedrock ids
NAME_ALIAS = {
    "dark_oak_wall_sign": "darkoak_wall_sign", "dark_oak_standing_sign": "darkoak_standing_sign",
    "oak_wall_sign": "wall_sign", "oak_standing_sign": "standing_sign", "oak_fence_gate": "fence_gate",
    "oak_trapdoor": "trapdoor", "oak_door": "wooden_door", "oak_button": "wooden_button",
    "oak_pressure_plate": "wooden_pressure_plate", "dirt_path": "grass_path", "magma_block": "magma",
    "bricks": "brick_block", "nether_bricks": "nether_brick", "lily_pad": "waterlily", "cobweb": "web",
    "sugar_cane": "reeds", "dead_bush": "deadbush", "jack_o_lantern": "lit_pumpkin",
    "terracotta": "hardened_clay", "snow_block": "snow", "note_block": "noteblock",
    "stonecutter": "stonecutter_block", "spawner": "mob_spawner", "slime_block": "slime",
}

# Names that were renamed after 1.21.60: write the 1.21.60 name, vanilla upgrades it.
LEGACY_NAME = {"chain": "iron_chain"}
LEGACY_DROP = {"lightning_rod": {"powered_bit"}}

ALIASES = {
    "cardinal": "minecraft:cardinal_direction",
    "half": "minecraft:vertical_half",
    "face": "minecraft:block_face",
    "mfacing": "minecraft:facing_direction",
    "axis": "pillar_axis",
    "facing": "facing_direction",
    "dir": "direction",
    "upper": "upper_block_bit",
    "upside": "upside_down_bit",
    "wdir": "weirdo_direction",
    "depth": "liquid_depth",
    "torch": "torch_facing_direction",
    "rot": "ground_sign_direction",
}

STRING_DEFAULTS = {
    "pillar_axis": "y", "minecraft:vertical_half": "bottom", "torch_facing_direction": "top",
    "minecraft:cardinal_direction": "south", "sea_grass_type": "default",
    "bamboo_leaf_size": "no_leaves", "bamboo_stalk_thickness": "thin", "dripstone_thickness": "tip",
    "big_dripleaf_tilt": "none", "cauldron_liquid": "water", "structure_block_type": "data",
    "lever_direction": "up_north_south", "attachment": "standing", "minecraft:block_face": "up",
    "minecraft:facing_direction": "up", "cracked_state": "no_cracks", "turtle_egg_count": "one_egg",
    "wall_connection_type_east": "none", "wall_connection_type_north": "none",
    "wall_connection_type_south": "none", "wall_connection_type_west": "none",
}
INT_DEFAULTS = {"facing_direction": 1}
BYTE_DEFAULTS = {"persistent_bit": 1}


def _check_name(name):
    if name in LEGACY_NAME:
        return LEGACY_NAME[name]
    if name in DENY or name.startswith(DENY_PREFIX) or name.endswith(DENY_SUFFIX):
        raise ValueError("block %s is too new / denied" % name)
    if name not in BLOCKDB:
        raise ValueError("unknown block %s" % name)
    return name


class Palette:
    def __init__(self):
        self.entries = []      # (name, {state: (type, value)})
        self.lookup = {}
        self.cache = {}
        self.nbt = []
        self.names = []
        self.get("air")

    def get(self, name, states=None, **kw):
        if name.startswith("minecraft:"):
            name = name[10:]
        name = NAME_ALIAS.get(name, name)
        ck = (name, tuple(sorted((states or {}).items())), tuple(sorted(kw.items())))
        hit = self.cache.get(ck)
        if hit is not None:
            return hit
        dbname = _check_name(name)
        spec = BLOCKDB[dbname]
        given = dict(states or {})
        given.update(kw)
        final = {}
        for k, v in given.items():
            key = k
            if key not in spec:
                if "minecraft:" + key in spec:
                    key = "minecraft:" + key
                elif ALIASES.get(key) in spec:
                    key = ALIASES[key]
                else:
                    raise ValueError("block %s has no state %s (has %s)" % (name, k, list(spec)))
            t, values = spec[key]
            if t == 1:
                v = int(bool(v))
            if v not in values:
                raise ValueError("block %s state %s=%r not in %r" % (name, key, v, values))
            final[key] = (t, v)
        for key, (t, values) in spec.items():
            if key in final or key in LEGACY_DROP.get(name, ()):
                continue
            if t == 8:
                d = STRING_DEFAULTS.get(key, values[0])
            elif t == 1:
                d = BYTE_DEFAULTS.get(key, 0)
            else:
                d = INT_DEFAULTS.get(key, values[0])
                if d not in values:
                    d = values[0]
            final[key] = (t, d)
        key = (name, tuple(sorted(final.items())))
        idx = self.lookup.get(key)
        if idx is None:
            idx = len(self.entries)
            self.lookup[key] = idx
            self.entries.append((name, final))
            self.names.append(name)
            st = an.CompoundTag()
            for sk, (t, v) in sorted(final.items()):
                st[sk] = an.ByteTag(v) if t == 1 else an.IntTag(v) if t == 3 else an.StringTag(v)
            tag = an.CompoundTag({
                "name": an.StringTag("minecraft:" + name),
                "states": st,
                "version": an.IntTag(BLOCK_VERSION),
            })
            self.nbt.append(an.NamedTag(tag, "").to_nbt(compressed=False, little_endian=True))
        self.cache[ck] = idx
        return idx

    def state(self, idx, key):
        return self.entries[idx][1].get(key, (None, None))[1]


PAL = Palette()


def B(name, **kw):
    """Block id for name + states (keyword aliases allowed)."""
    return PAL.get(name, None, **kw)


def BS(name, states):
    return PAL.get(name, states)


AIR = 0

# ---------------------------------------------------------------------------
# Physics classification (used by the trap checker and renderer)

PASSABLE_EXACT = {
    "air", "short_grass", "tall_grass", "fern", "large_fern", "deadbush", "dandelion", "poppy",
    "blue_orchid", "allium", "azure_bluet", "red_tulip", "orange_tulip", "white_tulip", "pink_tulip",
    "oxeye_daisy", "cornflower", "lily_of_the_valley", "wither_rose", "sunflower", "lilac", "rose_bush",
    "peony", "torchflower", "pitcher_plant", "torch", "soul_torch", "redstone_torch", "underwater_torch",
    "colored_torch_red", "colored_torch_blue", "colored_torch_green", "colored_torch_purple",
    "vine", "ladder", "glow_lichen", "sculk_vein", "resin_clump", "hanging_roots", "spore_blossom",
    "cave_vines", "cave_vines_body_with_berries", "cave_vines_head_with_berries", "weeping_vines",
    "twisting_vines", "seagrass", "kelp", "waterlily", "pink_petals", "moss_carpet", "pale_moss_carpet",
    "pale_hanging_moss", "brown_mushroom", "red_mushroom", "crimson_roots", "warped_roots",
    "nether_sprouts", "crimson_fungus", "warped_fungus", "standing_sign", "wall_sign", "chain",
    "end_rod", "lightning_rod", "rail", "golden_rail", "detector_rail", "activator_rail", "lever",
    "redstone_wire", "trip_wire", "tripwire_hook", "fire", "soul_fire", "web", "structure_void",
    "standing_banner", "wall_banner", "reeds", "sea_pickle", "amethyst_cluster", "small_amethyst_bud",
    "medium_amethyst_bud", "large_amethyst_bud", "pointed_dripstone", "cocoa", "azalea",
    "flowering_azalea", "mangrove_propagule", "frame", "glow_frame", "snow_layer", "candle",
    "open_eyeblossom", "closed_eyeblossom", "sweet_berry_bush", "small_dripleaf_block", "wheat",
    "carrots", "potatoes", "beetroot", "bamboo_sapling", "nether_wart", "light_block_0",
}
PASSABLE_SUFFIX = ("_sapling", "_carpet", "_button", "_pressure_plate", "_standing_sign", "_wall_sign",
                   "_hanging_sign", "_coral", "_coral_fan", "_coral_wall_fan", "_torch", "_candle",
                   "_flower", "_banner")
LOW_EXACT = {"campfire", "soul_campfire", "bed", "flower_pot", "daylight_detector",
             "daylight_detector_inverted", "skeleton_skull", "player_head", "zombie_head", "creeper_head",
             "dragon_head", "piglin_head", "wither_skeleton_skull", "lantern", "soul_lantern",
             "turtle_egg", "sniffer_egg", "decorated_pot", "stonecutter_block", "candle_cake", "cake"}
TALL_SUFFIX = ("_fence", "_wall", "_fence_gate")
TALL_EXACT = {"fence_gate", "nether_brick_fence", "border_block"}
LIQUIDS = {"water", "flowing_water", "lava", "flowing_lava"}
CLIMB = {"ladder", "vine", "scaffolding", "cave_vines", "cave_vines_body_with_berries",
         "cave_vines_head_with_berries", "weeping_vines", "twisting_vines"}


def physics(idx):
    """Returns (height_in_halves, liquid, climbable). height 0=no collision, 1=half, 2=full, 3=1.5 high."""
    name, st = PAL.entries[idx]
    climb = name in CLIMB
    if name in LIQUIDS:
        return 0, True, False
    if name.startswith("light_block_"):
        return 0, False, False
    if name in PASSABLE_EXACT or name.endswith(PASSABLE_SUFFIX):
        return 0, False, climb
    if name.endswith("_trapdoor") or name in ("trapdoor", "iron_trapdoor"):
        if st.get("open_bit", (0, 0))[1]:
            return 0, False, False
        if st.get("upside_down_bit", (0, 0))[1]:
            return 2, False, False
        return 0, False, False
    if name.endswith("_door") or name in ("wooden_door", "iron_door"):
        if st.get("open_bit", (0, 0))[1]:
            return 0, False, False
        return 2, False, False
    if name.endswith("_slab") and not name.endswith("double_slab"):
        if st.get("minecraft:vertical_half", (0, "bottom"))[1] == "bottom":
            return 1, False, False
        return 2, False, False
    if name in LOW_EXACT:
        return 1, False, False
    if name in TALL_EXACT or name.endswith(TALL_SUFFIX):
        if "gate" in name and st.get("open_bit", (0, 0))[1]:
            return 0, False, False
        return 3, False, False
    return 2, False, climb


def physics_tables():
    n = len(PAL.entries)
    h = np.zeros(n, np.int8)
    liq = np.zeros(n, bool)
    clb = np.zeros(n, bool)
    for i in range(n):
        h[i], liq[i], clb[i] = physics(i)
    return h, liq, clb


# ---------------------------------------------------------------------------
# NBT helpers for block entities

def nbt_compound(d):
    c = an.CompoundTag()
    for k, v in d.items():
        c[k] = v
    return c


def sign_text(text, color=-16777216, glow=False):
    return nbt_compound({
        "HideGlowOutline": an.ByteTag(0),
        "IgnoreLighting": an.ByteTag(1 if glow else 0),
        "PersistFormatting": an.ByteTag(1),
        "SignTextColor": an.IntTag(color),
        "Text": an.StringTag(text),
        "TextOwner": an.StringTag(""),
    })


def sign_be(x, y, z, front, back="", glow=True, hanging=False, color=-16777216):
    return nbt_compound({
        "BackText": sign_text(back, color, glow),
        "FrontText": sign_text(front, color, glow),
        "IsWaxed": an.ByteTag(1),
        "id": an.StringTag("HangingSign" if hanging else "Sign"),
        "isMovable": an.ByteTag(1),
        "x": an.IntTag(x), "y": an.IntTag(y), "z": an.IntTag(z),
    })


def simple_be(kind, x, y, z, **extra):
    d = {"id": an.StringTag(kind), "isMovable": an.ByteTag(1),
         "x": an.IntTag(x), "y": an.IntTag(y), "z": an.IntTag(z)}
    d.update(extra)
    return nbt_compound(d)


def flowerpot_be(x, y, z, plant, **states):
    pid = B(plant, **states)
    name, st = PAL.entries[pid]
    stc = an.CompoundTag()
    for sk, (t, v) in sorted(st.items()):
        stc[sk] = an.ByteTag(v) if t == 1 else an.IntTag(v) if t == 3 else an.StringTag(v)
    return simple_be("FlowerPot", x, y, z, PlantBlock=nbt_compound({
        "name": an.StringTag("minecraft:" + name), "states": stc, "version": an.IntTag(BLOCK_VERSION)}))


def banner_be(x, y, z, base, patterns=()):
    """base/pattern colours use Bedrock banner colour ids (0=black ... 15=white)."""
    pl = an.ListTag([nbt_compound({"Color": an.IntTag(c), "Pattern": an.StringTag(p)}) for p, c in patterns])
    return simple_be("Banner", x, y, z, Base=an.IntTag(base), Patterns=pl, Type=an.IntTag(0))


# ---------------------------------------------------------------------------

class Area:
    """Dense voxel buffer covering a chunk-aligned box of the overworld."""

    def __init__(self, name, x0, z0, sx, sz, y0=32, sy=128, biome=1):
        assert x0 % 16 == 0 and z0 % 16 == 0 and sx % 16 == 0 and sz % 16 == 0 and y0 % 16 == 0
        self.name = name
        self.x0, self.z0, self.y0 = x0, z0, y0
        self.sx, self.sy, self.sz = sx, sy, sz
        self.blk = np.zeros((sx, sy, sz), np.uint16)
        self.wet = np.zeros((sx, sy, sz), bool)      # water in the second block layer
        self.bio = np.full((sx, sz), biome, np.int32)
        self.be = {}

    # coordinate helpers -------------------------------------------------
    def inside(self, x, y, z):
        return (0 <= x - self.x0 < self.sx) and (0 <= y - self.y0 < self.sy) and (0 <= z - self.z0 < self.sz)

    def set(self, x, y, z, b):
        if self.inside(x, y, z):
            self.blk[x - self.x0, y - self.y0, z - self.z0] = b

    def setw(self, x, y, z, b):
        """Set a block that sits inside water (waterlogged plants etc)."""
        if self.inside(x, y, z):
            self.blk[x - self.x0, y - self.y0, z - self.z0] = b
            self.wet[x - self.x0, y - self.y0, z - self.z0] = True

    def put(self, x, y, z, b):
        """Set only if currently air."""
        if self.inside(x, y, z) and self.blk[x - self.x0, y - self.y0, z - self.z0] == 0:
            self.blk[x - self.x0, y - self.y0, z - self.z0] = b

    def get(self, x, y, z):
        if self.inside(x, y, z):
            return int(self.blk[x - self.x0, y - self.y0, z - self.z0])
        return 0

    def _box(self, x1, y1, z1, x2, y2, z2):
        xa, xb = sorted((x1, x2)); ya, yb = sorted((y1, y2)); za, zb = sorted((z1, z2))
        xa = max(xa, self.x0); xb = min(xb, self.x0 + self.sx - 1)
        ya = max(ya, self.y0); yb = min(yb, self.y0 + self.sy - 1)
        za = max(za, self.z0); zb = min(zb, self.z0 + self.sz - 1)
        if xa > xb or ya > yb or za > zb:
            return None
        return (slice(xa - self.x0, xb - self.x0 + 1), slice(ya - self.y0, yb - self.y0 + 1),
                slice(za - self.z0, zb - self.z0 + 1))

    def fill(self, x1, y1, z1, x2, y2, z2, b, only_air=False):
        s = self._box(x1, y1, z1, x2, y2, z2)
        if s is None:
            return
        if only_air:
            v = self.blk[s]
            v[v == 0] = b
        else:
            self.blk[s] = b
            self.wet[s] = False

    def replace(self, x1, y1, z1, x2, y2, z2, src, dst):
        s = self._box(x1, y1, z1, x2, y2, z2)
        if s is None:
            return
        v = self.blk[s]
        v[v == src] = dst

    def hollow(self, x1, y1, z1, x2, y2, z2, wall, inside=AIR):
        self.fill(x1, y1, z1, x2, y2, z2, wall)
        xa, xb = sorted((x1, x2)); ya, yb = sorted((y1, y2)); za, zb = sorted((z1, z2))
        if xb - xa > 1 and yb - ya > 1 and zb - za > 1:
            self.fill(xa + 1, ya + 1, za + 1, xb - 1, yb - 1, zb - 1, inside)

    def column_top(self, x, z, ymax=None, solid_only=True, htab=None):
        """Highest y whose block is non-air (or full-collision when htab given)."""
        if not (0 <= x - self.x0 < self.sx and 0 <= z - self.z0 < self.sz):
            return None
        col = self.blk[x - self.x0, :, z - self.z0]
        top = self.sy - 1 if ymax is None else min(ymax - self.y0, self.sy - 1)
        for i in range(top, -1, -1):
            b = col[i]
            if b != 0 and (htab is None or htab[b] >= 2):
                return i + self.y0
        return None

    def add_be(self, nbt):
        x, y, z = int(nbt["x"].py_int), int(nbt["y"].py_int), int(nbt["z"].py_int)
        self.be[(x, y, z)] = nbt

    # post processing ----------------------------------------------------
    def fix_walls(self):
        """Compute Bedrock wall connection states from neighbours."""
        names = PAL.names
        wall_ids = [i for i, n in enumerate(names) if n.endswith("_wall") and "sign" not in n and "banner" not in n]
        if not wall_ids:
            return
        htab, liq, _ = physics_tables()
        is_wall = np.zeros(len(names), bool)
        is_wall[wall_ids] = True
        connect = np.zeros(len(names), bool)
        for i, n in enumerate(names):
            if is_wall[i] or n.endswith("fence_gate") or n == "fence_gate" or n.endswith("glass_pane") \
                    or n == "iron_bars" or (htab[i] == 2 and "leaves" not in n and not n.endswith("_stairs")
                                            and not n.endswith("_slab") and n not in LOW_EXACT):
                connect[i] = True
        pos = np.argwhere(is_wall[self.blk])
        updates = []
        for x, y, z in pos:
            b = self.blk[x, y, z]
            name = names[b]
            above = self.blk[x, y + 1, z] if y + 1 < self.sy else 0
            above_solid = above != 0 and (htab[above] >= 2)
            conns = {}
            for dname, dx, dz in (("north", 0, -1), ("south", 0, 1), ("west", -1, 0), ("east", 1, 0)):
                nx, nz = x + dx, z + dz
                if 0 <= nx < self.sx and 0 <= nz < self.sz:
                    nb = self.blk[nx, y, nz]
                    if connect[nb]:
                        up_n = self.blk[nx, y + 1, nz] if y + 1 < self.sy else 0
                        tall = above_solid and up_n != 0
                        conns[dname] = "tall" if tall else "short"
            straight = (set(conns) == {"north", "south"} or set(conns) == {"east", "west"})
            post = 0 if (straight and not is_wall[above]) else 1
            if above != 0 and not is_wall[above] and htab[above] >= 1:
                post = 1 if not straight else post
            st = {"wall_connection_type_" + d: conns.get(d, "none") for d in ("north", "south", "west", "east")}
            st["wall_post_bit"] = post
            updates.append((x, y, z, name, st))
        for x, y, z, name, st in updates:
            self.blk[x, y, z] = PAL.get(name, st)

    # export ------------------------------------------------------------
    def chunks(self):
        for cx in range(self.x0 // 16, (self.x0 + self.sx) // 16):
            for cz in range(self.z0 // 16, (self.z0 + self.sz) // 16):
                yield cx, cz

    def encode_chunk(self, cx, cz):
        lx, lz = cx * 16 - self.x0, cz * 16 - self.z0
        sub = self.blk[lx:lx + 16, :, lz:lz + 16]
        wet = self.wet[lx:lx + 16, :, lz:lz + 16]
        out = {}
        key = struct.pack("<ii", cx, cz)
        nsec = self.sy // 16
        for s in range(nsec):
            blk = sub[:, s * 16:(s + 1) * 16, :]
            if not blk.any():
                continue
            cy = (self.y0 // 16) + s
            layers = [blk]
            w = wet[:, s * 16:(s + 1) * 16, :]
            if w.any():
                layers.append(np.where(w, B("water"), 0).astype(np.uint16))
            data = bytearray([9, len(layers), cy & 0xFF])
            for lay in layers:
                data += encode_storage(lay)
            out[key + bytes([0x2F, cy & 0xFF])] = bytes(data)
        # heightmap (index z*16+x, value = top+1 - (-64))
        nonair = sub != 0
        any_col = nonair.any(axis=1)
        top_idx = self.sy - 1 - np.argmax(nonair[:, ::-1, :], axis=1)
        hm = np.where(any_col, top_idx + self.y0 + 1 + 64, 0).astype("<i2")   # [x, z]
        hm_bytes = hm.T.copy().tobytes()
        bio = self.bio[lx:lx + 16, lz:lz + 16]
        out[key + b"\x2b"] = hm_bytes + encode_biomes(bio)
        out[key + b"\x2c"] = bytes([CHUNK_VERSION])
        out[key + b"\x36"] = struct.pack("<i", 2)
        out[key + b"\x40"] = b"\x00\x0a"
        out[key + b"\x41"] = b"\x00"
        bes = [v for (x, y, z), v in self.be.items() if x // 16 == cx and z // 16 == cz]
        if bes:
            out[key + b"\x31"] = b"".join(an.NamedTag(v, "").to_nbt(compressed=False, little_endian=True)
                                           for v in bes)
        return out


_BITS = (1, 2, 3, 4, 5, 6, 8, 16)


def _pack(idx, bits):
    bpw = 32 // bits
    nwords = -(-4096 // bpw)
    pad = np.zeros(nwords * bpw, np.uint64)
    pad[:4096] = idx
    pad = pad.reshape(nwords, bpw)
    shifts = (np.arange(bpw, dtype=np.uint64) * np.uint64(bits))
    words = np.bitwise_or.reduce(pad << shifts, axis=1).astype("<u4")
    return words.tobytes()


def encode_storage(blk):
    """blk: (16,16,16) array [x, y, z] of global palette ids."""
    flat = np.transpose(blk, (0, 2, 1)).reshape(-1)          # XZY order
    uniq, inv = np.unique(flat, return_inverse=True)
    n = len(uniq)
    bits = next(b for b in _BITS if (1 << b) >= n)
    data = bytearray([bits << 1])
    data += _pack(inv.astype(np.uint64), bits)
    data += struct.pack("<i", n)
    for u in uniq:
        data += PAL.nbt[u]
    return bytes(data)


def encode_biomes(bio):
    """bio: (16,16) [x, z] biome ids, same for every height; 24 sections (-64..320)."""
    uniq, inv = np.unique(bio.reshape(-1), return_inverse=True)
    if len(uniq) == 1:
        first = bytes([0]) + struct.pack("<i", int(uniq[0]))
    else:
        bits = next(b for b in _BITS if (1 << b) >= len(uniq))
        inv = inv.reshape(16, 16)
        idx = np.repeat(inv[:, :, None], 16, axis=2).reshape(-1)   # XZY
        first = bytes([bits << 1]) + _pack(idx.astype(np.uint64), bits) + struct.pack("<i", len(uniq))
        first += b"".join(struct.pack("<i", int(u)) for u in uniq)
    return first + b"\xff" * 23


# ---------------------------------------------------------------------------

def write_level_dat(path, template, changes):
    raw = open(template, "rb").read()
    root = an.load(raw[8:], compressed=False, little_endian=True)
    tag = root.compound
    for k, v in changes.items():
        tag[k] = v
    body = an.NamedTag(tag, "").to_nbt(compressed=False, little_endian=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<ii", 10, len(body)))
        f.write(body)


def write_db(areas, db_path):
    from leveldb import LevelDB
    db = LevelDB(db_path, create_if_missing=True)
    nkeys = 0
    for area in areas:
        for cx, cz in area.chunks():
            batch = area.encode_chunk(cx, cz)
            db.putBatch(batch)
            nkeys += len(batch)
    db.close()
    return nkeys


def zip_dir(src, dst):
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(src):
            for f in sorted(files):
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, src))
