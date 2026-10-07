// Boss skills. Every skill: draw the telegraph(s) -> wait `cast` ticks -> erase -> effects -> damage.
// Returns the number of ticks the caster stays busy.
import { MolangVariableMap } from "@minecraft/server";
import { DEG, yawTo, dirOf, hdist, rand, pick, valid, particle, soundAt } from "./util.js";
import { draw, move, setLen, recolor, erase, hits, outline, lineFx, areaFx } from "./telegraph.js";

// theme effects: [trail particle, impact particle, sound]
export const FX = {
  soul: ["minecraft:soul_particle", "minecraft:sculk_soul_particle", "mob.wither.shoot"],
  dust: ["minecraft:basic_smoke_particle", "minecraft:large_explosion", "dig.stone"],
  moon: ["minecraft:endrod", "minecraft:knockback_roar_particle", "mob.wolf.growl"],
  gold: ["minecraft:wax_particle", "minecraft:totem_particle", "random.anvil_land"],
  water: ["minecraft:basic_bubble_particle_manual", "minecraft:water_splash_particle_manual", "random.splash"],
  fire: ["minecraft:basic_flame_particle", "minecraft:lava_particle", "mob.blaze.shoot"],
  frost: ["minecraft:snowflake_particle", "minecraft:white_smoke_particle", "random.glass"],
  wind: ["minecraft:white_smoke_particle", "minecraft:wind_explosion_emitter", "wind_charge.burst"],
  poison: ["minecraft:villager_happy", "minecraft:dragon_breath_trail", "mob.enderdragon.flap"],
  time: ["minecraft:enchanting_table_particle", "minecraft:totem_particle", "block.bell.hit"],
  illusion: ["minecraft:basic_portal_particle", "minecraft:huge_explosion_emitter", "mob.evocation_illager.cast_spell"],
  blood: ["minecraft:redstone_ore_dust_particle", "minecraft:critical_hit_emitter", "mob.ravager.roar"],
  steam: ["minecraft:campfire_smoke_particle", "minecraft:white_smoke_particle", "random.fizz"],
  crit: ["minecraft:critical_hit_emitter", "minecraft:critical_hit_emitter", "mob.ravager.bite"],
};
const RGB = { red: [1, 0.2, 0.15], orange: [1, 0.55, 0.1], purple: [0.75, 0.35, 1], cyan: [0.25, 0.9, 1], gold: [1, 0.85, 0.25], green: [0.45, 1, 0.3] };

function glowVars(col) {
  const v = new MolangVariableMap();
  const c = RGB[col] || RGB.red;
  try { v.setColorRGB("variable.color", { red: c[0], green: c[1], blue: c[2] }); } catch (e) { }
  return v;
}
function fx(c, sk) { return FX[sk.fx] || FX.dust; }

