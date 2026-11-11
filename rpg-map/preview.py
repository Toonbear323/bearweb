"""Render preview images of the finished world into preview/."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build
from gen import render, blocks as bl
from gen.layout import *
from gen.nether import NF
build.T0 = time.time()
w, n, T = build.build()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preview')
os.makedirs(out, exist_ok=True)
def save(im, name, maxw=1400):
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)))
    im.convert('RGB').save(os.path.join(out, name), quality=86)
save(render.topdown(w), '00_map_overworld.jpg', 896)
save(render.topdown(n, ymax=60, scale=2), '01_map_nether.jpg', 1024)
save(render.iso(w, (-92, G - 2, -92, 92, G + 48, 92), view=0, S=6), '02_town.jpg')
save(render.iso(w, (-34, G - 1, -34, 34, G + 34, 34), view=0, S=10), '03_spawn_rotunda.jpg')
save(render.iso(w, (-72, G - 1, -74, 26, G + 44, 0), view=0, S=8), '04_shops_shrine.jpg')
x0 = PLOT_X0; save(render.iso(w, (x0 - 4, G - 1, PLOT_Z0 - 4, x0 + 210, G + 14, PLOT_Z0 + 160), view=0, S=4), '05_plots.jpg')
kx, kz = KEEP; save(render.iso(w, (kx - 44, KEEP_G - 1, kz - 44, kx + 44, KEEP_G + 26, kz + 44), view=0, S=8), '06_plains_keep.jpg')
save(render.iso(w, (kx - 12, KEEP_G - 16, kz - 50, kx + 56, KEEP_G - 4, kz + 32), view=0, S=9, cut_y=KEEP_G - 5), '07_plains_crypt.jpg')
px, pz = PYRAMID; save(render.iso(w, (px - 72, PYR_G - 1, pz - 52, px + 40, PYR_G + 40, pz + 46), view=3, S=6), '08_desert_pyramid.jpg')
mx, mz = MINE; save(render.iso(w, (mx - 22, MINE_G - 2, mz - 22, mx + 22, MINE_G + 30, mz + 14), view=0, S=10), '09_cave_entrance.jpg')
save(render.iso(w, (mx + 50, 30, mz - 70, mx + 96, 70, mz - 20), view=0, S=10, cut_y=52), '10_cave_geode.jpg')
save(render.iso(w, (-44, SEA - 6, 118, 44, SEA + 46, 204), view=0, S=8), '11_harbor.jpg')
ws = w.b.copy(); w.b[w.b == bl.WATER] = 0
save(render.iso(w, (-50, 14, 190, 50, 62, 405), view=1, S=6), '12_sunken_temple_drained.jpg')
w.b[:] = ws
hx, hz = HELLGATE; save(render.iso(w, (hx - 48, HELL_G - 4, hz - 48, hx + 48, HELL_G + 40, hz + 48), view=1, S=7), '13_hell_gate.jpg')
save(render.iso(n, (NOFF - 45, 36, 25, NOFF + 45, 75, 100), view=0, S=8, cut_y=54), '14_nether_hub.jpg')
save(render.iso(n, (NOFF - 50, 30, -250, NOFF + 50, 80, -30), view=0, S=5, cut_y=58), '15_burning_canyon.jpg')
save(render.iso(n, (NOFF + 96, 20, 6, NOFF + 250, 100, 122), view=0, S=6, cut_y=66), '16_nether_fortress.jpg')
save(render.iso(n, (NOFF - 250, 30, 6, NOFF - 96, 100, 122), view=1, S=6, cut_y=70), '17_piglin_bastion.jpg')
print('done', time.time() - build.T0)
