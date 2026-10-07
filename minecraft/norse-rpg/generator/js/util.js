// 아홉 세계의 항해 - shared helpers (@minecraft/server 2.0)
import { world, system, GameMode } from "@minecraft/server";

export const OW = () => world.getDimension("overworld");
export const now = () => system.currentTick;
export const DEG = Math.PI / 180;

// Minecraft yaw: 0 = +Z (south), 90 = -X (west), 180 = -Z, -90 = +X
export function yawTo(a, b) {
  return Math.atan2(-(b.x - a.x), b.z - a.z) / DEG;
}
export function dirOf(yaw) {
  return { x: -Math.sin(yaw * DEG), z: Math.cos(yaw * DEG) };
}
export function hdist(a, b) {
  return Math.hypot(a.x - b.x, a.z - b.z);
}
export function angDiff(a, b) {
  let d = ((a - b) % 360 + 540) % 360 - 180;
  return Math.abs(d);
}
export function inBox(l, b, m = 0) {
  return l.x >= b[0] - m && l.x < b[3] + 1 + m && l.y >= b[1] - m && l.y < b[4] + 1 + m && l.z >= b[2] - m && l.z < b[5] + 1 + m;
}
export function rand(a, b) {
  return a + Math.random() * (b - a);
}
export function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}
export function valid(e) {
  try { return !!e && e.isValid; } catch (err) { return false; }
}
export function isPlayer(e) {
  return !!e && e.typeId === "minecraft:player";
}
export function survivalish(p) {
  try {
    const m = String(p.getGameMode()).toLowerCase();
    return m !== "creative" && m !== "spectator";
  } catch (e) { return true; }
}
export function players() {
  try { return world.getPlayers(); } catch (e) { return []; }
}
export function cmd(c, dim) {
  try { return (dim || OW()).runCommand(c); } catch (e) { return undefined; }
}
export function store(key, def) {
  try {
    const v = world.getDynamicProperty(key);
    return v === undefined ? def : JSON.parse(v);
  } catch (e) { return def; }
}
export function save(key, v) {
  try { world.setDynamicProperty(key, JSON.stringify(v)); } catch (e) { }
}
export function pget(p, key, def) {
  try {
    const v = p.getDynamicProperty(key);
    return v === undefined ? def : JSON.parse(v);
  } catch (e) { return def; }
}
export function pset(p, key, v) {
  try { p.setDynamicProperty(key, JSON.stringify(v)); } catch (e) { }
}
export function title(p, t, sub, stay = 50) {
  try { p.onScreenDisplay.setTitle(t, { subtitle: sub || "", fadeInDuration: 8, stayDuration: stay, fadeOutDuration: 15 }); } catch (e) { }
}
export function bar(p, t) {
  try { p.onScreenDisplay.setActionBar(t); } catch (e) { }
}
export function sound(p, id, vol = 1, pitch = 1) {
  try { p.playSound(id, { volume: vol, pitch }); } catch (e) { }
}
export function soundAt(dim, id, loc, vol = 1, pitch = 1) {
  try { dim.playSound(id, loc, { volume: vol, pitch }); } catch (e) {
    for (const p of players()) if (hdist(p.location, loc) < 48) sound(p, id, vol, pitch);
  }
}
export function particle(dim, id, loc, vars) {
  try { dim.spawnParticle(id, loc, vars); } catch (e) { }
}
export async function showForm(p, form) {
  for (let i = 0; i < 20; i++) {
    let r;
    try { r = await form.show(p); } catch (e) { return { canceled: true }; }
    if (r.canceled && String(r.cancelationReason).toLowerCase() === "userbusy") {
      await new Promise((res) => system.runTimeout(res, 10));
      continue;
    }
    return r;
  }
  return { canceled: true };
}
export function tp(p, d, dim) {
  try {
    p.teleport({ x: d[0], y: d[1], z: d[2] }, { dimension: dim || OW(), rotation: { x: 0, y: d[3] ?? 0 } });
    return true;
  } catch (e) { return false; }
}
export function fmt(n) { return String(Math.floor(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
export { GameMode };
