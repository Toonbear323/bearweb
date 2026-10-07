// Ground telegraphs: every boss skill first draws its path and impact point on the floor.
// One decal entity per shape (see nr_telegraph.py for the model); damage tests use the same numbers,
// so what is drawn is exactly what hits.
import { OW, DEG, dirOf, hdist, angDiff, particle, valid } from "./util.js";

export const TG_ID = "nrpg:telegraph";
export const SHAPE = { circle: 0, ring: 1, line: 2, cone: 3, dot: 4 };
export const COLORS = { red: 0, orange: 1, purple: 2, cyan: 3, gold: 4, green: 5 };
export const RING_RATIOS = [0.2, 0.35, 0.5, 0.65, 0.8];
export const CONE_ANGLES = [60, 90, 120, 180];
const live = new Set();

export function ringVariant(inner, outer) {
  const r = inner / Math.max(outer, 0.01);
  let best = 0;
  for (let i = 1; i < RING_RATIOS.length; i++) if (Math.abs(RING_RATIOS[i] - r) < Math.abs(RING_RATIOS[best] - r)) best = i;
  return best;
}
export function coneVariant(angle) {
  let best = 0;
  for (let i = 1; i < CONE_ANGLES.length; i++) if (Math.abs(CONE_ANGLES[i] - angle) < Math.abs(CONE_ANGLES[best] - angle)) best = i;
  return best;
}

// s = {shape, x, y, z, yaw, a, b, v, dur (s), col}
// returns the shape object (with .ent); the shape stays usable for hit tests even if the entity failed
export function draw(s, dim) {
  dim = dim || OW();
  s.yaw = s.yaw || 0;
  if (s.shape === "ring") { s.v = ringVariant(s.inner, s.a); s.inner = RING_RATIOS[s.v] * s.a; }
  if (s.shape === "cone") { s.v = coneVariant(s.angle); s.angle = CONE_ANGLES[s.v]; }
  try {
    const e = dim.spawnEntity(TG_ID, { x: s.x, y: s.y + 0.02, z: s.z });
    e.setProperty("nrpg:shape", SHAPE[s.shape]);
    e.setProperty("nrpg:a", Math.min(96, Math.max(0, s.a)));
    e.setProperty("nrpg:b", Math.min(32, Math.max(0, s.b || 0)));
    e.setProperty("nrpg:v", s.v || 0);
    e.setProperty("nrpg:dur", Math.min(30, Math.max(0.05, s.dur || 1)));
    e.setProperty("nrpg:col", COLORS[s.col] ?? 0);
    e.teleport({ x: s.x, y: s.y + 0.02, z: s.z }, { rotation: { x: 0, y: s.yaw } });
    s.ent = e;
    live.add(e);
  } catch (err) { s.ent = undefined; }
  s.born = Date.now();
  return s;
}
export function move(s, x, y, z, yaw) {
  s.x = x; s.y = y; s.z = z; if (yaw !== undefined) s.yaw = yaw;
  if (!valid(s.ent)) return;
  try { s.ent.teleport({ x, y: y + 0.02, z }, { rotation: { x: 0, y: s.yaw } }); } catch (e) { }
}
export function setLen(s, a) {
  s.a = a;
  if (valid(s.ent)) try { s.ent.setProperty("nrpg:a", Math.min(96, Math.max(0, a))); } catch (e) { }
}
export function recolor(s, col) {
  s.col = col;
  if (valid(s.ent)) try { s.ent.setProperty("nrpg:col", COLORS[col] ?? 0); } catch (e) { }
}
export function erase(s) {
  if (!s) return;
  if (s.ent) {
    live.delete(s.ent);
    try { if (s.ent.isValid) s.ent.remove(); } catch (e) { }
  }
  s.ent = undefined;
}
export function cleanupAll(dim) {
  for (const e of live) try { if (e.isValid) e.remove(); } catch (err) { }
  live.clear();
  try { for (const e of (dim || OW()).getEntities({ type: TG_ID })) e.remove(); } catch (err) { }
}

