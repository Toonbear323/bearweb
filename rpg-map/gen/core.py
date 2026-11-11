"""Core data model for the Bear RPG map generator.

* block registry validated against the Bedrock 1.21.0 block-state table
* World: dense numpy voxel volume + block entities + biomes
* tiny little-endian NBT writer (the on-disk Bedrock flavour)
"""
import json
import os
import struct

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, "blockspec_1_21_0.json")))
BLOCK_VERSION = 18153475  # 1.21.0.3

# ----------------------------------------------------------------------------
# NBT (little endian, uncompressed)
# ----------------------------------------------------------------------------


class Byte(int):
    pass


class Short(int):
    pass


class Long(int):
    pass


class Float(float):
    pass


def _tag_id(v):
    if isinstance(v, bool):
        return 1
    if isinstance(v, Byte):
        return 1
    if isinstance(v, Short):
        return 2
    if isinstance(v, Long):
        return 4
    if isinstance(v, int):
        return 3
    if isinstance(v, float):
        return 5
    if isinstance(v, str):
        return 8
    if isinstance(v, (list, tuple)):
        return 9
    if isinstance(v, dict):
        return 10
    raise TypeError(type(v))


def _payload(v, out):
    t = _tag_id(v)
    if t == 1:
        out.append(struct.pack("<b", int(v)))
    elif t == 2:
        out.append(struct.pack("<h", int(v)))
    elif t == 3:
        out.append(struct.pack("<i", int(v)))
    elif t == 4:
        out.append(struct.pack("<q", int(v)))
    elif t == 5:
        out.append(struct.pack("<f", float(v)))
    elif t == 8:
        b = v.encode("utf-8")
        out.append(struct.pack("<H", len(b)))
        out.append(b)
    elif t == 9:
        et = _tag_id(v[0]) if len(v) else 0
        out.append(struct.pack("<bi", et, len(v)))
        for e in v:
            assert _tag_id(e) == et, "mixed list"
            _payload(e, out)
    elif t == 10:
        for k, e in v.items():
            kb = k.encode("utf-8")
            out.append(struct.pack("<bH", _tag_id(e), len(kb)))
            out.append(kb)
            _payload(e, out)
        out.append(b"\x00")
    return t


def nbt(compound, name=""):
    """Serialise a dict as a named root compound (little endian)."""
    out = []
    nb = name.encode("utf-8")
    out.append(struct.pack("<bH", 10, len(nb)))
    out.append(nb)
    _payload(compound, out)
    return b"".join(out)


# ----------------------------------------------------------------------------
# Block registry
# ----------------------------------------------------------------------------


def _parse(lit):
    if lit.startswith('"'):
        return ("s", lit[1:-1])
    if lit.endswith("b"):
        return ("b", int(lit[:-1]))
    return ("i", int(lit))


class Registry:
    def __init__(self):
        self.entries = []  # (name, ((key, type, value), ...))
        self.index = {}
        self._cache = {}
        self._nbt = {}

    def id(self, name, **st):
        key = (name, tuple(sorted(st.items())))
        r = self._cache.get(key)
        if r is not None:
            return r
        if name not in SPEC:
            raise KeyError("unknown block %r" % name)
        spec = SPEC[name]
        props = spec["p"]
        vals = {}
        for k, lit in spec["d"].items():
            vals[k] = _parse(lit)
        for k, v in st.items():
            pk = k if k in props else "minecraft:" + k
            if pk not in props:
                raise KeyError("block %s has no state %r (has %s)" % (name, k, list(props)))
            typ = _parse(props[pk][0])[0]
            if typ == "s":
                lit = '"%s"' % v
                pv = ("s", str(v))
            elif typ == "b":
                lit = "%db" % int(v)
                pv = ("b", int(v))
            else:
                lit = "%d" % int(v)
                pv = ("i", int(v))
            if lit not in props[pk]:
                raise ValueError("block %s state %s=%r not in %s" % (name, pk, v, props[pk]))
            vals[pk] = pv
        ent = (name, tuple(sorted((k, t, v) for k, (t, v) in vals.items())))
        r = self.index.get(ent)
        if r is None:
            r = len(self.entries)
            self.entries.append(ent)
            self.index[ent] = r
        self._cache[key] = r
        return r

    def name(self, i):
        return self.entries[i][0]

    def states(self, i):
        return {k: v for k, t, v in self.entries[i][1]}

    def with_state(self, i, **st):
        name, cur = self.entries[i]
        d = {k: v for k, t, v in cur}
        d.update({(k if k in d else "minecraft:" + k): v for k, v in st.items()})
        return self.id(name, **d)

    def palette_nbt(self, i):
        b = self._nbt.get(i)
        if b is None:
            name, st = self.entries[i]
            states = {}
            for k, t, v in st:
                states[k] = Byte(v) if t == "b" else (int(v) if t == "i" else str(v))
            b = nbt({"name": "minecraft:" + name, "states": states, "version": BLOCK_VERSION})
            self._nbt[i] = b
        return b


