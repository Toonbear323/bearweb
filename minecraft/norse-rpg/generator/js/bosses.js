// Boss arenas and boss brains. One controller per arena; skills come from skills.js.
import { world, system, EntityDamageCause, ItemStack } from "@minecraft/server";
import { OW, now, hdist, inBox, valid, isPlayer, survivalish, players, title, bar, sound, soundAt, particle, pget, pset, rand, yawTo } from "./util.js";
import { SKILLS } from "./skills.js";
import { erase, cleanupAll } from "./telegraph.js";
import { spawnMob, removeTagged } from "./mobs.js";
import { BOSSES, ARENAS, DUNGEONS } from "./data.js";

export const TEST = { on: false, log: [] };
const CTL = new Map();               // arena id -> controller
const ARENA_BY_ID = {};
for (const a of ARENAS) ARENA_BY_ID[a.id] = a;
const SKIN = {};                      // boss id -> illusion skin index
Object.keys(BOSSES).forEach((k, i) => { SKIN[k] = i; });

function log(msg) {
  console.warn("[nrpg] " + msg);
  if (TEST.on) TEST.log.push(msg);
}

class Ctl {
  constructor(arena, def, id) {
    this.arena = arena;
    this.def = def;
    this.bossId = id;
    this.dim = OW();
    this.col = def.color;
    this.events = [];
    this.tgs = [];
    this.ent = undefined;
    this.state = "idle";       // idle -> intro -> fight -> cleared
    this.stateAt = now();
    this.phase = 0;
    this.busyUntil = 0;
    this.cds = {};
    this.focus = undefined;
    this.lastSeen = now();
    this.forced = [];          // test mode: skills to cast in order
    this.hits = 0;
  }
  at(delay, fn) { this.events.push({ t: now() + Math.max(0, Math.round(delay)), fn }); }
  inArena(l, pad = 2) {
    const A = this.arena;
    return Math.hypot(l.x - A.x, l.z - A.z) <= A.r + pad && l.y > A.y - 4 && l.y < A.y + 14;
  }
  targets() {
    const out = [];
    for (const p of players()) {
      if (!survivalish(p)) continue;
      try { if (p.getComponent("minecraft:health").currentValue <= 0) continue; } catch (e) { }
      if (this.inArena(p.location)) out.push(p);
    }
    if (TEST.on) {
      try {
        for (const e of this.dim.getEntities({ type: "nrpg:dummy", location: { x: this.arena.x, y: this.arena.y, z: this.arena.z }, maxDistance: this.arena.r + 4 })) out.push(e);
      } catch (e) { }
    }
    return out;
  }
  hit(t, dmg, sk, from) {
    if (!valid(t) || !dmg) return;
    try {
      t.applyDamage(dmg, { cause: EntityDamageCause.entityAttack, damagingEntity: valid(this.ent) ? this.ent : undefined });
      this.hits++;
    } catch (e) {
      try { t.applyDamage(dmg); this.hits++; } catch (e2) { }
    }
    const eff = sk.effect;
    if (eff === "fire") { try { t.setOnFire(4, true); } catch (e) { } }
    else if (eff) {
      const amp = eff === "slowness" ? 1 : 0;
      const time = eff === "blindness" ? 60 : eff === "wither" ? 80 : 100;
      try { t.addEffect(eff, time, { amplifier: amp, showParticles: true }); } catch (e) { }
    }
  }
  push(p, from, strength) {
    const dx = p.location.x - from.x, dz = p.location.z - from.z;
    const d = Math.max(0.5, Math.hypot(dx, dz));
    try { p.applyKnockback({ x: dx / d * strength * 1.6, z: dz / d * strength * 1.6 }, strength > 0 ? 0.35 : 0.1); } catch (e) { }
  }
  minion(mobKey, loc) {
    const mine = this.minionCount();
    if (mine >= 8) return;
    spawnMob(mobKey, loc, ["nrpg_minion", "nrpg_minion_" + this.arena.id], this.dim);
  }
  minionCount() {
    try { return this.dim.getEntities({ tags: ["nrpg_minion_" + this.arena.id] }).length; } catch (e) { return 0; }
  }
  illusion(p) {
    try {
      const e = this.dim.spawnEntity("nrpg:illusion", p);
      e.setProperty("nrpg:skin", SKIN[this.bossId] || 0);
      e.addTag("nrpg_illusion_" + this.arena.id);
      e.nameTag = "§7" + this.def.ko + "의 환영";
      return e;
    } catch (e) { return undefined; }
  }
  clear() {
    for (const s of this.tgs) erase(s);
    this.tgs = [];
    this.events = [];
    removeTagged("nrpg_illusion_" + this.arena.id, this.dim);
  }
}