// ---------------------------------------------------------------- helpers bound to a controller
function floorAt(c, x, z, yHint) {
  try {
    const hit = c.dim.getBlockFromRay({ x, y: yHint + 2.5, z }, { x: 0, y: -1, z: 0 }, { maxDistance: 10, includeLiquidBlocks: false, includePassableBlocks: false });
    if (hit) return hit.block.location.y + 1;
  } catch (e) { }
  return yHint;
}
function rayLen(c, o, yaw, max) {
  const f = dirOf(yaw);
  try {
    const hit = c.dim.getBlockFromRay({ x: o.x, y: o.y + 1.3, z: o.z }, { x: f.x, y: 0, z: f.z },
      { maxDistance: max, includeLiquidBlocks: false, includePassableBlocks: false });
    if (hit) {
      const p = { x: hit.block.location.x + hit.faceLocation.x, z: hit.block.location.z + hit.faceLocation.z };
      return Math.max(3, Math.min(max, hdist(o, p)));
    }
  } catch (e) { }
  return max;
}
function origin(c) {
  const l = c.ent.location;
  return { x: l.x, y: c.arena.y, z: l.z };
}
function shapeEnd(s) {
  const f = dirOf(s.yaw);
  return { x: s.x + f.x * s.a, z: s.z + f.z * s.a };
}
function keep(c, s) { c.tgs.push(s); return s; }
function drop(c, s) { erase(s); const i = c.tgs.indexOf(s); if (i >= 0) c.tgs.splice(i, 1); }
function strike(c, sk, s, from) {
  // apply the shape: particles, sound, damage to everything inside
  drop(c, s);
  const [trail, boom, snd] = fx(c, sk);
  const vars = glowVars(c.col);
  if (s.shape === "line") {
    lineFx(s, trail, c.dim);
    lineFx(s, "nrpg:beam", c.dim, 0.5);
    const e = shapeEnd(s);
    particle(c.dim, boom, { x: e.x, y: s.y + 0.5, z: e.z });
    particle(c.dim, "nrpg:burst", { x: e.x, y: s.y + 0.3, z: e.z }, vars);
  } else {
    areaFx(s, trail, c.dim);
    particle(c.dim, boom, { x: s.x, y: s.y + 0.5, z: s.z });
    particle(c.dim, "nrpg:burst", { x: s.x, y: s.y + 0.3, z: s.z }, vars);
  }
  soundAt(c.dim, snd, { x: s.x, y: s.y, z: s.z }, 1.2, 0.9 + Math.random() * 0.2);
  for (const t of c.targets()) {
    if (hits(s, t.location)) c.hit(t, sk.dmg, sk, from || s);
  }
}
function aimTarget(c) {
  const ts = c.targets();
  if (!ts.length) return undefined;
  const cur = c.focus && ts.find((t) => t.id === c.focus);
  if (cur && Math.random() < 0.7) return cur;
  const t = pick(ts);
  c.focus = t.id;
  return t;
}
function face(c, yaw) {
  try { c.ent.setRotation({ x: 0, y: yaw }); } catch (e) { }
}
function dur(ticks) { return ticks / 20; }

// ---------------------------------------------------------------- skills
const K = {};

K.beam = (c, sk, o0, yaw0, caster) => {
  const src = caster || c.ent;
  const t = aimTarget(c);
  if (!t && yaw0 === undefined) return 0;
  const track = sk.track || 0, lock = sk.lock || 10;
  const cast = Math.max(sk.cast, track + lock);
  const o = o0 || { x: src.location.x, y: c.arena.y, z: src.location.z };
  let yaw = yaw0 !== undefined ? yaw0 : yawTo(o, t.location);
  const line = keep(c, draw({ shape: "line", x: o.x, y: o.y, z: o.z, yaw, a: rayLen(c, o, yaw, sk.len), b: sk.width, dur: dur(cast), col: track ? "orange" : c.col }, c.dim));
  if (!caster) face(c, yaw);
  // the aim follows the target's position (the caster's gaze), then locks: path turns the boss colour
  for (let i = 1; i <= track; i++) {
    c.at(i, () => {
      if (!valid(t)) return;
      yaw = yawTo(o, t.location);
      move(line, o.x, o.y, o.z, yaw);
      setLen(line, rayLen(c, o, yaw, sk.len));
      if (!caster) face(c, yaw);
      else try { src.setRotation({ x: 0, y: yaw }); } catch (e) { }
    });
  }
  if (track) c.at(track + 1, () => recolor(line, c.col));
  for (let i = 0; i < cast; i += 8) c.at(i, () => outline(line, c.dim));
  c.at(cast, () => {
    if (caster && !valid(caster)) { drop(c, line); return; }
    strike(c, sk, line, o);
    if (sk.pull) for (const p of c.targets()) if (hits(line, p.location)) c.push(p, o, -1.2);
  });
  return cast + 6;
};

K.radial = (c, sk) => {
  const o = origin(c);
  const t = aimTarget(c);
  const base = t ? yawTo(o, t.location) : rand(0, 360);
  const wave = (offset, delay) => {
    c.at(delay, () => {
      for (let i = 0; i < sk.count; i++) {
        const yaw = base + offset + i * 360 / sk.count;
        const s = keep(c, draw({ shape: "line", x: o.x, y: o.y, z: o.z, yaw, a: rayLen(c, o, yaw, sk.len), b: sk.width, dur: dur(sk.cast), col: c.col }, c.dim));
        for (let k = 0; k < sk.cast; k += 8) c.at(k, () => outline(s, c.dim));
        c.at(sk.cast, () => strike(c, sk, s, o));
      }
    });
  };
  wave(0, 0);
  if (sk.spin) { wave(sk.spin, sk.cast); return sk.cast * 2 + 6; }
  return sk.cast + 6;
};

