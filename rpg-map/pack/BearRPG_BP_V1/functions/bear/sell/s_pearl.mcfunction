tag @p[r=7] add bear_c
tag @a[tag=bear_c,hasitem={item=ender_pearl,quantity=1..}] add bear_b
clear @a[tag=bear_b] ender_pearl -1 1
scoreboard players add @a[tag=bear_b] gold 12
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[길드] §f엔더 진주 1개 판매! §6(+12 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[길드] 판매할 물건이 부족합니다. §7(엔더 진주 1개)"}]}
tag @a remove bear_b
tag @a remove bear_c
