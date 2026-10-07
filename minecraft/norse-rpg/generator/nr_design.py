"""Design data for 'Norse RPG: 아홉 세계의 항해' — spawn harbour, 10 dungeons, 22 bosses.

Every dungeon has the same 8-zone spine:
    start -> c1 -> c2 -> c3 (+mid-boss 1 from the mid tier up) -> c4 -> c5 (+mid-boss 2 from the mid tier up) -> c6 -> boss

Skills (all are announced on the ground before they hit; see js/skills.js):
    beam    line from the caster along its gaze to the impact point (track = ticks the aim follows the target,
            then the path locks for `lock` ticks before it fires)
    radial  `count` beams around the caster (cross / star), optional `spin` between two casts
    slam    circle around the caster            ring    donut around the caster (safe inside `inner`)
    cone    sector in front (track like beam)    strike  circle under every target
    rain    `count` circles scattered over the arena, falling one after another
    charge  line to the target, the caster dashes along it (`times` repeats with a new aim)
    leap    circle at the target, the caster lands there
    pull    big circle that drags players in, then a small circle explodes
    wave    `count` rings expanding outwards one after another
    sweep   `count` parallel lanes across the arena
    summon  small circles where minions climb out
    clone   illusions appear and each fires a tracked beam
Times are ticks (20 = 1 s), lengths are blocks.
"""

TIERS = {
    "beginner": dict(ko="초급", lv="Lv.1-4", size=(176, 288), sail="white_wool", stripe="red_wool"),
    "mid": dict(ko="중급", lv="Lv.5-7", size=(272, 448), sail="white_wool", stripe="blue_wool"),
    "high": dict(ko="상급", lv="Lv.8-10", size=(272, 448), sail="black_wool", stripe="yellow_wool"),
}

# vanilla mobs used in combat zones: name -> (entity, display name, armour/held, effects)
MOBS = {
    # D1 barrow coast
    "draugr": ("minecraft:zombie", "§7드라우그 전사", dict(head="chainmail_helmet", hand="stone_sword"), {}),
    "barrow_archer": ("minecraft:skeleton", "§7고분 궁수", dict(head="leather_helmet"), {}),
    "drowned_sailor": ("minecraft:drowned", "§3익사한 선원", dict(head="leather_helmet", hand="trident"), {}),
    "grave_spider": ("minecraft:spider", "§8무덤 거미", {}, {}),
    "draugr_elite": ("minecraft:zombie", "§6드라우그 친위병", dict(head="iron_helmet", chest="chainmail_chestplate", hand="iron_sword"), dict(resistance=0)),
    # D2 iron wood
    "iron_wolf": ("nrpg:iron_wolf", "§8철숲 늑대", {}, {}),
    "wood_ghoul": ("minecraft:zombie", "§2숲의 구울", dict(head="leather_helmet", hand="wooden_axe"), {}),
    "vine_spider": ("minecraft:cave_spider", "§2덩굴 거미", {}, {}),
    "hag_cultist": ("minecraft:witch", "§5앙그르보다의 신도", {}, {}),
    "wood_archer": ("minecraft:skeleton", "§2숲 사냥꾼의 망령", dict(head="leather_helmet"), {}),
    # D3 Andvari's cave
    "cave_spider": ("minecraft:cave_spider", "§8동굴 거미", {}, {}),
    "gold_miner": ("minecraft:husk", "§6황금에 미친 광부", dict(head="golden_helmet", hand="golden_pickaxe"), {}),
    "crystal_slime": ("minecraft:slime", "§d수정 슬라임", {}, {}),
    "cursed_bones": ("minecraft:skeleton", "§e저주받은 해골", dict(head="golden_helmet"), {}),
    "vault_rat": ("minecraft:silverfish", "§7금고 쥐", {}, {}),
    # D4 Hrungnir's mountain
    "troll_whelp": ("minecraft:zombie", "§a트롤 졸개", dict(head="leather_helmet", chest="leather_chestplate", hand="stone_axe"), dict(resistance=0)),
    "rock_thrower": ("minecraft:skeleton", "§7돌 투척꾼", dict(head="chainmail_helmet"), {}),
    "hunter_ghost": ("minecraft:vindicator", "§8트롤 사냥꾼의 망령", {}, {}),
    "mushroom_crawler": ("minecraft:cave_spider", "§c버섯 기생충", {}, {}),
    # D5 Naglfar shipyard
    "bone_sailor": ("minecraft:skeleton", "§7해골 선원", dict(head="iron_helmet", chest="chainmail_chestplate"), dict(resistance=0)),
    "deckhand": ("minecraft:zombie", "§8망자 갑판원", dict(head="iron_helmet", chest="iron_chestplate", hand="iron_axe"), dict(resistance=0)),
    "nail_cutter": ("minecraft:wither_skeleton", "§5손톱 깎는 자", dict(hand="stone_sword"), {}),
    "oarsman": ("minecraft:pillager", "§8나글파르 노잡이", {}, {}),
    "dock_brute": ("minecraft:vindicator", "§4부두 폭군", {}, dict(resistance=0)),
    # D6 Utgard
    "giant_servant": ("minecraft:vindicator", "§7우트가르드 하인", {}, dict(resistance=0)),
    "giant_hunter": ("minecraft:pillager", "§7거인의 사냥꾼", {}, {}),
    "illusionist": ("minecraft:evoker", "§5환영술사", {}, {}),
    "frost_wraith": ("minecraft:stray", "§b서리 망령", dict(head="chainmail_helmet"), {}),
    "giant_hound": ("minecraft:ravager", "§8거인의 사냥개", {}, {}),
    # D7 Nidavellir
    "dwarf_guard": ("minecraft:vindicator", "§6드베르그 경비병", dict(), dict(resistance=1)),
    "forge_spirit": ("minecraft:blaze", "§6용광로 정령", {}, {}),
    "slag_cube": ("minecraft:magma_cube", "§c슬래그 덩어리", {}, {}),
    "forge_rat": ("minecraft:silverfish", "§7대장간 쥐", {}, {}),
    "gold_skeleton": ("minecraft:skeleton", "§e금빛 파수꾼", dict(head="golden_helmet", chest="golden_chestplate"), dict(resistance=1)),
    # D8 Muspelheim
    "flame_spirit": ("minecraft:blaze", "§6무스펠 불꽃", {}, dict(strength=0)),
    "lava_cube": ("minecraft:magma_cube", "§c용암 덩어리", {}, {}),
    "ash_warrior": ("minecraft:wither_skeleton", "§8재의 전사", dict(hand="stone_sword", head="iron_helmet"), dict(resistance=1, strength=0)),
    "fire_boar": ("minecraft:zoglin", "§c무스펠 멧돼지", {}, {}),
    # D9 Helheim
    "hel_dead": ("minecraft:stray", "§b헬의 망자", dict(head="chainmail_helmet"), dict(resistance=1)),
    "hel_knight": ("minecraft:wither_skeleton", "§5헬의 기사", dict(hand="iron_sword", head="iron_helmet"), dict(resistance=1, strength=0)),
    "lost_soul": ("minecraft:vex", "§3길 잃은 영혼", {}, {}),
    "bog_dead": ("minecraft:bogged", "§2늪의 망자", dict(head="leather_helmet"), dict(resistance=0)),
    "corpse": ("minecraft:zombie", "§8나스트론드의 시체", dict(head="iron_helmet", chest="iron_chestplate", hand="iron_sword"), dict(resistance=1)),
    # D10 Asgard / Ragnarok
    "jotun_warrior": ("minecraft:vindicator", "§9요툰 전사", dict(), dict(resistance=1, strength=1)),
    "jotun_mage": ("minecraft:evoker", "§5요툰 주술사", {}, dict(resistance=0)),
    "storm_spirit": ("minecraft:breeze", "§b비프로스트 폭풍", {}, {}),
    "fenrir_pup": ("nrpg:fenrir_pup", "§8펜리르의 새끼", {}, dict(resistance=0)),
    "muspel_raider": ("minecraft:blaze", "§6무스펠 약탈자", {}, dict(strength=1)),
    "einherjar_fallen": ("minecraft:wither_skeleton", "§7타락한 에인헤랴르", dict(hand="diamond_sword", head="golden_helmet"), dict(resistance=1, strength=1)),
}


