"""Attack patterns of the Raven Witch (data only; make_pack.py turns it into behaviour-pack
commands, pattern_sheet.py draws it).

RULE: the boss never hurts anything directly.  A pattern only *places warning marks*; a mark shows
where it will hit for `warn` seconds (build_marks.MARKS) and then deals the damage itself.  So every
hit is announced on the ground first, by construction.

A step is (time, mark, place):
  ('players', dx, dz)   on every player within 40 blocks (offset in blocks)
  ('boss', dx, dz)      relative to the boss
  ('lane', angle, d)    d blocks along the line from the boss to the nearest player, turned by angle
"""
import math

AIM = '@p[r=40]'


def ring(mark, t, r, n, a0=0.0, who='boss'):
    return [(t, mark, (who, round(r * math.cos(a0 + i * 2 * math.pi / n), 2), round(r * math.sin(a0 + i * 2 * math.pi / n), 2))) for i in range(n)]


def lane(t, angle=0):
    return [(t, 'wave', ('lane', angle, 2.5 * i)) for i in range(1, 8)]


def on_players(mark, t):
    return [(t, mark, ('players', 0, 0))]


Q = math.pi / 4
PATTERNS = {
    # ---------------- phase 1
    1: dict(key='hex', anim='cast_hex', length=4.2, title=('Hex circles', '저주 마법진'),
            note='세 번 연속으로 플레이어 발밑에 마법진',
            steps=on_players('hex', 0.5) + on_players('hex', 1.4) + on_players('hex', 2.3)),
    2: dict(key='pumpkin', anim='cast_pumpkin', length=4.6, title=('Pumpkin bombs', '호박 폭탄'),
            note='보스 둘레 두 겹(안쪽 십자 + 바깥 대각선), 이어서 반대 배치',
            steps=ring('seed', 0.6, 5, 4) + ring('seed', 0.6, 10, 4, Q) + on_players('seed', 0.6)
            + ring('seed', 1.6, 5, 4, Q) + ring('seed', 1.6, 10, 4) + on_players('seed', 1.6)),
    3: dict(key='raven', anim='cast_raven', length=3.6, title=('Raven dive', '까마귀 돌진'),
            note='가장 가까운 플레이어 방향으로 긴 직선, 두 번',
            steps=lane(0.5) + lane(1.7)),
    4: dict(key='nova', anim='cast_nova', length=4.6, title=('Nova', '안쪽 폭발 → 바깥 고리'),
            note='먼저 보스 주변 6칸(멀어져야 함), 이어서 6~11칸 고리(붙어야 함)',
            steps=[(0.4, 'nova', ('boss', 0, 0)), (1.9, 'ring', ('boss', 0, 0))]),
    # ---------------- phase 2 (health <= 50%): same moves, more marks
    11: dict(key='hex', anim='cast_hex', length=4.2, title=('Hex circles+', '저주 마법진 (2페이즈)'),
             note='발밑 + 플레이어 둘레 네 곳(십자 → 대각선 → 십자)',
             steps=on_players('hex', 0.5) + ring('hex', 0.5, 6, 4, 0, 'players') + on_players('hex', 1.4) + ring('hex', 1.4, 6, 4, Q, 'players')
             + on_players('hex', 2.3) + ring('hex', 2.3, 6, 4, 0, 'players')),
    12: dict(key='pumpkin', anim='cast_pumpkin', length=4.6, title=('Pumpkin bombs+', '호박 폭탄 (2페이즈)'),
             note='세 겹으로 늘어남',
             steps=ring('seed', 0.6, 5, 4) + ring('seed', 0.6, 10, 4, Q) + ring('seed', 0.6, 14.5, 8, Q / 2) + on_players('seed', 0.6)
             + ring('seed', 1.6, 5, 4, Q) + ring('seed', 1.6, 10, 4) + ring('seed', 1.6, 14.5, 8) + on_players('seed', 1.6)),
    13: dict(key='raven', anim='cast_raven', length=3.6, title=('Raven dive+', '까마귀 돌진 (2페이즈)'),
             note='부채꼴 3줄, 이어서 그 사이 4줄',
             steps=lane(0.5, -24) + lane(0.5, 0) + lane(0.5, 24) + lane(1.7, -36) + lane(1.7, -12) + lane(1.7, 12) + lane(1.7, 36)),
    14: dict(key='nova', anim='cast_nova', length=4.6, title=('Nova+', '폭발 → 고리 (2페이즈)'),
             note='도망치는 자리에도 마법진',
             steps=[(0.4, 'nova', ('boss', 0, 0))] + on_players('hex', 1.0) + [(1.9, 'ring', ('boss', 0, 0))] + on_players('hex', 2.6)),
    # ---------------- phase change
    9: dict(key='enrage', anim='enrage', length=2.8, title=('Enrage', '2페이즈 돌입'),
            note='체력 50% 이하에서 한 번: 보스 주변 6칸 폭발',
            steps=[(0.2, 'nova', ('boss', 0, 0))]),
}
SOUNDS = {   # variant -> [(time, sound, volume, pitch)]
    'hex': [(0.0, 'mob.evocation_illager.prepare_attack', 2.0, 1.0), (0.5, 'mob.evocation_illager.cast_spell', 2.0, 1.2),
            (1.4, 'mob.evocation_illager.cast_spell', 2.0, 1.2), (2.3, 'mob.evocation_illager.cast_spell', 2.0, 1.2)],
    'pumpkin': [(0.0, 'mob.evocation_illager.prepare_summon', 2.0, 1.0), (0.6, 'mob.ghast.fireball', 2.0, 0.8), (1.6, 'mob.ghast.fireball', 2.0, 0.8)],
    'raven': [(0.0, 'mob.evocation_illager.prepare_attack', 2.0, 1.3), (1.35, 'mob.enderdragon.flap', 2.0, 1.6), (2.55, 'mob.enderdragon.flap', 2.0, 1.6)],
    'nova': [(0.0, 'mob.evocation_illager.prepare_wololo', 2.0, 0.8), (0.4, 'beacon.power', 2.0, 0.7), (1.9, 'beacon.power', 2.0, 0.9)],
    'enrage': [(0.0, 'mob.enderdragon.growl', 3.0, 1.2)],
}


def command(mark, place):
    ent = 'bear:mark_' + mark
    kind, a, b = place

    def rel(v):
        return '~' + (('%g' % v) if v else '')
    if kind == 'players':
        return '/execute at @a[r=40] run summon %s %s ~ %s' % (ent, rel(a), rel(b))
    if kind == 'boss':
        return '/summon %s %s ~ %s' % (ent, rel(a), rel(b))
    return '/execute at @s facing entity %s feet rotated ~%s 0 positioned ^ ^ ^%g run summon %s ~ ~ ~' % (AIM, ('%g' % a) if a else '', b, ent)


def timeline(n):
    p = PATTERNS[n]
    tl = {}

    def add(t, c):
        tl.setdefault('%.2f' % t, []).append(c)
    if p['key'] == 'raven':
        add(0.0, '/tp @s ~ ~ ~ facing %s' % AIM)
    for t, snd, vol, pitch in SOUNDS[p['key']]:
        add(t, '/playsound %s @a[r=48] ~ ~ ~ %g %g' % (snd, vol, pitch))
    for t, mark, place in p['steps']:
        add(t, command(mark, place))
    add(p['length'] - 0.2, '@s bear:pattern_end')
    return {k: tl[k] for k in sorted(tl, key=float)}
