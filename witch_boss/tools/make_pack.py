"""Assemble the add-on:  python3 make_pack.py V3
Writes ../V3/RavenWitch_RP, ../V3/RavenWitch_BP and ../RavenWitchBoss_V3.mcaddon

Fight design: the boss itself never deals damage.  Its patterns (patterns.py) only summon warning
marks; each mark shows the area for its warning time and then deals the damage (see mark_entity).
"""
import json
import os
import shutil
import sys
import zipfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_witch  # noqa: E402
import build_marks  # noqa: E402
import animlib  # noqa: E402
import patterns  # noqa: E402
from mclib import render  # noqa: E402

VER = sys.argv[1] if len(sys.argv) > 1 else 'V3'
N = int(VER[1:])
ROOT = os.path.join(HERE, '..', VER)
RP, BP = os.path.join(ROOT, 'RavenWitch_RP'), os.path.join(ROOT, 'RavenWitch_BP')
UUID = {'rp': '6f0c1a52-8d3b-4c1e-9a47-2b5e7c9d1f01', 'rpm': '0a7d4e83-51c2-4f6b-b8e9-3c6f8a1d2e02',
        'bp': 'c3e9b7a1-2f4d-4a8c-8b16-7d5e9f0a3b03', 'bpm': '9b2f6d47-e1a8-4c35-a7d2-4e8c0b6f5a04'}
FMT = '1.20.80'
MARKS = build_marks.MARKS
PAT = patterns.PATTERNS
MAX_HP = 300


def W(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=2, ensure_ascii=False)


shutil.rmtree(ROOT, ignore_errors=True)
ver = [1, 0, N - 1]

# ======================================================================== resource pack
W(os.path.join(RP, 'manifest.json'), {
    'format_version': 2,
    'header': {'name': 'Raven Witch Boss %s [RP]' % VER, 'description': '까마귀 마녀 보스 - 모델 / 애니메이션 / 예고 표시 (%s)' % VER,
               'uuid': UUID['rp'], 'version': ver, 'min_engine_version': [1, 20, 80]},
    'modules': [{'type': 'resources', 'uuid': UUID['rpm'], 'version': ver}],
    'dependencies': [{'uuid': UUID['bp'], 'version': ver}]})

# ---- witch model + texture
m = build_witch.build()
atlas = m.bake(max_w=1024)
os.makedirs(os.path.join(RP, 'textures', 'entity'), exist_ok=True)
atlas.save(os.path.join(RP, 'textures', 'entity', 'raven_witch.png'))
geo = m.to_json(bounds=(44, 8, 2))          # wide bounds: the raven flies far out during its dive
W(os.path.join(RP, 'models', 'entity', 'raven_witch.geo.json'), geo)

# ---- witch animations
A = animlib.witch_animations()
A['animation.raven_witch.aura'] = {'loop': True, 'animation_length': 1.0, 'particle_effects': {'0.0': {'effect': 'aura', 'locator': 'aura'}}}
A['animation.raven_witch.rage_aura'] = {'loop': True, 'animation_length': 1.0, 'particle_effects': {'0.0': {'effect': 'rage', 'locator': 'aura'}}}
W(os.path.join(RP, 'animations', 'raven_witch.animation.json'), {'format_version': '1.8.0', 'animations': A})
W(os.path.join(RP, 'animation_controllers', 'raven_witch.animation_controllers.json'), animlib.witch_controller())
anims = {'idle': 'animation.raven_witch.idle', 'move': 'animation.raven_witch.move', 'look_at_target': 'animation.common.look_at_target',
         'attack': 'controller.animation.raven_witch.attack', 'aura': 'animation.raven_witch.aura', 'rage_aura': 'animation.raven_witch.rage_aura'}
for k, (vs, an) in animlib.WITCH_STATES.items():
    anims[an] = 'animation.raven_witch.' + an
W(os.path.join(RP, 'entity', 'raven_witch.entity.json'), {
    'format_version': '1.10.0',
    'minecraft:client_entity': {'description': {
        'identifier': 'bear:raven_witch',
        'materials': {'default': 'entity_alphatest'},
        'textures': {'default': 'textures/entity/raven_witch'},
        'geometry': {'default': 'geometry.raven_witch'},
        'render_controllers': ['controller.render.raven_witch'],
        'spawn_egg': {'base_color': '#4B1E8A', 'overlay_color': '#F08A1A'},
        'particle_effects': {'aura': 'bear:witch_aura', 'rage': 'bear:witch_rage'},
        'scripts': {'animate': ['idle', {'move': 'math.min(1.0, query.modified_move_speed * 2.5)'}, 'look_at_target', 'attack', 'aura',
                                {'rage_aura': 'query.mark_variant == 1'}]},
        'animations': anims}}})
