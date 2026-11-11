scoreboard players set st_bastion bear_state 1
summon piglin_brute "§6피글린 족장" 7818 41 64
tag @e[type=piglin_brute,x=7818,y=41,z=64,r=3,c=1] add boss_bastion
replaceitem entity @e[tag=boss_bastion] slot.armor.head 0 golden_helmet
replaceitem entity @e[tag=boss_bastion] slot.armor.chest 0 netherite_chestplate
effect @e[tag=boss_bastion] health_boost 99999 29 true
effect @e[tag=boss_bastion] instant_health 1 7 true
effect @e[tag=boss_bastion] strength 99999 1 true
effect @e[tag=boss_bastion] resistance 99999 1 true
effect @e[tag=boss_bastion] fire_resistance 99999 0 true
summon piglin_brute 7816 41 56
summon piglin_brute 7816 41 72
summon piglin_brute 7794 41 64
summon piglin 7818 41 52
summon piglin 7818 41 76
title @a[r=48] title §6피글린 족장
title @a[r=48] subtitle §7황금 보루의 지배자
playsound mob.wither.spawn @a[r=48]