def Z(key, ko, desc, mobs=(), cap=0, mid=None):
    return dict(key=key, ko=ko, desc=desc, mobs=list(mobs), cap=cap, mid=mid)


DUNGEONS = [
    # ------------------------------------------------------------------ beginner (small)
    dict(id="d01", no=1, tier="beginner", key="barrow", ko="안개 해안의 고분", en="Barrow Coast",
         realm="미드가르드", biome=("stone_beach", "swampland"), color="§7",
         blurb="안개 낀 회색 해안. 바이킹 망자 드라우그가 잠든 무덤 언덕과 배 무덤이 있습니다.",
         zones=[
             Z("start", "상륙 해변", "회색 자갈 해변, 선착장, 야영지, 귀환선"),
             Z("c1", "부서진 롱쉽 해안", "난파된 롱쉽, 유목, 조수 웅덩이", ["drowned_sailor", "draugr"], 5),
             Z("c2", "룬스톤 언덕", "선돌 원, 늙은 참나무, 돌무덤", ["draugr", "barrow_archer"], 6),
             Z("c3", "고분 들판", "풀 덮인 무덤 언덕과 배 모양 돌 무덤", ["draugr", "barrow_archer", "grave_spider"], 7),
             Z("c4", "무덤 입구 협곡", "좁아지는 바위 협곡, 죽은 나무, 사슬, 고분 대문", ["draugr", "grave_spider"], 6),
             Z("c5", "지하 묘실 회랑", "뼈가 놓인 묘실 벽감, 거미줄, 영혼 랜턴", ["barrow_archer", "grave_spider", "draugr"], 7),
             Z("c6", "순장품 보관실", "배 무덤 방, 보물 상자, 촛불", ["draugr_elite", "barrow_archer"], 6),
             Z("boss", "고분왕의 왕좌실", "돔 지붕 원형 묘실, 왕좌, 룬 기둥"),
         ],
         boss="arnarr", mids=[]),
    dict(id="d02", no=2, tier="beginner", key="ironwood", ko="철의 숲 야른비드", en="Jarnvidr, the Iron Wood",
         realm="미드가르드 동쪽 끝", biome=("roofed_forest",), color="§8",
         blurb="늑대 거인들이 사는 검은 숲. 쇠처럼 단단한 고목 사이로 늑대 울음이 들립니다.",
         zones=[
             Z("start", "숲 가장자리 야영지", "울타리 친 야영지, 강 하구 선착장"),
             Z("c1", "녹슨 나무길", "검은 고목 사이 오솔길, 버섯, 쓰러진 나무", ["wood_ghoul", "iron_wolf"], 6),
             Z("c2", "늑대 굴", "바위 비탈의 굴, 뼈 무더기", ["iron_wolf", "wood_archer"], 6),
             Z("c3", "뼈의 공터", "거대한 짐승 뼈, 의식의 돌, 붉은 깃발", ["iron_wolf", "wood_ghoul", "hag_cultist"], 7),
             Z("c4", "덩굴 협곡 다리", "덩굴이 늘어진 협곡과 밧줄 다리", ["vine_spider", "wood_archer"], 6),
             Z("c5", "앙그르보다의 오두막", "늪 위 기둥 오두막, 가마솥, 독버섯", ["hag_cultist", "vine_spider", "wood_ghoul"], 7),
             Z("c6", "달빛 고목", "뿌리가 얽힌 거대한 고목, 빛나는 버섯", ["iron_wolf", "wood_ghoul", "wood_archer"], 7),
             Z("boss", "달을 삼키는 바위 언덕", "선돌로 둘러싼 바위 정상, 하늘에 뜬 창백한 달"),
         ],
         boss="hati", mids=[]),
    dict(id="d03", no=3, tier="beginner", key="andvari", ko="안드바리의 황금 동굴", en="Andvari's Falls",
         realm="스바르트알프헤임 입구", biome=("lush_caves", "dripstone_caves"), color="§6",
         blurb="폭포 뒤 동굴 깊은 곳, 난쟁이 안드바리가 저주받은 황금과 반지를 숨겨 둔 곳입니다.",
         zones=[
             Z("start", "폭포 앞 물가", "폭포가 떨어지는 협곡 호수, 선착장"),
             Z("c1", "물보라 동굴", "물길이 흐르는 동굴, 이끼, 종유석", ["cave_spider", "crystal_slime"], 6),
             Z("c2", "이끼 광맥", "진달래와 발광 열매가 자라는 무성한 동굴", ["cave_spider", "gold_miner"], 6),
             Z("c3", "수정 갱도", "자수정 정동, 광차 레일, 갱목", ["gold_miner", "crystal_slime", "cursed_bones"], 7),
             Z("c4", "지하 호수 다리", "지하 호수 위 돌다리와 섬", ["cursed_bones", "cave_spider"], 6),
             Z("c5", "저주받은 금화 창고", "금화 더미가 쌓인 난쟁이 금고", ["gold_miner", "vault_rat", "cursed_bones"], 7),
             Z("c6", "안드바리의 대장간", "용암 웅덩이, 모루, 용광로", ["gold_miner", "cursed_bones"], 7),
             Z("boss", "황금 저장고", "황금 언덕에 둘러싸인 둥근 대동굴"),
         ],
         boss="andvari", mids=[]),
    dict(id="d04", no=4, tier="beginner", key="hrungnir", ko="흐룽그니르의 돌산", en="Hrungnir's Mountain",
         realm="요툰헤임 국경", biome=("stony_peaks", "extreme_hills"), color="§7",
         blurb="돌 심장을 가진 거인 흐룽그니르의 산. 햇빛에 굳어 버린 트롤 석상이 길을 따라 서 있습니다.",
         zones=[
             Z("start", "산기슭 강변 선착장", "거인 발자국 웅덩이, 강변 부두"),
             Z("c1", "돌다리 길", "자연 돌다리와 바위 사이 자갈길", ["troll_whelp", "rock_thrower"], 6),
             Z("c2", "석화된 트롤 계곡", "이끼 낀 거대한 트롤 석상들", ["troll_whelp", "rock_thrower"], 7),
             Z("c3", "밧줄 다리 절벽", "절벽 길과 깊은 골짜기 위 밧줄 다리", ["rock_thrower", "mushroom_crawler"], 6),
             Z("c4", "트롤 사냥꾼의 폐허", "무너진 목책, 부서진 수레, 망루", ["hunter_ghost", "troll_whelp"], 6),
             Z("c5", "버섯 동굴", "거대한 버섯과 균사체 동굴", ["mushroom_crawler", "troll_whelp"], 7),
             Z("c6", "뼈 무더기 소굴", "트롤 소굴, 뼈, 가마솥, 약탈품", ["troll_whelp", "hunter_ghost", "rock_thrower"], 7),
             Z("boss", "그리오투나가르드 결투장", "토르가 흐룽그니르와 싸운 산정 돌 결투장"),
         ],
         boss="hrungnir", mids=[]),
    # ------------------------------------------------------------------ mid (castle-type, large)
    dict(id="d05", no=5, tier="mid", key="naglfar", ko="나글파르 조선 요새", en="Naglfar Shipyard",
         realm="세계의 끝 해안", biome=("deep_ocean", "basalt_deltas"), color="§5",
         blurb="망자의 손톱으로 배를 짓는 검은 요새. 라그나로크에 출항할 나글파르가 건조 독에 누워 있습니다.",
         zones=[
             Z("start", "검은 해안 상륙장", "검은 모래 해안, 외곽 방파제와 성문"),
             Z("c1", "외곽 부두 창고", "창고, 기중기, 화물, 사슬", ["bone_sailor", "deckhand", "oarsman"], 8),
             Z("c2", "성벽 순찰로", "거대한 성벽 위 길과 탑, 투석기", ["oarsman", "bone_sailor"], 8),
             Z("c3", "손톱 제련소", "영혼불 용광로, 손톱 더미, 사슬 컨베이어", ["nail_cutter", "deckhand"], 8, mid="naglfari"),
             Z("c4", "사슬 승강장", "어두운 독 위의 사슬 승강기와 비계", ["bone_sailor", "oarsman", "dock_brute"], 8),
             Z("c5", "거대 건조 독", "건조 중인 나글파르 선체와 비계", ["nail_cutter", "dock_brute"], 8, mid="hraesvelgr"),
             Z("c6", "나글파르 갑판", "돛대, 방패, 회색 돛, 밧줄", ["deckhand", "nail_cutter", "oarsman"], 9),
             Z("boss", "함교 결전", "거대한 키가 달린 나글파르 선미 갑판"),
         ],
         boss="hrym", mids=["naglfari", "hraesvelgr"]),
    dict(id="d06", no=6, tier="mid", key="utgard", ko="우트가르드 거인 성채", en="Utgard Citadel",
         realm="요툰헤임", biome=("extreme_hills", "taiga"), color="§9",
         blurb="토르마저 속아 넘어간 환영의 거인왕 우트가르다 로키의 성. 모든 것이 거인의 크기입니다.",
         zones=[
             Z("start", "성채 앞 황무지", "회색 황무지와 피오르 선착장"),
             Z("c1", "스크리미르의 장갑", "토르가 방으로 착각한 거인의 장갑 동굴", ["giant_servant", "frost_wraith"], 8),
             Z("c2", "외성 마당", "거인 크기의 통과 수레바퀴, 40칸 높이 성문", ["giant_servant", "giant_hunter"], 8),
             Z("c3", "먹기 시합장", "고기가 가득한 거대한 구유와 화덕", ["giant_servant", "giant_hunter"], 8, mid="logi"),
             Z("c4", "경주 회랑", "기둥이 늘어선 긴 경주로", ["frost_wraith", "giant_hunter", "illusionist"], 8),
             Z("c5", "뿔잔 연회장", "바다로 이어진 뿔잔과 회색 거인 고양이 석상", ["giant_servant", "illusionist"], 8, mid="elli"),
             Z("c6", "환영의 회랑", "유리와 색유리 거울 회랑", ["illusionist", "frost_wraith", "giant_hound"], 9),
             Z("boss", "거인왕의 옥좌", "기둥이 둘러싼 거대한 옥좌실"),
         ],
         boss="utgardaloki", mids=["logi", "elli"]),
    dict(id="d07", no=7, tier="mid", key="nidavellir", ko="니다벨리르 대장간 성채", en="Nidavellir Forge Citadel",
         realm="니다벨리르", biome=("dripstone_caves", "basalt_deltas"), color="§6",
         blurb="신들의 보물을 만든 난쟁이들의 산속 성채. 가장 깊은 곳에 안드바리의 반지에 홀린 파프니르가 있습니다.",
         zones=[
             Z("start", "산문 선착장", "산속 호수와 난쟁이 얼굴 대문"),
             Z("c1", "광석 운반로", "광차 레일, 광석 더미, 톱니 벽", ["dwarf_guard", "forge_rat"], 8),
             Z("c2", "용광로 구역", "거대한 용광로와 용암 수로, 굴뚝", ["forge_spirit", "slag_cube", "dwarf_guard"], 8),
             Z("c3", "풀무 탑", "높은 풀무 탑 작업장", ["dwarf_guard", "forge_spirit"], 8, mid="brokkr"),
             Z("c4", "보물 진열 회랑", "묠니르, 궁니르, 드라우프니르가 놓인 회랑", ["gold_skeleton", "dwarf_guard"], 8),
             Z("c5", "담금질 수로", "물과 용암이 만나는 수로, 증기", ["slag_cube", "forge_spirit", "gold_skeleton"], 8, mid="eitri"),
             Z("c6", "룬 각인실", "빛나는 룬 벽의 각인실", ["gold_skeleton", "dwarf_guard", "forge_spirit"], 9),
             Z("boss", "파프니르의 보물 동굴", "용이 지키는 황금 대동굴"),
         ],
         boss="fafnir", mids=["brokkr", "eitri"]),
    # ------------------------------------------------------------------ high (mythic realms, large)
    dict(id="d08", no=8, tier="high", key="muspelheim", ko="무스펠헤임 불꽃의 문", en="Muspelheim",
         realm="무스펠헤임", biome=("basalt_deltas", "crimson_forest"), color="§c",
         blurb="세상이 끝날 때 세계를 태울 불의 나라. 불의 거인 수르트가 불타는 검을 벼리고 있습니다.",
         zones=[
             Z("start", "재의 해안", "현무암과 흑암 해안, 용암 바다"),
             Z("c1", "용암 강 다리", "용암 강 위 사슬 다리", ["flame_spirit", "lava_cube"], 9),
             Z("c2", "현무암 숲", "현무암 기둥 숲과 진홍 균류 나무", ["fire_boar", "lava_cube", "flame_spirit"], 9),
             Z("c3", "무스펠 전초기지", "흑요석 성벽과 전쟁 깃발", ["ash_warrior", "flame_spirit"], 9, mid="muspellsson"),
             Z("c4", "분화구 계단", "용암 폭포 옆 분화구 계단", ["fire_boar", "ash_warrior"], 9),
             Z("c5", "흑요석 신전", "우는 흑요석 신전과 레바테인 제단", ["ash_warrior", "flame_spirit"], 9, mid="sinmara"),
             Z("c6", "불칼 대장간", "만들어지는 거대한 불의 검", ["ash_warrior", "fire_boar", "lava_cube"], 10),
             Z("boss", "수르트의 옥좌", "용암에 둘러싸인 분화구 심장"),
         ],
         boss="surtr", mids=["muspellsson", "sinmara"]),
    dict(id="d09", no=9, tier="high", key="helheim", ko="헬헤임 걀라르 다리", en="Helheim",
         realm="헬헤임", biome=("soulsand_valley", "deep_dark"), color="§3",
         blurb="죽은 자들의 나라. 칼날이 흐르는 강 걀을 건너면 반은 살아 있고 반은 죽은 여왕 헬이 기다립니다.",
         zones=[
             Z("start", "헬베그", "회색 안개 길과 걀 강 선착장"),
             Z("c1", "가시 숲", "죽은 나무와 뾰족한 가시, 스컬크", ["hel_dead", "lost_soul"], 9),
             Z("c2", "걀 강 해안", "칼날 얼음이 떠내려가는 강변", ["hel_dead", "bog_dead"], 9),
             Z("c3", "걀라르 다리", "황금 지붕 다리", ["hel_knight", "hel_dead"], 9, mid="modgudr"),
             Z("c4", "헬그린드", "뼈로 쌓은 헬의 성문", ["hel_knight", "lost_soul", "bog_dead"], 9),
             Z("c5", "그니파 동굴", "사슬이 걸린 개의 동굴", ["corpse", "hel_dead"], 9, mid="garm"),
             Z("c6", "나스트론드", "뱀으로 엮은 시체의 해안, 니드호그의 뼈", ["corpse", "hel_knight", "lost_soul"], 10),
             Z("boss", "엘류드니르", "반은 살고 반은 죽은 헬의 궁전"),
         ],
         boss="hel", mids=["modgudr", "garm"]),
    dict(id="d10", no=10, tier="high", key="ragnarok", ko="비프로스트와 신들의 황혼", en="Bifrost & Ragnarok",
         realm="아스가르드", biome=("cherry_grove", "meadow", "basalt_deltas"), color="§e",
         blurb="무지개 다리 비프로스트를 건너 아스가르드로. 라그나로크의 들판에서 사슬을 끊은 펜리르가 기다립니다.",
         zones=[
             Z("start", "비프로스트 기슭", "하늘 위 섬과 무지개 다리의 시작"),
             Z("c1", "무지개 다리", "불꽃 화로가 지키는 색유리 하늘 다리", ["storm_spirit", "jotun_warrior"], 9),
             Z("c2", "히민비요르그", "헤임달의 성문과 걀라르호른", ["jotun_warrior", "jotun_mage"], 9),
             Z("c3", "세계의 바다 성벽", "세계뱀이 솟아오르는 바다 성벽", ["jotun_warrior", "storm_spirit"], 9, mid="jormungandr"),
             Z("c4", "황금 방패 회랑", "황금 방패 지붕과 창 서까래의 발할라", ["einherjar_fallen", "jotun_mage"], 9),
             Z("c5", "이다볼 평원", "황금 말판이 놓인 신들의 들판", ["jotun_warrior", "fenrir_pup"], 9, mid="loki"),
             Z("c6", "불타는 위그리드", "부서진 무기와 불타는 황금 전당", ["muspel_raider", "einherjar_fallen", "fenrir_pup"], 10),
             Z("boss", "신들의 황혼", "불타는 이그드라실 가지 아래 부서진 하늘섬"),
         ],
         boss="fenrir", mids=["jormungandr", "loki"]),
]


