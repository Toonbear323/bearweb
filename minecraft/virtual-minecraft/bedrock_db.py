"""Read Minecraft Bedrock worlds with nothing but the Python standard library.

- LevelDB (Mojang's fork): .ldb/.sst tables and .log files with zlib / raw-deflate blocks
- little-endian NBT (level.dat, block palettes, entities, block entities)
- sub-chunk block storage (formats 1/8/9), entities (actorprefix and legacy), block entities
- diff_worlds(): which blocks, entities and block entities differ between two copies of a world
"""
import collections
import os
import struct
import zlib

# ----------------------------------------------------------------------------- varints


def _varint(b, o):
    r = s = 0
    while True:
        x = b[o]
        o += 1
        r |= (x & 0x7F) << s
        if x < 0x80:
            return r, o
        s += 7


# ----------------------------------------------------------------------------- NBT (little endian)


def _nbt_payload(t, b, o):
    if t == 1:
        return struct.unpack_from("<b", b, o)[0], o + 1
    if t == 2:
        return struct.unpack_from("<h", b, o)[0], o + 2
    if t == 3:
        return struct.unpack_from("<i", b, o)[0], o + 4
    if t == 4:
        return struct.unpack_from("<q", b, o)[0], o + 8
    if t == 5:
        return struct.unpack_from("<f", b, o)[0], o + 4
    if t == 6:
        return struct.unpack_from("<d", b, o)[0], o + 8
    if t == 7:
        n = struct.unpack_from("<i", b, o)[0]
        return bytes(b[o + 4:o + 4 + n]), o + 4 + n
    if t == 8:
        n = struct.unpack_from("<H", b, o)[0]
        return bytes(b[o + 2:o + 2 + n]).decode("utf-8", "replace"), o + 2 + n
    if t == 9:
        et = b[o]
        n = struct.unpack_from("<i", b, o + 1)[0]
        o += 5
        out = []
        for _ in range(max(n, 0)):
            v, o = _nbt_payload(et, b, o)
            out.append(v)
        return out, o
    if t == 10:
        d = {}
        while True:
            tt = b[o]
            o += 1
            if tt == 0:
                return d, o
            n = struct.unpack_from("<H", b, o)[0]
            name = bytes(b[o + 2:o + 2 + n]).decode("utf-8", "replace")
            o += 2 + n
            d[name], o = _nbt_payload(tt, b, o)
    if t == 11:
        n = struct.unpack_from("<i", b, o)[0]
        return list(struct.unpack_from("<%di" % n, b, o + 4)), o + 4 + 4 * n
    if t == 12:
        n = struct.unpack_from("<i", b, o)[0]
        return list(struct.unpack_from("<%dq" % n, b, o + 4)), o + 4 + 8 * n
    raise ValueError("unknown NBT tag %d" % t)


def read_nbt(b, o=0):
    """One named tag at offset o -> (value, new offset)."""
    t = b[o]
    n = struct.unpack_from("<H", b, o + 1)[0]
    return _nbt_payload(t, b, o + 3 + n)


def read_nbt_all(b):
    """Concatenated tags (block entities, legacy entities) -> list of values."""
    out, o = [], 0
    while o < len(b):
        if b[o] == 0:
            break
        v, o = read_nbt(b, o)
        out.append(v)
    return out


# ----------------------------------------------------------------------------- LevelDB

TABLE_MAGIC = 0xDB4775248B80FB57
LOG_BLOCK = 32768


def _snappy(src):
    n, o = _varint(src, 0)
    out = bytearray()
    while o < len(src):
        tag = src[o]
        o += 1
        kind = tag & 3
        if kind == 0:
            ln = tag >> 2
            if ln >= 60:
                nb = ln - 59
                ln = int.from_bytes(src[o:o + nb], "little")
                o += nb
            ln += 1
            out += src[o:o + ln]
            o += ln
            continue
        if kind == 1:
            ln = ((tag >> 2) & 7) + 4
            off = ((tag >> 5) << 8) | src[o]
            o += 1
        elif kind == 2:
            ln = (tag >> 2) + 1
            off = struct.unpack_from("<H", src, o)[0]
            o += 2
        else:
            ln = (tag >> 2) + 1
            off = struct.unpack_from("<I", src, o)[0]
            o += 4
        for _ in range(ln):
            out.append(out[-off])
    return bytes(out[:n])


