tag @s add bear_hero
tag @s remove bear_hero_new
scoreboard players add @s gold 3000
loot give @s loot "bear/sword_hero"
title @s title §6§l전설의 용사
title @s subtitle §f모든 던전을 정복했습니다!
tellraw @a {"rawtext": [{"text": "§6§l[베어 RPG] §r§e"}, {"selector": "@s"}, {"text": " §f님이 모든 던전을 정복하고 §6전설의 용사§f가 되었습니다!"}]}
playsound random.levelup @a
