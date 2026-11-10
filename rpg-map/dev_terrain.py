import sys, time
sys.path.insert(0, '.')
from gen.core import World, B, REG
from gen import terrain, render, blocks as bl
from gen.layout import *
t=time.time()
T = terrain.build_heightmap()
print('hm', time.time()-t, T.h.min(), T.h.max())
w = World(OX0, OZ0, OX1, OZ1, OY0, OY1, dim=0, biome=1, seed=11)
terrain.voxelize(w, T); print('vox', time.time()-t)
terrain.ores(w, T); print('ores', time.time()-t)
terrain.vegetation(w, T); print('veg', time.time()-t)
render.topdown(w, out='out/top.png'); print('render', time.time()-t)
import numpy as np
print('land frac', (T.land>0).mean(), 'kinds', np.bincount(T.kind.ravel()))
for name,(x,z) in dict(town=(0,0),plots=(-216,0),keep=KEEP,mine=MINE,pyr=PYRAMID,harbor=HARBOR,temple=TEMPLE,hell=HELLGATE,mount=MOUNTAIN).items():
    print(name, T.h[x-OX0, z-OZ0], round(float(T.land[x-OX0,z-OZ0]),2))