// ---------------------------------------------------------------- gates
function setGates(list, type, dim) {
  let ok = 0;
  for (const g of list || []) {
    try {
      const b = (dim || OW()).getBlock({ x: g[0], y: g[1], z: g[2] });
      if (b) { b.setType(type); ok++; }
    } catch (e) { }
  }
  return ok;
}
function closeEntry(c) { setGates(c.arena.entry, c.arena.gateBlock, c.dim); }
function openEntry(c) { setGates(c.arena.entry, "minecraft:air", c.dim); }
function closeExit(c) { setGates(c.arena.exit, c.arena.gateBlock, c.dim); }
function openExit(c) { setGates(c.arena.exit, "minecraft:air", c.dim); }

// ---------------------------------------------------------------- spawning / phases
function spawnBoss(c) {
  const A = c.arena;
  let e;
  try { e = c.dim.spawnEntity("nrpg:" + c.bossId, { x: A.x, y: A.y, z: A.z }); } catch (err) { log("spawn failed " + c.bossId + " " + err); return false; }
  c.ent = e;
  try { e.addTag("nrpg_boss"); e.addTag("nrpg_arena_" + A.id); } catch (err) { }
  try { e.nameTag = c.def.ko; } catch (err) { }
  const n = Math.max(1, c.targets().filter(isPlayer).length);
  if (n >= 2) { try { e.addEffect("resistance", 20000000, { amplifier: Math.min(2, Math.floor((n - 1) / 1.5)), showParticles: false }); } catch (err) { } }
  c.phase = 0;
  c.busyUntil = now() + 40;
  c.cds = {};
  c.hits = 0;
  c.state = "fight";
  c.stateAt = now();
  c.lastSeen = now();
  soundAt(c.dim, "mob.enderdragon.growl", A, 2, 0.8);
  particle(c.dim, "minecraft:huge_explosion_emitter", { x: A.x, y: A.y + 1, z: A.z });
  log("spawned " + c.bossId + " at arena " + A.id);
  return true;
}
function healthRatio(c) {
  try {
    const h = c.ent.getComponent("minecraft:health");
    return h.currentValue / h.effectiveMax;
  } catch (e) { return 1; }
}
function phaseCheck(c) {
  const r = healthRatio(c);
  const ph = c.def.phases;
  let p = 0;
  for (let i = 0; i < ph.length; i++) if (r <= ph[i][0] + 1e-6) p = i;
  if (p > c.phase) {
    c.phase = p;
    for (const t of c.targets()) if (isPlayer(t)) {
      title(t, "§c" + c.def.ko, "§f" + (p + 1) + "단계 — 더 강한 기술을 씁니다!", 40);
      sound(t, "mob.wither.spawn", 0.5, 1.2);
    }
    try { c.ent.setProperty("nrpg:phase", p); } catch (e) { }
    c.busyUntil = Math.max(c.busyUntil, now() + 20);
  }
}
function chooseSkill(c) {
  if (c.forced.length) return c.forced.shift();
  const pool = c.def.phases[c.phase][1];
  const ready = pool.filter((k) => (c.cds[k] || 0) <= now());
  if (!ready.length) return undefined;
  if (c.minionCount() >= 6) {
    const nos = ready.filter((k) => c.def.skills[k].kind !== "summon");
    if (nos.length) return nos[Math.floor(Math.random() * nos.length)];
  }
  return ready[Math.floor(Math.random() * ready.length)];
}
function cast(c, key) {
  const sk = c.def.skills[key];
  const fn = SKILLS[sk.kind];
  if (!fn) return;
  try { c.ent.triggerEvent("nrpg:cast_start"); } catch (e) { }
  try { c.ent.setProperty("nrpg:anim", ANIM[sk.kind] || 1); } catch (e) { }
  for (const t of c.targets()) if (isPlayer(t)) bar(t, "§c" + c.def.ko + " §f— §e" + sk.name);
  let busy = 0;
  try { busy = fn(c, sk) || 0; } catch (e) { log("skill error " + key + ": " + e); busy = 20; }
  const tgCount = c.tgs.length;
  c.busyUntil = now() + busy + Math.max(18, 46 - c.phase * 12);
  c.cds[key] = now() + (sk.cd || 60) + busy;
  c.at(busy, () => {
    try { c.ent.triggerEvent("nrpg:cast_end"); } catch (e) { }
    try { c.ent.setProperty("nrpg:anim", 0); } catch (e) { }
  });
  if (TEST.on) log("cast " + c.bossId + "." + key + " (" + sk.kind + ") telegraphs=" + tgCount + " busy=" + busy);
}
const ANIM = { beam: 3, radial: 3, slam: 2, ring: 4, cone: 5, strike: 1, rain: 1, charge: 6, leap: 7, pull: 4, wave: 2, sweep: 5, summon: 8, clone: 1 };

