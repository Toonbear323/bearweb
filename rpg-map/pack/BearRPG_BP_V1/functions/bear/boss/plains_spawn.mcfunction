scoreboard players set st_plains bear_state 1
summon zombie "§c폐허의 왕" 28 60 -230
tag @e[type=zombie,x=28,y=60,z=-230,r=3,c=1] add boss_plains
replaceitem entity @e[tag=boss_plains] slot.armor.head 0 golden_helmet
replaceitem entity @e[tag=boss_plains] slot.armor.chest 0 iron_chestplate
replaceitem entity @e[tag=boss_plains] slot.armor.legs 0 iron_leggings
replaceitem entity @e[tag=boss_plains] slot.armor.feet 0 iron_boots
replaceitem entity @e[tag=boss_plains] slot.weapon.mainhand 0 iron_sword
effect @e[tag=boss_plains] health_boost 99999 9 true
effect @e[tag=boss_plains] instant_damage 1 4 true
effect @e[tag=boss_plains] strength 99999 0 true
effect @e[tag=boss_plains] speed 99999 0 true
summon skeleton 22 59 -230
summon skeleton 34 59 -230
summon zombie 25 59 -234
summon zombie 31 59 -234
title @a[r=48] title §c폐허의 왕
title @a[r=48] subtitle §7초원 던전의 주인
playsound mob.wither.spawn @a[r=48]
