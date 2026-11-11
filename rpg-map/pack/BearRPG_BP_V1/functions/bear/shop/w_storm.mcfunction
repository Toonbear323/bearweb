tag @p[r=7] add bear_c
tag @a[tag=bear_c,scores={gold=1400..}] add bear_b
execute as @a[tag=bear_b] run loot give @s loot "bear/bow_storm"
scoreboard players remove @a[tag=bear_b] gold 1400
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[상점] §f폭풍의 활 구매 완료! §7(-1400 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[상점] 골드가 부족합니다. §7(폭풍의 활: 1400 골드)"}]}
execute as @a[tag=bear_c,tag=!bear_b] at @s run playsound note.bass @s ~ ~ ~
tag @a remove bear_b
tag @a remove bear_c
