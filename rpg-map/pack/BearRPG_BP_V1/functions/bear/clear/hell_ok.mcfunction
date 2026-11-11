scoreboard players set st_hell bear_state 0
tag @a[r=30,tag=!clr_hell] add bear_first
scoreboard players add @a[r=30,tag=bear_first] gold 900
scoreboard players add @a[r=30,tag=!bear_first] gold 225
execute as @a[tag=bear_first] run loot give @s loot "bear/sword_flame"
tellraw @a[r=30,tag=bear_first] {"rawtext": [{"text": "§6[보상] §f지옥 던전 최초 클리어! §6+900 골드 §f와 특별 장비를 받았습니다."}]}
tellraw @a[r=30,tag=!bear_first] {"rawtext": [{"text": "§6[보상] §f지옥 던전 클리어! §6+225 골드"}]}
tellraw @a {"rawtext": [{"text": "§6[베어 RPG] §e"}, {"selector": "@a[r=30]"}, {"text": " §f님이 §c지옥 던전§f을(를) 클리어했습니다!"}]}
tag @a[tag=bear_first] add clr_hell
tag @a remove bear_first
playsound random.levelup @a[r=30]
summon fireworks_rocket ~ ~3 ~
