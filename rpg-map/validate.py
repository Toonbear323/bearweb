"""Independent read-back of the generated world with Amulet (run with the amulet venv)."""
import sys, collections
import amulet
lvl = amulet.load_level(sys.argv[1])
print('version', lvl.level_wrapper.version, 'dims', lvl.dimensions)
tot = 0
bad = 0
be_count = collections.Counter()
names = collections.Counter()
for dim in ('minecraft:overworld', 'minecraft:the_nether'):
    coords = list(lvl.all_chunk_coords(dim))
    print(dim, 'chunks', len(coords), 'x', min(c[0] for c in coords), max(c[0] for c in coords), 'z', min(c[1] for c in coords), max(c[1] for c in coords))
    for i, (cx, cz) in enumerate(coords):
        try:
            ch = lvl.get_chunk(cx, cz, dim)
            tot += 1
            for be in ch.block_entities:
                be_count[be.base_name] += 1
            if i % 7 == 0:
                for b in ch.block_palette.blocks:
                    names[b.namespaced_name] += 1
        except Exception as e:
            bad += 1
            if bad < 5:
                print('ERR', dim, cx, cz, repr(e)[:200])
        if i % 200 == 0:
            lvl.unload()
print('chunks ok', tot, 'bad', bad)
print('block entities', dict(be_count))
print('universal palette names sampled:', len(names))
unk = [n for n in names if 'unknown' in n or 'info_update' in n]
print('unknown-like names:', unk)
def show(x, y, z, dim='minecraft:overworld'):
    b, be = lvl.get_version_block(x, y, z, dim, ('bedrock', (1, 21, 0)))
    s = str(be)[:260].replace('\n', ' ') if be is not None else ''
    print((x, y, z), str(b)[:110], s)
show(0, 70, 0); show(0, 69, 0); show(0, 71, 4)
show(-4, 70, 2); show(3, 71, -5)
lvl.close()
