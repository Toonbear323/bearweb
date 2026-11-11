scoreboard objectives add gold dummy "§6§l골드"
scoreboard objectives add bear_state dummy
scoreboard objectives setdisplay sidebar gold
scoreboard players add @a gold 0
scoreboard players add st_zones_off bear_state 0
scoreboard players add st_plains bear_state 0
scoreboard players add st_cave bear_state 0
scoreboard players add st_desert bear_state 0
scoreboard players add st_ocean bear_state 0
scoreboard players add st_hell bear_state 0
scoreboard players add st_fortress bear_state 0
scoreboard players add st_bastion bear_state 0
execute as @a[tag=!bear_joined] run function bear/init_player
execute unless score st_zones_off bear_state matches 1 run function bear/zones
tag @a[tag=clr_plains,tag=clr_cave,tag=clr_desert,tag=clr_ocean,tag=clr_hell,tag=clr_fortress,tag=clr_bastion,tag=!bear_hero] add bear_hero_new
execute as @a[tag=bear_hero_new] run function bear/hero
