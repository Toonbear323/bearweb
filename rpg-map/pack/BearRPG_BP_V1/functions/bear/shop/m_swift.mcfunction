tag @p[r=7] add bear_c
tag @a[tag=bear_c,scores={gold=40..}] add bear_b
execute as @a[tag=bear_b] run give @s potion 1 15
scoreboard players remove @a[tag=bear_b] gold 40
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[상점] §f신속의 물약 구매 완료! §7(-40 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[상점] 골드가 부족합니다. §7(신속의 물약: 40 골드)"}]}
execute as @a[tag=bear_c,tag=!bear_b] at @s run playsound note.bass @s ~ ~ ~
tag @a remove bear_b
tag @a remove bear_c
