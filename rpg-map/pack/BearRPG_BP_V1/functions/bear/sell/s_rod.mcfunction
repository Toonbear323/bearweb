tag @p[r=7] add bear_c
tag @a[tag=bear_c,hasitem={item=blaze_rod,quantity=2..}] add bear_b
clear @a[tag=bear_b] blaze_rod -1 2
scoreboard players add @a[tag=bear_b] gold 20
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[길드] §f블레이즈 막대 2개 판매! §6(+20 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[길드] 판매할 물건이 부족합니다. §7(블레이즈 막대 2개)"}]}
tag @a remove bear_b
tag @a remove bear_c
