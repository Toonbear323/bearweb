scoreboard players set st_plains bear_state 0
scoreboard players set st_cave bear_state 0
scoreboard players set st_desert bear_state 0
scoreboard players set st_ocean bear_state 0
scoreboard players set st_hell bear_state 0
scoreboard players set st_fortress bear_state 0
scoreboard players set st_bastion bear_state 0
kill @e[tag=boss_plains]
kill @e[tag=boss_cave]
kill @e[tag=boss_desert]
kill @e[tag=boss_ocean]
kill @e[tag=boss_hell]
kill @e[tag=boss_fortress]
kill @e[tag=boss_bastion]
tellraw @s {"rawtext": [{"text": "§e[관리] 모든 보스 상태를 초기화했습니다."}]}
