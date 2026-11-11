tag @p[r=5] add bear_w
execute as @a[tag=bear_w] in overworld run tp @s 228.5 85 -200.5 facing 228 86 -216
effect @a[tag=bear_w] resistance 4 4 true
execute as @a[tag=bear_w] at @s run playsound mob.endermen.portal @s ~ ~ ~
title @a[tag=bear_w] title §8동굴 던전
title @a[tag=bear_w] subtitle §7수정 동굴
tag @a remove bear_w
