
// =====================================================================
//  §b§l시공§f§l의 분침 (vh:chrono_blade) — 보스 「시간의 여신」 을 쓰러뜨리면 얻는 검 · 모델 tools/gen_chrono_blade.py
//  칼날 자체가 찢어진 시공간 (여신의 분침 검을 잇는 브레게 바늘 모양 · 달 고리 속 블랙홀)
//  효과는 여신의 것을 그대로 씀: 검기 vh:tgd_slash · 차원 찢김 vh:tgd_tear · 큰 시계 vh:tgd_bigclock · 파티클 vh:tgd_* · 소리 vh.tgd.*
//  우클릭 탭            → 「분침 베기」   검기가 앞으로 날아가며 벰 (세 번째마다 엇갈린 두 줄) · 맞은 적에 「시차 표식」 (최대 3)
//  우클릭 누르고 있기   → 「시간 압축」   0.5초마다 한 시각씩 (최대 열두 시) · 둘레의 적이 느려짐
//                놓으면 → 「자정 일섬」   바라보는 쪽으로 순간 돌진하며 길 위의 적을 모두 벰 → 0.7초 뒤 늦게 도착한 시간이 터짐 (시각 · 표식만큼)
//  웅크리고 우클릭      → 「찢어진 자정」 칼을 하늘로 들면 발밑에 큰 시계 · 둘레 14칸의 시간이 멈춤 → 멈춘 세계를 일곱 번 가름 (피해는 쌓임)
//                                         → 내리그으면 시간이 다시 흐르며 쌓인 피해가 한꺼번에 · 적마다 차원이 찢김
//  패시브              → 「시차의 잔상」 칼로 때린 적을 1.2초 뒤 시간의 잔상이 한 번 더 벰 · 들고 있으면 둘레를 밝힘 (빛 블록 15)
// =====================================================================
const CRB = {
  ID: "vh:chrono_blade", HOLD_TICKS: 7,
  TAP_CD: 0.55, WAVE_DMG: 8, WAVE_LEN: 12, WAVE_SPD: 1.1, WAVE_W: 2.8, MARK_MAX: 3,
  ECHO_DELAY: 24, ECHO_DMG: 5, ECHO_GAP: 20,
  HOUR_T: 10, HOURS: 12, SLOW_R: 8, IAI_CD: 6, DASH0: 4, DASH_PER: 0.75, CUT_W: 1.9, CUT_DMG: 6, HOUR_DMG: 2.2, MARK_DMG: 3, BURST_T: 14,
  SEV_CD: 35, SEV_R: 14, SEV_STOP: 6, SEV_CUTS: [10, 16, 22, 28, 34, 40, 46], SEV_FINAL: 52, SEV_CUT_DMG: 7, SEV_K: 1.5, SEV_BASE: 6,
};
const CRB_BLUE = { cr: 0.4, cg: 0.72, cb: 1 }, CRB_GOLD = { cr: 1, cg: 0.82, cb: 0.42 }, CRB_WHITE = { cr: 0.9, cg: 0.96, cb: 1 }, CRB_VIOL = { cr: 0.62, cg: 0.42, cb: 1 };
const crbPress = new Map(), crbHold = new Map(), crbSwing = new Map(), crbMarks = new Map(), crbEchoT = new Map();
const crbWaves = [], crbSevers = new Map();
const CRB_HINT = "§b탭 §f분침 베기 §7· §b꾹 §f자정 일섬 §7· §b웅크리고 §f찢어진 자정";

