// 능력 술래잡기 - The Skeld: vents (sneak on a grate to jump to the next vent) and the emergency button.
// Generated into behavior_packs/ability_tag_bp/scripts/skeld.js by pack.py (the data is filled in there).
import { world, system } from "@minecraft/server";

const VENTS = __VENTS__;      // [{group, name, x, y, z}]  x, z = north-west cell of the 2x2 grate, y = feet
const BUTTON = __BUTTON__;    // {x, y, z} emergency button block
const AREA = __AREA__;        // {x1, z1, x2, z2} the ship (only players in here are checked)
const VENT_COOLDOWN = 20;     // ticks
const MEETING_COOLDOWN = 200; // ticks

const lastVent = new Map();
const waitRelease = new Set();
let lastMeeting = -MEETING_COOLDOWN;

function inShip(p) {
  const l = p.location;
  return l.x >= AREA.x1 && l.x <= AREA.x2 + 1 && l.z >= AREA.z1 && l.z <= AREA.z2 + 1;
}

function ventAt(l) {
  const bx = Math.floor(l.x), by = Math.floor(l.y + 0.01), bz = Math.floor(l.z);
  return VENTS.findIndex((v) => bx >= v.x && bx <= v.x + 1 && bz >= v.z && bz <= v.z + 1 && Math.abs(by - v.y) <= 1);
}

function nextVent(i) {
  const group = VENTS.filter((v) => v.group === VENTS[i].group);
  const k = group.indexOf(VENTS[i]);
  return group[(k + 1) % group.length];
}

system.runInterval(() => {
  const now = system.currentTick;
  for (const p of world.getAllPlayers()) {
    if (!inShip(p)) continue;
    if (!p.isSneaking) {
      waitRelease.delete(p.id);
      continue;
    }
    if (waitRelease.has(p.id)) continue;
    const i = ventAt(p.location);
    if (i < 0) continue;
    const prev = lastVent.get(p.id);
    if (prev !== undefined && now - prev < VENT_COOLDOWN) continue;
    const d = nextVent(i);
    lastVent.set(p.id, now);
    waitRelease.add(p.id);       // stand up again before the next jump
    p.teleport({ x: d.x + 1, y: d.y, z: d.z + 1 }, { dimension: p.dimension });
    p.playSound("random.door_close");
    p.onScreenDisplay.setActionBar("§7벤트 이동 → §f" + d.name);
  }
}, 2);

function meeting(player) {
  const now = system.currentTick;
  if (now - lastMeeting < MEETING_COOLDOWN) {
    if (player) player.onScreenDisplay.setActionBar("§7긴급 회의는 잠시 후에 다시 열 수 있어요");
    return;
  }
  lastMeeting = now;
  const who = player ? player.name : "누군가";
  for (const p of world.getAllPlayers()) {
    if (!inShip(p)) continue;
    p.onScreenDisplay.setTitle("§c§l긴급 회의!", {
      fadeInDuration: 5,
      stayDuration: 50,
      fadeOutDuration: 15,
      subtitle: "§f" + who + "님이 회의를 소집했습니다",
    });
    p.playSound("raid.horn");
  }
}

if (world.afterEvents.buttonPush) {
  world.afterEvents.buttonPush.subscribe((ev) => {
    const b = ev.block;
    if (b.x !== BUTTON.x || b.y !== BUTTON.y || b.z !== BUTTON.z) return;
    const src = ev.source;
    meeting(src && src.typeId === "minecraft:player" ? src : undefined);
  });
}

// /scriptevent at:skeld diag     (checks that the script is running)
system.afterEvents.scriptEventReceive.subscribe(
  (ev) => {
    if (ev.id !== "at:skeld") return;
    if (ev.message.trim() === "diag") {
      console.warn(
        "[at] skeld ok: vents=" + VENTS.length +
        " groups=" + new Set(VENTS.map((v) => v.group)).size +
        " buttonPush=" + typeof world.afterEvents.buttonPush +
        " button=" + BUTTON.x + "," + BUTTON.y + "," + BUTTON.z
      );
    } else if (ev.message.trim() === "meeting") {
      const src = ev.sourceEntity;
      meeting(src && src.typeId === "minecraft:player" ? src : undefined);
    }
  },
  { namespaces: ["at"] }
);
