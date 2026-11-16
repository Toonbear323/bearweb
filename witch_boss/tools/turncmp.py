"""turnaround sheet (top row) vs simulated renders (bottom row)"""
import sys
from PIL import Image
HERE = __import__('os').path.dirname(__file__)
odir = sys.argv[1]
t = Image.open(HERE + '/../ref/turnaround.png').convert('RGB')
boxes = ((60, 80, 245, 345), (255, 80, 430, 345), (410, 80, 590, 345), (590, 80, 765, 345))
names = ('front_lit', 'left', 'back', 'right')
W, H = 400, 560
sh = Image.new('RGB', (W * 4, H * 2), (0, 0, 0))
for i, (b, n) in enumerate(zip(boxes, names)):
    c = t.crop(b)
    c = c.resize((W, int(c.height * W / c.width)), Image.LANCZOS)
    sh.paste(c, (i * W, 0))
    r = Image.open(odir + '/' + n + '.png').convert('RGB').crop((150, 0, 1010, 1060))
    r = r.resize((W, int(r.height * W / r.width)), Image.LANCZOS)
    sh.paste(r, (i * W, H))
sh.save(odir + '/cmp_turn.png')
