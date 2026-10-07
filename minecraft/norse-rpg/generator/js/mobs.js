// Themed vanilla mobs for combat zones and boss summons.
import { MOBS } from "./data.js";
import { OW, valid } from "./util.js";

const SLOT = { head: "slot.armor.head", chest: "slot.armor.chest", legs: "slot.armor.legs", feet: "slot.armor.feet", hand: "slot.weapon.mainhand" };
const EFFECT_TIME = 20000000;

export function spawnMob(key, loc, tags, dim, tier) {
  const def = MOBS[key];
  if (!def) return undefined;
  const [type, name, gear, effects] = def;
  dim = dim || OW();
  let e;
  try { e = dim.spawnEntity(type, loc); } catch (err) { return undefined; }
  try { e.nameTag = name; } catch (err) { }
  for (const t of tags || []) try { e.addTag(t); } catch (err) { }
  try { e.addTag("nrpg_mob"); } catch (err) { }
  for (const slot in gear) {
    try { e.runCommand("replaceitem entity @s " + SLOT[slot] + " 0 " + gear[slot]); } catch (err) { }
  }
  for (const eff in effects) {
    try { e.addEffect(eff, EFFECT_TIME, { amplifier: effects[eff], showParticles: false }); } catch (err) { }
  }
  // undead with a helmet never burn; the rest get fire resistance outdoors so the dusk sun does not matter
  try { e.addEffect("fire_resistance", EFFECT_TIME, { amplifier: 0, showParticles: false }); } catch (err) { }
  // deeper realms breed tougher foes
  const extra = tier === "high" ? { health_boost: 3, strength: 1, resistance: 0 } : tier === "mid" ? { health_boost: 1, strength: 0 } : {};
  for (const eff in extra) {
    try { e.addEffect(eff, EFFECT_TIME, { amplifier: extra[eff], showParticles: false }); } catch (err) { }
  }
  if (extra.health_boost !== undefined) {
    try { e.getComponent("minecraft:health").resetToMaxValue(); } catch (err) { }
  }
  return e;
}

export function removeTagged(tag, dim) {
  let n = 0;
  try {
    for (const e of (dim || OW()).getEntities({ tags: [tag] })) {
      if (valid(e)) { try { e.remove(); n++; } catch (err) { } }
    }
  } catch (err) { }
  return n;
}
