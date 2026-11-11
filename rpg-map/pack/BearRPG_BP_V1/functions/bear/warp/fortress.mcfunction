tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in nether run tp @s 8100.5 41 64.5 facing 8140 44 64
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §4네더 요새
title @a[tag=bear_w] subtitle §7위더의 성채
tag @a remove bear_w
