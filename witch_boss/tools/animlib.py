"""Client animations of the Raven Witch and of the warning marks (Bedrock animation JSON), plus a
tiny evaluator so the same data can be posed in the software renderer.

Sign reminders (animation JSON values, entity faces -Z):
  rotation x < 0 : swings a hanging limb forward / leans a standing part back
  rotation z > 0 : lifts a part that sticks out to her RIGHT (-X);  z < 0 lifts one on her LEFT
  position       : same axes as the geometry (+X = her left, +Y = up, -Z = forward), 16 = one block
"""
import math
import re

LT = 'query.life_time'


def S(amp, speed, phase=0, base=0, t=LT):
    """Molang  base + sin(t*speed + phase) * amp"""
    s = 'math.sin(%s * %s%s) * %s' % (t, speed, (' + %s' % phase) if phase else '', amp)
    return ('%s + %s' % (base, s)) if base else s


def K(**frames):
    """K(t0_0=[..], t0_5=[..]) -> keyframe dict"""
    return {k[1:].replace('_', '.'): v for k, v in frames.items()}


def kf(*pairs):
    return {('%.3f' % t).rstrip('0').rstrip('.') if t else '0.0': v for t, v in pairs}


# =============================================================================== witch
def witch_animations():
    A = {}
    A['animation.raven_witch.idle'] = {'loop': True, 'bones': {
        'body': {'position': [0, S(0.8, 90, base=1.2), 0]},
        'torso': {'rotation': [S(1.2, 90, 40), 0, S(0.8, 45)]},
        'skirt': {'rotation': [S(1.0, 90, 200), 0, S(0.6, 45, 180)]},
        'head': {'rotation': [S(1.5, 90, 90), 0, S(1.2, 60)]},
        'hatTop': {'rotation': [S(2.5, 90, 150), 0, S(2.0, 70)]},
        'hatTip': {'rotation': [S(3.5, 90, 210), 0, S(3.0, 70, 60)]},
        'pumpkin': {'rotation': [0, 0, S(3.0, 120)]},
        'spiral': {'rotation': [0, 0, S(2.0, 80)]},
        'charm': {'rotation': [0, 0, S(14, 160)]},
        'hairBack': {'rotation': [S(2.5, 90, 180, base=2), 0, S(1.5, 55)]},
        'hairBackTip': {'rotation': [S(4.0, 90, 250), 0, S(2.5, 55, 70)]},
        'rightArm': {'rotation': [0, 0, S(2.5, 90, base=2.5)]},
        'rightSleeve': {'rotation': [S(3.0, 90, 120), 0, S(2.0, 90, 60)]},
        'leftArm': {'rotation': [0, 0, S(-2.5, 90, base=-2.5)]},
        'leftSleeve': {'rotation': [S(3.0, 90, 120), 0, S(-2.0, 90, 60)]},
        'raven': {'position': [0, S(0.9, 220, base=0.4), 0], 'rotation': [0, 0, S(3.0, 110)]},
        'ravenHead': {'rotation': [S(6, 75), S(12, 60), 0]},
        'ravenTail': {'rotation': [S(8, 220, 90), 0, 0]},
        'ravenWingR': {'rotation': [0, 0, S(22, 560)]},
        'ravenWingRTip': {'rotation': [0, 0, S(18, 560, -50)]},
        'ravenWingL': {'rotation': [0, 0, S(-22, 560)]},
        'ravenWingLTip': {'rotation': [0, 0, S(-18, 560, -50)]}}}
    # gliding toward the target: the whole figure leans, hair / sleeves / skirt trail behind
    A['animation.raven_witch.move'] = {'loop': True, 'bones': {
        'torso': {'rotation': [7, 0, 0]},
        'skirt': {'rotation': [6, 0, 0]},
        'head': {'rotation': [-5, 0, 0]},
        'hairBack': {'rotation': [12, 0, 0]},
        'hairBackTip': {'rotation': [10, 0, 0]},
        'hatTop': {'rotation': [-5, 0, 0]},
        'hatTip': {'rotation': [-6, 0, 0]},
        'rightSleeve': {'rotation': [12, 0, 0]},
        'leftSleeve': {'rotation': [12, 0, 0]}}}

    # ---- 1. hex circles: three flicks of the raised right arm (marks appear at 0.5 / 1.4 / 2.3)
    up, flick = [-118, 0, 14], [-88, 0, 8]
    A['animation.raven_witch.cast_hex'] = {'loop': 'hold_on_last_frame', 'animation_length': 4.2, 'bones': {
        'rightArm': {'rotation': kf((0, [0, 0, 0]), (0.4, up), (0.5, flick), (0.72, up), (1.3, up), (1.4, flick), (1.62, up), (2.2, up),
                                    (2.3, flick), (2.52, up), (3.5, [-112, 0, 14]), (3.95, [0, 0, 0]))},
        'rightSleeve': {'rotation': kf((0, [0, 0, 0]), (0.4, [-28, 0, 0]), (0.5, [-8, 0, 0]), (0.72, [-28, 0, 0]), (1.3, [-28, 0, 0]),
                                       (1.4, [-8, 0, 0]), (1.62, [-28, 0, 0]), (2.2, [-28, 0, 0]), (2.3, [-8, 0, 0]), (2.52, [-28, 0, 0]),
                                       (3.5, [-24, 0, 0]), (3.95, [0, 0, 0]))},
        'leftArm': {'rotation': kf((0, [0, 0, 0]), (0.4, [10, 0, -28]), (3.5, [10, 0, -28]), (3.95, [0, 0, 0]))},
        'torso': {'rotation': kf((0, [0, 0, 0]), (0.4, [-5, -10, 0]), (0.5, [1, -10, 0]), (0.72, [-5, -10, 0]), (1.3, [-5, -10, 0]),
                                 (1.4, [1, -10, 0]), (1.62, [-5, -10, 0]), (2.2, [-5, -10, 0]), (2.3, [1, -10, 0]), (2.52, [-5, -10, 0]),
                                 (3.5, [-4, -8, 0]), (3.95, [0, 0, 0]))},
        'hatTip': {'rotation': kf((0, [0, 0, 0]), (0.5, [10, 0, 0]), (0.8, [-4, 0, 0]), (1.4, [10, 0, 0]), (1.7, [-4, 0, 0]),
                                  (2.3, [10, 0, 0]), (2.6, [-4, 0, 0]), (3.9, [0, 0, 0]))},
        'body': {'position': kf((0, [0, 0, 0]), (0.4, [0, 2.5, 0]), (3.5, [0, 2.5, 0]), (3.95, [0, 0, 0]))}}}

    # ---- 2. pumpkin bombs: both arms thrown overhead (bombs called at 0.6 and 1.6)
    A['animation.raven_witch.cast_pumpkin'] = {'loop': 'hold_on_last_frame', 'animation_length': 4.6, 'bones': {
        'rightArm': {'rotation': kf((0, [0, 0, 0]), (0.45, [-118, 0, 32]), (0.6, [-62, 0, 20]), (0.9, [-118, 0, 32]), (1.45, [-118, 0, 32]),
                                    (1.6, [-62, 0, 20]), (1.9, [-112, 0, 32]), (3.3, [-100, 0, 40]), (4.1, [0, 0, 0]))},
        'leftArm': {'rotation': kf((0, [0, 0, 0]), (0.45, [-118, 0, -32]), (0.6, [-62, 0, -20]), (0.9, [-118, 0, -32]), (1.45, [-118, 0, -32]),
                                   (1.6, [-62, 0, -20]), (1.9, [-112, 0, -32]), (3.3, [-100, 0, -40]), (4.1, [0, 0, 0]))},
        'rightSleeve': {'rotation': kf((0, [0, 0, 0]), (0.45, [-20, 0, 12]), (3.3, [-16, 0, 10]), (4.1, [0, 0, 0]))},
        'leftSleeve': {'rotation': kf((0, [0, 0, 0]), (0.45, [-20, 0, -12]), (3.3, [-16, 0, -10]), (4.1, [0, 0, 0]))},
        'torso': {'rotation': kf((0, [0, 0, 0]), (0.45, [-9, 0, 0]), (0.6, [4, 0, 0]), (0.9, [-9, 0, 0]), (1.45, [-9, 0, 0]), (1.6, [4, 0, 0]),
                                 (1.9, [-7, 0, 0]), (3.3, [-5, 0, 0]), (4.1, [0, 0, 0]))},
        'head': {'rotation': kf((0, [0, 0, 0]), (0.45, [-12, 0, 0]), (3.3, [-8, 0, 0]), (4.1, [0, 0, 0]))},
        'pumpkin': {'position': kf((0, [0, 0, 0]), (0.45, [0, 1, 0]), (0.6, [0, 7, 0]), (0.95, [0, 0, 0]), (1.45, [0, 1, 0]), (1.6, [0, 7, 0]),
                                   (1.95, [0, 0, 0])),
                    'rotation': kf((0, [0, 0, 0]), (0.45, [0, 0, 0]), (0.95, [0, 360, 0]), (1.45, [0, 360, 0]), (1.95, [0, 720, 0])),
                    'scale': kf((0, [1, 1, 1]), (0.45, [1.15, 0.85, 1.15]), (0.6, [0.9, 1.4, 0.9]), (0.95, [1, 1, 1]), (1.45, [1.15, 0.85, 1.15]),
                                (1.6, [0.9, 1.4, 0.9]), (1.95, [1, 1, 1]))},
        'hatTop': {'rotation': kf((0, [0, 0, 0]), (0.6, [-8, 0, 0]), (0.95, [5, 0, 0]), (1.6, [-8, 0, 0]), (1.95, [5, 0, 0]), (2.4, [0, 0, 0]))},
        'body': {'position': kf((0, [0, 0, 0]), (0.45, [0, 3, 0]), (3.3, [0, 3, 0]), (4.1, [0, 0, 0]))}}}

    # ---- 3. raven dive: she points, the raven lines up in front of her and shoots down the lane
    #         (lanes appear at 0.5 and 1.7, are hit at 1.4 and 2.6)
    perch, ready, far = [0, 0, 0], [16, -20, -22], [16, -30, -300]
    A['animation.raven_witch.cast_raven'] = {'loop': 'hold_on_last_frame', 'animation_length': 3.6, 'bones': {
        'leftArm': {'rotation': kf((0, [0, 0, 0]), (0.4, [-95, 0, -6]), (1.3, [-95, 0, -6]), (1.4, [-70, 0, -6]), (1.6, [-95, 0, -6]),
                                   (2.5, [-95, 0, -6]), (2.6, [-70, 0, -6]), (2.9, [-90, 0, -6]), (3.4, [0, 0, 0]))},
        'leftSleeve': {'rotation': kf((0, [0, 0, 0]), (0.4, [-15, 0, 0]), (2.9, [-15, 0, 0]), (3.4, [0, 0, 0]))},
        'rightArm': {'rotation': kf((0, [0, 0, 0]), (0.4, [25, 0, 18]), (2.9, [25, 0, 18]), (3.4, [0, 0, 0]))},
        'torso': {'rotation': kf((0, [0, 0, 0]), (0.4, [4, 14, 0]), (2.9, [4, 14, 0]), (3.4, [0, 0, 0]))},
        'raven': {'position': kf((0, perch), (0.5, ready), (1.3, [16, -18, -16]), (1.4, [16, -28, -120]), (1.52, far), (1.7, ready),
                                 (2.5, [16, -18, -16]), (2.6, [16, -28, -120]), (2.72, far), (2.95, ready), (3.4, perch)),
                  'rotation': kf((0, [0, 0, 0]), (0.5, [20, 0, 0]), (1.3, [-15, 0, 0]), (1.4, [60, 0, 0]), (1.52, [60, 0, 0]), (1.7, [20, 0, 0]),
                                 (2.5, [-15, 0, 0]), (2.6, [60, 0, 0]), (2.72, [60, 0, 0]), (2.95, [10, 0, 0]), (3.4, [0, 0, 0])),
                  'scale': kf((0, [1, 1, 1]), (0.5, [1.5, 1.5, 1.5]), (2.95, [1.5, 1.5, 1.5]), (3.4, [1, 1, 1]))}}}

    # ---- 4. nova: blast around her (called 0.4, hits 1.9), then the outer ring (called 1.9, hits 3.4)
    A['animation.raven_witch.cast_nova'] = {'loop': 'hold_on_last_frame', 'animation_length': 4.6, 'bones': {
        'body': {'position': kf((0, [0, 0, 0]), (0.4, [0, -1, 0]), (1.8, [0, 7, 0]), (1.9, [0, 0, 0]), (2.3, [0, 3, 0]), (3.3, [0, 9, 0]),
                                (3.4, [0, 0, 0]), (4.2, [0, 0, 0])),
                 'rotation': kf((0, [0, 0, 0]), (1.8, [0, 0, 0]), (2.3, [0, 360, 0]), (4.2, [0, 360, 0])),
                 'scale': kf((0, [1, 1, 1]), (0.4, [1.05, 0.93, 1.05]), (1.8, [0.97, 1.05, 0.97]), (1.9, [1.1, 0.9, 1.1]), (2.2, [1, 1, 1]),
                             (3.3, [0.97, 1.05, 0.97]), (3.4, [1.1, 0.9, 1.1]), (3.7, [1, 1, 1]))},
        'rightArm': {'rotation': kf((0, [0, 0, 0]), (0.4, [-55, -40, 0]), (1.8, [-70, -45, 0]), (1.9, [0, 0, 105]), (2.4, [0, 0, 60]),
                                    (3.3, [-112, 0, 50]), (3.4, [-40, 0, 20]), (4.2, [0, 0, 0]))},
        'leftArm': {'rotation': kf((0, [0, 0, 0]), (0.4, [-55, 40, 0]), (1.8, [-70, 45, 0]), (1.9, [0, 0, -105]), (2.4, [0, 0, -60]),
                                   (3.3, [-112, 0, -50]), (3.4, [-40, 0, -20]), (4.2, [0, 0, 0]))},
        'torso': {'rotation': kf((0, [0, 0, 0]), (0.4, [8, 0, 0]), (1.8, [10, 0, 0]), (1.9, [-10, 0, 0]), (2.4, [0, 0, 0]), (3.3, [-10, 0, 0]),
                                 (3.4, [12, 0, 0]), (4.2, [0, 0, 0]))},
        'head': {'rotation': kf((0, [0, 0, 0]), (0.4, [10, 0, 0]), (1.8, [12, 0, 0]), (1.9, [-12, 0, 0]), (2.4, [0, 0, 0]), (3.3, [-14, 0, 0]),
                                (3.4, [8, 0, 0]), (4.2, [0, 0, 0]))},
        'hairBack': {'rotation': kf((0, [0, 0, 0]), (1.9, [0, 0, 0]), (2.1, [28, 0, 0]), (2.6, [0, 0, 0]), (3.4, [0, 0, 0]), (3.55, [24, 0, 0]),
                                    (4.0, [0, 0, 0]))},
        'hairBackTip': {'rotation': kf((0, [0, 0, 0]), (1.9, [0, 0, 0]), (2.15, [24, 0, 0]), (2.7, [0, 0, 0]), (3.4, [0, 0, 0]),
                                       (3.6, [20, 0, 0]), (4.1, [0, 0, 0]))},
        'skirt': {'scale': kf((0, [1, 1, 1]), (1.9, [1, 1, 1]), (2.05, [1.18, 0.95, 1.18]), (2.5, [1, 1, 1]), (3.4, [1, 1, 1]),
                              (3.55, [1.18, 0.95, 1.18]), (4.0, [1, 1, 1]))},
        'hatTip': {'rotation': kf((0, [0, 0, 0]), (0.4, [12, 0, 0]), (1.9, [14, 0, 0]), (2.1, [-14, 0, 0]), (2.6, [0, 0, 0]), (3.4, [10, 0, 0]),
                                  (3.6, [-12, 0, 0]), (4.1, [0, 0, 0]))}}}

    # ---- phase change: she rises, shakes, and slams a blast around herself (called 0.2, hits 1.7)
    A['animation.raven_witch.enrage'] = {'loop': 'hold_on_last_frame', 'animation_length': 2.8, 'bones': {
        'body': {'position': kf((0, [0, 0, 0]), (1.5, [0, 12, 0]), (1.7, [0, -1, 0]), (2.4, [0, 0, 0]))},
        'rightArm': {'rotation': kf((0, [0, 0, 0]), (0.5, [-20, 0, 112]), (1.5, [-105, 0, 58]), (1.7, [-50, 0, 25]), (2.4, [0, 0, 0]))},
        'leftArm': {'rotation': kf((0, [0, 0, 0]), (0.5, [-20, 0, -112]), (1.5, [-105, 0, -58]), (1.7, [-50, 0, -25]), (2.4, [0, 0, 0]))},
        'head': {'rotation': kf((0, [0, 0, 0]), (0.5, [-16, 0, 0]), (1.5, [-20, 0, 0]), (1.7, [14, 0, 0]), (2.4, [0, 0, 0]))},
        'torso': {'rotation': kf((0, [0, 0, 0]), (0.5, [-8, 0, 0]), (1.5, [-10, 0, 0]), (1.7, [14, 0, 0]), (2.4, [0, 0, 0]))},
        'hatTop': {'rotation': [0, 0, 'query.anim_time < 1.7 ? math.sin(query.anim_time * 2400) * 5 : 0']},
        'hatTip': {'rotation': [0, 0, 'query.anim_time < 1.7 ? math.sin(query.anim_time * 2400 + 90) * 8 : 0']},
        'hairBack': {'rotation': kf((0, [0, 0, 0]), (1.5, [-6, 0, 0]), (1.85, [30, 0, 0]), (2.5, [0, 0, 0]))},
        'skirt': {'scale': kf((0, [1, 1, 1]), (1.7, [1, 1, 1]), (1.85, [1.2, 0.94, 1.2]), (2.4, [1, 1, 1]))},
        'raven': {'position': kf((0, [0, 0, 0]), (1.5, [0, 16, 0]), (2.4, [0, 0, 0]))}}}
    return A


