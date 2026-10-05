"""Compare the chunks Bedrock Dedicated Server saved against the Area you generated.

Run it in the same Python process that built the Area (block ids are indices into mcw.PAL):

    m = MyMap(...); m.build()
    checked, diffs, examples = compare(saved_world_dir, m.a)
    for key, n in diffs.most_common(): print(n, key, examples[key])

Expected, harmless differences (the game upgrading to its newest block format):
  * fence / wall / pane / iron bars connection states, stair "minecraft:corner"
  * renames such as chain -> iron_chain, extra states such as lightning_rod powered_bit
Real problems look like: a block replaced by air or water (unsupported block popped off, liquid
flowed), a state reset (e.g. chiseled_bookshelf books_stored -> 0 = missing block entity),
or 'missing subchunk' (the area was never loaded/saved - add a tickingarea).
"""
import collections
import struct

import amulet_nbt as an
import numpy as np
from leveldb import LevelDB


def decode_sub(v):
    n = v[1]
    o = 3
    layers = []
    for _ in range(n):
        bits = v[o] >> 1
        o += 1
        if bits == 0:
            idx = np.zeros(4096, np.int64)
        else:
            bpw = 32 // bits
            nw = -(-4096 // bpw)
            w = np.frombuffer(v[o:o + 4 * nw], "<u4").astype(np.uint64)
            o += 4 * nw
            idx = ((w[:, None] >> (np.arange(bpw, dtype=np.uint64) * np.uint64(bits))) &
                   np.uint64((1 << bits) - 1)).reshape(-1)[:4096].astype(np.int64)
        cnt = struct.unpack("<i", v[o:o + 4])[0] if bits else 1
        if bits:
            o += 4
        pal = []
        for _ in range(cnt):
            t = an.load(v[o:], compressed=False, little_endian=True)
            o += len(t.to_nbt(compressed=False, little_endian=True))
            c = t.compound
            st = tuple(sorted((k, c["states"][k].py_data) for k in c["states"])) if "states" in c else ()
            pal.append((c["name"].py_str.replace("minecraft:", ""), st))
        layers.append((idx.reshape(16, 16, 16), pal))   # [x][z][y]
    return layers


def compare(world_dir, area, ignore=()):
    from mcw import PAL
    db = LevelDB(world_dir + "/db")
    diffs = collections.Counter()
    examples = {}
    ref = [(n, tuple(sorted((k, v[1]) for k, v in st.items()))) for n, st in PAL.entries]
    checked = 0
    for cx, cz in area.chunks():
        for s in range(area.sy // 16):
            cy = area.y0 // 16 + s
            key = struct.pack("<ii", cx, cz) + bytes([0x2F, cy & 0xFF])
            try:
                v = db.get(key)
            except KeyError:
                v = None
            mine = area.blk[cx * 16 - area.x0:cx * 16 - area.x0 + 16, s * 16:s * 16 + 16,
                            cz * 16 - area.z0:cz * 16 - area.z0 + 16]
            if v is None:
                if mine.any():
                    diffs[("missing subchunk",)] += 1
                continue
            idx, pal = decode_sub(v)[0]
            checked += 1
            for x in range(16):
                for z in range(16):
                    for y in range(16):
                        a = ref[mine[x, y, z]]
                        b = pal[idx[x, z, y]]
                        if a[0] != b[0] or (a[1] != b[1] and a[0] not in ignore):
                            k = (a[0], b[0]) if a[0] != b[0] else (a[0] + " (state)",)
                            diffs[k] += 1
                            examples.setdefault(k, (cx * 16 + x, cy * 16 + y, cz * 16 + z, a, b))
    db.close()
    return checked, diffs, examples
