"""보스 「시간의 여신」 (vh:boss_chrono) 생성기 — 소환 「멈춘 회중시계」 (vh:stopped_clock) · 파티클 vh:tgd_* (tools/gen_chrono_particles.py)
사용자 그림 (별빛 속에 떠 있는 시간의 여신 · 가시 돋은 금빛 톱니 고리 · 모래시계 · 흰 망토 꼬리 끝의 금빛 투조 진자 · 금빛 기운) 을 따라:
  - 몸 = 짙은 남빛 살갗 (그림의 푸른 살갗 · 다리) · 흰 가슴옷 · 금빛 어깨 갑 · 목 깃 · 허리띠 · 팔찌 · 무릎 · 뾰족한 발끝 (모두 둥근 관 `tube` · 요정 여왕과 같은 도구)
    · 자세 = 그림처럼 떠서 한 다리는 곧게 발끝을 세우고 (발밑 작은 톱니 고리) 한 다리는 무릎을 굽힘 · 한 팔은 높이 들어 손 위의 혼천의를 · 한 팔은 아래로
  - 얼굴 = 시공간이 일그러지는 둥근 구체 ("얼굴은 시공간이 일그러지는 둥근느낌으로 가리고"): 유리 구체 (굽은 시공간 격자) 속에
    · 빨려 드는 시계 눈금 나선 · 휘어진 빛 고리 (중력 렌즈) · 사건의 지평선 · 거꾸로 도는 두 나선 · 구체를 감도는 궤도 고리 둘
  - 그림의 초록 부분 = 영롱한 푸른빛 ("초록색 부분은 영롱한 푸른빛으로"): 긴 머리 (짙은 사파이어 → 하늘빛 끝 · 결 · 윤기 띠 + 더해 빛나는 겉 결) ·
    망토 꼬리 끝 (흰색 → 푸른빛 · 더해 빛남) · 가슴 보석 · 혼천의 구슬
  - 금빛 톱니 고리: 머리 뒤 큰 후광 (가시 · 톱니 · 사슬 고리 · 눈금 = 잘라 그린 판 + 입체 띠 · 가시) · 허리를 비스듬히 감은 큰 고리 · 발밑 고리 · 떠 있는 모래시계 혼천의
  - 흰 망토 = 어깨에서 갈라져 양옆 · 아래로 흐르는 여덟 꼬리 (마디마다 흔들림) · 끝마다 금빛 투조 진자 (잘라 그림) + 작은 톱니
  - 허리 앞 흰 자락 둘 · 허리 고리에 매달린 모래시계 장식 · 몸 둘레를 감도는 금빛 기운 띠 셋 · 반짝이는 별
  - 2·3 페이즈 (`vh:phase`) = 거꾸로 도는 푸른 시계판 후광이 펼쳐짐 · 고리가 빨리 돎 · 꼬리 끝이 더 밝게
층: default 하나 (늘 밝음 · *_add 더해 빛남 · *_glass 유리 · *_cut 잘라 그림) · 앞 = -z · 그림의 오른쪽 = 모델 +x
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import boss_kit as BK
import ysm_kit as Y
import tex_kit
from ysm_kit import C, sstep, vnoise, fbm, nrm, Mat
from body_kit import Fig, tube, limb, bez, sparkle, flat_add, soft_add, translate_bones

NAME = "boss_chrono"
SCALE = 1.5                                                                               # 전체 크기 (v1.233 "전체 크기 1.5배") — 쉬는 애니의 base 크기
X_, Y_, Z_ = np.eye(3)
TAU = 2 * math.pi
LIGHT = nrm(np.array([0.35, 0.75, -0.55]))


def mix(a, b, t):
    """a → b (t 는 이미 색 축이 붙은 모양 · ysm_kit.mix 와 달리 축을 더 붙이지 않음)"""
    return a * (1 - t) + b * t


def lam(N): return float(np.clip(np.dot(N, LIGHT), -1, 1))
def shade(N, lo=0.62, hi=0.46): return lo + hi * max(0.0, lam(N))


def _q(P, k=1.0, seed=0.0):
    return P * k + seed


def _pol(S, T):
    u, v = (S - 0.5) * 2, (T - 0.5) * 2
    return u, v, np.hypot(u, v), np.arctan2(v, u)


def _fm(fn, edge=1.0, top=1.0, bot=1.0):
    return Mat(fn, edge=edge, top=top, bot=bot)


# ================================================================= 재질
def suit_fn(P, N, S, T):
    """남빛 살갗 (그림의 푸른 피부 · 다리): 짙은 남색 · 빛 쪽은 푸르게 · 윤기 · 옅은 결"""
    n = fbm(_q(P, 0.35), 1.0, 11)
    k = shade(N, 0.55, 0.6)
    c = mix(C(14, 22, 58)[None, None], C(46, 74, 150)[None, None], np.clip(k - 0.45, 0, 1)[..., None] * np.ones_like(S)[..., None] * 1.6)
    c = c * (0.86 + 0.28 * n)[..., None]
    rim = sstep(0.55, 0.95, 1 - abs(float(N[2])))                                          # 옆면 = 푸른 테
    c = c + C(30, 80, 170)[None, None] * (rim * 0.35 * sstep(0.4, 0.7, n))[..., None]
    gl = sstep(0.62, 0.8, fbm(_q(P, np.array([0.25, 0.9, 0.25])), 1.0, 13)) * max(0.0, lam(N))   # 길게 흐르는 윤기
    return np.clip(c + C(120, 170, 255)[None, None] * (gl * 0.4)[..., None], 0, 255)


SUIT = _fm(suit_fn, top=1.05, bot=0.8)


def inner_fn(P, N, S, T):
    """코르셋 · 열린 앞섶 속 (현자 지식의 신처럼 겹친 옷): 짙은 남색 비단 · 금빛 덩굴 투조 무늬 · 가는 세로 결"""
    c = suit_fn(P, N, S, T) * 0.85
    x, y = P[..., 0], P[..., 1]
    vine = np.abs(np.sin(y * 1.3 + np.sin(x * 2.6) * 1.6)) < 0.09
    curl = np.abs(np.hypot((x % 1.6) - 0.8, (y % 1.8) - 0.9) - 0.45) < 0.07
    m = (vine | curl)
    g = _gold_px(shade(N, 0.7, 0.4), np.full_like(x, 0.75))
    return np.where(m[..., None], g, c)




def cloth_fn(P, N, S, T):
    """흰 옷감 (가슴옷 · 망토 윗부분): 은빛 흰색 · 푸른 그늘 · 세로로 흐르는 주름"""
    w = fbm(_q(P, np.array([0.5, 0.12, 0.5])), 1.0, 21)
    fold = 0.5 + 0.5 * np.sin(P[..., 0] * 1.1 + P[..., 2] * 0.9 + w * 5.0)
    k = shade(N, 0.7, 0.35)
    hi, lo = C(246, 247, 252), C(150, 166, 200)
    t = np.clip(k * (0.78 + 0.3 * fold), 0, 1.15)
    c = mix(lo[None, None], hi[None, None], np.clip(t, 0, 1)[..., None])
    return np.clip(c * (0.94 + 0.08 * w)[..., None], 0, 255)


CLOTH = _fm(cloth_fn, edge=0.96, top=1.03, bot=0.82)


def bust_mat(c):
    """가슴 반구 (v1.235): 면 법선 대신 반구 가운데에서 잰 둥근 법선으로 명암 → 조각조각 각져 보이지 않고 매끈 · 위쪽 빛 · 아래 그늘"""
    c = np.array(c, float)
    def f(P, N, S, T):
        d = P - c
        n = d / np.maximum(np.linalg.norm(d, axis=-1), 1e-6)[..., None]
        k = 0.74 + 0.34 * np.clip(np.sum(n * LIGHT, axis=-1), 0, 1) - 0.12 * np.clip(-n[..., 1], 0, 1)
        return np.clip(mix(C(170, 182, 212)[None, None], C(250, 251, 255)[None, None], np.clip(k, 0, 1)[..., None]), 0, 255)
    return Mat(f, edge=1.0, top=1.0, bot=1.0)


def gold_fn(P, N, S, T, seed=31):
    """옛 금 (금빛 갑 · 고리 · 장식): 짙은 청동 금 → 밝은 금 · 새긴 소용돌이 홈 · 빛 쪽 반짝임"""
    k = shade(N, 0.5, 0.65)
    n = fbm(_q(P, 0.25), 1.0, seed)
    sc = np.sin(P[..., 0] * 0.9 + np.sin(P[..., 1] * 0.7) * 2.2) * np.sin(P[..., 1] * 0.8 + np.sin(P[..., 2] * 0.7) * 2.0 + P[..., 2] * 0.4)
    groove = sstep(0.12, 0.03, np.abs(sc)) * 0.5
    dark, mid, hi = C(92, 58, 24), C(196, 146, 66), C(255, 228, 150)
    t = np.clip(k * (0.85 + 0.3 * n), 0, 1.2)
    c = mix(dark[None, None], mid[None, None], np.clip(t * 1.4, 0, 1)[..., None])
    c = mix(c, hi[None, None], np.clip(t - 0.62, 0, 1)[..., None] * 1.8)
    c = c * (1 - 0.42 * groove)[..., None]
    return np.clip(c, 0, 255)


GOLD = _fm(gold_fn, edge=0.86, top=1.08, bot=0.72)


def blue_at(u):
    """영롱한 푸른빛 띠 (u 0 = 짙은 사파이어 → 1 = 맑은 하늘빛)"""
    u = np.clip(u, 0, 1)[..., None]
    a, b, c = C(14, 36, 128)[None, None], C(34, 112, 236)[None, None], C(132, 214, 255)[None, None]
    return np.where(u < 0.55, mix(a, b, u / 0.55), mix(b, c, (u - 0.55) / 0.45))


def hair_mat(u0, u1, seed=0):
    """긴 머리: 뿌리 (u0) → 끝 (u1) 로 짙은 사파이어 → 하늘빛 · 가로 결 · 윤기 띠 (머리 위쪽) · 빛 쪽 밝게"""
    def f(P, N, S, T):
        u = u1 + (u0 - u1) * T
        n = fbm(_q(P, 0.5, seed), 1.0, 41)
        st = 0.5 + 0.5 * np.sin(S * TAU * 2.6 + n * 5.0 + seed)
        c = blue_at(u * 0.9 + 0.08) * (0.68 + 0.42 * st)[..., None]
        band = np.exp(-((u - 0.16) / 0.07) ** 2) * (0.6 + 0.4 * st)
        c = mix(c, C(206, 238, 255)[None, None], (band * 0.55)[..., None])
        return np.clip(c * shade(N, 0.72, 0.38), 0, 255)
    return _fm(f, top=1.04, bot=0.8)


def hair_glow(u0, u1, seed=0):
    """머리 겉 결 (더해 빛남): 끝으로 갈수록 밝은 푸른 빛 · 결 따라"""
    def f(P, N, S, T):
        u = u1 + (u0 - u1) * T
        n = fbm(_q(P, 0.5, seed + 3), 1.0, 43)
        st = 0.5 + 0.5 * np.sin(S * TAU * 2.6 + n * 5.0 + seed)
        k = (0.25 + 0.75 * sstep(0.15, 1.0, u)) * (0.35 + 0.65 * st ** 2)
        return np.clip(C(30, 110, 230)[None, None] * (k * 0.55)[..., None], 0, 255)
    return _fm(f)


def cape_mat(u0, u1, seed=0):
    """흰 망토 꼬리: 위 (u 0) 흰색 → 끝 (u 1) 영롱한 푸른빛 · 길게 흐르는 주름 · 가장자리 그늘"""
    def f(P, N, S, T):
        u = u1 + (u0 - u1) * T
        w = fbm(_q(P, np.array([0.4, 0.2, 0.4]), seed), 1.0, 51)
        fold = 0.5 + 0.5 * np.sin(S * TAU * 1.5 + w * 4 + seed)
        k = shade(N, 0.86, 0.18)
        white = mix(C(160, 174, 206)[None, None], C(248, 249, 253)[None, None], np.clip(k * (0.8 + 0.25 * fold), 0, 1)[..., None])
        bt = sstep(0.35, 0.9, u)
        blue = blue_at(0.25 + 0.75 * sstep(0.4, 1.0, u) + 0.15 * (fold - 0.5)) * (0.8 + 0.3 * fold)[..., None]
        c = mix(white, blue, bt[..., None])
        edge = sstep(0.38, 0.5, np.abs(S - 0.5))
        c = np.clip(c * (1 - 0.18 * edge)[..., None], 0, 255)
        sc = 0.5 - 0.07 * (0.5 + 0.5 * np.sin(P[..., 1] * 0.9 + P[..., 0] * 0.6 + seed)) * sstep(0.3, 0.7, u)   # 꼬리 가장자리 = 물결진 천 끝 (잘라 그림)
        return np.dstack([c, np.where(np.abs(S - 0.5) <= sc, 255.0, 0.0)])
    return _fm(f, edge=1.0, top=1.03, bot=0.85)


def fur_mat(u0, u1, seed=0, cut=True):
    """복슬한 꼬리 털 (v1.241): 위 (u 0) 흰 털 → 끝 (u 1) 영롱한 푸른빛 · 가는 털 결 · 털뭉치 판은 털끝마다 길이가 다른 가닥으로 잘라 그림 (T 0 = 털끝)"""
    def f(P, N, S, T):
        u = u0 + (u1 - u0) * 0.5 + np.zeros_like(S)
        w = fbm(_q(P, 0.9, seed), 1.0, 71)
        strand = 0.5 + 0.5 * np.sin(S * TAU * 11 + w * 6.0 + seed)
        k = shade(N, 0.86, 0.22) * (0.88 + 0.16 * strand)
        if cut: k = k * (0.7 + 0.42 * (1 - T))                                              # 털끝은 밝고 뿌리는 그늘
        white = mix(C(150, 166, 204)[None, None], C(250, 251, 255)[None, None], np.clip(k, 0, 1)[..., None])
        blue = blue_at(0.25 + 0.75 * sstep(0.35, 1.0, u) + 0.2 * (strand - 0.5)) * np.clip(0.75 + 0.4 * k, 0, 1.3)[..., None]
        c = mix(white, blue, sstep(0.3, 0.85, u)[..., None])
        a = np.full_like(S, 255.0)
        if cut:                                                                               # 둥근 털뭉치 (끝이 둥글고 가장자리만 가는 가닥으로 들쭉날쭉)
            x = np.abs(S - 0.5) * 2
            sid = np.floor(S * 14.0)
            Ls = 0.84 + 0.16 * (0.5 + 0.5 * np.sin(sid * 12.9898 + seed * 3.1))
            h = 1 - T
            a = np.where(h <= Ls * np.sqrt(np.clip(1 - x ** 1.8, 0, 1)), 255.0, 0.0)
        return np.dstack([np.clip(c, 0, 255), a])
    return _fm(f, edge=1.0, top=1.0, bot=1.0)


def cape_glow(u0, u1, seed=0):
    def f(P, N, S, T):
        u = u1 + (u0 - u1) * T
        w = fbm(_q(P, 0.4, seed + 5), 1.0, 53)
        k = sstep(0.45, 1.0, u) * (0.6 + 0.4 * w) * (1 - sstep(0.3, 0.5, np.abs(S - 0.5)) * 0.7)
        return np.clip(C(26, 100, 220)[None, None] * (k * 0.6)[..., None], 0, 255)
    return _fm(f)


# ---- 잘라 그린 금빛 판 (투조 진자 · 톱니 고리 · 시계판)
def _gold_px(k, emb):
    """판 위 금빛: k = 띠 안 밝기 (0..1) · emb = 띠 가운데로 볼록"""
    dark, mid, hi = C(104, 66, 26), C(206, 154, 70), C(255, 232, 160)
    t = np.clip(0.35 + 0.65 * emb, 0, 1) * k
    c = mix(dark[None, None], mid[None, None], np.clip(t * 1.5, 0, 1)[..., None])
    return mix(c, hi[None, None], np.clip(t - 0.6, 0, 1)[..., None] * 2.2)


def _band(d, hw):
    """띠 가운데에서 떨어진 정도 d · 반폭 hw → (안 · 볼록)"""
    inside = np.abs(d) <= hw
    return inside, np.clip(1 - np.abs(d) / max(hw, 1e-4), 0, 1)


def spade_fn(P, N, S, T):
    """금빛 투조 진자 (망토 꼬리 끝 · 그림): 위 = 고리 목 · 둥근 몸 · 아래로 뾰족 · 안은 소용돌이 투조 · 가운데 푸른 보석"""
    u, v = (S - 0.5) * 2, T
    w = np.where(v < 0.12, 0.28, np.where(v < 0.42, 0.28 + 0.68 * sstep(0.12, 0.38, v), 0.96 * np.clip((1 - v) / 0.58, 0, 1) ** 0.85))
    inside = (np.abs(u) <= w) & (v > 0.02) & (v < 0.995)
    de = w - np.abs(u)                                                                      # 테두리까지
    m_edge, e_edge = _band(de - 0.07, 0.07)
    m_sp, e_sp = _band(u, 0.05)
    m_sp = m_sp & (v > 0.48)
    cs = []
    for cx, cy, r, hw in ((0.42, 0.42, 0.2, 0.055), (-0.42, 0.42, 0.2, 0.055), (0.24, 0.66, 0.13, 0.045), (-0.24, 0.66, 0.13, 0.045), (0.0, 0.84, 0.07, 0.04)):
        d = np.hypot(np.abs(u) * 0 + u - cx, (v - cy) * 1.15) - r
        cs.append(_band(d, hw))
    m_cur = np.zeros_like(u, bool); e_cur = np.zeros_like(u)
    for m, e in cs: m_cur |= m; e_cur = np.maximum(e_cur, e * m)
    g = np.hypot(u, (v - 0.27) * 1.2)
    m_gem = g < 0.15
    m_gs, e_gs = _band(g - 0.19, 0.045)
    m_neck, e_neck = _band(np.hypot(u, (v - 0.07) * 1.3) - 0.17, 0.06)
    metal = inside & (m_edge | m_sp | m_cur | m_gs) | m_neck
    emb = np.where(m_edge, e_edge, 0) + np.where(m_sp, e_sp, 0) + np.where(m_cur, e_cur, 0) + np.where(m_gs, e_gs, 0) + np.where(m_neck, e_neck, 0)
    c = _gold_px(shade(N, 0.6, 0.55), np.clip(emb, 0, 1))
    gem = blue_at(0.5 + 0.5 * (1 - g / 0.15)) + C(180, 230, 255)[None, None] * (sstep(0.08, 0.0, np.hypot(u + 0.05, v - 0.24)))[..., None]
    c = np.where(m_gem[..., None] & inside[..., None], gem, c)
    a = np.where((metal | (m_gem & inside)), 255.0, 0.0)
    return np.dstack([np.clip(c, 0, 255), a])


SPADE = _fm(spade_fn)
INNER = _fm(inner_fn, edge=0.85, top=1.05, bot=0.8)


def gear_plate(r_band=(0.62, 0.74), teeth=(0.74, 0.8, 28), spikes=(8, 1.0, 0.07), chain=(0.53, 18), ticks=60, gem=None, seed=0):
    """가시 돋은 금빛 톱니 고리 (그림의 고리): 넓은 띠 · 바깥 톱니 · 큰 가시 · 안쪽 사슬 고리 · 눈금 홈 · (gem = 열두 시 자리 푸른 점)"""
    r0, r1 = r_band; t0, t1, nt = teeth; ns, sL, sw = spikes; cr, nc = chain
    def f(P, N, S, T):
        u, v, r, a = _pol(S, T)
        k = shade(N, 0.62, 0.5)
        mb, eb = _band(r - (r0 + r1) / 2, (r1 - r0) / 2)
        tooth = (r >= t0 - 0.01) & (r <= t1) & (np.cos(a * nt) > 0.1)
        et = np.clip(1 - (r - t0) / max(t1 - t0, 1e-3), 0, 1) * 0.6
        ph = (a * ns / TAU) % 1.0
        dph = np.minimum(ph, 1 - ph) * TAU / ns * r                                         # 가시 가운데에서 옆으로
        ws = sw * np.clip((sL - r) / max(sL - t1, 1e-3), 0, 1)
        spike = (r > t1 - 0.02) & (r <= sL) & (dph <= ws)
        es = np.clip(1 - dph / np.maximum(ws, 1e-4), 0, 1)
        ph2 = ((a + math.pi / ns) * ns / TAU) % 1.0                                          # 사이 작은 가시
        dph2 = np.minimum(ph2, 1 - ph2) * TAU / ns * r
        ws2 = sw * 0.6 * np.clip((t1 + (sL - t1) * 0.45 - r) / max((sL - t1) * 0.45, 1e-3), 0, 1)
        spike2 = (r > t1 - 0.02) & (dph2 <= ws2)
        es2 = np.clip(1 - dph2 / np.maximum(ws2, 1e-4), 0, 1)
        la = (a * nc / TAU) % 1.0                                                             # 사슬 고리 (가로 · 세로 번갈아)
        idx = np.floor(a * nc / TAU)
        lx = (la - 0.5) * TAU / nc * cr
        ly = r - cr
        odd = (idx % 2) == 1
        ex = np.where(odd, np.hypot(lx / 0.055, ly / 0.03), np.hypot(lx / 0.075, ly / 0.045))
        mc = (ex > 0.62) & (ex < 1.0)
        ec = 1 - np.abs(ex - 0.81) / 0.19
        mi, ei = _band(r - (cr - 0.075), 0.012)
        tk = (np.cos(a * ticks) > 0.93) & mb & (np.abs(r - (r0 + r1) / 2) < (r1 - r0) * 0.3)
        metal = mb | tooth | spike | spike2 | mc | mi
        emb = np.where(mb, eb, 0) + np.where(tooth, et, 0) + np.where(spike, es, 0) + np.where(spike2, es2, 0) + np.where(mc, ec, 0) + np.where(mi, ei, 0)
        c = _gold_px(k, np.clip(emb, 0, 1))
        c = c * (1 - 0.45 * tk)[..., None]
        if gem is not None:
            g = np.hypot(u - 0, v + (r0 + r1) / 2)
            c = np.where((g < 0.05)[..., None], blue_at(np.full_like(g, 0.8)), c)
        return np.dstack([np.clip(c, 0, 255), np.where(metal, 255.0, 0.0)])
    return _fm(f)


def dial_fn(P, N, S, T):
    """시계판 (왕관 · 가슴 · 모래시계 혼천의): 금 테 · 흰 법랑 · 열두 눈금 · 금빛 두 바늘 · 둥글게 잘라 그림"""
    u, v, r, a = _pol(S, T)
    k = shade(N, 0.7, 0.4)
    c = mix(C(220, 226, 240)[None, None], C(255, 253, 244)[None, None], np.full_like(r, k)[..., None]) * np.ones_like(r)[..., None]
    rim, er = _band(r - 0.9, 0.1)
    tick = (np.cos(a * 12) > 0.96) & (r > 0.62) & (r < 0.78)
    mtk = (np.cos(a * 60) > 0.985) & (r > 0.7) & (r < 0.78)
    def hand(ang, L, w):
        d = np.array([math.cos(ang), math.sin(ang)])
        t = u * d[0] + v * d[1]; s = np.abs(-u * d[1] + v * d[0])
        return (t > -0.08) & (t < L) & (s < w * (1 - np.clip(t / L, 0, 1) * 0.7))
    hm = hand(-math.pi / 2 + 0.9, 0.62, 0.07) | hand(-math.pi / 2 - 1.9, 0.42, 0.09) | (r < 0.08)
    c = np.where((tick | mtk | hm)[..., None], _gold_px(k, np.full_like(r, 0.7)) * 0.75, c)
    c = np.where(rim[..., None], _gold_px(k, er), c)
    return np.dstack([np.clip(c, 0, 255), np.where(r < 1.0, 255.0, 0.0)])


DIAL = _fm(dial_fn)


# ---- 얼굴: 시공간이 일그러지는 둥근 구체
def lens_fn(P, N, S, T):
    """중력 렌즈: 가운데로 빨려 들며 휘는 빛 고리 (로그 간격 · 나선으로 비틀림) · 푸른 빛 · 가장자리 0"""
    u, v, r, a = _pol(S, T)
    n = fbm(np.dstack([S * 5, T * 5, np.zeros_like(S)]), 1.0, 61)
    ph = np.log(r + 0.03) * 7.5 + a * 1.0 + n * 1.2
    ring = (0.5 + 0.5 * np.cos(ph * TAU / 2.2)) ** 6
    env = sstep(0.12, 0.34, r) * (1 - sstep(0.82, 1.0, r))
    col = mix(C(40, 120, 255)[None, None], C(170, 230, 255)[None, None], sstep(0.3, 0.8, r)[..., None])
    return np.clip(col * (ring * env * 0.9)[..., None], 0, 255)


def ticks_fn(P, N, S, T):
    """빨려 드는 시계 눈금: 60 눈금 · 12 큰 눈금이 안으로 갈수록 나선으로 휘어 감김 (금빛)"""
    u, v, r, a = _pol(S, T)
    tw = a + 2.4 * np.log(r + 0.05)
    big = np.cos(tw * 12) > 0.86
    small = np.cos(tw * 60) > 0.9
    rr = (r % 0.16) / 0.16
    seg = (rr > 0.15) & (rr < 0.8)
    env = sstep(0.14, 0.3, r) * (1 - sstep(0.85, 1.0, r))
    m = (big & seg) * 1.0 + (small & seg & (r > 0.5)) * 0.45
    return np.clip(C(255, 214, 120)[None, None] * (m * env * (0.5 + 0.5 * r))[..., None], 0, 255)


def horizon_fn(P, N, S, T):
    """사건의 지평선: 가운데 구멍 둘레 흰 하늘빛 고리 + 빛무리 · 바깥 금빛 테 (조금씩 끊김)"""
    u, v, r, a = _pol(S, T)
    n = fbm(np.dstack([S * 9, T * 9, np.zeros_like(S)]), 1.0, 63)
    ring = np.exp(-((r - 0.24) / 0.035) ** 2) + 0.35 * np.exp(-((r - 0.24) / 0.12) ** 2)
    outer = np.exp(-((r - 0.9) / 0.03) ** 2) * sstep(0.35, 0.6, n) * 0.6
    c = C(210, 240, 255)[None, None] * (ring * (0.8 + 0.4 * n))[..., None] + C(255, 210, 120)[None, None] * outer[..., None]
    return np.clip(c, 0, 255)


def swirl_fn(arms, twist, c_in, c_out, k, r0, r1, seed):
    c_in, c_out = np.array(c_in, float), np.array(c_out, float)
    def f(P, N, S, T):
        u, v, r, a = _pol(S, T)
        n = fbm(np.dstack([S * 6, T * 6, np.full_like(S, seed * 0.1)]), 1.0, seed)
        ph = arms * (a + twist * np.log(r + 0.04)) + n * 2.0
        arm = (0.5 + 0.5 * np.cos(ph)) ** 3
        env = sstep(r0 * 0.6, r0, r) * (1 - sstep(r1 * 0.75, r1, r))
        t = np.clip((r - r0) / max(1e-3, r1 - r0), 0, 1)
        col = c_in[None, None] * (1 - t)[..., None] + c_out[None, None] * t[..., None]
        return np.clip(col * (k * env * (0.2 + 0.8 * arm) * (0.75 + 0.5 * n))[..., None], 0, 255)
    return f


def hole_fn(P, N, S, T):
    """구체 속 바탕 (잘라 그림 · 둥근 판): 가운데 검은 구멍 → 짙은 남색 → 푸른 우주 · 먼 별"""
    u, v, r, a = _pol(S, T)
    n = fbm(np.dstack([S * 5, T * 5, np.zeros_like(S)]), 1.0, 67)
    c = mix(C(2, 3, 12)[None, None], C(14, 26, 84)[None, None], sstep(0.2, 0.6, r)[..., None])
    c = mix(c, C(26, 64, 150)[None, None], sstep(0.6, 0.98, r)[..., None])
    c = c + C(40, 90, 200)[None, None] * (sstep(0.55, 0.85, n) * sstep(0.35, 0.8, r) * 0.4)[..., None]
    st = sstep(0.9, 0.97, vnoise(np.dstack([S * 20, T * 20, np.zeros_like(S)]), 1.0, 69)) * sstep(0.3, 0.5, r)
    c = mix(c, C(220, 236, 255)[None, None], (st * 0.85)[..., None])
    return np.dstack([np.clip(c, 0, 255), np.where(r < 0.98, 255.0, 0.0)])


FACE_C = [None]
ORB_O, ORB_R = 0.5, 3.4                                                                    # v1.247 얼굴 구체 가운데 (머리 가운데에서 앞으로) · 반지름 — 머리 앞으로 튀어나오지 않게 (옛 1.95 · 3.9)
ORB_K = ORB_R / 3.9


def orb_glass_fn(P, N, S, T):
    """얼굴 구체 유리: 휘어진 시공간 격자 (구체 위 위도 · 경도 줄 · 가운데로 갈수록 휘어 모임) · 옅은 푸른 · 가장자리 · 반짝임"""
    d = P - FACE_C[0]
    n = d / np.maximum(np.linalg.norm(d, axis=-1), 1e-6)[..., None]
    lat = np.arcsin(np.clip(n[..., 1], -1, 1))
    lon = np.arctan2(n[..., 0], -n[..., 2])
    front = np.clip(-n[..., 2], 0, 1)
    warp = 1.0 + 1.6 * front ** 3                                                           # 앞 (얼굴 가운데) 쪽으로 격자가 빨려 듦
    g1 = np.abs(np.sin(lat * 6 * warp + lon * front * 1.6)) < 0.08
    g2 = np.abs(np.sin(lon * 6 * warp - lat * front * 1.6)) < 0.08
    rim = 1 - np.abs(np.sum(n * nrm(np.array([0.0, 0.1, -1.0])), axis=-1))
    spec = sstep(0.93, 0.985, np.sum(n * nrm(np.array([0.5, 0.7, -0.5])), axis=-1))
    a = 34 + 120 * rim ** 2 + 120 * (g1 | g2) + 200 * spec
    c = mix(C(120, 190, 255)[None, None], C(240, 250, 255)[None, None], np.clip(spec + rim * 0.4 + (g1 | g2) * 0.3, 0, 1)[..., None])
    return np.dstack([c, np.clip(a, 0, 255)])


LENS = _fm(lens_fn)
TICKS = _fm(ticks_fn)
HORIZON = _fm(horizon_fn)
SWIRL_A = _fm(swirl_fn(2, 2.6, (90, 200, 255), (40, 60, 220), 0.9, 0.3, 0.98, 71))
SWIRL_B = _fm(swirl_fn(3, -1.9, (255, 225, 160), (80, 150, 255), 0.45, 0.4, 1.0, 73))
HOLE = _fm(hole_fn)
ORB_GLASS = _fm(orb_glass_fn)


# ---- 빛 (더해 빛남)
def streak_fn(P, N, S, T):
    """금빛 기운 띠 (그림의 금빛 붓질): 길이 (T) 따라 머리가 밝고 꼬리로 사라짐 · 가로 (S) 붓 결"""
    n = vnoise(np.dstack([S * 14, T * 2.5, np.zeros_like(S)]), 1.0, 81)
    across = 1 - sstep(0.25, 0.5, np.abs(S - 0.5))
    along = sstep(0.0, 0.12, T) * (1 - sstep(0.55, 1.0, T))
    fib = 0.45 + 0.55 * sstep(0.3, 0.75, n)
    k = across * along * fib
    c = mix(C(200, 120, 30)[None, None], C(255, 236, 150)[None, None], (k ** 0.7)[..., None])
    return np.clip(c * k[..., None] * 1.05, 0, 255)


STREAK = _fm(streak_fn)


def glow_disc_fn(col, k=1.0, p=1.6, r0=0.0):
    col = np.array(col, float)
    def f(P, N, S, T):
        u, v, r, a = _pol(S, T)
        m = np.clip(1 - np.abs(r - r0) / max(1 - r0, 1e-3), 0, 1) ** p
        return np.clip(col[None, None] * (k * m)[..., None], 0, 255)
    return _fm(f)


def rev_dial_fn(P, N, S, T):
    """거꾸로 도는 푸른 시계판 후광 (2페이즈 ~): 두 고리 · 로마 숫자 대신 열두 굵은 눈금 · 60 눈금 · 빛살"""
    u, v, r, a = _pol(S, T)
    rings = np.exp(-((r - 0.9) / 0.012) ** 2) + np.exp(-((r - 0.78) / 0.01) ** 2) * 0.8 + np.exp(-((r - 0.55) / 0.008) ** 2) * 0.5
    big = (np.cos(a * 12) > 0.97) & (r > 0.8) & (r < 0.89)
    small = (np.cos(a * 60) > 0.97) & (r > 0.82) & (r < 0.88)
    rays = (0.5 + 0.5 * np.cos(a * 24)) ** 8 * sstep(0.55, 0.78, r) * (1 - sstep(0.78, 0.82, r)) * 0.5
    k = rings + big * 0.9 + small * 0.5 + rays
    return np.clip(C(70, 170, 255)[None, None] * k[..., None], 0, 255)


HOURGLASS_GLASS = None


def hg_glass_fn(P, N, S, T):
    rim = sstep(0.3, 0.5, np.abs(S - 0.5))
    a = 60 + 150 * rim
    c = mix(C(180, 220, 255)[None, None], C(255, 255, 255)[None, None], rim[..., None])
    return np.dstack([c, np.clip(a, 0, 255)])


def sand_fn(P, N, S, T):
    n = vnoise(_q(P, 3.0), 1.0, 91)
    return np.clip(mix(C(230, 170, 80)[None, None], C(255, 230, 150)[None, None], n[..., None]) * shade(N, 0.8, 0.3), 0, 255)


HG_GLASS = _fm(hg_glass_fn)
SAND = _fm(sand_fn)
BLUE_GEM = _fm(lambda P, N, S, T: np.clip(blue_at(0.4 + 0.6 * (1 - np.hypot(S - 0.4, T - 0.35) * 1.6)) * (0.8 + 0.4 * shade(N, 0.5, 0.6)), 0, 255))
GEM_GLOW = glow_disc_fn((60, 150, 255), 0.9, 1.8)
HALO_GLOW = glow_disc_fn((70, 140, 255), 0.55, 2.2)
HALO_GLOW_W = glow_disc_fn((255, 220, 150), 0.35, 3.0)
REV_DIAL = _fm(rev_dial_fn)
STAR_ADD = flat_add((255, 236, 160), 1.0)
STAR_GLOW = soft_add((255, 190, 80), 0.6, 1.5)
BSTAR = flat_add((190, 230, 255), 1.0)
BSTAR_GLOW = soft_add((60, 140, 255), 0.6, 1.5)
RAY = _fm(lambda P, N, S, T: np.clip(C(255, 220, 120)[None, None] * ((1 - sstep(0.2, 0.5, np.abs(S - 0.5))) * (1 - T) ** 1.4 * 0.9)[..., None], 0, 255))
ORBIT = flat_add((120, 200, 255), 0.45)


# ================================================================= 조각 도우미
def rz_(a):
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def rx_(a):
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def ry_(a):
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


NOF = {'south': None, 'north': None, 'east': None, 'west': None, 'up': None, 'down': None}


def plate(sk, c, Rm, w, h, mat, two=True, dens=8, th=0.04):
    """판 (상자 z 면만 그림): Rm 열 = 판 x · y · 법선"""
    fc = dict(NOF); fc['south'] = mat
    if two: fc['north'] = mat
    return sk.rbox(c, Rm, (w, h, th), mat, faces=fc, dens=dens)


def ring_band(sk, c, Rm, r, w, t, n, mat, a0=0.0, dens=3.0, over=1.12):
    """고리 띠 (Rm 의 x-y 면 위 반지름 r 원 · 폭 w (반지름 쪽) · 두께 t (법선 쪽))"""
    out = []
    ax, ay, an = Rm[:, 0], Rm[:, 1], Rm[:, 2]
    for i in range(n):
        a = a0 + TAU * (i + 0.5) / n
        p = c + (ax * math.cos(a) + ay * math.sin(a)) * r
        tg = -ax * math.sin(a) + ay * math.cos(a)
        rd = ax * math.cos(a) + ay * math.sin(a)
        L = TAU * r / n * over
        out.append(sk.rbox(p, np.column_stack([rd, tg, an]), (w, L, t), mat, dens=dens))
    return out


def spike3d(sk, base, d, side, L, w0, t0, mat, n=3):
    """가늘어지는 가시 (base → d 쪽 L · 마디 n)"""
    out = []
    for k in range(n):
        q0, q1 = k / n, (k + 1) / n
        a, b = base + d * L * q0, base + d * L * q1
        ww = w0 * (1 - q0 * 0.85)
        out.append(sk.seg(a, b, max(ww, 0.12), max(t0 * (1 - q0 * 0.6), 0.12), mat, z_hint=side, over=1.08, dens=4))
    return out


def gear(F, sk, name, parent, c, Rm, R, band_w=None, th=1.0, n_band=None, spikes3d=4, plate_mat=None, pdens=6, glow=None):
    """톱니 고리 하나: 잘라 그린 판 (`<name>_cut`) + 입체 띠 (`<name>`) + 큰 가시 몇 (입체)
    기울인 고리 = 쉬는 자세 뼈대 `<name>_rest` (회전 Rm) 아래 xy 면에 지음 → `<name>` 을 z 로 돌리면 고리 법선 둘레로 돎 (교훈 91)"""
    band_w = band_w if band_w is not None else R * 0.12
    n_band = n_band or max(16, int(TAU * R / 1.6))
    rc = R * 0.68
    tilted = not np.allclose(Rm, np.eye(3))
    if tilted:
        F.add(f'{name}_rest', parent, c, None, rot=tex_kit.euler_of(Rm))
        parent, Rm = f'{name}_rest', np.eye(3)
    F.add(name, parent, c, ring_band(sk, c, Rm, rc, band_w, th, n_band, GOLD, dens=3.5))
    F.add(f'{name}_cut', name, c, [plate(sk, c, Rm, 2 * R, 2 * R, plate_mat or gear_plate(), dens=pdens)])
    sp = []
    ax, ay, an = Rm[:, 0], Rm[:, 1], Rm[:, 2]
    for i in range(spikes3d):
        a = math.pi / 2 + TAU * i / spikes3d
        d = ax * math.cos(a) + ay * math.sin(a)
        sp += spike3d(sk, c + d * R * 0.74, d, an, R * 0.27, R * 0.12, th * 0.9, GOLD)
    if sp: F.put(name, sp)
    if glow is not None:
        F.add(f'{name}_glow_add', name, c, [plate(sk, c - an * 0.3, Rm, 2.3 * R, 2.3 * R, glow, dens=1.2)])
    return Rm


def ribbon(sk, pts, ws, mats, z_hints, th=0.35, over=1.12, dens=3.0, flat=False):
    """점 이음 띠 (마디 k 의 폭 = (ws[k] + ws[k+1]) / 2 · 재질 mats[k] · 면 법선 z_hints[k]) · flat = 넓은 두 면만 그림 (빛 겹)"""
    out = []
    for k in range(len(pts) - 1):
        kw = {'faces': {**NOF, 'south': mats[k], 'north': mats[k]}} if flat else {}
        out.append(sk.seg(pts[k], pts[k + 1], (ws[k] + ws[k + 1]) / 2, th, mats[k], z_hint=z_hints[k], over=over, dens=dens, **kw))
    return out


def cubic(p0, p1, p2, p3, n):
    p0, p1, p2, p3 = map(lambda q: np.array(q, float), (p0, p1, p2, p3))
    return [(1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3 for t in np.linspace(0, 1, n)]


def tubes(sk, *a, **k):
    return [c for sg in tube(sk, *a, **k) for c in sg]


def dome(sk, c, Rm, rad, mat, n_lat=4, n_lon=10, lat0=0.0, th=0.5, dens=4):
    """반구 껍질 (Rm 의 y = 꼭대기 쪽)"""
    out = []
    ax, ay, az = Rm[:, 0], Rm[:, 1], Rm[:, 2]
    for j in range(n_lat):
        p0 = lat0 + (math.pi / 2 - lat0) * j / n_lat
        p1 = lat0 + (math.pi / 2 - lat0) * (j + 1) / n_lat
        pm = (p0 + p1) / 2
        ni = max(4, int(round(n_lon * math.cos(pm))))
        for i in range(ni):
            tm = TAU * (i + 0.5) / ni
            nl = ax * math.cos(pm) * math.cos(tm) + ay * math.sin(pm) + az * math.cos(pm) * math.sin(tm)
            p = c + nl * rad
            tu = nrm(np.cross(ay, nl)) if abs(np.dot(ay, nl)) < 0.999 else ax
            tv = nrm(np.cross(nl, tu))
            w = math.cos(pm) * TAU / ni * rad * 1.25 + 0.3
            h = (p1 - p0) * rad * 1.3
            out.append(sk.rbox(p, np.column_stack([tu, tv, nl]), (w, h, th), mat, dens=dens))
    return out


def sphere_shell(sk, c, rad, mat, nb=7, th=0.12, dens=4, keep_z=None):
    """구 껍질 · keep_z = 이 값보다 z 가 큰 쪽만 (뼈대 좌표 · 얼굴 뼈대는 +z = 앞)"""
    out = []
    for j in range(nb):
        p0, p1 = -math.pi / 2 + math.pi * j / nb, -math.pi / 2 + math.pi * (j + 1) / nb
        pm = (p0 + p1) / 2
        ni = max(4, int(round(TAU * rad * math.cos(pm) / 1.5)))
        for i in range(ni):
            tm = TAU * (i + 0.5) / ni
            n = np.array([math.cos(pm) * math.sin(tm), math.sin(pm), math.cos(pm) * math.cos(tm)])
            if keep_z is not None and n[2] < keep_z: continue
            tu = nrm(np.cross(Y_, n)) if abs(n[1]) < 0.999 else X_
            tv = nrm(np.cross(n, tu))
            w = math.cos(pm) * TAU / ni * rad * 1.2 + 0.2
            h = math.pi / nb * rad * 1.2
            out.append(sk.rbox(c + n * rad, np.column_stack([tu, tv, n]), (w, h, th), mat, dens=dens))
    return out


# ================================================================= 여신
def figure(sk):
    F = Fig(); J = F.J
    hip = np.array([0.0, 46.0, 0.3]); waist = np.array([0.0, 51.5, 0.5]); rib = np.array([0.0, 57.5, 0.2]); neck = np.array([0.0, 64.6, 0.5])
    HC = np.array([-0.4, 70.6, -0.1])
    sh_r, sh_l = np.array([6.3, 62.3, 0.6]), np.array([-6.3, 62.3, 0.6])                   # _r = 모델 +x (그림 오른쪽 · 내린 팔) · _l = -x (든 팔)
    el_r, wr_r = np.array([8.8, 54.4, 1.6]), np.array([9.6, 48.0, -2.0])
    el_l, wr_l = np.array([-8.8, 54.4, 1.6]), np.array([-9.6, 48.0, -2.0])                # v1.233 평소엔 내린 팔 (시전할 때만 듦 · 애니 RAISE)
    hip_r, hip_l = np.array([2.25, 43.6, 0.2]), np.array([-2.25, 43.6, 0.2])
    kn_l, an_l, to_l = np.array([-3.0, 29.6, -1.0]), np.array([-2.6, 16.4, 0.7]), np.array([-2.5, 10.4, -0.4])   # 곧게 뻗어 발끝을 세운 다리
    kn_r, an_r, to_r = np.array([4.2, 31.6, -6.4]), np.array([4.7, 20.4, 1.9]), np.array([4.9, 15.6, 4.0])     # 무릎을 굽힌 다리
    J.update(hip=hip, waist=waist, rib=rib, neck=neck, HC=HC, sh_r=sh_r, sh_l=sh_l, el_r=el_r, wr_r=wr_r, el_l=el_l, wr_l=wr_l, to_l=to_l)
    F.add('root', 'float', hip)
    # ---- 몸통 (엉덩이 밑 → 골반 → 가는 허리 → 갈비 → 가슴 → 목 밑)
    tp = [np.array([0, 41.6, 0.3]), np.array([0, 43.4, 0.3]), hip, np.array([0, 49.0, 0.4]), waist, np.array([0, 54.6, 0.4]), rib, np.array([0, 60.6, 0.3]), np.array([0, 63.0, 0.6])]
    trx = [1.8, 4.35, 4.85, 3.75, 2.75, 3.15, 3.75, 3.75, 2.1]   # v1.238 굵어진 팔다리에 맞춰 넓힘
    trz = [1.5, 2.8, 3.05, 2.5, 2.05, 2.2, 2.4, 2.2, 1.6]
    tseg = tube(sk, tp, trx, trz, 12, SUIT, side=X_)
    F.add('body', 'root', hip, [c for sg in tseg[:4] for c in sg])
    ch = [c for sg in tseg[4:] for c in sg]
    sline = [sh_l - X_ * 0.3, np.array([-4.2, 62.9, 0.6]), np.array([-1.8, 63.5, 0.5]), np.array([0, 63.6, 0.5]), np.array([1.8, 63.5, 0.5]), np.array([4.2, 62.9, 0.6]), sh_r + X_ * 0.3]   # v1.235 어깨 선 = 목 밑에서 어깨 끝으로 비스듬히 (수평 막대 없앰)
    ch += tubes(sk, sline, [0.95, 1.1, 1.05, 1.0, 1.05, 1.1, 0.95], [1.0, 1.3, 1.25, 1.2, 1.25, 1.3, 1.0], 10, SUIT, side=Y_)
    ch += tubes(sk, sline[1:-1], [1.3, 1.25, 1.2, 1.25, 1.3], [1.55, 1.5, 1.45, 1.5, 1.55], 10, CLOTH, side=Y_)
    ch += bodice(sk, F)
    F.add('chest', 'body', waist, ch)
    gc = np.array([0, 61.1, -3.05])                                                          # 푸른 보석 = 목걸이 가운데 (v1.235 · 가슴 사이를 덮지 않게 작게)
    F.add('chest_gem', 'chest', gc, dome(sk, gc + Z_ * 0.2, tex_kit.basis(-Z_, Y_), 0.62, BLUE_GEM, n_lat=2, n_lon=8, lat0=-0.3, th=0.35) + ring_band(sk, gc + Z_ * 0.15, np.eye(3), 0.75, 0.3, 0.4, 12, GOLD, dens=7))
    F.add('chest_gem_add', 'chest_gem', gc, [plate(sk, gc - Z_ * 0.3, np.eye(3), 2.0, 2.0, GEM_GLOW, dens=3)])
    # 금빛 목 깃 (넓게 펼친 깃 판 여섯 · 가시)
    col = []
    for i in range(9):
        a = -math.pi * 0.85 + math.pi * 1.7 * i / 8
        d = np.array([math.sin(a), 0, -math.cos(a)])
        base = neck + np.array([0, -0.9, 0]) + d * 1.6
        col.append(sk.seg(base, base + d * 1.6 + Y_ * 1.5, 1.4, 0.3, GOLD, z_hint=d, over=1.1, dens=5))
    F.add('collar', 'chest', neck, col)
    F.add('neck', 'chest', neck - Y_ * 1.4, tubes(sk, [neck - Y_ * 1.8, neck, neck + Y_ * 1.6], [0.95, 0.82, 0.8], [0.95, 0.82, 0.8], 8, SUIT, side=X_))
    # ---- 머리 (든 팔 쪽으로 조금 기울임)
    hu = nrm(np.array([-0.1, 1.0, 0.04])); fh = nrm(np.array([-0.05, -0.06, -1.0]))
    Rh = tex_kit.basis(hu, fh); hx, hu, fh = Rh[:, 0], Rh[:, 1], Rh[:, 2]
    J.update(hu=hu, fh=fh, hx=hx, Rh=Rh)
    hp_ = [HC - hu * 3.1 + fh * 0.7, HC - hu * 2.2 + fh * 0.45, HC - hu * 1.0 + fh * 0.12, HC + hu * 0.4, HC + hu * 1.6 - fh * 0.2, HC + hu * 2.7 - fh * 0.45, HC + hu * 3.4 - fh * 0.6]
    F.add('head', 'neck', neck + Y_ * 0.8, tubes(sk, hp_, [0.35, 1.6, 2.35, 2.65, 2.6, 2.0, 0.45], [0.35, 1.75, 2.5, 2.75, 2.7, 2.1, 0.45], 10, SUIT, side=hx))
    hair_cap(F, sk, HC, hu, fh, hx)
    face_orb(F, sk, HC, Rh)
    front_hair(F, sk, HC, Rh)
    crown(F, sk, HC, Rh)
    # ---- 팔
    for s, sh, el, wr in (('r', sh_r, el_r, wr_r), ('l', sh_l, el_l, wr_l)):
        ar = tube(sk, [sh, (sh + el) / 2, el, (el + wr) / 2, wr], [1.7, 1.52, 1.32, 1.14, 0.95], [1.62, 1.44, 1.24, 1.06, 0.88], 8, SUIT, side=Z_)
        F.add(f'arm_{s}', 'chest', sh, [c for sg in ar[:2] for c in sg])
        F.add(f'fore_{s}', f'arm_{s}', el, [c for sg in ar[2:] for c in sg])
        d = nrm(wr - el)
        br = tubes(sk, [wr - d * 2.6, wr - d * 1.9, wr - d * 0.4], [1.26, 1.34, 1.16], [1.2, 1.28, 1.1], 10, GOLD, side=Z_)   # 금 팔찌
        br += tubes(sk, [el - d * 0.5, el + d * 0.6], [1.52, 1.46], [1.46, 1.4], 10, GOLD, side=Z_)
        F.put(f'fore_{s}', br)
    capelet(F, sk)                                                                           # v1.240 금빛 어깨 갑 → 어깨 망토
    hand(F, sk, 'r', el_r, wr_r, curl=0.35, palm=-Z_)
    hand(F, sk, 'l', el_l, wr_l, curl=0.3, palm=-Z_)
    # ---- 다리
    for s, hp, kn, an, to in (('r', hip_r, kn_r, an_r, to_r), ('l', hip_l, kn_l, an_l, to_l)):
        th_ = bez(hp, (hp + kn) / 2 + np.array([0.0, -0.4, -0.6]), kn, 4)
        sh_ = [kn, kn + (an - kn) * 0.25 + np.array([0, 0, 0.25]), kn + (an - kn) * 0.55, kn + (an - kn) * 0.85, an, an + (to - an) * 0.55, to]
        rr = [2.95, 2.8, 2.6, 2.15, 2.5, 2.1, 1.45, 1.12, 0.82, 0.25]   # v1.237 굵게 (가는 막대 같던 다리)
        segs = tube(sk, th_ + sh_[1:], rr, [r * 0.94 for r in rr], 10, SUIT)
        nth = len(th_) - 1
        F.add(f'leg_{s}', 'body', hp, [c for sg in segs[:nth] for c in sg])
        F.add(f'shin_{s}', f'leg_{s}', kn, [c for sg in segs[nth:] for c in sg])
        d = nrm(an - kn)
        knee = dome(sk, kn, tex_kit.basis(-Z_, d), 2.2, GOLD, n_lat=3, n_lon=10, lat0=-0.1, th=0.4)
        F.put(f'shin_{s}', knee)
        dt = nrm(to - an)
        F.put(f'shin_{s}', tubes(sk, [an + dt * 0.4, an + (to - an) * 0.6, to + dt * 0.8], [1.2, 0.95, 0.14], [1.12, 0.88, 0.14], 8, GOLD, side=X_))   # 뾰족한 금 발끝
        F.put(f'shin_{s}', tubes(sk, [an - d * 0.6, an + d * 0.2], [1.32, 1.25], [1.32, 1.25], 10, GOLD, side=X_))
    waist_wear(F, sk)
    return F


def rect_link(sk, c, d, u, L, W, w, mat):
    """네모 고리 하나 (현자 사슬과 같음): 가운데 c · 긴 쪽 d · 넓은 쪽 u"""
    c, d, u = (np.array(v, float) for v in (c, d, u))
    out = []
    for sg in (-1, 1):
        out.append(sk.seg(c + u * sg * W / 2 - d * L / 2, c + u * sg * W / 2 + d * L / 2, w, w, mat, z_hint=np.cross(d, u), over=1.05, dens=5))
        out.append(sk.seg(c + d * sg * L / 2 - u * W / 2, c + d * sg * L / 2 + u * W / 2, w, w, mat, z_hint=np.cross(d, u), over=1.05, dens=5))
    return out


def necklace_fn(P, N, S, T):
    """초승달 금 목걸이 (잘라 그림): 아래로 휜 금 띠 두 겹 · 사이 투조 · 띠를 따라 푸른 보석 · 가운데 아래로 늘어진 물방울 보석"""
    u, v = (S - 0.5) * 2, (T - 0.5) * 2
    r = np.hypot(u, (v + 1.0) * 1.15)
    on_arc = (v > -0.75)
    m1, e1 = _band(r - 1.42, 0.07); m2, e2 = _band(r - 1.12, 0.05)
    lat = (r > 1.12) & (r < 1.42) & (np.abs(np.sin(np.arctan2(u, v + 1.0) * 14)) < 0.25)
    metal = on_arc & (m1 | m2 | lat)
    emb = np.where(m1, e1, 0) + np.where(m2, e2, 0) + np.where(lat, 0.5, 0)
    c = _gold_px(shade(N, 0.7, 0.4), np.clip(emb, 0, 1))
    gem = np.zeros_like(u, bool)
    for k in range(-3, 4):
        a = k * 0.32
        gx, gy = math.sin(a) * 1.27, math.cos(a) * 1.27 / 1.15 - 1.0
        gem |= np.hypot(u - gx, v - gy) < (0.11 if k else 0.15)
    drop = (np.abs(u) < 0.16 * np.clip((0.95 - v) / 0.55, 0, 1)) & (v > 0.4) & (v < 0.95)
    gem = gem | drop
    c = np.where(gem[..., None], blue_at(0.55 + 0.4 * (1 - np.abs(u))), c)
    return np.dstack([np.clip(c, 0, 255), np.where(metal | gem, 255.0, 0.0)])


NECKLACE = _fm(necklace_fn)


def gown_mat(v0, v1, hem=False, seed=0):
    """긴 드레스 (흰색 → 영롱한 푸른빛 · 아래로 갈수록 푸름 · 세로로 흐르는 주름 (세계 각으로 칠해 칸 사이가 이어짐) · hem = 물결진 밑단을 잘라 그림)"""
    def f(P, N, S, T):
        v = v1 + (v0 - v1) * T
        ang = np.arctan2(P[..., 0], -P[..., 2])
        w = fbm(_q(P, np.array([0.3, 0.08, 0.3]), seed), 1.0, 57)
        fold = 0.5 + 0.5 * np.sin(ang * 9 + w * 3.5)
        k = shade(N, 0.86, 0.18)
        white = mix(C(168, 180, 212)[None, None], C(250, 251, 254)[None, None], np.clip(k * (0.78 + 0.28 * fold), 0, 1)[..., None])
        blue = blue_at(0.2 + 0.75 * sstep(0.45, 1.0, v) + 0.12 * (fold - 0.5)) * (0.82 + 0.28 * fold)[..., None]
        c = mix(white, blue, sstep(0.35, 0.95, v)[..., None])
        a = np.full_like(S, 255.0)
        if hem:
            cut = 0.72 + 0.16 * np.sin(ang * 7 + 1.3) + 0.08 * np.sin(ang * 17)
            a = np.where(T <= cut, 255.0, 0.0)
        return np.dstack([np.clip(c, 0, 255), a])
    return _fm(f, edge=1.0, top=1.03, bot=0.85)


def sheer_fn(P, N, S, T):
    """비치는 겉치마 · 베일 (유리): 옅은 하늘빛 · 아래로 갈수록 짙게 · 세로 결 · 별가루"""
    ang = np.arctan2(P[..., 0], -P[..., 2])
    st = 0.5 + 0.5 * np.sin(ang * 13 + P[..., 1] * 0.2)
    dust = sstep(0.93, 0.98, vnoise(_q(P, 1.6), 1.0, 97))
    c = mix(C(150, 205, 255)[None, None], C(240, 250, 255)[None, None], (dust + 0.25 * st)[..., None])
    a = 46 + 40 * st + 180 * dust
    return np.dstack([np.clip(c, 0, 255), np.clip(a, 0, 255)])


SHEER = _fm(sheer_fn)


BODICE_Y = [52.9, 55.2, 57.3, 58.9, 60.7, 62.3]
BODICE_RX = [3.1, 3.4, 3.8, 3.95, 3.95, 3.5]                                                 # v1.238 넓힘 (팔다리 굵기에 맞춤)
BODICE_RZ = [2.3, 2.4, 2.5, 2.55, 2.4, 2.1]
BODICE_CZ = [0.5, 0.38, 0.25, 0.22, 0.3, 0.5]


def torso_pt(th, y):
    """윗옷 곡면 위의 점 (th = 각 · 0 = 앞 · + = 오른쪽 +x · y = 높이): 높이마다 타원 + 앞쪽 두 봉긋함 (가운데 ±1.8 · 아래로 처지게 · 가운데 골)"""
    rx, rz, cz = (float(np.interp(y, BODICE_Y, v)) for v in (BODICE_RX, BODICE_RZ, BODICE_CZ))
    x = rx * math.sin(th)
    z = cz - rz * math.cos(th)
    B = 2.25 * math.exp(-((y - 58.2) / (1.6 if y > 58.2 else 1.3)) ** 2)  # v1.236 더 크게                      # 위는 완만 · 아래는 둥글게 떨어짐
    w = math.exp(-((abs(x) - 1.8) / 1.3) ** 2)
    z -= B * w * max(0.0, math.cos(th)) ** 0.6
    return np.array([x, y, z])


def torso_pt_x(x, y):
    """앞쪽 곡면 위 x 자리의 점"""
    rx = float(np.interp(y, BODICE_Y, BODICE_RX))
    return torso_pt(math.asin(max(-0.98, min(0.98, x / rx))), y)


def shell_fn(P, N, S, T):
    """윗옷 곡면 명암 (v1.235): 칸마다 면 법선 대신 몸통 축 · 가슴 봉긋함에서 잰 매끈한 법선 → 칸 경계 · 네모진 밝은 자리 없음 + 옅은 세로 비단 결"""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    nc = np.dstack([x, np.zeros_like(x), z - 0.3])
    nc = nc / np.maximum(np.linalg.norm(nc, axis=-1), 1e-6)[..., None]
    sx = np.where(x >= 0, 1.75, -1.75)
    nl = np.dstack([x - sx, (y - 58.1) * 0.8, z + 0.6])
    nl = nl / np.maximum(np.linalg.norm(nl, axis=-1), 1e-6)[..., None]
    wl = (np.exp(-((np.abs(x) - 1.75) / 1.4) ** 2) * np.exp(-((y - 58.4) / 2.0) ** 2) * (z < -1.0))[..., None]
    n = nc * (1 - wl) + nl * wl
    n = n / np.maximum(np.linalg.norm(n, axis=-1), 1e-6)[..., None]
    k = 0.72 + 0.36 * np.clip(np.sum(n * LIGHT, axis=-1), 0, 1) - 0.22 * np.clip(-n[..., 1], 0, 1)
    w = fbm(_q(P, np.array([0.5, 0.1, 0.5])), 1.0, 23)
    k = k * (0.95 + 0.07 * np.sin(np.arctan2(x, -(z - 0.3)) * 10 + w * 3))
    return np.clip(mix(C(166, 178, 210)[None, None], C(250, 251, 255)[None, None], np.clip(k, 0, 1)[..., None]), 0, 255)


SHELL = Mat(shell_fn, edge=1.0, top=1.0, bot=1.0)


V_NECK = (1.7, 57.4, 62.6)                                                                # 앞섶 V (목 밑 반폭 · 끝 높이 · 위 높이)


def v_half(y):
    return V_NECK[0] * float(np.clip((y - V_NECK[1]) / (V_NECK[2] - V_NECK[1]), 0, 1)) ** 0.85


def torso_shell(sk):
    """윗옷 곡면 (격자 판 · 둘레 26 × 높이 12 · 가슴 부분은 둥근 명암 재질)"""
    NA, NY = 26, 12
    ys = np.linspace(BODICE_Y[0], BODICE_Y[-1], NY + 1)
    out = []
    for j in range(NY):
        for i in range(NA):
            a0, a1 = TAU * i / NA - math.pi, TAU * (i + 1) / NA - math.pi
            P00, P10, P01, P11 = torso_pt(a0, ys[j]), torso_pt(a1, ys[j]), torso_pt(a0, ys[j + 1]), torso_pt(a1, ys[j + 1])
            c = (P00 + P10 + P01 + P11) / 4
            du, dv = (P10 + P11 - P00 - P01) / 2, (P01 + P11 - P00 - P10) / 2
            n = nrm(np.cross(dv, du))
            if np.dot(n, c - np.array([0, c[1], 0.3])) < 0: n = -n
            Rm = tex_kit.basis(dv, n)
            inv = c[2] < 0 and abs(c[0]) < v_half(c[1]) and c[1] > V_NECK[1]                # 앞섶 V 안 = 남빛 금 덩굴 속옷 (곡면 칸 그대로)
            out.append(sk.rbox(c, Rm, (np.linalg.norm(du) * 1.2, np.linalg.norm(dv) * 1.2, 0.42), INNER if inv else SHELL, dens=6 if inv else 4))
    return out


def bodice(sk, F):
    """몸통 옷 (v1.234 "여신이라기엔 좀 아닌 것 같다"): 각진 상자 대신 몸을 따라 둥글게 감싼 옷 — 현자처럼 겹쳐 입되 여신답게
    · 흰 비단 윗옷 (몸 선을 따른 관 · 봉긋한 가슴) · V 자로 깊게 파인 앞섶 속 남빛 금 덩굴 · 앞섶 금 테
    · 초승달 금 목걸이 (푸른 보석 · 물방울 보석) · 남빛 코르셋 (금 띠 둘 · 엇갈린 끈) · 높이 선 깃"""
    J = F.J
    zf = -2.35
    J['zf'] = zf
    cs = torso_shell(sk)                                                                    # v1.235 흰 비단 윗옷 = 높이마다 앞쪽 두 곳이 부푼 한 장의 곡면 (가슴이 따로 튀어나온 원통 · 반구가 아님 · 이음매는 세로로만)
    for sg in (-1, 1):                                                                       # 앞섶 금 테 (곡면 위 V 가장자리 · 바깥으로 띄움)
        ys = np.linspace(V_NECK[1], V_NECK[2], 7)
        pts = [torso_pt_x(sg * v_half(y), y) + nrm(torso_pt_x(sg * v_half(y), y) - np.array([0, y, 0.3])) * 0.28 for y in ys]
        for p0, p1 in zip(pts, pts[1:]):
            cs.append(sk.seg(p0, p1, 0.28, 0.3, GOLD, z_hint=-Z_, over=1.12, dens=6))
    ub = [torso_pt(th, 56.7) + nrm(np.array([math.sin(th), 0, -math.cos(th)])) * 0.3 for th in np.linspace(-1.35, 1.35, 11)]                          # 가슴 밑 금 테 (엠파이어 선 · 곡면을 따라 앞 반 바퀴)
    for p0, p1 in zip(ub, ub[1:]):
        cs.append(sk.seg(p0, p1, 0.36, 0.3, GOLD, z_hint=nrm(np.array([(p0 + p1)[0] / 2, 0, -2.0])), over=1.1, dens=6))
    nc = np.array([0, 62.2, -2.75])                                                           # 초승달 금 목걸이
    cs.append(plate(sk, nc, tex_kit.basis(nrm(np.array([0, 1.0, 0.35])), nrm(np.array([0, 0.35, -1.0]))), 6.4, 3.6, NECKLACE, two=False, dens=14))
    cs += tubes(sk, [np.array([0, 49.2, 0.45]), np.array([0, 51.2, 0.5]), np.array([0, 53.3, 0.5])], [3.0, 2.85, 3.2], [2.3, 2.15, 2.35], 14, INNER, side=X_)   # 남빛 코르셋
    cs += tubes(sk, [np.array([0, 53.2, 0.5]), np.array([0, 53.75, 0.5])], [3.3, 3.3], [2.48, 2.48], 14, GOLD, side=X_)
    cs += tubes(sk, [np.array([0, 49.1, 0.45]), np.array([0, 49.7, 0.45])], [3.15, 3.15], [2.43, 2.43], 14, GOLD, side=X_)
    for k in range(4):                                                                       # 코르셋 앞 엇갈린 끈 (금)
        y = 50.0 + k * 0.8
        cs.append(sk.seg((-0.85, y, -1.92), (0.85, y + 0.8, -1.92), 0.18, 0.14, GOLD, z_hint=-Z_, dens=6))
        cs.append(sk.seg((0.85, y, -1.92), (-0.85, y + 0.8, -1.92), 0.18, 0.14, GOLD, z_hint=-Z_, dens=6))
    for k in range(14):                                                                      # 높이 선 깃 (흰 · 금 테 · 앞은 트임)
        a = TAU * k / 14
        if math.cos(a) < -0.8: continue
        e = np.array([math.sin(a), 0, -math.cos(a)])
        p0 = np.array([0, 63.3, 0.5]) + np.array([math.sin(a) * 1.9, 0, -math.cos(a) * 1.7]); p1 = p0 + e * 0.6 + Y_ * 2.2
        cs.append(sk.seg(p0, p1, 0.95, 0.3, CLOTH, z_hint=e, dens=5))
        cs.append(sk.seg(p1, p1 + e * 0.15 + Y_ * 0.35, 0.95, 0.4, GOLD, z_hint=e, dens=5))
    return cs


def gown_pt(a, v):
    """긴 드레스 위의 점 (a = 각 · 0 = 앞 (-z) · + = 오른쪽 +x · v 0 = 엉덩이 · 1 = 밑단): 아래로 넓게 퍼지며 물결 · 바람에 오른쪽 · 뒤로 끌림"""
    rx = 5.15 + 8.2 * v ** 1.15
    rz = 3.55 + 6.7 * v ** 1.15
    wav = 1 + 0.09 * v * math.sin(a * 6 + v * 2.5) + 0.04 * v * math.sin(a * 11 + 1.0)
    y = 47.6 - 43.0 * v
    return np.array([math.sin(a) * rx * wav + 2.6 * v * v, y, -math.cos(a) * rz * wav + 0.35 + 3.0 * v * v * (1 + math.cos(a)) * 0.5])


GOWN_SLIT = (0.18, 1.02, 0.22)                                                              # 오른 앞 트임 (각 · 각 · 이 v 아래부터) — 굽힌 다리가 드러남


def waist_wear(F, sk):
    """허리 아래 (v1.234 여신): 흰 골반 감싸개 · 네모 고리 금 사슬 허리띠 + 앞 모래시계 고리 · 옆으로 늘어진 사슬
    · 발끝 아래까지 흐르는 긴 드레스 (격자 판 · 흰색 → 영롱한 푸른빛 · 물결진 밑단 · 오른 앞 트임) + 비치는 겉치마 (유리)"""
    J = F.J
    F.put('body', tubes(sk, [np.array([0, 43.2, 0.35]), np.array([0, 45.6, 0.35]), np.array([0, 48.6, 0.4])], [4.75, 5.05, 3.9], [3.15, 3.3, 2.65], 14, CLOTH, side=X_))
    belt = []
    for k in range(14):
        a = TAU * (k + 0.5) / 14
        if math.cos(a) < -0.93: continue                                                      # 앞 가운데 = 모래시계 고리 자리
        c = np.array([math.sin(a) * 5.25, 48.0, -math.cos(a) * 3.45 + 0.35])
        tg = np.array([math.cos(a), 0, math.sin(a)])
        belt += rect_link(sk, c, tg, Y_, 2.2, 1.1 if k % 2 else 0.8, 0.26, GOLD)
    F.put('body', belt)
    bk = np.array([0, 48.0, -3.45])
    F.add('buckle', 'body', bk, hourglass(sk, bk, 2.2, 0.85) + ring_band(sk, bk - Z_ * 0.2, np.eye(3), 1.6, 0.4, 0.4, 14, GOLD, dens=6))
    for sg, s_ in ((-1, 'r'), (1, 'l')):                                                     # 엉덩이 옆으로 늘어진 사슬 (흔들림)
        a0 = np.array([sg * 5.35, 47.6, -0.4])
        par = 'body'
        for k in range(3):
            d = nrm(np.array([sg * 0.35, -1, -0.2]))
            c = a0 + d * (1.4 + 2.6 * k)
            u = nrm(np.cross(d, X_ if k % 2 == 0 else Z_))
            nm = f'hchain_{s_}{k}'
            F.add(nm, par, a0 + d * (2.6 * k), rect_link(sk, c, d, u, 2.8, 1.4, 0.3, GOLD)); par = nm
    NA, NV = 22, 8
    groups = [(0, 3), (3, 6), (6, 8)]
    par = 'body'
    for gi, (r0, r1) in enumerate(groups):
        cs, gl = [], []
        for j in range(r0, r1):
            v0, v1 = j / NV, (j + 1) / NV
            for i in range(NA):
                a0, a1 = TAU * i / NA - math.pi, TAU * (i + 1) / NA - math.pi
                am = (a0 + a1) / 2
                if GOWN_SLIT[0] < am < GOWN_SLIT[1] and v0 >= GOWN_SLIT[2]: continue
                P00, P10, P01, P11 = gown_pt(a0, v0), gown_pt(a1, v0), gown_pt(a0, v1), gown_pt(a1, v1)
                c = (P00 + P10 + P01 + P11) / 4
                du, dv = (P10 + P11 - P00 - P01) / 2, (P01 + P11 - P00 - P10) / 2
                n = nrm(np.cross(du, dv))
                if np.dot(n, c - np.array([0, c[1], 0.35])) < 0: n = -n
                Rm = tex_kit.basis(-dv, n)
                m = gown_mat(v0, v1, hem=(j == NV - 1), seed=i)
                cs.append(sk.rbox(c, Rm, (np.linalg.norm(du) * 1.1, np.linalg.norm(dv) * 1.08, 0.3), m, dens=2.6))
                if j >= 2:
                    Q = lambda a, v: gown_pt(a, v) + nrm(np.array([math.sin(a), 0, -math.cos(a)])) * (0.6 + 0.6 * v)
                    q00, q10, q01, q11 = Q(a0, v0), Q(a1, v0), Q(a0, v1), Q(a1, v1)
                    qc = (q00 + q10 + q01 + q11) / 4
                    qu, qv = (q10 + q11 - q00 - q01) / 2, (q01 + q11 - q00 - q10) / 2
                    gl.append(sk.rbox(qc, tex_kit.basis(-qv, n), (np.linalg.norm(qu) * 1.04, np.linalg.norm(qv) * 1.02, 0.05), SHEER, faces={**NOF, 'south': SHEER, 'north': SHEER}, dens=1.6))
        piv = gown_pt(0, r0 / NV) * np.array([0, 1, 0]) + np.array([0, 0, 0.35])
        nm = f'gown{gi}_cut'
        F.add(nm, par, piv, cs)
        if gl: F.add(f'gown{gi}_glass', nm, piv, gl)
        par = nm
    J['gown'] = len(groups)
    J['skirts'] = []


def sleeves(F, sk):
    """늘어진 소매 (여신): 위팔에서 넓게 벌어져 손목 아래로 길게 드리운 흰 비단 → 영롱한 푸른 끝 · 금 테 · 팔을 따라 움직임"""
    J = F.J
    for s, sg in (('r', 1), ('l', -1)):
        sh, el = J[f'sh_{s}'], J[f'el_{s}']
        a = sh + (el - sh) * 0.45 + np.array([0, 0, 0.9])
        pts = cubic(a, el + np.array([sg * 1.6, -1.5, 0.6]), el + np.array([sg * 3.0, -8.5, 1.2]), el + np.array([sg * 3.6, -15.0, 1.6]), 7)
        ws = [2.6, 3.6, 4.6, 5.4, 5.8, 5.6, 4.8]
        zh = [nrm(np.array([sg * 0.35, 0, -1.0]))] * 6
        mats = [cape_mat(0.1 + 0.85 * k / 6, 0.1 + 0.85 * (k + 1) / 6, seed=70 + k) for k in range(6)]
        F.add(f'sleeve_{s}_cut', f'arm_{s}', pts[0], ribbon(sk, pts[:3], ws[:3], mats[:2], zh[:2], th=0.3, over=1.06))
        F.add(f'sleeve_{s}_lo_cut', f'sleeve_{s}_cut', pts[2], ribbon(sk, pts[2:], ws[2:], mats[2:], zh[2:], th=0.3, over=1.06))
        F.add(f'sleeve_{s}_add', f'sleeve_{s}_lo_cut', pts[3], ribbon(sk, pts[3:], [w * 0.88 for w in ws[3:]], [cape_glow(0.55 + 0.12 * k, 0.67 + 0.12 * k) for k in range(3)], zh[3:], th=0.45, over=1.0, dens=1.5, flat=True))
        cuff = el + (np.array([0, 0, 0]))
        F.put(f'sleeve_{s}_cut', ring_band(sk, a + np.array([0, 0, -0.9]), tex_kit.basis(nrm(el - sh), Z_), 1.8, 0.35, 0.4, 12, GOLD, dens=6))


def veil(F, sk):
    """머리 뒤로 드리운 비치는 베일 (여신): 시계판 왕관 뒤에서 어깨 아래까지 · 옅은 하늘빛 유리 · 가장자리 금빛 별 · 흔들림"""
    J = F.J
    hc, hu, fh, hx = J['HC'], J['hu'], J['fh'], J['hx']
    top = hc + hu * 3.2 - fh * 0.8
    rows = [(0.0, 4.6, 0.0), (0.3, 7.4, 1.8), (0.6, 9.6, 3.2), (1.0, 11.0, 4.4)]
    cs = []
    for k in range(len(rows) - 1):
        (q0, w0, z0), (q1, w1, z1) = rows[k], rows[k + 1]
        p0 = top - hu * (18.0 * q0) - fh * (2.6 + z0); p1 = top - hu * (18.0 * q1) - fh * (2.6 + z1)
        for i in range(5):
            u0, u1 = (i / 5 - 0.5), ((i + 1) / 5 - 0.5)
            curve = lambda u, q: -fh * (1.6 * (1 - (2 * u) ** 2) * (0.4 + q))
            A, B_ = p0 + hx * (u0 + u1) / 2 * w0 + curve((u0 + u1) / 2, q0), p1 + hx * (u0 + u1) / 2 * w1 + curve((u0 + u1) / 2, q1)
            cs.append(sk.seg(A, B_, (w0 + w1) / 2 / 5 * 1.12, 0.05, SHEER, z_hint=-fh, over=1.04, faces={**NOF, 'south': SHEER, 'north': SHEER}, dens=1.8))
    F.add('veil_glass', 'head', top, cs)
    stars = []
    for i in range(7):
        q = i / 6
        p = top - hu * 18.0 - fh * (2.6 + 4.4) + hx * (q - 0.5) * 11.0 + Y_ * 0.3
        stars += sparkle(sk, p, -fh, 1.2, STAR_ADD, STAR_GLOW)
    F.add('veil_add', 'veil_glass', top, stars)


def hand(F, sk, s, el, wr, curl, palm):
    """손: 손바닥 + 손가락 넷 + 엄지 (펼침 · curl = 굽힘)"""
    d = nrm(wr - el)
    side = nrm(np.cross(d, palm))
    pc = wr + d * 0.9
    cs = [sk.seg(wr, wr + d * 1.7, 1.75, 0.62, SUIT, z_hint=palm, dens=6)]
    for k in range(4):
        o = side * (k - 1.5) * 0.34
        a = wr + d * 1.5 + o
        dd = nrm(d + side * (k - 1.5) * 0.14 + palm * curl)
        L = (1.25, 1.45, 1.4, 1.1)[k]
        m = a + dd * L * 0.55
        e = m + nrm(dd + palm * curl) * L * 0.5
        cs += [sk.seg(a, m, 0.3, 0.28, SUIT, z_hint=palm, dens=7), sk.seg(m, e, 0.26, 0.24, SUIT, z_hint=palm, dens=7)]
    a = wr + d * 0.5 - side * 0.65
    cs.append(sk.seg(a, a + nrm(d - side * 0.8 + palm * 0.3) * 1.2, 0.32, 0.3, SUIT, z_hint=palm, dens=7))
    F.add(f'hand_{s}', f'fore_{s}', wr, cs)


CAPE_C = np.array([0.0, 60.0, 0.4])                                                         # 어깨 망토 둥근 명암의 가운데


def capelet_mat(v0, v1, hem=False, seed=0):
    """어깨 망토 (v1.240 · 사용자 그림의 짧은 어깨 케이프 · 색은 여신에 맞춤): 흰 비단 · 세로 주름 · 아래 남빛 띠 + 금 줄 · 밑단 = 뾰족한 삼각 술 (잘라 그림 · 남빛 테 · 끝이 푸른빛)"""
    def f(P, N, S, T):
        v = v0 + (v1 - v0) * T
        d = P - CAPE_C
        n = d / np.maximum(np.linalg.norm(d, axis=-1), 1e-6)[..., None]
        k = 0.7 + 0.38 * np.clip(np.sum(n * LIGHT, axis=-1), 0, 1) - 0.18 * sstep(0.55, 1.0, v)
        ang = np.arctan2(P[..., 0], -(P[..., 2] - 0.4))
        w = fbm(_q(P, np.array([0.45, 0.1, 0.45]), seed), 1.0, 61)
        fold = 0.5 + 0.5 * np.sin(ang * 14 + w * 3.0)
        c = mix(C(164, 178, 212)[None, None], C(250, 251, 255)[None, None], np.clip(k * (0.82 + 0.24 * fold * sstep(0.2, 0.6, v)), 0, 1)[..., None])
        band = sstep(0.74, 0.76, v)                                                          # 아래 남빛 띠 (금 줄 둘)
        navy = mix(C(12, 20, 62)[None, None], C(40, 66, 150)[None, None], np.clip(k - 0.35, 0, 1)[..., None] * 1.5)
        c = mix(c, navy, band[..., None])
        gl = np.exp(-((v - 0.765) / 0.008) ** 2) + np.exp(-((v - 0.84) / 0.006) ** 2) * 0.8
        c = mix(c, _gold_px(np.clip(k, 0, 1), np.ones_like(v)), np.clip(gl, 0, 1)[..., None])
        a = np.full_like(v, 255.0)
        if hem:                                                                               # 뾰족한 삼각 술: 술 사이는 잘라 냄 · 남빛 테 · 끝으로 갈수록 영롱한 푸른빛
            saw = np.abs(((ang * 24 / TAU) % 1.0) - 0.5) * 2                                  # 0 = 술 가운데 · 1 = 술 사이
            tip = 0.86 + 0.14 * (1 - saw)
            inside = v <= tip
            depth = np.clip((v - 0.86) / 0.14, 0, 1)
            c = np.where((v > 0.86)[..., None], blue_at(0.25 + 0.7 * depth) * (0.8 + 0.25 * (1 - saw))[..., None], c)
            edge = inside & (v > tip - 0.012)
            c = np.where(edge[..., None], C(10, 16, 48)[None, None], c)
            a = np.where(inside, 255.0, 0.0)
        return np.dstack([np.clip(c, 0, 255), a])
    return _fm(f, edge=1.0, top=1.0, bot=1.0)


def _ell(a, sx, sz):
    return 1.0 / math.sqrt((math.sin(a) / sx) ** 2 + (math.cos(a) / sz) ** 2)


def cape_pt(a, v):
    """어깨 망토 위의 점 (a = 각 · 0 = 앞 (-z) · + = 오른쪽 +x · v 0 = 목 → 0.35 = 어깨 끝 → 1 = 밑단): 목에서 어깨 위로 봉긋하게 덮고 · 아래로 조금 퍼지며 떨어짐"""
    d = np.array([math.sin(a), 0.0, -math.cos(a)])
    s0, s1 = _ell(a, 2.45, 2.25), _ell(a, 8.6, 4.1)
    if v <= 0.35:
        t = v / 0.35
        s = (1 - t) ** 2 * s0 + 2 * t * (1 - t) * s1 * 0.8 + t * t * s1 * 0.97
        y = (1 - t) ** 2 * 64.3 + 2 * t * (1 - t) * 66.1 + t * t * 62.4
    else:
        t = (v - 0.35) / 0.65
        y2 = 55.7 + 0.6 * math.cos(a)
        s = (1 - t) ** 2 * s1 * 0.97 + 2 * t * (1 - t) * s1 * 1.03 + t * t * s1 * 1.26
        y = (1 - t) ** 2 * 62.4 + 2 * t * (1 - t) * 59.6 + t * t * y2
    return CAPE_C * np.array([1, 0, 1]) + d * s + Y_ * y


def cape_open(v): return 0.3 + 0.5 * v                                                     # 앞 트임 반각 (목에서 좁고 아래로 벌어지는 V · 목걸이 · 앞섶이 보임)
CAPE_SIDE = 5.0                                                                              # 이 |x| 밖 = 팔을 들면 같이 들리는 어깨 자락


def capelet(F, sk):
    """어깨 망토 (v1.240 · 금빛 어깨 갑 대신): 목에서 어깨를 덮는 짧은 흰 비단 케이프 · 앞은 트임 · 아래 남빛 띠 · 뾰족한 삼각 술 밑단
    · 가운데 (가슴 뼈대) + 양 어깨 자락 (팔을 들면 같이 들림 · 애니가 팔 회전을 줄여 따라감)"""
    NA, NV = 32, 7
    vs = [0, 0.12, 0.24, 0.35, 0.55, 0.76, 0.86, 1.0]
    parts = {'c': [], 'r': [], 'l': []}
    for j in range(NV):
        v0, v1 = vs[j], vs[j + 1]
        m = capelet_mat(v0, v1, hem=(j == NV - 1), seed=j)
        for i in range(NA):
            a0, a1 = TAU * i / NA - math.pi, TAU * (i + 1) / NA - math.pi
            am = (a0 + a1) / 2
            if abs(am) < cape_open((v0 + v1) / 2): continue
            P00, P10, P01, P11 = cape_pt(a0, v0), cape_pt(a1, v0), cape_pt(a0, v1), cape_pt(a1, v1)
            c = (P00 + P10 + P01 + P11) / 4
            du, dv = (P10 + P11 - P00 - P01) / 2, (P01 + P11 - P00 - P10) / 2
            n = nrm(np.cross(du, dv))
            if np.dot(n, c - np.array([0, c[1], 0.4])) < 0: n = -n
            cell = sk.rbox(c, tex_kit.basis(-dv, n), (np.linalg.norm(du) * 1.12, np.linalg.norm(dv) * 1.1, 0.34), m, dens=3.0)
            parts['r' if c[0] > CAPE_SIDE else 'l' if c[0] < -CAPE_SIDE else 'c'].append(cell)
    tr = []                                                                                  # 앞 트임 가장자리 · 목 둘레 금 테
    for sg in (-1, 1):
        q = lambda v: cape_pt(sg * cape_open(v), v)
        pts = [q(v) + nrm(q(v) - np.array([0, q(v)[1], 0.4])) * 0.25 for v in np.linspace(0.0, 0.84, 9)]
        for p0, p1 in zip(pts, pts[1:]):
            tr.append(sk.seg(p0, p1, 0.4, 0.3, GOLD, z_hint=nrm(np.array([sg * 0.6, 0, -1.0])), over=1.12, dens=6))
    ring = [cape_pt(a, 0.02) + Y_ * 0.15 for a in np.linspace(cape_open(0.02), TAU - cape_open(0.02), 17)]
    for p0, p1 in zip(ring, ring[1:]):
        tr.append(sk.seg(p0, p1, 0.45, 0.3, GOLD, z_hint=Y_, over=1.1, dens=6))
    F.add('cape_cut', 'chest', np.array([0, 64.3, 0.4]), parts['c'] + tr)
    for s, sg in (('r', 1), ('l', -1)):
        F.add(f'cape_{s}_cut', 'cape_cut', np.array([sg * CAPE_SIDE, 64.6, 0.4]), parts[s])


def hourglass(sk, c, h, r, glass=True):
    """작은 모래시계 (금 받침 위아래 · 유리 두 구 · 모래)"""
    out = [sk.cbox(c + Y_ * h * 0.5, (r * 2.4, h * 0.12, r * 2.4), GOLD, dens=6), sk.cbox(c - Y_ * h * 0.5, (r * 2.4, h * 0.12, r * 2.4), GOLD, dens=6)]
    for k in range(3):
        a = TAU * k / 3
        p = c + np.array([math.cos(a) * r * 1.1, 0, math.sin(a) * r * 1.1])
        out.append(sk.cbox(p, (0.18, h, 0.18), GOLD, dens=6))
    out.append(sk.cbox(c + Y_ * h * 0.22, (r * 1.2, h * 0.26, r * 1.2), SAND, dens=6))
    out.append(sk.cbox(c - Y_ * h * 0.33, (r * 1.6, h * 0.2, r * 1.6), SAND, dens=6))
    return out


def hair_cap(F, sk, hc, hu, fh, hx):
    """머리를 덮은 푸른 머리 (얼굴 앞만 비움)"""
    c0 = hc + hu * 0.5 - fh * 0.4
    ax = (3.05, 3.3, 3.05)
    cs = []
    nb = 7
    M = hair_mat(0.0, 0.18, seed=1)
    for j in range(nb):
        p0, p1 = -0.6 + (math.pi / 2 + 0.6) * j / nb, -0.6 + (math.pi / 2 + 0.6) * (j + 1) / nb
        pm = (p0 + p1) / 2
        ni = max(4, int(round(9 * math.cos(pm) + 3)))
        for i in range(ni):
            tm = TAU * (i + 0.5) / ni
            n_l = np.array([math.cos(pm) * math.sin(tm), math.sin(pm), math.cos(pm) * math.cos(tm)])
            if n_l[2] > 0.2 and n_l[1] < 0.6 and abs(n_l[0]) < 0.75: continue
            n = hx * n_l[0] + hu * n_l[1] + fh * n_l[2]
            p = c0 + (hx * n_l[0] * ax[0] + hu * n_l[1] * ax[1] + fh * n_l[2] * ax[2])
            tu = nrm(np.cross(hu, n)) if abs(np.dot(hu, n)) < 0.999 else hx
            tv = nrm(np.cross(n, tu))
            w = math.cos(pm) * TAU / ni * ax[0] * 1.3 + 0.5
            h = (math.pi / 2 + 0.6) / nb * ax[1] * 1.35
            cs.append(sk.rbox(p, np.column_stack([tu, tv, n]), (w, h, 0.75), M, dens=5))
    F.add('hair', 'head', c0, cs)


def hair_vmat(yt, yb, seed=0):
    """앞머리 · 옆머리 관 (v1.244): 높이로 칠함 (위 yt = 뿌리 짙은 사파이어 → 아래 yb = 끝 맑은 하늘빛) — 한 가닥을 한 관으로 지어 마디 이음매 없음 · 가는 결 · 윤기 띠"""
    def f(P, N, S, T):
        u = np.clip((yt - P[..., 1]) / max(yt - yb, 1e-3), 0, 1)
        n = fbm(_q(P, np.array([1.6, 0.25, 1.6]), seed), 1.0, 47)
        st = 0.5 + 0.5 * np.sin(n * 9.0 + seed)
        c = blue_at(0.08 + 0.82 * u) * (0.72 + 0.36 * st)[..., None]
        band = np.exp(-((u - 0.22) / 0.08) ** 2) * (0.5 + 0.5 * st)
        c = mix(c, C(210, 240, 255)[None, None], (band * 0.5)[..., None])
        return np.clip(c * shade(N, 0.7, 0.42), 0, 255)
    return _fm(f, top=1.04, bot=0.82)


def front_hair(F, sk, hc, Rh):
    """앞머리 · 옆머리 (v1.244 "흘러내리고 부피감 있게 · 지금은 너무 뻣뻣"): 납작한 띠 대신 가닥마다 둥근 관 (폭 > 두께 · 가운데 볼록 · 끝 뾰족)
    · 앞머리 = 가르마에서 얼굴 구체를 따라 옆으로 휘어 내려오다 (위 절반) 아래로 흘러내림 (아래 절반 · 물결) · 안쪽 큰 가닥 + 바깥 가는 가닥 두 겹 · 가운데 잔머리
    · 옆머리 = 구체 옆에서 가슴께까지 물결치며 흘러내리는 굵은 관 두 가닥씩 (위 · 아래 마디 뼈대 = 흔들림)"""
    hx, hu, fh = Rh[:, 0], Rh[:, 1], Rh[:, 2]
    oc = hc + fh * ORB_O + hu * 0.15                                                         # 얼굴 구체 가운데 (face_orb 와 같음)
    k_ = ORB_K
    D = lambda th, ph: hu * math.cos(th) + math.sin(th) * (fh * math.cos(ph) + hx * math.sin(ph))
    def outside(p, rmin):                                                                     # 구체 앞쪽에서는 반지름 rmin 밖으로 밀어냄 (묻히지 않게)
        d = p - oc; r = np.linalg.norm(d)
        return oc + d / r * rmin if r < rmin and np.dot(d, fh) > -0.5 else p
    def htube(pts, wx, wz, mat, n=5):
        """가닥 관: 폭 축 = 구체 바깥 방향 × 진행 방향"""
        t0 = nrm(pts[1] - pts[0]); side = nrm(np.cross(nrm(pts[0] - oc), t0))
        return [c for sg in tube(sk, pts, wx, wz, n, mat, over=1.14, dens=3.4, side=side) for c in sg]
    yt, yb = (oc + hu * 4.6 * k_)[1], (oc - hu * 4.0 * k_)[1]
    cs = []
    m = 9
    for layer, (R0, wmul, kk) in enumerate(((4.35 * k_, 1.0, 4), (4.85 * k_, 0.7, 4))):                   # 안쪽 큰 가닥 · 바깥 가는 가닥 (반 칸 엇갈림) = 부피
        for sg in (1, -1):
            for k in range(kk):
                q = k + 0.5 * layer
                ph0, th0 = math.radians(7 + 10 * q), math.radians(3 + 3 * q)
                ph1, th1 = math.radians(40 + 12 * q), math.radians(44 + 6 * q)
                Lf = 1.3 + 1.1 * q                                                            # 흘러내리는 길이 (바깥일수록 길게)
                pts = []
                for j in range(m):
                    t = j / (m - 1)
                    if t <= 0.5:                                                              # 위 절반: 구체를 따라 옆으로 휘어 내려옴 (가운데 볼록)
                        a = t / 0.5; e = a * a * (3 - 2 * a)
                        p = oc + D(th0 + (th1 - th0) * a, sg * (ph0 + (ph1 - ph0) * e)) * (R0 + 0.55 * math.sin(math.pi * a * 0.9))
                    else:                                                                     # 아래 절반: 아래로 흘러내리며 살짝 바깥으로 · 물결
                        a = (t - 0.5) / 0.5
                        top = oc + D(th1, sg * ph1) * (R0 + 0.55 * math.sin(math.pi * 0.9))
                        out = nrm(D(math.radians(90), sg * ph1) - hu * 0)
                        p = top - hu * Lf * a + out * (0.5 * a * a) + hx * sg * 0.35 * math.sin(a * math.pi * 1.5 + q)
                    pts.append(outside(p, R0 + 0.2))
                wx = [(1.25 + 0.45 * math.sin(math.pi * min(1, j / (m - 1) * 1.3))) * wmul * (1 - 0.92 * sstep(0.45, 1.0, j / (m - 1))) + 0.1 for j in range(m)]
                wz = [w * 0.62 + 0.08 for w in wx]
                cs += htube(pts, wx, wz, hair_vmat(yt, yb, seed=k + 3 * layer + (0 if sg > 0 else 7)))
    for k, (phd, thd, Lf, wg) in enumerate(((-12, 44, 1.4, 0.75), (10, 50, 1.9, 0.7))):   # 가운데 잔머리 (S 자로 흘러내림)
        pts = []
        for j in range(m):
            t = j / (m - 1)
            if t <= 0.5:
                a = t / 0.5
                p = oc + D(math.radians(3 + (thd - 3) * a), math.radians(phd + 6 * math.sin(a * 2.4 + k))) * (4.65 * k_ + 0.35 * math.sin(math.pi * a))
            else:
                a = (t - 0.5) / 0.5
                p = oc + D(math.radians(thd), math.radians(phd)) * 4.65 * k_ - hu * Lf * a + hx * 0.45 * math.sin(a * math.pi * 1.4 + k)
            pts.append(outside(p, 4.7 * k_))
        wx = [wg * (1 - 0.9 * sstep(0.4, 1.0, j / (m - 1))) + 0.1 for j in range(m)]
        cs += htube(pts, wx, [w * 0.6 + 0.06 for w in wx], hair_vmat(yt, yb, seed=30 + k), n=4)
    F.add('bangs', 'head', hc + hu * 3.0, cs)
    names = []
    for s, sg in (('r', 1), ('l', -1)):                                                       # 옆머리: 구체 옆 → 가슴께까지 물결치며 흘러내리는 굵은 관 (앞 · 뒤 두 가닥)
        for v, (phd, r0, L, w0) in enumerate(((74, 4.5, 11.0, 1.7), (98, 4.3, 9.0, 1.45))):
            ph = math.radians(phd) * sg
            P0 = oc + D(math.radians(30), ph) * r0 * k_
            P1 = oc + D(math.radians(80), ph) * (r0 * k_ + 0.6)
            P2 = oc + hx * sg * 5.0 * k_ - hu * (L * 0.5) + fh * (1.2 - 0.5 * v)
            P3 = oc + hx * sg * (4.2 + 0.3 * v) * k_ - hu * L + fh * (2.0 - 0.6 * v)
            mm = 11
            pts = cubic(P0, P1, P2, P3, mm)
            for j in range(2, mm):                                                            # 물결
                a = j / (mm - 1)
                pts[j] = pts[j] + hx * sg * 0.45 * math.sin(a * math.pi * 2.2 + v) * a + fh * 0.3 * math.sin(a * math.pi * 1.7 + v) * a
            wx = [(w0 + 0.5 * math.sin(math.pi * min(1, j / (mm - 1) * 1.6))) * (1 - 0.9 * sstep(0.5, 1.0, j / (mm - 1))) + 0.12 for j in range(mm)]
            wz = [w * 0.7 + 0.08 for w in wx]
            mat = hair_vmat((P0)[1] + 1, P3[1], seed=40 + v)
            segs = tube(sk, pts, wx, wz, 5, mat, over=1.14, dens=3.4, side=nrm(np.cross(nrm(pts[0] - oc), nrm(pts[1] - pts[0]))))
            h = 5
            F.add(f'slock_{s}{v}_0', 'head', pts[0], [c for sg_ in segs[:h] for c in sg_])
            F.add(f'slock_{s}{v}_1', f'slock_{s}{v}_0', pts[h], [c for sg_ in segs[h:] for c in sg_])
            F.J.setdefault('slock_dirs', {})[f'{s}{v}'] = [nrm(pts[h] - pts[0]), nrm(pts[-1] - pts[h])]
            names.append(f'{s}{v}')
    F.J['slocks'] = names


def face_orb(F, sk, hc, Rh):
    """얼굴 = 시공간이 일그러지는 둥근 구체: 바탕 구멍 · 빛 고리 · 빨려 드는 눈금 · 지평선 · 두 나선 (판 · 얼굴 앞 면 위) + 유리 구체 + 궤도 고리 둘"""
    hx, hu, fh = Rh[:, 0], Rh[:, 1], Rh[:, 2]
    Fc = hc + fh * 2.85 + hu * 0.15                                                         # 둥근 머리 앞면 바로 앞 (뼈대 face 의 +z = 얼굴 앞)
    FACE_C[0] = Fc - fh * 0.9
    ps = 0.6                                                                                 # 판 크기 (유리 구 안에 들게)
    F.J['FACE'] = Fc
    F.add('face', 'head', Fc, None, rot=tex_kit.euler_of(Rh))
    def pl(z, w, mat, dens=10, two=False):
        fc = dict(NOF); fc['south'] = mat
        if two: fc['north'] = mat
        return sk.rbox(Fc + np.array([0, 0, z]), np.eye(3), (w, w, 0.02), mat, faces=fc, dens=dens)
    F.add('face_hole_cut', 'face', Fc, [pl(-0.2, 6.2 * ps, HOLE, dens=12)])                      # 판은 기울이기 전 xy 면 (뼈대 face 가 머리 축으로 돎 · 교훈 91)
    F.add('face_lens_add', 'face', Fc, [pl(0.05, 6.8 * ps, LENS, dens=12)])
    F.add('face_ticks_add', 'face', Fc, [pl(0.2, 6.6 * ps, TICKS, dens=14)])
    F.add('face_horizon_add', 'face', Fc, [pl(0.35, 5.8 * ps, HORIZON, dens=12)])
    F.add('face_swirl_a_add', 'face', Fc, [pl(0.5, 7.2 * ps, SWIRL_A, dens=10)])
    F.add('face_swirl_b_add', 'face', Fc, [pl(0.7, 8.0 * ps, SWIRL_B, dens=9)])
    oc = Fc + np.array([0, 0, -(2.85 - ORB_O)])                                             # 판 기준 (뼈대 face 좌표) 유리 구 가운데
    F.add('face_orb_glass', 'face', Fc, sphere_shell(sk, oc, ORB_R, ORB_GLASS, nb=8, th=0.1, dens=5, keep_z=-0.35))
    for i, (tilt, yaw) in enumerate(((0.3, 0.2), (-0.35, -0.45))):                          # 궤도 고리 = 구체를 둘러싼 둥근 테 (v1.234 · 비스듬하면 눈 모양으로 보임) · 기울인 쉬는 자세 + z 로 돎
        F.add(f'face_orbit{i}', 'face', oc, None, rot=tex_kit.euler_of(ry_(yaw) @ rx_(tilt)))
        F.add(f'face_orbit{i}_add', f'face_orbit{i}', oc, ring_band(sk, oc, np.eye(3), ORB_R + 0.25 + 0.3 * i, 0.12, 0.12, 44, ORBIT, dens=2, over=1.05))


def crown(F, sk, hc, Rh):
    """머리 위 작은 시계판 왕관 (그림): 시계판 + 금 테 · 금빛 빛살 · 양옆 작은 가시"""
    hx, hu, fh = Rh[:, 0], Rh[:, 1], Rh[:, 2]
    c = hc + hu * 3.6 + fh * 1.6
    Rm = np.column_stack([hx, nrm(hu - fh * 0.25), nrm(fh + hu * 0.25)])
    cs = [plate(sk, c, Rm, 3.4, 3.4, DIAL, two=False, dens=14)]
    cs += ring_band(sk, c + Rm[:, 2] * 0.15, Rm, 1.62, 0.32, 0.4, 16, GOLD, dens=5)
    for sg in (-1, 1):
        b = c + hx * sg * 1.5 - hu * 0.3
        cs += spike3d(sk, b, nrm(hx * sg * 0.7 + hu), fh, 2.4, 0.55, 0.35, GOLD)
    F.add('crown_cut', 'head', c, cs)
    rays = []
    for k in range(9):
        a = math.pi * (0.1 + 0.8 * k / 8)
        d = Rm[:, 0] * math.cos(a) + Rm[:, 1] * math.sin(a)
        p = c + d * (2.4 + 1.6 * (k % 2))
        rays.append(sk.rbox(p + d * 1.2, np.column_stack([np.cross(d, Rm[:, 2]), d, Rm[:, 2]]), (0.35, 2.6 + (k % 2) * 1.2, 0.05), RAY, faces={**NOF, 'south': RAY, 'north': RAY}, dens=4))
    F.add('crown_rays_add', 'crown_cut', c, rays)


# ---------------------------------------------------------------- 머리카락 · 망토 꼬리
def flow_hair(F, sk):
    """영롱한 푸른 긴 머리 (그림): 뒤통수에서 등 뒤로 넘어가 그림 오른쪽 (+x) 아래로 넓게 물결치며 쏟아짐 (허리 · 넓적다리께까지) · 가닥 22 + 얼굴 옆 앞머리 넷
    가닥마다 마디 여덟 · 뼈대 셋 (흔들림) · 결 칠한 머리 + 넓은 두 면에만 더해 빛나는 겉 결 (`hflow<i>_<k>_add`)"""
    J = F.J
    hc, hu, fh, hx = J['HC'], J['hu'], J['fh'], J['hx']
    rng = np.random.default_rng(37)
    names = []
    N_ = 22
    for i in range(N_):
        q = i / (N_ - 1)
        th0 = math.pi * (0.15 + 0.7 * q)                                                     # 뒤통수 둘레 (왼 옆 → 뒤 → 오른 옆)
        st = hc + hu * (1.6 + 0.8 * math.sin(th0)) + hx * (-2.6 * math.cos(th0)) - fh * (1.2 + 1.4 * math.sin(th0))
        mid = np.array([3.0 + 11.0 * q + rng.uniform(-1, 1), 57.0 - 4.0 * q + rng.uniform(-1.5, 1.5), 3.4 + 1.2 * q])
        end = np.array([6.0 + 22.0 * q ** 0.9 + rng.uniform(-2, 2), 40.0 - 16.0 * q + rng.uniform(-3, 3), 4.6 + 2.6 * q + rng.uniform(-0.5, 0.5)])
        pts = cubic(st, st + np.array([1.0, -3.0, 2.2]), mid, end, 9)
        for k in range(2, 8): pts[k] = pts[k] + np.array([1.4 * math.sin(k * 1.15 + i * 0.9), 0.6 * math.cos(k * 0.9 + i), 0.6 * math.cos(k + i)])
        w0 = 3.6 - 1.0 * abs(q - 0.5)
        par = 'head'
        for sg, (a0, b0) in enumerate(((0, 3), (3, 6), (6, 8))):
            cs, gs = [], []
            for k in range(a0, b0):
                u0, u1 = k / 8, (k + 1) / 8
                d = nrm(pts[k + 1] - pts[k])
                zh0 = nrm(np.array([0.35 * math.sin(k * 0.7 + i), 0.15, -1.0]))
                zh = nrm(zh0 - d * np.dot(zh0, d))
                ww = w0 * (1 - 0.62 * (u0 + u1) / 2) + 0.3
                cs.append(sk.seg(pts[k], pts[k + 1], ww, 0.55, hair_mat(u0, u1, seed=i), z_hint=zh, over=1.14, dens=3))
                if u0 >= 0.12:
                    gm = hair_glow(u0, u1, seed=i)
                    gs.append(sk.seg(pts[k], pts[k + 1], ww * 0.9, 0.75, gm, z_hint=zh, over=1.0, dens=1.5, faces={**NOF, 'south': gm, 'north': gm}))
            nm = f'hflow{i}_{sg}'
            F.add(nm, par, pts[a0], cs)
            if gs: F.add(f'{nm}_add', nm, pts[a0], gs)
            par = nm
        names.append(i)
    for j, (sg, L, q) in enumerate(((-1, 12, 0.0), (-1, 8, 0.5), (1, 11, 0.0), (1, 7.5, 0.5))):   # 얼굴 옆으로 드리운 가는 앞머리 (구체 바깥 · 물결)
        a = hc + hu * (1.8 - q) + hx * sg * (3.1 + q * 0.3) + fh * (0.6 - q)
        pts = cubic(a, a + hx * sg * 1.2 - hu * 2.5 + fh * 0.4, a + hx * sg * 0.4 - hu * L * 0.6 + fh * 0.8, a + hx * sg * 1.4 - hu * L - fh * 0.2, 7)
        cs, gs = [], []
        for k in range(6):
            u0, u1 = k / 6 * 0.85, (k + 1) / 6 * 0.85
            zh = nrm(-fh + hx * sg * 0.5)
            cs.append(sk.seg(pts[k], pts[k + 1], 1.3 - 0.16 * k, 0.45, hair_mat(u0, u1, seed=30 + j), z_hint=zh, over=1.15, dens=4))
            if k: gm = hair_glow(u0, u1, seed=30 + j); gs.append(sk.seg(pts[k], pts[k + 1], 1.25 - 0.16 * k, 0.6, gm, z_hint=zh, over=1.08, dens=2, faces={**NOF, 'south': gm, 'north': gm}))
        F.add(f'hlock{j}', 'head', a, cs)
        F.add(f'hlock{j}_add', f'hlock{j}', a, gs)
    J['hflow'] = names


_TR = [  # v1.242 오른쪽 넷 (시작 (망토 판 가장자리) · 조절점 둘 · 끝 · 뿌리 폭 · 가운데 폭 · 끝 폭) → 왼쪽은 거울 — 좌우 대칭 부채꼴
    ((6.9, 59.6, 4.6), (16, 66, 9), (26, 68, 12), (36, 61, 14), 5.0, 10.0, 5.5),
    ((8.4, 54.6, 5.8), (18, 54, 10), (28, 47, 13), (35, 37, 14), 5.5, 11.0, 6.0),
    ((9.4, 49.2, 7.0), (16, 42, 11), (22, 30, 13), (26, 16, 13), 5.5, 10.5, 6.0),
    ((5.2, 44.6, 8.4), (8, 33, 11), (10, 21, 13), (11, 7, 12), 5.5, 9.5, 5.5),
]
_mx = lambda p: (-p[0], p[1], p[2])
TAILS = _TR + [(_mx(a), _mx(b), _mx(c), _mx(d), w0, wm, w1) for a, b, c, d, w0, wm, w1 in _TR]


def sheet_pt(u, v):
    """등 뒤 망토 판 위 한 점 (u 0 = 왼 · 1 = 오른 · v 0 = 어깨 · 1 = 아래 끝): 어깨 폭 → 아래로 넓어짐 (오른쪽으로 더) · 뒤로 휘며 물결"""
    xl, xr = -6.6 - 3.6 * v, 6.6 + 3.6 * v                                                 # v1.242 좌우 대칭
    x = xl + (xr - xl) * u
    y = 63.4 - 19.0 * v
    z = 3.6 + 5.0 * v + 0.9 * math.cos((u - 0.5) * 7.0) * v + 1.6 * (u - 0.5) ** 2 * (1 - v)
    return np.array([x, y, z])


def cape(F, sk):
    """흰 망토: 등 뒤 넓은 천 한 장 (격자 판 · 물결) + 그 가장자리에서 갈라져 휘날리는 여덟 꼬리 (흰색 → 영롱한 푸른빛 · 마디 셋 · 넓은 두 면만 빛나는 끝)
    끝마다 금빛 투조 진자 (잘라 그림) + 도는 작은 톱니"""
    J = F.J
    nu, nv = 7, 6
    mant = []
    for j in range(nv):
        for i in range(nu):
            u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
            P00, P10, P01, P11 = sheet_pt(u0, v0), sheet_pt(u1, v0), sheet_pt(u0, v1), sheet_pt(u1, v1)
            c = (P00 + P10 + P01 + P11) / 4
            du, dv = (P10 + P11 - P00 - P01) / 2, (P01 + P11 - P00 - P10) / 2
            n = nrm(np.cross(dv, du))
            if n[2] < 0: n = -n                                                              # 판 법선 = 뒤 (+z) 쪽
            Rm = tex_kit.basis(-dv, n)
            mant.append(sk.rbox(c, Rm, (np.linalg.norm(du) * 1.1, np.linalg.norm(dv) * 1.1, 0.35), cape_mat(v0 * 0.35, v1 * 0.35, seed=i + 7 * j), dens=3))
    F.add('mantle', 'chest', sheet_pt(0.5, 0.0), mant)
    J['tails'] = len(TAILS)
    for i, (s0, c1, c2, e, w0, wm, w1) in enumerate(TAILS):
        n = 12
        pts = cubic(s0, c1, c2, e, n)
        ii, sx = i % 4, (1 if i < 4 else -1)                                                  # 거울 짝은 같은 물결 (대칭)
        for k in range(1, n - 1): pts[k] = pts[k] + np.array([0, 0, 1.0 * math.sin(k * 0.8 + ii)])
        ws = []
        for k in range(n):
            t = k / (n - 1)
            ws.append(w0 + (wm - w0) * sstep(0.0, 0.45, t) - (wm - w1) * sstep(0.55, 1.0, t))
        zh = []
        for k in range(n - 1):
            d = nrm(pts[k + 1] - pts[k])
            want = nrm(np.array([sx * 0.25 * math.sin(k * 0.45 + ii * 1.3), 0.15, -1.0]))
            zh.append(nrm(want - d * np.dot(want, d)))
        U0 = 0.3
        uu = [U0 + (1 - U0) * k / (n - 1) for k in range(n)]
        cuts = [0, 4, 8, n - 1]
        J.setdefault('tail_dirs', []).append([nrm(pts[cuts[g + 1]] - pts[cuts[g]]) for g in range(3)])
        J.setdefault('tail_pts', []).append([pts[c] for c in cuts])   # 꼬리 물리 (애니) 에 쓰는 마디 방향
        par = 'mantle'
        for sg in range(3):                                                                  # v1.241 복슬한 털꼬리: 둥근 심 (관) + 마디마다 둘레로 뻗어 끝 쪽으로 빗긴 털뭉치 판 (잘라 그린 가닥)
            a, b = cuts[sg], cuts[sg + 1]
            nm = f'tail{i}_{sg}_cut'
            cs, gl = [], []
            for k in range(a, b):
                p0, p1 = pts[k], pts[k + 1]
                d = nrm(p1 - p0)
                r0, r1 = ws[k] * 0.27, ws[k + 1] * 0.27
                cs += tubes(sk, [p0, p1], [r0, r1], [r0 * 0.9, r1 * 0.9], 7, fur_mat(uu[k], uu[k + 1], seed=i + k, cut=False), dens=2.4, side=zh[k])
                e1 = nrm(zh[k] - d * np.dot(zh[k], d)); e2 = np.cross(d, e1)
                M = 8
                for j in range(M):                                                            # 털뭉치 (마디마다 반 칸씩 돌려 엇갈림)
                    ph = TAU * (j + 0.5 * (k % 2)) / M + ii * 0.7
                    rh = e1 * math.cos(ph) + e2 * math.sin(ph)
                    L = ws[k] * (0.62 + 0.1 * math.sin(j * 2.3 + k * 1.7 + i))
                    fd = nrm(rh * 0.75 + d * 1.0)
                    tg = nrm(np.cross(fd, rh))
                    root = (p0 + p1) / 2 - d * np.linalg.norm(p1 - p0) * 0.3 + rh * (r0 + r1) / 2 * 0.5
                    c0 = root + fd * L * 0.5
                    fm = fur_mat(uu[k], uu[k + 1], seed=i * 7 + k + j)
                    cs.append(sk.rbox(c0, tex_kit.basis(fd, np.cross(tg, fd)), (ws[k] * 0.62, L, 0.12), fm, faces={**NOF, 'south': fm, 'north': fm}, dens=2.6))
            F.add(nm, par, pts[a], cs)
            if gl: F.add(f'tail{i}_{sg}_add', nm, pts[a], gl)
            par = nm
        d = nrm(pts[-1] - pts[-2]); nz = zh[-1]
        Rt = np.column_stack([nrm(np.cross(-d, nz)), -d, nz])                                 # 판 y = 꼬리 쪽 (진자 머리) · 뾰족 끝이 바깥
        tip = [sk.seg(pts[-1] - d * 0.2, pts[-1] + d * 0.7, ws[-1] * 0.95, 0.7, GOLD, z_hint=nz, dens=4)]
        tip.append(plate(sk, pts[-1] + d * 4.6, Rt, 5.6, 9.2, SPADE, dens=10))
        F.add(f'tail{i}_tip_cut', par, pts[-1], tip)
        gc = pts[-1] + d * 1.2
        Rg = np.column_stack([nrm(np.cross(d, nz)), d, nz])
        F.add(f'tail{i}_gear_rest', f'tail{i}_tip_cut', gc, None, rot=tex_kit.euler_of(Rg))
        F.add(f'tail{i}_gear_cut', f'tail{i}_gear_rest', gc, [plate(sk, gc + Z_ * 0.05, np.eye(3), 4.2, 4.2, gear_plate(r_band=(0.5, 0.66), teeth=(0.66, 0.76, 16), spikes=(6, 1.0, 0.09), chain=(0.36, 10)), dens=10)])
        F.add(f'tail{i}_tip_add', f'tail{i}_tip_cut', pts[-1], [plate(sk, pts[-1] + d * 3.5 - nz * 0.4, Rt, 7, 9, GEM_GLOW, dens=3)])


# ---------------------------------------------------------------- 고리 · 혼천의 · 기운 · 별 · 바늘
def rings(F, sk):
    J = F.J
    hc = J['HC']
    HC2 = hc + np.array([0.6, 1.8, 4.6])                                                    # 머리 뒤 큰 후광 (그림처럼 머리 위 · 조금 오른쪽)
    J['HALO'] = HC2
    F.add('halo_root', 'chest', HC2)
    F.add('halo_glow_add', 'halo_root', HC2, [plate(sk, HC2 + Z_ * 1.2, np.eye(3), 26, 26, HALO_GLOW, dens=1.2), plate(sk, HC2 + Z_ * 1.0, np.eye(3), 20, 20, HALO_GLOW_W, dens=1.2)])
    gear(F, sk, 'halo', 'halo_root', HC2, np.eye(3), 15.0, band_w=1.7, th=1.2, spikes3d=4,
         plate_mat=gear_plate(r_band=(0.6, 0.72), teeth=(0.72, 0.78, 36), spikes=(8, 1.0, 0.06), chain=(0.5, 22), ticks=60), pdens=7)
    F.add('rev_dial_add', 'halo_root', HC2, [plate(sk, HC2 + Z_ * 0.6, np.eye(3), 34, 34, REV_DIAL, dens=4)])   # 2페이즈 ~ (크기 속성)
    gear(F, sk, 'halo_in', 'halo_root', HC2 + Z_ * -0.3, rz_(0.2), 7.0, band_w=0.8, th=0.6, spikes3d=0,
         plate_mat=gear_plate(r_band=(0.55, 0.68), teeth=(0.68, 0.76, 20), spikes=(12, 0.98, 0.05), chain=(0.42, 14)), pdens=8)
    # 허리를 비스듬히 감은 큰 톱니 고리 (그림)
    WC = np.array([0.6, 47.2, 0.6])
    Rw = rz_(-0.22) @ rx_(math.radians(62)) @ np.eye(3)
    Rw = np.column_stack([Rw[:, 0], Rw[:, 1], Rw[:, 2]])
    J['WAIST'] = WC
    F.add('waist_root', 'body', WC)
    gear(F, sk, 'wring', 'waist_root', WC, Rw, 14.5, band_w=1.5, th=0.9, spikes3d=6,
         plate_mat=gear_plate(r_band=(0.6, 0.71), teeth=(0.71, 0.77, 40), spikes=(10, 1.0, 0.05), chain=(0.5, 26)), pdens=6)
    ch = []
    for k, (a, L) in enumerate(((-0.5, 7.0), (-0.9, 9.5), (-1.25, 6.0))):                     # 고리에 매달린 모래시계 · 금 구슬 (그림 오른쪽 아래)
        p = WC + (Rw[:, 0] * math.cos(a) + Rw[:, 1] * math.sin(a)) * 14.5 * 0.68
        for j in range(int(L)):
            ch.append(sk.cbox(p - Y_ * (j + 0.5), (0.3, 0.75, 0.3) if j % 2 else (0.18, 0.75, 0.42), GOLD, dens=6))
        e = p - Y_ * (L + 1.3)
        if k == 1: ch += hourglass(sk, e, 2.6, 0.9)
        else: ch += dome(sk, e, tex_kit.basis(Y_, -Z_), 0.9, GOLD, n_lat=2, n_lon=8, lat0=-1.2, th=0.5)
    F.add('charms', 'waist_root', WC, ch)
    F.add('charms_glass', 'charms', WC, [sk.cbox(WC + (Rw[:, 0] * math.cos(-0.9) + Rw[:, 1] * math.sin(-0.9)) * 14.5 * 0.68 - Y_ * 10.8, (1.7, 2.3, 1.7), HG_GLASS, dens=4)])
    # 발밑 작은 톱니 고리
    FC = J['to_l'] - Y_ * 1.6
    F.add('foot_root', 'shin_l', FC)
    gear(F, sk, 'fring', 'foot_root', FC, rx_(math.radians(84)), 6.2, band_w=0.8, th=0.6, spikes3d=4,
         plate_mat=gear_plate(r_band=(0.58, 0.7), teeth=(0.7, 0.78, 24), spikes=(8, 1.0, 0.07), chain=(0.46, 12)), pdens=9)


def astrolabe(F, sk):
    """떠 있는 모래시계 혼천의 (그림 왼쪽 위): 큰 톱니 고리 + 가로지르는 고리 · 가운데 모래시계 · 든 손 위 작은 혼천의 + 푸른 구슬"""
    J = F.J
    AC = np.array([-24.0, 92.0, -3.0])
    J['ASTRO'] = AC
    F.add('astro', 'float', AC)
    R0 = ry_(0.45)
    gear(F, sk, 'astro_r0', 'astro', AC, R0, 9.0, band_w=1.1, th=0.9, spikes3d=4,
         plate_mat=gear_plate(r_band=(0.62, 0.74), teeth=(0.74, 0.8, 26), spikes=(8, 1.0, 0.07), chain=(0.52, 16)), pdens=8)
    F.add('astro_r1', 'astro', AC, ring_band(sk, AC, ry_(0.45 + math.pi / 2), 6.0, 0.7, 0.7, 30, GOLD, dens=4) + ring_band(sk, AC, rx_(math.pi / 2), 5.2, 0.55, 0.55, 26, GOLD, dens=4))
    F.add('astro_hg', 'astro', AC, hourglass(sk, AC, 7.2, 2.1))
    hg = []
    for sg in (-1, 1):                                                                        # 유리 두 구 (위아래로 좁아짐)
        for k in range(3):
            y0 = sg * (0.3 + k * 1.05)
            r = 1.0 + 0.55 * k if k < 2 else 1.75
            hg.append(sk.cbox(AC + Y_ * (y0 + sg * 0.5), (r * 1.6, 1.05, r * 1.6), HG_GLASS, dens=4))
    F.add('astro_hg_glass', 'astro_hg', AC, hg)
    F.add('astro_glow_add', 'astro', AC, [plate(sk, AC + Z_ * 0.5, R0, 22, 22, HALO_GLOW_W, dens=1.2)])
    # 든 손 위 작은 혼천의
    wr, el = J['wr_l'], J['el_l']
    d = nrm(wr - el)
    HO = wr + np.array([-1.4, 0.4, -3.4])                                                   # 내린 손 앞에 떠 있는 작은 혼천의
    J['HORB'] = HO
    F.add('horb', 'hand_l', HO)
    F.add('horb_rings', 'horb', HO, ring_band(sk, HO, rx_(0.9) @ ry_(0.3), 3.6, 0.42, 0.42, 22, GOLD, dens=5) + ring_band(sk, HO, ry_(1.3), 3.1, 0.38, 0.38, 20, GOLD, dens=5)
              + ring_band(sk, HO, rx_(math.pi / 2), 2.7, 0.34, 0.34, 18, GOLD, dens=5))
    F.add('horb_core', 'horb', HO, sphere_shell(sk, HO, 1.35, BLUE_GEM, nb=5, th=0.5, dens=5))
    F.add('horb_add', 'horb', HO, [plate(sk, HO - Z_ * 1.6, np.eye(3), 7, 7, GEM_GLOW, dens=1.5), plate(sk, HO, ry_(math.pi / 2), 6, 6, GEM_GLOW, dens=1.5)])


def streaks(F, sk):
    """몸 둘레를 감도는 금빛 기운 띠 셋 (그림의 금빛 붓질 · 더해 빛남 · 뼈대마다 돎)"""
    defs = [(np.array([0, 64, 0]), 30.0, 0.6, 2.5, 6.0, 14.0, 2.8), (np.array([0, 22, 0]), 30.0, 3.6, 5.8, 6.0, -10.0, 2.6), (np.array([0, 98, 0]), 20.0, -1.0, 1.3, -2.0, 6.0, 2.0)]
    for k, (c, R, a0, a1, y0, dy, w) in enumerate(defs):
        n = 18
        pts = []
        for j in range(n + 1):
            q = j / n
            a = a0 + (a1 - a0) * q
            pts.append(c + np.array([math.cos(a) * R, y0 + dy * q, -math.sin(a) * R]))
        cs = []
        for j in range(n):
            q = (j + 0.5) / n
            d = pts[j + 1] - pts[j]
            m = (pts[j] + pts[j + 1]) / 2
            radial = nrm(np.array([m[0] - c[0], 0, m[2] - c[2]]))
            ww = w * math.sin(math.pi * q) ** 0.6 + 0.3
            mat = _fm(lambda P, N, S, T, q0=j / n, q1=(j + 1) / n: streak_fn(P, N, S, (q1 + (q0 - q1) * T)))
            cs.append(sk.rbox(m, tex_kit.basis(d, radial), (ww, np.linalg.norm(d) * 1.08, 0.05), mat, faces={**NOF, 'south': mat, 'north': mat}, dens=1.6))
        F.add(f'streak{k}_add', 'float', c, cs)
    J = F.J
    J['streaks'] = len(defs)


BL_W, BL_L = 7.0, 40.0                                                                      # v1.245 분침 검 날 (폭 · 길이 px — 1.5 배로 약 0.7 × 3.8 칸)


def _blade_hw(y):
    """날 반폭 (y = 날밑에서 px): 리카소 → 어깨 → 곧게 가늘어짐 → 브레게 달 고리 → 뾰족 끝"""
    hw = np.where(y < 2.0, 1.15, np.where(y < 5.0, 1.15 + 1.35 * sstep(2.0, 5.0, y), 2.5 - 1.15 * np.clip((y - 5.0) / 23.0, 0, 1)))
    return np.where(y > 35.0, 1.35 * np.clip((BL_L - y) / 5.0, 0, 1) ** 0.9, hw)


BL_RING = (31.6, 3.3, 0.85)                                                                   # 달 고리 (가운데 y · 바깥 반지름 · 띠 폭)


def blade_fn(P, N, S, T):
    """분침 검 날 (잘라 그림 · 두 면): 금빛 날 · 남빛 홈에 금 눈금 60 · 흰빛 날 끝 · 끝 가까이 속이 빈 브레게 달 고리"""
    x, y = (S - 0.5) * BL_W, T * BL_L
    hw = _blade_hw(y)
    rc, ro, rb = BL_RING
    rr = np.hypot(x, y - rc)
    ring = (rr <= ro) & (rr >= ro - rb)
    hole = rr < ro - rb
    body = (np.abs(x) <= hw) & ~hole & (y > 0.05)
    de = np.clip((hw - np.abs(x)) / np.maximum(hw, 1e-3), 0, 1)
    c = _gold_px(shade(N, 0.62, 0.5), np.clip(0.4 + 0.6 * de, 0, 1))
    edge = (hw - np.abs(x) < 0.3) & (y > 2.0)
    c = np.where(edge[..., None], mix(C(210, 236, 255)[None, None], C(255, 255, 255)[None, None], de[..., None] * 0), c)
    ful = (np.abs(x) < np.maximum(hw * 0.36, 0.35)) & (y > 3.0) & (y < rc - ro - 0.6)
    tick = ful & (np.abs(((y - 3.0) / 0.42) % 1.0 - 0.5) > 0.36) & (np.abs(x) < hw * 0.22 + 0.1 * (np.round((y - 3.0) / 0.42) % 5 == 0))
    c = np.where(ful[..., None], mix(C(14, 30, 96)[None, None], C(40, 80, 190)[None, None], (1 - np.abs(x) / np.maximum(hw * 0.36, 0.35))[..., None]), c)
    c = np.where(tick[..., None], C(255, 222, 140)[None, None], c)
    em = np.clip(1 - np.abs(rr - (ro - rb / 2)) / (rb / 2), 0, 1)
    c = np.where(ring[..., None], _gold_px(shade(N, 0.62, 0.5), em), c)
    a = np.where(body | ring, 255.0, 0.0)
    return np.dstack([np.clip(c, 0, 255), a])


def blade_glow_fn(P, N, S, T):
    """날 둘레 푸른 빛 (더해 그림 · 날보다 조금 넓게) · 달 고리 속 푸른 보석빛"""
    x, y = (S - 0.5) * (BL_W + 4), T * (BL_L + 4) - 2
    hw = _blade_hw(np.clip(y, 0, BL_L))
    d = np.maximum(np.abs(x) - hw, 0) + np.maximum(-y, 0) + np.maximum(y - BL_L, 0)
    rc, ro, rb = BL_RING
    rr = np.hypot(x, y - rc)
    k = np.exp(-(d / 0.7) ** 2) * 0.42 * (y > 1.0) + np.exp(-(rr / (ro - rb)) ** 2) * 0.5
    return np.clip(mix(C(50, 120, 255)[None, None], C(190, 230, 255)[None, None], np.clip(k - 0.4, 0, 1)[..., None]) * k[..., None], 0, 255)


BLADE_M = _fm(blade_fn, edge=1.0, top=1.0, bot=1.0)
BLADE_G = _fm(blade_glow_fn)


def blade(F, sk):
    """분침 검 (v1.245 다시 만듦 · 가까이 오면 내린 손에 생겨남 · 평소 크기 0): 주먹에 쥔 남빛 손잡이 · 작은 시계판 날밑 (금 톱니 테 · 양옆 갈고리)
    · 넓은 금빛 날 (남빛 홈에 금 눈금) · 끝 가까이 속이 빈 브레게 달 고리 (푸른 빛) · 푸른 보석 자루 끝 · 날 둘레 빛 (blade_add)
    날 = 손 앞 (-z) 으로 조금 아래 · 날 면이 옆을 봄 (내리벨 때 날이 앞장섬)"""
    J = F.J
    wr, el = J['wr_r'], J['el_r']
    d = nrm(wr - el)
    pc = wr + d * 1.35                                                                       # 주먹 가운데
    bd = nrm(np.array([0.08, -0.22, -1.0]))
    J['BLADE'] = pc; J['BLADE_D'] = bd
    F.add('blade', 'hand_r', pc)
    nz = nrm(X_ - bd * np.dot(X_, bd))
    up = np.cross(bd, nz)
    g0 = pc + bd * 1.6                                                                       # 날밑
    cs = [sk.seg(pc - bd * 2.6, g0, 0.62, 0.62, _fm(lambda P, N, S, T: np.clip(mix(C(20, 36, 100)[None, None], C(240, 200, 110)[None, None], (np.abs(np.sin(T * 40 + S * 6)) > 0.8)[..., None] * 1.0) * shade(N, 0.6, 0.6), 0, 255)), z_hint=nz, dens=6)]
    cs.append(sk.cbox(pc - bd * 3.3, (1.3, 1.3, 1.3), BLUE_GEM, dens=6))                       # 자루 끝 보석
    cs += ring_band(sk, pc - bd * 3.3, tex_kit.basis(bd, nz), 0.95, 0.35, 0.5, 10, GOLD, dens=7)
    Rg = np.column_stack([nz, up, bd])
    cs.append(plate(sk, g0, Rg, 5.2, 5.2, DIAL, dens=9, th=0.5))                              # 시계판 날밑 (두 면)
    cs += ring_band(sk, g0, Rg, 2.75, 0.7, 0.9, 16, GOLD, dens=6)
    for sgn in (1, -1):                                                                      # 양옆 갈고리 (날 쪽으로 휜 가시)
        b0 = g0 + up * sgn * 2.9
        cs += spike3d(sk, b0, nrm(up * sgn + bd * 0.9), nz, 3.2, 0.8, 0.5, GOLD, n=3)
    Rb = tex_kit.basis(-bd, nz)
    cs.append(plate(sk, g0 + bd * (0.3 + BL_L / 2), Rb, BL_W, BL_L, BLADE_M, dens=8, th=0.55))
    cs.append(sk.seg(g0 + bd * 0.3, g0 + bd * 27.0, 0.75, 0.75, GOLD, z_hint=nz, dens=4))       # 등뼈 (옆에서 두께)
    F.add('blade_cut', 'blade', pc, cs)
    F.add('blade_add', 'blade', pc, [plate(sk, g0 + bd * (0.3 + BL_L / 2), Rb, BL_W + 4, BL_L + 4, BLADE_G, dens=2.2, th=0.7)])


def stars(F, sk):
    rng = np.random.default_rng(91)
    pts = ((-14, 88, -6, 2.2), (14, 92, 2, 1.6), (26, 76, -4, 2.4), (-30, 66, -2, 1.8), (32, 44, -6, 1.5), (-20, 30, -8, 2.0), (18, 20, -6, 1.6), (-8, 100, -2, 1.4), (36, 60, 4, 1.2), (-36, 82, 2, 1.4))
    for i, (x, y, z, s) in enumerate(pts):
        p = np.array([x, y, z], float)
        col = (STAR_ADD, STAR_GLOW) if i % 3 else (BSTAR, BSTAR_GLOW)
        F.add(f'twinkle{i}_add', 'float', p, sparkle(sk, p, nrm(np.array([rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.2), -1.0])), s * 2.0, *col))
    F.J['twinkles'] = len(pts)


def build():
    sk = Y.Skin(3.0, layer='default')
    F = figure(sk)
    F.bones[:0] = [{'name': 'base', 'pivot': [0, 0, 0]}, {'name': 'float', 'parent': 'base', 'pivot': [0, 46, 0]}]
    flow_hair(F, sk)
    cape(F, sk)
    sleeves(F, sk)
    veil(F, sk)
    rings(F, sk)
    astrolabe(F, sk)
    streaks(F, sk)
    blade(F, sk)
    stars(F, sk)
    img = sk.finalize(F.bones, width=2048)
    return F, img


def clock_icon():
    """멈춘 회중시계: 금 테 · 금 간 유리 · 푸른 시계판 · 멈춘 두 바늘 · 꼭지 고리 · 푸른 빛무리"""
    from PIL import ImageDraw, ImageFilter
    S_ = 256
    yy, xx = np.mgrid[0:S_, 0:S_]
    cx, cy, r = 128, 140, 88
    d = np.hypot(xx - cx, yy - cy) / r
    a = np.arctan2(yy - cy, xx - cx)
    q = np.dstack([xx / 30.0, yy / 30.0, np.zeros_like(xx, float)])
    face = blue_at(np.clip(0.2 + 0.7 * (1 - d) + 0.15 * fbm(q, 1.0, 5), 0, 1)[None])[0]
    tick = ((np.cos(a * 12) > 0.97) & (d > 0.7) & (d < 0.84)) | ((np.cos(a * 60) > 0.99) & (d > 0.78) & (d < 0.84))
    face = np.where(tick[..., None], C(255, 224, 140), face)
    rim = (d > 0.86) & (d < 1.0)
    gold = mix(C(120, 78, 30), C(255, 226, 140), (0.5 + 0.5 * np.cos(a - 2.2))[..., None])
    col = np.where(rim[..., None], gold, face)
    A = (d < 1.0) * 255.0
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), A]).astype(np.uint8), "RGBA")
    g = Image.new("RGBA", (S_, S_), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse((cx - r - 20, cy - r - 20, cx + r + 20, cy + r + 20), fill=(70, 150, 255, 120)); g = g.filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(g, im)
    dr = ImageDraw.Draw(out)
    dr.ellipse((cx - 22, cy - r - 40, cx + 22, cy - r + 4), outline=(236, 190, 90, 255), width=8)       # 꼭지 고리
    dr.rectangle((cx - 9, cy - r - 8, cx + 9, cy - r + 6), fill=(214, 160, 70, 255))
    dr.line((cx, cy, cx + 34, cy - 50), fill=(255, 232, 160, 255), width=7); dr.line((cx, cy, cx - 50, cy + 16), fill=(255, 232, 160, 255), width=9)
    dr.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(255, 240, 190, 255))
    for (x0, y0, x1, y1) in ((cx + 10, cy - 70, cx + 34, cy - 20), (cx + 34, cy - 20, cx + 70, cy - 8), (cx + 34, cy - 20, cx + 28, cy + 30), (cx - 30, cy + 40, cx - 64, cy + 50)):
        dr.line((x0, y0, x1, y1), fill=(230, 245, 255, 230), width=3)                           # 금 간 유리
    dr.ellipse((cx - 56, cy - 62, cx - 30, cy - 36), fill=(255, 255, 255, 140))
    return out


def post_entity():
    """BP: 떠 있음 (중력 없음 · 걷지 않음 — 스크립트가 띄워 옮김) · 체력 61 아래면 피해 없음 (죽음 연출이 끝날 때까지 버팀)
    사건 vh:dying · vh:mortal · vh:alive · 속성 vh:act (0 평소 · 1 등장 · 2 죽음) · vh:blade (1 = 분침 검이 손에)
    RP: 분침 검 크기를 부드럽게 (v.bl)"""
    p = os.path.join(BK.BP, f"entities/{NAME}.json")
    j = json.load(open(p))
    E = j["minecraft:entity"]
    c = E["components"]
    for k in ("minecraft:navigation.walk", "minecraft:movement.basic", "minecraft:jump.static", "minecraft:can_climb", "minecraft:behavior.random_stroll",
              "minecraft:behavior.melee_attack", "minecraft:behavior.look_at_player", "minecraft:behavior.float"):
        c.pop(k, None)
    c["minecraft:physics"] = {"has_gravity": False, "has_collision": True}
    c["minecraft:movement"] = {"value": 0.0}
    base = c["minecraft:damage_sensor"]["triggers"]
    hold = {"on_damage": {"filters": {"test": "actor_health", "subject": "self", "operator": "<", "value": 61}}, "deals_damage": "no"}
    c["minecraft:damage_sensor"] = {"triggers": base + [hold]}
    for k in (2, 3): E["component_groups"][f"vh:phase{k}"] = {"minecraft:attack": {"damage": 0}}
    E["component_groups"]["vh:dying"] = {"minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": "no"}]}}
    E["component_groups"]["vh:mortal"] = {"minecraft:damage_sensor": {"triggers": base}}
    E["events"]["vh:dying"] = {"add": {"component_groups": ["vh:dying"]}}
    E["events"]["vh:mortal"] = {"remove": {"component_groups": ["vh:dying"]}, "add": {"component_groups": ["vh:mortal"]}}
    E["events"]["vh:alive"] = {"remove": {"component_groups": ["vh:dying", "vh:mortal"]}}
    json.dump(j, open(p, "w"), indent=1, ensure_ascii=False)
    rp = os.path.join(BK.RP, f"entity/{NAME}.entity.json")
    r = json.load(open(rp))
    D = r["minecraft:client_entity"]["description"]
    D["scripts"]["pre_animation"] = ["v.bl = math.lerp(v.bl ?? 0, q.property('vh:blade'), 0.22);", "v.ph = math.lerp(v.ph ?? 1, q.property('vh:phase'), 0.05);"]
    json.dump(r, open(rp, "w"), indent=1)


def main():
    F, img = build()
    bones = F.bones
    img.save(os.path.join(BK.RP, f"textures/models/vh/{NAME}.png"))
    n = BK.write_boss(NAME, bones, {"default": (f"textures/models/vh/{NAME}", img.width, img.height)}, anims(F),
                      [("idle", f"animation.vh.{NAME}.idle", None)],
                      {"hp": 1600, "title": "§b§l시간의 여신", "box": (2.6, 8.0), "speed": 0.0, "melee": 0, "reach": 1.0, "egg": ("#1c2a6e", "#e6b45a"), "drop": "vh:chrono_blade", "xp": 2000,
                       "props": {"vh:act": (0, 3), "vh:blade": (0, 1)},
                       "loot": [{"rolls": 1, "entries": [{"type": "item", "name": "minecraft:nether_star", "weight": 1}]}, {"rolls": {"min": 3, "max": 5}, "entries": [{"type": "item", "name": "minecraft:gold_block", "weight": 2, "functions": [{"function": "set_count", "count": {"min": 1, "max": 3}}]},
                                                                             {"type": "item", "name": "minecraft:clock", "weight": 2, "functions": [{"function": "set_count", "count": {"min": 1, "max": 2}}]},
                                                                             {"type": "item", "name": "minecraft:lapis_lazuli", "weight": 3, "functions": [{"function": "set_count", "count": {"min": 8, "max": 20}}]},
                                                                             {"type": "item", "name": "minecraft:experience_bottle", "weight": 3, "functions": [{"function": "set_count", "count": {"min": 4, "max": 10}}]}]},
                                {"rolls": {"min": 4, "max": 8}, "entries": [{"type": "item", "name": "minecraft:diamond", "weight": 1}, {"type": "item", "name": "minecraft:glowstone_dust", "weight": 3}, {"type": "item", "name": "minecraft:gold_ingot", "weight": 3}]}]},
                      vb=(18, 18, 6))
    post_entity()
    BK.write_summon("stopped_clock", clock_icon(), (["GSG", "SCS", "GSG"], {"G": "minecraft:gold_block", "S": "minecraft:sand", "C": "minecraft:clock"}))
    BK.set_lang({"entity.vh:boss_chrono.name": "§b§l시간의 여신", "item.spawn_egg.entity.vh:boss_chrono.name": "시간의 여신 스폰 알",
                 "item.vh:stopped_clock.name": "§b§l멈춘 회중시계 §r§7(시간의 여신 소환)"},
                {"entity.vh:boss_chrono.name": "§b§lThe Goddess of Time", "item.spawn_egg.entity.vh:boss_chrono.name": "Spawn The Goddess of Time",
                 "item.vh:stopped_clock.name": "§b§lStopped Pocket Watch §r§7(summons The Goddess of Time)"})
    print(f"{NAME}: cubes {n} · tex {img.size}")


def K(*pairs):
    return {f"{t:.2f}": {"post": (list(v) if isinstance(v, (list, tuple)) else [v, v, v]), "lerp_mode": "catmullrom"} for t, v in pairs}


def anims(F):
    RAISE = [0, 0, 140]
    """쉬는 자세 (떠서 한 팔을 들고 · 한 다리를 굽힘) 위에 더함 · 애니 위치 x 는 모델 x 와 반대
    고리는 법선 둘레로 돎 (쉬는 자세 뼈대 아래 z) · 페이즈가 오를수록 빨리 (v.ph) · 분침 검 크기 = v.bl"""
    lt = "q.life_time"
    N = f"animation.vh.{NAME}"
    A = {}
    J = F.J
    sw = lambda f, a, ph=0: f"math.sin({lt}*{f} + {ph})*{a}"
    sp = lambda base, add: f"{lt}*({base} + {add}*(v.ph - 1))"
    idle = {"base": {"scale": SCALE},                                                      # v1.233 전체 1.5 배 (그림 밀도 그대로 · 애니로 키움)
            "float": {"position": [sw(23, 0.35), sw(60, 1.3), sw(31, 0.3, 1)]},                            # v1.239 떠 있는 몸이 천천히 8 자로 흔들림
            "body": {"rotation": [sw(45, 1.5), sw(30, 2.0, 1), f"3 + {sw(38, 1.2, 2)}"]},                 # 여신다운 자세 (v1.234): 엉덩이를 살짝 틀고 · 가슴은 반대로 · 고개를 숙여 갸웃
            "chest": {"rotation": [f"{sw(45, 1.2, 0.6)} + {sw(75, 0.9, 0.3)}", sw(29, 1.5, 2), -5]},          # 숨 · 엉덩이와 반대로 트는 가슴
            "head": {"rotation": [f"7 + {sw(40, 2.0, 1)}", f"{sw(13, 7.0, 0.5)} + {sw(27, 2.0)}", f"9 + {sw(33, 1.6, 2)}"]},   # 천천히 둘러봄
            "arm_l": {"rotation": [sw(50, 3.0), sw(31, 2.0, 1), sw(40, 2.5, 1)]}, "fore_l": {"rotation": [sw(50, 4.0, -0.8), 0, 0]}, "hand_l": {"rotation": [sw(50, 5.0, -1.6), 0, sw(37, 4.0, -0.5)]},   # 팔뚝 · 손이 한 박자씩 늦게
            "arm_r": {"rotation": [sw(42, 2.5, 2), sw(29, 1.5), sw(36, 2.0)]}, "fore_r": {"rotation": [sw(42, 4.0, 1.2), 0, 0]}, "hand_r": {"rotation": [sw(42, 6.0, 0.4), 0, sw(33, 4.0)]},
            "leg_r": {"rotation": [sw(40, 4.0), 0, sw(27, 1.5)]}, "shin_r": {"rotation": [sw(40, 5.0, -0.7), 0, 0]}, "shin_l": {"rotation": [sw(40, 2.5, 0.6), 0, 0]},
            "leg_l": {"rotation": [sw(40, 1.5, 1.3), 0, 0]},
            "halo": {"rotation": [0, 0, sp(10, 18)]}, "halo_in": {"rotation": [0, 0, sp(-28, -30)]},
            "halo_glow_add": {"scale": f"1 + {sw(70, 0.05)}"},
            "rev_dial_add": {"rotation": [0, 0, f"{lt}*-22"], "scale": "math.clamp((v.ph - 1)*1.4, 0, 1)*(1 + " + sw(90, 0.03) + ")"},
            "wring": {"rotation": [0, 0, sp(-16, -20)]}, "fring": {"rotation": [0, 0, sp(40, 30)]},
            "astro": {"position": [0, sw(50, 1.6, 1), 0], "rotation": [0, f"{lt}*14", 0]},
            "astro_r0": {"rotation": [0, 0, sp(24, 20)]}, "astro_r1": {"rotation": [0, f"{lt}*-36", 0]},
            "horb_rings": {"rotation": [f"{lt}*50", f"{lt}*34", 0]}, "horb_add": {"scale": f"1 + {sw(120, 0.12)}"},
            "chest_gem_add": {"scale": f"1 + {sw(110, 0.15)}"},
            "crown_rays_add": {"scale": f"1 + {sw(90, 0.08)}"},
            "blade": {"scale": "math.max(v.bl, 0.001)"},
            "mantle": {"rotation": [sw(40, 1.5), 0, 0]},
            "face_lens_add": {"rotation": [0, 0, f"{lt}*-20"], "scale": f"1 + {sw(80, 0.06)}"},
            "face_ticks_add": {"rotation": [0, 0, f"{lt}*35"], "scale": f"1 - math.mod({lt}*0.35, 1)*0.18"},
            "face_horizon_add": {"scale": f"1 + {sw(140, 0.07, 1)}"},
            "face_swirl_a_add": {"rotation": [0, 0, f"{lt}*-55"]},
            "face_swirl_b_add": {"rotation": [0, 0, f"{lt}*80"], "scale": f"1 + {sw(90, 0.05, 2)}"},
            "face_orbit0_add": {"rotation": [0, 0, f"{lt}*70"]}, "face_orbit1_add": {"rotation": [0, 0, f"{lt}*-52"]},
            "face_orb_glass": {"scale": f"1 + {sw(75, 0.025)}"}}
    for k, spd in zip(range(J['streaks']), (26, -20, 32)):
        idle[f"streak{k}_add"] = {"rotation": [0, f"{lt}*{spd}", 0], "scale": f"1 + {sw(60 + 13 * k, 0.06, k)}"}
    for i in range(J['twinkles']):
        idle[f"twinkle{i}_add"] = {"scale": f"0.25 + 0.75*math.pow(math.abs(math.sin({lt}*{55 + 13 * i} + {i * 1.7})), 3)", "rotation": [0, 0, f"{lt}*{20 + 7 * i}"]}
    for i in J['hflow']:
        for s_ in range(3):
            idle[f"hflow{i}_{s_}"] = {"rotation": [sw(45, 2.0 + 1.5 * s_, i * 0.6 + s_), 0, sw(36, 2.5 + 2 * s_, i * 0.5 + s_ * 0.8)]}
    for q, k in enumerate(J.get('slocks', [])):                                               # 옆머리 흔들림 (아래 마디가 늦게)
        idle[f"slock_{k}_0"] = {"rotation": [sw(44, 2.0, q), 0, sw(37, 2.0, q + 1)]}
        idle[f"slock_{k}_1"] = {"rotation": [sw(44, 4.0, q - 0.9), 0, sw(37, 3.5, q + 0.2)]}
    for j in range(4):
        idle[f"hlock{j}"] = {"rotation": [sw(50, 2.0, j), 0, sw(40, 2.0, j + 1)]}
    for i in range(J['tails']):                                                                # 꼬리 마디마다 물결 (끝으로 갈수록 크게 · 늦게)
        for s_ in range(3):
            idle[f"tail{i}_{s_}_cut"] = {"rotation": [sw(42, 2.0 + 2.2 * s_, i * 0.9 - s_ * 0.8), sw(30, 1.5 + s_, i), sw(36, 2.0 + 2.5 * s_, i * 0.7 - s_ * 0.9)]}
        idle[f"tail{i}_tip_add"] = {"scale": f"(1 + 0.35*(v.ph - 1))*(1 + {sw(100, 0.1, i)})"}
        idle[f"tail{i}_gear_cut"] = {"rotation": [0, 0, f"{lt}*{30 + 6 * i}"]}
    for g in range(J['gown']):                                                                # 긴 드레스 (아래로 갈수록 크게 물결) · 소매 · 베일
        idle[f"gown{g}_cut"] = {"rotation": [sw(36, 0.8 + 0.9 * g, g * 0.7), 0, sw(30, 0.7 + 0.8 * g, g * 0.9 + 1)]}
    for s_ in ('r', 'l'):
        idle[f"sleeve_{s_}_cut"] = {"rotation": [sw(42, 3.0, s_ == 'l'), 0, sw(36, 2.0, 1 + (s_ == 'l'))]}
        idle[f"sleeve_{s_}_lo_cut"] = {"rotation": [sw(42, 5.0, -0.7 + (s_ == 'l')), 0, sw(36, 3.5, 0.3)]}
    idle["veil_glass"] = {"rotation": [sw(38, 2.5, 0.4), 0, sw(31, 2.0, 1.2)]}
    for j in J['skirts']:                                                                    # 트임 자락 (위 · 아래 마디) · 엉덩이 사슬
        idle[f"skirt{j}_cut"] = {"rotation": [sw(44, 2.0, j * 1.1), 0, sw(38, 1.6, j + 1)]}
        idle[f"skirt{j}_lo_cut"] = {"rotation": [sw(44, 3.5, j * 1.1 - 0.8), 0, sw(38, 2.6, j + 0.2)]}
    for s_ in ('r', 'l'):
        for k in range(3): idle[f"hchain_{s_}{k}"] = {"rotation": [sw(55, 4 + 2 * k, k * 0.7 + (s_ == 'l')), 0, sw(45, 3 + 2 * k, k)]}
    A[f"{N}.idle"] = {"loop": True, "bones": idle}
    Z3 = [0, 0, 0]
    # v1.239 애니 다시 짬: 기술마다 예비 동작 (반대로 모음) → 넘치게 뻗음 → 되돌아와 자리 잡음 · 팔뚝 · 손 · 머리 · 옷자락이 한 박자씩 늦게 따라옴 · 멈춘 자세에서도 숨 · 떨림
    R2 = lambda d: [RAISE[0] + d[0], RAISE[1] + d[1], RAISE[2] + d[2]]
    A[f"{N}.cast_up"] = {"animation_length": 1.7, "bones": {                                     # 든 손을 더 높이 · 혼천의가 떠오르며 빛남 (시간 정지 · 시간의 끝)
        "arm_l": {"rotation": K((0, Z3), (0.22, [18, 0, -14]), (0.5, R2([-12, 0, 16])), (0.66, R2([4, 0, -6])), (0.8, RAISE), (1.2, R2([-3, 0, 3])), (1.45, [-10, 0, 40]), (1.7, Z3))},
        "fore_l": {"rotation": K((0, Z3), (0.22, [-30, 0, 0]), (0.55, [-8, 0, 0]), (0.75, [-22, 0, 0]), (1.2, [-18, 0, 0]), (1.5, [-12, 0, 0]), (1.7, Z3))},
        "hand_l": {"rotation": K((0, Z3), (0.25, [30, 0, 0]), (0.6, [-25, 0, 0]), (0.8, [-12, 0, 0]), (1.2, [-15, 0, 0]), (1.7, Z3))},
        "arm_r": {"rotation": K((0, Z3), (0.25, [-8, 0, -6]), (0.6, [10, 0, -22]), (1.2, [8, 0, -18]), (1.7, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.3, [-20, 0, 0]), (0.7, [-6, 0, 0]), (1.7, Z3))},
        "head": {"rotation": K((0, Z3), (0.22, [12, -4, 0]), (0.55, [-20, 10, 0]), (0.8, [-14, 8, 0]), (1.2, [-16, 8, 0]), (1.7, Z3))},
        "body": {"rotation": K((0, Z3), (0.22, [8, 0, -3]), (0.55, [-8, 0, 6]), (0.8, [-5, 0, 4]), (1.2, [-5, 0, 4]), (1.7, Z3))},
        "chest": {"rotation": K((0, Z3), (0.22, [6, 0, 0]), (0.55, [-7, 6, 0]), (1.2, [-5, 4, 0]), (1.7, Z3))},
        "float": {"position": K((0, Z3), (0.22, [0, -1.6, 0]), (0.55, [0, 2.6, 0]), (0.8, [0, 1.6, 0]), (1.2, [0, 2.0, 0]), (1.7, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.3, [6, 0, 0]), (0.65, [-14, 0, 0]), (1.2, [-8, 0, 0]), (1.7, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.3, [-3, 0, 0]), (0.65, [5, 0, 2]), (1.0, [2, 0, 0]), (1.7, Z3))},
        "astro": {"position": K((0, Z3), (0.25, [0, -1, 0]), (0.6, [0, 7, 0]), (1.2, [0, 6, 0]), (1.7, Z3)), "scale": K((0, 1), (0.25, 0.92), (0.6, 1.35), (0.8, 1.28), (1.2, 1.3), (1.7, 1))},
        "horb_add": {"scale": K((0, 1), (0.25, 0.7), (0.55, 2.6), (0.8, 2.1), (1.2, 2.2), (1.7, 1))},
        "halo": {"scale": K((0, 1), (0.25, 0.95), (0.6, 1.15), (0.8, 1.1), (1.2, 1.12), (1.7, 1))}}}
    A[f"{N}.flip"] = {"animation_length": 1.9, "bones": {                                        # 모래시계를 뒤집음 (되감기): 두 손으로 혼천의를 끌어내려 한 바퀴 반 · 모래시계 180°
        "astro": {"position": K((0, Z3), (0.2, [0, 2, 0]), (0.55, [-8, -10, -6]), (1.4, [-8, -10, -6]), (1.6, [-2, -1, -1]), (1.9, Z3)), "scale": K((0, 1), (0.2, 1.05), (0.55, 1.45), (1.4, 1.4), (1.9, 1))},
        "astro_hg": {"rotation": {"0.00": [0, 0, 0], "0.55": [0, 0, 0], "0.95": [0, 0, 150], "1.15": [0, 0, 190], "1.35": [0, 0, 180], "1.90": [0, 0, 180]}},
        "arm_l": {"rotation": K((0, Z3), (0.2, [-20, 0, 40]), (0.55, [12, 0, 112]), (0.9, [4, 0, 120]), (1.4, [10, 0, 110]), (1.65, [0, 0, 30]), (1.9, Z3))},
        "fore_l": {"rotation": K((0, Z3), (0.3, [-35, 0, 0]), (0.6, [-10, 0, 0]), (1.4, [-15, 0, 0]), (1.9, Z3))},
        "arm_r": {"rotation": K((0, Z3), (0.2, [10, 0, 10]), (0.55, [-64, 0, -30]), (0.95, [-56, 0, -36]), (1.4, [-60, 0, -30]), (1.65, [-15, 0, -8]), (1.9, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.3, [-10, 0, 0]), (0.6, [-34, 0, 0]), (1.4, [-30, 0, 0]), (1.9, Z3))},
        "hand_r": {"rotation": K((0, Z3), (0.6, [-20, 0, 15]), (1.0, [-10, 0, 40]), (1.4, [-15, 0, 30]), (1.9, Z3))},
        "body": {"rotation": K((0, Z3), (0.2, [-5, 8, 0]), (0.55, [8, -10, 0]), (1.0, [6, 6, 0]), (1.4, [7, -4, 0]), (1.9, Z3))},
        "chest": {"rotation": K((0, Z3), (0.55, [6, -6, 0]), (1.0, [4, 8, 0]), (1.9, Z3))},
        "halo": {"rotation": {"0.00": [0, 0, 0], "0.45": [0, 0, 10], "1.40": [0, 0, -370], "1.60": [0, 0, -360], "1.90": [0, 0, -360]}},
        "head": {"rotation": K((0, Z3), (0.2, [-6, 6, 0]), (0.55, [12, -10, 0]), (1.0, [14, 4, 0]), (1.4, [10, -8, 0]), (1.9, Z3))},
        "float": {"position": K((0, Z3), (0.2, [0, 1.5, 0]), (0.55, [0, -1.2, -0.6]), (1.4, [0, -1, -0.6]), (1.9, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.6, [-8, 0, 0]), (1.1, [4, 0, 0]), (1.9, Z3))}}}
    A[f"{N}.throw"] = {"animation_length": 1.05, "bones": {                                      # 내린 손을 뒤로 감았다 · 몸을 틀며 휘둘러 시곗바늘을 던짐 (팔뚝 · 손목이 늦게 채찍처럼)
        "arm_r": {"rotation": K((0, Z3), (0.28, [42, 0, 36]), (0.42, [-112, 0, -12]), (0.52, [-100, 0, -34]), (0.75, [-40, 0, -14]), (1.05, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.28, [-55, 0, 0]), (0.4, [-30, 0, 0]), (0.48, [-2, 0, 0]), (0.75, [-14, 0, 0]), (1.05, Z3))},
        "hand_r": {"rotation": K((0, Z3), (0.28, [40, 0, 0]), (0.44, [10, 0, 0]), (0.5, [-40, 0, 0]), (0.8, [-10, 0, 0]), (1.05, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.28, [-25, 0, 22]), (0.45, [22, 0, -18]), (0.75, [8, 0, -6]), (1.05, Z3))},
        "body": {"rotation": K((0, Z3), (0.28, [4, -20, -3]), (0.45, [-6, 18, 4]), (0.55, [-7, 24, 4]), (0.8, [-2, 6, 0]), (1.05, Z3))},
        "chest": {"rotation": K((0, Z3), (0.28, [0, -12, 0]), (0.45, [-4, 12, 0]), (0.8, Z3), (1.05, Z3))},
        "head": {"rotation": K((0, Z3), (0.28, [4, 18, 0]), (0.45, [-4, -12, 0]), (0.8, [0, -4, 0]), (1.05, Z3))},
        "float": {"position": K((0, Z3), (0.28, [0, -1.2, 1.2]), (0.45, [0, 0.6, -2.2]), (0.8, [0, 0.2, -0.6]), (1.05, Z3))},
        "leg_r": {"rotation": K((0, Z3), (0.28, [-8, 0, 0]), (0.48, [16, 0, 0]), (1.05, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.32, [0, 0, -3]), (0.55, [-4, 0, 5]), (0.8, [0, 0, -1]), (1.05, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.3, [-6, 0, 0]), (0.55, [10, 0, 0]), (1.05, Z3))},
        "halo": {"scale": K((0, 1), (0.42, 1.12), (0.6, 1.04), (1.05, 1))}}}
    A[f"{N}.sweep"] = {"animation_length": 1.7, "bones": {                                       # 두 팔이 진자처럼 좌우로 (진자의 심판) — 몸 · 옷자락은 늦게 반대로
        "arm_r": {"rotation": K((0, Z3), (0.3, [-24, 0, 74]), (0.75, [-52, 0, -26]), (1.2, [-22, 0, 66]), (1.45, [-10, 0, 20]), (1.7, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.38, [-26, 0, 0]), (0.85, [-8, 0, 0]), (1.3, [-24, 0, 0]), (1.7, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.3, [-22, 0, 54]), (0.75, [-10, 0, 6]), (1.2, [-22, 0, 52]), (1.45, [-8, 0, 16]), (1.7, Z3))},
        "fore_l": {"rotation": K((0, Z3), (0.38, [-20, 0, 0]), (0.85, [-4, 0, 0]), (1.3, [-18, 0, 0]), (1.7, Z3))},
        "body": {"rotation": K((0, Z3), (0.35, [0, -6, 11]), (0.8, [0, 6, -11]), (1.25, [0, -6, 10]), (1.7, Z3))},
        "chest": {"rotation": K((0, Z3), (0.3, [0, -8, 4]), (0.75, [0, 8, -4]), (1.2, [0, -8, 4]), (1.7, Z3))},
        "head": {"rotation": K((0, Z3), (0.4, [0, 6, -6]), (0.85, [0, -6, 6]), (1.3, [0, 6, -6]), (1.7, Z3))},
        "float": {"position": K((0, Z3), (0.35, [2.2, 1.2, 0]), (0.58, [0, 0, 0]), (0.8, [-2.2, 1.2, 0]), (1.02, [0, 0, 0]), (1.25, [2.2, 1.2, 0]), (1.7, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.45, [0, 0, -6]), (0.9, [0, 0, 6]), (1.35, [0, 0, -5]), (1.7, Z3))},
        "gown1_cut": {"rotation": K((0, Z3), (0.55, [0, 0, -5]), (1.0, [0, 0, 5]), (1.45, [0, 0, -3]), (1.7, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.45, [0, 8, 0]), (0.9, [0, -8, 0]), (1.35, [0, 6, 0]), (1.7, Z3))}}}
    A[f"{N}.conduct"] = {"animation_length": 1.9, "bones": {                                     # 두 팔을 가슴 앞에 모았다 활짝 · 허리 고리 · 후광이 커짐 (열두 시각 · 톱니 파동)
        "arm_r": {"rotation": K((0, Z3), (0.3, [-48, 0, 26]), (0.58, [-6, 0, -80]), (0.75, [-12, 0, -66]), (1.35, [-10, 0, -72]), (1.6, [-4, 0, -20]), (1.9, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.3, [-46, 0, -24]), (0.58, [-6, 0, 86]), (0.75, [-12, 0, 72]), (1.35, [-10, 0, 78]), (1.6, [-4, 0, 22]), (1.9, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.3, [-50, 0, 0]), (0.6, [-6, 0, 0]), (0.8, [-22, 0, 0]), (1.35, [-18, 0, 0]), (1.9, Z3))},
        "fore_l": {"rotation": K((0, Z3), (0.3, [-50, 0, 0]), (0.6, [-6, 0, 0]), (0.8, [-22, 0, 0]), (1.35, [-18, 0, 0]), (1.9, Z3))},
        "hand_r": {"rotation": K((0, Z3), (0.3, [20, 0, 0]), (0.62, [-30, 0, 0]), (1.35, [-20, 0, 0]), (1.9, Z3))},
        "hand_l": {"rotation": K((0, Z3), (0.3, [20, 0, 0]), (0.62, [-30, 0, 0]), (1.35, [-20, 0, 0]), (1.9, Z3))},
        "body": {"rotation": K((0, Z3), (0.3, [8, 0, 0]), (0.6, [-10, 0, 0]), (1.35, [-8, 0, 0]), (1.9, Z3))},
        "chest": {"rotation": K((0, Z3), (0.3, [8, 0, 0]), (0.6, [-8, 0, 0]), (1.0, [-6, 0, 0]), (1.35, [-7, 0, 0]), (1.9, Z3))},
        "head": {"rotation": K((0, Z3), (0.3, [14, 0, 0]), (0.65, [-16, 0, 0]), (1.35, [-12, 0, 0]), (1.9, Z3))},
        "wring": {"scale": K((0, 1), (0.3, 0.9), (0.62, 1.42), (0.8, 1.32), (1.35, 1.35), (1.9, 1))},
        "halo": {"scale": K((0, 1), (0.3, 0.92), (0.62, 1.26), (0.8, 1.18), (1.35, 1.2), (1.9, 1))},
        "float": {"position": K((0, Z3), (0.3, [0, -1.5, 0]), (0.62, [0, 3.6, 0]), (0.85, [0, 2.8, 0]), (1.35, [0, 3.2, 0]), (1.9, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.35, [8, 0, 0]), (0.7, [-16, 0, 0]), (1.35, [-10, 0, 0]), (1.9, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.35, [-3, 0, 0]), (0.7, [6, 0, 0]), (1.1, [2, 0, 0]), (1.9, Z3))},
        "gown1_cut": {"rotation": K((0, Z3), (0.45, [-2, 0, 0]), (0.85, [5, 0, 0]), (1.25, [1, 0, 0]), (1.9, Z3))}}}
    def AP(a, b):
        """오른팔 자세 = 팔 (어깨 → 팔꿈치) 방향 a · 검 날 방향 b (몸 기준 모델 좌표) → 팔 회전 (팔뚝 · 손은 쉬는 자세 그대로)"""
        def fr(a_, b_):
            a_ = nrm(np.array(a_, float)); b_ = np.array(b_, float); b_ = nrm(b_ - a_ * np.dot(a_, b_))
            return np.column_stack([a_, b_, np.cross(a_, b_)])
        R = fr(a, b) @ fr(J['el_r'] - J['sh_r'], J['BLADE_D']).T
        return [round(float(v), 1) for v in tex_kit.euler_of(R)]
    # v1.245 분침 검 3연격 (날이 주먹 앞으로 = 팔을 머리 위로 올리면 날이 등 뒤로 눕고 · 내리치면 앞을 크게 가름)
    A[f"{N}.slash"] = {"animation_length": 1.25, "bones": {                                      # 첫째: 오른 어깨 위로 감아올려 (떨며 버팀) → 왼쪽 아래로 크게 내리벰 (0.5 초) · 앞으로 내디딤 · 넘쳐 숙였다 일어섬
        "arm_r": {"rotation": K((0, Z3), (0.3, AP((0.45, 0.85, 0.3), (0.1, 0.2, 1))), (0.42, AP((0.4, 0.9, 0.35), (0.05, 0.3, 1))), (0.5, AP((0.15, -0.1, -1), (-0.55, -0.8, -0.2))),
                                (0.58, AP((-0.35, -0.75, -0.55), (-0.55, -0.35, 0.75))), (0.8, AP((-0.1, -0.85, -0.5), (-0.4, -0.3, -0.8))), (1.25, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.3, [-20, 0, 0]), (0.42, [-24, 0, 0]), (0.5, [-4, 0, 0]), (0.62, [-2, 0, 0]), (0.9, [-10, 0, 0]), (1.25, Z3))},
        "hand_r": {"rotation": K((0, Z3), (0.3, [14, 0, 0]), (0.42, [18, 0, 0]), (0.5, [-8, 0, 0]), (0.62, [-12, 0, 0]), (1.0, [-4, 0, 0]), (1.25, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.3, [-30, 0, 34]), (0.5, [14, 0, 18]), (0.62, [20, 0, 24]), (1.25, Z3))},
        "fore_l": {"rotation": K((0, Z3), (0.3, [-40, 0, 0]), (0.55, [-10, 0, 0]), (1.25, Z3))},
        "body": {"rotation": K((0, Z3), (0.3, [2, -30, -4]), (0.42, [2, -32, -4]), (0.5, [-12, 26, 5]), (0.6, [-16, 32, 6]), (0.9, [-5, 8, 2]), (1.25, Z3))},
        "chest": {"rotation": K((0, Z3), (0.3, [-8, -14, 0]), (0.5, [-4, 14, 0]), (0.62, [6, 16, 0]), (1.0, [1, 2, 0]), (1.25, Z3))},
        "head": {"rotation": K((0, Z3), (0.3, [-10, 22, 0]), (0.5, [6, -10, 0]), (0.65, [12, -14, 0]), (1.0, [2, -2, 0]), (1.25, Z3))},
        "float": {"position": K((0, Z3), (0.3, [0, 2.6, 2.2]), (0.42, [0, 3.0, 2.4]), (0.5, [0, -1.6, -5.0]), (0.6, [0, -2.2, -6.0]), (0.9, [0, -0.6, -2.0]), (1.25, Z3))},
        "leg_r": {"rotation": K((0, Z3), (0.3, [-18, 0, 0]), (0.5, [22, 0, 0]), (0.62, [26, 0, 0]), (1.25, Z3))},
        "leg_l": {"rotation": K((0, Z3), (0.3, [8, 0, 0]), (0.5, [-16, 0, 0]), (1.25, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.32, [-10, 0, 0]), (0.52, [18, 0, 0]), (0.75, [-4, 0, 0]), (1.25, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.35, [5, 0, -3]), (0.55, [-9, 0, 4]), (0.85, [2, 0, -1]), (1.25, Z3))},
        "gown1_cut": {"rotation": K((0, Z3), (0.42, [6, 0, -3]), (0.62, [-10, 0, 4]), (0.95, [2, 0, 0]), (1.25, Z3))},
        "halo": {"scale": K((0, 1), (0.42, 1.06), (0.52, 1.16), (1.25, 1))}}}
    A[f"{N}.slash2"] = {"animation_length": 1.05, "bones": {                                     # 둘째: 몸을 왼쪽으로 감아 팔을 가슴 앞에 모았다 → 오른쪽으로 크게 가로 벰 (0.42 초) · 반 바퀴 미끄러짐
        "arm_r": {"rotation": K((0, Z3), (0.28, AP((-0.45, -0.2, -0.85), (-0.85, 0.1, 0.45))), (0.36, AP((-0.5, -0.15, -0.8), (-0.8, 0.15, 0.55))), (0.42, AP((0.6, -0.25, -0.75), (-0.2, 0, -1))),
                                (0.5, AP((0.85, -0.25, 0.2), (0.3, 0, -1))), (0.7, AP((0.7, -0.5, 0.45), (0.6, -0.2, -0.6))), (1.05, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.28, [-16, 0, 0]), (0.42, [-4, 0, 0]), (0.55, [0, 0, 0]), (0.8, [-10, 0, 0]), (1.05, Z3))},
        "hand_r": {"rotation": K((0, Z3), (0.28, [10, 0, 0]), (0.42, [-6, 0, 0]), (0.52, [-10, 0, 0]), (1.05, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.28, [-14, 0, -24]), (0.45, [-30, 0, 46]), (0.6, [-24, 0, 52]), (1.05, Z3))},
        "body": {"rotation": K((0, Z3), (0.28, [0, 40, 3]), (0.36, [0, 42, 3]), (0.45, [-4, -30, -3]), (0.55, [-5, -40, -3]), (0.85, [-1, -8, 0]), (1.05, Z3))},
        "chest": {"rotation": K((0, Z3), (0.28, [2, 16, 0]), (0.45, [-4, -14, 0]), (0.6, [-4, -18, 0]), (1.05, Z3))},
        "head": {"rotation": K((0, Z3), (0.28, [4, -26, 0]), (0.45, [-2, 14, 0]), (0.7, [0, 4, 0]), (1.05, Z3))},
        "float": {"position": K((0, Z3), (0.28, [-2.0, 0.8, 1.4]), (0.45, [2.4, -0.8, -3.2]), (0.6, [3.0, -0.6, -3.6]), (1.05, Z3))},
        "leg_r": {"rotation": K((0, Z3), (0.3, [10, 0, -6]), (0.5, [-12, 0, 10]), (1.05, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.3, [0, -12, 0]), (0.5, [6, 14, 0]), (0.8, [0, -3, 0]), (1.05, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.32, [0, 0, 6]), (0.52, [0, 0, -8]), (0.8, [0, 0, 2]), (1.05, Z3))},
        "gown1_cut": {"rotation": K((0, Z3), (0.4, [0, 0, 7]), (0.6, [0, 0, -9]), (0.9, [0, 0, 2]), (1.05, Z3))}}}
    A[f"{N}.slash3"] = {"animation_length": 1.5, "bones": {                                      # 셋째: 웅크려 감았다 → 검을 옆으로 뻗고 한 바퀴 반 돌며 둘레를 벰 (0.45 ~ 0.85 초) → 솟구치며 올려 벰 (1.0 초)
        "float": {"position": K((0, Z3), (0.3, [0, -2.6, 1.0]), (0.45, [0, -1.0, 0]), (0.85, [0, 2.4, 0]), (1.0, [0, 6.0, -1.5]), (1.15, [0, 5.2, -1.0]), (1.5, Z3)),
                  "rotation": {"0.00": [0, 0, 0], "0.30": [0, 50, 0], "0.45": [0, 20, 0], "0.65": [0, -160, 0], "0.85": [0, -340, 0], "1.00": [0, -372, 0], "1.20": [0, -362, 0], "1.50": [0, -360, 0]}},
        "arm_r": {"rotation": K((0, Z3), (0.3, AP((0.6, -0.6, 0.5), (0.3, -0.3, -0.9))), (0.45, AP((1, -0.08, 0.1), (0, 0, -1))), (0.85, AP((1, -0.05, 0.1), (0, 0, -1))),
                                (1.0, AP((0.25, 0.95, -0.2), (0, 0.4, -1))), (1.15, AP((0.25, 0.9, -0.1), (0, 0.6, -0.8))), (1.5, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.3, [-14, 0, 0]), (0.45, [-2, 0, 0]), (0.9, [-2, 0, 0]), (1.0, [-6, 0, 0]), (1.5, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.3, [-20, 0, 40]), (0.45, [-6, 0, 80]), (0.85, [-4, 0, 86]), (1.0, [-20, 0, 40]), (1.5, Z3))},
        "body": {"rotation": K((0, Z3), (0.3, [14, 0, 0]), (0.45, [4, 0, 0]), (0.85, [-4, 0, 0]), (1.0, [-16, 0, 0]), (1.5, Z3))},
        "head": {"rotation": K((0, Z3), (0.3, [14, 0, 0]), (0.5, [0, 0, 0]), (1.0, [-22, 0, 0]), (1.5, Z3))},
        "leg_r": {"rotation": K((0, Z3), (0.3, [-30, 0, 0]), (0.5, [0, 0, -10]), (0.9, [0, 0, -14]), (1.0, [14, 0, 0]), (1.5, Z3))},
        "leg_l": {"rotation": K((0, Z3), (0.3, [-12, 0, 0]), (0.5, [0, 0, 10]), (0.9, [0, 0, 14]), (1.0, [8, 0, 0]), (1.5, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.3, [10, 0, 0]), (0.55, [-20, 0, 0]), (0.9, [-24, 0, 0]), (1.05, [16, 0, 0]), (1.5, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.45, [-6, 0, 0]), (0.85, [-10, 0, 0]), (1.05, [8, 0, 0]), (1.5, Z3))},
        "gown1_cut": {"rotation": K((0, Z3), (0.5, [-8, 0, 0]), (0.9, [-12, 0, 0]), (1.1, [9, 0, 0]), (1.5, Z3))},
        "halo": {"scale": K((0, 1), (0.45, 1.08), (0.85, 1.12), (1.0, 1.25), (1.5, 1))}}}
    SINK = -112                                                                               # 땅 밑까지 (모델 키 + 후광 · 혼천의)
    def rift(L, d0, d1, tp, u0, u1, end):
        """틈으로 가라앉았다 (d0 → d1) 다른 틈에서 떠오름 (u0 → u1 · 넘쳤다 자리 잡음) — tp = 스크립트가 옮기는 때"""
        return {
            "float": {"position": K((0, Z3), (d0, [0, 2.4, 0]), ((d0 + d1) / 2, [0, SINK * 0.28, 0]), (d1, [0, SINK, 0]), (tp, [0, SINK, 0]), (u0, [0, SINK, 0]),
                                    ((u0 + u1) / 2, [0, SINK * 0.3, 0]), (u1, [0, 3.2, 0]), ((u1 + end) / 2, [0, -0.8, 0]), (end, Z3))},
            "arm_r": {"rotation": K((0, Z3), (d0, [-10, 0, -18]), (d1, [-30, 0, -70]), (u0, [-30, 0, -70]), (u1, [-12, 0, -36]), ((u1 + end) / 2, [4, 0, -8]), (end, Z3))},
            "arm_l": {"rotation": K((0, Z3), (d0, [-10, 0, 18]), (d1, [-30, 0, 72]), (u0, [-30, 0, 72]), (u1, [-12, 0, 38]), ((u1 + end) / 2, [4, 0, 8]), (end, Z3))},
            "fore_r": {"rotation": K((0, Z3), (d1, [-24, 0, 0]), (u1, [-6, 0, 0]), (end, Z3))},
            "fore_l": {"rotation": K((0, Z3), (d1, [-24, 0, 0]), (u1, [-6, 0, 0]), (end, Z3))},
            "head": {"rotation": K((0, Z3), (d0, [18, 0, 0]), (d1, [-24, 0, 0]), (u0, [26, 0, 0]), (u1, [-10, 0, 0]), (end, Z3))},
            "body": {"rotation": K((0, Z3), (d0, [6, 0, 0]), (d1, [-4, 0, 0]), (u0, [-6, 0, 0]), (u1, [4, 0, 0]), (end, Z3))},
            "mantle": {"rotation": K((0, Z3), (d0, [6, 0, 0]), (d1, [-30, 0, 0]), (u0, [-30, 0, 0]), (u1, [14, 0, 0]), ((u1 + end) / 2, [-4, 0, 0]), (end, Z3))},
            "gown0_cut": {"rotation": K((0, Z3), (d0, [2, 0, 0]), (d1, [-8, 0, 0]), (u0, [-8, 0, 0]), (u1, [6, 0, 0]), (end, Z3))},
            "gown1_cut": {"rotation": K((0, Z3), (d0, [3, 0, 0]), (d1, [-10, 0, 0]), (u0, [-10, 0, 0]), (u1, [8, 0, 0]), (end, Z3))},
            "astro": {"position": K((0, Z3), (d1, [0, 10, 0]), (u0, [0, 10, 0]), (u1, [0, -2, 0]), (end, Z3))}}
    A[f"{N}.blink"] = {"animation_length": 1.7, "bones": rift(1.7, 0.3, 0.72, 0.8, 0.88, 1.32, 1.7)}   # 시간 도약 (v1.239): 발밑 타원 틈으로 가라앉아 (0.8 초에 옮김) 다른 틈에서 떠오름 — 옛 「옆으로 접힘」 없앰
    A[f"{N}.hop"] = {"animation_length": 1.0, "bones": rift(1.0, 0.1, 0.28, 0.32, 0.36, 0.66, 1.0)}   # 잔상 도약 (빠른 틈 · 0.3 초에 옮김)
    A[f"{N}.intro"] = {"animation_length": 3.2, "bones": {                                      # 등장: 땅의 틈에서 떠오르며 · 고리가 차례로 펼쳐지고 · 숙인 고개를 듦 · 든 손으로 시간을 엶
        "float": {"position": K((0, [0, SINK, 0]), (0.3, [0, SINK, 0]), (1.0, [0, SINK * 0.25, 0]), (1.4, [0, 3.0, 0]), (1.8, [0, -0.6, 0]), (2.2, Z3), (3.2, Z3))},
        "halo": {"scale": K((0, 0), (1.3, 0), (1.9, 1.15), (2.2, 0.96), (2.5, 1), (3.2, 1)), "rotation": {"0.00": [0, 0, 0], "1.30": [0, 0, 0], "2.40": [0, 0, 270], "3.20": [0, 0, 300]}},
        "wring": {"scale": K((0, 0), (1.6, 0), (2.2, 1.15), (2.5, 0.95), (2.8, 1), (3.2, 1))},
        "astro": {"scale": K((0, 0), (1.9, 0), (2.5, 1.15), (2.8, 0.95), (3.2, 1))},
        "head": {"rotation": K((0, [30, 0, 0]), (2.0, [30, 0, 0]), (2.5, [-8, 0, 0]), (2.8, [2, 0, 0]), (3.2, Z3))},
        "body": {"rotation": K((0, [10, 0, 0]), (1.4, [6, 0, 0]), (2.2, [-4, 0, 0]), (3.2, Z3))},
        "arm_r": {"rotation": K((0, [-20, 0, -40]), (1.4, [-20, 0, -40]), (2.0, [-6, 0, -12]), (3.2, Z3))},
        "arm_l": {"rotation": K((0, [-20, 0, 40]), (1.4, [-20, 0, 40]), (2.0, [-6, 0, 12]), (2.5, R2([-10, 0, 12])), (2.9, RAISE), (3.2, Z3))},
        "fore_l": {"rotation": K((0, Z3), (2.3, Z3), (2.6, [-22, 0, 0]), (3.2, Z3))},
        "mantle": {"rotation": K((0, [-30, 0, 0]), (1.0, [-30, 0, 0]), (1.6, [14, 0, 0]), (2.1, [-4, 0, 0]), (3.2, Z3))}}}
    A[f"{N}.awaken"] = {"animation_length": 2.5, "bones": {                                     # 페이즈: 몸을 웅크려 모았다 → 두 팔을 펼치며 솟구침 · 고리가 거꾸로 휘몰아침
        "arm_r": {"rotation": K((0, Z3), (0.35, [-40, 0, 30]), (0.7, [-34, 0, -70]), (0.9, [-28, 0, -58]), (1.9, [-30, 0, -62]), (2.2, [-8, 0, -16]), (2.5, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.35, [-40, 0, -28]), (0.7, [-14, 0, 92]), (0.9, [-10, 0, 78]), (1.9, [-10, 0, 82]), (2.2, [-4, 0, 18]), (2.5, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.35, [-60, 0, 0]), (0.75, [-8, 0, 0]), (1.0, [-20, 0, 0]), (2.5, Z3))},
        "fore_l": {"rotation": K((0, Z3), (0.35, [-60, 0, 0]), (0.75, [-8, 0, 0]), (1.0, [-20, 0, 0]), (2.5, Z3))},
        "head": {"rotation": K((0, Z3), (0.35, [24, 0, 0]), (0.75, [-26, 0, 0]), (1.9, [-20, 0, 0]), (2.5, Z3))},
        "body": {"rotation": K((0, Z3), (0.35, [14, 0, 0]), (0.75, [-10, 0, 0]), (1.9, [-6, 0, 0]), (2.5, Z3))},
        "chest": {"rotation": K((0, Z3), (0.35, [10, 0, 0]), (0.75, [-10, 0, 0]), (1.9, [-8, 0, 0]), (2.5, Z3))},
        "leg_r": {"rotation": K((0, Z3), (0.35, [-24, 0, 0]), (0.75, [10, 0, 0]), (2.5, Z3))},
        "leg_l": {"rotation": K((0, Z3), (0.35, [-14, 0, 0]), (0.75, [6, 0, 0]), (2.5, Z3))},
        "halo": {"rotation": {"0.00": [0, 0, 0], "0.40": [0, 0, 20], "2.50": [0, 0, -720]}, "scale": K((0, 1), (0.35, 0.85), (0.75, 1.38), (1.0, 1.26), (1.9, 1.3), (2.5, 1))},
        "wring": {"rotation": {"0.00": [0, 0, 0], "0.40": [0, 0, -20], "2.50": [0, 0, 540]}, "scale": K((0, 1), (0.35, 0.85), (0.75, 1.2), (1.9, 1.15), (2.5, 1))},
        "float": {"position": K((0, Z3), (0.35, [0, -2.4, 0]), (0.75, [0, 5.4, 0]), (1.0, [0, 3.8, 0]), (1.9, [0, 4.2, 0]), (2.5, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.35, [12, 0, 0]), (0.8, [-24, 0, 0]), (1.9, [-14, 0, 0]), (2.5, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.35, [-4, 0, 0]), (0.8, [8, 0, 0]), (1.3, [2, 0, 0]), (2.5, Z3))}}}
    A[f"{N}.die"] = {"animation_length": 4.0, "loop": "hold_on_last_frame", "bones": {            # 죽음: 움찔 → 고개를 떨굼 · 팔이 늘어짐 → 고리가 멈추며 기울고 작아짐 → 가라앉음
        "body": {"rotation": K((0, Z3), (0.2, [8, 0, 0]), (1.4, [18, 0, -6]), (4.0, [20, 0, -8]))},
        "head": {"rotation": K((0, Z3), (0.2, [-14, 0, 0]), (1.5, [30, 0, -10]), (4.0, [34, 0, -12]))},
        "arm_l": {"rotation": K((0, Z3), (1.4, [12, 0, -6]), (4.0, [14, 0, -8]))},
        "fore_l": {"rotation": K((0, Z3), (1.4, [20, 0, 0]), (4.0, [24, 0, 0]))},
        "arm_r": {"rotation": K((0, Z3), (1.4, [10, 0, 10]), (4.0, [12, 0, 12]))},
        "leg_r": {"rotation": K((0, Z3), (1.6, [-20, 0, 0]), (4.0, [-24, 0, 0]))},
        "halo": {"rotation": K((0, Z3), (1.0, [0, 0, 20]), (2.5, [16, 0, 40]), (4.0, [20, 0, 44])), "scale": K((0, 1), (2.0, 1.0), (3.4, 0.0), (4.0, 0.0))},
        "wring": {"scale": K((0, 1), (1.8, 1.0), (3.0, 0.0), (4.0, 0.0))},
        "astro": {"position": K((0, Z3), (1.5, [0, -4, 0]), (3.5, [0, -30, 0]), (4.0, [0, -30, 0])), "scale": K((0, 1), (2.6, 1.0), (3.4, 0.0), (4.0, 0.0))},
        "float": {"position": K((0, Z3), (1.0, [0, -1, 0]), (3.0, [0, -8, 0]), (4.0, [0, -9, 0])), "scale": K((0, 1), (3.0, 1), (4.0, 0.9))}}}
    A[f"{N}.grip"] = {"animation_length": 5.1, "bones": {                                     # v1.242 맞물린 두 시계: 손을 뻗어 (1.2 초) 움켜쥐어 배 앞으로 끌어옴 → 두 손으로 감싸 쥐고 비틂 (떨림) → 4.5 초에 깨지며 팔을 펼침
        "arm_r": {"rotation": K((0, Z3), (0.35, [-20, 0, -26]), (1.0, [-78, 0, -12]), (1.2, [-84, 0, -8]), (1.45, [-36, 0, 20]), (1.6, [-42, 0, 16]), (3.0, [-40, 0, 20]), (4.4, [-46, 0, 24]), (4.62, [-30, 0, -74]), (4.8, [-26, 0, -62]), (5.1, Z3))},
        "fore_r": {"rotation": K((0, Z3), (1.0, [-8, 0, 0]), (1.2, [-4, 0, 0]), (1.45, [-62, 0, 0]), (3.0, [-58, 0, 0]), (4.4, [-64, 0, 0]), (4.62, [-10, 0, 0]), (5.1, Z3))},
        "hand_r": {"rotation": K((0, Z3), (1.0, [-30, 0, 0]), (1.2, [20, 0, 0]), (1.5, [10, 0, 10]), (3.0, [10, 30, 10]), (4.4, [14, 80, 12]), (4.6, [-20, 0, 0]), (5.1, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.35, [10, 0, 10]), (1.2, [6, 0, 8]), (1.45, [-36, 0, -20]), (1.6, [-42, 0, -16]), (3.0, [-40, 0, -20]), (4.4, [-46, 0, -24]), (4.62, [-30, 0, 78]), (4.8, [-26, 0, 66]), (5.1, Z3))},
        "fore_l": {"rotation": K((0, Z3), (1.2, Z3), (1.45, [-62, 0, 0]), (3.0, [-58, 0, 0]), (4.4, [-64, 0, 0]), (4.62, [-10, 0, 0]), (5.1, Z3))},
        "hand_l": {"rotation": K((0, Z3), (1.5, [10, 0, -10]), (3.0, [10, -30, -10]), (4.4, [14, -80, -12]), (4.6, [-20, 0, 0]), (5.1, Z3))},
        "body": {"rotation": K((0, Z3), (1.0, [8, -10, 0]), (1.2, [10, -12, 0]), (1.5, [-6, 0, 0]), (3.0, [-4, 4, 0]), (4.4, [-8, -4, 0]), (4.62, [-12, 0, 0]), (5.1, Z3))},
        "chest": {"rotation": K((0, Z3), (1.2, [6, -6, 0]), (1.5, [4, 0, 0]), (3.0, [6, 0, 0]), (4.4, [8, 0, 0]), (4.62, [-10, 0, 0]), (5.1, Z3))},
        "head": {"rotation": K((0, Z3), (1.0, [6, -8, 0]), (1.5, [22, 0, 0]), (3.0, [24, 4, 0]), (4.4, [26, -4, 0]), (4.62, [-18, 0, 0]), (5.1, Z3))},
        "float": {"position": K((0, Z3), (1.0, [0, -1.2, -1.6]), (1.2, [0, -1.4, -2.0]), (1.5, [0, 1.0, 1.2]), (3.0, [0, 1.6, 0.8]), (4.4, [0, 2.2, 0.6]), (4.62, [0, 5.0, 1.6]), (4.85, [0, 3.0, 0.6]), (5.1, Z3))},
        "wring": {"scale": K((0, 1), (1.5, 1.1), (4.4, 1.25), (4.62, 1.45), (5.1, 1))},
        "halo": {"scale": K((0, 1), (1.5, 1.05), (4.4, 1.15), (4.62, 1.3), (5.1, 1))}}}
    # ---------------------------------------------------------------- v1.245 새 패턴 동작
    def _minrot(a, b):
        a, b = nrm(np.array(a, float)), nrm(np.array(b, float))
        v = np.cross(a, b); c = float(np.dot(a, b))
        if np.linalg.norm(v) < 1e-6: return np.eye(3)
        Kx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + Kx + Kx @ Kx * (1 / (1 + c))
    def chain(i, tg):
        """꼬리 i 마디 셋이 세계 (모델) 방향 tg[g] 를 가리키는 마디별 회전 (부모 회전을 빼서) · 끝 자리"""
        Rw = np.eye(3); out = []
        P = J['tail_pts'][i]; p = np.array(P[0], float)
        for g in range(3):
            d0 = J['tail_dirs'][i][g]
            Rl = _minrot(d0, Rw.T @ nrm(np.array(tg[g], float)))
            Rw = Rw @ Rl
            out.append([round(float(v), 1) for v in tex_kit.euler_of(Rl)])
            p = p + nrm(np.array(tg[g], float)) * np.linalg.norm(np.array(P[g + 1]) - np.array(P[g]))
        return out, p
    def tail_keys(i, poses):
        """poses = [(시각, 방향 셋 | None = 쉬는 자세)] → 마디 셋의 키"""
        ch = [dict() for _ in range(3)]
        for t, tg in poses:
            e = chain(i, tg)[0] if tg is not None else [Z3, Z3, Z3]
            for g in range(3): ch[g][t] = e[g]
        return {f"tail{i}_{g}_cut": {"rotation": K(*sorted(ch[g].items()))} for g in range(3)}
    def fan(i, k=1.0, up=0.4):
        sx = 1 if i < 4 else -1
        return [nrm(J['tail_dirs'][i][g] + np.array([sx * 0.7 * k, up * k * (1 + 0.3 * g), 0.15 * k])) for g in range(3)]
    STAB = {0: ([(0.45, 1.0, 0.35), (0.3, 0.55, -0.9), (0.08, -0.35, -1.0)], [(0.45, 1.0, 0.4), (0.3, 0.9, -0.3), (0.1, 0.9, 0.4)]),
            1: ([(0.85, 0.6, 0.3), (0.45, 0.25, -0.9), (0.1, -0.2, -1.0)], [(0.85, 0.6, 0.4), (0.5, 0.6, -0.3), (0.2, 0.7, 0.5)])}
    def stab_dirs(i, wind=False):
        sx = 1 if i < 4 else -1
        a = STAB[i % 4][1 if wind else 0]
        return [(sx * x, y, z) for x, y, z in a]
    J['stab_tips'] = {}
    for i in (0, 4, 1, 5):
        tip = chain(i, stab_dirs(i))[1] + nrm(np.array(stab_dirs(i)[2])) * 6.0
        J['stab_tips'][i] = tip
    LAND = -17.0
    tb = {"float": {"position": K((0, Z3), (0.22, [0, 4.0, 0.6]), (0.42, [0, LAND, -1.0]), (0.5, [0, LAND + 1.8, -0.6]), (0.62, [0, LAND + 0.6, 0]), (0.8, [0, LAND, -1.2]), (1.9, [0, LAND, -1.2]), (2.0, [0, LAND - 0.6, -1.6]), (2.3, [0, LAND + 0.8, 0]), (2.75, Z3))},
          "body": {"rotation": K((0, Z3), (0.22, [-6, 0, 0]), (0.42, [14, 0, 0]), (0.62, [6, 0, 0]), (0.8, [16, 0, 0]), (1.9, [14, 0, 0]), (2.0, [18, 0, 0]), (2.4, [2, 0, 0]), (2.75, Z3))},
          "chest": {"rotation": K((0, Z3), (0.42, [6, 0, 0]), (0.65, [-4, 0, 0]), (0.8, [8, 0, 0]), (1.9, [6, 0, 0]), (2.75, Z3))},
          "head": {"rotation": K((0, Z3), (0.42, [8, 0, 0]), (0.65, [-18, 0, 0]), (0.8, [-12, 0, 0]), (1.9, [-12, 0, 0]), (2.75, Z3))},
          "leg_r": {"rotation": K((0, Z3), (0.22, [-10, 0, 0]), (0.42, [22, 0, -6]), (0.6, [16, 0, -6]), (1.9, [16, 0, -6]), (2.3, [6, 0, 0]), (2.75, Z3))},
          "shin_r": {"rotation": K((0, Z3), (0.42, [-30, 0, 0]), (0.6, [-24, 0, 0]), (1.9, [-24, 0, 0]), (2.75, Z3))},
          "leg_l": {"rotation": K((0, Z3), (0.22, [-14, 0, 0]), (0.42, [-22, 0, 6]), (0.6, [-18, 0, 6]), (1.9, [-18, 0, 6]), (2.75, Z3))},
          "shin_l": {"rotation": K((0, Z3), (0.42, [28, 0, 0]), (0.6, [22, 0, 0]), (1.9, [22, 0, 0]), (2.75, Z3))},
          "arm_r": {"rotation": K((0, Z3), (0.22, [-20, 0, -20]), (0.42, [26, 0, -42]), (0.62, [18, 0, -34]), (0.8, [34, 0, -40]), (1.9, [30, 0, -38]), (2.0, [36, 0, -44]), (2.75, Z3))},
          "arm_l": {"rotation": K((0, Z3), (0.22, [-20, 0, 20]), (0.42, [26, 0, 42]), (0.62, [18, 0, 34]), (0.8, [34, 0, 40]), (1.9, [30, 0, 38]), (2.0, [36, 0, 44]), (2.75, Z3))},
          "fore_r": {"rotation": K((0, Z3), (0.42, [-18, 0, 0]), (1.9, [-14, 0, 0]), (2.75, Z3))}, "fore_l": {"rotation": K((0, Z3), (0.42, [-18, 0, 0]), (1.9, [-14, 0, 0]), (2.75, Z3))},
          "mantle": {"rotation": K((0, Z3), (0.42, [-16, 0, 0]), (0.62, [6, 0, 0]), (0.8, [-10, 0, 0]), (1.9, [-8, 0, 0]), (2.75, Z3))},
          "gown0_cut": {"rotation": K((0, Z3), (0.3, [-6, 0, 0]), (0.45, [10, 0, 0]), (0.6, [-3, 0, 0]), (0.8, [4, 0, 0]), (2.75, Z3))},
          "gown1_cut": {"rotation": K((0, Z3), (0.36, [-8, 0, 0]), (0.52, [12, 0, 0]), (0.7, [-3, 0, 0]), (0.9, [4, 0, 0]), (2.75, Z3))},
          "halo": {"scale": K((0, 1), (0.42, 0.92), (0.8, 1.2), (1.9, 1.15), (2.75, 1))}}
    for i in range(8):
        if i % 4 in (0, 1):                                                                   # 찌르는 두 쌍: 어깨 위로 감아 앞으로 겨눔 → 뒤로 당겼다 (0.62 · 1.75) 찌름 (0.8 · 1.9 초)
            S_, W_ = stab_dirs(i), stab_dirs(i, True)
            tb.update(tail_keys(i, [(0, None), (0.42, W_), (0.62, W_), (0.8, S_), (1.6, S_), (1.75, W_), (1.9, S_), (2.25, fan(i, 0.5)), (2.75, None)]))
        else:
            tb.update(tail_keys(i, [(0, None), (0.42, fan(i, 1.0)), (0.8, fan(i, 1.2, 0.6)), (1.9, fan(i, 1.1, 0.5)), (2.75, None)]))
    A[f"{N}.tail"] = {"animation_length": 2.75, "bones": tb}                                    # 꼬리 관통: 땅에 내려앉아 (0.42 초) 꼬리 두 쌍을 어깨 위로 감아 찌름 (0.8 · 1.9 초 · 스크립트가 꼬리 창을 뻗음)
    WL = 32.6
    hold = lambda base, amp, t0, t1, n_: [(t0 + (t1 - t0) * k / n_, [base[0], base[1] + amp * (1 if k % 2 else -1) * (k not in (0, n_)), base[2]]) for k in range(n_ + 1)]
    wb = {"float": {"position": K((0, Z3), (0.4, [0, -3.0, 0]), (1.4, [0, 10.0, 0]), *hold([0, 9.0, 0], 0.8, 1.8, 30.6, 20), (31.0, [0, 11.0, 0]), (31.4, [0, 6.0, 0]), (32.6, Z3))},
          "arm_r": {"rotation": K((0, Z3), (0.4, [-30, 0, 16]), (1.4, [-6, 0, -78]), (1.8, [-2, 0, -72]), *[(t, [-4, 0, -74 + 3 * ((k % 2) * 2 - 1)]) for k, t in enumerate(np.linspace(2.4, 30.4, 15))], (30.8, [-6, 0, -76]), (31.1, [-80, 0, -6]), (31.4, [-76, 0, 4]), (32.6, Z3))},
          "arm_l": {"rotation": K((0, Z3), (0.4, [-30, 0, -16]), (1.4, [-6, 0, 80]), (1.8, [-2, 0, 74]), *[(t, [-4, 0, 76 - 3 * ((k % 2) * 2 - 1)]) for k, t in enumerate(np.linspace(2.4, 30.4, 15))], (30.8, [-6, 0, 78]), (31.1, [-80, 0, 6]), (31.4, [-76, 0, -4]), (32.6, Z3))},
          "fore_r": {"rotation": K((0, Z3), (0.4, [-40, 0, 0]), (1.4, [-8, 0, 0]), (30.8, [-10, 0, 0]), (31.2, [-30, 0, 0]), (32.6, Z3))},
          "fore_l": {"rotation": K((0, Z3), (0.4, [-40, 0, 0]), (1.4, [-8, 0, 0]), (30.8, [-10, 0, 0]), (31.2, [-30, 0, 0]), (32.6, Z3))},
          "hand_r": {"rotation": K((0, Z3), (1.4, [0, 0, -30]), (30.8, [0, 0, -26]), (31.2, [-20, 0, 0]), (32.6, Z3))},
          "hand_l": {"rotation": K((0, Z3), (1.4, [0, 0, 30]), (30.8, [0, 0, 26]), (31.2, [-20, 0, 0]), (32.6, Z3))},
          "head": {"rotation": K((0, Z3), (0.4, [16, 0, 0]), (1.4, [-18, 0, 0]), (30.8, [-16, 0, 0]), (31.2, [10, 0, 0]), (32.6, Z3))},
          "body": {"rotation": K((0, Z3), (0.4, [10, 0, 0]), (1.4, [-6, 0, 0]), (30.8, [-5, 0, 0]), (31.2, [8, 0, 0]), (32.6, Z3))},
          "chest": {"rotation": K((0, Z3), (0.4, [8, 0, 0]), (1.4, [-10, 0, 0]), (30.8, [-9, 0, 0]), (31.2, [6, 0, 0]), (32.6, Z3))},
          "leg_r": {"rotation": K((0, Z3), (0.4, [-20, 0, 0]), (1.4, [8, 0, -4]), (30.8, [8, 0, -4]), (32.6, Z3))},
          "leg_l": {"rotation": K((0, Z3), (0.4, [-10, 0, 0]), (1.4, [4, 0, 4]), (30.8, [4, 0, 4]), (32.6, Z3))},
          "mantle": {"rotation": K((0, Z3), (0.4, [10, 0, 0]), (1.4, [-22, 0, 0]), (30.8, [-18, 0, 0]), (31.2, [8, 0, 0]), (32.6, Z3))},
          "halo": {"scale": K((0, 1), (0.4, 0.9), (1.4, 1.35), (30.8, 1.3), (31.2, 1.5), (32.6, 1))},
          "wring": {"scale": K((0, 1), (0.4, 0.9), (1.4, 1.3), (30.8, 1.25), (31.2, 1.45), (32.6, 1))}}
    for i in range(8): wb.update(tail_keys(i, [(0, None), (0.4, fan(i, 0.3, 0.1)), (1.4, fan(i, 1.4, 0.7)), (30.8, fan(i, 1.3, 0.6)), (31.2, fan(i, 1.6, 0.9)), (32.6, None)]))
    A[f"{N}.world"] = {"animation_length": WL, "bones": wb}                                     # 멈춘 세계 (v1.246 30 초): 떠올라 두 팔을 좌우로 펼치고 꼬리를 공작처럼 펼침 → 두 팔을 모아 시계를 깸 (31.1 초)
    A[f"{N}.summon"] = {"animation_length": 2.6, "bones": {                                     # 시곗바늘 창: 두 팔을 들어 등 뒤에 바늘을 펼침 → 든 손으로 앞을 가리킴 (0.95 초 ~ 차례로 날아감)
        "arm_l": {"rotation": K((0, Z3), (0.45, R2([-24, 0, 12])), (0.75, R2([-14, 0, 22])), (0.95, [-98, 0, 8]), (1.05, [-92, 0, 4]), (2.1, [-90, 0, 6]), (2.6, Z3))},
        "fore_l": {"rotation": K((0, Z3), (0.45, [-30, 0, 0]), (0.95, [-2, 0, 0]), (2.1, [-4, 0, 0]), (2.6, Z3))},
        "hand_l": {"rotation": K((0, Z3), (0.45, [-20, 0, 0]), (0.95, [-30, 0, 0]), (2.6, Z3))},
        "arm_r": {"rotation": K((0, Z3), (0.45, [-40, 0, -70]), (0.8, [-30, 0, -80]), (1.0, [14, 0, -34]), (2.1, [10, 0, -30]), (2.6, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.45, [-30, 0, 0]), (1.0, [-10, 0, 0]), (2.6, Z3))},
        "body": {"rotation": K((0, Z3), (0.45, [-8, 6, 0]), (0.95, [8, -16, 0]), (2.1, [6, -14, 0]), (2.6, Z3))},
        "chest": {"rotation": K((0, Z3), (0.45, [-8, 0, 0]), (0.95, [4, -10, 0]), (2.6, Z3))},
        "head": {"rotation": K((0, Z3), (0.45, [-20, 0, 0]), (0.95, [4, 10, 0]), (2.1, [2, 8, 0]), (2.6, Z3))},
        "float": {"position": K((0, Z3), (0.45, [0, 5.0, 1.0]), (0.95, [0, 2.0, -2.5]), (2.1, [0, 2.5, -2.0]), (2.6, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.5, [-18, 0, 0]), (1.0, [10, 0, 0]), (1.4, [-4, 0, 0]), (2.6, Z3))},
        "halo": {"scale": K((0, 1), (0.5, 1.25), (0.95, 1.1), (2.6, 1))},
        "astro": {"position": K((0, Z3), (0.5, [0, 6, 0]), (0.95, [0, 2, 0]), (2.6, Z3)), "scale": K((0, 1), (0.5, 1.3), (0.95, 1.1), (2.6, 1))}}}
    def dial_anim(L=4.8, t0=1.0, t1=4.0):
        """열두 시각: 든 팔로 땅의 큰 시계 바늘을 가리키며 바늘과 함께 한 바퀴 돎 (몸 = float y · 오른쪽으로 돎)"""
        ys = {f"{t:.2f}": [0, -360 * float(np.clip((t - t0) / (t1 - t0), 0, 1)), 0] for t in np.arange(0, L + 0.001, 0.1)}
        ys[f"{L:.2f}"] = [0, -360, 0]
        return {"float": {"rotation": ys, "position": K((0, Z3), (0.6, [0, 4.0, 0]), (t1, [0, 4.0, 0]), (t1 + 0.3, [0, 5.0, 0]), (L, Z3))},
                "arm_l": {"rotation": K((0, Z3), (0.6, [-56, 0, 30]), (t1, [-56, 0, 30]), (t1 + 0.3, R2([-10, 0, 10])), (L, Z3))},
                "fore_l": {"rotation": K((0, Z3), (0.6, [-6, 0, 0]), (t1, [-6, 0, 0]), (L, Z3))},
                "arm_r": {"rotation": K((0, Z3), (0.6, [-10, 0, -50]), (t1, [-10, 0, -52]), (L, Z3))},
                "body": {"rotation": K((0, Z3), (0.6, [6, -14, 4]), (t1, [6, -14, 4]), (L, Z3))},
                "head": {"rotation": K((0, Z3), (0.6, [24, -16, 0]), (t1, [24, -16, 0]), (L, Z3))},
                "mantle": {"rotation": K((0, Z3), (1.0, [-12, 0, 0]), (t1, [-14, 0, 0]), (L, Z3))},
                "gown0_cut": {"rotation": K((0, Z3), (1.2, [-6, 0, 6]), (t1, [-6, 0, 6]), (L, Z3))},
                "gown1_cut": {"rotation": K((0, Z3), (1.2, [-8, 0, 8]), (t1, [-8, 0, 8]), (L, Z3))}}
    A[f"{N}.dial"] = {"animation_length": 4.8, "bones": dial_anim()}
    def pend_anim(T0=0.9, Ts=1.2, n=3, Am=26):
        L = T0 + n * Ts + 0.9
        sw_ = lambda t: Am * math.cos(math.pi * min(max(t - T0, 0), n * Ts) / Ts)
        ts = list(np.arange(0.6, T0 + n * Ts + 0.01, 0.15))
        armr = [(0, Z3), (0.5, [-150, 0, -30])] + [(t, [-150, 0, -30 + sw_(t)]) for t in ts] + [(L, Z3)]
        arml = [(0, Z3), (0.5, [-150, 0, 30])] + [(t, [-150, 0, 30 + sw_(t)]) for t in ts] + [(L, Z3)]
        bod = [(0, Z3), (0.5, [-6, 0, 0])] + [(t, [-6, 0, sw_(t) * 0.35]) for t in ts] + [(L, Z3)]
        return L, {"arm_r": {"rotation": K(*armr)}, "arm_l": {"rotation": K(*arml)}, "body": {"rotation": K(*bod)},
                   "fore_r": {"rotation": K((0, Z3), (0.5, [-20, 0, 0]), (L - 0.9, [-20, 0, 0]), (L, Z3))}, "fore_l": {"rotation": K((0, Z3), (0.5, [-20, 0, 0]), (L - 0.9, [-20, 0, 0]), (L, Z3))},
                   "head": {"rotation": K((0, Z3), (0.5, [-24, 0, 0]), (L - 0.9, [-20, 0, 0]), (L, Z3))},
                   "float": {"position": K((0, Z3), (0.5, [0, 6.0, 0]), (L - 0.9, [0, 6.0, 0]), (L, Z3))},
                   "mantle": {"rotation": K((0, Z3), (0.5, [-20, 0, 0]), (L - 0.9, [-16, 0, 0]), (L, Z3))},
                   "halo": {"scale": K((0, 1), (0.5, 1.25), (L - 0.9, 1.2), (L, 1))}}
    PL_, pb = pend_anim()
    A[f"{N}.pend"] = {"animation_length": PL_, "bones": pb}                                     # 진자의 심판: 두 팔을 높이 들고 진자와 함께 좌우로 흔듦
    A[f"{N}.roll"] = {"animation_length": 1.5, "bones": {                                       # 톱니 굴림: 웅크려 두 팔을 뒤로 → 앞으로 낮게 휘둘러 톱니를 굴려 보냄 (0.6 초)
        "arm_r": {"rotation": K((0, Z3), (0.35, [46, 0, -24]), (0.6, [-56, 0, -14]), (0.8, [-86, 0, -24]), (1.5, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.35, [46, 0, 24]), (0.6, [-56, 0, 14]), (0.8, [-86, 0, 24]), (1.5, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.35, [-20, 0, 0]), (0.6, [-4, 0, 0]), (1.5, Z3))}, "fore_l": {"rotation": K((0, Z3), (0.35, [-20, 0, 0]), (0.6, [-4, 0, 0]), (1.5, Z3))},
        "body": {"rotation": K((0, Z3), (0.35, [-8, 0, 0]), (0.6, [18, 0, 0]), (0.8, [22, 0, 0]), (1.5, Z3))},
        "head": {"rotation": K((0, Z3), (0.35, [10, 0, 0]), (0.6, [-14, 0, 0]), (1.5, Z3))},
        "float": {"position": K((0, Z3), (0.35, [0, -3.0, 1.5]), (0.6, [0, -1.0, -3.0]), (0.8, [0, 0.5, -3.5]), (1.5, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.35, [-12, 0, 0]), (0.65, [14, 0, 0]), (1.0, [-3, 0, 0]), (1.5, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (0.4, [-6, 0, 0]), (0.7, [8, 0, 0]), (1.5, Z3))}}}
    # v1.246 부활: 장신구가 떨어져 부서지고 (0.35 ~ 1.6 초) 몸이 축 늘어져 매달림 → 등 뒤 시계가 거꾸로 돌며 (2.6 초 ~) 부서진 장신구가 거꾸로 날아와 붙고 (3.5 ~ 4.5 초) 다시 일어섬
    FL = 5.4
    rng = np.random.default_rng(246)
    piv = {b_['name']: b_['pivot'] for b_ in F.bones}
    orn = [n_ for n_ in ('halo_root', 'waist_root', 'fring_rest', 'astro', 'horb', 'crown_cut', 'chest_gem', 'buckle') if n_ in piv]
    orn += [n_ for n_ in piv if n_.startswith('hchain_') and n_[-1] == '0'] + [f'tail{i}_gear_rest' for i in range(J['tails'])]
    fb = {}
    for n_ in orn:
        y0 = piv[n_][1]
        drop = -(y0 + 10) if not n_.startswith('tail') else -60.0
        td = 0.35 + rng.uniform(0, 0.45); tl = td + 0.45 + abs(drop) / 260
        dx, dz = rng.uniform(-10, 10), rng.uniform(-8, 8)
        rx, ry, rz = rng.uniform(-260, 260, 3)
        land = [dx, drop, dz]
        fb[n_] = {"position": K((0, Z3), (td, [0, 1.5, 0]), ((td + tl) / 2, [dx * 0.5, drop * 0.3, dz * 0.5]), (tl, land), (tl + 0.08, [dx, drop + 2.0, dz]), (3.5, land),
                               (3.95, [dx * 0.6, drop * 0.55, dz * 0.6]), (4.35, [0, 2.0, 0]), (4.55, [0, -0.6, 0]), (FL, Z3)),
                  "rotation": K((0, Z3), (td, [0, 0, 0]), (tl, [rx, ry, rz]), (3.5, [rx, ry, rz]), (4.35, [-8, 0, 0]), (4.55, Z3), (FL, Z3)),
                  "scale": K((0, 1), (tl, 1), (tl + 0.05, 1.25), (tl + 0.14, 0), (3.5, 0), (3.62, 1.2), (3.75, 1), (FL, 1))}
    for k in range(J['streaks']): fb[f"streak{k}_add"] = {"scale": K((0, 1), (0.4, 1.1), (0.9, 0), (3.6, 0), (4.4, 1.15), (FL, 1))}
    for i in range(J['twinkles']): fb[f"twinkle{i}_add"] = {"scale": K((0, 1), (0.6, 0), (3.8, 0), (4.6, 1), (FL, 1))}
    fb.update({
        "float": {"position": K((0, Z3), (0.15, [0, 1.5, 1.2]), (0.5, [0, -2.0, 0.5]), (1.4, [0, -6.0, 0]), (2.0, [1.0, -6.5, 0]), (2.6, [-1.0, -6.0, 0]), (3.2, [0.6, -6.4, 0]),
                                (3.6, [0, -5.5, 0]), (4.5, [0, 5.0, 0]), (4.8, [0, 3.5, 0]), (FL, Z3)),
                  "rotation": K((0, Z3), (1.4, [0, 0, 3]), (2.0, [0, 0, -3]), (2.6, [0, 0, 2.5]), (3.2, [0, 0, -2]), (3.6, Z3), (FL, Z3))},
        "body": {"rotation": K((0, Z3), (0.15, [-12, 0, 0]), (0.6, [8, 0, 4]), (1.4, [10, 0, 5]), (3.5, [11, 0, 4]), (4.4, [-10, 0, 0]), (4.8, [-4, 0, 0]), (FL, Z3))},
        "chest": {"rotation": K((0, Z3), (0.15, [-8, 0, 0]), (1.4, [6, 0, -4]), (3.5, [7, 0, -4]), (4.4, [-8, 0, 0]), (FL, Z3))},
        "head": {"rotation": K((0, Z3), (0.15, [-24, 0, 0]), (0.7, [26, 0, 10]), (1.4, [38, 0, 14]), (3.5, [40, 0, 12]), (4.3, [-22, 0, 0]), (4.8, [-10, 0, 0]), (FL, Z3))},
        "arm_r": {"rotation": K((0, Z3), (0.15, [-30, 0, -40]), (0.9, [14, 0, 14]), (1.6, [12, 0, 18]), (3.5, [10, 0, 16]), (4.4, [-30, 0, -78]), (4.8, [-20, 0, -60]), (FL, Z3))},
        "arm_l": {"rotation": K((0, Z3), (0.15, [-30, 0, 40]), (0.9, [14, 0, -14]), (1.6, [12, 0, -18]), (3.5, [10, 0, -16]), (4.4, [-30, 0, 80]), (4.8, [-20, 0, 62]), (FL, Z3))},
        "fore_r": {"rotation": K((0, Z3), (0.9, [6, 0, 0]), (3.5, [6, 0, 0]), (4.4, [-14, 0, 0]), (FL, Z3))}, "fore_l": {"rotation": K((0, Z3), (0.9, [6, 0, 0]), (3.5, [6, 0, 0]), (4.4, [-14, 0, 0]), (FL, Z3))},
        "hand_r": {"rotation": K((0, Z3), (1.0, [20, 0, 0]), (3.5, [22, 0, 0]), (4.4, [-10, 0, 0]), (FL, Z3))}, "hand_l": {"rotation": K((0, Z3), (1.0, [20, 0, 0]), (3.5, [22, 0, 0]), (4.4, [-10, 0, 0]), (FL, Z3))},
        "leg_r": {"rotation": K((0, Z3), (1.0, [-20, 0, 4]), (3.5, [-22, 0, 4]), (4.4, [6, 0, 0]), (FL, Z3))}, "shin_r": {"rotation": K((0, Z3), (1.0, [24, 0, 0]), (3.5, [26, 0, 0]), (4.4, [0, 0, 0]), (FL, Z3))},
        "leg_l": {"rotation": K((0, Z3), (1.0, [6, 0, -4]), (3.5, [8, 0, -4]), (4.4, [-6, 0, 0]), (FL, Z3))}, "shin_l": {"rotation": K((0, Z3), (1.0, [12, 0, 0]), (3.5, [14, 0, 0]), (FL, Z3))},
        "mantle": {"rotation": K((0, Z3), (0.3, [-12, 0, 0]), (1.4, [14, 0, 0]), (3.5, [16, 0, 0]), (4.4, [-24, 0, 0]), (4.9, [6, 0, 0]), (FL, Z3))},
        "gown0_cut": {"rotation": K((0, Z3), (1.4, [6, 0, 2]), (3.5, [6, 0, 2]), (4.4, [-6, 0, 0]), (FL, Z3))},
        "gown1_cut": {"rotation": K((0, Z3), (1.4, [8, 0, 3]), (3.5, [8, 0, 3]), (4.4, [-8, 0, 0]), (FL, Z3))}})
    down = lambda i, k: [nrm(np.array([(0.3 if i < 4 else -0.3) * k * (1 + 0.3 * (i % 4)), -1.0, -0.15])) for g in range(3)]
    for i in range(J['tails']): fb.update(tail_keys(i, [(0, None), (0.3, fan(i, 0.4, 0.3)), (1.4, down(i, 1.0)), (3.5, down(i, 1.2)), (4.4, fan(i, 1.3, 0.7)), (4.9, fan(i, 0.4, 0.2)), (FL, None)]))
    A[f"{N}.fall"] = {"animation_length": FL, "bones": fb}
    for old in ("cast_up", "flip", "throw", "sweep", "conduct"): A.pop(f"{N}.{old}", None)    # v1.245 옛 기술 동작 지움 (기술을 갈아엎음)
    TD = J.get('tail_dirs', [])
    SD = J.get('slock_dirs', {})
    def _ev(ch, t):
        ks = sorted((float(k), (v["post"] if isinstance(v, dict) else v)) for k, v in ch.items())
        if t <= ks[0][0]: return np.array(ks[0][1], float)
        for (t0, a), (t1, b) in zip(ks, ks[1:]):
            if t <= t1: q = (t - t0) / max(t1 - t0, 1e-6); return np.array(a, float) * (1 - q) + np.array(b, float) * q
        return np.array(ks[-1][1], float)
    def _rod(w):
        a = np.linalg.norm(w)
        if a < 1e-6: return np.eye(3)
        k = w / a; Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        return np.eye(3) + math.sin(a) * Kx + (1 - math.cos(a)) * Kx @ Kx
    def physics(an, L, dirs, names, gain, cap, lag):
        """끌림 물리 (v1.242): 떠 있는 몸 (float) 이 움직이는 반대쪽으로 마디가 끌림 — 마디마다 한 박자씩 늦게 · 용수철 (넘쳤다 자리 잡음) · 가라앉으면 위로 · 솟으면 아래로"""
        fl = an["bones"].get("float", {}).get("position")
        if not isinstance(fl, dict): return
        P = lambda t: _ev(fl, min(max(t, 0), L)) * np.array([-1, 1, 1])                       # 애니 위치 x = 모델 x 반대
        dt = 1 / 120
        for d_, nm in zip(dirs, names):
            for g, (d, bn) in enumerate(zip(d_, nm)):
                w, wv = np.zeros(3), np.zeros(3)
                keys = {}
                for st_ in range(int(L / dt) + 1):
                    t = st_ * dt
                    tl = t - lag * g
                    V = (P(tl + 0.02) - P(tl - 0.02)) / 0.04
                    sp = np.linalg.norm(V)
                    tgt = np.zeros(3)
                    if sp > 1e-3:
                        ax = np.cross(d, -V / sp)
                        if np.linalg.norm(ax) > 1e-4: tgt = nrm(ax) * math.radians(min(sp * gain, cap)) * (1 - 0.25 * g)
                    wv += (90 * (tgt - w) - 11 * wv) * dt; w = w + wv * dt
                    if st_ % (32 if L > 10 else 16 if L > 4 else 8) == 0: keys[f"{t:.2f}"] = [round(v, 1) for v in tex_kit.euler_of(_rod(w))]
                keys[f"{L:.2f}"] = [0, 0, 0]
                base = an["bones"].get(bn, {}).get("rotation")
                if isinstance(base, dict):                                                    # v1.245 애니에 정한 자세 (꼬리 찌르기 · 펼침) 위에 끌림을 더함
                    keys = {t_: [round(a_ + b_, 1) for a_, b_ in zip(_ev(base, float(t_)), v_)] for t_, v_ in keys.items()}
                an["bones"][bn] = {"rotation": keys}
    for nm, an in A.items():
        if nm.endswith(".idle") or nm.endswith(".die"): continue
        L = an["animation_length"]
        physics(an, L, TD, [[f"tail{i}_{g}_cut" for g in range(3)] for i in range(len(TD))], 0.32, 58, 0.07)
        physics(an, L, [SD[k] for k in SD], [[f"slock_{k}_{g}" for g in range(2)] for k in SD], 0.22, 35, 0.06)
    for nm, an in A.items():                                                                 # v1.240 어깨 망토 자락이 팔을 따라 들림 (팔 회전의 일부 · 팔이 망토를 뚫지 않게)
        if nm.endswith(".idle"): continue
        for s_ in ("r", "l"):
            rot = an["bones"].get(f"arm_{s_}", {}).get("rotation")
            if not isinstance(rot, dict): continue
            an["bones"][f"cape_{s_}_cut"] = {"rotation": {t: {**kv, "post": [kv["post"][0] * 0.25, 0, kv["post"][2] * 0.55]} for t, kv in rot.items()}}
    for k in range(J['streaks']):
        A[f"{N}.die"]["bones"][f"streak{k}_add"] = {"scale": K((0, 1), (1.0, 1.1), (2.4, 0.0), (4.0, 0.0))}
    return A


if __name__ == "__main__":
    main()