def S(kind, cast, cd, dmg=0, **kw):
    d = dict(kind=kind, cast=cast, cd=cd, dmg=dmg)
    d.update(kw)
    return d


# model archetypes: humanoid / dwarf / giant / beast / dragon / serpent / spirit / winged
BOSSES = {
    # ---------------------------------------------------------------- D1
    "arnarr": dict(ko="고분왕 아르나르", title="망자들의 왕", dungeon="d01", role="final", model="humanoid",
                   hp=360, melee=5, speed=0.23, size=(1.2, 3.0), arena=15, color="red",
                   palette=dict(skin="#6f7a6a", cloth="#3b4a3f", metal="#7b7466", trim="#a8873e", glow="#7fe0ff"),
                   kit=dict(helm="horned", weapon="greatsword", beard=True, cape=True, crown=True, decay=True),
                   skills={
                       "slash": S("beam", 34, 50, 6, name="망자의 검기", len=16, width=3, track=14, lock=10, fx="soul"),
                       "slam": S("slam", 30, 60, 7, name="무덤 강타", radius=5, knock=0.9, fx="dust"),
                       "summon": S("summon", 40, 260, 0, name="고분의 부름", mob="draugr", count=3),
                       "curse": S("strike", 36, 70, 6, name="저주의 원", radius=2.5, effect="slowness", fx="soul"),
                   },
                   phases=[(1.0, ["slash", "slam", "summon"]), (0.5, ["slash", "slam", "curse", "summon"])]),
    # ---------------------------------------------------------------- D2
    "hati": dict(ko="하티", title="달을 쫓는 늑대", dungeon="d02", role="final", model="beast",
                 hp=420, melee=6, speed=0.32, size=(2.2, 2.4), arena=16, color="cyan",
                 palette=dict(fur="#9aa3ad", fur2="#5d6670", belly="#c9ced4", glow="#9fe8ff", rune="#7fd6ff"),
                 kit=dict(mane=True, chains=False, runes=True, scale=1.0),
                 skills={
                     "charge": S("charge", 30, 50, 7, name="달그림자 돌진", len=18, width=3, fx="moon"),
                     "claw": S("cone", 22, 40, 6, name="할퀴기", radius=6, angle=90, fx="crit"),
                     "leap": S("leap", 34, 70, 8, name="달빛 도약", radius=4, fx="moon"),
                     "howl": S("ring", 36, 90, 6, name="월광 포효", inner=3, outer=10, effect="slowness", fx="moon"),
                     "pack": S("summon", 40, 300, 0, name="늑대 무리", mob="iron_wolf", count=3),
                 },
                 phases=[(1.0, ["charge", "claw", "leap"]), (0.5, ["charge", "claw", "leap", "howl", "pack"])]),
    # ---------------------------------------------------------------- D3
    "andvari": dict(ko="안드바리", title="저주받은 황금의 난쟁이", dungeon="d03", role="final", model="dwarf",
                    hp=400, melee=5, speed=0.25, size=(1.4, 2.2), arena=15, color="gold",
                    palette=dict(skin="#c99a78", cloth="#4b3a6b", metal="#d9a92c", trim="#f4d65c", glow="#ffd84a", beard="#c3c8cc"),
                    kit=dict(helm="cap", weapon="pick", beard=True, ring=True, sack=True),
                    skills={
                        "rocks": S("rain", 36, 60, 6, name="황금 낙석", count=6, radius=2.5, stagger=6, fx="gold"),
                        "ray": S("beam", 36, 60, 7, name="저주의 반지 광선", len=20, width=2, track=20, lock=10, fx="gold"),
                        "whirl": S("pull", 40, 90, 8, name="물의 소용돌이", radius=8, core=3, fx="water"),
                        "burst": S("slam", 30, 60, 8, name="황금 폭발", radius=6, fx="gold"),
                        "thief": S("strike", 30, 70, 6, name="도둑맞은 금화", radius=2.2, fx="gold"),
                    },
                    phases=[(1.0, ["rocks", "ray", "burst"]), (0.5, ["rocks", "ray", "whirl", "burst", "thief"])]),
    # ---------------------------------------------------------------- D4
    "hrungnir": dict(ko="흐룽그니르", title="돌 심장의 거인", dungeon="d04", role="final", model="giant",
                     hp=520, melee=7, speed=0.2, size=(2.4, 4.6), arena=17, color="orange",
                     palette=dict(skin="#8a8a86", cloth="#5b5446", metal="#6c6c70", trim="#c25b2a", glow="#ff8a3d", moss="#5c7a3a"),
                     kit=dict(helm="none", weapon="whetstone", beard=False, stone=True, moss=True),
                     skills={
                         "whet": S("beam", 34, 50, 8, name="숫돌 투척", len=22, width=3, track=10, lock=10, fx="dust"),
                         "quake": S("wave", 30, 70, 8, name="대지 강타", count=3, step=3.5, width=2.5, delay=8, fx="dust"),
                         "boulder": S("strike", 40, 60, 7, name="바위 던지기", radius=3, fx="dust"),
                         "slide": S("rain", 40, 90, 7, name="산사태", count=8, radius=3, stagger=5, fx="dust"),
                         "rush": S("charge", 30, 70, 8, name="거인의 돌진", len=16, width=4, fx="dust"),
                     },
                     phases=[(1.0, ["whet", "quake", "boulder"]), (0.5, ["whet", "quake", "boulder", "slide", "rush"])]),
    # ---------------------------------------------------------------- D5
    "naglfari": dict(ko="나글파리", title="망자의 손톱을 모으는 자", dungeon="d05", role="mid1", model="humanoid",
                     hp=600, melee=7, speed=0.3, size=(1.2, 2.8), arena=15, color="purple",
                     palette=dict(skin="#8c8a9a", cloth="#2b2236", metal="#5a5566", trim="#9d7bd8", glow="#c58bff"),
                     kit=dict(helm="hood", weapon="hook", beard=False, hunch=True, claws=True),
                     skills={
                         "nails": S("rain", 34, 50, 7, name="손톱 비", count=8, radius=2, stagger=4, fx="soul"),
                         "hook": S("beam", 30, 50, 7, name="갈고리 사슬", len=18, width=2, track=12, lock=8, pull=True, fx="soul"),
                         "rake": S("cone", 20, 50, 7, name="세 갈래 할퀴기", radius=5, angle=120, times=3, fx="crit"),
                         "dirge": S("ring", 34, 80, 7, name="죽음의 원", inner=3, outer=8, fx="soul"),
                     },
                     phases=[(1.0, ["nails", "hook", "rake"]), (0.5, ["nails", "hook", "rake", "dirge"])]),
    "hraesvelgr": dict(ko="흐레스벨그", title="바람을 일으키는 독수리 거인", dungeon="d05", role="mid2", model="winged",
                       hp=700, melee=8, speed=0.3, size=(1.8, 3.4), arena=17, color="cyan",
                       palette=dict(skin="#d9c9a8", cloth="#6b5a44", metal="#8b8f98", trim="#e2b04a", glow="#aef6ff", feather="#4e4236", feather2="#e9e1cf"),
                       kit=dict(head="eagle", weapon="none", wings=True, talons=True),
                       skills={
                           "gale": S("sweep", 34, 60, 7, name="폭풍 날개", count=3, width=4, spacing=8, knock=1.4, fx="wind"),
                           "dive": S("leap", 34, 60, 8, name="급강하", radius=5, fx="wind"),
                           "feathers": S("strike", 28, 50, 6, name="깃털 화살", radius=2, times=2, fx="wind"),
                           "cyclone": S("ring", 36, 80, 7, name="회오리", inner=4, outer=12, knock=1.2, fx="wind"),
                       },
                       phases=[(1.0, ["gale", "dive", "feathers"]), (0.5, ["gale", "dive", "feathers", "cyclone"])]),
    "hrym": dict(ko="흐림", title="나글파르의 선장", dungeon="d05", role="final", model="giant",
                 hp=1100, melee=9, speed=0.24, size=(2.4, 4.8), arena=19, color="red",
                 palette=dict(skin="#7d93a6", cloth="#2e3440", metal="#4b5563", trim="#b8c4d1", glow="#9fd8ff", beard="#dfe8ef"),
                 kit=dict(helm="horned", weapon="anchor", beard=True, cape=True, frost=True),
                 skills={
                     "anchor": S("slam", 32, 50, 9, name="닻 내려치기", radius=7, knock=1.0, fx="water"),
                     "chain": S("beam", 34, 50, 9, name="닻 사슬 투척", len=24, width=3, track=16, lock=10, fx="water"),
                     "sweep": S("cone", 30, 60, 9, name="갑판 쓸기", radius=9, angle=120, fx="water"),
                     "crew": S("summon", 40, 300, 0, name="망자의 선원", mob="bone_sailor", count=4),
                     "tide": S("wave", 30, 90, 8, name="서리 파도", count=4, step=3.5, width=2.5, delay=7, effect="slowness", fx="frost"),
                     "barrage": S("rain", 40, 90, 9, name="나글파르의 포격", count=12, radius=3, stagger=3, fx="water"),
                     "cross": S("radial", 32, 80, 9, name="닻사슬 십자", count=4, len=22, width=3, spin=45, fx="water"),
                 },
                 phases=[(1.0, ["anchor", "chain", "sweep", "crew"]), (0.66, ["anchor", "chain", "sweep", "tide", "crew"]),
                         (0.33, ["chain", "sweep", "tide", "barrage", "cross"])]),
    # ---------------------------------------------------------------- D6
    "logi": dict(ko="로기", title="모든 것을 삼키는 들불", dungeon="d06", role="mid1", model="spirit",
                 hp=650, melee=7, speed=0.3, size=(1.4, 3.0), arena=16, color="orange",
                 palette=dict(core="#fff2a8", flame="#ff8a1f", flame2="#d63a12", ember="#5a1a0a", glow="#ffd27a"),
                 kit=dict(form="flame"),
                 skills={
                     "devour": S("pull", 40, 70, 8, name="불길 삼키기", radius=9, core=4, fx="fire"),
                     "spokes": S("radial", 32, 60, 8, name="불꽃 줄기", count=4, len=18, width=2.5, spin=45, fx="fire"),
                     "pyre": S("strike", 30, 50, 7, name="화염 장판", radius=3, effect="fire", fx="fire"),
                     "wildfire": S("ring", 34, 80, 7, name="들불", inner=4, outer=11, effect="fire", fx="fire"),
                 },
                 phases=[(1.0, ["devour", "spokes", "pyre"]), (0.5, ["devour", "spokes", "pyre", "wildfire"])]),
    "elli": dict(ko="엘리", title="늙음 그 자체", dungeon="d06", role="mid2", model="humanoid",
                 hp=750, melee=8, speed=0.22, size=(1.1, 2.6), arena=16, color="purple",
                 palette=dict(skin="#b9ab9a", cloth="#4a3d5c", metal="#7b6f86", trim="#c9b06a", glow="#d7b8ff", hair="#e8e6e1"),
                 kit=dict(helm="hood", weapon="staff", beard=False, hunch=True, hair=True),
                 skills={
                     "grip": S("strike", 30, 50, 8, name="세월의 손아귀", radius=2.5, effect="slowness", fx="time"),
                     "hourglass": S("ring", 36, 70, 8, name="시간의 고리", inner=4, outer=14, fx="time"),
                     "wither": S("cone", 28, 50, 8, name="노쇠", radius=8, angle=90, effect="weakness", fx="time"),
                     "sands": S("rain", 36, 70, 7, name="흩어지는 모래", count=9, radius=2.5, stagger=4, fx="time"),
                 },
                 phases=[(1.0, ["grip", "wither", "sands"]), (0.5, ["grip", "hourglass", "wither", "sands"])]),
    "utgardaloki": dict(ko="우트가르다 로키", title="환영의 거인왕", dungeon="d06", role="final", model="giant",
                        hp=1300, melee=9, speed=0.24, size=(2.2, 5.0), arena=20, color="purple",
                        palette=dict(skin="#a39b8e", cloth="#3c2f5a", metal="#6d6577", trim="#e0c25a", glow="#c9a4ff", beard="#5b4b3a"),
                        kit=dict(helm="crown", weapon="staff", beard=True, cape=True, robe=True),
                        skills={
                            "illusion": S("clone", 40, 140, 8, name="환영 분신", count=3, len=22, width=2.5, track=20, lock=12, fx="illusion"),
                            "ray": S("beam", 34, 50, 9, name="환영 광선", len=24, width=3, track=18, lock=10, fx="illusion"),
                            "hand": S("slam", 32, 60, 9, name="거인의 손", radius=8, fx="dust"),
                            "star": S("radial", 32, 70, 9, name="착각의 별", count=8, len=20, width=2, fx="illusion"),
                            "warp": S("sweep", 34, 80, 9, name="왜곡된 대지", count=4, width=4, spacing=9, fx="illusion"),
                            "endless": S("clone", 40, 160, 8, name="끝없는 환영", count=5, len=22, width=2.5, track=16, lock=12, fx="illusion"),
                            "fall": S("rain", 40, 80, 8, name="무너지는 천장", count=12, radius=3, stagger=3, fx="dust"),
                        },
                        phases=[(1.0, ["illusion", "ray", "hand"]), (0.66, ["illusion", "ray", "hand", "star", "warp"]),
                                (0.33, ["endless", "ray", "star", "warp", "fall"])]),
    # ---------------------------------------------------------------- D7
    "brokkr": dict(ko="브로크", title="풀무를 밟는 난쟁이", dungeon="d07", role="mid1", model="dwarf",
                   hp=700, melee=8, speed=0.25, size=(1.4, 2.2), arena=16, color="orange",
                   palette=dict(skin="#c48b6a", cloth="#5a3a24", metal="#7c7f86", trim="#d18a2c", glow="#ff9a3c", beard="#7a3b1c"),
                   kit=dict(helm="cap", weapon="bellows", beard=True, apron=True),
                   skills={
                       "blast": S("cone", 30, 50, 8, name="풀무 돌풍", radius=10, angle=60, knock=1.5, fx="fire"),
                       "hammer": S("slam", 28, 50, 8, name="망치 내려치기", radius=5, fx="fire"),
                       "embers": S("rain", 34, 60, 7, name="불씨 날리기", count=8, radius=2.5, stagger=4, fx="fire"),
                       "vent": S("radial", 32, 70, 8, name="용광로 분출", count=4, len=18, width=2.5, spin=45, fx="fire"),
                   },
                   phases=[(1.0, ["blast", "hammer", "embers"]), (0.5, ["blast", "hammer", "embers", "vent"])]),
    "eitri": dict(ko="에이트리", title="묠니르를 벼린 난쟁이", dungeon="d07", role="mid2", model="dwarf",
                  hp=800, melee=9, speed=0.25, size=(1.4, 2.2), arena=16, color="gold",
                  palette=dict(skin="#b9876a", cloth="#30405a", metal="#9aa0a8", trim="#e2b84a", glow="#ffe27a", beard="#d8d2c8"),
                  kit=dict(helm="winged", weapon="hammer", beard=True, apron=True),
                  skills={
                      "anvil": S("strike", 30, 50, 8, name="모루 낙하", radius=3, times=2, fx="gold"),
                      "steam": S("ring", 34, 70, 8, name="담금질 증기", inner=3, outer=10, fx="steam"),
                      "rune": S("beam", 34, 50, 9, name="룬 각인 광선", len=22, width=2.5, track=16, lock=10, fx="gold"),
                      "spin": S("charge", 30, 60, 9, name="망치 회전", len=16, width=4, times=2, fx="gold"),
                  },
                  phases=[(1.0, ["anvil", "rune", "spin"]), (0.5, ["anvil", "steam", "rune", "spin"])]),
    "fafnir": dict(ko="파프니르", title="황금에 눈먼 용", dungeon="d07", role="final", model="dragon",
                   hp=1500, melee=10, speed=0.26, size=(3.0, 3.4), arena=21, color="green",
                   palette=dict(scale="#3d5a2e", scale2="#22351b", belly="#b8a25a", horn="#d8cfb8", glow="#b6ff5a", wing="#2f3b25"),
                   kit=dict(wings=True, horns=True, spikes=True),
                   skills={
                       "breath": S("cone", 34, 50, 10, name="독의 숨결", radius=12, angle=90, track=14, lock=10, effect="poison", fx="poison"),
                       "tail": S("cone", 26, 50, 9, name="꼬리 쓸기", radius=8, angle=180, back=True, fx="dust"),
                       "gust": S("sweep", 34, 60, 9, name="날개 돌풍", count=3, width=4, spacing=9, knock=1.4, fx="wind"),
                       "venom": S("rain", 36, 70, 9, name="독액 비", count=10, radius=3, stagger=3, effect="poison", fx="poison"),
                       "greed": S("leap", 34, 70, 11, name="황금 탐욕", radius=6, fx="gold"),
                       "fury": S("radial", 32, 80, 10, name="용의 분노", count=8, len=22, width=2.5, fx="poison"),
                   },
                   phases=[(1.0, ["breath", "tail", "gust"]), (0.66, ["breath", "tail", "gust", "venom", "greed"]),
                           (0.33, ["breath", "venom", "greed", "fury", "gust"])]),
    # ---------------------------------------------------------------- D8
    "muspellsson": dict(ko="무스펠손", title="불꽃의 선봉장", dungeon="d08", role="mid1", model="humanoid",
                        hp=900, melee=10, speed=0.28, size=(1.4, 3.2), arena=17, color="orange",
                        palette=dict(skin="#4a2a22", cloth="#2a1a16", metal="#3a3434", trim="#ff7a1a", glow="#ffb347"),
                        kit=dict(helm="spiked", weapon="spear", beard=False, cape=True, cracks=True),
                        skills={
                            "spear": S("beam", 30, 50, 10, name="불창 투척", len=26, width=2, track=14, lock=8, fx="fire"),
                            "lava": S("strike", 30, 50, 9, name="용암 장판", radius=3, effect="fire", fx="fire"),
                            "assault": S("charge", 28, 60, 10, name="돌격", len=20, width=4, fx="fire"),
                            "vortex": S("ring", 34, 80, 9, name="불꽃 회오리", inner=3, outer=10, effect="fire", fx="fire"),
                        },
                        phases=[(1.0, ["spear", "lava", "assault"]), (0.5, ["spear", "lava", "assault", "vortex"])]),
    "sinmara": dict(ko="신마라", title="레바테인을 지키는 자", dungeon="d08", role="mid2", model="humanoid",
                    hp=1000, melee=10, speed=0.26, size=(1.1, 2.9), arena=17, color="red",
                    palette=dict(skin="#d8a38a", cloth="#6a1414", metal="#2e2a2a", trim="#ffb02e", glow="#ff5a2a", hair="#ff6a1a"),
                    kit=dict(helm="circlet", weapon="flamesword", beard=False, hair=True, robe=True),
                    skills={
                        "laeva": S("beam", 34, 50, 11, name="레바테인 광선", len=26, width=4, track=18, lock=10, fx="fire"),
                        "rings": S("wave", 30, 70, 10, name="불의 원", count=4, step=3.5, width=2.5, delay=7, effect="fire", fx="fire"),
                        "meteor": S("rain", 40, 70, 10, name="운석", count=10, radius=3, stagger=3, fx="fire"),
                        "star": S("radial", 32, 70, 10, name="불꽃 별", count=6, len=20, width=2.5, spin=30, fx="fire"),
                    },
                    phases=[(1.0, ["laeva", "rings", "meteor"]), (0.5, ["laeva", "rings", "meteor", "star"])]),
    "surtr": dict(ko="수르트", title="세계를 태우는 불의 거인", dungeon="d08", role="final", model="giant",
                  hp=2200, melee=12, speed=0.24, size=(2.6, 5.6), arena=23, color="orange",
                  palette=dict(skin="#3a1c14", cloth="#1c1210", metal="#2b2424", trim="#ff6a00", glow="#ffcf4a", beard="#ff8a1a"),
                  kit=dict(helm="crown", weapon="flamesword", beard=True, cape=True, cracks=True, fire=True),
                  skills={
                      "blade": S("beam", 34, 50, 13, name="불의 검 내려치기", len=28, width=5, track=18, lock=12, fx="fire"),
                      "swing": S("cone", 30, 50, 12, name="검 휘두르기", radius=12, angle=180, fx="fire"),
                      "rain": S("rain", 40, 70, 11, name="무스펠의 불비", count=14, radius=3.5, stagger=3, effect="fire", fx="fire"),
                      "collapse": S("wave", 32, 70, 12, name="대지 붕괴", count=4, step=4, width=3, delay=7, fx="fire"),
                      "star": S("radial", 32, 80, 12, name="불타는 별", count=8, len=24, width=3, spin=22.5, fx="fire"),
                      "worldfire": S("sweep", 36, 90, 12, name="세계를 태우는 불꽃", count=5, width=4, spacing=8, effect="fire", fx="fire"),
                  },
                  phases=[(1.0, ["blade", "swing", "rain"]), (0.66, ["blade", "swing", "rain", "collapse", "star"]),
                          (0.33, ["blade", "swing", "star", "worldfire", "rain"])]),
    # ---------------------------------------------------------------- D9
    "modgudr": dict(ko="모드구드", title="걀라르 다리의 문지기", dungeon="d09", role="mid1", model="humanoid",
                    hp=950, melee=10, speed=0.27, size=(1.1, 2.9), arena=16, color="cyan",
                    palette=dict(skin="#b8d0d6", cloth="#1f3a44", metal="#d4b04a", trim="#e8d27a", glow="#8ff3ff", hair="#e6f4f7"),
                    kit=dict(helm="winged", weapon="spear", beard=False, hair=True, robe=True, ghost=True),
                    skills={
                        "judge": S("sweep", 34, 60, 10, name="다리의 심판", count=4, width=3.5, spacing=8, fx="soul"),
                        "spear": S("beam", 30, 50, 10, name="혼령의 창", len=24, width=2, track=16, lock=8, fx="soul"),
                        "wail": S("ring", 34, 70, 9, name="통곡", inner=4, outer=11, effect="weakness", fx="soul"),
                        "hands": S("strike", 28, 50, 9, name="망자의 손", radius=2.5, times=2, effect="slowness", fx="soul"),
                    },
                    phases=[(1.0, ["judge", "spear", "hands"]), (0.5, ["judge", "spear", "wail", "hands"])]),
    "garm": dict(ko="가름", title="헬의 문을 지키는 개", dungeon="d09", role="mid2", model="beast",
                 hp=1050, melee=11, speed=0.33, size=(2.4, 2.6), arena=17, color="red",
                 palette=dict(fur="#3b2a28", fur2="#1e1514", belly="#6b3b33", glow="#ff3a2a", rune="#ff5a3a"),
                 kit=dict(mane=True, chains=True, runes=False, eyes4=True, scale=1.15),
                 skills={
                     "rush": S("charge", 26, 50, 11, name="피의 돌진", len=20, width=3, times=3, fx="blood"),
                     "bite": S("cone", 22, 40, 11, name="물어뜯기", radius=6, angle=80, fx="blood"),
                     "howl": S("ring", 34, 70, 10, name="울부짖음", inner=4, outer=12, effect="weakness", fx="blood"),
                     "break": S("slam", 30, 60, 11, name="사슬 끊기", radius=7, knock=1.1, fx="blood"),
                 },
                 phases=[(1.0, ["rush", "bite", "break"]), (0.5, ["rush", "bite", "howl", "break"])]),
    "hel": dict(ko="헬", title="죽은 자들의 여왕", dungeon="d09", role="final", model="humanoid",
                hp=2400, melee=12, speed=0.24, size=(1.3, 3.4), arena=22, color="purple",
                palette=dict(skin="#e8d6c8", skin2="#3a4a52", cloth="#1a1424", metal="#3c3846", trim="#9fe7ff", glow="#b28cff", hair="#121016"),
                kit=dict(helm="crown", weapon="staff", beard=False, hair=True, robe=True, half=True, cape=True),
                skills={
                    "gaze": S("beam", 40, 50, 13, name="죽음의 시선", len=30, width=3, track=30, lock=14, effect="wither", fx="soul"),
                    "half": S("cone", 34, 60, 12, name="반쪽의 저주", radius=22, angle=180, side=True, fx="soul"),
                    "legion": S("summon", 40, 300, 0, name="망자의 군세", mob="hel_dead", count=5),
                    "souls": S("rain", 38, 60, 11, name="영혼의 비", count=12, radius=3, stagger=3, fx="soul"),
                    "judgement": S("radial", 32, 70, 12, name="헬의 심판", count=8, len=24, width=2.5, spin=22.5, fx="soul"),
                    "gate": S("ring", 34, 80, 12, name="엘류드니르의 문", inner=5, outer=16, fx="soul"),
                },
                phases=[(1.0, ["gaze", "half", "souls", "legion"]), (0.66, ["gaze", "half", "souls", "judgement", "legion"]),
                        (0.33, ["gaze", "half", "judgement", "gate", "souls"])]),
    # ---------------------------------------------------------------- D10
    "jormungandr": dict(ko="요르문간드", title="세계를 휘감은 뱀", dungeon="d10", role="mid1", model="serpent",
                        hp=1200, melee=11, speed=0.25, size=(2.6, 3.6), arena=19, color="green",
                        palette=dict(scale="#2e5e5a", scale2="#173734", belly="#9fbf7a", horn="#cfe0c8", glow="#7dff9a", fin="#3a7a6a"),
                        kit=dict(segments=7),
                        skills={
                            "tide": S("sweep", 34, 60, 11, name="독의 파도", count=4, width=4, spacing=8, effect="poison", fx="poison"),
                            "spit": S("cone", 32, 50, 11, name="독 분사", radius=12, angle=60, track=14, lock=10, effect="poison", fx="poison"),
                            "ram": S("charge", 30, 60, 12, name="몸통 박치기", len=26, width=4, fx="water"),
                            "coil": S("ring", 36, 80, 11, name="세계뱀의 포위", inner=6, outer=17, fx="poison"),
                        },
                        phases=[(1.0, ["tide", "spit", "ram"]), (0.5, ["tide", "spit", "ram", "coil"])]),
    "loki": dict(ko="로키", title="사슬을 풀고 온 거짓의 신", dungeon="d10", role="mid2", model="humanoid",
                 hp=1100, melee=11, speed=0.28, size=(1.0, 2.8), arena=18, color="green",
                 palette=dict(skin="#d8b89a", cloth="#1c4a2a", metal="#3a3a3a", trim="#d4af37", glow="#7dff6a", hair="#1a1a12"),
                 kit=dict(helm="horns", weapon="daggers", beard=False, hair=True, cape=True),
                 skills={
                     "tricks": S("clone", 40, 120, 10, name="분신술", count=4, len=22, width=2, track=16, lock=10, fx="illusion"),
                     "shift": S("leap", 30, 50, 11, name="변신 도약", radius=5, fx="illusion"),
                     "star": S("radial", 30, 60, 11, name="속임수의 별", count=6, len=20, width=2.5, spin=30, fx="illusion"),
                     "prank": S("rain", 36, 60, 10, name="불의 장난", count=10, radius=2.5, stagger=3, effect="fire", fx="fire"),
                 },
                 phases=[(1.0, ["tricks", "shift", "star"]), (0.5, ["tricks", "shift", "star", "prank"])]),
    "fenrir": dict(ko="펜리르", title="신들의 황혼을 부르는 늑대", dungeon="d10", role="final", model="beast",
                   hp=3000, melee=14, speed=0.3, size=(3.4, 3.6), arena=24, color="red",
                   palette=dict(fur="#1f1f24", fur2="#0e0e12", belly="#3a3a44", glow="#ff3a1a", rune="#ff7a2a"),
                   kit=dict(mane=True, chains=True, runes=True, eyes4=False, scale=1.6),
                   skills={
                       "devour": S("cone", 32, 50, 14, name="포식", radius=11, angle=100, track=16, lock=10, fx="blood"),
                       "frenzy": S("charge", 28, 50, 13, name="폭주 돌진", len=26, width=4, times=2, fx="blood"),
                       "gleipnir": S("wave", 32, 70, 13, name="글레이프니르 끊기", count=4, step=4, width=3, delay=7, fx="blood"),
                       "howl": S("ring", 36, 70, 13, name="라그나로크의 울부짖음", inner=5, outer=16, effect="weakness", fx="blood"),
                       "eclipse": S("rain", 40, 80, 12, name="달을 삼키는 어둠", count=16, radius=3, stagger=2, effect="blindness", fx="blood"),
                       "fangs": S("radial", 30, 70, 13, name="이빨의 별", count=8, len=24, width=3, spin=22.5, fx="blood"),
                       "storm": S("sweep", 34, 80, 13, name="황혼의 폭풍", count=5, width=4, spacing=8, fx="blood"),
                       "pack": S("summon", 40, 300, 0, name="새끼 늑대들", mob="fenrir_pup", count=4),
                   },
                   phases=[(1.0, ["devour", "frenzy", "gleipnir", "pack"]), (0.66, ["devour", "frenzy", "gleipnir", "howl", "eclipse"]),
                           (0.33, ["devour", "frenzy", "fangs", "storm", "eclipse", "howl"])]),
}

ORDER = [d["id"] for d in DUNGEONS]
BY_ID = {d["id"]: d for d in DUNGEONS}


def check():
    ids = set()
    for d in DUNGEONS:
        assert len(d["zones"]) == 8 and d["zones"][0]["key"] == "start" and d["zones"][-1]["key"] == "boss"
        for z in d["zones"]:
            for m in z["mobs"]:
                assert m in MOBS, m
        assert d["boss"] in BOSSES and BOSSES[d["boss"]]["dungeon"] == d["id"]
        mids = [z["mid"] for z in d["zones"] if z["mid"]]
        assert mids == d["mids"], (d["id"], mids)
        assert (d["tier"] == "beginner") == (not mids)
        if mids:
            assert d["zones"][3]["mid"] and d["zones"][5]["mid"]
        ids.update([d["boss"]] + mids)
    assert ids == set(BOSSES), ids ^ set(BOSSES)
    for k, b in BOSSES.items():
        for _, pool in b["phases"]:
            for s in pool:
                assert s in b["skills"], (k, s)
        for s in b["skills"].values():
            if s["kind"] == "summon":
                assert s["mob"] in MOBS
    return len(BOSSES)


if __name__ == "__main__":
    print("bosses:", check())
