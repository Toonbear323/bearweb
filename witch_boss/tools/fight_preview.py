"""Simulation pictures of the fight (no game needed):
  python3 fight_preview.py <pack_dir (..\\V3)> <out_dir> [sheet,scenes,poses]
sheet  - top-down plan of every pattern: where the marks appear and when they hit
scenes - 3D renders of the boss with its warning marks at chosen moments
poses  - the joints / animations
"""
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mclib import load, render  # noqa: E402
import animlib  # noqa: E402
from build_marks import MARKS  # noqa: E402
from patterns import PATTERNS  # noqa: E402

BG = (10, 6, 22)
PLAYER = (0.0, -9.0)          # example player: 9 blocks in front of the boss (model -Z)
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'


def font(n):
    try:
        return ImageFont.truetype(FONT, n)
    except OSError:
        return ImageFont.load_default()


def place(pl):
    kind, a, b = pl
    if kind == 'players':
        return PLAYER[0] + a, PLAYER[1] + b
    if kind == 'boss':
        return a, b
    d = math.atan2(PLAYER[0], PLAYER[1]) + math.radians(a)
    return math.sin(d) * b, math.cos(d) * b


# ------------------------------------------------------------------ top-down plan
def sheet(out):
    order = [1, 2, 3, 4, 9, 11, 12, 13, 14]
    cw, ch, sc = 560, 660, 13.0
    im = Image.new('RGB', (cw * 5, ch * 2 + 70), (16, 12, 30))
    d = ImageDraw.Draw(im)
    d.text((20, 14), '까마귀 마녀 - 패턴 평면도 (위에서 본 모습).  원 = 바닥 예고 표시,  숫자 = 표시가 뜨는 순서,  아래 = 표시 → 타격 시각',
           font=font(26), fill=(240, 230, 255))
    tints = [(1.0, 5), (0.62, 2), (0.4, 2)]
    for idx, n in enumerate(order):
        p = PATTERNS[n]
        x0, y0 = (idx % 5) * cw, 70 + (idx // 5) * ch
        cx, cy = x0 + cw // 2, y0 + 300
        d.rectangle((x0 + 6, y0 + 6, x0 + cw - 6, y0 + ch - 6), outline=(70, 50, 120))
        for g in range(-20, 21, 4):
            d.line((cx + g * sc, cy - 20 * sc, cx + g * sc, cy + 20 * sc), fill=(30, 24, 52))
            d.line((cx - 20 * sc, cy + g * sc, cx + 20 * sc, cy + g * sc), fill=(30, 24, 52))
        d.text((x0 + 16, y0 + 12), '%s%s' % ('[2페이즈] ' if n > 9 else '', p['title'][1].replace(' (2페이즈)', '')), font=font(24), fill=(255, 255, 255))
        times = sorted({t for t, _, _ in p['steps']})
        for t, mark, pl in sorted(p['steps'], key=lambda s: -s[0]):
            q = MARKS[mark]
            k, wd = tints[min(times.index(t), 2)]
            col = tuple(int(int(q['rim'][i:i + 2], 16) * k) for i in (1, 3, 5))
            x, z = place(pl)
            px, py = cx + x * sc, cy - z * sc              # the player (model -Z) is drawn below the boss
            r = q['R'] * sc
            d.ellipse((px - r, py - r, px + r, py + r), outline=col, width=wd)
            if q['r0']:
                r0 = q['r0'] * sc
                d.ellipse((px - r0, py - r0, px + r0, py + r0), outline=col, width=wd)
                d.text((px - 8, py - (r + r0) / 2 - 12), str(times.index(t) + 1), font=font(22), fill=col)
            else:
                d.text((px - 6, py - 12), str(times.index(t) + 1), font=font(20), fill=col)
        d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(170, 90, 255), outline=(255, 255, 255))
        d.text((cx + 12, cy - 26), '보스', font=font(18), fill=(210, 170, 255))
        px, py = cx + PLAYER[0] * sc, cy - PLAYER[1] * sc
        d.rectangle((px - 5, py - 5, px + 5, py + 5), fill=(120, 255, 140))
        d.text((px + 10, py + 2), '플레이어', font=font(16), fill=(120, 255, 140))
        yy = y0 + 566
        for i, t in enumerate(times):
            marks = sorted({mk for tt, mk, _ in p['steps'] if tt == t})
            hit = ', '.join('%.2f초' % (t + MARKS[mk]['warn']) for mk in marks)
            d.text((x0 + 16 + (i % 2) * 270, yy + (i // 2) * 24), '%d) %.1f초 표시 → %s 타격' % (i + 1, t, hit), font=font(18), fill=(235, 225, 250))
        d.text((x0 + 16, y0 + 40), p['note'], font=font(17), fill=(170, 160, 200))
    d.text((4 * cw + 24, 70 + ch + 60), '모든 공격 공통\n\n1. 보스는 직접 피해를 주지 않음\n2. 바닥에 표시가 먼저 뜸\n3. 안쪽 원판이 테두리까지\n   차오르면 그 자리만 타격\n\n표시 시간\n' + '\n'.join(
        '  %s: %.2f초, 피해 %d' % ({'hex': '마법진', 'seed': '호박', 'wave': '돌진', 'nova': '폭발', 'ring': '고리'}[k], q['warn'], q['dmg'])
        for k, q in MARKS.items()), font=font(22), fill=(240, 230, 255), spacing=8)
    im.save(os.path.join(out, 'pattern_plan.png'))


# ------------------------------------------------------------------ 3D scenes
def scenes(pack, out):
    rp = os.path.join(pack, 'RavenWitch_RP')
    A = animlib.witch_animations()

    def L(n):
        return load(os.path.join(rp, 'models', 'entity', n + '.geo.json'), os.path.join(rp, 'textures', 'entity', n + '.png'))
    witch = L('raven_witch')
    marks = {k: L('mark_' + k) for k in MARKS}
    shots = [(1, 1.6, '저주 마법진  1.6초: 첫 표시가 거의 다 참 / 둘째 표시 시작'), (1, 1.84, '1.84초: 첫 표시 자리 폭발'),
             (2, 1.95, '호박 폭탄  1.95초: 첫 배치 호박 낙하 중, 둘째 배치 표시'), (3, 1.3, '까마귀 돌진  1.3초: 직선 예고'),
             (4, 1.7, '폭발  1.7초: 보스 주변 6칸 예고'), (4, 3.2, '3.2초: 바깥 고리 예고 (보스 옆이 안전)'),
             (13, 1.3, '2페이즈 돌진  1.3초: 부채꼴 3줄'), (12, 2.2, '2페이즈 호박  2.2초: 첫 배치 폭발')]
    size = (900, 640)
    cam = dict(yaw=24, pitch=33, dist=640, target=(0, 10, -70), size=size, fov=30, ss=1, alpha=True)
    ya = math.radians(cam['yaw'])
    tiles = []
    for n, t, title in shots:
        p = PATTERNS[n]
        objs = []
        for ts, mark, pl in p['steps']:
            age = t - ts
            w = MARKS[mark]['warn']
            if age < 0 or age > w + 0.45:
                continue
            x, z = place(pl)
            ps = animlib.pose([(animlib.mark_animation(w, MARKS[mark].get('bomb', False)), age, 1)])
            ps['mark'] = {'pos': (x * 16, 0, z * 16)}
            objs.append((x * math.sin(ya) * -1 + z * math.cos(ya) * -1, marks[mark], ps, False))
        wp = animlib.pose([(A['animation.raven_witch.idle'], 0, 1), (A['animation.raven_witch.' + p['anim']], t, 1)], 1.3)
        objs.append((0.0, witch, wp, True))
        im = Image.new('RGBA', size, (44, 62, 40, 255))
        for _, (g, tx), ps, lit in sorted(objs, key=lambda o: o[0]):      # far to near
            im.alpha_composite(render(g, tx, pose=ps, light=lit, **cam))
        ImageDraw.Draw(im).text((12, 8), title, font=font(26), fill=(255, 255, 255))
        tiles.append(im.convert('RGB'))
        print('scene', n, t)
    o = Image.new('RGB', (size[0] * 2, size[1] * 4))
    for i, tl in enumerate(tiles):
        o.paste(tl, ((i % 2) * size[0], (i // 2) * size[1]))
    o.save(os.path.join(out, 'fight_scenes.png'))


# ------------------------------------------------------------------ joints / animation frames
def poses(pack, out):
    rp = os.path.join(pack, 'RavenWitch_RP')
    geo, tex = load(os.path.join(rp, 'models', 'entity', 'raven_witch.geo.json'), os.path.join(rp, 'textures', 'entity', 'raven_witch.png'))
    A = animlib.witch_animations()
    rows = [('대기 (둥실둥실, 머리카락·모자·소매 흔들림)', [(None, 0.0, 0.2), (None, 0, 1.2), ('move', 0, 1.2)]),
            ('저주 마법진 시전', [('cast_hex', 0.4, 1), ('cast_hex', 0.5, 1), ('cast_hex', 1.0, 1)]),
            ('호박 폭탄 시전', [('cast_pumpkin', 0.45, 1), ('cast_pumpkin', 0.6, 1), ('cast_pumpkin', 0.8, 1)]),
            ('까마귀 돌진', [('cast_raven', 0.5, 1), ('cast_raven', 1.3, 1), ('cast_raven', 1.42, 1)]),
            ('폭발 → 고리', [('cast_nova', 0.4, 1), ('cast_nova', 1.9, 1), ('cast_nova', 3.3, 1)]),
            ('2페이즈 돌입', [('enrage', 0.6, 1), ('enrage', 1.5, 1), ('enrage', 1.72, 1)])]
    tw, th = 470, 470
    o = Image.new('RGB', (tw * 6, th * 3), BG)
    d = ImageDraw.Draw(o)
    for r, (title, frames) in enumerate(rows):
        bx, by = (r % 2) * tw * 3, (r // 2) * th
        for c, (an, t, life) in enumerate(frames):
            layers = [(A['animation.raven_witch.idle'], 0, 1)]
            if an:
                layers.append((A['animation.raven_witch.' + an], t, 1))
            kw = dict(yaw=32, pitch=10, dist=165, target=(0, 25, -2), fov=26)
            if an == 'cast_raven':
                kw = dict(yaw=72, pitch=14, dist=330, target=(0, 20, -85), fov=30)
            im = render(geo, tex, pose=animlib.pose(layers, life), size=(tw, th), bg=BG, ss=1, **kw)
            o.paste(im, (bx + c * tw, by))
            d.text((bx + c * tw + 10, by + th - 30), ('%.2f초' % t) if an and an != 'move' else ('이동 중' if an else ''), font=font(20), fill=(200, 190, 230))
        d.text((bx + 10, by + 8), title, font=font(26), fill=(255, 255, 255))
    o.save(os.path.join(out, 'animation_poses.png'))


if __name__ == '__main__':
    pack, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    what = sys.argv[3].split(',') if len(sys.argv) > 3 else ['sheet', 'scenes', 'poses']
    if 'sheet' in what:
        sheet(out)
    if 'scenes' in what:
        scenes(pack, out)
    if 'poses' in what:
        poses(pack, out)
