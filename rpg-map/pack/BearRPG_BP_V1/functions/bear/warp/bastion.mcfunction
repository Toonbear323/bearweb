tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in nether run tp @s 7899.5 41 64.5 facing 7876 46 64
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §6피글린 요새
title @a[tag=bear_w] subtitle §7황금 보루
tag @a remove bear_w
