#!/usr/bin/env python3
"""Builds the Starnight Witch addon (resource + behavior pack) and zips it as .mcaddon.
Usage: python3 build_pack.py [version_number]   (default 1 -> V1)"""
import json, os, shutil, sys, uuid, zipfile
from PIL import Image
import gen_witch

VER = int(sys.argv[1]) if len(sys.argv) > 1 else 1
TAG = 'V%d' % VER
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
OUT = os.path.join(BASE, TAG)
PREV = os.path.join(BASE, 'preview')
RP = os.path.join(OUT, 'StarnightWitch_RP_' + TAG)
BP = os.path.join(OUT, 'StarnightWitch_BP_' + TAG)
ID = 'bw:starnight_witch'
NS = uuid.UUID('6f0c1d2e-5b7a-4c3d-9e8f-102938475610')
uid = lambda n: str(uuid.uuid5(NS, n))


def wj(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def wt(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(PREV, exist_ok=True)
gen_witch.main(PREV)
os.makedirs(os.path.join(RP, 'textures/entity'), exist_ok=True)
os.makedirs(os.path.join(RP, 'models/entity'), exist_ok=True)
shutil.move(os.path.join(PREV, 'starnight_witch.png'), os.path.join(RP, 'textures/entity/starnight_witch.png'))
shutil.move(os.path.join(PREV, 'starnight_witch.geo.json'), os.path.join(RP, 'models/entity/starnight_witch.geo.json'))
for k in ('front', 'q34', 'q34b', 'side', 'back', 'low'):
    os.remove(os.path.join(PREV, 'view_%s.png' % k))
icon = Image.open(os.path.join(PREV, 'face_front.png')).crop((70, 0, 830, 760)).resize((256, 256), Image.LANCZOS)
for p in (RP, BP):
    icon.save(os.path.join(p, 'pack_icon.png')) if os.path.isdir(p) else (os.makedirs(p), icon.save(os.path.join(p, 'pack_icon.png')))

ver = [VER, 0, 0]
wj(os.path.join(RP, 'manifest.json'), {
    'format_version': 2,
    'header': {'name': 'Starnight Witch RP ' + TAG, 'description': 'Starnight Witch boss - model & texture (' + TAG + ')',
               'uuid': uid('rp'), 'version': ver, 'min_engine_version': [1, 20, 0]},
    'modules': [{'type': 'resources', 'uuid': uid('rp-mod'), 'version': ver}]})
wj(os.path.join(BP, 'manifest.json'), {
    'format_version': 2,
    'header': {'name': 'Starnight Witch BP ' + TAG, 'description': 'Starnight Witch boss - entity (' + TAG + ')',
               'uuid': uid('bp'), 'version': ver, 'min_engine_version': [1, 20, 0]},
    'modules': [{'type': 'data', 'uuid': uid('bp-mod'), 'version': ver}],
    'dependencies': [{'uuid': uid('rp'), 'version': ver}]})
wj(os.path.join(RP, 'entity/starnight_witch.entity.json'), {
    'format_version': '1.10.0',
    'minecraft:client_entity': {'description': {
        'identifier': ID,
        'materials': {'default': 'entity_alphatest'},
        'textures': {'default': 'textures/entity/starnight_witch'},
        'geometry': {'default': 'geometry.starnight_witch'},
        'render_controllers': ['controller.render.starnight_witch'],
        'spawn_egg': {'base_color': '#1c2566', 'overlay_color': '#ffe07a'}}}})
wj(os.path.join(RP, 'render_controllers/starnight_witch.render_controllers.json'), {
    'format_version': '1.8.0',
    'render_controllers': {'controller.render.starnight_witch': {
        'geometry': 'Geometry.default', 'materials': [{'*': 'Material.default'}], 'textures': ['Texture.default']}}})
wj(os.path.join(RP, 'texts/languages.json'), ['en_US', 'ko_KR'])
wt(os.path.join(RP, 'texts/en_US.lang'),
   'entity.%s.name=Starnight Witch\nitem.spawn_egg.entity.%s.name=Starnight Witch Spawn Egg\n' % (ID, ID))
wt(os.path.join(RP, 'texts/ko_KR.lang'),
   'entity.%s.name=별밤의 마녀\nitem.spawn_egg.entity.%s.name=별밤의 마녀 생성 알\n' % (ID, ID))
wj(os.path.join(BP, 'entities/starnight_witch.json'), {
    'format_version': '1.20.0',
    'minecraft:entity': {
        'description': {'identifier': ID, 'is_spawnable': True, 'is_summonable': True, 'is_experimental': False},
        'components': {
            'minecraft:type_family': {'family': ['starnight_witch', 'boss', 'monster', 'mob']},
            'minecraft:health': {'value': 400, 'max': 400},
            'minecraft:collision_box': {'width': 1.2, 'height': 3.1},
            'minecraft:physics': {},
            'minecraft:pushable': {'is_pushable': False, 'is_pushable_by_piston': False},
            'minecraft:knockback_resistance': {'value': 1.0},
            'minecraft:nameable': {},
            'minecraft:persistent': {},
            'minecraft:boss': {'should_darken_sky': False, 'hud_range': 55}}}})

mc = os.path.join(BASE, 'StarnightWitch_%s.mcaddon' % TAG)
with zipfile.ZipFile(mc, 'w', zipfile.ZIP_DEFLATED) as z:
    for root in (RP, BP):
        for d, _, fs in os.walk(root):
            for f in sorted(fs):
                full = os.path.join(d, f)
                z.write(full, os.path.relpath(full, OUT))
print('built', mc, os.path.getsize(mc), 'bytes')