WITCH_STATES = {   # client state  ->  (variants that select it, animation short name)
    'hex': ((1, 11), 'cast_hex'), 'pumpkin': ((2, 12), 'cast_pumpkin'), 'raven': ((3, 13), 'cast_raven'),
    'nova': ((4, 14), 'cast_nova'), 'enrage': ((9,), 'enrage')}


def witch_controller():
    states = {'default': {'transitions': [{k: ' || '.join('query.variant == %d' % n for n in vs)} for k, (vs, _) in WITCH_STATES.items()],
                          'blend_transition': 0.2}}
    for k, (vs, an) in WITCH_STATES.items():
        states[k] = {'animations': [an], 'blend_transition': 0.15,
                     'transitions': [{'default': ' && '.join('query.variant != %d' % n for n in vs)}]}
    return {'format_version': '1.10.0', 'animation_controllers': {'controller.animation.raven_witch.attack': {
        'initial_state': 'default', 'states': states}}}


# =============================================================================== warning marks
def mark_animation(warn, bomb=False):
    """warn seconds of warning (the fill grows until it touches the rim), then the eruption"""
    w = warn
    bones = {
        'rim': {'scale': kf((0, [0.2, 1, 0.2]), (0.12, [1.06, 1, 1.06]), (0.2, [1, 1, 1]), (w - 0.3, [1, 1, 1]), (w - 0.22, [1.04, 1.6, 1.04]),
                            (w - 0.15, [1, 1, 1]), (w - 0.07, [1.04, 1.6, 1.04]), (w, [1, 1, 1]), (w + 0.12, [1.12, 0.3, 1.12]),
                            (w + 0.22, [0, 0, 0]))},
        'rune': {'rotation': [0, 'query.anim_time * 80', 0],
                 'scale': kf((0, [0.2, 1, 0.2]), (0.15, [1, 1, 1]), (w, [1, 1, 1]), (w + 0.1, [0, 0, 0]))},
        'fill': {'scale': kf((0, [0.04, 1, 0.04]), (w, [1, 1, 1]), (w + 0.1, [1, 1, 1]), (w + 0.2, [0, 0, 0]))},
        'burst': {'scale': kf((0, [0, 0, 0]), (w - 0.01, [0, 0, 0]), (w, [1, 0.15, 1]), (w + 0.1, [1, 1.25, 1]), (w + 0.22, [1.05, 1, 1.05]),
                              (w + 0.42, [1.15, 0, 1.15]))}}
    if bomb:
        bones['bomb'] = {'position': kf((0, [0, 150, 0]), (w * 0.35, [0, 120, 0]), (w, [0, 0, 0])),
                         'rotation': [0, 'query.anim_time * 300', 'math.sin(query.anim_time * 500) * 12'],
                         'scale': kf((0, [0.6, 0.6, 0.6]), (w * 0.6, [1, 1, 1]), (w, [1.15, 1.15, 1.15]), (w + 0.06, [0, 0, 0]))}
    return {'loop': 'hold_on_last_frame', 'animation_length': round(w + 0.5, 3), 'bones': bones}