function crbUp(a, h) { return V.add(a, { x: 0, y: h, z: 0 }); }
function crbFlat(f) { const d = V.norm({ x: f.x, y: 0, z: f.z }); return d.x || d.z ? d : { x: 0, y: 0, z: 1 }; }
function crbMark(e, n = 1) {
  const m = crbMarks.get(e.id) ?? { n: 0, t: 0 };
  m.n = Math.min(CRB.MARK_MAX, m.n + n); m.t = now();
  crbMarks.set(e.id, m);
  const top = crbUp(e.location, height(e) + 0.35);
  for (let k = 0; k < m.n; k++) fx(e.dimension, "vh:tgd_glow", V.add(top, { x: (k - (m.n - 1) / 2) * 0.3, y: 0, z: 0 }), { ...CRB_GOLD, size: 0.35, life: 0.5 });
}
function crbTakeMarks(e) { const m = crbMarks.get(e.id); crbMarks.delete(e.id); return m && now() - m.t < 200 ? m.n : 0; }
function crbSlashFx(dim, at, f, roll, dir, sc = 10, life = 4) {
  return tgdSpawn(dim, "vh:tgd_slash", at, { "vh:y": tgdYaw(f), "vh:r": Math.max(-90, Math.min(90, Math.round(roll))), "vh:d": dir, "vh:s": Math.max(1, Math.min(40, Math.round(sc))), "vh:t": Math.max(1, Math.min(100, life)) }, Math.max(life, 12) + 2);
}

// ---------------------------------------------------------------- 들고 있으면 둘레를 밝힘 (빛의 검과 같은 방식 · 열쇠만 따로)
const CRB_LIGHT = "minecraft:light_block_15", CRB_LIGHT_KEY = "vh_crb_lights", crbLights = new Map();
function crbLightSave() { try { world.setDynamicProperty(CRB_LIGHT_KEY, JSON.stringify([...crbLights.values()].map((L) => [L.dim.id, L.x, L.y, L.z]))); } catch { } }
function crbLightOff(id) {
  const L = crbLights.get(id);
  if (!L) return;
  crbLights.delete(id);
  try { const b = L.dim.getBlock(L); if (b?.typeId === CRB_LIGHT) b.setType("minecraft:air"); } catch { }
  crbLightSave();
}
function crbLightAt(p) {
  const h = p.getHeadLocation(), at = { x: Math.floor(h.x), y: Math.floor(h.y), z: Math.floor(h.z) };
  const L = crbLights.get(p.id);
  if (L && L.x === at.x && L.y === at.y && L.z === at.z && L.dim === p.dimension) return;
  crbLightOff(p.id);
  try { const b = p.dimension.getBlock(at); if (b && b.typeId === "minecraft:air") { b.setType(CRB_LIGHT); crbLights.set(p.id, { dim: p.dimension, ...at }); crbLightSave(); } } catch { }
}
system.run(() => {
  try {
    const raw = world.getDynamicProperty(CRB_LIGHT_KEY);
    if (typeof raw !== "string") return;
    for (const [d, x, y, z] of JSON.parse(raw)) { try { const b = world.getDimension(d).getBlock({ x, y, z }); if (b?.typeId === CRB_LIGHT) b.setType("minecraft:air"); } catch { } }
    world.setDynamicProperty(CRB_LIGHT_KEY, "[]");
  } catch { }
});

