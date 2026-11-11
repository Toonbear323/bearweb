tag @a remove bear_in
tag @a[x=-84,y=40,z=-84,dx=168,dy=110,dz=168] add bear_in
tag @a[x=-46,y=30,z=-304,dx=108,dy=90,dz=100] add bear_in
tag @a[x=224,y=40,z=22,dx=110,dy=85,dz=92] add bear_in
tag @a[x=218,y=15,z=-310,dx=106,dy=85,dz=114] add bear_in
tag @a[x=-40,y=8,z=184,dx=80,dy=53,dz=228] add bear_in
tag @a[x=-30,y=56,z=126,dx=60,dy=64,dz=76] add bear_in
tag @a[x=-266,y=66,z=238,dx=28,dy=36,dz=28] add bear_in
execute in nether run tag @a[x=7744,y=-64,z=-256,dx=512,dy=400,dz=384] add bear_in
gamemode adventure @a[tag=bear_in,m=survival,tag=!bear_admin]
gamemode survival @a[tag=!bear_in,m=adventure,tag=!bear_admin]
