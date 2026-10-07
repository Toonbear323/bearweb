"""Resource pack checker (the dedicated server never loads resource packs, so this does it offline).

Parses every JSON file and follows the references a client would follow: client entities -> geometry, textures,
animations, animation controllers, render controllers; item_texture.json -> png files; particles -> textures;
client biomes -> fog identifiers. Prints problems and exits non-zero when there are any.

usage: python rp_check.py <resource pack dir>
"""
import json
import os
import re
import sys


def load(path):
    txt = open(path, encoding="utf8").read()
    txt = re.sub(r"^\s*//.*$", "", txt, flags=re.M)
    return json.loads(txt)


def main(rp):
    problems = []
    docs = {}
    for root, _, files in os.walk(rp):
        for f in files:
            if f.endswith(".json"):
                p = os.path.join(root, f)
                try:
                    docs[os.path.relpath(p, rp)] = load(p)
                except Exception as e:
                    problems.append("bad json %s: %s" % (os.path.relpath(p, rp), e))
    geos, anims, ctrls, rcs, fogs = set(), set(), set(), set(), set()
    for rel, d in docs.items():
        if not isinstance(d, dict):
            continue
        for g in d.get("minecraft:geometry", []):
            geos.add(g["description"]["identifier"])
        anims.update(d.get("animations", {}).keys())
        ctrls.update(d.get("animation_controllers", {}).keys())
        rcs.update(d.get("render_controllers", {}).keys())
        if "minecraft:fog_settings" in d:
            fogs.add(d["minecraft:fog_settings"]["description"]["identifier"])

    def tex_exists(t):
        return any(os.path.exists(os.path.join(rp, t + ext)) for ext in (".png", ".tga", ".jpg"))
    n_ent = 0
    for rel, d in docs.items():
        ce = d.get("minecraft:client_entity") if isinstance(d, dict) else None
        if not ce:
            continue
        n_ent += 1
        desc = ce["description"]
        ident = desc.get("identifier")
        for k, g in desc.get("geometry", {}).items():
            if g not in geos:
                problems.append("%s: geometry %s missing" % (ident, g))
        for k, t in desc.get("textures", {}).items():
            if not tex_exists(t):
                problems.append("%s: texture %s missing" % (ident, t))
        for k, a in desc.get("animations", {}).items():
            if a.startswith("animation.") and a not in anims:
                problems.append("%s: animation %s missing" % (ident, a))
            if a.startswith("controller.") and a not in ctrls:
                problems.append("%s: animation controller %s missing" % (ident, a))
        for r in desc.get("render_controllers", []):
            rid = r if isinstance(r, str) else list(r.keys())[0]
            if not rid.startswith("controller.render.default") and rid not in rcs:
                problems.append("%s: render controller %s missing" % (ident, rid))
    it = docs.get(os.path.join("textures", "item_texture.json"))
    if it:
        for k, v in it.get("texture_data", {}).items():
            t = v["textures"]
            for tt in (t if isinstance(t, list) else [t]):
                if not tex_exists(tt):
                    problems.append("item texture %s -> %s missing" % (k, tt))
    for rel, d in docs.items():
        pe = d.get("particle_effect") if isinstance(d, dict) else None
        if pe:
            t = pe["description"].get("basic_render_parameters", {}).get("texture")
            if t and not tex_exists(t):
                problems.append("particle %s: texture %s missing" % (pe["description"]["identifier"], t))
        cb = d.get("minecraft:client_biome") if isinstance(d, dict) else None
        if cb:
            fid = cb.get("components", {}).get("minecraft:fog_appearance", {}).get("fog_identifier")
            if fid and fid not in fogs:
                problems.append("biome %s: fog %s missing" % (cb["description"]["identifier"], fid))
    man = docs.get("manifest.json")
    if not man:
        problems.append("manifest.json missing")
    print("checked %d json files, %d client entities, %d geometries, %d animations, %d controllers, %d render controllers, %d fogs"
          % (len(docs), n_ent, len(geos), len(anims), len(ctrls), len(rcs), len(fogs)))
    for p in problems:
        print("PROBLEM", p)
    print("problems:", len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
