// 아홉 세계의 항해 - RPG systems: sailing, progression, enhancement, daily reward, zone mobs, guards.
import { world, system, ItemStack, EnchantmentTypes } from "@minecraft/server";
import { ActionFormData, MessageFormData } from "@minecraft/server-ui";
import { OW, now, players, survivalish, valid, inBox, hdist, title, bar, sound, particle, showForm, tp, pget, pset, rand, pick, GameMode } from "./util.js";
import { spawnMob, removeTagged } from "./mobs.js";
import { DUNGEONS, ORDER, ZONES, SPAWN, WORLDS } from "./data.js";

const TIER_KO = { beginner: "§a초급", mid: "§e중급", high: "§c상급" };
const ARRIVAL = () => SPAWN.arrival;

// ---------------------------------------------------------------- inventory helpers
function inv(p) {
  try { return p.getComponent("minecraft:inventory").container; } catch (e) { return undefined; }
}
export function give(p, id, n = 1) {
  const c = inv(p);
  let left = n;
  while (left > 0) {
    const k = Math.min(left, 64);
    try {
      const rest = c ? c.addItem(new ItemStack(id, k)) : undefined;
      if (rest) p.dimension.spawnItem(rest, p.location);
    } catch (e) {
      try { p.dimension.spawnItem(new ItemStack(id, k), p.location); } catch (err) { }
    }
    left -= k;
  }
}
function countItem(p, id) {
  const c = inv(p);
  let n = 0;
  if (!c) return 0;
  for (let i = 0; i < c.size; i++) {
    const it = c.getItem(i);
    if (it && it.typeId === id) n += it.amount;
  }
  return n;
}
function takeItem(p, id, n) {
  const c = inv(p);
  if (!c || countItem(p, id) < n) return false;
  for (let i = 0; i < c.size && n > 0; i++) {
    const it = c.getItem(i);
    if (!it || it.typeId !== id) continue;
    const k = Math.min(n, it.amount);
    if (it.amount - k <= 0) c.setItem(i, undefined);
    else { it.amount -= k; c.setItem(i, it); }
    n -= k;
  }
  return true;
}
function cleared(p) { return pget(p, "nrpg:cleared", []); }
function unlocked(p, did) {
  const i = ORDER.indexOf(did);
  return i <= 0 || cleared(p).includes(ORDER[i - 1]);
}
function fade(p, color) {
  try { p.camera.fade({ fadeTime: { fadeInTime: 0.6, holdTime: 0.8, fadeOutTime: 1.0 }, fadeColor: color || { red: 0, green: 0, blue: 0 } }); } catch (e) { }
}

// ---------------------------------------------------------------- travel
const BUSY = new Map();          // player id -> tick until which no new ship form opens
function sailTo(p, did) {
  const W = WORLDS[did], d = DUNGEONS[did];
  if (!W) return;
  fade(p);
  sound(p, "raid.horn", 0.7, 1.2);
  system.runTimeout(() => {
    tp(p, W.start);
    pset(p, "nrpg:where", did);
    title(p, d.color + "§l" + d.ko, "§7" + d.realm + " · " + TIER_KO[d.tier] + " §7" + d.lv, 90);
    sound(p, "ambient.weather.thunder", 0.4, 1.4);
    p.sendMessage("§6[항해] §f" + d.ko + "에 상륙했습니다. 귀환선에 오르면 항구로 돌아갑니다.");
  }, 14);
}
export function goHome(p, msg) {
  fade(p);
  system.runTimeout(() => {
    tp(p, ARRIVAL());
    pset(p, "nrpg:where", "");
    title(p, "§6§l미드가르드 항구", msg || "§7무사히 돌아왔습니다", 60);
    sound(p, "random.levelup", 0.6, 1.4);
  }, 14);
}