K.slam = (c, sk) => {
  const o = origin(c);
  const s = keep(c, draw({ shape: "circle", x: o.x, y: o.y, z: o.z, a: sk.radius, dur: dur(sk.cast), col: c.col }, c.dim));
  for (let k = 0; k < sk.cast; k += 8) c.at(k, () => outline(s, c.dim));
  c.at(sk.cast, () => {
    strike(c, sk, s, o);
    if (sk.knock) for (const p of c.targets()) if (hdist(p.location, o) < sk.radius + 1) c.push(p, o, sk.knock);
  });
  return sk.cast + 8;
};

K.ring = (c, sk) => {
  const o = origin(c);
  const s = keep(c, draw({ shape: "ring", x: o.x, y: o.y, z: o.z, a: sk.outer, inner: sk.inner, dur: dur(sk.cast), col: c.col }, c.dim));
  for (let k = 0; k < sk.cast; k += 8) c.at(k, () => outline(s, c.dim));
  c.at(sk.cast, () => {
    strike(c, sk, s, o);
    if (sk.knock) for (const p of c.targets()) if (hits(s, p.location)) c.push(p, o, sk.knock);
  });
  return sk.cast + 8;
};

K.cone = (c, sk) => {
  const times = sk.times || 1;
  const each = Math.max(sk.cast, (sk.track || 0) + (sk.lock || 0));
  let delay = 0;
  for (let n = 0; n < times; n++) {
    const castN = n === 0 ? each : Math.max(14, Math.round(each * 0.7));
    c.at(delay, () => {
      const o = origin(c);
      const t = aimTarget(c);
      let yaw = t ? yawTo(o, t.location) : (c.ent.getRotation().y);
      if (sk.back) yaw += 180;
      if (sk.side) yaw += Math.random() < 0.5 ? 90 : -90;
      const s = keep(c, draw({ shape: "cone", x: o.x, y: o.y, z: o.z, yaw, a: sk.radius, angle: sk.angle, dur: dur(castN), col: sk.track ? "orange" : c.col }, c.dim));
      if (!sk.back && !sk.side) face(c, yaw);
      const track = n === 0 ? (sk.track || 0) : 0;
      for (let i = 1; i <= track; i++) {
        c.at(i, () => {
          if (!valid(t)) return;
          const y2 = yawTo(o, t.location);
          move(s, o.x, o.y, o.z, y2);
          face(c, y2);
        });
      }
      if (sk.track) c.at(track + 1, () => recolor(s, c.col));
      for (let k = 0; k < castN; k += 8) c.at(k, () => outline(s, c.dim));
      c.at(castN, () => {
        strike(c, sk, s, o);
        if (sk.knock) for (const p of c.targets()) if (hits(s, p.location)) c.push(p, o, sk.knock);
      });
    });
    delay += castN + 4;
  }
  return delay + 4;
};

K.strike = (c, sk) => {
  const times = sk.times || 1;
  let delay = 0;
  for (let n = 0; n < times; n++) {
    const castN = n === 0 ? sk.cast : Math.max(16, Math.round(sk.cast * 0.75));
    c.at(delay, () => {
      for (const t of c.targets()) {
        const l = t.location;
        const y = floorAt(c, l.x, l.z, c.arena.y);
        const s = keep(c, draw({ shape: "circle", x: l.x, y, z: l.z, a: sk.radius, dur: dur(castN), col: c.col }, c.dim));
        for (let k = 0; k < castN; k += 8) c.at(k, () => outline(s, c.dim));
        c.at(castN, () => strike(c, sk, s));
      }
    });
    delay += castN + 2;
  }
  return Math.min(delay, sk.cast + 10);
};

