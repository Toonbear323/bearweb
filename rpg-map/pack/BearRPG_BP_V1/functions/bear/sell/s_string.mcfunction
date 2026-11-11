tag @p[r=7] add bear_c
tag @a[tag=bear_c,hasitem={item=string,quantity=8..}] add bear_b
clear @a[tag=bear_b] string -1 8
scoreboard players add @a[tag=bear_b] gold 8
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[길드] §f실 8개 판매! §6(+8 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[길드] 판매할 물건이 부족합니다. §7(실 8개)"}]}
tag @a remove bear_b
tag @a remove bear_c