async function shipForm(p, ship) {
  const did = ship.dungeon, d = DUNGEONS[did];
  const done = cleared(p).includes(did);
  const ok = unlocked(p, did);
  const zones = d.zones.slice(1).map((z, i) => (i === 6 ? "§c★ " : "§7- ") + z).join("\n");
  const prev = ORDER[ORDER.indexOf(did) - 1];
  let body = d.color + "§l" + d.ko + "§r  " + TIER_KO[d.tier] + " §7" + d.lv + "\n§f" + d.blurb + "\n\n" + zones + "\n\n";
  body += done ? "§a✔ 클리어한 던전입니다" : ok ? "§e도전 가능" : "§c잠김 — 먼저 " + DUNGEONS[prev].ko + "을(를) 클리어하세요";
  const f = new ActionFormData().title("§l" + d.no + "번 항로").body(body);
  if (ok) f.button("§l출항한다");
  f.button("아직이다");
  const r = await showForm(p, f);
  if (!r.canceled && ok && r.selection === 0) sailTo(p, did);
}
async function returnForm(p) {
  const f = new MessageFormData().title("§l귀환선").body("§f항구(미드가르드)로 돌아갈까요?\n§7던전 진행 상황은 보스마다 저장되지 않습니다.").button1("§l돌아간다").button2("더 머문다");
  const r = await showForm(p, f);
  if (!r.canceled && r.selection === 0) goHome(p);
}
function shipTick() {
  const t = now();
  for (const p of players()) {
    if (!survivalish(p)) continue;
    const l = p.location;
    let on = null, ret = false;
    for (const s of SPAWN.ships) if (inBox(l, s.deck, 0.5)) on = s;
    if (!on) for (const did in WORLDS) { const W = WORLDS[did]; if (W.ret && inBox(l, W.ret.deck, 0.5)) { ret = true; on = did; } }
    const key = p.id;
    const last = pget(p, "nrpg:onship", "");
    const tag = on ? (ret ? "r:" + on : "s:" + on.dungeon) : "";
    if (tag && tag !== last && (BUSY.get(key) || 0) < t) {
      BUSY.set(key, t + 60);
      if (ret) returnForm(p); else shipForm(p, on);
    } else if (tag && p.isSneaking && (BUSY.get(key) || 0) < t) {
      BUSY.set(key, t + 60);
      if (ret) returnForm(p); else shipForm(p, on);
    } else if (tag) {
      bar(p, "§7웅크리면 " + (ret ? "귀환" : "출항") + " 메뉴가 다시 열립니다");
    }
    if (tag !== last) pset(p, "nrpg:onship", tag);
    // exit portals after the final boss
    for (const did in WORLDS) {
      const W = WORLDS[did];
      if (W.exit && inBox(l, W.exit, 0.4)) {
        const d = DUNGEONS[did];
        goHome(p, "§a" + d.ko + " §f클리어! 항구로 돌아왔습니다");
        break;
      }
    }
  }
}

