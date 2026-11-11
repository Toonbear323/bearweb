tag @p[r=7] add bear_c
tag @a[tag=bear_c,scores={gold=2800..}] add bear_b
execute as @a[tag=bear_b] run loot give @s loot "bear/helm_guard"
execute as @a[tag=bear_b] run loot give @s loot "bear/chest_guard"
execute as @a[tag=bear_b] run loot give @s loot "bear/legs_guard"
execute as @a[tag=bear_b] run loot give @s loot "bear/boots_guard"
scoreboard players remove @a[tag=bear_b] gold 2800
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[상점] §f수호자 세트 구매 완료! §7(-2800 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[상점] 골드가 부족합니다. §7(수호자 세트: 2800 골드)"}]}
execute as @a[tag=bear_c,tag=!bear_b] at @s run playsound note.bass @s ~ ~ ~
tag @a remove bear_b
tag @a remove bear_c