REG = Registry()
B = REG.id
AIR = B("air")
assert AIR == 0


class Mix:
    """Weighted random block choice used for textured fills."""

    def __init__(self, *pairs):
        ids, w = [], []
        for p in pairs:
            if isinstance(p, (tuple, list)):
                ids.append(p[0])
                w.append(p[1])
            else:
                ids.append(p)
                w.append(1)
        self.ids = np.array(ids, np.uint16)
        w = np.array(w, float)
        self.p = w / w.sum()

    def sample(self, rng, shape=None):
        if shape is None:
            return int(self.ids[rng.choice(len(self.ids), p=self.p)])
        return self.ids[rng.choice(len(self.ids), size=shape, p=self.p)]


def bid(b, rng):
    """Resolve a block spec (int or Mix) to a single id."""
    if isinstance(b, Mix):
        return b.sample(rng)
    return b


# ----------------------------------------------------------------------------
# World
# ----------------------------------------------------------------------------

DIRS = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}
CW = {"N": "E", "E": "S", "S": "W", "W": "N"}
CCW = {v: k for k, v in CW.items()}


class World:
    def __init__(self, x0, z0, x1, z1, y0, y1, dim=0, biome=1, seed=1):
        assert x0 % 16 == 0 and z0 % 16 == 0 and x1 % 16 == 0 and z1 % 16 == 0
        assert y0 % 16 == 0 and y1 % 16 == 0
        self.x0, self.z0, self.x1, self.z1, self.y0, self.y1 = x0, z0, x1, z1, y0, y1
        self.sx, self.sz, self.sy = x1 - x0, z1 - z0, y1 - y0
        self.dim = dim
        self.b = np.zeros((self.sx, self.sz, self.sy), np.uint16)
        self.wl = np.zeros((self.sx, self.sz, self.sy), bool)  # waterlogged layer
        self.be = {}
        self.biome = np.full((self.sx, self.sz), biome, np.uint8)
        self.biome_boxes = []
        self.rng = np.random.default_rng(seed)

    def shift(self, dx, dz):
        """Translate the whole volume horizontally (dx, dz multiples of 16)."""
        assert dx % 16 == 0 and dz % 16 == 0
        self.x0 += dx
        self.x1 += dx
        self.z0 += dz
        self.z1 += dz
        be = {}
        for (x, y, z), d in self.be.items():
            d["x"] = x + dx
            d["z"] = z + dz
            be[(x + dx, y, z + dz)] = d
        self.be = be
        self.biome_boxes = [(a + dx, b, c + dz, d + dx, e, f + dz, g) for (a, b, c, d, e, f, g) in self.biome_boxes]

    # -- basic access -------------------------------------------------------
    def inb(self, x, y, z):
        return self.x0 <= x < self.x1 and self.z0 <= z < self.z1 and self.y0 <= y < self.y1

    def get(self, x, y, z):
        if not self.inb(x, y, z):
            return 0
        return int(self.b[x - self.x0, z - self.z0, y - self.y0])

    def set(self, x, y, z, b, keep=False):
        if not self.inb(x, y, z):
            return
        if keep and self.b[x - self.x0, z - self.z0, y - self.y0] != 0:
            return
        if isinstance(b, Mix):
            b = b.sample(self.rng)
        self.b[x - self.x0, z - self.z0, y - self.y0] = b
        self.be.pop((x, y, z), None)

    def _clip(self, xa, ya, za, xb, yb, zb):
        if xa > xb:
            xa, xb = xb, xa
        if ya > yb:
            ya, yb = yb, ya
        if za > zb:
            za, zb = zb, za
        xa, xb = max(xa, self.x0), min(xb, self.x1 - 1)
        ya, yb = max(ya, self.y0), min(yb, self.y1 - 1)
        za, zb = max(za, self.z0), min(zb, self.z1 - 1)
        if xa > xb or ya > yb or za > zb:
            return None
        return (slice(xa - self.x0, xb + 1 - self.x0), slice(za - self.z0, zb + 1 - self.z0),
                slice(ya - self.y0, yb + 1 - self.y0))

    def view(self, xa, ya, za, xb, yb, zb):
        s = self._clip(xa, ya, za, xb, yb, zb)
        return None if s is None else self.b[s]

    def fill(self, xa, ya, za, xb, yb, zb, b, keep=False, only=None):
        """Inclusive box fill. keep=True only replaces air; only=ids restricts targets."""
        s = self._clip(xa, ya, za, xb, yb, zb)
        if s is None:
            return
        v = self.b[s]
        val = b.sample(self.rng, v.shape) if isinstance(b, Mix) else b
        if keep:
            m = v == 0
            v[m] = val[m] if isinstance(val, np.ndarray) else val
        elif only is not None:
            m = np.isin(v, list(only))
            v[m] = val[m] if isinstance(val, np.ndarray) else val
        else:
            v[...] = val
            if self.be:
                self._drop_be(xa, ya, za, xb, yb, zb)

    def _drop_be(self, xa, ya, za, xb, yb, zb):
        if xa > xb:
            xa, xb = xb, xa
        if ya > yb:
            ya, yb = yb, ya
        if za > zb:
            za, zb = zb, za
        if (xb - xa + 1) * (yb - ya + 1) * (zb - za + 1) < len(self.be):
            for x in range(xa, xb + 1):
                for y in range(ya, yb + 1):
                    for z in range(za, zb + 1):
                        self.be.pop((x, y, z), None)
        else:
            for k in [k for k in self.be if xa <= k[0] <= xb and ya <= k[1] <= yb and za <= k[2] <= zb]:
                del self.be[k]

    def walls(self, xa, ya, za, xb, yb, zb, b):
        """Four vertical walls of a box."""
        self.fill(xa, ya, za, xb, yb, za, b)
        self.fill(xa, ya, zb, xb, yb, zb, b)
        self.fill(xa, ya, za, xa, yb, zb, b)
        self.fill(xb, ya, za, xb, yb, zb, b)

    def shell(self, xa, ya, za, xb, yb, zb, b):
        self.walls(xa, ya, za, xb, yb, zb, b)
        self.fill(xa, ya, za, xb, ya, zb, b)
        self.fill(xa, yb, za, xb, yb, zb, b)

    def top(self, x, z, ymax=None, ymin=None, ignore=None):
        """Highest non-air y in a column (or None)."""
        if not (self.x0 <= x < self.x1 and self.z0 <= z < self.z1):
            return None
        col = self.b[x - self.x0, z - self.z0]
        hi = self.sy - 1 if ymax is None else min(self.sy - 1, ymax - self.y0)
        lo = 0 if ymin is None else max(0, ymin - self.y0)
        for i in range(hi, lo - 1, -1):
            v = col[i]
            if v != 0 and (ignore is None or v not in ignore):
                return i + self.y0
        return None

    def water(self, x, y, z, on=True):
        if self.inb(x, y, z):
            self.wl[x - self.x0, z - self.z0, y - self.y0] = on

    # -- shapes -------------------------------------------------------------
    def mask_fill(self, xa, ya, za, mask, b, keep=False, only=None):
        """Apply a boolean mask [x,z,y] whose origin is (xa,ya,za)."""
        sx, sz, sy = mask.shape
        xb, yb, zb = xa + sx - 1, ya + sy - 1, za + sz - 1
        cxa, cxb = max(xa, self.x0), min(xb, self.x1 - 1)
        cya, cyb = max(ya, self.y0), min(yb, self.y1 - 1)
        cza, czb = max(za, self.z0), min(zb, self.z1 - 1)
        if cxa > cxb or cya > cyb or cza > czb:
            return
        m = mask[cxa - xa:cxb - xa + 1, cza - za:czb - za + 1, cya - ya:cyb - ya + 1]
        v = self.b[cxa - self.x0:cxb + 1 - self.x0, cza - self.z0:czb + 1 - self.z0, cya - self.y0:cyb + 1 - self.y0]
        if keep:
            m = m & (v == 0)
        if only is not None:
            m = m & np.isin(v, list(only))
        if isinstance(b, Mix):
            v[m] = b.sample(self.rng, int(m.sum()))
        else:
            v[m] = b

    def ellipsoid(self, cx, cy, cz, rx, ry, rz, b, keep=False, only=None, hollow=0.0):
        xa, xb = int(np.floor(cx - rx)), int(np.ceil(cx + rx))
        ya, yb = int(np.floor(cy - ry)), int(np.ceil(cy + ry))
        za, zb = int(np.floor(cz - rz)), int(np.ceil(cz + rz))
        X, Z, Y = np.meshgrid(np.arange(xa, xb + 1), np.arange(za, zb + 1), np.arange(ya, yb + 1), indexing="ij")
        d = ((X - cx) / max(rx, 0.01)) ** 2 + ((Y - cy) / max(ry, 0.01)) ** 2 + ((Z - cz) / max(rz, 0.01)) ** 2
        m = d <= 1.0
        if hollow:
            d2 = ((X - cx) / max(rx - hollow, 0.01)) ** 2 + ((Y - cy) / max(ry - hollow, 0.01)) ** 2 + (
                (Z - cz) / max(rz - hollow, 0.01)) ** 2
            m &= d2 > 1.0
        self.mask_fill(xa, ya, za, m, b, keep=keep, only=only)

    def sphere(self, cx, cy, cz, r, b, **kw):
        self.ellipsoid(cx, cy, cz, r, r, r, b, **kw)

    def cyl(self, cx, cz, r, ya, yb, b, keep=False, only=None, hollow=0.0):
        """Vertical cylinder; r may be fractional (x.5 gives nicer circles)."""
        if ya > yb:
            ya, yb = yb, ya
        xa, xb = int(np.floor(cx - r)), int(np.ceil(cx + r))
        za, zb = int(np.floor(cz - r)), int(np.ceil(cz + r))
        X, Z = np.meshgrid(np.arange(xa, xb + 1), np.arange(za, zb + 1), indexing="ij")
        d = (X - cx) ** 2 + (Z - cz) ** 2
        m = d <= r * r
        if hollow:
            m &= d > (r - hollow) ** 2
        m3 = np.repeat(m[:, :, None], yb - ya + 1, axis=2)
        self.mask_fill(xa, ya, za, m3, b, keep=keep, only=only)

    def line(self, p, q, b, r=0):
        x1, y1, z1 = p
        x2, y2, z2 = q
        n = int(max(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1))) + 1
        for i in range(n):
            t = i / max(n - 1, 1)
            x, y, z = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, z1 + (z2 - z1) * t
            if r <= 0:
                self.set(int(round(x)), int(round(y)), int(round(z)), b)
            else:
                self.sphere(x, y, z, r, b)

    # -- block entities -----------------------------------------------------
    def put(self, x, y, z, b, be=None):
        """Set a block together with its block-entity data."""
        if not self.inb(x, y, z):
            return
        self.set(x, y, z, b)
        if be is not None:
            d = dict(be)
            d.update({"x": x, "y": y, "z": z, "isMovable": Byte(1)})
            self.be[(x, y, z)] = d