// ---------------------------------------------------------------- return scroll / journal
const CHANNEL = new Map();
function channelHome(p, secs, cost) {
  if (CHANNEL.has(p.id)) return;
  const start = { x: p.location.x, y: p.location.y, z: p.location.z };
  const hp0 = health(p);
  let left = secs * 20;
  const id = system.runInterval(() => {
    if (!valid(p)) { system.clearRun(id); CHANNEL.delete(p.id); return; }
    const moved = hdist(p.location, start) > 1.2 || health(p) < hp0;
    if (moved) {
      bar(p, "§c귀환이 취소되었습니다");
      system.clearRun(id); CHANNEL.delete(p.id); return;
    }
    left -= 5;
    bar(p, "§a귀환 중... §f" + Math.ceil(left / 20) + "초 §7(움직이거나 맞으면 취소)");
    particle(p.dimension, "minecraft:totem_particle", { x: p.location.x, y: p.location.y + 1, z: p.location.z });
    if (left <= 0) {
      system.clearRun(id); CHANNEL.delete(p.id);
      if (cost && !takeItem(p, cost, 1)) { bar(p, "§c귀환 주문서가 없습니다"); return; }
      goHome(p);
    }
  }, 5);
  CHANNEL.set(p.id, id);
}
function health(p) {
  try { return p.getComponent("minecraft:health").currentValue; } catch (e) { return 20; }
}
async function journal(p) {
  const cl = cleared(p);
  let body = "§l진행도§r\n";
  for (const did of ORDER) {
    const d = DUNGEONS[did];
    const mark = cl.includes(did) ? "§a✔" : unlocked(p, did) ? "§e▶" : "§8✖";
    body += mark + " §f" + d.no + ". " + d.color + d.ko + " §7" + d.lv + "\n";
  }
  body += "\n§b룬 조각 §f" + countItem(p, "nrpg:rune_shard") + "   §d룬 정수 §f" + countItem(p, "nrpg:rune_core") + "   §e보호 주문서 §f" + countItem(p, "nrpg:ward_scroll");
  const streak = pget(p, "nrpg:daily", { last: "", streak: 0 });
  body += "\n§6일일보상 §f연속 " + streak.streak + "일" + (streak.last === dayKey(0) ? " §a(오늘 받음)" : " §e(받을 수 있음)");
  const f = new ActionFormData().title("§l모험가의 수첩").body(body)
    .button("§l항구로 귀환 §r§7(10초, 무료)").button("§l안내").button("닫기");
  const r = await showForm(p, f);
  if (r.canceled) return;
  if (r.selection === 0) channelHome(p, 10, undefined);
  else if (r.selection === 1) guide(p);
}
async function guide(p) {
  const text = [
    "§6§l아홉 세계의 항해§r",
    "§f항구의 배에 오르면 던전으로 출항합니다. 앞 던전을 클리어해야 다음 항로가 열립니다.",
    "§f던전은 시작 지역 → 전투 구역 6곳 → 최종 보스 순서입니다. 중급부터는 3·5번째 구역에 중간 보스가 있습니다.",
    "§c보스의 모든 기술은 맞기 전에 바닥에 범위와 경로가 표시됩니다. §f빨간 표시가 꽉 차기 전에 벗어나세요.",
    "§b룬 조각§f과 §d룬 정수§f로 대장간 모루에서 장비를 강화합니다(+10까지). 높은 단계는 실패하면 단계가 내려가거나 부서질 수 있으니 §e보호 주문서§f를 챙기세요.",
    "§f노른의 우물에서 하루 한 번 일일보상을 받습니다(한국 시간 기준, 7일 연속 보상).",
    "§f귀환선, 최종 보스 뒤의 룬 원, 귀환 주문서, 수첩으로 항구에 돌아올 수 있습니다.",
  ].join("\n\n");
  await showForm(p, new ActionFormData().title("§l안내").body(text).button("닫기"));
}