rc = {'controller.render.raven_witch': {'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ['Texture.default']},
      'controller.render.bear_mark': {'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ['Texture.default'],
                                      'ignore_lighting': True}}
W(os.path.join(RP, 'render_controllers', 'raven_witch.render_controllers.json'), {'format_version': '1.8.0', 'render_controllers': rc})

# ---- warning marks: model, texture, client entity, animation
mark_models = build_marks.build_all(os.path.join(ROOT, '_marks'))
mark_anims = {}
for name, q in MARKS.items():
    g, tex = mark_models[name]
    tex.save(os.path.join(RP, 'textures', 'entity', 'mark_%s.png' % name))
    W(os.path.join(RP, 'models', 'entity', 'mark_%s.geo.json' % name), g)
    mark_anims['animation.bear_mark.' + name] = animlib.mark_animation(q['warn'], q.get('bomb', False))
    W(os.path.join(RP, 'entity', 'mark_%s.entity.json' % name), {
        'format_version': '1.10.0',
        'minecraft:client_entity': {'description': {
            'identifier': 'bear:mark_' + name,
            'materials': {'default': 'entity_alphatest'},
            'textures': {'default': 'textures/entity/mark_' + name},
            'geometry': {'default': 'geometry.bear_mark_' + name},
            'render_controllers': ['controller.render.bear_mark'],
            'scripts': {'animate': ['life']},
            'animations': {'life': 'animation.bear_mark.' + name}}}})
shutil.rmtree(os.path.join(ROOT, '_marks'))
W(os.path.join(RP, 'animations', 'bear_mark.animation.json'), {'format_version': '1.8.0', 'animations': mark_anims})

# ---- particles (own little square spark texture; billboards are only used for sparks, never for the models)
sp = np.zeros((8, 16, 4), np.uint8)
sp[1:7, 1:7] = (255, 255, 255, 255)
sp[0, 2:6] = sp[7, 2:6] = (255, 255, 255, 255)
sp[2:6, 0] = sp[2:6, 7] = (255, 255, 255, 255)
for i in range(4):
    sp[3 - i:5 + i, 8 + i] = sp[3 - i:5 + i, 15 - i] = (255, 255, 255, 255)     # diamond
os.makedirs(os.path.join(RP, 'textures', 'particle'), exist_ok=True)
Image.fromarray(sp, 'RGBA').save(os.path.join(RP, 'textures', 'particle', 'bear_spark.png'))
AGE = 'variable.particle_age / variable.particle_lifetime'


def particle(ident, comps, size, grad, frame=0):
    c = {'minecraft:particle_appearance_billboard': {
        'size': ['%g * (1 - %s) + 0.02' % (size, AGE)] * 2, 'facing_camera_mode': 'lookat_xyz',
        'uv': {'texture_width': 16, 'texture_height': 8, 'uv': [8 * frame, 0], 'uv_size': [8, 8]}},
        'minecraft:particle_appearance_tinting': {'color': {'interpolant': AGE, 'gradient': grad}}}
    c.update(comps)
    W(os.path.join(RP, 'particles', ident.split(':')[1] + '.particle.json'), {'format_version': '1.10.0', 'particle_effect': {
        'description': {'identifier': ident, 'basic_render_parameters': {'material': 'particles_alpha', 'texture': 'textures/particle/bear_spark'}},
        'components': c}})


def argb(h):
    h = h.lstrip('#')
    return [round(int(h[i:i + 2], 16) / 255., 3) for i in (0, 2, 4)] + [1.0]


for ident, rate, cols in (('bear:witch_aura', 9, ['#F0C8FF', '#B45CFF', '#5A1EC8']), ('bear:witch_rage', 16, ['#FFE0F0', '#FF5A9A', '#B41E5A'])):
    particle(ident, {
        'minecraft:emitter_rate_steady': {'spawn_rate': rate, 'max_particles': 60},
        'minecraft:emitter_lifetime_once': {'active_time': 1.0},
        'minecraft:emitter_shape_box': {'offset': [0, 0.1, 0], 'half_dimensions': [1.0, 0.7, 1.0], 'direction': [0, 1, 0]},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 'math.random(0.9, 1.8)'},
        'minecraft:particle_initial_speed': 'math.random(0.3, 1.1)',
        'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, 0.8, 0], 'linear_drag_coefficient': 0.5}},
        0.14, {'0.0': argb(cols[0]), '0.5': argb(cols[1]), '1.0': argb(cols[2])}, frame=1)
for name, q in MARKS.items():
    shape = {'offset': [0, 0.15, 0], 'radius': q['R'], 'plane_normal': [0, 1, 0], 'surface_only': False, 'direction': [0, 1, 0]}
    if q['r0']:          # the ring only erupts on its band, never in the safe middle
        shape.update(radius=(q['R'] + q['r0']) / 2, surface_only=True)
    particle('bear:burst_' + name, {
        'minecraft:emitter_rate_instant': {'num_particles': int(min(160, 14 * q['R'] ** 1.5 + 20))},
        'minecraft:emitter_lifetime_once': {'active_time': 0.2},
        'minecraft:emitter_shape_disc': shape,
        'minecraft:particle_lifetime_expression': {'max_lifetime': 'math.random(0.45, 1.1)'},
        'minecraft:particle_initial_speed': 'math.random(3, 10)',
        'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, -10, 0], 'linear_drag_coefficient': 1.0}},
        0.2, {'0.0': argb(q['burst'][3]), '0.4': argb(q['burst'][2]), '1.0': argb(q['burst'][1])})

MARK_NAMES = {'hex': ('Hex Circle', '저주 마법진'), 'seed': ('Pumpkin Bomb', '호박 폭탄'), 'wave': ('Raven Dive', '까마귀 돌진'),
              'nova': ('Nova', '폭발'), 'ring': ('Nova Ring', '폭발 고리')}
for code, i, names in (('en_US', 0, ('Raven Witch', 'Raven Witch Spawn Egg')), ('ko_KR', 1, ('까마귀 마녀', '까마귀 마녀 생성 알'))):
    lang = 'entity.bear:raven_witch.name=%s\nitem.spawn_egg.entity.bear:raven_witch.name=%s\n' % names
    lang += ''.join('entity.bear:mark_%s.name=%s\n' % (k, v[i]) for k, v in MARK_NAMES.items())
    W(os.path.join(RP, 'texts', code + '.lang'), lang)
W(os.path.join(RP, 'texts', 'languages.json'), ['en_US', 'ko_KR'])

# ======================================================================== behaviour pack
W(os.path.join(BP, 'manifest.json'), {
    'format_version': 2,
    'header': {'name': 'Raven Witch Boss %s [BP]' % VER, 'description': '까마귀 마녀 보스 - 보스전 패턴 (%s)' % VER,
               'uuid': UUID['bp'], 'version': ver, 'min_engine_version': [1, 20, 80]},
    'modules': [{'type': 'data', 'uuid': UUID['bpm'], 'version': ver}],
    'dependencies': [{'uuid': UUID['rp'], 'version': ver}]})

# ---- the boss
P1 = [n for n in PAT if n < 9]
P2 = [n for n in PAT if n > 9]
ALLPAT = ['bear:pat_%d' % n for n in PAT]
groups = {
    'bear:idle_p1': {'minecraft:variant': {'value': 0}, 'minecraft:movement': {'value': 0.2},
                     'minecraft:timer': {'looping': True, 'time': [3.0, 4.5], 'time_down_event': {'event': 'bear:pick_pattern', 'target': 'self'}}},
    'bear:idle_p2': {'minecraft:variant': {'value': 0}, 'minecraft:movement': {'value': 0.26},
                     'minecraft:timer': {'looping': True, 'time': [1.8, 2.8], 'time_down_event': {'event': 'bear:pick_pattern', 'target': 'self'}}},
    'bear:phase2': {'minecraft:mark_variant': {'value': 1}}}
for n in PAT:
    # (the timer is only a safety net: the pattern's own timeline ends it 0.2 s before its length)
    groups['bear:pat_%d' % n] = {'minecraft:variant': {'value': n}, 'minecraft:movement': {'value': 0.0},
                                 'minecraft:timer': {'looping': False, 'time': round(PAT[n]['length'] + 1.0, 2),
                                                     'time_down_event': {'event': 'bear:pattern_end', 'target': 'self'}}}


def is_phase(n):
    return {'test': 'is_mark_variant', 'subject': 'self', 'operator': '==', 'value': n}


def pick(idle, pats):
    return [{'weight': 1, 'remove': {'component_groups': [idle]}, 'add': {'component_groups': ['bear:pat_%d' % n]}} for n in pats]


events = {
    'minecraft:entity_spawned': {'add': {'component_groups': ['bear:idle_p1']}},
    'bear:pick_pattern': {'sequence': [
        {'filters': {'all_of': [{'test': 'has_target', 'subject': 'self', 'value': True}, is_phase(0)]}, 'randomize': pick('bear:idle_p1', P1)},
        {'filters': {'all_of': [{'test': 'has_target', 'subject': 'self', 'value': True}, is_phase(1)]}, 'randomize': pick('bear:idle_p2', P2)}]},
    'bear:pattern_end': {'sequence': [
        {'remove': {'component_groups': ALLPAT}},
        {'filters': is_phase(0), 'add': {'component_groups': ['bear:idle_p1']}},
        {'filters': is_phase(1), 'add': {'component_groups': ['bear:idle_p2']}}]},
    'bear:enrage': {'remove': {'component_groups': ['bear:idle_p1']}, 'add': {'component_groups': ['bear:phase2', 'bear:pat_9']}}}
bp_anims = {'pattern': 'controller.animation.raven_witch.pattern'}
bp_anims.update({'pat_%d' % n: 'animation.raven_witch.pat_%d' % n for n in PAT})
W(os.path.join(BP, 'entities', 'raven_witch.json'), {
    'format_version': FMT,
    'minecraft:entity': {
        'description': {'identifier': 'bear:raven_witch', 'is_spawnable': True, 'is_summonable': True, 'is_experimental': False,
                        'animations': bp_anims, 'scripts': {'animate': ['pattern']}},
        'component_groups': groups,
        'components': {
            'minecraft:type_family': {'family': ['raven_witch', 'bear_boss', 'boss', 'mob']},
            'minecraft:health': {'value': MAX_HP, 'max': MAX_HP},
            'minecraft:collision_box': {'width': 1.3, 'height': 2.85},
            'minecraft:physics': {},
            'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': True},
            'minecraft:knockback_resistance': {'value': 1.0},
            'minecraft:damage_sensor': {'triggers': [{'cause': 'fall', 'deals_damage': False}]},
            'minecraft:variant': {'value': 0},
            'minecraft:mark_variant': {'value': 0},
            'minecraft:movement': {'value': 0.2},
            'minecraft:movement.basic': {},
            'minecraft:navigation.walk': {'can_path_over_water': True, 'avoid_water': True},
            'minecraft:jump.static': {},
            'minecraft:follow_range': {'value': 48, 'max': 48},
            'minecraft:nameable': {},
            'minecraft:persistent': {},
            'minecraft:experience_reward': {'on_death': 'query.last_hit_by_player ? 60 : 0'},
            'minecraft:boss': {'should_darken_sky': False, 'hud_range': 55},
            # phase change at half health - only between patterns, and only once
            'minecraft:environment_sensor': {'triggers': [{
                'filters': {'all_of': [{'test': 'actor_health', 'subject': 'self', 'operator': '<=', 'value': MAX_HP // 2},
                                       is_phase(0), {'test': 'is_variant', 'subject': 'self', 'operator': '==', 'value': 0}]},
                'event': 'bear:enrage', 'target': 'self'}]},
            'minecraft:behavior.float': {'priority': 0},
            'minecraft:behavior.nearest_attackable_target': {
                'priority': 1, 'must_see': False, 'reselect_targets': True, 'within_radius': 40,
                'entity_types': [{'filters': {'test': 'is_family', 'subject': 'other', 'value': 'player'}, 'max_dist': 40}]},
            'minecraft:behavior.move_towards_target': {'priority': 3, 'speed_multiplier': 1.0, 'within_radius': 40},
            'minecraft:behavior.look_at_player': {'priority': 6, 'look_distance': 40, 'probability': 1.0},
            'minecraft:behavior.random_stroll': {'priority': 7, 'speed_multiplier': 0.8},
            'minecraft:behavior.random_look_around': {'priority': 8}},
        'events': events}})

# server side: one state per pattern; the state's animation is a timeline of commands
states = {'idle': {'transitions': [{'pat_%d' % n: 'query.variant == %d' % n} for n in PAT] + [{'dead': '!query.is_alive'}]},
          'dead': {'on_entry': ['/event entity @e[family=witch_mark,r=64] bear:despawn', '/particle bear:burst_nova ~ ~1 ~',
                                '/playsound mob.wither.death @a[r=64] ~ ~ ~ 2 1.3']}}
bp_tl = {}
for n, p in PAT.items():
    states['pat_%d' % n] = {'animations': ['pat_%d' % n], 'transitions': [{'idle': 'query.variant != %d' % n}, {'dead': '!query.is_alive'}]}
    bp_tl['animation.raven_witch.pat_%d' % n] = {'loop': False, 'animation_length': p['length'], 'timeline': patterns.timeline(n)}
W(os.path.join(BP, 'animation_controllers', 'raven_witch.animation_controllers.json'), {
    'format_version': '1.10.0', 'animation_controllers': {'controller.animation.raven_witch.pattern': {'initial_state': 'idle', 'states': states}}})
W(os.path.join(BP, 'animations', 'raven_witch.animation.json'), {'format_version': '1.10.0', 'animations': bp_tl})

# ---- the marks: show the area for `warn` seconds, then hit it, then vanish
SAFE = 'family=!bear_boss'
mark_tl = {}
for name, q in MARKS.items():
    w = q['warn']
    sel = '@e[r=%g,%s]' % (q['R'], SAFE) if not q['r0'] else '@e[rm=%g,r=%g,%s]' % (q['r0'], q['R'], SAFE)
    vol = {'wave': 0.5, 'hex': 1.0, 'seed': 1.2, 'nova': 2.0, 'ring': 2.0}[name]
    pitch = {'wave': 1.8, 'hex': 1.4, 'seed': 0.9, 'nova': 0.7, 'ring': 0.6}[name]
    mark_tl['animation.bear_mark.%s.life' % name] = {'loop': False, 'animation_length': round(w + 0.7, 2), 'timeline': {
        '%.2f' % w: ['/damage %s %d magic' % (sel, q['dmg']), '/particle bear:burst_%s ~ ~ ~' % name,
                     '/playsound random.explode @a[r=40] ~ ~ ~ %g %g' % (vol, pitch)],
        '%.2f' % (w + 0.45): ['@s bear:despawn']}}
    W(os.path.join(BP, 'entities', 'mark_%s.json' % name), {
        'format_version': FMT,
        'minecraft:entity': {
            'description': {'identifier': 'bear:mark_' + name, 'is_spawnable': False, 'is_summonable': True, 'is_experimental': False,
                            'animations': {'life': 'animation.bear_mark.%s.life' % name}, 'scripts': {'animate': ['life']}},
            'component_groups': {'bear:despawn': {'minecraft:instant_despawn': {}}},
            'components': {
                'minecraft:type_family': {'family': ['bear_boss', 'witch_mark', 'inanimate']},
                'minecraft:collision_box': {'width': 0.2, 'height': 0.1},
                'minecraft:physics': {'has_gravity': True, 'has_collision': True},
                'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
                'minecraft:health': {'value': 1, 'max': 1},
                'minecraft:damage_sensor': {'triggers': [{'cause': 'all', 'deals_damage': False}]},
                'minecraft:knockback_resistance': {'value': 1.0},
                'minecraft:fire_immune': {},
                # safety net: never stays in the world, whatever happens
                'minecraft:timer': {'looping': False, 'time': round(w + 3.0, 2), 'time_down_event': {'event': 'bear:despawn', 'target': 'self'}}},
            'events': {'bear:despawn': {'add': {'component_groups': ['bear:despawn']}}}}})
W(os.path.join(BP, 'animations', 'bear_mark.animation.json'), {'format_version': '1.10.0', 'animations': mark_tl})

# ---- pack icons from the simulated view
icon = render(geo, atlas, yaw=28, pitch=8, dist=150, target=(0, 23, 0), size=(256, 256), fov=24, bg=(22, 10, 44), ss=4)
for p in (RP, BP):
    icon.save(os.path.join(p, 'pack_icon.png'))

# ---- .mcaddon
out = os.path.join(HERE, '..', 'RavenWitchBoss_%s.mcaddon' % VER)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for base in (RP, BP):
        for dp, _, fns in os.walk(base):
            for fn in sorted(fns):
                full = os.path.join(dp, fn)
                z.write(full, os.path.relpath(full, ROOT))
n = sum(len(b.cubes) for b in m.bones)
print('witch: bones', len(m.bones), 'cubes', n, 'atlas', atlas.size, '->', os.path.normpath(out), os.path.getsize(out), 'bytes')