def _block(data, off, size):
    raw = data[off:off + size]
    kind = data[off + size]
    if kind == 0:
        return raw
    if kind == 2:
        return zlib.decompress(raw)
    if kind == 4:
        return zlib.decompress(raw, -15)
    if kind == 1:
        return _snappy(raw)
    raise ValueError("unknown LevelDB block compression %d" % kind)


def _block_entries(blk):
    nrest = struct.unpack_from("<I", blk, len(blk) - 4)[0]
    end = len(blk) - 4 - 4 * nrest
    o, key = 0, b""
    while o < end:
        shared, o = _varint(blk, o)
        nonshared, o = _varint(blk, o)
        vlen, o = _varint(blk, o)
        key = key[:shared] + blk[o:o + nonshared]
        o += nonshared
        yield key, blk[o:o + vlen]
        o += vlen


def _put(out, key, seq, value):
    old = out.get(key)
    if old is None or old[0] < seq:
        out[key] = (seq, value)


def _read_table(path, out):
    data = open(path, "rb").read()
    if len(data) < 48 or struct.unpack_from("<Q", data, len(data) - 8)[0] != TABLE_MAGIC:
        return
    footer = data[-48:]
    o = 0
    for _ in range(2):              # metaindex handle (unused)
        _, o = _varint(footer, o)
    io_, o = _varint(footer, o)
    is_, o = _varint(footer, o)
    for _k, handle in _block_entries(_block(data, io_, is_)):
        bo, p = _varint(handle, 0)
        bs, p = _varint(handle, p)
        for ikey, val in _block_entries(_block(data, bo, bs)):
            tag = struct.unpack_from("<Q", ikey, len(ikey) - 8)[0]
            _put(out, ikey[:-8], tag >> 8, val if tag & 0xFF == 1 else None)


def _log_records(data):
    o, buf = 0, b""
    while o + 7 <= len(data):
        left = LOG_BLOCK - o % LOG_BLOCK
        if left < 7:
            o += left
            continue
        _crc, length, kind = struct.unpack_from("<IHB", data, o)
        if kind == 0 and length == 0:
            o += left
            continue
        o += 7
        if o + length > len(data):
            return                    # torn write at the end of the file
        frag = data[o:o + length]
        o += length
        if kind == 1:
            yield frag
        elif kind == 2:
            buf = frag
        elif kind == 3:
            buf += frag
        elif kind == 4:
            yield buf + frag
            buf = b""


def _read_log(path, out):
    for rec in _log_records(open(path, "rb").read()):
        if len(rec) < 12:
            continue
        seq, count = struct.unpack_from("<QI", rec, 0)
        o = 12
        try:
            for i in range(count):
                kind = rec[o]
                o += 1
                n, o = _varint(rec, o)
                key = rec[o:o + n]
                o += n
                val = None
                if kind == 1:
                    n, o = _varint(rec, o)
                    val = rec[o:o + n]
                    o += n
                _put(out, key, seq + i, val)
        except IndexError:
            pass


def _manifest(dbdir):
    """Live table numbers and the oldest log still needed, or None (then every file is read)."""
    try:
        name = open(os.path.join(dbdir, "CURRENT")).read().strip()
        data = open(os.path.join(dbdir, name), "rb").read()
    except OSError:
        return None
    live, log_no, prev_log = set(), 0, 0
    try:
        for rec in _log_records(data):
            o = 0
            while o < len(rec):
                tag, o = _varint(rec, o)
                if tag == 1:
                    n, o = _varint(rec, o)
                    o += n
                elif tag == 2:
                    log_no, o = _varint(rec, o)
                elif tag in (3, 4):
                    _, o = _varint(rec, o)
                elif tag == 5:
                    _, o = _varint(rec, o)
                    n, o = _varint(rec, o)
                    o += n
                elif tag == 6:
                    _, o = _varint(rec, o)
                    f, o = _varint(rec, o)
                    live.discard(f)
                elif tag == 7:
                    _, o = _varint(rec, o)
                    f, o = _varint(rec, o)
                    _, o = _varint(rec, o)
                    for _ in range(2):
                        n, o = _varint(rec, o)
                        o += n
                    live.add(f)
                elif tag == 9:
                    prev_log, o = _varint(rec, o)
                else:
                    return None
    except IndexError:
        return None
    return live, log_no, prev_log


def read_leveldb(dbdir):
    """Every live key of a LevelDB folder -> {key: value}."""
    files = []
    for fn in os.listdir(dbdir):
        stem, ext = os.path.splitext(fn)
        if ext in (".ldb", ".sst", ".log") and stem.isdigit():
            files.append((int(stem), ext, os.path.join(dbdir, fn)))
    man = _manifest(dbdir)
    out = {}
    for num, ext, path in sorted(files):
        if ext == ".log":
            if man is None or num >= man[1] or num == man[2]:
                _read_log(path, out)
        elif man is None or num in man[0]:
            _read_table(path, out)
    return {k: v for k, (_s, v) in out.items() if v is not None}


