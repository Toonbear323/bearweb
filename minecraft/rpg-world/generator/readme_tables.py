"""Prints the coordinate tables of README.md from world_info.json (python readme_tables.py)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
info = json.load(open(os.path.join(HERE, "..", "world_info.json"), encoding="utf8"))
NAMES = {k: v["name"] for k, v in info["regions"].items()}


def c(p):
    return "%d %d %d" % tuple(p[:3])


print("### 지역 도착 지점\n")
print("| 지역 | 도착 지점 (x y z) | 관리자 이동 |")
print("|---|---|---|")
for k, v in info["regions"].items():
    print("| %s | %s | `/function %s` |" % (v["name"], c(v["arrival"]), v["tp"]))

print("\n### 편의 공간 (상인 자리 · 엔더 상자)\n")
print("| 지역 | 이름 | 상인(NPC) 자리 | 엔더 상자 |")
print("|---|---|---|---|")
for s in info["shops"]:
    print("| %s | %s | %s | %s |" % (NAMES.get(s["region"], s["region"]), s["name"], c(s["npc_spot"]),
                                    " / ".join(c(e) for e in s["ender_chests"])))

print("\n### 사냥터\n")
print("| 지역 | 이름 | 내부 범위 (x1 y1 z1 ~ x2 y2 z2) | 지붕 | 입구 | 스폰 지점 | 함수 키 |")
print("|---|---|---|---|---|---|---|")
for h in info["hunting_grounds"]:
    b = h["box"]
    print("| %s | %s | %d %d %d ~ %d %d %d | %s | %s | %s | `%s` |" % (
        NAMES.get(h["region"], h["region"]), h["name"], *b, "있음" if h["roofed"] else "없음 (위가 열림)",
        " / ".join(c(e) for e in h["entrances"]), " / ".join(c(p) for p in h["spawn_points"]), h["key"]))

print("\n### 보스방\n")
print("| 지역 | 보스방 | 보스 소환 지점 | 입구 | 예시 보스 함수 |")
print("|---|---|---|---|---|")
for b in info["bosses"]:
    print("| %s | %s | %s | %s | `/function %s` |" % (NAMES.get(b["region"], b["region"]), b["name"],
                                                    c(b["boss_spawn"]), c(b["entrance"]), b["function"]))

print("\n### 뽑기 기계\n")
print("| 등급 | 버튼 위치 | 버튼을 누르면 실행되는 함수 |")
print("|---|---|---|")
for g in info["gacha"]:
    print("| %s | %s | `%s` |" % (g["tier"], c(g["button"]), g["function"]))

print("\n### 관문 (색 유리창)\n")
print("| 관문 | 위치 | 유리 색 |")
print("|---|---|---|")
for g in info["gates"]:
    nm = g["next"]
    for code in ("§a", "§2", "§b", "§5", "§c", "§f", "§l", "§r"):
        nm = nm.replace(code, "")
    pv = g["prev"]
    for code in ("§a", "§2", "§b", "§5", "§c", "§f", "§l", "§r"):
        pv = pv.replace(code, "")
    print("| %s → %s | %s | %s |" % (pv, nm, c(g["pos"]), g["glass"]))
v = info["verification"]
print("\n검사: 도달 %d · 갇힘 %d · 탈출 %d · 4칸 이상 낙하 %d" % (v["reachable"], v["trapped"], v["escaped"],
                                                            v["fall_edges"]))
for k, s in v["light"].items():
    print("  light", k, s)
