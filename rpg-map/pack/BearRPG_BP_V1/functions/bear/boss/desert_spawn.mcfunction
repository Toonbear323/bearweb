scoreboard players set st_desert bear_state 1
summon husk "§6태양왕 파라오" 294 78 72
tag @e[type=husk,x=294,y=78,z=72,r=3,c=1] add boss_desert
replaceitem entity @e[tag=boss_desert] slot.armor.head 0 golden_helmet
replaceitem entity @e[tag=boss_desert] slot.armor.chest 0 golden_chestplate
replaceitem entity @e[tag=boss_desert] slot.armor.legs 0 golden_leggings
replaceitem entity @e[tag=boss_desert] slot.armor.feet 0 golden_boots
replaceitem entity @e[tag=boss_desert] slot.weapon.mainhand 0 golden_sword
effect @e[tag=boss_desert] health_boost 99999 14 true
effect @e[tag=boss_desert] instant_damage 1 5 true
effect @e[tag=boss_desert] strength 99999 1 true
effect @e[tag=boss_desert] resistance 99999 0 true
summon husk 292 78 67
summon husk 292 78 77
summon husk 295 78 66
summon husk 295 78 78
summon skeleton 297 79 69
summon skeleton 297 79 75
title @a[r=48] title §6태양왕 파라오
title @a[r=48] subtitle §7피라미드의 주인
playsound mob.wither.spawn @a[r=48]