// ---------------------------------------------------------------- 탭 「분침 베기」
function crbTap(p) {
  if (crbSevers.has(p.id)) return;
  if (onCooldown(p, "crb_tap", "§b분침 베기")) return;
  setCd(p, "crb_tap", CRB.TAP_CD);
  const n = (crbSwing.get(p.id) ?? 0) + 1;
  crbSwing.set(p.id, n);
  anim(p, `animation.vh.chrono_blade.${n % 2 ? "slash_a" : "slash_b"}`, 0.1);
  const { f } = basisOf(p);
  const start = V.add(crbUp(p.location, 1.15), V.mul(crbFlat(f), 1.2));
  const dir = V.norm({ x: f.x, y: Math.max(-0.5, Math.min(0.5, f.y)), z: f.z });
  const rolls = n % 3 === 0 ? [[-40, 1], [40, 0]] : [[n % 2 ? -32 : 8, n % 2 ? 1 : 0]];
  for (const [roll, d] of rolls) crbWave(p, start, dir, roll, d, CRB.WAVE_DMG);
  fx(p.dimension, "vh:tgd_spark", start, { ...CRB_WHITE, n: 8, spd: 3, life: 0.3 });
  snd(p.dimension, "vh.tgd.slash", p.location, 1, 1.05 + Math.random() * 0.15);
  if (n % 3 === 0) snd(p.dimension, "vh.tgd.chime", p.location, 0.7, 1.5);
}
function crbWave(p, at, dir, roll, d, dmg) {
  const life = Math.ceil(CRB.WAVE_LEN / CRB.WAVE_SPD) + 2;
  const e = crbSlashFx(p.dimension, at, dir, roll, d, 8, life + 4);
  crbWaves.push({ p, dim: p.dimension, pos: { ...at }, dir, e, t: 0, life, hit: new Set(), dmg });
}
function tickCrbWaves() {
  for (let i = crbWaves.length - 1; i >= 0; i--) {
    const W = crbWaves[i];
    W.t++;
    const prev = W.pos;
    W.pos = V.add(W.pos, V.mul(W.dir, CRB.WAVE_SPD));
    let blocked = false;
    try { const b = W.dim.getBlock(W.pos); if (b && !b.isAir && !b.isLiquid && b.typeId !== CRB_LIGHT && !b.typeId.includes("grass") && !b.typeId.includes("flower")) blocked = true; } catch { }
    if (W.e && valid(W.e)) { try { W.e.teleport(W.pos); } catch { } }
    if (W.t % 2 === 0) fx(W.dim, "vh:tgd_glow", W.pos, { ...CRB_BLUE, size: 1.4, life: 0.25 });
    if (valid(W.p)) {
      for (const e of enemiesNear(W.p, W.pos, CRB.WAVE_W + 2)) {
        if (W.hit.has(e.id)) continue;
        if (tgdSeg3(center(e), prev, W.pos) > CRB.WAVE_W / 2 + 0.4) continue;
        W.hit.add(e.id);
        hurt(e, W.dmg, W.p);
        knock(e, W.p.location, 0.35, 0.15);
        crbMark(e);
        fx(W.dim, "vh:tgd_spark", center(e), { ...CRB_GOLD, n: 8, spd: 3, life: 0.4 });
        snd(W.dim, "vh.tgd.impact", e.location, 0.6, 1.4);
      }
    }
    if (W.t >= W.life || blocked) {
      if (blocked) fx(W.dim, "vh:tgd_spark", prev, { ...CRB_WHITE, n: 10, spd: 3, life: 0.4 });
      try { if (W.e && valid(W.e)) W.e.remove(); } catch { }
      crbWaves.splice(i, 1);
    }
  }
}

// ---------------------------------------------------------------- 패시브 「시차의 잔상」
world.afterEvents.entityHitEntity.subscribe((ev) => {
  try {
    const p = ev.damagingEntity, e = ev.hitEntity;
    if (p?.typeId !== "minecraft:player" || held(p) !== CRB.ID || !enemy(p, e)) return;
    const key = `${p.id}:${e.id}`, t = now();
    if ((crbEchoT.get(key) ?? -99) > t - CRB.ECHO_GAP) return;
    crbEchoT.set(key, t);
    crbMark(e);
    fx(p.dimension, "vh:tgd_warp", center(e), { ...CRB_BLUE, n: 6, r: 1.2, life: 0.4 });
    system.runTimeout(() => {
      if (!valid(e) || !valid(p)) return;
      const f = crbFlat(V.sub(e.location, p.location));
      crbSlashFx(e.dimension, center(e), f, Math.round(Math.random() * 120 - 60), Math.random() < 0.5 ? 1 : 0, 5, 4);
      hurt(e, CRB.ECHO_DMG, p);
      fx(e.dimension, "vh:tgd_spark", center(e), { ...CRB_BLUE, n: 10, spd: 3, life: 0.4 });
      snd(e.dimension, "vh.tgd.slash", e.location, 0.6, 1.6);
    }, CRB.ECHO_DELAY);
  } catch { }
});