# ----------------------------------------------------------------------------- world

TAG_DATA3D, TAG_VERSION, TAG_SUBCHUNK, TAG_BLOCK_ENTITY, TAG_ENTITY, TAG_LEGACY_VERSION = 43, 44, 47, 49, 50, 118
CHUNK_TAGS = set(range(43, 65)) | {TAG_LEGACY_VERSION}
DIM_NAMES = {0: "오버월드", 1: "네더", 2: "엔드"}


def parse_chunk_key(k):
    """(dim, cx, cz, tag, subchunk index or None) for chunk records, None for other keys."""
    n = len(k)
    if n in (9, 10):
        cx, cz = struct.unpack_from("<ii", k)
        dim, p = 0, 8
    elif n in (13, 14):
        cx, cz, dim = struct.unpack_from("<iii", k)
        if dim not in (1, 2):
            return None
        p = 12
    else:
        return None
    tag = k[p]
    if tag not in CHUNK_TAGS:
        return None
    if n in (10, 14):
        if tag != TAG_SUBCHUNK:
            return None
        return dim, cx, cz, tag, struct.unpack_from("<b", k, p + 1)[0]
    return dim, cx, cz, tag, None


def block_key(c):
    """Palette compound -> hashable (name, ((state, value), ...))."""
    name = c.get("name", "?")
    if name.startswith("minecraft:"):
        name = name[10:]
    st = c.get("states")
    if isinstance(st, dict):
        return name, tuple(sorted(st.items()))
    if "val" in c:
        return name, (("val", c["val"]),)
    return name, ()


