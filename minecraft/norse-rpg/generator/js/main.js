// 아홉 세계의 항해 — behaviour pack entry point (@minecraft/server 2.0, @minecraft/server-ui 2.0)
import { world, system } from "@minecraft/server";
import { OW, players, hdist } from "./util.js";
import { initBosses, forceBoss, bossStatus, TEST, allCtl, resetArena } from "./bosses.js";
import { liveCount, cleanupAll, TG_ID } from "./telegraph.js";
import { initRpg, rpgEvent } from "./rpg.js";
import { ARENAS, BOSSES } from "./data.js";

let started = false;
function init() {
  if (started) return;
  started = true;
  initBosses();
  initRpg();
  console.warn("[nrpg] ready: arenas=" + ARENAS.length + " bosses=" + Object.keys(BOSSES).length);
}
world.afterEvents.worldLoad.subscribe(() => init());
system.runTimeout(() => init(), 20);

// ---------------------------------------------------------------- admin / test events
system.afterEvents.scriptEventReceive.subscribe((ev) => {
  const id = ev.id, msg = (ev.message || "").trim();
  const args = msg.length ? msg.split(/\s+/) : [];
  if (!id.startsWith("nrpg:")) return;
  if (id === "nrpg:test") {
    // nrpg:test <arena> [skill ...]: boss fight against training dummies, skills cast in the given order
    TEST.on = true;
    const A = ARENAS.find((a) => a.id === args[0]);
    if (!A) { console.warn("[nrpg] test: no arena " + args[0]); return; }
    const dim = OW();
    try { for (const e of dim.getEntities({ type: "nrpg:dummy", location: { x: A.x, y: A.y, z: A.z }, maxDistance: A.r + 6 })) e.remove(); } catch (e) { }
    const spots = [[4, 0], [-3, 5], [0, -7]];
    for (const [dx, dz] of spots) {
      try { const d = dim.spawnEntity("nrpg:dummy", { x: A.x + dx + 0.5, y: A.y, z: A.z + dz + 0.5 }); d.nameTag = "dummy"; } catch (e) { console.warn("[nrpg] dummy failed " + e); }
    }
    const skills = args.length > 1 ? args.slice(1) : Object.keys(BOSSES[A.boss].skills);
    console.warn("[nrpg] test " + A.id + " -> " + forceBoss(A.id, skills) + " skills=" + skills.join(","));
  } else if (id === "nrpg:status") {
    console.warn("[nrpg] status " + bossStatus().join(" | ") + " telegraphs=" + liveCount());
  } else if (id === "nrpg:probe") {
    // list live telegraph entities with their synced properties
    const out = [];
    try {
      for (const e of OW().getEntities({ type: TG_ID })) {
        const r = e.getRotation();
        out.push(["s" + e.getProperty("nrpg:shape"), "a" + Number(e.getProperty("nrpg:a")).toFixed(1), "b" + Number(e.getProperty("nrpg:b")).toFixed(1),
          "v" + e.getProperty("nrpg:v"), "c" + e.getProperty("nrpg:col"), "yaw" + Math.round(r.y)].join(","));
      }
    } catch (e) { out.push("err " + e); }
    console.warn("[nrpg] probe n=" + out.length + " " + out.slice(0, 12).join(" ; "));
  } else if (id === "nrpg:dummies") {
    const out = [];
    try {
      for (const e of OW().getEntities({ type: "nrpg:dummy" })) {
        out.push(Math.round(e.getComponent("minecraft:health").currentValue));
      }
    } catch (e) { out.push("err " + e); }
    console.warn("[nrpg] dummies hp=" + out.join(","));
  } else if (id === "nrpg:hurt") {
    // nrpg:hurt <arena> <fraction of max hp>
    const c = allCtl().get(args[0]);
    if (c && c.ent) {
      try {
        const h = c.ent.getComponent("minecraft:health");
        h.setCurrentValue(Math.max(1, h.currentValue - h.effectiveMax * Number(args[1] || 0.4)));
        console.warn("[nrpg] hurt " + args[0] + " -> " + Math.round(h.currentValue) + "/" + h.effectiveMax);
      } catch (e) { console.warn("[nrpg] hurt failed " + e); }
    }
  } else if (id === "nrpg:kill") {
    const c = allCtl().get(args[0]);
    if (c && c.ent) { try { c.ent.kill(); } catch (e) { console.warn("[nrpg] kill failed " + e); } }
  } else if (id === "nrpg:reset") {
    for (const c of allCtl().values()) resetArena(c);
    cleanupAll();
    TEST.on = false;
    console.warn("[nrpg] reset all arenas");
  } else {
    rpgEvent(id, args, ev.sourceEntity);
  }
});
