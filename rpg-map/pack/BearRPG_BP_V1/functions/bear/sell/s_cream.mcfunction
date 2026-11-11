tag @p[r=7] add bear_c
tag @a[tag=bear_c,hasitem={item=magma_cream,quantity=2..}] add bear_b
clear @a[tag=bear_b] magma_cream -1 2
scoreboard players add @a[tag=bear_b] gold 14
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[길드] §f마그마 크림 2개 판매! §6(+14 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[길드] 판매할 물건이 부족합니다. §7(마그마 크림 2개)"}]}
tag @a remove bear_b
tag @a remove bear_c