// ---------------------------------------------------------------- 꾹 「시간 압축」 → 놓으면 「자정 일섬」
function crbHoldStart(p) {
  if (crbSevers.has(p.id)) return;
  const left = cdLeft(p, "crb_iai");
  crbHold.set(p.id, { t0: now(), hours: 0, blocked: left > 0 });
  if (left > 0) { bar(p, `§b자정 일섬 §7재사용 대기중... §f${left.toFixed(1)}초`); return; }
  try { p.playAnimation("animation.vh.chrono_blade.draw", { blendOutTime: 0.2, controller: "vh_crb", stopExpression: "!q.is_item_name_any('slot.weapon.mainhand', 0, 'vh:chrono_blade') || !q.is_using_item" }); } catch { }
  snd(p.dimension, "vh.tgd.cast", p.location, 0.8, 1.2);
}
function tickCrbHold() {
  const t = now();
  for (const [id, H] of crbHold) {
    const p = world.getEntity(id);
    if (!p || held(p) !== CRB.ID) { crbHold.delete(id); continue; }
    if (H.blocked) continue;
    const tt = t - H.t0, dim = p.dimension;
    const h = Math.min(CRB.HOURS, Math.floor(tt / CRB.HOUR_T));
    if (h > H.hours) {
      H.hours = h;
      tgdTick(dim, p.location, 0.9 + h * 0.08);
      fx(dim, "vh:tgd_ring", crbUp(p.location, 0.1), { ...CRB_BLUE, size: 2 + h * 0.4, life: 0.4 });
      if (h === CRB.HOURS) { snd(dim, "vh.tgd.gong", p.location, 0.9, 1.3); fx(dim, "vh:tgd_dial", crbUp(p.location, 0.1), { ...CRB_GOLD, size: 7, spin: -180, life: 0.8 }); }
    }
    const a = tt * (0.25 + H.hours * 0.04);                                                  // 허리 둘레를 도는 시곗바늘 둘 (점점 빨라짐)
    for (const [k, L] of [[0, 1.6], [Math.PI, 1.0]]) {
      const d = { x: Math.cos(a + k), y: 0, z: Math.sin(a + k) };
      fx(dim, "vh:tgd_hand", V.add(crbUp(p.location, 1.0), V.mul(d, L / 2 + 0.5)), { ...(k ? CRB_BLUE : CRB_GOLD), dx: d.x, dy: 0, dz: d.z, len: L, w: 0.16, life: 0.1 });
    }
    if (tt % 3 === 0) fx(dim, "vh:tgd_warp", crbUp(p.location, 1.0), { ...CRB_BLUE, n: 3, r: 2.4, life: 0.4 });
    if (tt % 10 === 0) for (const e of enemiesNear(p, p.location, CRB.SLOW_R)) { effect(e, "slowness", 30, 1); fx(dim, "vh:tgd_sand", crbUp(e.location, height(e)), { n: 3, r: 0.4, life: 0.6 }); }
    if (tt % 4 === 0) {
      const full = H.hours >= CRB.HOURS;
      bar(p, `§b시간 압축 ${full ? "§e" : "§f"}${"■".repeat(H.hours)}§8${"■".repeat(CRB.HOURS - H.hours)} §7(${H.hours}/12시)${full ? " §e§l자정 — 놓으세요" : ""}`);
    }
  }
}
function crbHoldEnd(p) {
  const H = crbHold.get(p.id);
  if (!H) return;
  crbHold.delete(p.id);
  if (H.blocked) return;
  if (H.hours < 1) { bar(p, "§7시간이 아직 모이지 않았어요"); return; }
  crbIai(p, H.hours);
}
function crbIai(p, hours) {
  setCd(p, "crb_iai", CRB.IAI_CD);
  const dim = p.dimension, f = V.norm(p.getViewDirection());
  const dir = V.norm({ x: f.x, y: f.y * 0.4, z: f.z });
  const from = crbUp(p.location, 0.9);
  let dist = CRB.DASH0 + hours * CRB.DASH_PER;
  try { const hit = dim.getBlockFromRay(from, dir, { maxDistance: dist + 1, includeLiquidBlocks: false, includePassableBlocks: false }); if (hit) dist = Math.max(0, Math.min(dist, V.dist(from, rayHit(hit)) - 0.8)); } catch { }
  const to = V.add(from, V.mul(dir, dist)), end = crbUp(to, -0.9);
  anim(p, "animation.vh.chrono_blade.iai", 0.1);
  const cut = enemiesNear(p, V.lerp(from, to, 0.5), dist / 2 + CRB.CUT_W + 1).filter((e) => tgdSeg3(center(e), from, to) <= CRB.CUT_W + Math.min(0.6, height(e) * 0.25));
  effect(p, "resistance", 10, 4); effect(p, "slow_falling", 20);
  fx(dim, "vh:tgd_dialv", from, { ...CRB_BLUE, size: 3, spin: 120, life: 0.5 });                    // 떠난 자리의 잔상 시계
  fx(dim, "vh:tgd_warp", from, { ...CRB_BLUE, n: 14, r: 1.6, life: 0.4 });
  try { p.teleport(end, { keepVelocity: false }); } catch { }
  if (dist > 0.5) {
    fx(dim, "vh:tgd_hand", V.lerp(from, to, 0.5), { ...CRB_WHITE, dx: dir.x, dy: dir.y, dz: dir.z, len: dist, w: 0.55, life: 0.45 });   // 시공간이 갈라진 한 줄
    fx(dim, "vh:tgd_hand", V.lerp(from, to, 0.5), { ...CRB_BLUE, dx: dir.x, dy: dir.y, dz: dir.z, len: dist * 1.05, w: 1.3, life: 0.6 });
    for (let k = 0; k <= dist; k += 1.2) fx(dim, "vh:tgd_spark", V.add(from, V.mul(dir, k)), { ...CRB_WHITE, n: 2, spd: 1.5, life: 0.3 });
  }
  crbSlashFx(dim, to, crbFlat(dir), 0, 0, 12, 4);
  fx(dim, "vh:tgd_spark", to, { ...CRB_WHITE, n: 18, spd: 5, life: 0.5 });
  snd(dim, "vh.tgd.zip", end, 1, 1.1); snd(dim, "vh.tgd.slash", end, 1, 0.8);
  const midnight = hours >= CRB.HOURS;
  if (midnight) {
    for (const e of enemiesNear(p, to, 5)) if (!cut.includes(e)) cut.push(e);
    crbSlashFx(dim, to, crbFlat(dir), 0, 1, 18, 5);
    fx(dim, "vh:tgd_dial", bxFloor(dim, crbUp(to, 1)), { ...CRB_GOLD, size: 10, spin: -240, life: 1 });
  }
  const list = cut.slice(0, 16).map((e) => ({ e, marks: crbTakeMarks(e) }));
  for (const C of list) {
    hurt(C.e, CRB.CUT_DMG, p);
    effect(C.e, "slowness", CRB.BURST_T + 4, 6);
    fx(dim, "vh:tgd_spark", center(C.e), { ...CRB_GOLD, n: 8, spd: 3, life: 0.4 });
    if (list.indexOf(C) < 8) tgdSpawn(dim, "vh:tgd_tear", V.add(bxFloor(dim, crbUp(C.e.location, 1)), { x: 0, y: 0.02, z: 0 }), { "vh:y": 0, "vh:w": CRB.BURST_T }, CRB.BURST_T + 26);
  }
  bar(p, `§b§l자정 일섬 §r§f${hours}시${midnight ? " §e§l자정!" : ""} §7— 베인 적 ${list.length}`);
  system.runTimeout(() => {                                                                  // 늦게 도착한 시간이 터짐
    for (const C of list) {
      if (!valid(C.e)) continue;
      const dmg = hours * CRB.HOUR_DMG + C.marks * CRB.MARK_DMG + (midnight ? 6 : 0);
      if (valid(p)) hurt(C.e, dmg, p); else { try { C.e.applyDamage(dmg); } catch { } }
      const c = center(C.e), fl = crbFlat(V.sub(C.e.location, end));
      crbSlashFx(dim, c, fl, -45, 1, 8, 4); crbSlashFx(dim, c, fl, 45, 0, 8, 4);
      fx(dim, "vh:tgd_spark", c, { ...CRB_WHITE, n: 16, spd: 5, life: 0.5 });
      fx(dim, "vh:tgd_warp", c, { ...CRB_VIOL, n: 10, r: 1.8, life: 0.4 });
      knock(C.e, end, 0.3, 0.45);
    }
    if (list.length) { snd(dim, "vh.tgd.tear", end, 1.2, 1); snd(dim, "vh.tgd.chime", end, 1, midnight ? 0.75 : 1.1); }
    if (midnight) snd(dim, "vh.tgd.gong", end, 1.4, 0.9);
  }, CRB.BURST_T);
}

