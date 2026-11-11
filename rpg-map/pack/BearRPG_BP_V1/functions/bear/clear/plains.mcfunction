execute if entity @e[tag=boss_plains] run tellraw @a[r=12] {"rawtext": [{"text": "§c보스가 아직 살아 있습니다!"}]}
execute unless entity @e[tag=boss_plains] if score st_plains bear_state matches 0 run tellraw @a[r=12] {"rawtext": [{"text": "§7보스를 처치한 뒤에 보상을 받을 수 있습니다."}]}
execute unless entity @e[tag=boss_plains] if score st_plains bear_state matches 1 run function bear/clear/plains_ok