K.rain = (c, sk) => {
  const A = c.arena;
  const pts = [];
  const ts = c.targets();
  for (let i = 0; i < sk.count; i++) {
    let p;
    for (let tries = 0; tries < 12; tries++) {
      if (i < ts.length * 2 && ts.length && Math.random() < 0.55) {
        const t = ts[i % ts.length].location;
        p = { x: t.x + rand(-2, 2), z: t.z + rand(-2, 2) };
      } else {
        const a = rand(0, 2 * Math.PI), r = Math.sqrt(Math.random()) * (A.r - 1.5);
        p = { x: A.x + Math.cos(a) * r, z: A.z + Math.sin(a) * r };
      }
      if (hdist(p, A) > A.r - 1) continue;
      if (pts.every((q) => hdist(q, p) > sk.radius * 1.3)) break;
    }
    pts.push(p);
  }
  pts.forEach((p, i) => {
    const castI = sk.cast + i * (sk.stagger || 0);
    const y = floorAt(c, p.x, p.z, A.y);
    const s = keep(c, draw({ shape: "circle", x: p.x, y, z: p.z, a: sk.radius, dur: dur(castI), col: c.col }, c.dim));
    for (let k = 0; k < castI; k += 8) c.at(k, () => outline(s, c.dim));
    c.at(castI - 6, () => particle(c.dim, fx(c, sk)[0], { x: p.x, y: y + 9, z: p.z }));
    c.at(castI, () => strike(c, sk, s));
  });
  return Math.min(sk.cast + 10, sk.cast + (sk.count - 1) * (sk.stagger || 0));
};

K.charge = (c, sk) => {
  const times = sk.times || 1;
  let delay = 0;
  for (let n = 0; n < times; n++) {
    const castN = n === 0 ? sk.cast : Math.max(16, Math.round(sk.cast * 0.7));
    c.at(delay, () => {
      const o = origin(c);
      const t = aimTarget(c);
      if (!t) return;
      const yaw = yawTo(o, t.location);
      const len = rayLen(c, o, yaw, sk.len) - 1;
      const s = keep(c, draw({ shape: "line", x: o.x, y: o.y, z: o.z, yaw, a: len, b: sk.width, dur: dur(castN), col: c.col }, c.dim));
      face(c, yaw);
      for (let k = 0; k < castN; k += 8) c.at(k, () => outline(s, c.dim));
      c.at(castN, () => {
        strike(c, sk, s, o);
        const f = dirOf(yaw);
        for (let k = 1; k <= 5; k++) {
          c.at(k, () => {
            const d = len * k / 5;
            try { c.ent.teleport({ x: o.x + f.x * d, y: o.y, z: o.z + f.z * d }, { rotation: { x: 0, y: yaw } }); } catch (e) { }
            particle(c.dim, fx(c, sk)[0], { x: o.x + f.x * d, y: o.y + 1, z: o.z + f.z * d });
          });
        }
        for (const p of c.targets()) if (hits(s, p.location)) c.push(p, o, 0.9);
      });
    });
    delay += castN + 8;
  }
  return delay + 4;
};

K.leap = (c, sk) => {
  const t = aimTarget(c);
  if (!t) return 0;
  const l = t.location;
  const y = floorAt(c, l.x, l.z, c.arena.y);
  const s = keep(c, draw({ shape: "circle", x: l.x, y, z: l.z, a: sk.radius, dur: dur(sk.cast), col: c.col }, c.dim));
  face(c, yawTo(c.ent.location, l));
  for (let k = 0; k < sk.cast; k += 8) c.at(k, () => outline(s, c.dim));
  c.at(sk.cast - 8, () => {
    try { c.ent.teleport({ x: c.ent.location.x, y: c.ent.location.y + 5, z: c.ent.location.z }); } catch (e) { }
    particle(c.dim, fx(c, sk)[1], c.ent.location);
  });
  c.at(sk.cast, () => {
    try { c.ent.teleport({ x: s.x, y: s.y, z: s.z }); } catch (e) { }
    strike(c, sk, s);
    for (const p of c.targets()) if (hits(s, p.location)) c.push(p, s, 0.8);
  });
  return sk.cast + 10;
};

