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
show(0, 70, 0)
show(8000, 40, 64, 'minecraft:the_nether'); show(8000, 43, 76, 'minecraft:the_nether')
cmds = collections.Counter()
for dim in ('minecraft:overworld', 'minecraft:the_nether'):
    for (cx, cz) in lvl.all_chunk_coords(dim):
        ch = lvl.get_chunk(cx, cz, dim)
        for be in ch.block_entities:
            if be.base_name == 'command_block':
                c = str(be.nbt.compound.get('utags').get('Command')) if be.nbt.compound.get('utags') is not None else str(be.nbt.compound.get('Command'))
                cmds[c.split('/')[1] if '/' in c else c[:20]] += 1
print('command blocks by kind:', dict(cmds))
lvl.close()
