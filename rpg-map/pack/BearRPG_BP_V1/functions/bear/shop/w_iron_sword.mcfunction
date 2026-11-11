tag @p[r=7] add bear_c
tag @a[tag=bear_c,scores={gold=60..}] add bear_b
execute as @a[tag=bear_b] run give @s iron_sword 1 0
scoreboard players remove @a[tag=bear_b] gold 60
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[상점] §f철 검 구매 완료! §7(-60 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[상점] 골드가 부족합니다. §7(철 검: 60 골드)"}]}
execute as @a[tag=bear_c,tag=!bear_b] at @s run playsound note.bass @s ~ ~ ~
tag @a remove bear_b
tag @a remove bear_c