// ---------------------------------------------------------------- rewards
function give(p, id, n) {
  try {
    const inv = p.getComponent("minecraft:inventory").container;
    const left = inv.addItem(new ItemStack(id, n));
    if (left) p.dimension.spawnItem(left, p.location);
  } catch (e) { }
}
function onDefeat(c) {
  const A = c.arena;
  const d = DUNGEONS[A.dungeon];
  const ps = players().filter((p) => c.inArena(p.location, 8));
  c.clear();
  removeTagged("nrpg_minion_" + A.id, c.dim);
  c.state = "cleared";
  c.stateAt = now();
  c.ent = undefined;
  openEntry(c);
  openExit(c);
  const tierMul = d ? ({ beginner: 1, mid: 2, high: 3 })[d.tier] : 1;
  for (const p of ps) {
    if (A.role === "final") {
      title(p, "§6§l던전 클리어!", "§f" + c.def.ko + " 처치 — " + (d ? d.ko : ""), 80);
      sound(p, "ui.toast.challenge_complete", 1, 1);
      const cl = pget(p, "nrpg:cleared", []);
      if (d && !cl.includes(d.id)) { cl.push(d.id); pset(p, "nrpg:cleared", cl); }
      give(p, "nrpg:rune_shard", 4 * tierMul + Math.floor(rand(0, 3)));
      give(p, "nrpg:rune_core", tierMul);
      if (tierMul === 3) give(p, "nrpg:ward_scroll", 1);
      p.sendMessage("§6[보상] §f룬 조각과 룬 정수를 받았습니다. 출구의 귀환선을 타면 항구로 돌아갑니다.");
    } else {
      title(p, "§e§l중간 보스 처치", "§f" + c.def.ko + " — 다음 구역 문이 열렸습니다", 60);
      sound(p, "random.levelup", 1, 0.8);
      give(p, "nrpg:rune_shard", 2 * tierMul + Math.floor(rand(0, 2)));
      if (tierMul >= 2) give(p, "nrpg:rune_core", 1);
    }
    try { p.addLevels(A.role === "final" ? 5 * tierMul : 2 * tierMul); } catch (e) { }
  }
  world.sendMessage("§6[아홉 세계] §f" + ps.map((p) => p.name).join(", ") + " 님이 §c" + c.def.ko + "§f을(를) 쓰러뜨렸습니다!");
  log("defeated " + c.bossId + " hits=" + c.hits);
}

// ---------------------------------------------------------------- loops
function tickBoss(c) {
  const t = now();
  // run due events (in order)
  if (c.events.length) {
    const due = c.events.filter((e) => e.t <= t);
    if (due.length) {
      c.events = c.events.filter((e) => e.t > t);
      due.sort((a, b) => a.t - b.t);
      for (const e of due) { try { e.fn(); } catch (err) { log("event error " + err); } }
    }
  }
  if (c.state !== "fight" || !valid(c.ent)) return;
  const l = c.ent.location;
  if (!c.inArena(l, 3)) {
    try { c.ent.teleport({ x: c.arena.x, y: c.arena.y, z: c.arena.z }); } catch (e) { }
  }
  phaseCheck(c);
  if (t < c.busyUntil) return;
  if (!c.targets().length) return;
  const key = chooseSkill(c);
  if (key) cast(c, key);
  else c.busyUntil = t + 10;
}

