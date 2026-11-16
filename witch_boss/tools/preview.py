"""Render the exported model (simulation of the in-game look) for comparison with the reference art.

python3 preview.py <build_dir> <out_dir> [view,view,...]
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mclib import load, render  # noqa: E402

PITCH, OX, OY, CX, GY = 21.8, -3.1, -3.1, 28.0, 46.0
BG = (10, 6, 22)
# orthographic camera lined up pixel-for-pixel with ../ref/front.png
TY = 22.8
ALIGN = dict(dist=400, target=(0, TY, 0), size=(1080, 1060), ortho=PITCH,
             shift=(OX + CX * PITCH - 540, OY + (GY - TY) * PITCH - 530), bg=BG)
VIEWS = {
    'front': dict(ALIGN, yaw=0, pitch=0, light=False),
    'front_lit': dict(ALIGN, yaw=0, pitch=0),
    'left': dict(ALIGN, yaw=90, pitch=0),       # seen from her left side
    'right': dict(ALIGN, yaw=-90, pitch=0),
    'back': dict(ALIGN, yaw=180, pitch=0),
    'q1': dict(yaw=35, pitch=8, dist=150, target=(0, 22.8, 0), size=(1080, 1060), fov=24, bg=BG),
    'q2': dict(yaw=-40, pitch=12, dist=150, target=(0, 22.8, 0), size=(1080, 1060), fov=24, bg=BG),
    'q3': dict(yaw=150, pitch=10, dist=150, target=(0, 22.8, 0), size=(1080, 1060), fov=24, bg=BG),
    'low': dict(yaw=20, pitch=-12, dist=150, target=(0, 22.8, 0), size=(1080, 1060), fov=24, bg=BG),
    'top': dict(yaw=20, pitch=55, dist=150, target=(0, 22.8, 0), size=(1080, 1060), fov=24, bg=BG),
}


def win(c0, c1, r0, r1, scale):
    return dict(window=(int(OX + c0 * PITCH), int(OY + r0 * PITCH), int(OX + c1 * PITCH), int(OY + r1 * PITCH)), scale=scale)


if __name__ == '__main__':
    bdir, odir = sys.argv[1], sys.argv[2]
    names = sys.argv[3].split(',') if len(sys.argv) > 3 else list(VIEWS)
    os.makedirs(odir, exist_ok=True)
    geo, tex = load(os.path.join(bdir, 'raven_witch.geo.json'), os.path.join(bdir, 'raven_witch.png'))
    for n in names:
        im = render(geo, tex, **VIEWS[n])
        im.save(os.path.join(odir, n + '.png'))
        print('rendered', n)
