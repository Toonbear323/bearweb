"""Side-by-side sheets: reference crop | simulated render crop | 50% blend, for a grid window.
python3 compare.py <out_dir> name c0 c1 r0 r1 scale [render_name]"""
import sys
from PIL import Image
HERE = __import__('os').path.dirname(__file__)
PITCH, OX, OY = 21.8, -3.1, -3.1
odir, name = sys.argv[1], sys.argv[2]
c0, c1, r0, r1 = (float(v) for v in sys.argv[3:7])
s = int(sys.argv[7])
rn = sys.argv[8] if len(sys.argv) > 8 else 'front'
box = (int(OX + c0 * PITCH), int(OY + r0 * PITCH), int(OX + c1 * PITCH), int(OY + r1 * PITCH))
a = Image.open(HERE + '/../ref/front.png').convert('RGB').crop(box)
b = Image.open(odir + '/' + rn + '.png').convert('RGB').crop(box)
w, h = a.size
a = a.resize((w * s, h * s), Image.NEAREST)
b = b.resize((w * s, h * s), Image.NEAREST)
sheet = Image.new('RGB', (w * s * 2 + 8, h * s), (255, 0, 255))
sheet.paste(a, (0, 0))
sheet.paste(b, (w * s + 8, 0))
sheet.save(odir + '/cmp_' + name + '.png')
print(sheet.size)
