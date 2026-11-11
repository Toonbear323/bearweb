tag @p[r=7] add bear_c
tag @a[tag=bear_c,hasitem={item=gunpowder,quantity=4..}] add bear_b
clear @a[tag=bear_b] gunpowder -1 4
scoreboard players add @a[tag=bear_b] gold 12
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[길드] §f화약 4개 판매! §6(+12 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[길드] 판매할 물건이 부족합니다. §7(화약 4개)"}]}
tag @a remove bear_b
tag @a remove bear_c
