tag @p[r=7] add bear_c
tag @a[tag=bear_c,scores={gold=1200..}] add bear_b
execute as @a[tag=bear_b] run loot give @s loot "bear/trident_tide"
scoreboard players remove @a[tag=bear_b] gold 1200
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[상점] §f해일의 삼지창 구매 완료! §7(-1200 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[상점] 골드가 부족합니다. §7(해일의 삼지창: 1200 골드)"}]}
execute as @a[tag=bear_c,tag=!bear_b] at @s run playsound note.bass @s ~ ~ ~
tag @a remove bear_b
tag @a remove bear_c
