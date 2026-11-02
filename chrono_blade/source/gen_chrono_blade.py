"""§b§l시공§f§l의 분침 (vh:chrono_blade) 생성기 — 보스 「시간의 여신」 을 쓰러뜨리면 얻는 검 (main.js CRB)
"시공간이 칼날이 된 것처럼": 여신의 분침 검 (브레게 바늘 모양) 을 그대로 잇되, 금빛 날 대신 **칼날 자체가 찢어진 시공간**
  - 칼날: 브레게 분침 실루엣 (넓은 뿌리 → 가늘어짐 → 끝 가까이 속이 빈 달 고리 → 가는 창끝) · 가로줄 조각 (두께 있는 판 · 발광)
          속 = 깊은 우주 (남빛 · 보랏빛 성운이 숨 쉬듯 번지고 · 달 고리 우물로 빨려 드는 나선 · 떠올랐다 사라지는 별)
          겉 = 더해 빛나는 시공간 막 (달 고리를 향해 휘어 빨려 드는 격자 고리 · 비틀린 열두 시 살 · 가장자리 분 눈금 60 · 등을 타고 오르는 초침 빛)
          테 = 사건의 지평선처럼 푸른 흰빛 · 둘레 빛무리 (중력 렌즈 · 바깥은 보랏빛)
  - 달 고리: 금빛 베젤 (새긴 눈금) · 속 = 작은 블랙홀 (검은 구 · 기울어진 강착 원반 (한쪽이 더 밝음 · 플립북으로 돎) · 광자 고리)
  - 달 고리를 감도는 궤도 고리 둘 (여신의 얼굴 구체와 같은 짜임 · 빛 알갱이가 고리를 따라 돎)
  - 날밑 = 시계판 (남빛 에나멜 · 기요셰 무늬 · 금 로마 숫자 · 금 톱니 테 · 앞뒤에 도는 시곗바늘) · 양옆 금빛 갈고리 (끝 푸른 보석) · 날 뿌리를 쥔 금 발톱
  - 날밑 둘레를 거꾸로 도는 로마 숫자 고리 (더해 빛남) · 칼날 곁을 떠도는 시공간 파편 여섯 · 칼끝 별
  - 자루 = 남빛 감은 천 + 금실 나선 · 자루 끝 = 작은 모래시계 (금 기둥 셋 · 유리 · 빛나는 모래 · 떨어지는 모래 줄기)
  - 휘두르면 시간의 잔상 둘이 늦게 따라옴 (공격 애니)
플립북: 한 칸 (FW x FH) 에 모든 조각을 그려 FR 칸 세로로 쌓음 → 그리기 설정 uv_anim 이 한 칸씩 내려감 (모든 움직임 = 정수 주기 → 이음매 없음)
재질: 이름 *_add = 더해 빛남 · *_glass = 반투명 · 나머지 = 발광 · 들면 머리 자리에 빛 블록 15 (스크립트) → 밤에도 빛깔 그대로
아이템 캔버스: 손 = (CX, CY, 1.6) · 위 (칼끝) = -z · 칼 넓은 면 = ±x (1인칭에서 카메라 쪽)
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import Polygon, Point, box as sbox
from gen_void_brush import CX, CY, R3
from gen_hourglass import EL
from gen_hope_planet import tri
from loft3d import nrm
from tex_kit import Sheet, tbox, seg, loft, lathe, basis, smooth, card, ring_pts, quad
from entity_files import write_geo, write_anims
from tp_fix import tp_hold

NAME = "chrono_blade"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "SevenHope_RP")
X_, Y_, Z_ = np.eye(3)
TAU = 2 * math.pi
H = np.array([CX, CY, 1.6])
P = lambda z, y=0.0, x=0.0: np.array([CX + x, CY + y, z])
FW, FH, FR, FPS = 512, 256, 16, 10                                                       # 플립북 한 칸 · 칸 수 · 초당 칸 (한 바퀴 1.6 초)
LIGHT = nrm(np.array([0.45, -0.35, -0.8]))

# ---------------------------------------------------------------- 치수 (캔버스 px)
ZB, LB = -3.0, 37.0                                                                      # 칼 뿌리 z · 칼 길이 (끝 z = -40)
SR, RO, RI = 26.0, 3.3, 2.0                                                              # 달 고리 (뿌리에서 거리 · 바깥 · 안 반지름)
TH = 0.5                                                                                 # 칼 두께
WR = 7.6                                                                                 # 칼 그림 폭 (px 캔버스 단위)
ZD, RD = -2.4, 3.1                                                                       # 시계판 날밑 (가운데 z · 반지름)
GZ0, GZ1 = 0.7, 6.2                                                                      # 자루
HG0, HG1 = 6.4, 10.6                                                                     # 자루 끝 모래시계
ZR = ZB - SR                                                                             # 달 고리 가운데 z
ZT = ZB - LB                                                                             # 칼끝 z
HS0, HS1 = -1.0, LB + 5.0                                                                # 빛무리 판 (뿌리에서 거리)
WH = 14.0                                                                                # 빛무리 판 폭

DEEP = np.array([4, 6, 18.0])
NAVY = np.array([18, 30, 92.0])
BLUE = np.array([46, 104, 230.0])
VIOL = np.array([118, 62, 210.0])
CYAN = np.array([90, 210, 255.0])
PALE = np.array([214, 238, 255.0])
GOLD = np.array([255, 212, 120.0])
DGOLD = np.array([150, 96, 34.0])
WARM = np.array([255, 200, 120.0])

PH, FRM = 0.0, 0                                                                         # 지금 그리는 칸 (0 ~ 1 · 번호)


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def grid(w, h):
    return np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)


def rgba(col, a=None):
    h, w = col.shape[:2]
    return np.dstack([np.clip(col, 0, 255), np.full((h, w), 255.0) if a is None else np.clip(a, 0, 1) * 255])


def add_rgba(col):
    """더해 빛나는 그림: 색만 (게임은 색 × 알파 → 알파를 밝기로 꽉 채움)"""
    col = np.clip(col, 0, 255)
    a = np.clip(col.max(-1) / 255 * 4, 0, 1)
    return np.dstack([col, a * 255])


# ---------------------------------------------------------------- 칼 실루엣
def hw(s):
    """칼 몸 반폭 (s = 뿌리에서 거리): 뿌리 살짝 벌어짐 → 달 고리까지 가늘어짐 → 고리 뒤 가는 창끝 (잎사귀처럼 살짝 부풂)"""
    s = np.asarray(s, float)
    body = 2.35 + 0.55 * sstep(0, 1.6, s) - 1.55 * np.clip((s - 1.6) / (SR - 1.6), 0, 1) ** 0.9
    t = np.clip((s - SR) / (LB - SR), 0, 1)
    tip = 1.32 * (1 - t) ** 0.8 + 0.42 * np.sin(np.pi * np.clip(t * 1.25, 0, 1)) * (1 - t)
    out = np.where(s < SR, body, tip)
    return np.where((s < 0) | (s > LB), -1.0, out)


def sil_de(X, s):
    """칼 실루엣 부호 거리 (+ = 속 · px): 몸 ∪ 달 고리 − 구멍"""
    r = np.hypot(X, s - SR)
    body = np.where((s >= 0) & (s <= LB), hw(np.clip(s, 0, LB)) - np.abs(X), np.minimum(-np.abs(s - np.clip(s, 0, LB)), hw(np.clip(s, 0, LB)) - np.abs(X)))
    ring = RO - r
    return np.minimum(np.maximum(body, ring), r - RI)


def blade_poly():
    ss = np.linspace(0, LB, 220)
    w = np.maximum(hw(ss), 0.0)
    pts = [(s, float(x)) for s, x in zip(ss, w)] + [(s, -float(x)) for s, x in zip(ss[::-1], w[::-1])]
    return Polygon(pts).buffer(0)


# ---------------------------------------------------------------- 그림 도우미
def stars_drift(w, h, n, seed, Xs, Ss, drift=(0.6, 2.4), size=(0.18, 0.42), bright=(0.5, 1.0), swirl=0.0):
    """떠올랐다 사라지는 별 (칸마다 자기 박자로 · 정수 한 바퀴 → 이음매 없음): Xs · Ss = 칸 좌표 (px 캔버스)"""
    r = np.random.default_rng(seed)
    out = np.zeros((h, w))
    for _ in range(n):
        x0, s0 = r.uniform(-WR / 2, WR / 2), r.uniform(-1, LB)
        dv, ph0 = r.uniform(*drift), r.uniform(0, 1)
        sz, b = r.uniform(*size), r.uniform(*bright)
        ph = (PH + ph0) % 1.0
        dx, ds = x0, s0 - SR
        rr = math.hypot(dx, ds) + 1e-3
        cx = x0 + swirl * (-ds / rr) * ph * 2.0 * math.exp(-rr / 9)                        # 우물 둘레로 조금 휘어 감김
        cs = s0 + dv * ph + swirl * (dx / rr) * ph * 2.0 * math.exp(-rr / 9)
        k = math.sin(math.pi * ph) ** 1.5 * b
        d2 = (Xs - cx) ** 2 + (Ss - cs) ** 2
        out += np.exp(-d2 / (sz * sz)) * k
        if b > 0.85:                                                                       # 밝은 별 = 네 갈래 빛
            out += (np.exp(-((Xs - cx) / 0.06) ** 2 - ((Ss - cs) / (sz * 3.2)) ** 2) + np.exp(-((Ss - cs) / 0.06) ** 2 - ((Xs - cx) / (sz * 3.2)) ** 2)) * k * 0.5
    return out


def stars_static(w, h, n, seed, Xs, Ss, size=(0.12, 0.3)):
    """제자리에서 반짝이는 먼 별 (정수 박자)"""
    r = np.random.default_rng(seed)
    out = np.zeros((h, w))
    for _ in range(n):
        cx, cs = r.uniform(-WR / 2, WR / 2), r.uniform(-1, LB)
        sz, m, ph0 = r.uniform(*size), int(r.integers(1, 4)), r.uniform(0, 1)
        k = 0.55 + 0.45 * math.sin(TAU * (m * PH + ph0))
        out += np.exp(-((Xs - cx) ** 2 + (Ss - cs) ** 2) / (sz * sz)) * k * r.uniform(0.4, 0.9)
    return out


def blade_coords(w, h, width=WR, s0=0.0, s1=LB):
    """칼 그림 칸 좌표: u = 로컬 +x (= 캔버스 -y) · v 0 = 칼끝 쪽 (위)"""
    u, v = grid(w, h)
    X = -(u - 0.5) * width
    S = s1 - v * (s1 - s0)
    return X, S


def nebula(w, h, seed, X, S):
    """성운 셋을 엇갈린 박자로 섞음 (합 = 1 · 숨 쉬듯 번짐) + 달 고리 우물로 빨려 드는 나선"""
    fs = []
    for k in range(3):
        a = smooth(h, w, 3, 12, seed + k * 7) * 0.6 + smooth(h, w, 7, 30, seed + k * 7 + 1) * 0.4
        b = smooth(h, w, 4, 16, seed + k * 7 + 2) * 0.55 + smooth(h, w, 9, 40, seed + k * 7 + 3) * 0.45
        wk = (1 + math.cos(TAU * (PH - k / 3))) / 3
        fs.append((a * wk, b * wk))
    A = sum(f[0] for f in fs); B = sum(f[1] for f in fs)
    r = np.hypot(X, S - SR) + 1e-3
    th = np.arctan2(X, S - SR)
    arm = 0.5 + 0.5 * np.sin(2 * th + 4.2 * np.log(r + 0.4) + TAU * PH)               # 나선 팔 (안으로 흘러 들어감)
    arm_w = np.exp(-(r / 7.5) ** 2)
    return A, B, arm, arm_w, r


# ---------------------------------------------------------------- 칸마다 그리는 그림
def r_void(w, h):
    """칼 속 (발광): 깊은 우주"""
    X, S = blade_coords(w, h)
    A, B, arm, arm_w, r = nebula(w, h, 11, X, S)
    de = sil_de(X, S)
    col = DEEP[None, None] * np.ones((h, w, 1))
    col = col + NAVY[None, None] * (0.25 + 0.55 * A)[..., None]
    col = col + BLUE[None, None] * (np.clip((A - 0.5) * 2.6, 0, 1) ** 1.5 * 0.65)[..., None]
    col = col + VIOL[None, None] * (np.clip((B - 0.52) * 2.6, 0, 1) ** 1.5 * 0.65)[..., None]
    fil = np.clip(1 - np.abs(A - B) * 9, 0, 1) ** 4                                      # 성운이 겹친 자리의 가는 실 (푸른 빛)
    col = col + CYAN[None, None] * (fil * 0.3)[..., None]
    col = col + (BLUE * 0.5 + CYAN * 0.5)[None, None] * (arm ** 4 * arm_w * 0.8)[..., None]
    lens = np.exp(-np.clip(r - RO, 0, None) / 1.1) * (r > RO)                             # 우물 둘레 밝음 (빛이 휨)
    col = col + np.array([80, 130, 255.0])[None, None] * (lens * 0.5)[..., None]
    deep = np.exp(-(np.clip(de, 0, None) / 0.28))                                        # 테 쪽 안쪽 빛 (가는 띠)
    col = col + np.array([110, 180, 255.0])[None, None] * (deep * 0.75)[..., None]
    st = stars_drift(w, h, 70, 21, X, S, swirl=1.0) + stars_static(w, h, 60, 22, X, S)
    col = col + PALE[None, None] * np.clip(st, 0, 1.3)[..., None]
    return rgba(col)


def r_veil(w, h):
    """겉 막 (더해 빛남): 빨려 드는 격자 고리 · 비틀린 열두 살 · 분 눈금 60 · 등을 타고 오르는 초침 빛 · 실루엣 밖은 검정"""
    X, S = blade_coords(w, h)
    de = sil_de(X, S)
    mask = np.clip(de / 0.12 + 0.5, 0, 1)
    r = np.hypot(X, S - SR) + 1e-3
    th = np.arctan2(X, S - SR)
    rw = r + 2.6 / (r + 0.5)                                                              # 휜 거리 (렌즈)
    f = (rw / 2.3 + PH) % 1.0                                                            # 고리가 우물 쪽으로 흘러 들어감
    rings = np.exp(-((f - 0.5) / 0.05) ** 2) * (0.16 + 0.5 * np.exp(-r / 5.0))
    tw = th + 2.2 / (r + 0.6) + TAU * PH / 12                                            # 열두 살 (한 바퀴에 한 칸씩 돎)
    sp = np.abs(((tw / (TAU / 12)) % 1.0) - 0.5) * (TAU / 12) * r
    spokes = np.exp(-(sp / 0.09) ** 2) * (0.12 + 0.4 * np.exp(-r / 4.0)) * np.clip(r / 1.5, 0, 1)
    k = rings + spokes
    col = (CYAN * 0.7 + PALE * 0.3)[None, None] * k[..., None]
    edge = hw(np.clip(S, 0, LB))                                                          # 가장자리 분 눈금 60 (금빛 · 5 분마다 길게)
    ticks = np.zeros_like(X)
    sk = np.linspace(1.2, LB - 2.2, 60)
    for i, s_ in enumerate(sk):
        if abs(s_ - SR) < RO + 0.4: continue
        L = 0.95 if i % 5 == 0 else 0.45
        wd = 0.1 if i % 5 == 0 else 0.07
        inband = np.clip((np.abs(X) - (edge - 0.18 - L)) / 0.08, 0, 1) * np.clip(((edge - 0.18) - np.abs(X)) / 0.08 + 1, 0, 1)
        ticks += np.exp(-((S - s_) / wd) ** 2) * inband * (1.0 if i % 5 == 0 else 0.7)
    col = col + WARM[None, None] * np.clip(ticks, 0, 1)[..., None] * 0.9
    spine = np.exp(-(X / 0.08) ** 2) * ((S > 1.0) & (np.abs(S - SR) > RO + 0.3) & (S < LB - 1.8))   # 등날 빛 + 오르는 초침 빛
    pulse = np.exp(-((((S / 12.5 - PH) % 1.0) - 0.5) / 0.045) ** 2)
    col = col + PALE[None, None] * (spine * (0.22 + 0.9 * pulse))[..., None]
    st = stars_drift(w, h, 26, 31, X, S, drift=(1.5, 4.0), size=(0.1, 0.22), bright=(0.6, 1.0), swirl=2.0)
    col = col + PALE[None, None] * np.clip(st, 0, 1)[..., None] * 0.6
    col = col * mask[..., None]
    return add_rgba(col)


def r_halo(w, h):
    """둘레 빛무리 (더해 빛남 · 칼 가운데 판): 테 밖으로 푸른 흰빛 → 보랏빛 (렌즈 무지갯빛) · 구멍 속 렌즈 빛"""
    X, S = blade_coords(w, h, WH, HS0, HS1)
    de = sil_de(X, S)
    do = np.clip(-de, 0, None)
    sh = 0.85 + 0.15 * np.sin(TAU * (2 * PH + S / 6.0) + X)
    g = (np.exp(-do / 0.55) * 0.8 + np.exp(-do / 2.0) * 0.32) * sh
    t = np.clip(do / 2.2, 0, 1)[..., None]
    col = (PALE * 0.5 + CYAN * 0.5)[None, None] * (1 - t) + VIOL[None, None] * t
    col = col * g[..., None]
    col = col + PALE[None, None] * (np.clip(de, 0, None) > 0)[..., None] * 0.4               # 칼 속 (가려짐 · 잔상 판에서는 보임)
    r = np.hypot(X, S - SR)
    hole = (r < RI) * np.exp(-(RI - r) / 0.45) * 0.9                                     # 구멍 속 렌즈 빛
    col = col + (CYAN * 0.6 + PALE * 0.4)[None, None] * hole[..., None]
    tip = np.exp(-(np.hypot(X, S - LB) / 1.6) ** 2) * (0.7 + 0.3 * math.sin(TAU * PH * 2))
    col = col + PALE[None, None] * tip[..., None] * 0.8
    return add_rgba(col)


def r_disk(w, h):
    """강착 원반 (더해 빛남): 속은 흰 금빛 → 금 → 푸름 · 결이 돎 (플립북) · 한쪽이 더 밝음"""
    u, v = grid(w, h)
    x, y = (u - 0.5) * 2, (v - 0.5) * 2
    r, a = np.hypot(x, y), np.arctan2(y, x)
    band = sstep(0.36, 0.46, r) * (1 - sstep(0.82, 1.0, r))
    q = np.clip((r - 0.4) / 0.55, 0, 1)
    col = np.array([255, 246, 220.0])[None, None] * (1 - sstep(0, 0.35, q))[..., None] + GOLD[None, None] * (sstep(0, 0.35, q) * (1 - sstep(0.4, 0.9, q)))[..., None] + np.array([80, 140, 255.0])[None, None] * sstep(0.4, 0.9, q)[..., None]
    streak = 0.65 + 0.35 * np.sin(5 * (a - TAU * PH) + 26 * r) * np.sin(3 * (a - TAU * PH) - 11 * r + 1.0)
    dop = 0.55 + 0.75 * (0.5 + 0.5 * np.cos(a - 0.4)) ** 2
    k = band * streak * dop
    return add_rgba(col * k[..., None] * 0.95)


def r_photon(w, h):
    """광자 고리 (더해 빛남): 검은 구를 두른 가는 흰 고리 + 속 렌즈 빛"""
    u, v = grid(w, h)
    x, y = (u - 0.5) * 2, (v - 0.5) * 2
    r, a = np.hypot(x, y), np.arctan2(y, x)
    fl = 0.85 + 0.15 * np.sin(3 * a + TAU * PH * 2)
    k = np.exp(-((r - 0.78) / 0.05) ** 2) * fl + np.exp(-((r - 0.86) / 0.14) ** 2) * 0.35 + (r < 0.72) * np.exp(-(0.72 - r) / 0.08) * 0.4
    k = k * (r < 1)
    col = PALE[None, None] * (0.6 + 0.4 * np.exp(-((r - 0.78) / 0.05) ** 2))[..., None] + CYAN[None, None] * 0.4
    return add_rgba(col * k[..., None])


def r_orbit(ph0):
    """궤도 고리 (더해 빛남): 가는 고리 + 고리를 따라 도는 빛 알갱이 둘"""
    def f(w, h):
        u, v = grid(w, h)
        x, y = (u - 0.5) * 2, (v - 0.5) * 2
        r, a = np.hypot(x, y), np.arctan2(y, x)
        ring = np.exp(-((r - 0.9) / 0.022) ** 2)
        k = ring * (0.35 + 0.15 * np.sin(12 * a))
        for off in (0.0, 0.5):
            da = np.angle(np.exp(1j * (a - TAU * (PH + ph0 + off))))
            k = k + np.exp(-(da / 0.09) ** 2 - ((r - 0.9) / 0.05) ** 2) * 1.2 + np.exp(-(np.clip(-da, 0, None) / 0.9) ** 2) * (da < 0) * ring * 0.8
        col = (CYAN * 0.55 + PALE * 0.45)[None, None] * np.ones((h, w, 1))
        return add_rgba(col * np.clip(k, 0, 1.4)[..., None])
    return f


def r_star(w, h):
    """칼끝 별 (더해 빛남): 네 갈래 + 가는 여덟 갈래 (한 바퀴에 45° 돎 · 대칭이라 이음매 없음)"""
    u, v = grid(w, h)
    x, y = (u - 0.5) * 2, (v - 0.5) * 2
    r, a = np.hypot(x, y), np.arctan2(y, x)
    a2 = a + TAU * PH / 8
    k = np.abs(np.cos(a * 2)) ** 30 * np.clip(1 - r, 0, 1) * 1.2 + np.abs(np.cos(a2 * 4)) ** 60 * np.clip(1 - r * 1.3, 0, 1) * 0.5 + np.exp(-(r / 0.14) ** 2) + 0.3 * np.exp(-(r / 0.45) ** 2)
    k = k * (0.8 + 0.2 * math.sin(TAU * PH * 3))
    t = np.exp(-(r / 0.25) ** 2)[..., None]
    col = CYAN[None, None] * (1 - t) + PALE[None, None] * t
    return add_rgba(col * np.clip(k, 0, 1.2)[..., None])


# ---------------------------------------------------------------- 로마 숫자 · 시계판 (데카르트 그림 → 극좌표 칸)
ROMAN = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]


def glyph_strokes(txt, gw, gh):
    """로마 숫자 획 (글자 가운데 0 · 위 +y · 폭 gw · 높이 gh): I = 세로 · V = 두 빗금 · X = 엇갈린 빗금 · 위아래 세리프 띠"""
    cw = {"I": 0.32, "V": 0.75, "X": 0.75}
    tot = sum(cw[c] for c in txt) + 0.12 * (len(txt) - 1)
    k = gw / tot
    x = -gw / 2
    out = []
    for c in txt:
        w_ = cw[c] * k
        x0, x1, xm = x, x + w_, x + w_ / 2
        if c == "I": out.append(((xm, -gh / 2), (xm, gh / 2)))
        elif c == "V": out += [((x0, gh / 2), (xm, -gh / 2)), ((x1, gh / 2), (xm, -gh / 2))]
        else: out += [((x0, gh / 2), (x1, -gh / 2)), ((x1, gh / 2), (x0, -gh / 2))]
        x = x1 + 0.12 * k
    out += [((-gw / 2 - 0.05 * gh, gh / 2), (gw / 2 + 0.05 * gh, gh / 2)), ((-gw / 2 - 0.05 * gh, -gh / 2), (gw / 2 + 0.05 * gh, -gh / 2))]
    return out


def numeral_img(N, half, rad, gh, width, ticks=None, rev=False, rot=0.0):
    """정사각 그림 (N px · 반폭 half px 캔버스): 반지름 rad 에 로마 숫자 열둘 (바깥을 향해 섬) · ticks = (반지름, 길이) 눈금 60
    rev = 뒤에서 보는 판 (좌우 뒤집음) · 값 = 0 ~ 1 세기"""
    S = 3
    im = Image.new("L", (N * S, N * S), 0)
    dr = ImageDraw.Draw(im)
    to = lambda x, y: ((x / half * 0.5 + 0.5) * N * S, (0.5 - y / half * 0.5) * N * S)
    for i, txt in enumerate(ROMAN):
        a = TAU * i / 12 + rot
        c = np.array([math.sin(a), math.cos(a)]) * rad
        ex, ey = np.array([math.cos(a), -math.sin(a)]), np.array([math.sin(a), math.cos(a)])
        for (p0, p1) in glyph_strokes(txt, gh * (0.42 + 0.17 * len(txt)), gh):
            q0 = c + ex * p0[0] + ey * p0[1]; q1 = c + ex * p1[0] + ey * p1[1]
            dr.line([to(*q0), to(*q1)], fill=255, width=max(1, int(width / half * 0.5 * N * S)))
    if ticks:
        tr, tl = ticks
        for i in range(60):
            a = TAU * i / 60 + rot
            L = tl * (1.8 if i % 5 == 0 else 1.0)
            e = np.array([math.sin(a), math.cos(a)])
            dr.line([to(*(e * tr)), to(*(e * (tr - L)))], fill=255 if i % 5 == 0 else 170, width=max(1, int(width * 0.7 / half * 0.5 * N * S)))
    im = im.resize((N, N), Image.LANCZOS)
    a = np.asarray(im, float) / 255
    return a[:, ::-1] if rev else a


def polar_sample(img_fn, w, h, radii, half, rev):
    """극좌표 칸 (u = 둘레 · v 0 = 바깥 고리 → 1 = 안 고리) 에 데카르트 그림을 옮김 — 판 앞 (rev=False) 에서 보면 오른쪽 = 캔버스 -y"""
    u, v = grid(w, h)
    ii = (1 - v) * (len(radii) - 1)
    r = np.interp(ii, np.arange(len(radii)), radii)
    th = u * TAU
    a, b = r * np.cos(th), r * np.sin(th)                                                # 판 좌표 (a = 캔버스 +y · b = 위 = -z)
    sx = -a if not rev else a                                                            # 화면 오른쪽
    return img_fn(sx, b)


def dial_fn(rev):
    """시계판 (발광): 남빛 에나멜 · 기요셰 (해살 + 동심 결) · 금 로마 숫자 · 금 눈금 · 가운데 푸른 보석"""
    half = RD
    num = numeral_img(320, half, RD * 0.66, RD * 0.2, 0.085, ticks=(RD * 0.83, RD * 0.07), rev=False)
    N = num.shape[0]

    def img(sx, sy):
        px = np.clip(((sx / half) * 0.5 + 0.5) * (N - 1), 0, N - 1).astype(int)
        py = np.clip((0.5 - (sy / half) * 0.5) * (N - 1), 0, N - 1).astype(int)
        g = num[py, px]
        r = np.hypot(sx, sy); a = np.arctan2(sx, sy)
        sun = 0.5 + 0.5 * np.cos(a * 48)
        conc = 0.5 + 0.5 * np.cos(r * 9.0)
        base = NAVY[None, None] * (0.85 + 0.25 * sun[..., None] * (r[..., None] / RD)) + BLUE[None, None] * (0.18 * conc[..., None])
        base = base * (1 - 0.35 * sstep(RD * 0.55, 0, r))[..., None] + np.array([30, 50, 140.0])[None, None] * sstep(RD * 0.5, 0, r)[..., None] * 0.6
        shine = np.exp(-((a - 0.7) / 0.45) ** 2) * 0.25                                   # 비스듬한 반사
        col = base * (1 + shine[..., None]) + GOLD[None, None] * g[..., None] * 0.95 * (1 - 0.95 * 0)
        col = col * (1 - g[..., None] * 0.05)
        col = col + (CYAN * 0.5)[None, None] * (np.exp(-(r / 0.35) ** 2) * 0.9)[..., None]
        return col

    def f(w, h):
        return rgba(polar_sample(img, w, h, DIAL_R, half, rev))
    return f


def r_numring(rev):
    """날밑 둘레를 도는 로마 숫자 고리 (더해 빛남)"""
    def f(w, h):
        g = numeral_img(w, NR_HALF, NR_R, 0.95, 0.11, ticks=(NR_R + 0.95, 0.28), rev=rev)
        u, v = grid(w, h)
        x, y = (u - 0.5) * 2 * NR_HALF, (v - 0.5) * 2 * NR_HALF
        r = np.hypot(x, y)
        ring = np.exp(-((r - (NR_R - 0.75)) / 0.05) ** 2) * 0.6 + np.exp(-((r - (NR_R + 1.05)) / 0.05) ** 2) * 0.6
        k = np.clip(g * 0.9 + ring, 0, 1) * (0.75 + 0.25 * math.sin(TAU * PH * 2))
        col = (WARM * 0.55 + CYAN * 0.45)[None, None] * np.ones((h, w, 1))
        return add_rgba(col * k[..., None] * 0.8)
    return f


def r_bezel(w, h):
    """달 고리 금 베젤 (u = 둘레 · v 0 = 바깥 → 1 = 안): 바깥 비탈 · 새긴 눈금 60 · 윤나는 안쪽 입술"""
    u, v = grid(w, h)
    q = v
    sh = 0.62 + 0.38 * np.cos(TAU * u - 0.9) * 0.5 + 0.2
    col = DGOLD[None, None] * (1 - q[..., None]) * 0.4 + GOLD[None, None] * (0.6 + 0.4 * q[..., None])
    col = col * sh[..., None]
    tk = ((np.abs(((u * 60) % 1.0) - 0.5) > 0.42) & (q > 0.3) & (q < 0.62))
    col = np.where(tk[..., None], col * 0.45, col)
    col = col + np.array([255, 250, 230.0])[None, None] * (np.exp(-((q - 0.9) / 0.06) ** 2) * 0.55)[..., None]
    col = col * (1 - 0.35 * np.exp(-((q - 0.05) / 0.06) ** 2))[..., None]
    return rgba(col)


def r_dialrim(w, h):
    """시계판 금 테 (u = 둘레 · v 0 = 바깥 → 1 = 안): 톱니 자국 · 구슬 줄"""
    u, v = grid(w, h)
    sh = 0.75 + 0.25 * np.cos(TAU * u - 0.6)
    col = GOLD[None, None] * (0.7 + 0.3 * np.sin(np.pi * v))[..., None] * sh[..., None]
    beads = np.exp(-((((u * 48) % 1.0) - 0.5) / 0.18) ** 2 - ((v - 0.5) / 0.22) ** 2)
    col = col * (0.75 + 0.35 * beads[..., None])
    return rgba(col)


def r_shard(w, h):
    """시공간 파편 (발광): 작은 우주 + 밝은 테"""
    u, v = grid(w, h)
    x, y = (u - 0.5) * 2, (v - 0.5) * 2
    n = smooth(h, w, 3, 5, 91 + FRM % 1) * 0.6 + smooth(h, w, 6, 10, 92) * 0.4
    col = DEEP[None, None] + NAVY[None, None] * (0.5 + n[..., None]) + VIOL[None, None] * np.clip((n - 0.55) * 2, 0, 1)[..., None] * 0.6
    edge = np.exp(-((1 - np.abs(x)) / 0.18) ** 2) + np.exp(-((1 - np.abs(y)) / 0.1) ** 2)
    col = col + (CYAN * 0.6 + PALE * 0.4)[None, None] * np.clip(edge, 0, 1)[..., None] * 0.9
    col = col + PALE[None, None] * (np.exp(-((x - 0.2) ** 2 + (y + 0.3) ** 2) / 0.01) * (0.6 + 0.4 * math.sin(TAU * PH * 2)))[..., None]
    return rgba(col)


def r_grip(w, h):
    """자루: 남빛 감은 천 (비스듬한 띠) · 띠마다 금실 점"""
    u, v = grid(w, h)
    ph = (v * 9 + u * 2) % 1.0
    band = np.sin(ph * np.pi) ** 0.6
    col = np.array([26, 36, 104.0])[None, None] * (0.45 + 0.7 * band[..., None])
    dot = np.exp(-(((ph - 0.5) / 0.1) ** 2 + ((((u * 4) % 1.0) - 0.5) / 0.1) ** 2))
    col = col * (1 - dot[..., None]) + GOLD[None, None] * dot[..., None]
    return rgba(col)


def m_flat(c, var=0.12, spec=0.0):
    def f(n, seed):
        k = smooth(n, n, 3, 3, seed)
        u, v = grid(n, n)
        col = np.array(c, float)[None, None] * (1 - var + 2 * var * k[..., None])
        col = col + spec * np.exp(-((v - 0.3) / 0.15) ** 2)[..., None]
        return rgba(col)
    return f


def m_glass(n, seed):
    u, v = grid(n, n)
    col = np.array([170, 210, 255.0])[None, None] * np.ones((n, n, 1)) + 60 * np.exp(-((u + v - 0.8) / 0.12) ** 2)[..., None]
    return rgba(col, np.full((n, n), 0.28))


# ---------------------------------------------------------------- 그림판 (칸마다 같은 자리 · 같은 순서)
class SubSheet(Sheet):
    """선반 채우기를 x0 에서 다시 시작 (키 큰 칸 셋을 왼쪽 기둥에 세우고 나머지를 오른쪽에)"""
    x0 = 0

    def alloc(self, w, h):
        if self.cx + w > self.W: self.cx, self.cy, self.rowh = self.x0, self.cy + self.rowh, 0
        assert self.cy + h <= self.H, "그림 칸이 모자라요"
        x, y = self.cx, self.cy
        self.cx += w; self.rowh = max(self.rowh, h)
        return x, y


DIAL_R = [0.05, 0.75, 1.45, 2.05, 2.55]                                                  # 시계판 동심 고리 (안 → 바깥)
NR_R, NR_HALF = 5.6, 7.4                                                                 # 숫자 고리 반지름 · 판 반폭


def paint(fr):
    global PH, FRM
    PH, FRM = fr / FR, fr
    sh = SubSheet(FW, FH, light=LIGHT)
    T = {}
    T["void"] = sh.region(r_void, 40, 200, glow=True, cells=1)                            # 왼쪽 기둥 (키 200)
    T["veil"] = sh.region(r_veil, 40, 200, glow=True, cells=1)
    T["halo"] = sh.region(r_halo, 64, 200, glow=True, cells=1)
    sh.x0, sh.rowh = sh.cx, 0                                                            # 이제부터 오른쪽 (x 144 ~)
    T["numf"] = sh.region(r_numring(False), 120, 120, glow=True, cells=1)
    T["disk"] = sh.region(r_disk, 64, 64, glow=True, cells=1)
    T["photon"] = sh.region(r_photon, 48, 48, glow=True, cells=1)
    T["orb0"] = sh.region(r_orbit(0.0), 64, 64, glow=True, cells=1)
    T["orb1"] = sh.region(r_orbit(0.37), 64, 64, glow=True, cells=1)
    T["star"] = sh.region(r_star, 40, 40, glow=True, cells=1)
    T["dialf"] = sh.region(dial_fn(False), 160, 32, glow=True, cells=1)
    T["dialb"] = sh.region(dial_fn(True), 160, 32, glow=True, cells=1)
    T["bezel"] = sh.region(r_bezel, 120, 12, cells=1)
    T["drim"] = sh.region(r_dialrim, 96, 8, cells=1)
    T["shard"] = sh.region(r_shard, 24, 40, glow=True, cells=1)
    T["grip"] = sh.region(r_grip, 16, 40)
    M = {}
    M["gold"] = sh.material(m_flat(GOLD, 0.1, 40), 16)
    M["dgold"] = sh.material(m_flat(DGOLD * 1.3, 0.12), 16)
    M["rim"] = sh.material(m_flat(np.array([150, 215, 255.0]), 0.08), 16, glow=True)
    M["gem"] = sh.material(m_flat(np.array([80, 170, 255.0]), 0.2, 60), 16, glow=True)
    M["black"] = sh.material(m_flat(np.array([4, 5, 12.0]), 0.3), 16, glow=True)
    M["sand"] = sh.material(m_flat(np.array([255, 214, 140.0]), 0.15, 30), 16, glow=True)
    M["glass"] = sh.material(m_glass, 16, glow=True)
    M["navy"] = sh.material(m_flat(np.array([22, 30, 84.0]), 0.15), 16)
    return sh, T, M


SH, T, M = paint(0)


# ---------------------------------------------------------------- 모양
R_FACE = basis(-Z_, X_)                                                                  # 칼 판: 로컬 y = 칼끝 · z = +x (넓은 면) · x = 캔버스 -y


def blade_strips(dz=0.3):
    """칼 몸: 가로줄 상자 (앞뒤 = 우주 그림 · 옆 = 테 빛) — 달 고리 자리는 금 베젤이 덮으므로 비움"""
    poly = blade_poly().difference(Point(SR, 0).buffer(RO - 0.12, 48))
    out = []
    n = int(math.ceil(LB / dz))
    for i in range(n):
        s0, s1 = i * dz, min(LB, (i + 1) * dz)
        cut = poly.intersection(sbox(s0, -10, s1, 10))
        if cut.is_empty: continue
        geoms = getattr(cut, "geoms", [cut])
        for g in geoms:
            if g.area < 1e-4: continue
            _, y0, _, y1 = g.bounds
            sm = (s0 + s1) / 2
            C = P(ZB - sm, (y0 + y1) / 2)
            u0, u1 = 0.5 - y1 / WR, 0.5 - y0 / WR
            v0, v1 = 1 - s1 / LB, 1 - s0 / LB
            face = SH.uv_reg(T["void"], 5, u0, u1, v0, v1)
            out.append(tbox(SH, C, R_FACE, (y1 - y0, s1 - s0, TH), M["rim"], 0, {"south": face, "north": face}))
    return out


def lathe_m(path, radii, n, m, th=0.1, caps=False, a0=0.0):
    """재질 하나로 칠한 돌린 관 (축 = 점 목록) · caps = 양 끝 막음"""
    path = [np.array(p_, float) for p_ in path]
    rings = []
    for i, Pp in enumerate(path):
        tg = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
        rings.append(ring_pts(Pp, tg, X_ if abs(nrm(tg)[0]) < 0.9 else Y_, radii[i], n, a0))
    out = []
    for i in range(len(rings) - 1):
        c_in = (path[i] + path[i + 1]) / 2
        for j in range(n):
            j2 = (j + 1) % n
            out.append(quad(SH, rings[i + 1][j], rings[i + 1][j2], rings[i][j], rings[i][j2], th, m, c_in, 0, 1.12, None))
    if caps:
        for i, sg in ((0, -1), (len(path) - 1, 1)):
            tg = nrm(path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]) * sg
            inner = [path[i] + (q - path[i]) * 0.04 for q in rings[i]]
            for j in range(n):
                j2 = (j + 1) % n
                out.append(quad(SH, rings[i][j], rings[i][j2], inner[j], inner[j2], th, m, path[i] - tg, 0, 1.15, None))
    return out


def annulus(C, r0, r1, nseg, reg, th, edge, sides=(1, -1), a0=0.0, rings=None):
    """판 고리 (칼 판과 같은 평면 · 앞뒤 두 겹): 그림 u = 둘레 · v 0 = 바깥"""
    rs = rings or [r0, r1]
    out = []
    for sg in sides:
        R = [ring_pts(C, X_, Y_, r, nseg, a0) for r in rs]
        out += loft(SH, R, th, reg, lambda i, sg=sg: C - X_ * sg, edge=edge, closed=True, over=1.06)
    return out


def disc_face(C, radii, nseg, reg, th, sg):
    R = [ring_pts(C, X_, Y_, r, nseg) for r in radii]
    return loft(SH, R, th, reg, lambda i: C - X_ * sg, edge=None, closed=True, over=1.08)


def star_rings(zs, ro, ri, n=2, a0=0.0, C=None):
    rings = []
    for z, a_, b_ in zip(zs, ro, ri):
        c = C(z)
        ring = []
        for k in range(2 * n):
            a = a0 + k * math.pi / n
            r = a_ if k % 2 == 0 else b_
            ring.append(c + np.array([math.cos(a), math.sin(a), 0]) * r)
        rings.append(ring)
    return rings


def crystal(C, d, L, wd, th, reg):
    """긴 마름모 결정 (축 d · 길이 L · 폭 wd · 두께 th)"""
    d = nrm(d)
    R = basis(d, X_)
    e1, e2 = R[:, 0], R[:, 2]
    zs = np.linspace(-L / 2, L / 2, 5)
    prof = [0.05, 0.75, 1.0, 0.6, 0.05]
    rings = []
    for z, k in zip(zs, prof):
        c = C + d * z
        rings.append([c + e1 * wd * k, c + e2 * th * k, c - e1 * wd * k, c - e2 * th * k])
    return loft(SH, rings, 0.06, reg, lambda i: C, edge=None, closed=True, over=1.1)


def build(prefix):
    Pn = lambda n: f"{prefix}_{n}"
    bones = [{"name": prefix, "parent": "root", "pivot": [CX, CY, 0.0]}]

    def add(name, parent, pivot, cubes=None, rot=None):
        b = {"name": Pn(name), "parent": parent if parent in ("root", prefix) else Pn(parent), "pivot": [R3(v) for v in pivot]}
        if rot is not None: b["rotation"] = [R3(v) for v in rot]
        if cubes: b["cubes"] = cubes
        bones.append(b)

    add("g", prefix, H)
    # ---- 칼날
    add("blade", "g", P(ZB))
    add("void", "blade", P(ZB), blade_strips())
    mid = P(ZB - LB / 2)
    add("veil_add", "blade", P(ZB), [card(SH, mid + X_ * (TH / 2 + 0.06), R_FACE, WR, LB, 0.02, T["veil"], back=False),
                                     card(SH, mid - X_ * (TH / 2 + 0.06), basis(-Z_, -X_), WR, LB, 0.02, T["veil"], back=False)])
    add("halo_add", "blade", P(ZB), [card(SH, P(ZB - (HS0 + HS1) / 2), R_FACE, WH, HS1 - HS0, 0.02, T["halo"], back=True)])
    # 칼 뿌리를 쥔 금 발톱 (양 날 · 앞뒤)
    claw = []
    for sg in (1, -1):
        pts = [(1.2, 2.6), (2.6, 2.95), (4.2, 2.75), (5.6, 2.3), (6.4, 1.7)]
        for (s_a, y_a), (s_b, y_b) in zip(pts[:-1], pts[1:]):
            claw.append(seg(SH, P(ZB - s_a, sg * y_a), P(ZB - s_b, sg * y_b), 0.75, TH + 0.5, M["gold"], z_hint=X_))
        claw.append(tbox(SH, P(ZB - 6.6, sg * 1.55), basis(-Z_, X_), (0.55, 0.55, TH + 0.7), M["gem"]))
    add("claw", "blade", P(ZB), claw)
    # ---- 달 고리: 금 베젤 · 블랙홀
    Cm = P(ZR)
    add("moon", "blade", Cm, annulus(Cm, RI, RO, 32, T["bezel"], 0.5, M["dgold"], rings=[RI, RI + 0.45, RO - 0.4, RO]))
    hole = lathe_m([Cm - X_ * 1.0, Cm - X_ * 0.7, Cm, Cm + X_ * 0.7, Cm + X_ * 1.0], [0.05, 0.72, 1.0, 0.72, 0.05], 10, M["black"])
    add("bh", "moon", Cm, hole)
    add("photon_add", "moon", Cm, [card(SH, Cm, R_FACE, 2.9, 2.9, 0.02, T["photon"], back=True)])
    nd = nrm(X_ * math.cos(math.radians(74)) - Z_ * math.sin(math.radians(74)))           # 강착 원반 법선 (거의 칼 축 쪽으로 누움)
    add("disk_add", "moon", Cm, [card(SH, Cm, basis(nrm(np.cross(nd, Y_)), nd), 5.0, 5.0, 0.02, T["disk"], back=True)])
    for k, (tilt, az) in enumerate(((58, 20), (-58, -35))):                               # 궤도 고리 둘 (달 고리를 감돎)
        add(f"orbit{k}", "moon", Cm, rot=[0, 0, az])
        n_ = nrm(X_ * math.cos(math.radians(tilt)) + Y_ * math.sin(math.radians(tilt)))
        add(f"orb{k}_add", f"orbit{k}", Cm, [card(SH, Cm, basis(nrm(np.cross(n_, Z_)), n_), 9.6, 9.6, 0.02, T[f"orb{k}"], back=True)])
    add("tip_add", "blade", P(ZT), [card(SH, P(ZT + 0.2), basis(-Z_, nrm(X_ + Y_ * a)), 6.0, 6.0, 0.02, T["star"], back=True) for a in (0.6, -0.6)])
    # ---- 시공간 파편 (칼 곁을 떠돎)
    rng = np.random.default_rng(37)
    for k in range(6):
        s_ = 7 + k * 4.6 + rng.uniform(-1, 1)
        sg = 1 if k % 2 == 0 else -1
        c = P(ZB - s_, sg * (hw(min(s_, LB - 1)) + 2.2 + rng.uniform(0, 1.2)), rng.uniform(-1.0, 1.0))
        d = nrm(-Z_ + Y_ * rng.uniform(-0.6, 0.6) + X_ * rng.uniform(-0.4, 0.4))
        add(f"sh{k}", "g", c, crystal(c, d, rng.uniform(1.5, 2.4), rng.uniform(0.35, 0.55), 0.18, T["shard"]))
    # ---- 날밑: 시계판
    Cd = P(ZD)
    add("guard", "g", Cd)
    dial = disc_face(Cd + X_ * 0.0, DIAL_R, 24, T["dialf"], 0.55, 1) + disc_face(Cd, DIAL_R, 24, T["dialb"], 0.55, -1)
    dial += annulus(Cd, DIAL_R[-1] - 0.02, RD, 24, T["drim"], 0.75, M["gold"])
    for i in range(24):                                                                   # 금 톱니
        a = TAU * (i + 0.5) / 24
        e = Y_ * math.cos(a) - Z_ * math.sin(a)
        dial.append(tbox(SH, Cd + e * (RD + 0.22), basis(e, X_), (0.5, 0.5, 1.2), M["gold"]))
    add("dial", "guard", Cd, dial)
    for side in (1, -1):                                                                  # 시곗바늘 (앞뒤 · 판 위에서 돎)
        o = Cd + X_ * side * 0.62
        add(f"hh{'f' if side > 0 else 'b'}", "guard", o, [seg(SH, o - Z_ * 0.2 * -1, o - Z_ * 1.55, 0.34, 0.12, M["gold"], z_hint=X_),
                                                          tbox(SH, o - Z_ * 1.25, basis(-Z_, X_), (0.62, 0.5, 0.12), M["gold"], 0, None)])
        add(f"mh{'f' if side > 0 else 'b'}", "guard", o, [seg(SH, o + Z_ * 0.35, o - Z_ * 2.25, 0.2, 0.1, M["gold"], z_hint=X_)])
        add(f"cap{'f' if side > 0 else 'b'}", "guard", o, [tbox(SH, o + X_ * side * 0.06, basis(-Z_, X_), (0.5, 0.5, 0.18), M["gem"])])
    add("num", "guard", Cd)
    add("num_add", "num", Cd, [card(SH, Cd + X_ * 0.95, R_FACE, NR_HALF * 2, NR_HALF * 2, 0.02, T["numf"], back=False),
                               card(SH, Cd - X_ * 0.95, basis(-Z_, -X_), NR_HALF * 2, NR_HALF * 2, 0.02, T["numf"], back=False)])
    # 양옆 금빛 갈고리 (시계판 3 · 9 시에서 뻗어 칼끝 쪽으로 휨 · 끝 푸른 보석)
    hook = []
    for sg in (1, -1):
        pts = [(ZD - 0.1, 2.9), (ZD - 0.7, 4.2), (ZD - 1.7, 5.15), (ZD - 3.0, 5.5), (ZD - 4.3, 5.2), (ZD - 5.2, 4.55), (ZD - 5.6, 3.85)]
        for i, ((za, ya), (zb, yb)) in enumerate(zip(pts[:-1], pts[1:])):
            w_ = 1.25 - 0.14 * i
            hook.append(seg(SH, P(za, sg * ya), P(zb, sg * yb), w_, 0.7, M["gold"], z_hint=X_))
            if i in (1, 3): hook.append(seg(SH, P(za, sg * (ya + 0.35)), P(zb, sg * (yb + 0.35)), 0.18, 0.85, M["dgold"], z_hint=X_))
        hook += loft(SH, star_rings([ZD - 5.3, ZD - 5.9, ZD - 6.6], [0.12, 0.55, 0.06], [0.1, 0.4, 0.05], 2, math.pi / 2, C=lambda z, sg=sg: P(z, sg * 3.75)), 0.12, T["shard"], lambda i, sg=sg: P(ZD - 5.9, sg * 3.75))
    add("hook", "guard", Cd, hook)
    # ---- 자루 · 모래시계
    zs = np.linspace(GZ0, GZ1, 7)
    grip = lathe(SH, [P(z) for z in zs], [0.78 + 0.05 * math.sin(math.pi * i / 6) for i in range(7)], X_, 8, 0.2, T["grip"], edge=M["navy"])
    for z, r in ((GZ0 + 0.15, 0.98), (GZ1 - 0.1, 0.98), ((GZ0 + GZ1) / 2, 0.88)):
        grip += lathe_m([P(z - 0.25), P(z + 0.25)], [r, r], 8, M["gold"], 0.2, caps=True)
    n = 26
    pts = [P(GZ0 + 0.4 + (GZ1 - GZ0 - 0.8) * t_) + (Y_ * math.cos(t_ * 15.7) + X_ * math.sin(t_ * 15.7)) * 0.84 for t_ in np.linspace(0, 1, n)]
    grip += [seg(SH, pts[i], pts[i + 1], 0.16, 0.16, M["gold"], z_hint=Z_) for i in range(n - 1)]
    add("grip", "g", H, grip)
    hgc = (HG0 + HG1) / 2
    pom = lathe_m([P(HG0), P(HG0 + 0.4)], [1.3, 1.3], 10, M["gold"], 0.2, caps=True) + lathe_m([P(HG1 - 0.4), P(HG1)], [1.3, 1.3], 10, M["gold"], 0.2, caps=True)
    pom += lathe_m([P(HG0 + 0.4), P(HG0 + 0.62)], [1.0, 1.0], 10, M["dgold"], 0.15, caps=True) + lathe_m([P(HG1 - 0.62), P(HG1 - 0.4)], [1.0, 1.0], 10, M["dgold"], 0.15, caps=True)
    for k in range(3):
        a = TAU * k / 3 + 0.5
        o = (Y_ * math.cos(a) + X_ * math.sin(a)) * 1.05
        pom.append(seg(SH, P(HG0 + 0.3) + o, P(HG1 - 0.3) + o, 0.22, 0.22, M["gold"], z_hint=Z_))
    pom += loft(SH, star_rings([HG1 + 0.1, HG1 + 0.6, HG1 + 1.3], [0.35, 0.6, 0.05], [0.3, 0.5, 0.05], 2, 0.0, C=lambda z: P(z)), 0.12, T["shard"], lambda i: P(HG1 + 0.6))
    add("pommel", "g", P(hgc), pom)
    gl = lathe_m([P(z) for z in np.linspace(HG0 + 0.62, HG1 - 0.62, 9)], [0.3, 0.8, 0.86, 0.5, 0.16, 0.5, 0.86, 0.8, 0.3], 8, M["glass"], 0.05)
    add("bulb_glass", "pommel", P(hgc), gl)
    add("sandt", "pommel", P(hgc - 0.1), lathe_m([P(HG0 + 1.3), P(HG0 + 1.75), P(hgc - 0.25)], [0.62, 0.45, 0.1], 6, M["sand"], 0.05, caps=True))
    add("sandb", "pommel", P(HG1 - 0.65), lathe_m([P(hgc + 0.7), P(HG1 - 1.1), P(HG1 - 0.68)], [0.08, 0.5, 0.7], 6, M["sand"], 0.05, caps=True))
    add("stream", "pommel", P(hgc), [seg(SH, P(hgc - 0.25), P(hgc + 0.75), 0.07, 0.07, M["sand"], z_hint=X_)])
    # ---- 시간의 잔상 (휘두를 때만 · 늦게 따라옴)
    for k in range(2):
        add(f"echo{k}", prefix, H)
        add(f"echo{k}_add", f"echo{k}", P(ZB), [card(SH, P(ZB - (HS0 + HS1) / 2), R_FACE, WH, HS1 - HS0, 0.02, T["halo"], back=True)])
    return bones


# ---------------------------------------------------------------- 애니
FP_ROOT = {"scale": tri(0.5), "rotation": [-74, -4, -150], "position": [9, 10.5, 1]}
TP_S = 0.55


def anims():
    out = {}
    t = "q.anim_time"
    form = f"math.clamp(({t} - 0.02)/0.4, 0, 1)"                                          # 손에 쥘 때 칼날이 시계판에서 펼쳐짐
    ease = f"(1 - math.pow(1 - {form}, 3))"
    ch = f"math.clamp(({EL} - 0.35)/3.0, 0, 1)"                                           # 꾹: 시간 압축 (0 ~ 1)
    for pre in ("fp", "tp"):
        b = {}
        if pre == "fp":
            b["fp"] = FP_ROOT
            b["tp"] = {"scale": [0, 0, 0]}
        else:
            b["fp"] = {"scale": [0, 0, 0]}
            root, _ = tp_hold(TP_S, spin_bone=False)
            b["tp"] = root
        b[f"{pre}_blade"] = {"scale": [f"0.2 + 0.8*{ease}", f"0.2 + 0.8*{ease}", f"math.max(0.02, {ease})"]}
        b[f"{pre}_halo_add"] = {"scale": [f"1 + math.sin({t}*230)*0.05", 1, f"1 + math.sin({t}*170)*0.02"]}
        b[f"{pre}_photon_add"] = {"scale": tri(f"1 + math.sin({t}*400)*0.06")}
        b[f"{pre}_disk_add"] = {"scale": tri(f"1 + math.sin({t}*150)*0.04")}
        for k in range(2):
            b[f"{pre}_orbit{k}"] = {"rotation": [0, 0, f"{t}*{(1 if k == 0 else -1) * (38 + 12 * k)}"]}
        b[f"{pre}_tip_add"] = {"rotation": [0, 0, f"{t}*35"], "scale": tri(f"0.85 + math.sin({t}*500)*0.15")}
        b[f"{pre}_num"] = {"rotation": [f"-{t}*14", 0, 0]}                                  # 숫자 고리는 거꾸로 돎
        b[f"{pre}_hhf"] = {"rotation": [f"{t}*7.5", 0, 0]}; b[f"{pre}_hhb"] = {"rotation": [f"{t}*7.5", 0, 0]}
        b[f"{pre}_mhf"] = {"rotation": [f"{t}*90", 0, 0]}; b[f"{pre}_mhb"] = {"rotation": [f"{t}*90", 0, 0]}
        b[f"{pre}_stream"] = {"scale": [f"0.7 + math.sin({t}*900)*0.3", f"0.7 + math.sin({t}*900)*0.3", 1]}
        b[f"{pre}_sandt"] = {"scale": [1, 1, f"1 - math.mod({t}, 20)/20*0.7"]}
        b[f"{pre}_sandb"] = {"scale": [1, 1, f"0.3 + math.mod({t}, 20)/20*0.7"]}
        for k in range(6):                                                                # 파편: 저마다 박자로 떠돎 · 돎
            sp = 60 + 17 * k
            b[f"{pre}_sh{k}"] = {"position": [f"math.sin({t}*{sp} + {k * 70})*0.7", f"math.cos({t}*{sp * 0.8:.1f} + {k * 50})*0.9", f"math.sin({t}*{sp * 0.6:.1f} + {k * 90})*1.1"],
                                 "rotation": [f"{t}*{40 + 9 * k}", f"math.sin({t}*{sp} + {k * 40})*25", 0],
                                 "scale": tri(ease)}
        for k in range(2): b[f"{pre}_echo{k}"] = {"scale": [0, 0, 0]}
        out[f"animation.vh.{NAME}.{pre}"] = {"loop": True, "animation_length": 3600, "bones": b}
        a = "math.clamp(v.attack_time, 0, 1)"
        sw = lambda ph: [f"-math.sin(math.clamp({a} - {ph}, 0, 1)*180)*70", f"math.sin(math.clamp({a} - {ph}, 0, 1)*180)*20", f"math.sin(math.clamp({a} - {ph}, 0, 1)*360)*16"]
        atk = {f"{pre}_g": {"rotation": sw(0)}, f"{pre}_halo_add": {"scale": tri(f"1 + math.sin({a}*180)*0.45")}}
        for k in range(2):                                                                # 잔상 = 같은 휘두름을 늦게 · 휘두르는 동안만
            atk[f"{pre}_echo{k}"] = {"rotation": sw(0.12 * (k + 1)), "scale": tri(f"math.clamp(math.sin({a}*180)*2.5, 0, 1)*{0.95 - 0.12 * k}")}
        out[f"animation.vh.{NAME}.{pre}_atk"] = {"loop": True, "bones": atk}
        out[f"animation.vh.{NAME}.{pre}_use"] = {"loop": True, "bones": {                 # 꾹: 시간이 압축됨 (바늘이 빨리 돎 · 숫자 고리가 커지며 빨라짐 · 파편이 칼로 모임 · 빛무리 · 블랙홀이 커짐)
            f"{pre}_g": {"rotation": [f"math.sin({EL}*1400)*0.8*{ch}", 0, 0]},
            f"{pre}_num": {"rotation": [f"-{EL}*(14 + 260*{ch})", 0, 0], "scale": tri(f"1 + 0.45*{ch}")},
            f"{pre}_mhf": {"rotation": [f"{EL}*(90 + 1800*{ch})", 0, 0]}, f"{pre}_mhb": {"rotation": [f"{EL}*(90 + 1800*{ch})", 0, 0]},
            f"{pre}_hhf": {"rotation": [f"{EL}*(8 + 150*{ch})", 0, 0]}, f"{pre}_hhb": {"rotation": [f"{EL}*(8 + 150*{ch})", 0, 0]},
            f"{pre}_halo_add": {"scale": [f"1 + 0.6*{ch}", 1, f"1 + 0.05*{ch}"]},
            f"{pre}_disk_add": {"scale": tri(f"1 + 0.5*{ch}")}, f"{pre}_photon_add": {"scale": tri(f"1 + 0.4*{ch}")},
            f"{pre}_orbit0": {"rotation": [0, 0, f"{EL}*(38 + 400*{ch})"]}, f"{pre}_orbit1": {"rotation": [0, 0, f"-{EL}*(50 + 400*{ch})"]},
            **{f"{pre}_sh{k}": {"scale": tri(f"1 - 0.55*{ch}")} for k in range(6)}}}
    return out


def player_anims():
    F_ = "(v.is_first_person ? 0 : 1)"
    hold = lambda r, ex=("", "", ""): [f"v.is_first_person ? 0 : ({r[i]}{ex[i]} - this)" for i in range(3)]
    key = lambda *pairs: {f"{tt:.2f}": [f"({v})*{F_}" for v in r] for tt, r in pairs}
    t = "q.anim_time"
    return {
        f"animation.vh.{NAME}.slash_a": {"animation_length": 0.4, "bones": {              # 탭 (홀수): 오른 위에서 왼 아래로 비스듬히
            "rightArm": {"rotation": key((0, (-150, -30, 20)), (0.1, (-40, 40, -10)), (0.4, (0, 0, 0)))},
            "body": {"rotation": key((0, (0, -12, 0)), (0.1, (0, 14, 0)), (0.4, (0, 0, 0)))}}},
        f"animation.vh.{NAME}.slash_b": {"animation_length": 0.4, "bones": {              # 탭 (짝수): 되받아 가로로
            "rightArm": {"rotation": key((0, (-85, 60, 0)), (0.1, (-85, -60, 0)), (0.4, (0, 0, 0)))},
            "body": {"rotation": key((0, (0, 18, 0)), (0.1, (0, -18, 0)), (0.4, (0, 0, 0)))}}},
        f"animation.vh.{NAME}.draw": {"loop": True, "bones": {                            # 꾹: 발도 자세 (칼을 왼 허리로 낮게 당기고 몸을 비틂)
            "rightArm": {"rotation": hold([-35, 55, 10], (f" + math.sin({t}*120)*1.5", "", ""))},
            "leftArm": {"rotation": hold([-30, -25, 0])},
            "body": {"rotation": hold([0, 28, 0])}}},
        f"animation.vh.{NAME}.iai": {"animation_length": 0.5, "bones": {                  # 놓으면 일섬 (가로로 크게 뽑아 벰)
            "rightArm": {"rotation": key((0, (-35, 55, 10)), (0.08, (-90, -80, 0)), (0.5, (0, 0, 0)))},
            "body": {"rotation": key((0, (0, 28, 0)), (0.08, (0, -25, 0)), (0.5, (0, 0, 0)))}}},
        f"animation.vh.{NAME}.sever": {"animation_length": 3.0, "bones": {                # 웅크리고: 칼을 하늘로 들어 시간을 멈추고 (멈춘 세계를 일곱 번 가름) → 2.6 초에 내리그음
            "rightArm": {"rotation": key((0, (0, 0, 0)), (0.3, (-178, 0, 0)), (2.45, (-178, 0, 0)), (2.6, (-35, 0, 0)), (3.0, (0, 0, 0)))},
            "leftArm": {"rotation": key((0, (0, 0, 0)), (0.3, (-60, 30, -30)), (2.45, (-60, 30, -30)), (3.0, (0, 0, 0)))},
            "head": {"rotation": key((0, (0, 0, 0)), (0.3, (-25, 0, 0)), (2.45, (-25, 0, 0)), (2.62, (10, 0, 0)), (3.0, (0, 0, 0)))}}},
    }


def write_files():
    att_p = os.path.join(RP, f"attachables/vh_{NAME}.json")
    att = json.load(open(att_p))
    A = att["minecraft:attachable"]["description"]
    A["materials"] = {"default": "entity_emissive_alpha", "glass": "entity_alphablend", "add": "entity_beam_additive"}
    A["textures"] = {"default": f"textures/models/vh/{NAME}"}
    A["render_controllers"] = ["controller.render.vh_crb"]
    json.dump(att, open(att_p, "w"), indent=1)
    rc = {"format_version": "1.10.0", "render_controllers": {"controller.render.vh_crb": {
        "geometry": "Geometry.default",
        "materials": [{"*": "Material.default"}, {"*_glass": "Material.glass"}, {"*_add": "Material.add"}],
        "textures": ["Texture.default"],
        "uv_anim": {"offset": [0, f"math.mod(math.floor(q.life_time * {FPS}), {FR}) / {FR}"], "scale": [1, 1]}}}}
    json.dump(rc, open(os.path.join(RP, "render_controllers/vh_crb.render_controllers.json"), "w"), indent=1)
    json.dump({"format_version": "1.10.0", "animations": player_anims()}, open(os.path.join(RP, f"animations/vh_{NAME}_player.animation.json"), "w"), indent=1)


def icon():
    """아이콘: 검은 바탕 위에 그린 뒤 밝기를 알파로 (빛나는 칼 · 블랙홀은 짙은 남빛으로 남김)"""
    sys.path.insert(0, os.path.join(ROOT, "tools", "preview"))
    os.environ["VH_TEX"], os.environ["VH_TEXMAX"], os.environ["ZCULL"] = "1", "96", "-1"
    import importlib, render_geo
    importlib.reload(render_geo)
    from render_geo import load_geo, Atlas, atlas_for, collect_faces
    from zbuf import zrender
    import pose_preview
    gp = os.path.join(RP, f"models/entity/vh_{NAME}.geo.json")
    geo, at = load_geo(gp), Atlas(atlas_for(gp))
    A_ = json.load(open(os.path.join(RP, f"animations/vh_{NAME}.animation.json")))["animations"]
    pose = pose_preview.pose_from(A_, [f"animation.vh.{NAME}.fp"], {"t": 2.0})
    pose = {k: v for k, v in pose.items() if not k.startswith("fp") or k.startswith("fp_")}
    fs = collect_faces(geo, at, pose, hide=("tp", "fp_num_add", "fp_echo0_add", "fp_echo1_add", "fp_orb0_add", "fp_orb1_add"))
    UP = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0.0]])
    fs = [((np.asarray(p) - [CX, CY, -15]) @ UP.T, c, g) for p, c, g in fs]
    im = zrender(fs, 90, 0, 1024, scale=1024 * 0.95 / 54, center=np.zeros(3), bg=(0, 0, 0, 255))
    a = np.asarray(im.convert("RGB")).astype(float)
    k = np.clip(a.max(-1) / 255 * 6, 0, 1)
    rgb = np.clip(a / np.maximum(k[..., None], 1e-3), 0, 255)
    im = Image.fromarray(np.dstack([rgb, k * 255]).astype(np.uint8), "RGBA").rotate(-45, resample=Image.BICUBIC, expand=True)
    im = im.crop(im.getbbox())
    kk = 250 / max(im.size)
    im = im.resize((max(1, int(im.width * kk)), max(1, int(im.height * kk))), Image.LANCZOS)
    out = Image.new("RGBA", (256, 256)); out.alpha_composite(im, ((256 - im.width) // 2, (256 - im.height) // 2))
    out.save(os.path.join(RP, f"textures/items/vh/{NAME}.png"))
    print("  아이콘 저장")


def main():
    fp, tp = build("fp"), build("tp")
    frames = [SH.img] + [paint(f)[0].img for f in range(1, FR)]
    strip = np.concatenate(frames, axis=0)
    Image.fromarray(np.clip(strip, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(RP, f"textures/models/vh/{NAME}.png"))
    root = {"name": "root", "pivot": [CX, CY, 0.0], "binding": "q.item_slot_to_bone_name(c.item_slot)"}
    write_geo(NAME, [root] + fp + tp, vb=(10, 10, 1), tex=(FW, FH * FR))
    write_anims(NAME, anims())
    write_files()
    print(f"{NAME}: bones {len(fp)} / cubes {sum(len(b.get('cubes', [])) for b in fp)} per view · 플립북 {FW}x{FH} x {FR}칸 · 그림판 끝 y={SH.cy + SH.rowh}")


if __name__ == "__main__":
    main()
    if "--icon" in sys.argv:
        icon()
