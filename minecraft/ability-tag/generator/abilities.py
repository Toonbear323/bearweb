"""Ability shop catalogue shared by the lobby builder and the behavior pack generator."""

# effects: (effect, amplifier, seconds or "infinite")
ABILITIES = [
    dict(id=1, key="speed", name="신속", color="§b", price=60,
         desc="이동 속도가 크게 증가합니다.", detail="신속 II · 게임 내내 유지",
         effects=[("speed", 1, "infinite")]),
    dict(id=2, key="jump", name="도약", color="§a", price=50,
         desc="점프력이 크게 증가합니다.", detail="점프 강화 II · 게임 내내 유지",
         effects=[("jump_boost", 1, "infinite")]),
    dict(id=3, key="invis", name="투명화", color="§7", price=80,
         desc="시작하자마자 모습을 감춥니다.", detail="투명화 · 게임 시작 후 30초",
         effects=[("invisibility", 0, 30)]),
    dict(id=4, key="feather", name="깃털", color="§f", price=40,
         desc="깃털처럼 가볍게 떨어집니다.", detail="느린 낙하 + 점프 강화 I",
         effects=[("slow_falling", 0, "infinite"), ("jump_boost", 0, "infinite")]),
    dict(id=5, key="owl", name="올빼미 눈", color="§9", price=25,
         desc="어두운 곳도 대낮처럼 보입니다.", detail="야간 투시 · 게임 내내 유지",
         effects=[("night_vision", 0, "infinite")]),
    dict(id=6, key="mermaid", name="인어", color="§3", price=40,
         desc="물속에서 숨 막힘 없이 잘 보입니다.", detail="전달체의 힘 + 신속 I",
         effects=[("conduit_power", 0, "infinite"), ("speed", 0, "infinite")]),
    dict(id=7, key="berserk", name="폭주", color="§c", price=70,
         desc="시작 직후 폭발적으로 질주합니다.", detail="신속 IV + 점프 강화 III · 15초",
         effects=[("speed", 3, 15), ("jump_boost", 2, 15)]),
    dict(id=8, key="hunter", name="사냥꾼", color="§6", price=70,
         desc="빠른 발과 밤눈을 함께 가집니다.", detail="신속 I + 야간 투시 · 게임 내내 유지",
         effects=[("speed", 0, "infinite"), ("night_vision", 0, "infinite")]),
]

START_COINS = 200
