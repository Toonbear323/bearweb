tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in overworld run tp @s 0.5 65 185.5 facing 0 65 198
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §3바다 던전
title @a[tag=bear_w] subtitle §7가라앉은 신전
tag @a remove bear_w