// ---------------------------------------------------------------- hit tests (horizontal, |dy| < 3)
const PR = 0.3;   // player half width
export function hits(s, l) {
  if (Math.abs(l.y - s.y) > 3.2) return false;
  const dx = l.x - s.x, dz = l.z - s.z;
  const d = Math.hypot(dx, dz);
  switch (s.shape) {
    case "circle": case "dot": return d <= s.a + PR;
    case "ring": return d >= s.inner - PR && d <= s.a + PR;
    case "line": {
      const f = dirOf(s.yaw);
      const t = dx * f.x + dz * f.z;
      const n = Math.abs(dx * f.z - dz * f.x);
      return t >= -PR && t <= s.a + PR && n <= s.b / 2 + PR;
    }
    case "cone": {
      if (d > s.a + PR) return false;
      if (d < 0.8) return true;
      const ang = Math.atan2(-dx, dz) / DEG;
      return angDiff(ang, s.yaw) <= s.angle / 2 + (PR / Math.max(d, 1)) / DEG;
    }
  }
  return false;
}

// ---------------------------------------------------------------- outline dust (a second, particle-only warning)
const DUST = "minecraft:redstone_wire_dust_particle";
export function outline(s, dim) {
  dim = dim || OW();
  const y = s.y + 0.15;
  const pts = [];
  const circ = (cx, cz, r) => {
    const n = Math.max(8, Math.min(48, Math.round(r * 2 * Math.PI / 1.6)));
    for (let i = 0; i < n; i++) { const t = i / n * 2 * Math.PI; pts.push([cx + Math.cos(t) * r, cz + Math.sin(t) * r]); }
  };
  if (s.shape === "circle" || s.shape === "dot") circ(s.x, s.z, s.a);
  else if (s.shape === "ring") { circ(s.x, s.z, s.a); circ(s.x, s.z, s.inner); }
  else if (s.shape === "line") {
    const f = dirOf(s.yaw), nx = f.z, nz = -f.x, w = s.b / 2;
    const n = Math.max(2, Math.min(40, Math.round(s.a / 1.6)));
    for (let i = 0; i <= n; i++) {
      const t = s.a * i / n;
      pts.push([s.x + f.x * t + nx * w, s.z + f.z * t + nz * w]);
      pts.push([s.x + f.x * t - nx * w, s.z + f.z * t - nz * w]);
    }
    const ex = s.x + f.x * s.a, ez = s.z + f.z * s.a;
    circ(ex, ez, Math.max(s.b * 0.8, 1));
  } else if (s.shape === "cone") {
    const n = Math.max(6, Math.round(s.a * s.angle * DEG / 1.6));
    for (let i = 0; i <= n; i++) {
      const a = (s.yaw - s.angle / 2 + s.angle * i / n);
      const f = dirOf(a);
      pts.push([s.x + f.x * s.a, s.z + f.z * s.a]);
    }
    for (const side of [-1, 1]) {
      const f = dirOf(s.yaw + side * s.angle / 2);
      for (let t = 1.5; t < s.a; t += 1.6) pts.push([s.x + f.x * t, s.z + f.z * t]);
    }
  }
  for (const [x, z] of pts) particle(dim, DUST, { x, y, z });
}

// beam / impact effects along a fired line
export function lineFx(s, id, dim, step = 0.7) {
  dim = dim || OW();
  const f = dirOf(s.yaw);
  for (let t = 0; t <= s.a; t += step) {
    particle(dim, id, { x: s.x + f.x * t, y: s.y + 1.0, z: s.z + f.z * t });
    if (s.b > 2.5) {
      const nx = f.z, nz = -f.x;
      particle(dim, id, { x: s.x + f.x * t + nx * s.b * 0.3, y: s.y + 0.6, z: s.z + f.z * t + nz * s.b * 0.3 });
      particle(dim, id, { x: s.x + f.x * t - nx * s.b * 0.3, y: s.y + 0.6, z: s.z + f.z * t - nz * s.b * 0.3 });
    }
  }
}
export function areaFx(s, id, dim, density = 0.35) {
  dim = dim || OW();
  const r = s.shape === "line" ? 0 : s.a;
  const n = Math.min(60, Math.max(4, Math.round(r * r * density)));
  for (let i = 0; i < n; i++) {
    const t = Math.random() * 2 * Math.PI, rr = Math.sqrt(Math.random()) * r;
    let x = s.x + Math.cos(t) * rr, z = s.z + Math.sin(t) * rr;
    if (s.shape === "ring" && rr < s.inner) continue;
    if (s.shape === "cone") {
      const a = s.yaw - s.angle / 2 + Math.random() * s.angle;
      const f = dirOf(a);
      x = s.x + f.x * rr; z = s.z + f.z * rr;
    }
    particle(dim, id, { x, y: s.y + 0.3 + Math.random() * 1.2, z });
  }
}
export function liveCount() { return live.size; }
