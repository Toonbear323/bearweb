"""Painting helpers shared by the witch model builder."""
import math
import numpy as np
from PIL import Image, ImageDraw


def C(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.


def T(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def mix(a, b, t):
    t = np.asarray(t, float)
    if t.ndim:          # t is always a scalar field, colours carry the trailing channel axis
        t = t[..., None]
    return a * (1 - t) + b * t


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-12), 0, 1)
    return t * t * (3 - 2 * t)


def ramp(t, stops):
    """stops: [(pos, '#hex'), ...] ascending; returns (...,3)"""
    t = np.clip(np.asarray(t, float), stops[0][0], stops[-1][0])
    xs = np.array([s[0] for s in stops])
    cs = np.array([C(s[1]) if isinstance(s[1], str) else s[1] for s in stops])
    return np.stack([np.interp(t, xs, cs[:, i]) for i in range(3)], -1)


def hashf(a, b, c, seed=0):
    """deterministic pseudo random in [0,1) from integer lattice coords"""
    a = np.asarray(a, np.int64)
    b = np.asarray(b, np.int64)
    c = np.asarray(c, np.int64)
    n = (a * 73856093) ^ (b * 19349663) ^ (c * 83492791) ^ (seed * 2654435761)
    n = (n ^ (n >> 13)) * 1274126177
    n = n ^ (n >> 16)
    return (n & 0xFFFF) / 65536.


def grain(ctx, amp=0.035, cell=4.0):
    """per-texel brightness jitter (keeps the pixel-art feel)"""
    P = ctx.P
    q = np.floor(P * cell + 1000.5).astype(np.int64)
    return 1 + (hashf(q[..., 0], q[..., 1], q[..., 2], ctx.seed) - .5) * 2 * amp


def vnoise(P, scale, seed=0):
    """smooth 3D value noise in [0,1]"""
    Q = P * scale + 1000.
    i = np.floor(Q).astype(np.int64)
    f = Q - i
    f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * hashf(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def rgba(rgb, a=1.0):
    a = np.broadcast_to(np.asarray(a, float), rgb.shape[:2])
    return np.concatenate([rgb, a[..., None]], -1)


def solid(col):
    c = C(col) if isinstance(col, str) else col

    def f(ctx):
        return np.broadcast_to(c, (ctx.h, ctx.w, 3)) * grain(ctx)[..., None]
    return f


# ------------------------------------------------ 2D supersampled canvas
class Canvas:
    """PIL canvas in *texel* coordinates, supersampled; alpha is thresholded on export."""

    def __init__(self, w, h, ss=4, bg=None):
        self.w, self.h, self.ss = w, h, ss
        self.im = Image.new('RGBA', (w * ss, h * ss), bg if bg else (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def poly(self, pts, fill):
        self.d.polygon(self._p(pts), fill=fill)

    def line(self, pts, fill, width=1.0):
        s = self.ss
        self.d.line(self._p(pts), fill=fill, width=max(1, int(round(width * s))), joint='curve')
        r = width * s / 2
        for x, y in (self._p(pts)[0], self._p(pts)[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def ell(self, cx, cy, rx, ry, fill):
        s = self.ss
        self.d.ellipse(((cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s), fill=fill)

    def rect(self, x0, y0, x1, y1, fill):
        s = self.ss
        self.d.rectangle((x0 * s, y0 * s, x1 * s - 1, y1 * s - 1), fill=fill)

    def arr(self):
        return np.asarray(self.im, float) / 255.

    def paste_arr(self, a):
        self.im = Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8), 'RGBA')
        self.d = ImageDraw.Draw(self.im)

    def grid(self):
        """texel-space coordinate grids at supersampled resolution"""
        s = self.ss
        X, Y = np.meshgrid((np.arange(self.w * s) + .5) / s, (np.arange(self.h * s) + .5) / s)
        return X, Y

    def out(self, cut=0.5):
        a = self.arr()
        s = self.ss
        pre = a[..., :3] * a[..., 3:4]
        pre = pre.reshape(self.h, s, self.w, s, 3).mean((1, 3))
        al = a[..., 3].reshape(self.h, s, self.w, s).mean((1, 3))
        rgb = pre / np.maximum(al[..., None], 1e-6)
        rgb[al < 1e-6] = 0
        return np.concatenate([rgb, (al >= cut).astype(float)[..., None]], -1)


def bez(p0, p1, p2, p3=None, n=24):
    ts = np.linspace(0, 1, n)
    p0, p1, p2 = (np.array(p, float) for p in (p0, p1, p2))
    if p3 is None:
        pts = ((1 - ts) ** 2)[:, None] * p0 + (2 * (1 - ts) * ts)[:, None] * p1 + (ts ** 2)[:, None] * p2
    else:
        p3 = np.array(p3, float)
        pts = ((1 - ts) ** 3)[:, None] * p0 + (3 * (1 - ts) ** 2 * ts)[:, None] * p1 + (3 * (1 - ts) * ts ** 2)[:, None] * p2 + (ts ** 3)[:, None] * p3
    return [tuple(p) for p in pts]


def ribbon(cv, pts, w0, w1, fill):
    """tapered thick polyline"""
    pts = np.array(pts, float)
    n = len(pts)
    tang = np.gradient(pts, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
    nor = np.stack([-tang[:, 1], tang[:, 0]], 1)
    ws = np.linspace(w0, w1, n)[:, None] / 2
    left = pts + nor * ws
    right = pts - nor * ws
    cv.poly([tuple(p) for p in left] + [tuple(p) for p in right[::-1]], fill)
    cv.ell(pts[0][0], pts[0][1], w0 / 2, w0 / 2, fill)
    cv.ell(pts[-1][0], pts[-1][1], w1 / 2, w1 / 2, fill)
