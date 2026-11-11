scoreboard players set st_bastion bear_state 0
tag @a[r=30,tag=!clr_bastion] add bear_first
scoreboard players add @a[r=30,tag=bear_first] gold 1600
scoreboard players add @a[r=30,tag=!bear_first] gold 400
execute as @a[tag=bear_first] run loot give @s loot "bear/axe_war"
tellraw @a[r=30,tag=bear_first] {"rawtext": [{"text": "§6[보상] §f피글린 요새 최초 클리어! §6+1600 골드 §f와 특별 장비를 받았습니다."}]}
tellraw @a[r=30,tag=!bear_first] {"rawtext": [{"text": "§6[보상] §f피글린 요새 클리어! §6+400 골드"}]}
tellraw @a {"rawtext": [{"text": "§6[베어 RPG] §e"}, {"selector": "@a[r=30]"}, {"text": " §f님이 §6피글린 요새§f을(를) 클리어했습니다!"}]}
tag @a[tag=bear_first] add clr_bastion
tag @a remove bear_first
playsound random.levelup @a[r=30]
summon fireworks_rocket ~ ~3 ~
