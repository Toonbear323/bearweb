scoreboard players set st_ocean bear_state 1
summon elder_guardian "§3심해의 수호자" 0 32 372
tag @e[type=elder_guardian,x=0,y=32,z=372,r=4,c=1] add boss_ocean
effect @e[tag=boss_ocean] resistance 99999 0 true
summon guardian -6 29 364
summon guardian 6 29 364
summon guardian 0 35 360
summon drowned -4 25 368
summon drowned 4 25 368
title @a[r=48] title §3심해의 수호자
title @a[r=48] subtitle §7가라앉은 신전의 주인
playsound mob.wither.spawn @a[r=48]
