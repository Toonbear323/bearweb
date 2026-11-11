tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in nether run tp @s 8000.5 41 67.5 facing 8000 42 44
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §c지옥 허브
title @a[tag=bear_w] subtitle §7세 갈래 길
tag @a remove bear_w
