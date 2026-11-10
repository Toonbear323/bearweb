import sys, time
sys.path.insert(0, '.')
from gen.core import World, B, REG
from gen import terrain, render, blocks as bl, kit, hub, town
from gen.layout import *
t=time.time()
T = terrain.build_heightmap()
w = World(-128, -128, 128, 128, OY0, OY1, dim=0, biome=1, seed=11)
# crop terrain arrays to the small dev world
import numpy as np
class TT: pass
T2 = TT()
sl = (slice(-128-OX0, 128-OX0), slice(-128-OZ0, 128-OZ0))
for k,v in T.__dict__.items():
    setattr(T2, k, v[sl] if isinstance(v, np.ndarray) and v.shape==(OX1-OX0, OZ1-OZ0) else v)
terrain.voxelize(w, T2, log=lambda *a: None)
hub.build_streets(w)
hub.build_walls(w, T2)
hub.rotunda(w)
hub.plaza_decor(w)
town.build_town(w, T2)
print('walls', kit.connect_walls(w), time.time()-t)
what = sys.argv[1] if len(sys.argv)>1 else 'all'
if what in ('all','top'): render.topdown(w, (-100,-100,100,100), scale=3, out='out/hub_top.png')
if what in ('all','iso'): render.iso(w, (-90, G-1, -90, 90, G+45, 90), view=0, S=4, out='out/hub_iso.png')
if what in ('all','gate'): render.iso(w, (-24, G-1, 60, 24, G+35, 90), view=0, S=12, out='out/hub_gate.png')
if what in ('all','rot'): render.iso(w, (-30, G-1, -30, 30, G+30, 30), view=0, S=10, out='out/hub_rot.png')
if what in ('all','tower'): render.iso(w, (55, G-1, 40, 90, G+40, 90), view=0, S=10, out='out/hub_tower.png')
if what in ('all','nw'): render.iso(w, (-72, G-1, -72, 0, G+40, 0), view=0, S=8, out='out/hub_nw.png')
if what in ('all','ne'): render.iso(w, (0, G-1, -72, 72, G+40, 0), view=1, S=8, out='out/hub_ne.png')
if what in ('all','se'): render.iso(w, (0, G-1, 0, 72, G+40, 72), view=2, S=8, out='out/hub_se.png')
if what in ('all','sw'): render.iso(w, (-72, G-1, 0, 0, G+40, 72), view=3, S=8, out='out/hub_sw.png')
print(time.time()-t)
if what in ('all','cut'):
    render.iso(w, (-30, G, -47, -4, G+5, -24), view=0, S=16, out='out/cut_weapon.png')
    render.iso(w, (-53, G, -41, -29, G+10, -7), view=0, S=14, out='out/cut_shrine.png')
    render.iso(w, (29, G, -28, 63, G+5, -8), view=0, S=14, out='out/cut_guild.png')
    render.iso(w, (-60, G, 5, -25, G+16, 48), view=0, S=10, out='out/park.png')
