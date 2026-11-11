tp @s 0.5 71 4.5 facing 0.5 72 -25.5
spawnpoint @s 0 71 4
scoreboard players add @s gold 50
give @s stone_sword 1
give @s bread 16
give @s torch 16
give @s leather_chestplate 1
title @s title §6§l베어 RPG
title @s subtitle §f모험을 시작하세요!
tellraw @s {"rawtext": [{"text": "§6[베어 RPG] §f환영합니다! 시작 지원금 §650 골드§f와 기본 장비를 지급했습니다."}]}
tellraw @s {"rawtext": [{"text": "§7· 북쪽 대로: 상점가  · 서쪽 대로: 차원문 신전(던전 이동)  · 동쪽 대로: 모험가 길드(전리품 판매)"}]}
tellraw @s {"rawtext": [{"text": "§7· 서문 밖 주택단지에서는 자유롭게 집을 지을 수 있습니다."}]}
playsound random.levelup @s
tag @s add bear_joined
