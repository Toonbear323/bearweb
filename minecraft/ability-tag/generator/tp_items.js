// 능력 술래잡기 - TP items: right-click (use) a named item to teleport to the lobby spawn or a map.
// Generated into behavior_packs/ability_tag_bp/scripts/main.js by pack.py (DESTS is filled in there).
import { world, system, ItemStack, ItemLockMode } from "@minecraft/server";

const DESTS = __DESTS__;
const COOLDOWN_TICKS = 20;
const AUTO_KEY = "at:auto_tp_items";
const lastUse = new Map();

function autoGive() {
  const v = world.getDynamicProperty(AUTO_KEY);
  return v === undefined ? true : v === true;
}

function makeItem(d) {
  const item = new ItemStack(d.item, 1);
  item.nameTag = d.name;
  item.setLore(d.lore);
  item.lockMode = ItemLockMode.inventory;
  item.keepOnDeath = true;
  return item;
}

function isDestItem(item, d) {
  return item !== undefined && item.typeId === d.item && item.nameTag === d.name;
}

function destOf(item) {
  if (item === undefined) return undefined;
  return DESTS.find((d) => isDestItem(item, d));
}

function containerOf(player) {
  const inv = player.getComponent("minecraft:inventory");
  return inv ? inv.container : undefined;
}

// Give every TP item the player is missing (preferred hotbar slot, otherwise any free slot).
function giveKit(player) {
  const c = containerOf(player);
  if (!c) return 0;
  let given = 0;
  for (const d of DESTS) {
    let has = false;
    for (let i = 0; i < c.size; i++) {
      if (isDestItem(c.getItem(i), d)) {
        has = true;
        break;
      }
    }
    if (has) continue;
    if (c.getItem(d.slot) === undefined) c.setItem(d.slot, makeItem(d));
    else c.addItem(makeItem(d));
    given++;
  }
  return given;
}

function clearKit(player) {
  const c = containerOf(player);
  if (!c) return;
  for (let i = 0; i < c.size; i++) {
    if (destOf(c.getItem(i)) !== undefined) c.setItem(i, undefined);
  }
}

function travel(player, d) {
  const now = system.currentTick;
  const prev = lastUse.get(player.id);
  if (prev !== undefined && now - prev < COOLDOWN_TICKS) return;
  lastUse.set(player.id, now);
  player.teleport(d.pos, { dimension: world.getDimension("overworld"), facingLocation: d.face });
  player.onScreenDisplay.setTitle(d.title, {
    fadeInDuration: 5,
    stayDuration: 30,
    fadeOutDuration: 10,
    subtitle: d.subtitle,
  });
  player.playSound("mob.endermen.portal");
}

function onUse(ev) {
  const player = ev.source;
  if (!player || player.typeId !== "minecraft:player") return;
  const d = destOf(ev.itemStack);
  if (d !== undefined) travel(player, d);
}

world.afterEvents.itemUse.subscribe(onUse);
// right-clicking while looking at a block counts too
if (world.afterEvents.itemUseOn) world.afterEvents.itemUseOn.subscribe(onUse);

world.afterEvents.playerSpawn.subscribe((ev) => {
  if (!autoGive()) return;
  const player = ev.player;
  system.runTimeout(() => {
    try {
      giveKit(player);
    } catch (e) {
      // player left before the delay ran out
    }
  }, 20);
});

// /scriptevent at:tpitems give|clear|auto_on|auto_off|diag    (as a player: only that player)
// /scriptevent at:tp lobby|forest|volcano|paradise|factory     (as a player)
system.afterEvents.scriptEventReceive.subscribe(
  (ev) => {
    const src = ev.sourceEntity;
    const isPlayer = src !== undefined && src.typeId === "minecraft:player";
    const targets = isPlayer ? [src] : world.getAllPlayers();
    const arg = ev.message.trim();
    if (ev.id === "at:tpitems") {
      if (arg === "give") targets.forEach(giveKit);
      else if (arg === "clear") targets.forEach(clearKit);
      else if (arg === "auto_on") world.setDynamicProperty(AUTO_KEY, true);
      else if (arg === "auto_off") world.setDynamicProperty(AUTO_KEY, false);
      else if (arg === "diag") {
        console.warn(
          "[at] tp items ok: dests=" + DESTS.length +
          " itemUse=" + typeof world.afterEvents.itemUse +
          " itemUseOn=" + typeof world.afterEvents.itemUseOn +
          " playerSpawn=" + typeof world.afterEvents.playerSpawn +
          " lock=" + ItemLockMode.inventory +
          " auto=" + autoGive() +
          " sample=" + makeItem(DESTS[0]).nameTag
        );
      }
    } else if (ev.id === "at:tp" && isPlayer) {
      const d = DESTS.find((x) => x.key === arg);
      if (d !== undefined) {
        lastUse.delete(src.id);
        travel(src, d);
      }
    }
  },
  { namespaces: ["at"] }
);