K.pull = (c, sk) => {
  const o = origin(c);
  const big = keep(c, draw({ shape: "ring", x: o.x, y: o.y, z: o.z, a: sk.radius, inner: sk.core, dur: dur(sk.cast), col: "orange" }, c.dim));
  const core = keep(c, draw({ shape: "circle", x: o.x, y: o.y, z: o.z, a: sk.core, dur: dur(sk.cast), col: c.col }, c.dim));
  for (let k = 4; k < sk.cast - 4; k += 4) {
    c.at(k, () => {
      for (const p of c.targets()) {
        const d = hdist(p.location, o);
        if (d < sk.radius + 1 && d > 1) c.push(p, o, -0.35);
      }
      particle(c.dim, fx(c, sk)[0], { x: o.x + rand(-sk.radius, sk.radius), y: o.y + 0.5, z: o.z + rand(-sk.radius, sk.radius) });
    });
  }
  for (let k = 0; k < sk.cast; k += 8) c.at(k, () => { outline(big, c.dim); outline(core, c.dim); });
  c.at(sk.cast, () => { drop(c, big); strike(c, sk, core, o); });
  return sk.cast + 8;
};

K.wave = (c, sk) => {
  const o = origin(c);
  for (let i = 0; i < sk.count; i++) {
    const castI = sk.cast + i * sk.delay;
    const inner = i * sk.step, outer = i * sk.step + sk.width;
    const s = keep(c, draw(inner < 0.5 ? { shape: "circle", x: o.x, y: o.y, z: o.z, a: outer, dur: dur(castI), col: c.col }
      : { shape: "ring", x: o.x, y: o.y, z: o.z, a: outer, inner, dur: dur(castI), col: c.col }, c.dim));
    for (let k = 0; k < castI; k += 8) c.at(k, () => outline(s, c.dim));
    c.at(castI, () => strike(c, sk, s, o));
  }
  return sk.cast + 8;
};

K.sweep = (c, sk) => {
  const A = c.arena;
  const t = aimTarget(c);
  const across = t ? yawTo(c.ent.location, t.location) + 90 : rand(0, 360);
  const f = dirOf(across), nrm = { x: f.z, z: -f.x };
  const L = A.r * 2;
  const total = (sk.count - 1) * sk.spacing;
  for (let i = 0; i < sk.count; i++) {
    const off = -total / 2 + i * sk.spacing + rand(-1, 1);
    const sx = A.x - f.x * A.r + nrm.x * off, sz = A.z - f.z * A.r + nrm.z * off;
    const castI = sk.cast + i * 6;
    const s = keep(c, draw({ shape: "line", x: sx, y: A.y, z: sz, yaw: across, a: L, b: sk.width, dur: dur(castI), col: c.col }, c.dim));
    for (let k = 0; k < castI; k += 8) c.at(k, () => outline(s, c.dim));
    c.at(castI, () => {
      strike(c, sk, s);
      if (sk.knock) for (const p of c.targets()) if (hits(s, p.location)) c.push(p, { x: p.location.x - f.x, z: p.location.z - f.z }, sk.knock);
    });
  }
  return sk.cast + 10;
};

K.summon = (c, sk) => {
  const o = origin(c);
  const pts = [];
  for (let i = 0; i < sk.count; i++) {
    const a = (i / sk.count) * 2 * Math.PI + rand(-0.3, 0.3), r = rand(4, Math.min(8, c.arena.r - 2));
    pts.push({ x: o.x + Math.cos(a) * r, z: o.z + Math.sin(a) * r });
  }
  for (const p of pts) {
    const s = keep(c, draw({ shape: "dot", x: p.x, y: o.y, z: p.z, a: 1.2, dur: dur(sk.cast), col: c.col }, c.dim));
    c.at(sk.cast, () => {
      drop(c, s);
      c.minion(sk.mob, { x: p.x, y: o.y, z: p.z });
      particle(c.dim, "minecraft:huge_explosion_emitter", { x: p.x, y: o.y + 0.5, z: p.z });
    });
  }
  return sk.cast + 6;
};

K.clone = (c, sk) => {
  const A = c.arena;
  let longest = 0;
  for (let i = 0; i < sk.count; i++) {
    const a = (i / sk.count) * 2 * Math.PI + rand(-0.4, 0.4), r = A.r - rand(2, 4);
    const p = { x: A.x + Math.cos(a) * r, y: A.y, z: A.z + Math.sin(a) * r };
    const ill = c.illusion(p);
    if (!ill) continue;
    const used = K.beam(c, sk, p, undefined, ill);
    longest = Math.max(longest, used);
    c.at(used + 2, () => { try { if (ill.isValid) ill.remove(); } catch (e) { } });
  }
  return Math.min(longest, sk.cast + 10);
};

export const SKILLS = K;
