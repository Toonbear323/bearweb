tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in overworld run tp @s 242.5 68 72.5 facing 292 73 72
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §e사막 던전
title @a[tag=bear_w] subtitle §7태양왕의 피라미드
tag @a remove bear_w
