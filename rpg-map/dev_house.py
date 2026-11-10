import sys, time
sys.path.insert(0, '.')
from gen.core import World, B, REG
from gen import render, blocks as bl, kit, houses
from gen.kit import Frame
w = World(-16, -16, 96, 48, -64, 64, dim=0, biome=1, seed=3)
w.fill(-16, -4, -16, 95, 0, 47, B('grass_block'))
G = 0
F = Frame.box(w, 2, G, 4, 13, 9, 'S')
info = houses.shell(F, 13, 9, floors=2, pal=houses.palette('spruce'), chimney=('W', 3), sign='테스트', dormer=True)
houses.furnish_home(F, info)
F = Frame.box(w, 24, G, 4, 9, 11, 'S')
info = houses.shell(F, 9, 11, floors=2, pal=houses.palette('dark'), roof_axis='z')
houses.furnish_home(F, info)
F = Frame.box(w, 40, G, 4, 17, 11, 'S')
info = houses.shell(F, 17, 11, floors=3, pal=houses.palette('brick'), chimney=('E', 4), dormer=True)
houses.furnish_home(F, info)
F = Frame.box(w, 64, G, 4, 11, 9, 'S')
info = houses.shell(F, 11, 9, floors=1, pal=houses.palette('moss'), jetty=False, chimney=('E', 3))
houses.furnish_home(F, info)
F = Frame.box(w, 80, G, 2, 11, 13, 'W')
info = houses.shell(F, 11, 13, floors=2, pal=houses.palette('red'), roof_axis='x')
print(kit.connect_walls(w))
render.iso(w, (-4, 0, -4, 95, 40, 30), view=0, S=6, out='out/h0.png')
render.iso(w, (-4, 0, -4, 95, 40, 30), view=2, S=6, out='out/h2.png')
render.iso(w, (-4, 0, -4, 60, 4, 30), view=0, S=8, out='out/hcut.png')
render.iso(w, (-2, 0, 0, 18, 30, 18), view=0, S=14, out='out/h_a.png')
render.iso(w, (38, 0, 0, 60, 30, 18), view=0, S=12, out='out/h_b.png')
