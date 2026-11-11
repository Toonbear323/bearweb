tag @p[r=7] add bear_c
tag @a[tag=bear_c,scores={gold=700..}] add bear_b
execute as @a[tag=bear_b] run give @s enchanted_golden_apple 1 0
scoreboard players remove @a[tag=bear_b] gold 700
execute as @a[tag=bear_b] at @s run playsound random.orb @s ~ ~ ~
tellraw @a[tag=bear_b] {"rawtext": [{"text": "§a[상점] §f마법이 부여된 구매 완료! §7(-700 골드)"}]}
tellraw @a[tag=bear_c,tag=!bear_b] {"rawtext": [{"text": "§c[상점] 골드가 부족합니다. §7(마법이 부여된: 700 골드)"}]}
execute as @a[tag=bear_c,tag=!bear_b] at @s run playsound note.bass @s ~ ~ ~
tag @a remove bear_b
tag @a remove bear_c