def decode_subchunk(v):
    """Sub-chunk record -> list of layers (indices[4096] or None for all-zero, palette keys).
    Index order is x*256 + z*16 + y. Returns None for formats this reader does not know."""
    ver = v[0]
    if ver == 1:
        nlayers, o = 1, 1
    elif ver == 8:
        nlayers, o = v[1], 2
    elif ver == 9:
        nlayers, o = v[1], 3
    else:
        return None
    layers = []
    for _ in range(nlayers):
        h = v[o]
        o += 1
        bits = h >> 1
        if bits == 0:
            idx, count = None, 1
        else:
            per = 32 // bits
            nw = -(-4096 // per)
            words = struct.unpack_from("<%dI" % nw, v, o)
            o += 4 * nw
            mask = (1 << bits) - 1
            shifts = [i * bits for i in range(per)]
            idx = [(w >> s) & mask for w in words for s in shifts]
            del idx[4096:]
            count = struct.unpack_from("<i", v, o)[0]
            o += 4
        pal = []
        for _ in range(count):
            c, o = read_nbt(v, o)
            pal.append(block_key(c))
        layers.append((idx, pal))
    return layers


class World:
    """A world folder (the one holding level.dat and db/)."""

    def __init__(self, path):
        self.path = path
        self.level = read_level_dat(os.path.join(path, "level.dat"))
        self.db = read_leveldb(os.path.join(path, "db"))
        self.chunks = collections.defaultdict(dict)     # (dim, cx, cz) -> {(tag, sub): value}
        self.actors = {}
        for k, v in self.db.items():
            if k.startswith(b"actorprefix"):
                self.actors[k] = v
                continue
            p = parse_chunk_key(k)
            if p:
                self.chunks[p[:3]][(p[3], p[4])] = v

    @property
    def name(self):
        return self.level.get("LevelName") or os.path.basename(self.path)

    @property
    def spawn(self):
        lv = self.level
        return lv.get("SpawnX", 0), lv.get("SpawnY", 64), lv.get("SpawnZ", 0)

    def chunk_exists(self, key):
        recs = self.chunks.get(key)
        return bool(recs) and ((TAG_VERSION, None) in recs or (TAG_LEGACY_VERSION, None) in recs)

    def chunk_keys(self, dim=0):
        return [k for k in self.chunks if k[0] == dim and self.chunk_exists(k)]

    def entities(self):
        """[(identifier, (x, y, z), custom name)] from both storage formats."""
        out = []
        for v in self.actors.values():
            try:
                out.append(_entity(read_nbt(v)[0]))
            except Exception:
                pass
        for recs in self.chunks.values():
            v = recs.get((TAG_ENTITY, None))
            if v:
                try:
                    out.extend(_entity(c) for c in read_nbt_all(v))
                except Exception:
                    pass
        return out

    def block_entities(self):
        """{(dim, x, y, z): id}"""
        out = {}
        for (dim, _cx, _cz), recs in self.chunks.items():
            v = recs.get((TAG_BLOCK_ENTITY, None))
            if not v:
                continue
            try:
                for c in read_nbt_all(v):
                    out[(dim, c.get("x", 0), c.get("y", 0), c.get("z", 0))] = c.get("id", "?")
            except Exception:
                pass
        return out


def _entity(c):
    ident = c.get("identifier", c.get("id", "?"))
    if isinstance(ident, str) and ident.startswith("minecraft:"):
        ident = ident[10:]
    pos = c.get("Pos") or [0, 0, 0]
    return str(ident), tuple(round(p, 1) for p in pos[:3]), c.get("CustomName", "")


def read_level_dat(path):
    data = open(path, "rb").read()
    try:
        return read_nbt(data, 8)[0]
    except Exception:
        return {}


# ----------------------------------------------------------------------------- diff


def _blocks(layer, gid):
    idx, pal = layer
    ids = [gid(k) for k in pal]
    if idx is None:
        return [ids[0]] * 4096
    try:
        return [ids[i] for i in idx]
    except IndexError:                # index past the palette: treat as the first entry
        return [ids[i] if i < len(ids) else ids[0] for i in idx]


def diff_worlds(a, b, max_examples=3):
    """Block, entity and block-entity differences between World a (before) and b (after)."""
    keys, key_id = [], {}

    def gid(k):
        i = key_id.get(k)
        if i is None:
            i = key_id[k] = len(keys)
            keys.append(k)
        return i

    air = [gid(("air", ()))] * 4096
    changes = collections.Counter()
    examples = collections.defaultdict(list)
    res = dict(compared=0, changed_subchunks=0, new_chunks=[], removed_chunks=[], unreadable=0)
    for ck in sorted(set(a.chunks) | set(b.chunks)):
        ea, eb = a.chunk_exists(ck), b.chunk_exists(ck)
        if not ea and eb:
            res["new_chunks"].append(ck)
            continue
        if ea and not eb:
            if not b.chunks.get(ck):
                res["removed_chunks"].append(ck)
            continue
        ra, rb = a.chunks.get(ck, {}), b.chunks.get(ck, {})
        subs = {s for (t, s) in ra if t == TAG_SUBCHUNK} | {s for (t, s) in rb if t == TAG_SUBCHUNK}
        dim, cx, cz = ck
        for s in sorted(subs):
            va, vb = ra.get((TAG_SUBCHUNK, s)), rb.get((TAG_SUBCHUNK, s))
            res["compared"] += 1
            if va == vb:
                continue
            la = decode_subchunk(va) if va else []
            lb = decode_subchunk(vb) if vb else []
            if la is None or lb is None:
                res["unreadable"] += 1
                continue
            changed = False
            for li in range(max(len(la), len(lb), 1)):
                ba = _blocks(la[li], gid) if li < len(la) else air
                bb = _blocks(lb[li], gid) if li < len(lb) else air
                if ba == bb:
                    continue
                changed = True
                for i in range(4096):
                    x, y = ba[i], bb[i]
                    if x != y:
                        ck2 = (li, x, y)
                        changes[ck2] += 1
                        if len(examples[ck2]) < max_examples:
                            examples[ck2].append((dim, cx * 16 + (i >> 8), s * 16 + (i & 15),
                                                  cz * 16 + ((i >> 4) & 15)))
            if changed:
                res["changed_subchunks"] += 1
    res["blocks"] = [(li, keys[x], keys[y], n, examples[(li, x, y)])
                     for (li, x, y), n in changes.most_common()]
    ent_a = collections.Counter(e[0] for e in a.entities())
    ent_b = collections.Counter(e[0] for e in b.entities())
    res["entities"] = sorted((k, ent_a[k], ent_b[k]) for k in set(ent_a) | set(ent_b))
    be_a, be_b = a.block_entities(), b.block_entities()
    lost = collections.Counter(be_a[p] for p in be_a if p not in be_b)
    gained = collections.Counter(be_b[p] for p in be_b if p not in be_a)
    res["block_entities_lost"] = lost.most_common()
    res["block_entities_new"] = gained.most_common()
    res["block_entities_lost_at"] = [p for p in be_a if p not in be_b][:max_examples * 5]
    return res
