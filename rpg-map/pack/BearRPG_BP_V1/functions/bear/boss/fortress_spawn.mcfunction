scoreboard players set st_fortress bear_state 1
summon wither_skeleton "§4위더 군주" 8224 41 64
tag @e[type=wither_skeleton,x=8224,y=41,z=64,r=3,c=1] add boss_fortress
replaceitem entity @e[tag=boss_fortress] slot.armor.head 0 netherite_helmet
replaceitem entity @e[tag=boss_fortress] slot.armor.chest 0 netherite_chestplate
replaceitem entity @e[tag=boss_fortress] slot.armor.legs 0 netherite_leggings
replaceitem entity @e[tag=boss_fortress] slot.armor.feet 0 netherite_boots
replaceitem entity @e[tag=boss_fortress] slot.weapon.mainhand 0 netherite_sword
effect @e[tag=boss_fortress] health_boost 99999 24 true
effect @e[tag=boss_fortress] instant_damage 1 6 true
effect @e[tag=boss_fortress] strength 99999 1 true
effect @e[tag=boss_fortress] speed 99999 0 true
summon wither_skeleton 8220 41 58
summon wither_skeleton 8220 41 70
summon wither_skeleton 8214 41 60
summon wither_skeleton 8214 41 68
summon blaze 8218 46 61
summon blaze 8218 46 67
title @a[r=48] title §4위더 군주
title @a[r=48] subtitle §7네더 요새의 지배자
playsound mob.wither.spawn @a[r=48]
