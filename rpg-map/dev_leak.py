import sys, time
sys.path.insert(0, '.')
import numpy as np
import build
from gen import blocks as bl, walk
from gen.core import REG
from gen.layout import *
build.T0 = time.time()
w, n, T = build.build()
def leaks(wd, liquid_names, ymax):
    ids = [i for i, (nm, _) in enumerate(REG.entries) if nm in liquid_names]
    A = wd.b[:, :, :ymax - wd.y0]
    liq = np.isin(A, ids)
    if 'water' in liquid_names:
        liq = liq | wd.wl[:, :, :ymax - wd.y0]
    air = A == 0
    adj = np.zeros_like(air)
    adj[1:, :, :] |= liq[:-1, :, :]
    adj[:-1, :, :] |= liq[1:, :, :]
    adj[:, 1:, :] |= liq[:, :-1, :]
    adj[:, :-1, :] |= liq[:, 1:, :]
    adj[:, :, :-1] |= liq[:, :, 1:]      # liquid above
    bad = np.argwhere(air & adj)
    return [(int(x) + wd.x0, int(y) + wd.y0, int(z) + wd.z0) for x, z, y in bad]
L = leaks(w, ('water', 'flowing_water'), SEA + 1)
print('overworld water leaks below sea level:', len(L))
import collections
reg = collections.Counter((x // 32 * 32, z // 32 * 32) for x, y, z in L)
print(reg.most_common(12))
print(L[:12])
L2 = leaks(w, ('water', 'flowing_water'), w.y1 - 1)
print('all-height water leaks:', len(L2), collections.Counter((x // 32 * 32, z // 32 * 32) for x, y, z in L2).most_common(8))
L3 = leaks(w, ('lava', 'flowing_lava'), w.y1 - 1)
print('overworld lava leaks:', len(L3), L3[:8])
L4 = leaks(n, ('lava', 'flowing_lava'), 127)
print('nether lava leaks:', len(L4), collections.Counter((x // 32 * 32, z // 32 * 32) for x, y, z in L4).most_common(8), L4[:6])
sel = [p for p in L if 190 <= p[2] < 230]
print(len(sel), sorted(sel)[:40])
for (x, y, z) in sorted(sel)[:6]:
    print((x, y, z), [(REG.name(w.get(x + dx, y + dy, z + dz)), bool(w.wl[x + dx - w.x0, z + dz - w.z0, y + dy - w.y0])) for dx, dy, dz in ((1,0,0),(-1,0,0),(0,0,1),(0,0,-1),(0,1,0),(0,-1,0))])
