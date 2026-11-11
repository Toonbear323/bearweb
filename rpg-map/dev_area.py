import sys, time
sys.path.insert(0, '.')
import numpy as np
from gen.core import World, B, REG
from gen import terrain, render, blocks as bl, kit
from gen.layout import *
def crop_world(cx, cz, half, seed=11):
    T = terrain.build_heightmap()
    x0, z0 = (cx-half)//16*16, (cz-half)//16*16
    x1, z1 = -(-(cx+half)//16)*16, -(-(cz+half)//16)*16
    x0, z0, x1, z1 = max(x0,OX0), max(z0,OZ0), min(x1,OX1), min(z1,OZ1)
    w = World(x0, z0, x1, z1, OY0, OY1, dim=0, biome=1, seed=seed)
    class TT: pass
    T2 = TT()
    sl = (slice(x0-OX0, x1-OX0), slice(z0-OZ0, z1-OZ0))
    for k,v in T.__dict__.items():
        setattr(T2, k, v[sl] if isinstance(v, np.ndarray) and v.shape==(OX1-OX0, OZ1-OZ0) else v)
    terrain.voxelize(w, T2, log=lambda *a: None)
    return w, T2
if __name__ == '__main__':
    what = sys.argv[1]
    t = time.time()
    if what == 'plains':
        from gen import d_plains
        w, T = crop_world(KEEP[0], KEEP[1], 80)
        d_plains.build(w, T)
        terrain.vegetation(w, T, log=lambda *a: None)
        kit.connect_walls(w)
        cx, cz = KEEP
        render.iso(w, (cx-50, KEEP_G-1, cz-50, cx+60, KEEP_G+30, cz+50), view=0, S=7, out='out/plains_iso.png')
        render.iso(w, (cx-12, KEEP_G-16, cz-50, cx+56, KEEP_G-4, cz+32), view=0, S=9, cut_y=KEEP_G-5, out='out/plains_crypt.png')
        render.iso(w, (cx-12, KEEP_G-16, cz+2, cx+56, KEEP_G-5, cz+32), view=2, S=12, cut_y=KEEP_G-6, out='out/plains_boss.png')
    if what == 'desert':
        from gen import d_desert
        w, T = crop_world(PYRAMID[0]-10, PYRAMID[1], 90)
        d_desert.build(w, T)
        terrain.vegetation(w, T, log=lambda *a: None)
        kit.connect_walls(w)
        cx, cz = PYRAMID
        render.iso(w, (cx-75, PYR_G-1, cz-55, cx+45, PYR_G+40, cz+50), view=3, S=6, out='out/desert_iso.png')
        render.iso(w, (cx-32, PYR_G-12, cz-28, cx+32, PYR_G+2, cz+28), view=3, S=9, cut_y=PYR_G-4, out='out/desert_low.png')
        render.iso(w, (cx-20, PYR_G+9, cz-14, cx+16, PYR_G+15, cz+16), view=3, S=12, cut_y=PYR_G+15, out='out/desert_king.png')
    if what == 'cave':
        from gen import d_cave
        mx, mz = MINE
        w, T = crop_world(mx+40, mz-45, 100)
        d_cave.build(w, T)
        terrain.vegetation(w, T, log=lambda *a: None)
        kit.connect_walls(w)
        render.iso(w, (mx-25, MINE_G-2, mz-30, mx+25, MINE_G+30, mz+15), view=0, S=10, out='out/cave_entry.png')
        render.iso(w, (mx-10, 24, mz-104, mx+96, 92, mz+8), view=0, S=6, cut_y=70, out='out/cave_70.png')
        render.iso(w, (mx+50, 30, mz-70, mx+96, 70, mz-20), view=0, S=12, cut_y=52, out='out/cave_geode.png')
        render.iso(w, (mx-10, 24, mz-70, mx+70, 45, mz-20), view=0, S=10, cut_y=36, out='out/cave_shrine.png')
        import numpy as np
        # sanity: nothing carved breaks the surface
        print('fallback colors:', [REG.entries[i][0] for i in range(len(REG.entries)) if tuple(render.color_table()[i])==(200,0,200)][:20])
    if what == 'ocean':
        from gen import d_ocean
        w, T = crop_world(0, 280, 168)
        d_ocean.build(w, T)
        terrain.vegetation(w, T, log=lambda *a: None)
        kit.connect_walls(w)
        render.iso(w, (-45, SEA-6, 120, 45, SEA+45, 205), view=0, S=8, out='out/ocean_harbor.png')
        # drain the sea for the temple view
        ws = w.b.copy()
        w.b[w.b == bl.WATER] = 0
        render.iso(w, (-50, 14, 190, 50, 62, 405), view=1, S=6, out='out/ocean_temple.png')
        render.iso(w, (-16, 22, 285, 16, 46, 400), view=1, S=8, cut_y=40, out='out/ocean_cut.png')
        w.b[:] = ws
        print('fallback colors:', [REG.entries[i][0] for i in range(1,len(REG.entries)) if tuple(render.color_table()[i])==(200,0,200)][:20])
    if what == 'nether':
        from gen import nether
        w = nether.make_world()
        print('terrain', time.time()-t)
        from gen import n_fort, n_bast
        nether.hub(w); nether.canyon(w); n_fort.build(w); n_bast.build(w)
        kit.connect_walls(w)
        print('built', time.time()-t)
        render.topdown(w, ymax=58, scale=2, out='out/nether_top.png')
        render.iso(w, (-45, 36, 25, 45, 75, 100), view=0, S=8, cut_y=52, out='out/nether_hub.png')
        render.iso(w, (-45, 30, -250, 45, 80, -160), view=0, S=7, cut_y=56, out='out/nether_arena.png')
        render.iso(w, (-50, 36, -110, 50, 80, -30), view=0, S=7, cut_y=58, out='out/nether_crimson.png')
        render.iso(w, (96, 20, 6, 250, 100, 122), view=0, S=6, cut_y=64, out='out/nether_fort.png')
        render.iso(w, (-250, 30, 6, -96, 100, 122), view=1, S=6, cut_y=70, out='out/nether_bast.png')
        print('fallback colors:', [REG.entries[i][0] for i in range(1,len(REG.entries)) if tuple(render.color_table()[i])==(200,0,200)][:20])
    print(time.time()-t)
