"""Assemble the add-on:  python3 make_pack.py V1
Writes ../V1/RavenWitch_RP, ../V1/RavenWitch_BP and ../RavenWitchBoss_V1.mcaddon"""
import json
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_witch  # noqa: E402
from mclib import render  # noqa: E402

VER = sys.argv[1] if len(sys.argv) > 1 else 'V1'
N = int(VER[1:])
ROOT = os.path.join(HERE, '..', VER)
RP, BP = os.path.join(ROOT, 'RavenWitch_RP'), os.path.join(ROOT, 'RavenWitch_BP')
UUID = {'rp': '6f0c1a52-8d3b-4c1e-9a47-2b5e7c9d1f01', 'rpm': '0a7d4e83-51c2-4f6b-b8e9-3c6f8a1d2e02',
        'bp': 'c3e9b7a1-2f4d-4a8c-8b16-7d5e9f0a3b03', 'bpm': '9b2f6d47-e1a8-4c35-a7d2-4e8c0b6f5a04'}


def W(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        if isinstance(obj, str):
            fh.write(obj)
        else:
            json.dump(obj, fh, indent=2, ensure_ascii=False)


shutil.rmtree(ROOT, ignore_errors=True)
# ---- model + texture
m = build_witch.build()
atlas = m.bake(max_w=1024)
os.makedirs(os.path.join(RP, 'textures', 'entity'), exist_ok=True)
atlas.save(os.path.join(RP, 'textures', 'entity', 'raven_witch.png'))
geo = m.to_json(bounds=(6, 5, 1.5))
W(os.path.join(RP, 'models', 'entity', 'raven_witch.geo.json'), geo)

# ---- resource pack
ver = [1, 0, N - 1]
W(os.path.join(RP, 'manifest.json'), {
    'format_version': 2,
    'header': {'name': 'Raven Witch Boss %s [RP]' % VER, 'description': '까마귀 마녀 보스 - 모델 / 텍스처 (%s)' % VER,
               'uuid': UUID['rp'], 'version': ver, 'min_engine_version': [1, 20, 80]},
    'modules': [{'type': 'resources', 'uuid': UUID['rpm'], 'version': ver}],
    'dependencies': [{'uuid': UUID['bp'], 'version': ver}]})
W(os.path.join(RP, 'entity', 'raven_witch.entity.json'), {
    'format_version': '1.10.0',
    'minecraft:client_entity': {'description': {
        'identifier': 'bear:raven_witch',
        'materials': {'default': 'entity_alphatest'},
        'textures': {'default': 'textures/entity/raven_witch'},
        'geometry': {'default': 'geometry.raven_witch'},
        'render_controllers': ['controller.render.raven_witch'],
        'spawn_egg': {'base_color': '#4B1E8A', 'overlay_color': '#F08A1A'},
        'scripts': {'animate': ['idle', 'look_at_target']},
        'animations': {'idle': 'animation.raven_witch.idle', 'look_at_target': 'animation.common.look_at_target'}}}})
W(os.path.join(RP, 'render_controllers', 'raven_witch.render_controllers.json'), {
    'format_version': '1.8.0',
    'render_controllers': {'controller.render.raven_witch': {
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ['Texture.default']}}})
W(os.path.join(RP, 'animations', 'raven_witch.animation.json'), {
    'format_version': '1.8.0',
    'animations': {'animation.raven_witch.idle': {
        'loop': True,
        'bones': {
            'body': {'position': [0, 'math.sin(query.life_time * 90) * 0.6', 0]},
            'raven': {'position': [0, 'math.sin(query.life_time * 220) * 0.8', 0]},
            'ravenWingR': {'rotation': [0, 0, 'math.sin(query.life_time * 520) * 16']},
            'ravenWingL': {'rotation': [0, 0, '-math.sin(query.life_time * 520) * 16']},
            'ravenHead': {'rotation': [0, 'math.sin(query.life_time * 60) * 10', 0]},
            'rightArm': {'rotation': [0, 0, 'math.sin(query.life_time * 90) * 2.5']},
            'leftArm': {'rotation': [0, 0, '-math.sin(query.life_time * 90) * 2.5']}}}}})
lang = 'entity.bear:raven_witch.name=%s\nitem.spawn_egg.entity.bear:raven_witch.name=%s\n'
W(os.path.join(RP, 'texts', 'en_US.lang'), lang % ('Raven Witch', 'Raven Witch Spawn Egg'))
W(os.path.join(RP, 'texts', 'ko_KR.lang'), lang % ('까마귀 마녀', '까마귀 마녀 생성 알'))
W(os.path.join(RP, 'texts', 'languages.json'), ['en_US', 'ko_KR'])

# ---- behaviour pack (only what is needed to summon and look at the model; the fight comes later)
W(os.path.join(BP, 'manifest.json'), {
    'format_version': 2,
    'header': {'name': 'Raven Witch Boss %s [BP]' % VER, 'description': '까마귀 마녀 보스 - 엔티티 (%s)' % VER,
               'uuid': UUID['bp'], 'version': ver, 'min_engine_version': [1, 20, 80]},
    'modules': [{'type': 'data', 'uuid': UUID['bpm'], 'version': ver}],
    'dependencies': [{'uuid': UUID['rp'], 'version': ver}]})
W(os.path.join(BP, 'entities', 'raven_witch.json'), {
    'format_version': '1.20.80',
    'minecraft:entity': {
        'description': {'identifier': 'bear:raven_witch', 'is_spawnable': True, 'is_summonable': True, 'is_experimental': False},
        'components': {
            'minecraft:type_family': {'family': ['raven_witch', 'boss', 'monster', 'mob']},
            'minecraft:health': {'value': 300, 'max': 300},
            'minecraft:collision_box': {'width': 1.3, 'height': 2.85},
            'minecraft:physics': {},
            'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': True},
            'minecraft:knockback_resistance': {'value': 1.0},
            'minecraft:movement': {'value': 0.2},
            'minecraft:movement.basic': {},
            'minecraft:navigation.walk': {'can_path_over_water': True},
            'minecraft:jump.static': {},
            'minecraft:nameable': {},
            'minecraft:persistent': {},
            'minecraft:boss': {'should_darken_sky': False, 'hud_range': 48},
            'minecraft:behavior.look_at_player': {'priority': 7, 'look_distance': 16, 'probability': 1.0},
            'minecraft:behavior.random_look_around': {'priority': 8}}}})

# ---- pack icons from the simulated front view
tex = atlas
icon = render(geo, tex, yaw=0, pitch=0, dist=400, target=(0, 23, 0), size=(256, 256), ortho=5.2, bg=(22, 10, 44), ss=4)
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
print('bones', len(m.bones), 'cubes', n, 'atlas', atlas.size, '->', os.path.normpath(out), os.path.getsize(out), 'bytes')