function arenaTick() {
  const t = now();
  for (const A of ARENAS) {
    let c = CTL.get(A.id);
    if (!c) { c = new Ctl(A, BOSSES[A.boss], A.boss); CTL.set(A.id, c); }
    const present = players().filter((p) => survivalish(p) && c.inArena(p.location, 4));
    if (present.length || (TEST.on && c.state === "fight" && c.targets().length)) c.lastSeen = t;
    if (c.state === "idle") {
      if (players().some((p) => survivalish(p) && inBox(p.location, A.trigger))) {
        c.state = "intro";
        c.stateAt = t;
        closeEntry(c);
        for (const p of players().filter((q) => c.inArena(q.location, 10))) {
          title(p, "§4§l" + c.def.ko, "§7" + c.def.title, 60);
          sound(p, "mob.warden.emerge", 1, 0.9);
        }
        c.at(50, () => { if (c.state === "intro") spawnBoss(c); });
      }
    } else if (c.state === "fight") {
      if (!valid(c.ent)) {
        // unloaded or removed without dying: wait for players; if nobody is around, reset
        if (t - c.lastSeen > 200) resetArena(c);
      } else if (t - c.lastSeen > 400) {
        resetArena(c);
      }
    } else if (c.state === "intro") {
      if (t - c.stateAt > 200 && !valid(c.ent)) resetArena(c);
    } else if (c.state === "cleared") {
      if (t - c.stateAt > (A.respawn || 6000) && t - c.lastSeen > 600) resetArena(c);
    }
  }
}
export function resetArena(c) {
  c.clear();
  if (valid(c.ent)) try { c.ent.remove(); } catch (e) { }
  c.ent = undefined;
  removeTagged("nrpg_minion_" + c.arena.id, c.dim);
  openEntry(c);
  closeExit(c);
  c.state = "idle";
  c.stateAt = now();
  c.forced = [];
}

world.afterEvents.entityDie.subscribe((ev) => {
  const e = ev.deadEntity;
  let tags = [];
  try { tags = e.getTags(); } catch (err) { return; }
  if (!tags.includes("nrpg_boss")) return;
  const at = tags.find((s) => s.startsWith("nrpg_arena_"));
  if (!at) return;
  const c = CTL.get(at.slice(11));
  if (c && c.state === "fight") onDefeat(c);
});

export function initBosses() {
  cleanupAll();
  for (const A of ARENAS) {
    const c = new Ctl(A, BOSSES[A.boss], A.boss);
    CTL.set(A.id, c);
  }
  // leftovers from a crash: no boss may exist without its controller
  try { for (const e of OW().getEntities({ tags: ["nrpg_boss"] })) e.remove(); } catch (e) { }
  removeTagged("nrpg_minion");
  system.runInterval(() => { for (const c of CTL.values()) tickBoss(c); }, 1);
  system.runInterval(arenaTick, 10);
  system.runInterval(() => {
    // gates: an arena that is idle keeps its exit gate shut (chunks may have been unloaded when it reset)
    for (const c of CTL.values()) {
      if (c.state === "idle" && players().some((p) => hdist(p.location, c.arena) < 40)) closeExit(c);
    }
  }, 100);
}

// ---------------------------------------------------------------- admin / test
export function forceBoss(arenaId, skills) {
  const c = CTL.get(arenaId);
  if (!c) return "no arena " + arenaId;
  if (c.state !== "fight" || !valid(c.ent)) {
    resetArena(c);
    closeEntry(c);
    if (!spawnBoss(c)) return "spawn failed";
  }
  if (skills) c.forced = skills.slice();
  return "ok " + c.bossId;
}
export function bossStatus() {
  const out = [];
  for (const [id, c] of CTL) {
    let hp = "-";
    if (valid(c.ent)) try { const h = c.ent.getComponent("minecraft:health"); hp = Math.round(h.currentValue) + "/" + h.effectiveMax; } catch (e) { }
    out.push(id + ":" + c.state + ":" + hp + ":ph" + c.phase + ":hits" + c.hits + ":tg" + c.tgs.length + ":min" + c.minionCount());
  }
  return out;
}
export function arenaOf(id) { return CTL.get(id); }
export function allCtl() { return CTL; }
