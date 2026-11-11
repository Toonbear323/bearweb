tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in overworld run tp @s -251.5 73 243.5 facing -252 75 256
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §c지옥문
title @a[tag=bear_w] subtitle §7화산 분화구
tag @a remove bear_w
