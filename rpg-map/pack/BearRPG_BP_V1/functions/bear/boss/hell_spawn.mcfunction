scoreboard players set st_hell bear_state 1
summon zoglin "§c용암의 군주" 8000 41 -210
tag @e[type=zoglin,x=8000,y=41,z=-210,r=3,c=1] add boss_hell
effect @e[tag=boss_hell] health_boost 99999 19 true
effect @e[tag=boss_hell] instant_damage 1 6 true
effect @e[tag=boss_hell] strength 99999 1 true
effect @e[tag=boss_hell] resistance 99999 0 true
summon zoglin 7993 41 -208
summon zoglin 8007 41 -208
summon blaze 7995 45 -215
summon blaze 8005 45 -215
summon magma_cube 8000 42 -218
title @a[r=48] title §c용암의 군주
title @a[r=48] subtitle §7불타는 협곡의 지배자
playsound mob.wither.spawn @a[r=48]