// ---------------------------------------------------------------- 웅크리고 「찢어진 자정」
function crbSever(p) {
  if (crbSevers.has(p.id)) return;
  if (onCooldown(p, "crb_sev", "§d찢어진 자정")) return;
  setCd(p, "crb_sev", CRB.SEV_CD);
  const dim = p.dimension, c = { ...p.location }, g = bxFloor(dim, crbUp(c, 1));
  anim(p, "animation.vh.chrono_blade.sever", 0.1);
  effect(p, "resistance", CRB.SEV_FINAL + 10, 4);
  const yaw = tgdYaw(crbFlat(p.getViewDirection()));
  const clock = tgdSpawn(dim, "vh:tgd_bigclock", V.add(g, { x: 0, y: 0.15, z: 0 }), { "vh:y": yaw, "vh:p": -90, "vh:s": 12, "vh:v": 120, "vh:m": 0, "vh:d": 1 }, CRB.SEV_FINAL + 24);
  crbSevers.set(p.id, { p, dim, c, g, t: 0, frozen: new Map(), clock });
  snd(dim, "vh.tgd.world", c, 1.2, 1.1); snd(dim, "vh.tgd.cast", c, 1, 0.9);
  fx(dim, "vh:tgd_rise", g, { ...CRB_BLUE, n: 24, r: 3, spd: 6, life: 0.8 });
  bar(p, "§d§l찢어진 자정 §r§7— 시간이 멈춘다");
}
function crbFreezeScan(S) {
  for (const e of enemiesNear(S.p, S.c, CRB.SEV_R)) {
    if (S.frozen.has(e.id) || V.dist(e.location, S.c) > CRB.SEV_R) continue;
    let rot; try { rot = e.getRotation(); } catch { }
    S.frozen.set(e.id, { e, loc: { ...e.location }, rot, dmg: 0, boss: BX.IDS.includes(e.typeId) || e.typeId === BOSS.ID });
    fx(S.dim, "vh:tgd_dialv", crbUp(e.location, height(e) + 0.6), { ...CRB_BLUE, size: 1.4, spin: 0, life: 0.6 });
  }
}
function tickCrbSevers() {
  for (const [id, S] of crbSevers) {
    S.t++;
    const p = S.p, dim = S.dim, t = S.t;
    if (!valid(p)) { crbSeverEnd(id, S, false); continue; }
    if (t === CRB.SEV_STOP) {
      crbFreezeScan(S);
      snd(dim, "vh.tgd.freeze", S.c, 1.2, 1); fx(dim, "vh:tgd_ring", crbUp(S.g, 0.1), { ...CRB_WHITE, size: CRB.SEV_R * 2, life: 0.8 });
    }
    if (t > CRB.SEV_STOP) {
      if (t % 4 === 0) crbFreezeScan(S);
      for (const [fid, F] of S.frozen) {                                                       // 멈춘 시간 (보스는 크게 느려지기만)
        if (!valid(F.e)) { S.frozen.delete(fid); continue; }
        try {
          if (F.boss) { if (t % 10 === 0) effect(F.e, "slowness", 14, 4); continue; }
          F.e.teleport(F.loc, F.rot ? { rotation: F.rot } : undefined);
          try { F.e.clearVelocity(); } catch { }
          if (t % 10 === 0) { effect(F.e, "slowness", 14, 255); effect(F.e, "weakness", 14, 255); }
        } catch { }
        if (t % 8 === 0) fx(dim, "vh:tgd_sand", crbUp(F.e.location, height(F.e) + 0.2), { n: 2, r: 0.3, life: 0.6 });
      }
      if (t % 3 === 0) for (let k = 0; k < 3; k++) {                                         // 허공에 멈춘 모래 · 빛 알갱이
        const a = Math.random() * Math.PI * 2, r = Math.random() * CRB.SEV_R;
        fx(dim, "vh:tgd_glow", V.add(S.c, { x: Math.cos(a) * r, y: 0.5 + Math.random() * 3, z: Math.sin(a) * r }), { ...(k % 2 ? CRB_GOLD : CRB_BLUE), size: 0.25, life: 0.5 });
      }
    }
    const ci = CRB.SEV_CUTS.indexOf(t);
    if (ci >= 0) {                                                                            // 멈춘 세계를 가름 (피해는 쌓기만)
      const a = ci * 2.4 + Math.random() * 0.6, d = { x: Math.cos(a), y: 0, z: Math.sin(a) };
      const mid = crbUp(S.g, 1.4 + Math.random() * 0.8), A = V.add(mid, V.mul(d, -CRB.SEV_R)), B = V.add(mid, V.mul(d, CRB.SEV_R));
      crbSlashFx(dim, mid, { x: -d.z, y: 0, z: d.x }, Math.round(Math.random() * 50 - 25), ci % 2, 34, 5);
      fx(dim, "vh:tgd_hand", mid, { ...CRB_WHITE, dx: d.x, dy: 0, dz: d.z, len: CRB.SEV_R * 2, w: 0.5, life: 0.5 });
      snd(dim, "vh.tgd.sweep", S.c, 1, 1 + ci * 0.05); tgdTick(dim, S.c, 1.2 + ci * 0.1);
      for (const F of S.frozen.values()) {
        if (!valid(F.e) || tgdSeg3(center(F.e), A, B) > 2.4) continue;
        F.dmg += CRB.SEV_CUT_DMG;
        fx(dim, "vh:tgd_spark", center(F.e), { ...CRB_GOLD, n: 6, spd: 2, life: 0.35 });
        fx(dim, "vh:tgd_glow", center(F.e), { ...CRB_VIOL, size: 1.2 + F.dmg * 0.04, life: 0.6 });
      }
      if (valid(p)) bar(p, `§d§l찢어진 자정 §r§f${ci + 1}/${CRB.SEV_CUTS.length} §7— 멈춘 세계를 가른다`);
    }
    if (t >= CRB.SEV_FINAL) crbSeverEnd(id, S, true);
  }
}
function crbSeverEnd(id, S, ok) {
  crbSevers.delete(id);
  const dim = S.dim;
  try { if (S.clock && valid(S.clock)) S.clock.remove(); } catch { }
  if (!ok) return;
  snd(dim, "vh.tgd.gong", S.c, 1.6, 0.85); snd(dim, "vh.tgd.thaw", S.c, 1.4, 1); snd(dim, "vh.tgd.break", S.c, 1.2, 0.9);
  fx(dim, "vh:tgd_ring", crbUp(S.g, 0.1), { ...CRB_BLUE, size: CRB.SEV_R * 2.2, life: 1 });
  fx(dim, "vh:tgd_spark", crbUp(S.c, 2), { ...CRB_WHITE, n: 40, spd: 7, life: 0.8 });
  crbSlashFx(dim, crbUp(S.g, 1.6), crbFlat(valid(S.p) ? S.p.getViewDirection() : { x: 0, y: 0, z: 1 }), 0, 0, 40, 6);
  let n = 0;
  for (const F of S.frozen.values()) {
    if (!valid(F.e)) continue;
    const dmg = CRB.SEV_BASE + F.dmg * CRB.SEV_K;
    if (valid(S.p)) hurt(F.e, dmg, S.p); else { try { F.e.applyDamage(dmg); } catch { } }
    knock(F.e, S.c, 0.4, 0.55);
    effect(F.e, "slowness", 40, 1);
    if (n < 10) tgdSpawn(dim, "vh:tgd_tear", V.add(bxFloor(dim, crbUp(F.e.location, 1)), { x: 0, y: 0.02, z: 0 }), { "vh:y": 0, "vh:w": 4 }, 30);
    fx(dim, "vh:tgd_warp", center(F.e), { ...CRB_VIOL, n: 14, r: 2, life: 0.5 });
    n++;
  }
  if (valid(S.p)) bar(S.p, `§d§l찢어진 자정 §r§7— 시간이 다시 흐른다 · ${n}`);
}