// ---------------------------------------------------------------- enhancement
const KIND = [
  ["sword", "weapon"], ["_axe", "weapon"], ["mace", "weapon"], ["trident", "trident"], ["crossbow", "crossbow"], ["bow", "bow"],
  ["helmet", "helmet"], ["chestplate", "armor"], ["leggings", "armor"], ["boots", "boots"],
];
const NAMES = {
  wooden_sword: "나무 검", stone_sword: "돌 검", iron_sword: "철 검", golden_sword: "금 검", diamond_sword: "다이아몬드 검", netherite_sword: "네더라이트 검",
  iron_axe: "철 도끼", diamond_axe: "다이아몬드 도끼", netherite_axe: "네더라이트 도끼", stone_axe: "돌 도끼", mace: "철퇴", trident: "삼지창",
  bow: "활", crossbow: "쇠뇌", shield: "방패",
  leather_helmet: "가죽 모자", leather_chestplate: "가죽 조끼", leather_leggings: "가죽 바지", leather_boots: "가죽 장화",
  chainmail_helmet: "사슬 투구", chainmail_chestplate: "사슬 갑옷", chainmail_leggings: "사슬 각반", chainmail_boots: "사슬 장화",
  iron_helmet: "철 투구", iron_chestplate: "철 흉갑", iron_leggings: "철 각반", iron_boots: "철 장화",
  diamond_helmet: "다이아몬드 투구", diamond_chestplate: "다이아몬드 흉갑", diamond_leggings: "다이아몬드 각반", diamond_boots: "다이아몬드 장화",
  netherite_helmet: "네더라이트 투구", netherite_chestplate: "네더라이트 흉갑", netherite_leggings: "네더라이트 각반", netherite_boots: "네더라이트 장화",
};
const RATE = [100, 95, 90, 80, 70, 60, 50, 42, 35, 30];
function kindOf(id) {
  for (const [s, k] of KIND) if (id.includes(s)) return k;
  return undefined;
}
function step(L, table) {
  let v = 0;
  for (const [lv, n] of table) if (L >= lv) v = n;
  return v;
}
function enchantsFor(kind, L) {
  const unb = step(L, [[3, 1], [5, 2], [7, 3]]);
  if (kind === "weapon") return { sharpness: step(L, [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]]), unbreaking: unb,
    fire_aspect: step(L, [[6, 1], [8, 2]]), looting: step(L, [[8, 1], [9, 2], [10, 3]]), knockback: step(L, [[9, 1]]) };
  if (kind === "bow") return { power: step(L, [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]]), unbreaking: unb, punch: step(L, [[6, 1], [8, 2]]), flame: step(L, [[7, 1]]), infinity: step(L, [[10, 1]]) };
  if (kind === "crossbow") return { quick_charge: step(L, [[1, 1], [4, 2], [7, 3]]), unbreaking: unb, piercing: step(L, [[2, 1], [5, 2], [8, 3], [9, 4]]), multishot: step(L, [[10, 1]]) };
  if (kind === "trident") return { impaling: step(L, [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]]), unbreaking: unb, loyalty: step(L, [[6, 1], [8, 2], [9, 3]]), channeling: step(L, [[10, 1]]) };
  const prot = step(L, [[1, 1], [3, 2], [5, 3], [7, 4]]);
  const e = { protection: prot, unbreaking: unb, thorns: step(L, [[8, 1], [9, 2], [10, 3]]) };
  if (kind === "helmet") e.respiration = step(L, [[6, 1], [9, 3]]);
  if (kind === "boots") e.feather_falling = step(L, [[4, 1], [6, 2], [8, 3], [10, 4]]);
  return e;
}
function applyLevel(item, L) {
  const kind = kindOf(item.typeId);
  try {
    const en = item.getComponent("minecraft:enchantable");
    if (en) {
      en.removeAllEnchantments();
      const want = enchantsFor(kind, L);
      for (const k in want) {
        if (want[k] <= 0) continue;
        try {
          const type = EnchantmentTypes.get(k);
          const lvl = Math.min(want[k], type.maxLevel);
          const ench = { type, level: lvl };
          if (en.canAddEnchantment(ench)) en.addEnchantment(ench);
        } catch (err) { }
      }
    }
  } catch (e) { }
  const base = NAMES[item.typeId.replace("minecraft:", "")] || "장비";
  const col = L >= 10 ? "§6" : L >= 7 ? "§d" : L >= 4 ? "§b" : "§a";
  item.nameTag = L > 0 ? col + "+" + L + " " + base : undefined;
  try { item.setLore(L > 0 ? ["§7룬 강화 §f+" + L, L >= 10 ? "§6전설의 장비" : "§8아홉 세계의 대장간"] : []); } catch (e) { }
  try { item.setDynamicProperty("nrpg:enh", L); } catch (e) { }
  return item;
}
function levelOf(item) {
  try { const v = item.getDynamicProperty("nrpg:enh"); if (typeof v === "number") return v; } catch (e) { }
  const m = /\+(\d+)/.exec(item.nameTag || "");
  return m ? Number(m[1]) : 0;
}
function costOf(L) {
  return { shard: 2 + L * 2, core: L >= 5 ? L - 3 : 0 };
}
async function enhanceForm(p) {
  const c = inv(p);
  const slot = p.selectedSlotIndex;
  const item = c ? c.getItem(slot) : undefined;
  if (!item || !kindOf(item.typeId)) {
    await showForm(p, new ActionFormData().title("§l룬 대장간").body("§f강화할 무기나 방어구를 §e손에 들고§f 모루를 사용하세요.\n\n§7검·도끼·철퇴·활·쇠뇌·삼지창·투구·갑옷·각반·장화를 강화할 수 있습니다.").button("닫기"));
    return;
  }
  const L = levelOf(item);
  if (L >= 10) {
    await showForm(p, new ActionFormData().title("§l룬 대장간").body("§6이미 최고 단계(+10)입니다.").button("닫기"));
    return;
  }
  const cost = costOf(L);
  const ward = countItem(p, "nrpg:ward_scroll");
  const risk = L >= 6 ? (L >= 7 ? "§c실패하면 단계가 내려가거나(70%) 장비가 부서집니다(30%)" : "§c실패하면 단계가 1 내려갑니다") : "§a실패해도 단계는 유지됩니다";
  const name = (item.nameTag || NAMES[item.typeId.replace("minecraft:", "")] || item.typeId);
  const body = "§f" + name + "\n§7현재 §f+" + L + " §7→ §b+" + (L + 1) + "\n\n§f성공 확률 §e" + RATE[L] + "%\n§f재료 §b룬 조각 " + cost.shard + "개" +
    (cost.core ? " §d룬 정수 " + cost.core + "개" : "") + "\n§7보유: 조각 " + countItem(p, "nrpg:rune_shard") + " / 정수 " + countItem(p, "nrpg:rune_core") +
    " / 보호 주문서 " + ward + "\n\n" + risk;
  const f = new ActionFormData().title("§l룬 대장간").body(body).button("§l강화한다");
  if (L >= 6 && ward > 0) f.button("§l§e보호 주문서를 쓰고 강화");
  f.button("그만둔다");
  const r = await showForm(p, f);
  if (r.canceled) return;
  const useWard = L >= 6 && ward > 0 && r.selection === 1;
  if (!(r.selection === 0 || useWard)) return;
  // the item must still be in the hand
  const now2 = c.getItem(p.selectedSlotIndex);
  if (!now2 || now2.typeId !== item.typeId || levelOf(now2) !== L) { p.sendMessage("§c손에 든 장비가 바뀌었습니다."); return; }
  if (countItem(p, "nrpg:rune_shard") < cost.shard || countItem(p, "nrpg:rune_core") < cost.core) { p.sendMessage("§c재료가 부족합니다."); sound(p, "note.bass", 1, 0.6); return; }
  takeItem(p, "nrpg:rune_shard", cost.shard);
  if (cost.core) takeItem(p, "nrpg:rune_core", cost.core);
  if (useWard) takeItem(p, "nrpg:ward_scroll", 1);
  const spot = SPAWN.stations.enhance[0];
  const loc = { x: spot[0] + 0.5, y: spot[1] + 1.2, z: spot[2] + 0.5 };
  if (Math.random() * 100 < RATE[L]) {
    c.setItem(p.selectedSlotIndex, applyLevel(now2, L + 1));
    title(p, "§b§l강화 성공!", "§f+" + (L + 1) + " " + (NAMES[now2.typeId.replace("minecraft:", "")] || ""), 50);
    sound(p, "random.anvil_use", 1, 1.3);
    sound(p, "random.levelup", 0.7, 1.6);
    particle(p.dimension, "minecraft:totem_particle", loc);
    if (L + 1 >= 8) world.sendMessage("§6[대장간] §f" + p.name + " 님이 §b+" + (L + 1) + " §f강화에 성공했습니다!");
  } else {
    sound(p, "random.anvil_land", 1, 0.7);
    if (L >= 6 && !useWard) {
      if (L >= 7 && Math.random() < 0.3) {
        c.setItem(p.selectedSlotIndex, undefined);
        title(p, "§c§l장비가 부서졌습니다", "§7보호 주문서가 있었다면...", 60);
        sound(p, "random.break", 1, 0.8);
        return;
      }
      c.setItem(p.selectedSlotIndex, applyLevel(now2, L - 1));
      title(p, "§c§l강화 실패", "§f단계가 §c+" + (L - 1) + "§f로 내려갔습니다", 50);
    } else {
      title(p, "§7§l강화 실패", useWard ? "§e보호 주문서가 장비를 지켰습니다" : "§7단계는 그대로입니다", 50);
    }
    particle(p.dimension, "minecraft:large_explosion", loc);
  }
}

