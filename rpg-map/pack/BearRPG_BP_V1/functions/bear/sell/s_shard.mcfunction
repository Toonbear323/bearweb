tag @p[r=7] add bear_c
tag @a[tag=bear_c,hasitem={item=prismarine_shard,quantity=8..}] add bear_b
clear @a[tag=bear_b] prismarine_shard -1 8
scoreboard players add @a[tag=bear_b] gold 16
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[길드] §f프리즈머린 조각 8개 판매! §6(+16 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[길드] 판매할 물건이 부족합니다. §7(프리즈머린 조각 8개)"}]}
tag @a remove bear_b
tag @a remove bear_c
