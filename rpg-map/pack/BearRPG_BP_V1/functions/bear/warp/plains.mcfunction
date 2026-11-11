tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in overworld run tp @s 0.5 72 -213.5 facing 0 73 -252
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §a초원 던전
title @a[tag=bear_w] subtitle §7폐허의 성채
tag @a remove bear_w