// ---------------------------------------------------------------- daily reward (Korean time)
function dayKey(offsetDays) {
  const d = new Date(Date.now() + 9 * 3600 * 1000 + offsetDays * 86400000);
  return d.toISOString().slice(0, 10);
}
const DAILY = [
  [["nrpg:rune_shard", 4], ["minecraft:bread", 8]],
  [["nrpg:rune_shard", 6], ["nrpg:return_scroll", 1]],
  [["nrpg:rune_shard", 8], ["minecraft:golden_carrot", 8]],
  [["nrpg:rune_shard", 8], ["nrpg:rune_core", 1]],
  [["nrpg:rune_shard", 10], ["nrpg:ward_scroll", 1]],
  [["nrpg:rune_shard", 12], ["nrpg:return_scroll", 2], ["minecraft:arrow", 32]],
  [["nrpg:rune_shard", 16], ["nrpg:rune_core", 2], ["nrpg:ward_scroll", 1], ["minecraft:golden_apple", 2]],
];
const ITEM_KO = { "nrpg:rune_shard": "룬 조각", "nrpg:rune_core": "룬 정수", "nrpg:ward_scroll": "보호 주문서", "nrpg:return_scroll": "귀환 주문서",
  "minecraft:bread": "빵", "minecraft:golden_carrot": "황금 당근", "minecraft:arrow": "화살", "minecraft:golden_apple": "황금 사과" };
