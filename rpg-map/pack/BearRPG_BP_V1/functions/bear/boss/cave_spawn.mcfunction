scoreboard players set st_cave bear_state 1
summon vindicator "§3심연의 광부 대장" 249 31 -252
tag @e[type=vindicator,x=249,y=31,z=-252,r=3,c=1] add boss_cave
effect @e[tag=boss_cave] health_boost 99999 14 true
effect @e[tag=boss_cave] instant_health 1 6 true
effect @e[tag=boss_cave] resistance 99999 0 true
summon cave_spider 252 31 -257
summon cave_spider 252 31 -247
summon cave_spider 257 31 -255
summon skeleton 251 32 -255
summon skeleton 251 32 -249
summon witch 245 32 -252
title @a[r=48] title §3심연의 광부 대장
title @a[r=48] subtitle §7수정 동굴의 지배자
playsound mob.wither.spawn @a[r=48]
