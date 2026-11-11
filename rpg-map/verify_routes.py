"""Route verification for every dungeon (substitute for play-testing)."""
import sys, time
sys.path.insert(0, '.')
import build
from gen import walk, dkit
from gen.layout import *
from gen.nether import NF
build.T0 = time.time()
for a in sys.argv[1:]:
    k, v = a.split('=')
    build.SEEDS[k] = int(v)
w, n, T = build.build()
R = dkit.REG
def run(label, world, start, goals, box):
    res, cnt = walk.reach(world, start, [g for _, g in goals], box)
    line = ', '.join('%s=%s' % (name, 'OK' if res[g] else 'XX') for name, g in goals)
    print('%-9s start=%s cells=%d  %s' % (label, start, cnt, line), flush=True)
    return all(res.values())
ok = True
# town: spawn -> shops, shrine pads, guild, gates
G1 = G + 1
ok &= run('town', w, (0, G + 3, 4), [('weapon', (-14, G+2, -37)), ('armor', (-14, G+2, -62)), ('tool', (14, G+2, -37)),
     ('magic', (14, G+2, -62)), ('food', (14, G+2, 38)), ('shrine_nave', (-41, G+3, -24)), ('pad_plains', (-50, G+3, -36)),
     ('pad_plots', (-32, G+3, -18)), ('guild', (46, G+2, -18)), ('inn', (45, G+2, 15)),
     ('gateN', (0, G1, -84)), ('gateS', (0, G1, 84)), ('gateE', (84, G1, 0)), ('gateW', (-84, G1, 0)), ('wallwalk', (30, G+7, -76))],
     (-90, G - 2, -90, 90, G + 30, 90))
kx, kz = KEEP
b = R['boss']['plains']['pos']
wp = R['warps']['plains']
ok &= run('plains', w, (int(wp[1]), int(wp[2]), int(wp[3])), [('keep_door', (kx, KEEP_G+1, kz+8)), ('hallA', (0, KEEP_G-9, kz-10)),
     ('barracks', (0, KEEP_G-9, kz-36)), ('prison', (26, KEEP_G-9, kz-36)), ('catacomb', (28, KEEP_G-9, kz-12)), ('boss', b),
     ('altar', (49, b[1], kz+17)), ('exit', (48, b[1], kz+20))], (kx-50, KEEP_G-20, kz-56, kx+64, KEEP_G+20, kz+50))
cx, cz = PYRAMID
b = R['boss']['desert']['pos']; wp = R['warps']['desert']
ok &= run('desert', w, (int(wp[1]), int(wp[2]), int(wp[3])), [('antechamber', (cx-8, PYR_G+1, cz)), ('hall', (cx+18, PYR_G-9, cz)),
     ('north_room', (cx+18, PYR_G-9, cz-20)), ('tomb', (cx+18, PYR_G-9, cz+20)), ('boss', b), ('altar', (cx+12, PYR_G+11, cz)),
     ('exit', (cx+11, PYR_G+11, cz+2))], (cx-70, PYR_G-14, cz-40, cx+40, PYR_G+30, cz+40))
mx, mz = MINE
b = R['boss']['cave']['pos']; wp = R['warps']['cave']
ok &= run('cave', w, (int(wp[1]), int(wp[2]), int(wp[3])), [('hub', (mx, MINE_G+1, mz-46)), ('lush', (mx+24, 66, mz-64)),
     ('dripstone', (mx+58, 56, mz-76)), ('geode', (mx+74, 44, mz-46)), ('boss', b), ('altar', (b[0]-34, b[1], b[2])),
     ('exit', (b[0]-29, b[1], b[2]+3))], (mx-12, 20, mz-106, mx+98, MINE_G+12, mz+12), )
tx, tz = TEMPLE
wp = R['warps']['ocean']; b = R['boss']['ocean']['pos']
ok &= run('ocean', w, (int(wp[1]), int(wp[2]), int(wp[3])), [('tunnel', (tx, 38, tz-60)), ('atrium', (tx, 38, tz-10)),
     ('gallery', (tx, 27, tz+20)), ('sanctum', b), ('vault', (tx, 38, tz+78)), ('altar', (tx, 38, tz+82))],
     (tx-30, 16, HARBOR[1]-10, tx+30, 72, tz+100))
wp = R['warps']['hell']
hub = (int(wp[1]) + NOFF, int(wp[2]), int(wp[3]))
b = R['boss']['hell']['pos']
ok &= run('hell', n, hub, [('canyon', (NOFF+0, NF+1, 30)), ('crimson', (NOFF+0, NF+1, -62)), ('soul', (NOFF-4, NF+1, -120)),
     ('boss', (b[0]+NOFF, b[1], b[2])), ('altar', (NOFF+0, NF+1, -247)), ('exit', (NOFF+5, NF+1, -244)),
     ('fort_gate', (NOFF+123, NF+1, 64)), ('bast_gate', (NOFF-125, NF+1, 64))], (NOFF-130, 20, -256, NOFF+130, 90, 120))
b = R['boss']['fortress']['pos']
ok &= run('fortress', n, (NOFF+100, NF+1, 64), [('keep', (NOFF+160, NF+1, 64)), ('upper', (NOFF+160, NF+9, 74)), ('roof', (NOFF+150, NF+16, 70)),
     ('north_tower', (NOFF+160, NF+1, 21)), ('south_tower', (NOFF+160, NF+1, 107)), ('boss', (b[0]+NOFF, b[1], b[2])),
     ('altar', (NOFF+245, NF+1, 64)), ('exit', (NOFF+244, NF+1, 61))], (NOFF+90, 30, 0, NOFF+255, 80, 127))
b = R['boss']['bastion']['pos']
ok &= run('bastion', n, (NOFF-100, NF+1, 64), [('gate', (NOFF-125, NF+1, 64)), ('stables', (NOFF-145, NF+1, 44)), ('hut', (NOFF-156, NF+1, 88)),
     ('boss', (b[0]+NOFF, b[1], b[2])), ('hoard', (NOFF-194, NF+1, 67)), ('gallery', (NOFF-205, NF+10, 50)),
     ('altar', (NOFF-227, NF+1, 64)), ('exit', (NOFF-221, NF+1, 68))], (NOFF-255, 30, 0, NOFF-90, 80, 127))
print('ALL ROUTES OK' if ok else 'SOME ROUTES BROKEN')