async function dailyForm(p) {
  const st = pget(p, "nrpg:daily", { last: "", streak: 0 });
  const today = dayKey(0), yest = dayKey(-1);
  const can = st.last !== today;
  const next = can ? (st.last === yest ? st.streak % 7 + 1 : 1) : st.streak;
  let body = "§f노른의 우물에서 하루 한 번 운명의 선물을 받습니다. §7(한국 시간 자정에 초기화)\n\n";
  for (let i = 0; i < 7; i++) {
    const mark = (can ? i + 1 < next : i + 1 <= next) ? "§a✔" : i + 1 === next && can ? "§e▶" : "§8·";
    body += mark + " §f" + (i + 1) + "일차: §7" + DAILY[i].map(([id, n]) => ITEM_KO[id] + " " + n).join(", ") + "\n";
  }
  body += can ? "\n§e오늘의 보상을 받을 수 있습니다!" : "\n§7오늘은 이미 받았습니다. 내일 다시 오세요.";
  const f = new ActionFormData().title("§l노른의 우물").body(body);
  if (can) f.button("§l받는다");
  f.button("닫기");
  const r = await showForm(p, f);
  if (r.canceled || !can || r.selection !== 0) return;
  const cur = pget(p, "nrpg:daily", { last: "", streak: 0 });
  if (cur.last === dayKey(0)) return;
  const streak = cur.last === dayKey(-1) ? cur.streak % 7 + 1 : 1;
  for (const [id, n] of DAILY[streak - 1]) give(p, id, n);
  pset(p, "nrpg:daily", { last: dayKey(0), streak });
  title(p, "§6§l일일보상 " + streak + "일차", "§f" + DAILY[streak - 1].map(([id, n]) => ITEM_KO[id] + " " + n).join(", "), 60);
  sound(p, "random.orb", 1, 1.2);
}

// ---------------------------------------------------------------- zone mobs
const ZSTATE = new Map();     // zone id -> { ents: [], lastSeen }
function zoneTick() {
  const t = now();
  const dim = OW();
  const ps = players().filter((p) => survivalish(p));
  for (const Z of ZONES) {
    let st = ZSTATE.get(Z.id);
    if (!st) { st = { ents: [], lastSeen: -99999 }; ZSTATE.set(Z.id, st); }
    st.ents = st.ents.filter((e) => valid(e));
    const near = ps.filter((p) => inBox(p.location, Z.box, 18));
    if (near.length) st.lastSeen = t;
    else {
      if (st.ents.length && t - st.lastSeen > 1200) {
        for (const e of st.ents) try { e.remove(); } catch (err) { }
        st.ents = [];
      }
      continue;
    }
    const tier = (DUNGEONS[Z.dungeon] || {}).tier;
    const cap = Math.min(Z.cap + Math.max(0, near.length - 1) * 2, Z.cap * 2);
    let spawned = 0;
    for (let tries = 0; tries < 6 && st.ents.length < cap && spawned < 2; tries++) {
      const pt = pick(Z.points);
      if (!pt) break;
      const dmin = Math.min(...near.map((p) => hdist(p.location, { x: pt[0], z: pt[2] })));
      if (dmin < 9 || dmin > 44) continue;
      const e = spawnMob(pick(Z.mobs), { x: pt[0], y: pt[1], z: pt[2] }, ["nrpg_zone_" + Z.id], dim, tier);
      if (e) { st.ents.push(e); spawned++; }
    }
  }
}