# =============================================================================== evaluator
def _molang(expr, t, life):
    if not isinstance(expr, str):
        return float(expr)
    e = expr.replace('query.life_time', repr(life)).replace('q.life_time', repr(life))
    e = e.replace('query.anim_time', repr(t)).replace('q.anim_time', repr(t))
    e = e.replace('math.sin', '_s').replace('math.cos', '_c').replace('math.abs', 'abs').replace('math.min', 'min').replace('math.max', 'max')
    m = re.match(r'^(.*)\?(.*):(.*)$', e)
    if m:
        e = '(%s) if (%s) else (%s)' % (m.group(2), m.group(1), m.group(3))
    return float(eval(e, {'_s': lambda d: math.sin(math.radians(d)), '_c': lambda d: math.cos(math.radians(d)), 'abs': abs, 'min': min, 'max': max}))


def _channel(ch, t, life):
    if isinstance(ch, dict):
        ks = sorted(ch, key=float)
        ts = [float(k) for k in ks]
        if t <= ts[0]:
            return [_molang(v, t, life) for v in ch[ks[0]]]
        if t >= ts[-1]:
            return [_molang(v, t, life) for v in ch[ks[-1]]]
        for i in range(len(ts) - 1):
            if ts[i] <= t <= ts[i + 1]:
                f = (t - ts[i]) / (ts[i + 1] - ts[i])
                a = [_molang(v, t, life) for v in ch[ks[i]]]
                b = [_molang(v, t, life) for v in ch[ks[i + 1]]]
                return [a[j] + (b[j] - a[j]) * f for j in range(3)]
    return [_molang(v, t, life) for v in ch]


def pose(layers, life=0.0):
    """layers: [(animation dict, time, weight)] -> pose dict for mclib.render"""
    out = {}
    for anim, t, wgt in layers:
        for bone, chans in anim['bones'].items():
            p = out.setdefault(bone, {'rot': [0, 0, 0], 'pos': [0, 0, 0], 'scale': [1, 1, 1]})
            if 'rotation' in chans:
                r = _channel(chans['rotation'], t, life)
                p['rot'] = [p['rot'][i] + r[i] * wgt for i in range(3)]
            if 'position' in chans:
                r = _channel(chans['position'], t, life)
                p['pos'] = [p['pos'][i] + r[i] * wgt for i in range(3)]
            if 'scale' in chans:
                r = _channel(chans['scale'], t, life)
                p['scale'] = [p['scale'][i] * (1 + (r[i] - 1) * wgt) for i in range(3)]
    return out