// ---------------------------------------------------------------- 들고 있을 때 (빛 · 째깍 · 안내)
function tickCrbHeld() {
  for (const p of world.getAllPlayers()) {
    if (held(p) !== CRB.ID) { if (crbLights.has(p.id)) crbLightOff(p.id); continue; }
    crbLightAt(p);
    if (now() % 20 === 0) snd(p.dimension, "random.click", handPos(p), 0.12, 1.8);
    if (now() % 10 === 0 && !crbHold.has(p.id) && !crbSevers.has(p.id) && now() - (lastMsg.get(p.id) ?? -99) > 30) {
      const a = cdLeft(p, "crb_iai"), s = cdLeft(p, "crb_sev");
      bar(p, `${CRB_HINT}${a > 0 ? ` §8| 일섬 ${a.toFixed(0)}초` : ""}${s > 0 ? ` §8| 자정 ${s.toFixed(0)}초` : ""}`);
      lastMsg.set(p.id, now() - 25);
    }
  }
}

// ---------------------------------------------------------------- 입력: 탭 / 꾹 / 웅크리고
world.afterEvents.itemUse.subscribe((ev) => {
  const p = ev.source;
  if (ev.itemStack?.typeId !== CRB.ID || p?.typeId !== "minecraft:player") return;
  if (crbHold.has(p.id)) { if (now() - crbHold.get(p.id).t0 > 3) crbHoldEnd(p); return; }
  if (p.isSneaking) return crbSever(p);
  const pr = crbPress.get(p.id);
  if (pr && now() - pr.t0 <= 3) return;
  crbPress.set(p.id, { t0: now() });
});
function crbRelease(ev) {
  try {
    if (ev.itemStack?.typeId !== CRB.ID) return;
    const p = ev.source, pr = crbPress.get(p.id);
    if (pr) { crbPress.delete(p.id); if (now() - pr.t0 < CRB.HOLD_TICKS) crbTap(p); return; }
    crbHoldEnd(p);
  } catch { }
}
world.afterEvents.itemStopUse.subscribe(crbRelease);
world.afterEvents.itemReleaseUse.subscribe(crbRelease);
system.runInterval(() => {
  for (const [id, pr] of crbPress) {
    const p = world.getEntity(id);
    if (!p || held(p) !== CRB.ID) { crbPress.delete(id); continue; }
    if (now() - pr.t0 >= CRB.HOLD_TICKS) { crbPress.delete(id); crbHoldStart(p); }
  }
  try { tickCrbHold(); } catch (e) { console.warn("[seven_hope] chrono blade hold " + e); }
  try { tickCrbWaves(); } catch (e) { console.warn("[seven_hope] chrono blade wave " + e); }
  try { tickCrbSevers(); } catch (e) { console.warn("[seven_hope] chrono blade sever " + e); }
  try { tickCrbHeld(); } catch (e) { console.warn("[seven_hope] chrono blade held " + e); }
}, 1);
system.runInterval(() => {
  const t = now();
  for (const [k, v] of crbEchoT) if (t - v > 200) crbEchoT.delete(k);
  for (const [k, m] of crbMarks) if (t - m.t > 200) crbMarks.delete(k);
}, 100);
world.afterEvents.playerLeave?.subscribe((ev) => { crbPress.delete(ev.playerId); crbHold.delete(ev.playerId); crbSwing.delete(ev.playerId); crbLightOff(ev.playerId); });
