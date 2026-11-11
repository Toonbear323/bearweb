execute if entity @e[type=wither] run tellraw @a[r=16] {"rawtext": [{"text": "§c위더가 이미 소환되어 있습니다!"}]}
execute unless entity @e[type=wither] run tellraw @a[r=48] {"rawtext": [{"text": "§4§l최종 도전: 위더가 전당에 나타났습니다!"}]}
execute unless entity @e[type=wither] run summon wither 8215 44 64