// ---------------------------------------------------------------- ambient particles
function ambientTick() {
  const dim = OW();
  for (const did in WORLDS) {
    for (const A of WORLDS[did].ambient || []) {
      for (const p of players()) {
        if (!inBox(p.location, A.box, 24)) continue;
        for (let i = 0; i < (A.rate || 1) * 2; i++) {
          const loc = { x: p.location.x + rand(-16, 16), y: p.location.y + rand(0, 8), z: p.location.z + rand(-16, 16) };
          if (inBox(loc, A.box, 4)) particle(dim, A.particle, loc);
        }
      }
    }
  }
}

// ---------------------------------------------------------------- guards: map edges, falls into the void
function inRegion(l, r, m = 2) {
  return l.x >= r[0] - m && l.x <= r[3] + 1 + m && l.z >= r[2] - m && l.z <= r[5] + 1 + m && l.y >= r[1] - 8 && l.y <= r[4] + 24;
}
function guardTick() {
  for (const p of players()) {
    if (!survivalish(p)) continue;
    const l = p.location;
    if (inRegion(l, SPAWN.region)) continue;
    let ok = false;
    for (const did in WORLDS) {
      if (inRegion(l, WORLDS[did].region)) {
        ok = true;
        if (l.y < WORLDS[did].region[1] + 1) { tp(p, WORLDS[did].start); p.sendMessage("§7[안내] 길을 잃어 시작 지점으로 돌아왔습니다."); }
        break;
      }
    }
    if (!ok) { tp(p, ARRIVAL()); p.sendMessage("§7[안내] 세계의 끝에 닿아 항구로 돌아왔습니다."); }
  }
}

// ---------------------------------------------------------------- training dummies
function dummyTick() {
  const dim = OW();
  const pts = SPAWN.dummies || [];
  if (!players().some((p) => hdist(p.location, { x: pts[0][0], z: pts[0][2] }) < 40)) return;
  let have = [];
  try { have = dim.getEntities({ type: "nrpg:dummy", tags: ["nrpg_training"] }); } catch (e) { }
  for (const pt of pts) {
    if (have.some((e) => hdist(e.location, { x: pt[0], z: pt[2] }) < 1.5)) continue;
    try {
      const e = dim.spawnEntity("nrpg:dummy", { x: pt[0], y: pt[1], z: pt[2] });
      e.addTag("nrpg_training");
      e.nameTag = "§7허수아비";
    } catch (e) { }
  }
}

// ---------------------------------------------------------------- first join, items, stations
function starterKit(p) {
  if (pget(p, "nrpg:kit", false)) return;
  pset(p, "nrpg:kit", true);
  for (const [id, n] of [["nrpg:journal", 1], ["minecraft:iron_sword", 1], ["minecraft:bow", 1], ["minecraft:arrow", 48], ["minecraft:shield", 1],
    ["minecraft:chainmail_helmet", 1], ["minecraft:chainmail_chestplate", 1], ["minecraft:chainmail_leggings", 1], ["minecraft:chainmail_boots", 1],
    ["minecraft:bread", 24], ["nrpg:return_scroll", 3], ["nrpg:rune_shard", 8]]) give(p, id, n);
  p.sendMessage("§6[아홉 세계] §f환영합니다! 수첩(§6모험가의 수첩§f)을 사용하면 안내를 볼 수 있습니다.");
}
function near3(l, s) {
  return Math.abs(l.x - s[0]) <= 1 && Math.abs(l.y - s[1]) <= 1 && Math.abs(l.z - s[2]) <= 1;
}

