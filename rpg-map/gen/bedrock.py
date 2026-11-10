"""Bedrock world writer: LevelDB chunks (sub-chunk v9 / Data3D), level.dat and .mcworld packaging."""
import json
import os
import shutil
import struct
import time
import zipfile

import numpy as np

from .core import REG, Byte, Float, Long, nbt

CHUNK_VERSION = 40
_BITS = [1, 2, 3, 4, 5, 6, 8, 16]


def _pack(idx, n_pal):
    """Pack 4096 palette indices into Bedrock's word-aligned bit storage."""
    for bits in _BITS:
        if (1 << bits) >= n_pal:
            break
    bpw = 32 // bits
    nw = -(-4096 // bpw)
    buf = np.zeros(nw * bpw, np.uint32)
    buf[:4096] = idx
    buf = buf.reshape(nw, bpw)
    shifts = (np.arange(bpw, dtype=np.uint32) * bits).astype(np.uint32)
    words = np.bitwise_or.reduce(buf << shifts, axis=1).astype("<u4")
    return bits, words.tobytes()


def _layer(sub):
    """sub: (16,16,16) [x,z,y] uint16 block ids -> serialized palettized layer."""
    flat = sub.reshape(-1)
    pal, inv = np.unique(flat, return_inverse=True)
    bits, data = _pack(inv, len(pal))
    out = [bytes([bits << 1]), data, struct.pack("<i", len(pal))]
    for p in pal:
        out.append(REG.palette_nbt(int(p)))
    return b"".join(out)


def _biome_section(arr):
    pal, inv = np.unique(arr.reshape(-1), return_inverse=True)
    if len(pal) == 1:
        return b"\x01" + struct.pack("<i", int(pal[0]))
    bits, data = _pack(inv, len(pal))
    return bytes([(bits << 1) | 1]) + data + struct.pack("<I", len(pal)) + pal.astype("<i4").tobytes()


def write_dimension(db, world, water_id, log=print):
    """Serialise every chunk of a World into the open LevelDB handle."""
    dim = world.dim
    y_min_dim = -64 if dim == 0 else 0
    n_bio = 25 if dim == 0 else 9
    assert world.y0 == y_min_dim, "world array must start at the dimension floor"
    nsub = world.sy // 16
    wl_layer_cache = {}
    # block entities grouped by chunk
    be_by_chunk = {}
    for (x, y, z), d in world.be.items():
        be_by_chunk.setdefault((x >> 4, z >> 4), []).append(d)
    boxes = world.biome_boxes
    batch = {}
    total = 0
    cx0, cz0 = world.x0 >> 4, world.z0 >> 4
    ncx, ncz = world.sx >> 4, world.sz >> 4
    for i in range(ncx):
        for j in range(ncz):
            cx, cz = cx0 + i, cz0 + j
            key = struct.pack("<ii", cx, cz) + (struct.pack("<i", dim) if dim else b"")
            ch = world.b[i * 16:(i + 1) * 16, j * 16:(j + 1) * 16, :]
            wl = world.wl[i * 16:(i + 1) * 16, j * 16:(j + 1) * 16, :]
            nz = ch != 0
            any_y = nz.any(axis=(0, 1))
            if not any_y.any():
                top_sub = -1
            else:
                top_sub = int(np.nonzero(any_y)[0][-1]) // 16
            for s in range(top_sub + 1):
                sub = ch[:, :, s * 16:(s + 1) * 16]
                if not any_y[s * 16:(s + 1) * 16].any():
                    continue
                swl = wl[:, :, s * 16:(s + 1) * 16]
                yidx = (world.y0 >> 4) + s
                layers = [_layer(sub)]
                if swl.any():
                    l2 = np.where(swl & (sub != water_id) & (sub != 0), water_id, 0).astype(np.uint16)
                    if l2.any():
                        layers.append(_layer(l2))
                val = bytes([9, len(layers), yidx & 0xFF]) + b"".join(layers)
                batch[key + b"\x2f" + struct.pack("<b", yidx)] = val
            # height map (zx order) relative to dimension floor
            rev = nz[:, :, ::-1]
            first = rev.argmax(axis=2)
            h = np.where(nz.any(axis=2), world.sy - first, 0).astype("<i2")
            d3 = [np.ascontiguousarray(h.T).tobytes()]
            bcol = world.biome[i * 16:(i + 1) * 16, j * 16:(j + 1) * 16]
            hit = [bx for bx in boxes if not (bx[3] < cx * 16 or bx[0] > cx * 16 + 15 or bx[5] < cz * 16 or
                                             bx[2] > cz * 16 + 15)]
            uniform = bcol.min() == bcol.max()
            for s in range(n_bio):
                ya = y_min_dim + s * 16
                shit = [bx for bx in hit if not (bx[4] < ya or bx[1] > ya + 15)]
                if uniform and not shit:
                    d3.append(b"\x01" + struct.pack("<i", int(bcol[0, 0])))
                    continue
                arr = np.repeat(bcol[:, :, None], 16, axis=2).astype(np.int32)
                for (xa, yb0, za, xb, yb1, zb, bid_) in shit:
                    lx0, lx1 = max(xa - cx * 16, 0), min(xb - cx * 16, 15)
                    lz0, lz1 = max(za - cz * 16, 0), min(zb - cz * 16, 15)
                    ly0, ly1 = max(yb0 - ya, 0), min(yb1 - ya, 15)
                    arr[lx0:lx1 + 1, lz0:lz1 + 1, ly0:ly1 + 1] = bid_
                d3.append(_biome_section(arr))
            batch[key + b"\x2b"] = b"".join(d3)
            batch[key + b"\x2c"] = bytes([CHUNK_VERSION])
            batch[key + b"\x36"] = struct.pack("<i", 2)
            bes = be_by_chunk.get((cx, cz))
            if bes:
                batch[key + b"\x31"] = b"".join(nbt(d) for d in bes)
            total += 1
            if len(batch) > 4000:
                db.putBatch(batch)
                batch = {}
        if i % 8 == 0:
            log("  dim %d: column %d/%d" % (dim, i, ncx))
    if batch:
        db.putBatch(batch)
    return total


FLAT_LAYERS = {
    "biome_id": 0,
    "block_layers": [
        {"block_name": "minecraft:bedrock", "count": 1},
        {"block_name": "minecraft:stone", "count": 103},
        {"block_name": "minecraft:sand", "count": 3},
        {"block_name": "minecraft:water", "count": 20},
    ],
    "encoding_version": 6,
    "structure_options": None,
    "world_version": "version.post_1_18",
}


def level_dat(name, spawn, seed=20261110):
    now = int(time.time())
    d = {
        "BiomeOverride": "",
        "CenterMapsToOrigin": Byte(0),
        "ConfirmedPlatformLockedContent": Byte(0),
        "Difficulty": 2,
        "FlatWorldLayers": json.dumps(FLAT_LAYERS, separators=(",", ":")),
        "ForceGameType": Byte(0),
        "GameType": 0,
        "Generator": 2,
        "InventoryVersion": "1.21.0",
        "LANBroadcast": Byte(1),
        "LANBroadcastIntent": Byte(1),
        "LastPlayed": Long(now),
        "LevelName": name,
        "LimitedWorldOriginX": spawn[0],
        "LimitedWorldOriginY": 32767,
        "LimitedWorldOriginZ": spawn[2],
        "MinimumCompatibleClientVersion": [1, 21, 0, 0, 0],
        "MultiplayerGame": Byte(1),
        "MultiplayerGameIntent": Byte(1),
        "NetherScale": 8,
        "NetworkVersion": 685,
        "Platform": 2,
        "PlatformBroadcastIntent": 3,
        "RandomSeed": Long(seed),
        "SpawnV1Villagers": Byte(0),
        "SpawnX": spawn[0],
        "SpawnY": spawn[1],
        "SpawnZ": spawn[2],
        "StorageVersion": 10,
        "Time": Long(1000),
        "WorldVersion": 1,
        "XBLBroadcastIntent": 3,
        "abilities": {
            "attackmobs": Byte(1), "attackplayers": Byte(1), "build": Byte(1), "doorsandswitches": Byte(1),
            "flySpeed": Float(0.05), "flying": Byte(0), "instabuild": Byte(0), "invulnerable": Byte(0),
            "lightning": Byte(0), "mayfly": Byte(0), "mine": Byte(1), "op": Byte(0), "opencontainers": Byte(1),
            "teleport": Byte(0), "walkSpeed": Float(0.1),
        },
        "baseGameVersion": "*",
        "bonusChestEnabled": Byte(0),
        "bonusChestSpawned": Byte(0),
        "cheatsEnabled": Byte(1),
        "commandblockoutput": Byte(0),
        "commandblocksenabled": Byte(1),
        "commandsEnabled": Byte(1),
        "currentTick": Long(1000),
        "daylightCycle": 0,
        "dodaylightcycle": Byte(1),
        "doentitydrops": Byte(1),
        "dofiretick": Byte(0),
        "doimmediaterespawn": Byte(0),
        "doinsomnia": Byte(0),
        "dolimitedcrafting": Byte(0),
        "domobloot": Byte(1),
        "domobspawning": Byte(1),
        "dotiledrops": Byte(1),
        "doweathercycle": Byte(1),
        "drowningdamage": Byte(1),
        "eduOffer": 0,
        "educationFeaturesEnabled": Byte(0),
        "experiments": {"experiments_ever_used": Byte(0), "saved_with_toggled_experiments": Byte(0)},
        "falldamage": Byte(1),
        "firedamage": Byte(1),
        "freezedamage": Byte(1),
        "functioncommandlimit": 10000,
        "hasBeenLoadedInCreative": Byte(1),
        "hasLockedBehaviorPack": Byte(0),
        "hasLockedResourcePack": Byte(0),
        "immutableWorld": Byte(0),
        "isCreatedInEditor": Byte(0),
        "isFromLockedTemplate": Byte(0),
        "isFromWorldTemplate": Byte(0),
        "isRandomSeedAllowed": Byte(0),
        "isSingleUseWorld": Byte(0),
        "isWorldTemplateOptionLocked": Byte(0),
        "keepinventory": Byte(1),
        "lastOpenedWithVersion": [1, 21, 0, 3, 0],
        "lightningLevel": Float(0.0),
        "lightningTime": 120000,
        "limitedWorldDepth": 16,
        "limitedWorldWidth": 16,
        "maxcommandchainlength": 65535,
        "mobgriefing": Byte(0),
        "naturalregeneration": Byte(1),
        "permissionsLevel": 0,
        "playerPermissionsLevel": 1,
        "playerssleepingpercentage": 100,
        "prid": "",
        "projectilescanbreakblocks": Byte(1),
        "pvp": Byte(0),
        "rainLevel": Float(0.0),
        "rainTime": 120000,
        "randomtickspeed": 1,
        "recipesunlock": Byte(0),
        "requiresCopiedPackRemovalCheck": Byte(0),
        "respawnblocksexplode": Byte(0),
        "sendcommandfeedback": Byte(0),
        "serverChunkTickRange": 4,
        "showbordereffect": Byte(1),
        "showcoordinates": Byte(1),
        "showdaysplayed": Byte(0),
        "showdeathmessages": Byte(1),
        "showrecipemessages": Byte(0),
        "showtags": Byte(1),
        "spawnMobs": Byte(1),
        "spawnradius": 1,
        "startWithMapEnabled": Byte(0),
        "texturePacksRequired": Byte(0),
        "tntexplodes": Byte(0),
        "tntexplosiondropdecay": Byte(0),
        "useMsaGamertagsOnly": Byte(0),
        "worldStartCount": Long(4294967295),
        "world_policies": {},
    }
    body = nbt(d)
    return struct.pack("<ii", 10, len(body)) + body


def write_world(folder, name, spawn, worlds, water_id, packs=None, icon=None, log=print):
    """worlds: list of World objects (one per dimension)."""
    from leveldb import LevelDB
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    db = LevelDB(os.path.join(folder, "db"), create_if_missing=True)
    for w in worlds:
        n = write_dimension(db, w, water_id, log=log)
        log("dimension %d: %d chunks" % (w.dim, n))
    db.compact()
    db.close()
    for f in ("LOCK",):
        p = os.path.join(folder, "db", f)
        if os.path.exists(p):
            os.remove(p)
    ld = level_dat(name, spawn)
    open(os.path.join(folder, "level.dat"), "wb").write(ld)
    open(os.path.join(folder, "level.dat_old"), "wb").write(ld)
    open(os.path.join(folder, "levelname.txt"), "w", encoding="utf-8").write(name)
    if icon and os.path.exists(icon):
        shutil.copy(icon, os.path.join(folder, "world_icon.jpeg"))
    if packs:
        refs = []
        for src, uuid, version in packs:
            dst = os.path.join(folder, "behavior_packs", os.path.basename(src.rstrip("/")))
            shutil.copytree(src, dst)
            refs.append({"pack_id": uuid, "version": version})
        json.dump(refs, open(os.path.join(folder, "world_behavior_packs.json"), "w"), indent=1)
        json.dump([], open(os.path.join(folder, "world_resource_packs.json"), "w"))


def pack_mcworld(folder, out):
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, _, files in os.walk(folder):
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, folder))
    return os.path.getsize(out)
