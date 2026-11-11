tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in nether run tp @s 8000.5 41 30.5 facing 8000 42 0
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §c지옥 던전
title @a[tag=bear_w] subtitle §7불타는 협곡
tag @a remove bear_w