export function initRpg() {
  world.afterEvents.playerSpawn.subscribe((ev) => {
    const p = ev.player;
    if (ev.initialSpawn) {
      system.runTimeout(() => {
        try { const a = ARRIVAL(); p.setSpawnPoint({ dimension: OW(), x: a[0], y: a[1], z: a[2] }); } catch (e) { }
        try { if (String(p.getGameMode()).toLowerCase() === "survival") p.setGameMode(GameMode.Adventure ?? GameMode.adventure); } catch (e) { }
        if (!pget(p, "nrpg:kit", false)) { tp(p, ARRIVAL()); title(p, "§6§l아홉 세계의 항해", "§f미드가르드 항구에 오신 것을 환영합니다", 100); }
        starterKit(p);
      }, 30);
    }
  });
  world.beforeEvents.playerInteractWithBlock.subscribe((ev) => {
    const b = ev.block, p = ev.player;
    if (!b || !p) return;
    const l = b.location;
    if ((SPAWN.stations.enhance || []).some((s) => near3(l, s))) {
      ev.cancel = true;
      system.run(() => enhanceForm(p));
    } else if ((SPAWN.stations.daily || []).some((s) => near3(l, s))) {
      ev.cancel = true;
      system.run(() => dailyForm(p));
    }
  });
  world.afterEvents.itemUse.subscribe((ev) => {
    const p = ev.source, it = ev.itemStack;
    if (!p || !it) return;
    if (it.typeId === "nrpg:return_scroll") channelHome(p, 5, "nrpg:return_scroll");
    else if (it.typeId === "nrpg:journal") journal(p);
  });
  world.afterEvents.entityDie.subscribe((ev) => {
    const e = ev.deadEntity;
    let tags = [];
    try { tags = e.getTags(); } catch (err) { return; }
    if (!tags.includes("nrpg_mob") || tags.some((t) => t.startsWith("nrpg_minion"))) return;
    if (Math.random() < 0.35) {
      try { e.dimension.spawnItem(new ItemStack("nrpg:rune_shard", Math.random() < 0.2 ? 2 : 1), e.location); } catch (err) { }
    }
  });
  world.afterEvents.entityHurt.subscribe((ev) => {
    const e = ev.hurtEntity;
    try {
      if (e.typeId !== "nrpg:dummy" || !e.hasTag("nrpg_training")) return;
      e.nameTag = "§c-" + ev.damage.toFixed(1) + " §7허수아비";
      const h = e.getComponent("minecraft:health");
      system.runTimeout(() => { try { h.resetToMaxValue(); e.nameTag = "§7허수아비"; } catch (err) { } }, 40);
    } catch (err) { }
  });
  system.runInterval(shipTick, 10);
  system.runInterval(zoneTick, 40);
  system.runInterval(ambientTick, 20);
  system.runInterval(guardTick, 20);
  system.runInterval(dummyTick, 200);
  console.warn("[nrpg] rpg ready: zones=" + ZONES.length + " ships=" + SPAWN.ships.length + " worlds=" + Object.keys(WORLDS).length);
}

// scriptevent hooks for testing: nrpg:sail <dungeon>, nrpg:home, nrpg:clearall, nrpg:enh <level>, nrpg:zones
export function rpgEvent(id, args, src) {
  const p = src && src.typeId === "minecraft:player" ? src : players()[0];
  if (id === "nrpg:zones") {
    let n = 0;
    for (const st of ZSTATE.values()) n += st.ents.filter((e) => valid(e)).length;
    console.warn("[nrpg] zones live mobs=" + n + " tracked=" + ZSTATE.size);
    return;
  }
  if (id === "nrpg:zonetest") {
    // spawn one mob of every zone's first type at its first point (no player needed)
    let ok = 0, bad = 0;
    for (const Z of ZONES) {
      if (args[0] && Z.dungeon !== args[0]) continue;
      const pt = Z.points[0];
      if (!pt) { bad++; continue; }
      const e = spawnMob(Z.mobs[0], { x: pt[0], y: pt[1], z: pt[2] }, ["nrpg_zonetest"], OW(), (DUNGEONS[Z.dungeon] || {}).tier);
      if (e) ok++; else bad++;
    }
    console.warn("[nrpg] zonetest spawned=" + ok + " failed=" + bad);
    removeTagged("nrpg_zonetest");
    return;
  }
  if (!p) { console.warn("[nrpg] no player for " + id); return; }
  if (id === "nrpg:sail") sailTo(p, args[0]);
  else if (id === "nrpg:home") goHome(p);
  else if (id === "nrpg:clearall") { pset(p, "nrpg:cleared", ORDER.slice()); p.sendMessage("all unlocked"); }
  else if (id === "nrpg:enh") {
    const c = inv(p);
    const it = c && c.getItem(p.selectedSlotIndex);
    if (it) c.setItem(p.selectedSlotIndex, applyLevel(it, Number(args[0] || 1)));
  }
}
