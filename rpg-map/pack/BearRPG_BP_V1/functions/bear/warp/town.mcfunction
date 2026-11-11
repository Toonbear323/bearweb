tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in overworld run tp @s 0.5 71 4.5 facing 0.5 72 -25.5
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §6베어 타운
title @a[tag=bear_w] subtitle §7스폰 광장
tag @a remove bear_w
