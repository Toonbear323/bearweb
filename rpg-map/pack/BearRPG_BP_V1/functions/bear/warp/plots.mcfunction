tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in overworld run tp @s -112.5 69 0.5 facing -133 70 0
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §d개인 집터
title @a[tag=bear_w] subtitle §7서바이벌 구역 · 자유 건축
tag @a remove bear_w
